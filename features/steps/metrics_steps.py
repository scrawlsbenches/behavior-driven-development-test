"""
Step definitions for metrics-related BDD tests.
"""
import asyncio
import re
from behave import given, when, then, use_step_matcher, register_type

from graph_of_thought import GraphOfThought, InMemoryMetricsCollector


# Custom type for parsing tags - stops at " should"
def parse_tags_type(text):
    return text

register_type(Tags=parse_tags_type)

use_step_matcher("parse")


# =============================================================================
# Metrics Setup Steps
# =============================================================================

@given("an in-memory metrics collector")
def step_in_memory_metrics(context):
    context.metrics = InMemoryMetricsCollector()


@given("a test graph with the metrics collector")
def step_graph_with_metrics(context):
    context.graph = GraphOfThought[str](
        evaluator=context.simple_evaluator,
        generator=context.simple_generator,
        metrics=context.metrics,
    )


# =============================================================================
# Metrics Actions
# =============================================================================

@when('I increment counter "{name}" by {value:d}')
@given('I increment counter "{name}" by {value:d}')
def step_increment_counter(context, name, value):
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    if collector:
        collector.increment(name, value)


@when('I increment counter "{name}" by {value:d} with tag "{tag_key}" = "{tag_value}"')
def step_increment_counter_with_tag(context, name, value, tag_key, tag_value):
    context.metrics.increment(name, value, tags={tag_key: tag_value})


@when('I set gauge "{name}" to {value:g}')
@given('I set gauge "{name}" to {value:g}')
def step_set_gauge(context, name, value):
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    if hasattr(context, 'registry') and context.registry:
        context.registry.gauge(name, float(value))
    elif collector:
        collector.gauge(name, float(value))


@when('I record histogram value {value:f} for "{name}"')
def step_record_histogram(context, name, value):
    context.metrics.histogram(name, value)


@when('I record timing {value:f} for "{name}"')
def step_record_timing(context, name, value):
    context.metrics.timing(name, value)


# =============================================================================
# Metrics Assertions
# =============================================================================

@then('counter "{name}" should be {value:d}')
def step_check_counter(context, name, value):
    assert context.metrics.counters.get(name, 0) == value, f"Expected counter {name}={value}, got {context.metrics.counters.get(name, 0)}"


@then('counter "{name}" should be greater than {value:d}')
def step_check_counter_gt(context, name, value):
    actual = context.metrics.counters.get(name, 0)
    assert actual > value, f"Expected counter {name}>{value}, got {actual}"


@then('gauge "{name}" should be {value:f}')
def step_check_gauge(context, name, value):
    assert context.metrics.gauges.get(name) == value, f"Expected gauge {name}={value}, got {context.metrics.gauges.get(name)}"


@then('histogram "{name}" should contain values {v1:f} and {v2:f}')
def step_check_histogram(context, name, v1, v2):
    values = context.metrics.histograms.get(name, [])
    assert v1 in values and v2 in values, f"Expected histogram {name} to contain {v1} and {v2}, got {values}"


@then('timing "{name}" should contain {value:f}')
def step_check_timing(context, name, value):
    values = context.metrics.timings.get(name, [])
    assert value in values, f"Expected timing {name} to contain {value}, got {values}"


# =============================================================================
# Counter Assertions (extended) - Using regex to avoid greedy matching
# =============================================================================

use_step_matcher("re")

# Non-tag version - must come AFTER tag version in file but uses negative lookahead
@then(r'the counter "(?P<name>[^"]+)" should equal (?P<value>\d+)')
def step_counter_equals(context, name, value):
    value = int(value)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    actual = collector.counters.get(name, 0) if collector else 0
    assert actual == value, f"Expected counter {name}={value}, got {actual}"


@then(r'the counter "(?P<name>[^"]+)" with tags (?P<tags>.+) should equal (?P<value>\d+)')
def step_counter_with_tags_equals(context, name, tags, value):
    value = int(value)
    parsed_tags = _parse_tags(tags)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    key = collector._make_key(name, parsed_tags)
    actual = collector.counters.get(key, 0)
    assert actual == value, f"Expected counter {name}[{tags}]={value}, got {actual}"


