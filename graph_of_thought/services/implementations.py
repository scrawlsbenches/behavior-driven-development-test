"""
Service Implementations - Null and simple implementations for all services.

These provide working defaults that can be replaced with production implementations.

ARCHITECTURE NOTE:
    Null implementations allow the system to function without any external dependencies.
    Simple implementations use in-memory storage and basic logic.
    Production implementations would connect to real systems (databases, APIs, etc.)
    
    Upgrade path:
    1. Start with Null (system works, no features)
    2. Move to Simple (features work, in-memory only)
    3. Move to Production (persistent, integrated)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid
import json
import os
from pathlib import Path

from .protocols import (
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


# =============================================================================
# Null Implementations (Pass-through, no-op)
# =============================================================================

class NullGovernanceService:
    """
    Governance that approves everything.
    
    Use when: You don't need approval workflows yet.
    Upgrade to: SimpleGovernanceService when you want basic policy checks,
                or a real implementation when you need external approvals.
    """
    
    def check_approval(
        self,
        action: str,
        context: dict[str, Any],
    ) -> tuple[ApprovalStatus, str]:
        return ApprovalStatus.APPROVED, "No governance configured - auto-approved"
    
    def request_approval(
        self,
        action: str,
        context: dict[str, Any],
        justification: str,
    ) -> str:
        return f"null-approval-{uuid.uuid4().hex[:8]}"
    
    def get_policies(self, scope: str) -> list[dict[str, Any]]:
        return []
    
    def record_audit(
        self,
        action: str,
        context: dict[str, Any],
        result: str,
        actor: str,
    ) -> None:
        pass  # No-op


class NullProjectManagementService:
    """
    Project management that returns empty results.
    
    Use when: Using only single-project CollaborativeProject directly.
    Upgrade to: SimpleProjectManagementService for cross-project views.
    """
    
    def get_active_projects(self) -> list[dict[str, Any]]:
        return []
    
    def get_blocked_items(self, project_id: str | None = None) -> list[dict[str, Any]]:
        return []
    
    def get_ready_items(self, project_id: str | None = None) -> list[dict[str, Any]]:
        return []
    
    def get_next_action(self, available_time_hours: float = 2.0) -> dict[str, Any] | None:
        return None
    
    def update_estimate(
        self,
        item_id: str,
        actual_hours: float,
        notes: str = "",
    ) -> None:
        pass
    
    def get_timeline(self, project_id: str) -> dict[str, Any]:
        return {}


class NullResourceService:
    """
    Resource service that never limits.
    
    Use when: You don't need budget tracking yet.
    Upgrade to: SimpleResourceService when you want to track consumption.
    
    WARNING: Without resource limits, runaway processes can be expensive.
    At minimum, implement token tracking for LLM calls.
    """
    
    def get_budget(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
    ) -> ResourceBudget | None:
        return None  # No budget = unlimited
    
    def allocate(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
    ) -> bool:
        return True  # Always succeeds
    
    def consume(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
        description: str = "",
    ) -> bool:
        return True  # Always succeeds
    
    def check_available(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
    ) -> tuple[bool, float]:
        return True, float('inf')  # Infinite resources
    
    def get_consumption_report(
        self,
        scope_type: str,
        scope_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        return {"message": "No resource tracking configured"}


class NullKnowledgeService:
    """
    Knowledge service that stores nothing and finds nothing.
    
    Use when: Just getting started, no knowledge base yet.
    Upgrade to: SimpleKnowledgeService for in-memory keyword search,
                then to a vector DB implementation for semantic search.
    
    COST OF NOT UPGRADING: You'll repeatedly solve the same problems
    and make contradictory decisions because nothing is remembered.
    """
    
    def store(self, entry: KnowledgeEntry) -> str:
        return f"null-{uuid.uuid4().hex[:8]}"  # Pretend to store
    
    def retrieve(
        self,
        query: str,
        entry_types: list[str] | None = None,
        project_filter: str | None = None,
        limit: int = 5,
    ) -> list[KnowledgeEntry]:
        return []  # Never finds anything
    
    def record_decision(self, decision: Decision) -> str:
        return f"null-decision-{uuid.uuid4().hex[:8]}"
    
    def find_contradictions(
        self,
        proposed_decision: str,
        project_id: str | None = None,
    ) -> list[Decision]:
        return []
    
    def get_patterns_for_problem(self, problem_description: str) -> list[KnowledgeEntry]:
        return []


class NullQuestionService:
    """
    Question service that doesn't route or track.
    
    Use when: Questions are handled manually in conversation.
    Upgrade to: SimpleQuestionService for tracking and batching.
    """
    
    def ask(
        self,
        question: str,
        context: str = "",
        priority: Priority = Priority.MEDIUM,
        asker: str = "ai",
    ) -> QuestionTicket:
        return QuestionTicket(
            id=f"null-q-{uuid.uuid4().hex[:8]}",
            question=question,
            context=context,
            priority=priority,
            asker=asker,
            status="open",
            routed_to="human",
            routing_reason="No routing configured",
        )
    
    def answer(
        self,
        ticket_id: str,
        answer: str,
        answered_by: str = "human",
    ) -> QuestionTicket:
        return QuestionTicket(
            id=ticket_id,
            question="(unknown - null service)",
            answer=answer,
            answered_by=answered_by,
            status="answered",
        )
    
    def get_pending(
        self,
        for_user: str | None = None,
        priority_filter: Priority | None = None,
    ) -> list[QuestionTicket]:
        return []
    
    def get_batched(self) -> dict[Priority, list[QuestionTicket]]:
        return {p: [] for p in Priority}
    
    def try_auto_answer(self, ticket_id: str) -> bool:
        return False  # Never auto-answers
    
    def route(self, ticket_id: str) -> str:
        return "human"  # Always routes to human


class NullCommunicationService:
    """
    Communication service that creates minimal handoffs.
    
    Use when: You're managing context manually.
    Upgrade to: SimpleCommunicationService for automatic context gathering.
    """
    
    def create_handoff(
        self,
        handoff_type: str,
        project_id: str,
        chunk_id: str | None = None,
    ) -> HandoffPackage:
        return HandoffPackage(
            id=f"null-handoff-{uuid.uuid4().hex[:8]}",
            handoff_type=handoff_type,
            project_id=project_id,
            chunk_id=chunk_id or "",
        )
    
    def get_resumption_context(self, project_id: str) -> str:
        return f"# Project: {project_id}\n\nNo context available (null service)."
    
    def record_intent(
        self,
        project_id: str,
        chunk_id: str | None,
        intent: str,
        constraints: list[str],
    ) -> None:
        pass
    
    def record_feedback(
        self,
        target_type: str,
        target_id: str,
        feedback: str,
        rating: int | None = None,
    ) -> None:
        pass
    
    def compress_history(
        self,
        project_id: str,
        max_tokens: int = 4000,
    ) -> str:
        return ""


# =============================================================================
# Simple Implementations (In-memory, basic logic)
# =============================================================================

class SimpleGovernanceService:
    """
    Basic governance with configurable policies.
    
    Policies are defined as simple rules:
    - action_name: "approve" | "deny" | "review" | condition_func
    
    ESCAPE CLAUSE: This is rule-based, not workflow-based.
    Real governance needs:
    - Multi-step approval workflows
    - Role-based permissions
    - Time-based policies (freeze periods)
    - External system integration
    """
    
    def __init__(self):
        self._policies: dict[str, Any] = {
            # Default: approve everything except production deploys
            "deploy_production": ApprovalStatus.NEEDS_REVIEW,
            "delete_project": ApprovalStatus.NEEDS_REVIEW,
        }
        self._audit_log: list[dict[str, Any]] = []
        self._pending_approvals: dict[str, dict[str, Any]] = {}
    
    def add_policy(self, action: str, status: ApprovalStatus | Callable) -> None:
        """Add or update a policy."""
        self._policies[action] = status
    
    def check_approval(
        self,
        action: str,
        context: dict[str, Any],
    ) -> tuple[ApprovalStatus, str]:
        policy = self._policies.get(action)
        
        if policy is None:
            return ApprovalStatus.APPROVED, "No policy defined - default approve"
        
        if callable(policy):
            # ESCAPE CLAUSE: Callable policies not fully implemented
            # They should return (ApprovalStatus, reason)
            try:
                result = policy(context)
                if isinstance(result, tuple):
                    return result
                return ApprovalStatus.APPROVED if result else ApprovalStatus.DENIED, ""
            except Exception as e:
                return ApprovalStatus.NEEDS_REVIEW, f"Policy error: {e}"
        
        if isinstance(policy, ApprovalStatus):
            return policy, f"Policy for '{action}' requires {policy.name}"
        
        return ApprovalStatus.APPROVED, "Unknown policy type - default approve"
    
    def request_approval(
        self,
        action: str,
        context: dict[str, Any],
        justification: str,
    ) -> str:
        approval_id = f"approval-{uuid.uuid4().hex[:8]}"
        self._pending_approvals[approval_id] = {
            "action": action,
            "context": context,
            "justification": justification,
            "requested_at": datetime.now().isoformat(),
            "status": "pending",
        }
        return approval_id
    
    def approve(self, approval_id: str, approver: str) -> bool:
        """Approve a pending request (called by human)."""
        if approval_id not in self._pending_approvals:
            return False
        self._pending_approvals[approval_id]["status"] = "approved"
        self._pending_approvals[approval_id]["approved_by"] = approver
        self._pending_approvals[approval_id]["approved_at"] = datetime.now().isoformat()
        return True
    
    def deny(self, approval_id: str, denier: str, reason: str) -> bool:
        """Deny a pending request (called by human)."""
        if approval_id not in self._pending_approvals:
            return False
        self._pending_approvals[approval_id]["status"] = "denied"
        self._pending_approvals[approval_id]["denied_by"] = denier
        self._pending_approvals[approval_id]["denied_at"] = datetime.now().isoformat()
        self._pending_approvals[approval_id]["denial_reason"] = reason
        return True
    
    def get_policies(self, scope: str) -> list[dict[str, Any]]:
        return [{"action": k, "policy": str(v)} for k, v in self._policies.items()]
    
    def record_audit(
        self,
        action: str,
        context: dict[str, Any],
        result: str,
        actor: str,
    ) -> None:
        self._audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "context": context,
            "result": result,
            "actor": actor,
        })
    
    def get_audit_log(
        self,
        action_filter: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve audit log entries."""
        logs = self._audit_log
        if action_filter:
            logs = [l for l in logs if l["action"] == action_filter]
        return logs[-limit:]


