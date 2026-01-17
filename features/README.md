# Graph of Thought - Enterprise Feature Specifications

This directory contains business-focused BDD specifications for the Graph of Thought enterprise application. Features are organized by business capability rather than technical service.

## Directory Structure

```
features/
├── PERSONAS.md                    # Enterprise persona definitions
├── README.md                      # This file
├── environment.py                 # Behave hooks and fixtures
│
├── ai_reasoning/                  # Core AI exploration capabilities
│   ├── thought_exploration.feature   # Graph-based reasoning (@mvp-p0)
│   ├── intelligent_search.feature    # Automated solution search (@mvp-p0)
│   └── llm_integration.feature       # LLM-powered generation (@mvp-p0)
│
├── project_management/            # Project and work tracking
│   └── project_lifecycle.feature     # Projects, chunks, handoffs (@mvp-p0)
│
├── cost_management/               # Budget and resource control
│   └── budget_and_consumption.feature # Token budgets, tracking (@mvp-p0)
│
├── governance_compliance/         # Approvals and audit
│   └── approval_workflows.feature    # Policies, approvals, audit (@mvp-p0)
│
├── knowledge_management/          # Organizational learning
│   ├── decisions_and_learnings.feature # Decision records (@mvp-p0)
│   └── question_routing.feature      # Question management (@mvp-p0)
│
├── platform/                      # Infrastructure concerns
│   ├── observability.feature         # Logging, metrics, tracing (@mvp-p1)
│   └── data_persistence.feature      # Storage, backup, recovery (@mvp-p0)
│
└── steps/                         # Step definitions (11 files, 4,055 lines)
    └── *.py
```

## MVP Priority Tags

| Tag | Meaning | Development Priority |
|-----|---------|---------------------|
| `@mvp-p0` | Must have for launch | Sprint 1-2 |
| `@mvp-p1` | Should have for launch | Sprint 3-4 |
| `@mvp-p2` | Nice to have for launch | Sprint 5+ |
| `@post-mvp` | Future enhancement | Backlog |
| `@wip` | Work in progress | Under development |

## Running Tests

```bash
# Run MVP-P0 critical features only
behave --tags=@mvp-p0

# Run all MVP features
behave --tags="@mvp-p0 or @mvp-p1 or @mvp-p2"

# Run specific business capability
behave features/ai_reasoning/
behave features/governance_compliance/

# Run features for a specific persona
behave --tags=@cost-management    # For Finance Administrator
behave --tags=@governance         # For Security Officer
behave --tags=@knowledge-management # For Knowledge Manager

# Run everything including WIP
behave --tags=""

# Dry run to validate step definitions
behave --dry-run
```

## Persona Reference

All feature files use consistent personas defined in `PERSONAS.md`:

| Persona | Role | Primary Features |
|---------|------|------------------|
| Alex | Engineering Manager | Project management, team visibility |
| Jordan | Data Scientist | AI reasoning, exploration |
| Morgan | Security Officer | Governance, compliance |
| Sam | Product Owner | Questions, decisions |
| Casey | DevOps Engineer | Observability, persistence |
| Drew | Finance Administrator | Budgets, cost management |
| Taylor | Junior Developer | Knowledge discovery |
| Riley | Compliance Auditor | Audit, reporting |
| Avery | Knowledge Manager | Knowledge curation |

## Feature File Conventions

### Structure
```gherkin
@category-tag @priority-tag
Feature: Business Capability Name
  As a [Persona]
  I want [capability]
  So that [business value]

  # ===========================================================================
  # Section Header
  # ===========================================================================
  # Business Rule: Explains the business logic being tested

  @mvp-p0 @critical
  Scenario: Clear behavior description
    Given [context]
    When [action]
    Then [outcome]
```

### Priority Guidelines

**@mvp-p0 (Must Have)**
- Core value proposition
- Would block all usage if missing
- Security/compliance requirements

**@mvp-p1 (Should Have)**
- Significant user value
- Key differentiators
- Important error handling

**@mvp-p2 (Nice to Have)**
- Enhanced experience
- Optimization features
- Advanced analytics

**@post-mvp (Future)**
- Advanced integrations
- Edge case handling
- Performance optimizations

## Legacy Features

The original 25 technical feature files remain in the `features/` root directory:
- `basic_operations.feature`, `governance.feature`, `search.feature`, etc.

**Status**: These legacy files use the generic "developer" persona and technical focus. The new enterprise-focused features in subdirectories provide business-aligned alternatives. Legacy files are maintained for backward compatibility with existing step definitions but are considered deprecated in favor of the new structure.

## Contributing

When adding new scenarios:

1. Identify the appropriate persona from `PERSONAS.md`
2. Write from the user's perspective, not implementation
3. Include business context and value
4. Add appropriate priority tags
5. Document business rules as comments
6. Keep scenarios focused on single behaviors
