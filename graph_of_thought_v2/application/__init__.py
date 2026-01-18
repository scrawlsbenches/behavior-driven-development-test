"""
Application Layer - Composition Root
=====================================

This is where everything comes together. The application layer:

1. CONFIGURES the system (loads settings from files, env, etc.)
2. REGISTERS services (tells the container what implements what)
3. BUILDS pipelines (wires middleware and handlers)
4. PROVIDES the public API (what users actually call)

THE COMPOSITION ROOT PATTERN
----------------------------

The composition root is the ONLY place that knows about concrete types.
Everything else depends on abstractions (protocols).

    # Only in composition root (application layer):
    from services.implementations import LLMGenerator
    container.register(Generator, LLMGenerator)

    # Everywhere else:
    from services.protocols import Generator  # Just the protocol
    class SearchHandler:
        def __init__(self, generator: Generator):  # Don't know it's LLM
            ...

This means:
- Changing implementations = change one file
- Testing = register test implementations
- No hidden dependencies throughout the codebase

THE BUILDER PATTERN
-------------------

The ApplicationBuilder guides construction:

    app = (ApplicationBuilder()
        .with_mode("production")           # Set defaults for prod
        .with_generator(my_generator)       # Override generator
        .with_persistence("/data/graphs")   # Configure persistence
        .use_middleware(LoggingMiddleware)  # Add middleware
        .build())                           # Create the app

The builder:
- Validates configuration at build time
- Provides sensible defaults per mode
- Makes construction discoverable (IDE autocomplete)
- Prevents invalid states (can't build without generator)

SERVICE LIFETIMES
-----------------

Services have different lifetimes:

SINGLETON: One instance for the entire application
    - Logger (stateless, shared)
    - MetricsCollector (aggregates globally)
    - Configuration (read once)

SCOPED: One instance per scope (e.g., per search)
    - Context (changes per operation)
    - Handler chain (might need fresh state)

TRANSIENT: New instance every time
    - Request objects
    - Context modifications

The container manages these lifetimes.

"""

from graph_of_thought_v2.application.builder import ApplicationBuilder
from graph_of_thought_v2.application.container import ServiceContainer
from graph_of_thought_v2.application.options import (
    GraphOptions,
    SearchOptions,
    BudgetOptions,
)

__all__ = [
    "ApplicationBuilder",
    "ServiceContainer",
    "GraphOptions",
    "SearchOptions",
    "BudgetOptions",
]
