"""
Execution Context - The Environment for Operations
===================================================

The execution context carries all the information needed to perform
operations, without carrying the ability to DO things (that's services).

WHAT CONTEXT ANSWERS
--------------------

- "Who is doing this?" → user_id
- "What project is this for?" → project_id
- "How much budget remains?" → budget
- "What are the limits?" → config
- "How do I trace this?" → trace_id

WHAT CONTEXT DOES NOT ANSWER
----------------------------

- "How do I generate thoughts?" → that's a service
- "How do I persist the graph?" → that's a service
- "Where do I log this?" → that's a service

Context is READ-ONLY information. No methods with side effects.

DESIGN DECISIONS
----------------

1. WHY BUDGET IS A SEPARATE CLASS

   Budget has behavior: checking if exceeded, consuming tokens, etc.
   But it's still IMMUTABLE. Consuming tokens returns a NEW budget.

   This allows tracking without mutation:
       new_budget = budget.consume(100)
       # budget is unchanged, new_budget has 100 less

2. WHY OPTIONAL FIELDS

   Not every operation needs every field:
   - CLI tool might not have user_id
   - Testing might not have trace_id
   - Simple scripts might not have budget

   Make fields optional with sensible defaults, not required with
   dummy values.

3. WHY trace_id

   Distributed tracing needs correlation IDs. Every context carries one.
   This allows:
   - Connecting logs across operations
   - Debugging request flows
   - Performance analysis

4. WHY child() METHOD

   Instead of modifying context (forbidden!), create derived contexts:

       child_context = context.child(depth=context.depth + 1)

   This maintains immutability while allowing operation-specific context.

"""

from dataclasses import dataclass, field, replace
from typing import Any
from uuid import uuid4


# =============================================================================
# BUDGET
# =============================================================================

@dataclass(frozen=True)
class Budget:
    """
    Immutable token budget for operations.

    Budget tracks how many tokens are available and how many have been used.
    It's immutable - "using" tokens returns a new Budget with less remaining.

    Attributes:
        total: Total tokens allocated.
        consumed: Tokens already used.
        warning_threshold: Percentage at which to warn (0.0 to 1.0).

    Example:
        >>> budget = Budget(total=10000)
        >>> budget.remaining
        10000
        >>> new_budget = budget.consume(500)
        >>> new_budget.remaining
        9500
        >>> budget.remaining  # Original unchanged
        10000

    Design Note:
        Budget is a VALUE OBJECT. Two budgets with the same values are equal.
        Budget has no identity - it's defined entirely by its attributes.
    """

    total: int
    """Total tokens allocated for this context."""

    consumed: int = 0
    """Tokens already consumed."""

    warning_threshold: float = 0.8
    """Warn when consumed exceeds this fraction of total (default 80%)."""

    @property
    def remaining(self) -> int:
        """Tokens still available."""
        return max(0, self.total - self.consumed)

    @property
    def utilization(self) -> float:
        """Fraction of budget consumed (0.0 to 1.0)."""
        if self.total == 0:
            return 0.0
        return self.consumed / self.total

    @property
    def is_exhausted(self) -> bool:
        """True if no tokens remain."""
        return self.remaining <= 0

    @property
    def is_warning(self) -> bool:
        """True if utilization exceeds warning threshold."""
        return self.utilization >= self.warning_threshold

    def consume(self, tokens: int) -> "Budget":
        """
        Return a new budget with tokens consumed.

        Args:
            tokens: Number of tokens to consume.

        Returns:
            New Budget with updated consumed count.

        Note:
            Does NOT check if budget is exhausted. That's middleware's job.
            This just tracks consumption.
        """
        return replace(self, consumed=self.consumed + tokens)

    def __str__(self) -> str:
        return f"Budget({self.consumed}/{self.total}, {self.utilization:.1%} used)"


# =============================================================================
# EXECUTION CONTEXT
# =============================================================================

