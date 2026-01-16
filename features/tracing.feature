@observability @tracing @testing @high
Feature: In-Memory Tracing Provider
  As a developer testing Graph of Thought
  I want an in-memory tracing provider
  So that I can verify tracing behavior in tests without external dependencies

  # ===========================================================================
  # FEATURE-LEVEL ESCAPE CLAUSES
  # ===========================================================================
  # ESCAPE CLAUSE: No OpenTelemetry integration.
  # Current: InMemoryTracingProvider stores spans locally for testing.
  # Requires: OpenTelemetry SDK, span exporters, trace context propagation.
  # Depends: None
  #
  # ESCAPE CLAUSE: No distributed trace context propagation.
  # Current: Parent-child relationships tracked within single process.
  # Requires: W3C trace context headers, cross-service propagation.
  # Depends: OpenTelemetry integration
  #
  # ESCAPE CLAUSE: No span sampling or filtering.
  # Current: All spans are captured.
  # Requires: Sampling configuration, head/tail-based sampling.
  # Depends: None

  # ===========================================================================
  # Span Creation
  # ===========================================================================

  Scenario: Creating a basic span
    Given an in-memory tracing provider
    When I start a span "process_request"
    Then the span "process_request" should exist
    And the provider should have 1 span

  Scenario: Span tracks start time
    Given an in-memory tracing provider
    When I start a span "timed_operation"
    Then the span "timed_operation" should have a start time

  Scenario: Ending a span records duration
    Given an in-memory tracing provider
    When I start a span "measured_operation"
    And I end the span "measured_operation"
    Then the span "measured_operation" should be ended
    And the span "measured_operation" should have a duration

  # ===========================================================================
  # Span Attributes
  # ===========================================================================

  Scenario: Setting attributes on a span
    Given an in-memory tracing provider
    When I start a span "user_operation"
    And I set attribute "user_id" to "123" on span "user_operation"
    Then the span "user_operation" should have attribute "user_id" with value "123"

  Scenario: Setting multiple attributes
    Given an in-memory tracing provider
    When I start a span "api_call"
    And I set attribute "method" to "GET" on span "api_call"
    And I set attribute "path" to "/users" on span "api_call"
    And I set attribute "status_code" to "200" on span "api_call"
    Then the span "api_call" should have 3 attributes

  Scenario: Initial attributes from span creation
    Given an in-memory tracing provider
    When I start a span "configured_span" with attributes service="api", version="1.0"
    Then the span "configured_span" should have attribute "service" with value "api"
    And the span "configured_span" should have attribute "version" with value "1.0"

  # ===========================================================================
  # Span Events
  # ===========================================================================

  Scenario: Adding events to a span
    Given an in-memory tracing provider
    When I start a span "event_span"
    And I add event "cache_hit" to span "event_span"
    Then the span "event_span" should have 1 event
    And the span "event_span" should have event "cache_hit"

  Scenario: Adding events with attributes
    Given an in-memory tracing provider
    When I start a span "detailed_span"
    And I add event "query_executed" with attributes query="SELECT *", rows="100" to span "detailed_span"
    Then the span "detailed_span" should have event "query_executed"

  Scenario: Multiple events on a span
    Given an in-memory tracing provider
    When I start a span "multi_event_span"
    And I add event "step_1" to span "multi_event_span"
    And I add event "step_2" to span "multi_event_span"
    And I add event "step_3" to span "multi_event_span"
    Then the span "multi_event_span" should have 3 events

  # ===========================================================================
  # Span Status
  # ===========================================================================

  Scenario: Setting span status to OK
    Given an in-memory tracing provider
    When I start a span "successful_operation"
    And I set status "OK" on span "successful_operation"
    Then the span "successful_operation" should have status "OK"

  Scenario: Setting span status to ERROR with description
    Given an in-memory tracing provider
    When I start a span "failed_operation"
    And I set status "ERROR" with description "Connection timeout" on span "failed_operation"
    Then the span "failed_operation" should have status "ERROR"
    And the span "failed_operation" should have status description "Connection timeout"

  # ===========================================================================
  # Parent-Child Relationships
  # ===========================================================================

  Scenario: Creating child spans
    Given an in-memory tracing provider
    When I start a span "parent_operation"
    And I start a child span "child_operation" under "parent_operation"
    Then the span "child_operation" should have parent "parent_operation"
    And the span "parent_operation" should have 1 child

  Scenario: Nested child spans
    Given an in-memory tracing provider
    When I start a span "grandparent"
    And I start a child span "parent" under "grandparent"
    And I start a child span "child" under "parent"
    Then the span "child" should have parent "parent"
    And the span "parent" should have parent "grandparent"
    And the span "grandparent" should have no parent

  Scenario: Multiple children under one parent
    Given an in-memory tracing provider
    When I start a span "parent_with_children"
    And I start a child span "child_1" under "parent_with_children"
    And I start a child span "child_2" under "parent_with_children"
    And I start a child span "child_3" under "parent_with_children"
    Then the span "parent_with_children" should have 3 children

  # ===========================================================================
  # Context Manager Support
  # ===========================================================================

  Scenario: Using span as context manager
    Given an in-memory tracing provider
    When I use span "context_span" as a context manager
    Then the span "context_span" should be ended

  Scenario: Context manager sets error status on exception
    Given an in-memory tracing provider
    When I use span "error_span" as a context manager that raises an error
    Then the span "error_span" should have status "ERROR"
    And the span "error_span" should be ended

  # ===========================================================================
  # Provider Queries
  # ===========================================================================

  Scenario: Getting all root spans with proper scoping
    Given an in-memory tracing provider
    When I start and end a span "root_1"
    And I start and end a span "root_2"
    And I start a child span "child_of_root_1" under "root_1"
    Then the provider should have 2 root spans
    And the span "child_of_root_1" should have parent "root_1"

  Scenario: Getting spans by name
    Given an in-memory tracing provider
    When I start a span "repeated_name"
    And I start a span "repeated_name"
    And I start a span "different_name"
    Then the provider should have 2 spans named "repeated_name"

  Scenario: Resetting the provider
    Given an in-memory tracing provider
    When I start a span "span_1"
    And I start a span "span_2"
    And I reset the tracing provider
    Then the provider should have 0 spans

  # ===========================================================================
  # Span Serialization
  # ===========================================================================

  Scenario: Converting span to dictionary
    Given an in-memory tracing provider
    When I start a span "serializable_span"
    And I set attribute "key" to "value" on span "serializable_span"
    And I add event "test_event" to span "serializable_span"
    And I end the span "serializable_span"
    Then the span "serializable_span" should be convertible to a dictionary
    And the dictionary should contain the span name
    And the dictionary should contain the attributes
    And the dictionary should contain the events

  # ===========================================================================
  # Edge Cases
  # ===========================================================================

  Scenario: Ending a span multiple times is safe
    Given an in-memory tracing provider
    When I start a span "double_end_span"
    And I end the span "double_end_span"
    And I end the span "double_end_span"
    Then the span "double_end_span" should be ended
    And the span "double_end_span" should have a duration

  Scenario: Empty provider has no spans
    Given an in-memory tracing provider
    Then the provider should have 0 spans
    And the provider should have 0 root spans

  Scenario: Automatic span propagation
    Given an in-memory tracing provider
    When I start a span "auto_parent"
    And I start a span "auto_child" without explicit parent
    Then the span "auto_child" should have parent "auto_parent"

  Scenario: Context manager restores parent as active
    Given an in-memory tracing provider
    When I use span "parent" as a context manager
    And I start a span "sibling"
    Then the span "sibling" should have no parent
    And the provider should have 2 root spans

  @wip
  Scenario: Exporting spans in OpenTelemetry format
    Given an in-memory tracing provider
    When I start a span "exportable"
    And I set attribute "service" to "test" on span "exportable"
    And I end the span "exportable"
    Then I should be able to export spans in OTLP format
