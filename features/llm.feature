@llm @integration @high
Feature: LLM Integration
  As a developer using Graph of Thought
  I want to use LLM-based generators and evaluators
  So that I can leverage AI for thought generation and evaluation

  # ===========================================================================
  # FEATURE-LEVEL ESCAPE CLAUSES
  # ===========================================================================
  # ESCAPE CLAUSE: Only Claude provider implemented.
  # Current: ClaudeGenerator, ClaudeEvaluator, ClaudeVerifier only.
  # Requires: OpenAI, local models (Ollama), Azure OpenAI implementations.
  # Depends: None
  #
  # ESCAPE CLAUSE: No streaming responses.
  # Current: Waits for complete response before processing.
  # Requires: Async generators yielding partial thoughts as they arrive.
  # Depends: None
  #
  # ESCAPE CLAUSE: No retry/backoff logic.
  # Current: Single attempt, fails on any error.
  # Requires: Exponential backoff, rate limit handling, timeout config.
  # Depends: None
  #
  # ESCAPE CLAUSE: No response caching.
  # Current: Every call hits the LLM API.
  # Requires: Cache layer (Redis/in-memory) with TTL, cache key generation.
  # Depends: None
  #
  # ESCAPE CLAUSE: No cost tracking.
  # Current: Token usage not tracked or reported.
  # Requires: Token counting, cost calculation per model, budget integration.
  # Depends: Resource service integration

  # ===========================================================================
  # Prompt Templates
  # ===========================================================================

  Scenario: Creating a custom prompt template
    Given a prompt template with system "You are helpful" and user "Help with: {topic}"
    When I format the template with topic "testing"
    Then the formatted user prompt should contain "Help with: testing"

  Scenario: Default generation template has required placeholders
    Given the default generation template
    Then the template should have placeholder "parent"
    And the template should have placeholder "path"
    And the template should have placeholder "num_children"

  Scenario: Default evaluation template has required placeholders
    Given the default evaluation template
    Then the template should have placeholder "thought"
    And the template should have placeholder "path"

  Scenario: Default verification template has required placeholders
    Given the default verification template
    Then the template should have placeholder "thought"
    And the template should have placeholder "path"

  # --- Template Edge Cases (TODO: Implement) ---

  @wip
  Scenario: Template validates required placeholders
    Given a prompt template with system "You are helpful" and user "Help with: {topic}"
    When I try to format the template without providing "topic"
    Then an error should be raised
    And the error should mention missing placeholder "topic"

  @wip
  Scenario: Template supports conditional sections
    Given a prompt template with optional context section
    When I format the template without context
    Then the context section should be omitted
    When I format the template with context "Previous discussion"
    Then the context section should contain "Previous discussion"

  # ===========================================================================
  # Response Parsing - Generator
  # ===========================================================================
  # ESCAPE CLAUSE: Context truncation is basic.
  # Current: Takes last 5 path items, truncates each to 50 chars.
  # Requires: Token-aware truncation, importance-based selection.
  # Depends: Token counting implementation

  Scenario: Generator parses JSON array response
    Given a mock LLM generator
    When the LLM returns '["thought 1", "thought 2", "thought 3"]'
    Then the generator should produce 3 thoughts
    And thought 1 should be "thought 1"

  Scenario: Generator parses JSON in markdown code block
    Given a mock LLM generator
    When the LLM returns a markdown code block with '["idea A", "idea B"]'
    Then the generator should produce 2 thoughts

  Scenario: Generator falls back to line parsing for non-JSON
    Given a mock LLM generator
    When the LLM returns plain text lines "1. First idea\n2. Second idea\n3. Third idea"
    Then the generator should produce 3 thoughts
    And thought 1 should be "First idea"

  # --- Generator Edge Cases (TODO: Implement) ---

  @wip
  Scenario: Generator handles rate limit errors with retry
    Given a mock LLM generator with rate limiting
    When the LLM returns a rate limit error
    Then the generator should retry after backoff
    And eventually produce thoughts

  @wip
  Scenario: Generator tracks token usage
    Given a mock LLM generator with token tracking
    When the LLM returns '["thought 1", "thought 2"]'
    Then the token usage should be recorded
    And include input tokens and output tokens

  @wip
  Scenario: Generator respects token budget
    Given a mock LLM generator
    And a remaining token budget of 100
    When I try to generate thoughts
    Then the generation should fail with budget exceeded error

  @wip
  Scenario: Generator handles malformed JSON gracefully
    Given a mock LLM generator
    When the LLM returns '["thought 1", "thought 2"'
    Then the generator should fall back to line parsing
    And produce at least 1 thought

  # ===========================================================================
  # Response Parsing - Evaluator
  # ===========================================================================

  Scenario: Evaluator parses JSON score response
    Given a mock LLM evaluator
    When the LLM returns '{"score": 0.85, "reasoning": "Good clarity"}'
    Then the evaluation score should be 0.85

  Scenario: Evaluator parses score from markdown code block
    Given a mock LLM evaluator
    When the LLM returns a markdown code block with '{"score": 0.7}'
    Then the evaluation score should be 0.7

  Scenario: Evaluator extracts number from plain text
    Given a mock LLM evaluator
    When the LLM returns 'The thought scores 0.6 overall'
    Then the evaluation score should be 0.6

  Scenario: Evaluator defaults to 0.5 for unparseable responses
    Given a mock LLM evaluator
    When the LLM returns 'Cannot evaluate this thought'
    Then the evaluation score should be 0.5

  # --- Evaluator Edge Cases (TODO: Implement) ---

  @wip
  Scenario: Evaluator caches identical thought evaluations
    Given a mock LLM evaluator with caching
    When I evaluate "Test thought" twice
    Then the LLM should only be called once
    And both evaluations should return the same score

  @wip
  Scenario: Evaluator validates score is in valid range
    Given a mock LLM evaluator
    When the LLM returns '{"score": 1.5}'
    Then the score should be clamped to 1.0

  @wip
  Scenario: Evaluator provides reasoning with score
    Given a mock LLM evaluator
    When the LLM returns '{"score": 0.8, "reasoning": "Clear and actionable"}'
    Then the evaluation score should be 0.8
    And the evaluation reasoning should be "Clear and actionable"

  # ===========================================================================
  # Response Parsing - Verifier
  # ===========================================================================

  Scenario: Verifier parses valid verification response
    Given a mock LLM verifier
    When the LLM returns '{"is_valid": true, "confidence": 0.9, "issues": []}'
    Then the verification should be valid
    And the verification confidence should be 0.9

  Scenario: Verifier parses invalid verification with issues
    Given a mock LLM verifier
    When the LLM returns '{"is_valid": false, "confidence": 0.8, "issues": ["Contradicts premise"]}'
    Then the verification should be invalid
    And the verification should have 1 issue

  Scenario: Verifier defaults to valid on parse error
    Given a mock LLM verifier
    When the LLM returns 'Unable to verify thought'
    Then the verification should be valid
    And the verification confidence should be 0.5

  # --- Verifier Edge Cases (TODO: Implement) ---

  @wip
  Scenario: Verifier categorizes issue severity
    Given a mock LLM verifier
    When the LLM returns verification with issues:
      | issue                    | severity |
      | Minor typo              | low      |
      | Contradicts premise     | high     |
    Then the verification should have 1 high severity issue
    And the verification should have 1 low severity issue

  @wip
  Scenario: Verifier suggests fixes for issues
    Given a mock LLM verifier
    When the LLM returns '{"is_valid": false, "issues": ["Contradicts premise"], "suggestions": ["Revise to align with premise"]}'
    Then the verification should include suggestion "Revise to align with premise"

  # ===========================================================================
  # Base Class Configuration
  # ===========================================================================

  Scenario: Generator configures temperature and max tokens
    Given a base LLM generator with temperature 0.9 and max_tokens 2048
    Then the generator should have temperature 0.9
    And the generator should have max_tokens 2048

  Scenario: Evaluator configures temperature and max tokens
    Given a base LLM evaluator with temperature 0.2 and max_tokens 512
    Then the evaluator should have temperature 0.2
    And the evaluator should have max_tokens 512

  Scenario: Generator configures number of children
    Given a base LLM generator with num_children 5
    Then the generator should produce up to 5 children

  # --- Configuration Edge Cases (TODO: Implement) ---

  @wip
  Scenario: Generator validates temperature range
    When I create a generator with temperature 2.0
    Then an error should be raised
    And the error should mention "temperature must be between 0 and 1"

  @wip
  Scenario: Generator supports model fallback
    Given a mock LLM generator with primary model "claude-opus-4-20250514" and fallback "claude-sonnet-4-20250514"
    When the primary model is unavailable
    Then the generator should use the fallback model
    And a warning should be logged

  # ===========================================================================
  # Provider Implementations (TODO: Implement)
  # ===========================================================================

  @wip
  Scenario: OpenAI generator produces thoughts
    Given an OpenAI generator with model "gpt-4"
    When I generate thoughts from "How to improve performance?"
    Then the generator should produce thoughts
    And the API call should use the correct model

  @wip
  Scenario: Local model generator produces thoughts
    Given a local Ollama generator with model "llama2"
    When I generate thoughts from "How to improve performance?"
    Then the generator should produce thoughts
    And no external API calls should be made

  @wip
  Scenario: Generator handles API timeout
    Given a mock LLM generator with timeout 5 seconds
    When the LLM takes 10 seconds to respond
    Then a timeout error should be raised
    And the error should be retryable
