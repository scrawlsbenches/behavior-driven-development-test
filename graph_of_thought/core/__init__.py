from __future__ import annotations
"""
Core types and protocols for Graph of Thought.
"""

from .types import (
    Thought,
    ThoughtStatus,
    Edge,
    SearchResult,
    SearchContext,
)

from .protocols import (
    ThoughtGenerator,
    ThoughtEvaluator,
    ThoughtVerifier,
    VerificationResult,
    GraphPersistence,
    IncrementalPersistence,
    MetricsCollector,
    TracingProvider,
    TraceSpan,
    Logger,
    SearchStrategy,
    SearchConfig,
    GoalPredicate,
    GraphOperations,
    ResourceLimiter,
    EventType,
    GraphEvent,
    EventHandler,
    EventEmitter,
)

from .exceptions import (
    GraphError,
    NodeNotFoundError,
    CycleDetectedError,
    ResourceExhaustedError,
    TimeoutError,
    GenerationError,
    EvaluationError,
    PersistenceError,
    ConfigurationError,
)

from .config import (
    GraphConfig,
    ResourceLimits,
    SearchDefaults,
)

__all__ = [
    # Types
    "Thought",
    "ThoughtStatus",
    "Edge",
    "SearchResult",
    "SearchContext",
    # Protocols
    "ThoughtGenerator",
    "ThoughtEvaluator",
    "ThoughtVerifier",
    "VerificationResult",
    "GraphPersistence",
    "IncrementalPersistence",
    "MetricsCollector",
    "TracingProvider",
    "TraceSpan",
    "Logger",
    "SearchStrategy",
    "SearchConfig",
    "GoalPredicate",
    "GraphOperations",
    "ResourceLimiter",
    "EventType",
    "GraphEvent",
    "EventHandler",
    "EventEmitter",
    # Exceptions
    "GraphError",
    "NodeNotFoundError",
    "CycleDetectedError",
    "ResourceExhaustedError",
    "TimeoutError",
    "GenerationError",
    "EvaluationError",
    "PersistenceError",
    "ConfigurationError",
    # Config
    "GraphConfig",
    "ResourceLimits",
    "SearchDefaults",
]
