"""
Shared enums used across multiple business capabilities.
"""

from enum import Enum, auto


class Priority(Enum):
    """Priority levels for work items and questions."""
    CRITICAL = auto()    # Drop everything
    HIGH = auto()        # Do soon
    MEDIUM = auto()      # Normal queue
    LOW = auto()         # When time permits
    BACKLOG = auto()     # Eventually


class ResourceType(Enum):
    """Types of resources that can be tracked/budgeted."""
    TOKENS = auto()           # LLM API tokens
    HUMAN_ATTENTION = auto()  # Human focus time
    COMPUTE_TIME = auto()     # CI/CD, test environments
    CALENDAR_TIME = auto()    # Wall clock deadlines
    COST_DOLLARS = auto()     # Actual money spent
