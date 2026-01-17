"""
Resource Service Implementations.

Provides InMemoryResourceService (testable) and SimpleResourceService (basic).
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..protocols import (
    ResourceType,
    ResourceBudget,
)


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
