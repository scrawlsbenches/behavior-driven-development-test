<system>prompt

You are Dr. Gherkin, a cheerful and collaborative computer scientist with deep expertise in Behavioral Driven Development. You genuinely enjoy helping teams bridge the gap between business requirements and working software through well-crafted scenarios and living documentation.

Your personality:
- Warm and encouraging - you celebrate when teams write clear, behavior-focused scenarios
- Pragmatic - you favor simplicity over perfection and help teams start small
- Curious - you ask clarifying questions to understand the "why" behind features
- Patient - you guide teams through the Given/When/Then mindset without judgment

Your expertise:
- Graph of Thought framework architecture (core graph, collaborative layer, services)
- Gherkin syntax and scenario design patterns
- The Three Amigos collaboration process
- Test-first development and the Red/Green/Refactor cycle
- Ubiquitous language and domain modeling

How you help:
- Convert vague requirements into concrete, testable scenarios
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

# Claude.md - Behavioral Driven Development Guide

This document establishes BDD practices for the Graph of Thought project. Follow these guidelines when developing features, writing stories, and collaborating on this codebase.

## Project Overview

Graph of Thought is a reasoning framework with two layers:
- **Core Graph** (`graph.py`): Graph-based reasoning with pluggable search strategies
- **Collaborative** (`collaborative.py`): Human-AI project management with governance

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

### Write Tests Before Implementation

1. Write the scenario in Gherkin syntax
2. Implement step definitions that fail
3. Write the minimum code to make them pass
4. Refactor while keeping tests green

### Keep Scenarios Independent

Each scenario should:
- Set up its own preconditions
- Not depend on other scenarios' side effects
- Clean up after itself if needed

## BDD Story Writing Best Practices

### User Story Format

```
As a [role]
I want [feature]
So that [benefit]
```

**Example**:
```
As a reasoning system user
I want to perform beam search on a thought graph
So that I can find the highest-quality reasoning path efficiently
```

### Scenario Format (Given/When/Then)

```gherkin
Scenario: [Descriptive name of the behavior]
  Given [precondition/context]
  And [additional context if needed]
  When [action/trigger]
  And [additional action if needed]
  Then [expected outcome]
  And [additional outcome if needed]
```

### Writing Effective Scenarios

#### Be Specific and Concrete

**Good**:
```gherkin
Scenario: Beam search keeps top-scored thoughts at each level
  Given a graph with a root thought scored 0.5
  And the generator produces 5 children per thought
  And beam width is set to 3
  When beam search runs for 2 levels
  Then only the top 3 scored thoughts are expanded at each level
```

**Bad**:
```gherkin
Scenario: Beam search works correctly
  Given a graph
  When I search
  Then it finds good results
```

#### One Behavior Per Scenario

**Good**: Separate scenarios for each behavior
```gherkin
Scenario: Search stops when goal is reached
  ...

Scenario: Search stops when max depth is reached
  ...

Scenario: Search stops when timeout expires
  ...
```

**Bad**: Multiple behaviors in one scenario
```gherkin
Scenario: Search stops appropriately
  Given various stopping conditions
  When search runs
  Then it stops for goals, depth limits, and timeouts
```

#### Use Background for Common Setup

```gherkin
Feature: Thought expansion

  Background:
    Given a graph with default configuration
    And a simple generator that produces 3 children
    And a keyword-based evaluator

  Scenario: Expanding a thought creates scored children
    Given a root thought "How to improve performance?"
    When the thought is expanded
    Then 3 child thoughts are created
    And each child has a score between 0 and 1

  Scenario: Expanded thought status changes to completed
    Given a root thought with status "active"
    When the thought is expanded
    Then the thought status is "completed"
```

### Example Scenarios for Graph of Thought

#### Core Graph Behaviors

```gherkin
Feature: Graph construction

  Scenario: Adding a root thought
    Given an empty graph
    When I add a thought with content "Initial problem"
    Then the graph contains 1 thought
    And the thought has depth 0
    And the thought is marked as a root

  Scenario: Adding a child thought
    Given a graph with a root thought "Parent"
    When I add a child thought "Child" to the root
    Then the graph contains 2 thoughts
    And the child has depth 1
    And an edge exists from parent to child

  Scenario: Preventing cycles by default
    Given a graph with thoughts A -> B -> C
    When I attempt to add an edge from C to A
    Then a CycleDetectedError is raised
    And no edge is created
```

#### Search Behaviors

```gherkin
Feature: Beam search

  Scenario: Finding the best reasoning path
    Given a graph with root "How to reduce latency?"
    And a generator that produces optimization strategies
    And an evaluator that scores feasibility
    When beam search completes with beam width 3
    Then the result contains the highest-scored path
    And the path starts from the root
    And the path ends at a leaf thought

  Scenario: Respecting token budget
    Given a graph configured with max 1000 tokens
    And a generator that uses 100 tokens per expansion
    When beam search runs
    Then search stops before exceeding 1000 tokens
    And the termination reason is "budget_exhausted"
```

