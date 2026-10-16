#!/usr/bin/env python3
"""Centralized model roles and configuration sync for Hermes Agent."""
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import yaml

def get_home():
    return os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))

def get_roles_file():
    return os.path.join(get_home(), "model-roles.json")

def get_cfg_file():
    return os.path.join(get_home(), "config.yaml")

def hermes(*args):
    env = os.environ.copy()
    env["HERMES_HOME"] = get_home()
    timeout = int(os.environ.get("HERMES_CMD_TIMEOUT", "60"))
    return subprocess.run(["hermes", *args], capture_output=True, text=True, timeout=timeout, env=env)

def load_roles():
    path = get_roles_file()
    if not os.path.exists(path):
        sys.exit(f"Roles file not found: {path}. Create it or copy from templates/model-roles.example.json")
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    roles = d.get("roles", {})
    for req in ("main", "main_fallbacks", "worker", "worker_fallbacks", "vision"):
        if req not in roles:
            sys.exit(f"Invalid model-roles.json: missing role '{req}'")
    return roles

def get_aux_sections():
    cfg_path = get_cfg_file()
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            aux = cfg.get("auxiliary", {})
            if isinstance(aux, dict):
                return [k for k in aux.keys() if k != "vision"]
        except yaml.YAMLError as exc:
            print(f"Warning: could not parse {cfg_path} ({exc}); falling back to CLI discovery.", file=sys.stderr)
        except OSError as exc:
            print(f"Warning: could not read {cfg_path} ({exc}); falling back to CLI discovery.", file=sys.stderr)
    r = hermes("config", "get", "auxiliary")
    return [ln.strip().rstrip(":") for ln in r.stdout.splitlines()
            if ln and not ln[0].isspace() and ln.rstrip().endswith(":") and ln.strip().rstrip(":") != "vision"]

def desired_map(roles):
    m, w, v = roles["main"], roles["worker"], roles["vision"]
    out = {
        "model.default": m["model"],
        "model.provider": m["provider"],
        "fallback_providers": json.dumps(roles["main_fallbacks"]),
        "delegation.provider": w["provider"],
        "delegation.model": w["model"],
        "delegation.fallback_providers": json.dumps(roles["worker_fallbacks"]),
        "auxiliary.vision.provider": v["provider"],
        "auxiliary.vision.model": v["model"],
    }
    for s in get_aux_sections():
        out[f"auxiliary.{s}.provider"] = m["provider"]
        out[f"auxiliary.{s}.model"] = m["model"]
    return out

def check_drift(want):
    drift = 0
    cfg_path = get_cfg_file()
    live_cfg = {}
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                live_cfg = yaml.safe_load(f) or {}
        except Exception:
            pass

    for k, v in want.items():
        val_live = live_cfg
        for part in k.split("."):
            if isinstance(val_live, dict):
                val_live = val_live.get(part)
            else:
                val_live = None
                break

        if val_live is None:
            raw = hermes("config", "get", k).stdout.strip()
            try:
                val_live = yaml.safe_load(raw)
            except Exception:
                val_live = raw

        try:
            want_parsed = json.loads(str(v)) if str(v).startswith("[") or str(v).startswith("{") else str(v)
        except Exception:
            want_parsed = str(v)

        if val_live != want_parsed:
            print(f"DRIFT {k}:\n  actual:  {val_live!r}\n  deseado: {want_parsed!r}")
            drift += 1
    print(f"{drift} keys with drift out of {len(want)}")
    sys.exit(1 if drift else 0)

def apply_roles(dry=False, only=None):
    roles = load_roles()
    want = desired_map(roles)
    if only:
        want = {k: v for k, v in want.items() if k.startswith(only)}

    cfg_path = get_cfg_file()
    bak = f"{cfg_path}.bak-roles-{time.strftime('%Y%m%d_%H%M%S')}"
    if not dry:
        shutil.copy2(cfg_path, bak)
        print(f"Backup created: {bak}")

    applied = []
    for k, v in want.items():
        cmd_str = f"hermes config set {shlex.quote(k)} {shlex.quote(str(v))}"
        print(("DRY: " if dry else "RUN: ") + cmd_str)
        if not dry:
            r = hermes("config", "set", k, str(v))
            if r.returncode != 0:
                print(f"ERROR applying {k}:\n{r.stderr}\nInitiating automatic ROLLBACK...")
                shutil.copy2(bak, cfg_path)
                print("Rollback completed. config.yaml restored.")
                sys.exit(1)
            applied.append(k)

    print("OK: dry-run completed" if dry else f"OK: {len(applied)} keys successfully applied.")

def get_role_value(rolename):
    roles = load_roles()
    if rolename not in roles:
        sys.exit(f"Unknown role '{rolename}'. Available: {sorted(roles.keys())}")
    rol = roles[rolename]
    if isinstance(rol, dict) and "model" in rol:
        print(f"{rol['provider']} / {rol['model']}")
    else:
        print(json.dumps(rol, ensure_ascii=False))
