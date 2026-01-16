"""
Default implementations of protocols.

These provide basic functionality that works out of the box.
Replace with production implementations as needed.
"""

from __future__ import annotations
from typing import TypeVar, Generic, Any, Callable, Awaitable
import asyncio
import time
import logging

from ..core import (
    Thought,
    Edge,
    SearchContext,
    ThoughtGenerator,
    ThoughtEvaluator,
    ThoughtVerifier,
    VerificationResult,
    MetricsCollector,
    Logger,
    TracingProvider,
    TraceSpan,
    ResourceLimiter,
    EventHandler,
    EventEmitter,
    GraphEvent,
)

T = TypeVar("T")


# =============================================================================
# Default Generator and Evaluator
# =============================================================================

class FunctionGenerator(Generic[T]):
    """
    Thought generator that wraps a simple function.
    
    Supports both sync and async functions.
    """
    
    def __init__(
        self,
        func: Callable[[T], list[T]] | Callable[[T], Awaitable[list[T]]],
    ):
        self._func = func
        self._is_async = asyncio.iscoroutinefunction(func)
    
    async def generate(
        self,
        parent: T,
        context: SearchContext[T],
    ) -> list[T]:
        if self._is_async:
            return await self._func(parent)
        else:
            return self._func(parent)


class FunctionEvaluator(Generic[T]):
    """
    Thought evaluator that wraps a simple function.
    
    Supports both sync and async functions.
    """
    
    def __init__(
        self,
        func: Callable[[T], float] | Callable[[T], Awaitable[float]],
    ):
        self._func = func
        self._is_async = asyncio.iscoroutinefunction(func)
    
    async def evaluate(
        self,
        content: T,
        context: SearchContext[T],
    ) -> float:
        if self._is_async:
            return await self._func(content)
        else:
            return self._func(content)


class ConstantEvaluator(Generic[T]):
    """Evaluator that returns a constant score."""
    
    def __init__(self, score: float = 0.0):
        self._score = score
    
    async def evaluate(
        self,
        content: T,
        context: SearchContext[T],
    ) -> float:
        return self._score


class NoOpVerifier(Generic[T]):
    """Verifier that always passes."""
    
    async def verify(
        self,
        content: T,
        context: SearchContext[T],
    ) -> VerificationResult:
        return VerificationResult(is_valid=True, confidence=1.0)


# =============================================================================
# Default Observability Implementations
# =============================================================================

