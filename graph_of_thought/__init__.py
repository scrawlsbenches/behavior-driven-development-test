from __future__ import annotations
"""
Graph of Thought - A flexible reasoning framework.

Includes two layers:
1. Core GoT - Graph-based reasoning exploration (graph.py)
2. Collaborative Projects - Human-AI project collaboration facade (collaborative.py)

This package provides a graph-based structure for representing and
traversing reasoning processes, with support for:
- Multiple search strategies (beam search, MCTS, iterative deepening)
- Pluggable LLM integration for thought generation and evaluation
- Persistence backends for checkpointing and storage
- Observability through metrics, logging, and tracing

Basic usage:
    ```python
    from graph_of_thought import GraphOfThought
    
    def evaluate(thought: str) -> float:
        return len(thought) / 100.0
    
    def generate(parent: str) -> list[str]:
        return [f"{parent} -> option A", f"{parent} -> option B"]
    
    graph = GraphOfThought[str](
        evaluator=evaluate,
        generator=generate,
    )
    
    root = graph.add_thought("Start")
    result = await graph.beam_search()
    print(result.best_path)
    ```

With LLM integration:
    ```python
    import anthropic
    from graph_of_thought import GraphOfThought
    from graph_of_thought.llm import ClaudeGenerator, ClaudeEvaluator
    
    client = anthropic.AsyncAnthropic()
    
    graph = GraphOfThought[str](
        generator=ClaudeGenerator(client),
        evaluator=ClaudeEvaluator(client),
    )
    
    root = graph.add_thought("How can I improve my Python code quality?")
    result = await graph.beam_search()
    ```
"""

__version__ = "0.1.0"

# Core types
from .core import (
    # Data types
    Thought,
    ThoughtStatus,
    Edge,
    SearchResult,
    SearchContext,
    
    # Protocols
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
    
    # Exceptions
    GraphError,
    NodeNotFoundError,
    CycleDetectedError,
    ResourceExhaustedError,
    TimeoutError,
    GenerationError,
    EvaluationError,
    PersistenceError,
    ConfigurationError,
    
    # Configuration
    GraphConfig,
    ResourceLimits,
    SearchDefaults,
)

# Main graph class
from .graph import GraphOfThought

# Default implementations
from .core.defaults import (
    FunctionGenerator,
    FunctionEvaluator,
    ConstantEvaluator,
    NoOpVerifier,
    NullMetricsCollector,
    InMemoryMetricsCollector,
    StandardLogger,
    NullLogger,
    NullTracingProvider,
    SimpleResourceLimiter,
    SimpleEventEmitter,
    LoggingEventHandler,
)

# Collaborative project facade
from .collaborative import (
    CollaborativeProject,
    ProjectNode,
    NodeType,
    ChunkStatus,
    QuestionPriority,
    RelationType,
    SessionContext,
)

__all__ = [
    # Version
    "__version__",
    
    # Main class
    "GraphOfThought",
    
    # Collaborative project facade
    "CollaborativeProject",
    "ProjectNode",
    "NodeType",
    "ChunkStatus",
    "QuestionPriority",
    "RelationType",
    "SessionContext",
    
    # Core types
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
    
    # Configuration
    "GraphConfig",
    "ResourceLimits",
    "SearchDefaults",
    
    # Default implementations
    "FunctionGenerator",
    "FunctionEvaluator",
    "ConstantEvaluator",
    "NoOpVerifier",
    "NullMetricsCollector",
    "InMemoryMetricsCollector",
    "StandardLogger",
    "NullLogger",
    "NullTracingProvider",
    "SimpleResourceLimiter",
    "SimpleEventEmitter",
    "LoggingEventHandler",
]
