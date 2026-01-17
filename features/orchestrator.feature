@services @orchestrator @high
Feature: Service Orchestrator
  As a developer using Graph of Thought
  I want to use the orchestrator to coordinate services
  So that I can manage cross-cutting concerns like governance and resources

  # ===========================================================================
  # Orchestrator Setup
  # ===========================================================================

  Scenario: Creating orchestrator with default services
    Given a default orchestrator
    Then the orchestrator should have governance service
    And the orchestrator should have resource service
    And the orchestrator should have knowledge service

  Scenario: Creating orchestrator with simple services
    Given a simple orchestrator
    Then the orchestrator should use simple implementations

  # ===========================================================================
  # Event Handling - Core Events
  # ===========================================================================

  Scenario: Handling chunk started event
    Given a simple orchestrator
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should allow proceeding
    And an audit record should be created

  Scenario: Governance blocks denied actions
    Given a simple orchestrator
    And a governance policy that denies "CHUNK_STARTED"
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should not allow proceeding
    And the reason should mention "Governance denied"

  Scenario: Governance requires review for sensitive actions
    Given a simple orchestrator
    And a governance policy requiring review for "CHUNK_STARTED"
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should not allow proceeding
    And an approval ID should be provided
    And the reason should mention "Requires approval"

  Scenario: Resource warnings when budget is below 1000 token threshold
    Given a simple orchestrator
    And an orchestrator token budget of 500 for project "test"
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should include a resource warning

  Scenario: Recording resource consumption on chunk completion
    Given a simple orchestrator
    And an orchestrator token budget of 10000 for project "test"
    When I handle a CHUNK_COMPLETED event for project "test" with 1000 tokens used
    Then the token consumption should be recorded

  # ===========================================================================
  # Event Handling - Knowledge Events
  # ===========================================================================

  Scenario: Capturing answers as knowledge
    Given a simple orchestrator
    When I handle a QUESTION_ANSWERED event with question "How to auth?" and answer "Use OAuth2"
    Then a knowledge entry should be created for the answer

  Scenario: Routing questions through the orchestrator
    Given a simple orchestrator
    When I handle a QUESTION_ASKED event with question "What are the security requirements?"
    Then the response should indicate routing to "security-team"

  # --- Knowledge Edge Cases (TODO: Implement) ---

  @wip
  Scenario: Orchestrator captures decision consequences
    Given a simple orchestrator
    When I record a decision "Use Redis for caching" with consequences:
      | consequence                        |
      | Need Redis infrastructure          |
      | 10x faster response times expected |
    Then the decision should have 2 consequences stored

  @wip
  Scenario: Orchestrator links answers to original questions
    Given a simple orchestrator
    And a pending question "What caching strategy?" with id "q-123"
    When I handle a QUESTION_ANSWERED event for question "q-123" with answer "Use Redis"
    Then the knowledge entry should reference question "q-123"

  # ===========================================================================
  # Event Handling - Session Events
  # ===========================================================================

  Scenario: Preparing for context compaction
    Given a simple orchestrator
    And recorded intent "Build API" for project "test"
    When I handle a CONTEXT_COMPACTING event for project "test"
    Then the response should include compaction content
    And a handoff should be created

  Scenario: Providing resumption context on session start
    Given a simple orchestrator
    And recorded intent "Build API" for project "test"
    When I handle a SESSION_STARTED event for project "test"
    Then the response should include resumption context

  # --- Session Edge Cases (TODO: Implement) ---

  @wip
  Scenario: Orchestrator handles session timeout gracefully
    Given a simple orchestrator
    And an active session for project "test" started 2 hours ago
    And a session timeout of 1 hour
    When I handle a SESSION_STARTED event for project "test"
    Then the previous session should be marked as timed out
    And a handoff should be created for the interrupted session

  @wip
  Scenario: Orchestrator merges context from multiple sessions
    Given a simple orchestrator
    And recorded intent "Build API" from session "s1" for project "test"
    And recorded intent "Add auth" from session "s2" for project "test"
    When I handle a SESSION_STARTED event for project "test"
    Then the resumption context should include both intents in chronological order

  # ===========================================================================
  # Convenience Methods
  # ===========================================================================

  Scenario: Convenience method for asking questions
    Given a simple orchestrator
    When I use the orchestrator to ask "Should we use caching?"
    Then a question ticket should be created

  Scenario: Convenience method for recording decisions
    Given a simple orchestrator
    When I use the orchestrator to record a decision "Use Redis" for project "test"
    Then the decision should be stored in knowledge

  Scenario: Convenience method for setting token budgets
    Given a simple orchestrator
    When I set a token budget of 5000 for project "test" via orchestrator
    Then the budget should be 5000 tokens

  Scenario: Getting cross-project status
    Given a simple orchestrator
    When I get the cross-project status
    Then the status should include pending questions count

  # --- Convenience Edge Cases (TODO: Implement) ---

  @wip
  Scenario: Orchestrator validates budget before setting
    Given a simple orchestrator
    When I try to set a negative token budget of -100 for project "test"
    Then an error should be raised
    And the error should mention "Budget must be positive"

  @wip
  Scenario: Orchestrator tracks question asker for follow-up
    Given a simple orchestrator
    When I use the orchestrator to ask "Should we use caching?" as user "alice"
    Then the question should have asker "alice"
    And alice should be notified when answered

  # ===========================================================================
  # Metrics and Custom Handlers
  # ===========================================================================

  Scenario: Tracking orchestrator metrics
    Given a simple orchestrator
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    And I handle a CHUNK_COMPLETED event for project "test" chunk "chunk1"
    Then the metrics should show 1 CHUNK_STARTED event
    And the metrics should show 1 CHUNK_COMPLETED event

  Scenario: Custom event handlers
    Given a simple orchestrator
    And a custom handler for CHUNK_STARTED that adds a warning
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should include the custom warning

  # --- Metrics Edge Cases (TODO: Implement) ---

  @wip
  Scenario: Orchestrator exports metrics in Prometheus format
    Given a simple orchestrator
    And 10 CHUNK_STARTED events processed
    And 8 CHUNK_COMPLETED events processed
    When I export metrics in Prometheus format
    Then the output should contain 'orchestrator_events_total{event="CHUNK_STARTED"} 10'
    And the output should contain 'orchestrator_events_total{event="CHUNK_COMPLETED"} 8'

  @wip
  Scenario: Orchestrator tracks event processing latency
    Given a simple orchestrator
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the metrics should include processing latency for the event

  # ===========================================================================
  # Error Handling (TODO: Implement)
  # ===========================================================================

  @wip
  Scenario: Orchestrator handles service failures gracefully
    Given a simple orchestrator
    And the knowledge service is failing
    When I handle a QUESTION_ANSWERED event with question "How to auth?" and answer "Use OAuth2"
    Then the response should indicate partial failure
    And the answer should be queued for retry

  @wip
  Scenario: Orchestrator implements circuit breaker for failing services
    Given a simple orchestrator
    And the governance service has failed 5 times in the last minute
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the governance check should be skipped
    And a warning should be logged about circuit breaker activation

  @wip
  Scenario: Orchestrator retries transient failures
    Given a simple orchestrator
    And a retry policy of 3 attempts with exponential backoff
    And the resource service fails once then succeeds
    When I handle a CHUNK_COMPLETED event for project "test" with 1000 tokens used
    Then the token consumption should be recorded
    And the metrics should show 1 retry

  # ===========================================================================
  # Async and Integration (TODO: Implement)
  # ===========================================================================

  @wip
  Scenario: Orchestrator processes events asynchronously
    Given a simple orchestrator with async event queue
    When I handle 10 CHUNK_STARTED events rapidly
    Then events should be queued for background processing
    And the caller should not be blocked
    And all events should eventually be processed

  @wip
  Scenario: Orchestrator integrates with external project management
    Given a simple orchestrator with Jira integration
    And a Jira project "PROJ-123" with status "In Progress"
    When I handle a CHUNK_STARTED event for project "PROJ-123" chunk "chunk1"
    Then the response should include Jira project status
    And blocked issues should be flagged

  @wip
  Scenario: Orchestrator assigns confidence to captured knowledge
    Given a simple orchestrator
    And a question "What database?" answered by expert "senior-architect"
    When I handle a QUESTION_ANSWERED event with answer "PostgreSQL"
    Then the knowledge entry should have confidence based on source reliability
    And the expert's track record should influence confidence

  @wip
  Scenario: Orchestrator converts answers back to typed decisions
    Given a simple orchestrator
    And an answered question about "Which framework to use?"
    When I retrieve knowledge for "framework"
    Then the entry should be reconstructable as a Decision
    And include the original question context

  # ===========================================================================
  # Event Type Specifications
  # ===========================================================================

  @wip
  Scenario: CHUNK_STARTED triggers governance and resource checks
    Given a simple orchestrator
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then a governance check should be performed
    And a resource check should be performed

  @wip
  Scenario: CHUNK_COMPLETED records resource consumption
    Given a simple orchestrator
    And an orchestrator token budget of 10000 for project "test"
    When I handle a CHUNK_COMPLETED event for project "test" with 1000 tokens used
    Then the resource service should record 1000 tokens consumed

  @wip
  Scenario: QUESTION_ASKED routes to appropriate team
    Given a simple orchestrator
    When I handle a QUESTION_ASKED event with question "What security measures?"
    Then the question should be routed to "security-team"

  @wip
  Scenario: QUESTION_ANSWERED captures answer as knowledge
    Given a simple orchestrator
    When I handle a QUESTION_ANSWERED event with question "Auth approach?" and answer "JWT"
    Then a knowledge entry should exist containing "JWT"

  @wip
  Scenario: SESSION_STARTED provides resumption context
    Given a simple orchestrator
    And recorded intent "Build API" for project "test"
    When I handle a SESSION_STARTED event for project "test"
    Then the response should contain "Build API" in resumption context

  @wip
  Scenario: CONTEXT_COMPACTING creates handoff package
    Given a simple orchestrator
    When I handle a CONTEXT_COMPACTING event for project "test"
    Then a handoff should be created for project "test"

  # ===========================================================================
  # Response Field Specifications
  # ===========================================================================

  @wip
  Scenario: Response includes allow_proceeding boolean
    Given a simple orchestrator
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should have allow_proceeding field as boolean

  @wip
  Scenario: Response includes reason when blocked
    Given a simple orchestrator
    And a governance policy that denies "CHUNK_STARTED"
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should have reason field explaining why blocked

  @wip
  Scenario: Response includes approval_id when review required
    Given a simple orchestrator
    And a governance policy requiring review for "CHUNK_STARTED"
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should have approval_id field

  @wip
  Scenario: Response includes warnings list for non-blocking concerns
    Given a simple orchestrator
    And an orchestrator token budget of 500 for project "test"
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should have warnings as a list
    And warnings should contain resource warning

  # ===========================================================================
  # Warning Threshold Specifications
  # ===========================================================================

  @wip
  Scenario: Resource warning triggers at 1000 token threshold
    Given a simple orchestrator
    And an orchestrator token budget of 999 for project "test"
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should include a resource warning

  @wip
  Scenario: No resource warning when budget above 1000 tokens
    Given a simple orchestrator
    And an orchestrator token budget of 1001 for project "test"
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should not include a resource warning

  @wip
  Scenario: Resource warning does not block the action
    Given a simple orchestrator
    And an orchestrator token budget of 500 for project "test"
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should include a resource warning
    And the response should allow proceeding
