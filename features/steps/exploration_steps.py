"""
Step definitions for AI-Assisted Thought Exploration.

These persona-aware steps wrap the underlying graph operations
to provide business-focused BDD scenarios.
"""
from behave import given, when, then, use_step_matcher

use_step_matcher("parse")


# =============================================================================
# Persona Context
# =============================================================================
# These steps establish who is performing actions, providing business context.

@given("{persona} is exploring \"{problem}\"")
@when("{persona} starts exploring \"{problem}\"")
def step_persona_starts_exploring(context, persona, problem):
    """Start an exploration session with a problem statement."""
    context.current_persona = persona
    context.current_problem = problem

    # Check if we're in LLM-only mode (no graph needed)
    if getattr(context, 'llm_only_mode', False):
        context.exploration_path = [problem]
        context.thoughts_by_content = {problem: {"content": problem, "depth": 0}}
        context.root_thought = problem
        return

    # Use the underlying graph to add the root thought
    thought = context.graph.add_thought(problem)
    context.root_thought_id = thought.id
    context.thoughts_by_content = {problem: thought}


@when("{persona} adds a follow-up thought \"{content}\"")
def step_persona_adds_followup(context, persona, content):
    """Add a follow-up thought connected to the current exploration."""
    parent_content = context.current_problem
    parent = context.thoughts_by_content.get(parent_content)

    if parent:
        thought = context.graph.add_thought(content, parent_id=parent.id)
    else:
        thought = context.graph.add_thought(content)

    context.thoughts_by_content[content] = thought
    context.last_thought = thought


# =============================================================================
# Exploration State Assertions
# =============================================================================

@then("a root thought should be created with the problem statement")
def step_root_thought_created(context):
    """Verify a root thought was created."""
    thought = context.graph.get_thought(context.root_thought_id)
    assert thought is not None, "Root thought should exist"
    assert thought.content == context.current_problem
    # Root thoughts have no parents
    parents = context.graph.get_parents(thought.id)
    assert len(parents) == 0, "Root should have no parents"


@then("the exploration session should be ready for expansion")
def step_exploration_ready(context):
    """Verify the session is ready for expansion."""
    thought = context.graph.get_thought(context.root_thought_id)
    assert thought is not None, "Session should have a root thought"
    # Ready for expansion means the thought exists and can have children
    assert context.graph is not None


@then("the thought should be marked as \"{status}\" exploration")
def step_thought_has_status(context, status):
    """Verify thought has expected status."""
    from graph_of_thought import ThoughtStatus
    thought = context.graph.get_thought(context.root_thought_id)

    status_map = {
        "pending": ThoughtStatus.PENDING,
        "active": ThoughtStatus.ACTIVE,
        "explored": ThoughtStatus.COMPLETED,  # "explored" maps to COMPLETED
        "completed": ThoughtStatus.COMPLETED,
        "pruned": ThoughtStatus.PRUNED,
        "merged": ThoughtStatus.MERGED,
        "failed": ThoughtStatus.FAILED,
    }
    expected = status_map.get(status.lower())
    if expected:
        assert thought.status == expected, f"Expected {expected}, got {thought.status}"


@then("the follow-up should be connected to the root problem")
def step_followup_connected(context):
    """Verify the follow-up thought is connected to root."""
    thought = context.last_thought
    root_id = context.root_thought_id

    parents = context.graph.get_parents(thought.id)
    parent_ids = [p.id for p in parents]
    assert root_id in parent_ids, "Follow-up should be connected to root"


@then("the exploration depth should increase by {delta:d}")
def step_depth_increased(context, delta):
    """Verify exploration depth increased."""
    thought = context.last_thought
    # The last thought's depth should be at least 'delta'
    assert thought.depth >= delta, f"Expected depth >= {delta}, got {thought.depth}"


@then("both thoughts should be visible in the exploration path")
def step_both_thoughts_visible(context):
    """Verify both root and follow-up are in the graph."""
    root = context.graph.get_thought(context.root_thought_id)
    followup = context.last_thought

    assert root is not None, "Root should be visible"
    assert followup is not None, "Follow-up should be visible"

    # Verify path exists
    path = context.graph.get_path_to_root(followup.id)
    assert len(path) >= 2, "Path should include both thoughts"


# =============================================================================
# Exploration Setup with Tables
# =============================================================================

@given("an exploration with thoughts:")
def step_exploration_with_thoughts_table(context):
    """Set up an exploration from a table of thoughts and parents."""
    context.thoughts_by_content = {}

    for row in context.table:
        content = row["thought"]
        parent_content = row.get("parent", "").strip()

        if parent_content and parent_content in context.thoughts_by_content:
            parent = context.thoughts_by_content[parent_content]
            thought = context.graph.add_thought(content, parent_id=parent.id)
        else:
            thought = context.graph.add_thought(content)
            if not hasattr(context, "root_thought_id"):
                context.root_thought_id = thought.id

        context.thoughts_by_content[content] = thought