@when(r'I increment counter "(?P<name>[^"]+)" by (?P<value>\d+) with tags (?P<tags>.+)')
def step_increment_counter_with_tags(context, name, value, tags):
    value = int(value)
    parsed_tags = _parse_tags(tags)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    if collector:
        collector.increment(name, value, tags=parsed_tags)

use_step_matcher("parse")


@when('I increment counter "{name}"')
def step_increment_counter_default(context, name):
    context.metrics.increment(name, 1)


# =============================================================================
# Gauge Assertions (extended) - Using regex to avoid greedy matching
# =============================================================================

use_step_matcher("re")

@then(r'the gauge "(?P<name>[^"]+)" should equal (?P<value>[\d.]+)')
def step_gauge_equals(context, name, value):
    value = float(value)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    actual = collector.gauges.get(name, 0) if collector else 0
    assert actual == value, f"Expected gauge {name}={value}, got {actual}"


@when(r'I set gauge "(?P<name>[^"]+)" to (?P<value>[\d.]+) with tags (?P<tags>.+)')
def step_set_gauge_with_tags(context, name, value, tags):
    value = float(value)
    parsed_tags = _parse_tags(tags)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    if collector:
        collector.gauge(name, value, tags=parsed_tags)


@then(r'the gauge "(?P<name>[^"]+)" with tags (?P<tags>.+) should equal (?P<value>[\d.]+)')
def step_gauge_with_tags_equals(context, name, tags, value):
    value = float(value)
    parsed_tags = _parse_tags(tags)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    key = collector._make_key(name, parsed_tags)
    actual = collector.gauges.get(key, 0)
    assert actual == value, f"Expected gauge {name}[{tags}]={value}, got {actual}"

use_step_matcher("parse")


# =============================================================================
# Histogram Assertions (extended)
# =============================================================================

@when('I record histogram "{name}" with value {value:g}')
@given('I record histogram "{name}" with value {value:g}')
def step_record_histogram_value(context, name, value):
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    if hasattr(context, 'registry') and context.registry:
        context.registry.histogram(name, float(value))
    elif collector:
        collector.histogram(name, float(value))


use_step_matcher("re")

@when(r'I record histogram "(?P<name>[^"]+)" with value (?P<value>[\d.]+) with tags (?P<tags>.+)')
def step_record_histogram_with_tags(context, name, value, tags):
    value = float(value)
    parsed_tags = _parse_tags(tags)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    if collector:
        collector.histogram(name, value, tags=parsed_tags)

# Use regex for all histogram assertions to avoid greedy parse matching
use_step_matcher("re")

@then(r'the histogram "(?P<name>[^"]+)" should contain (?P<count>\d+) values?')
def step_histogram_count(context, name, count):
    count = int(count)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    values = collector.histograms.get(name, []) if collector else []
    assert len(values) == count, f"Expected histogram {name} to have {count} values, got {len(values)}"


@then(r'the histogram "(?P<name>[^"]+)" should contain value (?P<value>[\d.]+)')
def step_histogram_contains_value(context, name, value):
    value = float(value)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    values = collector.histograms.get(name, []) if collector else []
    assert value in values, f"Expected histogram {name} to contain {value}, got {values}"


@then(r'the histogram "(?P<name>[^"]+)" with tags (?P<tags>.+) should contain value (?P<value>[\d.]+)')
def step_histogram_with_tags_contains(context, name, tags, value):
    value = float(value)
    parsed_tags = _parse_tags(tags)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    key = collector._make_key(name, parsed_tags)
    values = collector.histograms.get(key, [])
    assert value in values, f"Expected histogram {name}[{tags}] to contain {value}, got {values}"

use_step_matcher("parse")

@then('the histogram "{name}" values should be {expected}')
def step_histogram_values_equal(context, name, expected):
    import ast
    expected_list = ast.literal_eval(expected)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    actual = collector.histograms.get(name, []) if collector else []
    assert actual == expected_list, f"Expected histogram {name}={expected_list}, got {actual}"

