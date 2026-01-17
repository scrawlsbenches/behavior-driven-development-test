"""
Domain models for Governance & Compliance capability.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, List

from graph_of_thought.domain.enums import ApprovalStatus, ApprovalType, RequestStatus


@dataclass
class ApprovalRequest:
    """A request for approval in a governance workflow."""
    id: str
    action: str
    requester: str
    status: RequestStatus = RequestStatus.PENDING
    approval_type: ApprovalType = ApprovalType.STANDARD
    reason: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    approvers: List[str] = field(default_factory=list)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    denied_by: Optional[str] = None
    denied_at: Optional[datetime] = None
    denial_reason: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


@dataclass
class Policy:
    """A governance policy that defines approval requirements."""
    id: str
    name: str
    description: str = ""
    action_pattern: str = ""  # Regex or glob pattern for matching actions
    required_approvers: int = 1
    approver_roles: List[str] = field(default_factory=list)
    auto_approve: bool = False
    auto_deny: bool = False
    conditions: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
