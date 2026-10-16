#!/usr/bin/env python3
"""Anti-drift guard scanner for Hermes Agent skills."""
import glob as _glob
import os
import re
import sys

DEFAULT_ROOTS = [os.path.expanduser("~/.hermes/skills")] + _glob.glob(
    os.path.expanduser("~/.hermes/profiles/*/skills"))
ALLOW = os.path.expanduser("~/.hermes/scripts/model-drift-allow.txt")

PROV = r"(?:commandcode|nous|openrouter|openai-codex|omniroute|kiro-cli|deepseek|xkiro)"
KNOWN_FAMILIES = r"(?:claude|gpt|deepseek|qwen|solar|mimo|mistral|gemini|step|ling|longcat|nemotron)"

PATTERNS = [
    re.compile(r"(?<![\w-])(?:--model\s+|-m\s+)('([^']+)'|\"([^\"]+)\"|[a-zA-Z0-9_./:-]+)"),
    re.compile(r"(?<![\w-])config\s+(?:set|unset)\s+\S*(?:model|provider)\S*\s+('([^']+)'|\"([^\"]+)\"|\S+)", re.I),
    re.compile(r"(?<![\w-])\S+:free\b"),
    re.compile(r"(?<![\w-])" + PROV + r"/" + KNOWN_FAMILIES + r"[\w.-]*", re.I),
    re.compile(r"(?<![\w-])(?:gpt-[56][.\w-]*|claude-(?:opus|sonnet|fable|haiku)[.\w-]*)", re.I),
]

DRIFT_OK_RE = re.compile(r"<!--\s*drift-ok:\s*.+?\s*-->", re.I)
SKIP_TOKENS = ("<id>", "<model>", "<rol.model>", "<provider>", "<rol.provider>", "<job-id>", "provider/model")

def load_allow(allow_path=ALLOW):
    if not os.path.exists(allow_path):
        return []
    out = []
    with open(allow_path, encoding="utf-8") as fh:
        for l in fh:
            clean = l.split("#", 1)[0].strip()
            if clean:
                out.append(clean)
    return out

def is_allowed(rel, allow):
    for a in allow:
        if a.endswith("/"):
            if rel.startswith(a):
                return True
        elif a.endswith("SKILL.md"):
            skill_prefix = a[:-len("SKILL.md")]
            if rel.startswith(skill_prefix):
                return True
        elif rel == a:
            return True
    return False

def scan(root, allow, use_allow=True):
    if not os.path.isdir(root):
        print(f"Invalid root: {root}")
        sys.exit(2)
    offenders, scanned = [], 0
    for dirpath, _, files in os.walk(root, followlinks=False):
        for f in files:
            if not f.endswith(".md"):
                continue
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, root)
            if use_allow and is_allowed(rel, allow):
                continue
            scanned += 1
            with open(p, encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh, 1):
                    if DRIFT_OK_RE.search(line):
                        continue
                    for pat in PATTERNS:
                        for m in pat.finditer(line):
                            tok = m.group(0).rstrip(".")
                            if any(t in tok for t in SKIP_TOKENS):
                                continue
                            offenders.append((rel, i, tok))
    return offenders, scanned

def run_scan(roots=None, allow_path=ALLOW, use_allow=True):
    roots = roots or DEFAULT_ROOTS
    allow = load_allow(allow_path)
    total, total_scanned = 0, 0
    for root in roots:
        founders, scanned = scan(root, allow, use_allow)
        total_scanned += scanned
        for rel, i, tok in founders:
            print(f"{root} :: {rel}:{i}: {tok}")
        total += len(founders)
    if use_allow and roots == DEFAULT_ROOTS:
        stale = [a for a in allow if not any(
            os.path.exists(os.path.join(r, a)) for r in DEFAULT_ROOTS)]
        if stale:
            print("Stale allowlist entries (file no longer exists):", stale)
            sys.exit(2)
    if total_scanned == 0:
        print("0 files scanned — nothing to validate")
        sys.exit(2)
    print(f"\n{total} offenders found (scanned: {total_scanned} files; roots: {roots})")
    return total