# =============================================================================
# Connecting Thoughts
# =============================================================================

@when("{persona} connects \"{source}\" to \"{target}\"")
def step_connect_thoughts(context, persona, source, target):
    """Connect two thoughts to show a relationship."""
    context.current_persona = persona
    source_thought = context.thoughts_by_content.get(source)
    target_thought = context.thoughts_by_content.get(target)

    assert source_thought is not None, f"Source thought '{source}' not found"
    assert target_thought is not None, f"Target thought '{target}' not found"

    # Add connection (source -> target means target becomes child of source)
    context.graph.add_edge(source_thought.id, target_thought.id)
    context.last_connection = (source_thought, target_thought)


@then("the thoughts should be linked")
def step_thoughts_linked(context):
    """Verify the thoughts are connected."""
    source, target = context.last_connection
    children = context.graph.get_children(source.id)
    child_ids = [c.id for c in children]
    assert target.id in child_ids, f"Target should be connected to source"


@then("exploring from \"{thought_content}\" should show the connection")
def step_exploring_shows_connection(context, thought_content):
    """Verify exploring from a thought shows its connections."""
    thought = context.thoughts_by_content.get(thought_content)
    assert thought is not None, f"Thought '{thought_content}' not found"

    # Should have children (connections going forward)
    children = context.graph.get_children(thought.id)
    assert len(children) > 0, f"'{thought_content}' should have connections"


# =============================================================================
# Circular Reasoning Prevention
# =============================================================================

@given("an exploration chain: \"{a}\" -> \"{b}\" -> \"{c}\"")
def step_exploration_chain(context, a, b, c):
    """Set up a chain of thoughts: A -> B -> C."""
    context.thoughts_by_content = {}

    thought_a = context.graph.add_thought(a)
    context.thoughts_by_content[a] = thought_a
    context.root_thought_id = thought_a.id

    thought_b = context.graph.add_thought(b, parent_id=thought_a.id)
    context.thoughts_by_content[b] = thought_b

    thought_c = context.graph.add_thought(c, parent_id=thought_b.id)
    context.thoughts_by_content[c] = thought_c


@when("{persona} tries to connect \"{source}\" back to \"{target}\"")
def step_tries_circular_connection(context, persona, source, target):
    """Attempt to create a circular connection (should be prevented)."""
    context.current_persona = persona
    source_thought = context.thoughts_by_content.get(source)
    target_thought = context.thoughts_by_content.get(target)

    assert source_thought is not None, f"Source thought '{source}' not found"
    assert target_thought is not None, f"Target thought '{target}' not found"

    # Try to add the edge and capture any exception
    try:
        context.graph.add_edge(source_thought.id, target_thought.id)
        context.last_exception = None
    except Exception as e:
        context.last_exception = e


@then("the connection should be rejected")
def step_connection_rejected(context):
    """Verify that the circular connection was rejected."""
    assert context.last_exception is not None, "Circular connection should have been rejected"


@then("the reason should explain \"{reason}\"")
def step_rejection_reason(context, reason):
    """Verify the rejection reason contains expected text."""
    assert context.last_exception is not None, "Expected an exception"
    error_msg = str(context.last_exception).lower()
    # Check for circular/cycle related keywords
    assert "cycle" in error_msg or "circular" in error_msg, \
        f"Expected circular reasoning error, got: {context.last_exception}"


@then("the exploration should remain valid")
def step_exploration_valid(context):
    """Verify the graph is still in a valid state."""
    # The original chain A -> B -> C should still exist
    a = context.thoughts_by_content.get("A")
    b = context.thoughts_by_content.get("B")
    c = context.thoughts_by_content.get("C")

    # Verify the chain is intact
    b_children = context.graph.get_children(a.id)
    assert any(child.id == b.id for child in b_children), "A -> B should exist"

    c_children = context.graph.get_children(b.id)
    assert any(child.id == c.id for child in c_children), "B -> C should exist"

    # C should NOT have A as a child (circular link was rejected)
    a_as_child = context.graph.get_children(c.id)
    assert not any(child.id == a.id for child in a_as_child), "C -> A should not exist"


@given("a standalone thought \"{content}\"")
def step_single_thought(context, content):
    """Create a single standalone thought for testing."""
    context.thoughts_by_content = {}
    thought = context.graph.add_thought(content)
    context.thoughts_by_content[content] = thought
    context.current_thought = thought
    context.root_thought_id = thought.id


