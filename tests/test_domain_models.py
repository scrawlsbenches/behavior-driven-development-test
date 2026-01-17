"""
Unit tests for domain models in graph_of_thought.domain.models.

Tests cover:
1. Import paths from both graph_of_thought.domain.models and graph_of_thought.domain
2. Model instantiation with required fields
3. Default values
4. Properties and methods
5. Correct use of domain enums (not local duplicates)
"""

import pytest
from datetime import datetime


# =============================================================================
# Import Tests - Verify all models can be imported from expected paths
# =============================================================================


class TestImportsFromModels:
    """Test that all models can be imported from graph_of_thought.domain.models."""

    def test_import_shared_models(self):
        """Shared models (User, ResourceBudget) are importable from models package."""
        from graph_of_thought.domain.models import User, ResourceBudget
        assert User is not None
        assert ResourceBudget is not None

    def test_import_reasoning_models(self):
        """Reasoning models are importable from models package."""
        from graph_of_thought.domain.models import Thought, Edge, SearchResult, SearchContext
        assert Thought is not None
        assert Edge is not None
        assert SearchResult is not None
        assert SearchContext is not None

    def test_import_governance_models(self):
        """Governance models are importable from models package."""
        from graph_of_thought.domain.models import ApprovalRequest, Policy
        assert ApprovalRequest is not None
        assert Policy is not None

    def test_import_knowledge_models(self):
        """Knowledge models are importable from models package."""
        from graph_of_thought.domain.models import (
            Decision,
            KnowledgeEntry,
            Question,
            QuestionTicket,
            RoutingRule,
        )
        assert Decision is not None
        assert KnowledgeEntry is not None
        assert Question is not None
        assert QuestionTicket is not None
        assert RoutingRule is not None

    def test_import_project_models(self):
        """Project models are importable from models package."""
        from graph_of_thought.domain.models import (
            Project,
            WorkChunk,
            SessionHandoff,
            HandoffPackage,
        )
        assert Project is not None
        assert WorkChunk is not None
        assert SessionHandoff is not None
        assert HandoffPackage is not None

    def test_import_cost_models(self):
        """Cost models are importable from models package."""
        from graph_of_thought.domain.models import (
            Budget,
            ConsumptionRecord,
            AllocationRecord,
            BudgetWarning,
        )
        assert Budget is not None
        assert ConsumptionRecord is not None
        assert AllocationRecord is not None
        assert BudgetWarning is not None


class TestImportsFromDomain:
    """Test that all models can be imported from top-level graph_of_thought.domain."""

    def test_import_shared_models_from_domain(self):
        """Shared models are importable from domain package."""
        from graph_of_thought.domain import User, ResourceBudget
        assert User is not None
        assert ResourceBudget is not None

    def test_import_reasoning_models_from_domain(self):
        """Reasoning models are importable from domain package."""
        from graph_of_thought.domain import Thought, Edge, SearchResult, SearchContext
        assert Thought is not None
        assert Edge is not None
        assert SearchResult is not None
        assert SearchContext is not None

    def test_import_governance_models_from_domain(self):
        """Governance models are importable from domain package."""
        from graph_of_thought.domain import ApprovalRequest, Policy
        assert ApprovalRequest is not None
        assert Policy is not None

    def test_import_knowledge_models_from_domain(self):
        """Knowledge models are importable from domain package."""
        from graph_of_thought.domain import (
            Decision,
            KnowledgeEntry,
            Question,
            QuestionTicket,
            RoutingRule,
        )
        assert Decision is not None
        assert KnowledgeEntry is not None
        assert Question is not None
        assert QuestionTicket is not None
        assert RoutingRule is not None

    def test_import_project_models_from_domain(self):
        """Project models are importable from domain package."""
        from graph_of_thought.domain import (
            Project,
            WorkChunk,
            SessionHandoff,
            HandoffPackage,
        )
        assert Project is not None
        assert WorkChunk is not None
        assert SessionHandoff is not None
        assert HandoffPackage is not None

    def test_import_cost_models_from_domain(self):
        """Cost models are importable from domain package."""
        from graph_of_thought.domain import (
            Budget,
            ConsumptionRecord,
            AllocationRecord,
            BudgetWarning,
        )
        assert Budget is not None
        assert ConsumptionRecord is not None
        assert AllocationRecord is not None
        assert BudgetWarning is not None

    def test_import_enums_from_domain(self):
        """All domain enums are importable from domain package."""
        from graph_of_thought.domain import (
            # Shared
            Priority,
            ResourceType,
            # Reasoning
            ThoughtStatus,
            # Governance
            ApprovalStatus,
            ApprovalType,
            RequestStatus,
            # Knowledge
            QuestionPriority,
            QuestionStatus,
            # Project
            ProjectStatus,
            ChunkStatus,
            # Cost
            BudgetLevel,
            BudgetStatus,
        )
        # Verify all enums were imported
        assert Priority is not None
        assert ResourceType is not None
        assert ThoughtStatus is not None
        assert ApprovalStatus is not None
        assert ApprovalType is not None
        assert RequestStatus is not None
        assert QuestionPriority is not None
        assert QuestionStatus is not None
        assert ProjectStatus is not None
        assert ChunkStatus is not None
        assert BudgetLevel is not None
        assert BudgetStatus is not None


