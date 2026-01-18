"""
Core Layer - The Pure Heart of Graph of Thought
================================================

This layer contains the fundamental data structures and algorithms for
graph-based reasoning. It is the ONLY layer that truly matters - everything
else exists to support, extend, or constrain what happens here.

DESIGN PRINCIPLES
-----------------

1. ZERO DEPENDENCIES
   This layer imports NOTHING from other layers. Not context, not services,
   not middleware. It depends only on Python's standard library.

   Why? Because the core must be:
   - Testable without mocks (just call functions, check results)
   - Understandable in isolation (read these files, understand reasoning)
   - Stable over time (external changes don't ripple here)

2. PURE FUNCTIONS WHERE POSSIBLE
   Operations like expand() and evaluate() are pure: same input → same output.
   The graph itself is mutable (you add thoughts to it), but operations on
   thoughts are pure.

   This means:
   - Easy to test (no setup, no teardown, no state to manage)
   - Easy to parallelize (no shared mutable state between operations)
   - Easy to reason about (no "what changed this?")

3. SIMPLE DATA STRUCTURES
   A Thought is just: id + content + score
   A Graph is just: thoughts + parent-child relationships

   No metadata fields "just in case." No optional fields for future features.
   If we need more later, we add it then. YAGNI (You Aren't Gonna Need It).

4. ALGORITHMS ARE SEPARATE FROM DATA
   The Graph class knows how to store and retrieve thoughts.
   The search module knows how to explore the graph.
   They're separate because they change for different reasons:
   - Graph changes if we change how thoughts relate
   - Search changes if we change how we explore

WHAT BELONGS HERE
-----------------

✓ Thought dataclass
✓ Graph data structure
✓ Search algorithms (beam search, etc.)
✓ Pure expansion/evaluation function signatures

WHAT DOES NOT BELONG HERE
-------------------------

✗ LLM calls (that's a service)
✗ Persistence (that's a service)
✗ Logging (that's middleware)
✗ Budget checking (that's middleware)
✗ Governance (that's policy)
✗ Configuration loading (that's application)

If it has side effects, it doesn't belong here.
If it depends on external systems, it doesn't belong here.
If it changes based on environment, it doesn't belong here.

"""

from graph_of_thought_v2.core.thought import Thought
from graph_of_thought_v2.core.graph import Graph
from graph_of_thought_v2.core.search import SearchResult, beam_search

__all__ = [
    "Thought",
    "Graph",
    "SearchResult",
    "beam_search",
]
