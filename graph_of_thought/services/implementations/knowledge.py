"""
Knowledge Service Implementations.

Provides InMemoryKnowledgeService (testable) and SimpleKnowledgeService (basic with persistence).
"""

from __future__ import annotations
import json
import uuid
from pathlib import Path

from ..protocols import (
    Decision,
    KnowledgeEntry,
)


class InMemoryKnowledgeService:
    """
    In-memory knowledge service for testing and development.

    This implementation stores entries and supports retrieval.
    Unlike SimpleKnowledgeService, this has no persistence and includes test-friendly
    query methods for assertions.

    Use when: Writing tests that need to verify knowledge storage/retrieval behavior.

    Features:
    - Stores entries and decisions in memory
    - Basic keyword search (same as SimpleKnowledgeService)
    - Query methods for test assertions (get_all_entries, get_all_decisions, etc.)
    - clear() method to reset state between tests
    """

    def __init__(self, retrieval_enabled: bool = True):
        """
        Initialize the knowledge service.

        Args:
            retrieval_enabled: If False, retrieve() always returns empty list
                              (like old Null behavior). Default True.
        """
        self._entries: dict[str, KnowledgeEntry] = {}
        self._decisions: dict[str, Decision] = {}
        self._retrieval_enabled = retrieval_enabled

    # =========================================================================
    # KnowledgeService Protocol Implementation
    # =========================================================================

    def store(self, entry: KnowledgeEntry) -> str:
        """Store a knowledge entry. Returns entry ID."""
        if not entry.id:
            entry.id = f"ke-{uuid.uuid4().hex[:8]}"
        self._entries[entry.id] = entry
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

        Searches entry content and tags for query terms.
        Results are ranked by number of matching keywords.

        If retrieval_enabled is False, always returns empty list.
        """
        if not self._retrieval_enabled:
            return []

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
        """Record a decision and also store as knowledge entry for retrieval."""
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

        return decision.id

    def find_contradictions(
        self,
        proposed_decision: str,
        project_id: str | None = None,
    ) -> list[Decision]:
        """
        Find past decisions that might contradict a proposed decision.

        Uses keyword-based contradiction detection by looking for:
        1. Decisions with overlapping topic keywords
        2. Decisions with opposite sentiment indicators (e.g., "use X" vs "avoid X")

        Args:
            proposed_decision: The proposed decision text to check
            project_id: Optional filter to only check decisions from a specific project

        Returns:
            List of potentially contradicting decisions, ordered by relevance
        """
        if not proposed_decision:
            return []

        # Extract keywords from proposed decision
        proposed_lower = proposed_decision.lower()
        proposed_words = set(proposed_lower.split())

        # Contradiction indicators - pairs of opposite terms
        contradiction_pairs = [
            ("use", "avoid"),
            ("enable", "disable"),
            ("add", "remove"),
            ("include", "exclude"),
            ("allow", "deny"),
            ("approve", "reject"),
            ("start", "stop"),
            ("create", "delete"),
            ("sync", "async"),
            ("monolith", "microservice"),
        ]

        contradictions: list[tuple[float, Decision]] = []

        for decision in self._decisions.values():
            # Filter by project if specified
            if project_id and decision.project_id != project_id:
                continue

            decision_text = f"{decision.title} {decision.context} {decision.chosen} {decision.rationale}".lower()
            decision_words = set(decision_text.split())

            # Calculate topic overlap score
            common_words = proposed_words & decision_words
            # Filter out common stop words
            stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                         "being", "have", "has", "had", "do", "does", "did", "will",
                         "would", "could", "should", "may", "might", "must", "shall",
                         "to", "of", "in", "for", "on", "with", "at", "by", "from",
                         "as", "into", "through", "during", "before", "after", "above",
                         "below", "between", "under", "again", "further", "then", "once",
                         "and", "or", "but", "if", "because", "until", "while", "although",
                         "this", "that", "these", "those", "it", "its", "we", "they"}
            meaningful_common = common_words - stop_words

            if not meaningful_common:
                continue

            topic_score = len(meaningful_common)

            # Check for contradiction patterns
            contradiction_score = 0.0
            for word1, word2 in contradiction_pairs:
                # Check if proposed has word1 and decision has word2 (or vice versa)
                if (word1 in proposed_lower and word2 in decision_text) or \
                   (word2 in proposed_lower and word1 in decision_text):
                    contradiction_score += 2.0

            # Check for negation patterns
            negation_words = ["not", "no", "never", "without", "don't", "doesn't", "won't", "can't"]
            proposed_has_negation = any(neg in proposed_lower for neg in negation_words)
            decision_has_negation = any(neg in decision_text for neg in negation_words)

            # If one has negation and other doesn't, that's a potential contradiction
            if proposed_has_negation != decision_has_negation and topic_score > 0:
                contradiction_score += 1.0

            total_score = topic_score + contradiction_score

            if total_score >= 2.0:  # Minimum threshold for potential contradiction
                contradictions.append((total_score, decision))

        # Sort by score descending
        contradictions.sort(key=lambda x: x[0], reverse=True)

        return [decision for score, decision in contradictions]

    def get_patterns_for_problem(self, problem_description: str) -> list[KnowledgeEntry]:
        """Find patterns that might help with a problem."""
        return self.retrieve(
            query=problem_description,
            entry_types=["pattern"],
        )

    # =========================================================================
    # Test Assertion Methods
    # =========================================================================

    def get_all_entries(self) -> list[KnowledgeEntry]:
        """Get all stored knowledge entries. Useful for test assertions."""
        return list(self._entries.values())

    def get_all_decisions(self) -> list[Decision]:
        """Get all stored decisions. Useful for test assertions."""
        return list(self._decisions.values())

    def get_entry_by_id(self, entry_id: str) -> KnowledgeEntry | None:
        """Get a specific entry by ID. Returns None if not found."""
        return self._entries.get(entry_id)

    def get_entries_by_tag(self, tag: str) -> list[KnowledgeEntry]:
        """Get all entries that have a specific tag."""
        return [
            entry for entry in self._entries.values()
            if tag in entry.tags
        ]

    def get_entries_by_type(self, entry_type: str) -> list[KnowledgeEntry]:
        """
        Get all entries of a specific type.

        Args:
            entry_type: The type to filter by (e.g., "decision", "pattern", "discovery")

        Returns:
            List of entries matching the specified type
        """
        return [
            entry for entry in self._entries.values()
            if entry.entry_type == entry_type
        ]

    def get_entries_by_project(self, project_id: str) -> list[KnowledgeEntry]:
        """
        Get all entries from a specific project.

        Args:
            project_id: The project ID to filter by

        Returns:
            List of entries from the specified project
        """
        return [
            entry for entry in self._entries.values()
            if entry.source_project == project_id
        ]

    def get_decision_by_id(self, decision_id: str) -> Decision | None:
        """
        Get a specific decision by ID.

        Args:
            decision_id: The decision ID to look up

        Returns:
            The Decision if found, None otherwise
        """
        return self._decisions.get(decision_id)

    def get_decisions_by_project(self, project_id: str) -> list[Decision]:
        """
        Get all decisions for a specific project.

        Args:
            project_id: The project ID to filter by

        Returns:
            List of decisions from the specified project
        """
        return [
            decision for decision in self._decisions.values()
            if decision.project_id == project_id
        ]

    @property
    def entry_count(self) -> int:
        """Get the total number of stored entries."""
        return len(self._entries)

    @property
    def decision_count(self) -> int:
        """Get the total number of stored decisions."""
        return len(self._decisions)

    def clear(self) -> None:
        """Reset all state. Useful for test cleanup between test cases."""
        self._entries.clear()
        self._decisions.clear()


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