# =============================================================================
# Shared Models Tests
# =============================================================================


class TestUser:
    """Tests for the User model."""

    def test_user_with_required_fields(self):
        """User can be instantiated with required fields only."""
        from graph_of_thought.domain import User

        user = User(id="user-1", name="Jordan", role="Data Scientist")
        assert user.id == "user-1"
        assert user.name == "Jordan"
        assert user.role == "Data Scientist"

    def test_user_default_values(self):
        """User has correct default values for optional fields."""
        from graph_of_thought.domain import User

        user = User(id="user-1", name="Jordan", role="Data Scientist")
        assert user.email == ""
        assert user.team == ""

    def test_user_with_all_fields(self):
        """User can be instantiated with all fields."""
        from graph_of_thought.domain import User

        user = User(
            id="user-1",
            name="Jordan",
            role="Data Scientist",
            email="jordan@example.com",
            team="Analytics"
        )
        assert user.email == "jordan@example.com"
        assert user.team == "Analytics"


class TestResourceBudget:
    """Tests for the ResourceBudget model."""

    def test_resource_budget_with_required_fields(self):
        """ResourceBudget can be instantiated with required fields."""
        from graph_of_thought.domain import ResourceBudget, ResourceType

        budget = ResourceBudget(
            resource_type=ResourceType.TOKENS,
            allocated=10000.0
        )
        assert budget.resource_type == ResourceType.TOKENS
        assert budget.allocated == 10000.0

    def test_resource_budget_default_values(self):
        """ResourceBudget has correct default values."""
        from graph_of_thought.domain import ResourceBudget, ResourceType

        budget = ResourceBudget(
            resource_type=ResourceType.TOKENS,
            allocated=10000.0
        )
        assert budget.consumed == 0.0
        assert budget.unit == ""

    def test_resource_budget_remaining_property(self):
        """ResourceBudget.remaining calculates correctly."""
        from graph_of_thought.domain import ResourceBudget, ResourceType

        budget = ResourceBudget(
            resource_type=ResourceType.TOKENS,
            allocated=10000.0,
            consumed=2500.0
        )
        assert budget.remaining == 7500.0

    def test_resource_budget_percent_used_property(self):
        """ResourceBudget.percent_used calculates correctly."""
        from graph_of_thought.domain import ResourceBudget, ResourceType

        budget = ResourceBudget(
            resource_type=ResourceType.TOKENS,
            allocated=10000.0,
            consumed=2500.0
        )
        assert budget.percent_used == 25.0

    def test_resource_budget_percent_used_zero_allocation(self):
        """ResourceBudget.percent_used returns 0 when allocation is 0."""
        from graph_of_thought.domain import ResourceBudget, ResourceType

        budget = ResourceBudget(
            resource_type=ResourceType.TOKENS,
            allocated=0.0,
            consumed=0.0
        )
        assert budget.percent_used == 0.0

    def test_resource_budget_is_exhausted_false(self):
        """ResourceBudget.is_exhausted returns False when budget remains."""
        from graph_of_thought.domain import ResourceBudget, ResourceType

        budget = ResourceBudget(
            resource_type=ResourceType.TOKENS,
            allocated=10000.0,
            consumed=5000.0
        )
        assert budget.is_exhausted() is False

    def test_resource_budget_is_exhausted_true(self):
        """ResourceBudget.is_exhausted returns True when budget consumed."""
        from graph_of_thought.domain import ResourceBudget, ResourceType

        budget = ResourceBudget(
            resource_type=ResourceType.TOKENS,
            allocated=10000.0,
            consumed=10000.0
        )
        assert budget.is_exhausted() is True

    def test_resource_budget_is_exhausted_over_budget(self):
        """ResourceBudget.is_exhausted returns True when over budget."""
        from graph_of_thought.domain import ResourceBudget, ResourceType

        budget = ResourceBudget(
            resource_type=ResourceType.TOKENS,
            allocated=10000.0,
            consumed=12000.0
        )
        assert budget.is_exhausted() is True

    def test_resource_budget_uses_domain_enum(self):
        """ResourceBudget uses ResourceType from domain enums."""
        from graph_of_thought.domain import ResourceBudget, ResourceType
        from graph_of_thought.domain.enums import ResourceType as EnumResourceType

        budget = ResourceBudget(
            resource_type=ResourceType.TOKENS,
            allocated=10000.0
        )
        # Verify it's the same enum, not a duplicate
        assert budget.resource_type is ResourceType.TOKENS
        assert ResourceType is EnumResourceType


# =============================================================================
# Reasoning Models Tests
# =============================================================================


