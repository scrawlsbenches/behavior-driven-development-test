"""
Search - Algorithms for Exploring the Graph
============================================

Search algorithms traverse the graph to find the best path from root to
solution. They use expansion (generating new thoughts) and evaluation
(scoring thoughts) to guide the exploration.

DESIGN DECISIONS
----------------

1. WHY FUNCTIONS, NOT CLASSES?

   Search algorithms are pure functions: given a graph and operations,
   find the best path. They don't need state. Classes would add complexity
   without benefit.

   If you need to configure a search (max depth, beam width), pass a
   config object. Don't make the algorithm stateful.

2. WHY ASYNC?

   Expansion and evaluation often call LLMs, which are I/O bound. Async
   allows efficient parallelization. Even if your expander is synchronous,
   the overhead of async is negligible.

3. WHY PASS EXPAND/EVALUATE AS ARGUMENTS?

   The search algorithm doesn't know HOW to generate thoughts or score them.
   It just knows WHEN to call these operations. This separation allows:

   - Different generators for different problems
   - Different evaluators for different criteria
   - Testing with simple mock functions
   - Swapping strategies without changing search logic

4. WHY RETURN SearchResult, NOT JUST PATH?

   A result includes:
   - The best path found
   - Statistics about the search (nodes expanded, time taken)
   - Whether the search completed or was terminated

   This metadata is essential for debugging, optimization, and understanding.

5. WHY BEAM SEARCH AS DEFAULT?

   Beam search balances exploration and exploitation:
   - Explores multiple paths (not just greedy)
   - Limits memory by keeping only top-K at each level
   - Works well for most reasoning problems

   We can add other algorithms (MCTS, A*, etc.) as needed.

ALGORITHM OVERVIEW
------------------

BEAM SEARCH:

    1. Start with root thought(s) in the beam
    2. Expand all thoughts in the beam (generate children)
    3. Evaluate all children
    4. Keep top-K children as the new beam
    5. Repeat until max_depth or goal reached

    Beam width (K) controls exploration vs. speed tradeoff.
    Larger beam = more exploration, slower search.

THE EXPAND/EVALUATE PROTOCOL
----------------------------

These are the two extension points. The search calls them; you implement them.

    async def expand(thought: Thought[T], context: Context) -> list[T]:
        '''Generate child content from a parent thought.'''

    async def evaluate(thought: Thought[T], context: Context) -> float:
        '''Score a thought from 0.0 (bad) to 1.0 (good).'''

The context provides information about the search state (depth, budget).
Implementations can use this to make better decisions.

"""

from dataclasses import dataclass, field
from typing import TypeVar, Generic, Protocol, Callable, Awaitable
from graph_of_thought_v2.core.thought import Thought
from graph_of_thought_v2.core.graph import Graph

T = TypeVar("T")


# =============================================================================
# SEARCH RESULT
# =============================================================================

@dataclass
class SearchResult(Generic[T]):
    """
    The result of a search operation.

    Contains the best path found, along with metadata about the search.

    Attributes:
        best_path: The highest-scoring path from root to leaf.
        best_score: The score of the final thought in the best path.
        completed: Whether the search finished normally (vs. terminated).
        thoughts_expanded: Number of thoughts that were expanded.
        thoughts_evaluated: Number of thoughts that were evaluated.
        max_depth_reached: The deepest level explored.

    Example:
        >>> result = await beam_search(graph, expand, evaluate, config)
        >>> print(f"Best solution: {result.best_path[-1].content}")
        >>> print(f"Explored {result.thoughts_expanded} thoughts")
    """

    best_path: list[Thought[T]]
    """The path from root to the best leaf thought."""

    best_score: float
    """The score of the best leaf thought."""

    completed: bool = True
    """True if search finished normally, False if terminated early."""

    thoughts_expanded: int = 0
    """How many thoughts were expanded (had children generated)."""

    thoughts_evaluated: int = 0
    """How many thoughts were evaluated (had scores computed)."""

    max_depth_reached: int = 0
    """The maximum depth explored during search."""

    termination_reason: str | None = None
    """If completed is False, why was the search terminated?"""


