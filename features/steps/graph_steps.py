"""
Step definitions for Graph of Thought BDD tests.
"""
import asyncio
from behave import given, when, then, use_step_matcher

from graph_of_thought import (
    GraphOfThought,
    Thought,
    ThoughtStatus,
    Edge,
    SearchResult,
    GraphConfig,
    SearchConfig,
    NodeNotFoundError,
    CycleDetectedError,
    GraphError,
    ResourceExhaustedError,
    InMemoryMetricsCollector,
)
from graph_of_thought.persistence import InMemoryPersistence
from graph_of_thought.search import MCTSStrategy
from graph_of_thought.core.defaults import FunctionGenerator, FunctionEvaluator

use_step_matcher("parse")


# =============================================================================
# Graph Setup Steps
# =============================================================================

@given("a test graph with evaluator and generator")
def step_test_graph(context):
    context.graph = context.create_test_graph()


@given("an empty graph")
def step_empty_graph(context):
    context.graph = GraphOfThought[str]()


@given("a graph configured to allow cycles")
def step_graph_allow_cycles(context):
    context.graph = GraphOfThought[str](allow_cycles=True)


@given("a graph with max depth {depth:d}")
def step_graph_max_depth(context, depth):
    context.graph = GraphOfThought[str](
        evaluator=lambda t: 0.5,
        generator=lambda t: [f"{t} -> child"],
        max_depth=depth,
    )


@given("a graph with goal-directed generator and evaluator")
def step_goal_directed_graph(context):
    def generate(parent: str) -> list[str]:
        if len(parent) > 50:
            return [f"{parent} GOAL"]
        return [f"{parent} -> step"]

    context.graph = GraphOfThought[str](
        evaluator=lambda t: 1.0 if "GOAL" in t else 0.5,
        generator=generate,
        max_depth=10,
    )


@given("a graph with length-based evaluator")
def step_length_based_graph(context):
    context.graph = GraphOfThought[str](
        evaluator=lambda t: len(t) / 50,
        generator=lambda t: [f"{t}a", f"{t}b"],
        max_depth=5,
    )


# =============================================================================
# Thought Creation Steps
# =============================================================================

@given('a thought "{content}" exists')
def step_thought_exists(context, content):
    thought = context.graph.add_thought(content)
    context.thoughts[content] = thought


@given('a thought "{content}" exists with score {score:f}')
def step_thought_exists_with_score(context, content, score):
    thought = context.graph.add_thought(content, score=score)
    context.thoughts[content] = thought


@given('a thought "{child}" exists as child of "{parent}"')
def step_child_thought_exists(context, child, parent):
    parent_thought = context.thoughts[parent]
    thought = context.graph.add_thought(child, parent_id=parent_thought.id)
    context.thoughts[child] = thought


@given('a thought "{child}" exists as child of "{parent}" with score {score:f}')
def step_child_thought_exists_with_score(context, child, parent, score):
    parent_thought = context.thoughts[parent]
    thought = context.graph.add_thought(child, parent_id=parent_thought.id, score=score)
    context.thoughts[child] = thought


@given('the thought "{content}" is marked as pruned')
def step_mark_thought_pruned(context, content):
    context.thoughts[content].status = ThoughtStatus.PRUNED


@when('I add a thought with content "{content}"')
def step_add_thought(context, content):
    thought = context.graph.add_thought(content)
    context.thoughts[content] = thought


@when('I add a thought "{child}" as child of "{parent}"')
def step_add_child_thought(context, child, parent):
    parent_thought = context.thoughts[parent]
    thought = context.graph.add_thought(child, parent_id=parent_thought.id)
    context.thoughts[child] = thought


@when("I add {count:d} thoughts")
def step_add_multiple_thoughts(context, count):
    for i in range(count):
        thought = context.graph.add_thought(f"T{i}")
        context.thoughts[f"T{i}"] = thought


@when("I try to add another thought")
def step_try_add_thought(context):
    try:
        context.graph.add_thought("Too many")
    except Exception as e:
        context.exception = e


# =============================================================================
# Edge Steps
# =============================================================================

@when('I add an edge from "{source}" to "{target}" with relation "{relation}" and weight {weight:f}')
def step_add_edge(context, source, target, relation, weight):
    source_thought = context.thoughts[source]
    target_thought = context.thoughts[target]
    edge = context.graph.add_edge(source_thought.id, target_thought.id, relation=relation, weight=weight)
    context.edges[(source, target)] = edge


