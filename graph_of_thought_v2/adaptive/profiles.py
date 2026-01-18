"""
Domain Profiles - Pre-configured Settings for Specific Domains
===============================================================

This module provides pre-configured profiles for different use cases.

WHY PROFILES?
-------------

Each domain has different characteristics:

    Code Generation:
        - Solutions found quickly or not at all
        - Clear verification (tests pass/fail)
        - High quality bar (code must work)

    Research Synthesis:
        - Longer exploration needed
        - Uncertain verification
        - Lower quality bar (partial findings valuable)

    Debugging:
        - Hypothesis-driven search
        - Reproduction-based verification
        - Medium depth, wider exploration

Rather than manually configuring all parameters for each domain,
profiles provide sensible defaults that can be used directly or
customized.


PROFILE CONTENTS
----------------

Each DomainProfile contains:

    ┌─────────────────────────────────────────────────────────────┐
    │                      DomainProfile                          │
    │                                                             │
    │  name: str                                                  │
    │      Human-readable domain name                             │
    │                                                             │
    │  search_config: SearchConfig                                │
    │      max_depth, beam_width, goal_score, max_expansions      │
    │                                                             │
    │  depth_policy: DepthPolicy                                  │
    │      soft_limit, hard_limit, min_progress_rate, stagnation  │
    │                                                             │
    │  acceptable_threshold: float                                │
    │      Minimum score for acceptable solution                  │
    │                                                             │
    │  goal_threshold: float                                      │
    │      Score for ideal solution (early termination)           │
    │                                                             │
    │  compromise_threshold: float                                │
    │      Minimum score to offer as compromise                   │
    │                                                             │
    │  grounder_type: type | None                                 │
    │      Recommended grounder class for this domain             │
    │                                                             │
    │  extra_config: dict                                         │
    │      Domain-specific additional settings                    │
    └─────────────────────────────────────────────────────────────┘


AVAILABLE PROFILES
------------------

    CODE_GENERATION_PROFILE
        For: Writing code, implementing features
        Characteristics: High bar, quick termination, grounded by tests

    DEBUGGING_PROFILE
        For: Finding and fixing bugs
        Characteristics: Hypothesis exploration, reproduction-based

    RESEARCH_SYNTHESIS_PROFILE
        For: Combining information, answering complex questions
        Characteristics: Deep exploration, uncertain verification

    STRATEGIC_PLANNING_PROFILE
        For: Goal decomposition, action planning
        Characteristics: Moderate depth, actionable outputs

    DESIGN_PROFILE
        For: Architecture, component design
        Characteristics: Consistency checking, interface validation


HOW TO USE PROFILES
-------------------

1. USE DIRECTLY

    from graph_of_thought_v2.adaptive import (
        AdaptiveSearchController,
        CODE_GENERATION_PROFILE,
    )

    profile = CODE_GENERATION_PROFILE

    controller = AdaptiveSearchController(
        graph=my_graph,
        expander=my_expander,
        evaluator=my_evaluator,
        config=profile.search_config,
        depth_policy=profile.depth_policy,
        budget_negotiator=BudgetNegotiator(
            acceptable_threshold=profile.acceptable_threshold,
            goal_threshold=profile.goal_threshold,
            compromise_threshold=profile.compromise_threshold,
        ),
        ...
    )


2. CUSTOMIZE FROM PROFILE

    from graph_of_thought_v2.adaptive import CODE_GENERATION_PROFILE
    from dataclasses import replace

    # Start with profile, customize
    my_config = replace(
        CODE_GENERATION_PROFILE.search_config,
        max_depth=20,  # Override one setting
    )


3. CREATE CUSTOM PROFILE

    from graph_of_thought_v2.adaptive import DomainProfile, SearchConfig, DepthPolicy

    MY_DOMAIN_PROFILE = DomainProfile(
        name="my_domain",
        search_config=SearchConfig(
            max_depth=8,
            beam_width=5,
            goal_score=0.85,
        ),
        depth_policy=DepthPolicy(
            soft_limit=5,
            hard_limit=10,
        ),
        acceptable_threshold=0.65,
        goal_threshold=0.85,
        compromise_threshold=0.45,
        grounder_type=None,
        extra_config={"my_setting": True},
    )


RELATIONSHIP TO OTHER MODULES
-----------------------------

    profiles.py (this file)
        │
        ├── Configures: controller.py (AdaptiveSearchController)
        │   Provides config, depth_policy, thresholds
        │
        ├── Configures: budget.py (BudgetNegotiator)
        │   Provides acceptable/goal/compromise thresholds
        │
        ├── Configures: depth.py (DepthPolicy)
        │   Provides soft_limit, hard_limit, etc.
        │
        └── Recommends: grounding.py (Grounder implementations)
            grounder_type suggests which grounder to use

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Type

# Import our local types
from graph_of_thought_v2.adaptive.controller import SearchConfig
from graph_of_thought_v2.adaptive.depth import DepthPolicy

if TYPE_CHECKING:
    from graph_of_thought_v2.adaptive.grounding import Grounder


# =============================================================================
# DOMAIN PROFILE
# =============================================================================

@dataclass(frozen=True)
class DomainProfile:
    """
    Configuration profile for a specific domain.

    Bundles together all the settings needed for a particular use case.

    Attributes:
        name: Human-readable domain name
        search_config: Search parameters (depth, beam, goal)
        depth_policy: Depth management settings
        acceptable_threshold: Minimum score for acceptable solution
        goal_threshold: Score for ideal solution
        compromise_threshold: Minimum score to offer as compromise
        grounder_type: Recommended grounder class (or None)
        extra_config: Domain-specific additional settings

    Example:
        profile = DomainProfile(
            name="my_domain",
            search_config=SearchConfig(max_depth=10),
            depth_policy=DepthPolicy(soft_limit=7),
            acceptable_threshold=0.70,
            goal_threshold=0.95,
            compromise_threshold=0.50,
        )
    """

    name: str
    """
    Human-readable name for this domain.

    Used for logging, debugging, and display.
    Examples: "code_generation", "debugging", "research"
    """

    search_config: SearchConfig
    """
    Search configuration for this domain.

    Contains: max_depth, beam_width, goal_score, max_expansions
    """

    depth_policy: DepthPolicy
    """
    Depth management policy for this domain.

    Contains: soft_limit, hard_limit, min_progress_rate, stagnation_threshold
    """

    acceptable_threshold: float
    """
    Minimum score to consider a solution acceptable.

    Below this: Need to keep searching or compromise.
    Above this: Solution is usable.

    Typical range: 0.60-0.80 depending on domain.
    """

    goal_threshold: float
    """
    Score threshold for ideal solution.

    Above this: Stop searching, we found an excellent solution.
    Usually high (0.90-0.99).
    """

    compromise_threshold: float = 0.50
    """
    Minimum score to offer as compromise.

    Below this: Don't even suggest as alternative.
    Above this but below acceptable: Can propose with tradeoffs.

    Typical range: 0.40-0.60.
    """

    grounder_type: Type[Any] | None = None
    """
    Recommended grounder class for this domain.

    None if grounding not applicable or domain-independent.
    Examples: CodeExecutionGrounder, ResearchGrounder

    Note: This is a type hint, not an instance. Instantiation
    is the caller's responsibility.
    """

    extra_config: dict[str, Any] = field(default_factory=dict)
    """
    Domain-specific additional configuration.

    Free-form dictionary for settings not covered by standard fields.

    Examples:
        {"require_grounding": True}
        {"max_hypothesis_branches": 5}
    """

    def __str__(self) -> str:
        """Human-readable summary."""
        return (
            f"DomainProfile({self.name})\n"
            f"  Search: depth={self.search_config.max_depth}, "
            f"beam={self.search_config.beam_width}, "
            f"goal={self.search_config.goal_score}\n"
            f"  Depth: soft={self.depth_policy.soft_limit}, "
            f"hard={self.depth_policy.hard_limit}\n"
            f"  Thresholds: acceptable={self.acceptable_threshold}, "
            f"goal={self.goal_threshold}, "
            f"compromise={self.compromise_threshold}"
        )

    def create_budget_negotiator(self) -> Any:
        """
        Create a BudgetNegotiator configured for this profile.

        Returns:
            BudgetNegotiator with this profile's thresholds

        Example:
            negotiator = profile.create_budget_negotiator()
        """
        from graph_of_thought_v2.adaptive.budget import BudgetNegotiator

        return BudgetNegotiator(
            acceptable_threshold=self.acceptable_threshold,
            goal_threshold=self.goal_threshold,
            compromise_threshold=self.compromise_threshold,
        )


# =============================================================================
# CODE GENERATION PROFILE
# =============================================================================

CODE_GENERATION_PROFILE = DomainProfile(
    name="code_generation",

    search_config=SearchConfig(
        max_depth=12,
        """
        Moderate depth. Code solutions are usually found within 10-15 steps
        or not at all. Deeper searches rarely help.
        """,

        beam_width=4,
        """
        Moderate beam. Keep multiple approaches in parallel but don't
        waste resources on too many poor candidates.
        """,

        goal_score=0.95,
        """
        High bar. Code should work correctly. Don't accept partially
        working solutions as "goal reached".
        """,

        max_expansions=150,
        """
        Safety limit. Prevents runaway searches.
        """,
    ),

    depth_policy=DepthPolicy(
        soft_limit=8,
        """
        Evaluate progress after depth 8. If not converging, consider
        different approach.
        """,

        hard_limit=15,
        """
        Absolute stop at 15. If solution not found by then, problem
        likely needs reformulation.
        """,

        min_progress_rate=0.03,
        """
        Expect 3% improvement per depth. Code search usually shows
        clear progress or stalls completely.
        """,

        stagnation_threshold=4,
        """
        Concern after 4 depths without improvement.
        """,
    ),

    acceptable_threshold=0.75,
    """
    Code that mostly works. Some edge cases may fail.
    Usable for prototyping or with manual fixes.
    """,

    goal_threshold=0.95,
    """
    Code that passes all tests. Production ready.
    """,

    compromise_threshold=0.50,
    """
    Code with significant issues but potentially useful starting point.
    """,

    grounder_type=None,  # Would be CodeExecutionGrounder
    """
    In real implementation, would use a grounder that:
    - Extracts code from thoughts
    - Runs tests
    - Returns pass/fail with output
    """,

    extra_config={
        "require_grounding": True,
        "syntax_check_early": True,
        "prefer_simple_solutions": True,
    },
)


# =============================================================================
# DEBUGGING PROFILE
# =============================================================================

DEBUGGING_PROFILE = DomainProfile(
    name="debugging",

    search_config=SearchConfig(
        max_depth=10,
        """
        Moderate depth. Bug hunts follow hypothesis chains that
        shouldn't be too long.
        """,

        beam_width=5,
        """
        Wider beam. Keep multiple hypotheses in parallel since
        first guess is often wrong.
        """,

        goal_score=0.90,
        """
        High bar but not as strict as code gen. Bug fix that
        resolves the issue without breaking other things.
        """,

        max_expansions=100,
    ),

    depth_policy=DepthPolicy(
        soft_limit=6,
        hard_limit=12,
        min_progress_rate=0.05,
        stagnation_threshold=3,
    ),

    acceptable_threshold=0.70,
    """
    Plausible hypothesis with supporting evidence.
    """,

    goal_threshold=0.90,
    """
    Verified fix that passes regression tests.
    """,

    compromise_threshold=0.50,
    """
    Hypothesis worth investigating manually.
    """,

    grounder_type=None,  # Would be DebuggingGrounder

    extra_config={
        "require_reproduction": True,
        "run_regression_tests": True,
        "max_hypothesis_branches": 5,
    },
)


# =============================================================================
# RESEARCH SYNTHESIS PROFILE
# =============================================================================

RESEARCH_SYNTHESIS_PROFILE = DomainProfile(
    name="research_synthesis",

    search_config=SearchConfig(
        max_depth=15,
        """
        Deeper exploration. Research requires following threads
        and building understanding gradually.
        """,

        beam_width=3,
        """
        Narrower beam. Focus on most promising synthesis paths
        rather than broad exploration.
        """,

        goal_score=0.85,
        """
        Lower goal. Research is inherently uncertain. Don't
        demand perfection.
        """,

        max_expansions=200,
        """
        Allow more exploration for complex synthesis.
        """,
    ),

    depth_policy=DepthPolicy(
        soft_limit=10,
        hard_limit=20,
        min_progress_rate=0.02,
        """
        Lower progress expectation. Research progress is slower
        and less predictable.
        """,
        stagnation_threshold=5,
        """
        More patience before declaring stagnation.
        """,
    ),

    acceptable_threshold=0.60,
    """
    Reasonable synthesis with supporting evidence.
    May have gaps or uncertainties.
    """,

    goal_threshold=0.85,
    """
    Strong, well-supported synthesis.
    """,

    compromise_threshold=0.40,
    """
    Preliminary findings worth reviewing.
    """,

    grounder_type=None,  # Would be ResearchGrounder

    extra_config={
        "require_citations": True,
        "cross_reference_threshold": 0.7,
        "allow_uncertainty": True,
    },
)


# =============================================================================
# STRATEGIC PLANNING PROFILE
# =============================================================================

STRATEGIC_PLANNING_PROFILE = DomainProfile(
    name="strategic_planning",

    search_config=SearchConfig(
        max_depth=8,
        """
        Shallower depth. Strategy should be high-level.
        Too much depth leads to tactics, not strategy.
        """,

        beam_width=4,
        """
        Moderate beam. Consider multiple strategic directions.
        """,

        goal_score=0.80,
        """
        Moderate goal. Strategy is inherently uncertain.
        Good enough to act on.
        """,

        max_expansions=80,
    ),

    depth_policy=DepthPolicy(
        soft_limit=5,
        hard_limit=10,
        min_progress_rate=0.04,
        stagnation_threshold=3,
    ),

    acceptable_threshold=0.65,
    """
    Coherent strategy with actionable steps.
    """,

    goal_threshold=0.80,
    """
    Well-reasoned strategy with clear path.
    """,

    compromise_threshold=0.45,
    """
    Direction worth considering.
    """,

    grounder_type=None,  # Strategy is hard to ground

    extra_config={
        "require_actionable_steps": True,
        "max_strategy_branches": 3,
        "include_risk_assessment": True,
    },
)


# =============================================================================
# DESIGN PROFILE
# =============================================================================

DESIGN_PROFILE = DomainProfile(
    name="design",

    search_config=SearchConfig(
        max_depth=10,
        """
        Moderate depth. Design evolves through refinement
        but shouldn't go too deep too fast.
        """,

        beam_width=4,
        """
        Consider multiple design alternatives.
        """,

        goal_score=0.85,
        """
        Solid design that meets requirements.
        """,

        max_expansions=120,
    ),

    depth_policy=DepthPolicy(
        soft_limit=7,
        hard_limit=12,
        min_progress_rate=0.03,
        stagnation_threshold=4,
    ),

    acceptable_threshold=0.70,
    """
    Workable design that addresses main requirements.
    """,

    goal_threshold=0.85,
    """
    Clean design with good separation and extensibility.
    """,

    compromise_threshold=0.50,
    """
    Design sketch worth developing further.
    """,

    grounder_type=None,  # Would be DesignConsistencyChecker

    extra_config={
        "check_consistency": True,
        "validate_interfaces": True,
        "prefer_simplicity": True,
    },
)


# =============================================================================
# ALL PROFILES
# =============================================================================

ALL_PROFILES: dict[str, DomainProfile] = {
    "code_generation": CODE_GENERATION_PROFILE,
    "debugging": DEBUGGING_PROFILE,
    "research_synthesis": RESEARCH_SYNTHESIS_PROFILE,
    "strategic_planning": STRATEGIC_PLANNING_PROFILE,
    "design": DESIGN_PROFILE,
}
"""
Dictionary of all available profiles by name.

Example:
    profile = ALL_PROFILES["code_generation"]
"""


def get_profile(name: str) -> DomainProfile:
    """
    Get a profile by name.

    Args:
        name: Profile name (e.g., "code_generation")

    Returns:
        The corresponding DomainProfile

    Raises:
        KeyError: If profile not found

    Example:
        profile = get_profile("debugging")
    """
    return ALL_PROFILES[name]
