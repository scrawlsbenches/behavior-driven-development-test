# Applied Design: Self-Aware Graph of Thought

**Author:** Claude
**Date:** 2026-01-18
**Status:** Applied Design Specification
**Builds On:** DESIGN_PHILOSOPHY.md

---

## Overview

This document specifies a **self-aware, negotiating Graph of Thought** system designed for:

- **Code Generation**: Problem → approaches → implementations → tested solutions
- **Research Synthesis**: Question → hypotheses → evidence → conclusions
- **Strategic Planning**: Goal → strategies → tactics → actions
- **Design**: Requirements → architectures → components → implementations
- **Debugging**: Bug → causes → tests → fixes

**Not designed for:**
- Real-time systems (latency is acceptable)
- Highly creative open-ended tasks (structured problem-solving only)

---

## Core Design Philosophy

### The Self-Aware System

Unlike a naive search that blindly explores until resources run out, this system:

1. **Knows its constraints** before starting
2. **Monitors its progress** during execution
3. **Recognizes when it's stuck** or insufficient
4. **Negotiates for more resources** when needed
5. **Proposes compromises** when full solutions aren't achievable

### The Feedback Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│    ┌──────────┐     ┌──────────┐     ┌──────────────┐          │
│    │  EXPLORE │────▶│ EVALUATE │────▶│   DECIDE     │          │
│    └──────────┘     └──────────┘     └──────────────┘          │
│         ▲                                   │                   │
│         │                                   ▼                   │
│         │           ┌───────────────────────────────────────┐   │
│         │           │            DECISION OUTCOMES          │   │
│         │           ├───────────────────────────────────────┤   │
│         │           │  ✓ GOAL_REACHED → Return solution     │   │
│         │           │  → CONTINUE → Explore more            │──┘
│         │           │  ⚠ REQUEST_BUDGET → Ask for more      │
│         │           │  ≈ PROPOSE_COMPROMISE → Offer tradeoff│
│         │           │  ✗ ANTICIPATE_FAILURE → Prevent/mitig │
│         │           └───────────────────────────────────────┘
│         │                                   │
│         └───────────────────────────────────┘
│                     (with feedback)
└─────────────────────────────────────────────────────────────────┘
```

---

## Part I: Depth-Aware Reasoning with Feedback

### The Problem with Fixed Depth

Current implementation uses fixed `max_depth`:

```python
# Current: rigid depth limit
config = SearchConfig(max_depth=10)
# At depth 10, search stops regardless of progress
```

This is problematic because:
- Some problems need depth 3, others need depth 20
- Stopping at max_depth might abandon a near-solution
- Continuing past useful depth wastes resources

### Solution: Adaptive Depth with Soft/Hard Limits

```python
@dataclass
class DepthPolicy:
    """
    Policy for managing search depth with feedback.

    soft_limit: Depth at which to pause and evaluate progress
    hard_limit: Absolute maximum depth (safety bound)
    min_progress_rate: Minimum score improvement to justify continuing
    stagnation_threshold: Depths without improvement before concern
    """

    soft_limit: int = 7
    hard_limit: int = 15
    min_progress_rate: float = 0.05  # 5% improvement per depth
    stagnation_threshold: int = 3    # 3 depths without improvement

    def evaluate_depth(
        self,
        current_depth: int,
        score_history: list[float],
    ) -> DepthDecision:
        """
        Evaluate whether to continue deeper.

        Returns:
            DepthDecision with action and reasoning
        """
        if current_depth >= self.hard_limit:
            return DepthDecision(
                action=DepthAction.STOP,
                reason="Hard depth limit reached",
                suggestion="Consider problem decomposition"
            )

        if current_depth >= self.soft_limit:
            # Evaluate progress
            if len(score_history) >= 2:
                recent_progress = score_history[-1] - score_history[-2]

                if recent_progress < self.min_progress_rate:
                    return DepthDecision(
                        action=DepthAction.REQUEST_FEEDBACK,
                        reason=f"Progress slowing: {recent_progress:.1%} < {self.min_progress_rate:.1%}",
                        suggestion="May need different approach or more resources"
                    )

            # Check for stagnation
            if self._is_stagnating(score_history):
                return DepthDecision(
                    action=DepthAction.REQUEST_FEEDBACK,
                    reason="Score stagnating across multiple depths",
                    suggestion="Current approach may be exhausted"
                )

        return DepthDecision(action=DepthAction.CONTINUE)

    def _is_stagnating(self, score_history: list[float]) -> bool:
        """Check if scores have plateaued."""
        if len(score_history) < self.stagnation_threshold:
            return False

        recent = score_history[-self.stagnation_threshold:]
        max_diff = max(recent) - min(recent)
        return max_diff < 0.01  # Less than 1% variation
```

### Depth Feedback Integration

```python
@dataclass
class DepthDecision:
    """Result of depth evaluation."""
    action: DepthAction
    reason: str = ""
    suggestion: str = ""
    estimated_additional_depth_needed: int | None = None

class DepthAction(Enum):
    CONTINUE = "continue"           # Keep going
    STOP = "stop"                   # Hard stop
    REQUEST_FEEDBACK = "feedback"   # Ask supervisor/user
    BACKTRACK = "backtrack"         # Try different branch
