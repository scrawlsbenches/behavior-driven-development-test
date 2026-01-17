"""
Enums for Governance & Compliance capability.
"""

from enum import Enum, auto


class ApprovalStatus(Enum):
    """Result of a governance check."""
    APPROVED = auto()          # Proceed
    DENIED = auto()            # Cannot proceed
    NEEDS_REVIEW = auto()      # Human must review
    NEEDS_INFO = auto()        # More information required
    CONDITIONAL = auto()       # Approved with conditions


class ApprovalType(Enum):
    """Types of approval workflows."""
    STANDARD = "standard"
    EXPEDITED = "expedited"
    EMERGENCY = "emergency"


class RequestStatus(Enum):
    """Status of an approval request."""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
