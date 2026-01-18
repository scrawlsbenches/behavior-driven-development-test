"""
Graph - The Structure of Reasoning
==================================

The Graph is where thoughts live and connect. It's a directed graph where:
- Nodes are Thoughts
- Edges represent derivation (parent → child means "child was derived from parent")

Typically, reasoning graphs are trees (one parent per child), but the
structure supports DAGs (multiple parents) for future flexibility.

DESIGN DECISIONS
----------------

1. WHY A CLASS, NOT JUST DICTS?

   We could store thoughts in a dict and edges in another dict. But a class:
   - Encapsulates invariants (every child has a parent, except roots)
   - Provides a clear API (add, children, path_to_root)
   - Hides implementation details (could switch to adjacency matrix later)

2. WHY MUTABLE?

   Graphs grow as we explore. We add thoughts during search. Immutable
   graphs would require copying the entire structure on each addition,
   which is expensive and unnecessary.

   The graph is the ONE mutable thing in the core. Thoughts, once added,
   are mostly treated as immutable. Search algorithms don't modify the
   graph (they just read it). Only expansion adds new thoughts.

3. WHY MULTIPLE ROOTS?

   Most graphs have one root (the initial problem). But sometimes:
   - We want to explore multiple starting points
   - We merge graphs from different sessions
   - We resume from multiple promising paths

   Supporting multiple roots costs nothing and adds flexibility.

4. WHY NO REMOVE?

   Thoughts, once added, are not removed. This is intentional:
   - Simpler reasoning about state (thoughts don't disappear)
   - Audit trail preserved (we can see the full exploration)
   - No dangling references (children of removed thoughts)

   If you want to "hide" a thought, that's a view concern, not a
   graph concern. The graph is the complete record.

5. WHY STORE BOTH PARENT→CHILDREN AND CHILD→PARENT?

   Bidirectional indexing allows efficient:
   - children(thought) - for expansion
   - path_to_root(thought) - for understanding reasoning chains

   The cost is maintaining two dicts, but graphs are small (thousands of
   thoughts at most) and the convenience is worth it.

INVARIANTS
----------

These are always true for a valid Graph:

1. Every thought in the graph has a unique ID
2. Every thought except roots has exactly one parent (tree structure)
3. Every child's parent is also in the graph
4. There are no cycles (it's a DAG, specifically a forest of trees)

The class enforces these invariants. You cannot create an invalid graph
through the public API.

FUTURE CONSIDERATIONS
---------------------

- Weighted edges (confidence in derivation)
- Edge labels (type of derivation: "elaboration", "alternative", "criticism")
- Subgraph extraction (get all thoughts below a certain node)
- Serialization (to/from JSON, handled by persistence service)

"""

from typing import Generic, TypeVar, Iterator
from graph_of_thought_v2.core.thought import Thought

T = TypeVar("T")


