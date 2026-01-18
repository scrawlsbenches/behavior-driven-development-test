"""
LLM-Based Reasoning - Thinking with LLMs at Core Decision Points
=================================================================

THE FUNDAMENTAL INSIGHT
-----------------------

The previous design made a critical error: it tried to encode decision
logic in code. But we CANNOT know the right decisions upfront:

    # WRONG: Code decides with fixed thresholds
    if progress_rate < 0.05:
        return REQUEST_FEEDBACK

    # RIGHT: LLM reasons about the situation
    decision = await reasoner.reason(
        "Given this search state, should we continue deeper?",
        context=current_situation,
    )

The unknown cannot be handled with predetermined rules. The LLM must
reason through it at runtime, with full context.


WHERE LLMs MUST DECIDE
----------------------

There are core intersection points where reasoning is required:

    ┌─────────────────────────────────────────────────────────────────────┐
    │                     CORE DECISION POINTS                            │
    │                                                                     │
    │  1. DEPTH REASONING                                                 │
    │     "Should we continue deeper? Why or why not?"                    │
    │     The LLM sees: score history, current thoughts, goal             │
    │     The LLM decides: continue, stop, or try different path         │
    │                                                                     │
    │  2. BUDGET REASONING                                                │
    │     "Is more budget justified? What would it achieve?"              │
    │     The LLM sees: progress so far, what's needed, constraints       │
    │     The LLM decides: request amount, propose compromise, or stop   │
    │                                                                     │
    │  3. FAILURE REASONING                                               │
    │     "What could go wrong? What are the warning signs?"              │
    │     The LLM sees: current state, patterns, trajectory               │
    │     The LLM decides: what failures are likely, how to prevent      │
    │                                                                     │
    │  4. COMPROMISE REASONING                                            │
    │     "Is this good enough? What are we really sacrificing?"          │
    │     The LLM sees: best solution, goal, constraints                  │
    │     The LLM decides: accept, reject, or explain tradeoffs          │
    │                                                                     │
    │  5. PATH REASONING                                                  │
    │     "Which direction is most promising? Why?"                       │
    │     The LLM sees: current branches, scores, content                 │
    │     The LLM decides: which paths to pursue, which to abandon       │
    │                                                                     │
    │  6. META REASONING                                                  │
    │     "How is the overall search going? What should change?"          │
    │     The LLM sees: full search history, patterns, outcomes           │
    │     The LLM decides: strategy adjustments, when to pivot           │
    └─────────────────────────────────────────────────────────────────────┘


WHY LLMs, NOT CODE?
-------------------

Code-based decisions:
    - Fixed thresholds that may be wrong for this problem
    - No understanding of context or nuance
    - Can't explain why a decision was made
    - Can't adapt to unexpected situations

LLM-based reasoning:
    - Considers full context of the specific problem
    - Can explain its reasoning
    - Can recognize patterns we didn't anticipate
    - Can make nuanced judgments about quality

The Graph of Thought is about STRUCTURED REASONING. The structure comes
from the graph. The REASONING must come from an LLM.


THE REASONER PROTOCOL
---------------------

Every decision point uses the same pattern:

    class Reasoner(Protocol):
        async def reason(
            self,
            question: str,
            context: ReasoningContext,
        ) -> ReasoningResult:
            '''
            Ask the LLM to reason about a decision.

            Args:
                question: What we need to decide
                context: All relevant information

            Returns:
                ReasoningResult with decision and explanation
            '''
            ...

The LLM receives:
    - The specific question to answer
    - Full context about the situation
    - The options available
    - Constraints and goals

The LLM returns:
    - Its decision
    - Its reasoning (WHY it decided this)
    - Confidence level
    - Any caveats or concerns


REASONING CONTEXT
-----------------

The context given to the LLM must be comprehensive:

    @dataclass
    class ReasoningContext:
        # The original problem
        problem: str

        # Current state
        current_depth: int
        best_score: float
        score_history: list[float]

        # What we've explored
        thoughts_explored: int
        current_best_thought: str
        path_to_best: list[str]

        # Constraints
        budget_remaining: int
        budget_consumed: int
        depth_limit: int

        # Goals
        acceptable_threshold: float
        goal_threshold: float

        # Domain
        domain: str  # "code_generation", "debugging", etc.

        # Additional context
        extra: dict[str, Any]

The LLM has everything it needs to make an informed decision.


STRUCTURED REASONING PROMPTS
----------------------------

Each decision point has a structured prompt:

    DEPTH_REASONING_PROMPT = '''
    You are reasoning about whether to continue searching deeper.

    CURRENT SITUATION:
    - Depth: {depth} (limit: {depth_limit})
    - Best score: {best_score:.1%} (goal: {goal_threshold:.1%})
    - Score history: {score_history}
    - Budget remaining: {budget_remaining} tokens

    CURRENT BEST SOLUTION:
    {current_best_thought}

    QUESTION: Should we continue exploring deeper?

    Consider:
    1. Is progress still being made?
    2. Are we close enough to stop?
    3. Is the current direction promising?
    4. Would resources be better spent elsewhere?

    Respond with:
    - DECISION: CONTINUE | STOP | PIVOT
    - REASONING: Why you made this decision
    - CONFIDENCE: How confident you are (0.0-1.0)
    - CONCERNS: Any concerns or caveats
    '''


THE META-REASONER
-----------------

Above all specific reasoners is a META-REASONER that:
1. Monitors the overall search process
2. Decides when to invoke specific reasoners
3. Coordinates between different concerns
4. Can override or adjust other decisions

    meta_decision = await meta_reasoner.reason(
        question="How should we proceed with this search?",
        context=full_search_context,
    )

The meta-reasoner is the "executive function" of the search - it has
the big picture view and can make strategic decisions.


EXAMPLE: DEPTH DECISION WITH LLM
--------------------------------

Instead of:
    # Code decides based on threshold
    if progress_rate < 0.05:
        return DepthDecision(action=STOP)

We have:
    # LLM reasons about the situation
    result = await depth_reasoner.reason(
        question="Should we continue deeper?",
        context=ReasoningContext(
            problem="How do we optimize the database query?",
            current_depth=7,
            best_score=0.72,
            score_history=[0.3, 0.45, 0.55, 0.62, 0.68, 0.71, 0.72],
            current_best_thought="Add index on user_id column",
            budget_remaining=5000,
            ...
        ),
    )

    # LLM might respond:
    # DECISION: CONTINUE
    # REASONING: Score is still improving (0.71 -> 0.72) and we're close
    #            to acceptable (0.75). The indexing direction is promising.
    #            With 5000 tokens remaining, we can afford 2-3 more depths.
    # CONFIDENCE: 0.75
    # CONCERNS: Progress is slowing. If next depth doesn't improve by at
    #           least 0.02, we should reconsider.


IMPLEMENTATION NOTES
--------------------

1. PROMPT ENGINEERING
   The prompts must be carefully designed to:
   - Give the LLM all necessary context
   - Ask clear, specific questions
   - Request structured output
   - Include relevant constraints

2. OUTPUT PARSING
   LLM responses must be parsed reliably:
   - Use structured formats (JSON, XML)
   - Have fallback parsing
   - Validate decisions are valid options

3. COST MANAGEMENT
   LLM calls for reasoning have cost:
   - Use smaller/faster models for routine decisions
   - Cache similar decisions
   - Batch related questions
   - Only invoke reasoning when truly uncertain

4. RECURSION PREVENTION
   The reasoning LLM is DIFFERENT from the generation LLM:
   - Generation: Creates thought content
   - Reasoning: Makes meta-decisions about the search
   - Keep them separate to prevent confusion


RELATIONSHIP TO OTHER MODULES
-----------------------------

This module REPLACES the hardcoded logic in:
    - depth.py: DepthPolicy.evaluate_depth() → DepthReasoner.reason()
    - budget.py: BudgetNegotiator.negotiate() → BudgetReasoner.reason()
    - failure.py: FailureAnticipator.anticipate() → FailureReasoner.reason()
    - feedback.py: AutomaticFeedbackHandler → Replaced by LLM reasoning

The other modules still define the DATA STRUCTURES:
    - DepthDecision, BudgetSituation, etc. still exist
    - But they're created by LLM reasoning, not code rules

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Protocol, TypeVar, Generic
import json


# =============================================================================
# REASONING CONTEXT
# =============================================================================

@dataclass
class ReasoningContext:
    """
    Complete context for LLM reasoning.

    Contains everything the LLM needs to make an informed decision.
    This is the "state of the world" from the search's perspective.
    """

    # -------------------------------------------------------------------------
    # THE PROBLEM
    # -------------------------------------------------------------------------

    problem: str
    """
    The original problem being solved.

    This grounds all reasoning in the actual goal.
    """

    domain: str = "general"
    """
    The domain of the problem.

    Helps LLM apply domain-appropriate reasoning:
    - "code_generation": Think about correctness, tests, edge cases
    - "debugging": Think about hypotheses, reproduction, root causes
    - "research": Think about evidence, sources, synthesis
    - "planning": Think about feasibility, dependencies, risks
    - "design": Think about consistency, interfaces, simplicity
    """

    # -------------------------------------------------------------------------
    # CURRENT STATE
    # -------------------------------------------------------------------------

    current_depth: int = 0
    """Current search depth (0 = at root)."""

    best_score: float = 0.0
    """Best score achieved so far."""

    score_history: list[float] = field(default_factory=list)
    """Best score at each depth level."""

    thoughts_explored: int = 0
    """Total number of thoughts expanded."""

    # -------------------------------------------------------------------------
    # CURRENT BEST
    # -------------------------------------------------------------------------

    current_best_thought: str = ""
    """Content of the current best thought."""

    path_to_best: list[str] = field(default_factory=list)
    """Reasoning path from root to best thought."""

    # -------------------------------------------------------------------------
    # CONSTRAINTS
    # -------------------------------------------------------------------------

    budget_total: int = 0
    """Total budget allocated."""

    budget_consumed: int = 0
    """Budget consumed so far."""

    budget_remaining: int = 0
    """Budget remaining."""

    depth_soft_limit: int = 10
    """Soft depth limit (can be extended)."""

    depth_hard_limit: int = 20
    """Hard depth limit (cannot exceed)."""

    # -------------------------------------------------------------------------
    # GOALS
    # -------------------------------------------------------------------------

    acceptable_threshold: float = 0.70
    """Score threshold for "acceptable" solution."""

    goal_threshold: float = 0.95
    """Score threshold for "ideal" solution."""

    # -------------------------------------------------------------------------
    # ADDITIONAL CONTEXT
    # -------------------------------------------------------------------------

    recent_thoughts: list[str] = field(default_factory=list)
    """Recent thoughts generated (for pattern detection)."""

    grounding_results: list[dict[str, Any]] = field(default_factory=list)
    """Results of any grounding/verification attempts."""

    previous_decisions: list[dict[str, Any]] = field(default_factory=list)
    """Previous reasoning decisions (for consistency)."""

    extra: dict[str, Any] = field(default_factory=dict)
    """Any additional context needed."""

    def to_prompt_context(self) -> str:
        """
        Format context for inclusion in LLM prompt.

        Returns a human-readable summary of the current state.
        """
        lines = [
            "CURRENT SITUATION:",
            f"  Problem: {self.problem[:200]}{'...' if len(self.problem) > 200 else ''}",
            f"  Domain: {self.domain}",
            "",
            "PROGRESS:",
            f"  Depth: {self.current_depth} (soft limit: {self.depth_soft_limit}, hard: {self.depth_hard_limit})",
            f"  Best score: {self.best_score:.1%} (acceptable: {self.acceptable_threshold:.1%}, goal: {self.goal_threshold:.1%})",
            f"  Thoughts explored: {self.thoughts_explored}",
            f"  Score history: {[f'{s:.2f}' for s in self.score_history[-10:]]}",  # Last 10
            "",
            "BUDGET:",
            f"  Total: {self.budget_total}",
            f"  Consumed: {self.budget_consumed} ({self.budget_consumed/max(1,self.budget_total):.1%})",
            f"  Remaining: {self.budget_remaining}",
            "",
            "CURRENT BEST SOLUTION:",
            f"  {self.current_best_thought[:500]}{'...' if len(self.current_best_thought) > 500 else ''}",
        ]

        if self.path_to_best:
            lines.append("")
            lines.append("REASONING PATH:")
            for i, step in enumerate(self.path_to_best[-5:], 1):  # Last 5 steps
                lines.append(f"  {i}. {step[:100]}{'...' if len(step) > 100 else ''}")

        return "\n".join(lines)


# =============================================================================
# REASONING RESULT
# =============================================================================

@dataclass
class ReasoningResult:
    """
    Result of LLM reasoning.

    Contains the decision, the reasoning behind it, and metadata.
    """

    decision: str
    """
    The decision made.

    Format depends on the type of reasoning:
    - Depth: "CONTINUE" | "STOP" | "PIVOT"
    - Budget: "SUFFICIENT" | "REQUEST:5000" | "COMPROMISE" | "TERMINATE"
    - Failure: Description of anticipated failures
    - Compromise: "ACCEPT" | "REJECT"
    """

    reasoning: str
    """
    Explanation of why this decision was made.

    This is crucial - it lets us:
    - Understand the LLM's thinking
    - Debug unexpected decisions
    - Build trust in the system
    - Learn patterns for improvement
    """

    confidence: float = 0.5
    """
    LLM's confidence in the decision (0.0 to 1.0).

    Low confidence might trigger:
    - Requesting human input
    - Trying multiple approaches
    - More conservative actions
    """

    concerns: list[str] = field(default_factory=list)
    """
    Any concerns or caveats about the decision.

    The LLM might say "I'm recommending CONTINUE but..."
    """

    suggested_actions: list[str] = field(default_factory=list)
    """
    Specific actions the LLM suggests.

    More detailed than the decision itself.
    """

    raw_response: str = ""
    """
    Raw LLM response before parsing.

    Kept for debugging and analysis.
    """

    def __str__(self) -> str:
        return (
            f"ReasoningResult:\n"
            f"  Decision: {self.decision}\n"
            f"  Confidence: {self.confidence:.1%}\n"
            f"  Reasoning: {self.reasoning[:200]}..."
        )


# =============================================================================
# REASONER PROTOCOL
# =============================================================================

class Reasoner(Protocol):
    """
    Protocol for LLM-based reasoning.

    All decision points implement this protocol, allowing the LLM
    to reason about the situation and make decisions.
    """

    async def reason(
        self,
        question: str,
        context: ReasoningContext,
    ) -> ReasoningResult:
        """
        Ask the LLM to reason about a decision.

        Args:
            question: The specific question to answer
            context: Complete context for reasoning

        Returns:
            ReasoningResult with decision, reasoning, and confidence
        """
        ...


# =============================================================================
# LLM REASONER BASE CLASS
# =============================================================================

class LLMReasoner(ABC):
    """
    Base class for LLM-based reasoners.

    Provides common functionality for all reasoning types.
    Subclasses implement domain-specific prompts and parsing.

    Attributes:
        llm: The LLM to use for reasoning
        system_prompt: Base system prompt for this reasoner
    """

    def __init__(
        self,
        llm: Any,  # LLM interface - generate(prompt) -> response
        system_prompt: str = "",
    ):
        """
        Initialize reasoner with LLM.

        Args:
            llm: LLM that implements generate(prompt) -> response
            system_prompt: System prompt for this reasoner type
        """
        self.llm = llm
        self.system_prompt = system_prompt

    async def reason(
        self,
        question: str,
        context: ReasoningContext,
    ) -> ReasoningResult:
        """
        Reason about a decision using the LLM.

        Template method that:
        1. Builds the prompt
        2. Calls the LLM
        3. Parses the response
        """
        # Build prompt
        prompt = self._build_prompt(question, context)

        # Call LLM
        response = await self._call_llm(prompt)

        # Parse response
        result = self._parse_response(response, context)

        return result

    @abstractmethod
    def _build_prompt(self, question: str, context: ReasoningContext) -> str:
        """Build the full prompt for the LLM."""
        ...

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM and get response."""
        # Subclasses can override for different LLM interfaces
        if hasattr(self.llm, 'generate'):
            return await self.llm.generate(prompt)
        elif callable(self.llm):
            return await self.llm(prompt)
        else:
            raise ValueError("LLM must have generate() method or be callable")

    @abstractmethod
    def _parse_response(self, response: str, context: ReasoningContext) -> ReasoningResult:
        """Parse LLM response into ReasoningResult."""
        ...


