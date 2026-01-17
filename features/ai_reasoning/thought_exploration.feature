@wip @ai-reasoning @mvp-p0
Feature: AI-Assisted Thought Exploration
  As a Data Scientist exploring complex problems
  I want to create and navigate a graph of interconnected thoughts
  So that I can systematically explore solution spaces and build on promising ideas

  As an Engineering Manager
  I want my team's exploration sessions to be structured and traceable
  So that we can understand how conclusions were reached and build on past work

  # ===========================================================================
  # Starting a Reasoning Session - MVP-P0
  # ===========================================================================
  # Business Rule: Every exploration starts with a root question or problem statement.
  # This becomes the foundation for all subsequent reasoning.

  Background:
    Given a test graph with evaluator and generator

  @mvp-p0 @critical
  Scenario: Data scientist starts exploration with a problem statement
    When Jordan starts exploring "How can we reduce customer churn by 20%?"
    Then a root thought should be created with the problem statement
    And the exploration session should be ready for expansion
    And the thought should be marked as "pending" exploration

  @mvp-p0 @critical
  Scenario: Building on an existing idea with follow-up thoughts
    Given Jordan is exploring "How can we reduce customer churn by 20%?"
    When Jordan adds a follow-up thought "Analyze customer behavior patterns"
    Then the follow-up should be connected to the root problem
    And the exploration depth should increase by 1
    And both thoughts should be visible in the exploration path

  @mvp-p0 @critical
  Scenario: Connecting related ideas across the exploration
    Given an exploration with thoughts:
      | thought                              | parent                                    |
      | How can we reduce customer churn?    |                                           |
      | Analyze behavior patterns            | How can we reduce customer churn?         |
      | Improve onboarding experience        | How can we reduce customer churn?         |
    When Jordan connects "Analyze behavior patterns" to "Improve onboarding experience"
    Then the thoughts should be linked
    And exploring from "Analyze behavior patterns" should show the connection

  # ===========================================================================
  # Navigating the Thought Space - MVP-P0
  # ===========================================================================
  # Business Rule: Users need to trace how ideas evolved and find the most
  # promising paths through the exploration.

  @mvp-p0
  Scenario: Tracing the reasoning path to a conclusion
    Given an exploration with a deep thought chain:
      | depth | thought                                    |
      | 0     | Reduce customer churn                      |
      | 1     | Analyze usage patterns                     |
      | 2     | Users drop off after day 3                 |
      | 3     | Day 3 is first billing reminder            |
      | 4     | Offer trial extension on day 3             |
    When Jordan asks "How did we reach 'Offer trial extension'?"
    Then the full reasoning path should be displayed
    And each step should show how it led to the next

  @mvp-p0
  Scenario: Finding all ideas at a certain exploration depth
    Given an exploration where 5 ideas have been explored to depth 2
    When Jordan looks at "second-level insights"
    Then all 5 depth-2 thoughts should be listed
    And they should be sorted by their promise score

  @mvp-p1
  Scenario: Identifying dead-end explorations
    Given an exploration with some low-scoring thought chains
    When Jordan asks "Which paths aren't worth pursuing?"
    Then thoughts with scores below 0.3 should be highlighted
    And their parent paths should be flagged as "diminishing returns"

  # ===========================================================================
  # Managing Exploration Quality - MVP-P1
  # ===========================================================================
  # Business Rule: Not all thoughts are equally valuable. The system should
  # help users focus on promising directions and prune dead ends.

  @mvp-p1
  Scenario: Marking a thought direction as not worth pursuing
    Given Jordan is exploring "Improve customer retention"
    And has generated the thought "Reduce product price by 50%"
    When Jordan marks this thought as "not viable - would destroy margins"
    Then the thought should be marked as pruned
    And future expansions should not build on this thought
    And the pruning reason should be recorded for learning

  @mvp-p1
  Scenario: Merging duplicate or similar thoughts
    Given an exploration with similar thoughts:
      | thought                           | score |
      | Improve email onboarding          | 0.7   |
      | Better onboarding emails          | 0.8   |
      | Email onboarding improvements     | 0.6   |
    When Jordan merges these as "Improve onboarding email sequence"
    Then a single merged thought should exist with score 0.8
    And the original thoughts should be marked as merged
    And all child thoughts should now connect to the merged thought

  @mvp-p1
  Scenario: Scoring thoughts to prioritize exploration
    Given thoughts with different promise levels:
      | thought                        |
      | Reduce price                   |
      | Improve support response time  |
      | Add gamification               |
    When the thoughts are evaluated
    Then each thought should have a score between 0 and 1
    And "Improve support response time" should score highest
    And the scores should reflect business viability

  # ===========================================================================
  # Preventing Circular Reasoning - MVP-P0
  # ===========================================================================
  # Business Rule: Explorations must not contain circular reasoning paths.
  # This ensures logical integrity and prevents infinite loops.

  @mvp-p0 @critical
  Scenario: System prevents circular reasoning paths
    Given an exploration chain: "A" -> "B" -> "C"
    When Jordan tries to connect "C" back to "A"
    Then the connection should be rejected
    And the reason should explain "This would create circular reasoning"
    And the exploration should remain valid

  @mvp-p0 @critical
  Scenario: Detecting self-referential thoughts
    Given a thought "Improve performance"
    When Jordan tries to mark it as its own follow-up
    Then the action should be rejected
    And a clear error should explain why

  @mvp-p2
  Scenario: Allowing cycles when explicitly enabled for brainstorming
    Given a brainstorming session where cycles are allowed
    And thoughts "Feature A", "Feature B", and "Feature C"
    When Jordan connects them in a cycle to show interdependencies
    Then the circular connection should be allowed
    And the session should be marked as "non-linear exploration"

  # ===========================================================================
  # Session Persistence - MVP-P0
  # ===========================================================================
  # Business Rule: Exploration sessions must persist across browser refreshes,
  # logouts, and system restarts. No work should ever be lost.

  @mvp-p0 @critical
  Scenario: Saving exploration progress automatically
    Given Jordan has explored 15 thoughts over 30 minutes
    When Jordan's session is interrupted unexpectedly
    Then all 15 thoughts should be recoverable
    And the exploration structure should be intact
    And Jordan should be able to resume exactly where they left off

  @mvp-p0
  Scenario: Exporting exploration for sharing with team
    Given a completed exploration with 20 thoughts and a conclusion
    When Jordan exports the exploration
    Then a shareable format should be generated
    And it should include all thoughts, connections, and scores
    And team members should be able to import and continue the work

  @mvp-p1
  Scenario: Loading a previous exploration to continue work
    Given Jordan saved an exploration "Q3 Churn Analysis" last week
    When Jordan loads the saved exploration
    Then all thoughts should be restored
    And the exploration should be ready for continued work
    And new thoughts can be added to the existing structure

  # ===========================================================================
  # Exploration Statistics - MVP-P2
  # ===========================================================================
  # Business Rule: Teams need visibility into exploration patterns to improve
  # their analytical processes over time.

  @mvp-p2
  Scenario: Viewing exploration statistics
    Given an exploration with:
      | metric          | value |
      | total thoughts  | 45    |
      | max depth       | 7     |
      | pruned thoughts | 12    |
      | avg score       | 0.65  |
    When Jordan views exploration statistics
    Then all metrics should be displayed
    And insights should suggest "Consider pruning low-scoring branches"

  @mvp-p2
  Scenario: Visualizing the exploration as a tree
    Given an exploration with multiple branches
    When Jordan requests a visual representation
    Then a tree visualization should be generated
    And high-scoring paths should be visually emphasized
    And pruned branches should be visually de-emphasized

  # ===========================================================================
  # Edge Cases and Error Handling - Post-MVP
  # ===========================================================================

  @post-mvp @wip
  Scenario: Handling extremely deep explorations
    Given an exploration that has reached depth 50
    When Jordan tries to add another level
    Then a warning should suggest "Consider summarizing this branch"
    And the option to continue should still be available
    And performance should remain acceptable

  @post-mvp @wip
  Scenario: Recovering from corrupted exploration data
    Given an exploration with some corrupted thought data
    When Jordan loads the exploration
    Then recoverable thoughts should be restored
    And corrupted thoughts should be flagged
    And Jordan should be notified of what was lost
