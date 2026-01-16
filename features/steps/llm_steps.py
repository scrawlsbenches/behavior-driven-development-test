"""
Step definitions for LLM integration BDD tests.
"""
import asyncio
from behave import given, when, then, use_step_matcher

from graph_of_thought.llm import (
    PromptTemplate,
    DEFAULT_GENERATION_TEMPLATE,
    DEFAULT_EVALUATION_TEMPLATE,
    DEFAULT_VERIFICATION_TEMPLATE,
    BaseLLMGenerator,
    BaseLLMEvaluator,
    BaseLLMVerifier,
)

use_step_matcher("parse")


# =============================================================================
# Mock LLM Classes for Testing
# =============================================================================

class MockLLMGenerator(BaseLLMGenerator):
    """Mock generator that returns predefined responses."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mock_response = "[]"

    def set_response(self, response: str):
        self.mock_response = response

    async def _call_llm(self, system: str, user: str) -> str:
        return self.mock_response


class MockLLMEvaluator(BaseLLMEvaluator):
    """Mock evaluator that returns predefined responses."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mock_response = '{"score": 0.5}'

    def set_response(self, response: str):
        self.mock_response = response

    async def _call_llm(self, system: str, user: str) -> str:
        return self.mock_response


class MockLLMVerifier(BaseLLMVerifier):
    """Mock verifier that returns predefined responses."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mock_response = '{"is_valid": true, "confidence": 1.0, "issues": []}'

    def set_response(self, response: str):
        self.mock_response = response

    async def _call_llm(self, system: str, user: str) -> str:
        return self.mock_response


# =============================================================================
# Helper Functions
# =============================================================================

def create_mock_context():
    """Create a minimal SearchContext for testing."""
    from dataclasses import dataclass, field

    @dataclass
    class MockContext:
        current_depth: int = 0
        path_to_root: list = field(default_factory=list)
        siblings: list = field(default_factory=list)
        metadata: dict = field(default_factory=dict)

    return MockContext()


def execute_llm_response(context, response):
    """Execute the appropriate LLM component with the given response."""
    mock_context = create_mock_context()

    if hasattr(context, 'generator') and context.generator is not None:
        context.generator.set_response(response)
        context.thoughts = asyncio.run(context.generator.generate("test", mock_context))
    elif hasattr(context, 'evaluator') and context.evaluator is not None:
        context.evaluator.set_response(response)
        context.score = asyncio.run(context.evaluator.evaluate("test", mock_context))
    elif hasattr(context, 'verifier') and context.verifier is not None:
        context.verifier.set_response(response)
        context.verification = asyncio.run(context.verifier.verify("test", mock_context))


# =============================================================================
# Prompt Templates
# =============================================================================

@given('a prompt template with system "{system}" and user "{user}"')
def step_custom_template(context, system, user):
    context.template = PromptTemplate(system=system, user=user)


@when('I format the template with topic "{topic}"')
def step_format_template(context, topic):
    context.formatted_system, context.formatted_user = context.template.format(topic=topic)


@then('the formatted user prompt should contain "{text}"')
def step_check_formatted_user(context, text):
    assert text in context.formatted_user


@given("the default generation template")
def step_default_gen_template(context):
    context.template = DEFAULT_GENERATION_TEMPLATE


@given("the default evaluation template")
def step_default_eval_template(context):
    context.template = DEFAULT_EVALUATION_TEMPLATE


@given("the default verification template")
def step_default_verify_template(context):
    context.template = DEFAULT_VERIFICATION_TEMPLATE


@then('the template should have placeholder "{placeholder}"')
def step_check_placeholder(context, placeholder):
    full_template = context.template.system + context.template.user
    assert "{" + placeholder + "}" in full_template, \
        f"Placeholder {{{placeholder}}} not found in template"


# =============================================================================
# Mock Components Setup
# =============================================================================

@given("a mock LLM generator")
def step_mock_generator(context):
    context.generator = MockLLMGenerator()
    context.evaluator = None
    context.verifier = None


@given("a mock LLM evaluator")
def step_mock_evaluator(context):
    context.evaluator = MockLLMEvaluator()
    context.generator = None
    context.verifier = None


@given("a mock LLM verifier")
def step_mock_verifier(context):
    context.verifier = MockLLMVerifier()
    context.generator = None
    context.evaluator = None


# =============================================================================
# LLM Response Handling (Unified)
# =============================================================================

@when("the LLM returns '{response}'")
def step_llm_returns(context, response):
    execute_llm_response(context, response)


@when("the LLM returns a markdown code block with '{json_content}'")
def step_llm_returns_markdown(context, json_content):
    response = f"```json\n{json_content}\n```"
    execute_llm_response(context, response)


@when('the LLM returns plain text lines "{lines}"')
def step_llm_returns_lines(context, lines):
    response = lines.replace("\\n", "\n")
    execute_llm_response(context, response)


# =============================================================================
# Generator Assertions
# =============================================================================

@then("the generator should produce {count:d} thoughts")
def step_check_thought_count(context, count):
    assert len(context.thoughts) == count, \
        f"Expected {count} thoughts, got {len(context.thoughts)}"


@then('thought {index:d} should be "{content}"')
def step_check_thought_content(context, index, content):
    assert context.thoughts[index - 1] == content


# =============================================================================
# Evaluator Assertions
# =============================================================================

@then("the evaluation score should be {score:f}")
def step_check_eval_score(context, score):
    assert abs(context.score - score) < 0.01, \
        f"Expected score {score}, got {context.score}"


# =============================================================================
# Verifier Assertions
# =============================================================================

@then("the verification should be valid")
def step_verification_valid(context):
    assert context.verification.is_valid is True


@then("the verification should be invalid")
def step_verification_invalid(context):
    assert context.verification.is_valid is False


@then("the verification confidence should be {confidence:f}")
def step_check_verification_confidence(context, confidence):
    assert abs(context.verification.confidence - confidence) < 0.01


@then("the verification should have {count:d} issue")
@then("the verification should have {count:d} issues")
def step_check_issue_count(context, count):
    assert len(context.verification.issues) == count


# =============================================================================
# Base Class Configuration
# =============================================================================

@given("a base LLM generator with temperature {temp:f} and max_tokens {tokens:d}")
def step_configured_generator(context, temp, tokens):
    context.generator = MockLLMGenerator(temperature=temp, max_tokens=tokens)
    context.evaluator = None
    context.verifier = None


@given("a base LLM evaluator with temperature {temp:f} and max_tokens {tokens:d}")
def step_configured_evaluator(context, temp, tokens):
    context.evaluator = MockLLMEvaluator(temperature=temp, max_tokens=tokens)
    context.generator = None
    context.verifier = None


@given("a base LLM generator with num_children {count:d}")
def step_generator_num_children(context, count):
    context.generator = MockLLMGenerator(num_children=count)
    context.evaluator = None
    context.verifier = None


@then("the generator should have temperature {temp:f}")
def step_check_gen_temp(context, temp):
    assert abs(context.generator.temperature - temp) < 0.01


@then("the generator should have max_tokens {tokens:d}")
def step_check_gen_tokens(context, tokens):
    assert context.generator.max_tokens == tokens


@then("the evaluator should have temperature {temp:f}")
def step_check_eval_temp(context, temp):
    assert abs(context.evaluator.temperature - temp) < 0.01


@then("the evaluator should have max_tokens {tokens:d}")
def step_check_eval_tokens(context, tokens):
    assert context.evaluator.max_tokens == tokens


@then("the generator should produce up to {count:d} children")
def step_check_num_children(context, count):
    assert context.generator.num_children == count