class Graph(Generic[T]):
    """
    A directed graph of thoughts representing a reasoning process.

    The graph tracks thoughts and their relationships. Each thought can have
    one parent (except roots, which have none) and multiple children.

    Attributes:
        thoughts: All thoughts in the graph, keyed by ID.

    Example:
        >>> graph = Graph()
        >>> root = graph.add(Thought(content="How do we improve performance?"))
        >>> child1 = graph.add(Thought(content="Add caching"), parent=root)
        >>> child2 = graph.add(Thought(content="Optimize queries"), parent=root)
        >>> graph.children(root)
        [child1, child2]

    Thread Safety:
        This class is NOT thread-safe. If multiple threads need to modify
        the graph, external synchronization is required. In practice, graphs
        are typically modified by a single search process.

    Memory:
        All thoughts are stored in memory. For very large graphs (100k+ thoughts),
        consider using a persistence service with lazy loading.
    """

    def __init__(self) -> None:
        """Create an empty graph."""
        # Primary storage: id → thought
        self._thoughts: dict[str, Thought[T]] = {}

        # Relationship indexes
        self._children: dict[str, list[str]] = {}  # parent_id → [child_ids]
        self._parent: dict[str, str | None] = {}   # child_id → parent_id

        # Quick access to roots (thoughts with no parent)
        self._roots: set[str] = set()

    # =========================================================================
    # CORE OPERATIONS
    # =========================================================================

    def add(self, thought: Thought[T], parent: Thought[T] | None = None) -> Thought[T]:
        """
        Add a thought to the graph.

        Args:
            thought: The thought to add.
            parent: Optional parent thought. If None, this becomes a root.

        Returns:
            The added thought (same object, for chaining).

        Raises:
            ValueError: If thought ID already exists in graph.
            ValueError: If parent is not in the graph.

        Example:
            >>> graph = Graph()
            >>> root = graph.add(Thought(content="Problem"))
            >>> child = graph.add(Thought(content="Solution"), parent=root)
        """
        if thought.id in self._thoughts:
            raise ValueError(f"Thought with id {thought.id!r} already exists in graph")

        if parent is not None and parent.id not in self._thoughts:
            raise ValueError(f"Parent thought {parent.id!r} not in graph")

        # Store the thought
        self._thoughts[thought.id] = thought

        # Set up relationships
        parent_id = parent.id if parent else None
        self._parent[thought.id] = parent_id

        if parent_id is None:
            # This is a root
            self._roots.add(thought.id)
        else:
            # Add to parent's children
            if parent_id not in self._children:
                self._children[parent_id] = []
            self._children[parent_id].append(thought.id)

        # Initialize children list for this thought
        self._children[thought.id] = []

        return thought

    def get(self, thought_id: str) -> Thought[T] | None:
        """
        Get a thought by ID.

        Args:
            thought_id: The ID to look up.

        Returns:
            The thought, or None if not found.
        """
        return self._thoughts.get(thought_id)

    def __contains__(self, thought: Thought[T]) -> bool:
        """Check if a thought is in the graph."""
        return thought.id in self._thoughts

    def __len__(self) -> int:
        """Return the number of thoughts in the graph."""
        return len(self._thoughts)

    def __iter__(self) -> Iterator[Thought[T]]:
        """Iterate over all thoughts in the graph."""
        return iter(self._thoughts.values())

    # =========================================================================
    # RELATIONSHIP QUERIES
    # =========================================================================

    def children(self, thought: Thought[T]) -> list[Thought[T]]:
        """
        Get the children of a thought.

        Args:
            thought: The parent thought.

        Returns:
            List of child thoughts (empty if none).

        Raises:
            ValueError: If thought is not in the graph.
        """
        if thought.id not in self._thoughts:
            raise ValueError(f"Thought {thought.id!r} not in graph")

        child_ids = self._children.get(thought.id, [])
        return [self._thoughts[cid] for cid in child_ids]

    def parent(self, thought: Thought[T]) -> Thought[T] | None:
        """
        Get the parent of a thought.

        Args:
            thought: The child thought.

        Returns:
            The parent thought, or None if this is a root.

        Raises:
            ValueError: If thought is not in the graph.
        """
        if thought.id not in self._thoughts:
            raise ValueError(f"Thought {thought.id!r} not in graph")

        parent_id = self._parent.get(thought.id)
        if parent_id is None:
            return None
        return self._thoughts[parent_id]

    def roots(self) -> list[Thought[T]]:
        """
        Get all root thoughts (those with no parent).

        Returns:
            List of root thoughts.
        """
        return [self._thoughts[rid] for rid in self._roots]

    def path_to_root(self, thought: Thought[T]) -> list[Thought[T]]:
        """
        Get the path from a thought to its root.

        The path starts with the given thought and ends with the root.

        Args:
            thought: The starting thought.

        Returns:
            List of thoughts from this thought to the root (inclusive).

        Raises:
            ValueError: If thought is not in the graph.

        Example:
            >>> path = graph.path_to_root(leaf)
            >>> path  # [leaf, parent, grandparent, root]
        """
        if thought.id not in self._thoughts:
            raise ValueError(f"Thought {thought.id!r} not in graph")

        path = [thought]
        current = thought

        while True:
            parent_id = self._parent.get(current.id)
            if parent_id is None:
                break
            current = self._thoughts[parent_id]
            path.append(current)

        return path

    def depth(self, thought: Thought[T]) -> int:
        """
        Get the depth of a thought (distance from root).

        Roots have depth 0. Their children have depth 1. Etc.

        Args:
            thought: The thought to measure.

        Returns:
            The depth (0 for roots).

        Raises:
            ValueError: If thought is not in the graph.
        """
        return len(self.path_to_root(thought)) - 1

    # =========================================================================
    # TREE QUERIES
    # =========================================================================

    def leaves(self) -> list[Thought[T]]:
        """
        Get all leaf thoughts (those with no children).

        Returns:
            List of leaf thoughts.
        """
        return [t for t in self._thoughts.values() if not self._children.get(t.id)]

    def subtree(self, thought: Thought[T]) -> list[Thought[T]]:
        """
        Get all thoughts in the subtree rooted at the given thought.

        Includes the thought itself and all descendants.

        Args:
            thought: The root of the subtree.

        Returns:
            List of all thoughts in the subtree (breadth-first order).

        Raises:
            ValueError: If thought is not in the graph.
        """
        if thought.id not in self._thoughts:
            raise ValueError(f"Thought {thought.id!r} not in graph")

        result = []
        queue = [thought]

        while queue:
            current = queue.pop(0)
            result.append(current)
            queue.extend(self.children(current))

        return result

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def max_depth(self) -> int:
        """
        Get the maximum depth of the graph.

        Returns:
            The maximum depth, or -1 if the graph is empty.
        """
        if not self._thoughts:
            return -1
        return max(self.depth(t) for t in self._thoughts.values())

    def branching_factor(self) -> float:
        """
        Get the average branching factor (children per non-leaf node).

        Returns:
            The average branching factor, or 0.0 if no non-leaf nodes.
        """
        non_leaves = [t for t in self._thoughts.values() if self._children.get(t.id)]
        if not non_leaves:
            return 0.0
        total_children = sum(len(self._children[t.id]) for t in non_leaves)
        return total_children / len(non_leaves)
