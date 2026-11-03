# model-roles v3 — spec portátil para cualquier harness

**Problema:** cada CLI (Hermes, Claude Code, Codex, OpenCode) guarda el modelo en un archivo distinto y con IDs concretos. Al renombrar o perder el modelo, skills, crons y sesiones se rompen.

**Solución:** un solo `model-roles.json` con roles semánticos. Cada harness se adapta a él con un comando; nadie hardcodea SKUs.

## Reglas
1. **Roles obligatorios:** `main`, `worker`, `vision`. Opcionales: `*_fallbacks` (lista), `cheap`, `reasoning`, `cron_*`.
2. **Identidad = `{provider, model}`**. Nunca un ID pelado. Listas resuelven al primer endpoint.
3. **`status`** (opcional): marca un rol como `legacy-*` para documentar, sin romper el schema.
4. **Ubicación:** `~/.hermes/model-roles.json` (global) o `./model-roles.json` (repo; gana). 
5. **Adapters no crean archivos a ciegas:** si la config del harness no existe, error.
6. **Backup atómico** (`*.bak-roles-<ts>`) antes de escribir.
7. **Sin sustitución silenciosa:** si el modelo del rol no existe en el harness, error explícito.
8. **Nada de SKUs en skills/scripts:** leer el rol (`hermes-model-roles get worker`).

## Comandos
```bash
hermes-model-roles validate                 # JSON válido v3
hermes-model-roles get worker               # "provider / model"
hermes-model-roles apply                    # sincroniza Hermes (config.yaml)
hermes-model-roles check                    # drift Hermes
hermes-model-roles apply-target claude      # ~/.claude/settings.json → model = main.model
hermes-model-roles check-target claude
hermes-model-roles apply-target opencode    # opencode.json provider.<main.provider>.model
hermes-model-roles check-target opencode
hermes-model-roles scan                     # drift de SKUs en skills
```

## Ejemplo
```json
{
  "version": 3,
  "updated": "2026-10-22",
  "roles": {
    "main":   {"provider": "commandcode", "model": "deepseek/deepseek-v4.1-flash-fast"},
    "worker": {"provider": "commandcode", "model": "deepseek/deepseek-v4.1-flash-fast"},
    "vision": {"provider": "commandcode", "model": "deepseek/deepseek-v4-flash-vision-exp"},
    "main_fallbacks": [{"provider": "nous", "model": "upstage/solar-pro4:free"}],
    "cheap": [{"provider": "nous", "model": "upstage/solar-pro4:free"}]
  }
}
```

## Estado del mercado
No existe un estándar abierto equivalente. LiteLLM (`model_group_alias` + fallbacks) es lo más cercano pero es un proxy. Este spec es una convención personal portable; no un RFC de la industria.

## Agregar un target nuevo
1. Writer en `src/hermes_model_roles/targets.py` (apply + check, refuse-missing, backup).
2. Entrada en `TARGETS`.
3. Test en `tests/test_targets.py`.
4. Nada más.
