Feature: Persistence
  As a developer using Graph of Thought
  I want to persist graphs to storage
  So that I can resume long-running reasoning tasks

  Scenario: Saving and loading graph with in-memory persistence
    Given an in-memory persistence backend
    And a test graph with evaluator and generator
    And a thought "Root" exists with score 0.5
    When I save the graph with id "test" and metadata "test" = True
    And I load the graph with id "test"
    Then the loaded graph should have 1 thought
    And the loaded metadata should have "test" = True

  Scenario: Saving and loading checkpoint
    Given an in-memory persistence backend
    And a test graph with evaluator and generator
    And a thought "Root" exists
    When I save a checkpoint with id "cp1" and search state "current_depth" = 3
    And I load the checkpoint "cp1"
    Then the loaded search state should have "current_depth" = 3

  Scenario: Deleting a graph
    Given an in-memory persistence backend
    When I save a graph with id "test"
    And I delete the graph with id "test"
    Then loading graph "test" should return nothing