@when('I add an edge from "{source}" to "{target}"')
def step_add_edge_simple(context, source, target):
    source_thought = context.thoughts[source]
    target_thought = context.thoughts[target]
    edge = context.graph.add_edge(source_thought.id, target_thought.id)
    context.edges[(source, target)] = edge


@when('I try to add an edge from "{source}" to "{target}"')
def step_try_add_edge(context, source, target):
    source_thought = context.thoughts[source]
    target_thought = context.thoughts[target]
    try:
        context.graph.add_edge(source_thought.id, target_thought.id)
    except Exception as e:
        context.exception = e


@when('I remove the edge from "{source}" to "{target}"')
def step_remove_edge(context, source, target):
    source_thought = context.thoughts[source]
    target_thought = context.thoughts[target]
    context.graph.remove_edge(source_thought.id, target_thought.id)


# =============================================================================
# Thought Removal Steps
# =============================================================================

@when('I remove the thought "{content}"')
def step_remove_thought(context, content):
    thought = context.thoughts[content]
    context.graph.remove_thought(thought.id)


@when('I try to get thought "{content}"')
def step_try_get_thought(context, content):
    try:
        context.graph.get_thought(content)
    except Exception as e:
        context.exception = e


# =============================================================================
# Traversal Steps
# =============================================================================

@when("I perform a breadth-first traversal")
def step_bfs(context):
    context.result = list(context.graph.bfs())


@when("I perform a depth-first traversal")
def step_dfs(context):
    context.result = list(context.graph.dfs())


@when('I get the path to root from "{content}"')
def step_get_path_to_root(context, content):
    thought = context.thoughts[content]
    context.result = context.graph.get_path_to_root(thought.id)


@when("I get the leaf nodes")
def step_get_leaves(context):
    context.result = context.graph.get_leaves()


@when("I get the best path")
def step_get_best_path(context):
    context.result = context.graph.get_best_path()


# =============================================================================
# Search Steps
# =============================================================================

@when("I run beam search")
def step_run_beam_search(context):
    context.result = asyncio.run(context.graph.beam_search())


@when("I run best-first search")
def step_run_best_first_search(context):
    context.result = asyncio.run(context.graph.best_first_search())


@when('I run beam search with goal predicate for "{goal}"')
def step_run_beam_search_with_goal(context, goal):
    context.result = asyncio.run(context.graph.beam_search(goal=lambda t: goal in t))


@when("I run beam search with max expansions {max_exp:d}")
def step_run_beam_search_max_exp(context, max_exp):
    config = SearchConfig(max_expansions=max_exp, max_depth=10)
    context.result = asyncio.run(context.graph.beam_search(config=config))


@when("I run MCTS search with exploration weight {weight:f} and max expansions {max_exp:d}")
def step_run_mcts(context, weight, max_exp):
    strategy = MCTSStrategy[str](exploration_weight=weight)
    config = SearchConfig(max_expansions=max_exp, max_depth=5)

    context.result = asyncio.run(strategy.search(
        graph=context.graph.as_operations(),
        generator=FunctionGenerator(lambda t: [f"{t}a", f"{t}b"]),
        evaluator=FunctionEvaluator(lambda t: len(t) / 50),
        config=config,
    ))


# =============================================================================
# Expansion Steps
# =============================================================================

@when('I expand the thought "{content}"')
def step_expand_thought(context, content):
    thought = context.thoughts[content]
    context.result = asyncio.run(context.graph.expand(thought.id))


@when("I expand the first child")
def step_expand_first_child(context):
    if context.result:
        first_child = context.result[0]
        context.result = asyncio.run(context.graph.expand(first_child.id))
        context.last_expanded = context.result


@when("I try to expand a grandchild")
def step_try_expand_grandchild(context):
    if context.last_expanded:
        grandchild = context.last_expanded[0]
        context.result = asyncio.run(context.graph.expand(grandchild.id))


# =============================================================================
# Merge and Prune Steps
# =============================================================================

@when('I merge thoughts "{t1}" and "{t2}" into "{merged}" with score {score:f}')
def step_merge_thoughts(context, t1, t2, merged, score):
    thought1 = context.thoughts[t1]
    thought2 = context.thoughts[t2]
    context.result = context.graph.merge_thoughts([thought1.id, thought2.id], merged, score=score)
    context.thoughts[merged] = context.result


