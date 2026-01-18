<system>

You are Dr. Gherkin, a cheerful and collaborative computer scientist with deep expertise in Behavioral Driven Development using the behave framework. You genuinely enjoy helping teams bridge the gap between business requirements and working software through well-crafted scenarios and living documentation.

Your personality:
- Warm and encouraging - you celebrate when teams write clear, behavior-focused scenarios
- Pragmatic - you favor simplicity over perfection and help teams start small
- Curious - you ask clarifying questions to understand the "why" behind features
- Patient - you guide teams through the Given/When/Then mindset without judgment

Your expertise:
- Enterprise application architecture and business capability modeling
- Behave framework configuration, hooks, and context management
- Gherkin syntax and scenario design patterns
- The Three Amigos collaboration process
- Test-first development and the Red/Green/Refactor cycle
- Ubiquitous language and domain modeling
- MVP prioritization and sprint planning

How you help:
- Convert vague requirements into concrete, testable scenarios
- Write clean step definitions that follow behave best practices
- Configure behave environments with proper fixtures and hooks
- Identify missing edge cases and acceptance criteria
- Suggest appropriate domain terminology using established personas
- Guide developers from implementation-speak to behavior-speak
- Break down large features into independent, atomic scenarios
- Prioritize scenarios for MVP delivery

Your approach:
- Always start by understanding the user's goal before suggesting scenarios
- Prefer "What behavior should we see?" over "What code should we write?"
- Encourage collaboration: "Let's think about this from the user's perspective..."
- Celebrate progress: "That scenario captures the behavior nicely!"
- Gently redirect anti-patterns: "We could make this more focused by..."
- Ask "Which persona benefits from this?" to ensure business alignment

Remember: Good BDD is about shared understanding first, automation second. Help teams have better conversations about what they're building.

IMPORTANT - Environment Setup:
Before running ANY tests or commands, run: ./scripts/setup-dev.sh (installs dependencies and configures git hooks).

</system>

# CLAUDE.md - Behave BDD Guide for Graph of Thought

This document establishes BDD practices using the **behave** framework for the Graph of Thought enterprise application. Follow these guidelines when developing features, writing stories, and collaborating on this codebase.

## Environment Setup

**Requirements:** Python 3.9 or higher

```bash
# Install dependencies and configure git hooks
pip install -e ".[dev]"
git config core.hooksPath scripts/hooks

# Verify installation
behave --dry-run                 # Should list scenarios without errors
python -m pytest tests/ -q       # Should show passing architecture tests
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `behave: command not found` | Run `pip install -e ".[dev]"` |
| `ModuleNotFoundError: graph_of_thought` | Run `pip install -e ".[dev]"` to install in editable mode |
| Tests fail with import errors | Ensure you're in the project root directory |

## Session Startup Checklist

Run these commands at the start of every session to ensure correct state:

```bash
# 1. Required setup (installs deps, configures git hooks)
./scripts/setup-dev.sh

# 2. Check git state
git status

# 3. Read current status
cat docs/WIP.md

# 4. Verify actual test counts
behave --dry-run 2>&1 | tail -5

# 5. Compare WIP.md vs actual (detect drift)
#    If counts don't match, WIP.md needs updating
```

**Why this matters:** Documentation can drift from actual state between sessions. Always verify before assuming WIP.md is accurate.

## Project Overview

Graph of Thought is an enterprise AI-assisted reasoning and project management platform with six core business capabilities:

| Capability | Description | Primary Personas |
|------------|-------------|------------------|
| **AI Reasoning** | Graph-based thought exploration and intelligent search | Data Scientist, Engineering Manager |
| **Project Management** | Work chunks, session handoffs, team collaboration | Engineering Manager, Product Owner |
| **Cost Management** | Token budgets, consumption tracking, forecasting | Finance Administrator, Engineering Manager |
| **Governance & Compliance** | Approval workflows, policies, audit logging | Security Officer, Compliance Auditor |
| **Knowledge Management** | Decisions, learnings, question routing | Knowledge Manager, Junior Developer |
| **Platform** | Observability, persistence, configuration | DevOps Engineer |

## Running Tests

```bash
# Run all MVP scenarios (excludes @wip and @post-mvp)
behave

# Run by MVP priority
behave --tags=@mvp-p0              # Must have for launch
behave --tags="@mvp-p0 or @mvp-p1" # Should have for launch
behave --tags="@mvp-p0 or @mvp-p1 or @mvp-p2"  # All MVP features

# Run by business capability
behave features/ai_reasoning/
behave features/governance_compliance/
behave features/cost_management/

# Run by category tag
behave --tags=@governance
behave --tags=@knowledge-management
behave --tags=@platform

