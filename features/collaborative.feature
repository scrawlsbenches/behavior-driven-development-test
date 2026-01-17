@services @collaborative @high
Feature: Collaborative Project
  As a developer using Graph of Thought
  I want to manage human-AI collaborative projects
  So that I can track questions, decisions, and work chunks

  # ===========================================================================
  # Project and Node Creation
  # ===========================================================================

  Scenario: Creating a new project with a request
    Given a new collaborative project named "test_project"
    When I add a request "Build a REST API"
    Then the project should have 1 node
    And the node should be of type "REQUEST"
    And the node should have content "Build a REST API"

  Scenario: Asking a blocking question
    Given a collaborative project with a request "Build a CMS"
    When I ask a blocking question "Multi-tenant or single-tenant?"
    Then the project should have 2 nodes
    And there should be a question with priority "BLOCKING"

  Scenario: Planning a work chunk
    Given a collaborative project with a request "Build a CMS"
    When I plan a chunk "Core models" with estimated hours 3
    Then a chunk should be created with status "READY"
    And the chunk should have estimated hours 3

  Scenario: Starting a chunk creates a session
    Given a collaborative project with a request "Build a CMS"
    And a ready chunk "Core models" exists
    When I start chunk "Core models"
    Then a session should be active
    And the chunk should have status "IN_PROGRESS"

  # ===========================================================================
  # Node Type Specifications
  # ===========================================================================

  @wip
  Scenario: Adding a decision node to record architectural choices
    Given a collaborative project with a request "Build a CMS"
    When I record a decision "Use PostgreSQL for persistence"
    Then the project should have 2 nodes
    And there should be a node of type "DECISION"
    And the decision should have content "Use PostgreSQL for persistence"

  @wip
  Scenario: Questions link to the nodes they block
    Given a collaborative project with a request "Build a CMS"
    And a ready chunk "Database setup" exists
    When I ask a blocking question "PostgreSQL or MySQL?" for chunk "Database setup"
    Then the question should be linked to chunk "Database setup"
    And chunk "Database setup" should have status "BLOCKED"

  # ===========================================================================
  # Chunk Status Transitions
  # ===========================================================================

  @wip
  Scenario: Completing a chunk transitions status to COMPLETED
    Given a collaborative project with a request "Build a CMS"
    And an in-progress chunk "Core models" exists
    When I complete chunk "Core models"
    Then the chunk should have status "COMPLETED"
    And the session should be ended

  @wip
  Scenario: Answering a blocking question unblocks the chunk
    Given a collaborative project with a request "Build a CMS"
    And a blocked chunk "Database setup" waiting on question "PostgreSQL or MySQL?"
    When I answer question "PostgreSQL or MySQL?" with "PostgreSQL"
    Then chunk "Database setup" should have status "READY"

  @wip
  Scenario: Only one session can be active per chunk
    Given a collaborative project with a request "Build a CMS"
    And an in-progress chunk "Core models" with an active session
    When I try to start another session for chunk "Core models"
    Then an error should be raised indicating a session is already active

  # ===========================================================================
  # Session Lifecycle
  # ===========================================================================

  @wip
  Scenario: Interrupting a session creates a handoff package
    Given a collaborative project with a request "Build a CMS"
    And an in-progress chunk "Core models" with an active session
    When I interrupt the session for chunk "Core models"
    Then a handoff package should be created
    And the session should be ended
    And the chunk should have status "READY"

  @wip
  Scenario: Sessions track elapsed time
    Given a collaborative project with a request "Build a CMS"
    And a ready chunk "Core models" exists
    When I start chunk "Core models"
    And I wait 5 seconds
    And I complete chunk "Core models"
    Then the session duration should be at least 5 seconds
