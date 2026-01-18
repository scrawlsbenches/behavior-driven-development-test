# Graph of Thought v2 - Architecture Deep Dive

This document teaches you to **critically assess** this architecture. Don't accept anything at face value. Question every decision. Ask "is this correct?" at each step.

Good architecture survives scrutiny. Let's scrutinize.

---

## Table of Contents

1. [How to Read This Document](#how-to-read-this-document)
2. [The Claim: What This Architecture Promises](#the-claim-what-this-architecture-promises)
3. [Layer by Layer Examination](#layer-by-layer-examination)
4. [Critical Questions to Ask](#critical-questions-to-ask)
5. [Validation Exercises](#validation-exercises)
6. [Known Trade-offs and Limitations](#known-trade-offs-and-limitations)
7. [When This Architecture is Wrong](#when-this-architecture-is-wrong)

---

## How to Read This Document

**Don't trust this document.**

This README makes claims about the architecture. Your job is to verify them by:

1. **Reading the code** - Does the code match the claims?
2. **Asking "why"** - Is the reasoning sound?
3. **Finding counterexamples** - When would this break?
4. **Testing assumptions** - Can you prove or disprove the claims?

Every section ends with **Questions to Validate**. Don't skip them.

---

## The Claim: What This Architecture Promises

This architecture claims to provide:

| Claim | Supposed Benefit |
|-------|------------------|
| Pure core with zero dependencies | Testable without mocks |
| Inward-pointing dependencies | Changes don't ripple outward |
| Immutable context | Thread-safe, easy to reason about |
| Protocol-based services | Swappable implementations |
| Builder pattern for construction | Guided, validated setup |
| Middleware pipeline | Composable cross-cutting concerns |

### Questions to Validate

Before going further, ask yourself:

1. **Are these claims actually valuable?** Would a simpler architecture suffice?
2. **Are the claims testable?** How would you prove "testable without mocks"?
3. **What's the cost?** More layers = more indirection. Is it worth it?

---

## Layer by Layer Examination

### Layer 1: Core (`core/`)

**The Claim:** The core is pure. It has no dependencies on other layers. It can be tested without any infrastructure.

```
core/
├── thought.py    # Thought dataclass
├── graph.py      # Graph structure
└── search.py     # Search algorithms
```

**Examine `thought.py`:**

```python
@dataclass
class Thought(Generic[T]):
    content: T
    score: float = 0.0
    id: str = field(default_factory=lambda: str(uuid4()))
```

**Is this correct?**

- ✓ No imports from other layers (check the import statements)
- ✓ Pure data structure (no methods with side effects)
- ? But it imports `uuid4` - is that a "dependency"?

**Think about it:** We said "zero dependencies" but we use `uuid4`. Is the standard library a dependency? Where do we draw the line?

**Examine `graph.py`:**

The Graph class stores thoughts and relationships. Look at the `add` method:

```python
def add(self, thought: Thought[T], parent: Thought[T] | None = None) -> Thought[T]:
    if thought.id in self._thoughts:
        raise ValueError(f"Thought with id {thought.id!r} already exists")
    # ...
```

**Is this correct?**

- ✓ Validates input (no duplicate IDs)
- ✓ Maintains invariants (parent must exist)
- ? Raises ValueError - is exception handling part of "pure"?
- ? Mutates internal state (`self._thoughts[thought.id] = thought`)

**Think about it:** We claimed the core is "pure" but the Graph is mutable. Is this a contradiction? Or is there a difference between "pure functions" and "pure modules"?

**Examine `search.py`:**

```python
async def beam_search(
    graph: Graph[T],
    expand: Expander[T],
    evaluate: Evaluator[T],
    config: SearchConfig | None = None,
) -> SearchResult[T]:
```

**Is this correct?**

- ✓ Takes functions as arguments (dependency injection)
- ✓ Returns a result object (not side effects)
- ? But it's `async` - doesn't that imply I/O?
- ? It modifies the graph (`graph.add(child, parent=parent)`)

**Think about it:** The search algorithm adds thoughts to the graph. Is this a side effect? The graph is passed in, so the caller controls it. Is that "pure enough"?

### Questions to Validate - Core Layer

1. Open `core/thought.py`. Count the imports. Are any from other layers in this package?
2. Open `core/graph.py`. Find all methods that modify state. List them.
3. Can you write a test for `Graph.add()` without importing anything from `services/` or `middleware/`?
4. The search function is async. What happens if you try to call it synchronously? Is this a design flaw?

---

### Layer 2: Context (`context/`)

**The Claim:** Context is immutable data that flows through operations. It's separate from services (which do things).

```
context/
└── execution.py    # Context, Budget
```

**Examine `execution.py`:**

```python
@dataclass(frozen=True)
class Budget:
    total: int
    consumed: int = 0

    def consume(self, tokens: int) -> "Budget":
        return replace(self, consumed=self.consumed + tokens)
```

**Is this correct?**

- ✓ `frozen=True` means immutable
- ✓ `consume()` returns a NEW Budget, doesn't modify
- ✓ No side effects

```python
@dataclass(frozen=True)
class Context:
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str | None = None
    budget: Budget | None = None

    def child(self, **overrides) -> "Context":
        return replace(self, **overrides)
```

**Is this correct?**

- ✓ Also frozen (immutable)
- ✓ `child()` creates new context, doesn't modify
- ? But `default_factory` runs code - is that "pure"?

**Think about it:** The context uses `uuid4()` to generate trace IDs. This is non-deterministic. Does that break testability? How would you test code that depends on trace_id?

### Questions to Validate - Context Layer

1. Try to modify a Context after creation. What happens?
   ```python
   ctx = Context(user_id="alice")
   ctx.user_id = "bob"  # What happens?
   ```

2. Is `Budget.consume()` truly pure? Does it have any side effects?

3. The Context has a `config: dict` field. Dicts are mutable. Does this break immutability?
   ```python
   ctx = Context(config={"key": "value"})
   ctx.config["key"] = "changed"  # Does this work?
   ```

4. If it works, is the architecture broken? How would you fix it?

---

### Layer 3: Services (`services/`)

**The Claim:** Services are capabilities accessed through protocols. Implementations can be swapped without changing business logic.

```
services/
├── protocols.py           # What services CAN do
└── implementations/
    ├── memory.py          # InMemory implementations
    └── simple.py          # Simple implementations
```

**Examine `protocols.py`:**

```python
@runtime_checkable
class Generator(Protocol[T]):
    async def generate(
        self,
        thought: Thought[T],
        context: Any,  # Actually Context
    ) -> list[T]:
        ...
```

**Is this correct?**

- ✓ Protocol, not abstract class (duck typing)
- ✓ `@runtime_checkable` allows `isinstance()` checks
- ? `context: Any` - why not `context: Context`?

**Think about it:** The protocol uses `Any` for context to avoid circular imports. Is this a code smell? What are the alternatives?

**Examine `implementations/memory.py`:**

```python
class InMemoryLogger:
    def __init__(self, context: dict[str, Any] | None = None) -> None:
        self.entries: list[LogEntry] = []
        self.context: dict[str, Any] = context or {}
```

**Is this correct?**

- ✓ Stores logs in memory (no I/O)
- ✓ Simple, testable
- ? Has mutable state (`self.entries`)
- ? Shares entries between bound loggers (`child.entries = self.entries`)

**Think about it:** When you call `logger.bind()`, the child logger shares the same `entries` list as the parent. Is this intentional? What are the implications?

### Questions to Validate - Services Layer

1. Create a class that satisfies the `Generator` protocol without inheriting from anything:
   ```python
   class MyGenerator:
       async def generate(self, thought, context):
           return ["child1", "child2"]

   # Does this work?
   isinstance(MyGenerator(), Generator)  # ?
   ```

2. The `InMemoryPersistence` stores graphs directly (no serialization). What happens if you modify a graph after saving it?
   ```python
   persistence = InMemoryPersistence()
   graph = Graph()
   graph.add(Thought(content="original"))

   graph_id = await persistence.save(graph, ctx)
   graph.add(Thought(content="added after save"))

   loaded = await persistence.load(graph_id, ctx)
   len(loaded)  # What is this? 1 or 2?
   ```

3. Is this a bug or a feature? How would you fix it?

---

### Layer 4: Middleware (`middleware/`)

**The Claim:** Middleware wraps operations to add cross-cutting concerns. It's composable and order-independent (mostly).

```
middleware/
├── pipeline.py    # Core types
├── logging.py     # LoggingMiddleware
├── metrics.py     # MetricsMiddleware
└── budget.py      # BudgetMiddleware
```

**Examine `pipeline.py`:**

```python
class Pipeline(Generic[Req, Res]):
    def add(self, middleware_class: type, **kwargs) -> "Pipeline[Req, Res]":
        def factory(inner: Handler[Req, Res]) -> Handler[Req, Res]:
            return middleware_class(inner, **kwargs)
        self._middleware.append(factory)
        return self

    def build(self) -> Handler[Req, Res]:
        handler = self._core
        for factory in reversed(self._middleware):
            handler = factory(handler)
        return handler
```

**Is this correct?**

- ✓ Middleware wraps inner handler
- ✓ `reversed()` means first-added is outermost
- ? But `add()` stores a factory, not the middleware itself

**Think about it:** The pipeline creates middleware lazily at `build()` time. What if you add the same middleware class twice? Do you get two instances or one?

**Examine `budget.py`:**

```python
class BudgetMiddleware:
    async def handle(self, request: Req, context: Context) -> Res:
        if context.budget is not None:
            if context.budget.is_exhausted:
                if self._strict:
                    raise BudgetExhausted(...)
```

**Is this correct?**

- ✓ Checks budget before operation
- ✓ Configurable strictness
- ? Only checks BEFORE, doesn't update budget AFTER
- ? How does consumed budget get tracked?

**Think about it:** The middleware checks the budget but doesn't consume from it. Context is immutable. How does budget tracking actually work? Is something missing?

### Questions to Validate - Middleware Layer

1. What happens if you add middleware in this order?
   ```python
   pipeline = (Pipeline(handler)
       .add(BudgetMiddleware)
       .add(LoggingMiddleware)
       .build())
   ```
   Which runs first: budget check or logging? Trace through the code.

2. The `BudgetMiddleware` checks `context.budget.is_exhausted` but context is immutable. If an operation consumes budget, how does the next operation know?

3. Is the middleware pipeline truly "order-independent"? What if logging needs to log the budget state? Does order matter then?

---

### Layer 5: Application (`application/`)

**The Claim:** The application layer is the composition root. It's the only place that knows about concrete implementations.

```
application/
├── options.py     # Typed configuration
├── container.py   # Dependency injection
└── builder.py     # ApplicationBuilder
```

**Examine `container.py`:**

```python
def resolve(self, protocol: type) -> Any:
    if protocol not in self._registrations:
        raise KeyError(f"No registration for {protocol.__name__}")

    implementation, lifetime = self._registrations[protocol]

    if lifetime == Lifetime.SINGLETON and protocol in self._singletons:
        return self._singletons[protocol]

    # Create instance...
```

**Is this correct?**

- ✓ Singleton caching works
- ✓ Raises clear error for unregistered types
- ? Uses `type` as key - what about generic types like `Generator[str]`?

**Think about it:** The container uses `type` objects as keys. But `Generator[str]` and `Generator[int]` are different types. Does the container handle this? Try it.

**Examine `builder.py`:**

```python
def build(self) -> Application:
    errors = self._options.validate()
    if errors:
        raise ValueError(f"Invalid options: {', '.join(errors)}")

    container = ServiceContainer()
    self._register_services(container)

    return Application(container, self._options)
```

**Is this correct?**

- ✓ Validates before building (fail fast)
- ✓ Creates container internally (encapsulation)
- ? What if validation passes but registration fails?

**Think about it:** The builder validates options, then registers services. But service registration can also fail (e.g., missing dependency). Is the error handling complete?

### Questions to Validate - Application Layer

1. What happens if you call `build()` twice on the same builder?
   ```python
   builder = ApplicationBuilder()
   app1 = builder.build()
   app2 = builder.build()
   # Are app1 and app2 the same? Different? Shared state?
   ```

2. The container has `_construct()` that auto-wires dependencies. What happens with circular dependencies?
   ```python
   class A:
       def __init__(self, b: B): pass

   class B:
       def __init__(self, a: A): pass

   container.register(A, A)
   container.register(B, B)
   container.resolve(A)  # What happens?
   ```

3. Is there cycle detection? Should there be?

---

### Layer 6: Policy (`policy/`)

**The Claim:** Policy is business rules that exist separately from the core. It decides WHAT is allowed, not HOW things work.

```
policy/
├── governance.py   # Approval workflows
└── projects.py     # Work organization
```

**Examine `governance.py`:**

```python
class GovernancePolicy:
    def requires_approval(self, context: Context, operation: OperationType) -> bool:
        return any(rule.applies(context, operation) for rule in self._approval_rules)
```

**Is this correct?**

- ✓ Checks rules, doesn't enforce them
- ✓ Returns bool, lets caller decide what to do
- ? Rules are added via `add_approval_rule()` - is this mutable?

**Think about it:** The policy is mutable (you can add rules). Should it be? What if rules are added during operation?

**Examine `projects.py`:**

```python
@dataclass
class WorkChunk:
    def start(self) -> "WorkChunk":
        if self.status != ChunkStatus.PLANNED:
            raise ValueError(f"Cannot start chunk in {self.status} status")

        return WorkChunk(
            id=self.id,
            # ... copy all fields ...
            status=ChunkStatus.ACTIVE,
            started_at=datetime.now(),
        )
```

**Is this correct?**

- ✓ Returns new WorkChunk (immutable pattern)
- ✓ Validates state transitions
- ? Copies all fields manually - what if a field is added?

**Think about it:** The `start()` method manually copies every field. If someone adds a new field to WorkChunk and forgets to update `start()`, it will be lost. Is there a better pattern?

### Questions to Validate - Policy Layer

1. The GovernancePolicy uses `any()` to check rules. What if you need ALL rules to pass (AND logic instead of OR)?

2. WorkChunk transitions are: PLANNED → ACTIVE → COMPLETED. Can you go backwards? Should you be able to?

3. The Handoff class captures "accomplished" and "remaining". Who validates that these are filled in correctly? What stops someone from creating an empty handoff?

---

## Critical Questions to Ask

When evaluating ANY architecture, ask these questions:

### 1. Cohesion
> "Do things that change together live together?"

- If I change how thoughts are scored, how many files do I touch?
- If I add a new service, how many files do I touch?
- If I change the budget rules, how many files do I touch?

### 2. Coupling
> "Do things that shouldn't know about each other actually not know?"

- Does the Graph know about persistence?
- Does the search algorithm know about logging?
- Does the middleware know about specific services?

### 3. Testability
> "Can I test each part in isolation?"

- Can I test Graph without any services?
- Can I test search without a real LLM?
- Can I test middleware without a real handler?

### 4. Flexibility
> "Can I change my mind later?"

- Can I switch from in-memory to database persistence?
- Can I add a new type of middleware?
- Can I use a different search algorithm?

### 5. Understandability
> "Can a new developer understand this in 30 minutes?"

- Is the layer structure obvious?
- Are the responsibilities clear?
- Is the flow of data traceable?

---

## Validation Exercises

### Exercise 1: Trace a Search Operation

Start with this code:

```python
app = ApplicationBuilder().build()
graph = app.create_graph()
graph.add(Thought(content="How do we solve X?"))
result = await app.search(graph)
```

Trace the execution path:
1. Where does `app.search()` start? (`builder.py`)
2. What services does it resolve?
3. What middleware is applied?
4. Where does `beam_search()` get called?
5. How do expand/evaluate get invoked?

Draw the call graph. Does it match your mental model?

### Exercise 2: Add a New Service

Imagine you need to add a `CacheService` that caches LLM responses.

1. Where would the protocol go?
2. Where would the implementation go?
3. How would you register it in the container?
4. How would the Generator use it?

If you can answer these without reading code, the architecture is learnable.
If you have to read code, note which parts were confusing.

### Exercise 3: Break the Architecture

Try to violate the architectural rules:

1. Import something from `services/` in `core/`. Does it work? Should it?
2. Modify a frozen Context. What happens?
3. Register the same protocol twice. What happens?
4. Create a circular dependency. What happens?

A good architecture makes violations obvious or impossible.

### Exercise 4: Write a Test

Write a test for `beam_search` that:
- Uses a mock generator (returns fixed children)
- Uses a mock evaluator (returns fixed scores)
- Verifies the search finds the expected path

If you can write this test without importing from `services/implementations/`, the core is truly independent.

---

## Known Trade-offs and Limitations

Every architecture makes trade-offs. Here are ours:

### Trade-off 1: Layers vs. Simplicity

**We chose:** 6 layers (core, context, services, middleware, application, policy)

**Alternative:** Fewer layers, less indirection

**Why we chose this:** Each layer has a clear responsibility. Changes are localized.

**The cost:** More files to navigate. Indirection can be confusing.

**Is this correct?** For a simple script, no. For an enterprise system, probably yes. For this project? You decide.

### Trade-off 2: Protocols vs. Abstract Classes

**We chose:** Protocols (structural typing, duck typing)

**Alternative:** Abstract base classes (nominal typing)

**Why we chose this:** Protocols work with any class that has the right methods. No inheritance required.

**The cost:** Less IDE support. No guaranteed method implementation at definition time.

**Is this correct?** Protocols are more Pythonic. ABCs are more explicit. Neither is wrong.

### Trade-off 3: Immutable Context vs. Mutable State

**We chose:** Immutable context, mutable graph

**Alternative:** Everything immutable (functional), or everything mutable (OOP)

**Why we chose this:** Context is passed around and should be safe. Graph is owned by one place and grows.

**The cost:** Inconsistency. You have to know which things are immutable.

**Is this correct?** The hybrid approach adds cognitive load but matches the use case. Debatable.

### Trade-off 4: Simple DI Container vs. Full Framework

**We chose:** ~100 line custom container

**Alternative:** Use `dependency_injector`, `injector`, or similar

**Why we chose this:** No external dependencies. Easy to understand.

**The cost:** Missing features (scoped lifetime, auto-registration, etc.)

**Is this correct?** For this project, simple is fine. For larger projects, a real DI framework might be better.

---

## When This Architecture is Wrong

This architecture is NOT appropriate when:

### 1. You're Building a Script
If your code is < 500 lines, this is overkill. Just write functions.

### 2. You Need Maximum Performance
Every layer is indirection. Every protocol is a virtual call. If you need nanosecond performance, flatten the architecture.

### 3. You're Prototyping
If you don't know what you're building yet, architecture is premature. Build the messy version first.

### 4. You're the Only Developer
If no one else will read this code, simpler is better. Architecture is for teams.

### 5. The Domain is Simple
If "search a graph" is all you do, you don't need middleware, policies, and six layers. A single file might suffice.

---

## Final Questions

After reading this document and examining the code:

1. **Do you trust this architecture?** Why or why not?

2. **What would you change?** Be specific.

3. **What's missing?** What concerns aren't addressed?

4. **Is it over-engineered?** For what use case?

5. **Is it under-engineered?** For what use case?

6. **Would you use it?** In what context?

The goal isn't to prove the architecture is perfect. The goal is to understand it well enough to make an informed decision.

---

## Appendix: File-by-File Checklist

Use this checklist when reviewing each file:

```
□ Does the file do ONE thing?
□ Are the imports only from allowed layers?
□ Are there tests that prove it works?
□ Is the public API documented?
□ Are error cases handled?
□ Is the code readable without comments?
□ Could a junior developer understand this?
□ What happens if this file is deleted?
```

---

*This document is intentionally provocative. Good architecture should survive hard questions. If these questions reveal problems, that's valuable information.*
