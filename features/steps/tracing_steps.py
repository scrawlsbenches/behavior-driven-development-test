"""
Step definitions for tracing BDD tests.
"""
from behave import given, when, then, use_step_matcher

from graph_of_thought.core.defaults import InMemoryTracingProvider, InMemoryTraceSpan

use_step_matcher("parse")


# =============================================================================
# Provider Setup
# =============================================================================

@given("an in-memory tracing provider")
def step_in_memory_tracing_provider(context):
    context.tracing = InMemoryTracingProvider()
    context.spans = {}  # Track spans by name for easy access


# =============================================================================
# Span Creation
# =============================================================================

use_step_matcher("re")


@when(r'I start a span "(?P<name>[^"]+)" with attributes (?P<attrs>.+)')
def step_start_span_with_attrs(context, name, attrs):
    parsed_attrs = _parse_attributes(attrs)
    span = context.tracing.start_span(name, attributes=parsed_attrs)
    context.spans[name] = span
    context.current_span = span


use_step_matcher("parse")


@when('I start a span "{name}"')
def step_start_span(context, name):
    span = context.tracing.start_span(name)
    context.spans[name] = span
    context.current_span = span


@when('I start a span "{name}" without explicit parent')
def step_start_span_no_explicit_parent(context, name):
    # Start span using automatic parent propagation
    span = context.tracing.start_span(name)
    context.spans[name] = span


@when('I start a child span "{child}" under "{parent}"')
def step_start_child_span(context, child, parent):
    parent_span = context.spans.get(parent)
    span = context.tracing.start_span(child, parent_span=parent_span)
    context.spans[child] = span
    context.current_span = span


@when('I start and end a span "{name}"')
def step_start_and_end_span(context, name):
    """Start a span and immediately end it (simulates proper scoping)."""
    with context.tracing.start_span(name) as span:
        context.spans[name] = span


@when('I end the span "{name}"')
def step_end_span(context, name):
    span = context.spans.get(name)
    if span:
        span.end()


# =============================================================================
# Span Attributes
# =============================================================================

@when('I set attribute "{key}" to "{value}" on span "{name}"')
def step_set_attribute(context, key, value, name):
    span = context.spans.get(name)
    if span:
        span.set_attribute(key, value)


# =============================================================================
# Span Events
# =============================================================================

use_step_matcher("re")


@when(r'I add event "(?P<event_name>[^"]+)" with attributes (?P<attrs>.+) to span "(?P<span_name>[^"]+)"')
def step_add_event_with_attrs(context, event_name, attrs, span_name):
    span = context.spans.get(span_name)
    if span:
        parsed_attrs = _parse_attributes(attrs)
        span.add_event(event_name, attributes=parsed_attrs)


use_step_matcher("parse")


@when('I add event "{event_name}" to span "{span_name}"')
def step_add_event(context, event_name, span_name):
    span = context.spans.get(span_name)
    if span:
        span.add_event(event_name)


# =============================================================================
# Span Status
# =============================================================================

use_step_matcher("re")


@when(r'I set status "(?P<status>[^"]+)" with description "(?P<description>[^"]+)" on span "(?P<name>[^"]+)"')
def step_set_status_with_description(context, status, description, name):
    span = context.spans.get(name)
    if span:
        span.set_status(status, description)


@when(r'I set status "(?P<status>[^"]+)" on span "(?P<name>[^"]+)"')
def step_set_status(context, status, name):
    span = context.spans.get(name)
    if span:
        span.set_status(status)


use_step_matcher("parse")


# =============================================================================
# Context Manager
# =============================================================================

@when('I use span "{name}" as a context manager')
def step_use_context_manager(context, name):
    with context.tracing.start_span(name) as span:
        context.spans[name] = span
        # Normal execution


@when('I use span "{name}" as a context manager that raises an error')
def step_use_context_manager_with_error(context, name):
    try:
        with context.tracing.start_span(name) as span:
            context.spans[name] = span
            raise ValueError("Test error")
    except ValueError:
        pass  # Expected


# =============================================================================
# Provider Operations
# =============================================================================

@when("I reset the tracing provider")
def step_reset_provider(context):
    context.tracing.reset()
    context.spans.clear()


# =============================================================================
# Span Assertions
# =============================================================================

@then('the span "{name}" should exist')
def step_span_exists(context, name):
    span = context.tracing.get_span(name)
    assert span is not None, f"Span '{name}' does not exist"


@then('the span "{name}" should have a start time')
def step_span_has_start_time(context, name):
    span = context.spans.get(name)
    assert span is not None, f"Span '{name}' not found"
    assert span._start_time is not None, f"Span '{name}' has no start time"


@then('the span "{name}" should be ended')
def step_span_is_ended(context, name):
    span = context.spans.get(name)
    assert span is not None, f"Span '{name}' not found"
    assert span.is_ended, f"Span '{name}' is not ended"


