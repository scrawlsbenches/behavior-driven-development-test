Feature: Basic Graph Operations
  As a developer using Graph of Thought
  I want to perform basic graph operations
  So that I can build and manipulate reasoning graphs

  Background:
    Given a test graph with evaluator and generator

  Scenario: Creating an empty graph
    Given an empty graph
    Then the graph should contain 0 thoughts
    And the graph should have no root nodes
    And the graph should have no edges

  Scenario: Adding a root thought
    When I add a thought with content "Root"
    Then the graph should contain 1 thought
    And the thought "Root" should be a root node
    And the thought "Root" should have depth 0
    And the thought "Root" should have status "PENDING"

  Scenario: Adding a child thought
    Given a thought "Root" exists
    When I add a thought "Child" as child of "Root"
    Then the graph should contain 2 thoughts
    And the thought "Child" should have depth 1
    And the thought "Child" should not be a root node
    And "Root" should have "Child" as a child
    And "Child" should have "Root" as a parent

  Scenario: Adding an edge between existing thoughts
    Given a thought "T1" exists
    And a thought "T2" exists
    When I add an edge from "T1" to "T2" with relation "custom" and weight 0.5
    Then an edge should exist from "T1" to "T2"
    And the edge should have relation "custom"
    And the edge should have weight 0.5

  Scenario: Removing a thought
    Given a thought "Root" exists
    And a thought "Child" exists as child of "Root"
    When I remove the thought "Child"
    Then the graph should contain 1 thought
    And "Child" should not be in the graph
    And "Root" should have no children

  Scenario: Removing an edge
    Given a thought "Root" exists
    And a thought "Child" exists as child of "Root"
    When I remove the edge from "Root" to "Child"
    Then "Root" should have no children
    And "Child" should have no parents

  Scenario: Getting a nonexistent thought raises error
    When I try to get thought "nonexistent"
    Then a NodeNotFoundError should be raised

  Scenario: Checking if thought exists in graph
    Given a thought "Test" exists
    Then "Test" should be in the graph
    And "nonexistent" should not be in the graph