# =============================================================================
# SEARCH CONFIGURATION
# =============================================================================

@dataclass
class SearchConfig:
    """
    Configuration for search algorithms.

    Attributes:
        max_depth: Maximum depth to explore (root is depth 0).
        beam_width: Number of thoughts to keep at each level.
        max_expansions: Maximum total expansions before terminating.
        goal_score: If a thought reaches this score, stop searching.

    Example:
        >>> config = SearchConfig(max_depth=5, beam_width=3)
        >>> result = await beam_search(graph, expand, evaluate, config)
    """

    max_depth: int = 10
    """Maximum depth to explore. Deeper = more thorough, but slower."""

    beam_width: int = 3
    """Number of top thoughts to keep at each level. Wider = more exploration."""

    max_expansions: int = 100
    """Safety limit on total expansions. Prevents runaway searches."""

    goal_score: float = 0.95
    """If any thought scores this high, consider the search successful."""


# =============================================================================
# EXPAND/EVALUATE PROTOCOLS
# =============================================================================

class Expander(Protocol[T]):
    """
    Protocol for thought expansion.

    An expander generates child thoughts from a parent. This is where
    the "thinking" happens - typically by calling an LLM.

    The context argument provides information about the current search
    state, which implementations can use to generate better thoughts.
    """

    async def __call__(
        self,
        thought: Thought[T],
        context: "SearchContext[T]",
    ) -> list[T]:
        """
        Generate child content from a parent thought.

        Args:
            thought: The thought to expand.
            context: Information about the search state.

        Returns:
            List of content for child thoughts (not Thought objects).
            The search will wrap these in Thought objects.
        """
        ...


class Evaluator(Protocol[T]):
    """
    Protocol for thought evaluation.

    An evaluator scores a thought, indicating how promising it is.
    Higher scores mean the thought is more likely to lead to a solution.

    The context argument provides information about the current search
    state, which implementations can use for relative evaluation.
    """

    async def __call__(
        self,
        thought: Thought[T],
        context: "SearchContext[T]",
    ) -> float:
        """
        Score a thought.

        Args:
            thought: The thought to evaluate.
            context: Information about the search state.

        Returns:
            Score from 0.0 (worthless) to 1.0 (perfect).
        """
        ...


# =============================================================================
# SEARCH CONTEXT (passed to expand/evaluate)
# =============================================================================

@dataclass
class SearchContext(Generic[T]):
    """
    Context passed to expand and evaluate functions.

    This provides information about the current search state, allowing
    implementations to make context-aware decisions.

    Attributes:
        graph: The full graph (read-only access to all thoughts).
        current_depth: How deep we are in the search.
        path_to_root: The path from current thought to root.
        thoughts_expanded: How many thoughts have been expanded so far.
        config: The search configuration.

    Note:
        This is a CORE context, not the same as the execution context
        from the context layer. This context is specific to search.
    """

    graph: Graph[T]
    """The full graph being searched."""

    current_depth: int
    """Current depth in the search (root = 0)."""

    path_to_root: list[Thought[T]]
    """Path from current thought to root."""

    thoughts_expanded: int
    """Total expansions so far in this search."""

    config: SearchConfig
    """The search configuration."""


# =============================================================================
# BEAM SEARCH ALGORITHM
# =============================================================================

