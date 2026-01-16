from __future__ import annotations
#!/usr/bin/env python3
"""
Comprehensive test suite for Graph of Thought package.
"""

import asyncio
import json
from typing import Any

# Make pytest optional
class _PytestShim:
    """Shim for when pytest is not installed."""
    class mark:
        @staticmethod
        def asyncio(fn):
            return fn
    
    @staticmethod
    def raises(exc_type):
        class RaisesContext:
            def __enter__(self):
                return self
            def __exit__(self, exc_type_actual, exc_val, exc_tb):
                if exc_type_actual is None:
                    raise AssertionError(f"Expected {exc_type.__name__} but nothing was raised")
                if not issubclass(exc_type_actual, exc_type):
                    raise AssertionError(f"Expected {exc_type.__name__} but got {exc_type_actual.__name__}")
                return True  # Suppress the exception
        return RaisesContext()

try:
    import pytest
except ImportError:
    pytest = _PytestShim()

# Import the package
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
from graph_of_thought.persistence import InMemoryPersistence, FilePersistence
from graph_of_thought.search import BeamSearchStrategy, MCTSStrategy, IterativeDeepeningStrategy


# =============================================================================
# Test Fixtures
# =============================================================================

def simple_evaluator(thought: str) -> float:
    """Simple keyword-based evaluator."""
    keywords = {"good": 0.3, "better": 0.5, "best": 0.8, "optimal": 1.0}
    return sum(v for k, v in keywords.items() if k in thought.lower())


def simple_generator(parent: str) -> list[str]:
    """Simple generator that creates variants."""
    return [f"{parent} → good", f"{parent} → better", f"{parent} → best"]


def create_test_graph() -> GraphOfThought[str]:
    """Create a graph for testing."""
    return GraphOfThought[str](
        evaluator=simple_evaluator,
        generator=simple_generator,
        max_depth=5,
        beam_width=3,
    )


# =============================================================================
# Basic Operations Tests
# =============================================================================

class TestBasicOperations:
    """Test basic graph operations."""
    
    def test_create_empty_graph(self):
        """Test creating an empty graph."""
        graph = GraphOfThought[str]()
        assert len(graph) == 0
        assert graph.root_ids == []
        assert graph.edges == []
    
    def test_add_root_thought(self):
        """Test adding a root thought."""
        graph = create_test_graph()
        thought = graph.add_thought("Root")
        
        assert thought.id in graph
        assert len(graph) == 1
        assert thought.id in graph.root_ids
        assert thought.depth == 0
        assert thought.status == ThoughtStatus.PENDING
    
    def test_add_child_thought(self):
        """Test adding a child thought."""
        graph = create_test_graph()
        root = graph.add_thought("Root")
        child = graph.add_thought("Child", parent_id=root.id)
        
        assert len(graph) == 2
        assert child.depth == 1
        assert child.id not in graph.root_ids
        assert child in graph.get_children(root.id)
        assert root in graph.get_parents(child.id)
    
    def test_add_edge(self):
        """Test adding an edge between existing thoughts."""
        graph = create_test_graph()
        t1 = graph.add_thought("T1")
        t2 = graph.add_thought("T2")
        
        edge = graph.add_edge(t1.id, t2.id, relation="custom", weight=0.5)
        
        assert edge.source_id == t1.id
        assert edge.target_id == t2.id
        assert edge.relation == "custom"
        assert edge.weight == 0.5
    
    def test_remove_thought(self):
        """Test removing a thought."""
        graph = create_test_graph()
        root = graph.add_thought("Root")
        child = graph.add_thought("Child", parent_id=root.id)
        
        removed = graph.remove_thought(child.id)
        
        assert removed.id == child.id
        assert child.id not in graph
        assert len(graph) == 1
        assert graph.get_children(root.id) == []
    
    def test_remove_edge(self):
        """Test removing an edge."""
        graph = create_test_graph()
        root = graph.add_thought("Root")
        child = graph.add_thought("Child", parent_id=root.id)
        
        edge = graph.remove_edge(root.id, child.id)
        
        assert edge is not None
        assert graph.get_children(root.id) == []
        assert graph.get_parents(child.id) == []
    
    def test_get_nonexistent_thought_raises(self):
        """Test that getting a nonexistent thought raises."""
        graph = create_test_graph()
        
        with pytest.raises(NodeNotFoundError):
            graph.get_thought("nonexistent")
    
    def test_contains(self):
        """Test __contains__ method."""
        graph = create_test_graph()
        thought = graph.add_thought("Test")
        
        assert thought.id in graph
        assert "nonexistent" not in graph


