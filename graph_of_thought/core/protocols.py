"""
Protocol definitions for pluggable components.

These protocols define the interfaces that allow the Graph of Thought
to be extended with custom implementations for:
- Thought generation (LLM integration)
- Thought evaluation/scoring
- Persistence and checkpointing
- Observability (logging, metrics, tracing)
- Search strategies
"""

from __future__ import annotations
from typing import Protocol, TypeVar, Generic, Any, TYPE_CHECKING
from abc import abstractmethod

if TYPE_CHECKING:
    from .types import Thought, Edge, SearchResult, SearchContext

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)


# =============================================================================
# Thought Generation Protocols
# =============================================================================

class ThoughtGenerator(Protocol[T]):
    """
    Protocol for generating child thoughts from a parent.
    
    Implement this to integrate with LLMs or other generation systems.
    """
    
    async def generate(
        self,
        parent: T,
        context: SearchContext[T],
    ) -> list[T]:
        """
        Generate child thought contents from a parent thought.
        
        Args:
            parent: The parent thought content
            context: Search context with path history and budget info
            
        Returns:
            List of generated child thought contents
        """
        ...


class ThoughtEvaluator(Protocol[T]):
    """
    Protocol for scoring/evaluating thoughts.
    
    Implement this to integrate with LLMs or custom scoring functions.
    """
    
    async def evaluate(
        self,
        content: T,
        context: SearchContext[T],
    ) -> float:
        """
        Evaluate a thought and return a score.
        
        Args:
            content: The thought content to evaluate
            context: Search context with path history
            
        Returns:
            Score value (higher = better, typically 0.0 to 1.0)
        """
        ...


class ThoughtVerifier(Protocol[T]):
    """
    Protocol for verifying/validating generated thoughts.
    
    Implement this for self-consistency checks, fact verification, etc.
    """
    
    async def verify(
        self,
        content: T,
        context: SearchContext[T],
    ) -> VerificationResult:
        """
        Verify a thought's validity.
        
        Args:
            content: The thought content to verify
            context: Search context with path history
            
        Returns:
            Verification result with validity and issues
        """
        ...


