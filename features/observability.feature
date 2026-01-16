Feature: Observability
  As a developer using Graph of Thought
  I want to use observability utilities for logging and metrics
  So that I can monitor and debug my application

  # Logging Setup

  Scenario: Setting up basic logging
    When I set up logging with level INFO
    Then a logger should be configured
    And the logger should have level INFO

  Scenario: Setting up logging with custom format
    When I set up logging with format "%(name)s - %(message)s"
    Then the logger should use the custom format

  Scenario: Setting up logging with custom logger name
    When I set up logging with name "my_app"
    Then the logger should have name "my_app"

  # Timed Decorator

  Scenario: Timed decorator measures sync function execution
    Given a sync function decorated with @timed
    When I call the function
    Then the execution time should be logged

  Scenario: Timed decorator measures async function execution
    Given an async function decorated with @timed
    When I call the async function
    Then the execution time should be logged

  Scenario: Timed decorator uses custom metric name
    Given a function decorated with @timed("custom_metric")
    When I call the function
    Then the metric "custom_metric" should be logged

  # Counted Decorator

  Scenario: Counted decorator logs sync function calls
    Given a sync function decorated with @counted
    When I call the function 3 times
    Then the function call should be logged 3 times

  Scenario: Counted decorator logs async function calls
    Given an async function decorated with @counted
    When I call the async function
    Then the function call should be logged

  # Metrics Registry

  Scenario: Registering metrics collectors
    Given a metrics registry
    And an in-memory collector for observability
    When I register the collector
    Then the registry should have 1 collector

  Scenario: Incrementing counters through registry
    Given a metrics registry with an in-memory collector
    When I increment metric "requests" by 1
    Then the collector should have metric "requests" with value 1

  Scenario: Setting gauges through registry
    Given a metrics registry with an in-memory collector
    When I set gauge "active_connections" to 42
    Then the collector should have gauge "active_connections" with value 42

  Scenario: Recording histograms through registry
    Given a metrics registry with an in-memory collector
    When I record histogram "response_size" with value 1024
    Then the collector should have histogram "response_size"

  Scenario: Recording timing through registry
    Given a metrics registry with an in-memory collector
    When I record timing "request_duration" with 150.5 ms
    Then the collector should have timing "request_duration"

  Scenario: Unregistering collectors
    Given a metrics registry with an in-memory collector
    When I unregister the collector
    Then the registry should have 0 collectors

  # In-Memory Metrics Collector

  Scenario: In-memory collector tracks counters
    Given an in-memory collector for observability
    When I increment "api_calls" by 5
    And I increment "api_calls" by 3
    Then the counter "api_calls" should be 8

  Scenario: In-memory collector tracks gauges
    Given an in-memory collector for observability
    When I set gauge "queue_size" to 10
    And I set gauge "queue_size" to 5
    Then the gauge "queue_size" should be 5

  Scenario: In-memory collector supports tags
    Given an in-memory collector for observability
    When I increment "requests" with tag "endpoint" = "users"
    And I increment "requests" with tag "endpoint" = "orders"
    Then both tagged metrics should be tracked

  # Null Implementations

  Scenario: Null metrics collector accepts but discards metrics
    Given a null metrics collector
    When I increment "anything" by 100
    Then no error should occur

  Scenario: Null logger accepts but discards logs
    Given a null logger
    When I log "test message" at INFO level
    Then no error should occur

  Scenario: Null tracing provider creates null spans
    Given a null tracing provider
    When I start a span "test_operation"
    Then a null span should be returned