# Run WIP and future scenarios
behave --tags=@wip                 # Work in progress
behave --tags=@post-mvp            # Future enhancements
behave --tags=""                   # Everything

# Validation
behave --dry-run                   # Validate step definitions
behave --verbose                   # Detailed output
```

## Project Structure

```
features/
├── PERSONAS.md                         # Enterprise persona definitions
├── README.md                           # Feature organization guide
├── environment.py                      # Hooks and shared fixtures
│
├── ai_reasoning/                       # Core AI exploration
│   ├── thought_exploration.feature     # Graph-based reasoning (@mvp-p0)
│   ├── intelligent_search.feature      # Automated search strategies (@mvp-p0)
│   └── llm_integration.feature         # LLM generation/evaluation (@mvp-p0)
│
├── project_management/                 # Project and work tracking
│   └── project_lifecycle.feature       # Projects, chunks, handoffs (@mvp-p0)
│
├── cost_management/                    # Budget and resources
│   └── budget_and_consumption.feature  # Token budgets, tracking (@mvp-p0)
│
├── governance_compliance/              # Approvals and audit
│   └── approval_workflows.feature      # Policies, approvals, RBAC (@mvp-p0)
│
├── knowledge_management/               # Organizational learning
│   ├── decisions_and_learnings.feature # Decision records (@mvp-p0)
│   └── question_routing.feature        # Question management (@mvp-p0)
│
├── platform/                           # Infrastructure
│   ├── observability.feature           # Logging, metrics, tracing (@mvp-p1)
│   └── data_persistence.feature        # Storage, backup, recovery (@mvp-p0)
│
├── steps/                              # Step definitions
│   └── *.py
│
└── *.feature                           # Foundation API tests (library-level)

behave.ini                              # Behave configuration
```

## MVP Priority System

| Tag | Meaning | Sprint Target | Criteria |
|-----|---------|---------------|----------|
| `@mvp-p0` | Must have | Sprint 1-2 | Core value proposition, blocks usage |
| `@mvp-p1` | Should have | Sprint 3-4 | Key differentiator, significant value |
| `@mvp-p2` | Nice to have | Sprint 5+ | Improved experience, workarounds exist |
| `@post-mvp` | Future | Backlog | Advanced features, optimizations |
| `@wip` | In progress | Current | Under active development |

### Priority Guidelines

**@mvp-p0 scenarios** answer: "Can users accomplish the core task?"
- Creating and exploring thought graphs
- Tracking token consumption against budgets
- Recording decisions and routing questions
- Basic approval workflows and audit logging
- Saving and loading work reliably

**@mvp-p1 scenarios** answer: "Is the experience good enough for production?"
- Advanced search strategies
- SLA tracking and alerts
- Detailed observability
- Multi-approver workflows

**@mvp-p2 scenarios** answer: "What would delight users?"
- Forecasting and recommendations
- Advanced analytics
- Customizable dashboards

## Enterprise Personas

All feature files use consistent personas. Reference `features/PERSONAS.md` for full details.

| Persona | Role | Primary Concerns |
|---------|------|------------------|
| **Alex** | Engineering Manager | Team velocity, budget adherence, project visibility |
| **Jordan** | Data Scientist | Efficient exploration, token budgets, experiment tracking |
| **Morgan** | Security Officer | Compliance, audit trails, policy enforcement |
| **Sam** | Product Owner | Quick answers, documented decisions, scope clarity |
| **Casey** | DevOps Engineer | System health, deployment safety, issue diagnosis |
| **Drew** | Finance Administrator | Budget allocation, cost attribution, forecasting |
| **Taylor** | Junior Developer | Learning from past decisions, finding expertise |
| **Riley** | Compliance Auditor | Complete audit trails, compliance reports |
| **Avery** | Knowledge Manager | Knowledge curation, gap identification |

### Using Personas in Scenarios

```gherkin
# Good - specific persona with business context
Scenario: Data scientist tracks token usage against sprint budget
  Given Jordan is working on project "Customer Analysis"
  And the sprint budget is 50,000 tokens
  When Jordan's analysis consumes 2,500 tokens
  Then Jordan should see 47,500 tokens remaining
  And the projected daily burn rate should update

# Bad - generic developer without business context
Scenario: Token consumption is tracked
  Given a user and a budget of 50000
  When 2500 tokens are consumed
  Then remaining should be 47500
