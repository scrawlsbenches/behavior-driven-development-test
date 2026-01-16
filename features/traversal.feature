Feature: Graph Traversal
  As a developer using Graph of Thought
  I want to traverse the graph in different orders
  So that I can explore reasoning paths effectively

  Background:
    Given a test graph with evaluator and generator

  Scenario: Breadth-first traversal
    Given a thought "Root" exists
    And a thought "C1" exists as child of "Root"
    And a thought "C2" exists as child of "Root"
    And a thought "GC1" exists as child of "C1"
    When I perform a breadth-first traversal
    Then the first thought should be "Root"
    And thoughts "C1" and "C2" should come before "GC1"

  Scenario: Depth-first traversal
    Given a thought "Root" exists
    And a thought "C1" exists as child of "Root"
    And a thought "C2" exists as child of "Root"
    And a thought "GC1" exists as child of "C1"
    When I perform a depth-first traversal
    Then the first thought should be "Root"
    And "GC1" should be in the traversal

  Scenario: Getting path to root
    Given a thought "Root" exists
    And a thought "C1" exists as child of "Root"
    And a thought "GC1" exists as child of "C1"
    When I get the path to root from "GC1"
    Then the path should be "Root" -> "C1" -> "GC1"

  Scenario: Getting leaf nodes
    Given a thought "Root" exists
    And a thought "C1" exists as child of "Root"
    And a thought "C2" exists as child of "Root"
    And a thought "GC1" exists as child of "C1"
    When I get the leaf nodes
    Then the leaves should be "C2" and "GC1"

  Scenario: Getting best path by score
    Given a thought "Root" exists with score 0.0
    And a thought "C1" exists as child of "Root" with score 0.5
    And a thought "C2" exists as child of "Root" with score 0.3
    And a thought "GC1" exists as child of "C1" with score 0.9
    When I get the best path
    Then the path should be "Root" -> "C1" -> "GC1"
