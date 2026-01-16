@services @collaborative
Feature: Collaborative Project
  As a developer using Graph of Thought
  I want to manage human-AI collaborative projects
  So that I can track questions, decisions, and work chunks

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