```

### Modified Search Loop with Depth Awareness

```python
async def depth_aware_search(
    graph: Graph[T],
    expand: Expander[T],
    evaluate: Evaluator[T],
    config: SearchConfig,
    depth_policy: DepthPolicy,
    feedback_handler: FeedbackHandler,
) -> SearchResult[T]:
    """
    Search with depth-aware feedback loops.
    """
    score_history: list[float] = []
    current_depth = 0

    while True:
        # Standard beam search step
        beam = await expand_and_evaluate_beam(graph, beam, expand, evaluate)

        # Track best score at this depth
        best_at_depth = max(t.score for t in beam)
        score_history.append(best_at_depth)

        # Evaluate depth decision
        decision = depth_policy.evaluate_depth(current_depth, score_history)

        match decision.action:
            case DepthAction.CONTINUE:
                current_depth += 1

            case DepthAction.STOP:
                return SearchResult(
                    best_path=find_best_path(graph),
                    completed=True,
                    termination_reason=decision.reason,
                )

            case DepthAction.REQUEST_FEEDBACK:
                # Ask for guidance
                feedback = await feedback_handler.request_depth_feedback(
                    current_depth=current_depth,
                    score_history=score_history,
                    best_thought=find_best_thought(beam),
                    decision=decision,
                )

                match feedback.directive:
                    case FeedbackDirective.CONTINUE_DEEPER:
                        depth_policy.soft_limit += feedback.additional_depth
                        current_depth += 1
                    case FeedbackDirective.STOP_AND_RETURN:
                        return SearchResult(completed=True, ...)
                    case FeedbackDirective.TRY_DIFFERENT_BRANCH:
                        beam = feedback.alternative_beam

            case DepthAction.BACKTRACK:
                # Revert to earlier promising branch
                beam = select_alternative_beam(graph, score_history)
                current_depth = get_depth_of_beam(beam)
```

---

## Part II: Budget Negotiation

### The Problem with Fixed Budgets

Current budget handling:
```python
# Current: binary pass/fail
if budget.is_exhausted:
    raise BudgetExhausted()  # Operation fails
```

This is problematic because:
- We might be 90% of the way to a solution
- The caller doesn't know WHY more budget is needed
- No opportunity to approve additional resources

### Solution: Budget Negotiation Protocol

```python
@dataclass
class BudgetSituation:
    """Assessment of current budget situation."""

    # Current state
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
        return self.budget_consumed / self.budget_total if self.budget_total > 0 else 0

    @property
    def gap_to_acceptable(self) -> float:
        return max(0, self.acceptable_threshold - self.best_score_achieved)

    @property
    def has_acceptable_solution(self) -> bool:
        return self.best_score_achieved >= self.acceptable_threshold


@dataclass
class BudgetNegotiationResult:
    """Result of budget negotiation."""

    decision: BudgetDecision

    # If requesting increase
    requested_amount: int | None = None
    justification: str | None = None

    # If proposing compromise
    compromise: "CompromiseSolution | None" = None

    # Metadata
    situation: BudgetSituation | None = None


class BudgetDecision(Enum):
    SUFFICIENT = "sufficient"           # Budget is enough, continue
    REQUEST_INCREASE = "request"        # Ask for more budget
    PROPOSE_COMPROMISE = "compromise"   # Offer good-enough solution
    TERMINATE = "terminate"             # Cannot continue, no compromise


