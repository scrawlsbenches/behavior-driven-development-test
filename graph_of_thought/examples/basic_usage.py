from __future__ import annotations
#!/usr/bin/env python3
"""
Example usage of the Graph of Thought package.

This demonstrates:
1. Basic usage with simple functions
2. Configuration from environment/files
3. Using persistence
4. Using metrics
5. Search strategies
"""

import asyncio
from graph_of_thought import (
    GraphOfThought,
    GraphConfig,
    SearchConfig,
    InMemoryMetricsCollector,
    StandardLogger,
)
from graph_of_thought.persistence import InMemoryPersistence
from graph_of_thought.search import BeamSearchStrategy, MCTSStrategy


# =============================================================================
# Example 1: Basic Usage
# =============================================================================

def basic_example():
    """Simple example with function-based generator and evaluator."""
    
    def evaluate(thought: str) -> float:
        """Score thoughts based on keyword presence."""
        keywords = {
            "parallel": 0.3, "cache": 0.25, "algorithm": 0.2,
            "profile": 0.15, "optimize": 0.1, "reduce": 0.2,
            "complexity": 0.25, "memory": 0.15, "batch": 0.2,
        }
        score = sum(v for k, v in keywords.items() if k in thought.lower())
        return min(score, 1.0)
    
    def generate(parent: str) -> list[str]:
        """Generate refinements of a thought."""
        if "optimize" in parent.lower():
            return [
                f"{parent} → Use parallel processing",
                f"{parent} → Implement caching layer",
                f"{parent} → Reduce algorithmic complexity",
            ]
        elif "parallel" in parent.lower():
            return [
                f"{parent} → Use thread pool",
                f"{parent} → Batch operations",
            ]
        else:
            return [
                f"{parent} → Profile first",
                f"{parent} → Optimize hot paths",
            ]
    
    # Create graph with simple functions
    graph = GraphOfThought[str](
        evaluator=evaluate,
        generator=generate,
        max_depth=4,
        beam_width=2,
    )
    
    return graph


async def run_basic_example():
    """Run the basic example."""
    print("=" * 60)
    print("Basic Example")
    print("=" * 60)
    
    graph = basic_example()
    
    # Add root thought
    root = graph.add_thought("Optimize database query performance")
    print(f"\nRoot thought: {root.content}")
    
    # Run beam search
    result = await graph.beam_search()
    
    print(f"\nSearch completed:")
    print(f"  Termination: {result.termination_reason}")
    print(f"  Expansions: {result.thoughts_expanded}")
    print(f"  Best score: {result.best_score:.2f}")
    
    print("\nBest path:")
    for i, thought in enumerate(result.best_path):
        print(f"  {'  ' * i}→ [{thought.score:.2f}] {thought.content[:60]}...")
    
    print("\n" + graph.visualize())
    return graph


# =============================================================================
# Example 2: With Configuration and Observability
# =============================================================================

async def run_configured_example():
    """Example with full configuration and observability."""
    print("\n" + "=" * 60)
    print("Configured Example with Observability")
    print("=" * 60)
    
    # Create configuration
    config = GraphConfig(
        allow_cycles=False,
        auto_checkpoint=True,
    )
    config.limits.max_depth = 5
    config.limits.max_thoughts = 1000
    config.search.beam_width = 3
    config.search.max_expansions = 50
    
    # Create observability components
    metrics = InMemoryMetricsCollector()
    logger = StandardLogger("got_example")
    
    def evaluate(thought: str) -> float:
        keywords = {"optimize", "cache", "parallel", "algorithm", "reduce"}
        return min(sum(0.2 for k in keywords if k in thought.lower()), 1.0)
    
    def generate(parent: str) -> list[str]:
        return [
            f"{parent} → Approach A",
            f"{parent} → Approach B",
            f"{parent} → Approach C",
        ]
    
    # Create graph with configuration
    graph = GraphOfThought[str](
        config=config,
        evaluator=evaluate,
        generator=generate,
        metrics=metrics,
        logger=logger,
    )
    
    # Run search
    root = graph.add_thought("Optimize system performance")
    result = await graph.beam_search()
    
    print(f"\nSearch result: {result.termination_reason}")
    print(f"Best score: {result.best_score:.2f}")
    
    # Check metrics
    print("\nMetrics collected:")
    for key, value in metrics.counters.items():
        print(f"  {key}: {value}")
    
    print("\nGraph stats:")
    for key, value in graph.stats().items():
        print(f"  {key}: {value}")


