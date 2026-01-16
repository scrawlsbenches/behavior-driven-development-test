@services @verification @high
Feature: In-Memory Verification Provider
  As a developer testing Graph of Thought
  I want an in-memory verification provider
  So that I can verify thought validation behavior in tests without external dependencies

  # ===========================================================================
  # FEATURE-LEVEL ESCAPE CLAUSES
  # ===========================================================================
  # ESCAPE CLAUSE: No LLM-based verification.
  # Current: InMemoryVerifier uses configurable rules for testing.
  # Requires: LLM integration, prompt templates, response parsing.
  # Depends: LLM provider integration
  #
  # ESCAPE CLAUSE: No external fact-checking integration.
  # Current: Verification results are manually configured or rule-based.
  # Requires: External API integration, caching, rate limiting.
  # Depends: None
  #
  # ESCAPE CLAUSE: No async verification pipelines.
  # Current: Single synchronous verification per call.
  # Requires: Pipeline orchestration, parallel verification strategies.
  # Depends: None

  # ===========================================================================
  # Basic Verification
  # ===========================================================================

  Scenario: Creating a verifier with default pass behavior
    Given an in-memory verifier
    When I verify content "test content"
    Then the verifier result should pass
    And the verifier result confidence should be 1.0

  Scenario: Verifier tracks verification calls
    Given an in-memory verifier
    When I verify content "first"
    And I verify content "second"
    Then the verifier should have 2 verification calls

  Scenario: Verification result includes no issues by default
    Given an in-memory verifier
    When I verify content "valid content"
    Then the verifier result should have 0 issues

  # ===========================================================================
  # Configurable Results (Scenario Outline)
  # ===========================================================================
  # Consolidated from separate scenarios for fail mode, confidence, issues, metadata.

  Scenario Outline: Configuring verifier with <config_type>
    Given an in-memory verifier <configuration>
    When I verify content "<test_content>"
    Then <assertion>

  Examples:
    | config_type | configuration                                          | test_content       | assertion                                           |
    | fail mode   | configured to fail                                     | any content        | the verifier result should fail                     |
    | confidence  | with confidence 0.75                                   | test content       | the verifier result confidence should be 0.75       |

  Scenario: Configuring verifier with issues
    Given an in-memory verifier with issues "Missing citation", "Unclear reasoning"
    When I verify content "problematic content"
    Then the verifier result should have 2 issues
    And the verifier result should have issue "Missing citation"
    And the verifier result should have issue "Unclear reasoning"

  Scenario: Configuring verifier with metadata
    Given an in-memory verifier with metadata source="test", verified_at="2024-01-15"
    When I verify content "test content"
    Then the verifier result metadata should have "source" with value "test"
    And the verifier result metadata should have "verified_at" with value "2024-01-15"

  # ===========================================================================
  # Content-Based Rules (Scenario Outline)
  # ===========================================================================
  # Consolidated from separate matching and non-matching scenarios.

  Scenario Outline: Validation rule rejects content containing "<reject_word>" - <case>
    Given an in-memory verifier
    And a rule that rejects content containing "<reject_word>"
    When I verify content "<test_content>"
    Then the verifier result should <expected_result>

  Examples:
    | reject_word | test_content         | case          | expected_result |
    | error       | this has an error    | matching      | fail            |
    | error       | this is fine         | non-matching  | pass            |
    | spam        | this is spam content | matching      | fail            |
    | spam        | this is valid        | non-matching  | pass            |

  Scenario: Multiple rules are evaluated
    Given an in-memory verifier
    And a rule that rejects content containing "spam"
    And a rule that rejects content containing "invalid"
    When I verify content "this is spam content"
    Then the verifier result should fail

  Scenario: All rules must pass for verification to succeed
    Given an in-memory verifier
    And a rule that rejects content containing "spam"
    And a rule that rejects content containing "invalid"
    When I verify content "this is valid content"
    Then the verifier result should pass

  # ===========================================================================
  # Verification History
  # ===========================================================================

  Scenario: Querying verification history
    Given an in-memory verifier
    When I verify content "first content"
    And I verify content "second content"
    Then I should be able to get verification history
    And the history should contain 2 entries

  Scenario: Verification history includes content
    Given an in-memory verifier
    When I verify content "tracked content"
    Then the last verification should have content "tracked content"

  Scenario: Verification history includes result
    Given an in-memory verifier configured to fail
    When I verify content "failing content"
    Then the last verification should have result is_valid=False

  Scenario: Verification history includes timestamp
    Given an in-memory verifier
    When I verify content "timed content"
    Then the last verification should have a timestamp

  # ===========================================================================
  # Reset and Clear
  # ===========================================================================

  Scenario: Resetting the verifier clears history
    Given an in-memory verifier
    When I verify content "content 1"
    And I verify content "content 2"
    And I reset the verifier
    Then the verifier should have 0 verification calls

  Scenario: Resetting the verifier preserves configuration
    Given an in-memory verifier configured to fail
    When I verify content "before reset"
    And I reset the verifier
    And I verify content "after reset"
    Then the verifier result should fail
    And the verifier should have 1 verification call

  # ===========================================================================
  # Edge Cases
  # ===========================================================================

  Scenario: Verifying empty content
    Given an in-memory verifier
    When I verify content ""
    Then the verifier result should pass

  Scenario: Verifying None content
    Given an in-memory verifier
    When I verify None content
    Then the verifier result should pass

  Scenario: Verification with context is tracked
    Given an in-memory verifier
    When I verify content "test" with context depth=3
    Then the last verification should have context with depth 3

  Scenario: Sequential verifications maintain separate results
    Given an in-memory verifier
    And a rule that rejects content containing "bad"
    When I verify content "good content"
    And I verify content "bad content"
    And I verify content "another good"
    Then the verification history should show pass, fail, pass

  @wip
  Scenario: Async verification pipeline
    Given an in-memory verifier with async rules
    When I verify content with multiple async rules
    Then all rules should be evaluated concurrently

  @wip
  Scenario: Verification caching
    Given an in-memory verifier with caching enabled
    When I verify the same content twice
    Then the second verification should use cached result
    And only 1 actual verification should occur
