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
    def from_dict(cls, data: dict[str, Any]) -> Thought:
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
    A directed edge connecting two thoughts.
    """
    source_id: str
    target_id: str
    relation: str = "leads_to"
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize edge to dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "weight": self.weight,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Edge:
        """Deserialize edge from dictionary."""
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation=data.get("relation", "leads_to"),
            weight=data.get("weight", 1.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SearchResult(Generic[T]):
    """Result of a graph search operation."""
    best_path: list[Thought[T]]
    best_score: float
    thoughts_explored: int
    thoughts_expanded: int
    total_tokens_used: int
    wall_time_seconds: float
    termination_reason: str  # "goal_reached", "max_depth", "budget_exhausted", "timeout", "completed"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.termination_reason in ("goal_reached", "completed")


@dataclass
class SearchContext(Generic[T]):
    """Context passed to generators and evaluators during search."""
    current_thought: Thought[T]
    path_to_root: list[Thought[T]]
    depth: int
    tokens_remaining: int | None
    time_remaining_seconds: float | None
    metadata: dict[str, Any] = field(default_factory=dict)
