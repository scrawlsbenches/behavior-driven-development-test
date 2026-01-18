"""
Simple Implementations - For Getting Started
=============================================

These implementations provide basic functionality without external
dependencies. They're useful for:

1. LEARNING THE API
   Understand how search works without LLM complexity.

2. TESTING SEARCH LOGIC
   Verify search algorithms with predictable generation/evaluation.

3. PROTOTYPING
   Build the application structure before adding LLM integration.

4. OFFLINE DEVELOPMENT
   Work without API keys or network access.

LIMITATIONS
-----------

These implementations are NOT intelligent. They use simple heuristics:

- SimpleGenerator: Generates variations based on templates
- SimpleEvaluator: Scores based on content length and keywords

For real reasoning, use LLM-based implementations.

CUSTOMIZATION
-------------

You can extend these for domain-specific behavior:

    class MyGenerator(SimpleGenerator):
        def __init__(self, domain_templates: list[str]):
            super().__init__()
            self.templates = domain_templates

Or create entirely custom implementations - just satisfy the protocol.

"""

from typing import Any, TypeVar
import random

from graph_of_thought_v2.core import Thought

T = TypeVar("T")


# =============================================================================
# SIMPLE GENERATOR
# =============================================================================

class SimpleGenerator:
    """
    Basic generator using templates.

    Generates child thoughts by applying simple transformations to
    the parent content. Not intelligent, but deterministic and fast.

    Attributes:
        num_children: How many children to generate per expansion.
        templates: Transformation templates.

    Example:
        generator = SimpleGenerator(num_children=3)
        children = await generator.generate(thought, context)
        # Returns 3 variations of the thought content
    """

    # Default templates for generating variations
    DEFAULT_TEMPLATES = [
        "What if we {verb} {content}?",
        "Consider {content} from another angle",
        "Break down {content} into smaller parts",
        "What's the opposite of {content}?",
        "How does {content} relate to the goal?",
        "What assumptions are in {content}?",
        "Simplify: {content}",
        "Expand on: {content}",
    ]

    VERBS = ["explore", "question", "validate", "implement", "test", "refine"]

    def __init__(
        self,
        num_children: int = 3,
        templates: list[str] | None = None,
        seed: int | None = None,
    ) -> None:
        """
        Initialize the generator.

        Args:
            num_children: Number of children to generate (default 3).
            templates: Custom templates (default uses DEFAULT_TEMPLATES).
            seed: Random seed for reproducibility in tests.
        """
        self.num_children = num_children
        self.templates = templates or self.DEFAULT_TEMPLATES
        self._random = random.Random(seed)

    async def generate(
        self,
        thought: Thought[str],
        context: Any,
    ) -> list[str]:
        """
        Generate child content from a parent thought.

        For string content, applies templates to create variations.
        For non-string content, converts to string first.

        Args:
            thought: The thought to expand.
            context: Execution context (used for seeding if needed).

        Returns:
            List of child content strings.
        """
        content = str(thought.content)

        # Select templates and generate children
        selected = self._random.sample(
            self.templates,
            min(self.num_children, len(self.templates)),
        )

        children = []
        for template in selected:
            verb = self._random.choice(self.VERBS)
            child_content = template.format(
                content=content[:100],  # Truncate long content
                verb=verb,
            )
            children.append(child_content)

        return children

    # -------------------------------------------------------------------------
    # Configuration helpers
    # -------------------------------------------------------------------------

    def with_num_children(self, n: int) -> "SimpleGenerator":
        """Return a new generator with different num_children."""
        return SimpleGenerator(
            num_children=n,
            templates=self.templates,
        )


# =============================================================================
# SIMPLE EVALUATOR
# =============================================================================

class SimpleEvaluator:
    """
    Basic evaluator using heuristics.

    Scores thoughts based on simple rules:
    - Length (not too short, not too long)
    - Presence of positive/negative keywords
    - Specificity (numbers, concrete terms)

    This is NOT intelligent evaluation. For real scoring, use LLM.

    Attributes:
        positive_keywords: Words that increase score.
        negative_keywords: Words that decrease score.
        ideal_length: Target content length (chars).

    Example:
        evaluator = SimpleEvaluator()
        score = await evaluator.evaluate(thought, context)
        # Returns 0.0-1.0 based on heuristics
    """

    DEFAULT_POSITIVE = [
        "solution", "improve", "optimize", "efficient", "clear",
        "specific", "measurable", "actionable", "concrete", "test",
    ]

    DEFAULT_NEGATIVE = [
        "maybe", "perhaps", "unclear", "complex", "difficult",
        "impossible", "never", "always", "everything", "nothing",
    ]

    def __init__(
        self,
        positive_keywords: list[str] | None = None,
        negative_keywords: list[str] | None = None,
        ideal_length: int = 100,
    ) -> None:
        """
        Initialize the evaluator.

        Args:
            positive_keywords: Words that boost score.
            negative_keywords: Words that reduce score.
            ideal_length: Ideal content length in characters.
        """
        self.positive_keywords = positive_keywords or self.DEFAULT_POSITIVE
        self.negative_keywords = negative_keywords or self.DEFAULT_NEGATIVE
        self.ideal_length = ideal_length

    async def evaluate(
        self,
        thought: Thought[str],
        context: Any,
    ) -> float:
        """
        Score a thought based on heuristics.

        Scoring factors:
        1. Length score: How close to ideal length (0.0-0.3)
        2. Keyword score: Positive vs negative keywords (0.0-0.4)
        3. Specificity score: Numbers and concrete terms (0.0-0.3)

        Args:
            thought: The thought to evaluate.
            context: Execution context (unused in simple impl).

        Returns:
            Score from 0.0 to 1.0.
        """
        content = str(thought.content).lower()

        # 1. Length score (max 0.3)
        length = len(content)
        if length == 0:
            length_score = 0.0
        elif length < self.ideal_length / 2:
            length_score = length / self.ideal_length
        elif length > self.ideal_length * 3:
            length_score = 0.1  # Too long
        else:
            # Sweet spot
            deviation = abs(length - self.ideal_length) / self.ideal_length
            length_score = max(0, 0.3 - deviation * 0.2)

        # 2. Keyword score (max 0.4)
        positive_count = sum(1 for kw in self.positive_keywords if kw in content)
        negative_count = sum(1 for kw in self.negative_keywords if kw in content)
        keyword_diff = positive_count - negative_count
        keyword_score = min(0.4, max(0.0, 0.2 + keyword_diff * 0.05))

        # 3. Specificity score (max 0.3)
        # Numbers suggest concrete thinking
        has_numbers = any(c.isdigit() for c in content)
        # Specific terms
        specific_terms = ["step", "first", "then", "because", "result", "measure"]
        specific_count = sum(1 for term in specific_terms if term in content)
        specificity_score = (0.1 if has_numbers else 0.0) + min(0.2, specific_count * 0.05)

        # Combine scores
        total = length_score + keyword_score + specificity_score

        # Ensure in bounds
        return max(0.0, min(1.0, total))

    # -------------------------------------------------------------------------
    # Configuration helpers
    # -------------------------------------------------------------------------

    def with_keywords(
        self,
        positive: list[str] | None = None,
        negative: list[str] | None = None,
    ) -> "SimpleEvaluator":
        """Return a new evaluator with different keywords."""
        return SimpleEvaluator(
            positive_keywords=positive or self.positive_keywords,
            negative_keywords=negative or self.negative_keywords,
            ideal_length=self.ideal_length,
        )
