# DDD Refactoring Plan

## Overview

This document outlines the plan to refactor the Graph of Thought codebase to use a Domain-Driven Design (DDD) organizational structure.

## Current State

Domain models are scattered across multiple locations:
- `core/types.py` - Reasoning models (Thought, Edge, SearchResult)
- `services/protocols.py` - Service-related models (Decision, QuestionTicket, HandoffPackage)
- `features/steps/*.py` - Duplicate models defined in test files

Key issues:
- 27,505 line `implementations.py` file
- Duplicate domain models causing enum comparison issues
- No clear ownership of domain concepts

## Target Structure

```
graph_of_thought/
├── domain/                          # All domain models
│   ├── __init__.py                  # Re-exports everything
│   ├── models/
│   │   ├── __init__.py
│   │   ├── reasoning.py             # Thought, Edge, SearchResult, SearchContext
│   │   ├── governance.py            # ApprovalRequest, Policy
│   │   ├── knowledge.py             # Decision, KnowledgeEntry, Question, RoutingRule
│   │   ├── project.py               # Project, WorkChunk, SessionHandoff, HandoffPackage
│   │   ├── cost.py                  # Budget, ConsumptionRecord, AllocationRecord
│   │   └── shared.py                # User, ResourceBudget
│   └── enums/
│       ├── __init__.py
│       ├── reasoning.py             # ThoughtStatus
│       ├── governance.py            # ApprovalStatus, ApprovalType, RequestStatus
│       ├── knowledge.py             # QuestionPriority, QuestionStatus
│       ├── project.py               # ProjectStatus, ChunkStatus
│       ├── cost.py                  # BudgetLevel, BudgetStatus
│       └── shared.py                # Priority, ResourceType
│
├── core/                            # Infrastructure (keep existing)
│   ├── protocols.py                 # Technical protocols (imports from domain)
│   ├── exceptions.py
│   └── config.py
│
├── services/                        # Refactored services
│   ├── __init__.py
│   ├── protocols.py                 # Service protocols (imports from domain)
│   ├── implementations/             # Split from single 27K file
│   │   ├── __init__.py
│   │   ├── governance.py
│   │   ├── knowledge.py
│   │   ├── project.py
│   │   ├── resources.py
│   │   └── communication.py
│   └── orchestrator.py
```

## Migration Steps

### Step 1: Create domain/ directory structure
- [x] Create `domain/` directory
- [x] Create `domain/models/` subdirectory
- [x] Create `domain/enums/` subdirectory
- [x] Create `__init__.py` files

### Step 2: Extract and consolidate enums
- [x] Move `ThoughtStatus` from `core/types.py`
- [x] Move `ApprovalStatus`, `Priority`, `ResourceType` from `services/protocols.py`
- [x] Consolidate duplicate enums from step files
- [x] Create re-exports in `domain/enums/__init__.py`

### Step 3: Extract and consolidate models
- [x] Move `Thought`, `Edge`, `SearchResult`, `SearchContext` from `core/types.py`
- [x] Move `Decision`, `KnowledgeEntry`, `QuestionTicket`, `HandoffPackage`, `ResourceBudget` from `services/protocols.py`
- [x] Consolidate `User`, `WorkChunk`, `Budget`, etc. from step files (kept BDD-specific models, shared enums)
- [x] Create re-exports in `domain/models/__init__.py`

### Step 4: Update core/ imports
- [x] Update `core/types.py` to import from domain (re-exports for backwards compatibility)
- [x] `core/protocols.py` unchanged (no domain model dependencies)

### Step 5: Update services/ imports
- [x] Update `services/protocols.py` to import models from domain
- [x] Keep service protocols in `services/protocols.py`

### Step 6: Split implementations.py
- [x] Create `services/implementations/` directory
- [x] Extract governance implementations
- [x] Extract knowledge implementations
- [x] Extract project implementations
- [x] Extract resource implementations
- [x] Extract communication implementations
- [x] Update `services/implementations/__init__.py` with re-exports

### Step 7: Update step files
- [x] Update `knowledge_management_steps.py` to import enums from domain
- [x] Update `project_management_steps.py` to import ChunkStatus from domain
- [x] `cost_management_steps.py` - kept local enums (different meanings)
- [x] `governance_steps.py` - kept local enums (different values)

### Step 8: Update architecture tests
- [x] Add tests for domain model locations (test_domain_models.py, test_domain_enums.py)
- [x] Update `check_architecture.py` script
- [x] Verify all tests pass

### Step 9: Remove premature backwards compatibility
- [x] Remove re-exports from `core/types.py` (keep only TypeVar T)
- [x] Remove re-exports from `services/protocols.py` __all__
- [x] Update step files to import from `graph_of_thought.domain`
- [x] Simplify `test_backwards_compatibility.py`

## Import Hierarchy

After refactoring, the import hierarchy is:

```
domain/           ← No dependencies on other modules (leaf)
    ↑
core/             ← TypeVar only, no domain imports
    ↑
services/         ← Imports domain for type hints in protocols
    ↑
features/steps/   ← Imports domain + services (for tests)
```

## Single Source of Truth

All domain models and enums are imported from `graph_of_thought.domain`.

**Removed:** Re-exports from `core/types.py` and `services/protocols.py` were removed
because the codebase had no external users requiring backwards compatibility.

## Test Baseline (Pre-Refactor)

- pytest: 11 passed
- behave (stable): 209 scenarios passed
- behave (WIP MVP-P0): 59 scenarios passed

## Notes

- Run tests after each step to catch issues early
- Commit after each major step for easy rollback
- The enum comparison issue we fixed earlier was caused by duplicate enum definitions - this refactor will prevent similar issues