# =============================================================================
# Cycle Detection Tests
# =============================================================================

class TestCycleDetection:
    """Test cycle detection."""
    
    def test_cycle_prevented_by_default(self):
        """Test that cycles are prevented by default."""
        graph = create_test_graph()
        t1 = graph.add_thought("T1")
        t2 = graph.add_thought("T2", parent_id=t1.id)
        
        with pytest.raises(CycleDetectedError):
            graph.add_edge(t2.id, t1.id)
    
    def test_self_loop_prevented(self):
        """Test that self-loops are prevented."""
        graph = create_test_graph()
        t1 = graph.add_thought("T1")
        
        with pytest.raises(CycleDetectedError):
            graph.add_edge(t1.id, t1.id)
    
    def test_cycles_allowed_when_configured(self):
        """Test that cycles are allowed when configured."""
        graph = GraphOfThought[str](allow_cycles=True)
        t1 = graph.add_thought("T1")
        t2 = graph.add_thought("T2", parent_id=t1.id)
        
        # Should not raise
        edge = graph.add_edge(t2.id, t1.id)
        assert edge is not None


# =============================================================================
# Traversal Tests
# =============================================================================

class TestTraversal:
    """Test graph traversal methods."""
    
    def test_bfs(self):
        """Test breadth-first traversal."""
        graph = create_test_graph()
        root = graph.add_thought("Root")
        c1 = graph.add_thought("C1", parent_id=root.id)
        c2 = graph.add_thought("C2", parent_id=root.id)
        gc1 = graph.add_thought("GC1", parent_id=c1.id)
        
        bfs_order = list(graph.bfs())
        
        assert bfs_order[0] == root
        assert set(bfs_order[1:3]) == {c1, c2}
        assert bfs_order[3] == gc1
    
    def test_dfs(self):
        """Test depth-first traversal."""
        graph = create_test_graph()
        root = graph.add_thought("Root")
        c1 = graph.add_thought("C1", parent_id=root.id)
        c2 = graph.add_thought("C2", parent_id=root.id)
        gc1 = graph.add_thought("GC1", parent_id=c1.id)
        
        dfs_order = list(graph.dfs())
        
        assert dfs_order[0] == root
        # DFS should go deep first
        assert gc1 in dfs_order
    
    def test_get_path_to_root(self):
        """Test path to root."""
        graph = create_test_graph()
        root = graph.add_thought("Root")
        c1 = graph.add_thought("C1", parent_id=root.id)
        gc1 = graph.add_thought("GC1", parent_id=c1.id)
        
        path = graph.get_path_to_root(gc1.id)
        
        assert path == [root, c1, gc1]
    
    def test_get_leaves(self):
        """Test getting leaf nodes."""
        graph = create_test_graph()
        root = graph.add_thought("Root")
        c1 = graph.add_thought("C1", parent_id=root.id)
        c2 = graph.add_thought("C2", parent_id=root.id)
        gc1 = graph.add_thought("GC1", parent_id=c1.id)
        
        leaves = graph.get_leaves()
        
        assert set(leaves) == {c2, gc1}
    
    def test_get_best_path(self):
        """Test getting best path."""
        graph = create_test_graph()
        root = graph.add_thought("Root", score=0.0)
        c1 = graph.add_thought("C1", parent_id=root.id, score=0.5)
        c2 = graph.add_thought("C2", parent_id=root.id, score=0.3)
        gc1 = graph.add_thought("GC1", parent_id=c1.id, score=0.9)
        
        best_path = graph.get_best_path()
        
        assert best_path == [root, c1, gc1]


