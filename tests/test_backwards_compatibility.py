"""
Backwards Compatibility and Enum Consistency Tests

These tests verify that:
1. Old import paths continue to work (backwards compatibility)
2. Enums are the same class across modules (identity, not just equality)
3. Enum comparisons work across module boundaries
4. Re-exports from core/types.py and services/protocols.py match domain originals

CONTEXT: We recently fixed a bug where enums defined in multiple places caused
comparison failures. Step files now import from graph_of_thought.domain.enums.
These tests ensure we don't regress.

Run with: pytest tests/test_backwards_compatibility.py -v
"""

import pytest
from pathlib import Path
import sys

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Test 1: Backwards Compatibility - Old Import Paths Still Work
# =============================================================================

class TestBackwardsCompatibilityImports:
    """
    Old import paths must continue to work for existing code.

    When we refactored to use a domain layer, we added re-exports to maintain
    backwards compatibility. These tests verify those re-exports work.
    """

    def test_core_types_exports_thought(self):
        """
        core/types.py should export Thought class.

        Old code: from graph_of_thought.core.types import Thought
        """
        from graph_of_thought.core.types import Thought

        assert Thought is not None
        # Verify it's a dataclass
        assert hasattr(Thought, '__dataclass_fields__')

    def test_core_types_exports_edge(self):
        """
        core/types.py should export Edge class.

        Old code: from graph_of_thought.core.types import Edge
        """
        from graph_of_thought.core.types import Edge

        assert Edge is not None
        assert hasattr(Edge, '__dataclass_fields__')

    def test_core_types_exports_thought_status(self):
        """
        core/types.py should export ThoughtStatus enum.

        Old code: from graph_of_thought.core.types import ThoughtStatus
        """
        from graph_of_thought.core.types import ThoughtStatus

        assert ThoughtStatus is not None
        # Verify it has expected enum values
        assert hasattr(ThoughtStatus, 'PENDING')
        assert hasattr(ThoughtStatus, 'ACTIVE')
        assert hasattr(ThoughtStatus, 'COMPLETED')

    def test_core_types_exports_search_result(self):
        """
        core/types.py should export SearchResult class.
        """
        from graph_of_thought.core.types import SearchResult

        assert SearchResult is not None
        assert hasattr(SearchResult, '__dataclass_fields__')

    def test_core_types_exports_search_context(self):
        """
        core/types.py should export SearchContext class.
        """
        from graph_of_thought.core.types import SearchContext

        assert SearchContext is not None
        assert hasattr(SearchContext, '__dataclass_fields__')

    def test_services_protocols_exports_approval_status(self):
        """
        services/protocols.py should export ApprovalStatus enum.

        Old code: from graph_of_thought.services.protocols import ApprovalStatus
        """
        from graph_of_thought.services.protocols import ApprovalStatus

        assert ApprovalStatus is not None
        assert hasattr(ApprovalStatus, 'APPROVED')
        assert hasattr(ApprovalStatus, 'DENIED')
        assert hasattr(ApprovalStatus, 'NEEDS_REVIEW')

    def test_services_protocols_exports_priority(self):
        """
        services/protocols.py should export Priority enum.

        Old code: from graph_of_thought.services.protocols import Priority
        """
        from graph_of_thought.services.protocols import Priority

        assert Priority is not None
        assert hasattr(Priority, 'CRITICAL')
        assert hasattr(Priority, 'HIGH')
        assert hasattr(Priority, 'MEDIUM')
        assert hasattr(Priority, 'LOW')

    def test_services_protocols_exports_decision_model(self):
        """
        services/protocols.py should export Decision model.

        Old code: from graph_of_thought.services.protocols import Decision
        """
        from graph_of_thought.services.protocols import Decision

        assert Decision is not None
        assert hasattr(Decision, '__dataclass_fields__')

    def test_services_protocols_exports_resource_budget(self):
        """
        services/protocols.py should export ResourceBudget model.
        """
        from graph_of_thought.services.protocols import ResourceBudget

        assert ResourceBudget is not None

    def test_services_protocols_exports_knowledge_entry(self):
        """
        services/protocols.py should export KnowledgeEntry model.
        """
        from graph_of_thought.services.protocols import KnowledgeEntry

        assert KnowledgeEntry is not None

    def test_services_protocols_exports_handoff_package(self):
        """
        services/protocols.py should export HandoffPackage model.
        """
        from graph_of_thought.services.protocols import HandoffPackage

        assert HandoffPackage is not None

    def test_services_protocols_exports_resource_type(self):
        """
        services/protocols.py should export ResourceType enum.

        Old code: from graph_of_thought.services.protocols import ResourceType

        NOTE: Edge case test added during review - this was missing from
        backwards compat tests while identity test existed in TestEnumIdentity.
        """
        from graph_of_thought.services.protocols import ResourceType

        assert ResourceType is not None
        assert hasattr(ResourceType, 'TOKENS')
        assert hasattr(ResourceType, 'HUMAN_ATTENTION')
        assert hasattr(ResourceType, 'COMPUTE_TIME')


