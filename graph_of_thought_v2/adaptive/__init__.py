"""
Adaptive Search Package - Self-Aware Graph of Thought
======================================================

This package implements a self-aware, negotiating search system that knows its
constraints, monitors progress, and can request resources or propose compromises.

PACKAGE OVERVIEW
----------------

The adaptive search system is built from these components:

    ┌─────────────────────────────────────────────────────────────────────┐
    │                     AdaptiveSearchController                        │
    │                        (controller.py)                              │
    │                                                                     │
    │  Orchestrates the search loop, integrating all other components.    │
    │  This is the main entry point for running adaptive searches.        │
    └─────────────────────────────────────────────────────────────────────┘
                │
                │ uses
                ▼
    ┌───────────────────┬───────────────────┬───────────────────┐
    │   DepthPolicy     │  BudgetNegotiator │ FailureAnticipator│
    │   (depth.py)      │  (budget.py)      │ (failure.py)      │
    │                   │                   │                   │
    │ Manages search    │ Handles resource  │ Predicts problems │
    │ depth with soft/  │ negotiation when  │ before they occur │
    │ hard limits and   │ budget runs low.  │ and suggests      │
    │ feedback loops.   │ Can request more  │ prevention.       │
    │                   │ or propose        │                   │
    │                   │ compromises.      │                   │
    └───────────────────┴───────────────────┴───────────────────┘
                │                   │                   │
                │ produces          │ produces          │ produces
                ▼                   ▼                   ▼
    ┌───────────────────┬───────────────────┬───────────────────┐
    │  DepthDecision    │ CompromiseSolution│ AnticipatedFailure│
    │  (depth.py)       │ (compromise.py)   │ (failure.py)      │
    │                   │                   │                   │
    │ What to do about  │ A "good enough"   │ A predicted       │
    │ current depth:    │ solution with     │ failure with      │
    │ continue, stop,   │ explicit tradeoff │ likelihood and    │
    │ or ask for        │ documentation.    │ mitigation.       │
    │ feedback.         │                   │                   │
    └───────────────────┴───────────────────┴───────────────────┘

    ┌───────────────────┬───────────────────┐
    │  FeedbackHandler  │     Grounder      │
    │  (feedback.py)    │  (grounding.py)   │
    │                   │                   │
    │ Interface for     │ Tests thoughts    │
    │ getting decisions │ against external  │
    │ from human or     │ reality (code     │
    │ automated policy. │ execution, etc.)  │
    └───────────────────┴───────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │                        DomainProfile                                │
    │                        (profiles.py)                                │
    │                                                                     │
    │  Pre-configured settings for specific domains:                      │
    │  - CODE_GENERATION_PROFILE                                          │
    │  - DEBUGGING_PROFILE                                                │
    │  - RESEARCH_SYNTHESIS_PROFILE                                       │
    │  - STRATEGIC_PLANNING_PROFILE                                       │
    │  - DESIGN_PROFILE                                                   │
    └─────────────────────────────────────────────────────────────────────┘


HOW THE COMPONENTS INTERACT
---------------------------

1. DEPTH MANAGEMENT (depth.py → controller.py)

   The DepthPolicy evaluates whether to continue deeper:

       depth_policy.evaluate_depth(current_depth, score_history)
       → DepthDecision(action=CONTINUE|STOP|REQUEST_FEEDBACK)

   If REQUEST_FEEDBACK, the controller asks the FeedbackHandler.


2. BUDGET NEGOTIATION (budget.py → feedback.py → controller.py)

   When budget runs low, BudgetNegotiator assesses options:

       negotiator.assess_situation(graph, budget) → BudgetSituation
       negotiator.negotiate(situation, graph) → BudgetNegotiationResult

   The result might be:
   - SUFFICIENT: Keep going
   - REQUEST_INCREASE: Ask FeedbackHandler for more budget
   - PROPOSE_COMPROMISE: Offer a CompromiseSolution
   - TERMINATE: No options left


3. FAILURE ANTICIPATION (failure.py → controller.py)

   FailureAnticipator continuously monitors for problems:

       anticipator.anticipate(graph, budget, score_history)
       → [AnticipatedFailure, ...]

   High-likelihood failures trigger prevention or mitigation.


4. GROUNDING (grounding.py → controller.py)

   After generating thoughts, optionally verify them:

       if grounder.can_ground(thought):
           result = grounder.ground(thought, context)
           if result.verified is False:
               thought.score *= 0.1  # Penalize unverified

   Grounding connects reasoning to reality.


5. FEEDBACK (feedback.py → controller.py)

   When decisions need external input:

       feedback_handler.request_budget_increase(amount, justification)
       → BudgetResponse(APPROVED|DENIED|ACCEPT_COMPROMISE)

       feedback_handler.request_depth_feedback(depth, scores, decision)
       → FeedbackDirective(CONTINUE_DEEPER|STOP_AND_RETURN)


RELATIONSHIP TO EXISTING CODE
-----------------------------

This package EXTENDS the existing graph_of_thought_v2 architecture:

    existing core/search.py        → Pure beam search algorithm
    new adaptive/controller.py     → Self-aware search with negotiation

    existing middleware/budget.py  → Binary pass/fail budget checking
    new adaptive/budget.py         → Negotiating budget management

    existing context/execution.py  → Immutable execution context
    new adaptive/                   → Uses Context, adds feedback loops

The adaptive package can use the existing:
- Graph, Thought from core/
- Context from context/
- Generator, Evaluator protocols from services/
- SimpleGenerator, SimpleEvaluator for testing

It adds NEW capabilities:
- Depth-aware feedback
- Budget negotiation
- Compromise proposals
- Failure anticipation
- Grounding


USAGE EXAMPLE
-------------

    from graph_of_thought_v2.adaptive import (
        AdaptiveSearchController,
        DepthPolicy,
        BudgetNegotiator,
        FailureAnticipator,
        AutomaticFeedbackHandler,
        CODE_GENERATION_PROFILE,
    )

    # Use a domain profile for sensible defaults
    profile = CODE_GENERATION_PROFILE

    # Create controller with all components
    controller = AdaptiveSearchController(
        graph=my_graph,
        expander=my_expander,
        evaluator=my_evaluator,
        grounder=my_grounder,  # Optional
        config=profile.search_config,
        depth_policy=profile.depth_policy,
        budget_negotiator=BudgetNegotiator(
            acceptable_threshold=profile.acceptable_threshold,
            goal_threshold=profile.goal_threshold,
        ),
        failure_anticipator=FailureAnticipator(),
        feedback_handler=AutomaticFeedbackHandler(),
    )

    # Run search
    result = await controller.search(budget)

    if result.goal_reached:
        print("Found optimal solution!")
    elif result.compromise:
        print(f"Best compromise: {result.compromise.explain()}")
    else:
        print(f"Could not solve: {result.termination_reason}")


DESIGN PRINCIPLES
-----------------

1. SEPARATION OF CONCERNS
   Each component has one job. DepthPolicy doesn't know about budget.
   BudgetNegotiator doesn't know about depth. Controller orchestrates.

2. PROTOCOLS OVER CONCRETE TYPES
   FeedbackHandler and Grounder are protocols. You can implement them
   however you want (CLI, API, mock, policy-based).

3. IMMUTABLE DECISIONS
   DepthDecision, CompromiseSolution, AnticipatedFailure are data.
   They describe what to do, not how to do it.

4. EXPLICIT TRADEOFFS
   When compromising, tradeoffs are documented. When requesting budget,
   justification is provided. No hidden decisions.

5. TESTABLE WITHOUT EXTERNALS
   Everything can be tested with mocks. Real grounding (code execution)
   is an extension point, not a requirement.

"""

