"""
Step definitions for metrics-related BDD tests.
"""
import asyncio
from behave import given, when, then, use_step_matcher

from graph_of_thought import GraphOfThought, InMemoryMetricsCollector

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
def step_increment_counter(context, name, value):
    context.metrics.increment(name, value)


@when('I increment counter "{name}" by {value:d} with tag "{tag_key}" = "{tag_value}"')
def step_increment_counter_with_tag(context, name, value, tag_key, tag_value):
    context.metrics.increment(name, value, tags={tag_key: tag_value})


@when('I set gauge "{name}" to {value:f}')
def step_set_gauge(context, name, value):
    context.metrics.gauge(name, value)


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
