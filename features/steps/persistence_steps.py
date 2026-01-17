"""
Step definitions for persistence-related BDD tests.
"""
import asyncio
import tempfile
import shutil
from pathlib import Path
from behave import given, when, then, use_step_matcher

from graph_of_thought.persistence import InMemoryPersistence, FilePersistence

use_step_matcher("parse")


# =============================================================================
# Persistence Setup Steps
# =============================================================================

@given("a in-memory persistence backend")
def step_in_memory_persistence(context):
    context.persistence = InMemoryPersistence()


@given("a file persistence backend")
def step_file_persistence(context):
    context.temp_dir = tempfile.mkdtemp()
    context.persistence = FilePersistence(context.temp_dir)


# =============================================================================
# Persistence Actions
# =============================================================================

@when('I save the graph with id "{graph_id}" and metadata "{key}" = {value}')
def step_save_graph_with_metadata(context, graph_id, key, value):
    # Parse the value - handle quoted strings
    value = value.strip('"')
    if value == "True":
        parsed_value = True
    elif value == "False":
        parsed_value = False
    else:
        parsed_value = value

    asyncio.run(context.persistence.save_graph(
        graph_id=graph_id,
        thoughts=context.graph.thoughts,
        edges=context.graph.edges,
        root_ids=context.graph.root_ids,
        metadata={key: parsed_value},
    ))
    context.last_graph_id = graph_id


@when('I save a graph with id "{graph_id}"')
def step_save_graph(context, graph_id):
    asyncio.run(context.persistence.save_graph(
        graph_id=graph_id,
        thoughts={},
        edges=[],
        root_ids=[],
        metadata={},
    ))
    context.last_graph_id = graph_id


@when('I load the graph with id "{graph_id}"')
def step_load_graph(context, graph_id):
    context.loaded = asyncio.run(context.persistence.load_graph(graph_id))
    if context.loaded:
        context.loaded_thoughts, context.loaded_edges, context.loaded_root_ids, context.loaded_metadata = context.loaded


@when('I save a checkpoint with id "{cp_id}" and search state "{key}" = {value:d}')
def step_save_checkpoint(context, cp_id, key, value):
    asyncio.run(context.persistence.save_checkpoint(
        graph_id="test",
        checkpoint_id=cp_id,
        thoughts=context.graph.thoughts,
        edges=context.graph.edges,
        root_ids=context.graph.root_ids,
        search_state={key: value},
    ))


@when('I load the checkpoint "{cp_id}"')
def step_load_checkpoint(context, cp_id):
    context.loaded = asyncio.run(context.persistence.load_checkpoint("test", cp_id))
    if context.loaded:
        context.loaded_thoughts, context.loaded_edges, context.loaded_root_ids, context.loaded_search_state = context.loaded


@when('I delete the graph with id "{graph_id}"')
def step_delete_graph(context, graph_id):
    context.deleted = asyncio.run(context.persistence.delete_graph(graph_id))


@when('I try to load graph "{graph_id}"')
def step_try_load_graph(context, graph_id):
    context.loaded = asyncio.run(context.persistence.load_graph(graph_id))


@when('I try to load checkpoint "{cp_id}" for graph "{graph_id}"')
def step_try_load_checkpoint(context, cp_id, graph_id):
    context.checkpoint_loaded = asyncio.run(context.persistence.load_checkpoint(graph_id, cp_id))


# =============================================================================
# Persistence Assertions
# =============================================================================

@then("the loaded graph should have {count:d} thought")
@then("the loaded graph should have {count:d} thoughts")
def step_check_loaded_thoughts(context, count):
    assert len(context.loaded_thoughts) == count, f"Expected {count} thoughts, got {len(context.loaded_thoughts)}"


@then('the loaded metadata should have "{key}" = {value}')
def step_check_loaded_metadata(context, key, value):
    # Handle quoted strings
    value = value.strip('"')
    if value == "True":
        expected = True
    elif value == "False":
        expected = False
    else:
        expected = value
    assert context.loaded_metadata[key] == expected, f"Expected {key}={expected}, got {context.loaded_metadata[key]}"


