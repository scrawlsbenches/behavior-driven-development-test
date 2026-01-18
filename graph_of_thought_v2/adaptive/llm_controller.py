"""
LLM-Driven Search Controller - Reasoning at Every Decision Point
=================================================================

This controller puts LLMs in charge of all key decisions. Instead of
hardcoded thresholds and rules, the LLM reasons about each situation.

THE CORE PRINCIPLE
------------------

We cannot predetermine the right decisions. We must REASON through them.

    OLD WAY (controller.py):
        if progress_rate < 0.05:  # Hardcoded threshold
            decision = STOP

    NEW WAY (this file):
        decision = await depth_reasoner.reason(
            "Should we continue?",
            context=full_situation
        )
        # LLM decides based on actual context


WHERE LLMs DECIDE
-----------------

Every intersection point where a decision is needed:

    ┌─────────────────────────────────────────────────────────────────────┐
    │                     SEARCH LOOP WITH LLM REASONING                  │
    │                                                                     │
    │  while not done:                                                    │
    │                                                                     │
    │    ┌─────────────────────────────────────────────────────────────┐  │
    │    │ META-REASONING: "How is the search going overall?"          │  │
    │    │ LLM assesses overall health and strategic direction         │  │
    │    └─────────────────────────────────────────────────────────────┘  │
    │                              │                                      │
    │    ┌─────────────────────────────────────────────────────────────┐  │
    │    │ FAILURE-REASONING: "What could go wrong?"                   │  │
    │    │ LLM anticipates problems before they occur                  │  │
    │    └─────────────────────────────────────────────────────────────┘  │
    │                              │                                      │
    │    ┌─────────────────────────────────────────────────────────────┐  │
    │    │ BUDGET-REASONING: "Do we have enough resources?"            │  │
    │    │ LLM decides if more budget needed or compromise             │  │
    │    └─────────────────────────────────────────────────────────────┘  │
    │                              │                                      │
    │    ┌─────────────────────────────────────────────────────────────┐  │
    │    │ DEPTH-REASONING: "Should we continue deeper?"               │  │
    │    │ LLM decides if current direction is working                 │  │
    │    └─────────────────────────────────────────────────────────────┘  │
    │                              │                                      │
    │    ┌─────────────────────────────────────────────────────────────┐  │
    │    │ EXPAND: Generate new thoughts (existing LLM generation)     │  │
    │    └─────────────────────────────────────────────────────────────┘  │
    │                              │                                      │
    │    ┌─────────────────────────────────────────────────────────────┐  │
    │    │ EVALUATE: Score thoughts (existing LLM evaluation)          │  │
    │    └─────────────────────────────────────────────────────────────┘  │
    │                              │                                      │
    │    ┌─────────────────────────────────────────────────────────────┐  │
    │    │ PATH-REASONING: "Which paths are most promising?"           │  │
    │    │ LLM decides beam selection, not just scores                 │  │
    │    └─────────────────────────────────────────────────────────────┘  │
    │                              │                                      │
    │    ┌─────────────────────────────────────────────────────────────┐  │
    │    │ COMPROMISE-REASONING: "Is current best good enough?"        │  │
    │    │ LLM decides if we should accept or continue                 │  │
    │    └─────────────────────────────────────────────────────────────┘  │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘


THE REASONING HIERARCHY
-----------------------

    MetaReasoner (strategic oversight)
         │
         ├── FailureReasoner (risk assessment)
         ├── BudgetReasoner (resource allocation)
         ├── DepthReasoner (direction decisions)
         ├── PathReasoner (beam selection)
         └── CompromiseReasoner (acceptance decisions)

The MetaReasoner can override any other decision if the overall
strategy requires it.


COST CONSIDERATIONS
-------------------

Each reasoning call uses tokens. We manage this by:

1. REASONING_BUDGET: Separate budget for meta-reasoning
   - Reasoning is critical, shouldn't compete with generation
   - Typically 10-20% of total budget

2. REASONING_MODEL: Can use different model
   - Fast/cheap model for routine decisions
   - Better model for critical decisions

3. REASONING_FREQUENCY: Not every iteration
   - Simple heuristics for obvious cases
   - LLM reasoning for uncertain cases

4. CONTEXT_COMPRESSION: Don't send everything
   - Summarize history rather than full transcripts
   - Focus on relevant recent context


USAGE
-----

    from graph_of_thought_v2.adaptive.llm_controller import LLMDrivenController
    from graph_of_thought_v2.adaptive.reasoning import (
        DepthReasoner,
        BudgetReasoner,
        FailureReasoner,
        CompromiseReasoner,
        MetaReasoner,
        PathReasoner,
    )

    # Create reasoners with LLM
    reasoning_llm = MyLLM(model="fast-model")

    controller = LLMDrivenController(
        graph=my_graph,
        expander=my_generator,
        evaluator=my_evaluator,

        # The LLM reasoners
        depth_reasoner=DepthReasoner(reasoning_llm),
        budget_reasoner=BudgetReasoner(reasoning_llm),
        failure_reasoner=FailureReasoner(reasoning_llm),
        compromise_reasoner=CompromiseReasoner(reasoning_llm),
        meta_reasoner=MetaReasoner(reasoning_llm),
        path_reasoner=PathReasoner(reasoning_llm),

        # Config
        config=SearchConfig(...),
    )

    result = await controller.search(budget)

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar
import logging

from graph_of_thought_v2.adaptive.reasoning import (
    ReasoningContext,
    ReasoningResult,
    DepthReasoner,
    BudgetReasoner,
    FailureReasoner,
    CompromiseReasoner,
    MetaReasoner,
    PathReasoner,
)

T = TypeVar("T")
logger = logging.getLogger(__name__)


# =============================================================================
# SEARCH CONFIG
# =============================================================================

@dataclass
class SearchConfig:
    """Configuration for search."""
    max_depth: int = 15
    beam_width: int = 3
    goal_score: float = 0.95
    acceptable_score: float = 0.70
    max_expansions: int = 100

    # Reasoning configuration
    reasoning_frequency: int = 1  # Reason every N iterations (1 = always)
    require_reasoning_for_stop: bool = True  # Always reason before stopping


# =============================================================================
# SEARCH RESULT
# =============================================================================

@dataclass
class LLMSearchResult(Generic[T]):
    """
    Result of LLM-driven search.

    Includes full reasoning history for transparency.
    """

    best_path: list[Any]
    best_score: float
    completed: bool
    goal_reached: bool = False
    termination_reason: str = ""

    # The reasoning that led to this result
    reasoning_history: list[ReasoningResult] = field(default_factory=list)

    # Compromise if accepted
    compromise_accepted: bool = False
    compromise_reasoning: ReasoningResult | None = None

    # Statistics
    thoughts_expanded: int = 0
    max_depth_reached: int = 0
    reasoning_calls: int = 0

    def explain_termination(self) -> str:
        """Explain why the search terminated."""
        if self.goal_reached:
            return f"Goal reached with score {self.best_score:.1%}"

        if self.compromise_accepted and self.compromise_reasoning:
            return (
                f"Accepted compromise at score {self.best_score:.1%}.\n"
                f"Reasoning: {self.compromise_reasoning.reasoning}"
            )

        if self.reasoning_history:
            last = self.reasoning_history[-1]
            return (
                f"Terminated: {self.termination_reason}\n"
                f"Final reasoning: {last.reasoning}"
            )

        return self.termination_reason


# =============================================================================
# LLM-DRIVEN CONTROLLER
# =============================================================================

@dataclass
class LLMDrivenController(Generic[T]):
    """
    Search controller where LLMs make all key decisions.

    Instead of hardcoded rules, this controller asks LLM reasoners
    at every decision point.

    Attributes:
        graph: The thought graph to search
        expander: Generates child thoughts
        evaluator: Scores thoughts

        depth_reasoner: Decides about search depth
        budget_reasoner: Decides about resources
        failure_reasoner: Anticipates problems
        compromise_reasoner: Evaluates partial solutions
        meta_reasoner: Overall strategic oversight
        path_reasoner: Selects promising paths

        config: Search configuration
    """

    # Core components
    graph: Any  # Graph[T]
    expander: Any  # Generates children
    evaluator: Any  # Scores thoughts

    # LLM Reasoners - THE CORE DECISION MAKERS
    depth_reasoner: DepthReasoner
    budget_reasoner: BudgetReasoner
    failure_reasoner: FailureReasoner
    compromise_reasoner: CompromiseReasoner
    meta_reasoner: MetaReasoner
    path_reasoner: PathReasoner

    # Configuration
    config: SearchConfig = field(default_factory=SearchConfig)

    # Optional grounding
    grounder: Any | None = None

    async def search(
        self,
        budget: Any,
        problem: str = "",
        domain: str = "general",
    ) -> LLMSearchResult[T]:
        """
        Execute search with LLM reasoning at every decision point.

        Args:
            budget: Budget for the search
            problem: The problem being solved (for context)
            domain: Domain hint for reasoning

        Returns:
            LLMSearchResult with full reasoning history
        """
        # Initialize state
        score_history: list[float] = []
        reasoning_history: list[ReasoningResult] = []
        previous_decisions: list[dict] = []
        current_depth = 0
        thoughts_expanded = 0
        beam = list(self.graph.roots())

        # Score initial beam
        for thought in beam:
            if thought.score == 0:
                thought.score = await self._evaluate(thought)

        if beam:
            score_history.append(max(t.score for t in beam))

        # Build initial context
        context = self._build_context(
            problem=problem,
            domain=domain,
            current_depth=current_depth,
            score_history=score_history,
            beam=beam,
            budget=budget,
            previous_decisions=previous_decisions,
        )

        # Main loop
        iteration = 0
        while True:
            iteration += 1
            should_reason = (iteration % self.config.reasoning_frequency == 0)

            # =================================================================
            # META-REASONING: Overall assessment
            # =================================================================
            if should_reason:
                meta_result = await self.meta_reasoner.reason(
                    "How is the search going? Should we change strategy?",
                    context,
                )
                reasoning_history.append(meta_result)
                previous_decisions.append({
                    "type": "meta",
                    "decision": meta_result.decision,
                    "iteration": iteration,
                })

                logger.info(f"Meta reasoning: {meta_result.decision}")

                # Meta can trigger immediate termination
                if "STOP" in meta_result.decision.upper() or "TERMINATE" in meta_result.decision.upper():
                    return self._build_result(
                        completed=True,
                        reason=f"Meta-reasoner decided to stop: {meta_result.reasoning}",
                        score_history=score_history,
                        reasoning_history=reasoning_history,
                        thoughts_expanded=thoughts_expanded,
                    )

            # =================================================================
            # FAILURE-REASONING: What could go wrong?
            # =================================================================
            if should_reason:
                failure_result = await self.failure_reasoner.reason(
                    "What problems do you anticipate? What should we watch for?",
                    context,
                )
                reasoning_history.append(failure_result)

                logger.info(f"Failure anticipation: {len(failure_result.concerns)} concerns")

                # If high-risk failure anticipated, let meta-reasoner decide
                if failure_result.confidence > 0.8 and failure_result.concerns:
                    meta_override = await self.meta_reasoner.reason(
                        f"Failure reasoner has high-confidence concerns: {failure_result.concerns}. "
                        f"Should we abort, mitigate, or continue?",
                        context,
                    )
                    reasoning_history.append(meta_override)

                    if "ABORT" in meta_override.decision.upper():
                        return self._build_result(
                            completed=False,
                            reason=f"Aborted due to anticipated failure: {failure_result.concerns[0]}",
                            score_history=score_history,
                            reasoning_history=reasoning_history,
                            thoughts_expanded=thoughts_expanded,
                        )

            # =================================================================
            # BUDGET-REASONING: Do we have resources?
            # =================================================================
            if should_reason:
                budget_result = await self.budget_reasoner.reason(
                    "Do we have enough budget to continue? If not, what should we do?",
                    context,
                )
                reasoning_history.append(budget_result)
                previous_decisions.append({
                    "type": "budget",
                    "decision": budget_result.decision,
                    "iteration": iteration,
                })

                logger.info(f"Budget reasoning: {budget_result.decision}")

                if budget_result.decision.upper().startswith("REQUEST:"):
                    # Extract amount and handle request
                    # In real implementation, this would go to feedback handler
                    logger.warning(f"Budget increase requested: {budget_result.decision}")

                elif "COMPROMISE" in budget_result.decision.upper():
                    # Evaluate compromise
                    compromise_result = await self._evaluate_compromise(context, reasoning_history)
                    if compromise_result:
                        return compromise_result

                elif "TERMINATE" in budget_result.decision.upper():
                    return self._build_result(
                        completed=False,
                        reason=f"Budget reasoning terminated: {budget_result.reasoning}",
                        score_history=score_history,
                        reasoning_history=reasoning_history,
                        thoughts_expanded=thoughts_expanded,
                    )

            # =================================================================
            # DEPTH-REASONING: Should we go deeper?
            # =================================================================
            if should_reason:
                depth_result = await self.depth_reasoner.reason(
                    "Should we continue exploring deeper? Is the current direction working?",
                    context,
                )
                reasoning_history.append(depth_result)
                previous_decisions.append({
                    "type": "depth",
                    "decision": depth_result.decision,
                    "iteration": iteration,
                })

                logger.info(f"Depth reasoning: {depth_result.decision}")

                if depth_result.decision.upper() == "STOP":
                    return self._build_result(
                        completed=True,
                        reason=f"Depth reasoning decided to stop: {depth_result.reasoning}",
                        score_history=score_history,
                        reasoning_history=reasoning_history,
                        thoughts_expanded=thoughts_expanded,
                    )

                elif depth_result.decision.upper() == "PIVOT":
                    # LLM wants different direction - use path reasoning
                    logger.info("Pivoting based on depth reasoning")
                    # Continue but path reasoner will handle selection differently

            # =================================================================
            # EXPAND: Generate new thoughts
            # =================================================================
            new_thoughts = []
            for parent in beam:
                children_content = await self._expand(parent)
                thoughts_expanded += 1

                for content in children_content:
                    child = self._create_thought(content)
                    self.graph.add(child, parent=parent)
                    child.score = await self._evaluate(child)

                    # Optional grounding
                    if self.grounder and self.grounder.can_ground(child):
                        grounding = await self.grounder.ground(child, None)
                        if grounding.verified is False:
                            child.score *= 0.1

                    new_thoughts.append(child)

                    # Check for goal
                    if child.score >= self.config.goal_score:
                        return self._build_result(
                            completed=True,
                            goal_reached=True,
                            score_history=score_history + [child.score],
                            reasoning_history=reasoning_history,
                            thoughts_expanded=thoughts_expanded,
                        )

            if not new_thoughts:
                return self._build_result(
                    completed=True,
                    reason="No more thoughts generated",
                    score_history=score_history,
                    reasoning_history=reasoning_history,
                    thoughts_expanded=thoughts_expanded,
                )

            # =================================================================
            # PATH-REASONING: Which paths to pursue?
            # =================================================================
            if should_reason and len(new_thoughts) > self.config.beam_width:
                # Update context with new thoughts
                context = self._update_context(
                    context,
                    new_thoughts=[str(t.content)[:200] for t in new_thoughts],
                )

                path_result = await self.path_reasoner.reason(
                    "Which of these thoughts are most promising? "
                    "Which should we pursue and which should we abandon?",
                    context,
                )
                reasoning_history.append(path_result)

                logger.info(f"Path reasoning: {path_result.decision}")

                # Use LLM ranking if provided
                try:
                    ranking = self._parse_ranking(path_result.decision, len(new_thoughts))
                    if ranking:
                        # Reorder based on LLM preference
                        new_thoughts = [new_thoughts[i] for i in ranking if i < len(new_thoughts)]
                except Exception:
                    # Fall back to score-based ranking
                    pass

            # Score-based beam selection (default)
            new_thoughts.sort(key=lambda t: t.score, reverse=True)
            beam = new_thoughts[:self.config.beam_width]

            # Update history
            best_score = max(t.score for t in beam)
            score_history.append(best_score)
            current_depth += 1

            # Update context for next iteration
            context = self._build_context(
                problem=problem,
                domain=domain,
                current_depth=current_depth,
                score_history=score_history,
                beam=beam,
                budget=budget,
                previous_decisions=previous_decisions,
            )

            # Safety limits
            if thoughts_expanded >= self.config.max_expansions:
                # Let LLM reason about termination
                if self.config.require_reasoning_for_stop:
                    final_result = await self.meta_reasoner.reason(
                        f"We've reached the expansion limit ({self.config.max_expansions}). "
                        f"Best score is {best_score:.1%}. Should we stop or request more resources?",
                        context,
                    )
                    reasoning_history.append(final_result)

                return self._build_result(
                    completed=True,
                    reason="Expansion limit reached",
                    score_history=score_history,
                    reasoning_history=reasoning_history,
                    thoughts_expanded=thoughts_expanded,
                )

            if current_depth >= self.config.max_depth:
                if self.config.require_reasoning_for_stop:
                    final_result = await self.meta_reasoner.reason(
                        f"We've reached max depth ({self.config.max_depth}). "
                        f"Best score is {best_score:.1%}. Is this acceptable?",
                        context,
                    )
                    reasoning_history.append(final_result)

                return self._build_result(
                    completed=True,
                    reason="Depth limit reached",
                    score_history=score_history,
                    reasoning_history=reasoning_history,
                    thoughts_expanded=thoughts_expanded,
                )

    async def _evaluate_compromise(
        self,
        context: ReasoningContext,
        reasoning_history: list[ReasoningResult],
    ) -> LLMSearchResult | None:
        """Evaluate if current best should be accepted as compromise."""
        compromise_result = await self.compromise_reasoner.reason(
            "Should we accept the current best solution as a compromise? "
            "What are we giving up?",
            context,
        )
        reasoning_history.append(compromise_result)

        if compromise_result.decision.upper() == "ACCEPT":
            return self._build_result(
                completed=True,
                compromise_accepted=True,
                compromise_reasoning=compromise_result,
                reason=f"Accepted compromise: {compromise_result.reasoning}",
                score_history=context.score_history,
                reasoning_history=reasoning_history,
                thoughts_expanded=context.thoughts_explored,
            )

        return None  # Continue searching

    def _build_context(
        self,
        problem: str,
        domain: str,
        current_depth: int,
        score_history: list[float],
        beam: list[Any],
        budget: Any,
        previous_decisions: list[dict],
    ) -> ReasoningContext:
        """Build reasoning context from current state."""
        best_thought = max(beam, key=lambda t: t.score) if beam else None

        return ReasoningContext(
            problem=problem,
            domain=domain,
            current_depth=current_depth,
            best_score=best_thought.score if best_thought else 0.0,
            score_history=score_history,
            thoughts_explored=len(list(self.graph.all_thoughts())),
            current_best_thought=str(best_thought.content) if best_thought else "",
            path_to_best=[str(t.content) for t in self.graph.path_to_root(best_thought)[::-1]] if best_thought else [],
            budget_total=budget.total,
            budget_consumed=budget.consumed,
            budget_remaining=budget.remaining,
            depth_soft_limit=self.config.max_depth - 5,
            depth_hard_limit=self.config.max_depth,
            acceptable_threshold=self.config.acceptable_score,
            goal_threshold=self.config.goal_score,
            recent_thoughts=[str(t.content)[:200] for t in beam],
            previous_decisions=previous_decisions,
        )

    def _update_context(
        self,
        context: ReasoningContext,
        new_thoughts: list[str],
    ) -> ReasoningContext:
        """Update context with new thoughts."""
        # Create new context with updated recent_thoughts
        return ReasoningContext(
            problem=context.problem,
            domain=context.domain,
            current_depth=context.current_depth,
            best_score=context.best_score,
            score_history=context.score_history,
            thoughts_explored=context.thoughts_explored,
            current_best_thought=context.current_best_thought,
            path_to_best=context.path_to_best,
            budget_total=context.budget_total,
            budget_consumed=context.budget_consumed,
            budget_remaining=context.budget_remaining,
            depth_soft_limit=context.depth_soft_limit,
            depth_hard_limit=context.depth_hard_limit,
            acceptable_threshold=context.acceptable_threshold,
            goal_threshold=context.goal_threshold,
            recent_thoughts=new_thoughts,
            previous_decisions=context.previous_decisions,
        )

    def _build_result(
        self,
        completed: bool,
        goal_reached: bool = False,
        compromise_accepted: bool = False,
        compromise_reasoning: ReasoningResult | None = None,
        reason: str = "",
        score_history: list[float] | None = None,
        reasoning_history: list[ReasoningResult] | None = None,
        thoughts_expanded: int = 0,
    ) -> LLMSearchResult[T]:
        """Build search result."""
        all_thoughts = list(self.graph.all_thoughts())

        if not all_thoughts:
            return LLMSearchResult(
                best_path=[],
                best_score=0.0,
                completed=completed,
                goal_reached=goal_reached,
                termination_reason=reason,
                reasoning_history=reasoning_history or [],
                compromise_accepted=compromise_accepted,
                compromise_reasoning=compromise_reasoning,
                thoughts_expanded=thoughts_expanded,
                max_depth_reached=0,
                reasoning_calls=len(reasoning_history) if reasoning_history else 0,
            )

        best = max(all_thoughts, key=lambda t: t.score)
        best_path = self.graph.path_to_root(best)[::-1]
        max_depth = max(len(self.graph.path_to_root(t)) for t in all_thoughts) - 1

        return LLMSearchResult(
            best_path=best_path,
            best_score=best.score,
            completed=completed,
            goal_reached=goal_reached,
            termination_reason=reason,
            reasoning_history=reasoning_history or [],
            compromise_accepted=compromise_accepted,
            compromise_reasoning=compromise_reasoning,
            thoughts_expanded=thoughts_expanded,
            max_depth_reached=max_depth,
            reasoning_calls=len(reasoning_history) if reasoning_history else 0,
        )

    async def _expand(self, thought: Any) -> list[T]:
        """Expand a thought."""
        if hasattr(self.expander, 'generate'):
            return await self.expander.generate(thought, None)
        return await self.expander(thought, None)

    async def _evaluate(self, thought: Any) -> float:
        """Evaluate a thought."""
        if hasattr(self.evaluator, 'evaluate'):
            return await self.evaluator.evaluate(thought, None)
        return await self.evaluator(thought, None)

    def _create_thought(self, content: T) -> Any:
        """Create a new thought."""
        from graph_of_thought_v2.core import Thought
        return Thought(content=content)

    def _parse_ranking(self, decision: str, count: int) -> list[int] | None:
        """Parse ranking from LLM decision like '3, 1, 5, 2'."""
        try:
            parts = decision.replace(",", " ").split()
            indices = [int(p) - 1 for p in parts if p.isdigit()]  # Convert to 0-indexed
            return [i for i in indices if 0 <= i < count]
        except Exception:
            return None