use_step_matcher("parse")


# =============================================================================
# Timing Assertions (extended)
# =============================================================================

@when('I record timing "{name}" with {value:g} ms')
@given('I record timing "{name}" with {value:g} ms')
def step_record_timing_ms(context, name, value):
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    if hasattr(context, 'registry') and context.registry:
        context.registry.timing(name, float(value))
    elif collector:
        collector.timing(name, float(value))


use_step_matcher("re")

@when(r'I record timing "(?P<name>[^"]+)" with (?P<value>[\d.]+) ms with tags (?P<tags>.+)')
def step_record_timing_with_tags(context, name, value, tags):
    value = float(value)
    parsed_tags = _parse_tags(tags)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    if collector:
        collector.timing(name, value, tags=parsed_tags)


@then(r'the timing "(?P<name>[^"]+)" with tags (?P<tags>.+) should contain value (?P<value>[\d.]+)')
def step_timing_with_tags_contains(context, name, tags, value):
    value = float(value)
    parsed_tags = _parse_tags(tags)
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    key = collector._make_key(name, parsed_tags)
    values = collector.timings.get(key, [])
    assert value in values, f"Expected timing {name}[{tags}] to contain {value}, got {values}"

use_step_matcher("parse")


@then('the timing "{name}" should contain {count:d} value')
@then('the timing "{name}" should contain {count:d} values')
def step_timing_count(context, name, count):
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    values = collector.timings.get(name, []) if collector else []
    assert len(values) == count, f"Expected timing {name} to have {count} values, got {len(values)}"


@then('the timing "{name}" should contain value {value:g}')
def step_timing_contains_value(context, name, value):
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    values = collector.timings.get(name, []) if collector else []
    assert value in values, f"Expected timing {name} to contain {value}, got {values}"


# =============================================================================
# Query Operations
# =============================================================================

@then('the collector should have counters {expected}')
def step_collector_counters(context, expected):
    import ast
    expected_list = sorted(ast.literal_eval(expected))
    actual = sorted(context.metrics.counters.keys())
    assert actual == expected_list, f"Expected counters {expected_list}, got {actual}"


@then('the collector should have gauges {expected}')
def step_collector_gauges(context, expected):
    import ast
    expected_list = sorted(ast.literal_eval(expected))
    actual = sorted(context.metrics.gauges.keys())
    assert actual == expected_list, f"Expected gauges {expected_list}, got {actual}"


@then('the collector should have counter "{name}"')
def step_collector_has_counter(context, name):
    assert name in context.metrics.counters, f"Expected counter {name} to exist"


@then('the collector should not have counter "{name}"')
def step_collector_not_has_counter(context, name):
    assert name not in context.metrics.counters, f"Expected counter {name} to not exist"


# =============================================================================
# Reset Operations
# =============================================================================

@when("I reset all metrics")
def step_reset_metrics(context):
    # Handle both context.metrics and context.collector for compatibility
    collector = getattr(context, 'metrics', None) or getattr(context, 'collector', None)
    if collector:
        collector.reset()


@when('I reset counter "{name}"')
def step_reset_counter(context, name):
    if name in context.metrics.counters:
        del context.metrics.counters[name]


@when('I reset gauge "{name}"')
def step_reset_gauge(context, name):
    if name in context.metrics.gauges:
        del context.metrics.gauges[name]


# =============================================================================
# Helper Functions
# =============================================================================

def _parse_tags(tags_str: str) -> dict:
    """Parse tag string like 'endpoint="users", method="GET"' into dict."""
    result = {}
    # Split by comma, but handle values with commas inside quotes
    parts = []
    current = ""
    in_quotes = False
    for char in tags_str:
        if char == '"':
            in_quotes = not in_quotes
            current += char
        elif char == ',' and not in_quotes:
            parts.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current.strip())

    for part in parts:
        if '=' in part:
            key, value = part.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"')
            result[key] = value
    return result