# =============================================================================
# Example 3: With Persistence
# =============================================================================

async def run_persistence_example():
    """Example with persistence for checkpointing."""
    print("\n" + "=" * 60)
    print("Persistence Example")
    print("=" * 60)
    
    persistence = InMemoryPersistence()
    
    def evaluate(thought: str) -> float:
        return len(thought) / 100.0
    
    def generate(parent: str) -> list[str]:
        return [f"{parent} → Option {i}" for i in range(3)]
    
    # Create and populate graph
    graph = GraphOfThought[str](
        evaluator=evaluate,
        generator=generate,
        persistence=persistence,
    )
    
    root = graph.add_thought("Start reasoning")
    await graph.expand(root.id)
    
    # Save to persistence
    await persistence.save_graph(
        graph_id="example_graph",
        thoughts=graph.thoughts,
        edges=graph.edges,
        root_ids=graph.root_ids,
        metadata={"description": "Example graph"},
    )
    print("\nGraph saved to persistence")
    
    # Load from persistence
    loaded = await persistence.load_graph("example_graph")
    if loaded:
        thoughts, edges, root_ids, metadata = loaded
        print(f"Loaded graph: {len(thoughts)} thoughts, {len(edges)} edges")
    
    # Test serialization round-trip
    json_str = graph.to_json()
    restored = GraphOfThought.from_json(
        json_str,
        evaluator=evaluate,
        generator=generate,
    )
    print(f"JSON round-trip: {len(restored)} thoughts")


# =============================================================================
# Example 4: Custom Search Strategy
# =============================================================================

async def run_strategy_example():
    """Example with custom search strategy."""
    print("\n" + "=" * 60)
    print("Custom Strategy Example (MCTS)")
    print("=" * 60)
    
    def evaluate(thought: str) -> float:
        return min(len(thought) / 50.0, 1.0)
    
    def generate(parent: str) -> list[str]:
        return [f"{parent} → Branch {i}" for i in range(2)]
    
    graph = GraphOfThought[str](
        evaluator=evaluate,
        generator=generate,
        max_depth=6,
    )
    
    root = graph.add_thought("Root problem")
    
    # Use MCTS strategy
    strategy = MCTSStrategy[str](
        exploration_weight=1.414,
        simulations_per_expansion=5,
    )
    
    # Create generator/evaluator wrappers for the strategy
    from graph_of_thought.core.defaults import FunctionGenerator, FunctionEvaluator
    
    gen = FunctionGenerator(generate)
    eval_ = FunctionEvaluator(evaluate)
    
    config = SearchConfig(
        max_depth=6,
        max_expansions=20,
    )
    
    result = await strategy.search(
        graph=graph.as_operations(),
        generator=gen,
        evaluator=eval_,
        config=config,
    )
    
    print(f"\nMCTS result: {result.termination_reason}")
    print(f"Expansions: {result.thoughts_expanded}")
    print(f"Best score: {result.best_score:.2f}")


# =============================================================================
# Example 5: Goal-Directed Search
# =============================================================================

async def run_goal_example():
    """Example with goal-directed search."""
    print("\n" + "=" * 60)
    print("Goal-Directed Search Example")
    print("=" * 60)
    
    target = "solution found"
    
    def evaluate(thought: str) -> float:
        if target in thought.lower():
            return 1.0
        return 0.3
    
    def generate(parent: str) -> list[str]:
        depth = parent.count("→")
        if depth >= 3:
            return [f"{parent} → Solution Found!"]
        return [
            f"{parent} → Continue path A",
            f"{parent} → Continue path B",
        ]
    
    graph = GraphOfThought[str](
        evaluator=evaluate,
        generator=generate,
        max_depth=10,
    )
    
    root = graph.add_thought("Find the solution")
    
    # Define goal
    def goal(content: str) -> bool:
        return "solution found" in content.lower()
    
    result = await graph.beam_search(goal=goal)
    
    print(f"\nSearch terminated: {result.termination_reason}")
    if result.termination_reason == "goal_reached":
        print("Goal reached!")
        print(f"Path length: {len(result.best_path)}")
        for thought in result.best_path:
            print(f"  → {thought.content}")


# =============================================================================
# Main
# =============================================================================

async def main():
    """Run all examples."""
    await run_basic_example()
    await run_configured_example()
    await run_persistence_example()
    await run_strategy_example()
    await run_goal_example()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
