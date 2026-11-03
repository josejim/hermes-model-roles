"""Cross-harness adapters: write the native config of a target from model-roles.json.

Writers are idempotent and never create a target file from scratch (a missing
config means the harness was never installed — creating it could fight the
harness's own first-run wizard).
"""
import json
import os
import shutil
import time
import sys


def _backup(path):
    bak = f"{path}.bak-roles-{time.strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(path, bak)
    return bak


def _load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _dump_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _refuse_missing(path, target):
    if not os.path.exists(path):
        sys.exit(f"target config not found for {target}: {path} (never created blindly)")


def apply_claude(roles_path, target_path):
    _refuse_missing(target_path, "claude")
    _, model = _main(roles_path)
    _backup(target_path)
    cfg = _load_json(target_path)
    cfg["model"] = model
    if isinstance(cfg.get("env"), dict) and "ANTHROPIC_MODEL" in cfg["env"]:
        cfg["env"]["ANTHROPIC_MODEL"] = model
    _dump_json(target_path, cfg)
    return {"model": model}


def check_claude(roles_path, target_path):
    _refuse_missing(target_path, "claude")
    _, model = _main(roles_path)
    live = _load_json(target_path).get("model")
    return [] if live == model else [f"claude settings.json model: actual={live!r} deseado={model!r}"]


def apply_opencode(roles_path, target_path):
    _refuse_missing(target_path, "opencode")
    provider, model = _main(roles_path)
    _backup(target_path)
    cfg = _load_json(target_path)
    cfg.setdefault("provider", {}).setdefault(provider, {})["model"] = model
    _dump_json(target_path, cfg)
    return {"provider": provider, "model": model}


def check_opencode(roles_path, target_path):
    _refuse_missing(target_path, "opencode")
    provider, model = _main(roles_path)
    live = _load_json(target_path).get("provider", {}).get(provider, {}).get("model")
    return [] if live == model else [
        f"opencode provider.{provider}.model: actual={live!r} deseado={model!r}"]


def _main(roles_path):
    from .core import resolve_role
    return resolve_role(roles_path, "main")


TARGETS = {
    "claude": {"apply": apply_claude, "check": check_claude,
               "default_path": "~/.claude/settings.json"},
    "opencode": {"apply": apply_opencode, "check": check_opencode,
                 "default_path": "~/.config/opencode/opencode.json"},
}


def apply_target(target, roles_path, target_path=None):
    t = TARGETS[target]
    path = target_path or os.path.expanduser(t["default_path"])
    return t["apply"](roles_path, path)


def check_target(target, roles_path, target_path=None):
    t = TARGETS[target]
    path = target_path or os.path.expanduser(t["default_path"])
    return t["check"](roles_path, path)
