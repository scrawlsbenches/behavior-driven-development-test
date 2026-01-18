from __future__ import annotations
"""
Core types and protocols for Graph of Thought.

Domain models and enums are imported from graph_of_thought.domain.
"""

from graph_of_thought.domain import (
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
    FileSystem,
)

from .defaults import (
    InMemoryFileSystem,
    RealFileSystem,
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
    "FileSystem",
    # FileSystem implementations
    "InMemoryFileSystem",
    "RealFileSystem",
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
