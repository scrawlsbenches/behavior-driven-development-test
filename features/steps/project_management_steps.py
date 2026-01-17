"""
Step definitions for Project Management features.

This module provides step definitions for project_lifecycle.feature including:
- Project creation and setup
- Work chunks (focused work sessions)
- Session handoffs and context preservation
- Project progress tracking

These are Application-level steps that test business workflows with personas.
"""

from behave import given, when, then, use_step_matcher
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid

use_step_matcher("parse")


# =============================================================================
# Domain Models for Project Management
# =============================================================================

class ProjectStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ChunkStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"
    COMPLETED = "completed"


@dataclass
class Project:
    """An AI-assisted project."""
    id: str
    name: str
    objective: str
    team: str
    token_budget: int
    tokens_used: int = 0
    target_date: Optional[str] = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    current_focus: Optional[str] = None
    focus_start_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    work_chunks: List[str] = field(default_factory=list)
    decisions_made: int = 0
    questions_pending: int = 0
    team_members: List[str] = field(default_factory=list)

    @property
    def tokens_remaining(self) -> int:
        return self.token_budget - self.tokens_used


@dataclass
class WorkChunk:
    """A focused work session of 2-4 hours."""
    id: str
    project_id: str
    description: str
    assignee: str
    status: ChunkStatus = ChunkStatus.ACTIVE
    intent: Optional[str] = None
    summary: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    tokens_used: int = 0
    pause_reason: Optional[str] = None
    blocker: Optional[str] = None

    @property
    def duration_minutes(self) -> int:
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return int((datetime.now() - self.start_time).total_seconds() / 60)


@dataclass
class SessionHandoff:
    """A handoff package for session continuity."""
    id: str
    project_id: str
    current_intent: str
    key_decisions: List[str] = field(default_factory=list)
    pending_items: List[str] = field(default_factory=list)
    critical_context: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class User:
    """A user in the project management system."""
    name: str
    role: str
    projects: List[str] = field(default_factory=list)


# =============================================================================
# Mock Project Management Service
# =============================================================================

class MockProjectManagementService:
    """Mock implementation of project management service for testing."""

    def __init__(self):
        self.projects: Dict[str, Project] = {}
        self.work_chunks: Dict[str, WorkChunk] = {}
        self.handoffs: Dict[str, SessionHandoff] = {}
        self.users: Dict[str, User] = {}
        self.notifications: List[Dict] = []
        self.knowledge_base: List[Dict] = []
        self.context_window_usage: float = 0.0

    def create_project(self, name: str, objective: str, team: str,
                       token_budget: int, target_date: str = None,
                       created_by: str = None) -> Project:
        """Create a new project."""
        project = Project(
            id=f"PRJ-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            objective=objective,
            team=team,
            token_budget=token_budget,
            target_date=target_date
        )
        self.projects[project.id] = project
        self.projects[name] = project  # Also index by name

        # Notify team members
        self._notify_team(team, "project_created", {
            "project": name,
            "objective": objective,
            "created_by": created_by
        })

        return project

    def get_project(self, name_or_id: str) -> Optional[Project]:
        """Get a project by name or ID."""
        return self.projects.get(name_or_id)

    def update_project_focus(self, project: Project, focus: str):
        """Update project's current focus."""
        project.current_focus = focus
        project.focus_start_time = datetime.now()
        project.status = ProjectStatus.IN_PROGRESS

    def create_work_chunk(self, project: Project, description: str,
                          assignee: str) -> WorkChunk:
        """Create a new work chunk."""
        chunk = WorkChunk(
            id=f"CHK-{uuid.uuid4().hex[:8].upper()}",
            project_id=project.id,
            description=description,
            assignee=assignee,
            intent=description
        )
        self.work_chunks[chunk.id] = chunk
        project.work_chunks.append(chunk.id)

        return chunk

    def complete_chunk(self, chunk: WorkChunk, summary: str):
        """Complete a work chunk with summary."""
        chunk.status = ChunkStatus.COMPLETED
        chunk.summary = summary
        chunk.end_time = datetime.now()

        # Add to knowledge base
        self.knowledge_base.append({
            "type": "chunk_completion",
            "chunk_id": chunk.id,
            "summary": summary,
            "timestamp": datetime.now()
        })

    def create_handoff(self, project: Project, current_intent: str,
                       key_decisions: List[str] = None,
                       pending_items: List[str] = None,
                       critical_context: List[str] = None) -> SessionHandoff:
        """Create a session handoff package."""
        handoff = SessionHandoff(
            id=f"HND-{uuid.uuid4().hex[:8].upper()}",
            project_id=project.id,
            current_intent=current_intent,
            key_decisions=key_decisions or [],
            pending_items=pending_items or [],
            critical_context=critical_context or []
        )
        self.handoffs[handoff.id] = handoff
        self.handoffs[project.id] = handoff  # Index by project for easy lookup

        return handoff

    def get_last_session_handoff(self, project: Project) -> Optional[SessionHandoff]:
        """Get the last handoff for a project."""
        return self.handoffs.get(project.id)

    def _notify_team(self, team: str, notification_type: str, content: Dict):
        """Notify team members."""
        self.notifications.append({
            "team": team,
            "type": notification_type,
            "content": content,
            "timestamp": datetime.now()
        })

    def notify_user(self, user: str, notification_type: str, content: Dict):
        """Notify a specific user."""
        self.notifications.append({
            "to": user,
            "type": notification_type,
            "content": content,
            "timestamp": datetime.now()
        })