class TestThought:
    """Tests for the Thought model."""

    def test_thought_with_required_fields(self):
        """Thought can be instantiated with required field (content)."""
        from graph_of_thought.domain import Thought

        thought = Thought(content="What is the best approach?")
        assert thought.content == "What is the best approach?"

    def test_thought_default_values(self):
        """Thought has correct default values."""
        from graph_of_thought.domain import Thought, ThoughtStatus

        thought = Thought(content="Initial thought")
        assert thought.score == 0.0
        assert thought.depth == 0
        assert thought.status == ThoughtStatus.PENDING
        assert thought.metadata == {}
        assert thought.tokens_used == 0
        assert thought.generation_time_ms == 0.0
        # ID should be auto-generated
        assert thought.id is not None
        assert len(thought.id) == 32  # UUID hex

    def test_thought_uses_domain_enum(self):
        """Thought uses ThoughtStatus from domain enums."""
        from graph_of_thought.domain import Thought, ThoughtStatus
        from graph_of_thought.domain.enums import ThoughtStatus as EnumThoughtStatus

        thought = Thought(content="Test", status=ThoughtStatus.ACTIVE)
        assert thought.status == ThoughtStatus.ACTIVE
        assert ThoughtStatus is EnumThoughtStatus

    def test_thought_comparison_for_heap(self):
        """Thought comparison works for heap operations (higher score = higher priority)."""
        from graph_of_thought.domain import Thought

        low_score = Thought(content="Low", score=1.0)
        high_score = Thought(content="High", score=5.0)

        # Higher score should have priority (return True for __lt__)
        assert high_score < low_score

    def test_thought_equality_by_id(self):
        """Thoughts are equal if they have the same ID."""
        from graph_of_thought.domain import Thought

        thought1 = Thought(content="Same", id="abc123")
        thought2 = Thought(content="Different content", id="abc123")
        thought3 = Thought(content="Same", id="def456")

        assert thought1 == thought2
        assert thought1 != thought3

    def test_thought_hash_by_id(self):
        """Thought hash is based on ID."""
        from graph_of_thought.domain import Thought

        thought = Thought(content="Test", id="abc123")
        assert hash(thought) == hash("abc123")

    def test_thought_to_dict(self):
        """Thought.to_dict serializes correctly."""
        from graph_of_thought.domain import Thought, ThoughtStatus

        thought = Thought(
            content="Test content",
            score=0.85,
            depth=2,
            status=ThoughtStatus.COMPLETED,
            id="test-id",
            tokens_used=100,
            generation_time_ms=50.5
        )

        result = thought.to_dict()
        assert result["id"] == "test-id"
        assert result["content"] == "Test content"
        assert result["score"] == 0.85
        assert result["depth"] == 2
        assert result["status"] == "COMPLETED"
        assert result["tokens_used"] == 100
        assert result["generation_time_ms"] == 50.5

    def test_thought_from_dict(self):
        """Thought.from_dict deserializes correctly."""
        from graph_of_thought.domain import Thought, ThoughtStatus

        data = {
            "id": "test-id",
            "content": "Test content",
            "score": 0.85,
            "depth": 2,
            "status": "COMPLETED",
            "metadata": {"key": "value"},
            "tokens_used": 100,
            "generation_time_ms": 50.5
        }

        thought = Thought.from_dict(data)
        assert thought.id == "test-id"
        assert thought.content == "Test content"
        assert thought.score == 0.85
        assert thought.depth == 2
        assert thought.status == ThoughtStatus.COMPLETED
        assert thought.metadata == {"key": "value"}


class TestEdge:
    """Tests for the Edge model."""

    def test_edge_with_required_fields(self):
        """Edge can be instantiated with required fields."""
        from graph_of_thought.domain import Edge

        edge = Edge(source_id="thought-1", target_id="thought-2")
        assert edge.source_id == "thought-1"
        assert edge.target_id == "thought-2"

    def test_edge_default_values(self):
        """Edge has correct default values."""
        from graph_of_thought.domain import Edge

        edge = Edge(source_id="thought-1", target_id="thought-2")
        assert edge.relation == "leads_to"
        assert edge.weight == 1.0
        assert edge.metadata == {}

    def test_edge_to_dict(self):
        """Edge.to_dict serializes correctly."""
        from graph_of_thought.domain import Edge

        edge = Edge(
            source_id="thought-1",
            target_id="thought-2",
            relation="refines",
            weight=0.8,
            metadata={"reason": "clarification"}
        )

        result = edge.to_dict()
        assert result["source_id"] == "thought-1"
        assert result["target_id"] == "thought-2"
        assert result["relation"] == "refines"
        assert result["weight"] == 0.8
        assert result["metadata"] == {"reason": "clarification"}

    def test_edge_from_dict(self):
        """Edge.from_dict deserializes correctly."""
        from graph_of_thought.domain import Edge

        data = {
            "source_id": "thought-1",
            "target_id": "thought-2",
            "relation": "refines",
            "weight": 0.8,
            "metadata": {"reason": "clarification"}
        }

        edge = Edge.from_dict(data)
        assert edge.source_id == "thought-1"
        assert edge.target_id == "thought-2"
        assert edge.relation == "refines"
        assert edge.weight == 0.8


