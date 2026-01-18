"""
Policy Layer - Business Rules and Constraints
==============================================

The policy layer contains business logic that CONSTRAINS what the
application can do. It answers questions like:

- "Can this user perform this operation?"
- "Does this action require approval?"
- "Which project does this work belong to?"

WHY A SEPARATE POLICY LAYER
---------------------------

Business rules change independently from the core:

- Core: "Here's how to search a graph" (stable, algorithmic)
- Policy: "Users need manager approval for >$100 operations" (changes often)

By separating them:
- Policy changes don't touch core code
- Core remains pure and testable
- Different deployments can have different policies

POLICY VS MIDDLEWARE
--------------------

MIDDLEWARE wraps operations:        POLICY decides operations:
- Logging (always log)               - Can this user do this?
- Metrics (always measure)           - Does this need approval?
- Budget tracking (always track)     - Which project is this?

Middleware is about HOW we do things (with logging).
Policy is about WHETHER we do things (with permission).

POLICY CATEGORIES
-----------------

GOVERNANCE:
- Approval workflows (who approves what)
- Audit requirements (what to log)
- Compliance rules (SOC2, HIPAA, etc.)

PROJECTS:
- Work organization (chunks, handoffs)
- Team collaboration (who's working on what)
- Context management (session state)

AUTHENTICATION/AUTHORIZATION:
- Identity (who is this user?)
- Permissions (what can they do?)
- Roles (manager, developer, viewer)

DESIGN DECISIONS
----------------

1. POLICIES ARE CHECKABLE, NOT ENFORCEABLE

   Policies return True/False, not raise exceptions:
       if governance.can_proceed(context):
           do_the_thing()
       else:
           handle_rejection()

   The application decides what to do with rejections.

2. POLICIES ARE STATELESS

   Policies don't store data. They check rules against:
   - Context (who, what, when)
   - Configuration (rules, thresholds)

   State lives in services (persistence, knowledge).

3. POLICIES COMPOSE

   Multiple policies can apply:
       if all(p.allows(context) for p in policies):
           proceed()

   This allows fine-grained rules without complex logic.

"""

from graph_of_thought_v2.policy.governance import (
    GovernancePolicy,
    ApprovalRequirement,
    AuditRequirement,
)

from graph_of_thought_v2.policy.projects import (
    Project,
    WorkChunk,
    Handoff,
)

__all__ = [
    # Governance
    "GovernancePolicy",
    "ApprovalRequirement",
    "AuditRequirement",
    # Projects
    "Project",
    "WorkChunk",
    "Handoff",
]
