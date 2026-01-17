"""
Unit tests for domain enums in graph_of_thought/domain/enums/.

Tests verify:
1. Each enum can be imported from graph_of_thought.domain.enums
2. Each enum can be imported from graph_of_thought.domain (top-level)
3. Each enum has expected values (verify actual string/int values)
4. Enum members can be compared correctly
5. Enum members can be serialized/deserialized via .value and Enum(value)

Run with:
    python -m pytest tests/test_domain_enums.py -v

NOTE: The package must be installed in development mode (`pip install -e .`)
for imports to work correctly. Using `pytest` directly may fail if pytest
uses an isolated environment without the package installed.
"""

import pytest
from enum import Enum, auto


# ===========================================================================
# Import Tests - graph_of_thought.domain.enums
# ===========================================================================

class TestEnumImportsFromEnumsPackage:
    """Test that all enums can be imported from graph_of_thought.domain.enums."""

    def test_import_shared_enums_from_enums_package(self):
        """Priority and ResourceType should be importable from domain.enums."""
        from graph_of_thought.domain.enums import Priority, ResourceType
        assert Priority is not None
        assert ResourceType is not None

    def test_import_reasoning_enums_from_enums_package(self):
        """ThoughtStatus should be importable from domain.enums."""
        from graph_of_thought.domain.enums import ThoughtStatus
        assert ThoughtStatus is not None

    def test_import_governance_enums_from_enums_package(self):
        """ApprovalStatus, ApprovalType, RequestStatus should be importable from domain.enums."""
        from graph_of_thought.domain.enums import ApprovalStatus, ApprovalType, RequestStatus
        assert ApprovalStatus is not None
        assert ApprovalType is not None
        assert RequestStatus is not None

    def test_import_knowledge_enums_from_enums_package(self):
        """QuestionPriority, QuestionStatus should be importable from domain.enums."""
        from graph_of_thought.domain.enums import QuestionPriority, QuestionStatus
        assert QuestionPriority is not None
        assert QuestionStatus is not None

    def test_import_project_enums_from_enums_package(self):
        """ProjectStatus, ChunkStatus should be importable from domain.enums."""
        from graph_of_thought.domain.enums import ProjectStatus, ChunkStatus
        assert ProjectStatus is not None
        assert ChunkStatus is not None

    def test_import_cost_enums_from_enums_package(self):
        """BudgetLevel, BudgetStatus should be importable from domain.enums."""
        from graph_of_thought.domain.enums import BudgetLevel, BudgetStatus
        assert BudgetLevel is not None
        assert BudgetStatus is not None


# ===========================================================================
# Import Tests - graph_of_thought.domain (top-level)
# ===========================================================================

class TestEnumImportsFromDomainPackage:
    """Test that all enums can be imported from graph_of_thought.domain (top-level)."""

    def test_import_shared_enums_from_domain(self):
        """Priority and ResourceType should be importable from domain."""
        from graph_of_thought.domain import Priority, ResourceType
        assert Priority is not None
        assert ResourceType is not None

    def test_import_reasoning_enums_from_domain(self):
        """ThoughtStatus should be importable from domain."""
        from graph_of_thought.domain import ThoughtStatus
        assert ThoughtStatus is not None

    def test_import_governance_enums_from_domain(self):
        """ApprovalStatus, ApprovalType, RequestStatus should be importable from domain."""
        from graph_of_thought.domain import ApprovalStatus, ApprovalType, RequestStatus
        assert ApprovalStatus is not None
        assert ApprovalType is not None
        assert RequestStatus is not None

    def test_import_knowledge_enums_from_domain(self):
        """QuestionPriority, QuestionStatus should be importable from domain."""
        from graph_of_thought.domain import QuestionPriority, QuestionStatus
        assert QuestionPriority is not None
        assert QuestionStatus is not None

    def test_import_project_enums_from_domain(self):
        """ProjectStatus, ChunkStatus should be importable from domain."""
        from graph_of_thought.domain import ProjectStatus, ChunkStatus
        assert ProjectStatus is not None
        assert ChunkStatus is not None

    def test_import_cost_enums_from_domain(self):
        """BudgetLevel, BudgetStatus should be importable from domain."""
        from graph_of_thought.domain import BudgetLevel, BudgetStatus
        assert BudgetLevel is not None
        assert BudgetStatus is not None


