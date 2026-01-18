"""
Service Protocols - Contracts for Capabilities
==============================================

This file defines WHAT services can do, not HOW they do it.
It's the contract between the application and its capabilities.

WHY PROTOCOLS MATTER
--------------------

Protocols enable the Dependency Inversion Principle:

    HIGH-LEVEL MODULES (search algorithms)
           │
           ▼ depend on
    ABSTRACTIONS (these protocols)
           ▲
           │ implemented by
    LOW-LEVEL MODULES (LLM clients, file systems)

This means:
- Search doesn't know about OpenAI
- Persistence doesn't know about PostgreSQL
- We can swap implementations without changing business logic

PROTOCOL DESIGN GUIDELINES
--------------------------

1. MINIMAL SURFACE AREA
   Only define what's actually needed. Don't add methods "just in case."

2. SINGLE RESPONSIBILITY
   Each protocol does one thing. Logger logs. Generator generates.

3. CONTEXT PARAMETER
   Most methods take a Context. This provides tracing, user info, etc.
   without requiring the service to know about these concerns.

4. ASYNC BY DEFAULT
   Even if implementation is sync, define as async. Allows future
   optimization without changing contracts.

5. GENERIC TYPES
   Use TypeVar for content types. This allows typed thoughts:
   Generator[str] generates string thoughts.
   Generator[dict] generates structured thoughts.

"""

from typing import Protocol, TypeVar, Any, Generic, runtime_checkable
from graph_of_thought_v2.core import Thought, Graph

# Generic type for thought content
T = TypeVar("T")


# =============================================================================
# CORE SERVICES - Required for search
# =============================================================================

@runtime_checkable
class Generator(Protocol[T]):
    """
    Protocol for thought generation.

    A Generator creates new thought content from an existing thought.
    This is the "creative" part of reasoning - producing new ideas.

    The generator doesn't create Thought objects - it returns raw content.
    The search algorithm wraps content in Thoughts and adds to the graph.

    Why raw content, not Thoughts?
    - Generator doesn't assign IDs (that's the graph's job)
    - Generator doesn't assign scores (that's the evaluator's job)
    - Separation of concerns

    Implementations:
    - LLMGenerator: Uses language models to generate ideas
    - RulesGenerator: Uses domain rules to derive conclusions
    - HybridGenerator: Combines multiple strategies

    Example:
        class MyGenerator:
            async def generate(self, thought, context):
                # Maybe call an LLM
                response = await self.llm.complete(
                    f"Given: {thought.content}\\nGenerate 3 follow-up ideas:"
                )
                return parse_ideas(response)
    """

    async def generate(
        self,
        thought: Thought[T],
        context: Any,  # Actually Context, but avoiding circular import
    ) -> list[T]:
        """
        Generate child content from a parent thought.

        Args:
            thought: The thought to expand (parent).
            context: Execution context with budget, config, etc.

        Returns:
            List of content for child thoughts.
            Empty list means no children (leaf node).

        Note:
            This method may have side effects (LLM calls, API requests).
            Track token usage via context.consume_budget() in implementation.
        """
        ...


@runtime_checkable
class Evaluator(Protocol[T]):
    """
    Protocol for thought evaluation.

    An Evaluator scores a thought, indicating how promising it is.
    Higher scores = more likely to lead to a good solution.

    Scores should be between 0.0 and 1.0:
    - 0.0: This thought is worthless, don't explore further
    - 0.5: Neutral, neither good nor bad
    - 1.0: Perfect, this is the solution

    The evaluator receives the full Thought (not just content) so it can:
    - See the thought's current score (for refinement)
    - Access any metadata
    - Make relative comparisons

    Implementations:
    - LLMEvaluator: Uses language models to judge quality
    - HeuristicEvaluator: Uses rules and patterns
    - CompositeEvaluator: Combines multiple evaluators

    Example:
        class MyEvaluator:
            async def evaluate(self, thought, context):
                # Maybe call an LLM
                response = await self.llm.complete(
                    f"Rate this idea 0-10: {thought.content}"
                )
                return parse_score(response) / 10.0
    """

    async def evaluate(
        self,
        thought: Thought[T],
        context: Any,  # Actually Context
    ) -> float:
        """
        Score a thought.

        Args:
            thought: The thought to evaluate.
            context: Execution context with budget, config, etc.

        Returns:
            Score from 0.0 (worthless) to 1.0 (perfect).

        Note:
            This method may have side effects (LLM calls, API requests).
            Track token usage via context.consume_budget() in implementation.
        """
        ...


# =============================================================================
# INFRASTRUCTURE SERVICES - Cross-cutting concerns
# =============================================================================

@runtime_checkable
class Logger(Protocol):
    """
    Protocol for structured logging.

    Loggers record what happened during operations. They support:
    - Levels (debug, info, warning, error)
    - Structured data (key-value pairs)
    - Context binding (add fields to all subsequent logs)

    Why structured logging?
    - Machine-parseable (can query logs)
    - Consistent format
    - Correlation via trace_id

    Implementations:
    - StructuredLogger: JSON output to stdout/stderr
    - InMemoryLogger: Stores logs in memory (for testing)
    - CompositeLogger: Sends to multiple destinations

    Example:
        logger.info("Search started", depth=5, budget=10000)
        logger.error("Generation failed", error=str(e), thought_id=t.id)
    """

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug-level message with structured data."""
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info-level message with structured data."""
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning-level message with structured data."""
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error-level message with structured data."""
        ...

    def bind(self, **kwargs: Any) -> "Logger":
        """
        Create a child logger with bound context.

        All logs from the child will include the bound fields.

        Example:
            request_logger = logger.bind(request_id="abc", user="alice")
            request_logger.info("Processing")  # Includes request_id and user
        """
        ...


