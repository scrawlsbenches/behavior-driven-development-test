"""
Projects - Work Organization and Collaboration
==============================================

Projects organize reasoning work into manageable units. They track:
- Work chunks (focused 2-4 hour sessions)
- Handoffs (context for resuming work)
- Team collaboration (who's working on what)

PROJECTS VS GRAPHS
------------------

A Graph is a REASONING STRUCTURE (thoughts and connections).
A Project is a WORK CONTAINER (graphs, chunks, handoffs).

One project may contain:
- Multiple graphs (different aspects of the problem)
- Multiple work chunks (different sessions)
- Multiple team members (different contributors)

The graph doesn't know about projects. Projects wrap graphs.

WORK CHUNKS
-----------

A work chunk is a focused work session:
- Clear goal ("Implement the API endpoint")
- Time-boxed (typically 2-4 hours)
- Documented outcome ("Endpoint works, tests passing")

Chunks help with:
- Context switching (know where you left off)
- Handoffs (someone else can continue)
- Progress tracking (what got done)

HANDOFFS
--------

A handoff captures context for resuming work:
- What was accomplished
- What's left to do
- Any blockers or questions
- Relevant files/resources

Handoffs enable:
- Async collaboration (continue tomorrow)
- Team handoffs (colleague continues)
- AI handoffs (Claude continues)

DESIGN DECISIONS
----------------

1. PROJECTS ARE LIGHTWEIGHT

   Projects are just metadata containers. The actual work (graphs)
   lives in services. Projects track:
   - What graphs belong to this project
   - What chunks of work have been done
   - What's the current state

2. CHUNKS ARE IMMUTABLE ONCE COMPLETE

   You can update a chunk while working on it. Once completed,
   it's immutable (historical record). Start a new chunk for
   new work.

3. HANDOFFS ARE SNAPSHOTS

   A handoff is a point-in-time snapshot. Creating a new handoff
   doesn't modify the old one. This creates a history of handoffs.

"""

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime
from uuid import uuid4
from enum import Enum, auto


# =============================================================================
# ENUMS
# =============================================================================

class ChunkStatus(Enum):
    """Status of a work chunk."""
    PLANNED = auto()    # Created but not started
    ACTIVE = auto()     # Currently being worked on
    COMPLETED = auto()  # Finished successfully
    ABANDONED = auto()  # Stopped without completion


class ProjectStatus(Enum):
    """Status of a project."""
    ACTIVE = auto()
    PAUSED = auto()
    COMPLETED = auto()
    ARCHIVED = auto()


# =============================================================================
# WORK CHUNK
# =============================================================================

