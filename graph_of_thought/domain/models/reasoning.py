"""
Domain models for AI Reasoning capability.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Generic, TypeVar, Any
import uuid

from graph_of_thought.domain.enums import ThoughtStatus

T = TypeVar("T")


@dataclass
class Thought(Generic[T]):
    """
    A node in the Graph of Thought representing a single reasoning step.
    """
    content: T
    score: float = 0.0
    depth: int = 0
    status: ThoughtStatus = ThoughtStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    # Cost tracking
    tokens_used: int = 0
    generation_time_ms: float = 0.0

    def __lt__(self, other: Thought) -> bool:
        """For heap operations - higher scores have priority."""
        return self.score > other.score

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Thought):
            return False
        return self.id == other.id

    def to_dict(self) -> dict[str, Any]:
        """Serialize thought to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "depth": self.depth,
            "status": self.status.name,
            "metadata": self.metadata,
            "tokens_used": self.tokens_used,
            "generation_time_ms": self.generation_time_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Thought":
        """Deserialize thought from dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            score=data["score"],
            depth=data["depth"],
            status=ThoughtStatus[data["status"]],
            metadata=data.get("metadata", {}),
            tokens_used=data.get("tokens_used", 0),
            generation_time_ms=data.get("generation_time_ms", 0.0),
        )


@dataclass
class Edge:
    """
    A directed edge in the Graph of Thought.
    """
    source_id: str
    target_id: str
    weight: float = 1.0
    edge_type: str = "default"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash((self.source_id, self.target_id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Edge):
            return False
        return self.source_id == other.source_id and self.target_id == other.target_id


@dataclass
class SearchResult(Generic[T]):
    """Result from a search operation."""
    thoughts: list[Thought[T]]
    total_explored: int
    best_score: float
    search_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchContext(Generic[T]):
    """Context for search operations."""
    root_thought: Thought[T]
    max_depth: int = 5
    beam_width: int = 3
    constraints: dict[str, Any] = field(default_factory=dict)