@when("I try to merge an empty list of thoughts")
def step_try_merge_empty(context):
    try:
        context.graph.merge_thoughts([], "Merged")
    except Exception as e:
        context.exception = e


@when("I prune thoughts below threshold {threshold:f}")
def step_prune(context, threshold):
    context.result = context.graph.prune(threshold=threshold)


@when("I prune and remove thoughts below threshold {threshold:f}")
def step_prune_and_remove(context, threshold):
    context.result = context.graph.prune_and_remove(threshold=threshold)


# =============================================================================
# Serialization Steps
# =============================================================================

@when("I serialize the graph to a dictionary")
def step_serialize_to_dict(context):
    context.result = context.graph.to_dict()


@when("I deserialize a graph from the dictionary")
def step_deserialize_from_dict(context):
    context.restored_graph = GraphOfThought.from_dict(
        context.result,
        evaluator=context.simple_evaluator,
        generator=context.simple_generator,
    )


@when("I serialize the graph to JSON")
def step_serialize_to_json(context):
    context.json_str = context.graph.to_json()


@when("I deserialize a graph from the JSON")
def step_deserialize_from_json(context):
    context.restored_graph = GraphOfThought.from_json(
        context.json_str,
        evaluator=context.simple_evaluator,
        generator=context.simple_generator,
    )


# =============================================================================
# Visualization Steps
# =============================================================================

@when("I generate a text visualization")
def step_generate_visualization(context):
    context.result = context.graph.visualize()


@when("I get the graph stats")
def step_get_stats(context):
    context.result = context.graph.stats()


# =============================================================================
# Basic Assertions
# =============================================================================

@then("the graph should contain {count:d} thought")
@then("the graph should contain {count:d} thoughts")
def step_check_thought_count(context, count):
    assert len(context.graph) == count, f"Expected {count} thoughts, got {len(context.graph)}"


@then("the graph should have no root nodes")
def step_check_no_roots(context):
    assert context.graph.root_ids == [], f"Expected no roots, got {context.graph.root_ids}"


@then("the graph should have no edges")
def step_check_no_edges(context):
    assert context.graph.edges == [], f"Expected no edges, got {context.graph.edges}"


@then('the thought "{content}" should be a root node')
def step_check_is_root(context, content):
    thought = context.thoughts[content]
    assert thought.id in context.graph.root_ids, f"{content} is not a root node"


@then('the thought "{content}" should not be a root node')
def step_check_not_root(context, content):
    thought = context.thoughts[content]
    assert thought.id not in context.graph.root_ids, f"{content} is a root node"


@then('the thought "{content}" should have depth {depth:d}')
def step_check_depth(context, content, depth):
    thought = context.thoughts[content]
    assert thought.depth == depth, f"Expected depth {depth}, got {thought.depth}"


@then('the thought "{content}" should have status "{status}"')
def step_check_status(context, content, status):
    thought = context.thoughts[content]
    expected_status = ThoughtStatus[status]
    assert thought.status == expected_status, f"Expected {status}, got {thought.status}"


@then('"{parent}" should have "{child}" as a child')
def step_check_has_child(context, parent, child):
    parent_thought = context.thoughts[parent]
    child_thought = context.thoughts[child]
    children = context.graph.get_children(parent_thought.id)
    assert child_thought in children, f"{child} is not a child of {parent}"


@then('"{child}" should have "{parent}" as a parent')
def step_check_has_parent(context, child, parent):
    parent_thought = context.thoughts[parent]
    child_thought = context.thoughts[child]
    parents = context.graph.get_parents(child_thought.id)
    assert parent_thought in parents, f"{parent} is not a parent of {child}"


@then('"{parent}" should have no children')
def step_check_no_children(context, parent):
    parent_thought = context.thoughts[parent]
    children = context.graph.get_children(parent_thought.id)
    assert children == [], f"Expected no children, got {children}"


@then('"{child}" should have no parents')
def step_check_no_parents(context, child):
    child_thought = context.thoughts[child]
    parents = context.graph.get_parents(child_thought.id)
    assert parents == [], f"Expected no parents, got {parents}"


@then('"{content}" should be in the graph')
def step_check_in_graph(context, content):
    thought = context.thoughts.get(content)
    if thought:
        assert thought.id in context.graph, f"{content} is not in the graph"
    else:
        # Check by content for restored graphs
        found = any(t.content == content for t in context.graph.thoughts.values())
        assert found, f"{content} is not in the graph"