class TestSearchResult:
    """Tests for the SearchResult model."""

    def test_search_result_with_all_required_fields(self):
        """SearchResult can be instantiated with required fields."""
        from graph_of_thought.domain import SearchResult, Thought

        thoughts = [Thought(content="Root"), Thought(content="Goal")]
        result = SearchResult(
            best_path=thoughts,
            best_score=0.95,
            thoughts_explored=50,
            thoughts_expanded=20,
            total_tokens_used=5000,
            wall_time_seconds=2.5,
            termination_reason="goal_reached"
        )

        assert len(result.best_path) == 2
        assert result.best_score == 0.95
        assert result.thoughts_explored == 50
        assert result.thoughts_expanded == 20
        assert result.total_tokens_used == 5000
        assert result.wall_time_seconds == 2.5
        assert result.termination_reason == "goal_reached"

    def test_search_result_success_property_goal_reached(self):
        """SearchResult.success is True for goal_reached."""
        from graph_of_thought.domain import SearchResult

        result = SearchResult(
            best_path=[],
            best_score=0.95,
            thoughts_explored=50,
            thoughts_expanded=20,
            total_tokens_used=5000,
            wall_time_seconds=2.5,
            termination_reason="goal_reached"
        )
        assert result.success is True

    def test_search_result_success_property_completed(self):
        """SearchResult.success is True for completed."""
        from graph_of_thought.domain import SearchResult

        result = SearchResult(
            best_path=[],
            best_score=0.95,
            thoughts_explored=50,
            thoughts_expanded=20,
            total_tokens_used=5000,
            wall_time_seconds=2.5,
            termination_reason="completed"
        )
        assert result.success is True

    def test_search_result_success_property_false(self):
        """SearchResult.success is False for budget_exhausted, timeout, etc."""
        from graph_of_thought.domain import SearchResult

        for reason in ["budget_exhausted", "timeout", "max_depth"]:
            result = SearchResult(
                best_path=[],
                best_score=0.0,
                thoughts_explored=50,
                thoughts_expanded=20,
                total_tokens_used=5000,
                wall_time_seconds=2.5,
                termination_reason=reason
            )
            assert result.success is False, f"Expected success=False for {reason}"


class TestSearchContext:
    """Tests for the SearchContext model."""

    def test_search_context_with_required_fields(self):
        """SearchContext can be instantiated with required fields."""
        from graph_of_thought.domain import SearchContext, Thought

        current = Thought(content="Current thought")
        path = [Thought(content="Root")]

        context = SearchContext(
            current_thought=current,
            path_to_root=path,
            depth=3,
            tokens_remaining=1000,
            time_remaining_seconds=60.0
        )

        assert context.current_thought == current
        assert context.path_to_root == path
        assert context.depth == 3
        assert context.tokens_remaining == 1000
        assert context.time_remaining_seconds == 60.0

    def test_search_context_default_metadata(self):
        """SearchContext has empty metadata by default."""
        from graph_of_thought.domain import SearchContext, Thought

        context = SearchContext(
            current_thought=Thought(content="Test"),
            path_to_root=[],
            depth=0,
            tokens_remaining=None,
            time_remaining_seconds=None
        )
        assert context.metadata == {}


# =============================================================================
# Governance Models Tests
# =============================================================================


class TestApprovalRequest:
    """Tests for the ApprovalRequest model."""

    def test_approval_request_with_required_fields(self):
        """ApprovalRequest can be instantiated with required fields."""
        from graph_of_thought.domain import ApprovalRequest

        request = ApprovalRequest(
            id="req-1",
            action="deploy_production",
            requester="developer-1"
        )
        assert request.id == "req-1"
        assert request.action == "deploy_production"
        assert request.requester == "developer-1"

    def test_approval_request_default_values(self):
        """ApprovalRequest has correct default values."""
        from graph_of_thought.domain import ApprovalRequest, RequestStatus, ApprovalType

        request = ApprovalRequest(
            id="req-1",
            action="deploy_production",
            requester="developer-1"
        )
        assert request.status == RequestStatus.PENDING
        assert request.approval_type == ApprovalType.STANDARD
        assert request.reason == ""
        assert request.context == {}
        assert request.approvers == []
        assert request.approved_by is None
        assert request.approved_at is None
        assert request.denied_by is None
        assert request.denied_at is None
        assert request.denial_reason == ""
        assert isinstance(request.created_at, datetime)
        assert request.expires_at is None

    def test_approval_request_uses_domain_enums(self):
        """ApprovalRequest uses enums from domain layer."""
        from graph_of_thought.domain import ApprovalRequest, RequestStatus, ApprovalType
        from graph_of_thought.domain.enums import (
            RequestStatus as EnumRequestStatus,
            ApprovalType as EnumApprovalType
        )

        request = ApprovalRequest(
            id="req-1",
            action="deploy",
            requester="dev",
            status=RequestStatus.APPROVED,
            approval_type=ApprovalType.EXPEDITED
        )
        assert RequestStatus is EnumRequestStatus
        assert ApprovalType is EnumApprovalType


class TestPolicy:
    """Tests for the Policy model."""

    def test_policy_with_required_fields(self):
        """Policy can be instantiated with required fields."""
        from graph_of_thought.domain import Policy

        policy = Policy(id="policy-1", name="Production Deployment")
        assert policy.id == "policy-1"
        assert policy.name == "Production Deployment"

    def test_policy_default_values(self):
        """Policy has correct default values."""
        from graph_of_thought.domain import Policy

        policy = Policy(id="policy-1", name="Test Policy")
        assert policy.description == ""
        assert policy.action_pattern == ""
        assert policy.required_approvers == 1
        assert policy.approver_roles == []
        assert policy.auto_approve is False
        assert policy.auto_deny is False
        assert policy.conditions == {}
        assert policy.enabled is True
        assert isinstance(policy.created_at, datetime)


