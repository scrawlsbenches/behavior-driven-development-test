@core @persistence @serialization @high
Feature: Serialization
  As a developer using Graph of Thought
  I want to serialize and deserialize graphs
  So that I can save and restore reasoning state

  Background:
    Given a test graph with evaluator and generator

  Scenario: Serializing graph to dictionary
    Given a thought "Root" exists with score 0.5
    And a thought "Child" exists as child of "Root" with score 0.7
    When I serialize the graph to a dictionary
    Then the dictionary should contain "thoughts"
    And the dictionary should contain "edges"
    And the dictionary should contain "roots"
    And the dictionary should contain "config"
    And there should be 2 thoughts in the dictionary
    And there should be 1 edge in the dictionary

  Scenario: Deserializing graph from dictionary
    Given a thought "Root" exists with score 0.5
    And a thought "Child" exists as child of "Root" with score 0.7
    When I serialize the graph to a dictionary
    And I deserialize a graph from the dictionary
    Then the restored graph should have 2 thoughts
    And the restored graph should have the same root ids
    And the restored graph should have 1 edge

  Scenario: JSON roundtrip preserves graph structure
    Given a thought "Root" exists with score 0.5
    And a thought "Child" exists as child of "Root" with score 0.7
    When I serialize the graph to JSON
    And I deserialize a graph from the JSON
    Then the restored graph should have 2 thoughts
    And the restored graph should have the same root ids
    And the restored graph should have 1 edge

  # ===========================================================================
  # Detailed Validation (TODO: Implement step definitions)
  # ===========================================================================

  @wip
  Scenario: JSON roundtrip preserves thought scores
    Given a thought "Root" exists with score 0.5
    And a thought "Child" exists as child of "Root" with score 0.7
    When I serialize the graph to JSON
    And I deserialize a graph from the JSON
    Then the restored thought "Root" should have score 0.5
    And the restored thought "Child" should have score 0.7