# ===========================================================================
# shared.py - Priority and ResourceType
# ===========================================================================

class TestPriorityEnum:
    """Tests for the Priority enum from shared.py."""

    def test_priority_has_expected_members(self):
        """Priority should have CRITICAL, HIGH, MEDIUM, LOW, BACKLOG members."""
        from graph_of_thought.domain import Priority
        expected_members = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "BACKLOG"}
        actual_members = {member.name for member in Priority}
        assert actual_members == expected_members

    def test_priority_uses_auto_values(self):
        """Priority members should use auto() integer values."""
        from graph_of_thought.domain import Priority
        # NOTE: auto() generates sequential integers starting from 1
        assert isinstance(Priority.CRITICAL.value, int)
        assert isinstance(Priority.HIGH.value, int)
        assert isinstance(Priority.MEDIUM.value, int)
        assert isinstance(Priority.LOW.value, int)
        assert isinstance(Priority.BACKLOG.value, int)

    def test_priority_values_are_sequential(self):
        """Priority auto() values should be sequential integers."""
        from graph_of_thought.domain import Priority
        values = [Priority.CRITICAL.value, Priority.HIGH.value,
                  Priority.MEDIUM.value, Priority.LOW.value, Priority.BACKLOG.value]
        # Values should be 1, 2, 3, 4, 5 (auto() starts at 1)
        assert values == [1, 2, 3, 4, 5]

    def test_priority_member_comparison(self):
        """Priority members should be comparable for equality."""
        from graph_of_thought.domain import Priority
        assert Priority.CRITICAL == Priority.CRITICAL
        assert Priority.CRITICAL != Priority.LOW
        assert Priority.HIGH != Priority.MEDIUM

    def test_priority_identity(self):
        """Same Priority member should be identical (identity check)."""
        from graph_of_thought.domain import Priority
        p1 = Priority.CRITICAL
        p2 = Priority.CRITICAL
        assert p1 is p2

    def test_priority_serialization_deserialization(self):
        """Priority can be serialized via .value and deserialized via Priority(value)."""
        from graph_of_thought.domain import Priority
        original = Priority.HIGH
        serialized = original.value
        deserialized = Priority(serialized)
        assert deserialized == original


class TestResourceTypeEnum:
    """Tests for the ResourceType enum from shared.py."""

    def test_resource_type_has_expected_members(self):
        """ResourceType should have all expected resource types."""
        from graph_of_thought.domain import ResourceType
        expected_members = {"TOKENS", "HUMAN_ATTENTION", "COMPUTE_TIME",
                          "CALENDAR_TIME", "COST_DOLLARS"}
        actual_members = {member.name for member in ResourceType}
        assert actual_members == expected_members

    def test_resource_type_uses_auto_values(self):
        """ResourceType members should use auto() integer values."""
        from graph_of_thought.domain import ResourceType
        for member in ResourceType:
            assert isinstance(member.value, int)

    def test_resource_type_values_are_sequential(self):
        """ResourceType auto() values should be sequential integers."""
        from graph_of_thought.domain import ResourceType
        values = [ResourceType.TOKENS.value, ResourceType.HUMAN_ATTENTION.value,
                  ResourceType.COMPUTE_TIME.value, ResourceType.CALENDAR_TIME.value,
                  ResourceType.COST_DOLLARS.value]
        assert values == [1, 2, 3, 4, 5]

    def test_resource_type_member_comparison(self):
        """ResourceType members should be comparable for equality."""
        from graph_of_thought.domain import ResourceType
        assert ResourceType.TOKENS == ResourceType.TOKENS
        assert ResourceType.TOKENS != ResourceType.COST_DOLLARS

    def test_resource_type_serialization_deserialization(self):
        """ResourceType can be serialized and deserialized."""
        from graph_of_thought.domain import ResourceType
        original = ResourceType.TOKENS
        serialized = original.value
        deserialized = ResourceType(serialized)
        assert deserialized == original


