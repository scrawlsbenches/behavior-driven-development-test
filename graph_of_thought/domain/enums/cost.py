"""
Enums for Cost Management capability.
"""

from enum import Enum


class BudgetLevel(Enum):
    """Warning levels for budget consumption."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EXHAUSTED = "exhausted"


class BudgetStatus(Enum):
    """Status of a budget allocation."""
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"
