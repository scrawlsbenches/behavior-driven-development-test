"""
Service Implementations - How Services Do Things
=================================================

This package contains concrete implementations of service protocols.
Each implementation is a specific way of fulfilling a service contract.

IMPLEMENTATION CATEGORIES
-------------------------

1. IN-MEMORY IMPLEMENTATIONS
   For testing and development. No external dependencies.
   Fast, deterministic, inspectable.

   - InMemoryPersistence: Stores graphs in a dict
   - InMemoryLogger: Stores logs in a list
   - InMemoryMetrics: Stores metrics in dicts

2. SIMPLE IMPLEMENTATIONS
   Minimal implementations for getting started.
   No LLM calls, just basic logic.

   - SimpleGenerator: Rule-based generation
   - SimpleEvaluator: Heuristic scoring

3. LLM IMPLEMENTATIONS (future)
   Production implementations using language models.
   Requires API keys and network access.

   - LLMGenerator: Uses GPT/Claude for generation
   - LLMEvaluator: Uses GPT/Claude for evaluation

4. EXTERNAL IMPLEMENTATIONS (future)
   Integrations with external systems.

   - PostgresPersistence: Database storage
   - S3Persistence: Cloud storage
   - PrometheusMetrics: Metrics export

CHOOSING IMPLEMENTATIONS
------------------------

For TESTING:
    Use InMemory* implementations. They're fast, deterministic,
    and let you inspect internal state.

For DEVELOPMENT:
    Use Simple* implementations. They work without API keys
    and let you test the full flow.

For PRODUCTION:
    Use LLM* or external implementations. They provide
    real capabilities but require configuration.

The application builder makes this easy:

    # Testing
    app = ApplicationBuilder().with_mode("test").build()

    # Development
    app = ApplicationBuilder().with_mode("development").build()

    # Production
    app = (ApplicationBuilder()
        .with_mode("production")
        .with_generator(LLMGenerator(api_key=...))
        .build())

"""

from graph_of_thought_v2.services.implementations.memory import (
    InMemoryPersistence,
    InMemoryLogger,
    InMemoryMetrics,
)

from graph_of_thought_v2.services.implementations.simple import (
    SimpleGenerator,
    SimpleEvaluator,
)

__all__ = [
    # In-memory (testing)
    "InMemoryPersistence",
    "InMemoryLogger",
    "InMemoryMetrics",
    # Simple (development)
    "SimpleGenerator",
    "SimpleEvaluator",
]