# ===========================================================================
# reasoning.py - ThoughtStatus
# ===========================================================================

class TestThoughtStatusEnum:
    """Tests for the ThoughtStatus enum from reasoning.py."""

    def test_thought_status_has_expected_members(self):
        """ThoughtStatus should have all expected status values."""
        from graph_of_thought.domain import ThoughtStatus
        expected_members = {"PENDING", "ACTIVE", "COMPLETED", "PRUNED", "MERGED", "FAILED"}
        actual_members = {member.name for member in ThoughtStatus}
        assert actual_members == expected_members

    def test_thought_status_uses_auto_values(self):
        """ThoughtStatus members should use auto() integer values."""
        from graph_of_thought.domain import ThoughtStatus
        for member in ThoughtStatus:
            assert isinstance(member.value, int)

    def test_thought_status_values_are_sequential(self):
        """ThoughtStatus auto() values should be sequential integers."""
        from graph_of_thought.domain import ThoughtStatus
        values = [ThoughtStatus.PENDING.value, ThoughtStatus.ACTIVE.value,
                  ThoughtStatus.COMPLETED.value, ThoughtStatus.PRUNED.value,
                  ThoughtStatus.MERGED.value, ThoughtStatus.FAILED.value]
        assert values == [1, 2, 3, 4, 5, 6]

    def test_thought_status_member_comparison(self):
        """ThoughtStatus members should be comparable for equality."""
        from graph_of_thought.domain import ThoughtStatus
        assert ThoughtStatus.PENDING == ThoughtStatus.PENDING
        assert ThoughtStatus.ACTIVE != ThoughtStatus.COMPLETED
        assert ThoughtStatus.PRUNED != ThoughtStatus.MERGED

    def test_thought_status_serialization_deserialization(self):
        """ThoughtStatus can be serialized and deserialized."""
        from graph_of_thought.domain import ThoughtStatus
        original = ThoughtStatus.COMPLETED
        serialized = original.value
        deserialized = ThoughtStatus(serialized)
        assert deserialized == original


# ===========================================================================
# governance.py - ApprovalStatus, ApprovalType, RequestStatus
# ===========================================================================

class TestApprovalStatusEnum:
    """Tests for the ApprovalStatus enum from governance.py."""

    def test_approval_status_has_expected_members(self):
        """ApprovalStatus should have all expected status values."""
        from graph_of_thought.domain import ApprovalStatus
        expected_members = {"APPROVED", "DENIED", "NEEDS_REVIEW", "NEEDS_INFO", "CONDITIONAL"}
        actual_members = {member.name for member in ApprovalStatus}
        assert actual_members == expected_members

    def test_approval_status_uses_auto_values(self):
        """ApprovalStatus members should use auto() integer values."""
        from graph_of_thought.domain import ApprovalStatus
        for member in ApprovalStatus:
            assert isinstance(member.value, int)

    def test_approval_status_values_are_sequential(self):
        """ApprovalStatus auto() values should be sequential integers."""
        from graph_of_thought.domain import ApprovalStatus
        values = [ApprovalStatus.APPROVED.value, ApprovalStatus.DENIED.value,
                  ApprovalStatus.NEEDS_REVIEW.value, ApprovalStatus.NEEDS_INFO.value,
                  ApprovalStatus.CONDITIONAL.value]
        assert values == [1, 2, 3, 4, 5]

    def test_approval_status_member_comparison(self):
        """ApprovalStatus members should be comparable for equality."""
        from graph_of_thought.domain import ApprovalStatus
        assert ApprovalStatus.APPROVED == ApprovalStatus.APPROVED
        assert ApprovalStatus.APPROVED != ApprovalStatus.DENIED

    def test_approval_status_serialization_deserialization(self):
        """ApprovalStatus can be serialized and deserialized."""
        from graph_of_thought.domain import ApprovalStatus
        original = ApprovalStatus.NEEDS_REVIEW
        serialized = original.value
        deserialized = ApprovalStatus(serialized)
        assert deserialized == original


