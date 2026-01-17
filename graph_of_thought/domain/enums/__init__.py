"""
Domain enums organized by business capability.
"""

from graph_of_thought.domain.enums.shared import Priority, ResourceType
from graph_of_thought.domain.enums.reasoning import ThoughtStatus
from graph_of_thought.domain.enums.governance import ApprovalStatus, ApprovalType, RequestStatus
from graph_of_thought.domain.enums.knowledge import QuestionPriority, QuestionStatus
from graph_of_thought.domain.enums.project import ProjectStatus, ChunkStatus
from graph_of_thought.domain.enums.cost import BudgetLevel, BudgetStatus

__all__ = [
    # Shared
    "Priority",
    "ResourceType",
    # Reasoning
    "ThoughtStatus",
    # Governance
    "ApprovalStatus",
    "ApprovalType",
    "RequestStatus",
    # Knowledge
    "QuestionPriority",
    "QuestionStatus",
    # Project
    "ProjectStatus",
    "ChunkStatus",
    # Cost
    "BudgetLevel",
    "BudgetStatus",
]
