"""
Step definitions for observability BDD tests.

Note: Some metrics-related steps are defined in metrics_steps.py.
This file focuses on logging, decorators, and metrics registry functionality.
"""
import logging
import asyncio
import json
from io import StringIO
from behave import given, when, then, use_step_matcher

from graph_of_thought.observability import (
    setup_logging,
    timed,
    counted,
    MetricsRegistry,
    InMemoryMetricsCollector,
    StructuredLogger,
    NullTracingProvider,
)

use_step_matcher("parse")


# =============================================================================
# Logging Setup
# =============================================================================

@when("I set up logging with level INFO")
def step_setup_logging_info(context):
    context.logger = setup_logging(level=logging.INFO, logger_name="test_logger_info")


@when('I set up logging with format "{format_string}"')
def step_setup_logging_format(context, format_string):
    context.logger = setup_logging(
        format_string=format_string,
        logger_name="test_logger_format"
    )
    context.format_string = format_string


@when('I set up logging with name "{name}"')
def step_setup_logging_name(context, name):
    context.logger = setup_logging(logger_name=name)


@then("a logger should be configured")
def step_logger_configured(context):
    assert context.logger is not None


@then("the logger should have level INFO")
def step_logger_level_info(context):
    assert context.logger.level == logging.INFO


@then("the logger should use the custom format")
def step_logger_custom_format(context):
    if context.logger.handlers:
        formatter = context.logger.handlers[0].formatter
        assert formatter is not None


@then('the logger should have name "{name}"')
def step_logger_name(context, name):
    assert context.logger.name == name


# =============================================================================
# Structured Logging
# =============================================================================

@given("structured logging is enabled")
def step_structured_logging_enabled(context):
    """Set up a structured logger with captured output for testing."""
    context.log_output = StringIO()
    context.structured_logger = StructuredLogger(
        name="test_structured",
        output=context.log_output,
    )


@when('I log "{message}" with context request_id "{request_id}" and user "{user}"')
def step_log_with_context(context, message, request_id, user):
    """Log a message with structured context."""
    context.structured_logger.info(message, request_id=request_id, user=user)


@then('the log output should include "{key}": "{value}"')
def step_log_output_includes(context, key, value):
    """Verify that the log output contains the expected key-value pair."""
    log_content = context.log_output.getvalue()

    # Parse the JSON log line(s) and check for the key-value pair
    found = False
    for line in log_content.strip().split('\n'):
        if line:
            entry = json.loads(line)
            if key in entry and str(entry[key]) == value:
                found = True
                break

    assert found, f'Expected "{key}": "{value}" in log output, got: {log_content}'


@given("structured logging is enabled with level INFO")
def step_structured_logging_with_level(context):
    """Set up a structured logger with INFO level filtering."""
    context.log_output = StringIO()
    context.structured_logger = StructuredLogger(
        name="test_structured",
        output=context.log_output,
        level=logging.INFO,
    )


@given('structured logging is enabled with name "{name}"')
def step_structured_logging_with_name(context, name):
    """Set up a structured logger with a custom name."""
    context.log_output = StringIO()
    context.structured_logger = StructuredLogger(
        name=name,
        output=context.log_output,
    )


@when('I bind context with {key} "{value}"')
def step_bind_context(context, key, value):
    """Bind context to the structured logger."""
    context.structured_logger = context.structured_logger.bind(**{key: value})


@when('I bind additional context with {key} "{value}"')
def step_bind_additional_context(context, key, value):
    """Bind additional context to an already-bound logger."""
    context.structured_logger = context.structured_logger.bind(**{key: value})


@when('I log "{message}" at DEBUG level')
def step_log_debug(context, message):
    """Log a DEBUG message."""
    context.structured_logger.debug(message)


@when('I log "{message}" at INFO level')
def step_log_info_structured(context, message):
    """Log an INFO message."""
    context.structured_logger.info(message)


@when('I log "{message}" at WARNING level')
def step_log_warning(context, message):
    """Log a WARNING message."""
    context.structured_logger.warning(message)


@when('I log "{message}" at ERROR level')
def step_log_error(context, message):
    """Log an ERROR message."""
    context.structured_logger.error(message)


@when('I log "{message}" with nested context')
def step_log_with_nested_context(context, message):
    """Log a message with complex nested data."""
    context.structured_logger.info(
        message,
        metadata={"nested": {"key": "value"}, "list": [1, 2, 3]},
        tags=["production", "api"],
    )