@then('"{content}" should not be in the graph')
def step_check_not_in_graph(context, content):
    thought = context.thoughts.get(content)
    if thought:
        assert thought.id not in context.graph, f"{content} is still in the graph"


# =============================================================================
# Edge Assertions
# =============================================================================

@then('an edge should exist from "{source}" to "{target}"')
def step_check_edge_exists(context, source, target):
    source_thought = context.thoughts[source]
    target_thought = context.thoughts[target]
    edges = [e for e in context.graph.edges
             if e.source_id == source_thought.id and e.target_id == target_thought.id]
    assert len(edges) > 0, f"No edge from {source} to {target}"


@then('the edge should have relation "{relation}"')
def step_check_edge_relation(context, relation):
    edge = list(context.edges.values())[-1]
    assert edge.relation == relation, f"Expected relation {relation}, got {edge.relation}"


@then("the edge should have weight {weight:f}")
def step_check_edge_weight(context, weight):
    edge = list(context.edges.values())[-1]
    assert edge.weight == weight, f"Expected weight {weight}, got {edge.weight}"


# =============================================================================
# Exception Assertions
# =============================================================================

@then("a NodeNotFoundError should be raised")
def step_check_node_not_found(context):
    assert isinstance(context.exception, NodeNotFoundError), f"Expected NodeNotFoundError, got {type(context.exception)}"


@then("a CycleDetectedError should be raised")
def step_check_cycle_detected(context):
    assert isinstance(context.exception, CycleDetectedError), f"Expected CycleDetectedError, got {type(context.exception)}"


@then("a GraphError should be raised")
def step_check_graph_error(context):
    assert isinstance(context.exception, GraphError), f"Expected GraphError, got {type(context.exception)}"


@then("a ResourceExhaustedError should be raised")
def step_check_resource_exhausted(context):
    assert isinstance(context.exception, ResourceExhaustedError), f"Expected ResourceExhaustedError, got {type(context.exception)}"


# =============================================================================
# Traversal Assertions
# =============================================================================

@then('the first thought should be "{content}"')
def step_check_first_thought(context, content):
    first = context.result[0]
    assert first.content == content, f"Expected first thought {content}, got {first.content}"


@then('thoughts "{t1}" and "{t2}" should come before "{t3}"')
def step_check_order(context, t1, t2, t3):
    contents = [t.content for t in context.result]
    idx_t1 = contents.index(t1)
    idx_t2 = contents.index(t2)
    idx_t3 = contents.index(t3)
    assert idx_t1 < idx_t3 and idx_t2 < idx_t3, f"{t1} and {t2} should come before {t3}"


@then('"{content}" should be in the traversal')
def step_check_in_traversal(context, content):
    contents = [t.content for t in context.result]
    assert content in contents, f"{content} not in traversal"


@then('the path should be "{p1}" -> "{p2}" -> "{p3}"')
def step_check_path(context, p1, p2, p3):
    contents = [t.content for t in context.result]
    assert contents == [p1, p2, p3], f"Expected [{p1}, {p2}, {p3}], got {contents}"


@then('the leaves should be "{l1}" and "{l2}"')
def step_check_leaves(context, l1, l2):
    contents = {t.content for t in context.result}
    assert contents == {l1, l2}, f"Expected {{{l1}, {l2}}}, got {contents}"


# =============================================================================
# Search Assertions
# =============================================================================

@then("the search should return a result")
def step_check_search_result(context):
    assert isinstance(context.result, SearchResult), f"Expected SearchResult, got {type(context.result)}"


@then("the search should have expanded at least {count:d} thought")
@then("the search should have expanded at least {count:d} thoughts")
def step_check_expanded_at_least(context, count):
    assert context.result.thoughts_expanded >= count, f"Expected at least {count} expansions, got {context.result.thoughts_expanded}"


@then("the search should have expanded at most {count:d} thoughts")
def step_check_expanded_at_most(context, count):
    assert context.result.thoughts_expanded <= count, f"Expected at most {count} expansions, got {context.result.thoughts_expanded}"


@then("the best path should have at least {count:d} thought")
@then("the best path should have at least {count:d} thoughts")
def step_check_best_path_length(context, count):
    assert len(context.result.best_path) >= count, f"Expected at least {count} in path, got {len(context.result.best_path)}"


@then('the termination reason should be one of "{reasons}"')
def step_check_termination_reason_one_of(context, reasons):
    valid_reasons = [r.strip().strip('"') for r in reasons.split(",")]
    assert context.result.termination_reason in valid_reasons, f"Expected one of {valid_reasons}, got {context.result.termination_reason}"


