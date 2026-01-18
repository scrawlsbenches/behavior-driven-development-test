"""
Budget Negotiation - Resource Management with Negotiation
==========================================================

This module handles budget management that can negotiate for more resources
or propose compromises instead of simply failing.

PROBLEM STATEMENT
-----------------

The existing budget handling is binary:

    # From middleware/budget.py
    if budget.is_exhausted:
        raise BudgetExhausted()  # Hard failure

This is problematic because:
1. We might be 90% of the way to a solution
2. The caller doesn't know WHY more budget would help
3. There's no opportunity to approve additional resources
4. No compromise is offered

We need NEGOTIATING budget management that:
1. Assesses the current situation
2. Estimates what additional budget might achieve
3. Can request more resources with justification
4. Can propose compromises when full solution isn't achievable


HOW THIS MODULE FITS IN
-----------------------

    ┌─────────────────────────────────────────────────────────────┐
    │                  AdaptiveSearchController                   │
    │                     (controller.py)                         │
    └─────────────────────────────────────────────────────────────┘
                              │
                              │ 1. assess_situation()
                              │ 2. negotiate()
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    BudgetNegotiator                         │
    │                                                             │
    │  assess_situation(graph, budget) → BudgetSituation          │
    │  negotiate(situation, graph) → BudgetNegotiationResult      │
    │                                                             │
    │  Knows:                                                     │
    │    - acceptable_threshold (minimum acceptable score)        │
    │    - goal_threshold (ideal score)                           │
    │    - compromise_threshold (minimum for compromise)          │
    │    - tokens_per_expansion (for estimation)                  │
    └─────────────────────────────────────────────────────────────┘
                              │
                              │ returns
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                BudgetNegotiationResult                      │
    │                                                             │
    │  decision: BudgetDecision                                   │
    │    - SUFFICIENT: Budget is enough, continue                 │
    │    - REQUEST_INCREASE: Ask for more with justification      │
    │    - PROPOSE_COMPROMISE: Offer good-enough solution         │
    │    - TERMINATE: No options, cannot continue                 │
    │                                                             │
    │  requested_amount: int (if REQUEST_INCREASE)                │
    │  justification: str (why we need more)                      │
    │  compromise: CompromiseSolution (if PROPOSE_COMPROMISE)     │
    └─────────────────────────────────────────────────────────────┘


DECISION LOGIC
--------------

The BudgetNegotiator makes decisions based on:

1. ALREADY ACCEPTABLE
   If best_score >= acceptable_threshold → SUFFICIENT
   "We already have an acceptable solution, budget doesn't matter."

2. BUDGET REMAINING
   If budget.remaining > tokens_per_expansion → SUFFICIENT
   "We have budget left, keep going."

3. BUDGET EXHAUSTED, EVALUATE OPTIONS

   a. CLOSE TO ACCEPTABLE
      If estimated_tokens_for_acceptable < budget_total * 0.5 → REQUEST_INCREASE
      "We're close! A small additional budget could get us there."

   b. COMPROMISE AVAILABLE
      If best_score >= compromise_threshold → PROPOSE_COMPROMISE
      "We can't reach goal, but here's a decent alternative."

   c. NO OPTIONS
      → TERMINATE
      "Can't continue, no acceptable compromise available."


ESTIMATION LOGIC
----------------

To estimate tokens needed for a target score:

    1. Calculate historical progress rate:
       total_expansions = len(thoughts) - len(roots)
       score_improvement = current_best - initial_score
       improvement_per_expansion = score_improvement / total_expansions

    2. Estimate expansions needed:
       score_gap = target_score - current_score
       expansions_needed = score_gap / improvement_per_expansion

    3. Convert to tokens:
       tokens_needed = expansions_needed * tokens_per_expansion

This is a rough estimate! Confidence decreases with:
- Fewer historical data points
- Higher variance in progress rate
- Larger score gaps


INTEGRATION WITH FEEDBACK
-------------------------

When BudgetNegotiationResult.decision == REQUEST_INCREASE:

    result = negotiator.negotiate(situation, graph)

    if result.decision == BudgetDecision.REQUEST_INCREASE:
        # Ask FeedbackHandler (see feedback.py)
        response = await feedback_handler.request_budget_increase(
            requested_amount=result.requested_amount,
            justification=result.justification,
            compromise=result.compromise,  # Alternative if denied
        )

        match response.decision:
            case BudgetResponse.APPROVED:
                budget = budget.add(response.additional_amount)
                # Continue with more budget
            case BudgetResponse.ACCEPT_COMPROMISE:
                return build_result(compromise=result.compromise)
            case BudgetResponse.DENY:
                return build_result(terminated=True, reason="Budget denied")


INTEGRATION WITH COMPROMISE
---------------------------

When a compromise is proposed, it comes with explicit tradeoffs:

    compromise = CompromiseSolution(
        thought=best_available_thought,
        path=path_to_that_thought,
        score=0.72,  # Below 0.80 goal
        gap_to_acceptable=0.08,
        tradeoffs=["Solution quality 8% below target"],
    )

See compromise.py for CompromiseSolution structure.


USAGE EXAMPLE
-------------

    from graph_of_thought_v2.adaptive import BudgetNegotiator, BudgetDecision

    negotiator = BudgetNegotiator(
        acceptable_threshold=0.70,
        goal_threshold=0.95,
        compromise_threshold=0.50,
    )

    situation = negotiator.assess_situation(graph, budget)
    print(f"Best score: {situation.best_score_achieved:.1%}")
    print(f"Budget remaining: {situation.budget_remaining}")

    result = negotiator.negotiate(situation, graph)

    match result.decision:
        case BudgetDecision.SUFFICIENT:
            print("Continue searching")
        case BudgetDecision.REQUEST_INCREASE:
            print(f"Requesting {result.requested_amount} more tokens")
            print(f"Reason: {result.justification}")
        case BudgetDecision.PROPOSE_COMPROMISE:
            print(f"Proposing compromise: {result.compromise.explain()}")
        case BudgetDecision.TERMINATE:
            print("Cannot continue")


RELATIONSHIP TO OTHER MODULES
-----------------------------

    budget.py (this file)
        │
        ├── Used by: controller.py (AdaptiveSearchController)
        │   Controller calls assess_situation() and negotiate()
        │
        ├── Uses: compromise.py (CompromiseSolution)
        │   Creates CompromiseSolution when proposing alternatives
        │
        ├── Triggers: feedback.py (FeedbackHandler)
        │   When REQUEST_INCREASE, controller asks feedback handler
        │
        └── Configured by: profiles.py (DomainProfile)
            Each profile has domain-appropriate thresholds

    Relationship to middleware/budget.py:
        - middleware/budget.py: Binary enforcement (pass/fail)
        - adaptive/budget.py: Negotiating management (assess/propose/request)

        They can coexist:
        - Middleware catches catastrophic overruns
        - Negotiator handles graceful degradation

"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from graph_of_thought_v2.core import Graph, Thought
    from graph_of_thought_v2.context import Budget
    from graph_of_thought_v2.adaptive.compromise import CompromiseSolution


# =============================================================================
# BUDGET DECISION ENUM
# =============================================================================

class BudgetDecision(Enum):
    """
    Decisions that can result from budget negotiation.

    Used by: BudgetNegotiationResult.decision
    Handled by: AdaptiveSearchController (controller.py)
    """

    SUFFICIENT = auto()
    """
    Budget is sufficient to continue.

    Either:
    - We already have an acceptable solution
    - We have budget remaining to continue searching

    Controller behavior:
        continue search loop
    """

    REQUEST_INCREASE = auto()
    """
    Requesting additional budget with justification.

    We're close to acceptable but need more resources.
    Includes:
    - requested_amount: How much more we need
    - justification: Why we need it
    - compromise: Alternative if denied

    Controller behavior:
        response = await feedback_handler.request_budget_increase(...)
        act based on response
    """

    PROPOSE_COMPROMISE = auto()
    """
    Proposing a compromise solution.

    We can't reach the goal, but we have something usable.
    Includes:
    - compromise: The best we can offer with tradeoffs documented

    Controller behavior:
        return AdaptiveSearchResult(compromise=result.compromise)
        or ask feedback_handler to accept/reject
    """

    TERMINATE = auto()
    """
    Cannot continue. No acceptable compromise available.

    Budget exhausted AND no usable solution found.

    Controller behavior:
        return AdaptiveSearchResult(
            completed=False,
            reason="Budget exhausted with no acceptable solution"
        )
    """


# =============================================================================
# BUDGET SITUATION
# =============================================================================

@dataclass(frozen=True)
class BudgetSituation:
    """
    Assessment of current budget situation.

    Immutable snapshot of where we are with budget and progress.
    Created by BudgetNegotiator.assess_situation().

    Attributes:
        budget_remaining: Tokens remaining
        budget_consumed: Tokens used so far
        budget_total: Original budget
        best_score_achieved: Best score found so far
        acceptable_threshold: Minimum acceptable score
        goal_threshold: Ideal target score
        estimated_tokens_for_acceptable: Estimated tokens to reach acceptable
        estimated_tokens_for_goal: Estimated tokens to reach goal
        confidence_in_estimates: How confident we are (0.0 to 1.0)

    Created by: BudgetNegotiator.assess_situation()
    Used by: BudgetNegotiator.negotiate()

    Example:
        situation = BudgetSituation(
            budget_remaining=5000,
            budget_consumed=45000,
            budget_total=50000,
            best_score_achieved=0.68,
            acceptable_threshold=0.70,
            goal_threshold=0.95,
            estimated_tokens_for_acceptable=8000,
            estimated_tokens_for_goal=50000,
            confidence_in_estimates=0.6,
        )
        # Interpretation: We're close to acceptable, need ~8000 more tokens
    """

    # Budget state
    budget_remaining: int
    budget_consumed: int
    budget_total: int

    # Progress state
    best_score_achieved: float
    acceptable_threshold: float
    goal_threshold: float

    # Estimates
    estimated_tokens_for_acceptable: int | None
    estimated_tokens_for_goal: int | None
    confidence_in_estimates: float

    @property
    def utilization(self) -> float:
        """Budget utilization as fraction (0.0 to 1.0)."""
        if self.budget_total == 0:
            return 1.0
        return self.budget_consumed / self.budget_total

    @property
    def gap_to_acceptable(self) -> float:
        """Score gap to acceptable threshold (0.0 if already acceptable)."""
        return max(0.0, self.acceptable_threshold - self.best_score_achieved)

    @property
    def gap_to_goal(self) -> float:
        """Score gap to goal threshold (0.0 if already at goal)."""
        return max(0.0, self.goal_threshold - self.best_score_achieved)

    @property
    def has_acceptable_solution(self) -> bool:
        """Whether we've already found an acceptable solution."""
        return self.best_score_achieved >= self.acceptable_threshold

    @property
    def has_goal_solution(self) -> bool:
        """Whether we've already found a goal-quality solution."""
        return self.best_score_achieved >= self.goal_threshold

    @property
    def is_budget_exhausted(self) -> bool:
        """Whether budget is effectively exhausted."""
        return self.budget_remaining <= 0

    def __str__(self) -> str:
        """Human-readable summary."""
        return (
            f"BudgetSituation:\n"
            f"  Budget: {self.budget_consumed}/{self.budget_total} "
            f"({self.utilization:.1%} used, {self.budget_remaining} remaining)\n"
            f"  Score: {self.best_score_achieved:.1%} "
            f"(acceptable: {self.acceptable_threshold:.1%}, "
            f"goal: {self.goal_threshold:.1%})\n"
            f"  Gap to acceptable: {self.gap_to_acceptable:.1%}\n"
            f"  Estimated tokens for acceptable: {self.estimated_tokens_for_acceptable}\n"
            f"  Confidence: {self.confidence_in_estimates:.1%}"
        )


