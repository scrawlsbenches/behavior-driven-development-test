# Scenario Outline Changes Needed

This document lists all opportunities to reduce duplication in BDD feature files by converting repetitive scenarios to Scenario Outlines with Examples tables.

**Estimated Impact:** 37 scenarios → 12 Scenario Outlines (~68% reduction in duplication)

---

## High Priority Changes

### 1. persistence.feature

**File:** `features/persistence.feature`

#### Change 1.1: Persistence Backend Operations
**Lines affected:** 9-16, 34-42, 18-24, 51-57, 26-30, 59-66

**Current (6 separate scenarios):**
```gherkin
Scenario: Saving and loading graph with in-memory persistence
  Given an in-memory persistence backend
  ...

Scenario: Saving and loading graph with file persistence
  Given a file persistence backend
  ...
```

**Proposed (1 Scenario Outline):**
```gherkin
Scenario Outline: Saving and loading graph with <backend> persistence
  Given a <backend> persistence backend
  And a graph with thought "Root" and child "Child 1"
  When I save the graph with id "test_graph" and metadata version="1.0"
  And I load the graph with id "test_graph"
  Then the loaded graph should contain thought "Root"
  And the loaded graph should contain thought "Child 1"
  And the loaded metadata should have version "1.0"

Examples:
  | backend   |
  | in-memory |
  | file      |
```

#### Change 1.2: Checkpoint Operations
**Lines affected:** 18-24, 51-57

**Proposed:**
```gherkin
Scenario Outline: Checkpoint roundtrip with <backend> persistence
  Given a <backend> persistence backend
  When I save checkpoint "<checkpoint_id>" with state <state_key>=<state_value>
  And I load checkpoint "<checkpoint_id>"
  Then the loaded checkpoint state should have <state_key>=<state_value>

Examples:
  | backend   | checkpoint_id | state_key     | state_value |
  | in-memory | checkpoint_1  | current_depth | 3           |
  | file      | checkpoint_2  | beam_width    | 5           |
```

#### Change 1.3: Delete Operations
**Lines affected:** 26-30, 59-66

**Proposed:**
```gherkin
Scenario Outline: Deleting a <resource_type> with <backend> persistence
  Given a <backend> persistence backend
  And a saved <resource_type> with id "<resource_id>"
  When I delete the <resource_type> "<resource_id>"
  Then loading <resource_type> "<resource_id>" should return nothing

Examples:
  | backend   | resource_type | resource_id    |
  | in-memory | graph         | deletable      |
  | file      | graph         | file_deletable |
```

#### Change 1.4: Loading Non-Existent Resources
**Lines affected:** 68-76

**Current:**
```gherkin
Scenario: Loading non-existent graph returns nothing
  ...

Scenario: Loading non-existent checkpoint returns nothing
  ...
```

**Proposed:**
```gherkin
Scenario Outline: Loading non-existent <resource_type> returns nothing
  Given an in-memory persistence backend
  When I try to load <resource_type> "<resource_id>"
  Then the result should be nothing

Examples:
  | resource_type | resource_id          |
  | graph         | non_existent         |
  | checkpoint    | no_such_checkpoint   |
```

---

### 2. metrics_collector.feature

**File:** `features/metrics_collector.feature`

#### Change 2.1: Metric Type Operations
**Lines affected:** 23-30, 56-59, 78-82, 103-107

**Current (4 separate scenarios):**
```gherkin
Scenario: Counter starts at zero
  ...
Scenario: Gauge sets current value
  ...
Scenario: Histogram records single value
  ...
Scenario: Timing records single duration
  ...
```

**Proposed:**
```gherkin
Scenario Outline: <metric_type> records a single value
  Given an in-memory metrics collector
  When I <operation> "<metric_name>" with value <value>
  Then the <metric_type> "<metric_name>" should equal <expected>

Examples:
  | metric_type | operation        | metric_name      | value  | expected |
  | counter     | increment        | requests         | 5      | 5        |
  | gauge       | set              | temperature      | 72.5   | 72.5     |
  | histogram   | record           | response_size    | 1024   | 1024     |
  | timing      | record timing    | request_duration | 150.5  | 150.5    |
```

#### Change 2.2: Metric Accumulation Behavior
**Lines affected:** 32-36, 61-65, 84-90, 109-114

**Proposed:**
```gherkin
Scenario Outline: <metric_type> handles multiple operations with <behavior>
  Given an in-memory metrics collector
  When I <operation> "<metric_name>" with value <value1>
  And I <operation> "<metric_name>" with value <value2>
  Then the <metric_type> "<metric_name>" should <assertion>

Examples:
  | metric_type | operation     | metric_name  | value1 | value2 | behavior    | assertion              |
  | counter     | increment     | requests     | 5      | 3      | accumulate  | equal 8                |
  | gauge       | set           | queue_size   | 10     | 5      | overwrite   | equal 5                |
  | histogram   | record        | response     | 100    | 200    | accumulate  | contain 2 values       |
  | timing      | record timing | db_query     | 10.0   | 20.0   | accumulate  | contain 2 values       |
```