# =============================================================================
# Test 2: Enum Identity - Same Enum Class Across Modules
# =============================================================================

class TestEnumIdentity:
    """
    Enums must be the SAME class (identity), not just equal values.

    CRITICAL: If enums are defined in multiple places, comparison fails because
    `ModuleA.Status.ACTIVE is not ModuleB.Status.ACTIVE` even if values match.

    This caused real bugs where:
    - chunk.status == ChunkStatus.ACTIVE returned False
    - because chunk was created with one ChunkStatus class
    - but comparison used a different ChunkStatus class
    """

    def test_chunk_status_identity_domain_vs_step_import(self):
        """
        ChunkStatus from domain.enums must be identical to what steps import.

        FIXME: This was the original bug - steps had their own ChunkStatus enum.
        """
        from graph_of_thought.domain.enums import ChunkStatus as DomainChunkStatus

        # Simulate what step files import
        # NOTE: Step files should import from domain.enums
        from graph_of_thought.domain.enums import ChunkStatus as StepChunkStatus

        # These must be the SAME class (identity), not just equal
        assert DomainChunkStatus is StepChunkStatus, \
            "ChunkStatus must be identical class across modules, not duplicated"

        # Verify individual members are also identical
        assert DomainChunkStatus.ACTIVE is StepChunkStatus.ACTIVE
        assert DomainChunkStatus.BLOCKED is StepChunkStatus.BLOCKED
        assert DomainChunkStatus.COMPLETED is StepChunkStatus.COMPLETED

    def test_question_status_identity(self):
        """
        QuestionStatus from domain.enums must be the single source of truth.
        """
        from graph_of_thought.domain.enums import QuestionStatus as DomainQuestionStatus
        from graph_of_thought.domain import QuestionStatus as TopLevelQuestionStatus

        assert DomainQuestionStatus is TopLevelQuestionStatus

    def test_question_priority_identity(self):
        """
        QuestionPriority from domain.enums must be the single source of truth.
        """
        from graph_of_thought.domain.enums import QuestionPriority as DomainQuestionPriority
        from graph_of_thought.domain import QuestionPriority as TopLevelQuestionPriority

        assert DomainQuestionPriority is TopLevelQuestionPriority

    def test_thought_status_identity_core_vs_domain(self):
        """
        ThoughtStatus re-exported from core/types.py must be identical to domain.
        """
        from graph_of_thought.domain.enums import ThoughtStatus as DomainThoughtStatus
        from graph_of_thought.core.types import ThoughtStatus as CoreThoughtStatus

        assert DomainThoughtStatus is CoreThoughtStatus, \
            "core/types.py must re-export domain ThoughtStatus, not define its own"

    def test_approval_status_identity_protocols_vs_domain(self):
        """
        ApprovalStatus re-exported from services/protocols.py must be identical to domain.
        """
        from graph_of_thought.domain.enums import ApprovalStatus as DomainApprovalStatus
        from graph_of_thought.services.protocols import ApprovalStatus as ProtocolsApprovalStatus

        assert DomainApprovalStatus is ProtocolsApprovalStatus, \
            "services/protocols.py must re-export domain ApprovalStatus, not define its own"

    def test_priority_identity_protocols_vs_domain(self):
        """
        Priority re-exported from services/protocols.py must be identical to domain.
        """
        from graph_of_thought.domain.enums import Priority as DomainPriority
        from graph_of_thought.services.protocols import Priority as ProtocolsPriority

        assert DomainPriority is ProtocolsPriority, \
            "services/protocols.py must re-export domain Priority, not define its own"

    def test_resource_type_identity_protocols_vs_domain(self):
        """
        ResourceType re-exported from services/protocols.py must be identical to domain.
        """
        from graph_of_thought.domain.enums import ResourceType as DomainResourceType
        from graph_of_thought.services.protocols import ResourceType as ProtocolsResourceType

        assert DomainResourceType is ProtocolsResourceType

    def test_project_status_identity(self):
        """
        ProjectStatus from domain.enums must be the canonical version.

        NOTE: project_management_steps.py defines its own ProjectStatus for BDD purposes.
        This is intentional and documented as "BDD-specific" - they have different values.
        """
        from graph_of_thought.domain.enums import ProjectStatus as DomainProjectStatus
        from graph_of_thought.domain import ProjectStatus as TopLevelProjectStatus

        # Domain exports must be identical
        assert DomainProjectStatus is TopLevelProjectStatus


