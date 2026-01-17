@wip @platform @observability @mvp-p1
Feature: System Observability and Monitoring
  As a DevOps Engineer
  I want comprehensive logging, metrics, and tracing for AI operations
  So that I can diagnose issues quickly and maintain system health

  As an Engineering Manager
  I want dashboards showing system performance and usage patterns
  So that I can make informed decisions about capacity and resources

  As a Security Officer
  I want all significant operations logged with context
  So that we can investigate incidents and meet audit requirements

  # ===========================================================================
  # Structured Logging - MVP-P1
  # ===========================================================================
  # Business Rule: All operations produce structured logs that can be queried,
  # aggregated, and correlated. Logs include request context for tracing.

  Background:
    Given the observability system is configured

  @mvp-p1 @critical
  Scenario: Operations produce structured log entries
    Given an AI exploration session is active
    When Jordan expands a thought
    Then a log entry should be produced with:
      | field           | value                                |
      | timestamp       | 2024-01-15T10:30:00.123Z             |
      | level           | INFO                                 |
      | service         | thought-engine                       |
      | operation       | expand_thought                       |
      | user_id         | jordan_id                            |
      | project_id      | churn-analysis                       |
      | session_id      | sess_abc123                          |
      | thought_id      | thought_xyz                          |
      | tokens_used     | 150                                  |
      | duration_ms     | 234                                  |
    And the log should be searchable by any field

  @mvp-p1
  Scenario: Errors are logged with stack traces and context
    When an AI operation fails with an error
    Then the error log should include:
      | field           | content                              |
      | level           | ERROR                                |
      | error_type      | TokenBudgetExceeded                  |
      | error_message   | Budget exhausted for project         |
      | stack_trace     | Full stack trace                     |
      | request_context | User, project, operation details     |
      | recovery_action | What user should do                  |

  @mvp-p1
  Scenario: Log levels are appropriate for different events
    Then the following log levels should be used:
      | event_type                | level  |
      | Operation completed       | INFO   |
      | Slow operation warning    | WARN   |
      | Recoverable error         | WARN   |
      | Failed operation          | ERROR  |
      | System critical failure   | ERROR  |
      | Debug information         | DEBUG  |

  # ===========================================================================
  # Metrics Collection - MVP-P1
  # ===========================================================================
  # Business Rule: Key performance indicators are collected as metrics that
  # can be graphed, alerted on, and used for capacity planning.

  @mvp-p1 @critical
  Scenario: Core operation metrics are tracked
    Given operations are being performed
    Then the following metrics should be recorded:
      | metric                          | type      | labels                    |
      | thought_expansions_total        | counter   | project, user             |
      | tokens_consumed_total           | counter   | project, operation_type   |
      | search_duration_seconds         | histogram | search_type               |
      | active_sessions                 | gauge     | project                   |
      | pending_approvals               | gauge     | policy_type               |

  @mvp-p1
  Scenario: Response time percentiles are tracked
    Given 1000 search operations have been performed
    When Casey views response time metrics
    Then percentile data should be available:
      | percentile | value    |
      | p50        | 150ms    |
      | p90        | 400ms    |
      | p99        | 950ms    |
    And trends should be visible over time

  @mvp-p1
  Scenario: Error rates are tracked per operation type
    When some operations succeed and others fail
    Then error rate metrics should show:
      | operation           | success_rate |
      | thought_expansion   | 99.2%        |
      | search              | 98.5%        |
      | approval_check      | 99.9%        |
    And error spikes should trigger alerts

  # ===========================================================================
  # Distributed Tracing - MVP-P1
  # ===========================================================================
  # Business Rule: Complex operations span multiple services. Traces allow
  # following a request across all services for debugging.

  @mvp-p1 @critical
  Scenario: Request is traced across service boundaries
    Given a user request triggers multiple service calls
    When the request flows through:
      | service           | operation                |
      | api-gateway       | receive_request          |
      | thought-engine    | expand_thought           |
      | llm-service       | generate_children        |
      | resource-service  | check_budget             |
    Then a single trace should connect all spans
    And each span should show its duration
    And the trace ID should be consistent across all logs

  @mvp-p1
  Scenario: Trace shows parent-child relationships
    Given an expansion triggers LLM and evaluation calls
    When Casey views the trace
    Then the span hierarchy should be visible:
      """
      expand_thought (root) - 500ms
      ├── check_budget - 10ms
      ├── generate_llm_prompt - 5ms
      ├── call_llm - 400ms
      ├── parse_response - 15ms
      └── evaluate_children - 60ms
          ├── evaluate_child_1 - 18ms
          ├── evaluate_child_2 - 20ms
          └── evaluate_child_3 - 22ms
      """

  @mvp-p1
  Scenario: Slow spans are highlighted
    Given a trace with a slow service call
    When the LLM call takes 5 seconds (above threshold)
    Then the span should be flagged as slow
    And it should appear in slow query reports
    And similar slow traces should be grouped

  # ===========================================================================
  # Dashboards and Visualization - MVP-P2
  # ===========================================================================
  # Business Rule: Key metrics are visualized in dashboards for different
  # stakeholder needs.

  @mvp-p2
  Scenario: DevOps views system health dashboard
    When Casey opens the system health dashboard
    Then they should see:
      | panel                    | content                         |
      | Request Rate             | Requests per second, trending   |
      | Error Rate               | Errors per second, by type      |
      | Response Time            | p50, p90, p99 latencies         |
      | Active Sessions          | Current concurrent sessions     |
      | Token Consumption        | Tokens per minute               |
      | Service Health           | Up/Down status per service      |

  @mvp-p2
  Scenario: Engineering Manager views usage dashboard
    When Alex opens the usage dashboard
    Then they should see:
      | panel                    | content                         |
      | Usage by Team            | Token consumption per team      |
      | Usage by Project         | Token consumption per project   |
      | Active Users             | Concurrent users over time      |
      | Feature Usage            | Which features are used most    |
      | Question Response Time   | Average answer time             |

  # ===========================================================================
  # Alerting - MVP-P1
  # ===========================================================================
  # Business Rule: When metrics exceed thresholds, appropriate teams are
  # alerted through configured channels.

  @mvp-p1
  Scenario: Alert fires when error rate exceeds threshold
    Given an alert rule for error rate > 5%
    When the error rate reaches 7%
    Then an alert should be triggered
    And the on-call engineer should be notified
    And the alert should include:
      | field           | value                              |
      | severity        | warning                            |
      | metric          | error_rate                         |
      | current_value   | 7%                                 |
      | threshold       | 5%                                 |
      | affected_service| thought-engine                     |
      | runbook_link    | Link to troubleshooting guide      |

  @mvp-p1
  Scenario: Alert channels based on severity
    Then alerts should route to:
      | severity  | channels                           |
      | info      | dashboard, email                   |
      | warning   | dashboard, email, slack            |
      | critical  | dashboard, email, slack, pagerduty |

  @mvp-p1
  Scenario: Alert includes actionable context
    When a "budget_exhausted" alert fires
    Then the alert should include:
      | context                  | purpose                           |
      | affected_project         | Which project hit the limit       |
      | current_usage            | How much was consumed             |
      | budget_limit             | What the limit was                |
      | last_operations          | Recent operations consuming budget|
      | suggested_action         | Request budget increase           |

  # ===========================================================================
  # Audit Logging for Compliance - MVP-P0
  # ===========================================================================
  # Business Rule: Security-relevant events are logged in a tamper-evident
  # audit trail for compliance requirements.

  @mvp-p0 @critical
  Scenario: Security events are audit logged
    Then the following events should be audit logged:
      | event_type                | required_fields                    |
      | user_login                | user, ip, timestamp, success       |
      | permission_change         | user, target, old_perms, new_perms |
      | approval_decision         | approver, action, decision, target |
      | policy_change             | admin, policy, old_value, new_value|
      | data_export               | user, data_type, destination       |
    And audit logs should be immutable
    And audit logs should be retained per policy

  @mvp-p0
  Scenario: Audit log integrity verification
    Given audit logs for the past month
    When Riley runs integrity verification
    Then the system should confirm logs are untampered
    And any gaps should be flagged
    And a verification report should be generated

  # ===========================================================================
  # Log Retention and Search - MVP-P1
  # ===========================================================================

  @mvp-p1
  Scenario: Searching logs for incident investigation
    Given an incident affecting project "production-api"
    When Casey searches logs for:
      | filter         | value                    |
      | project_id     | production-api           |
      | time_range     | last_6_hours             |
      | level          | ERROR, WARN              |
    Then matching logs should be returned
    And they should be sorted by timestamp
    And related traces should be linked

  @mvp-p1
  Scenario: Log retention policies are enforced
    Given log retention policy of 90 days for standard logs
    And 7 years for audit logs
    When the retention job runs
    Then logs older than 90 days should be archived
    But audit logs should be retained for 7 years
    And storage costs should be optimized

  # ===========================================================================
  # Edge Cases - Post-MVP
  # ===========================================================================

  @post-mvp @wip
  Scenario: High-cardinality label handling
    Given a metric with user_id as a label
    And 10,000 unique users
    When the metric is queried
    Then cardinality should be managed efficiently
    And queries should complete in reasonable time

  @post-mvp @wip
  Scenario: Log aggregation during high volume
    Given 10,000 log entries per second
    When the system is under high load
    Then logs should not be dropped
    And system performance should not degrade
    And sampling should be applied if necessary
