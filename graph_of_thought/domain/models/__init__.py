"""
Domain models organized by business capability.
"""

from graph_of_thought.domain.models.shared import User, ResourceBudget
from graph_of_thought.domain.models.reasoning import Thought, Edge, SearchResult, SearchContext
from graph_of_thought.domain.models.governance import ApprovalRequest, Policy
from graph_of_thought.domain.models.knowledge import (
    Decision,
    KnowledgeEntry,
    Question,
    QuestionTicket,
    RoutingRule,
)
from graph_of_thought.domain.models.project import (
    Project,
    WorkChunk,
    SessionHandoff,
    HandoffPackage,
)
from graph_of_thought.domain.models.cost import (
    Budget,
    ConsumptionRecord,
    AllocationRecord,
    BudgetWarning,
)

__all__ = [
    # Shared
    "User",
    "ResourceBudget",
    # Reasoning
    "Thought",
    "Edge",
    "SearchResult",
    "SearchContext",
    # Governance
    "ApprovalRequest",
    "Policy",
    # Knowledge
    "Decision",
    "KnowledgeEntry",
    "Question",
    "QuestionTicket",
    "RoutingRule",
    # Project
    "Project",
    "WorkChunk",
    "SessionHandoff",
    "HandoffPackage",
    # Cost
    "Budget",
    "ConsumptionRecord",
    "AllocationRecord",
    "BudgetWarning",
]