class BudgetNegotiator:
    """
    Negotiates budget allocation during search.

    Instead of failing when budget runs out, this component:
    1. Assesses the current situation
    2. Estimates what additional budget might achieve
    3. Proposes either a budget increase or a compromise
    """

    def __init__(
        self,
        acceptable_threshold: float = 0.7,
        goal_threshold: float = 0.95,
        compromise_threshold: float = 0.5,
        tokens_per_expansion: int = 1500,  # Estimated
    ):
        self.acceptable_threshold = acceptable_threshold
        self.goal_threshold = goal_threshold
        self.compromise_threshold = compromise_threshold
        self.tokens_per_expansion = tokens_per_expansion

    def assess_situation(
        self,
        graph: Graph,
        budget: Budget,
    ) -> BudgetSituation:
        """Assess current budget situation."""

        best_thought = max(graph.all_thoughts(), key=lambda t: t.score)

        # Estimate tokens needed based on current progress rate
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

        return BudgetSituation(
            budget_remaining=budget.remaining,
            budget_consumed=budget.consumed,
            budget_total=budget.total,
            best_score_achieved=best_thought.score,
            acceptable_threshold=self.acceptable_threshold,
            goal_threshold=self.goal_threshold,
            estimated_tokens_for_acceptable=estimated_for_acceptable,
            estimated_tokens_for_goal=estimated_for_goal,
            confidence_in_estimates=self._estimate_confidence(graph),
        )

    def negotiate(
        self,
        situation: BudgetSituation,
        graph: Graph,
    ) -> BudgetNegotiationResult:
        """
        Negotiate based on current situation.

        Decision logic:
        1. If we have acceptable solution → SUFFICIENT
        2. If budget remains and progress possible → SUFFICIENT
        3. If budget exhausted but close to acceptable → REQUEST_INCREASE
        4. If compromise available → PROPOSE_COMPROMISE
        5. Otherwise → TERMINATE
        """

        # Case 1: Already have acceptable solution
        if situation.has_acceptable_solution:
            return BudgetNegotiationResult(
                decision=BudgetDecision.SUFFICIENT,
                situation=situation,
            )

        # Case 2: Budget remains
        if situation.budget_remaining > self.tokens_per_expansion:
            return BudgetNegotiationResult(
                decision=BudgetDecision.SUFFICIENT,
                situation=situation,
            )

        # Case 3: Budget exhausted, evaluate options

        # Can we get to acceptable with reasonable additional budget?
        if situation.estimated_tokens_for_acceptable is not None:
            additional_needed = situation.estimated_tokens_for_acceptable

            # If additional budget is less than 50% of original, request it
            if additional_needed < situation.budget_total * 0.5:
                return BudgetNegotiationResult(
                    decision=BudgetDecision.REQUEST_INCREASE,
                    requested_amount=additional_needed,
                    justification=self._build_justification(situation),
                    situation=situation,
                )

        # Case 4: Look for compromise
        compromise = self._find_compromise(graph, situation)
        if compromise is not None:
            return BudgetNegotiationResult(
                decision=BudgetDecision.PROPOSE_COMPROMISE,
                compromise=compromise,
                situation=situation,
            )

        # Case 5: No good options
        return BudgetNegotiationResult(
            decision=BudgetDecision.TERMINATE,
            situation=situation,
        )

    def _estimate_tokens_to_score(
        self,
        current_score: float,
        target_score: float,
        graph: Graph,
    ) -> int | None:
        """
        Estimate tokens needed to reach target score.

        Based on observed progress rate in the graph.
        """
        if current_score >= target_score:
            return 0

        # Calculate historical progress rate
        thoughts = list(graph.all_thoughts())
        if len(thoughts) < 2:
            return None

        # Score improvement per expansion
        total_expansions = len(thoughts) - len(graph.roots())
        if total_expansions == 0:
            return None

        score_improvement = current_score - min(t.score for t in graph.roots())
        improvement_per_expansion = score_improvement / total_expansions

        if improvement_per_expansion <= 0:
            return None  # No progress being made

        # Estimate expansions needed
        score_gap = target_score - current_score
        expansions_needed = int(score_gap / improvement_per_expansion) + 1

        # Convert to tokens
        return expansions_needed * self.tokens_per_expansion

    def _build_justification(self, situation: BudgetSituation) -> str:
        """Build human-readable justification for budget request."""
        return (
            f"Current best score: {situation.best_score_achieved:.1%}\n"
            f"Acceptable threshold: {situation.acceptable_threshold:.1%}\n"
            f"Gap: {situation.gap_to_acceptable:.1%}\n"
            f"Budget used: {situation.utilization:.1%}\n"
            f"Estimated additional tokens needed: {situation.estimated_tokens_for_acceptable}\n"
            f"Confidence in estimate: {situation.confidence_in_estimates:.1%}"
        )

    def _find_compromise(
        self,
        graph: Graph,
        situation: BudgetSituation,
    ) -> "CompromiseSolution | None":
        """Find best compromise solution if full solution not achievable."""

        # Get all thoughts above compromise threshold
        candidates = [
            t for t in graph.all_thoughts()
            if t.score >= self.compromise_threshold
        ]

        if not candidates:
            return None

        best_candidate = max(candidates, key=lambda t: t.score)

        return CompromiseSolution(
            thought=best_candidate,
            path=graph.path_to_root(best_candidate)[::-1],
            score=best_candidate.score,
            gap_to_acceptable=situation.acceptable_threshold - best_candidate.score,
            tradeoffs=self._identify_tradeoffs(best_candidate, situation),
        )

    def _identify_tradeoffs(
        self,
        thought: Thought,
        situation: BudgetSituation,
    ) -> list[str]:
        """Identify what's being sacrificed in a compromise."""
        tradeoffs = []

        gap = situation.acceptable_threshold - thought.score
        if gap > 0.2:
            tradeoffs.append("Solution quality significantly below target")
        elif gap > 0.1:
            tradeoffs.append("Solution quality moderately below target")
        else:
            tradeoffs.append("Solution quality slightly below target")

        return tradeoffs

    def _estimate_confidence(self, graph: Graph) -> float:
        """Estimate confidence in our predictions."""
        thoughts = list(graph.all_thoughts())

        # More thoughts = more data = higher confidence
        thought_factor = min(1.0, len(thoughts) / 50)

        # Consistent progress = higher confidence
        # (would need score history to compute properly)

        return thought_factor * 0.8  # Cap at 80%
```

### Compromise Solution Structure

```python
@dataclass
class CompromiseSolution:
    """
    A solution that doesn't meet the full goal but is acceptable.

    Includes explicit documentation of what's being traded off.
    """

    thought: Thought
    """The best thought found."""

    path: list[Thought]
    """Reasoning path from root to this thought."""

    score: float
    """Score achieved (below goal but above minimum)."""

    gap_to_acceptable: float
    """How far below the acceptable threshold."""

    tradeoffs: list[str]
    """What's being sacrificed in this compromise."""

    def explain(self) -> str:
        """Human-readable explanation of the compromise."""
        return (
            f"Compromise Solution (score: {self.score:.1%})\n"
            f"Gap to acceptable: {self.gap_to_acceptable:.1%}\n"
            f"Tradeoffs:\n" +
            "\n".join(f"  - {t}" for t in self.tradeoffs)
        )
```

---

## Part III: Anticipatory Failure Handling

### Known Failure Modes

Before starting, enumerate what can go wrong:

```python
class FailureMode(Enum):
    """Known failure modes for GoT search."""

    BUDGET_EXHAUSTED = "budget_exhausted"
    """Ran out of tokens before finding solution."""

    DEPTH_EXCEEDED = "depth_exceeded"
    """Hit maximum depth without convergence."""

    QUALITY_PLATEAU = "quality_plateau"
    """Scores stopped improving."""

    CIRCULAR_REASONING = "circular_reasoning"
    """Thoughts are repeating or cycling."""

    GROUNDING_FAILURE = "grounding_failure"
    """Generated solutions don't work in practice."""

    GENERATOR_EXHAUSTION = "generator_exhaustion"
    """Generator producing low-quality/duplicate thoughts."""

    EVALUATOR_UNRELIABLE = "evaluator_unreliable"
    """Scores are inconsistent or unreliable."""

    PROBLEM_INTRACTABLE = "problem_intractable"
    """Problem may not be solvable with current approach."""