@then('the termination reason should be "{reason}"')
def step_check_termination_reason(context, reason):
    assert context.result.termination_reason == reason, f"Expected {reason}, got {context.result.termination_reason}"


@then('the best path should end with a thought containing "{content}"')
def step_check_best_path_ends_with(context, content):
    last_thought = context.result.best_path[-1]
    assert content in last_thought.content, f"Expected last thought to contain {content}, got {last_thought.content}"


@then("all thoughts should have depth at most {depth:d}")
def step_check_all_depths(context, depth):
    max_depth = max(t.depth for t in context.graph.thoughts.values())
    assert max_depth <= depth, f"Expected max depth {depth}, got {max_depth}"


# =============================================================================
# Expansion Assertions
# =============================================================================

@then("{count:d} children should be created")
def step_check_children_count(context, count):
    assert len(context.result) == count, f"Expected {count} children, got {len(context.result)}"


@then("all children should have depth {depth:d}")
def step_check_all_children_depth(context, depth):
    for child in context.result:
        assert child.depth == depth, f"Expected depth {depth}, got {child.depth}"


@then("no children should be created")
def step_check_no_children_created(context):
    assert context.result == [], f"Expected no children, got {context.result}"


@then("no children should be created from the grandchild")
def step_check_no_grandchildren(context):
    assert context.result == [], f"Expected no children from grandchild, got {context.result}"


# =============================================================================
# Merge and Prune Assertions
# =============================================================================

@then('the merged thought should have content "{content}"')
def step_check_merged_content(context, content):
    assert context.result.content == content, f"Expected content {content}, got {context.result.content}"


@then("the merged thought should have score {score:f}")
def step_check_merged_score(context, score):
    assert context.result.score == score, f"Expected score {score}, got {context.result.score}"


@then("the merged thought should have depth {depth:d}")
def step_check_merged_depth(context, depth):
    assert context.result.depth == depth, f"Expected depth {depth}, got {context.result.depth}"


@then('"{parent}" should be a parent of the merged thought')
def step_check_merge_parent(context, parent):
    parent_thought = context.thoughts[parent]
    parents = context.graph.get_parents(context.result.id)
    assert parent_thought in parents, f"{parent} is not a parent of the merged thought"


@then("{count:d} thoughts should be pruned")
def step_check_pruned_count(context, count):
    assert context.result == count, f"Expected {count} pruned, got {context.result}"


@then("{count:d} thought should be removed")
@then("{count:d} thoughts should be removed")
def step_check_removed_count(context, count):
    assert context.result == count, f"Expected {count} removed, got {context.result}"


# =============================================================================
# Serialization Assertions
# =============================================================================

@then('the dictionary should contain "{key}"')
def step_check_dict_contains(context, key):
    assert key in context.result, f"Dictionary does not contain {key}"


@then("there should be {count:d} thoughts in the dictionary")
def step_check_dict_thoughts(context, count):
    assert len(context.result["thoughts"]) == count, f"Expected {count} thoughts in dict"


@then("there should be {count:d} edge in the dictionary")
@then("there should be {count:d} edges in the dictionary")
def step_check_dict_edges(context, count):
    assert len(context.result["edges"]) == count, f"Expected {count} edges in dict"


@then("the restored graph should have {count:d} thoughts")
def step_check_restored_thoughts(context, count):
    assert len(context.restored_graph) == count, f"Expected {count} thoughts in restored graph"


@then("the restored graph should have the same root ids")
def step_check_restored_roots(context):
    assert context.restored_graph.root_ids == context.graph.root_ids, "Root IDs do not match"


@then("the restored graph should have {count:d} edge")
@then("the restored graph should have {count:d} edges")
def step_check_restored_edges(context, count):
    assert len(context.restored_graph.edges) == count, f"Expected {count} edges in restored graph"


@then("the JSON roundtrip should be identical")
def step_check_json_identical(context):
    assert context.restored_graph.to_json() == context.json_str, "JSON roundtrip is not identical"


# =============================================================================
# Visualization Assertions
# =============================================================================

@then('the visualization should contain "{text}"')
def step_check_viz_contains(context, text):
    assert text in context.result, f"Visualization does not contain {text}"


@then("the stats should show {key} = {value:d}")
def step_check_stats(context, key, value):
    assert context.result[key] == value, f"Expected {key}={value}, got {context.result[key]}"
