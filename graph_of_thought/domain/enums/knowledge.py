"""
Enums for Knowledge Management capability.
"""

from enum import Enum


class QuestionPriority(Enum):
    """Priority levels for questions."""
    LOW = "low"
    NORMAL = "normal"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class QuestionStatus(Enum):
    """Status of a question in the system."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    ANSWERED = "answered"
    CLOSED = "closed"
