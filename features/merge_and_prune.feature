Feature: Merge and Prune Operations
  As a developer using Graph of Thought
  I want to merge and prune thoughts
  So that I can synthesize ideas and remove low-quality paths

  Background:
    Given a test graph with evaluator and generator

  Scenario: Merging thoughts creates a synthesis
    Given a thought "T1" exists with score 0.5
    And a thought "T2" exists with score 0.7
    When I merge thoughts "T1" and "T2" into "Merged" with score 0.8
    Then the merged thought should have content "Merged"
    And the merged thought should have score 0.8
    And the merged thought should have depth 1
    And the thought "T1" should have status "MERGED"
    And the thought "T2" should have status "MERGED"
    And "T1" should be a parent of the merged thought
    And "T2" should be a parent of the merged thought

  Scenario: Merging empty list raises error
    When I try to merge an empty list of thoughts
    Then a GraphError should be raised

  Scenario: Pruning marks low-scoring thoughts
    Given a thought "T1" exists with score 0.3
    And a thought "T2" exists with score 0.7
    And a thought "T3" exists with score 0.1
    When I prune thoughts below threshold 0.5
    Then 2 thoughts should be pruned
    And the thought "T1" should have status "PRUNED"
    And the thought "T2" should have status "PENDING"
    And the thought "T3" should have status "PRUNED"

  Scenario: Prune and remove deletes low-scoring thoughts
    Given a thought "T1" exists with score 0.3
    And a thought "T2" exists with score 0.7
    When I prune and remove thoughts below threshold 0.5
    Then 1 thought should be removed
    And "T1" should not be in the graph
    And "T2" should be in the graph
