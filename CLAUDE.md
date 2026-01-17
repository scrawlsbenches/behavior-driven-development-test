<system>prompt

You are Dr. Gherkin, a cheerful and collaborative computer scientist with deep expertise in Behavioral Driven Development using the behave framework. You genuinely enjoy helping teams bridge the gap between business requirements and working software through well-crafted scenarios and living documentation.

Your personality:
- Warm and encouraging - you celebrate when teams write clear, behavior-focused scenarios
- Pragmatic - you favor simplicity over perfection and help teams start small
- Curious - you ask clarifying questions to understand the "why" behind features
- Patient - you guide teams through the Given/When/Then mindset without judgment

Your expertise:
- Graph of Thought framework architecture (core graph, collaborative layer, services)
- Behave framework configuration, hooks, and context management
- Gherkin syntax and scenario design patterns
- The Three Amigos collaboration process
- Test-first development and the Red/Green/Refactor cycle
- Ubiquitous language and domain modeling

How you help:
- Convert vague requirements into concrete, testable scenarios
- Write clean step definitions that follow behave best practices
- Configure behave environments with proper fixtures and hooks
- Identify missing edge cases and acceptance criteria
- Suggest appropriate domain terminology for the Graph of Thought project
- Guide developers from implementation-speak to behavior-speak
- Break down large features into independent, atomic scenarios

Your approach:
- Always start by understanding the user's goal before suggesting scenarios
- Prefer "What behavior should we see?" over "What code should we write?"
- Encourage collaboration: "Let's think about this from the user's perspective..."
- Celebrate progress: "That scenario captures the behavior nicely!"
- Gently redirect anti-patterns: "We could make this more focused by..."

Remember: Good BDD is about shared understanding first, automation second. Help teams have better conversations about what they're building.

</system>prompt

# Claude.md - Behave BDD Guide for Graph of Thought

This document establishes BDD practices using the **behave** framework for the Graph of Thought project. Follow these guidelines when developing features, writing stories, and collaborating on this codebase.

## Project Overview

Graph of Thought is a reasoning framework with two layers:
- **Core Graph** (`graph.py`): Graph-based reasoning with pluggable search strategies
- **Collaborative** (`collaborative.py`): Human-AI project management with governance

## Running Tests

```bash
# Run all implemented scenarios (default - skips @wip)
behave

# Run specific feature file
behave features/search.feature

# Run scenarios by tag
behave --tags=@core
behave --tags=@search --tags=~@slow

# Run @wip scenarios (edge cases under development)
behave --tags=@wip

# Run ALL scenarios including @wip
behave --tags=""

# Run with verbose output
behave --verbose

# Dry run (validate steps without executing)
behave --dry-run
```

## Project Structure

```
features/
├── environment.py              # Hooks and shared fixtures
├── basic_operations.feature    # Graph CRUD operations
├── cycle_detection.feature     # DAG enforcement
├── traversal.feature           # BFS, DFS, path finding
├── search.feature              # Beam search, best-first
├── expansion.feature           # Thought expansion
├── merge_and_prune.feature     # Thought consolidation
├── serialization.feature       # JSON persistence
├── configuration.feature       # Config management
├── persistence.feature         # Storage backends
├── metrics.feature             # Observability
├── search_strategies.feature   # MCTS, etc.
├── resource_limits.feature     # Budget enforcement
├── visualization.feature       # Graph display
├── collaborative.feature       # Human-AI collaboration
├── services.feature            # Service implementations (governance, resources, knowledge)
├── orchestrator.feature        # Service orchestration and events
├── llm.feature                 # LLM integration (generators, evaluators, verifiers)
├── observability.feature       # Logging, metrics, tracing utilities
└── steps/
    ├── graph_steps.py          # Core graph operations
    ├── config_steps.py         # Configuration steps
    ├── persistence_steps.py    # Storage steps
    ├── metrics_steps.py        # Metrics steps
    ├── services_steps.py       # Service implementation steps
    ├── orchestrator_steps.py   # Orchestrator steps
    ├── llm_steps.py            # LLM integration steps
    └── observability_steps.py  # Observability steps

behave.ini                      # Behave configuration (skips @wip by default)
```

## Test Coverage Summary

| Category | Feature Files | Implemented | @wip (Edge Cases) |
|----------|--------------|-------------|-------------------|
| Core Graph | 8 | 56 | 0 |
| Services | 4 | 80 | 64 |
| **Total** | **18** | **135** | **64** |

## Escape Clauses and Development Workflow

Feature files document both implemented behavior AND known limitations via **escape clauses**. This enables development-driven planning.

### Escape Clause Format

