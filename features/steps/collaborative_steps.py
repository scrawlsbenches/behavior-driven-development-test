"""
Step definitions for collaborative project BDD tests.
"""
import tempfile
import shutil
from pathlib import Path
from behave import given, when, then, use_step_matcher

from graph_of_thought.collaborative import (
    CollaborativeProject,
    ProjectNode,
    NodeType,
    ChunkStatus,
    QuestionPriority,
)

use_step_matcher("parse")


# =============================================================================
# Project Setup Steps
# =============================================================================

@given('a new collaborative project named "{name}"')
def step_new_project(context, name):
    # Use a temp directory to avoid polluting the filesystem
    context.temp_dir = tempfile.mkdtemp()
    context.project = CollaborativeProject(
        name=name,
        base_path=Path(context.temp_dir) / name,
        auto_save=False,
    )


@given('a collaborative project with a request "{content}"')
def step_project_with_request(context, content):
    context.temp_dir = tempfile.mkdtemp()
    context.project = CollaborativeProject(
        name="test_project",
        base_path=Path(context.temp_dir) / "test_project",
        auto_save=False,
    )
    context.request_node = context.project.add_request(content)


@given('a blocking question "{question}" exists')
def step_blocking_question_exists(context, question):
    context.question_node = context.project.ask_question(
        question,
        priority=QuestionPriority.BLOCKING,
    )


@given('a blocking question "{question}" blocks chunk "{chunk_name}"')
def step_question_blocks_chunk(context, question, chunk_name):
    context.question_node = context.project.ask_question(
        question,
        priority=QuestionPriority.BLOCKING,
    )
    context.blocked_chunk = context.project.plan_chunk(
        name=chunk_name,
        description=f"Chunk: {chunk_name}",
        estimated_hours=2,
        blocked_by=[context.question_node.id],
    )


@given('a ready chunk "{name}" exists')
def step_ready_chunk_exists(context, name):
    context.chunk_node = context.project.plan_chunk(
        name=name,
        description=f"Chunk: {name}",
        estimated_hours=2,
    )


@given('chunk "{name}" is in progress')
def step_chunk_in_progress(context, name):
    # First create the chunk if it doesn't exist
    if not hasattr(context, 'chunk_node') or context.chunk_node is None:
        context.chunk_node = context.project.plan_chunk(
            name=name,
            description=f"Chunk: {name}",
            estimated_hours=2,
        )
    context.project.start_chunk(context.chunk_node.id)


@given('chunk "{name}" exists')
def step_chunk_exists(context, name):
    chunk = context.project.plan_chunk(
        name=name,
        description=f"Chunk: {name}",
        estimated_hours=2,
    )
    if not hasattr(context, 'chunks'):
        context.chunks = {}
    context.chunks[name] = chunk


@given('chunk "{name}" exists with status "{status}"')
def step_chunk_exists_with_status(context, name, status):
    chunk = context.project.plan_chunk(
        name=name,
        description=f"Chunk: {name}",
        estimated_hours=2,
    )
    if not hasattr(context, 'chunks'):
        context.chunks = {}
    context.chunks[name] = chunk

    # Set status if needed
    if status == "COMPLETE":
        context.project.start_chunk(chunk.id)
        context.project.complete_chunk(chunk.id, artifacts=[])


@given('chunk "{dependent}" depends on "{dependency}"')
def step_chunk_depends_on(context, dependent, dependency):
    dep_chunk = context.chunks.get(dependency)
    if dep_chunk is None:
        dep_chunk = context.project.plan_chunk(
            name=dependency,
            description=f"Chunk: {dependency}",
            estimated_hours=2,
        )
        if not hasattr(context, 'chunks'):
            context.chunks = {}
        context.chunks[dependency] = dep_chunk

    dependent_chunk = context.project.plan_chunk(
        name=dependent,
        description=f"Chunk: {dependent}",
        estimated_hours=2,
        depends_on=[dep_chunk.id],
    )
    context.chunks[dependent] = dependent_chunk