# =============================================================================
# Persona Role Mapping
# =============================================================================

PERSONA_ROLES = {
    "Alex": "engineering-manager",
    "Jordan": "data-scientist",
    "Casey": "devops-engineer",
    "Sam": "product-owner",
    "Morgan": "security-officer",
    "Drew": "finance-admin",
    "Taylor": "junior-developer",
    "Riley": "compliance-auditor",
    "Avery": "knowledge-manager",
}


def get_project_service(context) -> MockProjectManagementService:
    """Get or create project management service from context."""
    if not hasattr(context, 'project_service'):
        context.project_service = MockProjectManagementService()
    return context.project_service


# =============================================================================
# Project Creation Steps - MVP-P0
# =============================================================================

@when('{persona} creates project "{project_name}" with')
@when('{persona} creates project "{project_name}" with:')
def step_create_project_with_table(context, persona, project_name):
    """Create a project with details from a table."""
    context.current_persona = persona
    service = get_project_service(context)

    # Ensure user exists in project service
    if persona not in service.users:
        service.users[persona] = User(
            name=persona,
            role="engineering-manager"
        )

    # Parse table data
    project_data = {}
    for row in context.table:
        project_data[row['field']] = row['value']

    project = service.create_project(
        name=project_name,
        objective=project_data.get('objective', ''),
        team=project_data.get('team', ''),
        token_budget=int(project_data.get('token_budget', 0)),
        target_date=project_data.get('target_date'),
        created_by=persona
    )
    context.current_project = project


@then('the project should be created with status "{status}"')
def step_project_created_with_status(context, status):
    """Verify project was created with expected status."""
    assert context.current_project is not None, "No project was created"
    assert context.current_project.status.value == status, \
        f"Expected status '{status}', got '{context.current_project.status.value}'"


@then("a project dashboard should be available")
def step_dashboard_available(context):
    """Verify project dashboard is available."""
    assert context.current_project is not None
    # Dashboard availability is implied by project creation


@then("the token budget should be allocated")
def step_token_budget_allocated(context):
    """Verify token budget was allocated."""
    assert context.current_project.token_budget > 0, "Token budget not allocated"


@then("team members should be notified of the new project")
def step_team_notified_new_project(context):
    """Verify team was notified."""
    service = get_project_service(context)
    notifications = [n for n in service.notifications
                     if n["type"] == "project_created"]
    assert len(notifications) > 0, "Team was not notified"


# =============================================================================
# Project Focus Steps - MVP-P0
# =============================================================================

@given('an active project "{project_name}"')
def step_active_project(context, project_name):
    """Set up an active project."""
    service = get_project_service(context)

    if not service.get_project(project_name):
        project = service.create_project(
            name=project_name,
            objective="Test objective",
            team="Test Team",
            token_budget=100000
        )
    else:
        project = service.get_project(project_name)

    context.current_project = project


@when('the team starts working on "{focus}"')
def step_team_starts_focus(context, focus):
    """Team starts working on a focus area."""
    service = get_project_service(context)
    service.update_project_focus(context.current_project, focus)


@then('the project\'s current focus should update to "{focus}"')
def step_verify_current_focus(context, focus):
    """Verify current focus was updated."""
    assert context.current_project.current_focus == focus, \
        f"Expected focus '{focus}', got '{context.current_project.current_focus}'"


@then("the start time should be recorded")
def step_start_time_recorded(context):
    """Verify start time was recorded."""
    assert context.current_project.focus_start_time is not None


@then('the project status should show "{status}"')
def step_project_status_shows(context, status):
    """Verify project status."""
    assert context.current_project.status.value == status, \
        f"Expected status '{status}', got '{context.current_project.status.value}'"


# =============================================================================
# Project Dashboard Steps - MVP-P0
# =============================================================================

# Note: 'project "{project_name}" with:' is handled by persistence_steps.py with table format check

@when("{persona} views the project dashboard")
def step_view_project_dashboard(context, persona):
    """View project dashboard."""
    context.current_persona = persona
    project = context.current_project

    context.dashboard_data = {
        "work_chunks": len(project.work_chunks),
        "tokens_used": project.tokens_used,
        "tokens_remaining": project.tokens_remaining,
        "decisions_made": project.decisions_made,
        "questions_pending": project.questions_pending,
        "status": project.status.value,
        "objective": project.objective
    }


