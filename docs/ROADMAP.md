# Graph of Thought Roadmap

## Vision

Graph of Thought is an enterprise AI-assisted reasoning and project management platform that helps teams explore problems systematically, track decisions, manage AI costs, and maintain compliance.

## Business Capabilities

| Capability | Purpose | Primary Value |
|------------|---------|---------------|
| AI Reasoning | Graph-based thought exploration | Systematic problem solving |
| Project Management | Work chunks, handoffs, collaboration | Context preservation across sessions |
| Cost Management | Token budgets, consumption tracking | Predictable AI spend |
| Governance & Compliance | Approvals, policies, audit logging | Enterprise trust and SOC2 readiness |
| Knowledge Management | Decisions, learnings, question routing | Organizational memory |
| Platform | Observability, persistence, configuration | Production reliability |

## Milestones

### M1: Core Platform (MVP)
**Goal:** Functional system for single-team use

- All @mvp-p0 scenarios passing
- Graph-based reasoning with LLM integration
- Basic budget tracking and approval workflows
- Decision recording and question routing
- Reliable data persistence

### M2: Production Ready
**Goal:** Deployable to production environments

- All @mvp-p1 scenarios passing
- Full observability (logging, metrics, tracing)
- Multi-tenant data isolation
- Backup and recovery
- SLA tracking and alerts

### M3: Enterprise Scale
**Goal:** Multi-team deployment with advanced features

- All @mvp-p2 scenarios passing
- Cross-project analytics
- Forecasting and recommendations
- Advanced integrations (Jira, Slack, GitHub)
- Self-service team onboarding

### M4: Intelligence Layer
**Goal:** Learning system that improves over time

- @post-mvp features
- Auto-routing based on past patterns
- Estimation improvement from actuals
- Knowledge gap identification
- Proactive recommendations

## Technical Evolution

```
Phase 1: In-Memory     → Testing and rapid iteration
Phase 2: Simple        → Working logic, single instance
Phase 3: Production    → External systems, high availability
```

Each service follows this progression independently, allowing incremental hardening.

## Success Metrics

| Metric | M1 Target | M2 Target |
|--------|-----------|-----------|
| Test coverage (behave) | 209+ scenarios | 400+ scenarios |
| Architecture checks | Passing | Passing |
| Step definition coverage | 60% | 90% |
| Mean time to context recovery | - | < 5 min |
