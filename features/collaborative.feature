@services @collaborative @high
Feature: Collaborative Project
  As a developer using Graph of Thought
  I want to manage human-AI collaborative projects
  So that I can track questions, decisions, and work chunks

  # ===========================================================================
  # TERMINOLOGY
  # ===========================================================================
  # PROJECT: A graph-based representation of work. Contains nodes for requests,
  #   questions, decisions, and chunks connected by relationships.
  #
  # NODE TYPES:
  #   - REQUEST: Initial work request (e.g., "Build a REST API")
  #   - QUESTION: Something that needs answering before work can proceed
  #   - DECISION: A choice that was made (stored for future reference)
  #   - CHUNK: A unit of work that can be executed in a session
  #
  # CHUNK STATUSES:
  #   - READY: Chunk is planned and can be started
  #   - IN_PROGRESS: Chunk is currently being worked on in an active session
  #   - COMPLETED: Chunk work is finished
  #   - BLOCKED: Chunk cannot proceed (e.g., waiting for question answer)
  #
  # SESSION: An active work period on a chunk. One session per chunk at a time.
  #   Sessions track time, context, and produce handoffs when interrupted.

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