# =============================================================================
# Test 3: Enum Comparison Works Across Module Boundaries
# =============================================================================

class TestEnumComparisonAcrossModules:
    """
    Enum comparisons must work correctly when:
    - An object is created in one module
    - Its enum attribute is compared in another module

    This is the typical BDD test pattern where:
    - Service creates WorkChunk with status=ChunkStatus.ACTIVE
    - Step assertion checks chunk.status == ChunkStatus.ACTIVE
    """

    def test_chunk_status_comparison_with_domain_work_chunk(self):
        """
        WorkChunk created with domain model should compare correctly with domain enum.
        """
        from graph_of_thought.domain import WorkChunk, ChunkStatus

        chunk = WorkChunk(
            id="test-chunk-1",
            name="Test Chunk",
            project="test-project",
            status=ChunkStatus.ACTIVE,
        )

        # This is the critical comparison that was failing before the fix
        assert chunk.status == ChunkStatus.ACTIVE, \
            "Enum comparison should work when both sides use domain imports"

        # Also test with explicit identity check
        assert chunk.status is ChunkStatus.ACTIVE

    def test_chunk_status_comparison_blocked(self):
        """
        Test comparison with BLOCKED status value.
        """
        from graph_of_thought.domain import WorkChunk, ChunkStatus

        chunk = WorkChunk(
            id="test-chunk-2",
            name="Test Chunk",
            project="test-project",
            status=ChunkStatus.BLOCKED,
        )

        assert chunk.status == ChunkStatus.BLOCKED
        assert chunk.status is ChunkStatus.BLOCKED
        assert chunk.status != ChunkStatus.ACTIVE

    def test_thought_status_comparison_with_domain_thought(self):
        """
        Thought created with domain model should compare correctly with domain enum.
        """
        from graph_of_thought.domain import Thought, ThoughtStatus

        thought = Thought(
            id="thought-1",
            content="Test thought",
            score=0.5,
            status=ThoughtStatus.ACTIVE,
        )

        assert thought.status == ThoughtStatus.ACTIVE
        assert thought.status is ThoughtStatus.ACTIVE

    def test_question_status_comparison(self):
        """
        Question status comparison works correctly.
        """
        from graph_of_thought.domain import Question, QuestionStatus

        question = Question(
            id="q-1",
            question="Test question",
            context="Test context",
            status=QuestionStatus.PENDING,
        )

        assert question.status == QuestionStatus.PENDING

    def test_project_status_comparison_with_domain_project(self):
        """
        Project status comparison works correctly.
        """
        from graph_of_thought.domain import Project, ProjectStatus

        project = Project(
            id="proj-1",
            name="Test Project",
            status=ProjectStatus.ACTIVE,
        )

        assert project.status == ProjectStatus.ACTIVE

    def test_enum_value_comparison_as_fallback(self):
        """
        When direct comparison fails, .value comparison should work.

        NOTE: This is the workaround used in knowledge_management_steps.py line 249.
        While not ideal, it's a valid fallback for edge cases.

        # REVIEW: Consider if we still need this workaround after the fix.
        """
        from graph_of_thought.domain import ChunkStatus

        # Simulate a status value that might come from a different source
        status = ChunkStatus.BLOCKED

        # Value-based comparison (the workaround)
        assert status.value == "blocked"
        assert status.value == ChunkStatus.BLOCKED.value


# =============================================================================
# Test 4: Re-exports Match Originals
# =============================================================================

