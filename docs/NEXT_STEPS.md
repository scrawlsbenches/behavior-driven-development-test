# Next Steps

Prioritized by impact - what gets us furthest, fastest.

## Immediate (Complete Sprint 1-2)

### 1. Implement Data Persistence Step Definitions
**Why first:** Persistence underpins everything. Without reliable save/load, other features can't be trusted in production.

**Files:**
- `features/platform/data_persistence.feature` - 15 scenarios need steps
- `features/steps/persistence_steps.py` - extend existing

**Key scenarios:**
- Save and load exploration state
- Backup and recovery
- Checkpoint creation and rollback

### 2. Implement Knowledge Management Step Definitions
**Why second:** Decision recording and question routing are core to organizational memory.

**Files:**
- `features/knowledge_management/decisions_and_learnings.feature`
- `features/knowledge_management/question_routing.feature`
- `features/steps/knowledge_management_steps.py` - extend existing

**Key scenarios:**
- Record decision with context and rationale
- Route question to appropriate expert
- Search past decisions for similar problems

### 3. Remove @wip Tags from Completed Features
**Why:** Cleanup that validates our progress and makes test runs cleaner.

**Files to update:**
- `features/ai_reasoning/thought_exploration.feature`
- `features/ai_reasoning/intelligent_search.feature`
- `features/ai_reasoning/llm_integration.feature`
- `features/governance_compliance/approval_workflows.feature`
- `features/cost_management/budget_and_consumption.feature`
- `features/project_management/project_lifecycle.feature`

## Next Sprint (MVP-P1)

### 4. Implement Observability
**Why:** Production systems need visibility. Can't operate what you can't see.

**Files:**
- `features/platform/observability.feature`
- `features/steps/observability_steps.py` - extend existing

**Key scenarios:**
- Structured logging with request correlation
- Metrics for token consumption, latency, errors
- Trace propagation across service boundaries

### 5. Mark DDD Refactoring Plan Complete
**Why:** Housekeeping - the tests exist, mark the task done.

**File:** `docs/DDD_REFACTORING_PLAN.md`
- Step 8 tests exist in `tests/test_domain_*.py`

## Validation Commands

```bash
# After each step, verify no regressions
python scripts/check_architecture.py
behave --tags="not @wip and not @post-mvp"

# Check remaining undefined steps
behave --tags=@mvp-p0 --dry-run 2>&1 | grep "undefined"
```