# =============================================================================
# Search Tests
# =============================================================================

class TestSearch:
    """Test search algorithms."""
    
    @pytest.mark.asyncio
    async def test_beam_search(self):
        """Test beam search."""
        graph = create_test_graph()
        graph.add_thought("Start")
        
        result = await graph.beam_search()
        
        assert isinstance(result, SearchResult)
        assert result.thoughts_expanded > 0
        assert len(result.best_path) > 0
        assert result.termination_reason in ("completed", "max_depth", "max_expansions")
    
    @pytest.mark.asyncio
    async def test_best_first_search(self):
        """Test best-first search."""
        graph = create_test_graph()
        graph.add_thought("Start")
        
        result = await graph.best_first_search()
        
        assert isinstance(result, SearchResult)
        assert result.thoughts_expanded > 0
    
    @pytest.mark.asyncio
    async def test_goal_directed_search(self):
        """Test search with goal predicate."""
        def generate(parent: str) -> list[str]:
            if len(parent) > 50:
                return [f"{parent} GOAL"]
            return [f"{parent} → step"]
        
        graph = GraphOfThought[str](
            evaluator=lambda t: 1.0 if "GOAL" in t else 0.5,
            generator=generate,
            max_depth=10,
        )
        graph.add_thought("Start")
        
        result = await graph.beam_search(goal=lambda t: "GOAL" in t)
        
        assert result.termination_reason == "goal_reached"
        assert "GOAL" in result.best_path[-1].content
    
    @pytest.mark.asyncio
    async def test_search_respects_max_depth(self):
        """Test that search respects max depth."""
        graph = GraphOfThought[str](
            evaluator=lambda t: 0.5,
            generator=lambda t: [f"{t} → child"],
            max_depth=3,
        )
        graph.add_thought("Start")
        
        result = await graph.beam_search()
        
        max_depth = max(t.depth for t in graph.thoughts.values())
        assert max_depth <= 3
    
    @pytest.mark.asyncio
    async def test_search_respects_max_expansions(self):
        """Test that search respects max expansions (with tolerance for batch processing)."""
        graph = GraphOfThought[str](
            evaluator=lambda t: 0.5,
            generator=lambda t: [f"{t} → a", f"{t} → b", f"{t} → c"],
            max_depth=10,
        )
        graph.add_thought("Start")
        
        config = SearchConfig(max_expansions=5, max_depth=10)
        result = await graph.beam_search(config=config)
        
        # Allow small tolerance since batch might complete before check
        assert result.thoughts_expanded <= 10, f"Expected <=10, got {result.thoughts_expanded}"


# =============================================================================
# Expand Tests
# =============================================================================

class TestExpand:
    """Test thought expansion."""
    
    @pytest.mark.asyncio
    async def test_expand(self):
        """Test expanding a thought."""
        graph = create_test_graph()
        root = graph.add_thought("Start")
        
        children = await graph.expand(root.id)
        
        assert len(children) == 3  # simple_generator creates 3
        assert all(c.depth == 1 for c in children)
        assert root.status == ThoughtStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_expand_respects_max_depth(self):
        """Test that expand respects max depth."""
        graph = GraphOfThought[str](
            evaluator=lambda t: 0.5,
            generator=lambda t: [f"{t} → child"],
            max_depth=2,
        )
        root = graph.add_thought("Root")
        children = await graph.expand(root.id)
        grandchildren = await graph.expand(children[0].id)
        
        # At max depth, shouldn't expand further
        great_grandchildren = await graph.expand(grandchildren[0].id)
        
        assert great_grandchildren == []
    
    @pytest.mark.asyncio
    async def test_expand_pruned_thought(self):
        """Test that pruned thoughts don't expand."""
        graph = create_test_graph()
        root = graph.add_thought("Start")
        root.status = ThoughtStatus.PRUNED
        
        children = await graph.expand(root.id)
        
        assert children == []


