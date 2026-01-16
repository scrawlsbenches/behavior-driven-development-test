@core @visualization @low
Feature: Visualization
  As a developer using Graph of Thought
  I want to visualize the graph
  So that I can understand the reasoning structure

  Background:
    Given a test graph with evaluator and generator

  Scenario: Text visualization shows graph structure
    Given a thought "Root" exists with score 0.5
    And a thought "Child 1" exists as child of "Root" with score 0.7
    And a thought "Child 2" exists as child of "Root" with score 0.3
    When I generate a text visualization
    Then the visualization should contain "Root"
    And the visualization should contain "Child 1"
    And the visualization should contain "Child 2"
    And the visualization should contain "[0.50]"

  Scenario: Stats method returns graph statistics
    Given a thought "Root" exists with score 0.5
    And a thought "Child" exists as child of "Root" with score 0.7
    When I get the graph stats
    Then the stats should show total_thoughts = 2
    And the stats should show total_edges = 1
    And the stats should show root_count = 1
    And the stats should show leaf_count = 1
    And the stats should show max_depth = 1