async def beam_search(
    graph: Graph[T],
    expand: Expander[T] | Callable[[Thought[T], SearchContext[T]], Awaitable[list[T]]],
    evaluate: Evaluator[T] | Callable[[Thought[T], SearchContext[T]], Awaitable[float]],
    config: SearchConfig | None = None,
) -> SearchResult[T]:
    """
    Beam search algorithm for graph exploration.

    Beam search maintains a "beam" of the K most promising thoughts at each
    depth level. It expands all thoughts in the beam, evaluates the children,
    and keeps the top K for the next iteration.

    This balances thorough exploration (considering multiple paths) with
    efficiency (not exploring everything).

    Args:
        graph: The graph to search. Must have at least one root.
        expand: Function to generate child content from a thought.
        evaluate: Function to score a thought.
        config: Search parameters. Uses defaults if not provided.

    Returns:
        SearchResult containing the best path and search statistics.

    Raises:
        ValueError: If the graph has no roots.

    Algorithm:
        1. Initialize beam with root thoughts
        2. While depth < max_depth and expansions < max_expansions:
           a. Expand all thoughts in beam
           b. Evaluate all new children
           c. Keep top beam_width children as new beam
           d. If any thought scores >= goal_score, stop
        3. Return best path from any leaf

    Example:
        >>> async def my_expand(thought, ctx):
        ...     # Generate children (maybe call LLM)
        ...     return ["child1", "child2", "child3"]

        >>> async def my_evaluate(thought, ctx):
        ...     # Score the thought (maybe call LLM)
        ...     return 0.7

        >>> result = await beam_search(graph, my_expand, my_evaluate)
        >>> print(result.best_path)
    """
    config = config or SearchConfig()

    roots = graph.roots()
    if not roots:
        raise ValueError("Graph must have at least one root thought")

    # Statistics tracking
    total_expansions = 0
    total_evaluations = 0
    max_depth_seen = 0

    # Initialize beam with roots
    beam = roots.copy()

    # Evaluate initial beam
    for thought in beam:
        ctx = SearchContext(
            graph=graph,
            current_depth=0,
            path_to_root=[thought],
            thoughts_expanded=total_expansions,
            config=config,
        )
        thought.score = await evaluate(thought, ctx)
        total_evaluations += 1

        # Check for early goal
        if thought.score >= config.goal_score:
            return SearchResult(
                best_path=[thought],
                best_score=thought.score,
                completed=True,
                thoughts_expanded=total_expansions,
                thoughts_evaluated=total_evaluations,
                max_depth_reached=0,
            )

    # Main search loop
    current_depth = 0

    while current_depth < config.max_depth:
        if total_expansions >= config.max_expansions:
            break

        current_depth += 1
        max_depth_seen = max(max_depth_seen, current_depth)

        # Expand all thoughts in beam
        all_children: list[Thought[T]] = []

        for parent in beam:
            if total_expansions >= config.max_expansions:
                break

            ctx = SearchContext(
                graph=graph,
                current_depth=current_depth - 1,
                path_to_root=graph.path_to_root(parent),
                thoughts_expanded=total_expansions,
                config=config,
            )

            # Generate child content
            child_contents = await expand(parent, ctx)
            total_expansions += 1

            # Create and add child thoughts
            for content in child_contents:
                child = Thought(content=content)
                graph.add(child, parent=parent)
                all_children.append(child)

        if not all_children:
            # No children generated, search is complete
            break

        # Evaluate all children
        for child in all_children:
            ctx = SearchContext(
                graph=graph,
                current_depth=current_depth,
                path_to_root=graph.path_to_root(child),
                thoughts_expanded=total_expansions,
                config=config,
            )
            child.score = await evaluate(child, ctx)
            total_evaluations += 1

            # Check for goal
            if child.score >= config.goal_score:
                return SearchResult(
                    best_path=graph.path_to_root(child)[::-1],  # Reverse: root to leaf
                    best_score=child.score,
                    completed=True,
                    thoughts_expanded=total_expansions,
                    thoughts_evaluated=total_evaluations,
                    max_depth_reached=max_depth_seen,
                )

        # Keep top beam_width children
        all_children.sort(key=lambda t: t.score, reverse=True)
        beam = all_children[:config.beam_width]

    # Search complete, find best leaf
    leaves = graph.leaves()
    if not leaves:
        # Edge case: graph only has roots
        leaves = roots

    best_leaf = max(leaves, key=lambda t: t.score)
    best_path = graph.path_to_root(best_leaf)[::-1]  # Reverse: root to leaf

    return SearchResult(
        best_path=best_path,
        best_score=best_leaf.score,
        completed=total_expansions < config.max_expansions,
        thoughts_expanded=total_expansions,
        thoughts_evaluated=total_evaluations,
        max_depth_reached=max_depth_seen,
        termination_reason="max_expansions" if total_expansions >= config.max_expansions else None,
    )
