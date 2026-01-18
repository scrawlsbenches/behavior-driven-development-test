"""
Middleware Layer - Cross-Cutting Concerns as a Pipeline
========================================================

Middleware wraps operations to add behavior without modifying the core.
It's the layer where cross-cutting concerns live:

- Logging (what happened?)
- Metrics (how long? how many?)
- Budget enforcement (can we afford this?)
- Error handling (what if it fails?)
- Caching (did we do this before?)

THE PIPELINE MODEL
------------------

Middleware forms a pipeline. Each request passes through each middleware
in order, and responses flow back through in reverse:

    Request
       │
       ▼
    ┌──────────────────┐
    │ LoggingMiddleware │ ──► logs "starting"
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ BudgetMiddleware  │ ──► checks budget
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ MetricsMiddleware │ ──► starts timer
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │   Core Handler    │ ──► does the work
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ MetricsMiddleware │ ◄── records duration
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ BudgetMiddleware  │ ◄── tracks consumption
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ LoggingMiddleware │ ◄── logs "completed"
    └────────┬─────────┘
             │
             ▼
       Response

MIDDLEWARE VS SERVICES
----------------------

MIDDLEWARE wraps operations:         SERVICES perform operations:
- Logging middleware                  - Generator service
- Metrics middleware                  - Evaluator service
- Budget middleware                   - Persistence service

Middleware is about HOW we do things (with logging, with metrics).
Services are about WHAT we do (generate, evaluate, persist).

DESIGN DECISIONS
----------------

1. WHY A PIPELINE, NOT DECORATORS?

   Decorators are static (applied at definition time).
   Pipelines are dynamic (configured at runtime).

   With a pipeline, you can:
   - Add/remove middleware per environment
   - Reorder middleware as needed
   - Conditionally apply middleware

2. WHY ASYNC?

   Middleware often does I/O (logging to files, sending metrics).
   Async allows non-blocking execution.

3. WHY CONTEXT MODIFICATION?

   Some middleware needs to modify context:
   - Add trace IDs
   - Update remaining budget
   - Record timing information

   We handle this by returning a new context (immutable).

4. WHY COMPOSABLE HANDLERS?

   Each middleware wraps an inner handler. This makes testing easy:

       # Test just logging middleware
       inner = MockHandler()
       middleware = LoggingMiddleware(inner, logger)
       await middleware.handle(request, context)

"""

from graph_of_thought_v2.middleware.pipeline import (
    Middleware,
    Handler,
    Pipeline,
)

from graph_of_thought_v2.middleware.logging import LoggingMiddleware
from graph_of_thought_v2.middleware.metrics import MetricsMiddleware
from graph_of_thought_v2.middleware.budget import BudgetMiddleware

__all__ = [
    # Core types
    "Middleware",
    "Handler",
    "Pipeline",
    # Built-in middleware
    "LoggingMiddleware",
    "MetricsMiddleware",
    "BudgetMiddleware",
]
