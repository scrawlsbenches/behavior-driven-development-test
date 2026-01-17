@services @governance @high
Feature: Governance Service
  As a developer using Graph of Thought
  I want a governance service to manage approvals and policies
  So that I can control what actions are allowed in my application

  # ===========================================================================
  # TERMINOLOGY
  # ===========================================================================
  # This feature tests TWO implementations:
  #
  # 1. IN-MEMORY GOVERNANCE SERVICE (test double)
  #    - Auto-approves everything (always returns APPROVED)
  #    - Use when you need isolated tests without governance logic
  #
  # 2. SIMPLE GOVERNANCE SERVICE (lightweight implementation)
  #    - Enforces policies, records audits, manages approvals
  #    - Use when testing actual governance behavior
  #
  # APPROVAL STATUSES (from check_approval):
  #   - "APPROVED": Action is allowed to proceed immediately
  #   - "NEEDS_REVIEW": Action requires human approval before proceeding
  #   - "DENIED": Action is explicitly forbidden by policy
  #
  # PENDING APPROVAL STATUSES (from approval workflow):
  #   - "pending": Awaiting approver decision
  #   - "approved": Approver granted the request
  #   - "denied": Approver rejected the request
  #   - "expired": Request timed out without decision (future)
  #
  # POLICY TYPES:
  #   - "requires_review": Returns NEEDS_REVIEW, triggers approval workflow
  #   - "deny": Returns DENIED, blocks the action
  #   - "allow": Returns APPROVED (explicit allow, same as no policy)

  # ===========================================================================
  # In-Memory Governance Service (Test Double)
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

  @wip
  Scenario: Callable policy receives full context
    Given a simple governance service
    And a callable policy for action "deploy" that checks actor role
    When actor "developer" checks approval for action "deploy" on resource "production"
    Then the callable should receive action context including resource "production"
    And the callable should receive actor info including role "developer"
    And the callable should receive environment variables

  @wip
  Scenario: Policy definitions are validated on registration
    Given a simple governance service
    When I register a policy with invalid structure
    Then a validation error should be raised
    And the error should specify which fields are invalid

  @wip
  Scenario: Policies can be exported in structured format
    Given a simple governance service
    And a policy "deploy_production" requires review
    And a policy "minor_change" allows all
    When I export all policies
    Then each policy should have name, type, conditions, and actions
    And the export should be valid PolicyDefinition format

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
