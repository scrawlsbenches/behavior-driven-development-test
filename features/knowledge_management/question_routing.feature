@knowledge-management @questions @mvp-p0
Feature: Intelligent Question Routing
  As a Product Owner
  I want questions from AI sessions to reach the right experts quickly
  So that critical decisions aren't blocked waiting for answers

  As an Engineering Manager
  I want visibility into pending questions affecting my team's projects
  So that I can ensure timely responses and identify bottlenecks

  As a Data Scientist
  I want my blocking questions prioritized appropriately
  So that I can continue productive work without long waits

  # ===========================================================================
  # Asking Questions - MVP-P0
  # ===========================================================================
  # Business Rule: Questions can be blocking (stops work) or non-blocking
  # (nice to have). Blocking questions are prioritized and tracked.

  Background:
    Given the question service is available
    And question routing rules are configured

  @mvp-p0 @critical
  Scenario: Developer asks a blocking question during work
    Given Jordan is working on "Customer churn analysis"
    When Jordan asks a blocking question:
      | field       | value                                                |
      | question    | Should we include trial users in churn calculation?  |
      | context     | Analyzing retention metrics, trials behave differently|
      | blocking    | true                                                 |
    Then a question ticket should be created with high priority
    And the ticket should include work context
    And it should be routed to "product-owner"
    And Jordan should receive a tracking ID
    And the work chunk should be marked as "blocked"

  @mvp-p0 @critical
  Scenario: Question is routed based on content
    Given routing rules:
      | keyword_pattern  | route_to        | priority |
      | security         | security-team   | high     |
      | architecture     | tech-leads      | high     |
      | feature          | product-owner   | medium   |
      | budget           | finance         | medium   |
    When Jordan asks "What are the security requirements for API auth?"
    Then the question should be routed to "security-team"
    And the priority should be "high"

  @mvp-p0
  Scenario: Non-blocking question for additional context
    Given Jordan is exploring options and has a clarifying question
    When Jordan asks a non-blocking question:
      | field       | value                                          |
      | question    | Are there preferred libraries for data viz?    |
      | blocking    | false                                          |
    Then a question ticket should be created with normal priority
    And Jordan should be able to continue working
    And the work chunk should remain "active"

  # ===========================================================================
  # Answering Questions - MVP-P0
  # ===========================================================================
  # Business Rule: Answers are provided through the system, creating a
  # documented record. Answers become part of the knowledge base.

  @mvp-p0 @critical
  Scenario: Expert answers a blocking question
    Given a pending question "Should we include trial users in churn?"
    And the question is assigned to Sam (Product Owner)
    When Sam answers:
      """
      No, exclude trial users from churn calculation. They have different
      expectations and including them would skew our retention metrics.
      For trial conversion metrics, use a separate analysis.
      """
    Then the question should be marked as "answered"
    And Jordan should be notified immediately
    And Jordan's work chunk should be unblocked
    And the answer should be saved to the knowledge base

  @mvp-p0
  Scenario: Answer includes actionable guidance
    When Sam provides an answer
    Then Jordan should see:
      | section         | content                                    |
      | answer          | The expert's response                      |
      | answered_by     | Sam (Product Owner)                        |
      | answered_at     | 2024-01-15 14:30:00                        |
      | next_steps      | Any recommended actions                    |
    And Jordan should be able to ask follow-up questions

  @mvp-p1
  Scenario: Requesting clarification on an answer
    Given Jordan received an answer but needs more detail
    When Jordan asks a follow-up:
      """
      Thanks! Should we exclude trial users from all metrics,
      or just churn specifically?
      """
    Then the follow-up should be linked to the original question
    And Sam should be notified of the follow-up
    And the context should show the full conversation thread

  # ===========================================================================
  # Question Queue Management - MVP-P1
  # ===========================================================================
  # Business Rule: Experts see prioritized queues of questions in their domain.
  # SLAs ensure timely responses.

  @mvp-p1
  Scenario: Expert views their question queue
    Given Morgan (security-team) has 5 pending questions
    When Morgan opens their question queue
    Then questions should be sorted by:
      | priority | blocking_first | age        |
    And each question should show:
      | field           | visible |
      | question        | yes     |
      | asker           | yes     |
      | project         | yes     |
      | blocking_status | yes     |
      | age             | yes     |
      | sla_remaining   | yes     |

  @mvp-p1
  Scenario: SLA warning for aging questions
    Given a blocking question that has been pending for 3 hours
    And the SLA for blocking questions is 4 hours
    When the question approaches SLA breach
    Then the assigned expert should receive a reminder
    And the Engineering Manager should be cc'd
    And the question should be highlighted in the queue

  @mvp-p1
  Scenario: Reassigning questions
    Given a question assigned to Morgan who is unavailable
    When Alex (manager) reassigns to another security team member
    Then the new assignee should be notified
    And the reassignment should be logged
    And the original assignee should be removed

  # ===========================================================================
  # Question Priority and Escalation - MVP-P1
  # ===========================================================================
  # Business Rule: Critical questions affecting production or revenue have
  # special handling and escalation paths.

  @mvp-p1
  Scenario: Urgent question marked as production-critical
    Given Jordan discovers a potential production issue
    When Jordan asks an urgent question tagged "production-critical":
      | field       | value                                        |
      | question    | Is the payment API degradation known?        |
      | urgency     | production-critical                          |
      | blocking    | true                                         |
    Then the question should get highest priority
    And on-call personnel should be notified immediately
    And the SLA should be reduced to 30 minutes
    And a Slack/PagerDuty alert should be triggered

  @mvp-p1
  Scenario: Automatic escalation for breached SLA
    Given a blocking question has breached its 4-hour SLA
    When the escalation job runs
    Then the question should escalate to the team manager
    And a notification should include:
      | info              | value                           |
      | question_summary  | The original question           |
      | age               | 4 hours 15 minutes              |
      | original_assignee | Morgan                          |
      | impact            | Blocking Jordan's work chunk    |

  @mvp-p1
  Scenario: Manager views SLA metrics for their team
    When Alex views team question metrics
    Then they should see:
      | metric                    | value  |
      | Questions received (week) | 23     |
      | Average response time     | 2.5 hrs|
      | SLA compliance rate       | 87%    |
      | Currently pending         | 5      |
      | Blocking pending          | 2      |

  # ===========================================================================
  # Answer Quality and Feedback - MVP-P2
  # ===========================================================================
  # Business Rule: Question askers can rate answers. This helps improve
  # routing and identify expert effectiveness.

  @mvp-p2
  Scenario: Asker rates the answer helpfulness
    Given Jordan received an answer to their question
    When Jordan rates the answer:
      | rating      | 4/5 - Very helpful                   |
      | feedback    | Clear answer, could use an example   |
    Then the rating should be recorded
    And it should contribute to Sam's expert score
    And aggregate ratings should inform routing improvements

  @mvp-p2
  Scenario: Low-rated answers trigger review
    Given an answer received 1/5 rating with feedback "Didn't address my question"
    When the system processes the rating
    Then the question should be flagged for re-review
    And Sam's manager should be notified
    And Sam should see the feedback

  # ===========================================================================
  # Knowledge Base Integration - MVP-P1
  # ===========================================================================
  # Business Rule: Answered questions become searchable knowledge. Similar
  # questions should surface previous answers.

  @mvp-p1
  Scenario: Previous answer suggested for similar question
    Given a question "Should we include trial users in churn?" was answered
    When Taylor asks "Do trial conversions count in retention metrics?"
    Then the system should suggest:
      | suggestion                                          |
      | Similar question answered: "Should we include..."   |
    And Taylor can view the previous answer
    And Taylor can still ask if their question is different

  @mvp-p1
  Scenario: Converting question/answer to formal decision
    Given a significant question was answered about architecture
    When Avery reviews Q&A for knowledge capture
    Then they can convert the Q&A to a formal decision record
    And the original question context is preserved
    And it becomes searchable as a decision

  # ===========================================================================
  # Question Analytics - MVP-P2
  # ===========================================================================

  @mvp-p2
  Scenario: Identifying frequently asked topics
    When Avery views question analytics
    Then common themes should be identified:
      | topic              | count | suggested_action           |
      | Data privacy       | 15    | Create FAQ document        |
      | API authentication | 12    | Update documentation       |
      | Budget requests    | 10    | Simplify approval process  |

  @mvp-p2
  Scenario: Measuring question impact on productivity
    Given questions that blocked work
    When the system analyzes productivity impact
    Then reports should show:
      | metric                        | value      |
      | Total blocking time           | 45 hours   |
      | Average resolution time       | 3.2 hours  |
      | Productivity recovered        | 40 hours   |
      | Cost of delayed answers       | $12,000    |

  # ===========================================================================
  # Edge Cases - Post-MVP
  # ===========================================================================

  @post-mvp @wip
  Scenario: Question requires multiple experts
    Given a question spanning security and architecture
    When the system analyzes the question
    Then it should route to multiple experts:
      | expert        | aspect to address    |
      | security-team | Security implications|
      | tech-leads    | Architecture fit     |
    And the answer should be compiled from all inputs

  @post-mvp @wip
  Scenario: No available expert for question topic
    Given a question about an obscure technology with no assigned expert
    When routing fails to find an expert
    Then the question should escalate to management
    And a suggestion should be made to expand expertise coverage
    And the asker should be notified of the delay