class TestApprovalTypeEnum:
    """Tests for the ApprovalType enum from governance.py."""

    def test_approval_type_has_expected_members(self):
        """ApprovalType should have STANDARD, EXPEDITED, EMERGENCY members."""
        from graph_of_thought.domain import ApprovalType
        expected_members = {"STANDARD", "EXPEDITED", "EMERGENCY"}
        actual_members = {member.name for member in ApprovalType}
        assert actual_members == expected_members

    def test_approval_type_uses_string_values(self):
        """ApprovalType members should use string values (not auto())."""
        from graph_of_thought.domain import ApprovalType
        # NOTE: ApprovalType uses explicit string values, not auto()
        assert ApprovalType.STANDARD.value == "standard"
        assert ApprovalType.EXPEDITED.value == "expedited"
        assert ApprovalType.EMERGENCY.value == "emergency"

    def test_approval_type_member_comparison(self):
        """ApprovalType members should be comparable for equality."""
        from graph_of_thought.domain import ApprovalType
        assert ApprovalType.STANDARD == ApprovalType.STANDARD
        assert ApprovalType.STANDARD != ApprovalType.EMERGENCY

    def test_approval_type_serialization_deserialization(self):
        """ApprovalType can be serialized and deserialized via string value."""
        from graph_of_thought.domain import ApprovalType
        original = ApprovalType.EXPEDITED
        serialized = original.value
        assert serialized == "expedited"
        deserialized = ApprovalType(serialized)
        assert deserialized == original


class TestRequestStatusEnum:
    """Tests for the RequestStatus enum from governance.py."""

    def test_request_status_has_expected_members(self):
        """RequestStatus should have all expected status values."""
        from graph_of_thought.domain import RequestStatus
        expected_members = {"PENDING", "APPROVED", "DENIED", "EXPIRED", "CANCELLED"}
        actual_members = {member.name for member in RequestStatus}
        assert actual_members == expected_members

    def test_request_status_uses_string_values(self):
        """RequestStatus members should use string values."""
        from graph_of_thought.domain import RequestStatus
        assert RequestStatus.PENDING.value == "pending"
        assert RequestStatus.APPROVED.value == "approved"
        assert RequestStatus.DENIED.value == "denied"
        assert RequestStatus.EXPIRED.value == "expired"
        assert RequestStatus.CANCELLED.value == "cancelled"

    def test_request_status_member_comparison(self):
        """RequestStatus members should be comparable for equality."""
        from graph_of_thought.domain import RequestStatus
        assert RequestStatus.PENDING == RequestStatus.PENDING
        assert RequestStatus.PENDING != RequestStatus.APPROVED

    def test_request_status_serialization_deserialization(self):
        """RequestStatus can be serialized and deserialized via string value."""
        from graph_of_thought.domain import RequestStatus
        original = RequestStatus.EXPIRED
        serialized = original.value
        assert serialized == "expired"
        deserialized = RequestStatus(serialized)
        assert deserialized == original


# ===========================================================================
# knowledge.py - QuestionPriority, QuestionStatus
# ===========================================================================

class TestQuestionPriorityEnum:
    """Tests for the QuestionPriority enum from knowledge.py."""

    def test_question_priority_has_expected_members(self):
        """QuestionPriority should have LOW, NORMAL, MEDIUM, HIGH, CRITICAL members."""
        from graph_of_thought.domain import QuestionPriority
        expected_members = {"LOW", "NORMAL", "MEDIUM", "HIGH", "CRITICAL"}
        actual_members = {member.name for member in QuestionPriority}
        assert actual_members == expected_members

    def test_question_priority_uses_string_values(self):
        """QuestionPriority members should use string values."""
        from graph_of_thought.domain import QuestionPriority
        assert QuestionPriority.LOW.value == "low"
        assert QuestionPriority.NORMAL.value == "normal"
        assert QuestionPriority.MEDIUM.value == "medium"
        assert QuestionPriority.HIGH.value == "high"
        assert QuestionPriority.CRITICAL.value == "critical"

    def test_question_priority_member_comparison(self):
        """QuestionPriority members should be comparable for equality."""
        from graph_of_thought.domain import QuestionPriority
        assert QuestionPriority.HIGH == QuestionPriority.HIGH
        assert QuestionPriority.LOW != QuestionPriority.CRITICAL

    def test_question_priority_serialization_deserialization(self):
        """QuestionPriority can be serialized and deserialized via string value."""
        from graph_of_thought.domain import QuestionPriority
        original = QuestionPriority.CRITICAL
        serialized = original.value
        assert serialized == "critical"
        deserialized = QuestionPriority(serialized)
        assert deserialized == original