class NullMetricsCollector:
    """Metrics collector that discards all metrics."""
    
    def increment(
        self,
        metric: str,
        value: int = 1,
        tags: dict[str, str] | None = None,
    ) -> None:
        pass
    
    def gauge(
        self,
        metric: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        pass
    
    def histogram(
        self,
        metric: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        pass
    
    def timing(
        self,
        metric: str,
        value_ms: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        pass


class InMemoryMetricsCollector:
    """
    Metrics collector that stores metrics in memory.
    
    Useful for testing and debugging.
    """
    
    def __init__(self):
        self.counters: dict[str, int] = {}
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, list[float]] = {}
        self.timings: dict[str, list[float]] = {}
    
    def increment(
        self,
        metric: str,
        value: int = 1,
        tags: dict[str, str] | None = None,
    ) -> None:
        key = self._make_key(metric, tags)
        self.counters[key] = self.counters.get(key, 0) + value
    
    def gauge(
        self,
        metric: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        key = self._make_key(metric, tags)
        self.gauges[key] = value
    
    def histogram(
        self,
        metric: str,
        value: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        key = self._make_key(metric, tags)
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
    
    def timing(
        self,
        metric: str,
        value_ms: float,
        tags: dict[str, str] | None = None,
    ) -> None:
        key = self._make_key(metric, tags)
        if key not in self.timings:
            self.timings[key] = []
        self.timings[key].append(value_ms)
    
    def _make_key(self, metric: str, tags: dict[str, str] | None) -> str:
        if not tags:
            return metric
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{metric}[{tag_str}]"
    
    def reset(self) -> None:
        """Reset all metrics."""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.timings.clear()


class StandardLogger:
    """Logger that uses Python's standard logging module."""
    
    def __init__(self, name: str = "graph_of_thought"):
        self._logger = logging.getLogger(name)
        self._context: dict[str, Any] = {}
    
    def debug(self, message: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs: Any) -> None:
        self._log(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, message, kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, message, kwargs)
    
    def bind(self, **kwargs: Any) -> StandardLogger:
        new_logger = StandardLogger(self._logger.name)
        new_logger._context = {**self._context, **kwargs}
        return new_logger
    
    def _log(self, level: int, message: str, extra: dict[str, Any]) -> None:
        combined = {**self._context, **extra}
        if combined:
            extra_str = " ".join(f"{k}={v}" for k, v in combined.items())
            message = f"{message} | {extra_str}"
        self._logger.log(level, message)


class NullLogger:
    """Logger that discards all log messages."""
    
    def debug(self, message: str, **kwargs: Any) -> None:
        pass
    
    def info(self, message: str, **kwargs: Any) -> None:
        pass
    
    def warning(self, message: str, **kwargs: Any) -> None:
        pass
    
    def error(self, message: str, **kwargs: Any) -> None:
        pass
    
    def bind(self, **kwargs: Any) -> NullLogger:
        return self


class NullTraceSpan:
    """Trace span that does nothing."""
    
    def set_attribute(self, key: str, value: Any) -> None:
        pass
    
    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        pass
    
    def set_status(self, status: str, description: str | None = None) -> None:
        pass
    
    def end(self) -> None:
        pass
    
    def __enter__(self) -> NullTraceSpan:
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


class NullTracingProvider:
    """Tracing provider that creates null spans."""
    
    def start_span(
        self,
        name: str,
        parent_span: Any | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> NullTraceSpan:
        return NullTraceSpan()


# =============================================================================
# Default Resource Limiter
# =============================================================================

class SimpleResourceLimiter:
    """
    Simple in-memory resource limiter.
    
    Thread-safe for basic use cases.
    """
    
    def __init__(self, limits: dict[str, int] | None = None):
        self._limits = limits or {}
        self._usage: dict[str, int] = {}
        import threading
        self._lock = threading.Lock()
    
    def set_limit(self, resource_type: str, limit: int) -> None:
        """Set or update a resource limit."""
        with self._lock:
            self._limits[resource_type] = limit
    
    async def acquire(
        self,
        resource_type: str,
        amount: int = 1,
    ) -> bool:
        with self._lock:
            if resource_type not in self._limits:
                return True  # No limit set
            
            current = self._usage.get(resource_type, 0)
            limit = self._limits[resource_type]
            
            if current + amount <= limit:
                self._usage[resource_type] = current + amount
                return True
            return False
    
    def release(
        self,
        resource_type: str,
        amount: int = 1,
    ) -> None:
        with self._lock:
            current = self._usage.get(resource_type, 0)
            self._usage[resource_type] = max(0, current - amount)
    
    def get_remaining(self, resource_type: str) -> int | None:
        with self._lock:
            if resource_type not in self._limits:
                return None
            limit = self._limits[resource_type]
            used = self._usage.get(resource_type, 0)
            return limit - used
    
    def is_exhausted(self, resource_type: str) -> bool:
        remaining = self.get_remaining(resource_type)
        return remaining is not None and remaining <= 0
    
    def reset(self, resource_type: str | None = None) -> None:
        """Reset usage counters."""
        with self._lock:
            if resource_type:
                self._usage.pop(resource_type, None)
            else:
                self._usage.clear()


# =============================================================================
# Default Event Emitter
# =============================================================================

class SimpleEventEmitter(Generic[T]):
    """
    Simple synchronous event emitter.
    
    For production, consider using an async event bus.
    """
    
    def __init__(self):
        self._handlers: list[EventHandler[T]] = []
    
    def subscribe(self, handler: EventHandler[T]) -> None:
        if handler not in self._handlers:
            self._handlers.append(handler)
    
    def unsubscribe(self, handler: EventHandler[T]) -> None:
        if handler in self._handlers:
            self._handlers.remove(handler)
    
    async def emit(self, event: GraphEvent[T]) -> None:
        for handler in self._handlers:
            try:
                await handler.handle(event)
            except Exception:
                # Log but don't fail on handler errors
                pass


class LoggingEventHandler(Generic[T]):
    """Event handler that logs all events."""
    
    def __init__(self, logger: Logger | None = None):
        self._logger = logger or StandardLogger("graph_events")
    
    async def handle(self, event: GraphEvent[T]) -> None:
        thought_id = event.thought.id if event.thought else None
        self._logger.debug(
            f"Graph event: {event.event_type}",
            thought_id=thought_id,
            metadata=event.metadata,
        )
