"""
Orchestrator - Coordinates all services and enforces workflow.

The orchestrator is the central hub that:
1. Receives events from the CollaborativeProject facade
2. Calls into relevant services (governance, resources, etc.)
3. Returns decisions that affect the workflow
4. Maintains cross-cutting concerns (audit, metrics)

ARCHITECTURE NOTE:
    The orchestrator doesn't replace the facade - it augments it.
    CollaborativeProject handles project-specific state.
    Orchestrator handles cross-project concerns and service coordination.
    
    You can use CollaborativeProject without an orchestrator (simple mode)
    or with one (full features).

ESCAPE CLAUSE: Event handling is synchronous.
    For production with slow services:
    1. Make service calls async
    2. Queue non-critical events for background processing
    3. Add timeouts and circuit breakers
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from enum import Enum, auto
import uuid

from .protocols import (
    ServiceRegistry,
    GovernanceService,
    ProjectManagementService,
    ResourceService,
    KnowledgeService,
    QuestionService,
    CommunicationService,
    ApprovalStatus,
    Priority,
    ResourceType,
    ResourceBudget,
    Decision,
    KnowledgeEntry,
    QuestionTicket,
    HandoffPackage,
)
from .implementations import (
    InMemoryGovernanceService,
    InMemoryProjectManagementService,
    InMemoryResourceService,
    InMemoryKnowledgeService,
    InMemoryQuestionService,
    InMemoryCommunicationService,
)


class OrchestratorEvent(Enum):
    """Events that the orchestrator handles."""
    # Project lifecycle
    PROJECT_CREATED = auto()
    PROJECT_LOADED = auto()
    
    # Request handling
    REQUEST_ADDED = auto()
    
    # Question handling
    QUESTION_ASKED = auto()
    QUESTION_ANSWERED = auto()
    
    # Chunk handling
    CHUNK_PLANNED = auto()
    CHUNK_STARTED = auto()
    CHUNK_COMPLETED = auto()
    CHUNK_BLOCKED = auto()
    CHUNK_UNBLOCKED = auto()
    
    # Artifacts
    ARTIFACT_PRODUCED = auto()
    DISCOVERY_RECORDED = auto()
    
    # Session
    SESSION_STARTED = auto()
    SESSION_ENDED = auto()
    CONTEXT_COMPACTING = auto()


@dataclass
class OrchestratorResponse:
    """
    Response from orchestrator after handling an event.
    
    The facade checks this response and may modify its behavior.
    """
    proceed: bool = True                    # Whether to continue with the action
    reason: str = ""                        # Human-readable explanation
    
    # Governance
    approval_status: ApprovalStatus = ApprovalStatus.APPROVED
    approval_id: str | None = None          # For async approvals
    
    # Resources
    resource_warning: bool = False          # True if resources getting low
    resource_exhausted: bool = False        # True if budget exceeded
    resource_status: dict[str, ResourceBudget] = field(default_factory=dict)
    
    # Knowledge
    related_decisions: list[Decision] = field(default_factory=list)
    suggested_patterns: list[KnowledgeEntry] = field(default_factory=list)
    potential_contradictions: list[Decision] = field(default_factory=list)
    
    # Questions
    auto_answered: bool = False
    auto_answer: str = ""
    routed_to: str = ""
    
    # Actions for the facade to take
    actions: list[dict[str, Any]] = field(default_factory=list)


class Orchestrator:
    """
    Central coordinator for all services.
    
    Usage:
        # Create with services
        orchestrator = Orchestrator(
            governance=SimpleGovernanceService(),
            resources=SimpleResourceService(),
            knowledge=SimpleKnowledgeService(),
        )
        
        # Or create with registry
        registry = ServiceRegistry(governance=..., resources=...)
        orchestrator = Orchestrator.from_registry(registry)
        
        # Handle events
        response = orchestrator.handle(
            OrchestratorEvent.CHUNK_STARTED,
            project_id="my_project",
            chunk_id="chunk_123",
            context={...}
        )
        
        if not response.proceed:
            print(f"Cannot proceed: {response.reason}")
    """
    
    def __init__(
        self,
        governance: GovernanceService | None = None,
        project_management: ProjectManagementService | None = None,
        resources: ResourceService | None = None,
        knowledge: KnowledgeService | None = None,
        questions: QuestionService | None = None,
        communication: CommunicationService | None = None,
    ):
        # Use in-memory implementations for missing services (testable defaults)
        self.governance = governance or InMemoryGovernanceService()
        self.project_management = project_management or InMemoryProjectManagementService()
        self.resources = resources or InMemoryResourceService()
        self.knowledge = knowledge or InMemoryKnowledgeService()
        self.questions = questions or InMemoryQuestionService()
        self.communication = communication or InMemoryCommunicationService()
        
        # Event handlers
        self._handlers: dict[OrchestratorEvent, list[Callable]] = {
            event: [] for event in OrchestratorEvent
        }
        self._register_default_handlers()
        
        # Metrics
        # ESCAPE CLAUSE: Metrics are basic counters. Use Prometheus/StatsD for production.
        self._metrics: dict[str, int] = {}
    
    @classmethod
    def from_registry(cls, registry: ServiceRegistry) -> Orchestrator:
        """Create orchestrator from a service registry."""
        return cls(
            governance=registry.governance,
            project_management=registry.project_management,
            resources=registry.resources,
            knowledge=registry.knowledge,
            questions=registry.questions,
            communication=registry.communication,
        )
    
    @classmethod
    def create_simple(cls, persist_path: str | None = None) -> Orchestrator:
        """
        Create orchestrator with simple (in-memory) implementations.
        
        Good for getting started. Upgrade individual services as needed.
        """
        from .implementations import (
            SimpleGovernanceService,
            SimpleResourceService,
            SimpleKnowledgeService,
            SimpleQuestionService,
            SimpleCommunicationService,
        )
        
        knowledge = SimpleKnowledgeService(persist_path=persist_path)
        questions = SimpleQuestionService(knowledge_service=knowledge)
        
        return cls(
            governance=SimpleGovernanceService(),
            project_management=InMemoryProjectManagementService(),  # Needs external data
            resources=SimpleResourceService(),
            knowledge=knowledge,
            questions=questions,
            communication=SimpleCommunicationService(
                knowledge_service=knowledge,
                question_service=questions,
            ),
        )
    
    def handle(
        self,
        event: OrchestratorEvent,
        project_id: str = "",
        chunk_id: str = "",
        **context: Any,
    ) -> OrchestratorResponse:
        """
        Handle an event from the facade.
        
        This is the main entry point. The facade calls this for major actions,
        and the orchestrator coordinates service calls and returns a response.
        """
        self._increment_metric(f"events.{event.name}")
        
        response = OrchestratorResponse()
        
        # Build full context
        full_context = {
            "project_id": project_id,
            "chunk_id": chunk_id,
            "event": event.name,
            "timestamp": datetime.now().isoformat(),
            **context,
        }
        
        # Run registered handlers for this event
        for handler in self._handlers.get(event, []):
            try:
                handler_response = handler(full_context, response)
                if handler_response is not None:
                    response = handler_response
                
                # Stop if a handler says don't proceed
                if not response.proceed:
                    break
                    
            except Exception as e:
                # ESCAPE CLAUSE: Error handling is basic.
                # Production should have better error reporting and recovery.
                self._increment_metric(f"errors.{event.name}")
                response.actions.append({
                    "type": "log_error",
                    "error": str(e),
                    "handler": handler.__name__,
                })
        
        # Audit trail
        self.governance.record_audit(
            action=event.name,
            context=full_context,
            result="proceed" if response.proceed else f"blocked: {response.reason}",
            actor=context.get("actor", "system"),
        )
        
        return response
    
    def register_handler(
        self,
        event: OrchestratorEvent,
        handler: Callable[[dict[str, Any], OrchestratorResponse], OrchestratorResponse | None],
    ) -> None:
        """Register a custom handler for an event."""
        self._handlers[event].append(handler)
    
    # =========================================================================
    # Default Event Handlers
    # =========================================================================
    
    def _register_default_handlers(self) -> None:
        """Register default handlers for all events."""
        
        # Governance checks
        self._handlers[OrchestratorEvent.CHUNK_STARTED].append(self._check_governance)
        self._handlers[OrchestratorEvent.CHUNK_COMPLETED].append(self._check_governance)
        
        # Resource checks
        self._handlers[OrchestratorEvent.CHUNK_STARTED].append(self._check_resources)
        self._handlers[OrchestratorEvent.CHUNK_COMPLETED].append(self._record_resource_consumption)
        
        # Knowledge capture
        self._handlers[OrchestratorEvent.QUESTION_ANSWERED].append(self._capture_answer_as_knowledge)
        self._handlers[OrchestratorEvent.DISCOVERY_RECORDED].append(self._capture_discovery_as_knowledge)
        self._handlers[OrchestratorEvent.CHUNK_COMPLETED].append(self._suggest_related_knowledge)
        
        # Question routing
        self._handlers[OrchestratorEvent.QUESTION_ASKED].append(self._route_question)
        
        # Communication
        self._handlers[OrchestratorEvent.CONTEXT_COMPACTING].append(self._prepare_for_compaction)
        self._handlers[OrchestratorEvent.SESSION_STARTED].append(self._provide_resumption_context)
    
    def _check_governance(
        self,
        context: dict[str, Any],
        response: OrchestratorResponse,
    ) -> OrchestratorResponse | None:
        """Check if action is approved by governance."""
        event = context.get("event", "")
        
        status, reason = self.governance.check_approval(event, context)
        response.approval_status = status
        
        if status == ApprovalStatus.DENIED:
            response.proceed = False
            response.reason = f"Governance denied: {reason}"
        elif status == ApprovalStatus.NEEDS_REVIEW:
            # Request approval and block
            approval_id = self.governance.request_approval(
                event,
                context,
                context.get("justification", "No justification provided"),
            )
            response.approval_id = approval_id
            response.proceed = False
            response.reason = f"Requires approval (ID: {approval_id}): {reason}"
        elif status == ApprovalStatus.NEEDS_INFO:
            response.proceed = False
            response.reason = f"More information needed: {reason}"
        
        return response
    
    def _check_resources(
        self,
        context: dict[str, Any],
        response: OrchestratorResponse,
    ) -> OrchestratorResponse | None:
        """Check resource availability before starting work."""
        project_id = context.get("project_id", "")
        chunk_id = context.get("chunk_id", "")
        
        # Check token budget
        available, remaining = self.resources.check_available(
            ResourceType.TOKENS,
            "project",
            project_id,
            0,  # Just checking, not reserving
        )
        
        if remaining < 1000:  # Low threshold
            response.resource_warning = True
            response.actions.append({
                "type": "warn",
                "message": f"Low token budget: {remaining} remaining",
            })
        
        # Get budget status for response
        token_budget = self.resources.get_budget(ResourceType.TOKENS, "project", project_id)
        if token_budget:
            response.resource_status["tokens"] = token_budget
        
        return response
    
    def _record_resource_consumption(
        self,
        context: dict[str, Any],
        response: OrchestratorResponse,
    ) -> OrchestratorResponse | None:
        """Record resource consumption when chunk completes."""
        project_id = context.get("project_id", "")
        chunk_id = context.get("chunk_id", "")
        tokens_used = context.get("tokens_used", 0)
        actual_hours = context.get("actual_hours", 0)
        
        if tokens_used > 0:
            self.resources.consume(
                ResourceType.TOKENS,
                "project",
                project_id,
                tokens_used,
                f"Chunk {chunk_id}",
            )
        
        if actual_hours > 0:
            self.resources.consume(
                ResourceType.HUMAN_ATTENTION,
                "project",
                project_id,
                actual_hours,
                f"Chunk {chunk_id}",
            )
        
        return response
    
    def _capture_answer_as_knowledge(
        self,
        context: dict[str, Any],
        response: OrchestratorResponse,
    ) -> OrchestratorResponse | None:
        """Capture question answers as knowledge entries."""
        question = context.get("question", "")
        answer = context.get("answer", "")
        project_id = context.get("project_id", "")
        
        if question and answer:
            entry = KnowledgeEntry(
                id=f"qa-{uuid.uuid4().hex[:8]}",
                content=f"Q: {question}\n\nA: {answer}",
                entry_type="qa",
                source_project=project_id,
                tags=question.split()[:5],  # First 5 words as tags
            )
            self.knowledge.store(entry)
        
        return response
    
    def _capture_discovery_as_knowledge(
        self,
        context: dict[str, Any],
        response: OrchestratorResponse,
    ) -> OrchestratorResponse | None:
        """Capture discoveries as knowledge entries."""
        discovery = context.get("discovery", "")
        project_id = context.get("project_id", "")
        chunk_id = context.get("chunk_id", "")
        
        if discovery:
            entry = KnowledgeEntry(
                id=f"disc-{uuid.uuid4().hex[:8]}",
                content=discovery,
                entry_type="discovery",
                source_project=project_id,
                source_chunk=chunk_id,
            )
            self.knowledge.store(entry)
        
        return response
    
    def _suggest_related_knowledge(
        self,
        context: dict[str, Any],
        response: OrchestratorResponse,
    ) -> OrchestratorResponse | None:
        """Suggest related knowledge when starting/completing chunks."""
        chunk_name = context.get("chunk_name", "")
        chunk_description = context.get("chunk_description", "")
        
        if chunk_name or chunk_description:
            query = f"{chunk_name} {chunk_description}"
            
            patterns = self.knowledge.get_patterns_for_problem(query)
            response.suggested_patterns = patterns[:3]
            
            decisions = self.knowledge.retrieve(
                query,
                entry_types=["decision"],
                limit=3,
            )
            # ESCAPE CLAUSE: Converting KnowledgeEntry back to Decision not implemented
            # Would need to store Decision objects separately or in entry metadata
        
        return response
    
    def _route_question(
        self,
        context: dict[str, Any],
        response: OrchestratorResponse,
    ) -> OrchestratorResponse | None:
        """Route questions appropriately."""
        question = context.get("question", "")
        priority = context.get("priority", Priority.MEDIUM)
        
        # Try to auto-answer from knowledge base
        results = self.knowledge.retrieve(question, limit=1)
        if results and len(results[0].content) > 50:
            # ESCAPE CLAUSE: No confidence scoring
            # We found something but don't trust it enough to auto-answer
            response.actions.append({
                "type": "suggest_answer",
                "suggestion": results[0].content,
                "source": results[0].id,
            })
        
        # Create ticket and route
        ticket = self.questions.ask(
            question=question,
            context=context.get("question_context", ""),
            priority=priority,
            asker=context.get("actor", "ai"),
        )
        
        response.routed_to = ticket.routed_to
        
        return response
    
    def _prepare_for_compaction(
        self,
        context: dict[str, Any],
        response: OrchestratorResponse,
    ) -> OrchestratorResponse | None:
        """
        Prepare for context window compaction.
        
        This is called when the context window is about to be compacted.
        We need to ensure critical information is persisted.
        """
        project_id = context.get("project_id", "")
        
        # Record current intent
        self.communication.record_intent(
            project_id=project_id,
            chunk_id=context.get("chunk_id"),
            intent=context.get("current_goal", ""),
            constraints=context.get("constraints", []),
        )
        
        # Create handoff package
        handoff = self.communication.create_handoff(
            handoff_type="ai_to_ai",
            project_id=project_id,
            chunk_id=context.get("chunk_id"),
        )
        
        # Add compressed history to response for inclusion in compacted context
        compressed = self.communication.compress_history(project_id)
        response.actions.append({
            "type": "include_in_compaction",
            "content": compressed,
            "handoff_id": handoff.id,
        })
        
        return response
    
    def _provide_resumption_context(
        self,
        context: dict[str, Any],
        response: OrchestratorResponse,
    ) -> OrchestratorResponse | None:
        """Provide context when session starts."""
        project_id = context.get("project_id", "")
        
        resumption = self.communication.get_resumption_context(project_id)
        
        response.actions.append({
            "type": "show_resumption_context",
            "content": resumption,
        })
        
        return response
    
    # =========================================================================
    # Convenience Methods
    # =========================================================================
    
    def ask_question(
        self,
        question: str,
        context: str = "",
        priority: Priority = Priority.MEDIUM,
        project_id: str = "",
    ) -> QuestionTicket:
        """Convenience method to ask a question through the orchestrator."""
        response = self.handle(
            OrchestratorEvent.QUESTION_ASKED,
            project_id=project_id,
            question=question,
            question_context=context,
            priority=priority,
        )
        
        return self.questions.ask(question, context, priority)
    
    def record_decision(
        self,
        title: str,
        context: str,
        options: list[str],
        chosen: str,
        rationale: str,
        project_id: str = "",
        chunk_id: str = "",
    ) -> str:
        """Convenience method to record a decision."""
        decision = Decision(
            id=f"dec-{uuid.uuid4().hex[:8]}",
            title=title,
            context=context,
            options=options,
            chosen=chosen,
            rationale=rationale,
            consequences=[],  # ESCAPE CLAUSE: Not capturing consequences
            project_id=project_id,
            chunk_id=chunk_id,
        )
        
        return self.knowledge.record_decision(decision)
    
    def set_token_budget(
        self,
        project_id: str,
        tokens: int,
    ) -> ResourceBudget:
        """Set token budget for a project."""
        from .implementations import SimpleResourceService
        
        if isinstance(self.resources, SimpleResourceService):
            return self.resources.set_budget(
                ResourceType.TOKENS,
                "project",
                project_id,
                tokens,
                "tokens",
            )
        else:
            # For other implementations, try to allocate
            self.resources.allocate(
                ResourceType.TOKENS,
                "project",
                project_id,
                tokens,
            )
            return ResourceBudget(ResourceType.TOKENS, tokens, 0, "tokens")
    
    def get_pending_questions(self) -> list[QuestionTicket]:
        """Get all pending questions."""
        return self.questions.get_pending()
    
    def get_cross_project_status(self) -> dict[str, Any]:
        """
        Get status across all projects.
        
        ESCAPE CLAUSE: Limited without real project management integration.
        """
        return {
            "active_projects": self.project_management.get_active_projects(),
            "all_blocked": self.project_management.get_blocked_items(),
            "all_ready": self.project_management.get_ready_items(),
            "pending_questions": len(self.questions.get_pending()),
            "pending_approvals": self._count_pending_approvals(),
        }
    
    def _count_pending_approvals(self) -> int:
        """Count pending governance approvals."""
        from .implementations import SimpleGovernanceService
        
        if isinstance(self.governance, SimpleGovernanceService):
            return len([
                a for a in self.governance._pending_approvals.values()
                if a.get("status") == "pending"
            ])
        return 0
    
    def _increment_metric(self, name: str) -> None:
        self._metrics[name] = self._metrics.get(name, 0) + 1
    
    def get_metrics(self) -> dict[str, int]:
        return dict(self._metrics)
