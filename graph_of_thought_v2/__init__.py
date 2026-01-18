"""
Graph of Thought - A Pure Reasoning Engine
==========================================

This package implements a Graph of Thought: a data structure and set of algorithms
for exploring solutions through structured reasoning.

DESIGN PHILOSOPHY
-----------------

1. THE CORE IS PURE
   The graph of thought at its heart is just data and algorithms. It has no
   dependencies on external services, no side effects, and no knowledge of
   persistence, logging, or governance. This makes it:
   - Trivially testable (no mocks needed)
   - Easy to understand (read 50 lines, know everything)
   - Infinitely composable (wrap it however you need)

2. DEPENDENCIES POINT INWARD
   The architecture follows the Clean Architecture / Onion Architecture principle:

       Application → Middleware → Services → Context → Core

   Each layer only knows about layers to its right. The core knows nothing.
   This means you can:
   - Test the core without any infrastructure
   - Swap implementations without touching business logic
   - Add new features without modifying existing code

3. CONTEXT IS DATA, SERVICES ARE CAPABILITIES
   - Context: Immutable snapshots of "where we are" (depth, budget, config)
   - Services: Things that DO stuff (generate thoughts, persist graphs)

   Context is PASSED through operations.
   Services are INJECTED at construction.
   Never confuse the two.

4. COMPOSITION OVER INHERITANCE
   Everything is composed, nothing is inherited. Want logging? Wrap with
   middleware. Want governance? Add a policy layer. The core doesn't change.

5. THE PIT OF SUCCESS
   The API is designed so that:
   - The right way is the easy way (use the builder)
   - The wrong way is hard (no public constructors for complex objects)
   - Mistakes are visible (fail at construction, not at runtime)


PACKAGE STRUCTURE
-----------------

graph_of_thought_v2/
│
├── core/           # Pure data structures and algorithms
│                   # NO DEPENDENCIES - this is the heart
│
├── context/        # Immutable execution context
│                   # Depends only on core models
│
├── services/       # Capabilities with side effects
│                   # Protocols + implementations
│
├── middleware/     # Cross-cutting concerns as a pipeline
│                   # Logging, metrics, budget enforcement
│
├── application/    # Composition root - wires everything
│                   # Builder, container, configuration
│
└── policy/         # Business rules (optional layer)
                    # Governance, projects, collaboration


QUICK START
-----------

    from graph_of_thought_v2 import ApplicationBuilder

    # Build an application with sensible defaults
    app = (ApplicationBuilder()
        .with_generator(my_generator)
        .with_evaluator(my_evaluator)
        .build())

    # Create a graph and explore
    graph = app.create_graph()
    graph.add("How do we solve this problem?")

    result = await app.search(graph)
    print(result.best_path)


LONG-TERM VISION
----------------

This architecture is designed to support:

1. MULTIPLE FRONTENDS
   - CLI tool for developers
   - Web API for applications
   - Library for embedding
   All share the same core, differ only in application layer.

2. PLUGGABLE INTELLIGENCE
   - LLM-based generation today
   - Fine-tuned models tomorrow
   - Hybrid approaches in the future
   Services are protocols; implementations are swappable.

3. ENTERPRISE FEATURES
   - Governance and approval workflows
   - Multi-user collaboration
   - Audit trails and compliance
   All live in the policy layer, never touch the core.

4. SCALABILITY
   - In-memory for development
   - Distributed for production
   - The core doesn't care where data lives.

"""

from graph_of_thought_v2.core import Thought, Graph
from graph_of_thought_v2.context import Context
from graph_of_thought_v2.application import ApplicationBuilder

__all__ = [
    # Core - the essential types
    "Thought",
    "Graph",

    # Context - execution environment
    "Context",

    # Application - the entry point
    "ApplicationBuilder",
]

__version__ = "2.0.0"
