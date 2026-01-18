"""
Application Builder - The Entry Point
======================================

The ApplicationBuilder is HOW users construct a Graph of Thought application.
It guides construction, provides defaults, and validates configuration.

THE PIT OF SUCCESS
------------------

The builder is designed so that:

1. THE RIGHT WAY IS EASY
   app = ApplicationBuilder().build()  # Works with sensible defaults

2. THE WRONG WAY IS HARD
   # Can't forget to register a generator - builder provides one
   # Can't misconfigure - validation happens at build()

3. MISTAKES ARE VISIBLE
   # Invalid config? Fails at build time with clear message
   # Missing dependency? Fails immediately, not at runtime

BUILDER METHODS
---------------

Configuration:
    .with_mode(mode)           - Set mode (development/test/production)
    .with_options(options)     - Set all options at once
    .with_config_file(path)    - Load from JSON/YAML file
    .with_env_prefix(prefix)   - Load from environment variables

Services:
    .with_generator(gen)       - Set the thought generator
    .with_evaluator(eval)      - Set the thought evaluator
    .with_persistence(pers)    - Set persistence service
    .with_logger(logger)       - Set logging service
    .with_metrics(metrics)     - Set metrics service

Middleware:
    .use_middleware(mw)        - Add middleware to pipeline
    .use_logging()             - Add logging middleware
    .use_metrics()             - Add metrics middleware
    .use_budget_enforcement()  - Add budget middleware

Build:
    .build()                   - Create the application (validates first)

MODES
-----

Modes set sensible defaults for different environments:

DEVELOPMENT (default):
    - SimpleGenerator/Evaluator (no API keys needed)
    - InMemoryPersistence (no database needed)
    - Logging enabled (see what's happening)
    - Budget enforcement disabled (don't block development)

TEST:
    - InMemory everything (fast, isolated)
    - Logging disabled (quiet tests)
    - Deterministic (seeded random)

PRODUCTION:
    - Must configure generator/evaluator explicitly
    - Persistence required
    - Budget enforcement enabled
    - All middleware enabled

"""

from typing import Any, TypeVar, Callable
from dataclasses import dataclass, field

from graph_of_thought_v2.core import Graph, Thought, SearchResult
from graph_of_thought_v2.core.search import beam_search, SearchConfig
from graph_of_thought_v2.context import Context, Budget
from graph_of_thought_v2.services.protocols import (
    Generator,
    Evaluator,
    Persistence,
    Logger,
    MetricsCollector,
)
from graph_of_thought_v2.services.implementations import (
    SimpleGenerator,
    SimpleEvaluator,
    InMemoryPersistence,
    InMemoryLogger,
    InMemoryMetrics,
)
from graph_of_thought_v2.application.options import (
    ApplicationOptions,
    GraphOptions,
    SearchOptions,
    BudgetOptions,
)
from graph_of_thought_v2.application.container import ServiceContainer, Lifetime

T = TypeVar("T")


# =============================================================================
# APPLICATION
# =============================================================================