class SimpleResourceService:
    """
    In-memory resource tracking.
    
    ESCAPE CLAUSE: Budgets reset on restart. For persistence:
    1. Store budgets in database
    2. Store consumption events for audit
    3. Implement alerts/notifications at thresholds
    """
    
    def __init__(self):
        # Key: (resource_type, scope_type, scope_id)
        self._budgets: dict[tuple, ResourceBudget] = {}
        self._consumption_log: list[dict[str, Any]] = []
    
    def set_budget(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
        unit: str = "",
    ) -> ResourceBudget:
        """Set budget for a scope. Creates or updates."""
        key = (resource_type, scope_type, scope_id)
        existing = self._budgets.get(key)
        
        budget = ResourceBudget(
            resource_type=resource_type,
            allocated=amount,
            consumed=existing.consumed if existing else 0.0,
            unit=unit,
        )
        self._budgets[key] = budget
        return budget
    
    def get_budget(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
    ) -> ResourceBudget | None:
        key = (resource_type, scope_type, scope_id)
        return self._budgets.get(key)
    
    def allocate(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
    ) -> bool:
        # ESCAPE CLAUSE: No parent budget checks
        # Real implementation should verify against org/portfolio limits too
        key = (resource_type, scope_type, scope_id)
        if key in self._budgets:
            self._budgets[key].allocated += amount
        else:
            self._budgets[key] = ResourceBudget(
                resource_type=resource_type,
                allocated=amount,
            )
        return True
    
    def consume(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
        description: str = "",
    ) -> bool:
        key = (resource_type, scope_type, scope_id)
        budget = self._budgets.get(key)
        
        if budget is None:
            # No budget = no limit, but track consumption
            self._budgets[key] = ResourceBudget(
                resource_type=resource_type,
                allocated=float('inf'),
                consumed=amount,
            )
        elif budget.consumed + amount > budget.allocated:
            # Would exceed budget
            # ESCAPE CLAUSE: Hard stop. Could implement soft limits.
            return False
        else:
            budget.consumed += amount
        
        # Log consumption
        self._consumption_log.append({
            "timestamp": datetime.now().isoformat(),
            "resource_type": resource_type.name,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "amount": amount,
            "description": description,
        })
        
        return True
    
    def check_available(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
    ) -> tuple[bool, float]:
        budget = self.get_budget(resource_type, scope_type, scope_id)
        if budget is None:
            return True, float('inf')
        remaining = budget.remaining
        return amount <= remaining, remaining
    
    def get_consumption_report(
        self,
        scope_type: str,
        scope_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        relevant = [
            log for log in self._consumption_log
            if log["scope_type"] == scope_type and log["scope_id"] == scope_id
        ]
        
        # ESCAPE CLAUSE: Date filtering not implemented
        # Would need to parse timestamps
        
        by_resource: dict[str, float] = {}
        for log in relevant:
            rt = log["resource_type"]
            by_resource[rt] = by_resource.get(rt, 0) + log["amount"]
        
        return {
            "scope_type": scope_type,
            "scope_id": scope_id,
            "total_events": len(relevant),
            "by_resource": by_resource,
        }


class SimpleKnowledgeService:
    """
    In-memory knowledge base with keyword search.
    
    ESCAPE CLAUSE: This uses simple keyword matching.
    For production, implement semantic search:
    1. Use an embedding model (OpenAI, local model)
    2. Store embeddings in vector DB (Pinecone, Weaviate, pgvector)
    3. Hybrid search: keywords for exact match, semantic for concepts
    """
    
    def __init__(self, persist_path: str | None = None):
        self._entries: dict[str, KnowledgeEntry] = {}
        self._decisions: dict[str, Decision] = {}
        self._persist_path = Path(persist_path) if persist_path else None
        
        if self._persist_path and self._persist_path.exists():
            self._load()
    
    def store(self, entry: KnowledgeEntry) -> str:
        if not entry.id:
            entry.id = f"ke-{uuid.uuid4().hex[:8]}"
        self._entries[entry.id] = entry
        self._maybe_persist()
        return entry.id
    
    def retrieve(
        self,
        query: str,
        entry_types: list[str] | None = None,
        project_filter: str | None = None,
        limit: int = 5,
    ) -> list[KnowledgeEntry]:
        """
        Keyword-based retrieval.
        
        ESCAPE CLAUSE: This is O(n) scan with keyword matching.
        Production should use:
        - Inverted index for keywords
        - Vector similarity for semantic
        - Caching for frequent queries
        """
        query_terms = query.lower().split()
        
        results: list[tuple[float, KnowledgeEntry]] = []
        
        for entry in self._entries.values():
            # Filter by type
            if entry_types and entry.entry_type not in entry_types:
                continue
            
            # Filter by project
            if project_filter and entry.source_project != project_filter:
                continue
            
            # Score by keyword overlap
            content_lower = entry.content.lower()
            tag_text = " ".join(entry.tags).lower()
            full_text = f"{content_lower} {tag_text}"
            
            score = sum(1 for term in query_terms if term in full_text)
            
            if score > 0:
                results.append((score, entry))
        
        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        
        return [entry for score, entry in results[:limit]]
    
    def record_decision(self, decision: Decision) -> str:
        if not decision.id:
            decision.id = f"dec-{uuid.uuid4().hex[:8]}"
        
        self._decisions[decision.id] = decision
        
        # Also store as knowledge entry for retrieval
        entry = KnowledgeEntry(
            id=f"ke-{decision.id}",
            content=f"Decision: {decision.title}\n\nContext: {decision.context}\n\n"
                   f"Chosen: {decision.chosen}\n\nRationale: {decision.rationale}",
            entry_type="decision",
            source_project=decision.project_id,
            source_chunk=decision.chunk_id,
            tags=[decision.title] + decision.options,
        )
        self.store(entry)
        
        self._maybe_persist()
        return decision.id
    
    def find_contradictions(
        self,
        proposed_decision: str,
        project_id: str | None = None,
    ) -> list[Decision]:
        """
        ESCAPE CLAUSE: Not implemented - returns empty.
        
        To implement:
        1. Extract key claims from proposed decision
        2. Search for decisions with similar topics
        3. Use LLM to check for logical contradictions
        4. Return contradicting decisions with explanation
        """
        return []
    
    def get_patterns_for_problem(self, problem_description: str) -> list[KnowledgeEntry]:
        return self.retrieve(
            query=problem_description,
            entry_types=["pattern"],
        )
    
    def _maybe_persist(self) -> None:
        if self._persist_path:
            self._persist_path.mkdir(parents=True, exist_ok=True)
            
            data = {
                "entries": {k: self._entry_to_dict(v) for k, v in self._entries.items()},
                "decisions": {k: self._decision_to_dict(v) for k, v in self._decisions.items()},
            }
            
            with open(self._persist_path / "knowledge.json", "w") as f:
                json.dump(data, f, indent=2, default=str)
    
    def _load(self) -> None:
        path = self._persist_path / "knowledge.json"
        if not path.exists():
            return
        
        with open(path) as f:
            data = json.load(f)
        
        # ESCAPE CLAUSE: Deserialization is fragile
        # Would need proper schema validation in production
        for k, v in data.get("entries", {}).items():
            self._entries[k] = KnowledgeEntry(
                id=v["id"],
                content=v["content"],
                entry_type=v["entry_type"],
                source_project=v.get("source_project", ""),
                source_chunk=v.get("source_chunk", ""),
                tags=v.get("tags", []),
            )
    
    def _entry_to_dict(self, entry: KnowledgeEntry) -> dict:
        return {
            "id": entry.id,
            "content": entry.content,
            "entry_type": entry.entry_type,
            "source_project": entry.source_project,
            "source_chunk": entry.source_chunk,
            "tags": entry.tags,
        }
    
    def _decision_to_dict(self, decision: Decision) -> dict:
        return {
            "id": decision.id,
            "title": decision.title,
            "context": decision.context,
            "options": decision.options,
            "chosen": decision.chosen,
            "rationale": decision.rationale,
            "consequences": decision.consequences,
            "project_id": decision.project_id,
            "chunk_id": decision.chunk_id,
        }


class SimpleQuestionService:
    """
    In-memory question tracking with basic routing.
    
    ESCAPE CLAUSE: Routing is naive (everything goes to "human").
    Production routing needs:
    - Domain expert mapping
    - Code ownership data
    - Availability/on-call info
    - Knowledge base for auto-answers
    """
    
    def __init__(self, knowledge_service: KnowledgeService | None = None):
        self._tickets: dict[str, QuestionTicket] = {}
        self._knowledge = knowledge_service
    
    def ask(
        self,
        question: str,
        context: str = "",
        priority: Priority = Priority.MEDIUM,
        asker: str = "ai",
    ) -> QuestionTicket:
        ticket = QuestionTicket(
            id=f"q-{uuid.uuid4().hex[:8]}",
            question=question,
            context=context,
            priority=priority,
            asker=asker,
            status="open",
        )
        
        # Try auto-answer first
        if self._knowledge:
            results = self._knowledge.retrieve(question, limit=1)
            if results:
                # ESCAPE CLAUSE: No confidence scoring
                # We found something, but don't auto-answer without confidence
                ticket.routing_reason = f"Possible answer in knowledge base: {results[0].id}"
        
        # Route the question
        ticket.routed_to = self.route(ticket.id, ticket)
        
        self._tickets[ticket.id] = ticket
        return ticket
    
    def answer(
        self,
        ticket_id: str,
        answer: str,
        answered_by: str = "human",
    ) -> QuestionTicket:
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            raise ValueError(f"Unknown ticket: {ticket_id}")
        
        ticket.answer = answer
        ticket.answered_by = answered_by
        ticket.answered_at = datetime.now()
        ticket.status = "answered"
        
        return ticket
    
    def get_pending(
        self,
        for_user: str | None = None,
        priority_filter: Priority | None = None,
    ) -> list[QuestionTicket]:
        pending = [t for t in self._tickets.values() if t.status == "open"]
        
        if for_user:
            pending = [t for t in pending if t.routed_to == for_user]
        
        if priority_filter:
            pending = [t for t in pending if t.priority == priority_filter]
        
        # Sort by priority (CRITICAL first)
        priority_order = {p: i for i, p in enumerate(Priority)}
        pending.sort(key=lambda t: priority_order.get(t.priority, 99))
        
        return pending
    
    def get_batched(self) -> dict[Priority, list[QuestionTicket]]:
        batched = {p: [] for p in Priority}
        
        for ticket in self._tickets.values():
            if ticket.status == "open":
                batched[ticket.priority].append(ticket)
        
        return batched
    
    def try_auto_answer(self, ticket_id: str) -> bool:
        """
        ESCAPE CLAUSE: Always returns False.
        
        To implement:
        1. Search knowledge base for similar questions
        2. Compute confidence score
        3. If high confidence (>0.9), auto-answer and flag for verification
        4. If medium confidence, suggest answer to human
        5. If low confidence, route to human
        """
        return False
    
    def route(self, ticket_id: str, ticket: QuestionTicket | None = None) -> str:
        """
        ESCAPE CLAUSE: Routes everything to "human".
        
        To implement:
        1. Parse question for domain keywords
        2. Look up domain → expert mapping
        3. Check expert availability
        4. Fall back to general queue if no match
        """
        if ticket is None:
            ticket = self._tickets.get(ticket_id)
        
        if not ticket:
            return "human"
        
        # Simple keyword routing (placeholder)
        question_lower = ticket.question.lower()
        
        if any(kw in question_lower for kw in ["security", "auth", "permission"]):
            return "security-team"
        elif any(kw in question_lower for kw in ["requirement", "should we", "business"]):
            return "product-owner"
        elif any(kw in question_lower for kw in ["deploy", "infrastructure", "scaling"]):
            return "devops"
        else:
            return "human"  # Default to the user


class SimpleCommunicationService:
    """
    Basic communication service for context handoffs.
    
    ESCAPE CLAUSE: Intent and feedback storage is in-memory only.
    Production needs:
    - Persistent storage
    - Integration with project system for context gathering
    - LLM-based history compression
    """
    
    def __init__(
        self,
        project_service: ProjectManagementService | None = None,
        knowledge_service: KnowledgeService | None = None,
        question_service: QuestionService | None = None,
    ):
        self._project_service = project_service
        self._knowledge_service = knowledge_service
        self._question_service = question_service
        
        self._intents: dict[str, dict[str, Any]] = {}  # project_id -> intent
        self._feedback: list[dict[str, Any]] = []
        self._handoffs: dict[str, HandoffPackage] = {}
    
    def create_handoff(
        self,
        handoff_type: str,
        project_id: str,
        chunk_id: str | None = None,
    ) -> HandoffPackage:
        handoff = HandoffPackage(
            id=f"handoff-{uuid.uuid4().hex[:8]}",
            handoff_type=handoff_type,
            project_id=project_id,
            chunk_id=chunk_id or "",
        )
        
        # Gather context from intent
        intent_data = self._intents.get(project_id, {})
        handoff.intent = intent_data.get("intent", "")
        handoff.constraints = intent_data.get("constraints", [])
        
        # Gather blocked items
        if self._project_service:
            blocked = self._project_service.get_blocked_items(project_id)
            handoff.blockers = [b.get("name", str(b)) for b in blocked]
        
        # Gather open questions
        if self._question_service:
            pending = self._question_service.get_pending()
            handoff.open_questions = [q.question for q in pending[:5]]
        
        # Gather recent decisions
        if self._knowledge_service:
            decisions = self._knowledge_service.retrieve(
                query=project_id,
                entry_types=["decision"],
                limit=5,
            )
            handoff.key_decisions = [d.content[:200] for d in decisions]
        
        self._handoffs[handoff.id] = handoff
        return handoff
    
    def get_resumption_context(self, project_id: str) -> str:
        """
        Generate resumption context.
        
        ESCAPE CLAUSE: This is a simplified version.
        Ideally would pull from CollaborativeProject.get_resumption_context()
        and augment with cross-service information.
        """
        lines = [
            f"# Resumption Context: {project_id}",
            f"Generated: {datetime.now().isoformat()}",
            "",
        ]
        
        # Intent
        intent_data = self._intents.get(project_id, {})
        if intent_data:
            lines.extend([
                "## Intent",
                intent_data.get("intent", "Not recorded"),
                "",
                "## Constraints",
            ])
            for c in intent_data.get("constraints", []):
                lines.append(f"- {c}")
            lines.append("")
        
        # Blocked items
        if self._project_service:
            blocked = self._project_service.get_blocked_items(project_id)
            if blocked:
                lines.extend(["## Blocked", ""])
                for b in blocked:
                    lines.append(f"- {b.get('name', str(b))}")
                lines.append("")
        
        # Open questions
        if self._question_service:
            pending = self._question_service.get_pending()
            if pending:
                lines.extend(["## Open Questions", ""])
                for q in pending[:5]:
                    lines.append(f"- [{q.priority.name}] {q.question}")
                lines.append("")
        
        return "\n".join(lines)
    
    def record_intent(
        self,
        project_id: str,
        chunk_id: str | None,
        intent: str,
        constraints: list[str],
    ) -> None:
        self._intents[project_id] = {
            "intent": intent,
            "constraints": constraints,
            "chunk_id": chunk_id,
            "recorded_at": datetime.now().isoformat(),
        }
    
    def record_feedback(
        self,
        target_type: str,
        target_id: str,
        feedback: str,
        rating: int | None = None,
    ) -> None:
        """
        ESCAPE CLAUSE: Feedback is stored but not used.
        
        To make feedback actionable:
        1. Aggregate feedback by type/target
        2. Surface patterns (e.g., "chunks often underestimated")
        3. Adjust behavior based on feedback (e.g., increase estimates)
        4. Flag repeated negative feedback for human review
        """
        self._feedback.append({
            "target_type": target_type,
            "target_id": target_id,
            "feedback": feedback,
            "rating": rating,
            "recorded_at": datetime.now().isoformat(),
        })
    
    def compress_history(
        self,
        project_id: str,
        max_tokens: int = 4000,
    ) -> str:
        """
        ESCAPE CLAUSE: Compression is truncation, not summarization.
        
        For real compression:
        1. Use LLM to summarize each phase
        2. Keep recent items in full, older items summarized
        3. Preserve key decisions verbatim
        4. Include links to full history
        """
        context = self.get_resumption_context(project_id)
        
        # Rough token estimate (4 chars per token)
        max_chars = max_tokens * 4
        
        if len(context) <= max_chars:
            return context
        
        # Truncate with notice
        truncated = context[:max_chars - 100]
        return truncated + "\n\n... (truncated, see full history for details)"