# =============================================================================
# BUDGET NEGOTIATION RESULT
# =============================================================================

@dataclass(frozen=True)
class BudgetNegotiationResult:
    """
    Result of budget negotiation.

    Describes what action to take and includes any necessary data
    for that action (requested amount, compromise, etc.).

    Attributes:
        decision: What action to take (see BudgetDecision)
        requested_amount: Tokens requested (if REQUEST_INCREASE)
        justification: Why we need more (if REQUEST_INCREASE)
        compromise: Compromise solution (if PROPOSE_COMPROMISE or as fallback)
        situation: The BudgetSituation that led to this decision

    Created by: BudgetNegotiator.negotiate()
    Used by: AdaptiveSearchController

    Example (requesting increase):
        BudgetNegotiationResult(
            decision=BudgetDecision.REQUEST_INCREASE,
            requested_amount=8000,
            justification="Current best: 68%. Need ~8000 tokens to reach 70%.",
            compromise=CompromiseSolution(...),  # Fallback if denied
            situation=situation,
        )

    Example (proposing compromise):
        BudgetNegotiationResult(
            decision=BudgetDecision.PROPOSE_COMPROMISE,
            compromise=CompromiseSolution(score=0.65, tradeoffs=[...]),
            situation=situation,
        )
    """

    decision: BudgetDecision
    requested_amount: int | None = None
    justification: str | None = None
    compromise: Any | None = None  # Actually CompromiseSolution, avoiding circular import
    situation: BudgetSituation | None = None

    def __str__(self) -> str:
        """Human-readable summary."""
        parts = [f"BudgetNegotiationResult({self.decision.name})"]

        if self.requested_amount is not None:
            parts.append(f"  Requesting: {self.requested_amount} tokens")

        if self.justification:
            parts.append(f"  Justification: {self.justification}")

        if self.compromise is not None:
            parts.append(f"  Compromise available: score={self.compromise.score:.1%}")

        return "\n".join(parts)