# =============================================================================
# Knowledge Models Tests
# =============================================================================


class TestDecision:
    """Tests for the Decision model."""

    def test_decision_with_required_fields(self):
        """Decision can be instantiated with required fields."""
        from graph_of_thought.domain import Decision

        decision = Decision(
            id="dec-1",
            title="Use PostgreSQL for persistence",
            context="We need a reliable database",
            options=["PostgreSQL", "MySQL", "MongoDB"],
            chosen="PostgreSQL",
            rationale="Best support for complex queries",
            consequences=["Need DBA expertise", "Proven at scale"]
        )
        assert decision.id == "dec-1"
        assert decision.title == "Use PostgreSQL for persistence"
        assert decision.chosen == "PostgreSQL"

    def test_decision_default_values(self):
        """Decision has correct default values."""
        from graph_of_thought.domain import Decision

        decision = Decision(
            id="dec-1",
            title="Test Decision",
            context="Context",
            options=["A", "B"],
            chosen="A",
            rationale="Reason",
            consequences=["Effect"]
        )
        assert isinstance(decision.created_at, datetime)
        assert decision.created_by == ""
        assert decision.project_id == ""
        assert decision.chunk_id == ""
        assert decision.supersedes is None
        assert decision.outcome == ""
        assert decision.outcome_recorded_at is None


class TestKnowledgeEntry:
    """Tests for the KnowledgeEntry model."""

    def test_knowledge_entry_with_required_fields(self):
        """KnowledgeEntry can be instantiated with required fields."""
        from graph_of_thought.domain import KnowledgeEntry

        entry = KnowledgeEntry(
            id="ke-1",
            content="Always validate user input",
            entry_type="pattern"
        )
        assert entry.id == "ke-1"
        assert entry.content == "Always validate user input"
        assert entry.entry_type == "pattern"

    def test_knowledge_entry_default_values(self):
        """KnowledgeEntry has correct default values."""
        from graph_of_thought.domain import KnowledgeEntry

        entry = KnowledgeEntry(
            id="ke-1",
            content="Test content",
            entry_type="discovery"
        )
        assert entry.source_project == ""
        assert entry.source_chunk == ""
        assert entry.tags == []
        assert isinstance(entry.created_at, datetime)
        assert entry.embedding is None
        assert entry.relevance_score == 0.0


class TestQuestion:
    """Tests for the Question model."""

    def test_question_with_required_fields(self):
        """Question can be instantiated with required fields."""
        from graph_of_thought.domain import Question

        question = Question(
            id="q-1",
            question="How should we handle authentication?"
        )
        assert question.id == "q-1"
        assert question.question == "How should we handle authentication?"

    def test_question_default_values(self):
        """Question has correct default values."""
        from graph_of_thought.domain import Question, QuestionPriority, QuestionStatus

        question = Question(id="q-1", question="Test?")
        assert question.context == ""
        assert question.blocking is False
        assert question.priority == QuestionPriority.NORMAL
        assert question.status == QuestionStatus.PENDING
        assert question.asked_by == ""
        assert question.project == ""
        assert question.routed_to == ""
        assert question.assigned_to == ""
        assert question.answer == ""
        assert question.answered_by == ""
        assert question.answered_at is None
        assert question.next_steps == ""
        assert isinstance(question.created_at, datetime)

    def test_question_uses_domain_enums(self):
        """Question uses enums from domain layer."""
        from graph_of_thought.domain import Question, QuestionPriority, QuestionStatus
        from graph_of_thought.domain.enums import (
            QuestionPriority as EnumQuestionPriority,
            QuestionStatus as EnumQuestionStatus
        )

        assert QuestionPriority is EnumQuestionPriority
        assert QuestionStatus is EnumQuestionStatus


class TestQuestionTicket:
    """Tests for the QuestionTicket model."""

    def test_question_ticket_with_required_fields(self):
        """QuestionTicket can be instantiated with required fields."""
        from graph_of_thought.domain import QuestionTicket

        ticket = QuestionTicket(
            id="qt-1",
            question="What is the deployment process?"
        )
        assert ticket.id == "qt-1"
        assert ticket.question == "What is the deployment process?"

    def test_question_ticket_default_values(self):
        """QuestionTicket has correct default values."""
        from graph_of_thought.domain import QuestionTicket, Priority

        ticket = QuestionTicket(id="qt-1", question="Test?")
        assert ticket.context == ""
        assert ticket.asker == ""
        assert ticket.priority == Priority.MEDIUM
        assert ticket.routed_to == ""
        assert ticket.routing_reason == ""
        assert ticket.status == "open"
        assert isinstance(ticket.asked_at, datetime)
        assert ticket.answered_at is None
        assert ticket.answer == ""
        assert ticket.answered_by == ""
        assert ticket.validated is False
        assert ticket.validation_notes == ""
        assert ticket.captured_as_knowledge is False
        assert ticket.knowledge_entry_id == ""

    def test_question_ticket_uses_domain_enum(self):
        """QuestionTicket uses Priority from domain enums."""
        from graph_of_thought.domain import QuestionTicket, Priority
        from graph_of_thought.domain.enums import Priority as EnumPriority

        assert Priority is EnumPriority


