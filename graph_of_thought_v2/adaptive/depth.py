"""
Depth Management - Adaptive Depth Control with Feedback
========================================================

This module manages search depth with soft/hard limits and feedback loops.

PROBLEM STATEMENT
-----------------

Fixed depth limits are problematic:

    config = SearchConfig(max_depth=10)
    # What if the problem needs depth 3? We waste resources.
    # What if the problem needs depth 15? We stop too early.
    # What if we're at depth 9 with score 0.94? Should we stop or continue?

We need ADAPTIVE depth that:
1. Has soft limits (pause and evaluate)
2. Has hard limits (safety bounds)
3. Monitors progress rate
4. Detects stagnation
5. Can request feedback when uncertain


HOW THIS MODULE FITS IN
-----------------------

    ┌─────────────────────────────────────────────────────────────┐
    │                  AdaptiveSearchController                   │
    │                     (controller.py)                         │
    └─────────────────────────────────────────────────────────────┘
                              │
                              │ calls evaluate_depth() each iteration
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                      DepthPolicy                            │
    │                                                             │
    │  Input:                                                     │
    │    - current_depth: int                                     │
    │    - score_history: list[float] (best score at each depth)  │
    │                                                             │
    │  Output:                                                    │
    │    - DepthDecision with action and reasoning                │
    └─────────────────────────────────────────────────────────────┘
                              │
                              │ returns
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                     DepthDecision                           │
    │                                                             │
    │  action: DepthAction                                        │
    │    - CONTINUE: Keep exploring deeper                        │
    │    - STOP: Hard stop, return best found                     │
    │    - REQUEST_FEEDBACK: Ask for guidance                     │
    │    - BACKTRACK: Try a different branch                      │
    │                                                             │
    │  reason: str (why this decision)                            │
    │  suggestion: str (what to do about it)                      │
    └─────────────────────────────────────────────────────────────┘


DECISION LOGIC
--------------

The DepthPolicy makes decisions based on:

1. HARD LIMIT CHECK
   If current_depth >= hard_limit → STOP
   "We've gone as deep as allowed. Return best result."

2. SOFT LIMIT CHECK (when current_depth >= soft_limit)
   Evaluate whether continuing is worthwhile:

   a. PROGRESS RATE
      Calculate: (score[-1] - score[-2]) / 1 depth
      If progress_rate < min_progress_rate → REQUEST_FEEDBACK
      "Progress is slowing. Should we continue?"

   b. STAGNATION
      Check last N scores for plateau (variance < threshold)
      If stagnating → REQUEST_FEEDBACK
      "Scores have plateaued. Try different approach?"

3. NORMAL OPERATION (below soft limit)
   → CONTINUE
   "Still exploring, keep going."


INTEGRATION WITH FEEDBACK
-------------------------

When DepthDecision.action == REQUEST_FEEDBACK:

    decision = depth_policy.evaluate_depth(depth, scores)

    if decision.action == DepthAction.REQUEST_FEEDBACK:
        # Ask FeedbackHandler (see feedback.py)
        feedback = await feedback_handler.request_depth_feedback(
            current_depth=depth,
            score_history=scores,
            decision=decision,
        )

        match feedback.directive:
            case FeedbackDirective.CONTINUE_DEEPER:
                # Extend soft limit and continue
                depth_policy.soft_limit += feedback.additional_depth
            case FeedbackDirective.STOP_AND_RETURN:
                # Return current best
                return build_result()
            case FeedbackDirective.TRY_DIFFERENT_BRANCH:
                # Backtrack (handled by controller)
                pass


CONFIGURATION
-------------

DepthPolicy is configured with:

    depth_policy = DepthPolicy(
        soft_limit=7,              # Pause and evaluate at depth 7
        hard_limit=15,             # Never go beyond depth 15
        min_progress_rate=0.05,    # Expect 5% score improvement per depth
        stagnation_threshold=3,    # Worry after 3 depths without improvement
    )

Different domains need different settings:
- Code generation: Lower soft limit (solutions found quickly or not at all)
- Research: Higher soft limit (exploration takes longer)
- Debugging: Medium limits (hypothesis testing)

See profiles.py for domain-specific configurations.


USAGE EXAMPLE
-------------

    from graph_of_thought_v2.adaptive import DepthPolicy, DepthAction

    policy = DepthPolicy(soft_limit=5, hard_limit=10)
    score_history = [0.3, 0.45, 0.52, 0.58, 0.60, 0.61]  # Slowing down

    decision = policy.evaluate_depth(
        current_depth=5,
        score_history=score_history,
    )

    print(decision.action)      # DepthAction.REQUEST_FEEDBACK
    print(decision.reason)      # "Progress slowing: 1.7% < 5.0%"
    print(decision.suggestion)  # "May need different approach or more resources"


RELATIONSHIP TO OTHER MODULES
-----------------------------

    depth.py (this file)
        │
        ├── Used by: controller.py (AdaptiveSearchController)
        │   Controller calls evaluate_depth() each iteration
        │
        ├── Triggers: feedback.py (FeedbackHandler)
        │   When REQUEST_FEEDBACK, controller asks feedback handler
        │
        └── Configured by: profiles.py (DomainProfile)
            Each profile has domain-appropriate depth settings

"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Future type imports if needed


# =============================================================================
# DEPTH ACTION ENUM
# =============================================================================

class DepthAction(Enum):
    """
    Actions that can be taken based on depth evaluation.

    Used by: DepthDecision.action
    Handled by: AdaptiveSearchController (controller.py)
    """

    CONTINUE = auto()
    """
    Continue exploring deeper.

    Controller behavior:
        current_depth += 1
        continue search loop
    """

    STOP = auto()
    """
    Hard stop. Return best result found.

    Controller behavior:
        return AdaptiveSearchResult(completed=True, ...)
    """

    REQUEST_FEEDBACK = auto()
    """
    Uncertain whether to continue. Ask for guidance.

    Controller behavior:
        feedback = await feedback_handler.request_depth_feedback(...)
        act based on feedback.directive
    """

    BACKTRACK = auto()
    """
    Current branch exhausted. Try a different one.

    Controller behavior:
        beam = select_alternative_beam(graph, ...)
        current_depth = depth_of_new_beam
    """


# =============================================================================
# DEPTH DECISION
# =============================================================================

@dataclass(frozen=True)
class DepthDecision:
    """
    Result of evaluating current depth.

    This is an immutable data structure describing what to do,
    not how to do it. The controller interprets and acts on it.

    Attributes:
        action: What action to take (see DepthAction)
        reason: Human-readable explanation of why
        suggestion: What might help if action is REQUEST_FEEDBACK
        estimated_additional_depth_needed: If we think we know how much more

    Created by: DepthPolicy.evaluate_depth()
    Used by: AdaptiveSearchController

    Example:
        DepthDecision(
            action=DepthAction.REQUEST_FEEDBACK,
            reason="Progress slowing: 2% < 5% threshold",
            suggestion="Consider wider beam or different branch",
            estimated_additional_depth_needed=3,
        )
    """

    action: DepthAction
    reason: str = ""
    suggestion: str = ""
    estimated_additional_depth_needed: int | None = None

    def __str__(self) -> str:
        """Human-readable representation."""
        parts = [f"DepthDecision({self.action.name})"]
        if self.reason:
            parts.append(f"  Reason: {self.reason}")
        if self.suggestion:
            parts.append(f"  Suggestion: {self.suggestion}")
        return "\n".join(parts)


# =============================================================================
# DEPTH POLICY
# =============================================================================

@dataclass
class DepthPolicy:
    """
    Policy for managing search depth with feedback loops.

    This class encapsulates the rules for deciding whether to continue
    exploring deeper or pause for feedback.

    Attributes:
        soft_limit: Depth at which to evaluate whether to continue.
                   Can be extended based on feedback.
        hard_limit: Absolute maximum depth. Never exceeded.
        min_progress_rate: Minimum score improvement per depth to justify continuing.
                          E.g., 0.05 means expect 5% improvement each level.
        stagnation_threshold: Number of depths without meaningful improvement
                             before considering the search stagnant.

    Configuration guidance:
        - soft_limit < hard_limit (always)
        - soft_limit ~ 50-70% of expected solution depth
        - min_progress_rate depends on domain (higher for code, lower for research)
        - stagnation_threshold typically 2-5

    See profiles.py for domain-specific configurations.

    Example:
        policy = DepthPolicy(
            soft_limit=7,
            hard_limit=15,
            min_progress_rate=0.05,
            stagnation_threshold=3,
        )

        decision = policy.evaluate_depth(current_depth=8, score_history=[...])
    """

    soft_limit: int = 7
    """
    Depth at which to pause and evaluate progress.

    When current_depth >= soft_limit, the policy evaluates:
    - Is progress rate acceptable?
    - Are scores stagnating?

    If concerns, returns REQUEST_FEEDBACK.
    Can be dynamically extended when feedback approves more depth.
    """

    hard_limit: int = 15
    """
    Absolute maximum depth. Search stops here regardless.

    This is a safety bound to prevent:
    - Infinite loops
    - Resource exhaustion
    - Runaway searches

    Should be set based on domain knowledge:
    - Code: 10-15 (solutions found quickly or not at all)
    - Research: 15-25 (longer exploration acceptable)
    - Debugging: 10-15 (hypothesis chains shouldn't be too long)
    """

    min_progress_rate: float = 0.05
    """
    Minimum expected score improvement per depth.

    Calculated as: (score[d] - score[d-1]) for each depth d.
    If recent progress < min_progress_rate, triggers concern.

    Example:
        min_progress_rate = 0.05 (5%)
        score_history = [0.5, 0.54, 0.545]
        recent_progress = 0.545 - 0.54 = 0.005 (0.5%)
        0.5% < 5% → REQUEST_FEEDBACK

    Domain guidance:
        - Code generation: 0.05-0.10 (expect clear progress)
        - Research: 0.02-0.05 (slower, more exploratory)
        - Debugging: 0.03-0.07 (hypothesis refinement)
    """

    stagnation_threshold: int = 3
    """
    Number of depths with minimal improvement before stagnation.

    If the last N scores have variance < 1%, consider stagnant.

    Example:
        stagnation_threshold = 3
        score_history = [..., 0.72, 0.73, 0.725, 0.728]
        Last 3: [0.73, 0.725, 0.728] - variance ~0.3%
        → Stagnating, REQUEST_FEEDBACK
    """

    def evaluate_depth(
        self,
        current_depth: int,
        score_history: list[float],
    ) -> DepthDecision:
        """
        Evaluate whether to continue deeper.

        This is the main decision method. Called by AdaptiveSearchController
        at each depth level to determine next action.

        Args:
            current_depth: Current search depth (0 = root)
            score_history: Best score at each depth [score_0, score_1, ...]

        Returns:
            DepthDecision with action and reasoning

        Decision flow:
            1. Check hard limit → STOP if exceeded
            2. Check soft limit → evaluate progress if exceeded
               a. Check progress rate → REQUEST_FEEDBACK if too slow
               b. Check stagnation → REQUEST_FEEDBACK if stagnant
            3. Otherwise → CONTINUE

        Example:
            decision = policy.evaluate_depth(
                current_depth=8,
                score_history=[0.3, 0.45, 0.55, 0.62, 0.67, 0.70, 0.72, 0.73],
            )
            # decision.action might be REQUEST_FEEDBACK due to slowing progress
        """
        # -----------------------------------------------------------------
        # HARD LIMIT: Absolute stop
        # -----------------------------------------------------------------
        if current_depth >= self.hard_limit:
            return DepthDecision(
                action=DepthAction.STOP,
                reason=f"Hard depth limit ({self.hard_limit}) reached",
                suggestion="Consider problem decomposition for deeper exploration",
            )

        # -----------------------------------------------------------------
        # SOFT LIMIT: Evaluate whether to continue
        # -----------------------------------------------------------------
        if current_depth >= self.soft_limit:
            # Check progress rate
            if len(score_history) >= 2:
                recent_progress = score_history[-1] - score_history[-2]

                if recent_progress < self.min_progress_rate:
                    return DepthDecision(
                        action=DepthAction.REQUEST_FEEDBACK,
                        reason=(
                            f"Progress slowing: {recent_progress:.1%} < "
                            f"{self.min_progress_rate:.1%} threshold"
                        ),
                        suggestion="May need different approach or more resources",
                        estimated_additional_depth_needed=self._estimate_needed_depth(
                            score_history
                        ),
                    )

            # Check for stagnation
            if self._is_stagnating(score_history):
                return DepthDecision(
                    action=DepthAction.REQUEST_FEEDBACK,
                    reason=(
                        f"Scores stagnating over last {self.stagnation_threshold} depths"
                    ),
                    suggestion="Current approach may be exhausted, try different branch",
                )

        # -----------------------------------------------------------------
        # NORMAL: Continue exploring
        # -----------------------------------------------------------------
        return DepthDecision(
            action=DepthAction.CONTINUE,
            reason=f"Depth {current_depth} within limits, continuing",
        )

    def _is_stagnating(self, score_history: list[float]) -> bool:
        """
        Check if scores have plateaued.

        Stagnation = last N scores have < 1% variance.

        Args:
            score_history: Scores at each depth

        Returns:
            True if stagnating, False otherwise
        """
        if len(score_history) < self.stagnation_threshold:
            return False

        recent = score_history[-self.stagnation_threshold:]
        max_score = max(recent)
        min_score = min(recent)
        variance = max_score - min_score

        # Less than 1% variation = stagnant
        return variance < 0.01

    def _estimate_needed_depth(self, score_history: list[float]) -> int | None:
        """
        Estimate additional depth needed to reach goal.

        Based on average progress rate and gap to 0.95 (typical goal).

        Args:
            score_history: Scores at each depth

        Returns:
            Estimated additional depths, or None if can't estimate
        """
        if len(score_history) < 2:
            return None

        # Average progress rate
        total_progress = score_history[-1] - score_history[0]
        avg_rate = total_progress / len(score_history)

        if avg_rate <= 0:
            return None

        # Gap to typical goal (0.95)
        goal = 0.95
        gap = goal - score_history[-1]

        if gap <= 0:
            return 0

        return int(gap / avg_rate) + 1

    def extend_soft_limit(self, additional_depth: int) -> None:
        """
        Extend the soft limit after receiving feedback approval.

        Called when FeedbackHandler approves deeper exploration.

        Args:
            additional_depth: How many more depths to allow

        Example:
            # Feedback approved 5 more depths
            policy.extend_soft_limit(5)
            # Now soft_limit is 5 higher (but still bounded by hard_limit)
        """
        new_limit = self.soft_limit + additional_depth
        self.soft_limit = min(new_limit, self.hard_limit)

    def reset(self, soft_limit: int | None = None) -> None:
        """
        Reset policy to initial state or new soft limit.

        Useful for restarting search or trying different branch.

        Args:
            soft_limit: New soft limit, or None to keep current
        """
        if soft_limit is not None:
            self.soft_limit = min(soft_limit, self.hard_limit)
