"""
Thought - The Fundamental Unit of Reasoning
===========================================

A Thought is a single node in the reasoning graph. It contains:
- An identity (id)
- Content (what the thought says)
- A score (how promising this thought is)

That's it. No metadata, no timestamps, no user tracking. Those concerns
belong elsewhere. A Thought is pure data.

DESIGN DECISIONS
----------------

1. WHY GENERIC CONTENT (T)?

   Thoughts can contain anything: strings, structured data, embeddings.
   We don't prescribe what "content" means. This allows:

   - Simple text thoughts for prototyping
   - Structured thoughts with multiple fields
   - Vector embeddings for semantic search
   - Custom domain objects for specific applications

   The graph doesn't care what's inside a thought. It just stores and
   connects them.

2. WHY IMMUTABLE SCORE?

   Actually, score IS mutable in this design. Here's why:

   Scores may be refined as we learn more. A thought that seemed promising
   might look worse after we explore its children. A thought that seemed
   weak might be the only path to the solution.

   However, the Thought itself is mostly treated as immutable. We create
   thoughts, add them to the graph, and then the graph owns them. Direct
   mutation should be rare and intentional.

3. WHY STRING IDS?

   UUIDs are strings. Database IDs can be strings. Semantic IDs (like
   "root" or "best-path-node-3") are strings. Strings are universal.

   We generate UUIDs by default, but the system accepts any string.
   This allows:
   - Deterministic IDs for testing ("test-thought-1")
   - Meaningful IDs for debugging ("expansion-of-abc123")
   - External IDs for integration (database primary keys)

4. WHY NO PARENT REFERENCE?

   Thoughts don't know their parents. The Graph tracks relationships.

   Why? Because a thought could theoretically have multiple parents
   (in a DAG, not a tree). Even if we only support trees now, baking
   "parent" into Thought would make DAGs impossible later.

   Also: circular references are bugs waiting to happen. By keeping
   relationships in the Graph, we avoid Thought→Thought references
   that could create cycles or memory leaks.

5. WHY NO CHILDREN REFERENCE?

   Same reason as parents. The Graph is the source of truth for structure.
   Thoughts are just nodes. The Graph is the... graph.

FUTURE CONSIDERATIONS
---------------------

We might add:
- created_at: datetime (for debugging and visualization)
- metadata: dict (for extensibility)

But not yet. We add fields when we need them, not when we imagine
we might need them. Every field is a maintenance burden.

"""

from dataclasses import dataclass, field
from typing import Generic, TypeVar
from uuid import uuid4

# Generic type for thought content
# Could be str, dict, a domain object, an embedding vector, etc.
T = TypeVar("T")


@dataclass
class Thought(Generic[T]):
    """
    A single node in the reasoning graph.

    Thoughts are the fundamental unit of reasoning. Each thought contains
    some content (the "what") and a score (the "how promising").

    Attributes:
        id: Unique identifier for this thought. Auto-generated if not provided.
        content: The substance of this thought. Generic type allows flexibility.
        score: How promising this thought is (0.0 to 1.0, higher is better).

    Example:
        >>> thought = Thought(content="Use caching to improve performance")
        >>> thought.score = 0.85  # After evaluation

        >>> # With explicit ID (useful for testing)
        >>> thought = Thought(id="test-1", content="Test thought", score=0.5)

    Design Note:
        Thoughts don't know about their parents or children. The Graph
        maintains all relationships. This keeps Thoughts simple and
        prevents circular reference issues.
    """

    content: T
    """The substance of this thought. Can be any type."""

    score: float = 0.0
    """
    How promising this thought is, from 0.0 (worthless) to 1.0 (perfect).

    Scores are assigned by evaluators and used by search algorithms to
    prioritize which thoughts to expand. A score of 0.5 is neutral.

    Interpretation:
        0.0 - 0.2: Poor, unlikely to lead to solution
        0.2 - 0.4: Below average, explore only if nothing better
        0.4 - 0.6: Neutral, worth considering
        0.6 - 0.8: Promising, prioritize exploration
        0.8 - 1.0: Excellent, likely on the path to solution
    """

    id: str = field(default_factory=lambda: str(uuid4()))
    """
    Unique identifier for this thought.

    Auto-generated as UUID if not provided. Can be set explicitly for:
    - Testing (deterministic IDs make assertions easier)
    - Debugging (meaningful IDs aid comprehension)
    - Integration (match external system IDs)
    """

    def __hash__(self) -> int:
        """Thoughts are hashable by ID, allowing use in sets and as dict keys."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Two thoughts are equal if they have the same ID."""
        if not isinstance(other, Thought):
            return NotImplemented
        return self.id == other.id

    def __repr__(self) -> str:
        """Concise representation for debugging."""
        content_preview = str(self.content)[:50]
        if len(str(self.content)) > 50:
            content_preview += "..."
        return f"Thought(id={self.id!r}, score={self.score:.2f}, content={content_preview!r})"
