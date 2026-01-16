Feature: Search Strategies
  As a developer using Graph of Thought
  I want to use different search strategies
  So that I can optimize for different problem types

  Scenario: MCTS strategy explores the graph
    Given a graph with length-based evaluator
    And a thought "Start" exists
    When I run MCTS search with exploration weight 1.0 and max expansions 10
    Then the search should have expanded at least 1 thought