@given('a collaborative project with an active session on chunk "{name}"')
def step_project_with_active_session(context, name):
    context.temp_dir = tempfile.mkdtemp()
    context.project = CollaborativeProject(
        name="test_project",
        base_path=Path(context.temp_dir) / "test_project",
        auto_save=True,  # Enable auto_save for session persistence
    )
    context.project.add_request("Test request")
    context.chunk_node = context.project.plan_chunk(
        name=name,
        description=f"Chunk: {name}",
        estimated_hours=2,
    )
    context.project.start_chunk(context.chunk_node.id)


# =============================================================================
# Action Steps
# =============================================================================

@when('I add a request "{content}"')
def step_add_request(context, content):
    context.request_node = context.project.add_request(content)


@when('I ask a blocking question "{question}"')
def step_ask_blocking_question(context, question):
    context.question_node = context.project.ask_question(
        question,
        priority=QuestionPriority.BLOCKING,
    )


@when('I answer the question with "{answer}"')
def step_answer_question(context, answer):
    context.decision_node = context.project.answer_question(
        context.question_node.id,
        answer,
    )


@when('I plan a chunk "{name}" with estimated hours {hours:d}')
def step_plan_chunk(context, name, hours):
    context.chunk_node = context.project.plan_chunk(
        name=name,
        description=f"Chunk: {name}",
        estimated_hours=hours,
    )


@when('I try to start chunk "{name}"')
def step_try_start_chunk(context, name):
    try:
        context.project.start_chunk(context.blocked_chunk.id)
        context.start_succeeded = True
    except Exception as e:
        context.start_succeeded = False
        context.start_error = e


@when('I start chunk "{name}"')
def step_start_chunk(context, name):
    context.project.start_chunk(context.chunk_node.id)


@when('I complete chunk "{name}" with artifacts "{artifacts}"')
def step_complete_chunk_with_artifacts(context, name, artifacts):
    artifact_list = [a.strip() for a in artifacts.split(",")]
    context.project.complete_chunk(context.chunk_node.id, artifacts=artifact_list)


@when('I record a discovery "{content}"')
def step_record_discovery(context, content):
    context.discovery_node = context.project.record_discovery(
        content,
        chunk_id=context.chunk_node.id,
    )


@when('I record discovery "{content}" that affects "{chunk_name}"')
def step_record_discovery_affecting(context, content, chunk_name):
    affected_chunk = context.chunks.get(chunk_name)
    context.discovery_node = context.project.record_discovery(
        content,
        chunk_id=context.chunk_node.id,
        affects_chunks=[affected_chunk.id] if affected_chunk else [],
    )


@when("I serialize and restore the project")
def step_serialize_and_restore(context):
    # Save current state
    context.project._save()

    # Create a new project instance that loads from the saved state
    context.restored_project = CollaborativeProject(
        name=context.project.name,
        base_path=context.project.base_path,
        auto_save=False,
    )


@when("I simulate context loss and resume")
def step_simulate_context_loss(context):
    # Save current state
    context.project._save()

    # Create a new project instance (simulating restart)
    context.restored_project = CollaborativeProject(
        name=context.project.name,
        base_path=context.project.base_path,
        auto_save=False,
    )


# =============================================================================
# Assertion Steps
# =============================================================================

@then("the project should have {count:d} node")
@then("the project should have {count:d} nodes")
def step_check_node_count(context, count):
    assert len(context.project._nodes) == count, \
        f"Expected {count} nodes, got {len(context.project._nodes)}"


@then('the node should be of type "{node_type}"')
def step_check_node_type(context, node_type):
    expected_type = NodeType[node_type]
    assert context.request_node.node_type == expected_type, \
        f"Expected type {node_type}, got {context.request_node.node_type}"


@then('the node should have content "{content}"')
def step_check_node_content(context, content):
    assert context.request_node.content == content, \
        f"Expected content '{content}', got '{context.request_node.content}'"


@then('there should be a question with priority "{priority}"')
def step_check_question_priority(context, priority):
    expected_priority = QuestionPriority[priority]
    assert context.question_node.priority == expected_priority, \
        f"Expected priority {priority}, got {context.question_node.priority}"


@then("a decision node should be created")
def step_check_decision_created(context):
    assert context.decision_node is not None
    assert context.decision_node.node_type == NodeType.DECISION


