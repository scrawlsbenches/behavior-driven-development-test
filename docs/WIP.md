# Work in Progress

Current state of active development.

## Active Work

| Item | Status | Blockers |
|------|--------|----------|
| Data Persistence Steps | Not Started | None |
| Knowledge Management Steps | Not Started | None |

## Recently Completed

| Item | Completed | Notes |
|------|-----------|-------|
| Backwards Compatibility Cleanup | Sprint 1-2 | Single source of truth: graph_of_thought.domain |
| DDD Architecture Refactor | Sprint 1-2 | Domain layer, split services |
| AI Reasoning Steps | Sprint 1-2 | 24 scenarios |
| Governance Steps | Sprint 1-2 | 8 scenarios |
| Cost Management Steps | Sprint 1-2 | 7 scenarios |
| Project Management Steps | Sprint 1-2 | 7 scenarios |

## Test Status

```
pytest:  201 passed
behave:  255 scenarios passed (stable)
         328 scenarios skipped (@wip, @post-mvp)
```

## Features with @wip Scenarios

These features have MVP-P0 scenarios passing, but MVP-P1/P2 scenarios tagged @wip
that still need step definitions:

| Feature | MVP-P0 Status | @wip Scenarios | Need Step Definitions |
|---------|---------------|----------------|----------------------|
| `thought_exploration.feature` | 9 passing | 10 | Yes |
| `intelligent_search.feature` | 8 passing | 11 | Yes |
| `llm_integration.feature` | 7 passing | 21 | Yes |
| `approval_workflows.feature` | 8 passing | 15 | Yes |
| `budget_and_consumption.feature` | 7 passing | 15 | Yes |
| `project_lifecycle.feature` | 7 passing | 11 | Yes |

Note: The @wip tags on these scenarios are correct - they mark scenarios that
don't have step definitions yet. Do NOT remove @wip until step definitions exist.

## Features Needing Step Definitions

| Feature | Undefined Steps | Priority |
|---------|-----------------|----------|
| `data_persistence.feature` | ~40 | @mvp-p0 |
| `decisions_and_learnings.feature` | ~30 | @mvp-p0 |
| `question_routing.feature` | ~25 | @mvp-p0 |
| `observability.feature` | ~35 | @mvp-p1 |

## Quick Commands

```bash
# See what's still undefined
behave --dry-run --tags=@mvp-p0 2>&1 | tail -50

# Run only passing tests
behave --tags="not @wip and not @post-mvp"

# Check architecture
python scripts/check_architecture.py
```