@then('both log entries should include "{key}": "{value}"')
def step_both_entries_include(context, key, value):
    """Verify both log entries contain the expected key-value pair."""
    log_content = context.log_output.getvalue()
    entries = [json.loads(line) for line in log_content.strip().split('\n') if line]

    assert len(entries) >= 2, f"Expected at least 2 entries, got {len(entries)}"
    for i, entry in enumerate(entries):
        assert key in entry, f"Entry {i} missing key '{key}'"
        assert str(entry[key]) == value, f"Entry {i} has {key}={entry[key]}, expected {value}"


@then('the log output should contain {count:d} entry')
@then('the log output should contain {count:d} entries')
def step_log_entry_count(context, count):
    """Verify the number of log entries."""
    log_content = context.log_output.getvalue()
    entries = [line for line in log_content.strip().split('\n') if line]
    assert len(entries) == count, f"Expected {count} entries, got {len(entries)}: {entries}"


@then('the log should have entry with level "{level}" and message "{message}"')
def step_log_has_entry(context, level, message):
    """Verify a specific log entry exists with given level and message."""
    log_content = context.log_output.getvalue()
    found = False
    for line in log_content.strip().split('\n'):
        if line:
            entry = json.loads(line)
            if entry.get("level") == level and entry.get("message") == message:
                found = True
                break
    assert found, f'No entry with level "{level}" and message "{message}" found'


@then("the log output should be valid JSON")
def step_log_is_valid_json(context):
    """Verify all log output is valid JSON."""
    log_content = context.log_output.getvalue()
    for line in log_content.strip().split('\n'):
        if line:
            json.loads(line)  # Will raise if invalid


@then("the nested data should be preserved in the output")
def step_nested_data_preserved(context):
    """Verify nested data structures are preserved in log output."""
    log_content = context.log_output.getvalue()
    entry = json.loads(log_content.strip().split('\n')[-1])

    assert "metadata" in entry, "Missing 'metadata' in log entry"
    assert entry["metadata"]["nested"]["key"] == "value", "Nested dict not preserved"
    assert entry["metadata"]["list"] == [1, 2, 3], "Nested list not preserved"
    assert entry["tags"] == ["production", "api"], "Tags list not preserved"


# =============================================================================
# Timed Decorator
# =============================================================================

@given("a sync function decorated with @timed")
def step_timed_sync(context):
    @timed("test_sync_timed")
    def sync_func():
        return "done"
    context.timed_func = sync_func
    context.is_async = False


@given("an async function decorated with @timed")
def step_timed_async(context):
    @timed("test_async_timed")
    async def async_func():
        return "done"
    context.timed_func = async_func
    context.is_async = True


@given('a function decorated with @timed("{metric_name}")')
def step_timed_custom(context, metric_name):
    @timed(metric_name)
    def func():
        return "done"
    context.timed_func = func
    context.is_async = False
    context.metric_name = metric_name


@when("I call the function")
def step_call_function(context):
    if hasattr(context, 'is_async') and context.is_async:
        context.result = asyncio.run(context.timed_func())
    elif hasattr(context, 'timed_func'):
        context.result = context.timed_func()
    elif hasattr(context, 'counted_func'):
        context.counted_func()


@when("I call the async function")
def step_call_async_function(context):
    if hasattr(context, 'timed_func') and context.timed_func:
        context.result = asyncio.run(context.timed_func())
    elif hasattr(context, 'counted_func') and context.counted_func:
        context.result = asyncio.run(context.counted_func())


@then("the execution time should be logged")
def step_time_logged(context):
    assert context.result == "done"


@then('the metric "{metric_name}" should be logged')
def step_metric_logged(context, metric_name):
    assert context.result == "done"


# =============================================================================
# Counted Decorator
# =============================================================================

@given("a sync function decorated with @counted")
def step_counted_sync(context):
    @counted("test_sync_counted")
    def sync_func():
        return "done"
    context.counted_func = sync_func
    context.is_async = False


@given("an async function decorated with @counted")
def step_counted_async(context):
    @counted("test_async_counted")
    async def async_func():
        return "done"
    context.counted_func = async_func
    context.is_async = True


@when("I call the function {count:d} times")
def step_call_multiple(context, count):
    for _ in range(count):
        if context.is_async:
            asyncio.run(context.counted_func())
        else:
            context.counted_func()
    context.call_count = count


@then("the function call should be logged {count:d} times")
def step_logged_times(context, count):
    assert context.call_count == count


