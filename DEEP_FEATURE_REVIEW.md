# Deep Feature File Review: Enterprise Graph of Thought

**Review Date:** 2026-01-17
**Reviewer:** Claude Code Deep Analysis
**Feature Files Analyzed:** 25 files (~2,500 lines)
**Scenarios Reviewed:** 135 implemented + 64 @wip

---

## Executive Summary

This deep review identifies **actionable improvements** to make your feature files closer to real-world implementation standards. While the existing evaluation report gave a score of 92/100, this review focuses on specific gaps that could impact enterprise readiness and real-world usage.

### Key Finding Categories

| Category | Issues Found | Priority |
|----------|--------------|----------|
| Missing Real-World Scenarios | 12 | High |
| Incomplete Error Handling | 8 | High |
| Missing Integration Points | 6 | Medium |
| Terminology Inconsistencies | 5 | Medium |
| Missing Concurrency Scenarios | 4 | High |
| Underspecified Behavior | 7 | Medium |
| Missing Security Scenarios | 5 | High |

---

## 1. Missing Real-World Scenarios

### 1.1 No Network Failure Scenarios

**Location:** `llm.feature`, `orchestrator.feature`

**Problem:** The LLM integration and orchestrator features don't specify behavior during network failures, which are common in production.

**Current Gap:**
```gherkin
# llm.feature only has:
@wip
Scenario: Generator handles rate limit errors with retry
```

**Recommended Addition:**
```gherkin
@wip @resilience
Scenario: Generator handles network timeout gracefully
  Given a mock LLM generator
  And the network connection times out after 5 seconds
  When I try to generate thoughts
  Then the generator should retry 3 times with exponential backoff
  And finally raise a NetworkError with details

@wip @resilience
Scenario: Generator handles DNS resolution failure
  Given a mock LLM generator
  And DNS resolution fails for the API endpoint
  When I try to generate thoughts
  Then the generator should fail fast with a clear error message
  And not retry (DNS failures are not transient)

@wip @resilience
Scenario: Orchestrator continues with degraded service
  Given a simple orchestrator
  And the knowledge service is unreachable
  When I handle a CHUNK_COMPLETED event
  Then the event should be processed with governance only
  And a warning should indicate knowledge service unavailable
  And the event should be queued for retry when service recovers
```

### 1.2 No Data Migration/Versioning Scenarios

**Location:** `persistence.feature`, `knowledge.feature`

**Problem:** No scenarios for handling schema evolution or data format changes.

**Recommended Addition:**
```gherkin
@wip @migration
Scenario: Persistence handles v1 to v2 schema migration
  Given a file persistence backend with v1 schema graphs
  When I load a graph saved with v1 schema
  Then the graph should be automatically migrated to v2
  And the original v1 file should be preserved as backup
  And the migrated graph should function correctly

@wip @migration
Scenario: Knowledge service handles legacy entry formats
  Given a simple knowledge service
  And knowledge entries saved in the legacy format (pre-2025)
  When I retrieve knowledge
  Then legacy entries should be transparently converted
  And search should work across both formats
```

### 1.3 No Pagination Scenarios

**Location:** `knowledge.feature`, `questions.feature`, `resources.feature`

**Problem:** Real-world systems need pagination for large datasets.

**Recommended Addition:**
```gherkin
@wip @pagination
Scenario: Knowledge service supports paginated retrieval
  Given a simple knowledge service
  And 1000 knowledge entries exist
  When I search for "database" with page size 20
  Then 20 entries should be returned
  And the response should include total_count 150
  And the response should include next_page cursor

@wip @pagination
Scenario: Question service paginates pending questions
  Given a simple question service
  And 500 pending questions exist
  When I get pending questions with page 2 and size 50
  Then questions 51-100 should be returned
  And the response should indicate more pages available
```

---

## 2. Incomplete Error Handling Specifications

### 2.1 Missing Error Recovery Scenarios

**Location:** `collaborative.feature`

**Problem:** No scenarios for recovering from partial failures.

**Current:**
```gherkin
Scenario: Starting a chunk creates a session
  Given a collaborative project with a request "Build a CMS"
  And a ready chunk "Core models" exists
  When I start chunk "Core models"
  Then a session should be active
```