```

## Ubiquitous Language

Use these terms consistently across code, tests, and documentation:

### Core Concepts
| Term | Meaning |
|------|---------|
| **Thought** | A node in the reasoning graph containing content and a score |
| **Exploration** | A session of graph-based reasoning on a problem |
| **Expansion** | AI-generating follow-up thoughts from a parent thought |
| **Work Chunk** | A 2-4 hour focused work session with clear goals |
| **Handoff** | Context package for resuming work across sessions |

### Business Concepts
| Term | Meaning |
|------|---------|
| **Decision Record** | Documented decision with context, rationale, and consequences |
| **Learning** | Insight gained from work that benefits future projects |
| **Blocking Question** | Question that stops work until answered |
| **Approval Workflow** | Process requiring sign-off before action proceeds |
| **Token Budget** | Allocated AI usage limit for a project or team |

### Technical Concepts
| Term | Meaning |
|------|---------|
| **Beam Search** | Exploring top-K promising thoughts at each level |
| **Governance Policy** | Rule defining what actions require approval |
| **Audit Trail** | Immutable log of significant actions for compliance |
| **SLA** | Service level agreement for response times |

## Scenario Writing

### Business-Focused User Stories

```gherkin
@governance @mvp-p0
Feature: Production Change Approval Workflows
  As a Security Officer
  I want all production changes to require documented approval
  So that we maintain SOC2 compliance and demonstrate due diligence

  As an Engineering Manager
  I want visibility into pending approvals
  So that deployments aren't blocked by unknown bottlenecks
```

### Document Business Rules

```gherkin
# ===========================================================================
# Budget Warnings and Limits - MVP-P0
# ===========================================================================
# Business Rule: Users receive warnings at 80% consumption.
# Hard limits prevent work from continuing without approval.

@mvp-p0 @critical
Scenario: Warning when approaching budget threshold
  Given project "Analysis" with 100,000 token budget
  And 80% consumption warning threshold
  When consumption reaches 80,000 tokens
  Then Jordan should see a budget warning
  And the Engineering Manager should be notified
  And work should be allowed to continue
```

### Use Realistic Test Data

```gherkin
# Good - realistic business context
Scenario: Data science team tracks daily usage against sprint budget
  Given the "Q1 Customer Analysis" project
  And sprint budget of 50,000 tokens from Jan 15 to Jan 29
  When data scientist runs an experiment consuming 2,500 tokens
  Then the dashboard should show 47,500 tokens remaining

# Bad - abstract test data
Scenario: Track consumption
  Given project "test" with budget 50000
  When 2500 consumed
  Then remaining is 47500
```

## Behave Configuration

### environment.py Hooks

```python
def before_all(context):
    """Set up fixtures available to all scenarios."""
    context.simple_evaluator = lambda t: ...
    context.simple_generator = lambda t: ...
    context.create_test_graph = lambda: GraphOfThought(...)

def before_scenario(context, scenario):
    """Reset context before each scenario."""
    context.graph = None
    context.project = None
    context.user = None
    context.result = None
    context.exception = None
```

### Testing Infrastructure

**Data Persistence Testing:** Use an in-memory filesystem for persistence tests. This allows:
- Full control over file operations (create, read, write, delete)
- Verification of exact actions performed during save/load
- Simulation of failure scenarios (disk full, permissions, corruption)
- Fast tests without actual disk I/O
- Deterministic behavior across test runs

```python
# Example: In-memory filesystem for persistence testing
from io import StringIO, BytesIO

class InMemoryFileSystem:
    """Mock filesystem for testing persistence operations."""

    def __init__(self):
        self.files: Dict[str, bytes] = {}
        self.operations: List[str] = []  # Track all operations for assertions

    def write(self, path: str, content: bytes) -> None:
        self.files[path] = content
        self.operations.append(f"write:{path}")

    def read(self, path: str) -> bytes:
        self.operations.append(f"read:{path}")
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def exists(self, path: str) -> bool:
        return path in self.files

    def assert_written(self, path: str) -> None:
        """Assert a specific file was written."""
        assert f"write:{path}" in self.operations
```

### Step Definition Patterns

```python
from behave import given, when, then, use_step_matcher

use_step_matcher("parse")

# Persona-aware steps
@given('{persona} is working on project "{project}"')
def step_persona_working(context, persona, project):
    context.user = get_persona(persona)
    context.project = get_or_create_project(project)

# Business-focused assertions
@then('{persona} should see a budget warning')
def step_budget_warning(context, persona):
    assert context.user.has_notification("budget_warning")
    assert context.project.budget_status == "warning"
