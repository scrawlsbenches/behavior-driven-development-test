# Developer Tooling Scripts

This directory contains **developer tooling** - scripts that enforce codebase quality but aren't user-facing behavior.

## Quick Start

After cloning the repository, run:

```bash
./scripts/setup-dev.sh
```

This configures git hooks and installs dependencies. The architecture check will run automatically on every commit.

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

### setup-dev.sh

One-time setup after cloning:

```bash
./scripts/setup-dev.sh
```

This:
- Configures git to use `scripts/hooks/` for git hooks
- Installs the package in development mode
- No manual hook installation needed

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

## Hooks

The `hooks/` subdirectory contains git hooks that run automatically:

| Hook | Trigger | What It Does |
|------|---------|--------------|
| `pre-commit` | Before each commit | Runs architecture check |

Hooks are activated by `setup-dev.sh` via `git config core.hooksPath scripts/hooks`.

## Adding New Scripts

When adding developer tooling:

1. **Ask:** Does this enforce user behavior or code organization?
2. **If user behavior:** Write a behave feature with a persona
3. **If code organization:** Add a script here

Keep scripts focused and fast - they run on every commit/PR.