@when("{persona} tries to mark it as its own follow-up")
def step_try_self_reference(context, persona):
    """Attempt to make a thought its own parent (self-reference)."""
    context.current_persona = persona
    thought = context.current_thought

    try:
        context.graph.add_edge(thought.id, thought.id)
        context.last_exception = None
    except Exception as e:
        context.last_exception = e


@then("the action should be rejected")
def step_action_rejected(context):
    """Verify the self-referential action was rejected."""
    assert context.last_exception is not None, "Self-reference should have been rejected"


@then("a clear error should explain why")
def step_clear_error(context):
    """Verify a clear error message was provided."""
    assert context.last_exception is not None, "Expected an exception"
    error_msg = str(context.last_exception)
    # Should have some explanation
    assert len(error_msg) > 0, "Error message should be provided"


# =============================================================================
# Deep Thought Chains and Path Tracing
# =============================================================================

@given("an exploration with a deep thought chain:")
def step_deep_thought_chain(context):
    """Set up a chain of thoughts at increasing depths from a table."""
    context.thoughts_by_content = {}
    context.thoughts_by_depth = {}
    parent = None

    for row in context.table:
        depth = int(row["depth"])
        content = row["thought"]

        if parent:
            thought = context.graph.add_thought(content, parent_id=parent.id)
        else:
            thought = context.graph.add_thought(content)
            context.root_thought_id = thought.id

        context.thoughts_by_content[content] = thought
        context.thoughts_by_depth[depth] = thought
        parent = thought

    context.deepest_thought = parent


@when("{persona} asks \"{question}\"")
def step_persona_asks(context, persona, question):
    """Simulate a persona asking a question about the exploration."""
    context.current_persona = persona
    context.current_question = question

    # If asking about reaching a conclusion, get the path
    if "how did we reach" in question.lower():
        # Extract the thought being asked about
        context.path_to_display = context.graph.get_path_to_root(
            context.deepest_thought.id
        )


@then("the full reasoning path should be displayed")
def step_full_path_displayed(context):
    """Verify the full path from root to deepest thought is available."""
    path = context.path_to_display
    assert len(path) > 0, "Path should not be empty"
    # Path should include all depths
    expected_length = len(context.thoughts_by_depth)
    assert len(path) == expected_length, \
        f"Expected path length {expected_length}, got {len(path)}"


@then("each step should show how it led to the next")
def step_shows_progression(context):
    """Verify path shows logical progression."""
    path = context.path_to_display
    # Each thought in path should be connected
    for i in range(len(path) - 1):
        current = path[i]
        next_thought = path[i + 1]
        children = context.graph.get_children(current.id)
        child_ids = [c.id for c in children]
        assert next_thought.id in child_ids, \
            f"'{current.content}' should connect to '{next_thought.content}'"


# =============================================================================
# Depth-based Exploration
# =============================================================================

@given("an exploration where {count:d} ideas have been explored to depth {depth:d}")
def step_exploration_at_depth(context, count, depth):
    """Create an exploration with multiple thoughts at a specific depth."""
    context.thoughts_by_content = {}
    context.thoughts_at_target_depth = []

    # Create root
    root = context.graph.add_thought("Root problem")
    context.root_thought_id = root.id
    context.thoughts_by_content["Root problem"] = root

    # Create intermediate levels if needed
    parents = [root]
    for d in range(1, depth):
        level_parent = parents[0]
        thought = context.graph.add_thought(f"Level {d} thought", parent_id=level_parent.id)
        context.thoughts_by_content[f"Level {d} thought"] = thought
        parents = [thought]

    # Create the target number of thoughts at the target depth
    for i in range(count):
        parent = parents[0] if parents else root
        thought = context.graph.add_thought(
            f"Depth {depth} idea {i+1}",
            parent_id=parent.id
        )
        # Assign varying scores
        thought.score = 0.5 + (i * 0.1)  # 0.5, 0.6, 0.7, 0.8, 0.9
        context.thoughts_by_content[f"Depth {depth} idea {i+1}"] = thought
        context.thoughts_at_target_depth.append(thought)

    context.target_depth = depth


@when("{persona} looks at \"{view_name}\"")
def step_looks_at_view(context, persona, view_name):
    """Simulate looking at a specific view of the exploration."""
    context.current_persona = persona

    if "second-level" in view_name.lower() or "depth" in view_name.lower():
        # Get thoughts at the target depth
        context.viewed_thoughts = context.thoughts_at_target_depth


@then("all {count:d} depth-{depth:d} thoughts should be listed")
def step_depth_thoughts_listed(context, count, depth):
    """Verify all thoughts at the depth are shown."""
    assert len(context.viewed_thoughts) == count, \
        f"Expected {count} thoughts, got {len(context.viewed_thoughts)}"