# =============================================================================
# DEPTH REASONER
# =============================================================================

class DepthReasoner(LLMReasoner):
    """
    Reasons about search depth decisions.

    Asked: "Should we continue deeper?"
    Considers: Progress rate, proximity to goal, resource constraints
    Decides: CONTINUE | STOP | PIVOT
    """

    DEFAULT_SYSTEM_PROMPT = """You are a reasoning system that decides whether to continue searching deeper in a problem-solving process.

Your job is to analyze the current search state and decide:
- CONTINUE: Keep exploring deeper on the current path
- STOP: We've found good enough or can't do better, stop here
- PIVOT: Current direction isn't working, try a different approach

Consider:
1. Is meaningful progress still being made?
2. Are we close enough to the goal to stop?
3. Is the current direction promising based on the content?
4. Are we wasting resources on a dead end?
5. Would a different approach be more fruitful?

Be decisive but explain your reasoning clearly."""

    def __init__(self, llm: Any):
        super().__init__(llm, self.DEFAULT_SYSTEM_PROMPT)

    def _build_prompt(self, question: str, context: ReasoningContext) -> str:
        return f"""{self.system_prompt}

{context.to_prompt_context()}

QUESTION: {question}

Respond in this exact format:
DECISION: [CONTINUE or STOP or PIVOT]
REASONING: [Your explanation - be specific about why]
CONFIDENCE: [0.0 to 1.0]
CONCERNS: [Any concerns, or "None"]
SUGGESTED_ACTIONS: [Specific suggestions, or "None"]
"""

    def _parse_response(self, response: str, context: ReasoningContext) -> ReasoningResult:
        """Parse depth reasoning response."""
        lines = response.strip().split('\n')

        decision = "CONTINUE"  # Default
        reasoning = ""
        confidence = 0.5
        concerns = []
        actions = []

        for line in lines:
            line = line.strip()
            if line.startswith("DECISION:"):
                decision = line.replace("DECISION:", "").strip().upper()
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.replace("CONFIDENCE:", "").strip())
                except ValueError:
                    confidence = 0.5
            elif line.startswith("CONCERNS:"):
                concern = line.replace("CONCERNS:", "").strip()
                if concern.lower() != "none":
                    concerns.append(concern)
            elif line.startswith("SUGGESTED_ACTIONS:"):
                action = line.replace("SUGGESTED_ACTIONS:", "").strip()
                if action.lower() != "none":
                    actions.append(action)

        return ReasoningResult(
            decision=decision,
            reasoning=reasoning,
            confidence=confidence,
            concerns=concerns,
            suggested_actions=actions,
            raw_response=response,
        )


