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
behave:  209 scenarios passed (stable)
         374 scenarios skipped (@wip, @post-mvp)
```

## Features with @wip Tag

These features have step definitions but retain @wip tag:

- [ ] `thought_exploration.feature` - ready for tag removal
- [ ] `intelligent_search.feature` - ready for tag removal
- [ ] `llm_integration.feature` - ready for tag removal
- [ ] `approval_workflows.feature` - ready for tag removal
- [ ] `budget_and_consumption.feature` - ready for tag removal
- [ ] `project_lifecycle.feature` - ready for tag removal

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
