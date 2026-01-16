"""
Step definitions for persistence-related BDD tests.
"""
import asyncio
from behave import given, when, then, use_step_matcher

from graph_of_thought.persistence import InMemoryPersistence

use_step_matcher("parse")


# =============================================================================
# Persistence Setup Steps
# =============================================================================

@given("an in-memory persistence backend")
def step_in_memory_persistence(context):
    context.persistence = InMemoryPersistence()


# =============================================================================
# Persistence Actions
# =============================================================================

@when('I save the graph with id "{graph_id}" and metadata "{key}" = {value}')
def step_save_graph_with_metadata(context, graph_id, key, value):
    # Parse the value
    if value == "True":
        parsed_value = True
    elif value == "False":
        parsed_value = False
    else:
        parsed_value = value

    asyncio.run(context.persistence.save_graph(
        graph_id=graph_id,
        thoughts=context.graph.thoughts,
        edges=context.graph.edges,
        root_ids=context.graph.root_ids,
        metadata={key: parsed_value},
    ))


@when('I save a graph with id "{graph_id}"')
def step_save_graph(context, graph_id):
    asyncio.run(context.persistence.save_graph(
        graph_id=graph_id,
        thoughts={},
        edges=[],
        root_ids=[],
        metadata={},
    ))


@when('I load the graph with id "{graph_id}"')
def step_load_graph(context, graph_id):
    context.loaded = asyncio.run(context.persistence.load_graph(graph_id))
    if context.loaded:
        context.loaded_thoughts, context.loaded_edges, context.loaded_root_ids, context.loaded_metadata = context.loaded


@when('I save a checkpoint with id "{cp_id}" and search state "{key}" = {value:d}')
def step_save_checkpoint(context, cp_id, key, value):
    asyncio.run(context.persistence.save_checkpoint(
        graph_id="test",
        checkpoint_id=cp_id,
        thoughts=context.graph.thoughts,
        edges=context.graph.edges,
        root_ids=context.graph.root_ids,
        search_state={key: value},
    ))


@when('I load the checkpoint "{cp_id}"')
def step_load_checkpoint(context, cp_id):
    context.loaded = asyncio.run(context.persistence.load_checkpoint("test", cp_id))
    if context.loaded:
        context.loaded_thoughts, context.loaded_edges, context.loaded_root_ids, context.loaded_search_state = context.loaded


@when('I delete the graph with id "{graph_id}"')
def step_delete_graph(context, graph_id):
    context.deleted = asyncio.run(context.persistence.delete_graph(graph_id))


# =============================================================================
# Persistence Assertions
# =============================================================================

@then("the loaded graph should have {count:d} thought")
@then("the loaded graph should have {count:d} thoughts")
def step_check_loaded_thoughts(context, count):
    assert len(context.loaded_thoughts) == count, f"Expected {count} thoughts, got {len(context.loaded_thoughts)}"


@then('the loaded metadata should have "{key}" = {value}')
def step_check_loaded_metadata(context, key, value):
    if value == "True":
        expected = True
    elif value == "False":
        expected = False
    else:
        expected = value
    assert context.loaded_metadata[key] == expected, f"Expected {key}={expected}, got {context.loaded_metadata[key]}"


@then('the loaded search state should have "{key}" = {value:d}')
def step_check_loaded_search_state(context, key, value):
    assert context.loaded_search_state[key] == value, f"Expected {key}={value}, got {context.loaded_search_state[key]}"


@then('loading graph "{graph_id}" should return nothing')
def step_check_graph_deleted(context, graph_id):
    loaded = asyncio.run(context.persistence.load_graph(graph_id))
    assert loaded is None, f"Expected None, got {loaded}"