@then("the decision should be linked to the question")
def step_check_decision_linked(context):
    # Check that an edge exists from decision to question
    edges = [e for e in context.project._graph.edges
             if e.source_id == context.decision_node.id
             and e.target_id == context.question_node.id]
    assert len(edges) > 0, "Decision should be linked to question"


@then('a chunk should be created with status "{status}"')
def step_check_chunk_created_with_status(context, status):
    expected_status = ChunkStatus[status]
    assert context.chunk_node.status == expected_status, \
        f"Expected status {status}, got {context.chunk_node.status}"


@then("the chunk should have estimated hours {hours:d}")
def step_check_chunk_hours(context, hours):
    assert context.chunk_node.estimated_hours == hours, \
        f"Expected {hours} hours, got {context.chunk_node.estimated_hours}"


@then('the chunk should remain in status "{status}"')
def step_check_chunk_remains_status(context, status):
    expected_status = ChunkStatus[status]
    # Refresh the node from the project
    chunk = context.project._nodes[context.blocked_chunk.id]
    assert chunk.status == expected_status, \
        f"Expected status {status}, got {chunk.status}"


@then('chunk "{name}" should have status "{status}"')
def step_check_named_chunk_status(context, name, status):
    expected_status = ChunkStatus[status]
    chunk = context.chunks.get(name) or context.blocked_chunk
    # Refresh from project
    chunk = context.project._nodes[chunk.id]
    assert chunk.status == expected_status, \
        f"Expected chunk {name} to have status {status}, got {chunk.status}"


@then("a session should be active")
def step_check_session_active(context):
    assert context.project._session is not None, "Session should be active"


@then('the chunk should have status "{status}"')
def step_check_chunk_status(context, status):
    expected_status = ChunkStatus[status]
    chunk = context.project._nodes[context.chunk_node.id]
    assert chunk.status == expected_status, \
        f"Expected status {status}, got {chunk.status}"


@then("{count:d} artifact nodes should be created")
def step_check_artifact_count(context, count):
    artifacts = [n for n in context.project._nodes.values()
                 if n.node_type == NodeType.ARTIFACT]
    assert len(artifacts) == count, \
        f"Expected {count} artifacts, got {len(artifacts)}"


@then("a discovery node should be created")
def step_check_discovery_created(context):
    assert context.discovery_node is not None
    assert context.discovery_node.node_type == NodeType.DISCOVERY


@then("the discovery should be linked to the chunk")
def step_check_discovery_linked_to_chunk(context):
    edges = [e for e in context.project._graph.edges
             if e.source_id == context.discovery_node.id]
    assert len(edges) > 0, "Discovery should be linked to chunk"


@then('chunk "{name}" should be marked as affected')
def step_check_chunk_affected(context, name):
    chunk = context.chunks[name]
    # Check for AFFECTS edge from discovery to chunk
    edges = [e for e in context.project._graph.edges
             if e.target_id == chunk.id
             and e.source_id == context.discovery_node.id]
    assert len(edges) > 0, f"Chunk {name} should be marked as affected"


@then("the restored project should have {count:d} nodes")
def step_check_restored_node_count(context, count):
    assert len(context.restored_project._nodes) == count, \
        f"Expected {count} nodes, got {len(context.restored_project._nodes)}"


@then('the request content should be "{content}"')
def step_check_restored_request_content(context, content):
    request_node = context.restored_project._nodes[context.restored_project._request_id]
    assert request_node.content == content, \
        f"Expected content '{content}', got '{request_node.content}'"


@then("the session should be restored")
def step_check_session_restored(context):
    assert context.restored_project._session is not None, "Session should be restored"


@then('the current chunk should be "{name}"')
def step_check_current_chunk(context, name):
    session = context.restored_project._session
    assert session.current_chunk_id is not None, "Should have current chunk"
    chunk = context.restored_project._nodes[session.current_chunk_id]
    assert name in chunk.content, f"Expected current chunk '{name}', got '{chunk.content}'"


# =============================================================================
# Cleanup
# =============================================================================

def after_scenario(context, scenario):
    """Clean up temp directories after each scenario."""
    if hasattr(context, 'temp_dir'):
        shutil.rmtree(context.temp_dir, ignore_errors=True)
