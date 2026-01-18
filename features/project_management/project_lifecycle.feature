@project-management @mvp-p0
Feature: AI-Assisted Project Lifecycle
  As an Engineering Manager
  I want to create and track AI-assisted projects with clear phases
  So that I can maintain visibility into progress and ensure teams stay aligned

  As a Product Owner
  I want projects to capture requirements, decisions, and deliverables
  So that scope is clear and stakeholders stay informed

  # ===========================================================================
  # Project Creation and Setup - MVP-P0
  # ===========================================================================
  # Business Rule: Every AI-assisted project starts with a clear objective,
  # assigned team, and allocated budget. This ensures accountability and tracking.

  @mvp-p0 @critical
  Scenario: Engineering Manager creates a new AI-assisted project
    Given Alex is logged in as Engineering Manager
    When Alex creates project "Q1 Performance Optimization" with:
      | field            | value                                          |
      | objective        | Reduce API response time by 40%                |
      | team             | Backend Team                                   |
      | token_budget     | 100000                                         |
      | target_date      | 2024-03-31                                     |
    Then the project should be created with status "active"
    And a project dashboard should be available
    And the token budget should be allocated
    And team members should be notified of the new project

  @mvp-p0 @critical
  Scenario: Project tracks its current work focus
    Given an active project "API Optimization"
    When the team starts working on "Analyze current bottlenecks"
    Then the project's current focus should update to "Analyze current bottlenecks"
    And the start time should be recorded
    And the project status should show "in progress"

  @mvp-p0
  Scenario: Viewing project summary and progress
    Given project "API Optimization" with:
      | metric              | value     |
      | work_chunks         | 5         |
      | tokens_used         | 45000     |
      | tokens_remaining    | 55000     |
      | decisions_made      | 12        |
      | questions_pending   | 3         |
    When Alex views the project dashboard
    Then all metrics should be displayed
    And progress toward objective should be shown
    And pending blockers should be highlighted

  # ===========================================================================
  # Work Chunks - Units of Focused Effort - MVP-P0
  # ===========================================================================
  # Business Rule: Work is organized into "chunks" - focused sessions of 2-4 hours.
  # Each chunk has a clear goal and produces measurable outputs.

  @mvp-p0 @critical
  Scenario: Data scientist starts a focused work chunk
    Given project "Customer Churn Analysis"
    And Jordan is assigned to the project
    When Jordan starts a work chunk "Analyze usage patterns for churned users"
    Then the chunk should be created with status "active"
    And a timer should start tracking duration
    And Jordan's intent should be recorded for context
    And token consumption should be attributed to this chunk

  @mvp-p0
  Scenario: Completing a work chunk with deliverables
    Given an active work chunk "Analyze usage patterns"
    And Jordan has completed the analysis
    When Jordan completes the chunk with summary:
      """
      Analyzed 3 months of usage data. Found that 78% of churned users
      had zero logins in their second week. Key insight: day-7 to day-14
      is the critical retention window.
      """
    Then the chunk should be marked as "completed"
    And the summary should be saved to project knowledge
    And total duration and tokens used should be recorded
    And the project timeline should be updated

  @mvp-p1 @wip @wip
  Scenario: Work chunk discovers a blocker
    Given an active work chunk "Implement caching layer"
    When Casey encounters a blocker requiring external input
    And records blocker "Need Redis infrastructure approval from Platform team"
    Then the chunk status should change to "blocked"
    And a question should be routed to "platform-team"
    And the Engineering Manager should be notified
    And the blocking time should be tracked separately

  @mvp-p1 @wip @wip
  Scenario: Pausing and resuming work chunks
    Given an active work chunk that Jordan needs to pause
    When Jordan pauses the chunk for "end of day"
    Then the chunk should be marked as "paused"
    And current context should be preserved
    And a resumption summary should be generated

    When Jordan resumes the chunk the next day
    Then the previous context should be available
    And Jordan should see "You were working on: [context summary]"
    And the pause duration should not count toward work time

  # ===========================================================================
  # Session Handoffs - Continuity Across Sessions - MVP-P0
  # ===========================================================================
  # Business Rule: Work context must be preserved across sessions, browser
  # refreshes, and handoffs between team members. No context should be lost.

  @mvp-p0 @critical
  Scenario: AI session prepares handoff when context window is filling
    Given an AI session with extensive conversation history
    When the context window reaches 80% capacity
    Then a handoff package should be automatically prepared
    And it should include:
      | content                  | purpose                              |
      | current_intent           | What user is trying to accomplish    |
      | key_decisions            | Important choices made this session  |
      | pending_items            | Work that needs to continue          |
      | critical_context         | Must-know information for resumption |
    And the user should be notified that context will be compressed

  @mvp-p0 @critical
  Scenario: Seamless resumption after session break
    Given Jordan had a session working on "API optimization"
    And the session ended with intent "Testing cache configuration"
    When Jordan starts a new session on the same project
    Then the resumption context should be displayed
    And Jordan should see:
      """
      Welcome back! Last session you were: Testing cache configuration

      Key context:
      - Decided to use Redis for caching
      - Cache TTL set to 5 minutes for user data
      - Still need to: Test under load
      """
    And all previous exploration work should be accessible

  @mvp-p1 @wip @wip
  Scenario: Handoff from AI session to human team member
    Given an AI session has completed initial analysis
    When the AI prepares a handoff for human review
    Then the handoff should include:
      | section              | content                                    |
      | summary              | What was accomplished                      |
      | findings             | Key discoveries and insights               |
      | recommendations      | Suggested next steps                       |
      | open_questions       | Items needing human judgment               |
      | attachments          | Relevant artifacts and data                |
    And the human should be able to continue without re-reading everything

  @mvp-p1 @wip @wip
  Scenario: Handoff from human back to AI session
    Given a human team member has made decisions offline
    When they return to the AI session with updates
    Then they should be able to record:
      | update_type          | example                                    |
      | decision             | "Approved Redis infrastructure"           |
      | context              | "Budget approved for 3 Redis instances"   |
      | next_steps           | "Proceed with implementation"             |
    And the AI should incorporate these updates into context

  # ===========================================================================
  # Multi-User Collaboration - MVP-P1
  # ===========================================================================
  # Business Rule: Multiple team members may work on the same project.
  # Their work should be coordinated and visible to the team.

  @mvp-p1 @wip @wip
  Scenario: Multiple team members working on same project
    Given project "Large Migration" with team members Jordan and Casey
    When Jordan starts a chunk "Analyze source schema"
    And Casey starts a chunk "Set up target environment"
    Then both chunks should be visible on the project dashboard
    And there should be no resource conflicts
    And combined token usage should be tracked

  @mvp-p1 @wip @wip
  Scenario: Seeing team activity on a project
    Given project "API Optimization" with recent activity
    When Alex views the activity feed
    Then recent events should be listed:
      | time        | who    | action                               |
      | 10 min ago  | Jordan | Completed chunk "Load testing"       |
      | 30 min ago  | Casey  | Asked question about Redis config    |
      | 2 hours ago | Jordan | Made decision "Use Redis Cluster"    |
    And filter options should be available

  @mvp-p2 @wip @wip
  Scenario: Mentioning team members in project context
    Given Jordan is working on a chunk and needs Casey's input
    When Jordan mentions "@casey review the connection pool settings"
    Then Casey should receive a notification
    And the mention should appear in project activity
    And Casey should be able to respond asynchronously

  # ===========================================================================
  # Project Completion and Archival - MVP-P1
  # ===========================================================================

  @mvp-p1 @wip @wip
  Scenario: Closing a project with final summary
    Given project "Q1 Optimization" has achieved its objectives
    When Alex closes the project with outcome summary:
      """
      Achieved 45% reduction in API response time (exceeded 40% goal).
      Key changes: Redis caching, query optimization, connection pooling.
      Total cost: 85,000 tokens over 6 weeks.
      """
    Then the project should be marked as "completed"
    And the summary should be added to organizational knowledge
    And the final metrics should be recorded for reporting
    And team members should be notified of completion

  @mvp-p2 @wip @wip
  Scenario: Archiving project for future reference
    Given a completed project from 6 months ago
    When the retention period elapses
    Then the project should be archived
    And it should still be searchable
    And detailed exploration data should be in cold storage
    And key decisions should remain quickly accessible

  # ===========================================================================
  # Edge Cases and Error Handling - Post-MVP
  # ===========================================================================

  @post-mvp @wip
  Scenario: Recovering from session crash during active chunk
    Given an active work chunk when a session crash occurs
    When Jordan reconnects
    Then the chunk should be recoverable
    And work done up to 30 seconds before crash should be preserved
    And Jordan should see what might have been lost

  @post-mvp @wip
  Scenario: Handling conflicting edits from multiple sessions
    Given Jordan and Casey are editing the same exploration
    When both make changes simultaneously
    Then conflict resolution should be offered
    And no work should be lost from either party
    And the project history should show both versions
