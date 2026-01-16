@services @high
Feature: Service Implementations
  As a developer using Graph of Thought
  I want to use service implementations for governance, resources, and knowledge
  So that I can manage projects with proper controls

  # ===========================================================================
  # InMemory Services (Testable implementations with configurable behavior)
  # ===========================================================================
  # These provide testable implementations that can be configured to behave
  # like pass-through services or full-featured services with assertions.

  Scenario: In-memory governance service auto-approves everything
    Given an in-memory governance service
    When I check approval for action "deploy_production"
    Then the approval status should be "APPROVED"

  Scenario: In-memory resource service has unlimited resources
    Given an in-memory resource service
    When I check available tokens for project "test"
    Then resources should be available
    And remaining resources should be infinite

  Scenario: In-memory knowledge service stores but finds nothing
    Given an in-memory knowledge service
    When I store a knowledge entry "Test knowledge"
    And I retrieve knowledge for "Test"
    Then no knowledge entries should be found

  # ===========================================================================
  # Simple Governance Service
  # ===========================================================================
  # ESCAPE CLAUSE: Rule-based, not workflow-based.
  # Current: Policies are simple allow/deny/review rules checked synchronously.
  # Requires: Workflow engine for multi-step approvals, escalation, timeouts.
  # Depends: None
  #
  # ESCAPE CLAUSE: Callable policies not fully implemented.
  # Current: Callable policies exist but aren't invoked with full context.
  # Requires: Pass action context, actor info, and environment to callables.
  # Depends: None
  #
  # ESCAPE CLAUSE: Policy format is undefined.
  # Current: Returns raw dicts from get_policies().
  # Requires: Define PolicyDefinition dataclass with validation.
  # Depends: None

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

  # --- Governance Edge Cases (TODO: Implement) ---

  # ESCAPE CLAUSE: No approval expiration or timeout.
  # Current: Pending approvals stay pending forever.
  # Requires: Timestamp tracking, background job for expiration.
  # Depends: None
  @wip
  Scenario: Pending approval expires after timeout
    Given a simple governance service
    And an approval timeout of 1 hour
    When I request approval for action "deploy" with justification "Needed"
    And 2 hours pass without approval
    Then the pending approval status should be "expired"

  # ESCAPE CLAUSE: No approval escalation.
  # Current: Single approver, no escalation path.
  # Requires: Escalation rules, notification system.
  # Depends: Approval timeout implementation
  @wip
  Scenario: Unapproved request escalates to higher authority
    Given a simple governance service
    And an escalation policy after 30 minutes to "senior-admin"
    When I request approval for action "deploy" with justification "Critical"
    And 45 minutes pass without approval
    Then the request should be escalated to "senior-admin"

  # ===========================================================================
  # Simple Resource Service
  # ===========================================================================
  # ESCAPE CLAUSE: Budgets reset on restart.
  # Current: All budget state is in-memory.
  # Requires: Database persistence (PostgreSQL/Redis) for budget state.
  # Depends: None
  #
  # ESCAPE CLAUSE: No parent budget checks.
  # Current: Each scope's budget is independent.
  # Requires: Hierarchical budgets (org -> team -> project -> task).
  # Depends: None
  #
  # ESCAPE CLAUSE: Hard stop at budget.
  # Current: Consumption fails immediately when budget exceeded.
  # Requires: Soft limits with warnings, grace periods, override capability.
  # Depends: None

  Scenario: Simple resource service tracks budgets
    Given a simple resource service
    When I set a token budget of 10000 for project "test_project"
    Then the token budget for project "test_project" should be 10000

  Scenario: Simple resource service tracks consumption
    Given a simple resource service
    And a token budget of 10000 for project "test_project"
    When I consume 500 tokens for project "test_project"
    Then the remaining tokens for project "test_project" should be 9500

  Scenario: Simple resource service blocks over-budget consumption
    Given a simple resource service
    And a token budget of 100 for project "test_project"
    When I try to consume 150 tokens for project "test_project"
    Then the consumption should be rejected

  Scenario: Simple resource service generates consumption reports
    Given a simple resource service
    And a token budget of 10000 for project "test_project"
    When I consume 500 tokens for project "test_project" with description "Chunk 1"
    And I consume 300 tokens for project "test_project" with description "Chunk 2"
    And I get the consumption report for project "test_project"
    Then the report should show 2 consumption events
    And the report should show 800 total tokens consumed

  # --- Resource Edge Cases (TODO: Implement) ---

  # ESCAPE CLAUSE: Date filtering not implemented in consumption reports.
  # Current: Returns all consumption events regardless of date.
  # Requires: Parse timestamps, filter by start_date/end_date parameters.
  # Depends: None
  @wip
  Scenario: Resource service filters consumption report by date range
    Given a simple resource service
    And a token budget of 10000 for project "test_project"
    And consumption of 500 tokens on "2024-01-01"
    And consumption of 300 tokens on "2024-01-15"
    And consumption of 200 tokens on "2024-02-01"
    When I get the consumption report from "2024-01-01" to "2024-01-31"
    Then the report should show 2 consumption events
    And the report should show 800 total tokens consumed

  # ESCAPE CLAUSE: No soft budget limits with warnings.
  # Current: Hard stop at 100% budget.
  # Requires: Warning thresholds (e.g., 80%, 90%), notification hooks.
  # Depends: None
  @wip
  Scenario: Resource service warns when approaching budget limit
    Given a simple resource service
    And a token budget of 1000 for project "test_project"
    And a warning threshold at 80 percent
    When I consume 850 tokens for project "test_project"
    Then a budget warning should be issued
    And the consumption should succeed

  # ESCAPE CLAUSE: No budget override capability.
  # Current: Cannot exceed budget under any circumstances.
  # Requires: Override mechanism with audit trail, approval integration.
  # Depends: Governance service integration
  @wip
  Scenario: Authorized user can override budget limit
    Given a simple resource service
    And a token budget of 100 for project "test_project"
    And user "admin" has budget override permission
    When "admin" overrides budget to consume 150 tokens for project "test_project"
    Then the consumption should succeed
    And an audit entry should record the override

  # ESCAPE CLAUSE: Priority calculation is naive.
  # Current: Uses Priority enum directly without context.
  # Requires: Dynamic priority based on project state, deadlines, dependencies.
  # Depends: None
  @wip
  Scenario: Resource allocation considers project priority dynamically
    Given a simple resource service
    And project "critical" with deadline in 1 day
    And project "normal" with deadline in 30 days
    When both projects request 500 tokens with only 600 available
    Then project "critical" should receive tokens first

  # ESCAPE CLAUSE: Timeline projection not implemented.
  # Current: get_projected_timeline() returns empty dict.
  # Requires: Historical consumption analysis, trend extrapolation.
  # Depends: Date filtering for historical data
  @wip
  Scenario: Resource service projects budget exhaustion timeline
    Given a simple resource service
    And a token budget of 10000 for project "test_project"
    And historical consumption of 500 tokens per day for 5 days
    When I request a timeline projection for project "test_project"
    Then the projection should estimate exhaustion in 10 days

  # ===========================================================================
  # Simple Knowledge Service
  # ===========================================================================
  # ESCAPE CLAUSE: Uses simple keyword matching, not semantic search.
  # Current: O(n) scan checking if query words appear in content.
  # Requires: Embedding model (OpenAI/local), vector DB (Pinecone/pgvector).
  # Depends: None - but significant infrastructure change
  #
  # ESCAPE CLAUSE: Relevance scoring is placeholder.
  # Current: Returns 1.0 for matches, no real relevance ranking.
  # Requires: TF-IDF or embedding similarity scores.
  # Depends: Semantic search implementation
  #
  # ESCAPE CLAUSE: Embeddings not implemented.
  # Current: KnowledgeEntry.embedding is always None.
  # Requires: Embedding generation on store, storage in vector DB.
  # Depends: Semantic search implementation

  Scenario: Simple knowledge service stores and retrieves entries
    Given a simple knowledge service
    When I store knowledge "Authentication uses JWT tokens" with tags "auth, jwt"
    And I retrieve knowledge for "JWT authentication"
    Then 1 knowledge entry should be found
    And the entry should contain "JWT tokens"

  Scenario: Simple knowledge service filters by entry type
    Given a simple knowledge service
    And a knowledge entry "Pattern: Use factory methods" of type "pattern"
    And a knowledge entry "Decision: Use PostgreSQL" of type "decision"
    When I search knowledge for "factory" filtering by type "pattern"
    Then 1 knowledge entry should be found

  Scenario: Simple knowledge service records decisions
    Given a simple knowledge service
    When I record a decision "Use REST API" with rationale "Better tooling support"
    Then the decision should be stored
    And retrieving "REST API" should find the decision

  # --- Knowledge Edge Cases (TODO: Implement) ---

  # ESCAPE CLAUSE: get_related() not implemented.
  # Current: Returns empty list.
  # Requires: Relationship tracking or embedding similarity.
  # Depends: Semantic search for similarity-based relations
  @wip
  Scenario: Knowledge service finds related entries
    Given a simple knowledge service
    And a knowledge entry "JWT tokens for authentication"
    And a knowledge entry "OAuth2 for authorization"
    And a knowledge entry "Database schema design"
    When I get entries related to "JWT tokens for authentication"
    Then "OAuth2 for authorization" should be in related entries
    And "Database schema design" should not be in related entries

  # ESCAPE CLAUSE: Outcome tracking not implemented for decisions.
  # Current: Decision.outcome is always None.
  # Requires: Mechanism to record actual outcomes, link to decisions.
  # Depends: None
  @wip
  Scenario: Knowledge service tracks decision outcomes
    Given a simple knowledge service
    And a recorded decision "Use REST API" with id "dec-123"
    When I record outcome "REST API performed well under load" for decision "dec-123"
    Then the decision should have outcome "REST API performed well under load"

  # ESCAPE CLAUSE: Deserialization is fragile.
  # Current: JSON parsing with minimal validation.
  # Requires: Schema validation, migration support for format changes.
  # Depends: None
  @wip
  Scenario: Knowledge service handles corrupted entries gracefully
    Given a simple knowledge service with persistence
    And a corrupted entry in storage
    When I retrieve all knowledge entries
    Then valid entries should be returned
    And corrupted entries should be logged and skipped

  # ESCAPE CLAUSE: Real ADRs have more structure.
  # Current: Simplified Decision dataclass.
  # Requires: Full ADR fields (status, date, deciders, supersedes, etc.)
  # Depends: None
  @wip
  Scenario: Knowledge service supports full ADR structure
    Given a simple knowledge service
    When I record a full ADR with:
      | field       | value                    |
      | title       | Use PostgreSQL           |
      | status      | accepted                 |
      | deciders    | alice, bob               |
      | supersedes  | ADR-001                  |
    Then the ADR should be stored with all fields

  # ===========================================================================
  # Simple Question Service
  # ===========================================================================
  # ESCAPE CLAUSE: Routing is naive.
  # Current: Keyword matching routes to teams, default is "human".
  # Requires: ML classifier, context-aware routing, load balancing.
  # Depends: None
  #
  # ESCAPE CLAUSE: Auto-answer always returns False.
  # Current: can_auto_answer() always returns False.
  # Requires: Knowledge base integration, confidence thresholds.
  # Depends: Knowledge service with good retrieval
  #
  # ESCAPE CLAUSE: No confidence scoring for auto-answers.
  # Current: Not applicable since auto-answer disabled.
  # Requires: LLM-based answer generation with confidence estimation.
  # Depends: Auto-answer implementation, LLM integration

  Scenario: Simple question service creates tickets
    Given a simple question service
    When I ask a question "Should we use GraphQL?" with priority "HIGH"
    Then a question ticket should be created
    And the ticket should have status "open"
    And the ticket should have priority "HIGH"

  Scenario: Simple question service routes questions by keywords
    Given a simple question service
    When I ask a question "What are the security requirements?"
    Then the question should be routed to "security-team"

  Scenario: Simple question service routes business questions to product owner
    Given a simple question service
    When I ask a question "Should we add this feature?"
    Then the question should be routed to "product-owner"

  Scenario: Simple question service answers tickets
    Given a simple question service
    And a pending question "What database?"
    When I provide answer "PostgreSQL" from "architect"
    Then the ticket should have status "answered"
    And the ticket should have answer "PostgreSQL"

  Scenario: Simple question service returns pending questions by priority
    Given a simple question service
    And a question "Low priority question" with priority "LOW"
    And a question "Critical question" with priority "CRITICAL"
    When I get pending questions
    Then the first question should have priority "CRITICAL"

  # --- Question Edge Cases (TODO: Implement) ---

  # ESCAPE CLAUSE: No auto-answer capability.
  # Current: All questions require human response.
  # Requires: Knowledge base lookup, LLM generation, confidence threshold.
  # Depends: Knowledge service with semantic search
  @wip
  Scenario: Question service auto-answers from knowledge base
    Given a simple question service
    And a knowledge base with entry "We use PostgreSQL for all projects"
    When I ask a question "What database do we use?"
    And the confidence threshold is 0.8
    Then the question should be auto-answered
    And the answer should reference the knowledge base entry
    And the confidence should be above 0.8

  # ESCAPE CLAUSE: No question deduplication.
  # Current: Same question can be asked multiple times.
  # Requires: Similarity detection, linking to previous answers.
  # Depends: Semantic search for similarity
  @wip
  Scenario: Question service detects duplicate questions
    Given a simple question service
    And a previously answered question "What database should we use?"
    When I ask a question "Which database should we use?"
    Then the service should suggest the existing answer
    And offer to create a new ticket if unsatisfied

  # ESCAPE CLAUSE: No SLA tracking for question response times.
  # Current: No tracking of response times or SLA violations.
  # Requires: Timestamp tracking, SLA definitions, alerting.
  # Depends: None
  @wip
  Scenario: Question service tracks SLA compliance
    Given a simple question service
    And an SLA of 4 hours for HIGH priority questions
    And a HIGH priority question asked 5 hours ago without answer
    When I check SLA compliance
    Then the question should be flagged as SLA violation

  # ===========================================================================
  # Simple Communication Service
  # ===========================================================================
  # ESCAPE CLAUSE: Intent and feedback storage is in-memory only.
  # Current: All state lost on restart.
  # Requires: Database persistence for intents, feedback, handoffs.
  # Depends: None
  #
  # ESCAPE CLAUSE: Handoff is simplified version.
  # Current: Basic package with project, type, context.
  # Requires: Full handoff with attachments, thread history, action items.
  # Depends: None
  #
  # ESCAPE CLAUSE: Feedback is stored but not used for learning.
  # Current: Feedback recorded but never analyzed.
  # Requires: Feedback analysis, model fine-tuning pipeline.
  # Depends: None - but significant ML infrastructure
  #
  # ESCAPE CLAUSE: Compression is truncation, not summarization.
  # Current: Simply truncates history to max_tokens * 4 chars.
  # Requires: LLM-based summarization preserving key information.
  # Depends: LLM integration

  Scenario: Simple communication service creates handoff packages
    Given a simple communication service
    When I create a handoff for project "test_project" of type "ai_to_human"
    Then a handoff package should be created
    And the handoff should have type "ai_to_human"

  Scenario: Simple communication service records intent
    Given a simple communication service
    When I record intent "Implement user authentication" for project "test_project"
    And I get resumption context for project "test_project"
    Then the context should contain "Implement user authentication"

  Scenario: Simple communication service compresses history
    Given a simple communication service
    And a recorded intent "Build the API" for project "test_project"
    When I compress history for project "test_project" with max tokens 100
    Then the compressed history should not exceed 400 characters

  # --- Communication Edge Cases (TODO: Implement) ---

  # ESCAPE CLAUSE: No handoff attachments.
  # Current: Handoff has no file or artifact attachments.
  # Requires: Attachment storage, file upload handling.
  # Depends: None
  @wip
  Scenario: Communication service includes attachments in handoff
    Given a simple communication service
    And a file "architecture.png" attached to project "test_project"
    When I create a handoff for project "test_project" of type "ai_to_human"
    Then the handoff should include attachment "architecture.png"

  # ESCAPE CLAUSE: No intelligent summarization.
  # Current: Truncation loses information.
  # Requires: LLM summarization preserving key decisions, blockers, progress.
  # Depends: LLM integration
  @wip
  Scenario: Communication service summarizes history intelligently
    Given a simple communication service
    And project "test_project" with 50 recorded intents
    When I compress history for project "test_project" with max tokens 100
    Then the summary should mention key decisions made
    And the summary should mention current blockers
    And the summary should mention progress percentage

  # ESCAPE CLAUSE: No feedback loop for improvement.
  # Current: Feedback stored but ignored.
  # Requires: Feedback aggregation, pattern detection, improvement suggestions.
  # Depends: Feedback analysis infrastructure
  @wip
  Scenario: Communication service analyzes feedback patterns
    Given a simple communication service
    And 10 negative feedback entries mentioning "slow response"
    When I request a feedback analysis
    Then the analysis should identify "slow response" as a pattern
    And suggest improvements for response time
