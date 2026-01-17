"""
Step definitions for persistence-related BDD tests.
"""
import asyncio
import tempfile
import shutil
from pathlib import Path
from behave import given, when, then, use_step_matcher

from graph_of_thought.persistence import InMemoryPersistence, FilePersistence

use_step_matcher("parse")


# =============================================================================
# Persistence Setup Steps
# =============================================================================

@given("a in-memory persistence backend")
def step_in_memory_persistence(context):
    context.persistence = InMemoryPersistence()


@given("a file persistence backend")
def step_file_persistence(context):
    context.temp_dir = tempfile.mkdtemp()
    context.persistence = FilePersistence(context.temp_dir)


# =============================================================================
# Persistence Actions
# =============================================================================

@when('I save the graph with id "{graph_id}" and metadata "{key}" = {value}')
def step_save_graph_with_metadata(context, graph_id, key, value):
    # Parse the value - handle quoted strings
    value = value.strip('"')
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
    context.last_graph_id = graph_id


@when('I save a graph with id "{graph_id}"')
def step_save_graph(context, graph_id):
    asyncio.run(context.persistence.save_graph(
        graph_id=graph_id,
        thoughts={},
        edges=[],
        root_ids=[],
        metadata={},
    ))
    context.last_graph_id = graph_id


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


@when('I try to load graph "{graph_id}"')
def step_try_load_graph(context, graph_id):
    context.loaded = asyncio.run(context.persistence.load_graph(graph_id))


@when('I try to load checkpoint "{cp_id}" for graph "{graph_id}"')
def step_try_load_checkpoint(context, cp_id, graph_id):
    context.checkpoint_loaded = asyncio.run(context.persistence.load_checkpoint(graph_id, cp_id))


# =============================================================================
# Persistence Assertions
# =============================================================================

@then("the loaded graph should have {count:d} thought")
@then("the loaded graph should have {count:d} thoughts")
def step_check_loaded_thoughts(context, count):
    assert len(context.loaded_thoughts) == count, f"Expected {count} thoughts, got {len(context.loaded_thoughts)}"


@then('the loaded metadata should have "{key}" = {value}')
def step_check_loaded_metadata(context, key, value):
    # Handle quoted strings
    value = value.strip('"')
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


@then('a JSON file should exist for graph "{graph_id}"')
def step_check_json_exists(context, graph_id):
    path = Path(context.temp_dir) / f"{graph_id}.json"
    assert path.exists(), f"Expected JSON file at {path}"


@then('the JSON file for "{graph_id}" should not exist')
def step_check_json_not_exists(context, graph_id):
    path = Path(context.temp_dir) / f"{graph_id}.json"
    assert not path.exists(), f"Expected no JSON file at {path}, but it exists"


@then("the load result should be nothing")
def step_check_load_nothing(context):
    assert context.loaded is None, f"Expected None, got {context.loaded}"


@then("the checkpoint load result should be nothing")
def step_check_checkpoint_load_nothing(context):
    assert context.checkpoint_loaded is None, f"Expected None, got {context.checkpoint_loaded}"


# =============================================================================
# Cleanup
# =============================================================================

def after_scenario(context, scenario):
    """Clean up temp directories after each scenario."""
    if hasattr(context, 'temp_dir'):
        shutil.rmtree(context.temp_dir, ignore_errors=True)
