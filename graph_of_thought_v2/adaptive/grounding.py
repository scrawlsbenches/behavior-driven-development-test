"""
Grounding - Connect Reasoning to Reality
=========================================

This module defines how thoughts are verified against external reality.

PROBLEM STATEMENT
-----------------

Thoughts exist only as text. Without verification:
- Code might not compile
- Claims might be false
- Solutions might not work

Grounding connects abstract reasoning to concrete verification.


WHAT IS GROUNDING?
------------------

Grounding = testing a thought against external reality.

Examples by domain:
    Code Generation:
        Thought: "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
        Grounding: Run tests → passes/fails

    Debugging:
        Thought: "The bug is caused by race condition in line 42"
        Grounding: Reproduce with hypothesis → confirmed/refuted

    Research:
        Thought: "Studies show X correlates with Y"
        Grounding: Check citations → verified/unverified

    Design:
        Thought: "Component A should use interface B"
        Grounding: Check consistency → valid/invalid


HOW THIS MODULE FITS IN
-----------------------

    ┌─────────────────────────────────────────────────────────────┐
    │                  AdaptiveSearchController                   │
    │                     (controller.py)                         │
    │                                                             │
    │  After generating/evaluating thoughts:                      │
    │    if grounder and grounder.can_ground(thought):            │
    │        result = await grounder.ground(thought, context)     │
    │        adjust_score_based_on_grounding(thought, result)     │
    └─────────────────────────────────────────────────────────────┘
                              │
                              │ calls ground()
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                      Grounder (Protocol)                    │
    │                                                             │
    │  can_ground(thought) → bool                                 │
    │  ground(thought, context) → GroundingResult                 │
    │                                                             │
    │  Implementations:                                           │
    │    - MockGrounder (for testing)                             │
    │    - CodeExecutionGrounder (runs code)                      │
    │    - TestRunnerGrounder (runs tests)                        │
    │    - CitationGrounder (checks sources)                      │
    └─────────────────────────────────────────────────────────────┘
                              │
                              │ returns
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    GroundingResult                          │
    │                                                             │
    │  grounded: bool (was grounding attempted)                   │
    │  verified: bool | None (did it pass verification)           │
    │  evidence: str (output, logs, etc.)                         │
    │  confidence: float (how certain)                            │
    │  execution_time_ms: int                                     │
    │  resource_cost: int (tokens/compute used)                   │
    └─────────────────────────────────────────────────────────────┘


GROUNDING VS EVALUATION
-----------------------

Evaluation (from services/protocols.py):
    - Scores thoughts based on heuristics/LLM judgment
    - Fast, cheap, available for all thoughts
    - Subjective, may be fooled

Grounding (this module):
    - Verifies thoughts against external reality
    - Slower, more expensive, not always possible
    - Objective, definitive (when possible)

They complement each other:
    1. Generate thoughts
    2. Evaluate with LLM (fast filtering)
    3. Ground promising thoughts (verification)
    4. Adjust scores based on grounding


SCORE ADJUSTMENT AFTER GROUNDING
--------------------------------

The controller adjusts scores based on grounding:

    if grounding.verified is True:
        thought.score = min(1.0, thought.score * 1.2)  # Boost
    elif grounding.verified is False:
        thought.score *= 0.1  # Heavy penalty
    # If verified is None, grounding wasn't conclusive

This prioritizes verified solutions over unverified ones.


IMPLEMENTING A GROUNDER
-----------------------

To implement a domain-specific grounder:

    class MyGrounder:
        def can_ground(self, thought: Thought) -> bool:
            # Return True if this thought can be grounded
            return "code" in str(thought.content)

        async def ground(
            self,
            thought: Thought,
            context: GroundingContext,
        ) -> GroundingResult:
            # Perform grounding
            code = extract_code(thought.content)
            result = await run_tests(code)

            return GroundingResult(
                grounded=True,
                verified=result.passed,
                evidence=result.output,
                confidence=1.0 if result.passed else 0.9,
                execution_time_ms=result.time_ms,
                resource_cost=result.tokens,
            )


RELATIONSHIP TO OTHER MODULES
-----------------------------

    grounding.py (this file)
        │
        ├── Used by: controller.py (AdaptiveSearchController)
        │   Controller optionally grounds thoughts after generation
        │
        ├── Affects: failure.py (FailureAnticipator)
        │   GROUNDING_FAILURE mode tracks grounding success rate
        │
        └── Configured by: profiles.py (DomainProfile)
            Each profile specifies grounder_type


USAGE EXAMPLE
-------------

    from graph_of_thought_v2.adaptive import (
        Grounder,
        GroundingResult,
        GroundingContext,
        MockGrounder,
    )

    # For testing, use mock grounder
    grounder = MockGrounder(
        success_rate=0.7,  # 70% of thoughts verify
    )

    # In search loop
    for thought in new_thoughts:
        if grounder.can_ground(thought):
            context = GroundingContext(
                problem=original_problem,
                test_file="tests/test_solution.py",
            )
            result = await grounder.ground(thought, context)

            if result.verified:
                print(f"Verified: {thought.content[:50]}...")
            elif result.verified is False:
                print(f"Failed: {result.evidence}")

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, Generic
import random

if TYPE_CHECKING:
    from graph_of_thought_v2.core import Thought

T = TypeVar("T")


# =============================================================================
# GROUNDING CONTEXT
# =============================================================================

@dataclass
class GroundingContext:
    """
    Context information needed for grounding.

    Contains domain-specific information that grounders need
    to verify thoughts.

    Attributes:
        problem: The original problem statement
        test_file: Path to test file (for code grounding)
        expected_output: Expected output (for verification)
        knowledge_base: Reference data (for research grounding)
        extra: Additional domain-specific context

    Example (code generation):
        GroundingContext(
            problem="Write a function to sort a list",
            test_file="tests/test_sort.py",
            expected_output=None,
        )

    Example (research):
        GroundingContext(
            problem="What causes X?",
            knowledge_base=citation_database,
        )
    """

    problem: str = ""
    """Original problem statement for context."""

    test_file: str | None = None
    """Path to test file for code verification."""

    expected_output: Any | None = None
    """Expected output for comparison."""

    knowledge_base: Any | None = None
    """Reference data for fact checking."""

    timeout_ms: int = 30000
    """Maximum time for grounding operation."""

    extra: dict[str, Any] = field(default_factory=dict)
    """Additional domain-specific context."""


# =============================================================================
# GROUNDING RESULT
# =============================================================================

@dataclass(frozen=True)
class GroundingResult:
    """
    Result of grounding a thought.

    Describes whether grounding was attempted, whether it passed,
    and provides evidence and metadata.

    Attributes:
        grounded: Whether grounding was actually performed
        verified: Whether thought passed verification (None if inconclusive)
        evidence: Output, logs, or explanation from grounding
        confidence: How confident we are in the result (0.0 to 1.0)
        execution_time_ms: How long grounding took
        resource_cost: Resources consumed (tokens, compute, etc.)

    Interpretation:
        grounded=False: Couldn't attempt grounding (thought not groundable)
        grounded=True, verified=True: Passed verification
        grounded=True, verified=False: Failed verification
        grounded=True, verified=None: Grounding was inconclusive

    Example (successful verification):
        GroundingResult(
            grounded=True,
            verified=True,
            evidence="All 5 tests passed",
            confidence=1.0,
            execution_time_ms=1500,
            resource_cost=0,
        )

    Example (failed verification):
        GroundingResult(
            grounded=True,
            verified=False,
            evidence="AssertionError: expected 5, got 4",
            confidence=1.0,
            execution_time_ms=800,
            resource_cost=0,
        )
    """

    grounded: bool
    """Whether grounding was actually performed."""

    verified: bool | None
    """
    Whether thought passed verification.

    True: Passed (code works, claim verified, etc.)
    False: Failed (code broken, claim refuted, etc.)
    None: Inconclusive (couldn't determine)
    """

    evidence: str = ""
    """
    Evidence from grounding.

    Could be:
    - Test output
    - Error messages
    - Citations found/missing
    - Consistency check results
    """

    confidence: float = 1.0
    """
    Confidence in the verification result.

    1.0: Certain (tests definitively pass/fail)
    0.5-0.9: Likely (heuristic checks)
    < 0.5: Uncertain (weak evidence)
    """

    execution_time_ms: int = 0
    """How long grounding took in milliseconds."""

    resource_cost: int = 0
    """
    Resources consumed during grounding.

    Could be tokens (if LLM involved) or compute units.
    """

    def __str__(self) -> str:
        """Human-readable representation."""
        status = "verified" if self.verified else "failed" if self.verified is False else "inconclusive"
        return (
            f"GroundingResult({status}, "
            f"confidence={self.confidence:.1%}, "
            f"time={self.execution_time_ms}ms)"
        )

    @property
    def is_definitive(self) -> bool:
        """Whether result is definitive (not inconclusive)."""
        return self.grounded and self.verified is not None

    @property
    def is_successful(self) -> bool:
        """Whether grounding succeeded with verification."""
        return self.grounded and self.verified is True


# =============================================================================
# GROUNDER PROTOCOL
# =============================================================================

class Grounder(Protocol[T]):
    """
    Protocol for grounding thoughts in external reality.

    Implement this protocol to add domain-specific grounding.

    Type parameter T matches the thought content type.

    Methods:
        can_ground: Check if a thought can be grounded
        ground: Perform grounding and return result

    Example implementation:
        class CodeGrounder:
            def can_ground(self, thought: Thought[str]) -> bool:
                return "```" in thought.content  # Has code block

            async def ground(
                self,
                thought: Thought[str],
                context: GroundingContext,
            ) -> GroundingResult:
                code = extract_code(thought.content)
                result = await run_tests(code, context.test_file)
                return GroundingResult(
                    grounded=True,
                    verified=result.passed,
                    evidence=result.output,
                )
    """

    def can_ground(self, thought: Any) -> bool:
        """
        Check if this thought can be grounded.

        Args:
            thought: The thought to check

        Returns:
            True if grounding is possible, False otherwise

        Example:
            def can_ground(self, thought):
                # Can ground if contains code
                return "def " in str(thought.content)
        """
        ...

    async def ground(
        self,
        thought: Any,
        context: GroundingContext,
    ) -> GroundingResult:
        """
        Perform grounding on a thought.

        Args:
            thought: The thought to ground
            context: Context information for grounding

        Returns:
            GroundingResult with verification status

        Example:
            async def ground(self, thought, context):
                code = extract_code(thought.content)
                passed = await run_tests(code)
                return GroundingResult(
                    grounded=True,
                    verified=passed,
                    evidence="Test output...",
                )
        """
        ...


# =============================================================================
# MOCK GROUNDER (For Testing)
# =============================================================================

class MockGrounder:
    """
    Mock grounder for testing.

    Simulates grounding with configurable success rate.
    Useful for testing the search controller without real grounding.

    Attributes:
        success_rate: Probability of verification passing (0.0 to 1.0)
        can_ground_all: Whether all thoughts are groundable
        delay_ms: Simulated delay per grounding
        seed: Random seed for reproducibility

    Example:
        # 70% of thoughts will verify
        grounder = MockGrounder(success_rate=0.7)

        # Deterministic for tests
        grounder = MockGrounder(success_rate=0.5, seed=42)
    """

    def __init__(
        self,
        success_rate: float = 0.5,
        can_ground_all: bool = True,
        delay_ms: int = 0,
        seed: int | None = None,
    ):
        """
        Initialize mock grounder.

        Args:
            success_rate: Probability of successful verification
            can_ground_all: If True, can_ground always returns True
            delay_ms: Simulated delay (not actually waited)
            seed: Random seed for reproducibility
        """
        self.success_rate = success_rate
        self.can_ground_all = can_ground_all
        self.delay_ms = delay_ms
        self._random = random.Random(seed)
        self._call_count = 0

    def can_ground(self, thought: Any) -> bool:
        """
        Check if thought can be grounded.

        If can_ground_all is True, always returns True.
        Otherwise, uses heuristics based on thought content.

        Args:
            thought: The thought to check

        Returns:
            True if can be grounded
        """
        if self.can_ground_all:
            return True

        # Simple heuristic: ground if content is long enough
        content = str(thought.content)
        return len(content) > 20

    async def ground(
        self,
        thought: Any,
        context: GroundingContext,
    ) -> GroundingResult:
        """
        Simulate grounding.

        Returns success based on success_rate probability.

        Args:
            thought: The thought to ground
            context: Grounding context (unused in mock)

        Returns:
            GroundingResult with simulated verification
        """
        self._call_count += 1

        # Simulate grounding
        verified = self._random.random() < self.success_rate

        return GroundingResult(
            grounded=True,
            verified=verified,
            evidence=f"Mock grounding #{self._call_count}: {'passed' if verified else 'failed'}",
            confidence=0.9,
            execution_time_ms=self.delay_ms,
            resource_cost=0,
        )

    @property
    def call_count(self) -> int:
        """Number of times ground() was called."""
        return self._call_count

    def reset(self) -> None:
        """Reset call count."""
        self._call_count = 0


# =============================================================================
# ALWAYS-PASS GROUNDER (For Testing)
# =============================================================================

class AlwaysPassGrounder:
    """
    Grounder that always passes verification.

    Useful for testing happy paths without grounding complexity.
    """

    def can_ground(self, thought: Any) -> bool:
        """Always returns True."""
        return True

    async def ground(
        self,
        thought: Any,
        context: GroundingContext,
    ) -> GroundingResult:
        """Always returns successful verification."""
        return GroundingResult(
            grounded=True,
            verified=True,
            evidence="Always pass grounder",
            confidence=1.0,
            execution_time_ms=0,
            resource_cost=0,
        )


# =============================================================================
# NEVER-GROUND GROUNDER (For Testing)
# =============================================================================

class NeverGroundGrounder:
    """
    Grounder that never grounds anything.

    Useful for testing scenarios where grounding is disabled.
    """

    def can_ground(self, thought: Any) -> bool:
        """Always returns False."""
        return False

    async def ground(
        self,
        thought: Any,
        context: GroundingContext,
    ) -> GroundingResult:
        """Returns not grounded."""
        return GroundingResult(
            grounded=False,
            verified=None,
            evidence="Grounding disabled",
            confidence=0.0,
            execution_time_ms=0,
            resource_cost=0,
        )
