"""
Governance - Approval Workflows and Compliance
==============================================

Governance policies control what operations are allowed and what
oversight they require. This is where compliance, approval workflows,
and audit requirements live.

GOVERNANCE IS NOT ENFORCEMENT
-----------------------------

Governance policies CHECK rules, they don't ENFORCE them:

    policy = GovernancePolicy(rules)
    if policy.requires_approval(context, operation):
        await request_approval()  # Application handles this
    else:
        await execute_operation()

The application decides what to do when approval is required.

RULE TYPES
----------

APPROVAL REQUIREMENTS:
    "Operations costing >$100 need manager approval"
    "Production changes need two approvers"

AUDIT REQUIREMENTS:
    "Log all operations with cost >$10"
    "Record who approved each change"

COMPLIANCE REQUIREMENTS:
    "SOC2: All data access must be logged"
    "HIPAA: PHI access requires explicit consent"

WHY GOVERNANCE AS POLICY, NOT MIDDLEWARE
----------------------------------------

Middleware is fire-and-forget: log, then continue.
Governance may BLOCK: wait for approval, then continue.

Middleware can't:
- Wait for async human approval
- Block operations indefinitely
- Manage multi-step approval flows

Policy allows the application to handle these cases appropriately.

EXAMPLE WORKFLOW
----------------

1. Operation requested
2. Governance checks rules:
   - Cost: $150 (threshold: $100) → needs approval
   - Type: search (no special rules) → no approval
   - Combined: approval required from manager
3. Application creates approval request
4. Manager receives notification
5. Manager approves (or rejects)
6. Application continues (or aborts)
7. Audit trail records the full flow

"""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum, auto

from graph_of_thought_v2.context import Context


# =============================================================================
# ENUMS
# =============================================================================

class ApprovalStatus(Enum):
    """Status of an approval request."""
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()
    EXPIRED = auto()


class OperationType(Enum):
    """Types of operations that might need governance."""
    SEARCH = auto()
    EXPAND = auto()
    PERSIST = auto()
    DELETE = auto()
    EXPORT = auto()


# =============================================================================
# REQUIREMENTS
# =============================================================================

@dataclass
class ApprovalRequirement:
    """
    A rule defining when approval is required.

    Attributes:
        name: Human-readable rule name.
        condition: Function that returns True if rule applies.
        approver_roles: Roles that can approve.
        min_approvers: Minimum approvals needed.

    Example:
        # Operations over $100 need manager approval
        ApprovalRequirement(
            name="High cost approval",
            condition=lambda ctx, op: estimate_cost(ctx) > 100,
            approver_roles=["manager", "admin"],
            min_approvers=1,
        )
    """

    name: str
    """Human-readable rule name for audit trails."""

    condition: Any  # Callable[[Context, OperationType], bool]
    """Function that returns True if this rule applies."""

    approver_roles: list[str] = field(default_factory=lambda: ["admin"])
    """Roles that can approve operations matching this rule."""

    min_approvers: int = 1
    """Minimum number of approvals required."""

    def applies(self, context: Context, operation: OperationType) -> bool:
        """Check if this rule applies to the given context and operation."""
        return self.condition(context, operation)


@dataclass
class AuditRequirement:
    """
    A rule defining what must be audited.

    Attributes:
        name: Human-readable rule name.
        condition: Function that returns True if auditing required.
        fields: Context fields to include in audit log.

    Example:
        # Audit all operations with cost
        AuditRequirement(
            name="Cost audit",
            condition=lambda ctx, op: ctx.budget is not None,
            fields=["user_id", "project_id", "budget.consumed"],
        )
    """

    name: str
    """Human-readable rule name."""

    condition: Any  # Callable[[Context, OperationType], bool]
    """Function that returns True if auditing required."""

    fields: list[str] = field(default_factory=list)
    """Context fields to include in audit log."""

    def applies(self, context: Context, operation: OperationType) -> bool:
        """Check if this rule applies."""
        return self.condition(context, operation)


# =============================================================================
# GOVERNANCE POLICY
# =============================================================================

class GovernancePolicy:
    """
    Governance policy that checks rules against operations.

    Combines multiple approval and audit requirements into a coherent
    policy that can be queried.

    Example:
        policy = GovernancePolicy()
        policy.add_approval_rule(high_cost_rule)
        policy.add_audit_rule(all_operations_rule)

        if policy.requires_approval(context, OperationType.SEARCH):
            # Request approval
            requirements = policy.get_approval_requirements(context, op)
            ...

    Thread Safety:
        Policies are immutable after construction (rules are added
        during setup, not during operation). Safe to share.
    """

    def __init__(self) -> None:
        """Create an empty governance policy."""
        self._approval_rules: list[ApprovalRequirement] = []
        self._audit_rules: list[AuditRequirement] = []

    # =========================================================================
    # RULE MANAGEMENT
    # =========================================================================

    def add_approval_rule(self, rule: ApprovalRequirement) -> "GovernancePolicy":
        """
        Add an approval requirement rule.

        Args:
            rule: The approval rule to add.

        Returns:
            Self for chaining.
        """
        self._approval_rules.append(rule)
        return self

    def add_audit_rule(self, rule: AuditRequirement) -> "GovernancePolicy":
        """
        Add an audit requirement rule.

        Args:
            rule: The audit rule to add.

        Returns:
            Self for chaining.
        """
        self._audit_rules.append(rule)
        return self

    # =========================================================================
    # APPROVAL CHECKS
    # =========================================================================

    def requires_approval(
        self,
        context: Context,
        operation: OperationType,
    ) -> bool:
        """
        Check if an operation requires approval.

        Args:
            context: Execution context.
            operation: Type of operation.

        Returns:
            True if any approval rule applies.
        """
        return any(rule.applies(context, operation) for rule in self._approval_rules)

    def get_approval_requirements(
        self,
        context: Context,
        operation: OperationType,
    ) -> list[ApprovalRequirement]:
        """
        Get all approval requirements that apply.

        Args:
            context: Execution context.
            operation: Type of operation.

        Returns:
            List of applicable approval requirements.
        """
        return [rule for rule in self._approval_rules if rule.applies(context, operation)]

    # =========================================================================
    # AUDIT CHECKS
    # =========================================================================

    def requires_audit(
        self,
        context: Context,
        operation: OperationType,
    ) -> bool:
        """
        Check if an operation requires auditing.

        Args:
            context: Execution context.
            operation: Type of operation.

        Returns:
            True if any audit rule applies.
        """
        return any(rule.applies(context, operation) for rule in self._audit_rules)

    def get_audit_requirements(
        self,
        context: Context,
        operation: OperationType,
    ) -> list[AuditRequirement]:
        """
        Get all audit requirements that apply.

        Args:
            context: Execution context.
            operation: Type of operation.

        Returns:
            List of applicable audit requirements.
        """
        return [rule for rule in self._audit_rules if rule.applies(context, operation)]

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def allows(
        self,
        context: Context,
        operation: OperationType,
    ) -> bool:
        """
        Check if an operation is allowed without approval.

        This is a convenience method. An operation is "allowed" if it
        doesn't require approval. Operations requiring approval are
        not "disallowed" - they just need extra steps.

        Args:
            context: Execution context.
            operation: Type of operation.

        Returns:
            True if no approval is required.
        """
        return not self.requires_approval(context, operation)