@dataclass
class WorkChunk:
    """
    A focused work session within a project.

    Work chunks represent time-boxed, goal-oriented work sessions.
    They help with context management and handoffs.

    Attributes:
        id: Unique identifier.
        name: Short name for the chunk.
        goal: What this chunk aims to accomplish.
        status: Current status (planned, active, completed, abandoned).
        notes: Notes accumulated during work.
        started_at: When work started.
        completed_at: When work finished.
        graph_ids: IDs of graphs created/modified in this chunk.

    Example:
        chunk = WorkChunk(
            name="API Implementation",
            goal="Implement the /search endpoint",
        )
        chunk = chunk.start()
        # ... do work ...
        chunk = chunk.complete(notes="Endpoint works, needs tests")
    """

    name: str
    """Short name describing this chunk of work."""

    goal: str
    """What this chunk aims to accomplish."""

    id: str = field(default_factory=lambda: str(uuid4()))
    """Unique identifier."""

    status: ChunkStatus = ChunkStatus.PLANNED
    """Current status of the chunk."""

    notes: str = ""
    """Notes accumulated during work."""

    started_at: datetime | None = None
    """When work started (None if not started)."""

    completed_at: datetime | None = None
    """When work finished (None if not finished)."""

    graph_ids: list[str] = field(default_factory=list)
    """IDs of graphs created or modified in this chunk."""

    # =========================================================================
    # STATE TRANSITIONS
    # =========================================================================

    def start(self) -> "WorkChunk":
        """
        Start working on this chunk.

        Returns:
            New WorkChunk with status=ACTIVE and started_at set.

        Raises:
            ValueError: If chunk is not in PLANNED status.
        """
        if self.status != ChunkStatus.PLANNED:
            raise ValueError(f"Cannot start chunk in {self.status} status")

        return WorkChunk(
            id=self.id,
            name=self.name,
            goal=self.goal,
            status=ChunkStatus.ACTIVE,
            notes=self.notes,
            started_at=datetime.now(),
            completed_at=None,
            graph_ids=self.graph_ids.copy(),
        )

    def complete(self, notes: str = "") -> "WorkChunk":
        """
        Mark this chunk as completed.

        Args:
            notes: Summary of what was accomplished.

        Returns:
            New WorkChunk with status=COMPLETED and completed_at set.

        Raises:
            ValueError: If chunk is not in ACTIVE status.
        """
        if self.status != ChunkStatus.ACTIVE:
            raise ValueError(f"Cannot complete chunk in {self.status} status")

        return WorkChunk(
            id=self.id,
            name=self.name,
            goal=self.goal,
            status=ChunkStatus.COMPLETED,
            notes=notes or self.notes,
            started_at=self.started_at,
            completed_at=datetime.now(),
            graph_ids=self.graph_ids.copy(),
        )

    def abandon(self, reason: str = "") -> "WorkChunk":
        """
        Abandon this chunk (stop without completion).

        Args:
            reason: Why the chunk was abandoned.

        Returns:
            New WorkChunk with status=ABANDONED.
        """
        if self.status == ChunkStatus.COMPLETED:
            raise ValueError("Cannot abandon a completed chunk")

        return WorkChunk(
            id=self.id,
            name=self.name,
            goal=self.goal,
            status=ChunkStatus.ABANDONED,
            notes=f"ABANDONED: {reason}\n\n{self.notes}".strip(),
            started_at=self.started_at,
            completed_at=datetime.now(),
            graph_ids=self.graph_ids.copy(),
        )

    def add_graph(self, graph_id: str) -> "WorkChunk":
        """
        Associate a graph with this chunk.

        Args:
            graph_id: ID of the graph to associate.

        Returns:
            New WorkChunk with the graph added.
        """
        new_ids = self.graph_ids.copy()
        if graph_id not in new_ids:
            new_ids.append(graph_id)

        return WorkChunk(
            id=self.id,
            name=self.name,
            goal=self.goal,
            status=self.status,
            notes=self.notes,
            started_at=self.started_at,
            completed_at=self.completed_at,
            graph_ids=new_ids,
        )


# =============================================================================
# HANDOFF
# =============================================================================

@dataclass
class Handoff:
    """
    Context snapshot for resuming work.

    A handoff captures everything needed to continue work later,
    whether by the same person, a colleague, or an AI.

    Attributes:
        id: Unique identifier.
        created_at: When this handoff was created.
        accomplished: What was done.
        remaining: What's left to do.
        blockers: Any blockers or questions.
        context: Additional context (files, resources, notes).
        chunk_id: The work chunk this handoff is for.

    Example:
        handoff = Handoff(
            accomplished="Implemented basic search",
            remaining="Add pagination, error handling",
            blockers=["Need API key for production testing"],
            context={"relevant_files": ["search.py", "tests/test_search.py"]},
            chunk_id=current_chunk.id,
        )
    """

    accomplished: str
    """What was accomplished in this work session."""

    remaining: str
    """What's left to do."""

    id: str = field(default_factory=lambda: str(uuid4()))
    """Unique identifier."""

    created_at: datetime = field(default_factory=datetime.now)
    """When this handoff was created."""

    blockers: list[str] = field(default_factory=list)
    """Any blockers preventing progress."""

    context: dict[str, Any] = field(default_factory=dict)
    """Additional context (files, resources, decisions, etc.)."""

    chunk_id: str | None = None
    """ID of the work chunk this handoff is for."""