#### Change 2.3: Tagged Metrics
**Lines affected:** 38-43, 67-72, 92-97, 116-121

**Proposed:**
```gherkin
Scenario Outline: <metric_type> with tags creates separate metrics
  Given an in-memory metrics collector
  When I <operation> "<metric_name>" with value <value1> with tags <tag_key>="<tag_val1>"
  And I <operation> "<metric_name>" with value <value2> with tags <tag_key>="<tag_val2>"
  Then the <metric_type> "<metric_name>" with tags <tag_key>="<tag_val1>" should equal <value1>
  And the <metric_type> "<metric_name>" with tags <tag_key>="<tag_val2>" should equal <value2>

Examples:
  | metric_type | operation     | metric_name | tag_key  | tag_val1 | tag_val2 | value1 | value2 |
  | counter     | increment     | requests    | endpoint | users    | orders   | 1      | 2      |
  | gauge       | set           | connections | server   | primary  | replica  | 100    | 50     |
  | histogram   | record        | latency     | endpoint | fast     | slow     | 50     | 500    |
  | timing      | record timing | api_call    | service  | auth     | data     | 100.0  | 200.0  |
```

#### Change 2.4: Query Operations
**Lines affected:** 127-137

**Current:**
```gherkin
Scenario: List all counter names
  ...
Scenario: List all gauge names
  ...
```

**Proposed:**
```gherkin
Scenario Outline: List all <metric_type> names
  Given an in-memory metrics collector
  When I <operation1> "<name1>" with value <value1>
  And I <operation2> "<name2>" with value <value2>
  Then the collector should have <metric_type>s ["<name1>", "<name2>"]

Examples:
  | metric_type | operation1 | operation2 | name1    | name2  | value1 | value2 |
  | counter     | increment  | increment  | requests | errors | 1      | 1      |
  | gauge       | set        | set        | memory   | cpu    | 1024   | 50     |
```

---

### 3. verification.feature

**File:** `features/verification.feature`

#### Change 3.1: Configurable Verifier Results
**Lines affected:** 50-73

**Current (4 separate scenarios):**
```gherkin
Scenario: Configuring verifier to fail
  ...
Scenario: Configuring verifier with custom confidence
  ...
Scenario: Configuring verifier with issues
  ...
Scenario: Configuring verifier with metadata
  ...
```

**Proposed:**
```gherkin
Scenario Outline: Configuring verifier with <config_type>
  Given an in-memory verifier <configuration>
  When I verify content "<test_content>"
  Then <assertion>

Examples:
  | config_type | configuration                              | test_content | assertion                                        |
  | fail mode   | configured to fail                         | any content  | the verifier result should fail                  |
  | confidence  | with confidence 0.75                       | test content | the verifier result confidence should be 0.75    |
  | issues      | with issues "Missing citation"             | problematic  | the verifier result should have 1 issue          |
  | metadata    | with metadata source="test"                | test content | the result metadata should have "source"="test"  |
```

#### Change 3.2: Content-Based Rules
**Lines affected:** 79-102

**Current:**
```gherkin
Scenario: Adding validation rule that rejects specific content
  ...
Scenario: Adding validation rule that rejects specific content - passing case
  ...
```

**Proposed:**
```gherkin
Scenario Outline: Validation rule rejects content containing "<reject_word>" - <case>
  Given an in-memory verifier
  And a rule that rejects content containing "<reject_word>"
  When I verify content "<test_content>"
  Then the verifier result should <expected_result>

Examples:
  | reject_word | test_content         | case          | expected_result |
  | error       | this has an error    | matching      | fail            |
  | error       | this is fine         | non-matching  | pass            |
  | spam        | this is spam content | matching      | fail            |
  | spam        | this is valid        | non-matching  | pass            |
```

---

## Medium Priority Changes

### 4. llm.feature

**File:** `features/llm.feature`

#### Change 4.1: Response Parsing - Evaluator
**Lines affected:** 136-154

**Current:**
```gherkin
Scenario: Evaluator parses JSON score response
  ...
Scenario: Evaluator parses score from markdown code block
  ...
Scenario: Evaluator extracts number from plain text
  ...
Scenario: Evaluator defaults to 0.5 for unparseable responses
  ...
```

**Proposed:**
```gherkin
Scenario Outline: Evaluator parses <response_type> response
  Given a mock LLM evaluator
  When the LLM returns '<response>'
  Then the evaluation score should be <expected_score>

Examples:
  | response_type        | response                                          | expected_score |
  | JSON object          | {"score": 0.85, "reasoning": "Good clarity"}      | 0.85           |
  | markdown code block  | ```json\n{"score": 0.7}\n```                      | 0.7            |
  | plain text number    | The thought scores 0.6 overall                    | 0.6            |
  | unparseable          | Cannot evaluate this thought                      | 0.5            |
```