```gherkin
# ===========================================================================
# Simple Resource Service
# ===========================================================================
# ESCAPE CLAUSE: Budgets reset on restart.
# Current: All budget state is in-memory.
# Requires: Database persistence (PostgreSQL/Redis) for budget state.
# Depends: None

Scenario: Simple resource service tracks budgets
  ...implemented scenarios...

# --- Resource Edge Cases (TODO: Implement) ---

# ESCAPE CLAUSE: Date filtering not implemented in consumption reports.
# Current: Returns all consumption events regardless of date.
# Requires: Parse timestamps, filter by start_date/end_date parameters.
# Depends: None
@wip
Scenario: Resource service filters consumption report by date range
  ...desired behavior when implemented...
```

### Format Fields

| Field | Purpose |
|-------|---------|
| **ESCAPE CLAUSE** | What's simplified or missing |
| **Current** | How it behaves now |
| **Requires** | What's needed to implement properly |
| **Depends** | Other escape clauses that must be resolved first |

### Development Workflow

1. **Pick a @wip scenario** to implement
2. **Read the escape clause** to understand scope and dependencies
3. **Check "Depends"** for prerequisites
4. **Implement** until the scenario passes
5. **Remove the @wip tag** when complete

### Escape Clause Locations

- **Feature-level**: Architectural limitations affecting the whole module
- **Section-level**: Specific functionality that's stubbed
- **Scenario-level**: Edge cases marked with @wip

Escape clauses remain in Python source files for implementation reference, while feature files serve as the development specification.

## Behave Fundamentals

### Environment Setup (environment.py)

The `environment.py` file configures behave hooks and shared fixtures:

```python
def before_all(context):
    """Set up fixtures available to all scenarios."""
    # Add shared test utilities
    context.simple_evaluator = lambda t: sum(...)
    context.simple_generator = lambda t: [...]
    context.create_test_graph = lambda: GraphOfThought(...)

def before_scenario(context, scenario):
    """Reset context before each scenario."""
    context.graph = None
    context.thoughts = {}
    context.result = None
    context.exception = None
```

### Context Object

Behave's `context` object passes state between steps. Use it to store:
- Test fixtures and helpers (set in `before_all`)
- Scenario-specific state (set in steps, reset in `before_scenario`)

**Important**: Avoid reserved names like `config`, `table`, `text` which behave uses internally. Use prefixed names like `graph_config` instead.

### Step Definitions

Use the `parse` matcher for readable parameter extraction:

```python
from behave import given, when, then, use_step_matcher

use_step_matcher("parse")

@given('a thought "{content}" exists')
def step_thought_exists(context, content):
    thought = context.graph.add_thought(content)
    context.thoughts[content] = thought

@given('a thought "{content}" exists with score {score:f}')
def step_thought_with_score(context, content, score):
    thought = context.graph.add_thought(content, score=score)
    context.thoughts[content] = thought

@then("the graph should contain {count:d} thoughts")
def step_check_count(context, count):
    assert len(context.graph) == count
```

### Async Step Definitions

For async operations, use `asyncio.run()`:

```python
@when('I expand the thought "{content}"')
def step_expand(context, content):
    thought = context.thoughts[content]
    context.result = asyncio.run(context.graph.expand(thought.id))

@when("I run beam search")
def step_beam_search(context):
    context.result = asyncio.run(context.graph.beam_search())
```

### Data Tables

Use tables with explicit headers for structured data:

```gherkin
Scenario: Loading configuration
  Given a configuration dictionary with:
    | key          | value |
    | allow_cycles | True  |
    | max_depth    | 15    |
```

```python
@given("a configuration dictionary with:")
def step_config_dict(context):
    context.config_dict = {}
    for row in context.table:
        key = row["key"]
        value = row["value"]
        # Process key/value pairs
```

## BDD Best Practices

### Focus on Behavior, Not Implementation

Describe **what** the system does from the user's perspective, not **how** it does it internally.

**Good**: "When a thought is expanded, child thoughts are generated and scored"
**Bad**: "When expand() is called, it iterates through the generator output and calls evaluate()"

### Use Ubiquitous Language

Use domain terms consistently across code, tests, and documentation:

| Term | Meaning |
|------|---------|
| Thought | A node in the reasoning graph containing content and a score |
| Edge | A directed relationship between thoughts |
| Expansion | Generating child thoughts from a parent |
| Beam | The set of highest-scoring thoughts at a search level |
| Chunk | A 2-4 hour unit of collaborative work |
| Discovery | Knowledge gained during implementation |
| Artifact | A produced file or output |
| Orchestrator | Coordinates services and handles cross-cutting events |
| Governance | Approval workflows, policies, and audit trails |
| Resource Service | Budget management and consumption tracking |
| Knowledge Service | Storage and retrieval of decisions, patterns, learnings |
| Question Service | Human-in-the-loop question routing and tracking |
| Communication Service | Session handoffs and context compression |
| Escape Clause | Documented limitation with implementation guidance |
| @wip | Work-in-progress scenario (skipped by default) |

### Write Tests Before Implementation

1. Write the scenario in Gherkin syntax
2. Run `behave --dry-run` to generate step snippets
3. Implement step definitions that fail
4. Write the minimum code to make them pass
5. Refactor while keeping tests green

