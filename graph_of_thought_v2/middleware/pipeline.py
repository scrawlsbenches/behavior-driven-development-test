"""
Pipeline - The Middleware Infrastructure
========================================

This module defines the core types for building middleware pipelines:

- Handler: Something that processes a request and returns a response
- Middleware: Something that wraps a handler to add behavior
- Pipeline: A chain of middleware around a core handler

THE HANDLER PROTOCOL
--------------------

A handler is anything that can process a request:

    class Handler(Protocol[Req, Res]):
        async def handle(self, request: Req, context: Context) -> Res

The generic types allow type-safe pipelines:
- SearchHandler: Handler[SearchRequest, SearchResult]
- ExpansionHandler: Handler[Thought, list[Thought]]

THE MIDDLEWARE PATTERN
----------------------

Middleware wraps a handler and returns a new handler:

    class MyMiddleware:
        def __init__(self, inner: Handler):
            self.inner = inner

        async def handle(self, request, context):
            # Before
            result = await self.inner.handle(request, context)
            # After
            return result

This is the Decorator pattern applied to async handlers.

BUILDING PIPELINES
------------------

Pipelines are built inside-out:

    core = SearchHandler()
    with_metrics = MetricsMiddleware(core)
    with_logging = LoggingMiddleware(with_metrics)
    with_budget = BudgetMiddleware(with_logging)

    # Now: budget → logging → metrics → core

The Pipeline class handles this construction:

    pipeline = Pipeline(core)
        .add(MetricsMiddleware)
        .add(LoggingMiddleware)
        .add(BudgetMiddleware)
        .build()

"""

from typing import Protocol, TypeVar, Generic, Any, Callable, Awaitable
from dataclasses import dataclass
from graph_of_thought_v2.context import Context

# Generic types for requests and responses
Req = TypeVar("Req")
Res = TypeVar("Res")


# =============================================================================
# HANDLER PROTOCOL
# =============================================================================

class Handler(Protocol[Req, Res]):
    """
    Protocol for request handlers.

    A handler takes a request and context, and returns a response.
    This is the core abstraction for all operations.

    Type Parameters:
        Req: The request type.
        Res: The response type.

    Example:
        class SearchHandler:
            async def handle(
                self,
                request: SearchRequest,
                context: Context,
            ) -> SearchResult:
                # Do the search
                return result
    """

    async def handle(self, request: Req, context: Context) -> Res:
        """
        Process a request and return a response.

        Args:
            request: The request to process.
            context: Execution context (immutable).

        Returns:
            The response.
        """
        ...


# =============================================================================
# MIDDLEWARE PROTOCOL
# =============================================================================

class Middleware(Protocol[Req, Res]):
    """
    Protocol for middleware.

    Middleware wraps a handler and returns a new handler. It can:
    - Modify the request before passing to inner handler
    - Modify the response after receiving from inner handler
    - Short-circuit and return early (e.g., cached response)
    - Handle errors from the inner handler

    Middleware must be initialized with an inner handler.

    Example:
        class TimingMiddleware:
            def __init__(self, inner: Handler[Req, Res]):
                self.inner = inner

            async def handle(self, request: Req, context: Context) -> Res:
                start = time.time()
                result = await self.inner.handle(request, context)
                duration = time.time() - start
                print(f"Request took {duration:.2f}s")
                return result
    """

    async def handle(self, request: Req, context: Context) -> Res:
        """Process request, delegating to inner handler."""
        ...


# =============================================================================
# MIDDLEWARE RESULT
# =============================================================================

@dataclass
class MiddlewareResult(Generic[Res]):
    """
    Result from middleware that may modify context.

    Some middleware needs to return both a response AND an updated
    context (e.g., budget middleware updates remaining budget).

    Attributes:
        response: The actual response.
        context: Potentially modified context.

    Note:
        Most middleware just returns the response. This type is for
        middleware that needs to propagate context changes.
    """
    response: Res
    context: Context


# =============================================================================
# PIPELINE BUILDER
# =============================================================================

# Type for middleware factory: takes inner handler, returns handler
MiddlewareFactory = Callable[[Handler[Req, Res]], Handler[Req, Res]]


class Pipeline(Generic[Req, Res]):
    """
    Builder for middleware pipelines.

    Constructs a chain of middleware around a core handler.
    Middleware is added in order of execution (outermost first).

    Example:
        pipeline = (Pipeline(search_handler)
            .add(LoggingMiddleware, logger=logger)
            .add(MetricsMiddleware, metrics=metrics)
            .add(BudgetMiddleware, budget_tracker=tracker)
            .build())

        # Execution order: Logging → Metrics → Budget → Search

        result = await pipeline.handle(request, context)

    Design Note:
        The pipeline stores middleware as factories (constructors with
        partial arguments). This allows lazy construction and
        configuration flexibility.
    """

    def __init__(self, core: Handler[Req, Res]) -> None:
        """
        Create a pipeline with a core handler.

        Args:
            core: The innermost handler that does the actual work.
        """
        self._core = core
        self._middleware: list[MiddlewareFactory[Req, Res]] = []

    def add(
        self,
        middleware_class: type,
        **kwargs: Any,
    ) -> "Pipeline[Req, Res]":
        """
        Add middleware to the pipeline.

        Middleware is added in execution order (first added = outermost).

        Args:
            middleware_class: The middleware class.
            **kwargs: Arguments to pass to middleware constructor
                     (in addition to the inner handler).

        Returns:
            Self for chaining.

        Example:
            pipeline.add(LoggingMiddleware, logger=my_logger)
        """
        def factory(inner: Handler[Req, Res]) -> Handler[Req, Res]:
            return middleware_class(inner, **kwargs)

        self._middleware.append(factory)
        return self

    def build(self) -> Handler[Req, Res]:
        """
        Build the final handler with all middleware applied.

        Returns:
            A handler that passes through all middleware to the core.
        """
        handler = self._core

        # Apply middleware in reverse order (so first added is outermost)
        for factory in reversed(self._middleware):
            handler = factory(handler)

        return handler


# =============================================================================
# SIMPLE FUNCTION HANDLER
# =============================================================================

class FunctionHandler(Generic[Req, Res]):
    """
    Adapter to use a simple function as a handler.

    Allows using async functions directly in pipelines without
    creating a class.

    Example:
        async def my_search(request, context):
            return SearchResult(...)

        handler = FunctionHandler(my_search)
        pipeline = Pipeline(handler).add(LoggingMiddleware).build()
    """

    def __init__(
        self,
        func: Callable[[Req, Context], Awaitable[Res]],
    ) -> None:
        self._func = func

    async def handle(self, request: Req, context: Context) -> Res:
        return await self._func(request, context)
