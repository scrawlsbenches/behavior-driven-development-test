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

    Based on Architecture Decision Records (ADR) pattern.
    """
    id: str
    title: str
    context: str = ""
    decision: str = ""
    rationale: str = ""
    alternatives: str = ""
    consequences: str = ""
    made_by: str = ""
    project: str = ""
    date: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    status: str = "accepted"  # proposed, accepted, deprecated, superseded
    supersedes: Optional[str] = None  # ID of decision this supersedes
    superseded_by: Optional[str] = None  # ID of decision that supersedes this

    def __post_init__(self):
        # Build searchable text from all fields
        self.searchable_text = " ".join([
            self.title, self.context, self.decision,
            self.rationale, self.alternatives, self.consequences
        ]).lower()


@dataclass
class KnowledgeEntry:
    """
    A piece of knowledge that can be queried.

    Can be a decision, learning, FAQ, or any documented knowledge.
    """
    id: str
    content: str
    entry_type: str = "general"  # decision, learning, faq, documentation
    source: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Question:
    """A question asked during work."""
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
    A tracked question that needs answering.

    Used by the QuestionService for routing and tracking.
    """
    id: str
    question: str
    asker: str = ""
    context: str = ""
    priority: Priority = Priority.MEDIUM
    assigned_to: Optional[str] = None
    answer: Optional[str] = None
    answered_by: Optional[str] = None
    answered_at: Optional[datetime] = None
    blocking_work: bool = False
    work_chunk_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RoutingRule:
    """Rule for routing questions to appropriate experts."""
    keyword_pattern: str
    route_to: str
    priority: str = "normal"