```

### Anticipatory Failure Detection

```python
@dataclass
class AnticipatedFailure:
    """A failure mode that might occur."""

    mode: FailureMode
    likelihood: float  # 0.0 to 1.0
    estimated_when: int | None  # Depth/iteration when likely
    prevention: str | None  # What could prevent it
    mitigation: str | None  # What to do if it happens


class FailureAnticipator:
    """
    Predicts and prepares for failure modes.

    Runs continuously during search to:
    1. Detect early warning signs
    2. Estimate likelihood of each failure
    3. Suggest preventive actions
    4. Prepare mitigation strategies
    """

    def __init__(self):
        self.detectors: dict[FailureMode, FailureDetector] = {
            FailureMode.BUDGET_EXHAUSTED: BudgetExhaustionDetector(),
            FailureMode.DEPTH_EXCEEDED: DepthExceededDetector(),
            FailureMode.QUALITY_PLATEAU: QualityPlateauDetector(),
            FailureMode.CIRCULAR_REASONING: CircularReasoningDetector(),
            FailureMode.GROUNDING_FAILURE: GroundingFailureDetector(),
            FailureMode.GENERATOR_EXHAUSTION: GeneratorExhaustionDetector(),
        }

    def anticipate(
        self,
        graph: Graph,
        budget: Budget,
        score_history: list[float],
        config: SearchConfig,
    ) -> list[AnticipatedFailure]:
        """
        Analyze current state and predict likely failures.
        """
        predictions = []

        state = SearchState(
            graph=graph,
            budget=budget,
            score_history=score_history,
            config=config,
        )

        for mode, detector in self.detectors.items():
            assessment = detector.assess(state)

            if assessment.likelihood > 0.3:  # 30% threshold for concern
                predictions.append(AnticipatedFailure(
                    mode=mode,
                    likelihood=assessment.likelihood,
                    estimated_when=assessment.estimated_when,
                    prevention=assessment.prevention,
                    mitigation=assessment.mitigation,
                ))

        # Sort by likelihood (most likely first)
        predictions.sort(key=lambda p: p.likelihood, reverse=True)

        return predictions


class BudgetExhaustionDetector:
    """Detects impending budget exhaustion."""

    def assess(self, state: SearchState) -> FailureAssessment:
        budget = state.budget

        # Calculate consumption rate
        thoughts_created = len(list(state.graph.all_thoughts()))
        tokens_per_thought = budget.consumed / max(1, thoughts_created)

        # Estimate remaining thoughts possible
        remaining_thoughts = budget.remaining / tokens_per_thought if tokens_per_thought > 0 else 0

        # Estimate if we can reach acceptable score
        current_best = max((t.score for t in state.graph.all_thoughts()), default=0)
        score_gap = 0.7 - current_best  # 0.7 = acceptable threshold

        if score_gap <= 0:
            return FailureAssessment(likelihood=0.0)  # Already acceptable

        # Progress rate
        if len(state.score_history) >= 2:
            progress_rate = (state.score_history[-1] - state.score_history[0]) / len(state.score_history)
            thoughts_needed = score_gap / progress_rate if progress_rate > 0 else float('inf')

            if thoughts_needed > remaining_thoughts:
                likelihood = min(1.0, (thoughts_needed - remaining_thoughts) / thoughts_needed)
                return FailureAssessment(
                    likelihood=likelihood,
                    estimated_when=int(remaining_thoughts),
                    prevention="Request budget increase before exhaustion",
                    mitigation="Accept best available compromise solution",
                )

        # Default: estimate based on utilization
        utilization = budget.consumed / budget.total
        if utilization > 0.8:
            return FailureAssessment(
                likelihood=0.5,
                prevention="Increase beam pruning to conserve budget",
                mitigation="Prepare compromise solution",
            )

        return FailureAssessment(likelihood=utilization * 0.3)


class QualityPlateauDetector:
    """Detects when score improvement has stalled."""

    def assess(self, state: SearchState) -> FailureAssessment:
        history = state.score_history

        if len(history) < 5:
            return FailureAssessment(likelihood=0.1)  # Not enough data

        # Check last 5 scores for plateau
        recent = history[-5:]
        improvement = recent[-1] - recent[0]
        variance = max(recent) - min(recent)

        if improvement < 0.01 and variance < 0.02:
            # Stagnant for 5 iterations
            return FailureAssessment(
                likelihood=0.8,
                prevention="Try expanding from different branch",
                mitigation="Consider problem reformulation",
            )

        if improvement < 0.02:
            return FailureAssessment(
                likelihood=0.4,
                prevention="Increase exploration (wider beam)",
                mitigation="Accept current best if above minimum",
            )

        return FailureAssessment(likelihood=0.1)


class CircularReasoningDetector:
    """Detects when thoughts are repeating or cycling."""

    def assess(self, state: SearchState) -> FailureAssessment:
        thoughts = list(state.graph.all_thoughts())

        # Check for semantic duplicates (simplified: exact content match)
        contents = [str(t.content) for t in thoughts]
        unique_contents = set(contents)

        duplication_rate = 1 - (len(unique_contents) / len(contents)) if contents else 0

        if duplication_rate > 0.3:
            return FailureAssessment(
                likelihood=0.7,
                prevention="Add semantic deduplication",
                mitigation="Prune duplicate thoughts and increase diversity",
            )

        if duplication_rate > 0.1:
            return FailureAssessment(
                likelihood=0.3,
                prevention="Tune generator for more diversity",
            )

        return FailureAssessment(likelihood=duplication_rate)


@dataclass
class FailureAssessment:
    """Assessment from a failure detector."""
    likelihood: float
    estimated_when: int | None = None
    prevention: str | None = None
    mitigation: str | None = None
