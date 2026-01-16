"""
LLM integration for Graph of Thought.

This module provides thought generators and evaluators that
integrate with LLM APIs like Claude.

Example usage:
    from graph_of_thought.llm import ClaudeGenerator, ClaudeEvaluator
    
    generator = ClaudeGenerator(
        client=anthropic.AsyncAnthropic(),
        model="claude-sonnet-4-20250514",
    )
    
    evaluator = ClaudeEvaluator(
        client=anthropic.AsyncAnthropic(),
        model="claude-sonnet-4-20250514",
    )
    
    graph = GraphOfThought(
        generator=generator,
        evaluator=evaluator,
    )
"""

from __future__ import annotations
from typing import TypeVar, Any
from dataclasses import dataclass
import json
import re

from ..core import (
    SearchContext,
    ThoughtGenerator,
    ThoughtEvaluator,
    ThoughtVerifier,
    VerificationResult,
    GenerationError,
    EvaluationError,
)

T = TypeVar("T")


@dataclass
class PromptTemplate:
    """Template for LLM prompts."""
    system: str
    user: str
    
    def format(self, **kwargs: Any) -> tuple[str, str]:
        """Format the template with provided values."""
        return (
            self.system.format(**kwargs),
            self.user.format(**kwargs),
        )


# Default prompt templates
DEFAULT_GENERATION_TEMPLATE = PromptTemplate(
    system="""You are a reasoning assistant. Given a thought or problem statement, 
generate {num_children} distinct follow-up thoughts or approaches to explore.

Each thought should:
1. Build on or refine the parent thought
2. Be a complete, actionable idea
3. Be distinct from other generated thoughts

Respond with a JSON array of strings, each being a new thought.""",
    user="""Parent thought: {parent}

Context path: {path}

Generate {num_children} follow-up thoughts as a JSON array:"""
)


DEFAULT_EVALUATION_TEMPLATE = PromptTemplate(
    system="""You are a reasoning evaluator. Score the quality and promise of a thought
on a scale from 0.0 to 1.0, where:
- 0.0-0.2: Poor quality, unlikely to lead anywhere useful
- 0.3-0.4: Below average, some issues
- 0.5-0.6: Average, reasonable approach
- 0.7-0.8: Good quality, promising direction
- 0.9-1.0: Excellent, very likely to succeed

Consider:
1. Clarity and specificity
2. Logical coherence with the reasoning path
3. Likelihood of leading to a good solution
4. Novelty and insight

Respond with ONLY a JSON object: {{"score": <float>, "reasoning": "<brief explanation>"}}""",
    user="""Thought to evaluate: {thought}

Context path: {path}

Evaluate this thought:"""
)


DEFAULT_VERIFICATION_TEMPLATE = PromptTemplate(
    system="""You are a reasoning verifier. Check if a thought is valid and consistent
with the reasoning path.

Check for:
1. Logical consistency with parent thoughts
2. Factual accuracy (if applicable)
3. Internal coherence
4. Contradictions with earlier reasoning

Respond with a JSON object:
{{"is_valid": true/false, "confidence": <0.0-1.0>, "issues": ["issue1", ...]}}""",
    user="""Thought to verify: {thought}

Reasoning path: {path}

Verify this thought:"""
)


