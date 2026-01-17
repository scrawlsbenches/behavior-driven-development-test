"""
Project Management Service Implementations.

Provides InMemoryProjectManagementService for testing.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any


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
