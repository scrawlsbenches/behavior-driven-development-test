@services @governance @high
Feature: Governance Service
  As a developer using Graph of Thought
  I want a governance service to manage approvals and policies
  So that I can control what actions are allowed in my application

  # The governance service handles approval workflows, audit trails,
  # and policy enforcement for your application.

  # ===========================================================================
  # In-Memory Governance Service (For Testing)
  # ===========================================================================

  Scenario: In-memory governance service auto-approves all actions
    Given an in-memory governance service
    When I check approval for action "deploy_production"
    Then the approval status should be "APPROVED"

  # ===========================================================================
  # Simple Governance Service
  # ===========================================================================

  Scenario: Simple governance service checks policies
    Given a simple governance service
    And a policy "deploy_production" requires review
    When I check approval for action "deploy_production"
    Then the approval status should be "NEEDS_REVIEW"

  Scenario: Simple governance service approves undefined actions
    Given a simple governance service
    When I check approval for action "minor_change"
    Then the approval status should be "APPROVED"

  Scenario: Simple governance service records audit events
    Given a simple governance service
    When I record an audit event for action "test_action" by actor "user1"
    Then the audit log should have 1 entry
    And the audit entry should have actor "user1"

  Scenario: Simple governance service handles approval workflow
    Given a simple governance service
    When I request approval for action "deploy" with justification "Hotfix needed"
    Then an approval ID should be returned
    When the approval is granted by "admin"
    Then the pending approval status should be "approved"

  # ===========================================================================
  # Future Capabilities
  # ===========================================================================

  @wip
  Scenario: Pending approval expires after timeout
    Given a simple governance service
    And an approval timeout of 1 hour
    When I request approval for action "deploy" with justification "Needed"
    And 2 hours pass without approval
    Then the pending approval status should be "expired"

  @wip
  Scenario: Unapproved request escalates to higher authority
    Given a simple governance service
    And an escalation policy after 30 minutes to "senior-admin"
    When I request approval for action "deploy" with justification "Critical"
    And 45 minutes pass without approval
    Then the request should be escalated to "senior-admin"

  # ===========================================================================
  # Known Limitations (Escape Clauses)
  # ===========================================================================
  # ESCAPE CLAUSE: Rule-based, not workflow-based.
  # Current: Policies are simple allow/deny/review rules checked synchronously.
  # Requires: Workflow engine for multi-step approvals, escalation, timeouts.
  #
  # ESCAPE CLAUSE: Callable policies not fully implemented.
  # Current: Callable policies exist but aren't invoked with full context.
  # Requires: Pass action context, actor info, and environment to callables.
  #
  # ESCAPE CLAUSE: Policy format is undefined.
  # Current: Returns raw dicts from get_policies().
  # Requires: Define PolicyDefinition dataclass with validation.
