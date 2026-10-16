#!/usr/bin/env python3
"""CLI interface for hermes-model-roles plugin."""
import sys
from .core import apply_roles, check_drift, get_role_value, load_roles, desired_map
from .drift import run_scan

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print("Usage: hermes-model-roles [get <role> | apply [--dry-run] [--only PREFIX] | check | scan [--no-allow]]")
        sys.exit(0)

    cmd = args[0]
    if cmd == "get":
        if len(args) < 2:
            sys.exit("Error: role name required. e.g. hermes-model-roles get worker")
        get_role_value(args[1])
    elif cmd == "apply":
        dry = "--dry-run" in args
        only = None
        if "--only" in args:
            idx = args.index("--only")
            if idx + 1 >= len(args):
                sys.exit("Error: --only requires a PREFIX argument (e.g. --only delegation)")
            only = args[idx + 1]
        apply_roles(dry=dry, only=only)
    elif cmd in ("check", "--check"):
        roles = load_roles()
        want = desired_map(roles)
        check_drift(want)
    elif cmd == "scan":
        use_allow = "--no-allow" not in args
        roots = [args[i + 1] for i, a in enumerate(args) if a == "--root"]
        total = run_scan(roots=roots or None, use_allow=use_allow)
        sys.exit(1 if total else 0)
    else:
        sys.exit(f"Unknown command '{cmd}'. Available: get, apply, check, scan")

def handle_slash_command(raw_args: str) -> str:
    """Handler for /roles in Hermes chat sessions."""
    parts = raw_args.strip().split()
    if not parts:
        return "Usage: /roles [get <role> | check | scan]"
    sub = parts[0]
    if sub == "get":
        if len(parts) < 2:
            return "Usage: /roles get <role>"
        roles = load_roles()
        rol = roles.get(parts[1])
        if not rol:
            return f"Role '{parts[1]}' not found. Available: {list(roles.keys())}"
        return f"{rol.get('provider')} / {rol.get('model')}"
    elif sub == "check":
        roles = load_roles()
        want = desired_map(roles)
        try:
            check_drift(want)
            return "✓ 0 keys with drift. Config is in sync with model-roles.json."
        except SystemExit as e:
            return "⚠️ Drift detected between config and model-roles.json. Run `hermes roles apply` to fix."
    elif sub == "scan":
        total = run_scan()
        if total == 0:
            return "✓ Skill library clean. 0 unpinned model IDs found."
        return f"⚠️ {total} model ID offenders found in skill library."
    return f"Unknown /roles action '{sub}'. Use: get, check, scan"

if __name__ == "__main__":
    main()
