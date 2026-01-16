"""
Step definitions for verification BDD tests.
"""
import time
from behave import given, when, then, use_step_matcher

from graph_of_thought.core import SearchContext, Thought
from graph_of_thought.core.defaults import InMemoryVerifier

use_step_matcher("parse")


# =============================================================================
# Verifier Setup
# =============================================================================

@given("an in-memory verifier")
def step_in_memory_verifier(context):
    context.verifier = InMemoryVerifier()
    context.verification_result = None


@given("an in-memory verifier configured to fail")
def step_verifier_configured_to_fail(context):
    context.verifier = InMemoryVerifier(default_valid=False, default_confidence=0.0)
    context.verification_result = None


@given("an in-memory verifier with confidence {confidence:g}")
def step_verifier_with_confidence(context, confidence):
    context.verifier = InMemoryVerifier(default_confidence=confidence)
    context.verification_result = None


@given('an in-memory verifier with issues "{issue1}", "{issue2}"')
def step_verifier_with_issues(context, issue1, issue2):
    context.verifier = InMemoryVerifier(default_issues=[issue1, issue2])
    context.verification_result = None


use_step_matcher("re")


@given(r'an in-memory verifier with metadata (?P<metadata>.+)')
def step_verifier_with_metadata(context, metadata):
    parsed = _parse_key_values(metadata)
    context.verifier = InMemoryVerifier(default_metadata=parsed)
    context.verification_result = None


use_step_matcher("parse")


# =============================================================================
# Rules Configuration
# =============================================================================

@given('a rule that rejects content containing "{substring}"')
def step_add_rejection_rule(context, substring):
    def rule(content, ctx):
        if content and substring in str(content):
            return False, f"Content contains '{substring}'"
        return True, None
    context.verifier.add_rule(rule)


# =============================================================================
# Verification Actions
# =============================================================================

@when('I verify content "{content}"')
def step_verify_content(context, content):
    import asyncio
    # Create a minimal search context for testing
    search_context = _create_test_context()
    context.verification_result = asyncio.run(
        context.verifier.verify(content, search_context)
    )


@when('I verify content ""')
def step_verify_empty_content(context):
    import asyncio
    search_context = _create_test_context()
    context.verification_result = asyncio.run(
        context.verifier.verify("", search_context)
    )


@when("I verify None content")
def step_verify_none_content(context):
    import asyncio
    search_context = _create_test_context()
    context.verification_result = asyncio.run(
        context.verifier.verify(None, search_context)
    )


@when('I verify content "{content}" with context depth={depth:d}')
def step_verify_with_context(context, content, depth):
    import asyncio
    search_context = _create_test_context(depth=depth)
    context.verification_result = asyncio.run(
        context.verifier.verify(content, search_context)
    )


@when("I reset the verifier")
def step_reset_verifier(context):
    context.verifier.reset()


# =============================================================================
# Result Assertions
# =============================================================================

@then("the verifier result should pass")
def step_verifier_result_passes(context):
    assert context.verification_result is not None, "No verification result"
    assert context.verification_result.is_valid, "Expected verification to pass"


@then("the verifier result should fail")
def step_verifier_result_fails(context):
    assert context.verification_result is not None, "No verification result"
    assert not context.verification_result.is_valid, "Expected verification to fail"


@then("the verifier result confidence should be {confidence:g}")
def step_check_verifier_confidence(context, confidence):
    assert context.verification_result is not None, "No verification result"
    actual = context.verification_result.confidence
    assert abs(actual - confidence) < 0.001, f"Expected confidence {confidence}, got {actual}"


@then("the verifier result should have {count:d} issues")
def step_check_verifier_issue_count(context, count):
    assert context.verification_result is not None, "No verification result"
    actual = len(context.verification_result.issues)
    assert actual == count, f"Expected {count} issues, got {actual}"


@then('the verifier result should have issue "{issue}"')
def step_check_verifier_has_issue(context, issue):
    assert context.verification_result is not None, "No verification result"
    assert issue in context.verification_result.issues, \
        f"Expected issue '{issue}' not found in {context.verification_result.issues}"


@then('the verifier result metadata should have "{key}" with value "{value}"')
def step_check_verifier_metadata(context, key, value):
    assert context.verification_result is not None, "No verification result"
    metadata = context.verification_result.metadata
    assert key in metadata, f"Metadata missing key '{key}'"
    assert str(metadata[key]) == value, f"Expected {key}='{value}', got '{metadata[key]}'"


# =============================================================================
# History Assertions
# =============================================================================

@then("the verifier should have {count:d} verification calls")
@then("the verifier should have {count:d} verification call")
def step_check_call_count(context, count):
    actual = len(context.verifier.history)
    assert actual == count, f"Expected {count} calls, got {actual}"


@then("I should be able to get verification history")
def step_get_history(context):
    context.history = context.verifier.history
    assert context.history is not None


@then("the history should contain {count:d} entries")
def step_check_history_count(context, count):
    actual = len(context.history)
    assert actual == count, f"Expected {count} entries, got {actual}"


@then('the last verification should have content "{content}"')
def step_check_last_content(context, content):
    history = context.verifier.history
    assert len(history) > 0, "No verification history"
    last = history[-1]
    assert last["content"] == content, f"Expected content '{content}', got '{last['content']}'"


@then("the last verification should have result is_valid={valid}")
def step_check_last_result(context, valid):
    expected = valid == "True"
    history = context.verifier.history
    assert len(history) > 0, "No verification history"
    last = history[-1]
    actual = last["result"].is_valid
    assert actual == expected, f"Expected is_valid={expected}, got {actual}"


@then("the last verification should have a timestamp")
def step_check_last_timestamp(context):
    history = context.verifier.history
    assert len(history) > 0, "No verification history"
    last = history[-1]
    assert "timestamp" in last, "Missing timestamp in history entry"
    assert last["timestamp"] is not None, "Timestamp is None"


@then("the last verification should have context with depth {depth:d}")
def step_check_last_context_depth(context, depth):
    history = context.verifier.history
    assert len(history) > 0, "No verification history"
    last = history[-1]
    ctx = last["context"]
    assert ctx.depth == depth, f"Expected depth {depth}, got {ctx.depth}"


@then("the verification history should show pass, fail, pass")
def step_check_history_pattern(context):
    history = context.verifier.history
    assert len(history) >= 3, f"Expected at least 3 entries, got {len(history)}"
    results = [h["result"].is_valid for h in history[-3:]]
    expected = [True, False, True]
    assert results == expected, f"Expected {expected}, got {results}"


# =============================================================================
# Helper Functions
# =============================================================================

def _create_test_context(depth: int = 5) -> SearchContext:
    """Create a minimal SearchContext for testing."""
    root_thought = Thought(content="test", depth=0)
    return SearchContext(
        current_thought=root_thought,
        path_to_root=[root_thought],
        depth=depth,
        tokens_remaining=None,
        time_remaining_seconds=None,
    )


def _parse_key_values(kv_str: str) -> dict:
    """Parse key=value pairs like 'source=\"test\", verified_at=\"2024-01-15\"'."""
    result = {}
    parts = []
    current = ""
    in_quotes = False

    for char in kv_str:
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
