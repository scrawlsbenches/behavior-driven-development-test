# Graph of Thought

An enterprise AI-assisted reasoning and project management platform.

## What It Does

- **AI Reasoning** - Explore problems systematically using graph-based thought expansion
- **Project Management** - Track work chunks, handoffs, and team collaboration
- **Cost Management** - Monitor token budgets and consumption
- **Governance** - Approval workflows, policies, and audit logging
- **Knowledge Management** - Record decisions, route questions, preserve learnings

## Quick Start

```bash
# Setup development environment
./scripts/setup-dev.sh

# Run tests
behave --tags="not @wip and not @post-mvp"  # BDD scenarios
python -m pytest tests/                       # Architecture tests

# Check architecture
python scripts/check_architecture.py
```

## Project Structure

```
graph_of_thought/           # Core library
├── domain/                 # Domain models and enums (DDD)
├── core/                   # Graph engine and protocols
├── services/               # Business service implementations
└── graph.py                # Main GraphOfThought class

features/                   # BDD specifications (behave)
├── ai_reasoning/           # Thought exploration, search, LLM
├── project_management/     # Work tracking, handoffs
├── cost_management/        # Budgets, consumption
├── governance_compliance/  # Approvals, audit
├── knowledge_management/   # Decisions, questions
├── platform/               # Observability, persistence
└── steps/                  # Step definitions

tests/                      # Architecture validation (pytest)
docs/                       # Planning and documentation
```

## Documentation

| Document | Purpose |
|----------|---------|
| [CLAUDE.md](CLAUDE.md) | BDD practices and project conventions |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Long-term vision and milestones |
| [docs/SPRINTS.md](docs/SPRINTS.md) | Sprint planning and progress |
| [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) | Prioritized immediate actions |
| [docs/WIP.md](docs/WIP.md) | Current work in progress |
| [features/README.md](features/README.md) | Feature organization guide |
| [features/PERSONAS.md](features/PERSONAS.md) | Enterprise persona definitions |

## Architecture

Domain-Driven Design with clean layer separation:

```
domain/     ← No dependencies (models, enums)
    ↑
core/       ← Graph engine, protocols
    ↑
services/   ← Business logic implementations
```

All services use Protocol-based dependency injection for testability.

## Test Status

| Suite | Count | Status |
|-------|-------|--------|
| pytest (architecture) | 232 | Passing |
| behave (stable) | 209 | Passing |
| behave (MVP-P0) | 59+ | In Progress |

## License

Internal use.