# =============================================================================
# BUDGET REASONER
# =============================================================================

class BudgetReasoner(LLMReasoner):
    """
    Reasons about budget and resource decisions.

    Asked: "Is more budget justified? What should we do?"
    Considers: Progress so far, proximity to goal, cost-benefit
    Decides: SUFFICIENT | REQUEST:<amount> | COMPROMISE | TERMINATE
    """

    DEFAULT_SYSTEM_PROMPT = """You are a reasoning system that decides about resource allocation in a problem-solving process.

Your job is to analyze budget situation and decide:
- SUFFICIENT: Current budget is enough, continue
- REQUEST:<amount>: Request specific additional budget with justification
- COMPROMISE: Accept current best as good enough given constraints
- TERMINATE: Cannot continue meaningfully, stop

Consider:
1. How close are we to an acceptable solution?
2. Is additional budget likely to help based on progress so far?
3. What's the cost-benefit of more resources?
4. Is a partial solution valuable enough to accept?
5. Would more budget actually change the outcome?

Be economical but don't starve promising searches."""

    def __init__(self, llm: Any):
        super().__init__(llm, self.DEFAULT_SYSTEM_PROMPT)

    def _build_prompt(self, question: str, context: ReasoningContext) -> str:
        return f"""{self.system_prompt}

{context.to_prompt_context()}

QUESTION: {question}

Respond in this exact format:
DECISION: [SUFFICIENT or REQUEST:<amount> or COMPROMISE or TERMINATE]
REASONING: [Your explanation - be specific about cost-benefit]
CONFIDENCE: [0.0 to 1.0]
CONCERNS: [Any concerns, or "None"]
IF_REQUESTING: [What you expect additional budget to achieve, or "N/A"]
IF_COMPROMISING: [What tradeoffs you're accepting, or "N/A"]
"""

    def _parse_response(self, response: str, context: ReasoningContext) -> ReasoningResult:
        """Parse budget reasoning response."""
        lines = response.strip().split('\n')

        decision = "SUFFICIENT"
        reasoning = ""
        confidence = 0.5
        concerns = []
        actions = []

        for line in lines:
            line = line.strip()
            if line.startswith("DECISION:"):
                decision = line.replace("DECISION:", "").strip().upper()
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.replace("CONFIDENCE:", "").strip())
                except ValueError:
                    confidence = 0.5
            elif line.startswith("CONCERNS:"):
                concern = line.replace("CONCERNS:", "").strip()
                if concern.lower() not in ("none", "n/a"):
                    concerns.append(concern)
            elif line.startswith("IF_REQUESTING:"):
                expectation = line.replace("IF_REQUESTING:", "").strip()
                if expectation.lower() not in ("none", "n/a"):
                    actions.append(f"Expected outcome: {expectation}")
            elif line.startswith("IF_COMPROMISING:"):
                tradeoffs = line.replace("IF_COMPROMISING:", "").strip()
                if tradeoffs.lower() not in ("none", "n/a"):
                    actions.append(f"Accepting tradeoffs: {tradeoffs}")

        return ReasoningResult(
            decision=decision,
            reasoning=reasoning,
            confidence=confidence,
            concerns=concerns,
            suggested_actions=actions,
            raw_response=response,
        )


