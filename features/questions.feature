@services @questions @high
Feature: Question Service
  As a developer using Graph of Thought
  I want a question service to manage questions and answers
  So that I can route questions to the right people and track responses

  Background:
    Given a simple question service

  # ===========================================================================
  # Question Lifecycle
  # ===========================================================================

  Scenario: Question service creates tickets with status and priority
    When I ask a question "Should we use GraphQL?" with priority "HIGH"
    Then a question ticket should be created
    And the ticket should have status "open"
    And the ticket should have priority "HIGH"

  Scenario: Question service routes questions containing "security" to security team
    When I ask a question "What are the security requirements?"
    Then the question should be routed to "security-team"

  Scenario: Question service routes business questions to product owner
    When I ask a question "Should we add this feature?"
    Then the question should be routed to "product-owner"

  Scenario: Question service records answers from experts
    Given a pending question "What database?"
    When I provide answer "PostgreSQL" from "architect"
    Then the ticket should have status "answered"
    And the ticket should have answer "PostgreSQL"

  Scenario: Question service returns pending questions by priority
    Given a question "Low priority question" with priority "LOW"
    And a question "Critical question" with priority "CRITICAL"
    When I get pending questions
    Then the first question should have priority "CRITICAL"

  # ===========================================================================
  # Future Capabilities
  # ===========================================================================

  @wip
  Scenario: Question service auto-answers from knowledge base
    Given a knowledge base with entry "We use PostgreSQL for all projects"
    When I ask a question "What database do we use?"
    And the confidence threshold is 0.8
    Then the question should be auto-answered
    And the answer should reference the knowledge base entry
    And the confidence should be above 0.8

  @wip
  Scenario: Question service detects duplicate questions
    Given a previously answered question "What database should we use?"
    When I ask a question "Which database should we use?"
    Then the service should suggest the existing answer
    And offer to create a new ticket if unsatisfied

  @wip
  Scenario: Question service tracks SLA compliance
    Given an SLA of 4 hours for HIGH priority questions
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
  # Routing Keyword Specifications
  # ===========================================================================

  @wip
  Scenario: Questions containing "feature" route to product owner
    When I ask a question "What feature should we prioritize?"
    Then the question should be routed to "product-owner"

  @wip
  Scenario: Questions containing "business" route to product owner
    When I ask a question "What are the business requirements?"
    Then the question should be routed to "product-owner"

  @wip
  Scenario: Questions without routing keywords route to human for triage
    When I ask a question "How do we implement caching?"
    Then the question should be routed to "human"

  # ===========================================================================
  # Priority Level Ordering
  # ===========================================================================

  @wip
  Scenario: Priority ordering is CRITICAL > BLOCKING > HIGH > MEDIUM > LOW
    Given a question "Q1" with priority "LOW"
    And a question "Q2" with priority "MEDIUM"
    And a question "Q3" with priority "HIGH"
    And a question "Q4" with priority "BLOCKING"
    And a question "Q5" with priority "CRITICAL"
    When I get pending questions
    Then the questions should be ordered "Q5", "Q4", "Q3", "Q2", "Q1"

  @wip
  Scenario: Questions default to MEDIUM priority when not specified
    When I ask a question "What library should we use?"
    Then the ticket should have priority "MEDIUM"

  # ===========================================================================
  # Ticket Status Transitions
  # ===========================================================================

  @wip
  Scenario: Ticket status transitions from open to answered
    Given a pending question "What database?" with status "open"
    When I provide answer "PostgreSQL" from "architect"
    Then the ticket should have status "answered"

  @wip
  Scenario: Answered tickets cannot be answered again
    Given an answered question "What database?" with answer "PostgreSQL"
    When I try to provide another answer "MySQL" from "developer"
    Then an error should be raised indicating the question is already answered
