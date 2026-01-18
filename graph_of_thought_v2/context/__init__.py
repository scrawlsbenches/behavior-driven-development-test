"""
Context Layer - Immutable Execution Environment
================================================

Context is the "where we are" of an operation. It carries information
about the execution environment without having side effects.

THE FUNDAMENTAL DISTINCTION
---------------------------

CONTEXT is DATA:
- Immutable snapshots of state
- Passed through operations
- Used for decisions, not actions

SERVICES are CAPABILITIES:
- Have side effects
- Injected at construction
- Used to DO things

Never confuse the two. Context doesn't call APIs. Services do.

DESIGN DECISIONS
----------------

1. WHY IMMUTABLE (FROZEN DATACLASSES)?

   Mutable context is a source of bugs:
   - "Who changed the budget?"
   - "Why is the depth wrong?"
   - Thread safety issues

   Immutable context means:
   - Safe to pass around
   - Safe to share between tasks
   - Easy to reason about

   To "modify" context, create a child: context.child(budget=new_budget)

2. WHY LAYERED CONTEXTS?

   Different operations need different context:

   - ExecutionContext: The broadest (user, project, config)
   - SearchContext: For search operations (adds depth, path)
   - ExpansionContext: For expansion (adds parent thought)

   Each layer adds specificity. Inner contexts derive from outer ones.

3. WHY NOT JUST PASS INDIVIDUAL PARAMETERS?

   Functions with many parameters are hard to:
   - Call correctly (did I pass them in the right order?)
   - Extend (adding a parameter changes all call sites)
   - Test (need to provide all parameters)

   A context object:
   - Named fields (clear what's what)
   - Extensible (add fields without changing signatures)
   - Testable (create a context, pass it)

4. WHY SEPARATE FROM CORE?

   The core is PURE. It doesn't know about users, budgets, or traces.
   Context carries this application-level information WITHOUT polluting
   the core with business concerns.

   Core sees: thoughts, graphs, scores
   Context adds: user, budget, config, trace_id

CONTEXT DERIVATION
------------------

Contexts form a tree mirroring the operation tree:

    ExecutionContext (created at app start)
        │
        ├── SearchContext (created for each search)
        │       │
        │       ├── ExpansionContext (for each expansion)
        │       └── EvaluationContext (for each evaluation)
        │
        └── SearchContext (another search)
                │
                └── ...

Child contexts inherit from parents but can override values.

"""

from graph_of_thought_v2.context.execution import (
    Context,
    Budget,
)

__all__ = [
    "Context",
    "Budget",
]
