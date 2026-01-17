"""
Shared domain models used across multiple business capabilities.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from graph_of_thought.domain.enums import ResourceType


@dataclass
class User:
    """A user in the system."""
    id: str
    name: str
    role: str
    email: str = ""
    team: str = ""


@dataclass
class ResourceBudget:
    """Budget for a specific resource type."""
    resource_type: ResourceType
    allocated: float
    consumed: float = 0.0
    unit: str = ""  # "tokens", "minutes", "dollars", etc.

    @property
    def remaining(self) -> float:
        return self.allocated - self.consumed

    @property
    def percent_used(self) -> float:
        if self.allocated == 0:
            return 0.0
        return (self.consumed / self.allocated) * 100

    def is_exhausted(self) -> bool:
        return self.consumed >= self.allocated