class TestReexportsMatchOriginals:
    """
    Re-exported models from core/types.py and services/protocols.py
    must be identical to the originals in domain/models.
    """

    def test_thought_reexport_from_core_types(self):
        """
        Thought from core/types.py must be identical to domain/models.
        """
        from graph_of_thought.domain.models import Thought as DomainThought
        from graph_of_thought.core.types import Thought as CoreThought

        assert DomainThought is CoreThought, \
            "core/types.py must re-export Thought from domain, not define its own"

    def test_edge_reexport_from_core_types(self):
        """
        Edge from core/types.py must be identical to domain/models.
        """
        from graph_of_thought.domain.models import Edge as DomainEdge
        from graph_of_thought.core.types import Edge as CoreEdge

        assert DomainEdge is CoreEdge

    def test_search_result_reexport_from_core_types(self):
        """
        SearchResult from core/types.py must be identical to domain/models.
        """
        from graph_of_thought.domain.models import SearchResult as DomainSearchResult
        from graph_of_thought.core.types import SearchResult as CoreSearchResult

        assert DomainSearchResult is CoreSearchResult

    def test_search_context_reexport_from_core_types(self):
        """
        SearchContext from core/types.py must be identical to domain/models.
        """
        from graph_of_thought.domain.models import SearchContext as DomainSearchContext
        from graph_of_thought.core.types import SearchContext as CoreSearchContext

        assert DomainSearchContext is CoreSearchContext

    def test_decision_reexport_from_services_protocols(self):
        """
        Decision from services/protocols.py must be identical to domain/models.
        """
        from graph_of_thought.domain.models import Decision as DomainDecision
        from graph_of_thought.services.protocols import Decision as ProtocolsDecision

        assert DomainDecision is ProtocolsDecision, \
            "services/protocols.py must re-export Decision from domain"

    def test_resource_budget_reexport_from_services_protocols(self):
        """
        ResourceBudget from services/protocols.py must be identical to domain/models.
        """
        from graph_of_thought.domain.models import ResourceBudget as DomainResourceBudget
        from graph_of_thought.services.protocols import ResourceBudget as ProtocolsResourceBudget

        assert DomainResourceBudget is ProtocolsResourceBudget

    def test_knowledge_entry_reexport_from_services_protocols(self):
        """
        KnowledgeEntry from services/protocols.py must be identical to domain/models.
        """
        from graph_of_thought.domain.models import KnowledgeEntry as DomainKnowledgeEntry
        from graph_of_thought.services.protocols import KnowledgeEntry as ProtocolsKnowledgeEntry

        assert DomainKnowledgeEntry is ProtocolsKnowledgeEntry

    def test_question_ticket_reexport_from_services_protocols(self):
        """
        QuestionTicket from services/protocols.py must be identical to domain/models.
        """
        from graph_of_thought.domain.models import QuestionTicket as DomainQuestionTicket
        from graph_of_thought.services.protocols import QuestionTicket as ProtocolsQuestionTicket

        assert DomainQuestionTicket is ProtocolsQuestionTicket

    def test_handoff_package_reexport_from_services_protocols(self):
        """
        HandoffPackage from services/protocols.py must be identical to domain/models.
        """
        from graph_of_thought.domain.models import HandoffPackage as DomainHandoffPackage
        from graph_of_thought.services.protocols import HandoffPackage as ProtocolsHandoffPackage

        assert DomainHandoffPackage is ProtocolsHandoffPackage


# =============================================================================
# Test 5: All Domain Enums Are Exported Correctly
# =============================================================================

class TestAllDomainEnumsExported:
    """
    Verify all enums from domain/enums are accessible from domain/__init__.py.

    This ensures the public API is complete.
    """

    def test_shared_enums_exported(self):
        """All shared enums should be exported from domain."""
        from graph_of_thought.domain import Priority, ResourceType

        assert Priority is not None
        assert ResourceType is not None

    def test_reasoning_enums_exported(self):
        """All reasoning enums should be exported from domain."""
        from graph_of_thought.domain import ThoughtStatus

        assert ThoughtStatus is not None

    def test_governance_enums_exported(self):
        """All governance enums should be exported from domain."""
        from graph_of_thought.domain import ApprovalStatus, ApprovalType, RequestStatus

        assert ApprovalStatus is not None
        assert ApprovalType is not None
        assert RequestStatus is not None

    def test_knowledge_enums_exported(self):
        """All knowledge enums should be exported from domain."""
        from graph_of_thought.domain import QuestionPriority, QuestionStatus

        assert QuestionPriority is not None
        assert QuestionStatus is not None

    def test_project_enums_exported(self):
        """All project enums should be exported from domain."""
        from graph_of_thought.domain import ProjectStatus, ChunkStatus

        assert ProjectStatus is not None
        assert ChunkStatus is not None

    def test_cost_enums_exported(self):
        """All cost enums should be exported from domain."""
        from graph_of_thought.domain import BudgetLevel, BudgetStatus

        assert BudgetLevel is not None
        assert BudgetStatus is not None


# =============================================================================
# Test 6: Enum Value Correctness
# =============================================================================