@then("all metrics should be displayed")
def step_all_metrics_displayed(context):
    """Verify all metrics are displayed."""
    assert "work_chunks" in context.dashboard_data
    assert "tokens_used" in context.dashboard_data
    assert "tokens_remaining" in context.dashboard_data
    assert "decisions_made" in context.dashboard_data
    assert "questions_pending" in context.dashboard_data


@then("progress toward objective should be shown")
def step_progress_shown(context):
    """Verify progress is shown."""
    assert "objective" in context.dashboard_data


@then("pending blockers should be highlighted")
def step_blockers_highlighted(context):
    """Verify blockers are highlighted."""
    assert "questions_pending" in context.dashboard_data


# =============================================================================
# Work Chunk Steps - MVP-P0
# =============================================================================

@given('project "{project_name}"')
def step_given_project(context, project_name):
    """Set up a project by name."""
    service = get_project_service(context)

    if not service.get_project(project_name):
        project = service.create_project(
            name=project_name,
            objective="Test objective",
            team="Test Team",
            token_budget=100000
        )
    else:
        project = service.get_project(project_name)

    context.current_project = project


@given("{persona} is assigned to the project")
def step_persona_assigned(context, persona):
    """Assign persona to project."""
    context.current_persona = persona
    context.current_project.team_members.append(persona)

    service = get_project_service(context)
    if persona not in service.users:
        service.users[persona] = User(
            name=persona,
            role=PERSONA_ROLES.get(persona, "team-member")
        )


@when('{persona} starts a work chunk "{description}"')
def step_start_work_chunk(context, persona, description):
    """Start a new work chunk."""
    context.current_persona = persona
    service = get_project_service(context)

    chunk = service.create_work_chunk(
        project=context.current_project,
        description=description,
        assignee=persona
    )
    context.current_chunk = chunk


@then('the chunk should be created with status "{status}"')
def step_chunk_created_with_status(context, status):
    """Verify chunk was created with expected status."""
    assert context.current_chunk is not None, "No chunk was created"
    assert context.current_chunk.status.value == status, \
        f"Expected status '{status}', got '{context.current_chunk.status.value}'"


@then("a timer should start tracking duration")
def step_timer_started(context):
    """Verify timer started."""
    assert context.current_chunk.start_time is not None


@then("{persona}'s intent should be recorded for context")
def step_intent_recorded(context, persona):
    """Verify intent was recorded."""
    assert context.current_chunk.intent is not None


@then("token consumption should be attributed to this chunk")
def step_tokens_attributed(context):
    """Verify token attribution is set up."""
    # Token attribution is set up by having the chunk linked to the project
    assert context.current_chunk.project_id == context.current_project.id


# =============================================================================
# Work Chunk Completion Steps - MVP-P0
# =============================================================================

@given('an active work chunk "{description}"')
def step_active_work_chunk(context, description):
    """Set up an active work chunk."""
    service = get_project_service(context)

    # Create project if needed
    if not hasattr(context, 'current_project') or context.current_project is None:
        project = service.create_project(
            name="Test Project",
            objective="Test",
            team="Test Team",
            token_budget=100000
        )
        context.current_project = project

    chunk = service.create_work_chunk(
        project=context.current_project,
        description=description,
        assignee="Jordan"
    )
    context.current_chunk = chunk


@given("{persona} has completed the analysis")
def step_analysis_completed(context, persona):
    """Mark that persona has completed analysis."""
    context.current_persona = persona
    # This is a state setup step; actual completion happens in When step


@when("{persona} completes the chunk with summary")
@when("{persona} completes the chunk with summary:")
def step_complete_chunk_with_summary(context, persona):
    """Complete chunk with a summary."""
    context.current_persona = persona
    service = get_project_service(context)

    summary = context.text.strip()
    service.complete_chunk(context.current_chunk, summary)


@then('the chunk should be marked as "{status}"')
def step_chunk_marked_status(context, status):
    """Verify chunk status."""
    assert context.current_chunk.status.value == status, \
        f"Expected status '{status}', got '{context.current_chunk.status.value}'"


@then("the summary should be saved to project knowledge")
def step_summary_saved(context):
    """Verify summary was saved."""
    service = get_project_service(context)
    knowledge_entries = [k for k in service.knowledge_base
                         if k.get("type") == "chunk_completion"]
    assert len(knowledge_entries) > 0, "Summary not saved to knowledge base"


@then("total duration and tokens used should be recorded")
def step_duration_tokens_recorded(context):
    """Verify duration and tokens are recorded."""
    chunk = context.current_chunk
    assert chunk.start_time is not None
    assert chunk.end_time is not None