```

---

## Part IV: Domain-Specific Grounding

### The Grounding Protocol

```python
class Grounder(Protocol[T]):
    """
    Protocol for grounding thoughts in external reality.

    Grounding transforms theoretical thoughts into verified facts
    by testing them against real-world execution.
    """

    async def ground(
        self,
        thought: Thought[T],
        context: GroundingContext,
    ) -> GroundingResult:
        """
        Test a thought against reality.

        Args:
            thought: The thought to verify
            context: Information needed for grounding

        Returns:
            GroundingResult with verification status
        """
        ...

    def can_ground(self, thought: Thought[T]) -> bool:
        """Check if this thought can be grounded."""
        ...


@dataclass
class GroundingResult:
    """Result of grounding a thought."""

    grounded: bool
    """Whether the thought was successfully grounded."""

    verified: bool | None
    """If grounded, whether it passed verification."""

    evidence: str
    """Evidence from the grounding (output, logs, etc.)."""

    confidence: float
    """Confidence in the verification (0.0 to 1.0)."""

    execution_time_ms: int
    """How long grounding took."""

    resource_cost: int
    """Resources consumed (tokens, compute, etc.)."""
```

### Code Generation Grounder

```python
class CodeGenerationGrounder:
    """
    Grounder for code generation tasks.

    Grounds thoughts by:
    1. Extracting code from thought content
    2. Running syntax validation
    3. Executing tests if available
    4. Checking for runtime errors
    """

    def __init__(
        self,
        test_runner: TestRunner,
        sandbox: CodeSandbox,
        timeout_ms: int = 30000,
    ):
        self.test_runner = test_runner
        self.sandbox = sandbox
        self.timeout_ms = timeout_ms

    async def ground(
        self,
        thought: Thought[str],
        context: GroundingContext,
    ) -> GroundingResult:
        """Ground a code thought by execution."""

        start_time = time.monotonic()

        # Extract code from thought
        code = self._extract_code(thought.content)
        if code is None:
            return GroundingResult(
                grounded=False,
                verified=None,
                evidence="No code found in thought",
                confidence=0.0,
                execution_time_ms=0,
                resource_cost=0,
            )

        # Syntax validation
        syntax_result = await self.sandbox.check_syntax(code)
        if not syntax_result.valid:
            return GroundingResult(
                grounded=True,
                verified=False,
                evidence=f"Syntax error: {syntax_result.error}",
                confidence=1.0,  # Certain it's wrong
                execution_time_ms=self._elapsed_ms(start_time),
                resource_cost=10,
            )

        # Run tests
        test_result = await self.test_runner.run(
            code=code,
            test_file=context.test_file,
            timeout_ms=self.timeout_ms,
        )

        return GroundingResult(
            grounded=True,
            verified=test_result.passed,
            evidence=test_result.output,
            confidence=1.0 if test_result.passed else 0.9,
            execution_time_ms=self._elapsed_ms(start_time),
            resource_cost=test_result.tokens_used,
        )

    def can_ground(self, thought: Thought[str]) -> bool:
        """Check if thought contains groundable code."""
        return "```" in thought.content or self._looks_like_code(thought.content)

    def _extract_code(self, content: str) -> str | None:
        """Extract code block from content."""
        # Look for markdown code blocks
        import re
        match = re.search(r"```(?:\w+)?\n(.*?)```", content, re.DOTALL)
        if match:
            return match.group(1)

        # Check if content itself is code
        if self._looks_like_code(content):
            return content

        return None

    def _looks_like_code(self, content: str) -> bool:
        """Heuristic: does content look like code?"""
        code_indicators = ["def ", "class ", "import ", "return ", "if ", "for "]
        return any(indicator in content for indicator in code_indicators)

    def _elapsed_ms(self, start_time: float) -> int:
        return int((time.monotonic() - start_time) * 1000)
```

### Debugging Grounder

```python
class DebuggingGrounder:
    """
    Grounder for debugging tasks.

    Grounds thoughts (bug hypotheses) by:
    1. Attempting to reproduce the bug with the hypothesis
    2. Testing proposed fixes
    3. Verifying fix doesn't break other functionality
    """

    def __init__(
        self,
        reproducer: BugReproducer,
        test_suite: TestSuite,
    ):
        self.reproducer = reproducer
        self.test_suite = test_suite

    async def ground(
        self,
        thought: Thought[str],
        context: GroundingContext,
    ) -> GroundingResult:
        """Ground a debugging hypothesis."""

        thought_type = self._classify_thought(thought)

        match thought_type:
            case ThoughtType.HYPOTHESIS:
                return await self._ground_hypothesis(thought, context)
            case ThoughtType.FIX:
                return await self._ground_fix(thought, context)
            case _:
                return GroundingResult(
                    grounded=False,
                    verified=None,
                    evidence="Cannot ground this thought type",
                    confidence=0.0,
                    execution_time_ms=0,
                    resource_cost=0,
                )

    async def _ground_hypothesis(
        self,
        thought: Thought[str],
        context: GroundingContext,
    ) -> GroundingResult:
        """Test if a bug hypothesis is correct."""

        # Try to reproduce the bug based on the hypothesis
        reproduction = await self.reproducer.reproduce(
            hypothesis=thought.content,
            bug_report=context.bug_report,
        )

        return GroundingResult(
            grounded=True,
            verified=reproduction.reproduced,
            evidence=reproduction.trace,
            confidence=reproduction.confidence,
            execution_time_ms=reproduction.time_ms,
            resource_cost=reproduction.cost,
        )

    async def _ground_fix(
        self,
        thought: Thought[str],
        context: GroundingContext,
    ) -> GroundingResult:
        """Test if a proposed fix works."""

        # Apply the fix
        fix_code = self._extract_fix(thought.content)

        # Run the test that was failing
        failing_test_result = await self.test_suite.run_specific(
            test=context.failing_test,
            with_patch=fix_code,
        )

        if not failing_test_result.passed:
            return GroundingResult(
                grounded=True,
                verified=False,
                evidence=f"Fix doesn't resolve the bug: {failing_test_result.output}",
                confidence=1.0,
                execution_time_ms=failing_test_result.time_ms,
                resource_cost=failing_test_result.cost,
            )

        # Run regression tests
        regression_result = await self.test_suite.run_all(with_patch=fix_code)

        return GroundingResult(
            grounded=True,
            verified=regression_result.passed,
            evidence=(
                f"Fix resolves bug. "
                f"Regression: {regression_result.passed_count}/{regression_result.total_count} tests pass"
            ),
            confidence=regression_result.passed_count / regression_result.total_count,
            execution_time_ms=regression_result.time_ms,
            resource_cost=regression_result.cost,
        )