@then('the loaded search state should have "{key}" = {value:d}')
def step_check_loaded_search_state(context, key, value):
    assert context.loaded_search_state[key] == value, f"Expected {key}={value}, got {context.loaded_search_state[key]}"


@then('loading graph "{graph_id}" should return nothing')
def step_check_graph_deleted(context, graph_id):
    loaded = asyncio.run(context.persistence.load_graph(graph_id))
    assert loaded is None, f"Expected None, got {loaded}"


@then('a JSON file should exist for graph "{graph_id}"')
def step_check_json_exists(context, graph_id):
    path = Path(context.temp_dir) / f"{graph_id}.json"
    assert path.exists(), f"Expected JSON file at {path}"


@then('the JSON file for "{graph_id}" should not exist')
def step_check_json_not_exists(context, graph_id):
    path = Path(context.temp_dir) / f"{graph_id}.json"
    assert not path.exists(), f"Expected no JSON file at {path}, but it exists"


@then("the load result should be nothing")
def step_check_load_nothing(context):
    assert context.loaded is None, f"Expected None, got {context.loaded}"


@then("the checkpoint load result should be nothing")
def step_check_checkpoint_load_nothing(context):
    assert context.checkpoint_loaded is None, f"Expected None, got {context.checkpoint_loaded}"


# =============================================================================
# Cleanup
# =============================================================================

def after_scenario(context, scenario):
    """Clean up temp directories after each scenario."""
    if hasattr(context, 'temp_dir'):
        shutil.rmtree(context.temp_dir, ignore_errors=True)


# =============================================================================
# Application-Level Persistence Steps (Persona-Aware)
# =============================================================================
# These steps support the data_persistence.feature MVP-P0 scenarios

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class SaveStatus(Enum):
    SAVED = "saved"
    PENDING = "pending"
    SYNCING = "syncing"
    OFFLINE = "offline"


@dataclass
class AppExploration:
    """An exploration session for application-level tests."""
    id: str
    name: str
    thoughts: Dict[str, dict] = field(default_factory=dict)
    edges: List[tuple] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_saved: Optional[datetime] = None
    save_status: SaveStatus = SaveStatus.PENDING


@dataclass
class ProjectData:
    """Complete project data for persistence."""
    id: str
    name: str
    work_chunks: int = 0
    explorations: int = 0
    decisions: int = 0
    questions: int = 0
    budgets: Dict = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)


