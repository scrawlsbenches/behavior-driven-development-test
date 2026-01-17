@services @knowledge @high
Feature: Knowledge Service
  As a developer using Graph of Thought
  I want a knowledge service to store and retrieve information
  So that I can build applications that learn from past decisions

  # ===========================================================================
  # TERMINOLOGY
  # ===========================================================================
  # This feature tests TWO implementations:
  #
  # 1. IN-MEMORY KNOWLEDGE SERVICE (test double)
  #    - Stores entries but retrieval always returns empty
  #    - Use when you need isolated tests without knowledge lookup
  #
  # 2. SIMPLE KNOWLEDGE SERVICE (lightweight implementation)
  #    - Stores and retrieves entries using keyword matching
  #    - Use when testing actual knowledge storage behavior

  # ===========================================================================
  # In-Memory Knowledge Service (Test Double)
  # ===========================================================================

  Scenario: In-memory knowledge service stores entries without retrieval
    Given an in-memory knowledge service
    When I store a knowledge entry "Test knowledge"
    And I retrieve knowledge for "Test"
    Then no knowledge entries should be found

  # ===========================================================================
  # Simple Knowledge Service
  # ===========================================================================

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

  # ===========================================================================
  # Future Capabilities
  # ===========================================================================

  @wip
  Scenario: Knowledge service finds related entries
    Given a simple knowledge service
    And a knowledge entry "JWT tokens for authentication"
    And a knowledge entry "OAuth2 for authorization"
    And a knowledge entry "Database schema design"
    When I get entries related to "JWT tokens for authentication"
    Then "OAuth2 for authorization" should be in related entries
    And "Database schema design" should not be in related entries

  @wip
  Scenario: Knowledge service tracks decision outcomes
    Given a simple knowledge service
    And a recorded decision "Use REST API" with id "dec-123"
    When I record outcome "REST API performed well under load" for decision "dec-123"
    Then the decision should have outcome "REST API performed well under load"

  @wip
  Scenario: Knowledge service handles corrupted entries gracefully
    Given a simple knowledge service with persistence
    And a corrupted entry in storage
    When I retrieve all knowledge entries
    Then valid entries should be returned
    And corrupted entries should be logged and skipped

  @wip
  Scenario: Knowledge service supports full Architecture Decision Record structure
    Given a simple knowledge service
    When I record a full ADR with:
      | field       | value                    |
      | title       | Use PostgreSQL           |
      | status      | accepted                 |
      | deciders    | alice, bob               |
      | supersedes  | ADR-001                  |
    Then the ADR should be stored with all fields

  @wip
  Scenario: Knowledge service uses semantic search
    Given a simple knowledge service with embeddings enabled
    And a knowledge entry "We authenticate users with JWT tokens"
    And a knowledge entry "The weather today is sunny"
    When I search for "user login verification"
    Then the JWT entry should be found
    And the weather entry should not be found
    And the search should use semantic similarity not keywords

  @wip
  Scenario: Knowledge service returns relevance scores
    Given a simple knowledge service with embeddings enabled
    And a knowledge entry "PostgreSQL is our primary database"
    And a knowledge entry "We also use Redis for caching"
    When I search for "database storage"
    Then results should have relevance scores between 0 and 1
    And the PostgreSQL entry should have higher relevance than Redis entry

  @wip
  Scenario: Knowledge service generates embeddings on store
    Given a simple knowledge service with embeddings enabled
    When I store knowledge "New important decision about architecture"
    Then the entry should have a non-null embedding
    And the embedding should be a vector of appropriate dimensions

  # ===========================================================================
  # Known Limitations (Escape Clauses)
  # ===========================================================================
  # ESCAPE CLAUSE: Uses simple keyword matching, not semantic search.
  # Current: O(n) scan checking if query words appear in content.
  # Requires: Embedding model (OpenAI/local), vector DB (Pinecone/pgvector).
  #
  # ESCAPE CLAUSE: Relevance scoring is placeholder.
  # Current: Returns 1.0 for matches, no real relevance ranking.
  # Requires: TF-IDF or embedding similarity scores.
  #
  # ESCAPE CLAUSE: Embeddings not implemented.
  # Current: KnowledgeEntry.embedding is always None.
  # Requires: Embedding generation on store, storage in vector DB.