class VerificationResult:
    """Result of thought verification."""
    
    def __init__(
        self,
        is_valid: bool,
        confidence: float = 1.0,
        issues: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.is_valid = is_valid
        self.confidence = confidence
        self.issues = issues or []
        self.metadata = metadata or {}


# =============================================================================
# Persistence Protocols
# =============================================================================

class GraphPersistence(Protocol[T]):
    """
    Protocol for persisting graph state.
    
    Implement this for database storage, checkpointing, etc.
    """
    
    async def save_graph(
        self,
        graph_id: str,
        thoughts: dict[str, Thought[T]],
        edges: list[Edge],
        root_ids: list[str],
        metadata: dict[str, Any],
    ) -> None:
        """Save complete graph state."""
        ...
    
    async def load_graph(
        self,
        graph_id: str,
    ) -> tuple[dict[str, Thought[T]], list[Edge], list[str], dict[str, Any]] | None:
        """Load complete graph state. Returns None if not found."""
        ...
    
    async def save_checkpoint(
        self,
        graph_id: str,
        checkpoint_id: str,
        thoughts: dict[str, Thought[T]],
        edges: list[Edge],
        root_ids: list[str],
        search_state: dict[str, Any],
    ) -> None:
        """Save a search checkpoint for resume capability."""
        ...
    
    async def load_checkpoint(
        self,
        graph_id: str,
        checkpoint_id: str,
    ) -> tuple[dict[str, Thought[T]], list[Edge], list[str], dict[str, Any]] | None:
        """Load a search checkpoint. Returns None if not found."""
        ...
    
    async def delete_graph(self, graph_id: str) -> bool:
        """Delete a graph. Returns True if deleted, False if not found."""
        ...


class IncrementalPersistence(Protocol[T]):
    """
    Protocol for incremental persistence (append-only).
    
    More efficient for long-running searches than full saves.
    """
    
    async def append_thought(
        self,
        graph_id: str,
        thought: Thought[T],
    ) -> None:
        """Append a single thought to storage."""
        ...
    
    async def append_edge(
        self,
        graph_id: str,
        edge: Edge,
    ) -> None:
        """Append a single edge to storage."""
        ...
    
    async def update_thought_status(
        self,
        graph_id: str,
        thought_id: str,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update a thought's status."""
        ...


# =============================================================================
# Observability Protocols
# =============================================================================

class MetricsCollector(Protocol):
    """
    Protocol for collecting metrics.
    
    Implement this for Prometheus, StatsD, CloudWatch, etc.
    """
    
    def increment(
        self,
        metric: str,
        value: int = 1,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Increment a counter metric."""
        ...
    
    def gauge(
        self,
        metric: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge metric."""
        ...
    
    def histogram(
        self,
        metric: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Record a histogram value."""
        ...
    
    def timing(
        self,
        metric: str,
        value_ms: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Record a timing in milliseconds."""
        ...


class TracingProvider(Protocol):
    """
    Protocol for distributed tracing.
    
    Implement this for OpenTelemetry, Jaeger, etc.
    """
    
    def start_span(
        self,
        name: str,
        parent_span: Any | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> TraceSpan:
        """Start a new trace span."""
        ...


class TraceSpan(Protocol):
    """Protocol for a trace span."""
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the span."""
        ...
    
    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add an event to the span."""
        ...
    
    def set_status(self, status: str, description: str | None = None) -> None:
        """Set the span status."""
        ...
    
    def end(self) -> None:
        """End the span."""
        ...
    
    def __enter__(self) -> TraceSpan:
        ...
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        ...


class Logger(Protocol):
    """
    Protocol for structured logging.
    
    Implement this for structlog, loguru, standard logging, etc.
    """
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log at DEBUG level."""
        ...
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log at INFO level."""
        ...
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log at WARNING level."""
        ...
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log at ERROR level."""
        ...
    
    def bind(self, **kwargs: Any) -> Logger:
        """Return a new logger with bound context."""
        ...


# =============================================================================
# Search Strategy Protocol
# =============================================================================

class SearchStrategy(Protocol[T]):
    """
    Protocol for search algorithms.
    
    Implement this for custom search strategies like MCTS, A*, etc.
    """
    
    async def search(
        self,
        graph: GraphOperations[T],
        generator: ThoughtGenerator[T],
        evaluator: ThoughtEvaluator[T],
        config: SearchConfig,
        goal: GoalPredicate[T] | None = None,
    ) -> SearchResult[T]:
        """
        Execute the search strategy.
        
        Args:
            graph: Graph operations interface
            generator: Thought generator
            evaluator: Thought evaluator
            config: Search configuration
            goal: Optional goal predicate for early termination
            
        Returns:
            Search result with best path and statistics
        """
        ...


class GoalPredicate(Protocol[T]):
    """Protocol for goal checking."""
    
    def __call__(self, content: T) -> bool:
        """Return True if the content satisfies the goal."""
        ...


class SearchConfig:
    """Configuration for search operations."""
    
    def __init__(
        self,
        max_depth: int = 10,
        beam_width: int = 3,
        max_expansions: int = 100,
        max_tokens: int | None = None,
        timeout_seconds: float | None = None,
        checkpoint_interval: int | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.max_depth = max_depth
        self.beam_width = beam_width
        self.max_expansions = max_expansions
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.checkpoint_interval = checkpoint_interval
        self.metadata = metadata or {}


# =============================================================================
# Graph Operations Protocol (for search strategies)
# =============================================================================

class GraphOperations(Protocol[T]):
    """
    Protocol defining graph operations available to search strategies.
    
    This abstracts the graph structure so search strategies don't need
    direct access to internal graph state.
    """
    
    def get_thought(self, thought_id: str) -> Thought[T]:
        """Get a thought by ID."""
        ...
    
    def get_children(self, thought_id: str) -> list[Thought[T]]:
        """Get child thoughts."""
        ...
    
    def get_parents(self, thought_id: str) -> list[Thought[T]]:
        """Get parent thoughts."""
        ...
    
    def get_root_ids(self) -> list[str]:
        """Get root thought IDs."""
        ...
    
    def get_path_to_root(self, thought_id: str) -> list[Thought[T]]:
        """Get path from thought to root."""
        ...
    
    def add_thought(
        self,
        content: T,
        parent_id: str | None = None,
        score: float = 0.0,
        tokens_used: int = 0,
        generation_time_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> Thought[T]:
        """Add a new thought to the graph."""
        ...
    
    def update_thought_status(
        self,
        thought_id: str,
        status: str,
    ) -> None:
        """Update a thought's status."""
        ...
    
    def get_leaves(self) -> list[Thought[T]]:
        """Get all leaf thoughts."""
        ...
    
    def thought_count(self) -> int:
        """Get total thought count."""
        ...


# =============================================================================
# Resource Management Protocol
# =============================================================================

class ResourceLimiter(Protocol):
    """
    Protocol for resource limit enforcement.
    
    Implement this for token budgets, rate limiting, etc.
    """
    
    async def acquire(
        self,
        resource_type: str,
        amount: int = 1,
    ) -> bool:
        """
        Attempt to acquire resources.
        
        Returns True if acquired, False if limit exceeded.
        """
        ...
    
    def release(
        self,
        resource_type: str,
        amount: int = 1,
    ) -> None:
        """Release previously acquired resources."""
        ...
    
    def get_remaining(self, resource_type: str) -> int | None:
        """Get remaining resource budget. None if unlimited."""
        ...
    
    def is_exhausted(self, resource_type: str) -> bool:
        """Check if a resource is exhausted."""
        ...


# =============================================================================
# Event System Protocol
# =============================================================================

class EventType:
    """Event types for the graph."""
    THOUGHT_ADDED = "thought_added"
    THOUGHT_EXPANDED = "thought_expanded"
    THOUGHT_PRUNED = "thought_pruned"
    THOUGHT_MERGED = "thought_merged"
    EDGE_ADDED = "edge_added"
    SEARCH_STARTED = "search_started"
    SEARCH_COMPLETED = "search_completed"
    CHECKPOINT_SAVED = "checkpoint_saved"
    GOAL_REACHED = "goal_reached"


class GraphEvent(Generic[T]):
    """Event emitted by the graph."""
    
    def __init__(
        self,
        event_type: str,
        thought: Thought[T] | None = None,
        edge: Edge | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.event_type = event_type
        self.thought = thought
        self.edge = edge
        self.metadata = metadata or {}


class EventHandler(Protocol[T]):
    """Protocol for handling graph events."""
    
    async def handle(self, event: GraphEvent[T]) -> None:
        """Handle a graph event."""
        ...


class EventEmitter(Protocol[T]):
    """Protocol for event emission."""
    
    def subscribe(self, handler: EventHandler[T]) -> None:
        """Subscribe to events."""
        ...
    
    def unsubscribe(self, handler: EventHandler[T]) -> None:
        """Unsubscribe from events."""
        ...
    
    async def emit(self, event: GraphEvent[T]) -> None:
        """Emit an event to all subscribers."""
        ...