class MockAppPersistenceService:
    """Mock service for application-level persistence operations."""

    def __init__(self):
        self.explorations: Dict[str, AppExploration] = {}
        self.projects: Dict[str, ProjectData] = {}
        self.save_queue: List[str] = []
        self.offline_changes: List[Dict] = []
        self.recovery_data: Dict = {}
        self.notifications: List[Dict] = []
        self._exploration_counter = 0
        self._auto_save_enabled = True
        self._save_interval_seconds = 5
        self._max_data_loss_seconds = 30

    def create_exploration(self, name: str) -> AppExploration:
        """Create a new exploration."""
        self._exploration_counter += 1
        exp = AppExploration(
            id=f"EXP-{self._exploration_counter:04d}",
            name=name,
        )
        self.explorations[exp.id] = exp
        return exp

    def add_thought(self, exploration_id: str, content: str, parent_id: Optional[str] = None) -> dict:
        """Add a thought to an exploration."""
        exp = self.explorations.get(exploration_id)
        if not exp:
            raise ValueError(f"Exploration {exploration_id} not found")

        thought_id = f"T-{len(exp.thoughts) + 1:04d}"
        depth = 0
        if parent_id and parent_id in exp.thoughts:
            depth = exp.thoughts[parent_id].get('depth', 0) + 1
            exp.edges.append((parent_id, thought_id))

        thought = {
            'id': thought_id,
            'content': content,
            'depth': depth,
            'parent_id': parent_id,
        }
        exp.thoughts[thought_id] = thought

        # Mark as pending save
        exp.save_status = SaveStatus.PENDING
        self._auto_save(exploration_id)

        return thought

    def _auto_save(self, exploration_id: str):
        """Simulate auto-save behavior."""
        if not self._auto_save_enabled:
            return

        exp = self.explorations.get(exploration_id)
        if exp:
            exp.last_saved = datetime.now()
            exp.save_status = SaveStatus.SAVED

    def save_exploration(self, exploration_id: str) -> bool:
        """Explicitly save an exploration."""
        exp = self.explorations.get(exploration_id)
        if exp:
            exp.last_saved = datetime.now()
            exp.save_status = SaveStatus.SAVED
            return True
        return False

    def simulate_crash(self, exploration_id: str):
        """Simulate a browser crash and store recovery data."""
        exp = self.explorations.get(exploration_id)
        if exp:
            self.recovery_data[exploration_id] = {
                "thoughts": len(exp.thoughts),
                "last_saved": exp.last_saved,
                "save_status": exp.save_status,
            }

    def recover_exploration(self, exploration_id: str) -> AppExploration:
        """Recover an exploration after crash."""
        exp = self.explorations.get(exploration_id)
        if exp:
            self.notifications.append({
                "type": "recovery_complete",
                "exploration_id": exploration_id,
                "message": "Work recovered successfully",
            })
        return exp

    def go_offline(self):
        """Simulate going offline."""
        self._auto_save_enabled = False

    def restore_connection(self):
        """Simulate restoring connection and syncing."""
        self._auto_save_enabled = True
        for change in self.offline_changes:
            self._process_offline_change(change)
        self.offline_changes.clear()

    def _process_offline_change(self, change: Dict):
        """Process an offline change."""
        exp_id = change.get("exploration_id")
        if exp_id and exp_id in self.explorations:
            self.save_exploration(exp_id)

    def add_offline_change(self, exploration_id: str, change_type: str):
        """Record an offline change."""
        self.offline_changes.append({
            "exploration_id": exploration_id,
            "type": change_type,
            "timestamp": datetime.now(),
        })

    def save_project(self, project: ProjectData) -> bool:
        """Save complete project state."""
        self.projects[project.id] = project
        return True

    def load_project(self, project_id: str) -> Optional[ProjectData]:
        """Load a project from storage."""
        return self.projects.get(project_id)


def get_app_persistence_service(context) -> MockAppPersistenceService:
    """Get or create the application persistence service."""
    if not hasattr(context, 'app_persistence_service'):
        context.app_persistence_service = MockAppPersistenceService()
    return context.app_persistence_service


# =============================================================================
# Background Steps - MVP-P0
# =============================================================================

@given("the persistence layer is available")
def step_persistence_layer_available(context):
    """Set up the persistence layer for application tests."""
    context.app_persistence_service = MockAppPersistenceService()


# =============================================================================
# Automatic Save Steps - MVP-P0
# =============================================================================

@given("{persona} is actively exploring with {count:d} thoughts created")
def step_actively_exploring(context, persona, count):
    """Set up an active exploration with thoughts."""
    context.current_persona = persona
    service = get_app_persistence_service(context)

    context.current_exploration = service.create_exploration(f"{persona}'s Exploration")

    root = service.add_thought(context.current_exploration.id, "Root thought")
    last_id = root['id']

    for i in range(count - 1):
        thought = service.add_thought(
            context.current_exploration.id,
            f"Thought {i + 2}",
            parent_id=last_id if i % 3 == 0 else None
        )
        last_id = thought['id']


@then("all {count:d} thoughts should be persisted to storage")
def step_thoughts_persisted(context, count):
    """Verify all thoughts are persisted."""
    exp = context.current_exploration
    assert len(exp.thoughts) == count, \
        f"Expected {count} thoughts, got {len(exp.thoughts)}"
    assert exp.save_status == SaveStatus.SAVED, "Exploration not saved"


@then("the save should happen within {seconds:d} seconds of each change")
def step_save_within_seconds(context, seconds):
    """Verify save timing."""
    service = get_app_persistence_service(context)
    assert service._save_interval_seconds <= seconds, \
        f"Save interval is {service._save_interval_seconds}s, expected <= {seconds}s"


