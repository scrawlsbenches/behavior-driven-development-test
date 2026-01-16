"""
Step definitions for configuration-related BDD tests.
"""
from behave import given, when, then, use_step_matcher

from graph_of_thought import GraphOfThought, GraphConfig

use_step_matcher("parse")


# =============================================================================
# Configuration Setup Steps
# =============================================================================

@given("a configuration dictionary with:")
def step_config_dict(context):
    context.config_dict = {
        "allow_cycles": False,
        "limits": {},
        "search": {},
    }
    for row in context.table:
        key = row["key"]
        value = row["value"]

        if key == "allow_cycles":
            context.config_dict["allow_cycles"] = value.strip() == "True"
        elif key == "max_depth":
            context.config_dict["limits"]["max_depth"] = int(value.strip())
        elif key == "max_thoughts":
            context.config_dict["limits"]["max_thoughts"] = int(value.strip())
        elif key == "beam_width":
            context.config_dict["search"]["beam_width"] = int(value.strip())


@given("a config with max_thoughts {count:d}")
def step_config_max_thoughts(context, count):
    context.graph_config = GraphConfig()
    context.graph_config.limits.max_thoughts = count


@given("the config has beam_width {width:d}")
def step_config_beam_width(context, width):
    context.graph_config.search.beam_width = width


@given("a config with max_depth {depth:d}")
def step_config_max_depth(context, depth):
    context.graph_config = GraphConfig()
    context.graph_config.limits.max_depth = depth


@given("a graph with the config")
def step_graph_with_config(context):
    context.graph = GraphOfThought[str](config=context.graph_config)


# =============================================================================
# Configuration Actions
# =============================================================================

@when("I create a config from the dictionary")
def step_create_config_from_dict(context):
    context.graph_config = GraphConfig.from_dict(context.config_dict)


@when("I validate the config")
def step_validate_config(context):
    context.validation_issues = context.graph_config.validate()


@when("I serialize the config to JSON")
def step_serialize_config_json(context):
    context.json_str = context.graph_config.to_json()


@when("I deserialize the config from JSON")
def step_deserialize_config_json(context):
    context.restored_config = GraphConfig.from_json(context.json_str)


# =============================================================================
# Configuration Assertions
# =============================================================================

@then("the config should have allow_cycles {value}")
def step_check_allow_cycles(context, value):
    expected = value == "True"
    assert context.graph_config.allow_cycles == expected, f"Expected allow_cycles={expected}"


@then("the config should have max_depth {depth:d}")
def step_check_config_max_depth(context, depth):
    assert context.graph_config.limits.max_depth == depth, f"Expected max_depth={depth}"


@then("the config should have max_thoughts {count:d}")
def step_check_config_max_thoughts(context, count):
    assert context.graph_config.limits.max_thoughts == count, f"Expected max_thoughts={count}"


@then("the config should have beam_width {width:d}")
def step_check_config_beam_width(context, width):
    assert context.graph_config.search.beam_width == width, f"Expected beam_width={width}"


@then("there should be at least {count:d} validation issues")
def step_check_validation_issues(context, count):
    assert len(context.validation_issues) >= count, f"Expected at least {count} issues, got {len(context.validation_issues)}"


@then("the restored config should have max_depth {depth:d}")
def step_check_restored_config_depth(context, depth):
    assert context.restored_config.limits.max_depth == depth, f"Expected max_depth={depth}"