# =============================================================================
# PUBLIC API
# =============================================================================

from graph_of_thought_v2.adaptive.depth import (
    DepthPolicy,
    DepthDecision,
    DepthAction,
)

from graph_of_thought_v2.adaptive.budget import (
    BudgetNegotiator,
    BudgetSituation,
    BudgetNegotiationResult,
    BudgetDecision,
)

from graph_of_thought_v2.adaptive.compromise import (
    CompromiseSolution,
)

from graph_of_thought_v2.adaptive.failure import (
    FailureMode,
    FailureAnticipator,
    AnticipatedFailure,
    FailureAssessment,
)

from graph_of_thought_v2.adaptive.grounding import (
    Grounder,
    GroundingResult,
    GroundingContext,
    MockGrounder,
)

from graph_of_thought_v2.adaptive.feedback import (
    FeedbackHandler,
    FeedbackDirective,
    BudgetResponse,
    AutomaticFeedbackHandler,
)

from graph_of_thought_v2.adaptive.controller import (
    AdaptiveSearchController,
    AdaptiveSearchResult,
)

from graph_of_thought_v2.adaptive.profiles import (
    DomainProfile,
    CODE_GENERATION_PROFILE,
    DEBUGGING_PROFILE,
    RESEARCH_SYNTHESIS_PROFILE,
    STRATEGIC_PLANNING_PROFILE,
    DESIGN_PROFILE,
)

__all__ = [
    # Depth management
    "DepthPolicy",
    "DepthDecision",
    "DepthAction",
    # Budget negotiation
    "BudgetNegotiator",
    "BudgetSituation",
    "BudgetNegotiationResult",
    "BudgetDecision",
    # Compromise
    "CompromiseSolution",
    # Failure anticipation
    "FailureMode",
    "FailureAnticipator",
    "AnticipatedFailure",
    "FailureAssessment",
    # Grounding
    "Grounder",
    "GroundingResult",
    "GroundingContext",
    "MockGrounder",
    # Feedback
    "FeedbackHandler",
    "FeedbackDirective",
    "BudgetResponse",
    "AutomaticFeedbackHandler",
    # Controller
    "AdaptiveSearchController",
    "AdaptiveSearchResult",
    # Profiles
    "DomainProfile",
    "CODE_GENERATION_PROFILE",
    "DEBUGGING_PROFILE",
    "RESEARCH_SYNTHESIS_PROFILE",
    "STRATEGIC_PLANNING_PROFILE",
    "DESIGN_PROFILE",
]
