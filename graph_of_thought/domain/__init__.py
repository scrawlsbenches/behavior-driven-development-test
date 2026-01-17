"""
Domain layer for Graph of Thought.

This module contains all domain models and enums organized by business capability.
Import from here for a clean API:

    from graph_of_thought.domain import Decision, Question, WorkChunk
    from graph_of_thought.domain import ApprovalStatus, ChunkStatus, Priority
"""

from graph_of_thought.domain.enums import (
    # Shared
    Priority,
    ResourceType,
    # Reasoning
    ThoughtStatus,
    # Governance
    ApprovalStatus,
    ApprovalType,
    RequestStatus,
    # Knowledge
    QuestionPriority,
    QuestionStatus,
    # Project
    ProjectStatus,
    ChunkStatus,
    # Cost
    BudgetLevel,
    BudgetStatus,
)

from graph_of_thought.domain.models import (
    # Shared
    User,
    ResourceBudget,
    # Reasoning
    Thought,
    Edge,
    SearchResult,
    SearchContext,
    # Governance
    ApprovalRequest,
    Policy,
    # Knowledge
    Decision,
    KnowledgeEntry,
    Question,
    QuestionTicket,
    RoutingRule,
    # Project
    Project,
    WorkChunk,
    SessionHandoff,
    HandoffPackage,
    # Cost
    Budget,
    ConsumptionRecord,
    AllocationRecord,
    BudgetWarning,
)

__all__ = [
    # Enums - Shared
    "Priority",
    "ResourceType",
    # Enums - Reasoning
    "ThoughtStatus",
    # Enums - Governance
    "ApprovalStatus",
    "ApprovalType",
    "RequestStatus",
    # Enums - Knowledge
    "QuestionPriority",
    "QuestionStatus",
    # Enums - Project
    "ProjectStatus",
    "ChunkStatus",
    # Enums - Cost
    "BudgetLevel",
    "BudgetStatus",
    # Models - Shared
    "User",
    "ResourceBudget",
    # Models - Reasoning
    "Thought",
    "Edge",
    "SearchResult",
    "SearchContext",
    # Models - Governance
    "ApprovalRequest",
    "Policy",
    # Models - Knowledge
    "Decision",
    "KnowledgeEntry",
    "Question",
    "QuestionTicket",
    "RoutingRule",
    # Models - Project
    "Project",
    "WorkChunk",
    "SessionHandoff",
    "HandoffPackage",
    # Models - Cost
    "Budget",
    "ConsumptionRecord",
    "AllocationRecord",
    "BudgetWarning",
]