### Keep Scenarios Independent

Each scenario should:
- Set up its own preconditions (use Background for common setup)
- Not depend on other scenarios' side effects
- Clean up after itself if needed (use `after_scenario` hook)

## Scenario Writing

### User Story Format

```
Feature: [Feature name]
  As a [role]
  I want [feature]
  So that [benefit]
```

### Scenario Format

```gherkin
Scenario: [Descriptive name of the behavior]
  Given [precondition/context]
  And [additional context if needed]
  When [action/trigger]
  And [additional action if needed]
  Then [expected outcome]
  And [additional outcome if needed]
```

### Use Background for Common Setup

```gherkin
Feature: Thought expansion

  Background:
    Given a test graph with evaluator and generator

  Scenario: Expanding creates children
    Given a thought "Start" exists
    When I expand the thought "Start"
    Then 3 children should be created

  Scenario: Pruned thoughts don't expand
    Given a thought "Start" exists
    And the thought "Start" is marked as pruned
    When I expand the thought "Start"
    Then no children should be created
```

### One Behavior Per Scenario

**Good**: Separate scenarios
```gherkin
Scenario: Search stops when goal is reached
  ...

Scenario: Search stops when max depth is reached
  ...
```

**Bad**: Multiple behaviors combined
```gherkin
Scenario: Search stops appropriately
  Given various stopping conditions
  When search runs
  Then it stops for goals, depth limits, and timeouts
```

## Step Definition Patterns

### Reusable Given Steps

```python
# Parameterized setup
@given('a graph with max depth {depth:d}')
def step_graph_max_depth(context, depth):
    context.graph = GraphOfThought(max_depth=depth)

# Chained setup
@given('a thought "{child}" exists as child of "{parent}"')
def step_child_exists(context, child, parent):
    parent_thought = context.thoughts[parent]
    thought = context.graph.add_thought(child, parent_id=parent_thought.id)
    context.thoughts[child] = thought
```

### Exception Handling

```python
@when('I try to add an edge from "{source}" to "{target}"')
def step_try_add_edge(context, source, target):
    try:
        context.graph.add_edge(
            context.thoughts[source].id,
            context.thoughts[target].id
        )
    except Exception as e:
        context.exception = e

@then("a CycleDetectedError should be raised")
def step_check_cycle_error(context):
    assert isinstance(context.exception, CycleDetectedError)
```

### Flexible Assertions

```python
# Multiple decorators for singular/plural
@then("the graph should contain {count:d} thought")
@then("the graph should contain {count:d} thoughts")
def step_check_count(context, count):
    assert len(context.graph) == count

# String list parsing
@then('the termination reason should be one of "{reasons}"')
def step_check_reasons(context, reasons):
    valid = [r.strip().strip('"') for r in reasons.split(",")]
    assert context.result.termination_reason in valid
```

## Scenario Tagging

```gherkin
@core @search
Scenario: Beam search with custom width
  ...

@collaborative @blocking
Scenario: Blocking question workflow
  ...

@slow @integration
Scenario: Full project lifecycle
  ...

# @wip = Work in progress (skipped by default via behave.ini)
# Used for edge cases documented by escape clauses
@wip
Scenario: Resource service filters consumption report by date range
  ...
```

Run filtered:
```bash
behave --tags=@core
behave --tags=@search --tags=~@slow
behave --tags="@core and not @wip"

# Run @wip scenarios to see what needs implementation
behave --tags=@wip

# Run everything including @wip
behave --tags=""
```

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Incidental Details** | Too much setup noise | Extract to Background or helper steps |
| **Imperative Steps** | UI/implementation details | Use declarative, behavior-focused steps |
| **Coupled Scenarios** | Depend on execution order | Make each scenario self-contained |
| **Giant Scenarios** | Testing multiple behaviors | Split into focused scenarios |
| **Reserved Names** | `context.config` conflicts | Use `context.graph_config` |
| **Missing Headers** | First table row as header | Add explicit header row |

## Feature Checklist

When adding a new feature:

- [ ] User story clearly states role, feature, and benefit
- [ ] Scenarios cover happy path and key edge cases
- [ ] Given/When/Then steps use ubiquitous language
- [ ] Each scenario tests one behavior
- [ ] Step definitions are reusable where appropriate
- [ ] Background extracts common setup
- [ ] Appropriate tags are applied
- [ ] Async operations use `asyncio.run()`
- [ ] Data tables have explicit headers
- [ ] Escape clauses document known limitations
- [ ] Edge cases are captured as @wip scenarios
- [ ] Dependencies between escape clauses are noted

## Resources

- [Behave Documentation](https://behave.readthedocs.io/)
- [Gherkin Reference](https://cucumber.io/docs/gherkin/reference/)
- [BDD Best Practices](https://cucumber.io/docs/bdd/)
- [Example Mapping](https://cucumber.io/blog/bdd/example-mapping-introduction/)
