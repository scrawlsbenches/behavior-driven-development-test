"""
Search strategies for Graph of Thought.

This module contains pluggable search algorithms that can be used
with the GraphOfThought class.
"""

from __future__ import annotations
from typing import TypeVar, Generic, Callable, Any
from dataclasses import dataclass, field
import heapq
import time
import random
import math

from ..core import (
    Thought,
    ThoughtStatus,
    SearchResult,
    SearchConfig,
    ThoughtGenerator,
    ThoughtEvaluator,
    GoalPredicate,
    GraphOperations,
)

T = TypeVar("T")


class BeamSearchStrategy(Generic[T]):
    """
    Standard beam search strategy.
    
    Keeps top K candidates at each level and expands all of them.
    """
    
    async def search(
        self,
        graph: GraphOperations[T],
        generator: ThoughtGenerator[T],
        evaluator: ThoughtEvaluator[T],
        config: SearchConfig,
        goal: GoalPredicate[T] | None = None,
    ) -> SearchResult[T]:
        start_time = time.time()
        total_tokens = 0
        expansions = 0
        termination_reason = "completed"
        
        root_ids = graph.get_root_ids()
        if not root_ids:
            return self._empty_result("no_roots")
        
        current_beam = [graph.get_thought(rid) for rid in root_ids]
        best_thought = max(current_beam, key=lambda t: t.score)
        expanded: set[str] = set()
        
        while current_beam:
            elapsed = time.time() - start_time
            if config.timeout_seconds and elapsed >= config.timeout_seconds:
                termination_reason = "timeout"
                break
            
            if goal:
                for thought in current_beam:
                    if goal(thought.content):
                        termination_reason = "goal_reached"
                        best_thought = thought
                        break
                if termination_reason == "goal_reached":
                    break
            
            if expansions >= config.max_expansions:
                termination_reason = "max_expansions"
                break
            
            all_children: list[Thought[T]] = []
            for thought in current_beam:
                if thought.id in expanded:
                    continue
                if thought.depth >= config.max_depth:
                    continue
                if thought.status == ThoughtStatus.PRUNED:
                    continue
                
                # This would normally call graph.expand() but we're using
                # the generator/evaluator directly for flexibility
                context = self._make_context(graph, thought.id)
                child_contents = await generator.generate(thought.content, context)
                
                for content in child_contents:
                    score = await evaluator.evaluate(content, context)
                    child = graph.add_thought(
                        content,
                        parent_id=thought.id,
                        score=score,
                    )
                    all_children.append(child)
                    
                    if child.score > best_thought.score:
                        best_thought = child
                
                expanded.add(thought.id)
                expansions += 1
                
                if config.max_tokens and total_tokens >= config.max_tokens:
                    termination_reason = "budget_exhausted"
                    break
            
            if termination_reason != "completed":
                break
            
            if not all_children:
                break
            
            all_children.sort(key=lambda t: t.score, reverse=True)
            current_beam = all_children[:config.beam_width]
        
        wall_time = time.time() - start_time
        best_path = graph.get_path_to_root(best_thought.id)
        
        return SearchResult(
            best_path=best_path,
            best_score=best_thought.score,
            thoughts_explored=graph.thought_count(),
            thoughts_expanded=expansions,
            total_tokens_used=total_tokens,
            wall_time_seconds=wall_time,
            termination_reason=termination_reason,
        )
    
    def _make_context(self, graph: GraphOperations[T], thought_id: str):
        from ..core import SearchContext
        thought = graph.get_thought(thought_id)
        path = graph.get_path_to_root(thought_id)
        return SearchContext(
            current_thought=thought,
            path_to_root=path,
            depth=thought.depth,
            tokens_remaining=None,
            time_remaining_seconds=None,
        )
    
    def _empty_result(self, reason: str) -> SearchResult[T]:
        return SearchResult(
            best_path=[],
            best_score=0.0,
            thoughts_explored=0,
            thoughts_expanded=0,
            total_tokens_used=0,
            wall_time_seconds=0.0,
            termination_reason=reason,
        )


@dataclass
class MCTSNode(Generic[T]):
    """Node in the MCTS tree."""
    thought_id: str
    visits: int = 0
    total_score: float = 0.0
    children: list[MCTSNode[T]] = field(default_factory=list)
    parent: MCTSNode[T] | None = None
    is_expanded: bool = False
    
    @property
    def average_score(self) -> float:
        return self.total_score / self.visits if self.visits > 0 else 0.0
    
    def ucb1(self, exploration_weight: float = 1.414) -> float:
        """Calculate UCB1 score for node selection."""
        if self.visits == 0:
            return float('inf')
        
        parent_visits = self.parent.visits if self.parent else self.visits
        exploitation = self.average_score
        exploration = exploration_weight * math.sqrt(math.log(parent_visits) / self.visits)
        return exploitation + exploration


