@core @search @critical
Feature: Search Algorithms
  As a developer using Graph of Thought
  I want to search through the reasoning graph
  So that I can find optimal solution paths

  Background:
    Given a test graph with evaluator and generator

  # ===========================================================================
  # Basic Search Operations
  # ===========================================================================

  Scenario: Beam search terminates with valid reason
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

  # ===========================================================================
  # Termination Reason Specifications
  # ===========================================================================

  @wip
  Scenario: Search terminates with "completed" when frontier is exhausted
    Given a graph with a single leaf thought "End"
    And a thought "Start" exists with edge to "End"
    When I run beam search
    Then the termination reason should be "completed"

  @wip
  Scenario: Search terminates with "max_depth" when depth limit reached
    Given a graph with max depth 2
    And a thought "Start" exists
    And the generator produces children at each level
    When I run beam search
    Then the termination reason should be "max_depth"

  @wip
  Scenario: Search terminates with "max_expansions" when expansion limit reached
    Given a graph with max depth 100
    And a thought "Start" exists
    When I run beam search with max expansions 3
    Then the termination reason should be "max_expansions"

  @wip
  Scenario: Search terminates with "timeout" when time limit exceeded
    Given a slow generator that takes 1 second per expansion
    And a search timeout of 2 seconds
    And a thought "Start" exists
    When I run beam search
    Then the termination reason should be "timeout"

  # ===========================================================================
  # Search Result Specifications
  # ===========================================================================

  @wip
  Scenario: Search result contains best_path as list of thoughts
    Given a thought "Start" exists
    When I run beam search
    Then the search result should have best_path
    And best_path should be a list of thought strings

  @wip
  Scenario: Search result contains expansion statistics
    Given a thought "Start" exists
    When I run beam search
    Then the search result should have stats
    And stats should include expansions_count
    And stats should include max_depth_reached

  # ===========================================================================
  # Beam Search Specifications
  # ===========================================================================

  @wip
  Scenario: Beam search keeps only top-k candidates at each depth
    Given a beam width of 2
    And a thought "Start" exists
    And the generator produces 5 children per thought
    When I run beam search
    Then at each depth only 2 candidates should be kept

  @wip
  Scenario: Beam search may miss optimal path due to pruning
    Given a beam width of 1
    And a thought "Start" with two children: high-scoring "A" and low-scoring "B"
    And "B" leads to the optimal goal path
    When I run beam search
    Then the optimal path through "B" may not be found

  # ===========================================================================
  # Best-First Search Specifications
  # ===========================================================================

  @wip
  Scenario: Best-first search always expands highest-scoring frontier node
    Given a thought "Start" with children scored 0.3, 0.7, and 0.5
    When I run best-first search
    Then the first expansion should be the thought scored 0.7
