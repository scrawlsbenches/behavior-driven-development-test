"""
Domain models for Knowledge Management capability.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional

from graph_of_thought.domain.enums import QuestionPriority, QuestionStatus, Priority


@dataclass
class Decision:
    """
    A recorded decision with full context.

    ESCAPE CLAUSE: Real ADRs (Architecture Decision Records) have more structure.
    This is a simplified version that captures the essentials. Extend as needed.
    """
    id: str
    title: str
    context: str              # Why we faced this decision
    options: list[str]        # What we considered
    chosen: str               # What we picked
    rationale: str            # Why we picked it
    consequences: list[str]   # Expected impacts
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""      # Human or AI
    project_id: str = ""
    chunk_id: str = ""
    supersedes: str | None = None  # ID of decision this replaces

    # ESCAPE CLAUSE: Outcome tracking not implemented
    # These fields exist but nothing populates them yet
    outcome: str = ""         # What actually happened
    outcome_recorded_at: datetime | None = None


@dataclass
class KnowledgeEntry:
    """
    A piece of retrievable knowledge.

    ESCAPE CLAUSE: Real semantic search requires embeddings and a vector DB.
    This version uses simple keyword matching. The interface is correct but
    the implementation is naive.
    """
    id: str
    content: str
    entry_type: str  # "decision", "pattern", "discovery", "failure", "context"
    source_project: str = ""
    source_chunk: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    # ESCAPE CLAUSE: Embeddings not implemented
    # When you add a vector DB, populate this field
    embedding: list[float] | None = None

    # ESCAPE CLAUSE: Relevance scoring is placeholder
    relevance_score: float = 0.0


@dataclass
class Question:
    """A question asked during work (used by BDD step definitions)."""
    id: str
    question: str
    context: str = ""
    blocking: bool = False
    priority: QuestionPriority = QuestionPriority.NORMAL
    status: QuestionStatus = QuestionStatus.PENDING
    asked_by: str = ""
    project: str = ""
    routed_to: str = ""
    assigned_to: str = ""
    answer: str = ""
    answered_by: str = ""
    answered_at: Optional[datetime] = None
    next_steps: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class QuestionTicket:
    """
    A question that needs answering (used by QuestionService).

    Tracks the full lifecycle from asked to answered to validated.
    """
    id: str
    question: str
    context: str = ""
    asker: str = ""           # "ai" or user identifier
    priority: Priority = Priority.MEDIUM

    # Routing
    routed_to: str = ""       # Who should answer
    routing_reason: str = ""  # Why routed there

    # Status
    status: str = "open"      # open, answered, validated, closed
    asked_at: datetime = field(default_factory=datetime.now)
    answered_at: datetime | None = None

    # Answer
    answer: str = ""
    answered_by: str = ""

    # Validation
    validated: bool = False
    validation_notes: str = ""

    # Knowledge capture
    captured_as_knowledge: bool = False
    knowledge_entry_id: str = ""


@dataclass
class RoutingRule:
    """Rule for routing questions to appropriate experts."""
    keyword_pattern: str
    route_to: str
    priority: str = "normal"
