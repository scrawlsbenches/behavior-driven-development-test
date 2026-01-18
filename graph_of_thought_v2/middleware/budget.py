"""
Budget Middleware - Resource Consumption Enforcement
=====================================================

Enforces budget limits before operations and tracks consumption after.
This is the gatekeeper that prevents runaway costs.

HOW BUDGET ENFORCEMENT WORKS
----------------------------

BEFORE operation:
    1. Check if context has a budget
    2. If budget is exhausted, REJECT the operation
    3. If budget is in warning zone, LOG a warning
    4. Allow operation to proceed

AFTER operation:
    1. Track how much was consumed (if tracked)
    2. Update metrics
    3. Return result

The middleware DOES NOT modify context. Budget tracking happens
via a separate consumption tracker that's injected.

WHY MIDDLEWARE, NOT IN CORE
---------------------------

Budget enforcement is a POLICY, not part of reasoning:
- Core search doesn't know about money
- Core search doesn't know about limits
- Budget rules vary by organization

By putting enforcement in middleware:
- Core stays pure and testable
- Budget rules are configurable
- Different environments can have different policies

CONSUMPTION TRACKING
--------------------

The middleware needs to know how much an operation consumed.
Options:

1. RESULT-BASED: The result includes consumption info
   result.tokens_consumed

2. CALLBACK-BASED: Handler calls a tracker
   await consumption_tracker.record(500)

3. CONTEXT-BASED: Context tracks consumption
   new_context = context.consume_budget(500)

We support option 1 (result-based) for simplicity.

"""

from typing import TypeVar, Generic, Any, Protocol
import time

from graph_of_thought_v2.context import Context
from graph_of_thought_v2.middleware.pipeline import Handler
from graph_of_thought_v2.services.protocols import Logger, MetricsCollector

Req = TypeVar("Req")
Res = TypeVar("Res")


# =============================================================================
# EXCEPTIONS
# =============================================================================

class BudgetExhausted(Exception):
    """Raised when operation is rejected due to exhausted budget."""

    def __init__(
        self,
        message: str = "Budget exhausted",
        consumed: int = 0,
        total: int = 0,
    ) -> None:
        super().__init__(message)
        self.consumed = consumed
        self.total = total


class BudgetWarning(Exception):
    """Raised when budget is in warning zone (not fatal)."""

    def __init__(
        self,
        message: str = "Budget warning threshold reached",
        utilization: float = 0.0,
    ) -> None:
        super().__init__(message)
        self.utilization = utilization


# =============================================================================
# CONSUMPTION RESULT PROTOCOL
# =============================================================================

class HasConsumption(Protocol):
    """Protocol for results that include consumption info."""

    @property
    def tokens_consumed(self) -> int:
        """Number of tokens consumed by this operation."""
        ...


# =============================================================================
# BUDGET MIDDLEWARE
# =============================================================================

class BudgetMiddleware(Generic[Req, Res]):
    """
    Middleware that enforces budget limits.

    Before operation:
    - Rejects if budget is exhausted
    - Warns (via logger) if budget is in warning zone

    After operation:
    - Records consumption to metrics
    - Logs remaining budget

    Example:
        budget_middleware = BudgetMiddleware(
            inner=core_handler,
            logger=my_logger,
            metrics=my_metrics,
            strict=True,  # Raise on exhausted budget
        )

    Configuration:
        strict: If True, raise BudgetExhausted when budget is gone.
               If False, log warning but allow operation.
    """

    def __init__(
        self,
        inner: Handler[Req, Res],
        logger: Logger | None = None,
        metrics: MetricsCollector | None = None,
        strict: bool = True,
    ) -> None:
        """
        Initialize budget middleware.

        Args:
            inner: The handler to wrap.
            logger: Logger for warnings (optional).
            metrics: Metrics collector for tracking (optional).
            strict: If True, reject operations when budget exhausted.
        """
        self._inner = inner
        self._logger = logger
        self._metrics = metrics
        self._strict = strict

    async def handle(self, request: Req, context: Context) -> Res:
        """
        Handle request with budget enforcement.

        Checks budget before, tracks consumption after.
        """
        # BEFORE: Check budget
        if context.budget is not None:
            budget = context.budget

            # Check if exhausted
            if budget.is_exhausted:
                if self._strict:
                    if self._logger:
                        self._logger.warning(
                            "Operation rejected: budget exhausted",
                            consumed=budget.consumed,
                            total=budget.total,
                        )
                    raise BudgetExhausted(
                        consumed=budget.consumed,
                        total=budget.total,
                    )
                else:
                    if self._logger:
                        self._logger.warning(
                            "Budget exhausted but strict=False, allowing operation",
                            consumed=budget.consumed,
                            total=budget.total,
                        )

            # Check if warning threshold
            elif budget.is_warning:
                if self._logger:
                    self._logger.warning(
                        "Budget warning threshold reached",
                        utilization=f"{budget.utilization:.1%}",
                        remaining=budget.remaining,
                    )

        # EXECUTE: Run the operation
        result = await self._inner.handle(request, context)

        # AFTER: Track consumption
        if context.budget is not None and self._metrics:
            # Try to get consumption from result
            tokens_consumed = 0
            if hasattr(result, "tokens_consumed"):
                tokens_consumed = result.tokens_consumed

            if tokens_consumed > 0:
                self._metrics.increment(
                    "budget.tokens_consumed",
                    value=tokens_consumed,
                    project=context.project_id or "unknown",
                )

                # Record remaining budget as gauge
                new_remaining = context.budget.remaining - tokens_consumed
                self._metrics.gauge(
                    "budget.tokens_remaining",
                    new_remaining,
                    project=context.project_id or "unknown",
                )

        return result
