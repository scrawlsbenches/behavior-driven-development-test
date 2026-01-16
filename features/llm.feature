Feature: LLM Integration
  As a developer using Graph of Thought
  I want to use LLM-based generators and evaluators
  So that I can leverage AI for thought generation and evaluation

  # Prompt Templates

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

  # Response Parsing - Generator

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

  # Response Parsing - Evaluator

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

  # Response Parsing - Verifier

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

  # Base class configuration

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