class TestQuestionStatusEnum:
    """Tests for the QuestionStatus enum from knowledge.py."""

    def test_question_status_has_expected_members(self):
        """QuestionStatus should have PENDING, ASSIGNED, ANSWERED, CLOSED members."""
        from graph_of_thought.domain import QuestionStatus
        expected_members = {"PENDING", "ASSIGNED", "ANSWERED", "CLOSED"}
        actual_members = {member.name for member in QuestionStatus}
        assert actual_members == expected_members

    def test_question_status_uses_string_values(self):
        """QuestionStatus members should use string values."""
        from graph_of_thought.domain import QuestionStatus
        assert QuestionStatus.PENDING.value == "pending"
        assert QuestionStatus.ASSIGNED.value == "assigned"
        assert QuestionStatus.ANSWERED.value == "answered"
        assert QuestionStatus.CLOSED.value == "closed"

    def test_question_status_member_comparison(self):
        """QuestionStatus members should be comparable for equality."""
        from graph_of_thought.domain import QuestionStatus
        assert QuestionStatus.PENDING == QuestionStatus.PENDING
        assert QuestionStatus.PENDING != QuestionStatus.CLOSED

    def test_question_status_serialization_deserialization(self):
        """QuestionStatus can be serialized and deserialized via string value."""
        from graph_of_thought.domain import QuestionStatus
        original = QuestionStatus.ANSWERED
        serialized = original.value
        assert serialized == "answered"
        deserialized = QuestionStatus(serialized)
        assert deserialized == original


# ===========================================================================
# project.py - ProjectStatus, ChunkStatus
# ===========================================================================

class TestProjectStatusEnum:
    """Tests for the ProjectStatus enum from project.py."""

    def test_project_status_has_expected_members(self):
        """ProjectStatus should have all expected status values."""
        from graph_of_thought.domain import ProjectStatus
        expected_members = {"PLANNING", "ACTIVE", "ON_HOLD", "COMPLETED", "ARCHIVED"}
        actual_members = {member.name for member in ProjectStatus}
        assert actual_members == expected_members

    def test_project_status_uses_string_values(self):
        """ProjectStatus members should use string values."""
        from graph_of_thought.domain import ProjectStatus
        assert ProjectStatus.PLANNING.value == "planning"
        assert ProjectStatus.ACTIVE.value == "active"
        assert ProjectStatus.ON_HOLD.value == "on_hold"
        assert ProjectStatus.COMPLETED.value == "completed"
        assert ProjectStatus.ARCHIVED.value == "archived"

    def test_project_status_member_comparison(self):
        """ProjectStatus members should be comparable for equality."""
        from graph_of_thought.domain import ProjectStatus
        assert ProjectStatus.ACTIVE == ProjectStatus.ACTIVE
        assert ProjectStatus.PLANNING != ProjectStatus.COMPLETED

    def test_project_status_serialization_deserialization(self):
        """ProjectStatus can be serialized and deserialized via string value."""
        from graph_of_thought.domain import ProjectStatus
        original = ProjectStatus.ON_HOLD
        serialized = original.value
        assert serialized == "on_hold"
        deserialized = ProjectStatus(serialized)
        assert deserialized == original


