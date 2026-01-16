"""
Service Protocols - Interfaces for all subsystems.

These define what each service must provide. Start with null implementations,
upgrade incrementally.

ARCHITECTURE NOTE:
    All services are optional. The orchestrator works with whatever is provided
    and gracefully degrades when services are missing. This allows incremental
    adoption - you can start with just the facade and add services as needed.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Protocol, runtime_checkable, Callable, TypeVar


# =============================================================================
# Common Types
# =============================================================================

class ApprovalStatus(Enum):
    """Result of a governance check."""
    APPROVED = auto()          # Proceed
    DENIED = auto()            # Cannot proceed
    NEEDS_REVIEW = auto()      # Human must review
    NEEDS_INFO = auto()        # More information required
    CONDITIONAL = auto()       # Approved with conditions


class Priority(Enum):
    """Priority levels for work items and questions."""
    CRITICAL = auto()    # Drop everything
    HIGH = auto()        # Do soon
    MEDIUM = auto()      # Normal queue
    LOW = auto()         # When time permits
    BACKLOG = auto()     # Eventually


class ResourceType(Enum):
    """Types of resources that can be tracked/budgeted."""
    TOKENS = auto()           # LLM API tokens
    HUMAN_ATTENTION = auto()  # Human focus time
    COMPUTE_TIME = auto()     # CI/CD, test environments
    CALENDAR_TIME = auto()    # Wall clock deadlines
    COST_DOLLARS = auto()     # Actual money spent


@dataclass
class ResourceBudget:
    """Budget for a specific resource type."""
    resource_type: ResourceType
    allocated: float
    consumed: float = 0.0
    unit: str = ""  # "tokens", "minutes", "dollars", etc.
    
    @property
    def remaining(self) -> float:
        return self.allocated - self.consumed
    
    @property
    def percent_used(self) -> float:
        if self.allocated == 0:
            return 0.0
        return (self.consumed / self.allocated) * 100
    
    def is_exhausted(self) -> bool:
        return self.consumed >= self.allocated


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
class QuestionTicket:
    """
    A question that needs answering.
    
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
class HandoffPackage:
    """
    Everything needed for a context handoff (AI→Human, Human→AI, AI→AI).
    
    ESCAPE CLAUSE: This is the minimum viable handoff. Real handoffs might need:
    - Diff summaries for code changes
    - Test result attachments
    - Screenshots for UI work
    - Dependency graphs for architecture
    Extend this class as those needs emerge.
    """
    id: str
    handoff_type: str  # "ai_to_human", "human_to_ai", "ai_to_ai", "human_to_human"
    created_at: datetime = field(default_factory=datetime.now)
    
    # Context
    project_id: str = ""
    chunk_id: str = ""
    intent: str = ""          # What we're trying to achieve
    constraints: list[str] = field(default_factory=list)
    
    # State
    current_state: str = ""   # Where we are now
    blockers: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    
    # For code review handoffs
    changes_summary: str = ""
    risks: list[str] = field(default_factory=list)
    test_status: str = ""
    
    # Questions that need answering
    open_questions: list[str] = field(default_factory=list)
    
    # Past context (compressed)
    key_decisions: list[str] = field(default_factory=list)
    relevant_discoveries: list[str] = field(default_factory=list)


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
