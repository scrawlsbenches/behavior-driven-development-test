@cost-management @mvp-p0
Feature: Token Budget and Consumption Management
  As a Finance Administrator
  I want to allocate and track AI token budgets across teams and projects
  So that we can control costs, forecast accurately, and optimize spending

  As an Engineering Manager
  I want visibility into my team's token consumption
  So that projects stay within budget and I can plan resource allocation

  As a Data Scientist
  I want to know my remaining budget during work
  So that I can pace my exploration and avoid running out mid-analysis

  # ===========================================================================
  # Budget Allocation - MVP-P0
  # ===========================================================================
  # Business Rule: Every project must have an explicit token budget before work
  # can begin. Budgets can be set at project, team, or organizational level.

  @mvp-p0 @critical
  Scenario: Finance Administrator allocates quarterly budget to team
    Given Drew is logged in as Finance Administrator
    When Drew allocates 500000 tokens to "Data Science Team" for Q1 2024
    Then the team budget should be set to 500000 tokens
    And an allocation record should be created
    And the team's Engineering Manager should be notified
    And the budget should appear in cost dashboards

  @mvp-p0 @critical
  Scenario: Engineering Manager allocates team budget to project
    Given "Data Science Team" has 500000 tokens for the quarter
    When Alex allocates 100000 tokens to project "Churn Analysis"
    Then the project budget should be 100000 tokens
    And the team's remaining unallocated budget should be 400000
    And project members should see their available budget

  @mvp-p0
  Scenario: Viewing budget hierarchy
    Given budgets allocated as:
      | level        | name              | budget  | used   |
      | organization | Acme Corp Q1      | 2000000 | 800000 |
      | team         | Data Science      | 500000  | 200000 |
      | project      | Churn Analysis    | 100000  | 45000  |
    When Drew views the budget hierarchy
    Then all levels should be displayed with usage
    And rollup calculations should be accurate
    And each level should show percentage consumed

  # ===========================================================================
  # Consumption Tracking - MVP-P0
  # ===========================================================================
  # Business Rule: Every AI operation consumes tokens, which must be tracked
  # against the appropriate budget. Consumption is attributed to project, user,
  # and work chunk for full accountability.

  @mvp-p0 @critical
  Scenario: Token consumption recorded for AI operation
    Given Jordan is working on project "Churn Analysis"
    And the project has 100000 tokens remaining
    When Jordan's AI request consumes 500 tokens
    Then 500 tokens should be deducted from the project budget
    And 99500 tokens should remain
    And the consumption should be recorded with:
      | attribute    | value                          |
      | project      | Churn Analysis                 |
      | user         | Jordan                         |
      | chunk        | Usage pattern analysis         |
      | operation    | thought_expansion              |
      | timestamp    | 2024-01-15T10:30:00Z           |

  @mvp-p0
  Scenario: Viewing current budget status during work
    Given Jordan is working with 55000 tokens remaining
    And has used 45000 tokens today
    When Jordan checks budget status
    Then they should see:
      | metric              | value                      |
      | remaining           | 55000 tokens               |
      | used_today          | 45000 tokens               |
      | daily_average       | 15000 tokens               |
      | days_at_pace        | 3.7 days                   |
      | project_percent     | 45% consumed               |

  @mvp-p1 @wip @wip
  Scenario: Consumption report for project review
    Given project "Churn Analysis" has been running for 2 weeks
    When Alex requests a consumption report
    Then the report should include:
      | section              | content                               |
      | by_user              | Tokens consumed by each team member   |
      | by_work_chunk        | Tokens consumed by each work session  |
      | by_operation         | Breakdown by operation type           |
      | daily_trend          | Day-over-day consumption pattern      |
      | top_consumers        | Most expensive operations             |
    And recommendations for optimization should be included

  # ===========================================================================
  # Budget Warnings and Limits - MVP-P0
  # ===========================================================================
  # Business Rule: Users should be warned before exhausting their budget.
  # Hard limits prevent work from continuing without explicit approval.

  @mvp-p0 @critical
  Scenario: Warning when approaching budget threshold
    Given project "Analysis" with 100000 token budget
    And 80% consumption warning threshold
    When consumption reaches 80000 tokens
    Then Jordan should see a budget warning
    And the warning should say "20000 tokens (20%) remaining"
    And the Engineering Manager should be notified
    And work should be allowed to continue

  @mvp-p0 @critical
  Scenario: Hard stop when budget is exhausted
    Given project "Analysis" with only 100 tokens remaining
    When Jordan's request would consume 500 tokens
    Then the request should be blocked
    And Jordan should see "Budget exhausted. Request budget increase to continue."
    And a budget increase request form should be offered
    And the blocked attempt should be logged

  @mvp-p1 @wip @wip
  Scenario: Configurable warning thresholds
    Given Alex configures project warnings at 75% and 90%
    Then alerts should trigger at:
      | threshold | action                                      |
      | 75%       | Email notification to team                  |
      | 90%       | Dashboard warning + manager notification    |
      | 100%      | Hard stop + require budget increase         |

  @mvp-p1 @wip @wip
  Scenario: Emergency budget extension for critical work
    Given project "Production Incident" has exhausted its budget
    And Casey needs to continue debugging
    When Alex approves an emergency extension of 10000 tokens
    Then the budget should increase by 10000
    And the extension should be flagged as "emergency"
    And an audit record should capture the approval
    And work should resume immediately

  # ===========================================================================
  # Cost Forecasting - MVP-P1
  # ===========================================================================
  # Business Rule: Teams need to predict when budgets will be exhausted
  # and plan future allocations based on historical consumption patterns.

  @mvp-p1 @wip @wip
  Scenario: Predicting budget exhaustion date
    Given project "Analysis" consuming 5000 tokens daily on average
    And 50000 tokens remaining
    When Jordan views budget forecast
    Then predicted exhaustion should be in 10 days
    And a confidence interval should be shown
    And comparison to project deadline should be highlighted

  @mvp-p1 @wip @wip
  Scenario: Quarterly cost forecasting for team
    Given Data Science team's historical consumption:
      | month     | tokens_used |
      | October   | 150000      |
      | November  | 180000      |
      | December  | 165000      |
    When Drew forecasts Q1 needs
    Then predicted Q1 consumption should be approximately 500000
    And seasonal factors should be considered
    And the forecast should include uncertainty bounds

  @mvp-p2 @wip @wip
  Scenario: Cost optimization recommendations
    Given a project with usage patterns showing inefficiencies
    When the system analyzes consumption
    Then recommendations should include:
      | recommendation                        | estimated_savings |
      | Increase cache TTL to reduce re-calls | 15000 tokens     |
      | Batch similar expansions              | 8000 tokens      |
      | Use smaller model for initial scoring | 12000 tokens     |

  # ===========================================================================
  # Budget Governance - MVP-P1
  # ===========================================================================
  # Business Rule: Budget increases require appropriate approval based on
  # amount and organizational policies.

  @mvp-p1 @wip @wip
  Scenario: Requesting budget increase
    Given project "Analysis" needs additional 50000 tokens
    When Jordan submits a budget increase request with justification:
      """
      Discovery: Customer segments require separate analysis.
      Need additional tokens to complete segment-specific models.
      Expected ROI: Findings will inform $2M retention campaign.
      """
    Then the request should be routed to Alex for approval
    And Alex should see the request with full context
    And a notification should be sent

  @mvp-p1 @wip @wip
  Scenario: Approving budget increase
    Given a pending budget request for 50000 tokens
    When Alex approves the request
    Then the project budget should increase by 50000
    And an audit record should capture:
      | field           | value                          |
      | requested_by    | Jordan                         |
      | approved_by     | Alex                           |
      | amount          | 50000                          |
      | justification   | Segment analysis requirement   |
    And Jordan should be notified of approval

  @mvp-p1 @wip @wip
  Scenario: Large budget requests require Finance approval
    Given a budget increase request for 200000 tokens
    And organizational policy requiring Finance approval above 100000
    When Alex approves the request
    Then the request should escalate to Drew
    And Drew should see Alex's endorsement
    And final approval should come from Drew

  # ===========================================================================
  # Cost Attribution and Chargeback - MVP-P2
  # ===========================================================================

  @mvp-p2 @wip @wip
  Scenario: Monthly cost report for department chargeback
    Given multiple teams have consumed tokens in January:
      | team            | tokens    | cost_rate | total_cost |
      | Data Science    | 450000    | $0.01     | $4,500     |
      | Engineering     | 280000    | $0.01     | $2,800     |
      | Product         | 120000    | $0.01     | $1,200     |
    When Finance generates January chargeback report
    Then costs should be attributed by team
    And the report should be exportable to accounting systems
    And each team's manager should receive their summary

  @mvp-p2 @wip @wip
  Scenario: Cost attribution by client project
    Given a consulting engagement using AI capabilities
    When tokens are consumed on client project "Acme Consulting"
    Then costs should be tagged for client billing
    And they should appear on the client invoice
    And internal costs should be tracked separately

  # ===========================================================================
  # Resource Limits Beyond Tokens - MVP-P2
  # ===========================================================================

  @mvp-p2 @wip @wip
  Scenario: Limiting concurrent AI sessions
    Given team policy of maximum 5 concurrent sessions
    When a 6th team member tries to start an AI session
    Then the session should be queued
    And they should see "Queue position: 1. Estimated wait: 5 minutes"
    And they should have option to request priority

  @mvp-p2 @wip @wip
  Scenario: Rate limiting requests per minute
    Given a rate limit of 20 requests per minute
    When Jordan exceeds 20 requests in 60 seconds
    Then subsequent requests should be delayed
    And Jordan should see "Rate limit reached. Resuming in 30 seconds"
    And the delay should not count against work time

  # ===========================================================================
  # Edge Cases - Post-MVP
  # ===========================================================================

  @post-mvp @wip
  Scenario: Handling budget during service outage
    Given an AI service outage lasting 2 hours
    And work chunks that were interrupted
    When service is restored
    Then incomplete operations should be retried
    And tokens should not be double-charged
    And affected time should be credited if applicable

  @post-mvp @wip
  Scenario: Budget rollover at period end
    Given team has 50000 unused tokens at quarter end
    And a rollover policy allowing 20% carryover
    When the new quarter begins
    Then 10000 tokens should carry over
    And 40000 tokens should expire
    And the new quarter allocation should be added
