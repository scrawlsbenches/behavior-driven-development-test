# Cleanup: Remove Premature Backwards Compatibility

## Problem Statement

The codebase has re-exports in multiple locations that create confusion about where to import domain models and enums. This "backwards compatibility" layer was created during the DDD refactoring but serves no purpose - the codebase is 1 day old with no external users.

## Previous State

| Location | Re-exports | Used By |
|----------|------------|---------|
| `graph_of_thought.domain` | All models/enums (source of truth) | Most code |
| `core/types.py` | Thought, Edge, SearchResult, SearchContext, ThoughtStatus | Only backwards compat tests |
| `services/protocols.py` | ApprovalStatus, Priority, ResourceType, Decision, KnowledgeEntry, QuestionTicket, HandoffPackage, ResourceBudget | 2 step files + backwards compat tests |

## Goal

One source of truth: `graph_of_thought.domain`

## Execution Plan

### Step 1: Update step files to import from domain
- [x] `features/steps/orchestrator_steps.py` - change imports
- [x] `features/steps/services_steps.py` - change imports

### Step 2: Remove re-exports from core/types.py
- [x] Remove model/enum imports from domain
- [x] Keep only `T = TypeVar("T")`
- [x] Update `__all__` to only export `T`
- [x] Update module docstring

### Step 3: Remove re-exports from services/protocols.py
- [x] Keep imports (needed for protocol type hints)
- [x] Remove re-exports from `__all__`
- [x] Update module docstring (remove backwards compat note)

### Step 4: Update or remove backwards compatibility tests
- [x] `tests/test_backwards_compatibility.py` - simplified to test enum consistency only

### Step 5: Update documentation
- [x] `docs/DDD_REFACTORING_PLAN.md` - updated backwards compatibility section

### Step 6: Verify
- [x] Run `python scripts/check_architecture.py` - passed
- [x] Run `pytest tests/` - 201 passed
- [x] Run `behave --tags="not @wip and not @post-mvp"` - 209 scenarios passed

## Outcome

After cleanup:
- Domain models/enums: import from `graph_of_thought.domain`
- Service protocols: import from `graph_of_thought.services.protocols`
- Core types (TypeVar T): import from `graph_of_thought.core.types`

No confusion. One source of truth.

---

## Execution Log

**Started:** Completed in single session

**Changes made:**
1. `features/steps/orchestrator_steps.py` - imports now from `graph_of_thought.domain`
2. `features/steps/services_steps.py` - imports now from `graph_of_thought.domain`
3. `graph_of_thought/core/types.py` - reduced to only `T = TypeVar("T")`
4. `graph_of_thought/core/__init__.py` - imports domain types from `graph_of_thought.domain`
5. `graph_of_thought/services/protocols.py` - removed model/enum re-exports from `__all__`
6. `tests/test_backwards_compatibility.py` - simplified to test enum consistency within domain
7. `docs/DDD_REFACTORING_PLAN.md` - added Step 9, updated backwards compatibility section

**Status:** Complete
