"""
Enum Consistency Tests

These tests verify that:
1. Enums are the same class when imported from different paths within domain
2. Enum comparisons work correctly with domain models
3. BDD scenarios can compare enums reliably

CONTEXT: All domain models and enums live in graph_of_thought.domain.
This is the single source of truth.

Run with: pytest tests/test_backwards_compatibility.py -v
"""

import pytest
from pathlib import Path
import sys

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Test 1: Enum Identity Within Domain Layer
# =============================================================================

class TestEnumIdentity:
    """
    Enums imported from different domain paths must be identical classes.
    """

    def test_chunk_status_identity_domain_vs_step_import(self):
        """
        ChunkStatus imported from domain.enums and domain must be identical.
        """
        from graph_of_thought.domain.enums import ChunkStatus as EnumsChunkStatus
        from graph_of_thought.domain import ChunkStatus as DomainChunkStatus

        assert EnumsChunkStatus is DomainChunkStatus, \
            "ChunkStatus must be identical class across domain imports"

    def test_question_status_identity(self):
        """
        QuestionStatus from domain.enums must match domain top-level.
        """
        from graph_of_thought.domain.enums import QuestionStatus as EnumsQuestionStatus
        from graph_of_thought.domain import QuestionStatus as DomainQuestionStatus

        assert EnumsQuestionStatus is DomainQuestionStatus

    def test_question_priority_identity(self):
        """
        QuestionPriority from domain.enums must match domain top-level.
        """
        from graph_of_thought.domain.enums import QuestionPriority as EnumsQuestionPriority
        from graph_of_thought.domain import QuestionPriority as DomainQuestionPriority

        assert EnumsQuestionPriority is DomainQuestionPriority

    def test_thought_status_identity(self):
        """
        ThoughtStatus from domain.enums must match domain top-level.
        """
        from graph_of_thought.domain.enums import ThoughtStatus as EnumsThoughtStatus
        from graph_of_thought.domain import ThoughtStatus as DomainThoughtStatus

        assert EnumsThoughtStatus is DomainThoughtStatus

    def test_approval_status_identity(self):
        """
        ApprovalStatus from domain.enums must match domain top-level.
        """
        from graph_of_thought.domain.enums import ApprovalStatus as EnumsApprovalStatus
        from graph_of_thought.domain import ApprovalStatus as DomainApprovalStatus

        assert EnumsApprovalStatus is DomainApprovalStatus

    def test_priority_identity(self):
        """
        Priority from domain.enums must match domain top-level.
        """
        from graph_of_thought.domain.enums import Priority as EnumsPriority
        from graph_of_thought.domain import Priority as DomainPriority

        assert EnumsPriority is DomainPriority

    def test_resource_type_identity(self):
        """
        ResourceType from domain.enums must match domain top-level.
        """
        from graph_of_thought.domain.enums import ResourceType as EnumsResourceType
        from graph_of_thought.domain import ResourceType as DomainResourceType

        assert EnumsResourceType is DomainResourceType

    def test_project_status_identity(self):
        """
        ProjectStatus from domain.enums must match domain top-level.
        """
        from graph_of_thought.domain.enums import ProjectStatus as EnumsProjectStatus
        from graph_of_thought.domain import ProjectStatus as DomainProjectStatus

        assert EnumsProjectStatus is DomainProjectStatus


# =============================================================================
# Test 2: Enum Comparison Works With Domain Models
# =============================================================================

class TestEnumComparisonAcrossModules:
    """
    Enum comparisons must work correctly when:
    - An object is created in one module
    - Its enum attribute is compared in another module

    This is the typical BDD test pattern.
    """

    def test_chunk_status_comparison_with_domain_work_chunk(self):
        """
        WorkChunk created with domain model should compare correctly.
        """
        from graph_of_thought.domain import WorkChunk, ChunkStatus

        chunk = WorkChunk(
            id="test-chunk-1",
            name="Test Chunk",
            project="test-project",
            status=ChunkStatus.ACTIVE,
        )

        assert chunk.status == ChunkStatus.ACTIVE
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
        Thought created with domain model should compare correctly.
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
        Question created with domain model should compare correctly.
        """
        from graph_of_thought.domain import Question, QuestionStatus, QuestionPriority

        question = Question(
            id="q-1",
            question="Test question?",
            status=QuestionStatus.PENDING,
            priority=QuestionPriority.HIGH,
        )

        assert question.status == QuestionStatus.PENDING
        assert question.priority == QuestionPriority.HIGH

    def test_project_status_comparison_with_domain_project(self):
        """
        Project created with domain model should compare correctly.
        """
        from graph_of_thought.domain import Project, ProjectStatus

        project = Project(
            id="proj-1",
            name="Test Project",
            status=ProjectStatus.ACTIVE,
        )

        assert project.status == ProjectStatus.ACTIVE
        assert project.status is ProjectStatus.ACTIVE

    def test_enum_value_comparison_as_fallback(self):
        """
        Enum .value comparison works as fallback when needed.
        """
        from graph_of_thought.domain import ChunkStatus

        assert ChunkStatus.ACTIVE.value == "active"
        assert ChunkStatus.BLOCKED.value == "blocked"
        assert ChunkStatus.COMPLETED.value == "completed"


# =============================================================================
# Test 3: BDD Scenario Simulation
# =============================================================================

class TestBDDScenarioSimulation:
    """
    Simulate typical BDD patterns to ensure they work correctly.
    """

    def test_knowledge_service_work_chunk_flow(self):
        """
        Simulate: Knowledge service creates chunk, step checks status.
        """
        from graph_of_thought.domain import WorkChunk, ChunkStatus

        # Service creates chunk
        chunk = WorkChunk(
            id="CHUNK-001",
            name="Analysis",
            project="Customer Analysis",
            status=ChunkStatus.ACTIVE,
        )

        # Step checks status (typical assertion)
        assert chunk.status == ChunkStatus.ACTIVE, \
            f"Expected ACTIVE, got {chunk.status}"

        # Update status
        chunk.status = ChunkStatus.BLOCKED

        # Check updated status
        assert chunk.status == ChunkStatus.BLOCKED

    def test_question_routing_flow(self):
        """
        Simulate: Question service creates ticket, step checks priority.
        """
        from graph_of_thought.domain import QuestionTicket, Priority

        # Service creates ticket
        ticket = QuestionTicket(
            id="Q-001",
            question="How do we handle X?",
            priority=Priority.HIGH,
            status="pending",
        )

        # Step checks priority
        assert ticket.priority == Priority.HIGH

        # Routing based on priority
        if ticket.priority == Priority.CRITICAL:
            route_to = "immediate"
        elif ticket.priority == Priority.HIGH:
            route_to = "same_day"
        else:
            route_to = "backlog"

        assert route_to == "same_day"