class TestChunkStatusEnum:
    """Tests for the ChunkStatus enum from project.py."""

    def test_chunk_status_has_expected_members(self):
        """ChunkStatus should have ACTIVE, BLOCKED, PAUSED, COMPLETED members."""
        from graph_of_thought.domain import ChunkStatus
        expected_members = {"ACTIVE", "BLOCKED", "PAUSED", "COMPLETED"}
        actual_members = {member.name for member in ChunkStatus}
        assert actual_members == expected_members

    def test_chunk_status_uses_string_values(self):
        """ChunkStatus members should use string values."""
        from graph_of_thought.domain import ChunkStatus
        assert ChunkStatus.ACTIVE.value == "active"
        assert ChunkStatus.BLOCKED.value == "blocked"
        assert ChunkStatus.PAUSED.value == "paused"
        assert ChunkStatus.COMPLETED.value == "completed"

    def test_chunk_status_member_comparison(self):
        """ChunkStatus members should be comparable for equality."""
        from graph_of_thought.domain import ChunkStatus
        assert ChunkStatus.ACTIVE == ChunkStatus.ACTIVE
        assert ChunkStatus.BLOCKED != ChunkStatus.PAUSED

    def test_chunk_status_serialization_deserialization(self):
        """ChunkStatus can be serialized and deserialized via string value."""
        from graph_of_thought.domain import ChunkStatus
        original = ChunkStatus.BLOCKED
        serialized = original.value
        assert serialized == "blocked"
        deserialized = ChunkStatus(serialized)
        assert deserialized == original


# ===========================================================================
# cost.py - BudgetLevel, BudgetStatus
# ===========================================================================

class TestBudgetLevelEnum:
    """Tests for the BudgetLevel enum from cost.py."""

    def test_budget_level_has_expected_members(self):
        """BudgetLevel should have NORMAL, WARNING, CRITICAL, EXHAUSTED members."""
        from graph_of_thought.domain import BudgetLevel
        expected_members = {"NORMAL", "WARNING", "CRITICAL", "EXHAUSTED"}
        actual_members = {member.name for member in BudgetLevel}
        assert actual_members == expected_members

    def test_budget_level_uses_string_values(self):
        """BudgetLevel members should use string values."""
        from graph_of_thought.domain import BudgetLevel
        assert BudgetLevel.NORMAL.value == "normal"
        assert BudgetLevel.WARNING.value == "warning"
        assert BudgetLevel.CRITICAL.value == "critical"
        assert BudgetLevel.EXHAUSTED.value == "exhausted"

    def test_budget_level_member_comparison(self):
        """BudgetLevel members should be comparable for equality."""
        from graph_of_thought.domain import BudgetLevel
        assert BudgetLevel.NORMAL == BudgetLevel.NORMAL
        assert BudgetLevel.WARNING != BudgetLevel.CRITICAL

    def test_budget_level_serialization_deserialization(self):
        """BudgetLevel can be serialized and deserialized via string value."""
        from graph_of_thought.domain import BudgetLevel
        original = BudgetLevel.WARNING
        serialized = original.value
        assert serialized == "warning"
        deserialized = BudgetLevel(serialized)
        assert deserialized == original


class TestBudgetStatusEnum:
    """Tests for the BudgetStatus enum from cost.py."""

    def test_budget_status_has_expected_members(self):
        """BudgetStatus should have ACTIVE, FROZEN, CLOSED members."""
        from graph_of_thought.domain import BudgetStatus
        expected_members = {"ACTIVE", "FROZEN", "CLOSED"}
        actual_members = {member.name for member in BudgetStatus}
        assert actual_members == expected_members

    def test_budget_status_uses_string_values(self):
        """BudgetStatus members should use string values."""
        from graph_of_thought.domain import BudgetStatus
        assert BudgetStatus.ACTIVE.value == "active"
        assert BudgetStatus.FROZEN.value == "frozen"
        assert BudgetStatus.CLOSED.value == "closed"

    def test_budget_status_member_comparison(self):
        """BudgetStatus members should be comparable for equality."""
        from graph_of_thought.domain import BudgetStatus
        assert BudgetStatus.ACTIVE == BudgetStatus.ACTIVE
        assert BudgetStatus.FROZEN != BudgetStatus.CLOSED

    def test_budget_status_serialization_deserialization(self):
        """BudgetStatus can be serialized and deserialized via string value."""
        from graph_of_thought.domain import BudgetStatus
        original = BudgetStatus.FROZEN
        serialized = original.value
        assert serialized == "frozen"
        deserialized = BudgetStatus(serialized)
        assert deserialized == original


# ===========================================================================
# Cross-cutting concerns
# ===========================================================================