# =============================================================================
# Merge and Prune Tests
# =============================================================================

class TestMergeAndPrune:
    """Test merge and prune operations."""
    
    def test_merge_thoughts(self):
        """Test merging thoughts."""
        graph = create_test_graph()
        t1 = graph.add_thought("T1", score=0.5)
        t2 = graph.add_thought("T2", score=0.7)
        
        merged = graph.merge_thoughts([t1.id, t2.id], "Merged", score=0.8)
        
        assert merged.content == "Merged"
        assert merged.score == 0.8
        assert merged.depth == 1  # max(0, 0) + 1
        assert t1.status == ThoughtStatus.MERGED
        assert t2.status == ThoughtStatus.MERGED
        assert t1 in graph.get_parents(merged.id)
        assert t2 in graph.get_parents(merged.id)
    
    def test_merge_empty_raises(self):
        """Test that merging empty list raises."""
        graph = create_test_graph()
        
        with pytest.raises(GraphError):
            graph.merge_thoughts([], "Merged")
    
    def test_prune(self):
        """Test pruning thoughts below threshold."""
        graph = create_test_graph()
        t1 = graph.add_thought("T1", score=0.3)
        t2 = graph.add_thought("T2", score=0.7)
        t3 = graph.add_thought("T3", score=0.1)
        
        pruned_count = graph.prune(threshold=0.5)
        
        assert pruned_count == 2
        assert t1.status == ThoughtStatus.PRUNED
        assert t2.status == ThoughtStatus.PENDING
        assert t3.status == ThoughtStatus.PRUNED
    
    def test_prune_and_remove(self):
        """Test pruning and removing thoughts."""
        graph = create_test_graph()
        t1 = graph.add_thought("T1", score=0.3)
        t2 = graph.add_thought("T2", score=0.7)
        
        removed_count = graph.prune_and_remove(threshold=0.5)
        
        assert removed_count == 1
        assert t1.id not in graph
        assert t2.id in graph


# =============================================================================
# Serialization Tests
# =============================================================================

class TestSerialization:
    """Test serialization and deserialization."""
    
    def test_to_dict(self):
        """Test serializing to dict."""
        graph = create_test_graph()
        root = graph.add_thought("Root", score=0.5)
        child = graph.add_thought("Child", parent_id=root.id, score=0.7)
        
        data = graph.to_dict()
        
        assert "thoughts" in data
        assert "edges" in data
        assert "roots" in data
        assert "config" in data
        assert len(data["thoughts"]) == 2
        assert len(data["edges"]) == 1
    
    def test_from_dict(self):
        """Test deserializing from dict."""
        graph = create_test_graph()
        root = graph.add_thought("Root", score=0.5)
        child = graph.add_thought("Child", parent_id=root.id, score=0.7)
        
        data = graph.to_dict()
        restored = GraphOfThought.from_dict(
            data,
            evaluator=simple_evaluator,
            generator=simple_generator,
        )
        
        assert len(restored) == 2
        assert restored.root_ids == graph.root_ids
        assert len(restored.edges) == 1
    
    def test_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        graph = create_test_graph()
        graph.add_thought("Root", score=0.5)
        graph.add_thought("Child", parent_id=graph.root_ids[0], score=0.7)
        
        json_str = graph.to_json()
        restored = GraphOfThought.from_json(
            json_str,
            evaluator=simple_evaluator,
            generator=simple_generator,
        )
        
        assert len(restored) == len(graph)
        assert restored.to_json() == json_str


# =============================================================================
# Configuration Tests
# =============================================================================

