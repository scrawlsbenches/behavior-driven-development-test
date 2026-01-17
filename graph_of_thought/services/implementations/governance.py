"""
Governance Service Implementations.

Provides InMemoryGovernanceService (testable) and SimpleGovernanceService (basic).
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Callable
import uuid

from ..protocols import (
    GovernanceService,
    ApprovalStatus,
)


class InMemoryGovernanceService:
    """
    Testable in-memory governance service for BDD testing.

    Use when: Writing BDD tests that need to verify governance behavior,
              such as approval workflows, policy enforcement, and audit logging.

    Unlike SimpleGovernanceService (which has fixed default policies), this
    implementation provides full control over policies and state for testing.
    By default, it auto-approves everything (configurable via default_status).

    Features:
    - Configurable policies via constructor or methods
    - Full in-memory storage of approvals, policies, and audit records
    - Query methods for test assertions
    - Clear method to reset state between tests

    Example usage in tests:
        governance = InMemoryGovernanceService(
            policies={
                "deploy_production": ApprovalStatus.NEEDS_REVIEW,
                "delete_data": ApprovalStatus.DENIED,
            }
        )

        # Test that deployment requires review
        status, reason = governance.check_approval("deploy_production", {})
        assert status == ApprovalStatus.NEEDS_REVIEW

        # Verify audit trail
        governance.record_audit("deploy_production", {}, "pending", "ai")
        audit_log = governance.get_audit_log()
        assert len(audit_log) == 1
    """

    def __init__(
        self,
        policies: dict[str, ApprovalStatus] | None = None,
        default_status: ApprovalStatus = ApprovalStatus.APPROVED,
    ):
        """
        Initialize the governance service with optional policies.

        Args:
            policies: Initial policy mappings (action -> status).
                     If None, starts with no policies defined.
            default_status: Status to return when no policy matches an action.
                           Defaults to APPROVED for test convenience.
        """
        self._policies: dict[str, ApprovalStatus | Callable] = dict(policies) if policies else {}
        self._default_status = default_status
        self._audit_log: list[dict[str, Any]] = []
        self._pending_approvals: dict[str, dict[str, Any]] = {}
        self._resolved_approvals: dict[str, dict[str, Any]] = {}

    # =========================================================================
    # GovernanceService Protocol Methods
    # =========================================================================

    def check_approval(
        self,
        action: str,
        context: dict[str, Any],
    ) -> tuple[ApprovalStatus, str]:
        """
        Check if an action is approved based on configured policies.

        Returns the policy-defined status, or the default status if no
        policy is defined for the action.
        """
        policy = self._policies.get(action)

        if policy is None:
            return self._default_status, f"No policy defined - using default ({self._default_status.name})"

        if callable(policy):
            try:
                result = policy(context)
                if isinstance(result, tuple):
                    return result
                return ApprovalStatus.APPROVED if result else ApprovalStatus.DENIED, "Policy function evaluated"
            except Exception as e:
                return ApprovalStatus.NEEDS_REVIEW, f"Policy error: {e}"

        if isinstance(policy, ApprovalStatus):
            return policy, f"Policy for '{action}' requires {policy.name}"

        return self._default_status, "Unknown policy type - using default"

    def request_approval(
        self,
        action: str,
        context: dict[str, Any],
        justification: str,
    ) -> str:
        """
        Request approval for an action, storing it as pending.

        Returns an approval request ID that can be used to query or resolve
        the approval later.
        """
        approval_id = f"approval-{uuid.uuid4().hex[:8]}"
        self._pending_approvals[approval_id] = {
            "id": approval_id,
            "action": action,
            "context": context,
            "justification": justification,
            "requested_at": datetime.now().isoformat(),
            "status": "pending",
        }
        return approval_id

    def get_policies(self, scope: str) -> list[dict[str, Any]]:
        """
        Get all policies, optionally filtered by scope.

        Note: Scope filtering is not implemented in this simple version.
        All policies are returned regardless of scope.
        """
        return [
            {
                "action": action,
                "status": str(status) if isinstance(status, ApprovalStatus) else "callable",
                "scope": scope,
            }
            for action, status in self._policies.items()
        ]

    def record_audit(
        self,
        action: str,
        context: dict[str, Any],
        result: str,
        actor: str,
    ) -> None:
        """
        Record an action in the audit log.

        Each audit entry includes a timestamp and all provided details.
        """
        self._audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "context": context,
            "result": result,
            "actor": actor,
        })

    # =========================================================================
    # Policy Configuration Methods
    # =========================================================================

    def add_policy(
        self,
        action: str,
        status: ApprovalStatus | Callable[[dict[str, Any]], tuple[ApprovalStatus, str] | bool],
    ) -> None:
        """
        Add or update a policy for an action.

        Args:
            action: The action name to set policy for
            status: Either an ApprovalStatus or a callable that takes context
                   and returns (ApprovalStatus, reason) or bool
        """
        self._policies[action] = status

    def remove_policy(self, action: str) -> bool:
        """
        Remove a policy for an action.

        Returns True if a policy was removed, False if no policy existed.
        """
        if action in self._policies:
            del self._policies[action]
            return True
        return False

    def set_default_status(self, status: ApprovalStatus) -> None:
        """Set the default status for actions without explicit policies."""
        self._default_status = status

    # =========================================================================
    # Approval Management Methods (for simulating human approval workflow)
    # =========================================================================

    def approve(self, approval_id: str, approver: str, notes: str = "") -> bool:
        """
        Approve a pending request.

        Returns True if successful, False if approval_id not found.
        """
        if approval_id not in self._pending_approvals:
            return False

        approval = self._pending_approvals.pop(approval_id)
        approval["status"] = "approved"
        approval["approved_by"] = approver
        approval["approved_at"] = datetime.now().isoformat()
        approval["notes"] = notes
        self._resolved_approvals[approval_id] = approval
        return True

    def deny(self, approval_id: str, denier: str, reason: str = "") -> bool:
        """
        Deny a pending request.

        Returns True if successful, False if approval_id not found.
        """
        if approval_id not in self._pending_approvals:
            return False

        approval = self._pending_approvals.pop(approval_id)
        approval["status"] = "denied"
        approval["denied_by"] = denier
        approval["denied_at"] = datetime.now().isoformat()
        approval["denial_reason"] = reason
        self._resolved_approvals[approval_id] = approval
        return True

    # =========================================================================
    # Query Methods for Test Assertions
    # =========================================================================

    def get_audit_log(
        self,
        action_filter: str | None = None,
        actor_filter: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve audit log entries for test assertions.

        Args:
            action_filter: Filter to specific action type
            actor_filter: Filter to specific actor
            limit: Maximum number of entries to return (most recent first)

        Returns:
            List of audit entries matching the filters
        """
        logs = self._audit_log

        if action_filter:
            logs = [entry for entry in logs if entry["action"] == action_filter]

        if actor_filter:
            logs = [entry for entry in logs if entry["actor"] == actor_filter]

        if limit:
            logs = logs[-limit:]

        return logs

    def get_pending_approvals(
        self,
        action_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve all pending approval requests for test assertions.

        Args:
            action_filter: Filter to specific action type

        Returns:
            List of pending approval requests
        """
        approvals = list(self._pending_approvals.values())

        if action_filter:
            approvals = [a for a in approvals if a["action"] == action_filter]

        return approvals

    def get_approval_by_id(self, approval_id: str) -> dict[str, Any] | None:
        """
        Get details for a specific approval request by ID.

        Searches both pending and resolved approvals.

        Args:
            approval_id: The approval request ID

        Returns:
            Approval details dict, or None if not found
        """
        if approval_id in self._pending_approvals:
            return self._pending_approvals[approval_id]
        if approval_id in self._resolved_approvals:
            return self._resolved_approvals[approval_id]
        return None

    def get_resolved_approvals(
        self,
        status_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve all resolved (approved/denied) approval requests.

        Args:
            status_filter: Filter by resolution status ("approved" or "denied")

        Returns:
            List of resolved approval requests
        """
        approvals = list(self._resolved_approvals.values())

        if status_filter:
            approvals = [a for a in approvals if a["status"] == status_filter]

        return approvals

    # =========================================================================
    # Test Utility Methods
    # =========================================================================

    def clear(self) -> None:
        """
        Reset all state for clean test isolation.

        Clears:
        - All policies
        - Audit log
        - Pending approvals
        - Resolved approvals

        Note: Does not reset default_status. Call set_default_status()
        separately if needed.
        """
        self._policies.clear()
        self._audit_log.clear()
        self._pending_approvals.clear()
        self._resolved_approvals.clear()

    def clear_audit_log(self) -> None:
        """Clear only the audit log, preserving other state."""
        self._audit_log.clear()

    def clear_approvals(self) -> None:
        """Clear only approvals (pending and resolved), preserving other state."""
        self._pending_approvals.clear()
        self._resolved_approvals.clear()

    @property
    def audit_count(self) -> int:
        """Get the total number of audit log entries."""
        return len(self._audit_log)

    @property
    def pending_count(self) -> int:
        """Get the number of pending approvals."""
        return len(self._pending_approvals)

    @property
    def policy_count(self) -> int:
        """Get the number of configured policies."""
        return len(self._policies)


class SimpleGovernanceService:
    """
    Basic governance with configurable policies.

    Policies are defined as simple rules:
    - action_name: "approve" | "deny" | "review" | condition_func

    ESCAPE CLAUSE: This is rule-based, not workflow-based.
    Real governance needs:
    - Multi-step approval workflows
    - Role-based permissions
    - Time-based policies (freeze periods)
    - External system integration
    """

    def __init__(self):
        self._policies: dict[str, Any] = {
            # Default: approve everything except production deploys
            "deploy_production": ApprovalStatus.NEEDS_REVIEW,
            "delete_project": ApprovalStatus.NEEDS_REVIEW,
        }
        self._audit_log: list[dict[str, Any]] = []
        self._pending_approvals: dict[str, dict[str, Any]] = {}

    def add_policy(self, action: str, status: ApprovalStatus | Callable) -> None:
        """Add or update a policy."""
        self._policies[action] = status

    def check_approval(
        self,
        action: str,
        context: dict[str, Any],
    ) -> tuple[ApprovalStatus, str]:
        policy = self._policies.get(action)

        if policy is None:
            return ApprovalStatus.APPROVED, "No policy defined - default approve"

        if callable(policy):
            # ESCAPE CLAUSE: Callable policies not fully implemented
            # They should return (ApprovalStatus, reason)
            try:
                result = policy(context)
                if isinstance(result, tuple):
                    return result
                return ApprovalStatus.APPROVED if result else ApprovalStatus.DENIED, ""
            except Exception as e:
                return ApprovalStatus.NEEDS_REVIEW, f"Policy error: {e}"

        if isinstance(policy, ApprovalStatus):
            return policy, f"Policy for '{action}' requires {policy.name}"

        return ApprovalStatus.APPROVED, "Unknown policy type - default approve"

    def request_approval(
        self,
        action: str,
        context: dict[str, Any],
        justification: str,
    ) -> str:
        approval_id = f"approval-{uuid.uuid4().hex[:8]}"
        self._pending_approvals[approval_id] = {
            "action": action,
            "context": context,
            "justification": justification,
            "requested_at": datetime.now().isoformat(),
            "status": "pending",
        }
        return approval_id

    def approve(self, approval_id: str, approver: str) -> bool:
        """Approve a pending request (called by human)."""
        if approval_id not in self._pending_approvals:
            return False
        self._pending_approvals[approval_id]["status"] = "approved"
        self._pending_approvals[approval_id]["approved_by"] = approver
        self._pending_approvals[approval_id]["approved_at"] = datetime.now().isoformat()
        return True

    def deny(self, approval_id: str, denier: str, reason: str) -> bool:
        """Deny a pending request (called by human)."""
        if approval_id not in self._pending_approvals:
            return False
        self._pending_approvals[approval_id]["status"] = "denied"
        self._pending_approvals[approval_id]["denied_by"] = denier
        self._pending_approvals[approval_id]["denied_at"] = datetime.now().isoformat()
        self._pending_approvals[approval_id]["denial_reason"] = reason
        return True

    def get_policies(self, scope: str) -> list[dict[str, Any]]:
        return [{"action": k, "policy": str(v)} for k, v in self._policies.items()]

    def record_audit(
        self,
        action: str,
        context: dict[str, Any],
        result: str,
        actor: str,
    ) -> None:
        self._audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "context": context,
            "result": result,
            "actor": actor,
        })

    def get_audit_log(
        self,
        action_filter: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve audit log entries."""
        logs = self._audit_log
        if action_filter:
            logs = [l for l in logs if l["action"] == action_filter]
        return logs[-limit:]
