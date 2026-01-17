"""
Communication Service Implementations.

Provides InMemoryCommunicationService (testable) and SimpleCommunicationService (basic).
Also includes IntentRecord and FeedbackRecord dataclasses.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid

from ..protocols import (
    ProjectManagementService,
    KnowledgeService,
    QuestionService,
    HandoffPackage,
)


@dataclass
class IntentRecord:
    """A recorded intent for a project/chunk."""
    project_id: str
    chunk_id: str | None
    intent: str
    constraints: list[str]
    recorded_at: datetime = field(default_factory=datetime.now)


@dataclass
class FeedbackRecord:
    """A recorded feedback entry."""
    id: str
    target_type: str
    target_id: str
    feedback: str
    rating: int | None
    recorded_at: datetime = field(default_factory=datetime.now)


class InMemoryCommunicationService:
    """
    Testable in-memory communication service with query methods for assertions.

    Use when: You need a fully testable communication service that stores
    all data in memory and provides query methods for test assertions.

    This implementation:
    - Stores all handoff packages, intents, and feedback in memory
    - Provides query methods for retrieving stored data
    - Tracks resumption context per project
    - Supports clearing all state for test isolation

    Query methods for test assertions:
    - get_all_handoffs() -> list of all handoff packages
    - get_handoff_by_id(id) -> specific handoff or None
    - get_intents(project_id) -> list of intents for a project
    - get_feedback_history() -> list of all feedback records
    - clear() -> reset all state
    """

    def __init__(self) -> None:
        self._handoffs: dict[str, HandoffPackage] = {}
        self._intents: dict[str, list[IntentRecord]] = {}  # project_id -> list of intents
        self._feedback: list[FeedbackRecord] = []
        self._resumption_contexts: dict[str, str] = {}  # project_id -> context

    # =========================================================================
    # CommunicationService Protocol Implementation
    # =========================================================================

    def create_handoff(
        self,
        handoff_type: str,
        project_id: str,
        chunk_id: str | None = None,
    ) -> HandoffPackage:
        """
        Create a handoff package for context transfer.

        Stores the handoff in memory for later retrieval via get_handoff_by_id().
        """
        handoff = HandoffPackage(
            id=f"handoff-{uuid.uuid4().hex[:8]}",
            handoff_type=handoff_type,
            project_id=project_id,
            chunk_id=chunk_id or "",
        )

        # Populate from recorded intents if available
        project_intents = self._intents.get(project_id, [])
        if project_intents:
            latest_intent = project_intents[-1]
            handoff.intent = latest_intent.intent
            handoff.constraints = latest_intent.constraints.copy()

        self._handoffs[handoff.id] = handoff
        return handoff

    def get_resumption_context(self, project_id: str) -> str:
        """
        Generate human/AI-readable context for resuming work.

        Builds context from recorded intents and feedback.
        """
        lines = [
            f"# Resumption Context: {project_id}",
            f"Generated: {datetime.now().isoformat()}",
            "",
        ]

        # Include recorded intents
        project_intents = self._intents.get(project_id, [])
        if project_intents:
            latest_intent = project_intents[-1]
            lines.extend([
                "## Current Intent",
                latest_intent.intent,
                "",
            ])

            if latest_intent.constraints:
                lines.append("## Constraints")
                for constraint in latest_intent.constraints:
                    lines.append(f"- {constraint}")
                lines.append("")

            if len(project_intents) > 1:
                lines.append("## Intent History")
                for intent_record in project_intents[:-1]:
                    lines.append(f"- {intent_record.intent} (recorded: {intent_record.recorded_at.isoformat()})")
                lines.append("")

        # Include relevant feedback using exact project matching
        project_feedback = self._get_feedback_for_project(project_id)
        if project_feedback:
            lines.append("## Recent Feedback")
            for fb in project_feedback[-5:]:  # Last 5 feedback entries
                rating_str = f" (rating: {fb.rating})" if fb.rating is not None else ""
                lines.append(f"- [{fb.target_type}] {fb.feedback}{rating_str}")
            lines.append("")

        context = "\n".join(lines)
        self._resumption_contexts[project_id] = context
        return context

    def record_intent(
        self,
        project_id: str,
        chunk_id: str | None,
        intent: str,
        constraints: list[str],
    ) -> None:
        """
        Record the intent for current work.

        Stores intent in memory for retrieval via get_intents().
        """
        intent_record = IntentRecord(
            project_id=project_id,
            chunk_id=chunk_id,
            intent=intent,
            constraints=constraints.copy(),
        )

        if project_id not in self._intents:
            self._intents[project_id] = []
        self._intents[project_id].append(intent_record)

    def record_feedback(
        self,
        target_type: str,
        target_id: str,
        feedback: str,
        rating: int | None = None,
    ) -> None:
        """
        Record feedback on AI outputs.

        Stores feedback in memory for retrieval via get_feedback_history().
        """
        feedback_record = FeedbackRecord(
            id=f"feedback-{uuid.uuid4().hex[:8]}",
            target_type=target_type,
            target_id=target_id,
            feedback=feedback,
            rating=rating,
        )
        self._feedback.append(feedback_record)

    def compress_history(
        self,
        project_id: str,
        max_tokens: int = 4000,
        chars_per_token: float = 4.0,
    ) -> str:
        """
        Compress project history to fit in context window.

        Uses truncation with preservation of key sections.

        Args:
            project_id: The project to compress history for
            max_tokens: Maximum tokens to allow (default: 4000)
            chars_per_token: Character-to-token ratio for estimation (default: 4.0)
                           Use ~3.5 for code-heavy content, ~4.5 for prose

        Returns:
            Compressed context string that fits within token limit
        """
        context = self.get_resumption_context(project_id)

        # Calculate max characters based on configurable ratio
        max_chars = int(max_tokens * chars_per_token)

        if len(context) <= max_chars:
            return context

        # Try to preserve important sections by truncating middle content
        lines = context.split("\n")
        header_lines = []
        important_lines = []
        other_lines = []

        current_section = "header"
        for line in lines:
            if line.startswith("# ") or line.startswith("## "):
                if "Intent" in line or "Constraints" in line or "Blocked" in line:
                    current_section = "important"
                else:
                    current_section = "other"
                important_lines.append(line) if current_section == "important" else other_lines.append(line)
            elif current_section == "header" and line.strip():
                header_lines.append(line)
                if "Generated:" in line:
                    current_section = "other"
            elif current_section == "important":
                important_lines.append(line)
            else:
                other_lines.append(line)

        # Build compressed version
        result_lines = header_lines + [""] + important_lines

        # Add other content if space permits
        current_len = sum(len(line) + 1 for line in result_lines)
        for line in other_lines:
            if current_len + len(line) + 1 < max_chars - 100:
                result_lines.append(line)
                current_len += len(line) + 1
            else:
                break

        result = "\n".join(result_lines)

        if len(result) >= max_chars:
            # Still too long, do hard truncation
            result = result[:max_chars - 100]

        return result + "\n\n... (history compressed, see full context for details)"

    def _get_feedback_for_project(self, project_id: str) -> list[FeedbackRecord]:
        """
        Get feedback records for a project using proper matching.

        Matches feedback where:
        - target_id exactly equals project_id
        - target_id starts with "{project_id}/" (e.g., "proj1/chunk1")
        - target_id starts with "{project_id}:" (e.g., "proj1:task1")

        Args:
            project_id: The project ID to filter by

        Returns:
            List of matching feedback records
        """
        results = []
        for fb in self._feedback:
            target = fb.target_id
            if (target == project_id or
                target.startswith(f"{project_id}/") or
                target.startswith(f"{project_id}:")):
                results.append(fb)
        return results

    # =========================================================================
    # Query Methods for Test Assertions
    # =========================================================================

    def get_all_handoffs(self) -> list[HandoffPackage]:
        """
        Get all handoff packages.

        Returns:
            List of all handoff packages created, in no particular order.
        """
        return list(self._handoffs.values())

    def get_handoff_by_id(self, handoff_id: str) -> HandoffPackage | None:
        """
        Get a specific handoff package by ID.

        Args:
            handoff_id: The ID of the handoff to retrieve.

        Returns:
            The handoff package if found, None otherwise.
        """
        return self._handoffs.get(handoff_id)

    def get_intents(self, project_id: str) -> list[IntentRecord]:
        """
        Get all recorded intents for a project.

        Args:
            project_id: The project ID to get intents for.

        Returns:
            List of intent records for the project, in chronological order.
        """
        return self._intents.get(project_id, []).copy()

    def get_feedback_history(self) -> list[FeedbackRecord]:
        """
        Get all recorded feedback.

        Returns:
            List of all feedback records, in chronological order.
        """
        return self._feedback.copy()

    def get_feedback_for_project(self, project_id: str) -> list[FeedbackRecord]:
        """
        Get all feedback records for a specific project.

        This uses proper project matching (exact match or prefix with delimiter).

        Args:
            project_id: The project ID to filter by

        Returns:
            List of feedback records for the project
        """
        return self._get_feedback_for_project(project_id)

    def get_feedback_by_type(self, target_type: str) -> list[FeedbackRecord]:
        """
        Get all feedback records of a specific type.

        Args:
            target_type: The type to filter by (e.g., "chunk", "answer", "suggestion")

        Returns:
            List of feedback records matching the type
        """
        return [fb for fb in self._feedback if fb.target_type == target_type]

    def get_feedback_by_rating(
        self,
        min_rating: int | None = None,
        max_rating: int | None = None,
    ) -> list[FeedbackRecord]:
        """
        Get feedback records filtered by rating range.

        Args:
            min_rating: Minimum rating (inclusive), or None for no lower bound
            max_rating: Maximum rating (inclusive), or None for no upper bound

        Returns:
            List of feedback records with ratings in the specified range
        """
        results = []
        for fb in self._feedback:
            if fb.rating is None:
                continue
            if min_rating is not None and fb.rating < min_rating:
                continue
            if max_rating is not None and fb.rating > max_rating:
                continue
            results.append(fb)
        return results

    def get_latest_intent(self, project_id: str) -> IntentRecord | None:
        """
        Get the most recent intent for a project.

        Args:
            project_id: The project ID

        Returns:
            The latest IntentRecord if any exists, None otherwise
        """
        intents = self._intents.get(project_id, [])
        return intents[-1] if intents else None

    def get_handoffs_by_type(self, handoff_type: str) -> list[HandoffPackage]:
        """
        Get all handoffs of a specific type.

        Args:
            handoff_type: The type to filter by (e.g., "ai_to_human", "human_to_ai")

        Returns:
            List of handoff packages matching the type
        """
        return [h for h in self._handoffs.values() if h.handoff_type == handoff_type]

    def get_handoffs_for_project(self, project_id: str) -> list[HandoffPackage]:
        """
        Get all handoffs for a specific project.

        Args:
            project_id: The project ID to filter by

        Returns:
            List of handoff packages for the project
        """
        return [h for h in self._handoffs.values() if h.project_id == project_id]

    @property
    def handoff_count(self) -> int:
        """Get the total number of handoffs."""
        return len(self._handoffs)

    @property
    def feedback_count(self) -> int:
        """Get the total number of feedback records."""
        return len(self._feedback)

    @property
    def intent_count(self) -> int:
        """Get the total number of intent records across all projects."""
        return sum(len(intents) for intents in self._intents.values())

    def clear(self) -> None:
        """
        Reset all state.

        Clears all stored handoffs, intents, feedback, and resumption contexts.
        Useful for test isolation between test cases.
        """
        self._handoffs.clear()
        self._intents.clear()
        self._feedback.clear()
        self._resumption_contexts.clear()


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
