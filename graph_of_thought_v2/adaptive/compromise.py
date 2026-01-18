"""
Compromise Solutions - Good Enough with Explicit Tradeoffs
===========================================================

This module defines the structure for compromise solutions - alternatives
offered when the ideal solution isn't achievable within constraints.

PROBLEM STATEMENT
-----------------

When a search can't reach the goal, we have options:
1. Fail completely - "Sorry, couldn't do it"
2. Return best found - "Here's something, no idea if it's useful"
3. Propose compromise - "Here's something decent, here's what you're giving up"

Option 3 is the most helpful. This module provides the structure for it.


WHAT IS A COMPROMISE?
---------------------

A compromise is:
- A solution that doesn't meet the full goal
- But IS above a minimum threshold (usable)
- With EXPLICIT documentation of tradeoffs
- So the requester can make an informed decision

Example:
    Goal: Code that passes all tests (score 0.95)
    Compromise: Code that passes most tests (score 0.72)
    Tradeoffs:
        - "2 edge case tests failing"
        - "Error handling incomplete"
        - "Performance not optimized"

The requester can then decide:
- "Good enough for now, I'll fix the edge cases"
- "No, I need complete solution, give me more budget"
- "Actually, incomplete error handling is a dealbreaker"


HOW THIS MODULE FITS IN
-----------------------

    ┌─────────────────────────────────────────────────────────────┐
    │                    BudgetNegotiator                         │
    │                      (budget.py)                            │
    │                                                             │
    │  When budget exhausted, looks for compromise:               │
    │    compromise = self._find_compromise(graph, situation)     │
    └─────────────────────────────────────────────────────────────┘
                              │
                              │ creates
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   CompromiseSolution                        │
    │                                                             │
    │  thought: The best thought we found                         │
    │  path: How we got there (reasoning chain)                   │
    │  score: The score achieved                                  │
    │  gap_to_acceptable: How far below threshold                 │
    │  tradeoffs: What's being sacrificed                         │
    └─────────────────────────────────────────────────────────────┘
                              │
                              │ used by
                              ▼
    ┌───────────────────┬─────────────────────────────────────────┐
    │ BudgetNegotiation │         AdaptiveSearchResult            │
    │ Result            │                                         │
    │                   │  May include compromise if goal not     │
    │ Includes as       │  reached but usable solution found      │
    │ fallback option   │                                         │
    └───────────────────┴─────────────────────────────────────────┘


TRADEOFF DOCUMENTATION
----------------------

Tradeoffs should be:
1. SPECIFIC - Not "quality is lower" but "15% below target"
2. ACTIONABLE - What would need to be done to fix it
3. HONEST - Don't hide problems

Good tradeoffs:
    - "Solution quality 15% below target"
    - "2 of 5 test cases not handled"
    - "No error handling for network failures"
    - "Performance not optimized (O(n²) where O(n) possible)"

Bad tradeoffs:
    - "Not perfect" (too vague)
    - "Some issues" (what issues?)
    - "Needs work" (what work?)


RELATIONSHIP TO OTHER MODULES
-----------------------------

    compromise.py (this file)
        │
        ├── Created by: budget.py (BudgetNegotiator._find_compromise)
        │   When budget exhausted but usable solution exists
        │
        ├── Included in: budget.py (BudgetNegotiationResult.compromise)
        │   As alternative when requesting budget increase
        │
        ├── Included in: controller.py (AdaptiveSearchResult.compromise)
        │   As final result when goal not reached
        │
        └── Presented by: feedback.py (FeedbackHandler)
            To get approval/rejection of compromise


USAGE EXAMPLE
-------------

    from graph_of_thought_v2.adaptive import CompromiseSolution

    # Created by BudgetNegotiator, not usually manually
    compromise = CompromiseSolution(
        thought=best_thought,
        path=[root, step1, step2, best_thought],
        score=0.72,
        gap_to_acceptable=0.08,  # 0.80 - 0.72
        tradeoffs=[
            "Solution quality 8% below target",
            "Edge case handling incomplete",
        ],
    )

    # Present to user
    print(compromise.explain())
    # Output:
    # Compromise Solution (score: 72.0%)
    # Gap to acceptable: 8.0%
    # Tradeoffs:
    #   - Solution quality 8% below target
    #   - Edge case handling incomplete

    # Check if worth accepting
    if compromise.score > 0.60:
        print("This might be usable")

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from graph_of_thought_v2.core import Thought

T = TypeVar("T")


# =============================================================================
# COMPROMISE SOLUTION
# =============================================================================

@dataclass(frozen=True)
class CompromiseSolution(Generic[T]):
    """
    A solution that doesn't meet the full goal but is acceptable.

    Includes explicit documentation of what's being traded off,
    so the requester can make an informed decision.

    Attributes:
        thought: The best thought found
        path: Reasoning path from root to this thought
        score: Score achieved (below goal but above minimum)
        gap_to_acceptable: How far below the acceptable threshold
        tradeoffs: What's being sacrificed in this compromise

    Type parameter T matches the thought content type from the graph.

    Created by: BudgetNegotiator._find_compromise() in budget.py
    Used by:
        - BudgetNegotiationResult (as fallback)
        - AdaptiveSearchResult (as final result)
        - FeedbackHandler (to present for approval)

    Example:
        compromise = CompromiseSolution(
            thought=thought_with_partial_solution,
            path=[root, hypothesis, refinement, thought_with_partial_solution],
            score=0.72,
            gap_to_acceptable=0.08,
            tradeoffs=["Missing error handling", "2 tests failing"],
        )
    """

    thought: Any  # Actually Thought[T], avoiding complex generic import
    """
    The best thought found that forms the compromise.

    This contains the actual solution content.
    Access via thought.content for the solution.
    """

    path: list[Any] = field(default_factory=list)  # Actually list[Thought[T]]
    """
    Reasoning path from root to this thought.

    Ordered: [root, child1, child2, ..., thought]
    Shows how this solution was derived.
    Useful for understanding the reasoning chain.
    """

    score: float = 0.0
    """
    Score achieved by this thought.

    Between compromise_threshold and acceptable_threshold.
    Higher is better but still below goal.

    Example: 0.72 when acceptable is 0.80
    """

    gap_to_acceptable: float = 0.0
    """
    How far below the acceptable threshold.

    Calculated as: acceptable_threshold - score
    Positive number indicates shortfall.

    Example: 0.08 means 8% below acceptable
    """

    tradeoffs: list[str] = field(default_factory=list)
    """
    What's being sacrificed in this compromise.

    Should be specific and actionable:
        - "Solution quality 8% below target"
        - "Error handling incomplete"
        - "2 edge cases not covered"

    NOT vague statements like "not perfect" or "needs work".
    """

    def explain(self) -> str:
        """
        Human-readable explanation of the compromise.

        Returns a formatted string suitable for display to user.

        Returns:
            Multi-line explanation with score, gap, and tradeoffs

        Example output:
            Compromise Solution (score: 72.0%)
            Gap to acceptable: 8.0%
            Tradeoffs:
              - Solution quality 8% below target
              - Edge case handling incomplete
        """
        lines = [
            f"Compromise Solution (score: {self.score:.1%})",
            f"Gap to acceptable: {self.gap_to_acceptable:.1%}",
        ]

        if self.tradeoffs:
            lines.append("Tradeoffs:")
            for tradeoff in self.tradeoffs:
                lines.append(f"  - {tradeoff}")
        else:
            lines.append("Tradeoffs: None documented")

        return "\n".join(lines)

    def explain_path(self) -> str:
        """
        Explain the reasoning path to this compromise.

        Returns a formatted string showing how the solution was derived.

        Returns:
            Multi-line path explanation

        Example output:
            Reasoning path (4 steps):
            1. [0.30] How do we solve X?
            2. [0.45] Consider approach A
            3. [0.62] Refine approach A with constraint B
            4. [0.72] Implementation of refined approach
        """
        lines = [f"Reasoning path ({len(self.path)} steps):"]

        for i, thought in enumerate(self.path, 1):
            # Truncate content for display
            content = str(thought.content)[:50]
            if len(str(thought.content)) > 50:
                content += "..."
            lines.append(f"  {i}. [{thought.score:.2f}] {content}")

        return "\n".join(lines)

    @property
    def content(self) -> T:
        """
        Shortcut to access the solution content.

        Returns:
            The content of the compromise thought
        """
        return self.thought.content

    @property
    def is_close_to_acceptable(self) -> bool:
        """
        Whether this compromise is close to acceptable.

        "Close" means within 10% of acceptable threshold.

        Returns:
            True if gap_to_acceptable < 0.10
        """
        return self.gap_to_acceptable < 0.10

    def __str__(self) -> str:
        """String representation."""
        return f"CompromiseSolution(score={self.score:.1%}, gap={self.gap_to_acceptable:.1%})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"CompromiseSolution("
            f"score={self.score}, "
            f"gap={self.gap_to_acceptable}, "
            f"tradeoffs={self.tradeoffs})"
        )