@runtime_checkable
class MetricsCollector(Protocol):
    """
    Protocol for metrics collection.

    Metrics track measurements over time:
    - Counters (things that only go up)
    - Gauges (current values)
    - Histograms (distributions)

    Why metrics?
    - Performance monitoring
    - Alerting
    - Capacity planning

    Implementations:
    - PrometheusMetrics: Exports to Prometheus
    - InMemoryMetrics: Stores in memory (for testing)
    - StatsdMetrics: Sends to StatsD

    Example:
        metrics.increment("thoughts.expanded", tags={"project": "foo"})
        metrics.gauge("budget.remaining", 5000)
        metrics.histogram("search.duration_ms", 1234)
    """

    def increment(self, name: str, value: int = 1, **tags: str) -> None:
        """Increment a counter."""
        ...

    def gauge(self, name: str, value: float, **tags: str) -> None:
        """Set a gauge to a value."""
        ...

    def histogram(self, name: str, value: float, **tags: str) -> None:
        """Record a value in a histogram."""
        ...


@runtime_checkable
class Persistence(Protocol[T]):
    """
    Protocol for graph persistence.

    Persistence saves and loads graphs. It doesn't know about the
    graph's internal structure - it treats graphs as opaque objects.

    Why persistence as a service?
    - Graphs can be large (memory concerns)
    - Graphs need to survive restarts
    - Graphs can be shared across sessions

    Implementations:
    - FilePersistence: Saves to JSON files
    - DatabasePersistence: Saves to PostgreSQL/SQLite
    - InMemoryPersistence: Keeps in memory (for testing)
    - CloudPersistence: Saves to S3/GCS

    Example:
        graph_id = await persistence.save(graph, context)
        loaded = await persistence.load(graph_id, context)
    """

    async def save(
        self,
        graph: Graph[T],
        context: Any,  # Actually Context
    ) -> str:
        """
        Save a graph and return its ID.

        Args:
            graph: The graph to save.
            context: Execution context (for user, project, etc.).

        Returns:
            ID that can be used to load the graph later.
        """
        ...

    async def load(
        self,
        graph_id: str,
        context: Any,  # Actually Context
    ) -> Graph[T] | None:
        """
        Load a graph by ID.

        Args:
            graph_id: ID returned from save().
            context: Execution context.

        Returns:
            The graph, or None if not found.
        """
        ...

    async def delete(
        self,
        graph_id: str,
        context: Any,  # Actually Context
    ) -> bool:
        """
        Delete a graph by ID.

        Args:
            graph_id: ID of graph to delete.
            context: Execution context.

        Returns:
            True if deleted, False if not found.
        """
        ...

    async def list_graphs(
        self,
        context: Any,  # Actually Context
    ) -> list[str]:
        """
        List all graph IDs accessible in this context.

        Args:
            context: Execution context (filters by user/project).

        Returns:
            List of graph IDs.
        """
        ...


# =============================================================================
# DOMAIN SERVICES - Business capabilities (stubs for future)
# =============================================================================

@runtime_checkable
class KnowledgeService(Protocol):
    """
    Protocol for knowledge queries.

    Knowledge service provides historical context:
    - Past decisions and their outcomes
    - Patterns that worked or failed
    - Domain-specific facts

    This is NOT part of the graph - it's external knowledge that
    can inform generation and evaluation.

    Example:
        facts = await knowledge.query("database optimization", context)
        # Returns: ["Indexing improved query time by 80%", ...]
    """

    async def query(
        self,
        question: str,
        context: Any,
    ) -> list[str]:
        """Query for relevant knowledge."""
        ...

    async def record(
        self,
        fact: str,
        context: Any,
    ) -> None:
        """Record a new piece of knowledge."""
        ...


@runtime_checkable
class QuestionService(Protocol):
    """
    Protocol for managing blocking questions.

    When reasoning needs human input, it creates a question.
    The question blocks progress until answered.

    This handles the SLOW temporal domain (human response time)
    separately from the FAST domain (graph operations).

    Example:
        q_id = await questions.ask("Should we prioritize cost or speed?", ctx)
        # Later, human answers
        await questions.answer(q_id, "Prioritize speed", ctx)
        # Reasoning can now continue
    """

    async def ask(
        self,
        question: str,
        context: Any,
    ) -> str:
        """Ask a question, returns question ID."""
        ...

    async def answer(
        self,
        question_id: str,
        answer: str,
        context: Any,
    ) -> None:
        """Provide an answer to a question."""
        ...

    async def get_answer(
        self,
        question_id: str,
        context: Any,
    ) -> str | None:
        """Get the answer to a question, or None if unanswered."""
        ...