class MCTSStrategy(Generic[T]):
    """
    Monte Carlo Tree Search strategy.
    
    Good for problems where evaluation is expensive and we want to
    focus exploration on promising areas.
    """
    
    def __init__(
        self,
        exploration_weight: float = 1.414,
        simulations_per_expansion: int = 10,
        max_simulation_depth: int = 5,
    ):
        self.exploration_weight = exploration_weight
        self.simulations_per_expansion = simulations_per_expansion
        self.max_simulation_depth = max_simulation_depth
    
    async def search(
        self,
        graph: GraphOperations[T],
        generator: ThoughtGenerator[T],
        evaluator: ThoughtEvaluator[T],
        config: SearchConfig,
        goal: GoalPredicate[T] | None = None,
    ) -> SearchResult[T]:
        start_time = time.time()
        expansions = 0
        total_tokens = 0
        termination_reason = "completed"
        
        root_ids = graph.get_root_ids()
        if not root_ids:
            return self._empty_result("no_roots")
        
        # Create MCTS root nodes
        roots = [MCTSNode[T](thought_id=rid) for rid in root_ids]
        best_thought = graph.get_thought(root_ids[0])
        
        while expansions < config.max_expansions:
            elapsed = time.time() - start_time
            if config.timeout_seconds and elapsed >= config.timeout_seconds:
                termination_reason = "timeout"
                break
            
            # Select a root to work with
            root = max(roots, key=lambda r: r.ucb1(self.exploration_weight))
            
            # Selection: traverse tree using UCB1
            node = self._select(root)
            
            # Expansion: add children to the selected node
            if not node.is_expanded:
                thought = graph.get_thought(node.thought_id)
                if thought.depth < config.max_depth:
                    await self._expand(node, graph, generator, evaluator)
                    expansions += 1
                node.is_expanded = True
            
            # Simulation: random rollout to estimate value
            if node.children:
                child = random.choice(node.children)
                score = await self._simulate(
                    child, graph, generator, evaluator, config.max_depth
                )
            else:
                score = graph.get_thought(node.thought_id).score
            
            # Backpropagation: update scores up the tree
            self._backpropagate(node, score)
            
            # Track best
            current_thought = graph.get_thought(node.thought_id)
            if current_thought.score > best_thought.score:
                best_thought = current_thought
            
            # Check goal
            if goal and goal(current_thought.content):
                termination_reason = "goal_reached"
                best_thought = current_thought
                break
        
        wall_time = time.time() - start_time
        best_path = graph.get_path_to_root(best_thought.id)
        
        return SearchResult(
            best_path=best_path,
            best_score=best_thought.score,
            thoughts_explored=graph.thought_count(),
            thoughts_expanded=expansions,
            total_tokens_used=total_tokens,
            wall_time_seconds=wall_time,
            termination_reason=termination_reason,
        )
    
    def _select(self, root: MCTSNode[T]) -> MCTSNode[T]:
        """Select a node to expand using UCB1."""
        node = root
        while node.children and node.is_expanded:
            node = max(node.children, key=lambda n: n.ucb1(self.exploration_weight))
        return node
    
    async def _expand(
        self,
        node: MCTSNode[T],
        graph: GraphOperations[T],
        generator: ThoughtGenerator[T],
        evaluator: ThoughtEvaluator[T],
    ) -> None:
        """Expand a node by generating children."""
        thought = graph.get_thought(node.thought_id)
        context = self._make_context(graph, node.thought_id)
        
        child_contents = await generator.generate(thought.content, context)
        
        for content in child_contents:
            score = await evaluator.evaluate(content, context)
            child_thought = graph.add_thought(
                content,
                parent_id=node.thought_id,
                score=score,
            )
            child_node = MCTSNode[T](thought_id=child_thought.id, parent=node)
            node.children.append(child_node)
    
    async def _simulate(
        self,
        node: MCTSNode[T],
        graph: GraphOperations[T],
        generator: ThoughtGenerator[T],
        evaluator: ThoughtEvaluator[T],
        max_depth: int,
    ) -> float:
        """Run a random simulation from the node."""
        thought = graph.get_thought(node.thought_id)
        current_score = thought.score
        depth = thought.depth
        
        # Simple simulation: just return the node's score
        # In a real implementation, we might do random rollouts
        return current_score
    
    def _backpropagate(self, node: MCTSNode[T], score: float) -> None:
        """Backpropagate score up the tree."""
        current: MCTSNode[T] | None = node
        while current is not None:
            current.visits += 1
            current.total_score += score
            current = current.parent
    
    def _make_context(self, graph: GraphOperations[T], thought_id: str):
        from ..core import SearchContext
        thought = graph.get_thought(thought_id)
        path = graph.get_path_to_root(thought_id)
        return SearchContext(
            current_thought=thought,
            path_to_root=path,
            depth=thought.depth,
            tokens_remaining=None,
            time_remaining_seconds=None,
        )
    
    def _empty_result(self, reason: str) -> SearchResult[T]:
        return SearchResult(
            best_path=[],
            best_score=0.0,
            thoughts_explored=0,
            thoughts_expanded=0,
            total_tokens_used=0,
            wall_time_seconds=0.0,
            termination_reason=reason,
        )