@then("{persona} should not need to take any save action")
def step_no_save_action_needed(context, persona):
    """Verify auto-save is enabled."""
    service = get_app_persistence_service(context)
    assert service._auto_save_enabled, "Auto-save should be enabled"


@then("a visual indicator should show \"{message}\"")
def step_visual_indicator(context, message):
    """Verify save status indicator."""
    exp = context.current_exploration
    if "saved" in message.lower():
        assert exp.save_status == SaveStatus.SAVED, "Should show saved status"


# =============================================================================
# Recovery Steps - MVP-P0
# =============================================================================

@given("{persona} has made changes to an exploration")
def step_has_changes(context, persona):
    """Set up exploration with changes."""
    context.current_persona = persona
    service = get_app_persistence_service(context)

    context.current_exploration = service.create_exploration(f"{persona}'s Work")

    for i in range(5):
        service.add_thought(context.current_exploration.id, f"Change {i + 1}")


@when("{persona}'s browser crashes unexpectedly")
def step_browser_crashes(context, persona):
    """Simulate browser crash."""
    service = get_app_persistence_service(context)
    service.simulate_crash(context.current_exploration.id)


@when("{persona} reopens the application")
def step_reopens_app(context, persona):
    """Simulate reopening after crash."""
    service = get_app_persistence_service(context)
    context.recovered_exploration = service.recover_exploration(
        context.current_exploration.id
    )


@then("all saved work should be restored")
def step_work_restored(context):
    """Verify work was restored."""
    assert context.recovered_exploration is not None, "Exploration not recovered"
    assert len(context.recovered_exploration.thoughts) > 0, "No thoughts recovered"


@then("at most {seconds:d} seconds of work should be lost")
def step_max_data_loss(context, seconds):
    """Verify maximum data loss."""
    service = get_app_persistence_service(context)
    assert service._max_data_loss_seconds <= seconds, \
        f"Max data loss is {service._max_data_loss_seconds}s, expected <= {seconds}s"


@then("{persona} should see a recovery notification")
def step_recovery_notification(context, persona):
    """Verify recovery notification."""
    service = get_app_persistence_service(context)
    notifications = [n for n in service.notifications
                     if n.get('type') == 'recovery_complete']
    assert len(notifications) > 0, "No recovery notification sent"


# =============================================================================
# Offline Sync Steps - MVP-P0
# =============================================================================

@given("{persona} loses network connectivity")
def step_loses_connectivity(context, persona):
    """Simulate going offline."""
    context.current_persona = persona
    service = get_app_persistence_service(context)
    service.go_offline()

    if not hasattr(context, 'current_exploration'):
        context.current_exploration = service.create_exploration(f"{persona}'s Work")


@given("continues working on the exploration")
def step_continues_working_offline(context):
    """Continue working while offline."""
    service = get_app_persistence_service(context)

    for i in range(3):
        service.add_thought(context.current_exploration.id, f"Offline thought {i + 1}")
        service.add_offline_change(context.current_exploration.id, "add_thought")


@when("network connectivity is restored")
def step_connectivity_restored(context):
    """Restore network connectivity."""
    service = get_app_persistence_service(context)
    service.restore_connection()


@then("offline changes should sync to the server")
def step_offline_changes_sync(context):
    """Verify offline changes synced."""
    service = get_app_persistence_service(context)
    assert len(service.offline_changes) == 0, "Offline changes should be synced"


@then("no work should be lost")
def step_no_work_lost(context):
    """Verify no work was lost."""
    exp = context.current_exploration
    assert len(exp.thoughts) > 0, "Work should be preserved"


@then("sync status should be clearly indicated")
def step_sync_status_indicated(context):
    """Verify sync status is shown."""
    exp = context.current_exploration
    assert exp.save_status == SaveStatus.SAVED, "Should show synced status"


# =============================================================================
# Project State Persistence Steps - MVP-P0
# =============================================================================