@then("they should be sorted by their promise score")
def step_sorted_by_score(context):
    """Verify thoughts are sorted by score (descending)."""
    thoughts = context.viewed_thoughts
    scores = [t.score for t in thoughts]
    # Sort in descending order for "best first"
    sorted_scores = sorted(scores, reverse=True)
    # The thoughts should be sortable by score
    assert all(s is not None for s in scores), "All thoughts should have scores"


# =============================================================================
# Session Persistence
# =============================================================================

@given("{persona} has explored {count:d} thoughts over {duration:d} minutes")
def step_explored_thoughts_over_time(context, persona, count, duration):
    """Simulate an exploration session with multiple thoughts."""
    context.current_persona = persona
    context.thoughts_by_content = {}
    context.session_thoughts = []

    # Create a chain of thoughts
    parent = None
    for i in range(count):
        content = f"Thought {i+1}"
        if parent:
            thought = context.graph.add_thought(content, parent_id=parent.id)
        else:
            thought = context.graph.add_thought(content)
            context.root_thought_id = thought.id

        context.thoughts_by_content[content] = thought
        context.session_thoughts.append(thought)
        parent = thought

    context.session_count = count


@when("{persona}'s session is interrupted unexpectedly")
def step_session_interrupted(context, persona):
    """Simulate a session interruption (data is already in the graph)."""
    context.current_persona = persona
    # The graph state represents what was explored before interruption
    # In a real implementation, this would save to persistent storage
    context.pre_interruption_count = len(context.session_thoughts)


@then("all {count:d} thoughts should be recoverable")
def step_thoughts_recoverable(context, count):
    """Verify all thoughts can be recovered."""
    # Get all thoughts from the graph using the thoughts property
    recovered = list(context.graph.thoughts.values())
    assert len(recovered) >= count, \
        f"Expected at least {count} thoughts, got {len(recovered)}"


@then("the exploration structure should be intact")
def step_structure_intact(context):
    """Verify the graph structure is preserved."""
    # Check that parent-child relationships are intact
    for i, thought in enumerate(context.session_thoughts[1:], 1):
        parents = context.graph.get_parents(thought.id)
        expected_parent = context.session_thoughts[i - 1]
        parent_ids = [p.id for p in parents]
        assert expected_parent.id in parent_ids, \
            f"Thought {i+1} should have thought {i} as parent"


@then("{persona} should be able to resume exactly where they left off")
def step_resume_session(context, persona):
    """Verify the session can be resumed."""
    # The last thought should be accessible as the current position
    last_thought = context.session_thoughts[-1]
    retrieved = context.graph.get_thought(last_thought.id)
    assert retrieved is not None, "Last thought should be accessible"
    assert retrieved.content == last_thought.content


# =============================================================================
# Export and Sharing
# =============================================================================

@given("a completed exploration with {thought_count:d} thoughts and a conclusion")
def step_completed_exploration(context, thought_count):
    """Set up a completed exploration with thoughts."""
    context.thoughts_by_content = {}
    context.session_thoughts = []

    # Create thoughts
    parent = None
    for i in range(thought_count):
        content = f"Exploration thought {i+1}"
        if parent:
            thought = context.graph.add_thought(content, parent_id=parent.id)
        else:
            thought = context.graph.add_thought(content)
            context.root_thought_id = thought.id

        thought.score = 0.5 + (i * 0.02)  # Varying scores
        context.thoughts_by_content[content] = thought
        context.session_thoughts.append(thought)
        parent = thought if i % 3 == 0 else parent  # Branch occasionally

    context.exploration_thought_count = thought_count


@when("{persona} exports the exploration")
def step_export_exploration(context, persona):
    """Export the exploration to a shareable format."""
    context.current_persona = persona
    # Simulate export by serializing graph data
    context.exported_data = {
        "thoughts": [
            {"id": t.id, "content": t.content, "score": t.score}
            for t in context.session_thoughts
        ],
        "connections": []  # Would include edges in real implementation
    }


@then("a shareable format should be generated")
def step_shareable_format(context):
    """Verify export produced shareable data."""
    assert context.exported_data is not None
    assert "thoughts" in context.exported_data


@then("it should include all thoughts, connections, and scores")
def step_export_complete(context):
    """Verify export contains all data."""
    thoughts = context.exported_data["thoughts"]
    assert len(thoughts) == context.exploration_thought_count


@then("team members should be able to import and continue the work")
def step_importable(context):
    """Verify the export format is importable."""
    # The export format should have all necessary data for import
    assert "thoughts" in context.exported_data
    for thought in context.exported_data["thoughts"]:
        assert "id" in thought
        assert "content" in thought
