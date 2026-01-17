@services @resources @high
Feature: Resource Service
  As a developer using Graph of Thought
  I want a resource service to manage budgets and consumption
  So that I can track and control resource usage in my projects

  # ===========================================================================
  # TERMINOLOGY
  # ===========================================================================
  # This feature tests TWO implementations:
  #
  # 1. IN-MEMORY RESOURCE SERVICE (test double)
  #    - Returns unlimited resources for any project
  #    - Use when you need isolated tests without resource tracking
  #
  # 2. SIMPLE RESOURCE SERVICE (lightweight implementation)
  #    - Tracks budgets, consumption, and enforces limits
  #    - Use when testing actual resource management behavior

  # ===========================================================================
  # In-Memory Resource Service (Test Double)
  # ===========================================================================

  Scenario: In-memory resource service has unlimited resources
    Given an in-memory resource service
    When I check available tokens for project "test"
    Then resources should be available
    And remaining resources should be infinite

  # ===========================================================================
  # Simple Resource Service
  # ===========================================================================

  Scenario: Simple resource service tracks budgets
    Given a simple resource service
    When I set a token budget of 10000 for project "test_project"
    Then the token budget for project "test_project" should be 10000

  Scenario: Simple resource service tracks consumption
    Given a simple resource service
    And a token budget of 10000 for project "test_project"
    When I consume 500 tokens for project "test_project"
    Then the remaining tokens for project "test_project" should be 9500

  Scenario: Simple resource service blocks over-budget consumption
    Given a simple resource service
    And a token budget of 100 for project "test_project"
    When I try to consume 150 tokens for project "test_project"
    Then the consumption should be rejected

  Scenario: Simple resource service generates consumption reports
    Given a simple resource service
    And a token budget of 10000 for project "test_project"
    When I consume 500 tokens for project "test_project" with description "Chunk 1"
    And I consume 300 tokens for project "test_project" with description "Chunk 2"
    And I get the consumption report for project "test_project"
    Then the report should show 2 consumption events
    And the report should show 800 total tokens consumed

  # ===========================================================================
  # Future Capabilities
  # ===========================================================================

  @wip
  Scenario: Resource service filters consumption report by date range
    Given a simple resource service
    And a token budget of 10000 for project "test_project"
    And consumption of 500 tokens on "2024-01-01"
    And consumption of 300 tokens on "2024-01-15"
    And consumption of 200 tokens on "2024-02-01"
    When I get the consumption report from "2024-01-01" to "2024-01-31"
    Then the report should show 2 consumption events
    And the report should show 800 total tokens consumed

  @wip
  Scenario: Resource service warns when approaching budget limit
    Given a simple resource service
    And a token budget of 1000 for project "test_project"
    And a warning threshold at 80 percent
    When I consume 850 tokens for project "test_project"
    Then a budget warning should be issued
    And the consumption should succeed

  @wip
  Scenario: Authorized user can override budget limit
    Given a simple resource service
    And a token budget of 100 for project "test_project"
    And user "admin" has budget override permission
    When "admin" overrides budget to consume 150 tokens for project "test_project"
    Then the consumption should succeed
    And an audit entry should record the override

  @wip
  Scenario: Resource allocation considers project priority dynamically
    Given a simple resource service
    And project "critical" with deadline in 1 day
    And project "normal" with deadline in 30 days
    When both projects request 500 tokens with only 600 available
    Then project "critical" should receive tokens first

  @wip
  Scenario: Resource service projects budget exhaustion timeline
    Given a simple resource service
    And a token budget of 10000 for project "test_project"
    And historical consumption of 500 tokens per day for 5 days
    When I request a timeline projection for project "test_project"
    Then the projection should estimate exhaustion in 10 days

  @wip
  Scenario: Resource service persists budgets across restarts
    Given a simple resource service with database persistence
    And a token budget of 10000 for project "test_project"
    And consumption of 500 tokens for project "test_project"
    When the service restarts
    Then the token budget for project "test_project" should be 10000
    And the remaining tokens for project "test_project" should be 9500

  @wip
  Scenario: Resource service enforces hierarchical budget limits
    Given a simple resource service
    And organization "acme" with budget of 100000 tokens
    And team "engineering" under "acme" with budget of 50000 tokens
    And project "test_project" under "engineering" with budget of 10000 tokens
    When I try to consume 60000 tokens for project "test_project"
    Then the consumption should be rejected
    And the rejection should mention team budget exceeded

  @wip
  Scenario: Parent budget consumption rolls up from children
    Given a simple resource service
    And organization "acme" with budget of 100000 tokens
    And team "engineering" under "acme" with budget of 50000 tokens
    And project "project_a" under "engineering" with budget of 10000 tokens
    And project "project_b" under "engineering" with budget of 10000 tokens
    When I consume 5000 tokens for project "project_a"
    And I consume 3000 tokens for project "project_b"
    Then the team "engineering" remaining budget should be 42000 tokens
    And the organization "acme" remaining budget should be 92000 tokens

  # ===========================================================================
  # Known Limitations (Escape Clauses)
  # ===========================================================================
  # ESCAPE CLAUSE: Budgets reset on restart.
  # Current: All budget state is in-memory.
  # Requires: Database persistence (PostgreSQL/Redis) for budget state.
  #
  # ESCAPE CLAUSE: No parent budget checks.
  # Current: Each scope's budget is independent.
  # Requires: Hierarchical budgets (org -> team -> project -> task).
  #
  # ESCAPE CLAUSE: Hard stop at budget.
  # Current: Consumption fails immediately when budget exceeded.
  # Requires: Soft limits with warnings, grace periods, override capability.
