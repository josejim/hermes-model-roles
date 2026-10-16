# Hermes Model Roles (`hermes-model-roles`)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Hermes Plugin](https://img.shields.io/badge/Hermes_Plugin-v1.0.0-green.svg)](https://hermes-agent.nousresearch.com)

**Centralized model roles and anti-drift guard for [Hermes Agent](https://github.com/NousResearch/hermes-agent).**

Eliminates hardcoded model IDs across agent skills and configuration files. Model IDs change rapidly; hardcoded references create maintenance debt and silent breakage across your skill library.

This plugin introduces:
1. **Single Source of Truth (`model-roles.json`)**: Define semantic roles (`main`, `worker`, `worker_fallbacks`, `vision`).
2. **Automated Configuration Sync (`hermes roles apply`)**: Syncs `model.default`, `delegation.*`, and all dynamic `auxiliary.*` sections with automatic backups and atomic rollback.
3. **Drift Verification (`hermes roles check`)**: PyYAML structural validation ensuring active config matches desired roles.
4. **Anti-Drift Scanner (`hermes roles scan`)**: Failsafe scanner detecting unpinned model IDs in skills, while allowing annotated historical records (`<!-- drift-ok: reason -->`).

---

## Installation

Install directly into Hermes Agent via CLI:

```bash
hermes plugins install github.com/josejim/hermes-model-roles
```

Alternatively, clone into your user plugins directory:
```bash
git clone https://github.com/josejim/hermes-model-roles ~/.hermes/plugins/model-roles
```

---

## Quickstart

### 1. Initialize your model roles

Copy the template to your Hermes home directory:

```bash
cp templates/model-roles.example.json ~/.hermes/model-roles.json
```

Customize roles according to your provider and tier:

```json
{
  "version": 2,
  "roles": {
    "main": {
      "provider": "commandcode",
      "model": "deepseek/deepseek-v4.1-flash-fast"
    },
    "main_fallbacks": [
      {
        "provider": "nous",
        "model": "upstage/solar-pro4:free"
      }
    ],
    "worker": {
      "provider": "commandcode",
      "model": "deepseek/deepseek-v4.1-flash-fast"
    },
    "worker_fallbacks": [
      {
        "provider": "nous",
        "model": "upstage/solar-pro4:free"
      }
    ],
    "vision": {
      "provider": "commandcode",
      "model": "deepseek/deepseek-v4-flash-vision-exp"
    }
  }
}
```

### 2. Apply to Hermes configuration

```bash
# Preview what would change without modifying config.yaml
hermes roles apply --dry-run

# Apply changes (creates automatic backup config.yaml.bak-roles-* first)
hermes roles apply

# Verify zero drift between live config and roles
hermes roles check
```

### 3. Read roles inside Skills

In your `SKILL.md` workflows, instruct agents to query roles dynamically rather than hardcoding names:

```bash
python3 -m hermes_model_roles.cli get worker
# Outputs: commandcode / deepseek/deepseek-v4.1-flash-fast
```

### 4. Scan skills for hardcoded IDs

```bash
hermes roles scan
```

To allow historical notes in skills without triggering the scanner, append an inline marker:

```markdown
Historical benchmark <!-- drift-ok: historical record, not routing -->: model X exhibited high latency.
```

---

## Commands

| Command | Action |
|---|---|
| `hermes roles get <role>` | Read provider/model for a role (read-only runtime contract) |
| `hermes roles apply` | Sync `model-roles.json` to `config.yaml` with rollback protection |
| `hermes roles apply --only <prefix>` | Selectively sync specific configuration subsets |
| `hermes roles check` | Assert zero drift between config and roles (exit 0/1) |
| `hermes roles scan` | Audit skill library against unpinned model IDs |

In Hermes chat sessions, `/roles` is also available as an interactive command.

---

## Contributing & License

Contributions are welcome! Please run `pytest` before submitting pull requests.

Distributed under the **MIT License**.
