@services @communication @high
Feature: Communication Service
  As a developer using Graph of Thought
  I want a communication service to manage context handoffs
  So that I can transfer work between AI and human collaborators seamlessly

  # ===========================================================================
  # TERMINOLOGY
  # ===========================================================================
  # HANDOFF PACKAGE: A structured bundle of context information transferred
  #   between AI and human collaborators. Contains project state, intent history,
  #   and any pending action items needed for seamless work continuation.
  #
  # HANDOFF TYPES:
  #   - ai_to_human: AI transferring work to human (e.g., needs decision/approval)
  #   - human_to_ai: Human delegating work to AI (e.g., implement this feature)
  #
  # INTENT: A recorded statement of what work is being done or planned.
  #   Used to provide context when resuming work after interruption.
  #
  # CONTEXT COMPRESSION: Reducing history size while preserving key information.
  #   Current implementation uses simple truncation (4 chars ≈ 1 token estimate).
  #   Future: LLM-based summarization.

  Background:
    Given a simple communication service

  # ===========================================================================
  # Handoff Management
  # ===========================================================================

  Scenario: Communication service creates handoff packages
    When I create a handoff for project "test_project" of type "ai_to_human"
    Then a handoff package should be created
    And the handoff should have type "ai_to_human"

  Scenario: Communication service records and retrieves intent
    When I record intent "Implement user authentication" for project "test_project"
    And I get resumption context for project "test_project"
    Then the context should contain "Implement user authentication"

  Scenario: Communication service compresses long history using truncation
    # Note: Current compression uses simple truncation at ~4 characters per token.
    # This is a placeholder until LLM-based summarization is implemented.
    Given a recorded intent "Build the API" for project "test_project"
    When I compress history for project "test_project" with max tokens 100
    Then the compressed history should not exceed 400 characters

  # ===========================================================================
  # Future Capabilities
  # ===========================================================================

  @wip
  Scenario: Communication service includes attachments in handoff
    Given a file "architecture.png" attached to project "test_project"
    When I create a handoff for project "test_project" of type "ai_to_human"
    Then the handoff should include attachment "architecture.png"

  @wip
  Scenario: Communication service summarizes history intelligently
    Given project "test_project" with 50 recorded intents
    When I compress history for project "test_project" with max tokens 100
    Then the summary should mention key decisions made
    And the summary should mention current blockers
    And the summary should mention progress percentage

  @wip
  Scenario: Communication service analyzes feedback patterns
    Given 10 negative feedback entries mentioning "slow response"
    When I request a feedback analysis
    Then the analysis should identify "slow response" as a pattern
    And suggest improvements for response time

  @wip
  Scenario: Communication service persists state to database
    Given a simple communication service with database persistence
    And recorded intent "Build API" for project "test_project"
    And feedback "Great work" for project "test_project"
    When the service restarts
    Then the intent "Build API" should be retrievable
    And the feedback "Great work" should be retrievable

  @wip
  Scenario: Communication service includes thread history in handoff
    Given a conversation thread with 5 messages for project "test_project"
    When I create a handoff for project "test_project" of type "ai_to_human"
    Then the handoff should include the conversation thread
    And messages should be in chronological order

  @wip
  Scenario: Communication service includes action items in handoff
    Given pending action items for project "test_project":
      | item                    | assignee |
      | Review PR #123          | alice    |
      | Update documentation    | bob      |
    When I create a handoff for project "test_project" of type "ai_to_human"
    Then the handoff should include 2 action items
    And each action item should have assignee information

  # ===========================================================================
  # Known Limitations (Escape Clauses)
  # ===========================================================================
  # ESCAPE CLAUSE: Intent and feedback storage is in-memory only.
  # Current: All state lost on restart.
  # Requires: Database persistence for intents, feedback, handoffs.
  #
  # ESCAPE CLAUSE: Handoff is simplified version.
  # Current: Basic package with project, type, context.
  # Requires: Full handoff with attachments, thread history, action items.
  #
  # ESCAPE CLAUSE: Feedback is stored but not used for learning.
  # Current: Feedback recorded but never analyzed.
  # Requires: Feedback analysis, model fine-tuning pipeline.
  #
  # ESCAPE CLAUSE: Compression is truncation, not summarization.
  # Current: Simply truncates history to max_tokens * 4 chars.
  # Requires: LLM-based summarization preserving key information.
