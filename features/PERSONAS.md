# Enterprise Personas Reference

This document defines the personas used across all feature files. Reference these when writing new scenarios to ensure consistent business focus.

---

## Primary Personas

### Engineering Manager (Alex)
**Role**: Leads a team of 5-10 engineers working on AI-assisted projects
**Goals**:
- Deliver projects on time and within budget
- Maintain visibility into team progress and blockers
- Ensure quality and compliance standards are met
**Pain Points**:
- Unclear project status across multiple AI sessions
- Budget overruns from untracked token usage
- Decisions made without documentation
**Success Metrics**:
- Sprint velocity, budget adherence, question resolution time

### Data Scientist (Jordan)
**Role**: Uses AI reasoning to explore complex analytical problems
**Goals**:
- Explore solution spaces efficiently within token budgets
- Track experiment history and learnings
- Build on previous work without starting over
**Pain Points**:
- Running out of tokens mid-analysis
- Losing context between sessions
- Repeating failed approaches
**Success Metrics**:
- Cost per insight, experiment success rate, time to solution

### Security Officer (Morgan)
**Role**: Ensures all AI-assisted work meets security and compliance requirements
**Goals**:
- Maintain complete audit trails for all decisions
- Enforce approval workflows for sensitive operations
- Demonstrate compliance during audits
**Pain Points**:
- Unauthorized changes to production systems
- Incomplete audit logs
- Manual compliance reporting
**Success Metrics**:
- Zero unauthorized deployments, 100% audit coverage, audit preparation time

### Product Owner (Sam)
**Role**: Defines requirements and priorities for AI-assisted development
**Goals**:
- Get questions answered quickly to unblock development
- Ensure decisions align with product strategy
- Track feature progress and scope changes
**Pain Points**:
- Blocked development waiting for answers
- Decisions made without product input
- Losing track of scope changes
**Success Metrics**:
- Question response time, decision alignment, scope clarity

### DevOps Engineer (Casey)
**Role**: Manages deployment and infrastructure for AI systems
**Goals**:
- Deploy changes safely with proper approvals
- Monitor system health and performance
- Quickly diagnose and resolve issues
**Pain Points**:
- Deployments without proper review
- Difficult to trace issues across services
- Missing observability data
**Success Metrics**:
- Deployment success rate, mean time to resolution, system uptime

### Compliance Auditor (Riley) - External
**Role**: Reviews organization's AI governance for regulatory compliance
**Goals**:
- Verify all required approvals were obtained
- Confirm data handling meets regulations
- Generate compliance reports efficiently
**Pain Points**:
- Incomplete or scattered audit trails
- Manual evidence collection
- Unclear policy enforcement
**Success Metrics**:
- Audit completion time, finding severity, evidence completeness

---

## Secondary Personas

### Junior Developer (Taylor)
**Role**: New team member learning to use AI-assisted development
**Goals**:
- Understand how to use the system effectively
- Learn from previous decisions and patterns
- Get help when stuck without blocking seniors
**Pain Points**:
- Unclear where to find past decisions
- Not knowing who to ask questions
- Fear of exceeding budgets

### Finance Administrator (Drew)
**Role**: Manages AI usage budgets across the organization
**Goals**:
- Allocate budgets fairly across teams
- Forecast costs accurately
- Identify cost optimization opportunities
**Pain Points**:
- Unexpected budget overruns
- Unclear cost attribution
- Manual budget tracking

### Knowledge Manager (Avery)
**Role**: Curates organizational learnings from AI-assisted work
**Goals**:
- Capture decisions and their rationale
- Make knowledge discoverable across teams
- Identify patterns and best practices
**Pain Points**:
- Knowledge siloed in individual sessions
- Duplicate decisions across teams
- Outdated information persisting

---

## MVP Priority Tags

Use these tags to guide development prioritization:

| Tag | Meaning | Criteria |
|-----|---------|----------|
| `@mvp-p0` | Must have for launch | Core value proposition, blocks all usage |
| `@mvp-p1` | Should have for launch | Key differentiator, significant user value |
| `@mvp-p2` | Nice to have for launch | Improves experience, can workaround |
| `@post-mvp` | Future enhancement | Advanced features, optimizations |

---

## Feature Priority Matrix

| Business Capability | MVP-P0 | MVP-P1 | MVP-P2 | Post-MVP |
|---------------------|--------|--------|--------|----------|
| AI Reasoning | Thought exploration, basic search | Advanced search strategies | Visualization | MCTS, custom strategies |
| Project Management | Session tracking, handoffs | Work chunks, progress | Team collaboration | Multi-project views |
| Cost Management | Budget tracking, consumption | Warnings, limits | Forecasting | Hierarchical budgets |
| Governance | Basic approvals, audit log | Policy enforcement | Approval workflows | External integrations |
| Knowledge | Decision recording, retrieval | Question routing | Semantic search | Pattern detection |
| Platform | Persistence, basic metrics | Logging, tracing | Dashboards | External observability |
