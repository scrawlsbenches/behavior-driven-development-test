"""
Adaptive Search Controller - Orchestrating Self-Aware Search
=============================================================

This module contains the main controller that orchestrates adaptive search
by integrating all the other components.

THE CONTROLLER'S JOB
--------------------

The AdaptiveSearchController is the central orchestrator that:
1. Runs the search loop
2. Checks depth limits via DepthPolicy
3. Manages budget via BudgetNegotiator
4. Anticipates failures via FailureAnticipator
5. Grounds thoughts via Grounder (optional)
6. Gets external guidance via FeedbackHandler

It integrates all the pieces from this package into a coherent search.


SEARCH LOOP OVERVIEW
--------------------

    ┌─────────────────────────────────────────────────────────────────────┐
    │                        SEARCH LOOP                                  │
    │                                                                     │
    │  while not done:                                                    │
    │                                                                     │
    │      ┌──────────────────────────────────────────────────────────┐   │
    │      │ PHASE 1: ANTICIPATE FAILURES                             │   │
    │      │                                                          │   │
    │      │ anticipated = failure_anticipator.anticipate(...)        │   │
    │      │ for failure in anticipated:                              │   │
    │      │     if failure.is_high_risk:                             │   │
    │      │         handle_anticipated_failure(failure)              │   │
    │      └──────────────────────────────────────────────────────────┘   │
    │                              │                                      │
    │                              ▼                                      │
    │      ┌──────────────────────────────────────────────────────────┐   │
    │      │ PHASE 2: CHECK BUDGET                                    │   │
    │      │                                                          │   │
    │      │ situation = budget_negotiator.assess_situation(...)      │   │
    │      │ result = budget_negotiator.negotiate(...)                │   │
    │      │ handle budget decision (sufficient/request/compromise)   │   │
    │      └──────────────────────────────────────────────────────────┘   │
    │                              │                                      │
    │                              ▼                                      │
    │      ┌──────────────────────────────────────────────────────────┐   │
    │      │ PHASE 3: CHECK DEPTH                                     │   │
    │      │                                                          │   │
    │      │ decision = depth_policy.evaluate_depth(...)              │   │
    │      │ handle depth decision (continue/stop/feedback)           │   │
    │      └──────────────────────────────────────────────────────────┘   │
    │                              │                                      │
    │                              ▼                                      │
    │      ┌──────────────────────────────────────────────────────────┐   │
    │      │ PHASE 4: EXPAND AND EVALUATE                             │   │
    │      │                                                          │   │
    │      │ for thought in beam:                                     │   │
    │      │     children = await expander(thought, context)          │   │
    │      │     for child in children:                               │   │
    │      │         child.score = await evaluator(child, context)    │   │
    │      │         if grounder.can_ground(child):                   │   │
    │      │             result = await grounder.ground(child, ...)   │   │
    │      │             adjust_score(child, result)                  │   │
    │      └──────────────────────────────────────────────────────────┘   │
    │                              │                                      │
    │                              ▼                                      │
    │      ┌──────────────────────────────────────────────────────────┐   │
    │      │ PHASE 5: UPDATE STATE                                    │   │
    │      │                                                          │   │
    │      │ track best score                                         │   │
    │      │ select beam for next iteration                           │   │
    │      │ check for goal reached                                   │   │
    │      │ increment depth                                          │   │
    │      └──────────────────────────────────────────────────────────┘   │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘


DEPENDENCIES
------------

The controller depends on:

    FROM THIS PACKAGE (adaptive/):
        - DepthPolicy (depth.py): Depth limit management
        - BudgetNegotiator (budget.py): Budget negotiation
        - FailureAnticipator (failure.py): Failure prediction
        - FeedbackHandler (feedback.py): External guidance
        - Grounder (grounding.py): Optional verification
        - CompromiseSolution (compromise.py): Compromise results

    FROM CORE PACKAGE (core/):
        - Graph: The thought graph
        - Thought: Individual thoughts
        - SearchConfig: Search configuration (or similar)

    FROM SERVICES PACKAGE (services/):
        - Generator protocol: Creates child thoughts
        - Evaluator protocol: Scores thoughts

    FROM CONTEXT PACKAGE (context/):
        - Context: Execution context
        - Budget: Budget tracking


CONFIGURATION
-------------

The controller is configured with:

    controller = AdaptiveSearchController(
        # The graph to search
        graph=my_graph,

        # How to expand thoughts (from services/)
        expander=my_generator,

        # How to score thoughts (from services/)
        evaluator=my_evaluator,

        # Optional: verify thoughts
        grounder=my_grounder,  # or None

        # Search parameters
        config=SearchConfig(
            max_depth=10,
            beam_width=3,
            goal_score=0.95,
        ),

        # Depth management
        depth_policy=DepthPolicy(
            soft_limit=7,
            hard_limit=15,
        ),

        # Budget management
        budget_negotiator=BudgetNegotiator(
            acceptable_threshold=0.70,
            goal_threshold=0.95,
        ),

        # Failure detection
        failure_anticipator=FailureAnticipator(),

        # Decision making
        feedback_handler=AutomaticFeedbackHandler(),
    )


USAGE EXAMPLE
-------------

    from graph_of_thought_v2.adaptive import (
        AdaptiveSearchController,
        DepthPolicy,
        BudgetNegotiator,
        FailureAnticipator,
        AutomaticFeedbackHandler,
    )
    from graph_of_thought_v2.core import Graph, Thought
    from graph_of_thought_v2.services.implementations import SimpleGenerator, SimpleEvaluator

    # Create graph with initial problem
    graph = Graph()
    root = Thought(content="How do we solve X?")
    graph.add(root)

    # Create controller
    controller = AdaptiveSearchController(
        graph=graph,
        expander=SimpleGenerator(),
        evaluator=SimpleEvaluator(),
        grounder=None,  # No grounding
        config=SearchConfig(max_depth=10, beam_width=3, goal_score=0.95),
        depth_policy=DepthPolicy(soft_limit=7, hard_limit=15),
        budget_negotiator=BudgetNegotiator(),
        failure_anticipator=FailureAnticipator(),
        feedback_handler=AutomaticFeedbackHandler(),
    )

    # Run search
    budget = Budget(total=50000)
    result = await controller.search(budget)

    # Check result
    if result.goal_reached:
        print(f"Found solution: {result.best_path[-1].content}")
    elif result.compromise:
        print(f"Compromise: {result.compromise.explain()}")
    else:
        print(f"Failed: {result.termination_reason}")


RELATIONSHIP TO OTHER MODULES
-----------------------------

    controller.py (this file)
        │
        ├── Uses: depth.py (DepthPolicy)
        │   Checks depth limits each iteration
        │
        ├── Uses: budget.py (BudgetNegotiator)
        │   Manages budget negotiation
        │
        ├── Uses: failure.py (FailureAnticipator)
        │   Predicts failures each iteration
        │
        ├── Uses: feedback.py (FeedbackHandler)
        │   Gets external decisions when needed
        │
        ├── Uses: grounding.py (Grounder)
        │   Optionally verifies thoughts
        │
        ├── Uses: compromise.py (CompromiseSolution)
        │   Included in results when goal not reached
        │
        └── Configured by: profiles.py (DomainProfile)
            Provides pre-configured settings

    Relationship to core/search.py:
        - core/search.py: Pure beam search algorithm
        - adaptive/controller.py: Self-aware search with negotiation

        They serve different purposes:
        - core/search.py for simple, predictable search
        - controller.py for complex, adaptive search

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypeVar, Callable, Awaitable

if TYPE_CHECKING:
    from graph_of_thought_v2.core import Graph, Thought
    from graph_of_thought_v2.context import Context, Budget

# Type for thought content
T = TypeVar("T")


# =============================================================================
# SEARCH CONFIG (Simple version for this module)
# =============================================================================

@dataclass
class SearchConfig:
    """
    Configuration for adaptive search.

    Attributes:
        max_depth: Maximum search depth (hard limit handled by DepthPolicy)
        beam_width: Number of thoughts to keep at each level
        goal_score: Score threshold for early termination
        max_expansions: Maximum total expansions (safety limit)

    This is a simplified config. For full options, see application/options.py.
    """

    max_depth: int = 10
    beam_width: int = 3
    goal_score: float = 0.95
    max_expansions: int = 100


# =============================================================================
# ADAPTIVE SEARCH RESULT
# =============================================================================

@dataclass
class AdaptiveSearchResult(Generic[T]):
    """
    Result of adaptive search.

    Contains the search outcome plus metadata about the search process.

    Attributes:
        best_path: Path from root to best thought found
        best_score: Score of the best thought
        completed: Whether search completed normally
        goal_reached: Whether goal score was achieved
        termination_reason: Why search terminated (if not goal)
        compromise: Compromise solution if goal not reached
        thoughts_expanded: Total thoughts expanded
        max_depth_reached: Maximum depth explored
        budget_requests: History of budget negotiations
        anticipated_failures: Failures that were anticipated

    Example:
        AdaptiveSearchResult(
            best_path=[root, step1, step2, solution],
            best_score=0.92,
            completed=True,
            goal_reached=False,
            termination_reason="Depth limit reached",
            compromise=CompromiseSolution(...),
            thoughts_expanded=150,
            max_depth_reached=10,
        )
    """

    best_path: list[Any]  # list[Thought[T]]
    best_score: float
    completed: bool
    goal_reached: bool = False
    termination_reason: str | None = None
    compromise: Any | None = None  # CompromiseSolution
    thoughts_expanded: int = 0
    max_depth_reached: int = 0
    budget_requests: list[Any] = field(default_factory=list)  # BudgetNegotiationResult
    anticipated_failures: list[Any] = field(default_factory=list)  # AnticipatedFailure

    def __str__(self) -> str:
        """Human-readable summary."""
        status = "GOAL REACHED" if self.goal_reached else "completed" if self.completed else "terminated"
        lines = [
            f"AdaptiveSearchResult: {status}",
            f"  Best score: {self.best_score:.1%}",
            f"  Thoughts expanded: {self.thoughts_expanded}",
            f"  Max depth: {self.max_depth_reached}",
        ]

        if self.termination_reason:
            lines.append(f"  Reason: {self.termination_reason}")

        if self.compromise:
            lines.append(f"  Compromise available: score={self.compromise.score:.1%}")

        return "\n".join(lines)

    @property
    def has_solution(self) -> bool:
        """Whether any solution was found (goal or compromise)."""
        return self.goal_reached or self.compromise is not None

    @property
    def solution_score(self) -> float:
        """Score of the solution (best or compromise)."""
        if self.goal_reached:
            return self.best_score
        if self.compromise:
            return self.compromise.score
        return self.best_score


# =============================================================================
# ADAPTIVE SEARCH CONTROLLER
# =============================================================================

@dataclass
class AdaptiveSearchController(Generic[T]):
    """
    Orchestrates adaptive search with self-awareness.

    This is the main entry point for running adaptive searches.
    It integrates all components from this package.

    Attributes:
        graph: The thought graph to search
        expander: Function to generate child thoughts
        evaluator: Function to score thoughts
        grounder: Optional function to verify thoughts
        config: Search configuration
        depth_policy: Depth management policy
        budget_negotiator: Budget negotiation handler
        failure_anticipator: Failure prediction
        feedback_handler: External decision handler

    Type parameter T matches the thought content type.

    Example:
        controller = AdaptiveSearchController(
            graph=my_graph,
            expander=my_generator.generate,
            evaluator=my_evaluator.evaluate,
            grounder=my_grounder,
            config=SearchConfig(),
            depth_policy=DepthPolicy(),
            budget_negotiator=BudgetNegotiator(),
            failure_anticipator=FailureAnticipator(),
            feedback_handler=AutomaticFeedbackHandler(),
        )

        result = await controller.search(budget)
    """

    # Core components
    graph: Any  # Graph[T]
    """The thought graph being searched."""

    expander: Any  # Callable that generates children
    """
    Function to expand thoughts.

    Signature: async (thought, context) -> list[content]
    Usually from Generator.generate() in services/protocols.py
    """

    evaluator: Any  # Callable that scores thoughts
    """
    Function to score thoughts.

    Signature: async (thought, context) -> float
    Usually from Evaluator.evaluate() in services/protocols.py
    """

    grounder: Any | None = None  # Grounder[T] | None
    """
    Optional grounder for verification.

    If provided, promising thoughts are verified against reality.
    See grounding.py for Grounder protocol.
    """

    # Configuration
    config: SearchConfig = field(default_factory=SearchConfig)
    """Search configuration (depth, beam width, goal score)."""

    # Adaptive components
    depth_policy: Any = None  # DepthPolicy
    """
    Depth management policy.

    If None, uses default DepthPolicy().
    See depth.py.
    """

    budget_negotiator: Any = None  # BudgetNegotiator
    """
    Budget negotiation handler.

    If None, uses default BudgetNegotiator().
    See budget.py.
    """

    failure_anticipator: Any = None  # FailureAnticipator
    """
    Failure prediction.

    If None, uses default FailureAnticipator().
    See failure.py.
    """

    feedback_handler: Any = None  # FeedbackHandler
    """
    External decision handler.

    If None, uses AutomaticFeedbackHandler().
    See feedback.py.
    """

    def __post_init__(self):
        """Initialize default components if not provided."""
        # Import here to avoid circular imports at module level
        from graph_of_thought_v2.adaptive.depth import DepthPolicy
        from graph_of_thought_v2.adaptive.budget import BudgetNegotiator
        from graph_of_thought_v2.adaptive.failure import FailureAnticipator
        from graph_of_thought_v2.adaptive.feedback import AutomaticFeedbackHandler

        if self.depth_policy is None:
            self.depth_policy = DepthPolicy()

        if self.budget_negotiator is None:
            self.budget_negotiator = BudgetNegotiator()

        if self.failure_anticipator is None:
            self.failure_anticipator = FailureAnticipator()

        if self.feedback_handler is None:
            self.feedback_handler = AutomaticFeedbackHandler()

    async def search(
        self,
        budget: Any,  # Budget
    ) -> AdaptiveSearchResult[T]:
        """
        Execute adaptive search.

        This is the main entry point. Runs the search loop with all
        adaptive features enabled.

        Args:
            budget: Budget for the search operation

        Returns:
            AdaptiveSearchResult with outcome and metadata

        The search loop:
            1. Anticipate failures
            2. Check budget
            3. Check depth
            4. Expand and evaluate
            5. Update state
            6. Repeat until done

        Example:
            budget = Budget(total=50000)
            result = await controller.search(budget)

            if result.goal_reached:
                print("Success!")
            elif result.compromise:
                print(f"Compromise: {result.compromise.explain()}")
        """
        # Import types for this method
        from graph_of_thought_v2.adaptive.depth import DepthAction
        from graph_of_thought_v2.adaptive.budget import BudgetDecision
        from graph_of_thought_v2.adaptive.feedback import (
            FeedbackDirective,
            BudgetResponseDecision,
            FailureAction,
        )
        from graph_of_thought_v2.adaptive.grounding import GroundingContext

        # Initialize search state
        score_history: list[float] = []
        current_depth = 0
        beam = list(self.graph.roots())
        all_anticipated_failures: list[Any] = []
        all_budget_requests: list[Any] = []
        thoughts_expanded = 0

        # Get initial scores for roots
        for thought in beam:
            if thought.score == 0:
                thought.score = await self._evaluate_thought(thought, current_depth)

        if beam:
            score_history.append(max(t.score for t in beam))

        # Main search loop
        while True:
            # =================================================================
            # PHASE 1: ANTICIPATE FAILURES
            # =================================================================
            anticipated = self.failure_anticipator.anticipate(
                graph=self.graph,
                budget=budget,
                score_history=score_history,
                config=self.config,
                current_depth=current_depth,
            )
            all_anticipated_failures.extend(anticipated)

            # Handle high-risk failures
            for failure in anticipated:
                if failure.likelihood > 0.7:
                    action = await self.feedback_handler.handle_anticipated_failure(
                        failure
                    )
                    if action == FailureAction.ABORT:
                        return self._build_result(
                            completed=False,
                            reason=f"Aborted due to anticipated failure: {failure.mode.name}",
                            score_history=score_history,
                            thoughts_expanded=thoughts_expanded,
                            budget_requests=all_budget_requests,
                            anticipated_failures=all_anticipated_failures,
                        )

            # =================================================================
            # PHASE 2: CHECK BUDGET
            # =================================================================
            situation = self.budget_negotiator.assess_situation(self.graph, budget)
            negotiation = self.budget_negotiator.negotiate(situation, self.graph)
            all_budget_requests.append(negotiation)

            if negotiation.decision == BudgetDecision.REQUEST_INCREASE:
                response = await self.feedback_handler.request_budget_increase(
                    requested_amount=negotiation.requested_amount or 0,
                    justification=negotiation.justification or "",
                    compromise=negotiation.compromise,
                )

                if response.decision == BudgetResponseDecision.APPROVED:
                    # Would update budget here - for now, continue
                    pass
                elif response.decision == BudgetResponseDecision.ACCEPT_COMPROMISE:
                    return self._build_result(
                        completed=True,
                        compromise=negotiation.compromise,
                        score_history=score_history,
                        thoughts_expanded=thoughts_expanded,
                        budget_requests=all_budget_requests,
                        anticipated_failures=all_anticipated_failures,
                    )
                else:  # DENIED
                    return self._build_result(
                        completed=False,
                        reason="Budget increase denied",
                        score_history=score_history,
                        thoughts_expanded=thoughts_expanded,
                        budget_requests=all_budget_requests,
                        anticipated_failures=all_anticipated_failures,
                    )

            elif negotiation.decision == BudgetDecision.PROPOSE_COMPROMISE:
                accepted = await self.feedback_handler.propose_compromise(
                    negotiation.compromise
                )
                if accepted:
                    return self._build_result(
                        completed=True,
                        compromise=negotiation.compromise,
                        score_history=score_history,
                        thoughts_expanded=thoughts_expanded,
                        budget_requests=all_budget_requests,
                        anticipated_failures=all_anticipated_failures,
                    )

            elif negotiation.decision == BudgetDecision.TERMINATE:
                return self._build_result(
                    completed=False,
                    reason="Budget exhausted with no acceptable solution",
                    score_history=score_history,
                    thoughts_expanded=thoughts_expanded,
                    budget_requests=all_budget_requests,
                    anticipated_failures=all_anticipated_failures,
                )

            # =================================================================
            # PHASE 3: CHECK DEPTH
            # =================================================================
            depth_decision = self.depth_policy.evaluate_depth(
                current_depth, score_history
            )

            if depth_decision.action == DepthAction.STOP:
                return self._build_result(
                    completed=True,
                    reason=depth_decision.reason,
                    score_history=score_history,
                    thoughts_expanded=thoughts_expanded,
                    budget_requests=all_budget_requests,
                    anticipated_failures=all_anticipated_failures,
                )

            elif depth_decision.action == DepthAction.REQUEST_FEEDBACK:
                feedback = await self.feedback_handler.request_depth_feedback(
                    current_depth=current_depth,
                    score_history=score_history,
                    decision=depth_decision,
                )

                if feedback.directive == FeedbackDirective.STOP_AND_RETURN:
                    return self._build_result(
                        completed=True,
                        reason="Stopped by feedback",
                        score_history=score_history,
                        thoughts_expanded=thoughts_expanded,
                        budget_requests=all_budget_requests,
                        anticipated_failures=all_anticipated_failures,
                    )
                elif feedback.directive == FeedbackDirective.CONTINUE_DEEPER:
                    self.depth_policy.extend_soft_limit(feedback.additional_depth)

            # =================================================================
            # PHASE 4: EXPAND AND EVALUATE
            # =================================================================
            new_thoughts: list[Any] = []

            for parent in beam:
                # Expand
                children_content = await self._expand_thought(parent, current_depth)
                thoughts_expanded += 1

                for content in children_content:
                    # Create child thought
                    child = self._create_thought(content)
                    self.graph.add(child, parent=parent)

                    # Evaluate
                    child.score = await self._evaluate_thought(child, current_depth + 1)

                    # Ground if possible
                    if self.grounder and self.grounder.can_ground(child):
                        grounding_result = await self.grounder.ground(
                            child,
                            GroundingContext(),
                        )

                        # Adjust score based on grounding
                        if grounding_result.verified is True:
                            child.score = min(1.0, child.score * 1.2)
                        elif grounding_result.verified is False:
                            child.score *= 0.1

                    new_thoughts.append(child)

                    # Check for goal
                    if child.score >= self.config.goal_score:
                        return self._build_result(
                            completed=True,
                            goal_reached=True,
                            score_history=score_history + [child.score],
                            thoughts_expanded=thoughts_expanded,
                            budget_requests=all_budget_requests,
                            anticipated_failures=all_anticipated_failures,
                        )

            # =================================================================
            # PHASE 5: UPDATE STATE
            # =================================================================
            if not new_thoughts:
                return self._build_result(
                    completed=True,
                    reason="No more thoughts to explore",
                    score_history=score_history,
                    thoughts_expanded=thoughts_expanded,
                    budget_requests=all_budget_requests,
                    anticipated_failures=all_anticipated_failures,
                )

            # Track best score
            best_at_depth = max(t.score for t in new_thoughts)
            score_history.append(best_at_depth)

            # Select beam for next iteration
            new_thoughts.sort(key=lambda t: t.score, reverse=True)
            beam = new_thoughts[:self.config.beam_width]

            current_depth += 1

            # Safety check
            if thoughts_expanded >= self.config.max_expansions:
                return self._build_result(
                    completed=True,
                    reason="Max expansions reached",
                    score_history=score_history,
                    thoughts_expanded=thoughts_expanded,
                    budget_requests=all_budget_requests,
                    anticipated_failures=all_anticipated_failures,
                )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    async def _expand_thought(self, thought: Any, depth: int) -> list[T]:
        """Expand a thought using the expander."""
        # The expander might be a method or callable
        if hasattr(self.expander, 'generate'):
            return await self.expander.generate(thought, None)
        return await self.expander(thought, None)

    async def _evaluate_thought(self, thought: Any, depth: int) -> float:
        """Evaluate a thought using the evaluator."""
        if hasattr(self.evaluator, 'evaluate'):
            return await self.evaluator.evaluate(thought, None)
        return await self.evaluator(thought, None)

    def _create_thought(self, content: T) -> Any:
        """Create a new thought with the given content."""
        # Import here to avoid circular import
        from graph_of_thought_v2.core import Thought
        return Thought(content=content)

    def _build_result(
        self,
        completed: bool,
        goal_reached: bool = False,
        reason: str | None = None,
        compromise: Any | None = None,
        score_history: list[float] | None = None,
        thoughts_expanded: int = 0,
        budget_requests: list[Any] | None = None,
        anticipated_failures: list[Any] | None = None,
    ) -> AdaptiveSearchResult[T]:
        """Build the search result."""
        # Find best thought
        all_thoughts = list(self.graph.all_thoughts())

        if not all_thoughts:
            return AdaptiveSearchResult(
                best_path=[],
                best_score=0.0,
                completed=completed,
                goal_reached=goal_reached,
                termination_reason=reason,
                compromise=compromise,
                thoughts_expanded=thoughts_expanded,
                max_depth_reached=0,
                budget_requests=budget_requests or [],
                anticipated_failures=anticipated_failures or [],
            )

        best_thought = max(all_thoughts, key=lambda t: t.score)
        best_path = self.graph.path_to_root(best_thought)[::-1]

        # Calculate max depth
        max_depth = 0
        for thought in all_thoughts:
            path = self.graph.path_to_root(thought)
            max_depth = max(max_depth, len(path) - 1)

        return AdaptiveSearchResult(
            best_path=best_path,
            best_score=best_thought.score,
            completed=completed,
            goal_reached=goal_reached,
            termination_reason=reason,
            compromise=compromise,
            thoughts_expanded=thoughts_expanded,
            max_depth_reached=max_depth,
            budget_requests=budget_requests or [],
            anticipated_failures=anticipated_failures or [],
        )
