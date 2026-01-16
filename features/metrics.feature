Feature: Metrics Collection
  As a developer using Graph of Thought
  I want to collect metrics about graph operations
  So that I can monitor and optimize performance

  Scenario: In-memory metrics collector records values
    Given an in-memory metrics collector
    When I increment counter "counter" by 5
    And I set gauge "gauge" to 10.5
    And I record histogram value 1.0 for "histogram"
    And I record histogram value 2.0 for "histogram"
    And I record timing 100.0 for "timing"
    Then counter "counter" should be 5
    And gauge "gauge" should be 10.5
    And histogram "histogram" should contain values 1.0 and 2.0
    And timing "timing" should contain 100.0

  Scenario: Metrics with tags
    Given an in-memory metrics collector
    When I increment counter "counter" by 1 with tag "env" = "test"
    Then counter "counter[env=test]" should be 1

  Scenario: Graph collects metrics during operations
    Given an in-memory metrics collector
    And a test graph with the metrics collector
    And a thought "Root" exists
    When I expand the thought "Root"
    Then counter "thoughts.added" should be greater than 0
    And counter "thoughts.expanded" should be greater than 0
