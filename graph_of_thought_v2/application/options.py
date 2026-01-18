"""
Options - Typed Configuration
==============================

Options are strongly-typed configuration classes. They replace loose
dictionaries with validated, documented settings.

WHY TYPED OPTIONS
-----------------

Dicts are error-prone:
    config["max_dpeth"]  # Typo, fails at runtime
    config["max_depth"]  # Is this int? str? float?

Options are safe:
    options.max_depth  # IDE autocomplete
    options.max_depth  # Type is int, enforced

THE OPTIONS PATTERN (from ASP.NET Core)
---------------------------------------

1. Define options as dataclasses
2. Load from configuration sources (file, env, etc.)
3. Validate at startup (fail fast)
4. Inject as Options[T] where needed

    @dataclass
    class GraphOptions:
        max_depth: int = 10

    # In builder
    builder.add_options(GraphOptions, section="graph")

    # In service (receives validated options)
    class SearchHandler:
        def __init__(self, options: GraphOptions):
            self.max_depth = options.max_depth

CONFIGURATION SOURCES
---------------------

Options can be loaded from multiple sources (in priority order):
1. Default values (in dataclass)
2. Configuration files (JSON, YAML)
3. Environment variables
4. Command-line arguments

Later sources override earlier ones.

VALIDATION
----------

Options are validated at load time:
- Type checking (max_depth must be int)
- Range checking (max_depth must be > 0)
- Required fields (api_key cannot be None in production)

Invalid options = fail at startup, not at runtime.

"""

from dataclasses import dataclass, field
from typing import Any
import os


# =============================================================================
# GRAPH OPTIONS
# =============================================================================

@dataclass
class GraphOptions:
    """
    Configuration for graph behavior.

    Attributes:
        allow_cycles: Whether cycles are allowed in the graph.
                     Default False (tree structure only).
        max_thoughts: Maximum thoughts allowed in a single graph.
                     Safety limit to prevent memory issues.

    Environment Variables:
        GOT_GRAPH_ALLOW_CYCLES: "true" or "false"
        GOT_GRAPH_MAX_THOUGHTS: integer

    Example:
        options = GraphOptions(max_thoughts=5000)
        # Or from environment:
        options = GraphOptions.from_env()
    """

    allow_cycles: bool = False
    """
    Allow cycles in thought graphs.

    If False (default), graphs are trees: each thought has at most
    one parent. If True, thoughts can have multiple parents (DAG).

    Trees are simpler and prevent infinite loops. DAGs allow more
    complex reasoning structures but require cycle detection.
    """

    max_thoughts: int = 10000
    """
    Maximum thoughts per graph.

    Safety limit to prevent memory exhaustion. When reached,
    new thoughts are rejected.

    Typical graphs have 100-1000 thoughts. Increase for very
    deep explorations.
    """

    @classmethod
    def from_env(cls, prefix: str = "GOT_GRAPH_") -> "GraphOptions":
        """Load options from environment variables."""
        allow_cycles = os.getenv(f"{prefix}ALLOW_CYCLES", "false").lower() == "true"
        max_thoughts = int(os.getenv(f"{prefix}MAX_THOUGHTS", "10000"))
        return cls(allow_cycles=allow_cycles, max_thoughts=max_thoughts)

    def validate(self) -> list[str]:
        """Validate options, return list of errors (empty if valid)."""
        errors = []
        if self.max_thoughts < 1:
            errors.append("max_thoughts must be at least 1")
        if self.max_thoughts > 1_000_000:
            errors.append("max_thoughts exceeds safe limit (1,000,000)")
        return errors


# =============================================================================
# SEARCH OPTIONS
# =============================================================================

