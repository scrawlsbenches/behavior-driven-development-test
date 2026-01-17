@wip @ai-reasoning @llm @mvp-p0
Feature: LLM Integration for Thought Generation and Evaluation
  As a Data Scientist
  I want AI-powered generation of follow-up thoughts
  So that I can explore solution spaces more thoroughly than manual brainstorming

  As an Engineering Manager
  I want LLM usage to be reliable, cost-efficient, and auditable
  So that the team can depend on AI capabilities while controlling costs

  As a DevOps Engineer
  I want LLM integrations to be resilient and observable
  So that I can diagnose issues and maintain system reliability

  # ===========================================================================
  # Thought Generation - MVP-P0
  # ===========================================================================
  # Business Rule: The LLM generates relevant follow-up thoughts based on
  # the current thought and exploration context. Outputs are parsed and scored.

  Background:
    Given the LLM service is configured and available

  @mvp-p0 @critical
  Scenario: LLM generates relevant follow-up thoughts
    Given Jordan is exploring "How to improve API performance?"
    And the current thought is "Analyze database query patterns"
    When Jordan requests AI expansion
    Then the LLM should generate 3-5 follow-up thoughts
    And thoughts should be relevant to database performance
    And examples might include:
      | thought                                  | relevance |
      | Add query caching with Redis             | high      |
      | Identify and optimize N+1 queries        | high      |
      | Consider read replica for heavy reads    | medium    |
    And each thought should include a rationale

  @mvp-p0 @critical
  Scenario: Generated thoughts use exploration context
    Given an exploration path:
      | depth | thought                           |
      | 0     | Improve user retention            |
      | 1     | Focus on first-week experience    |
      | 2     | Identify day-3 drop-off causes    |
    When Jordan expands "Identify day-3 drop-off causes"
    Then generated thoughts should reference retention context
    And should not suggest unrelated improvements
    And should build on the "first-week experience" focus

  @mvp-p0
  Scenario: LLM response is parsed correctly
    When the LLM returns thoughts in JSON format:
      """json
      ["Add caching layer", "Optimize slow queries", "Use connection pooling"]
      """
    Then 3 thoughts should be created
    And each thought should be properly formatted
    And no parsing errors should occur

  @mvp-p1
  Scenario: LLM response in markdown is parsed correctly
    When the LLM returns thoughts in markdown format:
      """
      Here are some ideas:
      ```json
      ["Idea one", "Idea two"]
      ```
      """
    Then the JSON should be extracted from markdown
    And 2 thoughts should be created

  @mvp-p1
  Scenario: Plain text response is parsed as line items
    When the LLM returns plain text:
      """
      1. First idea to consider
      2. Second approach
      3. Third alternative
      """
    Then each numbered line should become a thought
    And numbering should be stripped
    And 3 thoughts should be created

  # ===========================================================================
  # Thought Evaluation and Scoring - MVP-P0
  # ===========================================================================
  # Business Rule: Thoughts are scored for quality, feasibility, and relevance.
  # Scores guide which paths are most worth exploring.

  @mvp-p0 @critical
  Scenario: LLM evaluates thought quality
    Given a thought "Implement Redis caching for user sessions"
    And the exploration context is "Improve API performance"
    When the thought is evaluated
    Then a score between 0 and 1 should be assigned
    And the score should reflect:
      | factor          | weight |
      | relevance       | high   |
      | feasibility     | medium |
      | impact          | high   |
    And a reasoning explanation should be provided

  @mvp-p0
  Scenario: Evaluation score is parsed from JSON response
    When the LLM evaluator returns:
      """json
      {"score": 0.85, "reasoning": "Highly relevant and feasible approach"}
      """
    Then the thought score should be 0.85
    And the reasoning should be accessible

  @mvp-p0
  Scenario: Evaluation handles unparseable response gracefully
    When the LLM evaluator returns unparseable text
    Then a neutral score of 0.5 should be assigned
    And the system should not fail
    And a warning should be logged

  @mvp-p1
  Scenario: Scores out of range are clamped
    When the LLM returns score 1.5
    Then the score should be clamped to 1.0
    When the LLM returns score -0.3
    Then the score should be clamped to 0.0

  # ===========================================================================
  # Thought Verification - MVP-P1
  # ===========================================================================
  # Business Rule: Thoughts can be verified for logical consistency and
  # factual accuracy before being presented as conclusions.

  @mvp-p1
  Scenario: LLM verifies thought validity
    Given a thought claiming "Redis supports transactions"
    When verification is requested
    Then the verifier should check factual accuracy
    And return:
      | field      | value                                    |
      | is_valid   | true                                     |
      | confidence | 0.9                                      |
      | notes      | Redis supports MULTI/EXEC transactions   |

  @mvp-p1
  Scenario: Verification identifies invalid claims
    Given a thought with an incorrect claim
    When verification is requested
    Then the verifier should identify issues:
      | field      | value                                    |
      | is_valid   | false                                    |
      | confidence | 0.8                                      |
      | issues     | ["Contradicts documented behavior"]      |
    And the thought should be flagged for review

  @mvp-p1
  Scenario: Verification is optional and non-blocking
    Given a thought that hasn't been verified
    Then it should still be usable in exploration
    And verification can be requested later
    And unverified status should be visible

  # ===========================================================================
  # LLM Configuration - MVP-P1
  # ===========================================================================
  # Business Rule: LLM behavior can be tuned for different use cases.
  # Configuration affects token usage and output quality.

  @mvp-p1
  Scenario: Configuring generation temperature
    Given the default temperature is 0.7
    When Jordan configures temperature 0.9 for creative brainstorming
    Then generated thoughts should be more diverse
    And unexpected ideas should be more likely

    When Jordan configures temperature 0.2 for focused analysis
    Then generated thoughts should be more conservative
    And they should closely follow the context

  @mvp-p1
  Scenario: Configuring number of generated thoughts
    When Jordan sets generation count to 8
    Then up to 8 thoughts should be generated per expansion
    And token usage should increase proportionally

  @mvp-p1
  Scenario: Configuring max tokens per request
    Given a max_tokens setting of 1024
    When generation is requested
    Then the LLM request should respect the limit
    And output should be truncated if necessary
    And the setting should balance cost vs. completeness

  # ===========================================================================
  # Error Handling and Resilience - MVP-P1
  # ===========================================================================
  # Business Rule: LLM failures should not crash the application. Graceful
  # degradation and clear user feedback are required.

  @mvp-p1 @critical
  Scenario: Handling LLM timeout gracefully
    Given the LLM service is slow
    When a request times out after 30 seconds
    Then Jordan should see "AI service is slow, please retry"
    And the exploration should remain usable
    And partial results should be saved if available
    And the timeout should be logged

  @mvp-p1
  Scenario: Handling rate limit errors
    Given the LLM rate limit is exceeded
    When a request fails with rate limit error
    Then Jordan should see estimated wait time
    And automatic retry should be scheduled
    And the work chunk should not be blocked
    And the rate limit should be tracked in metrics

  @mvp-p1
  Scenario: Fallback to alternative model
    Given the primary model "claude-opus-4-5-20251101" is unavailable
    And a fallback model "claude-sonnet-4-20250514" is configured
    When generation is requested
    Then the fallback model should be used
    And Jordan should be notified of the fallback
    And output quality may be different
    And the event should be logged

  @mvp-p1
  Scenario: Handling malformed LLM response
    When the LLM returns malformed JSON
    Then the system should attempt line-based parsing
    And if all parsing fails, return empty results with message
    And the malformed response should be logged for debugging
    And the exploration should remain stable

  # ===========================================================================
  # Cost Tracking and Optimization - MVP-P0
  # ===========================================================================
  # Business Rule: LLM usage is metered and attributed to projects for
  # accurate cost tracking and budgeting.

  @mvp-p0 @critical
  Scenario: Token usage is tracked per request
    Given Jordan makes an LLM request
    When the request completes
    Then token usage should be recorded:
      | field          | tracked |
      | input_tokens   | yes     |
      | output_tokens  | yes     |
      | total_tokens   | yes     |
      | model          | yes     |
      | cost_estimate  | yes     |
    And usage should be attributed to:
      | attribution    | value                |
      | user           | Jordan               |
      | project        | Churn Analysis       |
      | operation      | thought_expansion    |

  @mvp-p1
  Scenario: Cost optimization suggestions
    Given Jordan's project has high LLM costs
    When cost analysis runs
    Then suggestions might include:
      | suggestion                              | potential_savings |
      | Use smaller model for initial scoring   | 30%               |
      | Batch similar expansions                | 15%               |
      | Reduce temperature (fewer tokens)       | 10%               |

  @mvp-p1
  Scenario: Request blocked when budget exhausted
    Given project budget is exhausted
    When Jordan tries to request LLM generation
    Then the request should be blocked
    And Jordan should see "Token budget exhausted"
    And a budget increase request should be offered

  # ===========================================================================
  # Prompt Templates - MVP-P1
  # ===========================================================================
  # Business Rule: Prompts are templated for consistency and can be customized
  # for specific use cases.

  @mvp-p1
  Scenario: Default generation prompt includes context
    Given the default generation template
    When a prompt is generated for thought expansion
    Then the prompt should include:
      | section          | content                          |
      | parent_thought   | The thought being expanded       |
      | path_context     | Previous thoughts in the path    |
      | generation_count | How many ideas to generate       |
      | format_instructions| Expected output format         |

  @mvp-p1
  Scenario: Custom prompt templates for specific domains
    Given a custom template for "Security Analysis":
      """
      You are a security expert. Given this security concern:
      {parent_thought}

      Context from prior analysis:
      {path_context}

      Generate {num_children} potential security implications or mitigations.
      Focus on OWASP Top 10 and enterprise security best practices.
      """
    When the template is used for security-tagged thoughts
    Then generated thoughts should have security focus
    And they should reference security frameworks

  # ===========================================================================
  # Provider Flexibility - MVP-P2
  # ===========================================================================

  @mvp-p2
  Scenario: Switching between LLM providers
    Given configured providers:
      | provider  | use_case                |
      | anthropic | Primary generation      |
      | openai    | Fallback, evaluation    |
      | local     | Development, testing    |
    When the provider is switched
    Then the system should adapt to provider specifics
    And prompt format should adjust if needed
    And metrics should track per-provider usage

  @mvp-p2 @wip
  Scenario: Local model for development
    Given a local Ollama instance with llama2
    When developing offline
    Then the local model should be usable
    And no external API calls should be made
    And development costs should be zero

  # ===========================================================================
  # Edge Cases - Post-MVP
  # ===========================================================================

  @post-mvp @wip
  Scenario: Streaming responses for long generations
    Given streaming is enabled
    When a large generation is requested
    Then partial results should be streamed as available
    And Jordan should see thoughts appearing incrementally
    And the final result should be complete

  @post-mvp @wip
  Scenario: Context window management for long explorations
    Given an exploration with 50 thoughts in the path
    When the context exceeds model limits
    Then older context should be intelligently summarized
    And the most relevant context should be preserved
    And no generation quality should be lost
