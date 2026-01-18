# API Improvement Opportunities

Discovered while building `dogfood_demo.py` - a demo that models our development workflow.

## Summary

| Issue | Category | Severity | Suggested Fix |
|-------|----------|----------|---------------|
| Generator/Evaluator receive strings, not Thoughts | Confusing API | Medium | Rename params or provide wrapper |
| SearchConfig ceremony required | Verbose API | Medium | Add convenience `search()` method |
| `record_discovery(found_in=...)` expects node ID | Misleading parameter | Low | Rename or document better |
| Inconsistent naming (`name` vs `title`, `notes` vs `summary`) | Inconsistent API | Medium | Standardize naming conventions |
| `ask_question(blocking=True)` doesn't work | Missing convenience | Low | Add boolean shorthand |
| No simple `search()` method | Missing feature | Medium | Add `search()` with defaults |

---

## 1. Generator/Evaluator Receive Strings, Not Thought Objects

### The Problem

When creating a `GraphOfThought` with custom evaluator/generator functions, the functions receive the thought **content** (a string), not the `Thought` object. This is confusing because the parameter is often named `thought`.

```python
# What I wrote (intuitive but wrong)
def evaluator(thought):
    content = thought.content.lower()  # AttributeError!

# What actually works
def evaluator(thought_content):  # It's actually a string
    content = thought_content.lower()
```

### Why It Matters

- Parameter naming suggests a `Thought` object
- Inconsistent with how other parts of the codebase work
- Easy to make this mistake repeatedly

### Potential Feature Scenario

```gherkin
@api-usability @mvp-p1
Feature: Intuitive Generator and Evaluator APIs
  As a Data Scientist building custom reasoning strategies
  I want clear, predictable function signatures
  So that I can implement evaluators without reading source code

  Scenario: Evaluator function receives thought object for full context
    Given Jordan creates a custom evaluator function
    When the evaluator is called during graph expansion
    Then the evaluator should receive a Thought object
    And the Thought should have accessible "content" and "score" attributes

  Scenario: Generator function receives thought object for context
    Given Jordan creates a custom generator function
    When the generator is called to expand a thought
    Then the generator should receive a Thought object
    And Jordan can access the thought's content, score, and metadata
```

### Suggested Fix

Either:
1. **Change the API** to pass `Thought` objects (breaking change)
2. **Rename parameters** to `content: str` to make it clear
3. **Create wrapper classes** that accept `Thought -> T` functions

---

## 2. SearchConfig Ceremony Required for beam_search()

### The Problem

To run a search, you must create a `SearchConfig` object even for simple cases:

```python
# Current - verbose
config = SearchConfig(max_expansions=6, beam_width=2, max_depth=3)
result = await graph.beam_search(config=config)

# More intuitive
result = await graph.search(max_depth=3, beam_width=2)
```

### Why It Matters

- Extra ceremony for common operations
- Discoverability: users might not know `SearchConfig` exists
- Simple use cases require understanding the config class

### Potential Feature Scenario

```gherkin
@api-usability @mvp-p1
Feature: Simple Search API
  As a Data Scientist exploring ideas
  I want to run searches with minimal configuration
  So that I can quickly explore without learning config classes

  Scenario: Quick search with keyword arguments
    Given Jordan has a thought graph with multiple paths
    When Jordan runs a search with max_depth=3 and beam_width=2
    Then the search should complete successfully
    And Jordan should not need to create a SearchConfig object

  Scenario: SearchConfig for advanced use cases
    Given Jordan needs fine-grained control over search behavior
    When Jordan creates a SearchConfig with timeout and checkpointing
    Then the search should respect all configuration options
```

### Suggested Fix

Add a convenience method:
```python
async def search(
    self,
    max_depth: int = 10,
    beam_width: int = 3,
    max_expansions: int = 100,
    goal: GoalPredicate | None = None,
) -> SearchResult:
    """Simple search with keyword arguments."""
    config = SearchConfig(max_depth=max_depth, beam_width=beam_width, ...)
    return await self.beam_search(config=config, goal=goal)
```

---

## 3. `record_discovery(found_in=...)` Expects Node ID

### The Problem

The `found_in` parameter name suggests a location (file, module, context) but actually expects a graph node ID:

```python
# What I tried (intuitive but wrong)
project.record_discovery(
    "Important finding",
    found_in="dogfood_demo.py"  # NodeNotFoundError!
)

# What it actually expects
project.record_discovery(
    "Important finding",
    found_in="node-abc123"  # A valid node ID in the project graph
)
```

### Why It Matters

- Parameter name is misleading
- Common use case (recording where you found something) doesn't work as expected

### Potential Feature Scenario

```gherkin
@api-usability @mvp-p2
Feature: Recording Discoveries with Context
  As an Engineering Manager tracking team learnings
  I want to record where discoveries were made
  So that future team members can trace back to the source

  Scenario: Record discovery with file source
    Given Alex is working on the "Platform Redesign" project
    When Alex records a discovery "Config loading is slow"
    And specifies the source as "config_loader.py"
    Then the discovery should be linked to that source location
    And the handoff should show where the discovery was made

  Scenario: Record discovery linked to work chunk
    Given Alex found an issue while working on "Database Migration"
    When Alex records the discovery
    Then it should automatically link to the current work chunk
```