class TestRoutingRule:
    """Tests for the RoutingRule model."""

    def test_routing_rule_with_required_fields(self):
        """RoutingRule can be instantiated with required fields."""
        from graph_of_thought.domain import RoutingRule

        rule = RoutingRule(
            keyword_pattern="security|authentication",
            route_to="security-team"
        )
        assert rule.keyword_pattern == "security|authentication"
        assert rule.route_to == "security-team"

    def test_routing_rule_default_values(self):
        """RoutingRule has correct default values."""
        from graph_of_thought.domain import RoutingRule

        rule = RoutingRule(keyword_pattern="test", route_to="team")
        assert rule.priority == "normal"


# =============================================================================
# Project Models Tests
# =============================================================================


class TestProject:
    """Tests for the Project model."""

    def test_project_with_required_fields(self):
        """Project can be instantiated with required fields."""
        from graph_of_thought.domain import Project

        project = Project(id="proj-1", name="Customer Analysis")
        assert project.id == "proj-1"
        assert project.name == "Customer Analysis"

    def test_project_default_values(self):
        """Project has correct default values."""
        from graph_of_thought.domain import Project, ProjectStatus

        project = Project(id="proj-1", name="Test")
        assert project.description == ""
        assert project.status == ProjectStatus.PLANNING
        assert project.owner == ""
        assert project.team == []
        assert isinstance(project.created_at, datetime)
        assert project.started_at is None
        assert project.completed_at is None
        assert project.metadata == {}

    def test_project_uses_domain_enum(self):
        """Project uses ProjectStatus from domain enums."""
        from graph_of_thought.domain import Project, ProjectStatus
        from graph_of_thought.domain.enums import ProjectStatus as EnumProjectStatus

        project = Project(id="proj-1", name="Test", status=ProjectStatus.ACTIVE)
        assert ProjectStatus is EnumProjectStatus


class TestWorkChunk:
    """Tests for the WorkChunk model."""

    def test_work_chunk_with_required_fields(self):
        """WorkChunk can be instantiated with required fields."""
        from graph_of_thought.domain import WorkChunk

        chunk = WorkChunk(
            id="chunk-1",
            name="Implement login flow",
            project="proj-1"
        )
        assert chunk.id == "chunk-1"
        assert chunk.name == "Implement login flow"
        assert chunk.project == "proj-1"

    def test_work_chunk_default_values(self):
        """WorkChunk has correct default values."""
        from graph_of_thought.domain import WorkChunk, ChunkStatus

        chunk = WorkChunk(id="chunk-1", name="Test", project="proj-1")
        assert chunk.status == ChunkStatus.ACTIVE
        assert chunk.goals == []
        assert chunk.assigned_to == ""
        assert isinstance(chunk.started_at, datetime)
        assert chunk.completed_at is None
        assert chunk.blocked_by is None
        assert chunk.notes == ""
        assert chunk.deliverables == []

    def test_work_chunk_uses_domain_enum(self):
        """WorkChunk uses ChunkStatus from domain enums."""
        from graph_of_thought.domain import WorkChunk, ChunkStatus
        from graph_of_thought.domain.enums import ChunkStatus as EnumChunkStatus

        assert ChunkStatus is EnumChunkStatus


class TestSessionHandoff:
    """Tests for the SessionHandoff model."""

    def test_session_handoff_with_required_fields(self):
        """SessionHandoff can be instantiated with required fields."""
        from graph_of_thought.domain import SessionHandoff

        handoff = SessionHandoff(id="handoff-1", from_session="session-a")
        assert handoff.id == "handoff-1"
        assert handoff.from_session == "session-a"

    def test_session_handoff_default_values(self):
        """SessionHandoff has correct default values."""
        from graph_of_thought.domain import SessionHandoff

        handoff = SessionHandoff(id="handoff-1", from_session="session-a")
        assert handoff.to_session is None
        assert handoff.chunk_id == ""
        assert handoff.summary == ""
        assert handoff.next_steps == []
        assert handoff.open_questions == []
        assert handoff.context == {}
        assert isinstance(handoff.created_at, datetime)
        assert handoff.picked_up_at is None


class TestHandoffPackage:
    """Tests for the HandoffPackage model."""

    def test_handoff_package_with_required_fields(self):
        """HandoffPackage can be instantiated with required fields."""
        from graph_of_thought.domain import HandoffPackage

        package = HandoffPackage(
            id="pkg-1",
            handoff_type="ai_to_human"
        )
        assert package.id == "pkg-1"
        assert package.handoff_type == "ai_to_human"

    def test_handoff_package_default_values(self):
        """HandoffPackage has correct default values."""
        from graph_of_thought.domain import HandoffPackage

        package = HandoffPackage(id="pkg-1", handoff_type="human_to_ai")
        assert isinstance(package.created_at, datetime)
        assert package.project_id == ""
        assert package.chunk_id == ""
        assert package.intent == ""
        assert package.constraints == []
        assert package.current_state == ""
        assert package.blockers == []
        assert package.next_actions == []
        assert package.changes_summary == ""
        assert package.risks == []
        assert package.test_status == ""
        assert package.open_questions == []
        assert package.key_decisions == []
        assert package.relevant_discoveries == []