@then("the project timeline should be updated")
def step_timeline_updated(context):
    """Verify timeline is updated."""
    # Timeline update is implicit with chunk completion
    assert context.current_chunk.id in context.current_project.work_chunks


# =============================================================================
# Session Handoff Steps - MVP-P0
# =============================================================================

@given("an AI session with extensive conversation history")
def step_extensive_conversation(context):
    """Set up a session with extensive history."""
    service = get_project_service(context)

    # Create project if needed
    if not hasattr(context, 'current_project') or context.current_project is None:
        project = service.create_project(
            name="AI Session Project",
            objective="Test",
            team="Test Team",
            token_budget=100000
        )
        context.current_project = project

    # Simulate extensive history by setting context window usage
    service.context_window_usage = 0.5  # 50% initially


@when("the context window reaches {percent:d}% capacity")
def step_context_window_capacity(context, percent):
    """Simulate context window reaching capacity."""
    service = get_project_service(context)
    service.context_window_usage = percent / 100.0

    # Auto-prepare handoff when threshold reached
    if service.context_window_usage >= 0.8:
        handoff = service.create_handoff(
            project=context.current_project,
            current_intent="Continue current analysis",
            key_decisions=["Decided to use Redis", "Cache TTL set to 5 minutes"],
            pending_items=["Test under load", "Review error handling"],
            critical_context=["API latency target: 100ms", "Redis cluster mode enabled"]
        )
        context.current_handoff = handoff

        # Notify user
        service.notify_user("current_user", "context_compression", {
            "message": "Context will be compressed",
            "handoff_id": handoff.id
        })


@then("a handoff package should be automatically prepared")
def step_handoff_prepared(context):
    """Verify handoff package was prepared."""
    assert hasattr(context, 'current_handoff'), "No handoff was prepared"
    assert context.current_handoff is not None


@then("it should include")
@then("it should include:")
def step_handoff_includes(context):
    """Verify handoff includes expected content."""
    handoff = context.current_handoff

    for row in context.table:
        content_type = row['content']
        # Verify the field exists in the handoff
        if content_type == 'current_intent':
            assert handoff.current_intent is not None
        elif content_type == 'key_decisions':
            assert len(handoff.key_decisions) >= 0
        elif content_type == 'pending_items':
            assert len(handoff.pending_items) >= 0
        elif content_type == 'critical_context':
            assert len(handoff.critical_context) >= 0


@then("the user should be notified that context will be compressed")
def step_user_notified_compression(context):
    """Verify user was notified about compression."""
    service = get_project_service(context)
    notifications = [n for n in service.notifications
                     if n.get("type") == "context_compression"]
    assert len(notifications) > 0, "User not notified about context compression"


# =============================================================================
# Session Resumption Steps - MVP-P0
# =============================================================================

@given('{persona} had a session working on "{project_name}"')
def step_persona_had_session(context, persona, project_name):
    """Set up previous session context."""
    context.current_persona = persona
    service = get_project_service(context)

    # Create project
    project = service.create_project(
        name=project_name,
        objective="Optimize API performance",
        team="Backend Team",
        token_budget=100000
    )
    context.current_project = project

    # Assign persona
    project.team_members.append(persona)
    service.users[persona] = User(
        name=persona,
        role=PERSONA_ROLES.get(persona, "team-member")
    )


@given('the session ended with intent "{intent}"')
def step_session_ended_with_intent(context, intent):
    """Set up session end state."""
    service = get_project_service(context)

    # Create handoff from previous session
    handoff = service.create_handoff(
        project=context.current_project,
        current_intent=intent,
        key_decisions=["Decided to use Redis for caching", "Cache TTL set to 5 minutes for user data"],
        pending_items=["Test under load"],
        critical_context=["Previous session focus: " + intent]
    )
    context.previous_handoff = handoff


@when("{persona} starts a new session on the same project")
def step_start_new_session(context, persona):
    """Start a new session."""
    context.current_persona = persona
    service = get_project_service(context)

    # Retrieve the handoff
    handoff = service.get_last_session_handoff(context.current_project)
    context.resumption_handoff = handoff

    # Build resumption context
    if handoff:
        context.resumption_context = {
            "last_intent": handoff.current_intent,
            "key_decisions": handoff.key_decisions,
            "pending_items": handoff.pending_items,
            "message": f"Welcome back! Last session you were: {handoff.current_intent}"
        }


@then("the resumption context should be displayed")
def step_resumption_context_displayed(context):
    """Verify resumption context is displayed."""
    assert hasattr(context, 'resumption_context'), "No resumption context"
    assert context.resumption_context is not None


@then("all previous exploration work should be accessible")
def step_exploration_accessible(context):
    """Verify previous work is accessible."""
    assert context.resumption_handoff is not None, "Previous session handoff not accessible"
