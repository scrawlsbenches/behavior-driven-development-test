"""
Collaborative Project Graph - A facade over Graph of Thought for human-AI collaboration.

This layer transforms GoT from "AI explores solution space" to "human and AI 
navigate project complexity together."

Key concepts:
- Questions block progress until answered (forcing clarification upfront)
- Chunks are 2-4 hour work units with explicit scope
- Decisions are recorded and traceable
- Discoveries during implementation can affect other chunks
- Sessions can be resumed after context loss

The graph tracks the evolution of understanding, not just code artifacts.

ORCHESTRATOR INTEGRATION:
    The CollaborativeProject can optionally connect to an Orchestrator for:
    - Governance checks (approval workflows)
    - Resource tracking (token budgets, time)
    - Knowledge management (capturing decisions, patterns)
    - Question routing (auto-answers, expert routing)
    - Communication (handoffs, context compression)
    
    Without an orchestrator, the facade works standalone (simple mode).
    With an orchestrator, you get cross-project features and service integration.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, TYPE_CHECKING
from enum import Enum, auto
from datetime import datetime
import json
import os
from pathlib import Path

# Import the underlying Graph of Thought
from graph_of_thought import (
    GraphOfThought,
    Thought,
    ThoughtStatus,
    GraphConfig,
)

# Type checking import for orchestrator (avoid circular import)
if TYPE_CHECKING:
    from graph_of_thought.services import Orchestrator, OrchestratorResponse


class NodeType(Enum):
    """Types of nodes in the project graph."""
    REQUEST = auto()      # Original user request
    QUESTION = auto()     # Clarifying question (blocks until answered)
    DECISION = auto()     # Answer to a question or design choice
    CHUNK = auto()        # Work unit (2-4 hours)
    ARTIFACT = auto()     # Produced file or output
    DISCOVERY = auto()    # Something learned during implementation
    CHECKPOINT = auto()   # Session boundary marker


class ChunkStatus(Enum):
    """Status of a work chunk."""
    BLOCKED = auto()      # Waiting on questions/dependencies
    READY = auto()        # Can be started
    IN_PROGRESS = auto()  # Currently being worked
    REVIEW = auto()       # Done, awaiting approval
    COMPLETE = auto()     # Finished and approved
    DEFERRED = auto()     # Pushed to later


class QuestionPriority(Enum):
    """How critical is this question?"""
    BLOCKING = auto()     # Cannot proceed without answer
    IMPORTANT = auto()    # Should answer before implementation
    NICE_TO_HAVE = auto() # Can make reasonable default


@dataclass
class ProjectNode:
    """
    A node in the project graph.
    
    This wraps the underlying Thought with project-specific semantics.
    """
    id: str
    node_type: NodeType
    content: str
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Type-specific fields
    status: ChunkStatus | None = None  # For CHUNK nodes
    priority: QuestionPriority | None = None  # For QUESTION nodes
    estimated_hours: float | None = None  # For CHUNK nodes
    actual_hours: float | None = None  # For CHUNK nodes
    acceptance_criteria: list[str] = field(default_factory=list)  # For CHUNK nodes
    file_paths: list[str] = field(default_factory=list)  # For ARTIFACT nodes
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "node_type": self.node_type.name,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "status": self.status.name if self.status else None,
            "priority": self.priority.name if self.priority else None,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "acceptance_criteria": self.acceptance_criteria,
            "file_paths": self.file_paths,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectNode:
        return cls(
            id=data["id"],
            node_type=NodeType[data["node_type"]],
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
            status=ChunkStatus[data["status"]] if data.get("status") else None,
            priority=QuestionPriority[data["priority"]] if data.get("priority") else None,
            estimated_hours=data.get("estimated_hours"),
            actual_hours=data.get("actual_hours"),
            acceptance_criteria=data.get("acceptance_criteria", []),
            file_paths=data.get("file_paths", []),
        )


class RelationType(Enum):
    """Types of relationships between nodes."""
    SPAWNS = auto()       # Request spawns questions/chunks
    BLOCKS = auto()       # Question blocks chunk
    ANSWERS = auto()      # Decision answers question
    DEPENDS_ON = auto()   # Chunk depends on chunk
    PRODUCES = auto()     # Chunk produces artifact
    DISCOVERED_IN = auto() # Discovery found during chunk
    AFFECTS = auto()      # Discovery affects chunk
    CONTINUES = auto()    # Session continues from checkpoint


@dataclass
class SessionContext:
    """
    Context for the current working session.
    
    This is what gets written to disk to survive context loss.
    """
    project_name: str
    session_started: datetime
    current_chunk_id: str | None = None
    current_goal: str | None = None
    notes: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "session_started": self.session_started.isoformat(),
            "current_chunk_id": self.current_chunk_id,
            "current_goal": self.current_goal,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionContext:
        return cls(
            project_name=data["project_name"],
            session_started=datetime.fromisoformat(data["session_started"]),
            current_chunk_id=data.get("current_chunk_id"),
            current_goal=data.get("current_goal"),
            notes=data.get("notes", []),
        )


class CollaborativeProject:
    """
    A facade over Graph of Thought for human-AI collaboration on software projects.
    
    Key behaviors:
    - Questions must be answered before blocked chunks can start
    - The graph tracks project evolution, not just current state
    - Sessions can be resumed after context loss
    - Markdown export makes state human-readable
    
    Example:
        project = CollaborativeProject("my_cms")
        
        # Start with the request
        project.add_request("Build me a content management system")
        
        # AI should ask questions first
        project.ask_question(
            "Multi-tenant or single-tenant?",
            priority=QuestionPriority.BLOCKING,
            affects_chunks=["architecture"]
        )
        
        # Human answers
        project.answer_question(question_id, "Multi-tenant, each customer isolated")
        
        # Now we can plan chunks
        project.plan_chunk(
            name="Core data models",
            description="Define tenant, user, content models",
            estimated_hours=3,
            depends_on=[],
            acceptance_criteria=["Models defined", "Migrations created", "Tests pass"]
        )
    """
    
    def __init__(
        self,
        name: str,
        base_path: str | Path | None = None,
        auto_save: bool = True,
        orchestrator: Orchestrator | None = None,
    ):
        """
        Create or load a collaborative project.
        
        Args:
            name: Project identifier
            base_path: Directory for project files (default: ./projects/{name})
            auto_save: Whether to save after each modification
            orchestrator: Optional orchestrator for service integration
            
        INTEGRATION NOTE:
            With orchestrator:
            - Events are emitted for governance, resources, knowledge
            - Responses may block actions or add warnings
            - Cross-project features become available
            
            Without orchestrator:
            - Facade works standalone
            - All operations succeed by default
            - No cross-project visibility
        """
        self.name = name
        self.base_path = Path(base_path) if base_path else Path(f"./projects/{name}")
        self.auto_save = auto_save
        self._orchestrator = orchestrator
        
        # Underlying graph
        self._graph: GraphOfThought[str] = GraphOfThought(
            config=GraphConfig(allow_cycles=True)  # Discoveries can create cycles
        )
        
        # Project-level state
        self._nodes: dict[str, ProjectNode] = {}
        self._request_id: str | None = None
        self._session: SessionContext | None = None
        
        # Try to load existing project
        if self.base_path.exists():
            self._load()
            # Notify orchestrator of project load
            self._emit_event("PROJECT_LOADED")
        else:
            self._emit_event("PROJECT_CREATED")
    
    def _emit_event(
        self,
        event_name: str,
        chunk_id: str = "",
        **context: Any,
    ) -> OrchestratorResponse | None:
        """
        Emit event to orchestrator if connected.
        
        Returns response from orchestrator, or None if no orchestrator.
        
        ESCAPE CLAUSE: Event emission is synchronous and blocking.
        For production with slow services:
        1. Make emission async
        2. Queue non-critical events
        3. Add timeouts
        """
        if self._orchestrator is None:
            return None
        
        try:
            from graph_of_thought.services import OrchestratorEvent
            
            event = getattr(OrchestratorEvent, event_name, None)
            if event is None:
                return None
            
            return self._orchestrator.handle(
                event=event,
                project_id=self.name,
                chunk_id=chunk_id,
                **context,
            )
        except Exception as e:
            # ESCAPE CLAUSE: Silent failure on orchestrator errors
            # Production should log these properly
            return None
    
    # =========================================================================
    # Core Operations
    # =========================================================================
    
    def add_request(self, content: str) -> ProjectNode:
        """
        Record the original user request.
        
        This is the root of the project graph.
        """
        if self._request_id is not None:
            raise ValueError("Project already has a request. Use add_followup_request instead.")
        
        thought = self._graph.add_thought(content)
        node = ProjectNode(
            id=thought.id,
            node_type=NodeType.REQUEST,
            content=content,
        )
        self._nodes[node.id] = node
        self._request_id = node.id
        
        # Emit event to orchestrator
        self._emit_event("REQUEST_ADDED", request_content=content)
        
        if self.auto_save:
            self._save()
        
        return node
    
    def ask_question(
        self,
        question: str,
        priority: QuestionPriority = QuestionPriority.BLOCKING,
        context: str | None = None,
        suggested_default: str | None = None,
        parent_id: str | None = None,
    ) -> ProjectNode:
        """
        Record a clarifying question.
        
        BLOCKING questions must be answered before affected chunks can start.
        
        Args:
            question: The question text
            priority: How critical is this question
            context: Why this question matters
            suggested_default: What we'll assume if not answered
            parent_id: What spawned this question (default: request)
        """
        parent = parent_id or self._request_id
        if parent is None:
            raise ValueError("No request to attach question to")
        
        thought = self._graph.add_thought(question, parent_id=parent)
        node = ProjectNode(
            id=thought.id,
            node_type=NodeType.QUESTION,
            content=question,
            priority=priority,
            metadata={
                "context": context,
                "suggested_default": suggested_default,
                "answered": False,
            }
        )
        self._nodes[node.id] = node
        
        # Emit event to orchestrator - may route question or suggest auto-answer
        # ESCAPE CLAUSE: We don't act on auto-answer suggestions yet.
        # Future: if orchestrator suggests answer with high confidence, present to user
        from graph_of_thought.services import Priority as ServicePriority
        priority_map = {
            QuestionPriority.BLOCKING: ServicePriority.CRITICAL,
            QuestionPriority.IMPORTANT: ServicePriority.HIGH,
            QuestionPriority.NICE_TO_HAVE: ServicePriority.LOW,
        }
        self._emit_event(
            "QUESTION_ASKED",
            question=question,
            question_context=context or "",
            priority=priority_map.get(priority, ServicePriority.MEDIUM),
        )
        
        if self.auto_save:
            self._save()
        
        return node
    
    def answer_question(
        self,
        question_id: str,
        answer: str,
        rationale: str | None = None,
    ) -> ProjectNode:
        """
        Record an answer to a question.
        
        This unblocks any chunks that were waiting on this question.
        """
        question = self._nodes.get(question_id)
        if question is None or question.node_type != NodeType.QUESTION:
            raise ValueError(f"No question found with id {question_id}")
        
        thought = self._graph.add_thought(answer, parent_id=question_id)
        node = ProjectNode(
            id=thought.id,
            node_type=NodeType.DECISION,
            content=answer,
            metadata={
                "question_id": question_id,
                "rationale": rationale,
            }
        )
        self._nodes[node.id] = node
        
        # Mark question as answered
        question.metadata["answered"] = True
        question.metadata["answer_id"] = node.id
        
        # Update blocked chunks
        self._update_chunk_readiness()
        
        if self.auto_save:
            self._save()
        
        return node
    
    def plan_chunk(
        self,
        name: str,
        description: str,
        estimated_hours: float = 2.0,
        depends_on: list[str] | None = None,
        blocked_by_questions: list[str] | None = None,
        acceptance_criteria: list[str] | None = None,
        not_in_scope: list[str] | None = None,
    ) -> ProjectNode:
        """
        Plan a work chunk (2-4 hour unit).
        
        Chunks start BLOCKED if they have unanswered questions or 
        incomplete dependencies.
        """
        parent = self._request_id
        if parent is None:
            raise ValueError("No request to attach chunk to")
        
        content = f"**{name}**\n\n{description}"
        thought = self._graph.add_thought(content, parent_id=parent)
        
        # Determine initial status
        blocking_questions = blocked_by_questions or []
        unanswered = [q for q in blocking_questions 
                      if not self._nodes.get(q, {}).metadata.get("answered", False)]
        
        incomplete_deps = [d for d in (depends_on or [])
                          if self._nodes.get(d, {}).status != ChunkStatus.COMPLETE]
        
        if unanswered or incomplete_deps:
            status = ChunkStatus.BLOCKED
        else:
            status = ChunkStatus.READY
        
        node = ProjectNode(
            id=thought.id,
            node_type=NodeType.CHUNK,
            content=content,
            status=status,
            estimated_hours=estimated_hours,
            acceptance_criteria=acceptance_criteria or [],
            metadata={
                "name": name,
                "depends_on": depends_on or [],
                "blocked_by_questions": blocking_questions,
                "not_in_scope": not_in_scope or [],
            }
        )
        self._nodes[node.id] = node
        
        # Add dependency edges
        for dep_id in (depends_on or []):
            if dep_id in self._nodes:
                self._graph.add_edge(dep_id, thought.id, relation="depends_on")
        
        if self.auto_save:
            self._save()
        
        return node
    
    def start_chunk(self, chunk_id: str, goal: str | None = None) -> ProjectNode:
        """
        Begin working on a chunk.
        
        This records the start time and sets up session context for recovery.
        
        ORCHESTRATOR INTEGRATION:
            If connected, checks:
            - Governance approval (may require review for sensitive chunks)
            - Resource availability (token budget, time budget)
            
            May be blocked if governance denies or resources exhausted.
        """
        chunk = self._nodes.get(chunk_id)
        if chunk is None or chunk.node_type != NodeType.CHUNK:
            raise ValueError(f"No chunk found with id {chunk_id}")
        
        if chunk.status == ChunkStatus.BLOCKED:
            blockers = self.get_blockers(chunk_id)
            raise ValueError(f"Chunk is blocked by: {blockers}")
        
        # Check with orchestrator
        response = self._emit_event(
            "CHUNK_STARTED",
            chunk_id=chunk_id,
            chunk_name=chunk.metadata.get("name", ""),
            chunk_description=chunk.content,
            estimated_hours=chunk.estimated_hours or 2.0,
            goal=goal or chunk.metadata.get("name", "Work on chunk"),
        )
        
        # Handle orchestrator response
        if response is not None:
            if not response.proceed:
                # ESCAPE CLAUSE: We raise an exception on governance denial.
                # Alternative: return a status object instead of raising.
                raise ValueError(f"Cannot start chunk: {response.reason}")
            
            if response.resource_warning:
                # Note: We proceed but the warning is logged
                # ESCAPE CLAUSE: Warnings are not surfaced to the user yet.
                # Future: Store warnings in session context for display.
                chunk.metadata["resource_warning"] = True
            
            # Store any suggested patterns from knowledge service
            if response.suggested_patterns:
                chunk.metadata["suggested_patterns"] = [
                    p.content[:200] for p in response.suggested_patterns
                ]
        
        chunk.status = ChunkStatus.IN_PROGRESS
        chunk.metadata["started_at"] = datetime.now().isoformat()
        
        # Set up session context
        self._session = SessionContext(
            project_name=self.name,
            session_started=datetime.now(),
            current_chunk_id=chunk_id,
            current_goal=goal or chunk.metadata.get("name", "Work on chunk"),
        )
        
        # Notify orchestrator of session start
        self._emit_event(
            "SESSION_STARTED",
            chunk_id=chunk_id,
            current_goal=self._session.current_goal,
        )
        
        if self.auto_save:
            self._save()
        
        return chunk
    
    def complete_chunk(
        self,
        chunk_id: str,
        actual_hours: float | None = None,
        produced_files: list[str] | None = None,
        discoveries: list[str] | None = None,
        notes: str | None = None,
        tokens_used: int = 0,
    ) -> ProjectNode:
        """
        Mark a chunk as complete.
        
        This records what was produced and any discoveries made.
        
        ORCHESTRATOR INTEGRATION:
            - Records resource consumption (time, tokens)
            - Captures discoveries as knowledge
            - May check governance for completion approval
        """
        chunk = self._nodes.get(chunk_id)
        if chunk is None or chunk.node_type != NodeType.CHUNK:
            raise ValueError(f"No chunk found with id {chunk_id}")
        
        # Check with orchestrator (some chunks may need completion approval)
        response = self._emit_event(
            "CHUNK_COMPLETED",
            chunk_id=chunk_id,
            chunk_name=chunk.metadata.get("name", ""),
            actual_hours=actual_hours or 0,
            tokens_used=tokens_used,
            produced_files=produced_files or [],
            notes=notes or "",
        )
        
        if response is not None and not response.proceed:
            # Governance denied completion (rare, but possible for critical chunks)
            raise ValueError(f"Cannot complete chunk: {response.reason}")
        
        chunk.status = ChunkStatus.COMPLETE
        chunk.actual_hours = actual_hours
        chunk.metadata["completed_at"] = datetime.now().isoformat()
        chunk.metadata["notes"] = notes
        chunk.metadata["tokens_used"] = tokens_used
        
        # Record produced artifacts
        for file_path in (produced_files or []):
            self.record_artifact(file_path, produced_by=chunk_id)
        
        # Record discoveries (orchestrator also captures these as knowledge)
        for discovery in (discoveries or []):
            self.record_discovery(discovery, found_in=chunk_id)
        
        # Update other chunks that depended on this one
        self._update_chunk_readiness()
        
        # Emit unblock events for newly unblocked chunks
        for node in self._nodes.values():
            if node.node_type == NodeType.CHUNK and node.status == ChunkStatus.READY:
                if chunk_id in node.metadata.get("depends_on", []):
                    self._emit_event(
                        "CHUNK_UNBLOCKED",
                        chunk_id=node.id,
                        chunk_name=node.metadata.get("name", ""),
                        unblocked_by=chunk_id,
                    )
        
        # Clear session context
        if self._session and self._session.current_chunk_id == chunk_id:
            self._emit_event("SESSION_ENDED", chunk_id=chunk_id)
            self._session = None
        
        if self.auto_save:
            self._save()
        
        return chunk
    
    def record_artifact(
        self,
        file_path: str,
        description: str | None = None,
        produced_by: str | None = None,
    ) -> ProjectNode:
        """Record a produced artifact (file, document, etc.)."""
        thought = self._graph.add_thought(
            file_path,
            parent_id=produced_by or self._request_id,
        )
        node = ProjectNode(
            id=thought.id,
            node_type=NodeType.ARTIFACT,
            content=description or file_path,
            file_paths=[file_path],
            metadata={"produced_by": produced_by},
        )
        self._nodes[node.id] = node
        
        if self.auto_save:
            self._save()
        
        return node
    
    def record_discovery(
        self,
        discovery: str,
        found_in: str | None = None,
        affects_chunks: list[str] | None = None,
    ) -> ProjectNode:
        """
        Record something learned during implementation.
        
        Discoveries can affect other chunks (potentially re-blocking them
        or changing their scope).
        
        ORCHESTRATOR INTEGRATION:
            Discoveries are captured as knowledge entries for future retrieval.
            Cross-project discoveries can be found when working on similar problems.
        """
        thought = self._graph.add_thought(
            discovery,
            parent_id=found_in or self._request_id,
        )
        node = ProjectNode(
            id=thought.id,
            node_type=NodeType.DISCOVERY,
            content=discovery,
            metadata={
                "found_in": found_in,
                "affects_chunks": affects_chunks or [],
            }
        )
        self._nodes[node.id] = node
        
        # Emit event for knowledge capture
        self._emit_event(
            "DISCOVERY_RECORDED",
            chunk_id=found_in or "",
            discovery=discovery,
            affects_chunks=affects_chunks or [],
        )
        
        # Add edges to affected chunks
        for chunk_id in (affects_chunks or []):
            if chunk_id in self._nodes:
                self._graph.add_edge(thought.id, chunk_id, relation="affects")
        
        if self.auto_save:
            self._save()
        
        return node
    
    def add_session_note(self, note: str) -> None:
        """Add a note to the current session (survives context loss)."""
        if self._session is None:
            self._session = SessionContext(
                project_name=self.name,
                session_started=datetime.now(),
            )
        self._session.notes.append(f"[{datetime.now().strftime('%H:%M')}] {note}")
        
        if self.auto_save:
            self._save()
    
    # =========================================================================
    # Query Operations
    # =========================================================================
    
    def get_unanswered_questions(self) -> list[ProjectNode]:
        """Get all questions that haven't been answered yet."""
        return [
            node for node in self._nodes.values()
            if node.node_type == NodeType.QUESTION
            and not node.metadata.get("answered", False)
        ]
    
    def get_blocking_questions(self) -> list[ProjectNode]:
        """Get BLOCKING priority questions that haven't been answered."""
        return [
            q for q in self.get_unanswered_questions()
            if q.priority == QuestionPriority.BLOCKING
        ]
    
    def get_ready_chunks(self) -> list[ProjectNode]:
        """Get chunks that are ready to start."""
        return [
            node for node in self._nodes.values()
            if node.node_type == NodeType.CHUNK
            and node.status == ChunkStatus.READY
        ]
    
    def get_blocked_chunks(self) -> list[ProjectNode]:
        """Get chunks that are blocked."""
        return [
            node for node in self._nodes.values()
            if node.node_type == NodeType.CHUNK
            and node.status == ChunkStatus.BLOCKED
        ]
    
    def get_blockers(self, chunk_id: str) -> dict[str, list[str]]:
        """Get what's blocking a specific chunk."""
        chunk = self._nodes.get(chunk_id)
        if chunk is None:
            return {"error": [f"Chunk {chunk_id} not found"]}
        
        blockers = {"questions": [], "dependencies": []}
        
        # Check questions
        for q_id in chunk.metadata.get("blocked_by_questions", []):
            q = self._nodes.get(q_id)
            if q and not q.metadata.get("answered", False):
                blockers["questions"].append(q.content)
        
        # Check dependencies
        for dep_id in chunk.metadata.get("depends_on", []):
            dep = self._nodes.get(dep_id)
            if dep and dep.status != ChunkStatus.COMPLETE:
                blockers["dependencies"].append(dep.metadata.get("name", dep_id))
        
        return blockers
    
    def get_project_status(self) -> dict[str, Any]:
        """Get a summary of project status."""
        chunks = [n for n in self._nodes.values() if n.node_type == NodeType.CHUNK]
        questions = [n for n in self._nodes.values() if n.node_type == NodeType.QUESTION]
        
        return {
            "project": self.name,
            "request": self._nodes.get(self._request_id).content if self._request_id else None,
            "questions": {
                "total": len(questions),
                "unanswered": len([q for q in questions if not q.metadata.get("answered")]),
                "blocking_unanswered": len(self.get_blocking_questions()),
            },
            "chunks": {
                "total": len(chunks),
                "blocked": len([c for c in chunks if c.status == ChunkStatus.BLOCKED]),
                "ready": len([c for c in chunks if c.status == ChunkStatus.READY]),
                "in_progress": len([c for c in chunks if c.status == ChunkStatus.IN_PROGRESS]),
                "complete": len([c for c in chunks if c.status == ChunkStatus.COMPLETE]),
            },
            "estimated_hours_remaining": sum(
                c.estimated_hours or 0 for c in chunks 
                if c.status not in (ChunkStatus.COMPLETE, ChunkStatus.DEFERRED)
            ),
            "session": self._session.to_dict() if self._session else None,
        }
    
    def can_proceed(self) -> tuple[bool, str]:
        """
        Check if work can proceed.
        
        Returns (can_proceed, reason).
        """
        blocking = self.get_blocking_questions()
        if blocking:
            questions = "\n".join(f"  - {q.content}" for q in blocking)
            return False, f"Blocked by {len(blocking)} unanswered questions:\n{questions}"
        
        ready = self.get_ready_chunks()
        if not ready:
            blocked = self.get_blocked_chunks()
            if blocked:
                return False, f"No ready chunks. {len(blocked)} chunks are blocked on dependencies."
            return False, "No chunks planned. Use plan_chunk() to add work items."
        
        return True, f"{len(ready)} chunks ready to start."
    
    # =========================================================================
    # Session Recovery
    # =========================================================================
    
    def get_resumption_context(self) -> str:
        """
        Generate context for resuming after context loss.
        
        This is what a fresh Claude context should read first.
        """
        status = self.get_project_status()
        
        lines = [
            f"# Project Resumption: {self.name}",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Original Request",
            self._nodes.get(self._request_id).content if self._request_id else "No request recorded",
            "",
        ]
        
        # Session context if any
        if self._session:
            lines.extend([
                "## Active Session",
                f"Started: {self._session.session_started.isoformat()}",
                f"Current goal: {self._session.current_goal or 'None set'}",
            ])
            if self._session.current_chunk_id:
                chunk = self._nodes.get(self._session.current_chunk_id)
                if chunk:
                    lines.append(f"Working on: {chunk.metadata.get('name', chunk.id)}")
            if self._session.notes:
                lines.append("Session notes:")
                for note in self._session.notes:
                    lines.append(f"  {note}")
            lines.append("")
        
        # Blocking questions
        blocking = self.get_blocking_questions()
        if blocking:
            lines.extend([
                "## ⚠️ BLOCKING QUESTIONS (must answer before proceeding)",
            ])
            for q in blocking:
                lines.append(f"- [{q.id[:8]}] {q.content}")
                if q.metadata.get("suggested_default"):
                    lines.append(f"  Default if not answered: {q.metadata['suggested_default']}")
            lines.append("")
        
        # Ready chunks
        ready = self.get_ready_chunks()
        if ready:
            lines.extend([
                "## Ready to Start",
            ])
            for c in ready:
                lines.append(f"- [{c.id[:8]}] {c.metadata.get('name', 'Unnamed')} ({c.estimated_hours}h)")
            lines.append("")
        
        # In progress
        in_progress = [n for n in self._nodes.values() 
                       if n.node_type == NodeType.CHUNK and n.status == ChunkStatus.IN_PROGRESS]
        if in_progress:
            lines.extend([
                "## In Progress",
            ])
            for c in in_progress:
                lines.append(f"- [{c.id[:8]}] {c.metadata.get('name', 'Unnamed')}")
            lines.append("")
        
        # Recent discoveries
        discoveries = [n for n in self._nodes.values() if n.node_type == NodeType.DISCOVERY]
        if discoveries:
            recent = sorted(discoveries, key=lambda d: d.created_at, reverse=True)[:5]
            lines.extend([
                "## Recent Discoveries",
            ])
            for d in recent:
                lines.append(f"- {d.content}")
            lines.append("")
        
        # Summary
        lines.extend([
            "## Summary",
            f"Questions: {status['questions']['unanswered']} unanswered of {status['questions']['total']}",
            f"Chunks: {status['chunks']['complete']} complete, {status['chunks']['ready']} ready, {status['chunks']['blocked']} blocked",
            f"Estimated hours remaining: {status['estimated_hours_remaining']}",
        ])
        
        can_proceed, reason = self.can_proceed()
        lines.extend([
            "",
            "## Next Action",
            reason,
        ])
        
        return "\n".join(lines)
    
    # =========================================================================
    # Persistence
    # =========================================================================
    
    def _save(self) -> None:
        """Save project state to disk."""
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Save main state
        state = {
            "name": self.name,
            "request_id": self._request_id,
            "nodes": {nid: n.to_dict() for nid, n in self._nodes.items()},
            "graph": self._graph.to_dict(),
            "session": self._session.to_dict() if self._session else None,
        }
        
        with open(self.base_path / "project.json", "w") as f:
            json.dump(state, f, indent=2, default=str)
        
        # Save human-readable resumption context
        with open(self.base_path / "RESUME.md", "w") as f:
            f.write(self.get_resumption_context())
    
    def _load(self) -> None:
        """Load project state from disk."""
        state_file = self.base_path / "project.json"
        if not state_file.exists():
            return
        
        with open(state_file, "r") as f:
            state = json.load(f)
        
        self.name = state["name"]
        self._request_id = state.get("request_id")
        self._nodes = {nid: ProjectNode.from_dict(nd) for nid, nd in state["nodes"].items()}
        self._graph = GraphOfThought.from_dict(state["graph"])
        self._session = SessionContext.from_dict(state["session"]) if state.get("session") else None
    
    def _update_chunk_readiness(self) -> None:
        """Update chunk statuses based on current blockers."""
        for node in self._nodes.values():
            if node.node_type != NodeType.CHUNK:
                continue
            if node.status in (ChunkStatus.COMPLETE, ChunkStatus.IN_PROGRESS, ChunkStatus.DEFERRED):
                continue
            
            blockers = self.get_blockers(node.id)
            has_blockers = blockers.get("questions") or blockers.get("dependencies")
            
            if has_blockers and node.status != ChunkStatus.BLOCKED:
                node.status = ChunkStatus.BLOCKED
            elif not has_blockers and node.status == ChunkStatus.BLOCKED:
                node.status = ChunkStatus.READY
    
    # =========================================================================
    # Export
    # =========================================================================
    
    def to_markdown(self) -> str:
        """Export entire project as markdown."""
        lines = [
            f"# {self.name}",
            "",
            "## Request",
            self._nodes.get(self._request_id).content if self._request_id else "None",
            "",
        ]
        
        # Questions and Decisions
        questions = [n for n in self._nodes.values() if n.node_type == NodeType.QUESTION]
        if questions:
            lines.extend(["## Questions & Decisions", ""])
            for q in questions:
                status = "✅" if q.metadata.get("answered") else "❓"
                lines.append(f"### {status} {q.content}")
                if q.metadata.get("context"):
                    lines.append(f"*Context: {q.metadata['context']}*")
                if q.metadata.get("answered"):
                    answer_id = q.metadata.get("answer_id")
                    answer = self._nodes.get(answer_id)
                    if answer:
                        lines.append(f"**Answer:** {answer.content}")
                elif q.metadata.get("suggested_default"):
                    lines.append(f"*Default: {q.metadata['suggested_default']}*")
                lines.append("")
        
        # Chunks
        chunks = [n for n in self._nodes.values() if n.node_type == NodeType.CHUNK]
        if chunks:
            lines.extend(["## Work Chunks", ""])
            for c in sorted(chunks, key=lambda x: x.created_at):
                status_icon = {
                    ChunkStatus.BLOCKED: "🚫",
                    ChunkStatus.READY: "🟡",
                    ChunkStatus.IN_PROGRESS: "🔵",
                    ChunkStatus.REVIEW: "🟠",
                    ChunkStatus.COMPLETE: "✅",
                    ChunkStatus.DEFERRED: "⏸️",
                }.get(c.status, "❓")
                lines.append(f"### {status_icon} {c.metadata.get('name', 'Unnamed')}")
                lines.append(f"*Status: {c.status.name} | Estimate: {c.estimated_hours}h*")
                lines.append("")
                lines.append(c.content.split("\n\n", 1)[-1] if "\n\n" in c.content else c.content)
                
                if c.acceptance_criteria:
                    lines.append("")
                    lines.append("**Acceptance Criteria:**")
                    for criterion in c.acceptance_criteria:
                        lines.append(f"- [ ] {criterion}")
                
                if c.metadata.get("not_in_scope"):
                    lines.append("")
                    lines.append("**Not in scope:**")
                    for item in c.metadata["not_in_scope"]:
                        lines.append(f"- {item}")
                
                lines.append("")
        
        # Discoveries
        discoveries = [n for n in self._nodes.values() if n.node_type == NodeType.DISCOVERY]
        if discoveries:
            lines.extend(["## Discoveries", ""])
            for d in discoveries:
                lines.append(f"- {d.content}")
            lines.append("")
        
        # Artifacts
        artifacts = [n for n in self._nodes.values() if n.node_type == NodeType.ARTIFACT]
        if artifacts:
            lines.extend(["## Artifacts", ""])
            for a in artifacts:
                lines.append(f"- `{a.file_paths[0] if a.file_paths else 'unknown'}` - {a.content}")
            lines.append("")
        
        return "\n".join(lines)