```

## Scenario Tags

### Category Tags
```gherkin
@ai-reasoning          # AI exploration features
@project-management    # Project and work tracking
@cost-management       # Budget and resources
@governance            # Approvals and compliance
@knowledge-management  # Decisions and questions
@platform              # Infrastructure concerns
```

### Priority Tags
```gherkin
@mvp-p0    # Must have for launch
@mvp-p1    # Should have for launch
@mvp-p2    # Nice to have
@post-mvp  # Future enhancement
@wip       # Work in progress
```

### Quality Tags
```gherkin
@critical  # Business-critical scenario
@security  # Security-related
@slow      # Long-running test
```

## Feature Checklist

When adding a new feature:

- [ ] **Persona identified** - Which persona benefits? Check PERSONAS.md
- [ ] **Business value stated** - "So that..." explains why it matters
- [ ] **MVP priority assigned** - @mvp-p0, @mvp-p1, @mvp-p2, or @post-mvp
- [ ] **Business rules documented** - Comments explain the logic
- [ ] **Realistic test data** - Uses believable names, values, contexts
- [ ] **One behavior per scenario** - Focused, atomic tests
- [ ] **Declarative steps** - Behavior, not implementation
- [ ] **Background extracts common setup** - DRY principle
- [ ] **Edge cases captured** - As @wip or @post-mvp scenarios
- [ ] **Category tag applied** - @governance, @cost-management, etc.

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Generic "developer" persona** | No business context | Use specific personas from PERSONAS.md |
| **Technical user stories** | "I want a service" | Focus on business outcomes |
| **Abstract test data** | "project test", "user123" | Use realistic names and values |
| **Imperative steps** | "Click button, enter text" | Describe behavior declaratively |
| **Testing internal state** | "Service should exist" | Test observable behavior |
| **Missing business rules** | Why does this matter? | Document rules as comments |
| **No priority tag** | What to build first? | Add @mvp-p0/p1/p2 tags |

## Development Workflow

1. **Identify the persona** - Who benefits from this feature?
2. **Write the user story** - As [persona], I want [capability], so that [value]
3. **Document business rules** - What logic governs this behavior?
4. **Write scenarios** - Cover happy path, then edge cases
5. **Assign priority** - @mvp-p0 for core, @mvp-p1/@mvp-p2 for enhancements
6. **Run dry-run** - `behave --dry-run` to generate step snippets
7. **Implement steps** - Write failing step definitions
8. **Implement code** - Make steps pass
9. **Refactor** - Clean up while tests stay green

## Developer Tooling (Non-BDD)

Some quality enforcement doesn't belong in behave features. These tools ensure codebase consistency but aren't user-facing behavior:

### What Goes Where

| Concern | Tool | Why |
|---------|------|-----|
| Business behavior | behave features | User-facing, needs personas |
| Architecture rules | pytest + CI scripts | Developer tooling, no persona |
| Code style | ruff/black | Automated formatting |
| Type safety | mypy | Static analysis |

### Architecture Enforcement

```bash
# Fast CI check - run before tests
python scripts/check_architecture.py

# Detailed pytest checks
pytest tests/test_architecture.py -v
```

**Rules enforced:**
- Protocols must be defined in `protocols.py`
- Implementations must be in `implementations.py`
- No global service instances
- Business logic imports protocols, not implementations
- Services injected via constructor, not instantiated directly

### Why Not BDD for Architecture?

BDD features answer: "What behavior should the user see?"
Architecture tests answer: "Is the code organized correctly?"

There's no persona for "the codebase itself." Architecture enforcement is internal developer tooling - same category as linting and type checking. Mixing it into behave features would dilute the business focus.

**Rule of thumb:** If you can't identify a persona from `PERSONAS.md` who benefits from the behavior, it's probably developer tooling, not a BDD feature.

## Planning Documents

Project planning lives in `docs/`. Update these files as work progresses:

| Document | Update When | What to Update |
|----------|-------------|----------------|
| `ROADMAP.md` | Milestones change | Vision, capabilities, success metrics |
| `SPRINTS.md` | Sprint boundaries | Move items between sprints, update status |
| `NEXT_STEPS.md` | Completing tasks | Remove done items, add newly discovered work |
| `WIP.md` | Daily | Current status, test counts, active work |

**Update frequency:**
- `WIP.md` - Update when starting or finishing work
- `NEXT_STEPS.md` - Update when completing a prioritized item
- `SPRINTS.md` - Update at sprint boundaries or when scope changes
- `ROADMAP.md` - Update when strategic direction shifts

## Resources

- [Behave Documentation](https://behave.readthedocs.io/)
- [Gherkin Reference](https://cucumber.io/docs/gherkin/reference/)
- [BDD Best Practices](https://cucumber.io/docs/bdd/)
- [Example Mapping](https://cucumber.io/blog/bdd/example-mapping-introduction/)
- `features/PERSONAS.md` - Detailed persona profiles
- `features/README.md` - Feature organization guide
- `scripts/check_architecture.py` - Architecture enforcement (CI)
- `tests/test_architecture.py` - Detailed architecture tests
