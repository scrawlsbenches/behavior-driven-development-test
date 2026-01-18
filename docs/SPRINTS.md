# Sprint Planning

## Sprint Overview

| Sprint | Focus | Priority Tag | Status |
|--------|-------|--------------|--------|
| 1-2 | Core MVP | @mvp-p0 | In Progress |
| 3-4 | Production Readiness | @mvp-p1 | Planned |
| 5+ | Enhanced Experience | @mvp-p2 | Backlog |

## Sprint 1-2: Core MVP (@mvp-p0)

**Goal:** Deliver core value proposition - users can explore problems, track costs, and record decisions.

### Completed

| Feature | Scenarios | Status |
|---------|-----------|--------|
| Thought Exploration | 9 | Done |
| Intelligent Search | 8 | Done |
| LLM Integration | 7 | Done |
| Approval Workflows | 8 | Done |
| Budget & Consumption | 7 | Done |
| Project Lifecycle | 7 | Done |
| DDD Architecture Refactor | - | Done |
| Foundation API Tests | 209 | Done |

### Remaining

| Feature | Work Needed |
|---------|-------------|
| Decisions & Learnings | Step definitions |
| Question Routing | Step definitions |
| Data Persistence | Step definitions for backup/recovery |

### Definition of Done
- All @mvp-p0 scenarios passing
- Architecture checks passing
- No @wip tags on completed features

## Sprint 3-4: Production Readiness (@mvp-p1)

**Goal:** System is observable, recoverable, and ready for production deployment.

### Planned Work

| Feature | Scenarios | Priority |
|---------|-----------|----------|
| Observability | 12 | High |
| Advanced Search Strategies | 4 | Medium |
| Multi-approver Workflows | 3 | Medium |
| SLA Tracking | 2 | Medium |

### Key Deliverables
- Structured logging with correlation IDs
- Prometheus-compatible metrics
- OpenTelemetry tracing integration
- Backup verification and restore testing

## Sprint 5+: Enhanced Experience (@mvp-p2)

**Goal:** Delight users with advanced features and analytics.

### Backlog

- Forecasting and budget recommendations
- Cross-project analytics
- Customizable dashboards
- Advanced integrations

## Running Sprint Tests

```bash
# Current sprint (MVP-P0)
behave --tags=@mvp-p0

# Next sprint (MVP-P1)
behave --tags=@mvp-p1

# All MVP work
behave --tags="@mvp-p0 or @mvp-p1 or @mvp-p2"
```
