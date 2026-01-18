"""
Services Layer - Capabilities with Side Effects
================================================

Services are things that DO stuff. They have side effects: calling APIs,
reading files, writing logs. They're injected at construction time and
used throughout the application.

THE SERVICE CONTRACT
--------------------

Every service is defined as a PROTOCOL (interface), not a class:

    class Generator(Protocol):
        async def generate(self, thought, context) -> list[str]: ...

Implementations satisfy the protocol:

    class LLMGenerator:  # No inheritance needed!
        async def generate(self, thought, context) -> list[str]:
            return await self.llm.complete(...)

This allows:
- Duck typing (anything with the right methods works)
- Easy testing (simple mocks without inheritance)
- Multiple implementations (LLM, rules-based, hybrid)

SERVICES VS CONTEXT
-------------------

Services DO things:              Context DESCRIBES things:
- Call LLMs                      - Current user
- Write to disk                  - Remaining budget
- Send notifications             - Configuration values
- Record metrics                 - Trace ID

Services are INJECTED:           Context is PASSED:
- Once, at construction          - To each operation
- Live for app lifetime          - Immutable snapshots
- Shared across operations       - Operation-specific

SERVICE CATEGORIES
------------------

CORE SERVICES (required for search):
- Generator: Creates child thoughts from parents
- Evaluator: Scores thoughts

INFRASTRUCTURE SERVICES (cross-cutting):
- Logger: Records what happened
- Metrics: Tracks measurements
- Persistence: Saves/loads graphs

DOMAIN SERVICES (business capabilities):
- Knowledge: Queries historical information
- Questions: Manages blocking questions

EXTERNAL SERVICES (integrations):
- LLM: Large language model API
- Notifications: Alerts and messages

DESIGN DECISIONS
----------------

1. WHY PROTOCOLS, NOT ABC?

   Abstract Base Classes (ABC) require inheritance:
       class MyGenerator(GeneratorABC): ...

   Protocols use structural typing:
       class MyGenerator:  # Just implement the methods
           async def generate(self, thought, context) -> list[str]: ...

   Benefits:
   - No "forgot to inherit" bugs
   - Works with third-party classes
   - More Pythonic (duck typing)

2. WHY ASYNC EVERYWHERE?

   Most real services are I/O bound (LLM calls, disk, network).
   Even if a service is sync, the overhead of async is negligible.
   Consistent async allows easy parallelization.

3. WHY SEPARATE PROTOCOL FILE?

   Protocols are CONTRACTS. They should be:
   - Easy to find (one file)
   - Stable (change less than implementations)
   - Dependency-free (no implementation imports)

   Code depends on protocols, not implementations.

"""

# Protocols (what services CAN do)
from graph_of_thought_v2.services.protocols import (
    Generator,
    Evaluator,
    Persistence,
    Logger,
    MetricsCollector,
)

# Implementations (HOW services do it)
from graph_of_thought_v2.services.implementations import (
    # In-memory implementations for testing
    InMemoryPersistence,
    InMemoryLogger,
    InMemoryMetrics,
    # Simple implementations for getting started
    SimpleGenerator,
    SimpleEvaluator,
)

__all__ = [
    # Protocols
    "Generator",
    "Evaluator",
    "Persistence",
    "Logger",
    "MetricsCollector",
    # In-memory implementations
    "InMemoryPersistence",
    "InMemoryLogger",
    "InMemoryMetrics",
    # Simple implementations
    "SimpleGenerator",
    "SimpleEvaluator",
]
