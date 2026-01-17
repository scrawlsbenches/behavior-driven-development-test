"""
Enums for AI Reasoning capability.
"""

from enum import Enum, auto


class ThoughtStatus(Enum):
    """Status of a thought node in the graph."""
    PENDING = auto()
    ACTIVE = auto()
    COMPLETED = auto()
    PRUNED = auto()
    MERGED = auto()
    FAILED = auto()
