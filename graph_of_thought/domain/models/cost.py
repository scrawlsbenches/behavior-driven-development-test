"""
Domain models for Cost Management capability.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional

from graph_of_thought.domain.enums import BudgetLevel, BudgetStatus


@dataclass
class Budget:
    """A token/cost budget for a project or team."""
    id: str
    name: str
    project: str = ""
    team: str = ""
    allocated: float = 0.0
    consumed: float = 0.0
    unit: str = "tokens"
    status: BudgetStatus = BudgetStatus.ACTIVE
    warning_threshold: float = 0.8  # Warn at 80% consumption
    hard_limit: bool = True  # Stop work when exhausted
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def remaining(self) -> float:
        return self.allocated - self.consumed

    @property
    def percent_used(self) -> float:
        if self.allocated == 0:
            return 0.0
        return (self.consumed / self.allocated) * 100

    @property
    def level(self) -> BudgetLevel:
        percent = self.percent_used
        if percent >= 100:
            return BudgetLevel.EXHAUSTED
        elif percent >= 90:
            return BudgetLevel.CRITICAL
        elif percent >= self.warning_threshold * 100:
            return BudgetLevel.WARNING
        return BudgetLevel.NORMAL


@dataclass
class ConsumptionRecord:
    """Record of resource consumption."""
    id: str
    budget_id: str
    amount: float
    operation: str = ""
    user: str = ""
    project: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AllocationRecord:
    """Record of budget allocation or adjustment."""
    id: str
    budget_id: str
    amount: float
    allocation_type: str = "initial"  # initial, increase, decrease, transfer
    reason: str = ""
    approved_by: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BudgetWarning:
    """Warning about budget status."""
    id: str
    budget_id: str
    level: BudgetLevel
    message: str
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