class TestEnumConsistency:
    """Tests for cross-cutting enum concerns and consistency."""

    def test_all_enums_are_proper_enum_subclasses(self):
        """All domain enums should be proper Enum subclasses."""
        from graph_of_thought.domain import (
            Priority, ResourceType, ThoughtStatus,
            ApprovalStatus, ApprovalType, RequestStatus,
            QuestionPriority, QuestionStatus,
            ProjectStatus, ChunkStatus,
            BudgetLevel, BudgetStatus,
        )
        all_enums = [
            Priority, ResourceType, ThoughtStatus,
            ApprovalStatus, ApprovalType, RequestStatus,
            QuestionPriority, QuestionStatus,
            ProjectStatus, ChunkStatus,
            BudgetLevel, BudgetStatus,
        ]
        for enum_class in all_enums:
            assert issubclass(enum_class, Enum), f"{enum_class.__name__} should be an Enum"

    def test_enum_members_are_not_directly_comparable_across_types(self):
        """Enum members from different enums should not be equal even if they have same name."""
        from graph_of_thought.domain import (
            ThoughtStatus, ProjectStatus, ChunkStatus,
            QuestionStatus, RequestStatus, BudgetStatus
        )
        # NOTE: Multiple enums have ACTIVE member but they should not be equal
        assert ThoughtStatus.ACTIVE != ProjectStatus.ACTIVE
        assert ChunkStatus.ACTIVE != BudgetStatus.ACTIVE
        # Multiple enums have PENDING member
        assert ThoughtStatus.PENDING != QuestionStatus.PENDING
        assert RequestStatus.PENDING != QuestionStatus.PENDING

    def test_string_valued_enums_can_be_json_serialized(self):
        """String-valued enums should have JSON-serializable values."""
        import json
        from graph_of_thought.domain import (
            ApprovalType, RequestStatus, QuestionPriority, QuestionStatus,
            ProjectStatus, ChunkStatus, BudgetLevel, BudgetStatus,
        )
        string_enums = [
            ApprovalType, RequestStatus, QuestionPriority, QuestionStatus,
            ProjectStatus, ChunkStatus, BudgetLevel, BudgetStatus,
        ]
        for enum_class in string_enums:
            for member in enum_class:
                # Should not raise
                serialized = json.dumps(member.value)
                assert isinstance(serialized, str)

    def test_auto_valued_enums_values_can_be_json_serialized(self):
        """Auto-valued (integer) enums should have JSON-serializable values."""
        import json
        from graph_of_thought.domain import (
            Priority, ResourceType, ThoughtStatus, ApprovalStatus,
        )
        auto_enums = [Priority, ResourceType, ThoughtStatus, ApprovalStatus]
        for enum_class in auto_enums:
            for member in enum_class:
                # Should not raise
                serialized = json.dumps(member.value)
                assert isinstance(serialized, str)


class TestEnumReExports:
    """Test that enums are properly re-exported at different package levels."""

    def test_enums_same_class_at_both_levels(self):
        """Enums imported from domain and domain.enums should be the same class."""
        from graph_of_thought.domain import Priority as DomainPriority
        from graph_of_thought.domain.enums import Priority as EnumsPriority
        assert DomainPriority is EnumsPriority

        from graph_of_thought.domain import ThoughtStatus as DomainThought
        from graph_of_thought.domain.enums import ThoughtStatus as EnumsThought
        assert DomainThought is EnumsThought

        from graph_of_thought.domain import ApprovalType as DomainApproval
        from graph_of_thought.domain.enums import ApprovalType as EnumsApproval
        assert DomainApproval is EnumsApproval

    def test_all_enums_in_enums_package_all_list(self):
        """All expected enums should be in the __all__ list of the enums package."""
        from graph_of_thought.domain import enums
        expected_exports = [
            "Priority", "ResourceType",
            "ThoughtStatus",
            "ApprovalStatus", "ApprovalType", "RequestStatus",
            "QuestionPriority", "QuestionStatus",
            "ProjectStatus", "ChunkStatus",
            "BudgetLevel", "BudgetStatus",
        ]
        for name in expected_exports:
            assert name in enums.__all__, f"{name} should be in enums.__all__"
