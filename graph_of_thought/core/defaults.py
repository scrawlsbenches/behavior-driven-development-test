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
import json
import sys
from datetime import datetime, timezone
from io import StringIO

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


class InMemoryVerifier(Generic[T]):
    """
    Verifier that stores verification history in memory for testing.

    Supports configurable default results, custom validation rules,
    and full history tracking for test assertions.

    Example:
        verifier = InMemoryVerifier()
        verifier.add_rule(lambda content, ctx: (False, "error") if "bad" in content else (True, None))
        result = await verifier.verify("bad content", context)
        assert not result.is_valid
        assert len(verifier.history) == 1
    """

    def __init__(
        self,
        default_valid: bool = True,
        default_confidence: float = 1.0,
        default_issues: list[str] | None = None,
        default_metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize the in-memory verifier.

        Args:
            default_valid: Default validation result when no rules reject
            default_confidence: Default confidence score (0.0 to 1.0)
            default_issues: Default issues to include in results
            default_metadata: Default metadata to include in results
        """
        self._default_valid = default_valid
        self._default_confidence = default_confidence
        self._default_issues = list(default_issues) if default_issues else []
        self._default_metadata = dict(default_metadata) if default_metadata else {}
        self._rules: list[Callable[[T, SearchContext[T]], tuple[bool, str | None]]] = []
        self._history: list[dict[str, Any]] = []

    @property
    def history(self) -> list[dict[str, Any]]:
        """Get verification history."""
        return list(self._history)

    def add_rule(
        self,
        rule: Callable[[T, SearchContext[T]], tuple[bool, str | None]],
    ) -> None:
        """
        Add a validation rule.

        Args:
            rule: Function that takes (content, context) and returns
                  (is_valid, issue_message). If is_valid is False,
                  the issue_message is added to the result.
        """
        self._rules.append(rule)

    async def verify(
        self,
        content: T,
        context: SearchContext[T],
    ) -> VerificationResult:
        """
        Verify content and record in history.

        Evaluates all rules. If any rule returns False, verification fails.
        All rule issues are collected into the result.

        Args:
            content: Content to verify
            context: Search context

        Returns:
            VerificationResult with validation status and details
        """
        issues = list(self._default_issues)
        is_valid = self._default_valid
        confidence = self._default_confidence

        # Evaluate all rules
        for rule in self._rules:
            rule_valid, issue = rule(content, context)
            if not rule_valid:
                is_valid = False
                confidence = 0.0
                if issue:
                    issues.append(issue)

        result = VerificationResult(
            is_valid=is_valid,
            confidence=confidence,
            issues=issues if issues else None,
            metadata=dict(self._default_metadata) if self._default_metadata else None,
        )

        # Record in history
        self._history.append({
            "content": content,
            "context": context,
            "result": result,
            "timestamp": time.time(),
        })

        return result

    def reset(self) -> None:
        """Clear verification history (preserves configuration)."""
        self._history.clear()

    def clear_rules(self) -> None:
        """Clear all validation rules."""
        self._rules.clear()


# =============================================================================
# Default Observability Implementations
# =============================================================================

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


class StructuredLogger:
    """
    Logger that outputs structured JSON log entries.

    Supports context binding for adding persistent context to all log messages.
    Each log entry is a JSON object with timestamp, level, message, and context.

    Example output:
        {"timestamp": "2024-01-15T10:30:00Z", "level": "INFO", "message": "Processing", "request_id": "123"}
    """

    def __init__(
        self,
        name: str = "graph_of_thought",
        output: Any | None = None,
        level: int = logging.DEBUG,
    ):
        """
        Initialize structured logger.

        Args:
            name: Logger name included in log entries
            output: Output stream (defaults to sys.stderr). Can be StringIO for testing.
            level: Minimum log level to output
        """
        self._name = name
        self._output = output if output is not None else sys.stderr
        self._level = level
        self._context: dict[str, Any] = {}

    def _format_value(self, value: Any) -> Any:
        """Format a value for JSON serialization."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        if isinstance(value, (list, tuple)):
            return [self._format_value(v) for v in value]
        if isinstance(value, dict):
            return {k: self._format_value(v) for k, v in value.items()}
        return str(value)

    def _log(self, level: int, level_name: str, message: str, extra: dict[str, Any]) -> None:
        """Write a structured log entry."""
        if level < self._level:
            return

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": level_name,
            "logger": self._name,
            "message": message,
        }

        # Merge bound context and extra kwargs
        combined_context = {**self._context, **extra}
        for key, value in combined_context.items():
            entry[key] = self._format_value(value)

        json_line = json.dumps(entry)
        self._output.write(json_line + "\n")

        # Flush if possible to ensure immediate output
        if hasattr(self._output, 'flush'):
            self._output.flush()

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._log(logging.DEBUG, "DEBUG", message, kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        self._log(logging.INFO, "INFO", message, kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self._log(logging.WARNING, "WARNING", message, kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        self._log(logging.ERROR, "ERROR", message, kwargs)

    def bind(self, **kwargs: Any) -> StructuredLogger:
        """
        Return a new logger with additional bound context.

        The bound context will be included in all subsequent log messages
        from the returned logger.

        Example:
            logger = StructuredLogger()
            request_logger = logger.bind(request_id="123", user="alice")
            request_logger.info("Processing")  # Includes request_id and user
        """
        new_logger = StructuredLogger(
            name=self._name,
            output=self._output,
            level=self._level,
        )
        new_logger._context = {**self._context, **kwargs}
        return new_logger

    def get_output(self) -> str:
        """
        Get captured output if using StringIO.

        Returns:
            The captured log output as a string.

        Raises:
            AttributeError: If output stream doesn't support getvalue().
        """
        return self._output.getvalue()


class InMemoryTraceSpan:
    """
    Trace span that stores data in memory for testing.

    Captures all span operations for verification in tests.
    Supports context manager protocol for automatic end() calls.
    When used as a context manager, properly restores the parent span
    as active when exiting (like OpenTelemetry).
    """

    def __init__(
        self,
        name: str,
        parent: InMemoryTraceSpan | None = None,
        attributes: dict[str, Any] | None = None,
        provider: Any | None = None,
    ):
        self._name = name
        self._parent = parent
        self._attributes: dict[str, Any] = dict(attributes) if attributes else {}
        self._events: list[dict[str, Any]] = []
        self._status: str | None = None
        self._status_description: str | None = None
        self._start_time = time.time()
        self._end_time: float | None = None
        self._children: list[InMemoryTraceSpan] = []
        self._provider = provider  # Reference to provider for context restoration

        if parent:
            parent._children.append(self)

    @property
    def name(self) -> str:
        """Get span name."""
        return self._name

    @property
    def parent(self) -> InMemoryTraceSpan | None:
        """Get parent span."""
        return self._parent

    @property
    def attributes(self) -> dict[str, Any]:
        """Get span attributes."""
        return self._attributes.copy()

    @property
    def events(self) -> list[dict[str, Any]]:
        """Get span events."""
        return list(self._events)

    @property
    def status(self) -> str | None:
        """Get span status."""
        return self._status

    @property
    def status_description(self) -> str | None:
        """Get span status description."""
        return self._status_description

    @property
    def duration_ms(self) -> float | None:
        """Get span duration in milliseconds, or None if not ended."""
        if self._end_time is None:
            return None
        return (self._end_time - self._start_time) * 1000

    @property
    def children(self) -> list[InMemoryTraceSpan]:
        """Get child spans."""
        return list(self._children)

    @property
    def is_ended(self) -> bool:
        """Check if span has ended."""
        return self._end_time is not None

    def set_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the span."""
        self._attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add an event to the span."""
        self._events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": dict(attributes) if attributes else {},
        })

    def set_status(self, status: str, description: str | None = None) -> None:
        """Set the span status."""
        self._status = status
        self._status_description = description

    def end(self) -> None:
        """End the span."""
        if self._end_time is None:
            self._end_time = time.time()

    def __enter__(self) -> InMemoryTraceSpan:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.set_status("ERROR", str(exc_val) if exc_val else None)
        self.end()
        # Restore parent as active span (OpenTelemetry-like behavior)
        if self._provider is not None:
            self._provider._active_span = self._parent

    def to_dict(self) -> dict[str, Any]:
        """Convert span to dictionary for inspection."""
        return {
            "name": self._name,
            "parent_name": self._parent._name if self._parent else None,
            "attributes": self._attributes,
            "events": self._events,
            "status": self._status,
            "status_description": self._status_description,
            "duration_ms": self.duration_ms,
            "is_ended": self.is_ended,
            "children": [child._name for child in self._children],
        }


class InMemoryTracingProvider:
    """
    Tracing provider that stores spans in memory for testing.

    Useful for verifying tracing behavior in tests without external dependencies.
    Tracks all spans created, supports parent-child relationships.

    Example:
        provider = InMemoryTracingProvider()
        with provider.start_span("operation") as span:
            span.set_attribute("user_id", "123")
        assert provider.get_span("operation").attributes["user_id"] == "123"
    """

    def __init__(self):
        self._spans: list[InMemoryTraceSpan] = []
        self._active_span: InMemoryTraceSpan | None = None

    def start_span(
        self,
        name: str,
        parent_span: InMemoryTraceSpan | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> InMemoryTraceSpan:
        """Start a new trace span.

        Automatically inherits from the active span if no explicit parent
        is provided (OpenTelemetry-like behavior). When used as a context
        manager, the span properly restores the parent as active on exit.

        Args:
            name: Span name
            parent_span: Explicit parent span (overrides automatic propagation)
            attributes: Initial span attributes

        Returns:
            The new span, which is now the active span
        """
        # Use explicit parent if provided, otherwise inherit from active span
        parent = parent_span if parent_span is not None else self._active_span
        span = InMemoryTraceSpan(name, parent=parent, attributes=attributes, provider=self)
        self._spans.append(span)
        self._active_span = span
        return span

    @property
    def spans(self) -> list[InMemoryTraceSpan]:
        """Get all spans."""
        return list(self._spans)

    def get_span(self, name: str) -> InMemoryTraceSpan | None:
        """Get a span by name (returns first match)."""
        for span in self._spans:
            if span.name == name:
                return span
        return None

    def get_spans_by_name(self, name: str) -> list[InMemoryTraceSpan]:
        """Get all spans with a given name."""
        return [span for span in self._spans if span.name == name]

    def get_root_spans(self) -> list[InMemoryTraceSpan]:
        """Get all root spans (spans without parents)."""
        return [span for span in self._spans if span.parent is None]

    def reset(self) -> None:
        """Clear all stored spans."""
        self._spans.clear()
        self._active_span = None


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
    """Event handler that logs all graph events as structured JSON."""

    def __init__(self, logger: Logger | None = None):
        self._logger = logger or StructuredLogger("graph_events")
    
    async def handle(self, event: GraphEvent[T]) -> None:
        thought_id = event.thought.id if event.thought else None
        self._logger.debug(
            f"Graph event: {event.event_type}",
            thought_id=thought_id,
            metadata=event.metadata,
        )