# =============================================================================
# BUDGET NEGOTIATOR
# =============================================================================

@dataclass
class BudgetNegotiator:
    """
    Negotiates budget allocation during search.

    Instead of failing when budget runs out, this component:
    1. Assesses the current situation
    2. Estimates what additional budget might achieve
    3. Proposes either a budget increase or a compromise

    Attributes:
        acceptable_threshold: Minimum score to consider acceptable (e.g., 0.70)
        goal_threshold: Ideal target score (e.g., 0.95)
        compromise_threshold: Minimum score for a compromise (e.g., 0.50)
        tokens_per_expansion: Estimated tokens per thought expansion

    Configuration guidance:
        - acceptable_threshold: What's "good enough" for the domain
        - goal_threshold: What's "ideal" - search stops early if reached
        - compromise_threshold: Below this, don't even offer compromise
        - tokens_per_expansion: Measure empirically or estimate ~1500

    See profiles.py for domain-specific configurations.

    Example:
        negotiator = BudgetNegotiator(
            acceptable_threshold=0.70,
            goal_threshold=0.95,
            compromise_threshold=0.50,
            tokens_per_expansion=1500,
        )

        situation = negotiator.assess_situation(graph, budget)
        result = negotiator.negotiate(situation, graph)
    """

    acceptable_threshold: float = 0.70
    """
    Score threshold for "acceptable" solution.

    Above this: We have something usable.
    Below this: Need to keep searching or compromise.

    Domain guidance:
        - Code generation: 0.75-0.85 (code should mostly work)
        - Research: 0.60-0.70 (synthesis can be partial)
        - Debugging: 0.70-0.80 (fix should resolve issue)
    """

    goal_threshold: float = 0.95
    """
    Score threshold for "goal" solution.

    Above this: Ideal solution, stop searching.
    This triggers early termination in controller.

    Usually set high (0.90-0.99) since it's the ideal.
    """

    compromise_threshold: float = 0.50
    """
    Minimum score to offer as compromise.

    Below this: Don't even suggest it as an option.
    Above this but below acceptable: Offer as compromise with tradeoffs.

    Domain guidance:
        - Code generation: 0.40-0.50 (partial solution might help)
        - Research: 0.40-0.50 (preliminary findings)
        - Debugging: 0.50-0.60 (hypothesis worth investigating)
    """

    tokens_per_expansion: int = 1500
    """
    Estimated tokens per thought expansion.

    Used for estimating budget needs:
        tokens_needed = expansions_needed * tokens_per_expansion

    Includes:
        - Generator call: ~500-1000 tokens (prompt + response)
        - Evaluator call: ~200-500 tokens (per child)
        - Overhead: ~100-200 tokens

    Measure empirically for your setup, or use 1500 as reasonable default.
    """

    def assess_situation(
        self,
        graph: Any,  # Actually Graph, avoiding circular import
        budget: Any,  # Actually Budget, avoiding circular import
    ) -> BudgetSituation:
        """
        Assess current budget situation.

        Analyzes the graph and budget to understand:
        - How much budget is left
        - What score we've achieved
        - How much more budget we might need

        Args:
            graph: The thought graph being searched
            budget: Current budget state

        Returns:
            BudgetSituation with complete assessment

        Implementation notes:
            - Finds best thought in graph by score
            - Calculates historical progress rate
            - Estimates tokens needed for acceptable/goal
            - Computes confidence based on data available

        Example:
            situation = negotiator.assess_situation(graph, budget)
            print(situation)  # Detailed breakdown
        """
        # Find best thought
        all_thoughts = list(graph.all_thoughts())

        if not all_thoughts:
            # Empty graph, return default situation
            return BudgetSituation(
                budget_remaining=budget.remaining,
                budget_consumed=budget.consumed,
                budget_total=budget.total,
                best_score_achieved=0.0,
                acceptable_threshold=self.acceptable_threshold,
                goal_threshold=self.goal_threshold,
                estimated_tokens_for_acceptable=None,
                estimated_tokens_for_goal=None,
                confidence_in_estimates=0.0,
            )

        best_thought = max(all_thoughts, key=lambda t: t.score)

        # Estimate tokens needed
        estimated_for_acceptable = self._estimate_tokens_to_score(
            current_score=best_thought.score,
            target_score=self.acceptable_threshold,
            graph=graph,
        )

        estimated_for_goal = self._estimate_tokens_to_score(
            current_score=best_thought.score,
            target_score=self.goal_threshold,
            graph=graph,
        )

        confidence = self._estimate_confidence(graph)

        return BudgetSituation(
            budget_remaining=budget.remaining,
            budget_consumed=budget.consumed,
            budget_total=budget.total,
            best_score_achieved=best_thought.score,
            acceptable_threshold=self.acceptable_threshold,
            goal_threshold=self.goal_threshold,
            estimated_tokens_for_acceptable=estimated_for_acceptable,
            estimated_tokens_for_goal=estimated_for_goal,
            confidence_in_estimates=confidence,
        )

    def negotiate(
        self,
        situation: BudgetSituation,
        graph: Any,  # Actually Graph
    ) -> BudgetNegotiationResult:
        """
        Negotiate based on current situation.

        Decides what action to take given the budget situation.

        Args:
            situation: Current budget situation (from assess_situation)
            graph: The thought graph (for finding compromise if needed)

        Returns:
            BudgetNegotiationResult with decision and supporting data

        Decision logic:
            1. If already acceptable → SUFFICIENT
            2. If budget remaining → SUFFICIENT
            3. If budget exhausted:
               a. If close to acceptable → REQUEST_INCREASE
               b. If compromise available → PROPOSE_COMPROMISE
               c. Otherwise → TERMINATE

        Example:
            result = negotiator.negotiate(situation, graph)

            if result.decision == BudgetDecision.REQUEST_INCREASE:
                print(f"Need {result.requested_amount} more tokens")
                print(f"Because: {result.justification}")
        """
        # -----------------------------------------------------------------
        # Case 1: Already have acceptable solution
        # -----------------------------------------------------------------
        if situation.has_acceptable_solution:
            return BudgetNegotiationResult(
                decision=BudgetDecision.SUFFICIENT,
                situation=situation,
            )

        # -----------------------------------------------------------------
        # Case 2: Budget remaining
        # -----------------------------------------------------------------
        if situation.budget_remaining > self.tokens_per_expansion:
            return BudgetNegotiationResult(
                decision=BudgetDecision.SUFFICIENT,
                situation=situation,
            )

        # -----------------------------------------------------------------
        # Case 3: Budget exhausted, evaluate options
        # -----------------------------------------------------------------

        # Can we reach acceptable with reasonable additional budget?
        if situation.estimated_tokens_for_acceptable is not None:
            additional_needed = situation.estimated_tokens_for_acceptable

            # If additional budget is less than 50% of original, request it
            if additional_needed < situation.budget_total * 0.5:
                compromise = self._find_compromise(graph, situation)

                return BudgetNegotiationResult(
                    decision=BudgetDecision.REQUEST_INCREASE,
                    requested_amount=additional_needed,
                    justification=self._build_justification(situation),
                    compromise=compromise,  # Fallback if denied
                    situation=situation,
                )

        # Look for compromise
        compromise = self._find_compromise(graph, situation)

        if compromise is not None:
            return BudgetNegotiationResult(
                decision=BudgetDecision.PROPOSE_COMPROMISE,
                compromise=compromise,
                situation=situation,
            )

        # No options left
        return BudgetNegotiationResult(
            decision=BudgetDecision.TERMINATE,
            situation=situation,
        )

    def _estimate_tokens_to_score(
        self,
        current_score: float,
        target_score: float,
        graph: Any,
    ) -> int | None:
        """
        Estimate tokens needed to reach target score.

        Based on observed progress rate in the graph.

        Args:
            current_score: Current best score
            target_score: Target score to reach
            graph: The thought graph (for historical data)

        Returns:
            Estimated tokens, or None if can't estimate

        Algorithm:
            1. Calculate improvement per expansion from history
            2. Estimate expansions needed for score gap
            3. Convert to tokens

        Limitations:
            - Assumes linear progress (usually optimistic)
            - Less accurate with less data
            - Doesn't account for diminishing returns
        """
        if current_score >= target_score:
            return 0

        thoughts = list(graph.all_thoughts())
        if len(thoughts) < 2:
            return None

        # Calculate historical progress rate
        roots = list(graph.roots())
        total_expansions = len(thoughts) - len(roots)

        if total_expansions == 0:
            return None

        # Find initial score (from roots)
        initial_score = max((t.score for t in roots), default=0.0)
        score_improvement = current_score - initial_score

        if score_improvement <= 0:
            return None

        improvement_per_expansion = score_improvement / total_expansions

        if improvement_per_expansion <= 0:
            return None

        # Estimate expansions needed
        score_gap = target_score - current_score
        expansions_needed = int(score_gap / improvement_per_expansion) + 1

        # Convert to tokens
        return expansions_needed * self.tokens_per_expansion

    def _build_justification(self, situation: BudgetSituation) -> str:
        """
        Build human-readable justification for budget request.

        Args:
            situation: Current budget situation

        Returns:
            Multi-line justification string
        """
        lines = [
            f"Current best score: {situation.best_score_achieved:.1%}",
            f"Acceptable threshold: {situation.acceptable_threshold:.1%}",
            f"Gap to acceptable: {situation.gap_to_acceptable:.1%}",
            f"Budget utilization: {situation.utilization:.1%}",
        ]

        if situation.estimated_tokens_for_acceptable is not None:
            lines.append(
                f"Estimated tokens needed: {situation.estimated_tokens_for_acceptable}"
            )

        lines.append(f"Confidence in estimate: {situation.confidence_in_estimates:.1%}")

        return "\n".join(lines)

    def _find_compromise(
        self,
        graph: Any,
        situation: BudgetSituation,
    ) -> Any | None:  # Returns CompromiseSolution | None
        """
        Find best compromise solution.

        Looks for thoughts above compromise_threshold that could
        serve as a "good enough" alternative.

        Args:
            graph: The thought graph
            situation: Current budget situation

        Returns:
            CompromiseSolution if found, None otherwise

        See compromise.py for CompromiseSolution structure.
        """
        # Import here to avoid circular import
        from graph_of_thought_v2.adaptive.compromise import CompromiseSolution

        thoughts = list(graph.all_thoughts())

        # Filter to thoughts above compromise threshold
        candidates = [
            t for t in thoughts
            if t.score >= self.compromise_threshold
        ]

        if not candidates:
            return None

        # Find best candidate
        best = max(candidates, key=lambda t: t.score)

        # Build path to this thought
        path = graph.path_to_root(best)[::-1]  # Reverse to root-first

        # Identify tradeoffs
        tradeoffs = self._identify_tradeoffs(best.score, situation)

        return CompromiseSolution(
            thought=best,
            path=path,
            score=best.score,
            gap_to_acceptable=situation.acceptable_threshold - best.score,
            tradeoffs=tradeoffs,
        )

    def _identify_tradeoffs(
        self,
        score: float,
        situation: BudgetSituation,
    ) -> list[str]:
        """
        Identify what's being sacrificed in a compromise.

        Args:
            score: The compromise score
            situation: Current situation (for thresholds)

        Returns:
            List of tradeoff descriptions
        """
        tradeoffs = []

        gap = situation.acceptable_threshold - score

        if gap > 0.2:
            tradeoffs.append(
                f"Solution quality significantly below target "
                f"({gap:.1%} gap)"
            )
        elif gap > 0.1:
            tradeoffs.append(
                f"Solution quality moderately below target "
                f"({gap:.1%} gap)"
            )
        elif gap > 0:
            tradeoffs.append(
                f"Solution quality slightly below target "
                f"({gap:.1%} gap)"
            )

        # Add domain-specific tradeoffs could be added here

        return tradeoffs

    def _estimate_confidence(self, graph: Any) -> float:
        """
        Estimate confidence in our predictions.

        More data points = higher confidence.

        Args:
            graph: The thought graph

        Returns:
            Confidence score from 0.0 to 1.0
        """
        thoughts = list(graph.all_thoughts())

        # More thoughts = more data = higher confidence
        thought_factor = min(1.0, len(thoughts) / 50)

        # Cap at 80% - estimates are never certain
        return thought_factor * 0.8