### Suggested Fix

Either:
1. **Rename parameter** to `parent_node_id` to be explicit
2. **Add separate parameter** `source_file: str` for file references
3. **Make it optional** and auto-link to current chunk if available

---

## 4. Inconsistent Naming Conventions

### The Problem

Similar concepts have different names across the API:

| Concept | `plan_chunk()` | `KnowledgeEntry` | Intuitive |
|---------|---------------|------------------|-----------|
| Title | `name` | N/A (in content) | `title` |
| Summary | `notes` | `content` | `summary` or `description` |

```python
# Inconsistent naming
chunk = project.plan_chunk(name="My Chunk", ...)  # Why not title?
project.complete_chunk(chunk.id, notes="Done")     # Why not summary?

entry = KnowledgeEntry(content="Title\n\nBody...")  # No title field?
```

### Why It Matters

- Cognitive load: must remember different names for same concept
- IDE autocomplete doesn't help when names vary
- Documentation burden

### Potential Feature Scenario

```gherkin
@api-usability @mvp-p2
Feature: Consistent API Naming
  As a Developer integrating Graph of Thought
  I want consistent parameter names across the API
  So that I can write code without constantly checking documentation

  Scenario: Work chunks use standard naming
    Given Sam is planning work for the team
    When Sam creates a work chunk
    Then Sam can specify a "title" for the chunk
    And Sam can provide a "description" for details
    And Sam can add a "summary" when completing

  Scenario: Knowledge entries have explicit title field
    Given Avery is capturing a pattern
    When Avery creates a knowledge entry
    Then Avery can specify a "title" separately from "content"
    And the title appears in listings without parsing content
```

### Suggested Fix

Standardize on:
- `title` for short identifiers
- `description` for longer explanations
- `summary` for completion notes
- `content` for body text

---

## 5. `ask_question(blocking=True)` Doesn't Work

### The Problem

The intuitive way to mark a question as blocking doesn't work:

```python
# What I tried (intuitive but wrong)
project.ask_question(
    question="Should we proceed?",
    blocking=True  # Not a valid parameter!
)

# What actually works
project.ask_question(
    question="Should we proceed?",
    priority=QuestionPriority.BLOCKING
)
```

### Why It Matters

- `blocking` is the most common reason to prioritize a question
- Requiring an enum import for a boolean concept adds friction

### Potential Feature Scenario

```gherkin
@api-usability @mvp-p2
Feature: Simple Blocking Question API
  As a Developer asking questions during work
  I want a simple way to mark questions as blocking
  So that I don't need to import priority enums for common cases

  Scenario: Mark question as blocking with boolean
    Given Taylor is implementing a feature
    When Taylor asks a question with blocking=True
    Then the question should be marked as blocking
    And work should show as blocked until answered

  Scenario: Use priority enum for fine-grained control
    Given Taylor needs to specify URGENT vs IMPORTANT priority
    When Taylor uses QuestionPriority.URGENT
    Then the question should have urgent priority
```

### Suggested Fix

Add `blocking: bool = False` parameter that sets priority to BLOCKING when True:
```python
def ask_question(
    self,
    question: str,
    context: str = "",
    blocking: bool = False,  # Convenience parameter
    priority: QuestionPriority = QuestionPriority.NORMAL,
) -> Question:
    if blocking:
        priority = QuestionPriority.BLOCKING
    ...
```

---

## 6. No Simple `search()` Method

### The Problem

Only `beam_search()` exists. Users must know this is the search method:

```python
# What I tried first
result = await graph.search(...)  # AttributeError!

# What exists
result = await graph.beam_search(config=config)
```

### Why It Matters

- `search()` is the obvious method name
- `beam_search` implies there are other search types (there aren't currently)
- Adds friction for new users

### Potential Feature Scenario

```gherkin
@api-usability @mvp-p1
Feature: Default Search Method
  As a Data Scientist new to Graph of Thought
  I want an obvious search method name
  So that I can explore thoughts without learning search algorithm names

  Scenario: Simple search with default algorithm
    Given Jordan has created a thought graph
    When Jordan calls graph.search()
    Then the search should use sensible defaults
    And return a SearchResult with the best path

  Scenario: Explicit algorithm selection
    Given Jordan needs a specific search strategy
    When Jordan calls graph.beam_search() or graph.depth_first_search()
    Then the specified algorithm should be used
```

### Suggested Fix

Add `search()` as an alias or wrapper for `beam_search()` with sensible defaults.

---

## Next Steps

1. **Review** these scenarios with the team
2. **Prioritize** based on user impact and implementation effort
3. **Add to feature files** in appropriate capability directories
4. **Implement** step definitions and code changes

## Related Files

- `graph_of_thought/graph.py` - GraphOfThought class
- `graph_of_thought/collaborative.py` - CollaborativeProject class
- `graph_of_thought/core/protocols.py` - SearchConfig
- `graph_of_thought/domain/models/knowledge.py` - KnowledgeEntry, Decision