**Missing Recovery Scenario:**
```gherkin
@wip @recovery
Scenario: Recovering from crashed session
  Given a collaborative project with a request "Build a CMS"
  And a chunk "Core models" with a crashed session (no clean shutdown)
  When I attempt to start a new session for chunk "Core models"
  Then the crashed session should be recovered
  And work artifacts should be preserved
  And the new session should have access to previous context

@wip @recovery
Scenario: Partial chunk completion is preserved on crash
  Given an in-progress chunk "Core models"
  And 3 artifacts have been created during the session
  When the session crashes unexpectedly
  Then the 3 artifacts should be preserved
  And a recovery checkpoint should be created
  And the chunk status should be "INTERRUPTED" not "LOST"
```

### 2.2 Missing Validation Error Scenarios

**Location:** `governance.feature`, `resources.feature`

**Problem:** Input validation scenarios are sparse.

**Recommended Addition:**
```gherkin
@wip @validation
Scenario: Governance service validates policy names
  Given a simple governance service
  When I try to register a policy with name containing special characters "deploy/prod!"
  Then a validation error should be raised
  And the error should specify invalid characters

@wip @validation
Scenario: Resource service validates project identifiers
  Given a simple resource service
  When I try to set budget for project ""
  Then a validation error should be raised
  And the error should indicate "project_id cannot be empty"

@wip @validation
Scenario: Resource service rejects negative budget amounts
  Given a simple resource service
  When I try to set a token budget of -1000 for project "test"
  Then a validation error should be raised
  And the current budget should be unchanged
```

---

## 3. Missing Integration Point Specifications

### 3.1 No Webhook/Event Emission Scenarios

**Location:** `orchestrator.feature`

**Problem:** Real enterprise systems need external notification capabilities.

**Recommended Addition:**
```gherkin
@wip @webhooks
Scenario: Orchestrator emits webhook on critical events
  Given a simple orchestrator
  And a webhook configured for CHUNK_COMPLETED events to "https://api.example.com/hooks"
  When I handle a CHUNK_COMPLETED event for project "test"
  Then a POST request should be sent to the webhook URL
  And the payload should include event type, project, and timestamp

@wip @webhooks
Scenario: Orchestrator retries failed webhook delivery
  Given a simple orchestrator
  And a webhook configured that returns 500 errors
  When I handle a CHUNK_COMPLETED event for project "test"
  Then the webhook should be retried 3 times
  And the failed delivery should be logged
  And the event should be queued for later retry

@wip @webhooks
Scenario: Orchestrator supports webhook authentication
  Given a simple orchestrator
  And a webhook with HMAC signature verification
  When I handle an event
  Then the webhook payload should include X-Signature header
  And the signature should be verifiable with the shared secret
```

### 3.2 No External Identity Provider Scenarios

**Location:** `governance.feature`

**Problem:** Enterprise systems need to integrate with identity providers.

**Recommended Addition:**
```gherkin
@wip @identity
Scenario: Governance service validates actor from JWT token
  Given a simple governance service with JWT validation
  And a valid JWT token for user "alice" with roles "developer", "reviewer"
  When I check approval for action "deploy" with the token
  Then the actor should be extracted as "alice"
  And the roles should be available for policy evaluation

@wip @identity
Scenario: Governance service rejects expired tokens
  Given a simple governance service with JWT validation
  And an expired JWT token for user "alice"
  When I check approval for action "deploy" with the token
  Then an authentication error should be raised
  And the error should indicate "token expired"
```

---

## 4. Terminology Inconsistencies

### 4.1 Inconsistent Service Naming

**Problem:** Some features use "in-memory" while others use "simple" for test implementations.

**Examples:**
- `resources.feature`: "In-memory resource service has unlimited resources"
- `resources.feature`: "Simple resource service tracks budgets"
- `knowledge.feature`: "In-memory knowledge service accepts stores..."
- `knowledge.feature`: "Simple knowledge service stores and retrieves..."

