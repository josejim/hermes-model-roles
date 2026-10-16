---
name: model-roles
description: "Use when routing or changing models across skills."
version: 1.0.0
author: Jose Jimenez
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [models, configuration, roles, drift, routing]
    requires_tools: [terminal]
---

# Centralized Model Roles

Standing architecture: **never hardcode model IDs in skills or scripts**. Model IDs change frequently; hardcoded references create maintenance debt and silent drift across the skill library.

## Single Source of Truth

All model assignments live in `~/.hermes/model-roles.json`:

```json
{
  "version": 2,
  "roles": {
    "main": {"provider": "commandcode", "model": "<model-id>"}, <!-- drift-ok: schema-example -->
    "main_fallbacks": [ <!-- drift-ok: schema-example -->
      {"provider": "nous", "model": "<fallback-free-1>"}, <!-- drift-ok: schema-example -->
      {"provider": "nous", "model": "<fallback-free-2>"} <!-- drift-ok: schema-example -->
    ],
    "worker": {"provider": "commandcode", "model": "<model-id>"}, <!-- drift-ok: schema-example -->
    "worker_fallbacks": [ <!-- drift-ok: schema-example -->
      {"provider": "nous", "model": "<fallback-free-1>"}, <!-- drift-ok: schema-example -->
      {"provider": "nous", "model": "<fallback-free-2>"} <!-- drift-ok: schema-example -->
    ],
    "vision": {"provider": "commandcode", "model": "<vision-model-id>"} <!-- drift-ok: schema-example -->
  }
}
```

## Reading Roles at Runtime (Read-Only)

Skills and scripts that need to know which model to use MUST read from the roles file — never guess or hardcode:

```bash
hermes-model-roles get <role>     # e.g. get worker -> "commandcode / deepseek/..."
# in-session slash command:
/roles get <role>
```

## Applying Changes to Hermes Config

When a model changes:
1. Edit `~/.hermes/model-roles.json` (update the role's `model` and/or `provider`).
2. Apply to Hermes config (manual action — never called from worker skills):

```bash
hermes-model-roles apply --dry-run   # preview changes
hermes-model-roles apply             # creates config.yaml backup first and applies atomically
hermes-model-roles check             # asserts 0 drift between config and roles
hermes-model-roles apply --only delegation  # selectively applies a group of keys
```

`apply` writes:
- `model.default` and `model.provider`
- `fallback_providers` (from `main_fallbacks`)
- `delegation.model`, `delegation.provider`, `delegation.fallback_providers`
- `auxiliary.vision` (from `vision` role)
- All other `auxiliary.*` sections dynamically discovered from `config.yaml`

If any key fails during apply, an automatic rollback restores the original `config.yaml`.

## Anti-Drift Guard

To prevent model IDs from creeping back into skills:

```bash
hermes-model-roles scan             # exits 0 if clean, 1 if offenders, 2 if configuration is broken
hermes-model-roles scan --no-allow   # scans everything ignoring the allowlist
```

### Legitimate Historical References

When a skill documents historical findings (e.g. "model X failed on benchmark Y"), append an inline comment so the guard skips it:

```markdown
Historical note <!-- drift-ok: historical record, not routing -->: model X exhibited high latency.
```

## Rules and Pitfalls

- **Skills use `get`, never `apply`**: `apply` rewrites global configuration keys. An automated worker skill calling `apply` creates uncontrolled side-effects across the entire gateway.
- **Never put API keys in `argv`**: passing secrets on the command line exposes credentials in process tables (`ps`). Use a config file or environment descriptor.
- **Failsafe guard**: `hermes roles scan` fails closed (exit 2) on missing directories, stale allowlist entries, or zero scanned files.
- **Exceptions must be declared**: external pipelines (e.g. local scripts with dedicated config files), MoA presets, and per-cron overrides are NOT governed by `model-roles.json`. Each must be documented in its owning skill as an explicit exception.