class BaseLLMGenerator:
    """
    Base class for LLM-based thought generators.
    
    Subclass this and implement _call_llm for specific LLM providers.
    """
    
    def __init__(
        self,
        template: PromptTemplate | None = None,
        num_children: int = 3,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        self.template = template or DEFAULT_GENERATION_TEMPLATE
        self.num_children = num_children
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    async def generate(
        self,
        parent: str,
        context: SearchContext[str],
    ) -> list[str]:
        """Generate child thoughts from a parent."""
        path_str = " -> ".join(str(t.content)[:50] for t in context.path_to_root[-5:])
        
        system, user = self.template.format(
            parent=parent,
            path=path_str or "(root)",
            num_children=self.num_children,
        )
        
        try:
            response = await self._call_llm(system, user)
            return self._parse_response(response)
        except Exception as e:
            raise GenerationError(f"Failed to generate thoughts: {e}", cause=e)
    
    async def _call_llm(self, system: str, user: str) -> str:
        """Call the LLM API. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _call_llm")
    
    def _parse_response(self, response: str) -> list[str]:
        """Parse the LLM response into a list of thoughts."""
        # Try to extract JSON array
        try:
            # Handle markdown code blocks
            if "```" in response:
                match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
                if match:
                    response = match.group(1)
            
            thoughts = json.loads(response)
            if isinstance(thoughts, list):
                return [str(t) for t in thoughts if t]
        except json.JSONDecodeError:
            pass
        
        # Fallback: split by newlines and clean up
        lines = [line.strip() for line in response.split("\n") if line.strip()]
        return [re.sub(r"^[\d\.\-\*\)]+\s*", "", line) for line in lines if line]


class BaseLLMEvaluator:
    """
    Base class for LLM-based thought evaluators.
    
    Subclass this and implement _call_llm for specific LLM providers.
    """
    
    def __init__(
        self,
        template: PromptTemplate | None = None,
        temperature: float = 0.3,
        max_tokens: int = 256,
    ):
        self.template = template or DEFAULT_EVALUATION_TEMPLATE
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    async def evaluate(
        self,
        content: str,
        context: SearchContext[str],
    ) -> float:
        """Evaluate a thought and return a score."""
        path_str = " -> ".join(str(t.content)[:50] for t in context.path_to_root[-5:])
        
        system, user = self.template.format(
            thought=content,
            path=path_str or "(root)",
        )
        
        try:
            response = await self._call_llm(system, user)
            return self._parse_response(response)
        except Exception as e:
            raise EvaluationError(f"Failed to evaluate thought: {e}", cause=e)
    
    async def _call_llm(self, system: str, user: str) -> str:
        """Call the LLM API. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _call_llm")
    
    def _parse_response(self, response: str) -> float:
        """Parse the LLM response into a score."""
        try:
            # Handle markdown code blocks
            if "```" in response:
                match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
                if match:
                    response = match.group(1)
            
            data = json.loads(response)
            if isinstance(data, dict) and "score" in data:
                return float(data["score"])
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
        
        # Fallback: try to find a number
        numbers = re.findall(r"(?:^|[^\d])(\d*\.?\d+)(?:[^\d]|$)", response)
        for num_str in numbers:
            try:
                num = float(num_str)
                if 0 <= num <= 1:
                    return num
            except ValueError:
                continue
        
        return 0.5  # Default to middle score


class BaseLLMVerifier:
    """
    Base class for LLM-based thought verifiers.
    
    Subclass this and implement _call_llm for specific LLM providers.
    """
    
    def __init__(
        self,
        template: PromptTemplate | None = None,
        temperature: float = 0.3,
        max_tokens: int = 512,
    ):
        self.template = template or DEFAULT_VERIFICATION_TEMPLATE
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    async def verify(
        self,
        content: str,
        context: SearchContext[str],
    ) -> VerificationResult:
        """Verify a thought's validity."""
        path_str = " -> ".join(str(t.content)[:50] for t in context.path_to_root[-5:])
        
        system, user = self.template.format(
            thought=content,
            path=path_str or "(root)",
        )
        
        try:
            response = await self._call_llm(system, user)
            return self._parse_response(response)
        except Exception as e:
            return VerificationResult(
                is_valid=True,  # Default to valid on error
                confidence=0.5,
                issues=[f"Verification failed: {e}"],
            )
    
    async def _call_llm(self, system: str, user: str) -> str:
        """Call the LLM API. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _call_llm")
    
    def _parse_response(self, response: str) -> VerificationResult:
        """Parse the LLM response into a verification result."""
        try:
            if "```" in response:
                match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
                if match:
                    response = match.group(1)
            
            data = json.loads(response)
            return VerificationResult(
                is_valid=bool(data.get("is_valid", True)),
                confidence=float(data.get("confidence", 1.0)),
                issues=data.get("issues", []),
            )
        except (json.JSONDecodeError, ValueError):
            return VerificationResult(is_valid=True, confidence=0.5)


# Example implementation for Claude (requires anthropic package)
class ClaudeGenerator(BaseLLMGenerator):
    """
    Thought generator using Claude API.
    
    Requires: pip install anthropic
    
    Usage:
        import anthropic
        
        generator = ClaudeGenerator(
            client=anthropic.AsyncAnthropic(),
            model="claude-sonnet-4-20250514",
        )
    """
    
    def __init__(
        self,
        client: Any,  # anthropic.AsyncAnthropic
        model: str = "claude-sonnet-4-20250514",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.client = client
        self.model = model
    
    async def _call_llm(self, system: str, user: str) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text


class ClaudeEvaluator(BaseLLMEvaluator):
    """
    Thought evaluator using Claude API.
    
    Requires: pip install anthropic
    """
    
    def __init__(
        self,
        client: Any,  # anthropic.AsyncAnthropic
        model: str = "claude-sonnet-4-20250514",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.client = client
        self.model = model
    
    async def _call_llm(self, system: str, user: str) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text


class ClaudeVerifier(BaseLLMVerifier):
    """
    Thought verifier using Claude API.
    
    Requires: pip install anthropic
    """
    
    def __init__(
        self,
        client: Any,  # anthropic.AsyncAnthropic
        model: str = "claude-sonnet-4-20250514",
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.client = client
        self.model = model
    
    async def _call_llm(self, system: str, user: str) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text


__all__ = [
    "PromptTemplate",
    "DEFAULT_GENERATION_TEMPLATE",
    "DEFAULT_EVALUATION_TEMPLATE",
    "DEFAULT_VERIFICATION_TEMPLATE",
    "BaseLLMGenerator",
    "BaseLLMEvaluator",
    "BaseLLMVerifier",
    "ClaudeGenerator",
    "ClaudeEvaluator",
    "ClaudeVerifier",
]
