@observability @logging @metrics @high
Feature: Observability
  As a developer using Graph of Thought
  I want to use observability utilities for logging and metrics
  So that I can monitor and debug my application

  # ===========================================================================
  # FEATURE-LEVEL ESCAPE CLAUSES
  # ===========================================================================
  # RESOLVED: In-memory tracing implemented via InMemoryTracingProvider class.
  # InMemoryTracingProvider stores spans in memory for testing and debugging.
  # See features/tracing.feature for detailed tracing specifications.
  #
  # ESCAPE CLAUSE: No OpenTelemetry/Jaeger integration.
  # Current: InMemoryTracingProvider for testing only.
  # Requires: OpenTelemetry SDK, span exporters, trace context propagation.
  # Depends: None
  #
  # ESCAPE CLAUSE: No Prometheus/StatsD integration.
  # Current: InMemoryMetricsCollector for testing only.
  # Requires: Prometheus client, StatsD client, metric exposition endpoint.
  # Depends: None
  #
  # ESCAPE CLAUSE: Decorators only log to debug level.
  # Current: @timed and @counted log to logging.debug().
  # Requires: Integration with metrics collectors, configurable log levels.
  # Depends: Metrics registry integration
  #
  # RESOLVED: Structured logging implemented via StructuredLogger class.
  # StructuredLogger outputs JSON with context binding support.
  # Use StructuredLogger(output=StringIO()) for testing, or output to stderr in production.
  #
  # MOVED: InMemoryMetricsCollector scenarios moved to features/metrics_collector.feature
  # See that file for testing-focused metrics collector specifications.

  # ===========================================================================
  # Logging Setup
  # ===========================================================================

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

  # --- Logging Edge Cases ---

  Scenario: Logging with structured context
    Given structured logging is enabled
    When I log "Processing request" with context request_id "123" and user "alice"
    Then the log output should include "request_id": "123"
    And the log output should include "user": "alice"

  Scenario: Bound context persists across multiple log calls
    Given structured logging is enabled
    When I bind context with request_id "REQ-456"
    And I log "First message" at INFO level
    And I log "Second message" at INFO level
    Then both log entries should include "request_id": "REQ-456"

  Scenario: Log level filtering respects minimum level
    Given structured logging is enabled with level INFO
    When I log "Debug message" at DEBUG level
    And I log "Info message" at INFO level
    Then the log output should contain 1 entry
    And the log output should include "message": "Info message"

  Scenario: Chained context binding accumulates context
    Given structured logging is enabled
    When I bind context with service "api"
    And I bind additional context with request_id "789"
    And I log "Chained context" at INFO level
    Then the log output should include "service": "api"
    And the log output should include "request_id": "789"

  Scenario: All log levels produce correct output
    Given structured logging is enabled
    When I log "Debug msg" at DEBUG level
    And I log "Info msg" at INFO level
    And I log "Warning msg" at WARNING level
    And I log "Error msg" at ERROR level
    Then the log output should contain 4 entries
    And the log should have entry with level "DEBUG" and message "Debug msg"
    And the log should have entry with level "INFO" and message "Info msg"
    And the log should have entry with level "WARNING" and message "Warning msg"
    And the log should have entry with level "ERROR" and message "Error msg"

  Scenario: Complex data types are serialized correctly
    Given structured logging is enabled
    When I log "Complex data" with nested context
    Then the log output should be valid JSON
    And the nested data should be preserved in the output

  Scenario: Logger name appears in output
    Given structured logging is enabled with name "my_service"
    When I log "Test message" at INFO level
    Then the log output should include "logger": "my_service"

  @wip
  Scenario: Logging to multiple handlers
    When I set up logging with console and file handlers
    Then logs should appear in console
    And logs should appear in the log file

  @wip
  Scenario: Log level filtering per handler
    When I set up logging with INFO to console and DEBUG to file
    Then DEBUG messages should appear in file only
    And INFO messages should appear in both

  # ===========================================================================
  # Timed Decorator
  # ===========================================================================

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

  # --- Timed Edge Cases (TODO: Implement) ---

  @wip
  Scenario: Timed decorator reports to metrics collector
    Given a metrics registry with an in-memory collector
    And a function decorated with @timed("api_call")
    When I call the function
    Then the collector should have timing "api_call"

  @wip
  Scenario: Timed decorator handles exceptions
    Given a sync function decorated with @timed that raises an error
    When I call the function
    Then the execution time should still be logged
    And the error should propagate

  @wip
  Scenario: Timed decorator supports percentile tracking
    Given a function decorated with @timed with percentile tracking
    When I call the function 100 times with varying durations
    Then I should be able to query p50 latency
    And I should be able to query p99 latency

  # ===========================================================================
  # Counted Decorator
  # ===========================================================================

  Scenario: Counted decorator logs sync function calls
    Given a sync function decorated with @counted
    When I call the function 3 times
    Then the function call should be logged 3 times

  Scenario: Counted decorator logs async function calls
    Given an async function decorated with @counted
    When I call the async function
    Then the function call should be logged

  # --- Counted Edge Cases (TODO: Implement) ---

  @wip
  Scenario: Counted decorator reports to metrics collector
    Given a metrics registry with an in-memory collector
    And a function decorated with @counted("api_calls")
    When I call the function 5 times
    Then the collector should have counter "api_calls" with value 5

  @wip
  Scenario: Counted decorator tracks success vs failure
    Given a function decorated with @counted that sometimes fails
    When I call the function 10 times with 3 failures
    Then the collector should have counter "function_success" with value 7
    And the collector should have counter "function_failure" with value 3

  # ===========================================================================
  # Metrics Registry
  # ===========================================================================

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

  # --- Registry Edge Cases (TODO: Implement) ---

  @wip
  Scenario: Registry exports metrics in Prometheus format
    Given a metrics registry with an in-memory collector
    And counter "requests" with value 100
    And gauge "active_users" with value 42
    When I export metrics in Prometheus format
    Then the output should contain 'requests 100'
    And the output should contain 'active_users 42'

  @wip
  Scenario: Registry supports metric namespacing
    Given a metrics registry with namespace "myapp"
    When I increment metric "requests" by 1
    Then the full metric name should be "myapp_requests"

  @wip
  Scenario: Registry aggregates across multiple collectors
    Given a metrics registry with 2 in-memory collectors
    When I increment metric "requests" by 1
    Then both collectors should have the metric

  # ===========================================================================
  # Default Implementations
  # Note: InMemoryMetricsCollector is now in features/metrics_collector.feature
  # ===========================================================================

  Scenario: Default metrics collector stores metrics
    Given a default metrics collector
    When I increment "anything" by 100
    Then the counter "anything" should equal 100

  Scenario: Logger outputs structured JSON format
    Given a logger configured for testing
    When I log "test message" at INFO level
    Then the log should contain the message as structured JSON

  Scenario: Default tracing provider creates spans
    Given a default tracing provider
    When I start a span "test_operation" for observability
    Then an in-memory span should be returned

  # ===========================================================================
  # Distributed Tracing (TODO: Implement)
  # ===========================================================================

  @wip
  Scenario: Creating trace spans
    Given an OpenTelemetry tracing provider
    When I start a span "process_request"
    And I add attribute "user_id" = "123"
    And I end the span
    Then the span should be exported

  @wip
  Scenario: Nested spans create parent-child relationship
    Given an OpenTelemetry tracing provider
    When I start a span "parent_operation"
    And I start a child span "child_operation"
    And I end both spans
    Then the child span should have parent "parent_operation"

  @wip
  Scenario: Trace context propagates across service boundaries
    Given an OpenTelemetry tracing provider
    When I start a span "api_call"
    And I extract trace headers
    Then the headers should contain traceparent
    And the headers should contain tracestate

  @wip
  Scenario: Spans record errors
    Given an OpenTelemetry tracing provider
    When I start a span "failing_operation"
    And an error occurs during the span
    Then the span should have status ERROR
    And the span should contain error details

  # ===========================================================================
  # Alerting (TODO: Implement)
  # ===========================================================================

  @wip
  Scenario: Defining metric alert thresholds
    Given a metrics registry with alerting enabled
    When I define an alert "high_error_rate" for error_rate > 0.05
    And the error_rate reaches 0.08
    Then an alert should be triggered

  @wip
  Scenario: Alert cooldown prevents spam
    Given a metrics registry with alerting enabled
    And an alert "high_error_rate" with 5 minute cooldown
    When the alert triggers twice within 1 minute
    Then only 1 alert notification should be sent