# =============================================================================
# PROJECT
# =============================================================================

@dataclass
class Project:
    """
    Container for organizing work.

    A project groups related graphs, work chunks, and handoffs
    into a coherent unit of work.

    Attributes:
        id: Unique identifier.
        name: Project name.
        description: Project description.
        status: Current status.
        chunks: Work chunks in this project.
        handoffs: Handoffs created in this project.
        graph_ids: All graphs associated with this project.
        created_at: When the project was created.

    Example:
        project = Project(
            name="API Redesign",
            description="Redesign the public API for v2",
        )
        chunk = WorkChunk(name="Design Phase", goal="Define API surface")
        project = project.add_chunk(chunk)
    """

    name: str
    """Project name."""

    description: str = ""
    """Project description."""

    id: str = field(default_factory=lambda: str(uuid4()))
    """Unique identifier."""

    status: ProjectStatus = ProjectStatus.ACTIVE
    """Current project status."""

    chunks: list[WorkChunk] = field(default_factory=list)
    """Work chunks in this project."""

    handoffs: list[Handoff] = field(default_factory=list)
    """Handoffs created in this project."""

    graph_ids: list[str] = field(default_factory=list)
    """All graphs associated with this project."""

    created_at: datetime = field(default_factory=datetime.now)
    """When the project was created."""

    # =========================================================================
    # CHUNK MANAGEMENT
    # =========================================================================

    def add_chunk(self, chunk: WorkChunk) -> "Project":
        """
        Add a work chunk to the project.

        Args:
            chunk: The work chunk to add.

        Returns:
            New Project with the chunk added.
        """
        new_chunks = self.chunks.copy()
        new_chunks.append(chunk)

        return Project(
            id=self.id,
            name=self.name,
            description=self.description,
            status=self.status,
            chunks=new_chunks,
            handoffs=self.handoffs.copy(),
            graph_ids=self.graph_ids.copy(),
            created_at=self.created_at,
        )

    def get_active_chunk(self) -> WorkChunk | None:
        """Get the currently active work chunk, if any."""
        for chunk in self.chunks:
            if chunk.status == ChunkStatus.ACTIVE:
                return chunk
        return None

    # =========================================================================
    # HANDOFF MANAGEMENT
    # =========================================================================

    def add_handoff(self, handoff: Handoff) -> "Project":
        """
        Add a handoff to the project.

        Args:
            handoff: The handoff to add.

        Returns:
            New Project with the handoff added.
        """
        new_handoffs = self.handoffs.copy()
        new_handoffs.append(handoff)

        return Project(
            id=self.id,
            name=self.name,
            description=self.description,
            status=self.status,
            chunks=self.chunks.copy(),
            handoffs=new_handoffs,
            graph_ids=self.graph_ids.copy(),
            created_at=self.created_at,
        )

    def get_latest_handoff(self) -> Handoff | None:
        """Get the most recent handoff, if any."""
        if not self.handoffs:
            return None
        return max(self.handoffs, key=lambda h: h.created_at)

    # =========================================================================
    # GRAPH MANAGEMENT
    # =========================================================================

    def add_graph(self, graph_id: str) -> "Project":
        """
        Associate a graph with this project.

        Args:
            graph_id: ID of the graph to associate.

        Returns:
            New Project with the graph added.
        """
        new_ids = self.graph_ids.copy()
        if graph_id not in new_ids:
            new_ids.append(graph_id)

        return Project(
            id=self.id,
            name=self.name,
            description=self.description,
            status=self.status,
            chunks=self.chunks.copy(),
            handoffs=self.handoffs.copy(),
            graph_ids=new_ids,
            created_at=self.created_at,
        )