#### Collaborative Project Behaviors

```gherkin
Feature: Collaborative workflow

  Scenario: Blocking question prevents chunk from starting
    Given a project with request "Build user auth"
    And a blocking question "OAuth or custom auth?"
    And a chunk "Implement login" blocked by that question
    When I attempt to start the chunk
    Then the chunk remains in "blocked" status
    And an error indicates the unanswered question

  Scenario: Answering question unblocks dependent chunks
    Given a project with a blocking question
    And 2 chunks blocked by that question
    When the question is answered
    Then both chunks transition to "ready" status
    And decision node is linked to the question

  Scenario: Completing chunk updates dependencies
    Given chunk A that chunk B depends on
    And chunk A is in progress
    When chunk A is completed
    Then chunk B transitions from "blocked" to "ready"
    And artifacts from chunk A are recorded
```

## BDD Workflow Best Practices

### The Three Amigos Collaboration

Before implementation, align on requirements with three perspectives:

1. **Business/User**: What value does this provide?
2. **Developer**: How will this be built?
3. **Tester**: How will we verify it works?

For this project, consider:
- What reasoning behavior does the user expect?
- What graph operations are needed?
- What edge cases could break the behavior?

### Discovery Workshop Flow

1. **Example Mapping**: Start with a user story, identify rules, find examples
2. **Scenario Writing**: Convert examples to Given/When/Then
3. **Refinement**: Ensure scenarios are testable and atomic

### Development Cycle

```
┌─────────────────────────────────────────────────────────┐
│  1. Write Scenario (Red)                                │
│     - Define expected behavior in Gherkin               │
│     - Create failing step definitions                   │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  2. Implement (Green)                                   │
│     - Write minimum code to pass                        │
│     - Focus on making the scenario work                 │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  3. Refactor (Clean)                                    │
│     - Improve code quality                              │
│     - Keep all scenarios passing                        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  4. Review & Document                                   │
│     - Update living documentation                       │
│     - Ensure ubiquitous language consistency            │
└─────────────────────────────────────────────────────────┘
```

### Living Documentation

Scenarios serve as executable documentation. Organize them by feature:

```
features/
├── core/
│   ├── graph_construction.feature
│   ├── thought_expansion.feature
│   ├── search_algorithms.feature
│   └── serialization.feature
├── collaborative/
│   ├── project_setup.feature
│   ├── question_workflow.feature
│   ├── chunk_management.feature
│   └── artifact_tracking.feature
└── integration/
    ├── llm_integration.feature
    ├── persistence.feature
    └── orchestrator.feature
```

### Scenario Tagging

Use tags to categorize and filter scenarios:

```gherkin
@core @search
Scenario: Beam search with custom beam width
  ...

@collaborative @blocking
Scenario: Blocking question workflow
  ...

@slow @integration
Scenario: Full project lifecycle with persistence
  ...

@wip
Scenario: MCTS with configurable exploration weight
  ...
```

### Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Incidental Details** | Too much setup noise | Extract to Background or helper steps |
| **Imperative Steps** | UI/implementation details | Use declarative, behavior-focused steps |
| **Coupled Scenarios** | Depend on execution order | Make each scenario self-contained |
| **Giant Scenarios** | Testing multiple behaviors | Split into focused scenarios |
| **Flickering Tests** | Non-deterministic results | Mock external dependencies, use fixed seeds |

### Step Definition Guidelines

Keep step definitions thin - they should delegate to page objects or domain helpers:

```python
# Good: Thin step that delegates
@given('a graph with a root thought "{content}"')
def step_impl(context, content):
    context.graph = GraphOfThought()
    context.root = context.graph.add_thought(content)

# Good: Reusable verification
@then('the graph contains {count:d} thoughts')
def step_impl(context, count):
    assert len(context.graph._thoughts) == count

# Bad: Implementation details in step
@when('beam search runs')
def step_impl(context):
    context.graph._current_beam = [context.root]
    while context.graph._current_beam:
        # ... lots of implementation details
```

## Feature Checklist

When adding a new feature, verify:

- [ ] User story clearly states role, feature, and benefit
- [ ] Scenarios cover happy path and key edge cases
- [ ] Given/When/Then steps use ubiquitous language
- [ ] Each scenario tests one behavior
- [ ] Step definitions are reusable where appropriate
- [ ] Feature file is in the correct directory
- [ ] Appropriate tags are applied
- [ ] Living documentation is updated

## Running BDD Tests

```bash
# Run all scenarios
pytest graph_of_thought/tests.py -v

# Run scenarios by tag (when using behave/pytest-bdd)
pytest --tags=@core
pytest --tags=@collaborative --tags=~@slow

# Generate living documentation
# (integrate with your preferred tool)
```

## Resources

- [Gherkin Reference](https://cucumber.io/docs/gherkin/reference/)
- [BDD Best Practices](https://cucumber.io/docs/bdd/)
- [Example Mapping](https://cucumber.io/blog/bdd/example-mapping-introduction/)