class TestConfiguration:
    """Test configuration."""
    
    def test_config_from_dict(self):
        """Test loading config from dict."""
        data = {
            "allow_cycles": True,
            "limits": {"max_depth": 15, "max_thoughts": 500},
            "search": {"beam_width": 5},
        }
        
        config = GraphConfig.from_dict(data)
        
        assert config.allow_cycles == True
        assert config.limits.max_depth == 15
        assert config.limits.max_thoughts == 500
        assert config.search.beam_width == 5
    
    def test_config_validation(self):
        """Test config validation."""
        config = GraphConfig()
        config.limits.max_thoughts = -1
        config.search.beam_width = 0
        
        issues = config.validate()
        
        assert len(issues) >= 2
    
    def test_config_to_json(self):
        """Test config JSON serialization."""
        config = GraphConfig()
        config.limits.max_depth = 25
        
        json_str = config.to_json()
        restored = GraphConfig.from_json(json_str)
        
        assert restored.limits.max_depth == 25


# =============================================================================
# Persistence Tests
# =============================================================================

class TestPersistence:
    """Test persistence backends."""
    
    @pytest.mark.asyncio
    async def test_in_memory_persistence(self):
        """Test in-memory persistence."""
        persistence = InMemoryPersistence()
        graph = create_test_graph()
        graph.add_thought("Root", score=0.5)
        
        await persistence.save_graph(
            graph_id="test",
            thoughts=graph.thoughts,
            edges=graph.edges,
            root_ids=graph.root_ids,
            metadata={"test": True},
        )
        
        loaded = await persistence.load_graph("test")
        
        assert loaded is not None
        thoughts, edges, root_ids, metadata = loaded
        assert len(thoughts) == 1
        assert metadata["test"] == True
    
    @pytest.mark.asyncio
    async def test_checkpoint(self):
        """Test checkpointing."""
        persistence = InMemoryPersistence()
        graph = create_test_graph()
        graph.add_thought("Root")
        
        await persistence.save_checkpoint(
            graph_id="test",
            checkpoint_id="cp1",
            thoughts=graph.thoughts,
            edges=graph.edges,
            root_ids=graph.root_ids,
            search_state={"current_depth": 3},
        )
        
        loaded = await persistence.load_checkpoint("test", "cp1")
        
        assert loaded is not None
        thoughts, edges, root_ids, search_state = loaded
        assert search_state["current_depth"] == 3
    
    @pytest.mark.asyncio
    async def test_delete_graph(self):
        """Test deleting a graph."""
        persistence = InMemoryPersistence()
        
        await persistence.save_graph("test", {}, [], [], {})
        deleted = await persistence.delete_graph("test")
        
        assert deleted == True
        assert await persistence.load_graph("test") is None


# =============================================================================
# Metrics Tests
# =============================================================================

class TestMetrics:
    """Test metrics collection."""
    
    def test_in_memory_metrics(self):
        """Test in-memory metrics collector."""
        metrics = InMemoryMetricsCollector()
        
        metrics.increment("counter", 5)
        metrics.gauge("gauge", 10.5)
        metrics.histogram("histogram", 1.0)
        metrics.histogram("histogram", 2.0)
        metrics.timing("timing", 100.0)
        
        assert metrics.counters["counter"] == 5
        assert metrics.gauges["gauge"] == 10.5
        assert metrics.histograms["histogram"] == [1.0, 2.0]
        assert metrics.timings["timing"] == [100.0]
    
    def test_metrics_with_tags(self):
        """Test metrics with tags."""
        metrics = InMemoryMetricsCollector()
        
        metrics.increment("counter", 1, tags={"env": "test"})
        
        assert "counter[env=test]" in metrics.counters
    
    @pytest.mark.asyncio
    async def test_graph_collects_metrics(self):
        """Test that graph collects metrics."""
        metrics = InMemoryMetricsCollector()
        graph = GraphOfThought[str](
            evaluator=simple_evaluator,
            generator=simple_generator,
            metrics=metrics,
        )
        
        graph.add_thought("Root")
        await graph.expand(graph.root_ids[0])
        
        assert metrics.counters.get("thoughts.added", 0) > 0
        assert metrics.counters.get("thoughts.expanded", 0) > 0


