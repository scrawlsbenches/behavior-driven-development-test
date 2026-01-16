Feature: Persistence
  As a developer using Graph of Thought
  I want to persist graphs to storage
  So that I can resume long-running reasoning tasks

  # In-Memory Persistence

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

  # File Persistence

  Scenario: Saving and loading graph with file persistence
    Given a file persistence backend
    And a test graph with evaluator and generator
    And a thought "Root" exists with score 0.5
    And a thought "Child" exists as child of "Root" with score 0.7
    When I save the graph with id "test_graph" and metadata "version" = "1.0"
    And I load the graph with id "test_graph"
    Then the loaded graph should have 2 thoughts
    And the loaded metadata should have "version" = "1.0"

  Scenario: File persistence creates JSON files
    Given a file persistence backend
    And a test graph with evaluator and generator
    And a thought "Root" exists
    When I save the graph with id "my_graph" and metadata "test" = True
    Then a JSON file should exist for graph "my_graph"

  Scenario: File persistence checkpoint roundtrip
    Given a file persistence backend
    And a test graph with evaluator and generator
    And a thought "Root" exists
    When I save a checkpoint with id "checkpoint_1" and search state "beam_width" = 5
    And I load the checkpoint "checkpoint_1"
    Then the loaded search state should have "beam_width" = 5

  Scenario: Deleting a file-persisted graph
    Given a file persistence backend
    And a test graph with evaluator and generator
    And a thought "Root" exists
    When I save the graph with id "to_delete" and metadata "test" = True
    And I delete the graph with id "to_delete"
    Then loading graph "to_delete" should return nothing
    And the JSON file for "to_delete" should not exist

  Scenario: Loading non-existent graph returns nothing
    Given a file persistence backend
    When I try to load graph "non_existent"
    Then the load result should be nothing

  Scenario: Loading non-existent checkpoint returns nothing
    Given a file persistence backend
    When I try to load checkpoint "no_such_checkpoint" for graph "test"
    Then the checkpoint load result should be nothing