@dataclass
class SearchOptions:
    """
    Configuration for search behavior.

    Attributes:
        max_depth: Maximum depth to explore.
        beam_width: Number of thoughts to keep at each level.
        max_expansions: Total expansions before terminating.
        goal_score: Score threshold to consider search successful.

    Environment Variables:
        GOT_SEARCH_MAX_DEPTH: integer
        GOT_SEARCH_BEAM_WIDTH: integer
        GOT_SEARCH_MAX_EXPANSIONS: integer
        GOT_SEARCH_GOAL_SCORE: float (0.0 to 1.0)

    Example:
        options = SearchOptions(max_depth=5, beam_width=5)
    """

    max_depth: int = 10
    """
    Maximum depth to explore (root is depth 0).

    Deeper searches find more thorough solutions but take longer.
    For quick explorations, use 3-5. For thorough analysis, use 10-20.
    """

    beam_width: int = 3
    """
    Number of promising thoughts to keep at each level.

    Wider beam = more exploration = better solutions but slower.
    Typical values: 2-5 for fast, 5-10 for thorough.
    """

    max_expansions: int = 100
    """
    Maximum total expansions (safety limit).

    Prevents runaway searches. Each expansion generates multiple
    children, so total thoughts = expansions × average_children.
    """

    goal_score: float = 0.95
    """
    Score threshold for early termination.

    If any thought scores this high, search stops. Set to 1.0 to
    always explore fully. Set lower for "good enough" solutions.
    """

    @classmethod
    def from_env(cls, prefix: str = "GOT_SEARCH_") -> "SearchOptions":
        """Load options from environment variables."""
        return cls(
            max_depth=int(os.getenv(f"{prefix}MAX_DEPTH", "10")),
            beam_width=int(os.getenv(f"{prefix}BEAM_WIDTH", "3")),
            max_expansions=int(os.getenv(f"{prefix}MAX_EXPANSIONS", "100")),
            goal_score=float(os.getenv(f"{prefix}GOAL_SCORE", "0.95")),
        )

    def validate(self) -> list[str]:
        """Validate options, return list of errors."""
        errors = []
        if self.max_depth < 1:
            errors.append("max_depth must be at least 1")
        if self.beam_width < 1:
            errors.append("beam_width must be at least 1")
        if self.max_expansions < 1:
            errors.append("max_expansions must be at least 1")
        if not 0.0 <= self.goal_score <= 1.0:
            errors.append("goal_score must be between 0.0 and 1.0")
        return errors


# =============================================================================
# BUDGET OPTIONS
# =============================================================================

@dataclass
class BudgetOptions:
    """
    Configuration for budget management.

    Attributes:
        default_tokens: Default token budget for new contexts.
        warning_threshold: Utilization percentage for warnings.
        enforce_limits: Whether to reject operations when exhausted.

    Environment Variables:
        GOT_BUDGET_DEFAULT_TOKENS: integer
        GOT_BUDGET_WARNING_THRESHOLD: float (0.0 to 1.0)
        GOT_BUDGET_ENFORCE_LIMITS: "true" or "false"

    Example:
        options = BudgetOptions(default_tokens=50000)
    """

    default_tokens: int = 50000
    """
    Default token budget for contexts that don't specify one.

    This is a sensible starting point. Adjust based on typical
    operation costs and organizational limits.
    """

    warning_threshold: float = 0.8
    """
    Utilization threshold for warning (0.0 to 1.0).

    When budget utilization exceeds this, warnings are logged.
    Default 0.8 = warn at 80% consumed.
    """

    enforce_limits: bool = True
    """
    Whether to reject operations when budget is exhausted.

    If True (default), operations fail when budget is gone.
    If False, operations continue but with warnings logged.

    Use False for development/testing, True for production.
    """

    @classmethod
    def from_env(cls, prefix: str = "GOT_BUDGET_") -> "BudgetOptions":
        """Load options from environment variables."""
        return cls(
            default_tokens=int(os.getenv(f"{prefix}DEFAULT_TOKENS", "50000")),
            warning_threshold=float(os.getenv(f"{prefix}WARNING_THRESHOLD", "0.8")),
            enforce_limits=os.getenv(f"{prefix}ENFORCE_LIMITS", "true").lower() == "true",
        )

    def validate(self) -> list[str]:
        """Validate options, return list of errors."""
        errors = []
        if self.default_tokens < 0:
            errors.append("default_tokens cannot be negative")
        if not 0.0 <= self.warning_threshold <= 1.0:
            errors.append("warning_threshold must be between 0.0 and 1.0")
        return errors


# =============================================================================
# OPTIONS CONTAINER
# =============================================================================

@dataclass
class ApplicationOptions:
    """
    Container for all application options.

    Groups related options for easy access and validation.

    Example:
        options = ApplicationOptions()
        options.validate()  # Check all options
        print(options.search.max_depth)
    """

    graph: GraphOptions = field(default_factory=GraphOptions)
    search: SearchOptions = field(default_factory=SearchOptions)
    budget: BudgetOptions = field(default_factory=BudgetOptions)

    @classmethod
    def from_env(cls) -> "ApplicationOptions":
        """Load all options from environment variables."""
        return cls(
            graph=GraphOptions.from_env(),
            search=SearchOptions.from_env(),
            budget=BudgetOptions.from_env(),
        )

    def validate(self) -> list[str]:
        """Validate all options, return list of all errors."""
        errors = []
        errors.extend(self.graph.validate())
        errors.extend(self.search.validate())
        errors.extend(self.budget.validate())
        return errors