@then('the span "{name}" should have a duration')
def step_span_has_duration(context, name):
    span = context.spans.get(name)
    assert span is not None, f"Span '{name}' not found"
    assert span.duration_ms is not None, f"Span '{name}' has no duration"
    assert span.duration_ms >= 0, f"Span '{name}' has negative duration"


@then('the span "{name}" should have attribute "{key}" with value "{value}"')
def step_span_has_attribute(context, name, key, value):
    span = context.spans.get(name)
    assert span is not None, f"Span '{name}' not found"
    assert key in span.attributes, f"Span '{name}' missing attribute '{key}'"
    assert str(span.attributes[key]) == value, f"Expected {key}='{value}', got '{span.attributes[key]}'"


@then('the span "{name}" should have {count:d} attributes')
def step_span_attribute_count(context, name, count):
    span = context.spans.get(name)
    assert span is not None, f"Span '{name}' not found"
    actual = len(span.attributes)
    assert actual == count, f"Expected {count} attributes, got {actual}"


@then('the span "{name}" should have {count:d} event')
@then('the span "{name}" should have {count:d} events')
def step_span_event_count(context, name, count):
    span = context.spans.get(name)
    assert span is not None, f"Span '{name}' not found"
    actual = len(span.events)
    assert actual == count, f"Expected {count} events, got {actual}"


@then('the span "{name}" should have event "{event_name}"')
def step_span_has_event(context, name, event_name):
    span = context.spans.get(name)
    assert span is not None, f"Span '{name}' not found"
    event_names = [e["name"] for e in span.events]
    assert event_name in event_names, f"Span '{name}' missing event '{event_name}'"


@then('the span "{name}" should have status "{status}"')
def step_span_has_status(context, name, status):
    span = context.spans.get(name)
    assert span is not None, f"Span '{name}' not found"
    assert span.status == status, f"Expected status '{status}', got '{span.status}'"


@then('the span "{name}" should have status description "{description}"')
def step_span_has_status_description(context, name, description):
    span = context.spans.get(name)
    assert span is not None, f"Span '{name}' not found"
    assert span.status_description == description, f"Expected description '{description}', got '{span.status_description}'"


@then('the span "{child}" should have parent "{parent}"')
def step_span_has_parent(context, child, parent):
    child_span = context.spans.get(child)
    assert child_span is not None, f"Span '{child}' not found"
    assert child_span.parent is not None, f"Span '{child}' has no parent"
    assert child_span.parent.name == parent, f"Expected parent '{parent}', got '{child_span.parent.name}'"


@then('the span "{name}" should have no parent')
def step_span_has_no_parent(context, name):
    span = context.spans.get(name)
    assert span is not None, f"Span '{name}' not found"
    assert span.parent is None, f"Span '{name}' should have no parent, but has '{span.parent.name}'"


@then('the span "{name}" should have {count:d} child')
@then('the span "{name}" should have {count:d} children')
def step_span_child_count(context, name, count):
    span = context.spans.get(name)
    assert span is not None, f"Span '{name}' not found"
    actual = len(span.children)
    assert actual == count, f"Expected {count} children, got {actual}"


# =============================================================================
# Provider Assertions
# =============================================================================

@then('the provider should have {count:d} span')
@then('the provider should have {count:d} spans')
def step_provider_span_count(context, count):
    actual = len(context.tracing.spans)
    assert actual == count, f"Expected {count} spans, got {actual}"


@then('the provider should have {count:d} root span')
@then('the provider should have {count:d} root spans')
def step_provider_root_span_count(context, count):
    actual = len(context.tracing.get_root_spans())
    assert actual == count, f"Expected {count} root spans, got {actual}"


@then('the provider should have {count:d} spans named "{name}"')
def step_provider_spans_by_name(context, count, name):
    actual = len(context.tracing.get_spans_by_name(name))
    assert actual == count, f"Expected {count} spans named '{name}', got {actual}"


# =============================================================================
# Serialization Assertions
# =============================================================================

@then('the span "{name}" should be convertible to a dictionary')
def step_span_to_dict(context, name):
    span = context.spans.get(name)
    assert span is not None, f"Span '{name}' not found"
    context.span_dict = span.to_dict()
    assert isinstance(context.span_dict, dict), "to_dict() should return a dictionary"


@then("the dictionary should contain the span name")
def step_dict_has_name(context):
    assert "name" in context.span_dict, "Dictionary missing 'name'"
    assert context.span_dict["name"] is not None, "Dictionary 'name' is None"


@then("the dictionary should contain the attributes")
def step_dict_has_attributes(context):
    assert "attributes" in context.span_dict, "Dictionary missing 'attributes'"


@then("the dictionary should contain the events")
def step_dict_has_events(context):
    assert "events" in context.span_dict, "Dictionary missing 'events'"


# =============================================================================
# Helper Functions
# =============================================================================

def _parse_attributes(attrs_str: str) -> dict:
    """Parse attribute string like 'service=\"api\", version=\"1.0\"' into dict."""
    result = {}
    parts = []
    current = ""
    in_quotes = False

    for char in attrs_str:
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
