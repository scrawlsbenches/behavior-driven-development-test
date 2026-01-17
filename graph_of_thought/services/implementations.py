"""
Service Implementations - InMemory and simple implementations for all services.

These provide working defaults that can be replaced with production implementations.

ARCHITECTURE NOTE:
    InMemory implementations provide testable defaults with configurable behavior.
    Simple implementations use in-memory storage and basic business logic.
    Production implementations would connect to real systems (databases, APIs, etc.)

    Upgrade path:
    1. Start with InMemory (testable, configurable defaults)
    2. Move to Simple (features work, in-memory storage)
    3. Move to Production (persistent, integrated)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
import uuid
import json
import os
from pathlib import Path

from .protocols import (
    GovernanceService,
    ProjectManagementService,
    ResourceService,
    KnowledgeService,
    QuestionService,
    CommunicationService,
    ApprovalStatus,
    Priority,
    ResourceType,
    ResourceBudget,
    Decision,
    KnowledgeEntry,
    QuestionTicket,
    HandoffPackage,
)


# =============================================================================
# InMemory Implementations (Testable defaults with configurable behavior)
# =============================================================================

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


class InMemoryProjectManagementService:
    """
    In-memory project management service for testing.

    Stores projects, blocked items, and ready items in memory with
    helper methods for test setup and assertions.

    Use when: Writing tests that need controllable project state.
    Upgrade to: Real project management integration (Jira, Linear, etc.)
    """

    def __init__(self):
        self._projects: dict[str, dict[str, Any]] = {}
        self._blocked_items: dict[str, list[dict[str, Any]]] = {}  # project_id -> items
        self._ready_items: dict[str, list[dict[str, Any]]] = {}    # project_id -> items
        self._estimates: dict[str, dict[str, Any]] = {}            # item_id -> estimate data

    # =========================================================================
    # Test Setup Methods
    # =========================================================================

    def add_project(
        self,
        id: str,
        name: str,
        status: str = "active",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Add a project to the in-memory store.

        Args:
            id: Unique project identifier
            name: Human-readable project name
            status: Project status (default: "active")
            **kwargs: Additional project attributes

        Returns:
            The created project dict
        """
        project = {
            "id": id,
            "name": name,
            "status": status,
            **kwargs,
        }
        self._projects[id] = project
        # Initialize item lists for this project
        if id not in self._blocked_items:
            self._blocked_items[id] = []
        if id not in self._ready_items:
            self._ready_items[id] = []
        return project

    def add_blocked_item(
        self,
        project_id: str,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Add a blocked item to a project.

        Args:
            project_id: The project to add the item to
            item: The blocked item dict (should have 'id', 'name', 'blocked_reason', etc.)

        Returns:
            The item that was added
        """
        if project_id not in self._blocked_items:
            self._blocked_items[project_id] = []

        # Ensure item has project_id
        item_with_project = {**item, "project_id": project_id}
        self._blocked_items[project_id].append(item_with_project)
        return item_with_project

    def add_ready_item(
        self,
        project_id: str,
        item: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Add a ready item to a project.

        Args:
            project_id: The project to add the item to
            item: The ready item dict (should have 'id', 'name', 'priority', etc.)

        Returns:
            The item that was added
        """
        if project_id not in self._ready_items:
            self._ready_items[project_id] = []

        # Ensure item has project_id
        item_with_project = {**item, "project_id": project_id}
        self._ready_items[project_id].append(item_with_project)
        return item_with_project

    def get_all_projects(self) -> list[dict[str, Any]]:
        """
        Get all projects (regardless of status).

        Returns:
            List of all project dicts
        """
        return list(self._projects.values())

    def clear(self) -> None:
        """Reset all state to empty."""
        self._projects.clear()
        self._blocked_items.clear()
        self._ready_items.clear()
        self._estimates.clear()

    # =========================================================================
    # ProjectManagementService Protocol Implementation
    # =========================================================================

    def get_active_projects(self) -> list[dict[str, Any]]:
        """Get all active projects."""
        return [p for p in self._projects.values() if p.get("status") == "active"]

    def get_blocked_items(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """
        Get blocked items, optionally filtered by project.

        If project_id is None, returns blocked items across all projects.
        """
        if project_id is not None:
            return list(self._blocked_items.get(project_id, []))

        # Return all blocked items across all projects
        all_blocked = []
        for items in self._blocked_items.values():
            all_blocked.extend(items)
        return all_blocked

    def get_ready_items(self, project_id: str | None = None) -> list[dict[str, Any]]:
        """
        Get items ready to work on, optionally filtered by project.

        If project_id is None, returns ready items across all projects.
        """
        if project_id is not None:
            return list(self._ready_items.get(project_id, []))

        # Return all ready items across all projects
        all_ready = []
        for items in self._ready_items.values():
            all_ready.extend(items)
        return all_ready

    def get_next_action(self, available_time_hours: float = 2.0) -> dict[str, Any] | None:
        """
        Suggest the highest-priority item that fits in available time.

        Prioritization order:
        1. CRITICAL priority items
        2. HIGH priority items
        3. Items with estimated_hours <= available_time_hours
        """
        all_ready = self.get_ready_items()

        if not all_ready:
            return None

        # Priority mapping for sorting
        priority_order = {
            "CRITICAL": 0,
            "critical": 0,
            "HIGH": 1,
            "high": 1,
            "MEDIUM": 2,
            "medium": 2,
            "LOW": 3,
            "low": 3,
            "BACKLOG": 4,
            "backlog": 4,
        }

        # Filter by time and sort by priority
        candidates = []
        for item in all_ready:
            estimated = item.get("estimated_hours", 1.0)
            if estimated <= available_time_hours:
                priority = item.get("priority", "MEDIUM")
                order = priority_order.get(priority, 2)
                candidates.append((order, item))

        if not candidates:
            # No items fit the time constraint, return highest priority anyway
            candidates = [
                (priority_order.get(item.get("priority", "MEDIUM"), 2), item)
                for item in all_ready
            ]

        candidates.sort(key=lambda x: x[0])
        return candidates[0][1] if candidates else None

    def update_estimate(
        self,
        item_id: str,
        actual_hours: float,
        notes: str = "",
    ) -> None:
        """Record actual time for estimation improvement."""
        self._estimates[item_id] = {
            "actual_hours": actual_hours,
            "notes": notes,
            "recorded_at": datetime.now().isoformat(),
        }

    def get_timeline(self, project_id: str) -> dict[str, Any]:
        """
        Get projected timeline for a project.

        Returns timeline info based on ready items and historical estimate data.
        Uses recorded estimates to calculate accuracy metrics.
        """
        project = self._projects.get(project_id)
        if not project:
            return {}

        ready = self.get_ready_items(project_id)
        blocked = self.get_blocked_items(project_id)

        total_estimated = sum(
            item.get("estimated_hours", 1.0) for item in ready
        )

        # Calculate estimate accuracy from historical data
        accuracy_data = self._calculate_estimate_accuracy(project_id)

        return {
            "project_id": project_id,
            "project_name": project.get("name", ""),
            "ready_item_count": len(ready),
            "blocked_item_count": len(blocked),
            "total_estimated_hours": total_estimated,
            "adjusted_estimated_hours": total_estimated * accuracy_data.get("adjustment_factor", 1.0),
            "estimate_accuracy": accuracy_data,
        }

    def _calculate_estimate_accuracy(self, project_id: str) -> dict[str, Any]:
        """
        Calculate estimate accuracy metrics based on recorded actual times.

        Returns dict with:
        - items_with_actuals: Number of items that have actual time recorded
        - average_ratio: Average of (actual / estimated) for completed items
        - adjustment_factor: Suggested multiplier for future estimates
        """
        items_with_actuals = 0
        ratios = []

        # Get all items for this project
        all_ready = self._ready_items.get(project_id, [])
        all_blocked = self._blocked_items.get(project_id, [])
        all_items = all_ready + all_blocked

        for item in all_items:
            item_id = item.get("id")
            if item_id and item_id in self._estimates:
                estimate_data = self._estimates[item_id]
                actual = estimate_data.get("actual_hours", 0)
                estimated = item.get("estimated_hours", 1.0)
                if actual > 0 and estimated > 0:
                    ratios.append(actual / estimated)
                    items_with_actuals += 1

        if not ratios:
            return {
                "items_with_actuals": 0,
                "average_ratio": 1.0,
                "adjustment_factor": 1.0,
            }

        average_ratio = sum(ratios) / len(ratios)

        return {
            "items_with_actuals": items_with_actuals,
            "average_ratio": round(average_ratio, 2),
            "adjustment_factor": round(average_ratio, 2),
        }

    # =========================================================================
    # State Transition Methods
    # =========================================================================

    def move_to_blocked(
        self,
        project_id: str,
        item_id: str,
        blocked_reason: str,
    ) -> bool:
        """
        Move an item from ready to blocked state.

        Args:
            project_id: The project the item belongs to
            item_id: The ID of the item to move
            blocked_reason: Reason why the item is now blocked

        Returns:
            True if item was moved, False if item not found
        """
        ready_items = self._ready_items.get(project_id, [])

        for i, item in enumerate(ready_items):
            if item.get("id") == item_id:
                # Remove from ready list
                moved_item = ready_items.pop(i)
                # Add blocked reason and move to blocked list
                moved_item["blocked_reason"] = blocked_reason
                moved_item["blocked_at"] = datetime.now().isoformat()
                self.add_blocked_item(project_id, moved_item)
                return True

        return False

    def move_to_ready(
        self,
        project_id: str,
        item_id: str,
        unblock_notes: str = "",
    ) -> bool:
        """
        Move an item from blocked to ready state.

        Args:
            project_id: The project the item belongs to
            item_id: The ID of the item to move
            unblock_notes: Optional notes about how the blocker was resolved

        Returns:
            True if item was moved, False if item not found
        """
        blocked_items = self._blocked_items.get(project_id, [])

        for i, item in enumerate(blocked_items):
            if item.get("id") == item_id:
                # Remove from blocked list
                moved_item = blocked_items.pop(i)
                # Remove blocked metadata and add unblock notes
                moved_item.pop("blocked_reason", None)
                moved_item.pop("blocked_at", None)
                if unblock_notes:
                    moved_item["unblock_notes"] = unblock_notes
                moved_item["unblocked_at"] = datetime.now().isoformat()
                self.add_ready_item(project_id, moved_item)
                return True

        return False

    def update_item_priority(
        self,
        project_id: str,
        item_id: str,
        new_priority: str,
    ) -> bool:
        """
        Update the priority of an item.

        Args:
            project_id: The project the item belongs to
            item_id: The ID of the item to update
            new_priority: New priority value (e.g., "CRITICAL", "HIGH", "MEDIUM", "LOW")

        Returns:
            True if item was updated, False if not found
        """
        # Check ready items
        for item in self._ready_items.get(project_id, []):
            if item.get("id") == item_id:
                item["priority"] = new_priority
                return True

        # Check blocked items
        for item in self._blocked_items.get(project_id, []):
            if item.get("id") == item_id:
                item["priority"] = new_priority
                return True

        return False

    # =========================================================================
    # Query Methods for Test Assertions
    # =========================================================================

    def get_item_by_id(self, item_id: str) -> dict[str, Any] | None:
        """
        Get an item by its ID, searching across all projects and states.

        Args:
            item_id: The item ID to look up

        Returns:
            The item dict if found, None otherwise
        """
        # Search in ready items
        for items in self._ready_items.values():
            for item in items:
                if item.get("id") == item_id:
                    return item

        # Search in blocked items
        for items in self._blocked_items.values():
            for item in items:
                if item.get("id") == item_id:
                    return item

        return None

    def get_items_by_priority(
        self,
        priority: str,
        project_id: str | None = None,
        include_blocked: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Get all items with a specific priority.

        Args:
            priority: The priority to filter by (e.g., "CRITICAL", "HIGH")
            project_id: Optional filter to specific project
            include_blocked: Whether to include blocked items (default: False)

        Returns:
            List of items matching the priority filter
        """
        priority_upper = priority.upper()
        results = []

        # Get ready items
        if project_id:
            ready = self._ready_items.get(project_id, [])
        else:
            ready = []
            for items in self._ready_items.values():
                ready.extend(items)

        for item in ready:
            item_priority = str(item.get("priority", "MEDIUM")).upper()
            if item_priority == priority_upper:
                results.append(item)

        # Optionally include blocked items
        if include_blocked:
            if project_id:
                blocked = self._blocked_items.get(project_id, [])
            else:
                blocked = []
                for items in self._blocked_items.values():
                    blocked.extend(items)

            for item in blocked:
                item_priority = str(item.get("priority", "MEDIUM")).upper()
                if item_priority == priority_upper:
                    results.append(item)

        return results

    def get_project_by_id(self, project_id: str) -> dict[str, Any] | None:
        """
        Get a project by its ID.

        Args:
            project_id: The project ID to look up

        Returns:
            The project dict if found, None otherwise
        """
        return self._projects.get(project_id)

    def get_estimate_history(self, item_id: str) -> dict[str, Any] | None:
        """
        Get the estimate history for an item.

        Args:
            item_id: The item ID to look up

        Returns:
            The estimate data if found, None otherwise
        """
        return self._estimates.get(item_id)

    @property
    def total_item_count(self) -> int:
        """Get the total number of items across all projects and states."""
        count = 0
        for items in self._ready_items.values():
            count += len(items)
        for items in self._blocked_items.values():
            count += len(items)
        return count

    @property
    def project_count(self) -> int:
        """Get the total number of projects."""
        return len(self._projects)


class InMemoryResourceService:
    """
    Testable in-memory resource service for BDD testing.

    Provides full ResourceService protocol implementation with additional
    query methods for test assertions. Stores all budgets, allocations,
    and consumption records in memory with easy inspection.

    Use when: Writing BDD tests that need to verify resource consumption,
              budget enforcement, and allocation behavior.

    Test-friendly features:
    - Constructor accepts initial budgets
    - Query methods for consumption history and totals
    - Clear method to reset state between tests
    - Detailed consumption records with timestamps
    """

    @dataclass
    class ConsumptionRecord:
        """Individual consumption event for tracking and assertions."""
        timestamp: datetime
        resource_type: ResourceType
        scope_type: str
        scope_id: str
        amount: float
        description: str
        remaining_after: float

    def __init__(
        self,
        initial_budgets: dict[tuple[ResourceType, str, str], float] | None = None,
        unlimited: bool = False,
    ):
        """
        Initialize with optional pre-configured budgets.

        Args:
            initial_budgets: Dict mapping (resource_type, scope_type, scope_id)
                           to budget amounts
            unlimited: If True, check_available always returns (True, inf)
                      for any scope without explicit budget (like old Null behavior)
        """
        # Key: (resource_type, scope_type, scope_id)
        self._budgets: dict[tuple[ResourceType, str, str], ResourceBudget] = {}
        self._consumption_history: list[InMemoryResourceService.ConsumptionRecord] = []
        self._unlimited = unlimited

        # Initialize any provided budgets
        if initial_budgets:
            for (resource_type, scope_type, scope_id), amount in initial_budgets.items():
                self._budgets[(resource_type, scope_type, scope_id)] = ResourceBudget(
                    resource_type=resource_type,
                    allocated=amount,
                    consumed=0.0,
                )

    # =========================================================================
    # ResourceService Protocol Implementation
    # =========================================================================

    def get_budget(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
    ) -> ResourceBudget | None:
        """Get budget for a resource in a scope."""
        key = (resource_type, scope_type, scope_id)
        return self._budgets.get(key)

    def allocate(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
    ) -> bool:
        """
        Allocate budget. Returns False if would result in negative allocation.

        If budget exists, adds to existing allocation.
        If budget doesn't exist, creates new budget with the allocation.
        """
        key = (resource_type, scope_type, scope_id)

        if key in self._budgets:
            if self._budgets[key].allocated + amount < 0:
                return False
            self._budgets[key].allocated += amount
        else:
            if amount < 0:
                return False
            self._budgets[key] = ResourceBudget(
                resource_type=resource_type,
                allocated=amount,
                consumed=0.0,
            )
        return True

    def consume(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
        description: str = "",
    ) -> bool:
        """
        Record resource consumption. Returns False if would exceed budget.

        Creates detailed consumption record for test assertions.
        """
        key = (resource_type, scope_type, scope_id)
        budget = self._budgets.get(key)

        if budget is None:
            # No budget means no tracking - auto-create unlimited budget
            budget = ResourceBudget(
                resource_type=resource_type,
                allocated=float('inf'),
                consumed=0.0,
            )
            self._budgets[key] = budget

        # Check if consumption would exceed budget
        if budget.consumed + amount > budget.allocated:
            return False

        # Record consumption
        budget.consumed += amount

        # Create detailed record for test assertions
        record = InMemoryResourceService.ConsumptionRecord(
            timestamp=datetime.now(),
            resource_type=resource_type,
            scope_type=scope_type,
            scope_id=scope_id,
            amount=amount,
            description=description,
            remaining_after=budget.remaining,
        )
        self._consumption_history.append(record)

        return True

    def check_available(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
    ) -> tuple[bool, float]:
        """Check if amount is available. Returns (available, remaining)."""
        budget = self.get_budget(resource_type, scope_type, scope_id)

        if budget is None:
            return True, float('inf')

        remaining = budget.remaining
        return amount <= remaining, remaining

    def get_consumption_report(
        self,
        scope_type: str,
        scope_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """Get consumption breakdown for reporting."""
        relevant_records = [
            r for r in self._consumption_history
            if r.scope_type == scope_type and r.scope_id == scope_id
        ]

        # Filter by date range if provided
        if start_date:
            relevant_records = [r for r in relevant_records if r.timestamp >= start_date]
        if end_date:
            relevant_records = [r for r in relevant_records if r.timestamp <= end_date]

        # Aggregate by resource type
        by_resource: dict[str, float] = {}
        for record in relevant_records:
            rt_name = record.resource_type.name
            by_resource[rt_name] = by_resource.get(rt_name, 0) + record.amount

        # Get current budgets for this scope
        budgets_for_scope = {
            rt.name: {
                "allocated": b.allocated,
                "consumed": b.consumed,
                "remaining": b.remaining,
                "percent_used": b.percent_used,
            }
            for (rt, st, sid), b in self._budgets.items()
            if st == scope_type and sid == scope_id
        }

        return {
            "scope_type": scope_type,
            "scope_id": scope_id,
            "total_events": len(relevant_records),
            "consumption_by_resource": by_resource,
            "budgets": budgets_for_scope,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
        }

    # =========================================================================
    # Test-Friendly Query Methods
    # =========================================================================

    def get_consumption_history(
        self,
        scope_id: str,
        resource_type: ResourceType | None = None,
        scope_type: str | None = None,
    ) -> list[ConsumptionRecord]:
        """
        Get consumption records for a scope, optionally filtered.

        Args:
            scope_id: The scope ID to query
            resource_type: Optional filter by resource type
            scope_type: Optional filter by scope type

        Returns:
            List of ConsumptionRecord objects for test assertions
        """
        records = [r for r in self._consumption_history if r.scope_id == scope_id]

        if resource_type is not None:
            records = [r for r in records if r.resource_type == resource_type]

        if scope_type is not None:
            records = [r for r in records if r.scope_type == scope_type]

        return records

    def get_total_consumed(
        self,
        scope_id: str,
        resource_type: ResourceType | None = None,
        scope_type: str | None = None,
    ) -> float:
        """
        Get total amount consumed for a scope.

        Args:
            scope_id: The scope ID to query
            resource_type: Optional filter by resource type
            scope_type: Optional filter by scope type

        Returns:
            Total consumed amount
        """
        records = self.get_consumption_history(scope_id, resource_type, scope_type)
        return sum(r.amount for r in records)

    def get_remaining(
        self,
        scope_id: str,
        resource_type: ResourceType,
        scope_type: str = "project",
    ) -> float:
        """
        Get remaining budget for a scope.

        Args:
            scope_id: The scope ID to query
            resource_type: The resource type to check
            scope_type: The scope type (default: "project")

        Returns:
            Remaining budget amount, or inf if no budget set
        """
        budget = self.get_budget(resource_type, scope_type, scope_id)
        return budget.remaining if budget else float('inf')

    def set_budget(
        self,
        scope_id: str,
        amount: float,
        resource_type: ResourceType = ResourceType.TOKENS,
        scope_type: str = "project",
        unit: str = "",
    ) -> ResourceBudget:
        """
        Set or update budget for a scope.

        This is a convenience method for test setup that provides
        sensible defaults for common test scenarios.

        Args:
            scope_id: The scope ID to set budget for
            amount: The budget amount to allocate
            resource_type: Resource type (default: TOKENS)
            scope_type: Scope type (default: "project")
            unit: Optional unit label

        Returns:
            The created or updated ResourceBudget
        """
        key = (resource_type, scope_type, scope_id)
        existing = self._budgets.get(key)

        budget = ResourceBudget(
            resource_type=resource_type,
            allocated=amount,
            consumed=existing.consumed if existing else 0.0,
            unit=unit,
        )
        self._budgets[key] = budget
        return budget

    def clear(self) -> None:
        """
        Reset all state for test isolation.

        Clears all budgets, allocations, and consumption history.
        Call this in test setup/teardown for clean test isolation.
        """
        self._budgets.clear()
        self._consumption_history.clear()

    # =========================================================================
    # Additional Test Helpers
    # =========================================================================

    def get_all_budgets(self) -> dict[tuple[ResourceType, str, str], ResourceBudget]:
        """Get all budgets for inspection in tests."""
        return dict(self._budgets)

    def get_all_consumption_records(self) -> list[ConsumptionRecord]:
        """Get all consumption records for inspection in tests."""
        return list(self._consumption_history)

    def has_budget(
        self,
        scope_id: str,
        resource_type: ResourceType = ResourceType.TOKENS,
        scope_type: str = "project",
    ) -> bool:
        """Check if a budget exists for a scope."""
        key = (resource_type, scope_type, scope_id)
        return key in self._budgets

    def is_exhausted(
        self,
        scope_id: str,
        resource_type: ResourceType = ResourceType.TOKENS,
        scope_type: str = "project",
    ) -> bool:
        """Check if budget is exhausted (consumed >= allocated)."""
        budget = self.get_budget(resource_type, scope_type, scope_id)
        return budget.is_exhausted() if budget else False


class InMemoryKnowledgeService:
    """
    In-memory knowledge service for testing and development.

    This implementation stores entries and supports retrieval.
    Unlike SimpleKnowledgeService, this has no persistence and includes test-friendly
    query methods for assertions.

    Use when: Writing tests that need to verify knowledge storage/retrieval behavior.

    Features:
    - Stores entries and decisions in memory
    - Basic keyword search (same as SimpleKnowledgeService)
    - Query methods for test assertions (get_all_entries, get_all_decisions, etc.)
    - clear() method to reset state between tests
    """

    def __init__(self, retrieval_enabled: bool = True):
        """
        Initialize the knowledge service.

        Args:
            retrieval_enabled: If False, retrieve() always returns empty list
                              (like old Null behavior). Default True.
        """
        self._entries: dict[str, KnowledgeEntry] = {}
        self._decisions: dict[str, Decision] = {}
        self._retrieval_enabled = retrieval_enabled

    # =========================================================================
    # KnowledgeService Protocol Implementation
    # =========================================================================

    def store(self, entry: KnowledgeEntry) -> str:
        """Store a knowledge entry. Returns entry ID."""
        if not entry.id:
            entry.id = f"ke-{uuid.uuid4().hex[:8]}"
        self._entries[entry.id] = entry
        return entry.id

    def retrieve(
        self,
        query: str,
        entry_types: list[str] | None = None,
        project_filter: str | None = None,
        limit: int = 5,
    ) -> list[KnowledgeEntry]:
        """
        Keyword-based retrieval.

        Searches entry content and tags for query terms.
        Results are ranked by number of matching keywords.

        If retrieval_enabled is False, always returns empty list.
        """
        if not self._retrieval_enabled:
            return []

        query_terms = query.lower().split()

        results: list[tuple[float, KnowledgeEntry]] = []

        for entry in self._entries.values():
            # Filter by type
            if entry_types and entry.entry_type not in entry_types:
                continue

            # Filter by project
            if project_filter and entry.source_project != project_filter:
                continue

            # Score by keyword overlap
            content_lower = entry.content.lower()
            tag_text = " ".join(entry.tags).lower()
            full_text = f"{content_lower} {tag_text}"

            score = sum(1 for term in query_terms if term in full_text)

            if score > 0:
                results.append((score, entry))

        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)

        return [entry for score, entry in results[:limit]]

    def record_decision(self, decision: Decision) -> str:
        """Record a decision and also store as knowledge entry for retrieval."""
        if not decision.id:
            decision.id = f"dec-{uuid.uuid4().hex[:8]}"

        self._decisions[decision.id] = decision

        # Also store as knowledge entry for retrieval
        entry = KnowledgeEntry(
            id=f"ke-{decision.id}",
            content=f"Decision: {decision.title}\n\nContext: {decision.context}\n\n"
                   f"Chosen: {decision.chosen}\n\nRationale: {decision.rationale}",
            entry_type="decision",
            source_project=decision.project_id,
            source_chunk=decision.chunk_id,
            tags=[decision.title] + decision.options,
        )
        self.store(entry)

        return decision.id

    def find_contradictions(
        self,
        proposed_decision: str,
        project_id: str | None = None,
    ) -> list[Decision]:
        """
        Find past decisions that might contradict a proposed decision.

        Uses keyword-based contradiction detection by looking for:
        1. Decisions with overlapping topic keywords
        2. Decisions with opposite sentiment indicators (e.g., "use X" vs "avoid X")

        Args:
            proposed_decision: The proposed decision text to check
            project_id: Optional filter to only check decisions from a specific project

        Returns:
            List of potentially contradicting decisions, ordered by relevance
        """
        if not proposed_decision:
            return []

        # Extract keywords from proposed decision
        proposed_lower = proposed_decision.lower()
        proposed_words = set(proposed_lower.split())

        # Contradiction indicators - pairs of opposite terms
        contradiction_pairs = [
            ("use", "avoid"),
            ("enable", "disable"),
            ("add", "remove"),
            ("include", "exclude"),
            ("allow", "deny"),
            ("approve", "reject"),
            ("start", "stop"),
            ("create", "delete"),
            ("sync", "async"),
            ("monolith", "microservice"),
        ]

        contradictions: list[tuple[float, Decision]] = []

        for decision in self._decisions.values():
            # Filter by project if specified
            if project_id and decision.project_id != project_id:
                continue

            decision_text = f"{decision.title} {decision.context} {decision.chosen} {decision.rationale}".lower()
            decision_words = set(decision_text.split())

            # Calculate topic overlap score
            common_words = proposed_words & decision_words
            # Filter out common stop words
            stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                         "being", "have", "has", "had", "do", "does", "did", "will",
                         "would", "could", "should", "may", "might", "must", "shall",
                         "to", "of", "in", "for", "on", "with", "at", "by", "from",
                         "as", "into", "through", "during", "before", "after", "above",
                         "below", "between", "under", "again", "further", "then", "once",
                         "and", "or", "but", "if", "because", "until", "while", "although",
                         "this", "that", "these", "those", "it", "its", "we", "they"}
            meaningful_common = common_words - stop_words

            if not meaningful_common:
                continue

            topic_score = len(meaningful_common)

            # Check for contradiction patterns
            contradiction_score = 0.0
            for word1, word2 in contradiction_pairs:
                # Check if proposed has word1 and decision has word2 (or vice versa)
                if (word1 in proposed_lower and word2 in decision_text) or \
                   (word2 in proposed_lower and word1 in decision_text):
                    contradiction_score += 2.0

            # Check for negation patterns
            negation_words = ["not", "no", "never", "without", "don't", "doesn't", "won't", "can't"]
            proposed_has_negation = any(neg in proposed_lower for neg in negation_words)
            decision_has_negation = any(neg in decision_text for neg in negation_words)

            # If one has negation and other doesn't, that's a potential contradiction
            if proposed_has_negation != decision_has_negation and topic_score > 0:
                contradiction_score += 1.0

            total_score = topic_score + contradiction_score

            if total_score >= 2.0:  # Minimum threshold for potential contradiction
                contradictions.append((total_score, decision))

        # Sort by score descending
        contradictions.sort(key=lambda x: x[0], reverse=True)

        return [decision for score, decision in contradictions]

    def get_patterns_for_problem(self, problem_description: str) -> list[KnowledgeEntry]:
        """Find patterns that might help with a problem."""
        return self.retrieve(
            query=problem_description,
            entry_types=["pattern"],
        )

    # =========================================================================
    # Test Assertion Methods
    # =========================================================================

    def get_all_entries(self) -> list[KnowledgeEntry]:
        """Get all stored knowledge entries. Useful for test assertions."""
        return list(self._entries.values())

    def get_all_decisions(self) -> list[Decision]:
        """Get all stored decisions. Useful for test assertions."""
        return list(self._decisions.values())

    def get_entry_by_id(self, entry_id: str) -> KnowledgeEntry | None:
        """Get a specific entry by ID. Returns None if not found."""
        return self._entries.get(entry_id)

    def get_entries_by_tag(self, tag: str) -> list[KnowledgeEntry]:
        """Get all entries that have a specific tag."""
        return [
            entry for entry in self._entries.values()
            if tag in entry.tags
        ]

    def get_entries_by_type(self, entry_type: str) -> list[KnowledgeEntry]:
        """
        Get all entries of a specific type.

        Args:
            entry_type: The type to filter by (e.g., "decision", "pattern", "discovery")

        Returns:
            List of entries matching the specified type
        """
        return [
            entry for entry in self._entries.values()
            if entry.entry_type == entry_type
        ]

    def get_entries_by_project(self, project_id: str) -> list[KnowledgeEntry]:
        """
        Get all entries from a specific project.

        Args:
            project_id: The project ID to filter by

        Returns:
            List of entries from the specified project
        """
        return [
            entry for entry in self._entries.values()
            if entry.source_project == project_id
        ]

    def get_decision_by_id(self, decision_id: str) -> Decision | None:
        """
        Get a specific decision by ID.

        Args:
            decision_id: The decision ID to look up

        Returns:
            The Decision if found, None otherwise
        """
        return self._decisions.get(decision_id)

    def get_decisions_by_project(self, project_id: str) -> list[Decision]:
        """
        Get all decisions for a specific project.

        Args:
            project_id: The project ID to filter by

        Returns:
            List of decisions from the specified project
        """
        return [
            decision for decision in self._decisions.values()
            if decision.project_id == project_id
        ]

    @property
    def entry_count(self) -> int:
        """Get the total number of stored entries."""
        return len(self._entries)

    @property
    def decision_count(self) -> int:
        """Get the total number of stored decisions."""
        return len(self._decisions)

    def clear(self) -> None:
        """Reset all state. Useful for test cleanup between test cases."""
        self._entries.clear()
        self._decisions.clear()


class InMemoryQuestionService:
    """
    Testable in-memory question service with full state tracking.

    Use when: You need a testable QuestionService that tracks all state
    for assertions in BDD tests.

    Unlike SimpleQuestionService (which focuses on production use),
    this implementation:
    - Stores all tickets, answers, and routing decisions
    - Provides query methods for test assertions
    - Supports configurable keyword routing
    - Supports basic auto-answer with knowledge base integration
    - Can be cleared/reset between tests

    Example:
        # Create with custom routing rules
        service = InMemoryQuestionService(
            routing_rules={
                "database-team": ["database", "sql", "postgres", "migration"],
                "frontend-team": ["react", "css", "ui", "component"],
            }
        )

        # Or with knowledge base for auto-answer
        knowledge = InMemoryKnowledgeService()
        service = InMemoryQuestionService(knowledge_service=knowledge)
    """

    # Default routing rules mapping route -> keywords
    DEFAULT_ROUTING_RULES: dict[str, list[str]] = {
        "security-team": ["security", "auth", "permission", "credential", "encryption"],
        "product-owner": ["requirement", "should we", "business", "stakeholder", "feature"],
        "devops": ["deploy", "infrastructure", "scaling", "kubernetes", "docker", "ci/cd"],
        "architect": ["design", "architecture", "pattern", "refactor", "structure"],
        "qa-team": ["test", "testing", "qa", "quality", "coverage", "bug"],
    }

    def __init__(
        self,
        routing_rules: dict[str, list[str]] | None = None,
        knowledge_service: KnowledgeService | None = None,
        auto_answer_threshold: float = 0.7,
    ):
        """
        Initialize the question service.

        Args:
            routing_rules: Custom routing rules mapping route name to keywords.
                          If None, uses DEFAULT_ROUTING_RULES.
            knowledge_service: Optional knowledge service for auto-answer capability.
            auto_answer_threshold: Confidence threshold for auto-answering (0-1).
                                  Higher values require more keyword matches.
        """
        self._tickets: dict[str, QuestionTicket] = {}
        self._routing_history: list[dict[str, Any]] = []
        self._routing_rules = routing_rules if routing_rules is not None else self.DEFAULT_ROUTING_RULES.copy()
        self._knowledge_service = knowledge_service
        self._auto_answer_threshold = auto_answer_threshold
        self._auto_answer_history: list[dict[str, Any]] = []

    def ask(
        self,
        question: str,
        context: str = "",
        priority: Priority = Priority.MEDIUM,
        asker: str = "ai",
    ) -> QuestionTicket:
        """
        Submit a question. Routes automatically and returns ticket.
        """
        ticket = QuestionTicket(
            id=f"q-{uuid.uuid4().hex[:8]}",
            question=question,
            context=context,
            priority=priority,
            asker=asker,
            status="open",
        )

        # Route the question
        routed_to = self._determine_route(ticket)
        ticket.routed_to = routed_to
        ticket.routing_reason = self._get_routing_reason(ticket, routed_to)

        # Record routing decision
        self._routing_history.append({
            "ticket_id": ticket.id,
            "question": question,
            "routed_to": routed_to,
            "routing_reason": ticket.routing_reason,
            "priority": priority.name,
            "timestamp": datetime.now().isoformat(),
        })

        self._tickets[ticket.id] = ticket
        return ticket

    def answer(
        self,
        ticket_id: str,
        answer: str,
        answered_by: str = "human",
    ) -> QuestionTicket:
        """Record an answer to a question."""
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            raise ValueError(f"Unknown ticket: {ticket_id}")

        ticket.answer = answer
        ticket.answered_by = answered_by
        ticket.answered_at = datetime.now()
        ticket.status = "answered"

        return ticket

    def get_pending(
        self,
        for_user: str | None = None,
        priority_filter: Priority | None = None,
    ) -> list[QuestionTicket]:
        """Get pending questions, optionally filtered."""
        pending = [t for t in self._tickets.values() if t.status == "open"]

        if for_user:
            pending = [t for t in pending if t.routed_to == for_user]

        if priority_filter:
            pending = [t for t in pending if t.priority == priority_filter]

        # Sort by priority (CRITICAL first)
        priority_order = {p: i for i, p in enumerate(Priority)}
        pending.sort(key=lambda t: priority_order.get(t.priority, 99))

        return pending

    def get_batched(self) -> dict[Priority, list[QuestionTicket]]:
        """
        Get questions batched by priority for efficient review.
        """
        batched = {p: [] for p in Priority}

        for ticket in self._tickets.values():
            if ticket.status == "open":
                batched[ticket.priority].append(ticket)

        return batched

    def try_auto_answer(self, ticket_id: str) -> bool:
        """
        Attempt to answer from knowledge base.

        Uses keyword matching to find relevant knowledge entries and
        calculates a confidence score based on match quality.

        Returns True if auto-answered, False if needs human.

        The auto-answer is recorded in the ticket with answered_by="auto"
        and can be verified or overridden by a human.
        """
        if not self._knowledge_service:
            return False

        ticket = self._tickets.get(ticket_id)
        if not ticket:
            return False

        # Search knowledge base for relevant entries
        results = self._knowledge_service.retrieve(
            query=ticket.question,
            limit=3,
        )

        if not results:
            self._record_auto_answer_attempt(ticket_id, False, 0.0, "No matching entries")
            return False

        # Calculate confidence based on keyword overlap
        question_words = set(ticket.question.lower().split())
        best_score = 0.0
        best_entry = None

        for entry in results:
            entry_words = set(entry.content.lower().split())
            # Calculate Jaccard-like similarity
            intersection = len(question_words & entry_words)
            union = len(question_words | entry_words)
            score = intersection / union if union > 0 else 0.0

            if score > best_score:
                best_score = score
                best_entry = entry

        if best_score >= self._auto_answer_threshold and best_entry:
            # Auto-answer with the best matching entry
            ticket.answer = f"[Auto-answered from knowledge base]\n\n{best_entry.content}"
            ticket.answered_by = "auto"
            ticket.answered_at = datetime.now()
            ticket.status = "auto_answered"  # Distinct status for verification
            ticket.validation_notes = f"Confidence: {best_score:.2%}, Source: {best_entry.id}"

            self._record_auto_answer_attempt(
                ticket_id, True, best_score,
                f"Matched entry {best_entry.id}"
            )
            return True

        self._record_auto_answer_attempt(
            ticket_id, False, best_score,
            f"Confidence {best_score:.2%} below threshold {self._auto_answer_threshold:.2%}"
        )
        return False

    def _record_auto_answer_attempt(
        self,
        ticket_id: str,
        success: bool,
        confidence: float,
        reason: str,
    ) -> None:
        """Record an auto-answer attempt for debugging and improvement."""
        self._auto_answer_history.append({
            "ticket_id": ticket_id,
            "success": success,
            "confidence": confidence,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        })

    def route(self, ticket_id: str) -> str:
        """
        Determine who should answer a question.

        Returns the routed_to value.
        """
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            return "human"

        return self._determine_route(ticket)

    def _determine_route(self, ticket: QuestionTicket) -> str:
        """
        Internal routing logic using configurable keyword matching.

        Routes based on question content keywords using the configured
        routing rules.

        Returns:
            The route name (e.g., "security-team") or "human" as default
        """
        question_lower = ticket.question.lower()

        # Check each route's keywords
        for route, keywords in self._routing_rules.items():
            if any(kw.lower() in question_lower for kw in keywords):
                return route

        return "human"  # Default to the user

    def _get_routing_reason(self, ticket: QuestionTicket, routed_to: str) -> str:
        """Generate a routing reason based on the routing decision."""
        if routed_to == "human":
            return "Default routing to human (no keyword matches)"

        # Find matching keywords for explanation
        question_lower = ticket.question.lower()
        keywords = self._routing_rules.get(routed_to, [])
        matched = [kw for kw in keywords if kw.lower() in question_lower]

        if matched:
            return f"Matched keywords for {routed_to}: {', '.join(matched)}"
        else:
            return f"Routed to {routed_to}"

    # =========================================================================
    # Query methods for test assertions
    # =========================================================================

    def get_all_tickets(self) -> list[QuestionTicket]:
        """
        Get all tickets in the system.

        Returns:
            List of all QuestionTicket instances, regardless of status.
        """
        return list(self._tickets.values())

    def get_ticket_by_id(self, ticket_id: str) -> QuestionTicket | None:
        """
        Get a specific ticket by its ID.

        Args:
            ticket_id: The ticket ID to look up.

        Returns:
            The QuestionTicket if found, None otherwise.
        """
        return self._tickets.get(ticket_id)

    def get_tickets_by_status(self, status: str) -> list[QuestionTicket]:
        """
        Get all tickets with a specific status.

        Args:
            status: The status to filter by (e.g., "open", "answered", "validated", "closed").

        Returns:
            List of QuestionTicket instances with the specified status.
        """
        return [t for t in self._tickets.values() if t.status == status]

    def get_routing_history(self) -> list[dict[str, Any]]:
        """
        Get the history of all routing decisions made.

        Returns:
            List of routing decision records, each containing:
            - ticket_id: ID of the ticket
            - question: The question text
            - routed_to: Who the question was routed to
            - routing_reason: Why it was routed there
            - priority: Priority level name
            - timestamp: When the routing decision was made
        """
        return list(self._routing_history)

    def get_tickets_by_route(self, routed_to: str) -> list[QuestionTicket]:
        """
        Get all tickets routed to a specific destination.

        Args:
            routed_to: The route to filter by (e.g., "security-team", "human")

        Returns:
            List of tickets routed to the specified destination
        """
        return [t for t in self._tickets.values() if t.routed_to == routed_to]

    def get_tickets_by_priority(self, priority: Priority) -> list[QuestionTicket]:
        """
        Get all tickets with a specific priority.

        Args:
            priority: The Priority enum value to filter by

        Returns:
            List of tickets with the specified priority
        """
        return [t for t in self._tickets.values() if t.priority == priority]

    def get_auto_answer_history(self) -> list[dict[str, Any]]:
        """
        Get the history of auto-answer attempts.

        Returns:
            List of auto-answer attempt records, each containing:
            - ticket_id: ID of the ticket
            - success: Whether auto-answer was successful
            - confidence: Confidence score (0-1)
            - reason: Explanation of the outcome
            - timestamp: When the attempt was made
        """
        return list(self._auto_answer_history)

    def get_answered_tickets(self) -> list[QuestionTicket]:
        """
        Get all tickets that have been answered.

        Returns:
            List of tickets with status "answered" or "auto_answered"
        """
        return [t for t in self._tickets.values() if t.status in ("answered", "auto_answered")]

    def get_auto_answered_tickets(self) -> list[QuestionTicket]:
        """
        Get all tickets that were auto-answered.

        Returns:
            List of tickets with status "auto_answered"
        """
        return [t for t in self._tickets.values() if t.status == "auto_answered"]

    def set_routing_rules(self, rules: dict[str, list[str]]) -> None:
        """
        Update the routing rules.

        Args:
            rules: New routing rules mapping route name to keywords
        """
        self._routing_rules = rules.copy()

    def add_routing_rule(self, route: str, keywords: list[str]) -> None:
        """
        Add or update a single routing rule.

        Args:
            route: The route name (e.g., "database-team")
            keywords: List of keywords that should route to this destination
        """
        self._routing_rules[route] = keywords.copy()

    def get_routing_rules(self) -> dict[str, list[str]]:
        """
        Get the current routing rules.

        Returns:
            Copy of the current routing rules dictionary
        """
        return {k: v.copy() for k, v in self._routing_rules.items()}

    def set_knowledge_service(self, service: KnowledgeService | None) -> None:
        """
        Set or update the knowledge service for auto-answer capability.

        Args:
            service: KnowledgeService instance, or None to disable auto-answer
        """
        self._knowledge_service = service

    def set_auto_answer_threshold(self, threshold: float) -> None:
        """
        Set the confidence threshold for auto-answering.

        Args:
            threshold: Value between 0 and 1. Higher values require better matches.
        """
        self._auto_answer_threshold = max(0.0, min(1.0, threshold))

    @property
    def ticket_count(self) -> int:
        """Get the total number of tickets."""
        return len(self._tickets)

    @property
    def pending_count(self) -> int:
        """Get the number of open tickets."""
        return len([t for t in self._tickets.values() if t.status == "open"])

    @property
    def answered_count(self) -> int:
        """Get the number of answered tickets (including auto-answered)."""
        return len([t for t in self._tickets.values() if t.status in ("answered", "auto_answered")])

    def clear(self) -> None:
        """
        Reset all state.

        Clears all tickets, routing history, and auto-answer history.
        Preserves routing rules and configuration. Useful for resetting
        state between tests.
        """
        self._tickets.clear()
        self._routing_history.clear()
        self._auto_answer_history.clear()


@dataclass
class IntentRecord:
    """A recorded intent for a project/chunk."""
    project_id: str
    chunk_id: str | None
    intent: str
    constraints: list[str]
    recorded_at: datetime = field(default_factory=datetime.now)


@dataclass
class FeedbackRecord:
    """A recorded feedback entry."""
    id: str
    target_type: str
    target_id: str
    feedback: str
    rating: int | None
    recorded_at: datetime = field(default_factory=datetime.now)


class InMemoryCommunicationService:
    """
    Testable in-memory communication service with query methods for assertions.

    Use when: You need a fully testable communication service that stores
    all data in memory and provides query methods for test assertions.

    This implementation:
    - Stores all handoff packages, intents, and feedback in memory
    - Provides query methods for retrieving stored data
    - Tracks resumption context per project
    - Supports clearing all state for test isolation

    Query methods for test assertions:
    - get_all_handoffs() -> list of all handoff packages
    - get_handoff_by_id(id) -> specific handoff or None
    - get_intents(project_id) -> list of intents for a project
    - get_feedback_history() -> list of all feedback records
    - clear() -> reset all state
    """

    def __init__(self) -> None:
        self._handoffs: dict[str, HandoffPackage] = {}
        self._intents: dict[str, list[IntentRecord]] = {}  # project_id -> list of intents
        self._feedback: list[FeedbackRecord] = []
        self._resumption_contexts: dict[str, str] = {}  # project_id -> context

    # =========================================================================
    # CommunicationService Protocol Implementation
    # =========================================================================

    def create_handoff(
        self,
        handoff_type: str,
        project_id: str,
        chunk_id: str | None = None,
    ) -> HandoffPackage:
        """
        Create a handoff package for context transfer.

        Stores the handoff in memory for later retrieval via get_handoff_by_id().
        """
        handoff = HandoffPackage(
            id=f"handoff-{uuid.uuid4().hex[:8]}",
            handoff_type=handoff_type,
            project_id=project_id,
            chunk_id=chunk_id or "",
        )

        # Populate from recorded intents if available
        project_intents = self._intents.get(project_id, [])
        if project_intents:
            latest_intent = project_intents[-1]
            handoff.intent = latest_intent.intent
            handoff.constraints = latest_intent.constraints.copy()

        self._handoffs[handoff.id] = handoff
        return handoff

    def get_resumption_context(self, project_id: str) -> str:
        """
        Generate human/AI-readable context for resuming work.

        Builds context from recorded intents and feedback.
        """
        lines = [
            f"# Resumption Context: {project_id}",
            f"Generated: {datetime.now().isoformat()}",
            "",
        ]

        # Include recorded intents
        project_intents = self._intents.get(project_id, [])
        if project_intents:
            latest_intent = project_intents[-1]
            lines.extend([
                "## Current Intent",
                latest_intent.intent,
                "",
            ])

            if latest_intent.constraints:
                lines.append("## Constraints")
                for constraint in latest_intent.constraints:
                    lines.append(f"- {constraint}")
                lines.append("")

            if len(project_intents) > 1:
                lines.append("## Intent History")
                for intent_record in project_intents[:-1]:
                    lines.append(f"- {intent_record.intent} (recorded: {intent_record.recorded_at.isoformat()})")
                lines.append("")

        # Include relevant feedback using exact project matching
        project_feedback = self._get_feedback_for_project(project_id)
        if project_feedback:
            lines.append("## Recent Feedback")
            for fb in project_feedback[-5:]:  # Last 5 feedback entries
                rating_str = f" (rating: {fb.rating})" if fb.rating is not None else ""
                lines.append(f"- [{fb.target_type}] {fb.feedback}{rating_str}")
            lines.append("")

        context = "\n".join(lines)
        self._resumption_contexts[project_id] = context
        return context

    def record_intent(
        self,
        project_id: str,
        chunk_id: str | None,
        intent: str,
        constraints: list[str],
    ) -> None:
        """
        Record the intent for current work.

        Stores intent in memory for retrieval via get_intents().
        """
        intent_record = IntentRecord(
            project_id=project_id,
            chunk_id=chunk_id,
            intent=intent,
            constraints=constraints.copy(),
        )

        if project_id not in self._intents:
            self._intents[project_id] = []
        self._intents[project_id].append(intent_record)

    def record_feedback(
        self,
        target_type: str,
        target_id: str,
        feedback: str,
        rating: int | None = None,
    ) -> None:
        """
        Record feedback on AI outputs.

        Stores feedback in memory for retrieval via get_feedback_history().
        """
        feedback_record = FeedbackRecord(
            id=f"feedback-{uuid.uuid4().hex[:8]}",
            target_type=target_type,
            target_id=target_id,
            feedback=feedback,
            rating=rating,
        )
        self._feedback.append(feedback_record)

    def compress_history(
        self,
        project_id: str,
        max_tokens: int = 4000,
        chars_per_token: float = 4.0,
    ) -> str:
        """
        Compress project history to fit in context window.

        Uses truncation with preservation of key sections.

        Args:
            project_id: The project to compress history for
            max_tokens: Maximum tokens to allow (default: 4000)
            chars_per_token: Character-to-token ratio for estimation (default: 4.0)
                           Use ~3.5 for code-heavy content, ~4.5 for prose

        Returns:
            Compressed context string that fits within token limit
        """
        context = self.get_resumption_context(project_id)

        # Calculate max characters based on configurable ratio
        max_chars = int(max_tokens * chars_per_token)

        if len(context) <= max_chars:
            return context

        # Try to preserve important sections by truncating middle content
        lines = context.split("\n")
        header_lines = []
        important_lines = []
        other_lines = []

        current_section = "header"
        for line in lines:
            if line.startswith("# ") or line.startswith("## "):
                if "Intent" in line or "Constraints" in line or "Blocked" in line:
                    current_section = "important"
                else:
                    current_section = "other"
                important_lines.append(line) if current_section == "important" else other_lines.append(line)
            elif current_section == "header" and line.strip():
                header_lines.append(line)
                if "Generated:" in line:
                    current_section = "other"
            elif current_section == "important":
                important_lines.append(line)
            else:
                other_lines.append(line)

        # Build compressed version
        result_lines = header_lines + [""] + important_lines

        # Add other content if space permits
        current_len = sum(len(line) + 1 for line in result_lines)
        for line in other_lines:
            if current_len + len(line) + 1 < max_chars - 100:
                result_lines.append(line)
                current_len += len(line) + 1
            else:
                break

        result = "\n".join(result_lines)

        if len(result) >= max_chars:
            # Still too long, do hard truncation
            result = result[:max_chars - 100]

        return result + "\n\n... (history compressed, see full context for details)"

    def _get_feedback_for_project(self, project_id: str) -> list[FeedbackRecord]:
        """
        Get feedback records for a project using proper matching.

        Matches feedback where:
        - target_id exactly equals project_id
        - target_id starts with "{project_id}/" (e.g., "proj1/chunk1")
        - target_id starts with "{project_id}:" (e.g., "proj1:task1")

        Args:
            project_id: The project ID to filter by

        Returns:
            List of matching feedback records
        """
        results = []
        for fb in self._feedback:
            target = fb.target_id
            if (target == project_id or
                target.startswith(f"{project_id}/") or
                target.startswith(f"{project_id}:")):
                results.append(fb)
        return results

    # =========================================================================
    # Query Methods for Test Assertions
    # =========================================================================

    def get_all_handoffs(self) -> list[HandoffPackage]:
        """
        Get all handoff packages.

        Returns:
            List of all handoff packages created, in no particular order.
        """
        return list(self._handoffs.values())

    def get_handoff_by_id(self, handoff_id: str) -> HandoffPackage | None:
        """
        Get a specific handoff package by ID.

        Args:
            handoff_id: The ID of the handoff to retrieve.

        Returns:
            The handoff package if found, None otherwise.
        """
        return self._handoffs.get(handoff_id)

    def get_intents(self, project_id: str) -> list[IntentRecord]:
        """
        Get all recorded intents for a project.

        Args:
            project_id: The project ID to get intents for.

        Returns:
            List of intent records for the project, in chronological order.
        """
        return self._intents.get(project_id, []).copy()

    def get_feedback_history(self) -> list[FeedbackRecord]:
        """
        Get all recorded feedback.

        Returns:
            List of all feedback records, in chronological order.
        """
        return self._feedback.copy()

    def get_feedback_for_project(self, project_id: str) -> list[FeedbackRecord]:
        """
        Get all feedback records for a specific project.

        This uses proper project matching (exact match or prefix with delimiter).

        Args:
            project_id: The project ID to filter by

        Returns:
            List of feedback records for the project
        """
        return self._get_feedback_for_project(project_id)

    def get_feedback_by_type(self, target_type: str) -> list[FeedbackRecord]:
        """
        Get all feedback records of a specific type.

        Args:
            target_type: The type to filter by (e.g., "chunk", "answer", "suggestion")

        Returns:
            List of feedback records matching the type
        """
        return [fb for fb in self._feedback if fb.target_type == target_type]

    def get_feedback_by_rating(
        self,
        min_rating: int | None = None,
        max_rating: int | None = None,
    ) -> list[FeedbackRecord]:
        """
        Get feedback records filtered by rating range.

        Args:
            min_rating: Minimum rating (inclusive), or None for no lower bound
            max_rating: Maximum rating (inclusive), or None for no upper bound

        Returns:
            List of feedback records with ratings in the specified range
        """
        results = []
        for fb in self._feedback:
            if fb.rating is None:
                continue
            if min_rating is not None and fb.rating < min_rating:
                continue
            if max_rating is not None and fb.rating > max_rating:
                continue
            results.append(fb)
        return results

    def get_latest_intent(self, project_id: str) -> IntentRecord | None:
        """
        Get the most recent intent for a project.

        Args:
            project_id: The project ID

        Returns:
            The latest IntentRecord if any exists, None otherwise
        """
        intents = self._intents.get(project_id, [])
        return intents[-1] if intents else None

    def get_handoffs_by_type(self, handoff_type: str) -> list[HandoffPackage]:
        """
        Get all handoffs of a specific type.

        Args:
            handoff_type: The type to filter by (e.g., "ai_to_human", "human_to_ai")

        Returns:
            List of handoff packages matching the type
        """
        return [h for h in self._handoffs.values() if h.handoff_type == handoff_type]

    def get_handoffs_for_project(self, project_id: str) -> list[HandoffPackage]:
        """
        Get all handoffs for a specific project.

        Args:
            project_id: The project ID to filter by

        Returns:
            List of handoff packages for the project
        """
        return [h for h in self._handoffs.values() if h.project_id == project_id]

    @property
    def handoff_count(self) -> int:
        """Get the total number of handoffs."""
        return len(self._handoffs)

    @property
    def feedback_count(self) -> int:
        """Get the total number of feedback records."""
        return len(self._feedback)

    @property
    def intent_count(self) -> int:
        """Get the total number of intent records across all projects."""
        return sum(len(intents) for intents in self._intents.values())

    def clear(self) -> None:
        """
        Reset all state.

        Clears all stored handoffs, intents, feedback, and resumption contexts.
        Useful for test isolation between test cases.
        """
        self._handoffs.clear()
        self._intents.clear()
        self._feedback.clear()
        self._resumption_contexts.clear()


# =============================================================================
# Simple Implementations (In-memory, basic logic)
# =============================================================================

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


class SimpleResourceService:
    """
    In-memory resource tracking.
    
    ESCAPE CLAUSE: Budgets reset on restart. For persistence:
    1. Store budgets in database
    2. Store consumption events for audit
    3. Implement alerts/notifications at thresholds
    """
    
    def __init__(self):
        # Key: (resource_type, scope_type, scope_id)
        self._budgets: dict[tuple, ResourceBudget] = {}
        self._consumption_log: list[dict[str, Any]] = []
    
    def set_budget(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
        unit: str = "",
    ) -> ResourceBudget:
        """Set budget for a scope. Creates or updates."""
        key = (resource_type, scope_type, scope_id)
        existing = self._budgets.get(key)
        
        budget = ResourceBudget(
            resource_type=resource_type,
            allocated=amount,
            consumed=existing.consumed if existing else 0.0,
            unit=unit,
        )
        self._budgets[key] = budget
        return budget
    
    def get_budget(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
    ) -> ResourceBudget | None:
        key = (resource_type, scope_type, scope_id)
        return self._budgets.get(key)
    
    def allocate(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
    ) -> bool:
        # ESCAPE CLAUSE: No parent budget checks
        # Real implementation should verify against org/portfolio limits too
        key = (resource_type, scope_type, scope_id)
        if key in self._budgets:
            self._budgets[key].allocated += amount
        else:
            self._budgets[key] = ResourceBudget(
                resource_type=resource_type,
                allocated=amount,
            )
        return True
    
    def consume(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
        description: str = "",
    ) -> bool:
        key = (resource_type, scope_type, scope_id)
        budget = self._budgets.get(key)
        
        if budget is None:
            # No budget = no limit, but track consumption
            self._budgets[key] = ResourceBudget(
                resource_type=resource_type,
                allocated=float('inf'),
                consumed=amount,
            )
        elif budget.consumed + amount > budget.allocated:
            # Would exceed budget
            # ESCAPE CLAUSE: Hard stop. Could implement soft limits.
            return False
        else:
            budget.consumed += amount
        
        # Log consumption
        self._consumption_log.append({
            "timestamp": datetime.now().isoformat(),
            "resource_type": resource_type.name,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "amount": amount,
            "description": description,
        })
        
        return True
    
    def check_available(
        self,
        resource_type: ResourceType,
        scope_type: str,
        scope_id: str,
        amount: float,
    ) -> tuple[bool, float]:
        budget = self.get_budget(resource_type, scope_type, scope_id)
        if budget is None:
            return True, float('inf')
        remaining = budget.remaining
        return amount <= remaining, remaining
    
    def get_consumption_report(
        self,
        scope_type: str,
        scope_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        relevant = [
            log for log in self._consumption_log
            if log["scope_type"] == scope_type and log["scope_id"] == scope_id
        ]
        
        # ESCAPE CLAUSE: Date filtering not implemented
        # Would need to parse timestamps
        
        by_resource: dict[str, float] = {}
        for log in relevant:
            rt = log["resource_type"]
            by_resource[rt] = by_resource.get(rt, 0) + log["amount"]
        
        return {
            "scope_type": scope_type,
            "scope_id": scope_id,
            "total_events": len(relevant),
            "by_resource": by_resource,
        }


class SimpleKnowledgeService:
    """
    In-memory knowledge base with keyword search.
    
    ESCAPE CLAUSE: This uses simple keyword matching.
    For production, implement semantic search:
    1. Use an embedding model (OpenAI, local model)
    2. Store embeddings in vector DB (Pinecone, Weaviate, pgvector)
    3. Hybrid search: keywords for exact match, semantic for concepts
    """
    
    def __init__(self, persist_path: str | None = None):
        self._entries: dict[str, KnowledgeEntry] = {}
        self._decisions: dict[str, Decision] = {}
        self._persist_path = Path(persist_path) if persist_path else None
        
        if self._persist_path and self._persist_path.exists():
            self._load()
    
    def store(self, entry: KnowledgeEntry) -> str:
        if not entry.id:
            entry.id = f"ke-{uuid.uuid4().hex[:8]}"
        self._entries[entry.id] = entry
        self._maybe_persist()
        return entry.id
    
    def retrieve(
        self,
        query: str,
        entry_types: list[str] | None = None,
        project_filter: str | None = None,
        limit: int = 5,
    ) -> list[KnowledgeEntry]:
        """
        Keyword-based retrieval.
        
        ESCAPE CLAUSE: This is O(n) scan with keyword matching.
        Production should use:
        - Inverted index for keywords
        - Vector similarity for semantic
        - Caching for frequent queries
        """
        query_terms = query.lower().split()
        
        results: list[tuple[float, KnowledgeEntry]] = []
        
        for entry in self._entries.values():
            # Filter by type
            if entry_types and entry.entry_type not in entry_types:
                continue
            
            # Filter by project
            if project_filter and entry.source_project != project_filter:
                continue
            
            # Score by keyword overlap
            content_lower = entry.content.lower()
            tag_text = " ".join(entry.tags).lower()
            full_text = f"{content_lower} {tag_text}"
            
            score = sum(1 for term in query_terms if term in full_text)
            
            if score > 0:
                results.append((score, entry))
        
        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)
        
        return [entry for score, entry in results[:limit]]
    
    def record_decision(self, decision: Decision) -> str:
        if not decision.id:
            decision.id = f"dec-{uuid.uuid4().hex[:8]}"
        
        self._decisions[decision.id] = decision
        
        # Also store as knowledge entry for retrieval
        entry = KnowledgeEntry(
            id=f"ke-{decision.id}",
            content=f"Decision: {decision.title}\n\nContext: {decision.context}\n\n"
                   f"Chosen: {decision.chosen}\n\nRationale: {decision.rationale}",
            entry_type="decision",
            source_project=decision.project_id,
            source_chunk=decision.chunk_id,
            tags=[decision.title] + decision.options,
        )
        self.store(entry)
        
        self._maybe_persist()
        return decision.id
    
    def find_contradictions(
        self,
        proposed_decision: str,
        project_id: str | None = None,
    ) -> list[Decision]:
        """
        ESCAPE CLAUSE: Not implemented - returns empty.
        
        To implement:
        1. Extract key claims from proposed decision
        2. Search for decisions with similar topics
        3. Use LLM to check for logical contradictions
        4. Return contradicting decisions with explanation
        """
        return []
    
    def get_patterns_for_problem(self, problem_description: str) -> list[KnowledgeEntry]:
        return self.retrieve(
            query=problem_description,
            entry_types=["pattern"],
        )
    
    def _maybe_persist(self) -> None:
        if self._persist_path:
            self._persist_path.mkdir(parents=True, exist_ok=True)
            
            data = {
                "entries": {k: self._entry_to_dict(v) for k, v in self._entries.items()},
                "decisions": {k: self._decision_to_dict(v) for k, v in self._decisions.items()},
            }
            
            with open(self._persist_path / "knowledge.json", "w") as f:
                json.dump(data, f, indent=2, default=str)
    
    def _load(self) -> None:
        path = self._persist_path / "knowledge.json"
        if not path.exists():
            return
        
        with open(path) as f:
            data = json.load(f)
        
        # ESCAPE CLAUSE: Deserialization is fragile
        # Would need proper schema validation in production
        for k, v in data.get("entries", {}).items():
            self._entries[k] = KnowledgeEntry(
                id=v["id"],
                content=v["content"],
                entry_type=v["entry_type"],
                source_project=v.get("source_project", ""),
                source_chunk=v.get("source_chunk", ""),
                tags=v.get("tags", []),
            )
    
    def _entry_to_dict(self, entry: KnowledgeEntry) -> dict:
        return {
            "id": entry.id,
            "content": entry.content,
            "entry_type": entry.entry_type,
            "source_project": entry.source_project,
            "source_chunk": entry.source_chunk,
            "tags": entry.tags,
        }
    
    def _decision_to_dict(self, decision: Decision) -> dict:
        return {
            "id": decision.id,
            "title": decision.title,
            "context": decision.context,
            "options": decision.options,
            "chosen": decision.chosen,
            "rationale": decision.rationale,
            "consequences": decision.consequences,
            "project_id": decision.project_id,
            "chunk_id": decision.chunk_id,
        }


class SimpleQuestionService:
    """
    In-memory question tracking with basic routing.
    
    ESCAPE CLAUSE: Routing is naive (everything goes to "human").
    Production routing needs:
    - Domain expert mapping
    - Code ownership data
    - Availability/on-call info
    - Knowledge base for auto-answers
    """
    
    def __init__(self, knowledge_service: KnowledgeService | None = None):
        self._tickets: dict[str, QuestionTicket] = {}
        self._knowledge = knowledge_service
    
    def ask(
        self,
        question: str,
        context: str = "",
        priority: Priority = Priority.MEDIUM,
        asker: str = "ai",
    ) -> QuestionTicket:
        ticket = QuestionTicket(
            id=f"q-{uuid.uuid4().hex[:8]}",
            question=question,
            context=context,
            priority=priority,
            asker=asker,
            status="open",
        )
        
        # Try auto-answer first
        if self._knowledge:
            results = self._knowledge.retrieve(question, limit=1)
            if results:
                # ESCAPE CLAUSE: No confidence scoring
                # We found something, but don't auto-answer without confidence
                ticket.routing_reason = f"Possible answer in knowledge base: {results[0].id}"
        
        # Route the question
        ticket.routed_to = self.route(ticket.id, ticket)
        
        self._tickets[ticket.id] = ticket
        return ticket
    
    def answer(
        self,
        ticket_id: str,
        answer: str,
        answered_by: str = "human",
    ) -> QuestionTicket:
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            raise ValueError(f"Unknown ticket: {ticket_id}")
        
        ticket.answer = answer
        ticket.answered_by = answered_by
        ticket.answered_at = datetime.now()
        ticket.status = "answered"
        
        return ticket
    
    def get_pending(
        self,
        for_user: str | None = None,
        priority_filter: Priority | None = None,
    ) -> list[QuestionTicket]:
        pending = [t for t in self._tickets.values() if t.status == "open"]
        
        if for_user:
            pending = [t for t in pending if t.routed_to == for_user]
        
        if priority_filter:
            pending = [t for t in pending if t.priority == priority_filter]
        
        # Sort by priority (CRITICAL first)
        priority_order = {p: i for i, p in enumerate(Priority)}
        pending.sort(key=lambda t: priority_order.get(t.priority, 99))
        
        return pending
    
    def get_batched(self) -> dict[Priority, list[QuestionTicket]]:
        batched = {p: [] for p in Priority}
        
        for ticket in self._tickets.values():
            if ticket.status == "open":
                batched[ticket.priority].append(ticket)
        
        return batched
    
    def try_auto_answer(self, ticket_id: str) -> bool:
        """
        ESCAPE CLAUSE: Always returns False.
        
        To implement:
        1. Search knowledge base for similar questions
        2. Compute confidence score
        3. If high confidence (>0.9), auto-answer and flag for verification
        4. If medium confidence, suggest answer to human
        5. If low confidence, route to human
        """
        return False
    
    def route(self, ticket_id: str, ticket: QuestionTicket | None = None) -> str:
        """
        ESCAPE CLAUSE: Routes everything to "human".
        
        To implement:
        1. Parse question for domain keywords
        2. Look up domain → expert mapping
        3. Check expert availability
        4. Fall back to general queue if no match
        """
        if ticket is None:
            ticket = self._tickets.get(ticket_id)
        
        if not ticket:
            return "human"
        
        # Simple keyword routing (placeholder)
        question_lower = ticket.question.lower()
        
        if any(kw in question_lower for kw in ["security", "auth", "permission"]):
            return "security-team"
        elif any(kw in question_lower for kw in ["requirement", "should we", "business"]):
            return "product-owner"
        elif any(kw in question_lower for kw in ["deploy", "infrastructure", "scaling"]):
            return "devops"
        else:
            return "human"  # Default to the user


class SimpleCommunicationService:
    """
    Basic communication service for context handoffs.
    
    ESCAPE CLAUSE: Intent and feedback storage is in-memory only.
    Production needs:
    - Persistent storage
    - Integration with project system for context gathering
    - LLM-based history compression
    """
    
    def __init__(
        self,
        project_service: ProjectManagementService | None = None,
        knowledge_service: KnowledgeService | None = None,
        question_service: QuestionService | None = None,
    ):
        self._project_service = project_service
        self._knowledge_service = knowledge_service
        self._question_service = question_service
        
        self._intents: dict[str, dict[str, Any]] = {}  # project_id -> intent
        self._feedback: list[dict[str, Any]] = []
        self._handoffs: dict[str, HandoffPackage] = {}
    
    def create_handoff(
        self,
        handoff_type: str,
        project_id: str,
        chunk_id: str | None = None,
    ) -> HandoffPackage:
        handoff = HandoffPackage(
            id=f"handoff-{uuid.uuid4().hex[:8]}",
            handoff_type=handoff_type,
            project_id=project_id,
            chunk_id=chunk_id or "",
        )
        
        # Gather context from intent
        intent_data = self._intents.get(project_id, {})
        handoff.intent = intent_data.get("intent", "")
        handoff.constraints = intent_data.get("constraints", [])
        
        # Gather blocked items
        if self._project_service:
            blocked = self._project_service.get_blocked_items(project_id)
            handoff.blockers = [b.get("name", str(b)) for b in blocked]
        
        # Gather open questions
        if self._question_service:
            pending = self._question_service.get_pending()
            handoff.open_questions = [q.question for q in pending[:5]]
        
        # Gather recent decisions
        if self._knowledge_service:
            decisions = self._knowledge_service.retrieve(
                query=project_id,
                entry_types=["decision"],
                limit=5,
            )
            handoff.key_decisions = [d.content[:200] for d in decisions]
        
        self._handoffs[handoff.id] = handoff
        return handoff
    
    def get_resumption_context(self, project_id: str) -> str:
        """
        Generate resumption context.
        
        ESCAPE CLAUSE: This is a simplified version.
        Ideally would pull from CollaborativeProject.get_resumption_context()
        and augment with cross-service information.
        """
        lines = [
            f"# Resumption Context: {project_id}",
            f"Generated: {datetime.now().isoformat()}",
            "",
        ]
        
        # Intent
        intent_data = self._intents.get(project_id, {})
        if intent_data:
            lines.extend([
                "## Intent",
                intent_data.get("intent", "Not recorded"),
                "",
                "## Constraints",
            ])
            for c in intent_data.get("constraints", []):
                lines.append(f"- {c}")
            lines.append("")
        
        # Blocked items
        if self._project_service:
            blocked = self._project_service.get_blocked_items(project_id)
            if blocked:
                lines.extend(["## Blocked", ""])
                for b in blocked:
                    lines.append(f"- {b.get('name', str(b))}")
                lines.append("")
        
        # Open questions
        if self._question_service:
            pending = self._question_service.get_pending()
            if pending:
                lines.extend(["## Open Questions", ""])
                for q in pending[:5]:
                    lines.append(f"- [{q.priority.name}] {q.question}")
                lines.append("")
        
        return "\n".join(lines)
    
    def record_intent(
        self,
        project_id: str,
        chunk_id: str | None,
        intent: str,
        constraints: list[str],
    ) -> None:
        self._intents[project_id] = {
            "intent": intent,
            "constraints": constraints,
            "chunk_id": chunk_id,
            "recorded_at": datetime.now().isoformat(),
        }
    
    def record_feedback(
        self,
        target_type: str,
        target_id: str,
        feedback: str,
        rating: int | None = None,
    ) -> None:
        """
        ESCAPE CLAUSE: Feedback is stored but not used.
        
        To make feedback actionable:
        1. Aggregate feedback by type/target
        2. Surface patterns (e.g., "chunks often underestimated")
        3. Adjust behavior based on feedback (e.g., increase estimates)
        4. Flag repeated negative feedback for human review
        """
        self._feedback.append({
            "target_type": target_type,
            "target_id": target_id,
            "feedback": feedback,
            "rating": rating,
            "recorded_at": datetime.now().isoformat(),
        })
    
    def compress_history(
        self,
        project_id: str,
        max_tokens: int = 4000,
    ) -> str:
        """
        ESCAPE CLAUSE: Compression is truncation, not summarization.
        
        For real compression:
        1. Use LLM to summarize each phase
        2. Keep recent items in full, older items summarized
        3. Preserve key decisions verbatim
        4. Include links to full history
        """
        context = self.get_resumption_context(project_id)
        
        # Rough token estimate (4 chars per token)
        max_chars = max_tokens * 4
        
        if len(context) <= max_chars:
            return context
        
        # Truncate with notice
        truncated = context[:max_chars - 100]
        return truncated + "\n\n... (truncated, see full history for details)"
