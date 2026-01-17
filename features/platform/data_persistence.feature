@platform @persistence @mvp-p0
Feature: Data Persistence and Recovery
  As a Data Scientist
  I want my exploration work to be automatically saved
  So that I never lose progress due to browser crashes or network issues

  As a DevOps Engineer
  I want reliable data storage with backup and recovery capabilities
  So that we can recover from failures and meet our RTO/RPO requirements

  As an Engineering Manager
  I want assurance that project data is durable and recoverable
  So that critical business work is protected

  # ===========================================================================
  # Automatic Save - MVP-P0
  # ===========================================================================
  # Business Rule: All user work is automatically persisted. Users should never
  # need to manually save, and should never lose more than 30 seconds of work.

  Background:
    Given the persistence layer is available

  @mvp-p0 @critical
  Scenario: Exploration progress is saved automatically
    Given Jordan is actively exploring with 20 thoughts created
    Then all 20 thoughts should be persisted to storage
    And the save should happen within 5 seconds of each change
    And Jordan should not need to take any save action
    And a visual indicator should show "All changes saved"

  @mvp-p0 @critical
  Scenario: Recovery after unexpected session termination
    Given Jordan has made changes to an exploration
    When Jordan's browser crashes unexpectedly
    And Jordan reopens the application
    Then all saved work should be restored
    And at most 30 seconds of work should be lost
    And Jordan should see a recovery notification

  @mvp-p0
  Scenario: Offline changes sync when connection restored
    Given Jordan loses network connectivity
    And continues working on the exploration
    When network connectivity is restored
    Then offline changes should sync to the server
    And no work should be lost
    And sync status should be clearly indicated

  # ===========================================================================
  # Project Data Storage - MVP-P0
  # ===========================================================================
  # Business Rule: Projects, chunks, decisions, and questions are persisted
  # in durable storage with appropriate indexing for quick retrieval.

  @mvp-p0 @critical
  Scenario: Complete project state is persisted
    Given project "Churn Analysis" with:
      | component        | count |
      | work_chunks      | 12    |
      | explorations     | 5     |
      | decisions        | 8     |
      | questions        | 15    |
    When the project is saved
    Then all components should be stored durably
    And relationships between components should be preserved
    And the project should be fully recoverable

  @mvp-p0
  Scenario: Loading project restores complete state
    Given a saved project "API Optimization"
    When Alex loads the project
    Then all project data should be restored:
      | component        | status              |
      | work_chunks      | all loaded          |
      | explorations     | all loaded          |
      | decisions        | all loaded          |
      | questions        | all loaded          |
      | budgets          | current values      |
      | permissions      | all applied         |

  @mvp-p1
  Scenario: Large exploration graphs load efficiently
    Given an exploration with 500 thoughts and 600 edges
    When the exploration is loaded
    Then loading should complete within 3 seconds
    And memory usage should be reasonable
    And the graph should be fully navigable

  # ===========================================================================
  # Storage Backends - MVP-P1
  # ===========================================================================
  # Business Rule: The system supports multiple storage backends for different
  # deployment scenarios (development, testing, production).

  @mvp-p1
  Scenario Outline: Persistence works across storage backends
    Given the storage backend is "<backend>"
    When I save an exploration with 10 thoughts
    And I load the exploration
    Then all 10 thoughts should be restored
    And all edges should be intact
    And thought scores should be preserved

    Examples:
      | backend     |
      | in-memory   |
      | file-system |
      | postgresql  |

  @mvp-p1
  Scenario: Storage backend is configured per environment
    Then the following backends should be used:
      | environment | backend        | purpose                    |
      | development | file-system    | Easy debugging             |
      | testing     | in-memory      | Fast test execution        |
      | staging     | postgresql     | Production-like testing    |
      | production  | postgresql     | Durability and performance |

  # ===========================================================================
  # Backup and Recovery - MVP-P1
  # ===========================================================================
  # Business Rule: Regular backups ensure data can be recovered in case of
  # catastrophic failure. RTO and RPO are defined and tested.

  @mvp-p1 @critical
  Scenario: Automated daily backups are performed
    Given the backup schedule is daily at 2:00 AM
    When the scheduled backup runs
    Then a complete backup should be created
    And the backup should be verified for integrity
    And it should be stored in a separate location
    And old backups should be rotated per retention policy

  @mvp-p1
  Scenario: Point-in-time recovery is possible
    Given backups from the past 7 days
    And transaction logs since last backup
    When Casey needs to recover to yesterday at 3:00 PM
    Then recovery to that point should be possible
    And recovered data should be consistent
    And the recovery process should be documented

  @mvp-p1
  Scenario: Recovery time objective is met
    Given the RTO is 4 hours
    When a simulated disaster recovery is performed
    Then full service should be restored within 4 hours
    And all data up to RPO should be available
    And recovery steps should be logged for audit

  @mvp-p2
  Scenario: Backup verification through restore testing
    Given monthly restore testing is scheduled
    When the restore test runs
    Then a backup should be restored to a test environment
    And data integrity checks should pass
    And application functionality should be verified
    And a test report should be generated

  # ===========================================================================
  # Data Lifecycle Management - MVP-P2
  # ===========================================================================
  # Business Rule: Data has lifecycle states (active, archived, deleted) with
  # appropriate handling for each.

  @mvp-p2
  Scenario: Archiving old project data
    Given project "Q1 Analysis" completed 6 months ago
    And an archival policy of 90 days after completion
    When the archival job runs
    Then the project should be moved to archive storage
    And it should still be searchable with "archived" flag
    And detailed data should be in cold storage
    And key decisions should remain quickly accessible

  @mvp-p2
  Scenario: Soft delete with recovery window
    When Jordan deletes an exploration
    Then the exploration should be marked as deleted
    And it should be recoverable for 30 days
    And it should not appear in normal listings
    And permanent deletion should occur after 30 days

  @mvp-p2
  Scenario: Data export for portability
    Given Jordan wants to export project data
    When Jordan requests a data export
    Then a complete export package should be generated
    And it should include all project data in portable format
    And the format should be documented for import elsewhere
    And the export should be downloadable

  # ===========================================================================
  # Checkpoints and Versioning - MVP-P1
  # ===========================================================================
  # Business Rule: Users can create named checkpoints of their work and
  # revert to previous states if needed.

  @mvp-p1
  Scenario: Creating a named checkpoint
    Given Jordan has an exploration at a significant milestone
    When Jordan creates checkpoint "Before optimization changes"
    Then the current state should be saved as a checkpoint
    And the checkpoint should have a timestamp
    And it should be listed in available checkpoints

  @mvp-p1
  Scenario: Reverting to a previous checkpoint
    Given checkpoints:
      | name                       | date       |
      | Before optimization changes| 2024-01-10 |
      | After initial analysis     | 2024-01-08 |
    When Jordan reverts to "Before optimization changes"
    Then the exploration should return to that state
    And current state should be preserved as backup
    And a reversion record should be logged

  @mvp-p1
  Scenario: Comparing current state to checkpoint
    Given a checkpoint from 3 days ago
    When Jordan compares current state to the checkpoint
    Then differences should be highlighted:
      | change_type    | count |
      | added_thoughts | 12    |
      | removed_thoughts| 3    |
      | modified_scores| 8     |

  # ===========================================================================
  # Multi-Tenant Data Isolation - MVP-P2
  # ===========================================================================
  # Business Rule: In multi-tenant deployments, each tenant's data must be
  # completely isolated from other tenants.

  @mvp-p2 @critical
  Scenario: Tenant data is isolated in storage
    Given tenants "AcmeCorp" and "GlobalInc"
    When user from "AcmeCorp" queries for projects
    Then only "AcmeCorp" projects should be returned
    And "GlobalInc" data should never be accessible
    And database queries should include tenant filtering

  @mvp-p2
  Scenario: Tenant-specific backup and recovery
    Given a recovery is needed for tenant "AcmeCorp"
    When recovery is performed
    Then only "AcmeCorp" data should be affected
    And "GlobalInc" should have no downtime
    And tenant isolation should be maintained

  # ===========================================================================
  # Edge Cases - Post-MVP
  # ===========================================================================

  @post-mvp @wip
  Scenario: Handling storage quota exhaustion
    Given a tenant approaching their storage quota
    When the quota is reached
    Then new writes should be blocked with clear message
    And existing data should remain accessible
    And quota increase should be requestable
    And admins should be notified

  @post-mvp @wip
  Scenario: Graceful degradation during storage issues
    Given the primary database is experiencing latency
    When operations continue
    Then read operations should use read replicas
    And write operations should be queued if possible
    And users should see degraded mode notification
    And no data should be lost