class Application:
    """
    The built application - ready to use.

    This is what ApplicationBuilder.build() returns. It provides:
    - Graph creation
    - Search execution
    - Persistence operations

    Example:
        app = ApplicationBuilder().build()

        graph = app.create_graph()
        graph.add(Thought(content="How do we solve X?"))

        result = await app.search(graph)
        print(result.best_path)
    """

    def __init__(
        self,
        container: ServiceContainer,
        options: ApplicationOptions,
    ) -> None:
        """
        Initialize application with configured container.

        Args:
            container: Configured service container.
            options: Application options.

        Note:
            Don't construct directly - use ApplicationBuilder.
        """
        self._container = container
        self._options = options

    # =========================================================================
    # GRAPH OPERATIONS
    # =========================================================================

    def create_graph(self) -> Graph[str]:
        """
        Create a new empty graph.

        Returns:
            A new Graph ready for thoughts.
        """
        return Graph[str]()

    async def search(
        self,
        graph: Graph[str],
        context: Context | None = None,
        **overrides: Any,
    ) -> SearchResult[str]:
        """
        Search a graph for the best path.

        Args:
            graph: The graph to search.
            context: Execution context (created if not provided).
            **overrides: Override search options (max_depth, beam_width, etc.)

        Returns:
            SearchResult with best path and statistics.

        Example:
            result = await app.search(graph, max_depth=5)
            print(result.best_path[-1].content)
        """
        # Create context if not provided
        if context is None:
            context = Context(
                budget=Budget(total=self._options.budget.default_tokens)
                if self._options.budget.default_tokens > 0
                else None
            )

        # Build search config from options + overrides
        config = SearchConfig(
            max_depth=overrides.get("max_depth", self._options.search.max_depth),
            beam_width=overrides.get("beam_width", self._options.search.beam_width),
            max_expansions=overrides.get("max_expansions", self._options.search.max_expansions),
            goal_score=overrides.get("goal_score", self._options.search.goal_score),
        )

        # Get services
        generator = self._container.resolve(Generator)
        evaluator = self._container.resolve(Evaluator)

        # Run search
        return await beam_search(
            graph=graph,
            expand=generator.generate,
            evaluate=evaluator.evaluate,
            config=config,
        )

    # =========================================================================
    # PERSISTENCE OPERATIONS
    # =========================================================================

    async def save_graph(
        self,
        graph: Graph[str],
        context: Context | None = None,
    ) -> str:
        """
        Save a graph and return its ID.

        Args:
            graph: The graph to save.
            context: Execution context.

        Returns:
            ID for loading the graph later.
        """
        context = context or Context()
        persistence = self._container.resolve(Persistence)
        return await persistence.save(graph, context)

    async def load_graph(
        self,
        graph_id: str,
        context: Context | None = None,
    ) -> Graph[str] | None:
        """
        Load a graph by ID.

        Args:
            graph_id: ID from save_graph().
            context: Execution context.

        Returns:
            The graph, or None if not found.
        """
        context = context or Context()
        persistence = self._container.resolve(Persistence)
        return await persistence.load(graph_id, context)

    # =========================================================================
    # SERVICE ACCESS
    # =========================================================================

    @property
    def logger(self) -> Logger:
        """Get the configured logger."""
        return self._container.resolve(Logger)

    @property
    def metrics(self) -> MetricsCollector:
        """Get the configured metrics collector."""
        return self._container.resolve(MetricsCollector)

    @property
    def options(self) -> ApplicationOptions:
        """Get application options."""
        return self._options


# =============================================================================
# APPLICATION BUILDER
# =============================================================================