**Recommendation:** Standardize terminology:
- **In-Memory**: Test double that stubs behavior (returns defaults)
- **Simple**: Minimal working implementation with real logic

Add a terminology section at the top of each service feature:
```gherkin
# ===========================================================================
# Terminology
# ===========================================================================
# In-Memory Service: Test double with stubbed behavior (always succeeds, no persistence)
# Simple Service: Minimal implementation with real logic (in-memory storage)
# Full Service: Production-ready with external dependencies (database, cache, etc.)
```

### 4.2 Inconsistent Status Values

**Problem:** Status values use different cases and formats.

**Examples:**
- `collaborative.feature`: status "READY", "IN_PROGRESS", "COMPLETED"
- `questions.feature`: status "open", "answered"
- `governance.feature`: status "pending", "approved", "denied"

**Recommendation:** Standardize all status values to UPPER_SNAKE_CASE:
```gherkin
# Consistent status values across all features
# Questions: OPEN, ANSWERED, CLOSED
# Chunks: READY, IN_PROGRESS, BLOCKED, COMPLETED
# Approvals: PENDING, APPROVED, DENIED, EXPIRED
```

---

## 5. Missing Concurrency Scenarios

### 5.1 No Race Condition Specifications

**Location:** `collaborative.feature`, `resources.feature`

**Problem:** No scenarios for concurrent access, which is critical for multi-user systems.

**Recommended Addition:**
```gherkin
@wip @concurrency
Scenario: Two users cannot start the same chunk simultaneously
  Given a collaborative project with a request "Build a CMS"
  And a ready chunk "Core models" exists
  When user "alice" starts chunk "Core models"
  And user "bob" simultaneously tries to start chunk "Core models"
  Then only one session should be created
  And the second attempt should fail with "chunk already in progress"

@wip @concurrency
Scenario: Concurrent budget consumption uses optimistic locking
  Given a simple resource service
  And a token budget of 1000 for project "test"
  When 10 concurrent requests each try to consume 100 tokens
  Then exactly 10 requests should succeed
  And the final budget should be 0
  And no race conditions should occur

@wip @concurrency
Scenario: Question answers handle concurrent responses
  Given a pending question "What database?"
  When "alice" and "bob" simultaneously submit answers
  Then only the first answer should be recorded
  And the second should receive "already answered" error
```

### 5.2 No Locking/Transaction Scenarios

**Location:** `governance.feature`, `knowledge.feature`

**Recommended Addition:**
```gherkin
@wip @transactions
Scenario: Multi-step approval is atomic
  Given a simple governance service
  And an approval requiring 2 approvers
  When "tech-lead" approves while system is recording
  And the system crashes mid-transaction
  Then the approval should be rolled back
  And the approval state should be consistent on restart

@wip @transactions
Scenario: Knowledge service updates are atomic
  Given a simple knowledge service
  When I update entry "E1" with new content
  And the update fails mid-write
  Then the original entry should be preserved
  And no partial updates should exist
```

---

## 6. Underspecified Behavior

### 6.1 Undefined Edge Boundaries

**Location:** `search.feature`, `search_strategies.feature`

**Problem:** Search scenarios don't specify behavior at exact boundaries.

**Missing Scenarios:**
```gherkin
@wip @boundaries
Scenario: Beam search with exactly max_depth nodes
  Given a graph with max depth 5
  And a linear chain of exactly 5 thoughts
  When I run beam search
  Then the termination reason should be "max_depth"
  And the last thought in best_path should be at depth 5

@wip @boundaries
Scenario: Beam search with exactly max_expansions
  Given a graph with max expansions 10
  When I run beam search and exactly 10 expansions occur
  Then the termination reason should be "max_expansions"
  And the expansions count should be exactly 10

@wip @boundaries
Scenario: Search with beam width of 1 (greedy search)
  Given a beam width of 1
  And a thought "Start" exists
  When I run beam search
  Then only the highest-scoring thought should be kept at each level
  And the search should behave as greedy best-first
```

### 6.2 Incomplete State Machine Specifications

**Location:** `collaborative.feature`

**Problem:** Chunk status transitions aren't fully specified.