# =============================================================================
# FAILURE REASONER
# =============================================================================

class FailureReasoner(LLMReasoner):
    """
    Reasons about potential failures and risks.

    Asked: "What could go wrong? What are the warning signs?"
    Considers: Current trajectory, patterns, resource state
    Returns: Anticipated failures with prevention/mitigation
    """

    DEFAULT_SYSTEM_PROMPT = """You are a reasoning system that anticipates problems in a problem-solving process.

Your job is to:
1. Identify what could go wrong
2. Assess likelihood of each problem
3. Suggest prevention strategies
4. Suggest mitigation if prevention fails

Look for warning signs like:
- Declining progress rates
- Repetitive or circular thinking
- Resource depletion trajectories
- Quality plateau patterns
- Mismatch between approach and problem

Be vigilant but not alarmist. Focus on actionable concerns."""

    def __init__(self, llm: Any):
        super().__init__(llm, self.DEFAULT_SYSTEM_PROMPT)

    def _build_prompt(self, question: str, context: ReasoningContext) -> str:
        return f"""{self.system_prompt}

{context.to_prompt_context()}

QUESTION: {question}

Respond in this exact format:
ANTICIPATED_FAILURES:
1. [Failure mode]: [Likelihood 0.0-1.0]
   - Warning signs: [What you're seeing]
   - Prevention: [How to prevent]
   - Mitigation: [What to do if it happens]
2. [Next failure mode if any]
   ...

OVERALL_ASSESSMENT: [Brief summary of risk level]
RECOMMENDED_ACTION: [Most important thing to do now]
"""

    def _parse_response(self, response: str, context: ReasoningContext) -> ReasoningResult:
        """Parse failure reasoning response."""
        # For failure reasoning, the "decision" is the overall assessment
        # and the detailed failures go in suggested_actions

        lines = response.strip().split('\n')

        decision = "LOW_RISK"  # Default
        reasoning = response  # Keep full response as reasoning
        confidence = 0.5
        concerns = []
        actions = []

        in_failures = False
        current_failure = []

        for line in lines:
            line = line.strip()
            if "ANTICIPATED_FAILURES:" in line:
                in_failures = True
                continue
            elif line.startswith("OVERALL_ASSESSMENT:"):
                in_failures = False
                decision = line.replace("OVERALL_ASSESSMENT:", "").strip()
            elif line.startswith("RECOMMENDED_ACTION:"):
                action = line.replace("RECOMMENDED_ACTION:", "").strip()
                actions.append(action)
            elif in_failures and line:
                if line[0].isdigit() and current_failure:
                    # New failure, save previous
                    concerns.append(" ".join(current_failure))
                    current_failure = [line]
                else:
                    current_failure.append(line)

        if current_failure:
            concerns.append(" ".join(current_failure))

        return ReasoningResult(
            decision=decision,
            reasoning=reasoning,
            confidence=confidence,
            concerns=concerns,
            suggested_actions=actions,
            raw_response=response,
        )


