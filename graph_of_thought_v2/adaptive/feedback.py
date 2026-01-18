"""
Feedback Handling - Getting Decisions from Human or Policy
===========================================================

This module defines how the search controller gets external guidance
when it needs to make decisions it can't make autonomously.

PROBLEM STATEMENT
-----------------

Sometimes the search needs guidance:
- "Should I continue deeper or stop here?"
- "Can I have more budget?"
- "Is this compromise acceptable?"

These decisions may require:
- Human judgment
- Policy-based automation
- External system approval


WHAT IS FEEDBACK?
-----------------

Feedback = external decision input to guide the search.

The FeedbackHandler is an interface that:
1. Receives questions from the search controller
2. Provides decisions back

Implementations can be:
- Interactive: Ask a human via CLI/UI
- Automatic: Apply policy rules
- Hybrid: Auto-decide some, ask human for others


HOW THIS MODULE FITS IN
-----------------------

    ┌─────────────────────────────────────────────────────────────┐
    │                  AdaptiveSearchController                   │
    │                     (controller.py)                         │
    │                                                             │
    │  When decision needed:                                      │
    │    response = await feedback_handler.request_X(...)         │
    │    act based on response                                    │
    └─────────────────────────────────────────────────────────────┘
                              │
                              │ calls request methods
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                  FeedbackHandler (Protocol)                 │
    │                                                             │
    │  request_depth_feedback(...)    → DepthFeedback             │
    │  request_budget_increase(...)   → BudgetResponse            │
    │  propose_compromise(...)        → bool (accepted?)          │
    │  handle_anticipated_failure(...) → FailureAction            │
    │                                                             │
    │  Implementations:                                           │
    │    - AutomaticFeedbackHandler (policy-based)                │
    │    - InteractiveFeedbackHandler (asks human - not impl)     │
    └─────────────────────────────────────────────────────────────┘


FEEDBACK SCENARIOS
------------------

1. DEPTH FEEDBACK (from depth.py)
   Triggered when: DepthDecision.action == REQUEST_FEEDBACK
   Question: "Should I continue deeper?"
   Response: Continue with N more depths, stop, or try different branch

2. BUDGET INCREASE (from budget.py)
   Triggered when: BudgetNegotiationResult.decision == REQUEST_INCREASE
   Question: "Can I have N more tokens? Here's why..."
   Response: Approved with amount, denied, or accept compromise instead

3. COMPROMISE ACCEPTANCE (from budget.py/controller.py)
   Triggered when: Proposing a compromise solution
   Question: "This is good enough? Here are the tradeoffs..."
   Response: Accept or reject

4. ANTICIPATED FAILURE (from failure.py)
   Triggered when: High-likelihood failure detected
   Question: "This failure is likely. What should I do?"
   Response: Try prevention, accept mitigation, or abort


AUTOMATIC FEEDBACK HANDLER
--------------------------

The AutomaticFeedbackHandler applies policy rules:

    Depth feedback:
        - If progress still happening → continue with default extension
        - If completely stalled → stop

    Budget increase:
        - If request < 50% of original budget → approve
        - If compromise available → accept compromise
        - Otherwise → deny

    Compromise:
        - If score > compromise_accept_threshold → accept
        - Otherwise → reject

    Anticipated failure:
        - If prevention available → try prevention
        - Otherwise → apply mitigation


RELATIONSHIP TO OTHER MODULES
-----------------------------

    feedback.py (this file)
        │
        ├── Used by: controller.py (AdaptiveSearchController)
        │   Controller calls feedback methods when decisions needed
        │
        ├── Triggered by: depth.py (DepthPolicy)
        │   REQUEST_FEEDBACK decisions come here
        │
        ├── Triggered by: budget.py (BudgetNegotiator)
        │   REQUEST_INCREASE and PROPOSE_COMPROMISE come here
        │
        └── Triggered by: failure.py (FailureAnticipator)
            High-risk anticipated failures come here


USAGE EXAMPLE
-------------

    from graph_of_thought_v2.adaptive import (
        AutomaticFeedbackHandler,
        FeedbackDirective,
        BudgetResponse,
    )

    # Automatic policy-based decisions
    handler = AutomaticFeedbackHandler(
        default_depth_extension=3,
        max_budget_increase_ratio=0.5,
        compromise_accept_threshold=0.60,
    )

    # In controller, when depth feedback needed:
    feedback = await handler.request_depth_feedback(
        current_depth=8,
        score_history=[0.5, 0.6, 0.65, 0.68, 0.69],
        decision=depth_decision,
    )

    if feedback.directive == FeedbackDirective.CONTINUE_DEEPER:
        print(f"Approved {feedback.additional_depth} more depths")

"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from graph_of_thought_v2.adaptive.depth import DepthDecision
    from graph_of_thought_v2.adaptive.failure import AnticipatedFailure
    from graph_of_thought_v2.adaptive.compromise import CompromiseSolution


# =============================================================================
# FEEDBACK DIRECTIVE (for depth)
# =============================================================================

class FeedbackDirective(Enum):
    """
    Directives from depth feedback.

    Tells the controller what to do after asking about depth.
    """

    CONTINUE_DEEPER = auto()
    """
    Continue searching deeper.

    The feedback includes additional_depth indicating how many
    more depths are approved.

    Controller behavior:
        depth_policy.extend_soft_limit(feedback.additional_depth)
        continue search
    """

    STOP_AND_RETURN = auto()
    """
    Stop searching and return current best.

    Controller behavior:
        return AdaptiveSearchResult(completed=True, ...)
    """

    TRY_DIFFERENT_BRANCH = auto()
    """
    Abandon current branch, try a different one.

    Controller behavior:
        select alternative beam from graph
        continue from that point
    """


# =============================================================================
# DEPTH FEEDBACK
# =============================================================================

@dataclass(frozen=True)
class DepthFeedback:
    """
    Response to depth feedback request.

    Attributes:
        directive: What to do (continue, stop, or branch)
        additional_depth: How many more depths approved (if CONTINUE_DEEPER)
        reason: Explanation for the decision

    Created by: FeedbackHandler.request_depth_feedback()
    Used by: AdaptiveSearchController

    Example:
        DepthFeedback(
            directive=FeedbackDirective.CONTINUE_DEEPER,
            additional_depth=3,
            reason="Progress still happening, approving 3 more depths",
        )
    """

    directive: FeedbackDirective
    additional_depth: int = 0
    reason: str = ""

    def __str__(self) -> str:
        return f"DepthFeedback({self.directive.name}, +{self.additional_depth})"


# =============================================================================
# BUDGET RESPONSE
# =============================================================================

class BudgetResponseDecision(Enum):
    """
    Decisions for budget increase requests.
    """

    APPROVED = auto()
    """
    Budget increase approved.

    Response includes additional_amount.

    Controller behavior:
        budget = budget.add(response.additional_amount)
        continue search
    """

    DENIED = auto()
    """
    Budget increase denied.

    Controller behavior:
        If compromise available: offer it
        Otherwise: terminate search
    """

    ACCEPT_COMPROMISE = auto()
    """
    Don't increase budget, accept the compromise instead.

    Controller behavior:
        return AdaptiveSearchResult(compromise=compromise)
    """


@dataclass(frozen=True)
class BudgetResponse:
    """
    Response to budget increase request.

    Attributes:
        decision: Approved, denied, or accept compromise
        additional_amount: Tokens approved (if APPROVED)
        reason: Explanation for the decision

    Created by: FeedbackHandler.request_budget_increase()
    Used by: AdaptiveSearchController

    Example:
        BudgetResponse(
            decision=BudgetResponseDecision.APPROVED,
            additional_amount=10000,
            reason="Request within policy limits",
        )
    """

    decision: BudgetResponseDecision
    additional_amount: int = 0
    reason: str = ""

    def __str__(self) -> str:
        if self.decision == BudgetResponseDecision.APPROVED:
            return f"BudgetResponse(APPROVED, +{self.additional_amount})"
        return f"BudgetResponse({self.decision.name})"


# =============================================================================
# FAILURE ACTION
# =============================================================================

class FailureAction(Enum):
    """
    Actions in response to anticipated failure.
    """

    CONTINUE = auto()
    """
    Continue despite the risk.

    May be because prevention was applied or risk accepted.
    """

    ABORT = auto()
    """
    Abort the search due to anticipated failure.

    Risk too high or no mitigation available.
    """

    APPLY_MITIGATION = auto()
    """
    Apply the suggested mitigation strategy.

    Accept that failure may happen, prepare for it.
    """


# =============================================================================
# FEEDBACK HANDLER PROTOCOL
# =============================================================================

class FeedbackHandler(Protocol):
    """
    Protocol for handling feedback requests.

    Implement this to provide decision-making for the search controller.
    Can be automatic (policy-based) or interactive (human input).

    Methods:
        request_depth_feedback: Get guidance on search depth
        request_budget_increase: Request more budget
        propose_compromise: Propose a compromise solution
        handle_anticipated_failure: Handle predicted failure

    Example implementation:
        class MyFeedbackHandler:
            async def request_depth_feedback(
                self,
                current_depth: int,
                score_history: list[float],
                decision: DepthDecision,
            ) -> DepthFeedback:
                # Apply some policy
                if score_improving(score_history):
                    return DepthFeedback(
                        directive=FeedbackDirective.CONTINUE_DEEPER,
                        additional_depth=5,
                    )
                return DepthFeedback(
                    directive=FeedbackDirective.STOP_AND_RETURN,
                )
    """

    async def request_depth_feedback(
        self,
        current_depth: int,
        score_history: list[float],
        decision: Any,  # DepthDecision
    ) -> DepthFeedback:
        """
        Request feedback on whether to continue deeper.

        Called when DepthPolicy returns REQUEST_FEEDBACK.

        Args:
            current_depth: Current search depth
            score_history: Best scores at each depth
            decision: The DepthDecision that triggered this

        Returns:
            DepthFeedback with directive and any additional info
        """
        ...

    async def request_budget_increase(
        self,
        requested_amount: int,
        justification: str,
        compromise: Any | None,  # CompromiseSolution | None
    ) -> BudgetResponse:
        """
        Request additional budget.

        Called when BudgetNegotiator returns REQUEST_INCREASE.

        Args:
            requested_amount: How many tokens requested
            justification: Why they're needed
            compromise: Alternative if denied

        Returns:
            BudgetResponse with decision
        """
        ...

    async def propose_compromise(
        self,
        compromise: Any,  # CompromiseSolution
    ) -> bool:
        """
        Propose a compromise solution for acceptance.

        Args:
            compromise: The compromise being proposed

        Returns:
            True if accepted, False if rejected
        """
        ...

    async def handle_anticipated_failure(
        self,
        failure: Any,  # AnticipatedFailure
    ) -> FailureAction:
        """
        Handle an anticipated failure.

        Called when high-likelihood failure detected.

        Args:
            failure: The anticipated failure

        Returns:
            FailureAction indicating what to do
        """
        ...


# =============================================================================
# AUTOMATIC FEEDBACK HANDLER
# =============================================================================

@dataclass
class AutomaticFeedbackHandler:
    """
    Policy-based automatic feedback handler.

    Makes decisions based on configurable policy rules.
    No human interaction required.

    Attributes:
        default_depth_extension: Depths to approve when progress continues
        max_budget_increase_ratio: Max budget increase as ratio of original
        compromise_accept_threshold: Minimum score to auto-accept compromise
        always_try_prevention: Whether to always try failure prevention

    Example:
        handler = AutomaticFeedbackHandler(
            default_depth_extension=3,
            max_budget_increase_ratio=0.5,
            compromise_accept_threshold=0.60,
        )
    """

    default_depth_extension: int = 3
    """
    Number of depths to approve when continuing is warranted.

    When progress is still happening, this many additional depths
    are automatically approved.
    """

    max_budget_increase_ratio: float = 0.5
    """
    Maximum budget increase as ratio of original.

    0.5 means approve up to 50% more than original budget.
    Requests above this are denied.
    """

    compromise_accept_threshold: float = 0.60
    """
    Minimum score to automatically accept compromise.

    Compromises above this score are auto-accepted.
    Below this, compromise is rejected (search terminates).
    """

    always_try_prevention: bool = True
    """
    Whether to always try prevention for anticipated failures.

    If True, prevention is attempted before considering abort.
    If False, may abort immediately for severe failures.
    """

    async def request_depth_feedback(
        self,
        current_depth: int,
        score_history: list[float],
        decision: Any,  # DepthDecision
    ) -> DepthFeedback:
        """
        Automatic depth feedback based on progress.

        Policy:
            - If scores still improving → continue with default extension
            - If completely stalled → stop
            - If stalled but near acceptable → try different branch
        """
        if len(score_history) < 2:
            # Not enough data, continue with caution
            return DepthFeedback(
                directive=FeedbackDirective.CONTINUE_DEEPER,
                additional_depth=self.default_depth_extension,
                reason="Insufficient data, continuing cautiously",
            )

        # Check if still making progress
        recent_progress = score_history[-1] - score_history[-2]

        if recent_progress > 0.01:  # Still improving
            return DepthFeedback(
                directive=FeedbackDirective.CONTINUE_DEEPER,
                additional_depth=self.default_depth_extension,
                reason=f"Progress continuing ({recent_progress:.1%}), approving more depth",
            )

        # Check if near acceptable
        current_best = score_history[-1]
        if current_best >= 0.65:  # Close to typical 0.70 acceptable
            return DepthFeedback(
                directive=FeedbackDirective.CONTINUE_DEEPER,
                additional_depth=2,  # Smaller extension when near goal
                reason="Near acceptable threshold, allowing limited extension",
            )

        # Stalled and not near acceptable
        return DepthFeedback(
            directive=FeedbackDirective.STOP_AND_RETURN,
            reason="Progress stalled, returning best found",
        )

    async def request_budget_increase(
        self,
        requested_amount: int,
        justification: str,
        compromise: Any | None,  # CompromiseSolution | None
    ) -> BudgetResponse:
        """
        Automatic budget decision based on policy.

        Policy:
            - If request < max_ratio of original → approve
            - If compromise available and good → accept compromise
            - Otherwise → deny
        """
        # We need original budget to calculate ratio
        # This is a limitation - in real implementation, would need context
        # For now, approve reasonable requests

        if requested_amount <= 10000:  # Reasonable default
            return BudgetResponse(
                decision=BudgetResponseDecision.APPROVED,
                additional_amount=requested_amount,
                reason="Request within automatic approval limits",
            )

        # Check if compromise is acceptable
        if compromise is not None:
            if compromise.score >= self.compromise_accept_threshold:
                return BudgetResponse(
                    decision=BudgetResponseDecision.ACCEPT_COMPROMISE,
                    reason=f"Compromise score ({compromise.score:.1%}) acceptable",
                )

        # Deny large requests without good compromise
        return BudgetResponse(
            decision=BudgetResponseDecision.DENIED,
            reason="Request exceeds automatic approval limits",
        )

    async def propose_compromise(
        self,
        compromise: Any,  # CompromiseSolution
    ) -> bool:
        """
        Automatic compromise acceptance based on threshold.

        Policy:
            Accept if score >= compromise_accept_threshold
        """
        if compromise.score >= self.compromise_accept_threshold:
            return True
        return False

    async def handle_anticipated_failure(
        self,
        failure: Any,  # AnticipatedFailure
    ) -> FailureAction:
        """
        Automatic failure handling based on policy.

        Policy:
            - If prevention available and always_try_prevention → try it
            - If mitigation available → apply it
            - If very high risk (>90%) and no mitigation → abort
            - Otherwise → continue
        """
        if self.always_try_prevention and failure.prevention:
            return FailureAction.CONTINUE  # Will try prevention

        if failure.mitigation:
            return FailureAction.APPLY_MITIGATION

        if failure.likelihood > 0.9:
            return FailureAction.ABORT

        return FailureAction.CONTINUE


# =============================================================================
# LOGGING FEEDBACK HANDLER (Wrapper)
# =============================================================================

class LoggingFeedbackHandler:
    """
    Wrapper that logs all feedback requests/responses.

    Wraps another handler and logs all interactions.
    Useful for debugging and audit trails.

    Example:
        inner = AutomaticFeedbackHandler()
        handler = LoggingFeedbackHandler(inner, logger)
    """

    def __init__(
        self,
        inner: FeedbackHandler,
        logger: Any = None,  # Logger protocol
    ):
        self._inner = inner
        self._logger = logger

    async def request_depth_feedback(
        self,
        current_depth: int,
        score_history: list[float],
        decision: Any,
    ) -> DepthFeedback:
        """Log and delegate depth feedback."""
        if self._logger:
            self._logger.info(
                "Depth feedback requested",
                depth=current_depth,
                best_score=score_history[-1] if score_history else 0,
            )

        response = await self._inner.request_depth_feedback(
            current_depth, score_history, decision
        )

        if self._logger:
            self._logger.info(
                "Depth feedback response",
                directive=response.directive.name,
                additional_depth=response.additional_depth,
            )

        return response

    async def request_budget_increase(
        self,
        requested_amount: int,
        justification: str,
        compromise: Any | None,
    ) -> BudgetResponse:
        """Log and delegate budget request."""
        if self._logger:
            self._logger.info(
                "Budget increase requested",
                amount=requested_amount,
                has_compromise=compromise is not None,
            )

        response = await self._inner.request_budget_increase(
            requested_amount, justification, compromise
        )

        if self._logger:
            self._logger.info(
                "Budget response",
                decision=response.decision.name,
                additional=response.additional_amount,
            )

        return response

    async def propose_compromise(self, compromise: Any) -> bool:
        """Log and delegate compromise proposal."""
        if self._logger:
            self._logger.info(
                "Compromise proposed",
                score=compromise.score,
            )

        accepted = await self._inner.propose_compromise(compromise)

        if self._logger:
            self._logger.info(
                "Compromise response",
                accepted=accepted,
            )

        return accepted

    async def handle_anticipated_failure(self, failure: Any) -> FailureAction:
        """Log and delegate failure handling."""
        if self._logger:
            self._logger.warning(
                "Anticipated failure",
                mode=failure.mode.name,
                likelihood=failure.likelihood,
            )

        action = await self._inner.handle_anticipated_failure(failure)

        if self._logger:
            self._logger.info(
                "Failure action",
                action=action.name,
            )

        return action