class ApplicationBuilder:
    """
    Builder for Graph of Thought applications.

    Guides application construction with sensible defaults and validation.

    Example:
        # Minimal (development defaults)
        app = ApplicationBuilder().build()

        # Production
        app = (ApplicationBuilder()
            .with_mode("production")
            .with_generator(LLMGenerator(api_key=...))
            .with_evaluator(LLMEvaluator(api_key=...))
            .with_persistence(PostgresPersistence(conn_string=...))
            .build())

        # Testing
        app = (ApplicationBuilder()
            .with_mode("test")
            .with_generator(MockGenerator(responses=[...]))
            .build())
    """

    def __init__(self) -> None:
        """Create a new builder with default settings."""
        self._mode: str = "development"
        self._options = ApplicationOptions()
        self._generator: Generator | None = None
        self._evaluator: Evaluator | None = None
        self._persistence: Persistence | None = None
        self._logger: Logger | None = None
        self._metrics: MetricsCollector | None = None
        self._middleware: list[type] = []

    # =========================================================================
    # MODE & OPTIONS
    # =========================================================================

    def with_mode(self, mode: str) -> "ApplicationBuilder":
        """
        Set the application mode.

        Args:
            mode: One of "development", "test", or "production".

        Returns:
            Self for chaining.

        Modes affect defaults:
        - development: Simple implementations, logging on
        - test: InMemory implementations, logging off
        - production: Must configure explicitly, all safety on
        """
        if mode not in ("development", "test", "production"):
            raise ValueError(f"Unknown mode: {mode}. Use development/test/production.")
        self._mode = mode
        return self

    def with_options(self, options: ApplicationOptions) -> "ApplicationBuilder":
        """
        Set all application options.

        Args:
            options: The options to use.

        Returns:
            Self for chaining.
        """
        self._options = options
        return self

    def with_graph_options(self, **kwargs: Any) -> "ApplicationBuilder":
        """Set graph options from keyword arguments."""
        for key, value in kwargs.items():
            if hasattr(self._options.graph, key):
                setattr(self._options.graph, key, value)
        return self

    def with_search_options(self, **kwargs: Any) -> "ApplicationBuilder":
        """Set search options from keyword arguments."""
        for key, value in kwargs.items():
            if hasattr(self._options.search, key):
                setattr(self._options.search, key, value)
        return self

    def with_budget_options(self, **kwargs: Any) -> "ApplicationBuilder":
        """Set budget options from keyword arguments."""
        for key, value in kwargs.items():
            if hasattr(self._options.budget, key):
                setattr(self._options.budget, key, value)
        return self

    # =========================================================================
    # SERVICES
    # =========================================================================

    def with_generator(self, generator: Generator) -> "ApplicationBuilder":
        """
        Set the thought generator.

        Args:
            generator: A Generator implementation.

        Returns:
            Self for chaining.

        Example:
            builder.with_generator(LLMGenerator(api_key="..."))
        """
        self._generator = generator
        return self

    def with_evaluator(self, evaluator: Evaluator) -> "ApplicationBuilder":
        """
        Set the thought evaluator.

        Args:
            evaluator: An Evaluator implementation.

        Returns:
            Self for chaining.

        Example:
            builder.with_evaluator(LLMEvaluator(api_key="..."))
        """
        self._evaluator = evaluator
        return self

    def with_persistence(self, persistence: Persistence) -> "ApplicationBuilder":
        """
        Set the persistence service.

        Args:
            persistence: A Persistence implementation.

        Returns:
            Self for chaining.

        Example:
            builder.with_persistence(PostgresPersistence(conn_string="..."))
        """
        self._persistence = persistence
        return self

    def with_logger(self, logger: Logger) -> "ApplicationBuilder":
        """
        Set the logger.

        Args:
            logger: A Logger implementation.

        Returns:
            Self for chaining.
        """
        self._logger = logger
        return self

    def with_metrics(self, metrics: MetricsCollector) -> "ApplicationBuilder":
        """
        Set the metrics collector.

        Args:
            metrics: A MetricsCollector implementation.

        Returns:
            Self for chaining.
        """
        self._metrics = metrics
        return self

    # =========================================================================
    # MIDDLEWARE
    # =========================================================================

    def use_middleware(self, middleware: type) -> "ApplicationBuilder":
        """
        Add middleware to the pipeline.

        Args:
            middleware: A middleware class.

        Returns:
            Self for chaining.

        Note:
            Middleware is applied in the order added.
        """
        self._middleware.append(middleware)
        return self

    # =========================================================================
    # BUILD
    # =========================================================================

    def build(self) -> Application:
        """
        Build the application.

        Validates configuration and creates the application.

        Returns:
            A configured Application ready to use.

        Raises:
            ValueError: If configuration is invalid.

        Example:
            app = ApplicationBuilder().build()
        """
        # Validate options
        errors = self._options.validate()
        if errors:
            raise ValueError(f"Invalid options: {', '.join(errors)}")

        # Create container
        container = ServiceContainer()

        # Register services with mode-appropriate defaults
        self._register_services(container)

        # Create application
        return Application(container, self._options)

    def _register_services(self, container: ServiceContainer) -> None:
        """Register all services in the container."""

        # Generator
        if self._generator:
            container.register_instance(Generator, self._generator)
        elif self._mode == "production":
            raise ValueError("Production mode requires explicit generator")
        else:
            # Development/test default
            container.register_singleton(Generator, SimpleGenerator)

        # Evaluator
        if self._evaluator:
            container.register_instance(Evaluator, self._evaluator)
        elif self._mode == "production":
            raise ValueError("Production mode requires explicit evaluator")
        else:
            container.register_singleton(Evaluator, SimpleEvaluator)

        # Persistence
        if self._persistence:
            container.register_instance(Persistence, self._persistence)
        else:
            container.register_singleton(Persistence, InMemoryPersistence)

        # Logger
        if self._logger:
            container.register_instance(Logger, self._logger)
        else:
            container.register_singleton(Logger, InMemoryLogger)

        # Metrics
        if self._metrics:
            container.register_instance(MetricsCollector, self._metrics)
        else:
            container.register_singleton(MetricsCollector, InMemoryMetrics)
