# Developer Tooling Scripts

This directory contains **developer tooling** - scripts that enforce codebase quality but aren't user-facing behavior.

## Why These Aren't BDD Features

BDD features (in `features/`) specify **user behavior**:
- They have personas (Jordan, Morgan, Alex, etc.)
- They describe business value ("So that...")
- Stakeholders can read and validate them

These scripts enforce **developer constraints**:
- No persona benefits from "protocols in the right file"
- They're internal code organization rules
- Only developers care about them

**Rule of thumb:** If you can't identify a persona from `features/PERSONAS.md` who benefits, it's developer tooling, not a BDD feature.

## Available Scripts

### check_architecture.py

Fast architecture enforcement for CI pipelines.

```bash
python scripts/check_architecture.py
```

**Rules enforced:**
- Protocols defined in `protocols.py` only
- Implementations defined in `implementations.py` only
- No global service instances
- No direct service instantiation outside factories
- Business logic imports protocols, not implementations

**Exit codes:**
- `0` - All checks passed
- `1` - Violations found (blocks merge)

**Add to CI:**
```yaml
- name: Check Architecture
  run: python scripts/check_architecture.py
```

## Adding New Scripts

When adding developer tooling:

1. **Ask:** Does this enforce user behavior or code organization?
2. **If user behavior:** Write a behave feature with a persona
3. **If code organization:** Add a script here

Keep scripts focused and fast - they run on every PR.