# =============================================================================
# Cost Models Tests
# =============================================================================


class TestBudget:
    """Tests for the Budget model."""

    def test_budget_with_required_fields(self):
        """Budget can be instantiated with required fields."""
        from graph_of_thought.domain import Budget

        budget = Budget(id="budget-1", name="Sprint Budget")
        assert budget.id == "budget-1"
        assert budget.name == "Sprint Budget"

    def test_budget_default_values(self):
        """Budget has correct default values."""
        from graph_of_thought.domain import Budget, BudgetStatus

        budget = Budget(id="budget-1", name="Test")
        assert budget.project == ""
        assert budget.team == ""
        assert budget.allocated == 0.0
        assert budget.consumed == 0.0
        assert budget.unit == "tokens"
        assert budget.status == BudgetStatus.ACTIVE
        assert budget.warning_threshold == 0.8
        assert budget.hard_limit is True
        assert budget.period_start is None
        assert budget.period_end is None
        assert isinstance(budget.created_at, datetime)

    def test_budget_remaining_property(self):
        """Budget.remaining calculates correctly."""
        from graph_of_thought.domain import Budget

        budget = Budget(
            id="budget-1",
            name="Test",
            allocated=50000.0,
            consumed=12500.0
        )
        assert budget.remaining == 37500.0

    def test_budget_percent_used_property(self):
        """Budget.percent_used calculates correctly."""
        from graph_of_thought.domain import Budget

        budget = Budget(
            id="budget-1",
            name="Test",
            allocated=50000.0,
            consumed=25000.0
        )
        assert budget.percent_used == 50.0

    def test_budget_percent_used_zero_allocation(self):
        """Budget.percent_used returns 0 when allocation is 0."""
        from graph_of_thought.domain import Budget

        budget = Budget(id="budget-1", name="Test", allocated=0.0)
        assert budget.percent_used == 0.0

    def test_budget_level_normal(self):
        """Budget.level returns NORMAL for low consumption."""
        from graph_of_thought.domain import Budget, BudgetLevel

        budget = Budget(
            id="budget-1",
            name="Test",
            allocated=100000.0,
            consumed=50000.0  # 50%
        )
        assert budget.level == BudgetLevel.NORMAL

    def test_budget_level_warning(self):
        """Budget.level returns WARNING at threshold."""
        from graph_of_thought.domain import Budget, BudgetLevel

        budget = Budget(
            id="budget-1",
            name="Test",
            allocated=100000.0,
            consumed=80000.0,  # 80%
            warning_threshold=0.8
        )
        assert budget.level == BudgetLevel.WARNING

    def test_budget_level_critical(self):
        """Budget.level returns CRITICAL at 90%."""
        from graph_of_thought.domain import Budget, BudgetLevel

        budget = Budget(
            id="budget-1",
            name="Test",
            allocated=100000.0,
            consumed=90000.0  # 90%
        )
        assert budget.level == BudgetLevel.CRITICAL

    def test_budget_level_exhausted(self):
        """Budget.level returns EXHAUSTED at 100%."""
        from graph_of_thought.domain import Budget, BudgetLevel

        budget = Budget(
            id="budget-1",
            name="Test",
            allocated=100000.0,
            consumed=100000.0  # 100%
        )
        assert budget.level == BudgetLevel.EXHAUSTED

    def test_budget_level_exhausted_over_budget(self):
        """Budget.level returns EXHAUSTED when over budget."""
        from graph_of_thought.domain import Budget, BudgetLevel

        budget = Budget(
            id="budget-1",
            name="Test",
            allocated=100000.0,
            consumed=120000.0  # 120%
        )
        assert budget.level == BudgetLevel.EXHAUSTED

    def test_budget_uses_domain_enums(self):
        """Budget uses enums from domain layer."""
        from graph_of_thought.domain import Budget, BudgetStatus, BudgetLevel
        from graph_of_thought.domain.enums import (
            BudgetStatus as EnumBudgetStatus,
            BudgetLevel as EnumBudgetLevel
        )

        assert BudgetStatus is EnumBudgetStatus
        assert BudgetLevel is EnumBudgetLevel


class TestConsumptionRecord:
    """Tests for the ConsumptionRecord model."""

    def test_consumption_record_with_required_fields(self):
        """ConsumptionRecord can be instantiated with required fields."""
        from graph_of_thought.domain import ConsumptionRecord

        record = ConsumptionRecord(
            id="rec-1",
            budget_id="budget-1",
            amount=2500.0
        )
        assert record.id == "rec-1"
        assert record.budget_id == "budget-1"
        assert record.amount == 2500.0

    def test_consumption_record_default_values(self):
        """ConsumptionRecord has correct default values."""
        from graph_of_thought.domain import ConsumptionRecord

        record = ConsumptionRecord(id="rec-1", budget_id="budget-1", amount=100.0)
        assert record.operation == ""
        assert record.user == ""
        assert record.project == ""
        assert isinstance(record.timestamp, datetime)
        assert record.metadata == {}


