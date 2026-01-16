Feature: Search Strategies
  As a developer using Graph of Thought
  I want to use different search strategies
  So that I can optimize for different problem types

  Scenario: MCTS strategy explores the graph
    Given a graph with length-based evaluator
    And a thought "Start" exists
    When I run MCTS search with exploration weight 1.0 and max expansions 10
    Then the search should have expanded at least 1 thought

  Scenario: Beam search strategy keeps top candidates
    Given a graph with length-based evaluator
    And a thought "Start" exists
    When I run beam search strategy with beam width 3 and max expansions 10
    Then the search should have expanded at least 1 thought
    And the search should return a result

  Scenario: Beam search strategy respects timeout
    Given a graph with slow evaluator
    And a thought "Start" exists
    When I run beam search strategy with timeout 0.1 seconds
    Then the termination reason should be "timeout"

  Scenario: Iterative deepening gradually increases depth
    Given a graph with length-based evaluator
    And a thought "Start" exists
    When I run iterative deepening search with max depth 3
    Then the search should have expanded at least 1 thought
    And the search should return a result

  Scenario: Beam search strategy reaches goal
    Given a graph with goal-reaching generator
    And a thought "Start" exists
    When I run beam search strategy with goal predicate
    Then the termination reason should be "goal_reached"

  Scenario: MCTS balances exploration and exploitation
    Given a graph with varied score evaluator
    And a thought "Start" exists
    When I run MCTS search with exploration weight 2.0 and max expansions 20
    Then the search should have expanded at least 5 thoughts