```

### Research Synthesis Grounder

```python
class ResearchGrounder:
    """
    Grounder for research synthesis tasks.

    Grounds thoughts (claims, hypotheses) by:
    1. Checking citations and sources
    2. Cross-referencing with known facts
    3. Identifying contradictions
    """

    def __init__(
        self,
        knowledge_base: KnowledgeBase,
        citation_checker: CitationChecker,
    ):
        self.knowledge_base = knowledge_base
        self.citation_checker = citation_checker

    async def ground(
        self,
        thought: Thought[str],
        context: GroundingContext,
    ) -> GroundingResult:
        """Ground a research claim."""

        # Extract claims from thought
        claims = self._extract_claims(thought.content)

        if not claims:
            return GroundingResult(
                grounded=False,
                verified=None,
                evidence="No verifiable claims found",
                confidence=0.0,
                execution_time_ms=0,
                resource_cost=0,
            )

        # Verify each claim
        verifications = []
        for claim in claims:
            verification = await self._verify_claim(claim)
            verifications.append(verification)

        # Aggregate results
        verified_count = sum(1 for v in verifications if v.verified)
        total_count = len(verifications)

        return GroundingResult(
            grounded=True,
            verified=verified_count == total_count,
            evidence=self._format_verifications(verifications),
            confidence=verified_count / total_count,
            execution_time_ms=sum(v.time_ms for v in verifications),
            resource_cost=sum(v.cost for v in verifications),
        )

    async def _verify_claim(self, claim: str) -> ClaimVerification:
        """Verify a single claim."""

        # Check knowledge base
        kb_result = await self.knowledge_base.check(claim)

        # Check citations if present
        citation_result = await self.citation_checker.check(claim)

        # Combine evidence
        verified = kb_result.supported and (
            citation_result.valid if citation_result else True
        )

        return ClaimVerification(
            claim=claim,
            verified=verified,
            evidence=f"KB: {kb_result.evidence}. Citations: {citation_result}",
            time_ms=kb_result.time_ms + (citation_result.time_ms if citation_result else 0),
            cost=kb_result.cost + (citation_result.cost if citation_result else 0),
        )