class TestAllocationRecord:
    """Tests for the AllocationRecord model."""

    def test_allocation_record_with_required_fields(self):
        """AllocationRecord can be instantiated with required fields."""
        from graph_of_thought.domain import AllocationRecord

        record = AllocationRecord(
            id="alloc-1",
            budget_id="budget-1",
            amount=50000.0
        )
        assert record.id == "alloc-1"
        assert record.budget_id == "budget-1"
        assert record.amount == 50000.0

    def test_allocation_record_default_values(self):
        """AllocationRecord has correct default values."""
        from graph_of_thought.domain import AllocationRecord

        record = AllocationRecord(id="alloc-1", budget_id="budget-1", amount=1000.0)
        assert record.allocation_type == "initial"
        assert record.reason == ""
        assert record.approved_by == ""
        assert isinstance(record.timestamp, datetime)


class TestBudgetWarning:
    """Tests for the BudgetWarning model."""

    def test_budget_warning_with_required_fields(self):
        """BudgetWarning can be instantiated with required fields."""
        from graph_of_thought.domain import BudgetWarning, BudgetLevel

        warning = BudgetWarning(
            id="warn-1",
            budget_id="budget-1",
            level=BudgetLevel.WARNING,
            message="Budget at 80% consumption"
        )
        assert warning.id == "warn-1"
        assert warning.budget_id == "budget-1"
        assert warning.level == BudgetLevel.WARNING
        assert warning.message == "Budget at 80% consumption"

    def test_budget_warning_default_values(self):
        """BudgetWarning has correct default values."""
        from graph_of_thought.domain import BudgetWarning, BudgetLevel

        warning = BudgetWarning(
            id="warn-1",
            budget_id="budget-1",
            level=BudgetLevel.CRITICAL,
            message="Critical"
        )
        assert warning.acknowledged is False
        assert warning.acknowledged_by is None
        assert warning.acknowledged_at is None
        assert isinstance(warning.created_at, datetime)

    def test_budget_warning_uses_domain_enum(self):
        """BudgetWarning uses BudgetLevel from domain enums."""
        from graph_of_thought.domain import BudgetWarning, BudgetLevel
        from graph_of_thought.domain.enums import BudgetLevel as EnumBudgetLevel

        assert BudgetLevel is EnumBudgetLevel


# =============================================================================
# Cross-Module Enum Consistency Tests
# =============================================================================


class TestEnumConsistency:
    """
    Verify that models use domain enums from the centralized location,
    not local duplicate definitions.
    """

    def test_all_models_use_centralized_enums(self):
        """
        All models should import enums from graph_of_thought.domain.enums,
        not define their own local versions.
        """
        # Import from models
        from graph_of_thought.domain.models.shared import ResourceBudget
        from graph_of_thought.domain.models.reasoning import Thought
        from graph_of_thought.domain.models.governance import ApprovalRequest
        from graph_of_thought.domain.models.knowledge import Question, QuestionTicket
        from graph_of_thought.domain.models.project import Project, WorkChunk
        from graph_of_thought.domain.models.cost import Budget, BudgetWarning

        # Import canonical enums
        from graph_of_thought.domain.enums import (
            ResourceType,
            ThoughtStatus,
            RequestStatus,
            ApprovalType,
            QuestionPriority,
            QuestionStatus,
            Priority,
            ProjectStatus,
            ChunkStatus,
            BudgetStatus,
            BudgetLevel,
        )

        # Create instances and verify enum types match
        rb = ResourceBudget(resource_type=ResourceType.TOKENS, allocated=100)
        assert type(rb.resource_type).__module__ == "graph_of_thought.domain.enums.shared"

        t = Thought(content="test", status=ThoughtStatus.PENDING)
        assert type(t.status).__module__ == "graph_of_thought.domain.enums.reasoning"

        ar = ApprovalRequest(id="1", action="test", requester="user",
                            status=RequestStatus.PENDING, approval_type=ApprovalType.STANDARD)
        assert type(ar.status).__module__ == "graph_of_thought.domain.enums.governance"
        assert type(ar.approval_type).__module__ == "graph_of_thought.domain.enums.governance"

        q = Question(id="1", question="test?", priority=QuestionPriority.NORMAL,
                    status=QuestionStatus.PENDING)
        assert type(q.priority).__module__ == "graph_of_thought.domain.enums.knowledge"
        assert type(q.status).__module__ == "graph_of_thought.domain.enums.knowledge"

        qt = QuestionTicket(id="1", question="test?", priority=Priority.MEDIUM)
        assert type(qt.priority).__module__ == "graph_of_thought.domain.enums.shared"

        p = Project(id="1", name="test", status=ProjectStatus.PLANNING)
        assert type(p.status).__module__ == "graph_of_thought.domain.enums.project"

        wc = WorkChunk(id="1", name="test", project="p1", status=ChunkStatus.ACTIVE)
        assert type(wc.status).__module__ == "graph_of_thought.domain.enums.project"

        b = Budget(id="1", name="test", status=BudgetStatus.ACTIVE)
        assert type(b.status).__module__ == "graph_of_thought.domain.enums.cost"

        bw = BudgetWarning(id="1", budget_id="b1", level=BudgetLevel.WARNING, message="test")
        assert type(bw.level).__module__ == "graph_of_thought.domain.enums.cost"