**Missing State Diagram Scenarios:**
```gherkin
@wip @states
Scenario: Chunk status transitions follow valid state machine
  # Valid transitions: READY -> IN_PROGRESS -> COMPLETED
  #                   READY -> BLOCKED -> READY -> IN_PROGRESS
  #                   IN_PROGRESS -> INTERRUPTED -> READY
  Given a collaborative project with a request "Build a CMS"
  And a ready chunk "Core models" exists
  When I try to complete chunk "Core models" directly (skip IN_PROGRESS)
  Then an invalid state transition error should be raised

@wip @states
Scenario: Cannot restart a completed chunk
  Given a collaborative project with a request "Build a CMS"
  And a completed chunk "Core models" exists
  When I try to start chunk "Core models"
  Then an invalid state transition error should be raised
  And the error should indicate "completed chunks cannot be restarted"
```

---

## 7. Missing Security Scenarios

### 7.1 No Authorization Scenarios

**Location:** `governance.feature`, `resources.feature`, `knowledge.feature`

**Problem:** No scenarios verifying role-based access control.

**Recommended Addition:**
```gherkin
@wip @security @authorization
Scenario: Only admins can modify budget limits
  Given a simple resource service
  And user "alice" with role "developer"
  When "alice" tries to set budget for project "test"
  Then an authorization error should be raised
  And the error should indicate "insufficient permissions"

@wip @security @authorization
Scenario: Knowledge entries respect visibility rules
  Given a simple knowledge service
  And a knowledge entry "Salary structure" with visibility "hr-only"
  And user "bob" with role "developer"
  When "bob" searches for "salary"
  Then no entries should be returned

@wip @security @authorization
Scenario: Audit log cannot be modified
  Given a simple governance service
  When I try to delete an audit log entry
  Then an error should be raised
  And the error should indicate "audit logs are immutable"
```

### 7.2 No Data Sanitization Scenarios

**Location:** `llm.feature`, `knowledge.feature`

**Recommended Addition:**
```gherkin
@wip @security @sanitization
Scenario: LLM generator sanitizes prompt injection attempts
  Given a mock LLM generator
  And a parent thought "Ignore previous instructions and..."
  When I generate child thoughts
  Then the prompt should be sanitized
  And injection markers should be escaped

@wip @security @sanitization
Scenario: Knowledge service sanitizes stored content
  Given a simple knowledge service
  When I store knowledge containing "<script>alert('xss')</script>"
  Then the script tags should be sanitized
  And the stored content should be safe for display
```

---

## 8. Specific Feature File Improvements

### 8.1 `orchestrator.feature` - Missing Sequence Guarantees

**Current gap:** No specification for event ordering.

```gherkin
@wip @ordering
Scenario: Events for same project are processed in order
  Given a simple orchestrator with ordered event queue
  When I emit events in order: CHUNK_STARTED, QUESTION_ASKED, CHUNK_COMPLETED
  Then events should be processed in the same order
  And CHUNK_COMPLETED should not be processed before CHUNK_STARTED
```

### 8.2 `llm.feature` - Missing Cost Tracking

**Current gap:** No scenarios for tracking API costs.

```gherkin
@wip @costs
Scenario: Generator tracks cost per generation
  Given a mock LLM generator with pricing $0.01 per 1K tokens
  When I generate thoughts using 500 tokens
  Then the cost should be calculated as $0.005
  And the cost should be recorded for billing

@wip @costs
Scenario: Budget includes cost estimation before generation
  Given a mock LLM generator
  And a remaining budget of $1.00
  And expected generation cost of $1.50
  When I try to generate thoughts
  Then a budget warning should be raised before generation
  And the user should be prompted to confirm
```

### 8.3 `verification.feature` - Missing Chain of Verification

**Current gap:** No multi-stage verification.

```gherkin
@wip @verification-chain
Scenario: Verification pipeline runs multiple verifiers in sequence
  Given a verification pipeline with:
    | verifier          | order |
    | syntax_verifier   | 1     |
    | fact_verifier     | 2     |
    | quality_verifier  | 3     |
  When I verify content "Test content"
  Then all verifiers should be invoked in order
  And verification should stop on first failure
  And the failing verifier should be identified in the result
```