class IterativeDeepeningStrategy(Generic[T]):
    """
    Iterative deepening search strategy.
    
    Combines depth-first search's space efficiency with
    breadth-first search's completeness.
    """
    
    async def search(
        self,
        graph: GraphOperations[T],
        generator: ThoughtGenerator[T],
        evaluator: ThoughtEvaluator[T],
        config: SearchConfig,
        goal: GoalPredicate[T] | None = None,
    ) -> SearchResult[T]:
        start_time = time.time()
        total_expansions = 0
        termination_reason = "completed"
        best_thought: Thought[T] | None = None
        
        root_ids = graph.get_root_ids()
        if not root_ids:
            return self._empty_result("no_roots")
        
        for max_depth in range(1, config.max_depth + 1):
            elapsed = time.time() - start_time
            if config.timeout_seconds and elapsed >= config.timeout_seconds:
                termination_reason = "timeout"
                break
            
            # DFS to current depth limit
            result = await self._depth_limited_search(
                graph, generator, evaluator, config, goal, max_depth
            )
            
            total_expansions += result.thoughts_expanded
            
            if result.best_path:
                if best_thought is None or result.best_score > best_thought.score:
                    best_thought = result.best_path[-1]
            
            if result.termination_reason == "goal_reached":
                termination_reason = "goal_reached"
                best_thought = result.best_path[-1]
                break
            
            if total_expansions >= config.max_expansions:
                termination_reason = "max_expansions"
                break
        
        wall_time = time.time() - start_time
        best_path = graph.get_path_to_root(best_thought.id) if best_thought else []
        
        return SearchResult(
            best_path=best_path,
            best_score=best_thought.score if best_thought else 0.0,
            thoughts_explored=graph.thought_count(),
            thoughts_expanded=total_expansions,
            total_tokens_used=0,
            wall_time_seconds=wall_time,
            termination_reason=termination_reason,
        )
    
    async def _depth_limited_search(
        self,
        graph: GraphOperations[T],
        generator: ThoughtGenerator[T],
        evaluator: ThoughtEvaluator[T],
        config: SearchConfig,
        goal: GoalPredicate[T] | None,
        max_depth: int,
    ) -> SearchResult[T]:
        """Perform DFS up to a depth limit."""
        start_time = time.time()
        expansions = 0
        
        root_ids = graph.get_root_ids()
        stack = [(graph.get_thought(rid), 0) for rid in reversed(root_ids)]
        best_thought = stack[0][0] if stack else None
        expanded: set[str] = set()
        
        while stack:
            thought, depth = stack.pop()
            
            if goal and goal(thought.content):
                return SearchResult(
                    best_path=graph.get_path_to_root(thought.id),
                    best_score=thought.score,
                    thoughts_explored=graph.thought_count(),
                    thoughts_expanded=expansions,
                    total_tokens_used=0,
                    wall_time_seconds=time.time() - start_time,
                    termination_reason="goal_reached",
                )
            
            if best_thought is None or thought.score > best_thought.score:
                best_thought = thought
            
            if depth >= max_depth:
                continue
            
            if thought.id in expanded:
                continue
            
            expanded.add(thought.id)
            
            # Expand
            context = self._make_context(graph, thought.id)
            child_contents = await generator.generate(thought.content, context)
            
            for content in child_contents:
                score = await evaluator.evaluate(content, context)
                child = graph.add_thought(
                    content,
                    parent_id=thought.id,
                    score=score,
                )
                stack.append((child, depth + 1))
            
            expansions += 1
        
        return SearchResult(
            best_path=graph.get_path_to_root(best_thought.id) if best_thought else [],
            best_score=best_thought.score if best_thought else 0.0,
            thoughts_explored=graph.thought_count(),
            thoughts_expanded=expansions,
            total_tokens_used=0,
            wall_time_seconds=time.time() - start_time,
            termination_reason="completed",
        )
    
    def _make_context(self, graph: GraphOperations[T], thought_id: str):
        from ..core import SearchContext
        thought = graph.get_thought(thought_id)
        path = graph.get_path_to_root(thought_id)
        return SearchContext(
            current_thought=thought,
            path_to_root=path,
            depth=thought.depth,
            tokens_remaining=None,
            time_remaining_seconds=None,
        )
    
    def _empty_result(self, reason: str) -> SearchResult[T]:
        return SearchResult(
            best_path=[],
            best_score=0.0,
            thoughts_explored=0,
            thoughts_expanded=0,
            total_tokens_used=0,
            wall_time_seconds=0.0,
            termination_reason=reason,
        )
