@governance @compliance @mvp-p0
Feature: Approval Workflows and Policy Enforcement
  As a Security Officer
  I want all sensitive AI operations to require documented approval
  So that we maintain SOC2 compliance and can demonstrate due diligence during audits

  As a Compliance Auditor
  I want a complete audit trail of all approvals and policy decisions
  So that I can verify proper governance during regulatory reviews

  As an Engineering Manager
  I want visibility into pending approvals affecting my team
  So that deployments aren't blocked by unknown approval bottlenecks

  # ===========================================================================
  # Policy Definition and Management - MVP-P0
  # ===========================================================================
  # Business Rule: Policies define which actions require approval, who can approve,
  # and under what conditions. Policies are version-controlled and auditable.

  Background:
    Given the organization has configured governance policies

  @mvp-p0 @critical
  Scenario: Security Officer defines approval policy for production changes
    Given Morgan is logged in as Security Officer
    When Morgan creates a policy for "production_deployment":
      | field                | value                                    |
      | action               | production_deployment                    |
      | requires_approval    | true                                     |
      | approvers            | tech-lead, security-team                 |
      | approval_type        | all_required                             |
      | auto_expire_hours    | 24                                       |
    Then the policy should be saved and active
    And any production deployment should now require approval
    And the policy should be version-tracked

  @mvp-p0 @critical
  Scenario: Policy automatically blocks unapproved sensitive actions
    Given a policy requiring approval for "external_api_call"
    When Casey tries to make an external API call without approval
    Then the action should be blocked
    And the response should indicate "Requires approval from: api-security-team"
    And an approval request should be automatically created
    And Casey should be able to track the approval status

  @mvp-p0
  Scenario: Viewing active policies
    Given multiple governance policies are configured
    When Morgan views the policy dashboard
    Then all policies should be listed with:
      | policy                    | status  | last_modified | applied_count |
      | production_deployment     | active  | 2024-01-10    | 47            |
      | external_api_call         | active  | 2024-01-08    | 23            |
      | budget_override           | active  | 2024-01-05    | 8             |
    And each policy should show its approval requirements

  # ===========================================================================
  # Approval Request Workflow - MVP-P0
  # ===========================================================================
  # Business Rule: When an action requires approval, a request is created with
  # full context. Approvers can approve, deny, or request more information.

  @mvp-p0 @critical
  Scenario: Engineer submits action requiring approval
    Given Casey needs to deploy to production
    When Casey submits a deployment request with:
      | field           | value                                         |
      | action          | production_deployment                         |
      | target          | payment-service v2.3.1                        |
      | justification   | Critical bug fix for payment processing       |
      | risk_assessment | Low - only affects error handling path        |
    Then an approval request should be created
    And it should be routed to "tech-lead" and "security-team"
    And Casey should receive confirmation with tracking ID
    And approvers should receive notification

  @mvp-p0 @critical
  Scenario: Approver reviews and approves request
    Given a pending approval request from Casey for production deployment
    When Alex (tech-lead) reviews the request
    Then Alex should see:
      | section             | content                                    |
      | requestor           | Casey                                      |
      | action              | production_deployment                      |
      | target              | payment-service v2.3.1                     |
      | justification       | Critical bug fix for payment processing    |
      | risk_assessment     | Low - only affects error handling path     |
      | related_changes     | [Links to commits, PRs]                    |

    When Alex approves with comment "Reviewed code, approve for deployment"
    Then the approval should be recorded
    And if all required approvers have approved
    Then Casey should be notified "Approved - you may proceed"
    And the action should be unblocked

  @mvp-p0
  Scenario: Approver denies request with reason
    Given a pending approval request for external API integration
    When Morgan reviews and denies with reason:
      """
      Security review found PII exposure risk. Please:
      1. Add data masking for user emails
      2. Implement rate limiting
      3. Add audit logging for all external calls
      Resubmit after addressing these concerns.
      """
    Then the request should be marked as "denied"
    And Casey should receive the detailed feedback
    And the denial reason should be preserved in audit log
    And Casey should be able to submit a new request addressing concerns

  @mvp-p1 @wip
  Scenario: Approval request times out
    Given an approval request pending for 24 hours
    And a policy with 24-hour expiration
    When the timeout is reached
    Then the request should be marked as "expired"
    And the requestor should be notified
    And they should be able to resubmit
    And expiration should be logged in audit trail

  # ===========================================================================
  # Multi-Approver Workflows - MVP-P1
  # ===========================================================================
  # Business Rule: Some actions require approval from multiple parties.
  # Policies can specify "all required" or "any one" approval types.

  @mvp-p1 @wip
  Scenario: Action requiring approval from all specified parties
    Given a policy for "major_architecture_change" requiring all of:
      | approver          | role                  |
      | tech-lead         | Technical leadership  |
      | security-team     | Security review       |
      | product-owner     | Business alignment    |
    When Casey submits an architecture change request
    Then approvals should be required from all three parties
    And the action should remain blocked until all approve
    And partial approval status should be visible

  @mvp-p1 @wip
  Scenario: Tracking partial approvals
    Given a request requiring approval from tech-lead, security, and product
    And tech-lead has approved
    When Casey checks request status
    Then they should see:
      | approver      | status   | timestamp             | comment              |
      | tech-lead     | approved | 2024-01-15 10:30:00   | LGTM                 |
      | security-team | pending  |                       |                      |
      | product-owner | pending  |                       |                      |

  @mvp-p1 @wip
  Scenario: Action requiring any one approver
    Given a policy for "config_change" requiring any one of:
      | approver          |
      | tech-lead         |
      | senior-engineer   |
    When any one approver approves
    Then the action should be unblocked
    And other pending approvals should be cancelled
    And the approving party should be recorded

  # ===========================================================================
  # Audit Logging - MVP-P0
  # ===========================================================================
  # Business Rule: Every governance-related action must be logged with full
  # context for compliance audits. Logs are tamper-evident and retained per policy.

  @mvp-p0 @critical
  Scenario: All approval decisions are logged
    Given Morgan approves a sensitive action
    Then an audit record should be created with:
      | field           | value                                    |
      | timestamp       | 2024-01-15T14:30:00Z                     |
      | action_type     | approval_decision                        |
      | actor           | Morgan                                   |
      | actor_role      | security-officer                         |
      | decision        | approved                                 |
      | target          | external_api_integration                 |
      | context         | [Full request details]                   |
      | ip_address      | 10.0.1.45                                |
      | session_id      | sess_abc123                              |
    And the record should be immutable

  @mvp-p0
  Scenario: Viewing audit history for compliance review
    Given Riley (Compliance Auditor) needs to review Q4 approvals
    When Riley queries the audit log for:
      | parameter      | value                    |
      | date_range     | 2023-10-01 to 2023-12-31 |
      | action_types   | approval_decision        |
      | policy         | production_deployment    |
    Then all matching records should be returned
    And they should include complete decision context
    And the query itself should be logged for audit

  @mvp-p1 @wip
  Scenario: Audit log retention and archival
    Given audit logs older than 7 years
    When the retention job runs
    Then logs older than 7 years should be archived to cold storage
    And they should remain queryable with longer retrieval time
    And the archival action should be logged

  # ===========================================================================
  # Policy Violation Handling - MVP-P1
  # ===========================================================================
  # Business Rule: When policies are violated (intentionally or accidentally),
  # appropriate stakeholders must be notified and incidents tracked.

  @mvp-p1 @wip
  Scenario: Detecting and reporting policy bypass attempt
    Given a policy blocking direct database access
    When Casey attempts direct database modification
    Then the attempt should be blocked
    And an incident should be created
    And Morgan (Security Officer) should receive immediate alert
    And the incident should include:
      | field           | value                              |
      | severity        | high                               |
      | actor           | Casey                              |
      | attempted_action| direct_database_modification       |
      | policy_violated | no_direct_db_access                |
      | outcome         | blocked                            |

  @mvp-p1 @wip
  Scenario: Policy exception request
    Given a policy blocks an action Casey legitimately needs
    When Casey requests a policy exception with justification
    Then Morgan should receive the exception request
    And Morgan can grant a time-limited exception
    And the exception should be logged with:
      | field           | value                              |
      | exception_type  | temporary                          |
      | valid_until     | 2024-01-16T18:00:00Z               |
      | granted_by      | Morgan                             |
      | justification   | Emergency production fix           |

  # ===========================================================================
  # Compliance Reporting - MVP-P1
  # ===========================================================================
  # Business Rule: The system must generate reports demonstrating compliance
  # with relevant frameworks (SOC2, GDPR, HIPAA, etc.)

  @mvp-p1 @wip
  Scenario: Generating SOC2 compliance report
    Given audit data for Q4 2023
    When Riley requests a SOC2 access control report
    Then the report should include:
      | section                          | content                         |
      | approval_coverage                | 100% of sensitive actions       |
      | approval_timeliness              | 95% approved within SLA         |
      | policy_violations                | 3 blocked, 0 successful bypasses|
      | access_reviews                   | Quarterly reviews completed     |
    And the report should be exportable as PDF
    And evidence links should be included

  @mvp-p2 @wip
  Scenario: Continuous compliance monitoring dashboard
    Given real-time governance data
    When Morgan views the compliance dashboard
    Then they should see:
      | metric                    | value  | status |
      | Pending approvals         | 5      | normal |
      | Approval SLA breaches     | 0      | good   |
      | Policy violations (24h)   | 1      | warning|
      | Audit log integrity       | passed | good   |
    And anomalies should be highlighted

  # ===========================================================================
  # Role-Based Access Control - MVP-P1
  # ===========================================================================
  # Business Rule: Users have roles that determine their permissions.
  # Roles are assigned by administrators and tracked in audit logs.

  @mvp-p1 @wip
  Scenario: Role determines what actions user can perform
    Given the following role permissions:
      | role            | can_approve | can_deploy | can_modify_policy |
      | developer       | no          | no         | no                |
      | senior-engineer | no          | yes        | no                |
      | tech-lead       | yes         | yes        | no                |
      | security-officer| yes         | no         | yes               |
    When Casey (developer) tries to approve a request
    Then the action should be denied
    And they should see "You don't have permission to approve"

  @mvp-p1 @wip
  Scenario: Assigning roles to users
    Given Alex is a platform administrator
    When Alex assigns "tech-lead" role to Casey
    Then Casey should have tech-lead permissions
    And the role assignment should be logged
    And Casey should be notified of their new role

  @mvp-p2 @wip
  Scenario: Role escalation for emergency situations
    Given Casey needs temporary elevated permissions for incident response
    When Alex grants temporary "admin" role for 4 hours
    Then Casey should have elevated permissions
    And a timer should track the temporary grant
    And permissions should auto-revoke after 4 hours
    And all actions during elevation should be specially flagged in audit log

  # ===========================================================================
  # Multi-Tenancy Governance - MVP-P2
  # ===========================================================================

  @mvp-p2 @wip
  Scenario: Tenant-specific policies
    Given tenants "AcmeCorp" and "GlobalInc" with different compliance needs
    When AcmeCorp requires HIPAA compliance
    And GlobalInc requires SOC2 only
    Then each tenant should have tenant-specific policies
    And policy changes should only affect their own tenant
    And cross-tenant access should be blocked

  # ===========================================================================
  # Edge Cases - Post-MVP
  # ===========================================================================

  @post-mvp @wip
  Scenario: Handling approval during approver unavailability
    Given a request pending with only one approver available
    And that approver is on vacation
    When the request approaches SLA breach
    Then an escalation should trigger to backup approvers
    And the original approver's manager should be notified
    And SLA should account for business hours only

  @post-mvp @wip
  Scenario: Bulk approval for similar requests
    Given 10 similar configuration change requests
    When a tech-lead selects all for bulk review
    Then they should be able to approve all at once
    And each individual approval should still be logged
    And any exceptions should be flagged for individual review
