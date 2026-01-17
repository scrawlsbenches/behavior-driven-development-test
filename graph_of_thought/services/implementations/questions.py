"""
Question Service Implementations.

Provides InMemoryQuestionService (testable) and SimpleQuestionService (basic).
"""

from __future__ import annotations
from datetime import datetime
from typing import Any
import uuid

from ..protocols import (
    KnowledgeService,
    Priority,
    QuestionTicket,
)


class InMemoryQuestionService:
    """
    Testable in-memory question service with full state tracking.

    Use when: You need a testable QuestionService that tracks all state
    for assertions in BDD tests.

    Unlike SimpleQuestionService (which focuses on production use),
    this implementation:
    - Stores all tickets, answers, and routing decisions
    - Provides query methods for test assertions
    - Supports configurable keyword routing
    - Supports basic auto-answer with knowledge base integration
    - Can be cleared/reset between tests

    Example:
        # Create with custom routing rules
        service = InMemoryQuestionService(
            routing_rules={
                "database-team": ["database", "sql", "postgres", "migration"],
                "frontend-team": ["react", "css", "ui", "component"],
            }
        )

        # Or with knowledge base for auto-answer
        knowledge = InMemoryKnowledgeService()
        service = InMemoryQuestionService(knowledge_service=knowledge)
    """

    # Default routing rules mapping route -> keywords
    DEFAULT_ROUTING_RULES: dict[str, list[str]] = {
        "security-team": ["security", "auth", "permission", "credential", "encryption"],
        "product-owner": ["requirement", "should we", "business", "stakeholder", "feature"],
        "devops": ["deploy", "infrastructure", "scaling", "kubernetes", "docker", "ci/cd"],
        "architect": ["design", "architecture", "pattern", "refactor", "structure"],
        "qa-team": ["test", "testing", "qa", "quality", "coverage", "bug"],
    }

    def __init__(
        self,
        routing_rules: dict[str, list[str]] | None = None,
        knowledge_service: KnowledgeService | None = None,
        auto_answer_threshold: float = 0.7,
    ):
        """
        Initialize the question service.

        Args:
            routing_rules: Custom routing rules mapping route name to keywords.
                          If None, uses DEFAULT_ROUTING_RULES.
            knowledge_service: Optional knowledge service for auto-answer capability.
            auto_answer_threshold: Confidence threshold for auto-answering (0-1).
                                  Higher values require more keyword matches.
        """
        self._tickets: dict[str, QuestionTicket] = {}
        self._routing_history: list[dict[str, Any]] = []
        self._routing_rules = routing_rules if routing_rules is not None else self.DEFAULT_ROUTING_RULES.copy()
        self._knowledge_service = knowledge_service
        self._auto_answer_threshold = auto_answer_threshold
        self._auto_answer_history: list[dict[str, Any]] = []

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
        ticket = QuestionTicket(
            id=f"q-{uuid.uuid4().hex[:8]}",
            question=question,
            context=context,
            priority=priority,
            asker=asker,
            status="open",
        )

        # Route the question
        routed_to = self._determine_route(ticket)
        ticket.routed_to = routed_to
        ticket.routing_reason = self._get_routing_reason(ticket, routed_to)

        # Record routing decision
        self._routing_history.append({
            "ticket_id": ticket.id,
            "question": question,
            "routed_to": routed_to,
            "routing_reason": ticket.routing_reason,
            "priority": priority.name,
            "timestamp": datetime.now().isoformat(),
        })

        self._tickets[ticket.id] = ticket
        return ticket

    def answer(
        self,
        ticket_id: str,
        answer: str,
        answered_by: str = "human",
    ) -> QuestionTicket:
        """Record an answer to a question."""
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
        """Get pending questions, optionally filtered."""
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
        """
        Get questions batched by priority for efficient review.
        """
        batched = {p: [] for p in Priority}

        for ticket in self._tickets.values():
            if ticket.status == "open":
                batched[ticket.priority].append(ticket)

        return batched

    def try_auto_answer(self, ticket_id: str) -> bool:
        """
        Attempt to answer from knowledge base.

        Uses keyword matching to find relevant knowledge entries and
        calculates a confidence score based on match quality.

        Returns True if auto-answered, False if needs human.

        The auto-answer is recorded in the ticket with answered_by="auto"
        and can be verified or overridden by a human.
        """
        if not self._knowledge_service:
            return False

        ticket = self._tickets.get(ticket_id)
        if not ticket:
            return False

        # Search knowledge base for relevant entries
        results = self._knowledge_service.retrieve(
            query=ticket.question,
            limit=3,
        )

        if not results:
            self._record_auto_answer_attempt(ticket_id, False, 0.0, "No matching entries")
            return False

        # Calculate confidence based on keyword overlap
        question_words = set(ticket.question.lower().split())
        best_score = 0.0
        best_entry = None

        for entry in results:
            entry_words = set(entry.content.lower().split())
            # Calculate Jaccard-like similarity
            intersection = len(question_words & entry_words)
            union = len(question_words | entry_words)
            score = intersection / union if union > 0 else 0.0

            if score > best_score:
                best_score = score
                best_entry = entry

        if best_score >= self._auto_answer_threshold and best_entry:
            # Auto-answer with the best matching entry
            ticket.answer = f"[Auto-answered from knowledge base]\n\n{best_entry.content}"
            ticket.answered_by = "auto"
            ticket.answered_at = datetime.now()
            ticket.status = "auto_answered"  # Distinct status for verification
            ticket.validation_notes = f"Confidence: {best_score:.2%}, Source: {best_entry.id}"

            self._record_auto_answer_attempt(
                ticket_id, True, best_score,
                f"Matched entry {best_entry.id}"
            )
            return True

        self._record_auto_answer_attempt(
            ticket_id, False, best_score,
            f"Confidence {best_score:.2%} below threshold {self._auto_answer_threshold:.2%}"
        )
        return False

    def _record_auto_answer_attempt(
        self,
        ticket_id: str,
        success: bool,
        confidence: float,
        reason: str,
    ) -> None:
        """Record an auto-answer attempt for debugging and improvement."""
        self._auto_answer_history.append({
            "ticket_id": ticket_id,
            "success": success,
            "confidence": confidence,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })

    def route(self, ticket_id: str) -> str:
        """
        Determine who should answer a question.

        Returns the routed_to value.
        """
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            return "human"

        return self._determine_route(ticket)

    def _determine_route(self, ticket: QuestionTicket) -> str:
        """
        Internal routing logic using configurable keyword matching.

        Routes based on question content keywords using the configured
        routing rules.

        Returns:
            The route name (e.g., "security-team") or "human" as default
        """
        question_lower = ticket.question.lower()

        # Check each route's keywords
        for route, keywords in self._routing_rules.items():
            if any(kw.lower() in question_lower for kw in keywords):
                return route

        return "human"  # Default to the user

    def _get_routing_reason(self, ticket: QuestionTicket, routed_to: str) -> str:
        """Generate a routing reason based on the routing decision."""
        if routed_to == "human":
            return "Default routing to human (no keyword matches)"

        # Find matching keywords for explanation
        question_lower = ticket.question.lower()
        keywords = self._routing_rules.get(routed_to, [])
        matched = [kw for kw in keywords if kw.lower() in question_lower]

        if matched:
            return f"Matched keywords for {routed_to}: {', '.join(matched)}"
        else:
            return f"Routed to {routed_to}"

    # =========================================================================
    # Query methods for test assertions
    # =========================================================================

    def get_all_tickets(self) -> list[QuestionTicket]:
        """
        Get all tickets in the system.

        Returns:
            List of all QuestionTicket instances, regardless of status.
        """
        return list(self._tickets.values())

    def get_ticket_by_id(self, ticket_id: str) -> QuestionTicket | None:
        """
        Get a specific ticket by its ID.

        Args:
            ticket_id: The ticket ID to look up.

        Returns:
            The QuestionTicket if found, None otherwise.
        """
        return self._tickets.get(ticket_id)

    def get_tickets_by_status(self, status: str) -> list[QuestionTicket]:
        """
        Get all tickets with a specific status.

        Args:
            status: The status to filter by (e.g., "open", "answered", "validated", "closed").

        Returns:
            List of QuestionTicket instances with the specified status.
        """
        return [t for t in self._tickets.values() if t.status == status]

    def get_routing_history(self) -> list[dict[str, Any]]:
        """
        Get the history of all routing decisions made.

        Returns:
            List of routing decision records, each containing:
            - ticket_id: ID of the ticket
            - question: The question text
            - routed_to: Who the question was routed to
            - routing_reason: Why it was routed there
            - priority: Priority level name
            - timestamp: When the routing decision was made
        """
        return list(self._routing_history)

    def get_tickets_by_route(self, routed_to: str) -> list[QuestionTicket]:
        """
        Get all tickets routed to a specific destination.

        Args:
            routed_to: The route to filter by (e.g., "security-team", "human")

        Returns:
            List of tickets routed to the specified destination
        """
        return [t for t in self._tickets.values() if t.routed_to == routed_to]

    def get_tickets_by_priority(self, priority: Priority) -> list[QuestionTicket]:
        """
        Get all tickets with a specific priority.

        Args:
            priority: The Priority enum value to filter by

        Returns:
            List of tickets with the specified priority
        """
        return [t for t in self._tickets.values() if t.priority == priority]

    def get_auto_answer_history(self) -> list[dict[str, Any]]:
        """
        Get the history of auto-answer attempts.

        Returns:
            List of auto-answer attempt records, each containing:
            - ticket_id: ID of the ticket
            - success: Whether auto-answer was successful
            - confidence: Confidence score (0-1)
            - reason: Explanation of the outcome
            - timestamp: When the attempt was made
        """
        return list(self._auto_answer_history)

    def get_answered_tickets(self) -> list[QuestionTicket]:
        """
        Get all tickets that have been answered.

        Returns:
            List of tickets with status "answered" or "auto_answered"
        """
        return [t for t in self._tickets.values() if t.status in ("answered", "auto_answered")]

    def get_auto_answered_tickets(self) -> list[QuestionTicket]:
        """
        Get all tickets that were auto-answered.

        Returns:
            List of tickets with status "auto_answered"
        """
        return [t for t in self._tickets.values() if t.status == "auto_answered"]

    def set_routing_rules(self, rules: dict[str, list[str]]) -> None:
        """
        Update the routing rules.

        Args:
            rules: New routing rules mapping route name to keywords
        """
        self._routing_rules = rules.copy()

    def add_routing_rule(self, route: str, keywords: list[str]) -> None:
        """
        Add or update a single routing rule.

        Args:
            route: The route name (e.g., "database-team")
            keywords: List of keywords that should route to this destination
        """
        self._routing_rules[route] = keywords.copy()

    def get_routing_rules(self) -> dict[str, list[str]]:
        """
        Get the current routing rules.

        Returns:
            Copy of the current routing rules dictionary
        """
        return {k: v.copy() for k, v in self._routing_rules.items()}

    def set_knowledge_service(self, service: KnowledgeService | None) -> None:
        """
        Set or update the knowledge service for auto-answer capability.

        Args:
            service: KnowledgeService instance, or None to disable auto-answer
        """
        self._knowledge_service = service

    def set_auto_answer_threshold(self, threshold: float) -> None:
        """
        Set the confidence threshold for auto-answering.

        Args:
            threshold: Value between 0 and 1. Higher values require better matches.
        """
        self._auto_answer_threshold = max(0.0, min(1.0, threshold))

    @property
    def ticket_count(self) -> int:
        """Get the total number of tickets."""
        return len(self._tickets)

    @property
    def pending_count(self) -> int:
        """Get the number of open tickets."""
        return len([t for t in self._tickets.values() if t.status == "open"])

    @property
    def answered_count(self) -> int:
        """Get the number of answered tickets (including auto-answered)."""
        return len([t for t in self._tickets.values() if t.status in ("answered", "auto_answered")])

    def clear(self) -> None:
        """
        Reset all state.

        Clears all tickets, routing history, and auto-answer history.
        Preserves routing rules and configuration. Useful for resetting
        state between tests.
        """
        self._tickets.clear()
        self._routing_history.clear()
        self._auto_answer_history.clear()


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
        2. Look up domain -> expert mapping
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
