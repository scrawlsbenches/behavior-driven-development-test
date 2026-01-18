"""
Metrics Middleware - Operation Measurements
============================================

Records metrics about operations:
- Counters: How many operations happened
- Histograms: How long operations took
- Gauges: Current state (e.g., queue depth)

WHY METRICS
-----------

Metrics answer questions like:
- How many searches per minute?
- What's the p99 latency?
- How often do operations fail?
- How much budget is consumed?

This data enables:
- Alerting (notify when error rate spikes)
- Capacity planning (predict resource needs)
- Performance optimization (find slow operations)

METRIC NAMING
-------------

We use a consistent naming scheme:

    graph_of_thought.{operation}.{metric}

Examples:
    graph_of_thought.search.total      - Counter of searches
    graph_of_thought.search.duration   - Histogram of search times
    graph_of_thought.search.errors     - Counter of failed searches

Tags provide dimensions:
    graph_of_thought.search.total{project="foo"}

CARDINALITY WARNING
-------------------

Tags should have bounded cardinality. Good tags:
- project_id (bounded set of projects)
- operation_type (bounded set of operations)
- error_type (bounded set of error classes)

Bad tags:
- trace_id (unbounded, creates infinite series)
- user_id (potentially unbounded)
- timestamp (infinite)

"""

from typing import TypeVar, Generic, Any
import time

from graph_of_thought_v2.context import Context
from graph_of_thought_v2.middleware.pipeline import Handler
from graph_of_thought_v2.services.protocols import MetricsCollector

Req = TypeVar("Req")
Res = TypeVar("Res")


class MetricsMiddleware(Generic[Req, Res]):
    """
    Middleware that records operation metrics.

    Records:
    - Counter: {prefix}.total - Total operations
    - Counter: {prefix}.errors - Failed operations
    - Histogram: {prefix}.duration_ms - Operation duration

    All metrics include tags for filtering:
    - project: Project ID (if available)
    - operation: Operation name

    Example:
        metrics_middleware = MetricsMiddleware(
            inner=core_handler,
            metrics=my_metrics,
            prefix="graph_of_thought.search",
        )
    """

    def __init__(
        self,
        inner: Handler[Req, Res],
        metrics: MetricsCollector,
        prefix: str = "graph_of_thought.operation",
    ) -> None:
        """
        Initialize metrics middleware.

        Args:
            inner: The handler to wrap.
            metrics: Metrics collector for recording.
            prefix: Prefix for metric names.
        """
        self._inner = inner
        self._metrics = metrics
        self._prefix = prefix

    async def handle(self, request: Req, context: Context) -> Res:
        """
        Handle request with metrics recording.

        Records total count, duration, and error count.
        """
        # Build tags (only bounded cardinality fields!)
        tags: dict[str, str] = {}
        if context.project_id:
            tags["project"] = context.project_id

        # Record that operation started
        self._metrics.increment(f"{self._prefix}.total", **tags)

        start_time = time.time()

        try:
            # Execute inner handler
            result = await self._inner.handle(request, context)

            # Record duration
            duration_ms = (time.time() - start_time) * 1000
            self._metrics.histogram(
                f"{self._prefix}.duration_ms",
                duration_ms,
                **tags,
            )

            return result

        except Exception as e:
            # Record error
            self._metrics.increment(
                f"{self._prefix}.errors",
                error_type=type(e).__name__,
                **tags,
            )

            # Still record duration for failed requests
            duration_ms = (time.time() - start_time) * 1000
            self._metrics.histogram(
                f"{self._prefix}.duration_ms",
                duration_ms,
                success="false",
                **tags,
            )

            raise