@dataclass(frozen=True)
class Context:
    """
    Immutable execution context for operations.

    Context carries the "who, what, when, how much" of an operation without
    carrying the ability to DO anything. It's read-only information.

    Attributes:
        trace_id: Correlation ID for distributed tracing.
        user_id: Who initiated this operation (optional).
        project_id: Which project this belongs to (optional).
        budget: Token budget for this context (optional).
        config: Configuration dictionary (optional).

    Creating Context:
        >>> ctx = Context()  # Minimal context
        >>> ctx = Context(user_id="alice", project_id="my-project")
        >>> ctx = Context(budget=Budget(total=10000))

    Deriving Child Contexts:
        >>> child = ctx.child(budget=new_budget)
        >>> deep = ctx.child(depth=5)  # Via extras

    Design Note:
        Context uses frozen=True for immutability. All "modifications"
        return new Context objects. This ensures safety in concurrent
        operations and makes reasoning about state trivial.
    """

    trace_id: str = field(default_factory=lambda: str(uuid4()))
    """
    Correlation ID for tracing.

    Auto-generated if not provided. Use the same trace_id across related
    operations to connect logs and metrics.
    """

    user_id: str | None = None
    """
    Who initiated this operation.

    Optional because not all contexts have a user (e.g., background jobs,
    system operations, testing).
    """

    project_id: str | None = None
    """
    Which project this operation belongs to.

    Optional because not all operations are project-scoped.
    """

    budget: Budget | None = None
    """
    Token budget for this context.

    Optional because not all operations have budgets (e.g., testing,
    local development).
    """

    config: dict[str, Any] = field(default_factory=dict)
    """
    Configuration for this context.

    A flexible dictionary for operation-specific settings. Prefer typed
    Options classes (in application layer) for production use.
    """

    extras: dict[str, Any] = field(default_factory=dict)
    """
    Extension point for additional context.

    Use extras for domain-specific context that doesn't belong in the
    core fields. Example: extras={"depth": 3, "parent_id": "abc123"}
    """

    def child(self, **overrides: Any) -> "Context":
        """
        Create a child context with overridden values.

        Child contexts inherit all values from the parent but can override
        specific fields. Use this to create operation-specific contexts.

        Args:
            **overrides: Fields to override in the child context.

        Returns:
            New Context with overridden values.

        Example:
            >>> child = ctx.child(budget=new_budget)
            >>> child = ctx.child(extras={**ctx.extras, "depth": 5})

        Note:
            The original context is unchanged. This is a functional update.
        """
        # Handle extras specially - merge rather than replace
        if "extras" in overrides:
            merged_extras = {**self.extras, **overrides["extras"]}
            overrides["extras"] = merged_extras

        return replace(self, **overrides)

    def with_budget(self, budget: Budget) -> "Context":
        """Convenience method to create child with new budget."""
        return self.child(budget=budget)

    def consume_budget(self, tokens: int) -> "Context":
        """
        Create child context with tokens consumed from budget.

        Args:
            tokens: Number of tokens to consume.

        Returns:
            New Context with updated budget.

        Raises:
            ValueError: If context has no budget.
        """
        if self.budget is None:
            raise ValueError("Cannot consume budget: context has no budget")
        return self.child(budget=self.budget.consume(tokens))

    @property
    def has_budget(self) -> bool:
        """True if this context has a budget."""
        return self.budget is not None

    @property
    def budget_exhausted(self) -> bool:
        """True if budget exists and is exhausted."""
        return self.budget is not None and self.budget.is_exhausted

    def __str__(self) -> str:
        parts = [f"Context(trace={self.trace_id[:8]}...)"]
        if self.user_id:
            parts.append(f"user={self.user_id}")
        if self.project_id:
            parts.append(f"project={self.project_id}")
        if self.budget:
            parts.append(str(self.budget))
        return " ".join(parts)


# =============================================================================
# CONTEXT FACTORY (convenience)
# =============================================================================

def create_context(
    *,
    user_id: str | None = None,
    project_id: str | None = None,
    budget_tokens: int | None = None,
    trace_id: str | None = None,
    **config: Any,
) -> Context:
    """
    Convenience factory for creating contexts.

    Args:
        user_id: Who initiated this operation.
        project_id: Which project this belongs to.
        budget_tokens: Total token budget (creates Budget if provided).
        trace_id: Correlation ID (auto-generated if not provided).
        **config: Additional configuration key-value pairs.

    Returns:
        A new Context with the specified values.

    Example:
        >>> ctx = create_context(
        ...     user_id="alice",
        ...     project_id="my-project",
        ...     budget_tokens=10000,
        ...     max_depth=5,
        ...     beam_width=3,
        ... )
    """
    budget = Budget(total=budget_tokens) if budget_tokens else None

    return Context(
        trace_id=trace_id or str(uuid4()),
        user_id=user_id,
        project_id=project_id,
        budget=budget,
        config=config,
    )