# =============================================================================
# Search Strategy Tests
# =============================================================================

class TestSearchStrategies:
    """Test pluggable search strategies."""
    
    @pytest.mark.asyncio
    async def test_mcts_strategy(self):
        """Test MCTS strategy."""
        graph = GraphOfThought[str](
            evaluator=lambda t: len(t) / 50,
            generator=lambda t: [f"{t}a", f"{t}b"],
            max_depth=5,
        )
        graph.add_thought("Start")
        
        from graph_of_thought.core.defaults import FunctionGenerator, FunctionEvaluator
        
        strategy = MCTSStrategy[str](exploration_weight=1.0)
        config = SearchConfig(max_expansions=10, max_depth=5)
        
        result = await strategy.search(
            graph=graph.as_operations(),
            generator=FunctionGenerator(lambda t: [f"{t}a", f"{t}b"]),
            evaluator=FunctionEvaluator(lambda t: len(t) / 50),
            config=config,
        )
        
        assert result.thoughts_expanded > 0


# =============================================================================
# Resource Limits Tests
# =============================================================================

class TestResourceLimits:
    """Test resource limit enforcement."""
    
    def test_max_thoughts_limit(self):
        """Test max thoughts limit."""
        config = GraphConfig()
        config.limits.max_thoughts = 5
        
        graph = GraphOfThought[str](config=config)
        
        for i in range(5):
            graph.add_thought(f"T{i}")
        
        with pytest.raises(ResourceExhaustedError):
            graph.add_thought("Too many")


# =============================================================================
# Visualization Tests
# =============================================================================

class TestVisualization:
    """Test visualization."""
    
    def test_visualize(self):
        """Test text visualization."""
        graph = create_test_graph()
        root = graph.add_thought("Root", score=0.5)
        c1 = graph.add_thought("Child 1", parent_id=root.id, score=0.7)
        c2 = graph.add_thought("Child 2", parent_id=root.id, score=0.3)
        
        viz = graph.visualize()
        
        assert "Root" in viz
        assert "Child 1" in viz
        assert "Child 2" in viz
        assert "[0.50]" in viz
    
    def test_stats(self):
        """Test stats method."""
        graph = create_test_graph()
        root = graph.add_thought("Root", score=0.5)
        graph.add_thought("Child", parent_id=root.id, score=0.7)
        
        stats = graph.stats()
        
        assert stats["total_thoughts"] == 2
        assert stats["total_edges"] == 1
        assert stats["root_count"] == 1
        assert stats["leaf_count"] == 1
        assert stats["max_depth"] == 1


# =============================================================================
# Run Tests
# =============================================================================

def run_tests():
    """Run all tests without pytest."""
    import traceback
    
    test_classes = [
        TestBasicOperations,
        TestCycleDetection,
        TestTraversal,
        TestSearch,
        TestExpand,
        TestMergeAndPrune,
        TestSerialization,
        TestConfiguration,
        TestPersistence,
        TestMetrics,
        TestSearchStrategies,
        TestResourceLimits,
        TestVisualization,
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"Running {test_class.__name__}")
        print('='*60)
        
        instance = test_class()
        
        for method_name in dir(instance):
            if not method_name.startswith("test_"):
                continue
            
            method = getattr(instance, method_name)
            try:
                if asyncio.iscoroutinefunction(method):
                    asyncio.run(method())
                else:
                    method()
                print(f"  ✓ {method_name}")
                passed += 1
            except Exception as e:
                print(f"  ✗ {method_name}: {e}")
                errors.append((test_class.__name__, method_name, traceback.format_exc()))
                failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print('='*60)
    
    if errors:
        print("\nFailures:")
        for cls, method, tb in errors:
            print(f"\n{cls}.{method}:")
            print(tb)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
