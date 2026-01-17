"""
Service Protocols - Interfaces for all subsystems.

These define what each service must provide. Start with null implementations,
upgrade incrementally.

ARCHITECTURE NOTE:
    All services are optional. The orchestrator works with whatever is provided
    and gracefully degrades when services are missing. This allows incremental
    adoption - you can start with just the facade and add services as needed.

NOTE: Domain models and enums are now imported from graph_of_thought.domain.
This module re-exports them for backwards compatibility.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

# Import domain models and enums from the domain layer
from graph_of_thought.domain.enums import (
    ApprovalStatus,
    Priority,
    ResourceType,
)
from graph_of_thought.domain.models import (
    ResourceBudget,
    Decision,
    KnowledgeEntry,
    QuestionTicket,
    HandoffPackage,
)

# Re-export for backwards compatibility
__all__ = [
    # Enums
    "ApprovalStatus",
    "Priority",
    "ResourceType",
    # Models
    "ResourceBudget",
    "Decision",
    "KnowledgeEntry",
    "QuestionTicket",
    "HandoffPackage",
    # Service Protocols
    "GovernanceService",
    "ProjectManagementService",
    "ResourceService",
    "KnowledgeService",
    "QuestionService",
    "CommunicationService",
    # Registry
    "ServiceRegistry",
]


# =============================================================================
# Service Protocols
# =============================================================================

@runtime_checkable
class GovernanceService(Protocol):
    """
    Enforces policies and manages approvals.

    INTEGRATION POINT: Connect to your org's approval systems (Jira, GitHub PRs,
    Slack workflows, etc.) by implementing this protocol.
    """

    def check_approval(
        self,
        action: str,
        context: dict[str, Any],
    ) -> tuple[ApprovalStatus, str]:
        """
        Check if an action is approved.

        Args:
            action: What's being attempted ("start_chunk", "complete_chunk",
                   "make_decision", "deploy", etc.)
            context: Relevant context (project_id, chunk_id, user, etc.)

        Returns:
            (status, reason) - Status and human-readable explanation
        """
        ...

    def request_approval(
        self,
        action: str,
        context: dict[str, Any],
        justification: str,
    ) -> str:
        """
        Request approval for an action that needs review.

        Returns:
            Approval request ID for tracking
        """
        ...

    def get_policies(self, scope: str) -> list[dict[str, Any]]:
        """
        Get active policies for a scope (project, org, etc.).

        ESCAPE CLAUSE: Policy format is undefined. This returns raw dicts.
        Define a Policy dataclass when patterns emerge.
        """
        ...

    def record_audit(
        self,
        action: str,
        context: dict[str, Any],
        result: str,
        actor: str,
    ) -> None:
        """Record an action for audit trail."""
        ...


@runtime_checkable
class ProjectManagementService(Protocol):
    """
    Manages work across projects.

    INTEGRATION POINT: Connect to Jira, Linear, GitHub Projects, etc.
    """

    def get_active_projects(self) -> list[dict[str, Any]]:
        """Get all active projects for this user/context."""
        ...

    def get_blocked_items(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """
        Get blocked items, optionally filtered by project.

        If project_id is None, returns blocked items across all projects.
        """
        ...

    def get_ready_items(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """Get items ready to work on."""
        ...

    def get_next_action(self, available_time_hours: float = 2.0) -> dict[str, Any] | None:
        """
        Suggest the highest-priority item that fits in available time.

        ESCAPE CLAUSE: Priority calculation is naive (just uses Priority enum).
        Real prioritization considers:
        - Deadlines
        - Dependencies (unblock others)
        - Context switching cost
        - Energy/focus level
        - Strategic importance
        """
        ...

    def update_estimate(
        self,
        item_id: str,
        actual_hours: float,
        notes: str = "",
    ) -> None:
        """Record actual time for estimation improvement."""
        ...

    def get_timeline(self, project_id: str) -> dict[str, Any]:
        """
        Get projected timeline for a project.

        ESCAPE CLAUSE: Timeline projection not implemented. Returns empty dict.
        Real implementation needs:
        - Dependency graph analysis
        - Historical velocity
        - Resource availability
        - Risk buffers
        """
        ...


@runtime_checkable
class ResourceService(Protocol):
    """
    Tracks and enforces resource budgets.

    INTEGRATION POINT: Connect to billing APIs, time tracking systems, etc.
    """

    def get_budget(
        self,
        resource_type: ResourceType,
        scope_type: str,  # "project", "chunk", "user", "org"
        scope_id: str,
    ) -> ResourceBudget | None:
        """Get budget for a resource in a scope."""
        ...

    def allocate(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
    ) -> bool:
        """Allocate budget. Returns False if exceeds limits."""
        ...

    def consume(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
        description: str = "",
    ) -> bool:
        """
        Record resource consumption. Returns False if would exceed budget.

        ESCAPE CLAUSE: Currently hard-stops at budget. Real implementation might:
        - Allow soft limits with warnings
        - Support budget extensions with approval
        - Have different behavior per resource type
        """
        ...

    def check_available(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
    ) -> tuple[bool, float]:
        """
        Check if amount is available. Returns (available, remaining).
        """
        ...

    def get_consumption_report(
        self,
        scope_type: str,
        scope_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get consumption breakdown for reporting."""
        ...


