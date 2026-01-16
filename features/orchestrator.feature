Feature: Service Orchestrator
  As a developer using Graph of Thought
  I want to use the orchestrator to coordinate services
  So that I can manage cross-cutting concerns like governance and resources

  Scenario: Creating orchestrator with null services
    Given a default orchestrator
    Then the orchestrator should have governance service
    And the orchestrator should have resource service
    And the orchestrator should have knowledge service

  Scenario: Creating orchestrator with simple services
    Given a simple orchestrator
    Then the orchestrator should use simple implementations

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

  Scenario: Resource warnings when budget is low
    Given a simple orchestrator
    And an orchestrator token budget of 500 for project "test"
    When I handle a CHUNK_STARTED event for project "test" chunk "chunk1"
    Then the response should include a resource warning

  Scenario: Recording resource consumption on chunk completion
    Given a simple orchestrator
    And an orchestrator token budget of 10000 for project "test"
    When I handle a CHUNK_COMPLETED event for project "test" with 1000 tokens used
    Then the token consumption should be recorded

  Scenario: Capturing answers as knowledge
    Given a simple orchestrator
    When I handle a QUESTION_ANSWERED event with question "How to auth?" and answer "Use OAuth2"
    Then a knowledge entry should be created for the answer

  Scenario: Routing questions through the orchestrator
    Given a simple orchestrator
    When I handle a QUESTION_ASKED event with question "What are the security requirements?"
    Then the response should indicate routing to "security-team"

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
