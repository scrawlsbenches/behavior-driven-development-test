@observability @metrics @testing @high
Feature: In-Memory Metrics Collector
  As a developer testing Graph of Thought
  I want an in-memory metrics collector
  So that I can verify metrics are recorded correctly in tests

  # This collector is designed for testing and development, NOT production.
  # For production metrics, implement a PrometheusMetricsCollector or similar.

  Background:
    Given an in-memory metrics collector

  # ===========================================================================
  # Counter Operations
  # ===========================================================================

  Scenario: Counter starts at zero
    Then the counter "requests" should equal 0

  Scenario: Counter increments by specified value
    When I increment counter "requests" by 5
    Then the counter "requests" should equal 5

  Scenario: Counter accumulates multiple increments
    When I increment counter "requests" by 5
    And I increment counter "requests" by 3
    Then the counter "requests" should equal 8

  Scenario Outline: Counter with <tag_type> tags creates separate metrics
    When I increment counter "requests" by <value1> with tags <tags1>
    And I increment counter "requests" by <value2> with tags <tags2>
    Then the counter "requests" with tags <tags1> should equal <value1>
    And the counter "requests" with tags <tags2> should equal <value2>

  Examples:
    | tag_type | value1 | value2 | tags1                           | tags2                            |
    | single   | 1      | 2      | endpoint="users"                | endpoint="orders"                |
    | multiple | 1      | 3      | endpoint="users", method="GET"  | endpoint="users", method="POST"  |

  # ===========================================================================
  # Gauge Operations
  # ===========================================================================

  Scenario: Gauge sets current value
    When I set gauge "temperature" to 72.5
    Then the gauge "temperature" should equal 72.5

  Scenario: Gauge overwrites previous value
    When I set gauge "queue_size" to 10
    And I set gauge "queue_size" to 5
    Then the gauge "queue_size" should equal 5

  Scenario: Gauge with tags creates separate metrics
    When I set gauge "connections" to 100 with tags server="primary"
    And I set gauge "connections" to 50 with tags server="replica"
    Then the gauge "connections" with tags server="primary" should equal 100
    And the gauge "connections" with tags server="replica" should equal 50

  # ===========================================================================
  # Histogram Operations
  # ===========================================================================

  Scenario: Histogram records single value
    When I record histogram "response_size" with value 1024
    Then the histogram "response_size" should contain 1 value
    And the histogram "response_size" should contain value 1024

  Scenario: Histogram accumulates multiple values
    When I record histogram "response_size" with value 100
    And I record histogram "response_size" with value 200
    And I record histogram "response_size" with value 300
    Then the histogram "response_size" should contain 3 values
    And the histogram "response_size" values should be [100, 200, 300]

  Scenario: Histogram with tags creates separate metrics
    When I record histogram "latency" with value 50 with tags endpoint="fast"
    And I record histogram "latency" with value 500 with tags endpoint="slow"
    Then the histogram "latency" with tags endpoint="fast" should contain value 50
    And the histogram "latency" with tags endpoint="slow" should contain value 500

  # ===========================================================================
  # Timing Operations
  # ===========================================================================

  Scenario: Timing records single duration
    When I record timing "request_duration" with 150.5 ms
    Then the timing "request_duration" should contain 1 value
    And the timing "request_duration" should contain value 150.5

  Scenario: Timing accumulates multiple durations
    When I record timing "db_query" with 10.0 ms
    And I record timing "db_query" with 20.0 ms
    And I record timing "db_query" with 30.0 ms
    Then the timing "db_query" should contain 3 values

  Scenario: Timing with tags creates separate metrics
    When I record timing "api_call" with 100.0 ms with tags service="auth"
    And I record timing "api_call" with 200.0 ms with tags service="data"
    Then the timing "api_call" with tags service="auth" should contain value 100.0
    And the timing "api_call" with tags service="data" should contain value 200.0

  # ===========================================================================
  # Query Operations
  # ===========================================================================

  Scenario Outline: List all <metric_type> names
    When I <setup_operation1>
    And I <setup_operation2>
    Then the collector should have <metric_type>s <expected_list>

  Examples:
    | metric_type | setup_operation1               | setup_operation2              | expected_list          |
    | counter     | increment counter "requests" by 1 | increment counter "errors" by 1 | ["errors", "requests"] |
    | gauge       | set gauge "memory" to 1024     | set gauge "cpu" to 50         | ["cpu", "memory"]      |

  Scenario: Check if metric exists
    When I increment counter "requests" by 1
    Then the collector should have counter "requests"
    And the collector should not have counter "errors"

  # ===========================================================================
  # Reset Operations
  # ===========================================================================

  Scenario: Reset clears all metrics
    Given I increment counter "requests" by 100
    And I set gauge "connections" to 50
    And I record histogram "latency" with value 100
    And I record timing "duration" with 50.0 ms
    When I reset all metrics
    Then the counter "requests" should equal 0
    And the gauge "connections" should equal 0
    And the histogram "latency" should contain 0 values
    And the timing "duration" should contain 0 values

  @wip
  Scenario: Reset individual counter
    Given I increment counter "requests" by 100
    And I increment counter "errors" by 10
    When I reset counter "requests"
    Then the counter "requests" should equal 0
    And the counter "errors" should equal 10

  @wip
  Scenario: Reset individual gauge
    Given I set gauge "memory" to 1024
    And I set gauge "cpu" to 50
    When I reset gauge "memory"
    Then the gauge "memory" should equal 0
    And the gauge "cpu" should equal 50

  # ===========================================================================
  # Edge Cases
  # ===========================================================================

  Scenario: Increment with default value of 1
    When I increment counter "events"
    Then the counter "events" should equal 1

  Scenario: Empty collector has no metrics
    Then the collector should have counters []
    And the collector should have gauges []

  Scenario: Tags are sorted for consistent keys
    When I increment counter "requests" by 1 with tags z="last", a="first"
    And I increment counter "requests" by 2 with tags a="first", z="last"
    Then the counter "requests" with tags a="first", z="last" should equal 3