@runtime_checkable
class KnowledgeService(Protocol):
    """
    Stores and retrieves organizational knowledge.

    INTEGRATION POINT: Connect to vector DBs (Pinecone, Weaviate),
    document stores, wikis, etc.
    """

    def store(self, entry: KnowledgeEntry) -> str:
        """Store a knowledge entry. Returns entry ID."""
        ...

    def retrieve(
        self,
        query: str,
        entry_types: list[str] | None = None,
        project_filter: str | None = None,
        limit: int = 5,
    ) -> list[KnowledgeEntry]:
        """
        Retrieve relevant knowledge for a query.

        ESCAPE CLAUSE: Uses keyword matching, not semantic search.
        To upgrade:
        1. Generate embeddings for entries (store in entry.embedding)
        2. Generate embedding for query
        3. Use cosine similarity for ranking
        4. Consider hybrid search (keywords + semantic)
        """
        ...

    def record_decision(self, decision: Decision) -> str:
        """Record a decision (converts to KnowledgeEntry internally)."""
        ...

    def find_contradictions(
        self,
        proposed_decision: str,
        project_id: str | None = None,
    ) -> list[Decision]:
        """
        Find past decisions that might contradict a proposed decision.

        ESCAPE CLAUSE: Not implemented. Returns empty list.
        Needs semantic understanding of decisions to detect contradictions.
        """
        ...

    def get_patterns_for_problem(self, problem_description: str) -> list[KnowledgeEntry]:
        """Find patterns that might help with a problem."""
        ...


@runtime_checkable
class QuestionService(Protocol):
    """
    Routes and manages questions.

    INTEGRATION POINT: Connect to Slack, email, ticketing systems for routing.
    """

    def ask(
        self,
        question: str,
        context: str = "",
        priority: Priority = Priority.MEDIUM,
        asker: str = "ai",
    ) -> QuestionTicket:
        """
        Submit a question. Routes automatically and returns ticket.
        """
        ...

    def answer(
        self,
        ticket_id: str,
        answer: str,
        answered_by: str = "human",
    ) -> QuestionTicket:
        """Record an answer to a question."""
        ...

    def get_pending(
        self,
        for_user: str | None = None,
        priority_filter: Priority | None = None,
    ) -> list[QuestionTicket]:
        """Get pending questions, optionally filtered."""
        ...

    def get_batched(self) -> dict[Priority, list[QuestionTicket]]:
        """
        Get questions batched by priority for efficient review.

        The idea: instead of interrupting for each question, batch them:
        - CRITICAL: Surface immediately
        - HIGH: Review twice daily
        - MEDIUM: Daily review
        - LOW/BACKLOG: Weekly review
        """
        ...

    def try_auto_answer(self, ticket_id: str) -> bool:
        """
        Attempt to answer from knowledge base.

        Returns True if auto-answered, False if needs human.

        ESCAPE CLAUSE: Auto-answer confidence scoring not implemented.
        Currently never auto-answers. When implemented:
        1. Search knowledge base
        2. If high-confidence match found, propose answer
        3. Either auto-accept or flag for human verification
        """
        ...

    def route(self, ticket_id: str) -> str:
        """
        Determine who should answer a question.

        ESCAPE CLAUSE: Routing logic is placeholder.
        Real routing considers:
        - Question topic → domain expert
        - Question about requirements → product owner
        - Question about code → code owner
        - Question already answered → knowledge base

        Returns the routed_to value.
        """
        ...


@runtime_checkable
class CommunicationService(Protocol):
    """
    Manages context handoffs and session communication.

    This is the glue that helps survive context loss and enable async work.
    """

    def create_handoff(
        self,
        handoff_type: str,
        project_id: str,
        chunk_id: str | None = None,
    ) -> HandoffPackage:
        """
        Create a handoff package for context transfer.

        Automatically gathers relevant context from other services.
        """
        ...

    def get_resumption_context(self, project_id: str) -> str:
        """
        Generate human/AI-readable context for resuming work.

        This is the key method for surviving context loss.
        """
        ...

    def record_intent(
        self,
        project_id: str,
        chunk_id: str | None,
        intent: str,
        constraints: list[str],
    ) -> None:
        """
        Record the intent for current work.

        Intent documents help verify that outputs match what was requested.
        """
        ...

    def record_feedback(
        self,
        target_type: str,  # "chunk", "answer", "suggestion"
        target_id: str,
        feedback: str,
        rating: int | None = None,  # 1-5 scale
    ) -> None:
        """
        Record feedback on AI outputs.

        ESCAPE CLAUSE: Feedback is stored but not used for learning.
        Future: use feedback to improve prompts, routing, estimates.
        """
        ...

    def compress_history(
        self,
        project_id: str,
        max_tokens: int = 4000,
    ) -> str:
        """
        Compress project history to fit in context window.

        ESCAPE CLAUSE: Compression is naive (truncation + summarization headers).
        Real compression might use:
        - LLM summarization of each phase
        - Importance-weighted selection
        - Hierarchical summarization
        """
        ...


# =============================================================================
# Service Registry
# =============================================================================

@dataclass
class ServiceRegistry:
    """
    Holds references to all services.

    Services are optional - if None, the orchestrator uses null behavior.
    """
    governance: GovernanceService | None = None
    project_management: ProjectManagementService | None = None
    resources: ResourceService | None = None
    knowledge: KnowledgeService | None = None
    questions: QuestionService | None = None
    communication: CommunicationService | None = None

    def has_service(self, name: str) -> bool:
        return getattr(self, name, None) is not None