```

---

## Part V: Integration Architecture

### The Complete Search Controller

```python
class AdaptiveSearchController:
    """
    Orchestrates search with all self-aware capabilities.

    Integrates:
    - Depth-aware feedback
    - Budget negotiation
    - Anticipatory failure handling
    - Domain-specific grounding
    """

    def __init__(
        self,
        graph: Graph,
        expander: Expander,
        evaluator: Evaluator,
        grounder: Grounder | None,
        config: SearchConfig,
        depth_policy: DepthPolicy,
        budget_negotiator: BudgetNegotiator,
        failure_anticipator: FailureAnticipator,
        feedback_handler: FeedbackHandler,
    ):
        self.graph = graph
        self.expander = expander
        self.evaluator = evaluator
        self.grounder = grounder
        self.config = config
        self.depth_policy = depth_policy
        self.budget_negotiator = budget_negotiator
        self.failure_anticipator = failure_anticipator
        self.feedback_handler = feedback_handler

    async def search(
        self,
        budget: Budget,
    ) -> AdaptiveSearchResult:
        """
        Execute search with full self-awareness.
        """

        score_history: list[float] = []
        current_depth = 0
        beam = self.graph.roots()

        # Track anticipated failures
        all_anticipated_failures: list[AnticipatedFailure] = []

        while True:
            # ===== PHASE 1: Anticipate Failures =====
            anticipated = self.failure_anticipator.anticipate(
                graph=self.graph,
                budget=budget,
                score_history=score_history,
                config=self.config,
            )
            all_anticipated_failures.extend(anticipated)

            # Handle high-likelihood failures
            for failure in anticipated:
                if failure.likelihood > 0.7:
                    action = await self._handle_anticipated_failure(failure)
                    if action == FailureAction.ABORT:
                        return self._build_result(
                            completed=False,
                            reason=f"Anticipated failure: {failure.mode}",
                        )

            # ===== PHASE 2: Check Budget =====
            situation = self.budget_negotiator.assess_situation(self.graph, budget)
            negotiation = self.budget_negotiator.negotiate(situation, self.graph)

            match negotiation.decision:
                case BudgetDecision.REQUEST_INCREASE:
                    response = await self.feedback_handler.request_budget_increase(
                        requested_amount=negotiation.requested_amount,
                        justification=negotiation.justification,
                        compromise=negotiation.compromise,
                    )

                    match response.decision:
                        case BudgetResponse.APPROVED:
                            budget = budget.add(response.additional_amount)
                        case BudgetResponse.ACCEPT_COMPROMISE:
                            return self._build_result(
                                completed=True,
                                compromise=negotiation.compromise,
                            )
                        case BudgetResponse.DENY:
                            return self._build_result(
                                completed=False,
                                reason="Budget increase denied",
                            )

                case BudgetDecision.PROPOSE_COMPROMISE:
                    accepted = await self.feedback_handler.propose_compromise(
                        negotiation.compromise
                    )
                    if accepted:
                        return self._build_result(
                            completed=True,
                            compromise=negotiation.compromise,
                        )

                case BudgetDecision.TERMINATE:
                    return self._build_result(
                        completed=False,
                        reason="Cannot continue: no budget and no acceptable compromise",
                    )

            # ===== PHASE 3: Check Depth =====
            depth_decision = self.depth_policy.evaluate_depth(
                current_depth, score_history
            )

            match depth_decision.action:
                case DepthAction.STOP:
                    return self._build_result(
                        completed=True,
                        reason=depth_decision.reason,
                    )

                case DepthAction.REQUEST_FEEDBACK:
                    feedback = await self.feedback_handler.request_depth_feedback(
                        current_depth=current_depth,
                        score_history=score_history,
                        decision=depth_decision,
                    )

                    if feedback.directive == FeedbackDirective.STOP_AND_RETURN:
                        return self._build_result(completed=True)
                    elif feedback.directive == FeedbackDirective.CONTINUE_DEEPER:
                        self.depth_policy.soft_limit += feedback.additional_depth

            # ===== PHASE 4: Expand and Evaluate =====
            new_thoughts = []
            for parent in beam:
                children_content = await self.expander(parent, self._make_context(current_depth))

                for content in children_content:
                    child = Thought(content=content)
                    self.graph.add(child, parent=parent)

                    # Evaluate
                    child.score = await self.evaluator(child, self._make_context(current_depth + 1))

                    # Ground if possible
                    if self.grounder and self.grounder.can_ground(child):
                        grounding = await self.grounder.ground(child, self._make_grounding_context())
                        child.grounded = grounding.grounded
                        child.verified = grounding.verified

                        # Adjust score based on grounding
                        if grounding.verified is False:
                            child.score *= 0.1  # Heavily penalize failed verification
                        elif grounding.verified is True:
                            child.score = min(1.0, child.score * 1.2)  # Boost verified thoughts

                    new_thoughts.append(child)

                    # Check for goal
                    if child.score >= self.config.goal_score:
                        return self._build_result(
                            completed=True,
                            goal_reached=True,
                        )

            # ===== PHASE 5: Update State =====
            if not new_thoughts:
                return self._build_result(
                    completed=True,
                    reason="No more thoughts to explore",
                )

            # Track best score
            best_score = max(t.score for t in new_thoughts)
            score_history.append(best_score)

            # Select beam for next iteration
            new_thoughts.sort(key=lambda t: t.score, reverse=True)
            beam = new_thoughts[:self.config.beam_width]

            current_depth += 1

    async def _handle_anticipated_failure(
        self,
        failure: AnticipatedFailure,
    ) -> FailureAction:
        """Handle an anticipated failure."""

        # Try prevention first
        if failure.prevention:
            prevented = await self._try_prevention(failure)
            if prevented:
                return FailureAction.CONTINUE

        # Ask for guidance
        return await self.feedback_handler.handle_anticipated_failure(failure)

    def _build_result(
        self,
        completed: bool,
        reason: str | None = None,
        compromise: CompromiseSolution | None = None,
        goal_reached: bool = False,
    ) -> AdaptiveSearchResult:
        """Build the final search result."""

        best_thought = max(self.graph.all_thoughts(), key=lambda t: t.score)
        best_path = self.graph.path_to_root(best_thought)[::-1]

        return AdaptiveSearchResult(
            best_path=best_path,
            best_score=best_thought.score,
            completed=completed,
            goal_reached=goal_reached,
            termination_reason=reason,
            compromise=compromise,
            thoughts_expanded=len(list(self.graph.all_thoughts())),
            max_depth_reached=max(len(self.graph.path_to_root(t)) for t in self.graph.leaves()),
        )


@dataclass
class AdaptiveSearchResult:
    """Result of adaptive search with full metadata."""

    best_path: list[Thought]
    best_score: float
    completed: bool
    goal_reached: bool = False
    termination_reason: str | None = None
    compromise: CompromiseSolution | None = None
    thoughts_expanded: int = 0
    max_depth_reached: int = 0
    budget_requests: list[BudgetNegotiationResult] = field(default_factory=list)
    anticipated_failures: list[AnticipatedFailure] = field(default_factory=list)
```

---

## Part VI: Configuration Profiles

### Domain-Specific Defaults

```python
@dataclass
class DomainProfile:
    """Configuration profile for a specific domain."""

    name: str
    search_config: SearchConfig
    depth_policy: DepthPolicy
    acceptable_threshold: float
    goal_threshold: float
    grounder_type: type[Grounder] | None

    # Domain-specific settings
    extra_config: dict[str, Any] = field(default_factory=dict)


# Predefined profiles
CODE_GENERATION_PROFILE = DomainProfile(
    name="code_generation",
    search_config=SearchConfig(
        max_depth=12,
        beam_width=4,
        max_expansions=150,
        goal_score=0.95,  # High bar: code must work
    ),
    depth_policy=DepthPolicy(
        soft_limit=8,
        hard_limit=15,
        min_progress_rate=0.03,
        stagnation_threshold=4,
    ),
    acceptable_threshold=0.75,  # Code that mostly works
    goal_threshold=0.95,  # Code that passes all tests
    grounder_type=CodeGenerationGrounder,
    extra_config={
        "require_grounding": True,  # Must test code
        "syntax_check_early": True,  # Fail fast on syntax errors
    },
)