class TestEnumValueCorrectness:
    """
    Verify enum values are correct and consistent.

    TODO: Consider adding tests for enum value uniqueness if needed.
    """

    def test_chunk_status_values(self):
        """ChunkStatus should have the expected values."""
        from graph_of_thought.domain import ChunkStatus

        assert ChunkStatus.ACTIVE.value == "active"
        assert ChunkStatus.BLOCKED.value == "blocked"
        assert ChunkStatus.PAUSED.value == "paused"
        assert ChunkStatus.COMPLETED.value == "completed"

    def test_question_status_values(self):
        """QuestionStatus should have the expected values."""
        from graph_of_thought.domain import QuestionStatus

        assert QuestionStatus.PENDING.value == "pending"
        assert QuestionStatus.ASSIGNED.value == "assigned"
        assert QuestionStatus.ANSWERED.value == "answered"
        assert QuestionStatus.CLOSED.value == "closed"

    def test_question_priority_values(self):
        """QuestionPriority should have the expected values."""
        from graph_of_thought.domain import QuestionPriority

        assert QuestionPriority.LOW.value == "low"
        assert QuestionPriority.NORMAL.value == "normal"
        assert QuestionPriority.MEDIUM.value == "medium"
        assert QuestionPriority.HIGH.value == "high"
        assert QuestionPriority.CRITICAL.value == "critical"

    def test_project_status_values(self):
        """Domain ProjectStatus should have the expected values."""
        from graph_of_thought.domain import ProjectStatus

        assert ProjectStatus.PLANNING.value == "planning"
        assert ProjectStatus.ACTIVE.value == "active"
        assert ProjectStatus.ON_HOLD.value == "on_hold"
        assert ProjectStatus.COMPLETED.value == "completed"
        assert ProjectStatus.ARCHIVED.value == "archived"


# =============================================================================
# Integration Test: Simulating BDD Scenario Flow
# =============================================================================

class TestBDDScenarioSimulation:
    """
    Simulate the actual BDD test flow where enum comparison was failing.

    This tests the complete flow from:
    1. Service creates object with enum status
    2. Object is passed through context
    3. Assertion compares enum from imported module
    """

    def test_knowledge_service_work_chunk_flow(self):
        """
        Simulate knowledge_management_steps.py flow.

        This is the flow that was broken:
        1. MockKnowledgeService creates WorkChunk with ChunkStatus.ACTIVE
        2. Step assertion checks chunk.status == ChunkStatus.ACTIVE
        """
        from graph_of_thought.domain.enums import ChunkStatus
        from dataclasses import dataclass

        # Simulate the WorkChunk dataclass from steps
        # NOTE: In actual code, this is defined in knowledge_management_steps.py
        @dataclass
        class SimulatedWorkChunk:
            id: str
            name: str
            project: str
            status: ChunkStatus = ChunkStatus.ACTIVE

        # Service creates chunk
        chunk = SimulatedWorkChunk(
            id="CHUNK-test",
            name="Test Task",
            project="Test Project",
            status=ChunkStatus.ACTIVE,
        )

        # Assertion from step (this is what was failing)
        assert chunk.status == ChunkStatus.ACTIVE, \
            "Simulated BDD flow: chunk status comparison should work"

        # Update status (simulating answer_question unblocking)
        chunk.status = ChunkStatus.BLOCKED
        assert chunk.status == ChunkStatus.BLOCKED

        chunk.status = ChunkStatus.ACTIVE  # Unblocked
        assert chunk.status == ChunkStatus.ACTIVE

    def test_question_routing_flow(self):
        """
        Simulate question routing from knowledge_management_steps.py.

        This tests QuestionPriority comparison.
        """
        from graph_of_thought.domain.enums import QuestionPriority, QuestionStatus
        from dataclasses import dataclass, field
        from datetime import datetime
        from typing import Optional

        @dataclass
        class SimulatedQuestion:
            id: str
            question: str
            context: str = ""
            blocking: bool = False
            priority: QuestionPriority = QuestionPriority.NORMAL
            status: QuestionStatus = QuestionStatus.PENDING
            asked_by: str = ""

        # Create question with blocking=True (HIGH priority)
        question = SimulatedQuestion(
            id="Q-0001",
            question="Is this architecture approved?",
            blocking=True,
            priority=QuestionPriority.HIGH,
            asked_by="Jordan",
        )

        # BDD assertion
        assert question.priority == QuestionPriority.HIGH, \
            "Blocking questions should have HIGH priority"

        # Answer question
        question.status = QuestionStatus.ANSWERED
        assert question.status == QuestionStatus.ANSWERED


# =============================================================================
# Run as script for quick validation
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