# =============================================================================
# COMPROMISE REASONER
# =============================================================================

class CompromiseReasoner(LLMReasoner):
    """
    Reasons about whether to accept a compromise solution.

    Asked: "Is this solution acceptable? What are we sacrificing?"
    Considers: Solution quality, goal requirements, tradeoffs
    Decides: ACCEPT | REJECT with explanation
    """

    DEFAULT_SYSTEM_PROMPT = """You are a reasoning system that evaluates compromise solutions.

Your job is to decide if a partial solution is acceptable given constraints.

Consider:
1. How close is this to what was actually needed?
2. What specific gaps or issues remain?
3. Is this usable as-is, or does it need work?
4. What would we gain by continuing vs accepting now?
5. Are the tradeoffs acceptable for this use case?

Be pragmatic. Perfect is the enemy of good, but don't accept garbage either."""

    def __init__(self, llm: Any):
        super().__init__(llm, self.DEFAULT_SYSTEM_PROMPT)

    def _build_prompt(self, question: str, context: ReasoningContext) -> str:
        return f"""{self.system_prompt}

{context.to_prompt_context()}

QUESTION: {question}

Evaluate this solution and decide whether to accept it.

Respond in this exact format:
DECISION: [ACCEPT or REJECT]
QUALITY_ASSESSMENT: [How good is this solution, really?]
GAPS: [What's missing or incomplete]
TRADEOFFS: [What you're giving up by accepting this]
IF_ACCEPT: [How to make the most of this partial solution]
IF_REJECT: [What would need to change to accept]
CONFIDENCE: [0.0 to 1.0]
"""

    def _parse_response(self, response: str, context: ReasoningContext) -> ReasoningResult:
        """Parse compromise reasoning response."""
        lines = response.strip().split('\n')

        decision = "REJECT"  # Default to caution
        reasoning = ""
        confidence = 0.5
        concerns = []
        actions = []

        for line in lines:
            line = line.strip()
            if line.startswith("DECISION:"):
                decision = line.replace("DECISION:", "").strip().upper()
            elif line.startswith("QUALITY_ASSESSMENT:"):
                reasoning = line.replace("QUALITY_ASSESSMENT:", "").strip()
            elif line.startswith("GAPS:"):
                gap = line.replace("GAPS:", "").strip()
                if gap.lower() != "none":
                    concerns.append(f"Gap: {gap}")
            elif line.startswith("TRADEOFFS:"):
                tradeoff = line.replace("TRADEOFFS:", "").strip()
                if tradeoff.lower() != "none":
                    concerns.append(f"Tradeoff: {tradeoff}")
            elif line.startswith("IF_ACCEPT:") or line.startswith("IF_REJECT:"):
                action = line.split(":", 1)[1].strip()
                if action.lower() != "none":
                    actions.append(action)
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.replace("CONFIDENCE:", "").strip())
                except ValueError:
                    confidence = 0.5

        return ReasoningResult(
            decision=decision,
            reasoning=reasoning,
            confidence=confidence,
            concerns=concerns,
            suggested_actions=actions,
            raw_response=response,
        )


