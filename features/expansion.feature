@core @graph @expansion
Feature: Thought Expansion
  As a developer using Graph of Thought
  I want to expand thoughts to generate children
  So that I can explore the solution space

  Background:
    Given a test graph with evaluator and generator

  Scenario: Expanding a thought creates children
    Given a thought "Start" exists
    When I expand the thought "Start"
    Then 3 children should be created
    And all children should have depth 1
    And the thought "Start" should have status "COMPLETED"

  Scenario: Expansion respects max depth
    Given a graph with max depth 2
    And a thought "Root" exists
    When I expand the thought "Root"
    And I expand the first child
    And I try to expand a grandchild
    Then no children should be created from the grandchild

  Scenario: Pruned thoughts do not expand
    Given a thought "Start" exists
    And the thought "Start" is marked as pruned
    When I expand the thought "Start"
    Then no children should be created