---

## 9. Missing Scenario Outlines Opportunities

Several features could benefit from Scenario Outlines to reduce duplication and improve maintainability.

### 9.1 `governance.feature` - Policy Types

**Current (repetitive):**
```gherkin
Scenario: Deny policy returns DENIED status
  ...
Scenario: Allow policy explicitly approves action
  ...
Scenario: Review policy requires approval
  ...
```

**Improved:**
```gherkin
Scenario Outline: Policy type "<policy_type>" returns "<expected_status>" status
  Given a simple governance service
  And a policy "<action>" with type "<policy_type>"
  When I check approval for action "<action>"
  Then the approval status should be "<expected_status>"

Examples:
  | policy_type | action             | expected_status |
  | deny        | delete_production  | DENIED          |
  | allow       | read_data          | APPROVED        |
  | review      | deploy_production  | NEEDS_REVIEW    |
```

### 9.2 `llm.feature` - Response Parsing

**Improved:**
```gherkin
Scenario Outline: Evaluator parses "<format>" response correctly
  Given a mock LLM evaluator
  When the LLM returns '<response>'
  Then the evaluation score should be <expected_score>

Examples:
  | format         | response                                    | expected_score |
  | JSON           | {"score": 0.85, "reasoning": "Good"}       | 0.85           |
  | Markdown JSON  | ```json\n{"score": 0.7}\n```               | 0.7            |
  | Plain text     | The thought scores 0.6 overall             | 0.6            |
  | Unparseable    | Cannot evaluate this thought               | 0.5            |
```

---

## 10. Recommended New Feature Files

Based on the analysis, consider adding these new feature files for completeness:

### 10.1 `security.feature`
Consolidate all security-related scenarios (authorization, authentication, sanitization).

### 10.2 `resilience.feature`
Consolidate all fault tolerance scenarios (retries, circuit breakers, fallbacks).

### 10.3 `migration.feature`
Cover schema evolution and data migration scenarios.

### 10.4 `performance.feature`
Cover performance characteristics and SLA scenarios.

---

## 11. Quick Wins (Low Effort, High Impact)

1. **Add Background to `search_strategies.feature`** - Currently missing, each scenario sets up its own graph.

2. **Standardize @wip comments** - Some use `# TODO: Implement`, others use `# --- Edge Cases ---`. Pick one format.

3. **Add @critical tags** - Mark scenarios that must pass for MVP functionality.

4. **Add explicit timeout specifications** - Many scenarios mention timeouts without specifying values.

5. **Add data cleanup scenarios** - Ensure idempotent test runs.

---

## 12. Summary of Recommended Actions

### Immediate (Before Next Sprint)
1. Add missing error recovery scenarios to `collaborative.feature`
2. Add concurrency scenarios to `resources.feature`
3. Standardize terminology (in-memory vs simple)
4. Add security/authorization scenarios to `governance.feature`

### Short-Term (Next 2-3 Sprints)
1. Add network failure scenarios to `llm.feature`
2. Add pagination scenarios to `knowledge.feature` and `questions.feature`
3. Add webhook scenarios to `orchestrator.feature`
4. Convert repetitive scenarios to Scenario Outlines

### Medium-Term (Before Production)
1. Create `security.feature` file
2. Create `resilience.feature` file
3. Add migration/versioning scenarios
4. Complete all state machine specifications

---

## Conclusion

Your feature files have a strong foundation with excellent documentation practices (especially the escape clause pattern). The improvements identified in this review focus on **real-world production concerns** that enterprise systems face:

- **Fault tolerance**: Network failures, crashes, partial writes
- **Concurrency**: Race conditions, locking, transactions
- **Security**: Authorization, authentication, data sanitization
- **Operations**: Pagination, migrations, webhooks

Addressing these gaps will make your Graph of Thought application more resilient and production-ready.

**Priority Order:**
1. Security scenarios (authorization, sanitization)
2. Concurrency scenarios (race conditions, locking)
3. Error recovery scenarios (crash recovery, partial failures)
4. Integration scenarios (webhooks, external systems)

---

*Review completed: 2026-01-17*
