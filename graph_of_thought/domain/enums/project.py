"""
Enums for Project Management capability.
"""

from enum import Enum


class ProjectStatus(Enum):
    """Status of a project."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ChunkStatus(Enum):
    """Status of a work chunk."""
    ACTIVE = "active"
    BLOCKED = "blocked"
    PAUSED = "paused"
    COMPLETED = "completed"