DEBUGGING_PROFILE = DomainProfile(
    name="debugging",
    search_config=SearchConfig(
        max_depth=10,
        beam_width=5,  # More hypotheses in parallel
        max_expansions=100,
        goal_score=0.90,  # Bug fixed and tests pass
    ),
    depth_policy=DepthPolicy(
        soft_limit=6,
        hard_limit=12,
        min_progress_rate=0.05,
        stagnation_threshold=3,
    ),
    acceptable_threshold=0.70,  # Plausible hypothesis
    goal_threshold=0.90,  # Verified fix
    grounder_type=DebuggingGrounder,
    extra_config={
        "require_reproduction": True,
        "run_regression_tests": True,
    },
)

RESEARCH_SYNTHESIS_PROFILE = DomainProfile(
    name="research_synthesis",
    search_config=SearchConfig(
        max_depth=15,  # Deeper exploration
        beam_width=3,
        max_expansions=200,
        goal_score=0.85,  # Research is inherently uncertain
    ),
    depth_policy=DepthPolicy(
        soft_limit=10,
        hard_limit=20,
        min_progress_rate=0.02,  # Slower progress expected
        stagnation_threshold=5,
    ),
    acceptable_threshold=0.60,  # Reasonable synthesis
    goal_threshold=0.85,  # Strong, well-supported synthesis
    grounder_type=ResearchGrounder,
    extra_config={
        "require_citations": True,
        "cross_reference_threshold": 0.7,
    },
)

STRATEGIC_PLANNING_PROFILE = DomainProfile(
    name="strategic_planning",
    search_config=SearchConfig(
        max_depth=8,  # Strategy shouldn't be too deep
        beam_width=4,
        max_expansions=80,
        goal_score=0.80,
    ),
    depth_policy=DepthPolicy(
        soft_limit=5,
        hard_limit=10,
        min_progress_rate=0.04,
        stagnation_threshold=3,
    ),
    acceptable_threshold=0.65,
    goal_threshold=0.80,
    grounder_type=None,  # Strategy is harder to ground
    extra_config={
        "require_actionable_steps": True,
        "max_strategy_branches": 3,
    },
)

DESIGN_PROFILE = DomainProfile(
    name="design",
    search_config=SearchConfig(
        max_depth=10,
        beam_width=4,
        max_expansions=120,
        goal_score=0.85,
    ),
    depth_policy=DepthPolicy(
        soft_limit=7,
        hard_limit=12,
        min_progress_rate=0.03,
        stagnation_threshold=4,
    ),
    acceptable_threshold=0.70,
    goal_threshold=0.85,
    grounder_type=None,  # Design grounding is domain-specific
    extra_config={
        "check_consistency": True,
        "validate_interfaces": True,
    },
)
```

---

## Part VII: Usage Example

```python
async def solve_coding_problem(
    problem: str,
    test_file: str,
    budget_tokens: int = 50000,
) -> AdaptiveSearchResult:
    """
    Complete example of using adaptive GoT for code generation.
    """

    # Load domain profile
    profile = CODE_GENERATION_PROFILE

    # Create graph with initial problem
    graph = Graph[str]()
    root = Thought(content=problem)
    graph.add(root)

    # Initialize components
    expander = LLMExpander(model="claude-3-opus")
    evaluator = LLMEvaluator(model="claude-3-haiku")  # Cheaper for eval
    grounder = CodeGenerationGrounder(
        test_runner=PytestRunner(),
        sandbox=DockerSandbox(),
    )

    budget = Budget(total=budget_tokens)

    # Create controller
    controller = AdaptiveSearchController(
        graph=graph,
        expander=expander,
        evaluator=evaluator,
        grounder=grounder,
        config=profile.search_config,
        depth_policy=profile.depth_policy,
        budget_negotiator=BudgetNegotiator(
            acceptable_threshold=profile.acceptable_threshold,
            goal_threshold=profile.goal_threshold,
        ),
        failure_anticipator=FailureAnticipator(),
        feedback_handler=InteractiveFeedbackHandler(),  # Or AutomaticFeedbackHandler
    )

    # Run search
    result = await controller.search(budget)

    # Handle result
    if result.goal_reached:
        print(f"Found solution with score {result.best_score:.1%}")
        print(f"Solution:\n{result.best_path[-1].content}")
    elif result.compromise:
        print(f"Proposing compromise (score {result.compromise.score:.1%})")
        print(result.compromise.explain())
    else:
        print(f"Could not find solution: {result.termination_reason}")

    return result
```

---

## Conclusion

This applied design transforms the Graph of Thought from a blind search mechanism into a **self-aware reasoning system** that:

1. **Knows its depth** and gets feedback when going too deep
2. **Negotiates budget** rather than failing when resources run low
3. **Proposes compromises** when perfect solutions aren't achievable
4. **Anticipates failures** before they happen
5. **Grounds thoughts** in domain-specific reality

The key insight is that **reasoning should be a dialogue**, not a monologue. The system should communicate its state, ask for help when stuck, and propose alternatives when constraints prevent the ideal solution.

This design is appropriate for the specified domains (code generation, research, planning, design, debugging) precisely because these tasks:
- Can tolerate latency (not real-time)
- Have clear quality criteria (groundable)
- Benefit from structured exploration (not purely creative)
- Have natural compromises (partial solutions have value)

The system thinks things through from start to finish, knows its limitations ahead of time, and gracefully handles the gap between what's desired and what's achievable.