#### Change 4.2: Template Placeholder Validation
**Lines affected:** 44-58

**Current:**
```gherkin
Scenario: Default generation template has required placeholders
  ...
Scenario: Default evaluation template has required placeholders
  ...
Scenario: Default verification template has required placeholders
  ...
```

**Proposed:**
```gherkin
Scenario Outline: Default <template_type> template has required placeholders
  Given the default <template_type> template
  Then the template should have placeholder "<placeholder1>"
  And the template should have placeholder "<placeholder2>"

Examples:
  | template_type | placeholder1 | placeholder2 |
  | generation    | parent       | num_children |
  | evaluation    | thought      | path         |
  | verification  | thought      | path         |
```

---

### 5. tracing.feature

**File:** `features/tracing.feature`

#### Change 5.1: Span Status
**Lines affected:** 100-111

**Current:**
```gherkin
Scenario: Setting span status to OK
  ...
Scenario: Setting span status to ERROR with description
  ...
```

**Proposed:**
```gherkin
Scenario Outline: Setting span status to <status>
  Given an in-memory tracing provider
  When I start a span "<span_name>"
  And I set status "<status>" <with_description> on span "<span_name>"
  Then the span "<span_name>" should have status "<status>"
  <description_assertion>

Examples:
  | status | span_name            | with_description                        | description_assertion                                    |
  | OK     | successful_operation | (no description)                        |                                                          |
  | ERROR  | failed_operation     | with description "Connection timeout"   | And the span should have status description "Connection timeout" |
```

#### Change 5.2: Child Span Creation
**Lines affected:** 117-139

**Current:**
```gherkin
Scenario: Creating child spans
  ...
Scenario: Nested child spans
  ...
Scenario: Multiple children under one parent
  ...
```

**Proposed:**
```gherkin
Scenario Outline: Creating <scenario_type> child spans
  Given an in-memory tracing provider
  When I start a span "parent"
  <child_creation_steps>
  Then <assertion>

Examples:
  | scenario_type    | child_creation_steps                                      | assertion                              |
  | single child     | And I start a child span "child" under "parent"           | the span "child" should have parent "parent" |
  | multiple children| And I start 3 child spans under "parent"                  | the span "parent" should have 3 children |
```

---

### 6. search.feature

**File:** `features/search.feature`

#### Change 6.1: Search Algorithm Tests
**Lines affected:** 10-22

**Current:**
```gherkin
Scenario: Beam search finds a path
  ...
Scenario: Best-first search finds a path
  ...
```

**Proposed:**
```gherkin
Scenario Outline: <algorithm> finds a path
  Given a test graph with evaluator and generator
  And a thought "Start" exists
  When I run <algorithm>
  Then at least 1 thought should be expanded
  And the best path should contain "Start"

Examples:
  | algorithm        |
  | beam search      |
  | best-first search|
```

---

### 7. services.feature

**File:** `features/services.feature`

#### Change 7.1: Null Service Behaviors
**Lines affected:** 13-28

**Current:**
```gherkin
Scenario: Null governance service auto-approves everything
  ...
Scenario: Null resource service has unlimited resources
  ...
Scenario: Null knowledge service stores but finds nothing
  ...
```

**Proposed:**
```gherkin
Scenario Outline: Null <service_type> service has <behavior>
  Given a null <service_type> service
  When I <action>
  Then <assertion>

Examples:
  | service_type | behavior             | action                        | assertion                        |
  | governance   | auto-approval        | check approval for "deploy"   | the status should be APPROVED    |
  | resource     | unlimited resources  | check available tokens        | resources should be unlimited    |
  | knowledge    | no retrieval         | store and retrieve knowledge  | no entries should be found       |
```

---

## Summary

| File | Current Scenarios | After Refactoring | Reduction |
|------|------------------|-------------------|-----------|
| persistence.feature | 8 | 4 | 50% |
| metrics_collector.feature | 12 | 4 | 67% |
| verification.feature | 6 | 2 | 67% |
| llm.feature | 7 | 2 | 71% |
| tracing.feature | 5 | 2 | 60% |
| search.feature | 2 | 1 | 50% |
| services.feature | 3 | 1 | 67% |
| **Total** | **43** | **16** | **63%** |

---

## Implementation Notes

1. **Step Definition Updates**: Some step definitions may need modification to handle parameterized values from Examples tables.

2. **Readability Trade-off**: While Scenario Outlines reduce duplication, ensure the Examples table remains readable. Consider splitting into multiple Scenario Outlines if the table becomes too wide.

3. **Tag Inheritance**: Tags applied to a Scenario Outline apply to all Examples. Use row-specific tags if needed:
   ```gherkin
   Examples:
     | backend   |
     | in-memory |
     @slow
     | file      |
   ```

4. **Error Message Clarity**: Ensure test failure messages clearly identify which Example row failed.

5. **Gradual Migration**: Implement changes file-by-file, running tests after each change to ensure no regressions.

---

*Document created as part of BDD quality improvement initiative*