# =============================================================================
# META REASONER
# =============================================================================

class MetaReasoner(LLMReasoner):
    """
    Reasons about the overall search process.

    The "executive function" that:
    - Monitors overall progress
    - Coordinates between concerns
    - Decides on strategy adjustments
    - Can override other decisions

    Asked: "How is the search going? What should we do differently?"
    """

    DEFAULT_SYSTEM_PROMPT = """You are the meta-reasoning system overseeing a problem-solving search process.

Your job is to:
1. Assess overall search health
2. Identify strategic issues
3. Recommend adjustments
4. Coordinate between depth/budget/quality concerns

You see the big picture. Other reasoners focus on specific aspects.
You decide if the overall strategy is working.

Consider:
1. Is the search converging or diverging?
2. Are we in a productive region of the solution space?
3. Should we fundamentally change approach?
4. Are we balancing exploration vs exploitation well?
5. What's the most important thing to address now?"""

    def __init__(self, llm: Any):
        super().__init__(llm, self.DEFAULT_SYSTEM_PROMPT)

    def _build_prompt(self, question: str, context: ReasoningContext) -> str:
        return f"""{self.system_prompt}

{context.to_prompt_context()}

PREVIOUS DECISIONS:
{self._format_previous_decisions(context.previous_decisions)}

QUESTION: {question}

Respond in this exact format:
OVERALL_ASSESSMENT: [How is the search going overall?]
STRATEGIC_ISSUES: [What strategic problems do you see?]
RECOMMENDED_STRATEGY: [What should we do differently?]
PRIORITY_ACTION: [Single most important thing to do now]
CONFIDENCE: [0.0 to 1.0]
"""

    def _format_previous_decisions(self, decisions: list[dict]) -> str:
        if not decisions:
            return "No previous decisions recorded."

        lines = []
        for d in decisions[-5:]:  # Last 5 decisions
            lines.append(f"- {d.get('type', 'unknown')}: {d.get('decision', 'unknown')}")
        return "\n".join(lines)

    def _parse_response(self, response: str, context: ReasoningContext) -> ReasoningResult:
        """Parse meta reasoning response."""
        lines = response.strip().split('\n')

        decision = ""
        reasoning = ""
        confidence = 0.5
        concerns = []
        actions = []

        for line in lines:
            line = line.strip()
            if line.startswith("OVERALL_ASSESSMENT:"):
                reasoning = line.replace("OVERALL_ASSESSMENT:", "").strip()
            elif line.startswith("STRATEGIC_ISSUES:"):
                issue = line.replace("STRATEGIC_ISSUES:", "").strip()
                if issue.lower() != "none":
                    concerns.append(issue)
            elif line.startswith("RECOMMENDED_STRATEGY:"):
                decision = line.replace("RECOMMENDED_STRATEGY:", "").strip()
            elif line.startswith("PRIORITY_ACTION:"):
                action = line.replace("PRIORITY_ACTION:", "").strip()
                actions.append(action)
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.replace("CONFIDENCE:", "").strip())
                except ValueError:
                    confidence = 0.5

        return ReasoningResult(
            decision=decision,
            reasoning=reasoning,
            confidence=confidence,
            concerns=concerns,
            suggested_actions=actions,
            raw_response=response,
        )


