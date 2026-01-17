@services @questions @high
Feature: Question Service
  As a developer using Graph of Thought
  I want a question service to manage questions and answers
  So that I can route questions to the right people and track responses

  # The question service manages the lifecycle of questions: creation, routing,
  # answering, and priority management. Questions can be routed to teams
  # based on keywords or auto-answered from a knowledge base.

  # ===========================================================================
  # Simple Question Service
  # ===========================================================================

  Scenario: Question service creates tickets with status and priority
    Given a simple question service
    When I ask a question "Should we use GraphQL?" with priority "HIGH"
    Then a question ticket should be created
    And the ticket should have status "open"
    And the ticket should have priority "HIGH"

  Scenario: Question service routes questions to security team
    Given a simple question service
    When I ask a question "What are the security requirements?"
    Then the question should be routed to "security-team"

  Scenario: Question service routes business questions to product owner
    Given a simple question service
    When I ask a question "Should we add this feature?"
    Then the question should be routed to "product-owner"

  Scenario: Question service records answers from experts
    Given a simple question service
    And a pending question "What database?"
    When I provide answer "PostgreSQL" from "architect"
    Then the ticket should have status "answered"
    And the ticket should have answer "PostgreSQL"

  Scenario: Question service returns pending questions by priority
    Given a simple question service
    And a question "Low priority question" with priority "LOW"
    And a question "Critical question" with priority "CRITICAL"
    When I get pending questions
    Then the first question should have priority "CRITICAL"

  # ===========================================================================
  # Future Capabilities
  # ===========================================================================

  @wip
  Scenario: Question service auto-answers from knowledge base
    Given a simple question service
    And a knowledge base with entry "We use PostgreSQL for all projects"
    When I ask a question "What database do we use?"
    And the confidence threshold is 0.8
    Then the question should be auto-answered
    And the answer should reference the knowledge base entry
    And the confidence should be above 0.8

  @wip
  Scenario: Question service detects duplicate questions
    Given a simple question service
    And a previously answered question "What database should we use?"
    When I ask a question "Which database should we use?"
    Then the service should suggest the existing answer
    And offer to create a new ticket if unsatisfied

  @wip
  Scenario: Question service tracks SLA compliance
    Given a simple question service
    And an SLA of 4 hours for HIGH priority questions
    And a HIGH priority question asked 5 hours ago without answer
    When I check SLA compliance
    Then the question should be flagged as SLA violation

  @wip
  Scenario: Question service uses ML-based routing
    Given a simple question service with ML classifier
    And historical routing data showing "database" questions go to "dba-team"
    When I ask a question "Should we add an index to the users table?"
    Then the classifier should analyze the question context
    And route to "dba-team" based on learned patterns
    And the confidence should be above 0.7

  @wip
  Scenario: Question service balances load across teams
    Given a simple question service with load balancing
    And team "backend-team" with 5 pending questions
    And team "frontend-team" with 2 pending questions
    When I ask a general development question "How should we structure this feature?"
    Then the question should be routed considering team workload
    And prefer teams with lower pending question counts

  # ===========================================================================
  # Known Limitations (Escape Clauses)
  # ===========================================================================
  # ESCAPE CLAUSE: Routing is naive.
  # Current: Keyword matching routes to teams, default is "human".
  # Requires: ML classifier, context-aware routing, load balancing.
  #
  # ESCAPE CLAUSE: Auto-answer always returns False.
  # Current: can_auto_answer() always returns False.
  # Requires: Knowledge base integration, confidence thresholds.
  #
  # ESCAPE CLAUSE: No confidence scoring for auto-answers.
  # Current: Not applicable since auto-answer disabled.
  # Requires: LLM-based answer generation with confidence estimation.
