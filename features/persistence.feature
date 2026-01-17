@core @persistence @storage @high
Feature: Persistence
  As a developer using Graph of Thought
  I want to persist graphs to storage
  So that I can resume long-running reasoning tasks

  # ===========================================================================
  # Graph Save/Load Operations (Scenario Outline)
  # ===========================================================================
  # Consolidated from separate in-memory and file persistence scenarios
  # to reduce duplication and improve maintainability.

  Scenario Outline: Saving and loading graph with <backend> persistence
    Given a <backend> persistence backend
    And a test graph with evaluator and generator
    And a thought "Root" exists with score 0.5
    When I save the graph with id "<graph_id>" and metadata "<meta_key>" = <meta_value>
    And I load the graph with id "<graph_id>"
    Then the loaded graph should have <thought_count> thoughts
    And the loaded metadata should have "<meta_key>" = <meta_value>

  Examples:
    | backend   | graph_id   | meta_key | meta_value | thought_count |
    | in-memory | test       | test     | True       | 1             |
    | file      | test_graph | version  | "1.0"      | 1             |

  # ===========================================================================
  # Checkpoint Operations (Scenario Outline)
  # ===========================================================================

  Scenario Outline: Checkpoint roundtrip with <backend> persistence
    Given a <backend> persistence backend
    And a test graph with evaluator and generator
    And a thought "Root" exists
    When I save a checkpoint with id "<checkpoint_id>" and search state "<state_key>" = <state_value>
    And I load the checkpoint "<checkpoint_id>"
    Then the loaded search state should have "<state_key>" = <state_value>

  Examples:
    | backend   | checkpoint_id | state_key     | state_value |
    | in-memory | cp1           | current_depth | 3           |
    | file      | checkpoint_1  | beam_width    | 5           |

  # ===========================================================================
  # Delete Operations (Scenario Outline)
  # ===========================================================================

  Scenario Outline: Deleting a graph with <backend> persistence
    Given a <backend> persistence backend
    And a test graph with evaluator and generator
    And a thought "Root" exists
    When I save the graph with id "<graph_id>" and metadata "test" = True
    And I delete the graph with id "<graph_id>"
    Then loading graph "<graph_id>" should return nothing

  Examples:
    | backend   | graph_id  |
    | in-memory | test      |
    | file      | to_delete |

  # ===========================================================================
  # Loading Non-Existent Resources
  # ===========================================================================
  # These scenarios have different step definitions and cannot be easily
  # consolidated into a single Scenario Outline without step definition changes.

  Scenario: Loading non-existent graph returns nothing
    Given a file persistence backend
    When I try to load graph "non_existent"
    Then the load result should be nothing

  Scenario: Loading non-existent checkpoint returns nothing
    Given a file persistence backend
    When I try to load checkpoint "no_such_checkpoint" for graph "test"
    Then the checkpoint load result should be nothing

  # ===========================================================================
  # File-Specific Scenarios (Cannot be consolidated)
  # ===========================================================================

  Scenario: File persistence creates JSON files
    Given a file persistence backend
    And a test graph with evaluator and generator
    And a thought "Root" exists
    When I save the graph with id "my_graph" and metadata "test" = True
    Then a JSON file should exist for graph "my_graph"

  Scenario: File persistence graph with multiple thoughts
    Given a file persistence backend
    And a test graph with evaluator and generator
    And a thought "Root" exists with score 0.5
    And a thought "Child" exists as child of "Root" with score 0.7
    When I save the graph with id "multi_thought" and metadata "version" = "1.0"
    And I load the graph with id "multi_thought"
    Then the loaded graph should have 2 thoughts
    And the loaded metadata should have "version" = "1.0"

  Scenario: Deleting file-persisted graph removes JSON file
    Given a file persistence backend
    And a test graph with evaluator and generator
    And a thought "Root" exists
    When I save the graph with id "json_delete" and metadata "test" = True
    And I delete the graph with id "json_delete"
    Then loading graph "json_delete" should return nothing
    And the JSON file for "json_delete" should not exist
