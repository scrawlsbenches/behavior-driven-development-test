@core @graph @validation
Feature: Cycle Detection
  As a developer using Graph of Thought
  I want the graph to detect and prevent cycles by default
  So that I maintain a valid DAG structure for reasoning

  Background:
    Given a test graph with evaluator and generator

  Scenario: Cycles are prevented by default
    Given a thought "T1" exists
    And a thought "T2" exists as child of "T1"
    When I try to add an edge from "T2" to "T1"
    Then a CycleDetectedError should be raised

  Scenario: Self-loops are prevented
    Given a thought "T1" exists
    When I try to add an edge from "T1" to "T1"
    Then a CycleDetectedError should be raised

  Scenario: Cycles are allowed when configured
    Given a graph configured to allow cycles
    And a thought "T1" exists
    And a thought "T2" exists as child of "T1"
    When I add an edge from "T2" to "T1"
    Then an edge should exist from "T2" to "T1"
