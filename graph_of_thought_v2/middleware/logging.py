"""
Logging Middleware - Structured Operation Logging
=================================================

Logs the start and completion of every operation, with structured data.
Essential for debugging and understanding what happened.

WHAT GETS LOGGED
----------------

Before operation:
    INFO: Operation started
          trace_id=abc123 operation=search request_type=SearchRequest

After success:
    INFO: Operation completed
          trace_id=abc123 operation=search duration_ms=150 success=true

After failure:
    ERROR: Operation failed
           trace_id=abc123 operation=search duration_ms=50 error=BudgetExhausted

WHY STRUCTURED LOGGING
----------------------

Structured logs (key=value pairs) are:
- Machine parseable (can query and analyze)
- Consistent format (easy to find fields)
- Correlation-friendly (trace_id links related logs)

CONTEXT BINDING
---------------

The middleware binds trace_id to all logs automatically:

    logger = logger.bind(trace_id=context.trace_id)
    # All subsequent logs include trace_id

This means you don't need to pass trace_id everywhere.

"""

from typing import TypeVar, Generic, Any
import time

from graph_of_thought_v2.context import Context
from graph_of_thought_v2.middleware.pipeline import Handler
from graph_of_thought_v2.services.protocols import Logger

Req = TypeVar("Req")
Res = TypeVar("Res")


class LoggingMiddleware(Generic[Req, Res]):
    """
    Middleware that logs operation start and completion.

    Logs:
    - When an operation starts (INFO level)
    - When an operation completes successfully (INFO level)
    - When an operation fails (ERROR level)

    All logs include:
    - trace_id: For correlation
    - operation: What type of operation
    - duration_ms: How long it took

    Example:
        logging_middleware = LoggingMiddleware(
            inner=core_handler,
            logger=my_logger,
            operation_name="search",
        )
    """

    def __init__(
        self,
        inner: Handler[Req, Res],
        logger: Logger,
        operation_name: str = "operation",
    ) -> None:
        """
        Initialize logging middleware.

        Args:
            inner: The handler to wrap.
            logger: Logger service for output.
            operation_name: Name to use in log messages.
        """
        self._inner = inner
        self._logger = logger
        self._operation_name = operation_name

    async def handle(self, request: Req, context: Context) -> Res:
        """
        Handle request with logging.

        Logs start, then delegates to inner handler, then logs
        completion or failure.
        """
        # Bind context to logger for correlation
        log = self._logger.bind(
            trace_id=context.trace_id,
            operation=self._operation_name,
        )

        # Add user/project if available
        if context.user_id:
            log = log.bind(user_id=context.user_id)
        if context.project_id:
            log = log.bind(project_id=context.project_id)

        # Log start
        log.info(
            f"{self._operation_name} started",
            request_type=type(request).__name__,
        )

        start_time = time.time()

        try:
            # Execute inner handler
            result = await self._inner.handle(request, context)

            # Log success
            duration_ms = (time.time() - start_time) * 1000
            log.info(
                f"{self._operation_name} completed",
                duration_ms=round(duration_ms, 2),
                success=True,
            )

            return result

        except Exception as e:
            # Log failure
            duration_ms = (time.time() - start_time) * 1000
            log.error(
                f"{self._operation_name} failed",
                duration_ms=round(duration_ms, 2),
                success=False,
                error_type=type(e).__name__,
                error=str(e),
            )
            raise