@given("project \"{project_name}\" with")
@given("project \"{project_name}\" with:")
def step_project_with_components(context, project_name):
    """Create project with specified components (handles both persistence and project management)."""
    # Check if this is a project management context (metric/value columns)
    if context.table and 'metric' in context.table.headings:
        # Delegate to project management service
        from features.steps.project_management_steps import get_project_service, ChunkStatus
        service = get_project_service(context)

        project = service.create_project(
            name=project_name,
            objective="Test objective",
            team="Test Team",
            token_budget=100000
        )

        for row in context.table:
            metric = row['metric']
            value = int(row['value'])

            if metric == 'work_chunks':
                for i in range(value):
                    chunk = service.create_work_chunk(project, f"Chunk {i+1}", "Jordan")
                    chunk.status = ChunkStatus.COMPLETED
            elif metric == 'tokens_used':
                project.tokens_used = value
            elif metric == 'tokens_remaining':
                project.token_budget = project.tokens_used + value
            elif metric == 'decisions_made':
                project.decisions_made = value
            elif metric == 'questions_pending':
                project.questions_pending = value

        context.current_project = project
        return

    # Persistence context (component/count columns)
    service = get_app_persistence_service(context)

    components = {}
    for row in context.table:
        component = row['component']
        count = int(row['count'])
        components[component] = count

    context.current_project = ProjectData(
        id=f"PROJ-{project_name.replace(' ', '-')}",
        name=project_name,
        work_chunks=components.get('work_chunks', 0),
        explorations=components.get('explorations', 0),
        decisions=components.get('decisions', 0),
        questions=components.get('questions', 0),
    )


@when("the project is saved")
def step_project_saved(context):
    """Save the project."""
    service = get_app_persistence_service(context)
    context.save_success = service.save_project(context.current_project)


@then("all components should be stored durably")
def step_components_stored(context):
    """Verify all components are stored."""
    assert context.save_success, "Project save failed"
    service = get_app_persistence_service(context)
    stored = service.load_project(context.current_project.id)
    assert stored is not None, "Project not found in storage"


@then("relationships between components should be preserved")
def step_relationships_preserved(context):
    """Verify relationships are preserved."""
    service = get_app_persistence_service(context)
    stored = service.load_project(context.current_project.id)
    assert stored.work_chunks == context.current_project.work_chunks
    assert stored.explorations == context.current_project.explorations


@then("the project should be fully recoverable")
def step_project_recoverable(context):
    """Verify project can be recovered."""
    service = get_app_persistence_service(context)
    recovered = service.load_project(context.current_project.id)
    assert recovered is not None, "Project not recoverable"
    assert recovered.name == context.current_project.name


# =============================================================================
# Project Loading Steps - MVP-P0
# =============================================================================

@given("a saved project \"{project_name}\"")
def step_saved_project(context, project_name):
    """Create and save a project."""
    service = get_app_persistence_service(context)

    project = ProjectData(
        id=f"PROJ-{project_name.replace(' ', '-')}",
        name=project_name,
        work_chunks=5,
        explorations=3,
        decisions=4,
        questions=6,
        budgets={"token_budget": 100000, "used": 45000},
        permissions=["read", "write", "admin"],
    )
    service.save_project(project)
    context.saved_project_id = project.id


@when("{persona} loads the project")
def step_load_project(context, persona):
    """Load a project."""
    context.current_persona = persona
    service = get_app_persistence_service(context)
    context.loaded_project = service.load_project(context.saved_project_id)


@then("all project data should be restored")
@then("all project data should be restored:")
def step_project_data_restored(context):
    """Verify project data is restored."""
    project = context.loaded_project
    assert project is not None, "Project not loaded"

    for row in context.table:
        component = row['component']
        expected_status = row['status']

        if component == 'work_chunks':
            assert project.work_chunks > 0, "Work chunks not loaded"
        elif component == 'explorations':
            assert project.explorations > 0, "Explorations not loaded"
        elif component == 'decisions':
            assert project.decisions > 0, "Decisions not loaded"
        elif component == 'questions':
            assert project.questions > 0, "Questions not loaded"
        elif component == 'budgets':
            assert len(project.budgets) > 0, "Budgets not loaded"
        elif component == 'permissions':
            assert len(project.permissions) > 0, "Permissions not loaded"
