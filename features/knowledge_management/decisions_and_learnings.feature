@wip @knowledge-management @mvp-p0
Feature: Organizational Decisions and Learnings
  As an Engineering Manager
  I want all significant decisions to be documented with their rationale
  So that teams can learn from past choices and avoid repeating mistakes

  As a Knowledge Manager
  I want to curate and organize learnings across teams
  So that institutional knowledge is preserved and discoverable

  As a Junior Developer
  I want to find previous decisions on similar problems
  So that I can learn from team experience without repeatedly asking seniors

  # ===========================================================================
  # Recording Decisions - MVP-P0
  # ===========================================================================
  # Business Rule: Decisions are captured with their context, rationale, and
  # consequences. They become searchable organizational knowledge.

  Background:
    Given the knowledge service is available

  @mvp-p0 @critical
  Scenario: Developer records a technical decision
    Given Jordan is working on project "API Optimization"
    When Jordan records a decision:
      | field           | value                                              |
      | title           | Use Redis for caching layer                        |
      | context         | API response times exceed 500ms, need caching      |
      | decision        | Implement Redis caching with 5-minute TTL          |
      | rationale       | Redis provides sub-ms reads, team has expertise    |
      | alternatives    | Memcached (less features), In-memory (not shared)  |
      | consequences    | Need Redis infrastructure, adds operational cost   |
    Then the decision should be saved to the knowledge base
    And it should be searchable by "caching" and "Redis"
    And it should be linked to project "API Optimization"
    And the decision timestamp should be recorded

  @mvp-p0 @critical
  Scenario: Finding previous decisions on a topic
    Given decisions exist in the knowledge base:
      | title                              | project      | date       |
      | Use Redis for caching              | API Opt      | 2024-01-10 |
      | PostgreSQL for user data           | Core         | 2023-11-15 |
      | Redis Cluster for session storage  | Auth         | 2023-09-20 |
    When Taylor searches for "Redis"
    Then the search should return 2 decisions
    And results should show the decision title, project, and date
    And Taylor should be able to view full details of each

  @mvp-p0
  Scenario: Viewing decision in full context
    Given a decision "Use Redis for caching" exists
    When Taylor views the full decision
    Then they should see all recorded details:
      | section         | present |
      | title           | yes     |
      | context         | yes     |
      | decision        | yes     |
      | rationale       | yes     |
      | alternatives    | yes     |
      | consequences    | yes     |
      | made_by         | yes     |
      | date            | yes     |
      | related_project | yes     |

  # ===========================================================================
  # Learning from Experience - MVP-P1
  # ===========================================================================
  # Business Rule: Beyond decisions, teams capture learnings - insights gained
  # from work that benefit future projects.

  @mvp-p1
  Scenario: Recording a learning from project work
    Given Jordan has discovered an important pattern
    When Jordan records a learning:
      | field           | value                                              |
      | title           | Connection pooling critical for PostgreSQL at scale|
      | discovery       | Saw 10x latency without pooling at 100+ connections|
      | recommendation  | Always use PgBouncer for production deployments    |
      | evidence        | Load test results, production metrics              |
      | tags            | postgresql, performance, infrastructure            |
    Then the learning should be saved
    And it should be discoverable by future teams
    And it should be tagged for easy categorization

  @mvp-p1
  Scenario: Linking learnings to project outcomes
    Given project "Q1 Optimization" achieved 45% latency reduction
    When Alex records the project outcome
    Then associated learnings should be linked
    And the success metrics should validate the learnings
    And future teams can see "This learning contributed to 45% improvement"

  @mvp-p1
  Scenario: Knowledge Manager curates learnings
    Given multiple unreviewed learnings from the past month
    When Avery reviews and curates them
    Then they can:
      | action              | purpose                                     |
      | verify              | Mark as team-validated                      |
      | categorize          | Add to appropriate knowledge area           |
      | link_related        | Connect related decisions and learnings     |
      | highlight           | Feature in team newsletters                 |
      | archive             | Mark as outdated if superseded              |

  # ===========================================================================
  # Decision Templates and Consistency - MVP-P1
  # ===========================================================================
  # Business Rule: Standard templates ensure decisions capture required context.
  # Different decision types may have different templates.

  @mvp-p1
  Scenario: Using decision template for architecture choices
    Given an "Architecture Decision Record" template
    When Jordan starts a new architecture decision
    Then the template should prompt for:
      | field           | required | guidance                                    |
      | title           | yes      | Short, searchable title                     |
      | status          | yes      | Proposed, Accepted, Deprecated, Superseded  |
      | context         | yes      | What situation led to this decision?        |
      | decision        | yes      | What are we doing?                          |
      | rationale       | yes      | Why this choice over alternatives?          |
      | consequences    | yes      | What are the trade-offs?                    |
      | alternatives    | no       | What other options were considered?         |

  @mvp-p1
  Scenario: Decision requires minimum information before saving
    When Jordan tries to save a decision without rationale
    Then saving should be prevented
    And a message should indicate "Rationale is required"
    And Jordan should be prompted to complete the field

  # ===========================================================================
  # Decision Lifecycle - MVP-P2
  # ===========================================================================
  # Business Rule: Decisions have lifecycle states. They can become outdated
  # or be superseded by newer decisions.

  @mvp-p2
  Scenario: Superseding an old decision
    Given decision "Use PostgreSQL 12" from 2022
    When Jordan creates decision "Migrate to PostgreSQL 15"
    And marks it as superseding the old decision
    Then the old decision should be marked "Superseded"
    And it should link to the new decision
    And searches should prioritize the current decision
    And the old decision should still be accessible for history

  @mvp-p2
  Scenario: Flagging potentially outdated decisions
    Given a decision made 2 years ago about "AWS region selection"
    And technology landscape has changed significantly
    When the system runs staleness check
    Then the decision should be flagged for review
    And the original decision-maker should be notified
    And they can confirm "Still valid" or mark for update

  # ===========================================================================
  # Knowledge Discovery - MVP-P1
  # ===========================================================================
  # Business Rule: Knowledge should be surfaced proactively when relevant
  # to current work, not just when explicitly searched.

  @mvp-p1
  Scenario: Proactive knowledge suggestions during work
    Given Jordan is working on "Database optimization"
    And past decisions exist about database topics
    When Jordan starts exploring options
    Then relevant past decisions should be suggested:
      | decision                              | relevance |
      | Use connection pooling                | high      |
      | PostgreSQL over MySQL for analytics   | medium    |
    And Jordan should be able to dismiss or save suggestions

  @mvp-p1
  Scenario: Related decisions shown when viewing a decision
    Given Jordan is viewing "Use Redis for caching"
    Then related decisions should be displayed:
      | decision                    | relationship         |
      | Redis Cluster architecture  | same topic           |
      | Cache invalidation strategy | same project         |
      | Memcached evaluation        | alternative explored |

  @mvp-p2 @wip
  Scenario: Semantic search for finding decisions
    When Taylor searches for "how do we handle user sessions?"
    Then the system should understand the semantic meaning
    And return decisions about session management
    # Even if they don't contain the exact phrase "user sessions"

  # ===========================================================================
  # Decision Analytics - MVP-P2
  # ===========================================================================

  @mvp-p2
  Scenario: Knowledge base health metrics
    When Avery views knowledge base analytics
    Then they should see:
      | metric                        | value  |
      | Total decisions               | 247    |
      | Decisions this month          | 12     |
      | Average decisions per project | 8      |
      | Most active contributor       | Jordan |
      | Decisions needing review      | 15     |
      | Search success rate           | 78%    |

  @mvp-p2
  Scenario: Identifying knowledge gaps
    Given project areas with few documented decisions
    When Avery runs knowledge gap analysis
    Then gaps should be highlighted:
      | area              | decisions | status        |
      | Authentication    | 12        | well covered  |
      | Caching           | 8         | adequate      |
      | Monitoring        | 2         | needs attention|
      | Security          | 1         | critical gap  |

  # ===========================================================================
  # Edge Cases - Post-MVP
  # ===========================================================================

  @post-mvp @wip
  Scenario: Conflicting decisions detection
    Given two decisions with contradictory recommendations
    When the conflict is detected
    Then both decision authors should be notified
    And they should be prompted to resolve the conflict
    And searches should highlight the conflict to users

  @post-mvp @wip
  Scenario: Decision impact tracking
    Given a decision "Use microservices architecture"
    When projects using this decision report outcomes
    Then aggregated impact should be visible:
      | outcome_type     | projects | avg_impact |
      | positive         | 5        | +30% velocity|
      | neutral          | 2        | no change   |
      | negative         | 1        | complexity   |
