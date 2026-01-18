"""
Failure Anticipation - Predict and Prevent Problems
====================================================

This module predicts failure modes before they happen and suggests
prevention or mitigation strategies.

PROBLEM STATEMENT
-----------------

Reactive failure handling is too late:

    # Current approach
    try:
        result = await search(graph, budget)
    except BudgetExhausted:
        print("Oops, ran out of budget")  # Too late to do anything

We need PROACTIVE failure anticipation that:
1. Monitors for warning signs during search
2. Predicts likely failures before they occur
3. Suggests prevention strategies
4. Prepares mitigation if prevention fails


KNOWN FAILURE MODES
-------------------

We enumerate failure modes we can detect:

    BUDGET_EXHAUSTED
        Signs: High utilization, consumption rate > remaining / expansions_needed
        Prevention: Request budget increase early
        Mitigation: Accept compromise solution

    DEPTH_EXCEEDED
        Signs: Approaching hard limit without acceptable solution
        Prevention: Widen beam, try different branches
        Mitigation: Return best found at current depth

    QUALITY_PLATEAU
        Signs: Scores not improving over multiple depths
        Prevention: Increase diversity, try different generator
        Mitigation: Accept current best as potential local maximum

    CIRCULAR_REASONING
        Signs: Semantic similarity between thoughts, repeated content
        Prevention: Add deduplication, increase diversity
        Mitigation: Prune duplicates, force novel generation

    GROUNDING_FAILURE
        Signs: High rate of failed verifications
        Prevention: More conservative generation, simpler solutions
        Mitigation: Focus on groundable subproblems

    GENERATOR_EXHAUSTION
        Signs: Low-quality/repetitive generations
        Prevention: Temperature increase, different prompts
        Mitigation: Switch to different generator or stop


HOW THIS MODULE FITS IN
-----------------------

    ┌─────────────────────────────────────────────────────────────┐
    │                  AdaptiveSearchController                   │
    │                     (controller.py)                         │
    │                                                             │
    │  Each iteration:                                            │
    │    anticipated = anticipator.anticipate(graph, budget, ...) │
    │    for failure in anticipated:                              │
    │        if failure.likelihood > 0.7:                         │
    │            handle_anticipated_failure(failure)              │
    └─────────────────────────────────────────────────────────────┘
                              │
                              │ calls anticipate()
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   FailureAnticipator                        │
    │                                                             │
    │  Has detectors for each failure mode:                       │
    │    - BudgetExhaustionDetector                               │
    │    - DepthExceededDetector                                  │
    │    - QualityPlateauDetector                                 │
    │    - CircularReasoningDetector                              │
    │                                                             │
    │  Each detector assesses likelihood and suggests actions     │
    └─────────────────────────────────────────────────────────────┘
                              │
                              │ returns list of
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                   AnticipatedFailure                        │
    │                                                             │
    │  mode: Which failure mode (from FailureMode enum)           │
    │  likelihood: 0.0 to 1.0                                     │
    │  estimated_when: Depth/iteration when likely                │
    │  prevention: What could prevent it                          │
    │  mitigation: What to do if it happens                       │
    └─────────────────────────────────────────────────────────────┘


DETECTOR PATTERN
----------------

Each detector follows the same pattern:

    class SomeFailureDetector:
        def assess(self, state: SearchState) -> FailureAssessment:
            # Analyze state for warning signs
            # Return likelihood and suggestions

            return FailureAssessment(
                likelihood=0.7,
                estimated_when=current_depth + 3,
                prevention="Do X to prevent",
                mitigation="If happens, do Y",
            )

Detectors are independent and can be added/removed easily.


HANDLING ANTICIPATED FAILURES
-----------------------------

When a high-likelihood failure is detected:

    for failure in anticipated:
        if failure.likelihood > 0.7:
            # Try prevention first
            if failure.prevention:
                success = await try_prevention(failure)
                if success:
                    continue  # Crisis averted

            # Ask for guidance
            action = await feedback_handler.handle_anticipated_failure(failure)

            if action == FailureAction.ABORT:
                return build_result(reason=f"Anticipated: {failure.mode}")


RELATIONSHIP TO OTHER MODULES
-----------------------------

    failure.py (this file)
        │
        ├── Used by: controller.py (AdaptiveSearchController)
        │   Controller calls anticipate() each iteration
        │
        ├── Triggers: feedback.py (FeedbackHandler)
        │   High-likelihood failures may need guidance
        │
        └── Uses: SearchState (internal)
            Bundles graph, budget, score_history for analysis


USAGE EXAMPLE
-------------

    from graph_of_thought_v2.adaptive import (
        FailureAnticipator,
        FailureMode,
    )

    anticipator = FailureAnticipator()

    # During search loop
    anticipated = anticipator.anticipate(
        graph=graph,
        budget=budget,
        score_history=score_history,
        config=config,
    )

    for failure in anticipated:
        print(f"Warning: {failure.mode.name}")
        print(f"  Likelihood: {failure.likelihood:.1%}")
        print(f"  Prevention: {failure.prevention}")
        print(f"  Mitigation: {failure.mitigation}")

"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from graph_of_thought_v2.core import Graph
    from graph_of_thought_v2.context import Budget


# =============================================================================
# FAILURE MODE ENUM
# =============================================================================

class FailureMode(Enum):
    """
    Known failure modes for Graph of Thought search.

    Each mode has:
    - Characteristic warning signs
    - Prevention strategies
    - Mitigation strategies

    Used by: AnticipatedFailure.mode, detector selection
    """

    BUDGET_EXHAUSTED = auto()
    """
    Ran out of tokens before finding acceptable solution.

    Warning signs:
        - Budget utilization > 80%
        - Consumption rate suggests exhaustion before goal

    Prevention:
        - Request budget increase proactively
        - Increase pruning aggressiveness

    Mitigation:
        - Accept best available compromise
        - Return partial solution with documentation
    """

    DEPTH_EXCEEDED = auto()
    """
    Hit maximum depth without finding acceptable solution.

    Warning signs:
        - Approaching hard limit
        - Score progress slowing near limit

    Prevention:
        - Try wider beam earlier
        - Backtrack to different branch

    Mitigation:
        - Return best at current depth
        - Suggest problem decomposition
    """

    QUALITY_PLATEAU = auto()
    """
    Scores stopped improving despite continued exploration.

    Warning signs:
        - Score variance < 1% over N depths
        - Best score unchanged for several iterations

    Prevention:
        - Increase generator diversity
        - Try different expansion strategy

    Mitigation:
        - Accept current best as local maximum
        - Suggest reformulating problem
    """

    CIRCULAR_REASONING = auto()
    """
    Thoughts are repeating or semantically cycling.

    Warning signs:
        - High semantic similarity between thoughts
        - Repeated content patterns
        - Thoughts referencing earlier thoughts

    Prevention:
        - Enable semantic deduplication
        - Increase temperature/diversity

    Mitigation:
        - Prune duplicate branches
        - Force novel generation direction
    """

    GROUNDING_FAILURE = auto()
    """
    Generated solutions failing verification at high rate.

    Warning signs:
        - > 50% of grounded thoughts fail verification
        - Consistent failure patterns

    Prevention:
        - More conservative generation
        - Break problem into simpler parts

    Mitigation:
        - Focus on groundable subproblems
        - Return ungrounded but high-scoring solution
    """

    GENERATOR_EXHAUSTION = auto()
    """
    Generator producing low-quality or repetitive outputs.

    Warning signs:
        - Declining average child scores
        - High similarity between siblings
        - Increasing rejection rate

    Prevention:
        - Vary prompts/context
        - Adjust temperature

    Mitigation:
        - Switch generator
        - Accept current best
    """

    EVALUATOR_UNRELIABLE = auto()
    """
    Scores are inconsistent or unreliable.

    Warning signs:
        - High variance in scores for similar thoughts
        - Scores don't correlate with grounding results

    Prevention:
        - Use ensemble evaluation
        - Calibrate evaluator

    Mitigation:
        - Rely more on grounding
        - Use simpler heuristics
    """


# =============================================================================
# FAILURE ASSESSMENT
# =============================================================================

@dataclass(frozen=True)
class FailureAssessment:
    """
    Assessment from a single failure detector.

    Describes the likelihood of a specific failure mode
    and what to do about it.

    Attributes:
        likelihood: Probability of this failure (0.0 to 1.0)
        estimated_when: When failure likely to occur (depth/iteration)
        prevention: Strategy to prevent the failure
        mitigation: Strategy if failure occurs anyway

    Created by: Individual failure detectors
    Used by: FailureAnticipator to build AnticipatedFailure

    Example:
        FailureAssessment(
            likelihood=0.75,
            estimated_when=12,  # At depth 12
            prevention="Request 10000 more tokens now",
            mitigation="Accept compromise at score 0.68",
        )
    """

    likelihood: float = 0.0
    """
    Probability this failure will occur (0.0 to 1.0).

    Thresholds:
        - < 0.3: Low concern, monitor only
        - 0.3 - 0.7: Moderate concern, consider prevention
        - > 0.7: High concern, act now
    """

    estimated_when: int | None = None
    """
    Estimated depth/iteration when failure will occur.

    None if can't estimate timing.
    Used to prioritize prevention timing.
    """

    prevention: str | None = None
    """
    Strategy to prevent this failure.

    Should be actionable and specific:
        - "Request 5000 additional tokens"
        - "Switch to wider beam (5 instead of 3)"

    None if no prevention available.
    """

    mitigation: str | None = None
    """
    Strategy if failure occurs despite prevention.

    The "Plan B" for when prevention fails:
        - "Accept compromise at score 0.65"
        - "Return best path found so far"

    None if no mitigation available (fatal failure).
    """


# =============================================================================
# ANTICIPATED FAILURE
# =============================================================================

@dataclass(frozen=True)
class AnticipatedFailure:
    """
    A failure mode that might occur.

    Combines failure mode identification with assessment data.

    Attributes:
        mode: Which failure mode (from FailureMode enum)
        likelihood: Probability (0.0 to 1.0)
        estimated_when: When likely to occur
        prevention: What could prevent it
        mitigation: What to do if it happens

    Created by: FailureAnticipator.anticipate()
    Used by: AdaptiveSearchController

    Example:
        AnticipatedFailure(
            mode=FailureMode.BUDGET_EXHAUSTED,
            likelihood=0.8,
            estimated_when=None,  # Imminent
            prevention="Request budget increase",
            mitigation="Accept compromise solution",
        )
    """

    mode: FailureMode
    likelihood: float
    estimated_when: int | None = None
    prevention: str | None = None
    mitigation: str | None = None

    def __str__(self) -> str:
        """Human-readable representation."""
        lines = [
            f"AnticipatedFailure: {self.mode.name}",
            f"  Likelihood: {self.likelihood:.1%}",
        ]

        if self.estimated_when is not None:
            lines.append(f"  Expected at: depth {self.estimated_when}")

        if self.prevention:
            lines.append(f"  Prevention: {self.prevention}")

        if self.mitigation:
            lines.append(f"  Mitigation: {self.mitigation}")

        return "\n".join(lines)

    @property
    def is_high_risk(self) -> bool:
        """Whether this is a high-risk failure (> 70% likelihood)."""
        return self.likelihood > 0.7

    @property
    def is_imminent(self) -> bool:
        """Whether failure is imminent (within 2 depths or unknown timing)."""
        return self.estimated_when is None or self.estimated_when <= 2


# =============================================================================
# SEARCH STATE (Internal)
# =============================================================================

@dataclass
class SearchState:
    """
    Bundled search state for failure detection.

    Groups the data that detectors need to analyze.
    Internal to this module.

    Attributes:
        graph: Current thought graph
        budget: Current budget state
        score_history: Best scores at each depth
        config: Search configuration
        current_depth: Current search depth
        grounding_stats: Optional grounding success/failure stats
    """

    graph: Any  # Graph
    budget: Any  # Budget
    score_history: list[float]
    config: Any  # SearchConfig
    current_depth: int = 0
    grounding_stats: dict[str, int] = field(default_factory=dict)


# =============================================================================
# FAILURE DETECTOR PROTOCOL
# =============================================================================

class FailureDetector(Protocol):
    """
    Protocol for failure detection.

    Each detector monitors for one type of failure.
    Implement this protocol to add new failure detection.

    Example implementation:
        class MyFailureDetector:
            def assess(self, state: SearchState) -> FailureAssessment:
                # Analyze state
                if warning_signs_detected:
                    return FailureAssessment(
                        likelihood=0.8,
                        prevention="Do something",
                    )
                return FailureAssessment(likelihood=0.1)
    """

    def assess(self, state: SearchState) -> FailureAssessment:
        """
        Assess likelihood of this failure mode.

        Args:
            state: Current search state

        Returns:
            FailureAssessment with likelihood and suggestions
        """
        ...


# =============================================================================
# CONCRETE DETECTORS
# =============================================================================

class BudgetExhaustionDetector:
    """
    Detects impending budget exhaustion.

    Analyzes consumption rate and remaining budget to predict
    whether we'll run out before reaching acceptable solution.

    Warning signs:
        - High utilization (> 80%)
        - Consumption rate exceeds remaining / needed_expansions
    """

    def assess(self, state: SearchState) -> FailureAssessment:
        """Assess likelihood of budget exhaustion."""
        budget = state.budget

        # Already exhausted
        if budget.remaining <= 0:
            return FailureAssessment(
                likelihood=1.0,
                prevention=None,  # Too late
                mitigation="Accept best available solution",
            )

        # Calculate consumption rate
        thoughts = list(state.graph.all_thoughts())
        if not thoughts:
            return FailureAssessment(likelihood=0.1)

        tokens_per_thought = budget.consumed / len(thoughts) if thoughts else 0

        # Estimate if we can reach acceptable
        current_best = max((t.score for t in thoughts), default=0.0)
        acceptable = 0.70  # TODO: Get from config

        if current_best >= acceptable:
            return FailureAssessment(likelihood=0.0)

        # Estimate progress rate
        if len(state.score_history) < 2:
            # Not enough data, estimate based on utilization
            utilization = budget.consumed / budget.total if budget.total > 0 else 1.0
            return FailureAssessment(
                likelihood=utilization * 0.5,
                prevention="Monitor budget closely",
            )

        # Calculate if budget will last
        score_gap = acceptable - current_best
        progress_rate = (state.score_history[-1] - state.score_history[0]) / len(state.score_history)

        if progress_rate <= 0:
            return FailureAssessment(
                likelihood=0.9,
                prevention="No progress being made, try different approach",
                mitigation="Accept current best or terminate",
            )

        thoughts_needed = score_gap / progress_rate
        tokens_needed = thoughts_needed * tokens_per_thought

        if tokens_needed > budget.remaining:
            shortage = tokens_needed - budget.remaining
            likelihood = min(1.0, shortage / tokens_needed)

            return FailureAssessment(
                likelihood=likelihood,
                prevention=f"Request {int(shortage)} additional tokens",
                mitigation="Accept compromise solution",
            )

        return FailureAssessment(
            likelihood=0.2,
            prevention="Budget appears sufficient",
        )


class QualityPlateauDetector:
    """
    Detects when score improvement has stalled.

    Analyzes score history for signs of plateau.

    Warning signs:
        - Score variance < 1% over last N iterations
        - No improvement in best score for several depths
    """

    def __init__(self, plateau_window: int = 5):
        self.plateau_window = plateau_window

    def assess(self, state: SearchState) -> FailureAssessment:
        """Assess likelihood of quality plateau."""
        history = state.score_history

        if len(history) < self.plateau_window:
            return FailureAssessment(likelihood=0.1)

        # Check recent scores for plateau
        recent = history[-self.plateau_window:]
        variance = max(recent) - min(recent)
        improvement = recent[-1] - recent[0]

        if variance < 0.01 and improvement < 0.01:
            # Definitely plateaued
            return FailureAssessment(
                likelihood=0.9,
                prevention="Try wider beam or different branch",
                mitigation="Accept current best as local maximum",
            )

        if variance < 0.02:
            # Possibly plateauing
            return FailureAssessment(
                likelihood=0.5,
                prevention="Increase generator diversity",
                mitigation="Consider accepting current solution",
            )

        return FailureAssessment(likelihood=0.1)


class CircularReasoningDetector:
    """
    Detects when thoughts are repeating or cycling.

    Analyzes thought content for duplicates and patterns.

    Warning signs:
        - Multiple thoughts with same/similar content
        - Cyclic reference patterns
    """

    def assess(self, state: SearchState) -> FailureAssessment:
        """Assess likelihood of circular reasoning."""
        thoughts = list(state.graph.all_thoughts())

        if len(thoughts) < 5:
            return FailureAssessment(likelihood=0.1)

        # Check for exact duplicates (simple heuristic)
        contents = [str(t.content)[:100] for t in thoughts]  # First 100 chars
        unique = set(contents)

        duplication_rate = 1 - (len(unique) / len(contents))

        if duplication_rate > 0.3:
            return FailureAssessment(
                likelihood=0.8,
                prevention="Enable semantic deduplication",
                mitigation="Prune duplicate branches",
            )

        if duplication_rate > 0.1:
            return FailureAssessment(
                likelihood=0.4,
                prevention="Increase generation diversity",
            )

        return FailureAssessment(likelihood=duplication_rate)


class DepthExceededDetector:
    """
    Detects when approaching depth limit without solution.

    Analyzes current depth vs limits and progress.

    Warning signs:
        - Within 2 depths of hard limit
        - No acceptable solution found
    """

    def assess(self, state: SearchState) -> FailureAssessment:
        """Assess likelihood of depth limit being exceeded."""
        current = state.current_depth
        hard_limit = getattr(state.config, 'max_depth', 15)

        if current >= hard_limit:
            return FailureAssessment(
                likelihood=1.0,
                prevention=None,
                mitigation="Return best found",
            )

        remaining = hard_limit - current

        if remaining <= 2:
            # Very close to limit
            thoughts = list(state.graph.all_thoughts())
            best = max((t.score for t in thoughts), default=0.0)

            if best < 0.70:  # Below acceptable
                return FailureAssessment(
                    likelihood=0.8,
                    estimated_when=hard_limit,
                    prevention="Try different branch urgently",
                    mitigation="Accept best available",
                )

        if remaining <= 5:
            return FailureAssessment(
                likelihood=0.3,
                estimated_when=hard_limit,
                prevention="Consider backtracking if stuck",
            )

        return FailureAssessment(likelihood=0.1)


# =============================================================================
# FAILURE ANTICIPATOR
# =============================================================================

class FailureAnticipator:
    """
    Predicts and prepares for failure modes.

    Runs multiple detectors to identify potential failures
    before they occur, enabling prevention or mitigation.

    Attributes:
        detectors: Map of failure modes to their detectors
        concern_threshold: Likelihood threshold to report (default 0.3)

    Example:
        anticipator = FailureAnticipator()

        # During search
        failures = anticipator.anticipate(graph, budget, scores, config)

        for failure in failures:
            if failure.is_high_risk:
                take_action(failure)
    """

    def __init__(self, concern_threshold: float = 0.3):
        """
        Initialize with default detectors.

        Args:
            concern_threshold: Only report failures above this likelihood
        """
        self.concern_threshold = concern_threshold

        self.detectors: dict[FailureMode, FailureDetector] = {
            FailureMode.BUDGET_EXHAUSTED: BudgetExhaustionDetector(),
            FailureMode.QUALITY_PLATEAU: QualityPlateauDetector(),
            FailureMode.CIRCULAR_REASONING: CircularReasoningDetector(),
            FailureMode.DEPTH_EXCEEDED: DepthExceededDetector(),
        }

    def anticipate(
        self,
        graph: Any,
        budget: Any,
        score_history: list[float],
        config: Any,
        current_depth: int = 0,
    ) -> list[AnticipatedFailure]:
        """
        Analyze current state and predict likely failures.

        Runs all registered detectors and returns anticipated failures
        above the concern threshold, sorted by likelihood.

        Args:
            graph: Current thought graph
            budget: Current budget state
            score_history: Best scores at each depth
            config: Search configuration
            current_depth: Current search depth

        Returns:
            List of AnticipatedFailure, sorted by likelihood (highest first)

        Example:
            failures = anticipator.anticipate(graph, budget, scores, config)

            for f in failures:
                print(f"{f.mode.name}: {f.likelihood:.1%}")
        """
        state = SearchState(
            graph=graph,
            budget=budget,
            score_history=score_history,
            config=config,
            current_depth=current_depth,
        )

        predictions: list[AnticipatedFailure] = []

        for mode, detector in self.detectors.items():
            assessment = detector.assess(state)

            if assessment.likelihood >= self.concern_threshold:
                predictions.append(AnticipatedFailure(
                    mode=mode,
                    likelihood=assessment.likelihood,
                    estimated_when=assessment.estimated_when,
                    prevention=assessment.prevention,
                    mitigation=assessment.mitigation,
                ))

        # Sort by likelihood (highest first)
        predictions.sort(key=lambda p: p.likelihood, reverse=True)

        return predictions

    def add_detector(self, mode: FailureMode, detector: FailureDetector) -> None:
        """
        Add or replace a failure detector.

        Args:
            mode: The failure mode this detector handles
            detector: The detector implementation
        """
        self.detectors[mode] = detector

    def remove_detector(self, mode: FailureMode) -> None:
        """
        Remove a failure detector.

        Args:
            mode: The failure mode to stop detecting
        """
        self.detectors.pop(mode, None)
