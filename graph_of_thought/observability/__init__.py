"""
Observability utilities for Graph of Thought.

This module provides utilities for logging, metrics, and tracing.
Add production implementations (Prometheus, OpenTelemetry, etc.) as needed.
"""

from __future__ import annotations
from typing import Any
import time
import logging
from contextlib import contextmanager
from functools import wraps

from ..core.defaults import (
    InMemoryMetricsCollector,
    StandardLogger,
    StructuredLogger,
    InMemoryTracingProvider,
    InMemoryTraceSpan,
)


# Re-export defaults
__all__ = [
    "InMemoryMetricsCollector",
    "StandardLogger",
    "StructuredLogger",
    "InMemoryTracingProvider",
    "InMemoryTraceSpan",
    "setup_logging",
    "timed",
    "counted",
    "log_context",
    "MetricsRegistry",
]


def setup_logging(
    level: int = logging.INFO,
    format_string: str | None = None,
    logger_name: str = "graph_of_thought",
) -> logging.Logger:
    """
    Set up basic logging configuration.
    
    Args:
        level: Logging level
        format_string: Custom format string
        logger_name: Name for the logger
        
    Returns:
        Configured logger
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(handler)
    
    return logger


def timed(metric_name: str | None = None):
    """
    Decorator to time function execution.
    
    Usage:
        @timed("my_function_time")
        async def my_function():
            ...
    """
    def decorator(func):
        name = metric_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed_ms = (time.time() - start) * 1000
                # Log timing (could be extended to use metrics collector)
                logging.debug(f"{name} took {elapsed_ms:.2f}ms")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.time() - start) * 1000
                logging.debug(f"{name} took {elapsed_ms:.2f}ms")
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def counted(metric_name: str | None = None):
    """
    Decorator to count function calls.
    
    Usage:
        @counted("my_function_calls")
        def my_function():
            ...
    """
    def decorator(func):
        name = metric_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logging.debug(f"{name} called")
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logging.debug(f"{name} called")
            return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


@contextmanager
def log_context(**kwargs: Any):
    """
    Context manager to add context to log messages.
    
    Usage:
        with log_context(request_id="123", user="alice"):
            logger.info("Processing request")
    """
    # This is a placeholder - in production, use structlog or similar
    yield


class MetricsRegistry:
    """
    Registry for collecting metrics from multiple sources.
    
    Use this to aggregate metrics from different parts of the system.
    """
    
    def __init__(self):
        self._collectors: list[Any] = []
    
    def register(self, collector: Any) -> None:
        """Register a metrics collector."""
        self._collectors.append(collector)
    
    def unregister(self, collector: Any) -> None:
        """Unregister a metrics collector."""
        if collector in self._collectors:
            self._collectors.remove(collector)
    
    def increment(self, metric: str, value: int = 1, tags: dict[str, str] | None = None) -> None:
        """Increment a counter on all registered collectors."""
        for collector in self._collectors:
            collector.increment(metric, value, tags)
    
    def gauge(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Set a gauge on all registered collectors."""
        for collector in self._collectors:
            collector.gauge(metric, value, tags)
    
    def histogram(self, metric: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a histogram value on all registered collectors."""
        for collector in self._collectors:
            collector.histogram(metric, value, tags)
    
    def timing(self, metric: str, value_ms: float, tags: dict[str, str] | None = None) -> None:
        """Record a timing on all registered collectors."""
        for collector in self._collectors:
            collector.timing(metric, value_ms, tags)
