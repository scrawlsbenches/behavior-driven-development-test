Feature: Search Algorithms
  As a developer using Graph of Thought
  I want to search through the reasoning graph
  So that I can find optimal solution paths

  Background:
    Given a test graph with evaluator and generator

  Scenario: Beam search finds a path
    Given a thought "Start" exists
    When I run beam search
    Then the search should return a result
    And the search should have expanded at least 1 thought
    And the best path should have at least 1 thought
    And the termination reason should be one of "completed", "max_depth", "max_expansions"

  Scenario: Best-first search finds a path
    Given a thought "Start" exists
    When I run best-first search
    Then the search should return a result
    And the search should have expanded at least 1 thought

  Scenario: Goal-directed search reaches goal
    Given a graph with goal-directed generator and evaluator
    And a thought "Start" exists
    When I run beam search with goal predicate for "GOAL"
    Then the termination reason should be "goal_reached"
    And the best path should end with a thought containing "GOAL"

  Scenario: Search respects max depth
    Given a graph with max depth 3
    And a thought "Start" exists
    When I run beam search
    Then all thoughts should have depth at most 3

  Scenario: Search respects max expansions
    Given a graph with max depth 10
    And a thought "Start" exists
    When I run beam search with max expansions 5
    Then the search should have expanded at most 10 thoughts
