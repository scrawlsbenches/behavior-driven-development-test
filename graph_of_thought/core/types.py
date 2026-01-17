"""
Core types and data structures for Graph of Thought.

NOTE: This module re-exports from graph_of_thought.domain for backwards compatibility.
New code should import directly from graph_of_thought.domain.
"""

from typing import TypeVar

# Re-export from domain layer for backwards compatibility
from graph_of_thought.domain.enums import ThoughtStatus
from graph_of_thought.domain.models import (
    Thought,
    Edge,
    SearchResult,
    SearchContext,
)

T = TypeVar("T")

__all__ = [
    "T",
    "ThoughtStatus",
    "Thought",
    "Edge",
    "SearchResult",
    "SearchContext",
]
