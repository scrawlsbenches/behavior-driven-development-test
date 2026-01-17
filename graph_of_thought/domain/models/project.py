"""
Domain models for Project Management capability.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional

from graph_of_thought.domain.enums import ProjectStatus, ChunkStatus


@dataclass
class Project:
    """A project being worked on."""
    id: str
    name: str
    description: str = ""
    status: ProjectStatus = ProjectStatus.PLANNING
    owner: str = ""
    team: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkChunk:
    """
    A focused work session (2-4 hours) with clear goals.
    """
    id: str
    name: str
    project: str
    status: ChunkStatus = ChunkStatus.ACTIVE
    goals: List[str] = field(default_factory=list)
    assigned_to: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    blocked_by: Optional[str] = None  # Question or issue blocking work
    notes: str = ""
    deliverables: List[str] = field(default_factory=list)


@dataclass
class SessionHandoff:
    """Context package for resuming work across sessions."""
    id: str
    from_session: str
    to_session: Optional[str] = None
    chunk_id: str = ""
    summary: str = ""
    next_steps: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    picked_up_at: Optional[datetime] = None


@dataclass
class HandoffPackage:
    """
    Complete context for resuming work.

    Used when transitioning between sessions or team members.
    """
    id: str
    project_id: str
    summary: str
    key_decisions: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
