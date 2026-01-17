@core @search @critical
Feature: Search Algorithms
  As a developer using Graph of Thought
  I want to search through the reasoning graph
  So that I can find optimal solution paths

  # ===========================================================================
  # TERMINOLOGY
  # ===========================================================================
  # SEARCH RESULT: Contains best_path (list of thoughts), termination_reason,
  #   and stats (expansions count, max depth reached, etc.)
  #
  # TERMINATION REASONS:
  #   - "completed": Search exhausted all frontier nodes (no more to expand)
  #   - "max_depth": Reached configured maximum depth limit
  #   - "max_expansions": Reached configured expansion count limit
  #   - "goal_reached": Found a thought satisfying the goal predicate
  #   - "timeout": Search exceeded time limit (if configured)
  #
  # BEAM SEARCH: Keeps top-k candidates at each depth level (k = beam_width).
  #   More memory-efficient than best-first but may miss optimal paths.
  #
  # BEST-FIRST SEARCH: Always expands highest-scoring frontier node.
  #   Finds optimal path but may use more memory.

  Background:
    Given a test graph with evaluator and generator

  Scenario: Beam search terminates with valid reason
    # Note: Exact termination reason depends on graph structure and limits.
    # This test verifies the search completes with one of the valid reasons.
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
    Then the search should have expanded at most 5 thoughts