# =============================================================================
# PATH REASONER
# =============================================================================

class PathReasoner(LLMReasoner):
    """
    Reasons about which paths to pursue.

    Asked: "Which thoughts are most promising? Why?"
    Considers: Content quality, diversity, alignment with goal
    Returns: Ranked paths with reasoning
    """

    DEFAULT_SYSTEM_PROMPT = """You are a reasoning system that evaluates and ranks solution paths.

Your job is to:
1. Assess which paths are most promising
2. Explain why certain paths are better
3. Identify paths that should be abandoned
4. Ensure diversity in exploration

Consider:
1. Which paths are making real progress toward the goal?
2. Which paths are stuck or circular?
3. Are we exploring diverse enough approaches?
4. Which paths have the best content quality?
5. Which paths align best with the actual problem?

Be selective. Resources are limited. Focus on what's working."""

    def __init__(self, llm: Any):
        super().__init__(llm, self.DEFAULT_SYSTEM_PROMPT)

    def _build_prompt(self, question: str, context: ReasoningContext) -> str:
        # Format recent thoughts for evaluation
        thoughts_text = "\n".join([
            f"  {i+1}. {t[:200]}..." if len(t) > 200 else f"  {i+1}. {t}"
            for i, t in enumerate(context.recent_thoughts[:10])
        ])

        return f"""{self.system_prompt}

PROBLEM: {context.problem}

RECENT THOUGHTS TO EVALUATE:
{thoughts_text}

CURRENT BEST: {context.current_best_thought[:300]}...

QUESTION: {question}

Respond in this exact format:
RANKING: [List numbers in order of promise, e.g., "3, 1, 5, 2, 4"]
REASONING: [Why this ranking]
ABANDON: [Which numbers to abandon, or "None"]
MISSING: [What approaches are we NOT exploring that we should?]
"""

    def _parse_response(self, response: str, context: ReasoningContext) -> ReasoningResult:
        """Parse path reasoning response."""
        lines = response.strip().split('\n')

        decision = ""  # The ranking
        reasoning = ""
        concerns = []
        actions = []

        for line in lines:
            line = line.strip()
            if line.startswith("RANKING:"):
                decision = line.replace("RANKING:", "").strip()
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("ABANDON:"):
                abandon = line.replace("ABANDON:", "").strip()
                if abandon.lower() != "none":
                    concerns.append(f"Abandon: {abandon}")
            elif line.startswith("MISSING:"):
                missing = line.replace("MISSING:", "").strip()
                if missing.lower() != "none":
                    actions.append(f"Missing approach: {missing}")

        return ReasoningResult(
            decision=decision,
            reasoning=reasoning,
            confidence=0.7,  # Path ranking is inherently uncertain
            concerns=concerns,
            suggested_actions=actions,
            raw_response=response,
        )