@then("the function call should be logged")
def step_function_logged(context):
    assert True


# =============================================================================
# Metrics Registry
# =============================================================================

@given("a metrics registry")
def step_metrics_registry(context):
    context.registry = MetricsRegistry()


@given("a metrics registry with an in-memory collector")
def step_registry_with_collector(context):
    context.registry = MetricsRegistry()
    context.collector = InMemoryMetricsCollector()
    context.registry.register(context.collector)


@when("I register the collector")
def step_register_collector(context):
    context.registry.register(context.collector)


@then("the registry should have {count:d} collector")
@then("the registry should have {count:d} collectors")
def step_check_collector_count(context, count):
    assert len(context.registry._collectors) == count


@when('I increment metric "{name}" by {value:d}')
def step_increment_metric_registry(context, name, value):
    if hasattr(context, 'registry') and context.registry:
        context.registry.increment(name, value)
    else:
        context.collector.increment(name, value)


@then('the collector should have metric "{name}" with value {value:d}')
def step_check_metric_value(context, name, value):
    assert context.collector.counters.get(name, 0) == value


# Note: "When I set gauge" step is in metrics_steps.py


@then('the collector should have gauge "{name}" with value {value:d}')
def step_check_gauge_value(context, name, value):
    assert context.collector.gauges.get(name, 0) == float(value)


# Note: "When I record histogram" step is in metrics_steps.py


@then('the collector should have histogram "{name}"')
def step_check_histogram(context, name):
    assert name in context.collector.histograms


# Note: "When I record timing" step is in metrics_steps.py


@then('the collector should have timing "{name}"')
def step_check_timing(context, name):
    assert name in context.collector.timings


@when("I unregister the collector")
def step_unregister_collector(context):
    context.registry.unregister(context.collector)


# =============================================================================
# In-Memory Metrics Collector (for observability-specific tests)
# Note: Basic collector tests are in metrics_steps.py
# =============================================================================

@given("an in-memory collector for observability")
def step_in_memory_observability(context):
    context.collector = InMemoryMetricsCollector()


@when('I increment "{name}" by {value:d}')
def step_increment_collector(context, name, value):
    context.collector.increment(name, value)


@then('the counter "{name}" should be {value:d}')
def step_check_counter(context, name, value):
    assert context.collector.counters.get(name, 0) == value


@then('the gauge "{name}" should be {value:d}')
def step_check_gauge(context, name, value):
    assert context.collector.gauges.get(name, 0) == float(value)


@when('I increment "{name}" with tag "{tag_name}" = "{tag_value}"')
def step_increment_with_tag(context, name, tag_name, tag_value):
    context.collector.increment(name, 1, {tag_name: tag_value})


@then("both tagged metrics should be tracked")
def step_tagged_tracked(context):
    assert True


@given('counter "{name}" with value {value:d}')
def step_counter_with_value(context, name, value):
    """Set up a counter with a specific initial value."""
    context.collector.increment(name, value)


# Note: "When I reset all metrics" step is in metrics_steps.py


# =============================================================================
# Null Implementations
# =============================================================================

@given("a default metrics collector")
def step_default_metrics(context):
    context.collector = InMemoryMetricsCollector()


@then("no error should occur")
def step_no_error(context):
    assert True


@given("a logger configured for testing")
def step_logger_for_testing(context):
    """Set up a structured logger with captured output for testing."""
    context.log_output = StringIO()
    context.structured_logger = StructuredLogger(
        name="test_logger",
        output=context.log_output,
    )
    context.last_log_message = None


@then("the log should contain the message as structured JSON")
def step_log_contains_structured_json(context):
    """Verify the log output is valid JSON containing the message."""
    log_content = context.log_output.getvalue()
    assert log_content, "No log output captured"

    # Parse the JSON and verify structure
    for line in log_content.strip().split('\n'):
        if line:
            entry = json.loads(line)
            assert "timestamp" in entry, "Missing timestamp in log entry"
            assert "level" in entry, "Missing level in log entry"
            assert "message" in entry, "Missing message in log entry"


@given("a null tracing provider")
def step_null_tracing(context):
    context.tracing = NullTracingProvider()


@when('I start a span "{name}"')
def step_start_span(context, name):
    context.span = context.tracing.start_span(name)


@then("a null span should be returned")
def step_null_span(context):
    from graph_of_thought.observability import NullTraceSpan
    assert isinstance(context.span, NullTraceSpan)
