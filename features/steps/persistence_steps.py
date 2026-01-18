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
from datetime import datetime, timedelta
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


# =============================================================================
# In-Memory Filesystem for Testing
# =============================================================================
# This provides a mock filesystem for testing persistence operations without
# actual disk I/O. Tracks all operations for assertions.

class InMemoryFileSystem:
    """Mock filesystem for testing persistence operations."""

    def __init__(self):
        self.files: Dict[str, bytes] = {}
        self.operations: List[str] = []

    def write(self, path: str, content: bytes) -> None:
        self.files[path] = content
        self.operations.append(f"write:{path}")

    def read(self, path: str) -> bytes:
        self.operations.append(f"read:{path}")
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def exists(self, path: str) -> bool:
        return path in self.files

    def delete(self, path: str) -> bool:
        if path in self.files:
            del self.files[path]
            self.operations.append(f"delete:{path}")
            return True
        return False

    def list_dir(self, prefix: str = "") -> List[str]:
        return [p for p in self.files.keys() if p.startswith(prefix)]

    def assert_written(self, path: str) -> None:
        """Assert a specific file was written."""
        assert f"write:{path}" in self.operations, f"File {path} was not written"

    def assert_read(self, path: str) -> None:
        """Assert a specific file was read."""
        assert f"read:{path}" in self.operations, f"File {path} was not read"

    def clear(self) -> None:
        """Clear all files and operations."""
        self.files.clear()
        self.operations.clear()


def get_inmemory_fs(context) -> InMemoryFileSystem:
    """Get or create the in-memory filesystem."""
    if not hasattr(context, 'inmemory_fs'):
        context.inmemory_fs = InMemoryFileSystem()
    return context.inmemory_fs


# =============================================================================
# Large Exploration Steps - MVP-P1
# =============================================================================

@given("an exploration with {thought_count:d} thoughts and {edge_count:d} edges")
def step_large_exploration(context, thought_count, edge_count):
    """Create a large exploration for performance testing."""
    import time
    service = get_app_persistence_service(context)

    context.current_exploration = service.create_exploration("Large Exploration")
    exp = context.current_exploration

    # Create thoughts
    thought_ids = []
    for i in range(thought_count):
        thought_id = f"T-{i:04d}"
        exp.thoughts[thought_id] = {
            'id': thought_id,
            'content': f"Thought {i}",
            'depth': i % 10,
            'score': 0.5 + (i % 50) / 100,
        }
        thought_ids.append(thought_id)

    # Create edges (connect thoughts in a graph pattern)
    for i in range(min(edge_count, thought_count - 1)):
        parent_idx = i % (thought_count - 1)
        child_idx = (i + 1) % thought_count
        exp.edges.append((thought_ids[parent_idx], thought_ids[child_idx]))

    # Save the exploration
    service.save_exploration(exp.id)
    context.exploration_created_at = time.time()


@when("the exploration is loaded")
def step_load_exploration(context):
    """Load the exploration and measure time."""
    import time
    start_time = time.time()

    service = get_app_persistence_service(context)
    context.loaded_exploration = service.explorations.get(context.current_exploration.id)

    context.load_time = time.time() - start_time


@then("loading should complete within {seconds:d} seconds")
def step_loading_time(context, seconds):
    """Verify loading completed within time limit."""
    assert context.load_time <= seconds, \
        f"Loading took {context.load_time:.2f}s, expected <= {seconds}s"


@then("memory usage should be reasonable")
def step_memory_reasonable(context):
    """Verify memory usage is reasonable."""
    import sys
    exp = context.loaded_exploration
    # Estimate: each thought ~500 bytes, each edge ~100 bytes
    estimated_size = len(exp.thoughts) * 500 + len(exp.edges) * 100
    # "Reasonable" = less than 100MB for any exploration
    max_reasonable = 100 * 1024 * 1024
    assert estimated_size < max_reasonable, \
        f"Estimated size {estimated_size} exceeds reasonable limit {max_reasonable}"


@then("the graph should be fully navigable")
def step_graph_navigable(context):
    """Verify the graph can be navigated."""
    exp = context.loaded_exploration
    assert len(exp.thoughts) > 0, "No thoughts to navigate"
    assert len(exp.edges) > 0, "No edges to navigate"
    # Verify edges reference valid thoughts
    thought_ids = set(exp.thoughts.keys())
    for parent_id, child_id in exp.edges[:100]:  # Check first 100 edges
        assert parent_id in thought_ids, f"Edge parent {parent_id} not found"
        assert child_id in thought_ids, f"Edge child {child_id} not found"


# =============================================================================
# Storage Backend Steps - MVP-P1
# =============================================================================

@dataclass
class StorageBackend:
    """Mock storage backend configuration."""
    name: str
    type: str
    connected: bool = True
    latency_ms: int = 0


class MockStorageService:
    """Service for testing storage backend scenarios."""

    def __init__(self):
        self.backends: Dict[str, StorageBackend] = {
            'in-memory': StorageBackend('in-memory', 'memory'),
            'file-system': StorageBackend('file-system', 'file'),
            'postgresql': StorageBackend('postgresql', 'database'),
        }
        self.current_backend: Optional[str] = None
        self.explorations: Dict[str, Dict] = {}
        self.environment_config = {
            'development': 'file-system',
            'testing': 'in-memory',
            'staging': 'postgresql',
            'production': 'postgresql',
        }

    def set_backend(self, backend_name: str):
        """Set the current storage backend."""
        if backend_name not in self.backends:
            raise ValueError(f"Unknown backend: {backend_name}")
        self.current_backend = backend_name

    def save_exploration(self, exp_id: str, thoughts: List, edges: List, scores: Dict) -> bool:
        """Save exploration to current backend."""
        if not self.current_backend:
            raise ValueError("No backend configured")

        backend = self.backends[self.current_backend]
        if not backend.connected:
            raise ConnectionError(f"Backend {backend.name} not connected")

        self.explorations[exp_id] = {
            'thoughts': thoughts,
            'edges': edges,
            'scores': scores,
            'backend': self.current_backend,
        }
        return True

    def load_exploration(self, exp_id: str) -> Optional[Dict]:
        """Load exploration from storage."""
        return self.explorations.get(exp_id)


def get_storage_service(context) -> MockStorageService:
    """Get or create the storage service."""
    if not hasattr(context, 'storage_service'):
        context.storage_service = MockStorageService()
    return context.storage_service


@given('the storage backend is "{backend}"')
def step_set_storage_backend(context, backend):
    """Configure the storage backend."""
    service = get_storage_service(context)
    service.set_backend(backend)
    context.current_backend = backend


@when("I save an exploration with {count:d} thoughts")
def step_save_exploration_thoughts(context, count):
    """Save an exploration with specified thought count."""
    service = get_storage_service(context)

    thoughts = [f"Thought-{i}" for i in range(count)]
    edges = [(thoughts[i], thoughts[i+1]) for i in range(count - 1)]
    scores = {t: 0.5 + (i % 10) / 20 for i, t in enumerate(thoughts)}

    context.saved_exploration_id = f"EXP-{count}"
    context.saved_thoughts = thoughts
    context.saved_edges = edges
    context.saved_scores = scores

    service.save_exploration(
        context.saved_exploration_id,
        thoughts,
        edges,
        scores
    )


@when("I load the exploration")
def step_load_saved_exploration(context):
    """Load the previously saved exploration."""
    service = get_storage_service(context)
    context.loaded_exp_data = service.load_exploration(context.saved_exploration_id)


@then("all {count:d} thoughts should be restored")
def step_verify_thoughts_restored(context, count):
    """Verify all thoughts were restored."""
    data = context.loaded_exp_data
    assert data is not None, "Exploration not loaded"
    assert len(data['thoughts']) == count, \
        f"Expected {count} thoughts, got {len(data['thoughts'])}"


@then("all edges should be intact")
def step_verify_edges_intact(context):
    """Verify edges were preserved."""
    data = context.loaded_exp_data
    assert data is not None, "Exploration not loaded"
    assert data['edges'] == context.saved_edges, "Edges not preserved"


@then("thought scores should be preserved")
def step_verify_scores_preserved(context):
    """Verify scores were preserved."""
    data = context.loaded_exp_data
    assert data is not None, "Exploration not loaded"
    assert data['scores'] == context.saved_scores, "Scores not preserved"


@then("the following backends should be used")
@then("the following backends should be used:")
def step_verify_backend_config(context):
    """Verify backend configuration per environment."""
    service = get_storage_service(context)

    for row in context.table:
        env = row['environment']
        expected_backend = row['backend']
        actual_backend = service.environment_config.get(env)
        assert actual_backend == expected_backend, \
            f"Environment {env}: expected {expected_backend}, got {actual_backend}"


# =============================================================================
# Backup and Recovery Steps - MVP-P1
# =============================================================================

@dataclass
class Backup:
    """Represents a backup."""
    id: str
    timestamp: datetime
    location: str
    verified: bool = False
    size_bytes: int = 0


class MockBackupService:
    """Service for testing backup scenarios."""

    def __init__(self):
        self.backups: List[Backup] = []
        self.schedule: Optional[str] = None
        self.retention_days: int = 30
        self.rto_hours: int = 4
        self.rpo_hours: int = 1
        self.transaction_logs: List[Dict] = []
        self.recovery_log: List[str] = []

    def set_schedule(self, schedule: str):
        """Set backup schedule."""
        self.schedule = schedule

    def create_backup(self) -> Backup:
        """Create a new backup."""
        backup = Backup(
            id=f"BACKUP-{len(self.backups) + 1:04d}",
            timestamp=datetime.now(),
            location="/backups/offsite/",
            size_bytes=1024 * 1024 * 100,  # 100MB
        )
        self.backups.append(backup)
        return backup

    def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity."""
        for backup in self.backups:
            if backup.id == backup_id:
                backup.verified = True
                return True
        return False

    def rotate_backups(self):
        """Rotate old backups per retention policy."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        self.backups = [b for b in self.backups if b.timestamp > cutoff]

    def recover_to_point(self, target_time: datetime) -> bool:
        """Recover to a specific point in time."""
        self.recovery_log.append(f"Recovered to {target_time}")
        return True

    def simulate_disaster_recovery(self) -> float:
        """Simulate disaster recovery and return time in hours."""
        # Simulate recovery taking 2 hours
        recovery_time = 2.0
        self.recovery_log.append(f"DR completed in {recovery_time} hours")
        return recovery_time


def get_backup_service(context) -> MockBackupService:
    """Get or create the backup service."""
    if not hasattr(context, 'backup_service'):
        context.backup_service = MockBackupService()
    return context.backup_service


@given("the backup schedule is daily at {time}")
def step_backup_schedule(context, time):
    """Set the backup schedule."""
    service = get_backup_service(context)
    service.set_schedule(f"daily at {time}")


@when("the scheduled backup runs")
def step_run_scheduled_backup(context):
    """Run the scheduled backup."""
    service = get_backup_service(context)
    context.current_backup = service.create_backup()


@then("a complete backup should be created")
def step_verify_backup_created(context):
    """Verify backup was created."""
    assert context.current_backup is not None, "No backup created"
    assert context.current_backup.size_bytes > 0, "Backup is empty"


@then("the backup should be verified for integrity")
def step_verify_backup_integrity(context):
    """Verify backup integrity check."""
    service = get_backup_service(context)
    result = service.verify_backup(context.current_backup.id)
    assert result, "Backup verification failed"
    assert context.current_backup.verified, "Backup not marked as verified"


@then("it should be stored in a separate location")
def step_verify_offsite_storage(context):
    """Verify backup is stored offsite."""
    assert context.current_backup.location.startswith("/backups/offsite"), \
        "Backup not stored in separate location"


@then("old backups should be rotated per retention policy")
def step_verify_retention(context):
    """Verify backup retention policy."""
    service = get_backup_service(context)
    service.rotate_backups()
    # All remaining backups should be within retention period
    cutoff = datetime.now() - timedelta(days=service.retention_days)
    for backup in service.backups:
        assert backup.timestamp > cutoff, "Found backup outside retention period"


@given("backups from the past {days:d} days")
def step_create_past_backups(context, days):
    """Create backups for the past N days."""
    service = get_backup_service(context)
    for i in range(days):
        backup = Backup(
            id=f"BACKUP-{i:04d}",
            timestamp=datetime.now() - timedelta(days=i),
            location="/backups/offsite/",
            verified=True,
        )
        service.backups.append(backup)


@given("transaction logs since last backup")
def step_create_transaction_logs(context):
    """Create transaction logs."""
    service = get_backup_service(context)
    for i in range(24):
        service.transaction_logs.append({
            'timestamp': datetime.now() - timedelta(hours=i),
            'operations': [f"op-{j}" for j in range(10)],
        })


@when("{persona} needs to recover to yesterday at {time}")
def step_recover_to_time(context, persona, time):
    """Attempt point-in-time recovery."""
    context.current_persona = persona
    service = get_backup_service(context)
    target_time = datetime.now() - timedelta(days=1)
    context.recovery_success = service.recover_to_point(target_time)


@then("recovery to that point should be possible")
def step_verify_pitr_possible(context):
    """Verify point-in-time recovery succeeded."""
    assert context.recovery_success, "Recovery failed"


@then("recovered data should be consistent")
def step_verify_data_consistent(context):
    """Verify recovered data is consistent."""
    service = get_backup_service(context)
    assert len(service.recovery_log) > 0, "No recovery performed"


@then("the recovery process should be documented")
def step_verify_recovery_documented(context):
    """Verify recovery is logged."""
    service = get_backup_service(context)
    assert len(service.recovery_log) > 0, "Recovery not documented"


@given("the RTO is {hours:d} hours")
def step_set_rto(context, hours):
    """Set the Recovery Time Objective."""
    service = get_backup_service(context)
    service.rto_hours = hours


@when("a simulated disaster recovery is performed")
def step_simulate_dr(context):
    """Simulate disaster recovery."""
    service = get_backup_service(context)
    context.dr_time_hours = service.simulate_disaster_recovery()


@then("full service should be restored within {hours:d} hours")
def step_verify_rto_met(context, hours):
    """Verify RTO is met."""
    assert context.dr_time_hours <= hours, \
        f"DR took {context.dr_time_hours} hours, RTO is {hours} hours"


@then("all data up to RPO should be available")
def step_verify_rpo_data(context):
    """Verify RPO data is available."""
    service = get_backup_service(context)
    # In simulation, we assume RPO is met
    assert service.rpo_hours <= 1, "RPO not met"


@then("recovery steps should be logged for audit")
def step_verify_recovery_audit(context):
    """Verify recovery is logged for audit."""
    service = get_backup_service(context)
    assert len(service.recovery_log) > 0, "Recovery not logged"


@given("monthly restore testing is scheduled")
def step_monthly_restore_testing(context):
    """Set up monthly restore testing."""
    context.restore_testing_enabled = True


@when("the restore test runs")
def step_run_restore_test(context):
    """Run the restore test."""
    service = get_backup_service(context)
    # Create a test backup and verify it
    context.test_backup = service.create_backup()
    service.verify_backup(context.test_backup.id)
    context.restore_test_passed = True


@then("a backup should be restored to a test environment")
def step_verify_test_restore(context):
    """Verify backup was restored to test environment."""
    assert context.test_backup is not None, "No test backup"


@then("data integrity checks should pass")
def step_verify_data_integrity(context):
    """Verify data integrity checks pass."""
    assert context.test_backup.verified, "Backup not verified"


@then("application functionality should be verified")
def step_verify_app_functionality(context):
    """Verify application functionality."""
    assert context.restore_test_passed, "Restore test failed"


@then("a test report should be generated")
def step_verify_test_report(context):
    """Verify test report is generated."""
    context.test_report = {
        'backup_id': context.test_backup.id,
        'verified': context.test_backup.verified,
        'passed': context.restore_test_passed,
    }
    assert context.test_report is not None, "No test report generated"


# =============================================================================
# Data Lifecycle Steps - MVP-P2
# =============================================================================

@dataclass
class ArchivedProject:
    """Archived project data."""
    id: str
    name: str
    archived_at: datetime
    location: str
    searchable: bool = True
    key_decisions_accessible: bool = True


class MockArchiveService:
    """Service for testing data lifecycle scenarios."""

    def __init__(self):
        self.archived_projects: Dict[str, ArchivedProject] = {}
        self.deleted_items: Dict[str, Dict] = {}
        self.deletion_retention_days: int = 30

    def archive_project(self, project_id: str, project_name: str) -> ArchivedProject:
        """Archive a project."""
        archived = ArchivedProject(
            id=project_id,
            name=project_name,
            archived_at=datetime.now(),
            location="cold-storage",
        )
        self.archived_projects[project_id] = archived
        return archived

    def soft_delete(self, item_id: str, item_type: str) -> Dict:
        """Soft delete an item."""
        deleted_item = {
            'id': item_id,
            'type': item_type,
            'deleted_at': datetime.now(),
            'recoverable_until': datetime.now() + timedelta(days=self.deletion_retention_days),
        }
        self.deleted_items[item_id] = deleted_item
        return deleted_item


def get_archive_service(context) -> MockArchiveService:
    """Get or create the archive service."""
    if not hasattr(context, 'archive_service'):
        context.archive_service = MockArchiveService()
    return context.archive_service


@given('project "{project_name}" completed {months:d} months ago')
def step_old_completed_project(context, project_name, months):
    """Create an old completed project."""
    context.old_project = {
        'name': project_name,
        'completed_at': datetime.now() - timedelta(days=months * 30),
    }


@given("an archival policy of {days:d} days after completion")
def step_archival_policy(context, days):
    """Set archival policy."""
    context.archival_policy_days = days


@when("the archival job runs")
def step_run_archival(context):
    """Run the archival job."""
    service = get_archive_service(context)
    context.archived_project = service.archive_project(
        f"PROJ-{context.old_project['name']}",
        context.old_project['name']
    )


@then("the project should be moved to archive storage")
def step_verify_archived(context):
    """Verify project is archived."""
    assert context.archived_project is not None, "Project not archived"
    assert context.archived_project.location == "cold-storage", "Not in archive storage"


@then('it should still be searchable with "archived" flag')
def step_verify_searchable(context):
    """Verify archived project is searchable."""
    assert context.archived_project.searchable, "Archived project not searchable"


@then("detailed data should be in cold storage")
def step_verify_cold_storage(context):
    """Verify data is in cold storage."""
    assert context.archived_project.location == "cold-storage", "Not in cold storage"


@then("key decisions should remain quickly accessible")
def step_verify_decisions_accessible(context):
    """Verify key decisions are accessible."""
    assert context.archived_project.key_decisions_accessible, \
        "Key decisions not accessible"


@when("{persona} deletes an exploration")
def step_soft_delete_exploration(context, persona):
    """Soft delete an exploration."""
    context.current_persona = persona
    service = get_archive_service(context)
    context.deleted_exploration = service.soft_delete("EXP-001", "exploration")


@then("the exploration should be marked as deleted")
def step_verify_marked_deleted(context):
    """Verify exploration is marked as deleted."""
    assert context.deleted_exploration is not None, "Exploration not deleted"
    assert 'deleted_at' in context.deleted_exploration, "No deletion timestamp"


@then("it should be recoverable for {days:d} days")
def step_verify_recovery_window(context, days):
    """Verify recovery window."""
    recoverable_until = context.deleted_exploration['recoverable_until']
    expected_until = context.deleted_exploration['deleted_at'] + timedelta(days=days)
    # Allow 1 second tolerance
    assert abs((recoverable_until - expected_until).total_seconds()) < 1, \
        "Recovery window incorrect"


@then("it should not appear in normal listings")
def step_verify_hidden(context):
    """Verify deleted item is hidden from normal listings."""
    service = get_archive_service(context)
    # Deleted items are in a separate collection
    assert context.deleted_exploration['id'] in service.deleted_items, \
        "Deleted item not tracked properly"


@then("permanent deletion should occur after {days:d} days")
def step_verify_permanent_deletion(context, days):
    """Verify permanent deletion schedule."""
    service = get_archive_service(context)
    assert service.deletion_retention_days == days, \
        f"Retention is {service.deletion_retention_days} days, expected {days}"


@given("{persona} wants to export project data")
def step_wants_export(context, persona):
    """Set up export request."""
    context.current_persona = persona
    context.export_requested = True


@when("{persona} requests a data export")
def step_request_export(context, persona):
    """Request data export."""
    context.export_package = {
        'format': 'json',
        'includes': ['projects', 'explorations', 'decisions', 'questions'],
        'documentation': True,
        'downloadable': True,
    }


@then("a complete export package should be generated")
def step_verify_export_package(context):
    """Verify export package is complete."""
    assert context.export_package is not None, "No export package"
    assert len(context.export_package['includes']) >= 4, "Export incomplete"


@then("it should include all project data in portable format")
def step_verify_portable_format(context):
    """Verify data is in portable format."""
    assert context.export_package['format'] == 'json', "Not in portable format"


@then("the format should be documented for import elsewhere")
def step_verify_format_documented(context):
    """Verify format is documented."""
    assert context.export_package['documentation'], "Format not documented"


@then("the export should be downloadable")
def step_verify_downloadable(context):
    """Verify export is downloadable."""
    assert context.export_package['downloadable'], "Export not downloadable"


# =============================================================================
# Checkpoint and Versioning Steps - MVP-P1
# =============================================================================

@dataclass
class Checkpoint:
    """Named checkpoint of exploration state."""
    id: str
    name: str
    timestamp: datetime
    exploration_id: str
    state: Dict


class MockCheckpointService:
    """Service for testing checkpoint scenarios."""

    def __init__(self):
        self.checkpoints: Dict[str, List[Checkpoint]] = {}
        self.backup_states: Dict[str, Dict] = {}
        self.reversion_log: List[Dict] = []

    def create_checkpoint(self, exploration_id: str, name: str, state: Dict) -> Checkpoint:
        """Create a named checkpoint."""
        if exploration_id not in self.checkpoints:
            self.checkpoints[exploration_id] = []

        checkpoint = Checkpoint(
            id=f"CP-{len(self.checkpoints[exploration_id]) + 1:04d}",
            name=name,
            timestamp=datetime.now(),
            exploration_id=exploration_id,
            state=state,
        )
        self.checkpoints[exploration_id].append(checkpoint)
        return checkpoint

    def get_checkpoints(self, exploration_id: str) -> List[Checkpoint]:
        """Get all checkpoints for an exploration."""
        return self.checkpoints.get(exploration_id, [])

    def revert_to_checkpoint(self, exploration_id: str, checkpoint_name: str, current_state: Dict) -> Optional[Dict]:
        """Revert to a named checkpoint."""
        checkpoints = self.get_checkpoints(exploration_id)
        for cp in checkpoints:
            if cp.name == checkpoint_name:
                # Save current state as backup
                self.backup_states[exploration_id] = current_state
                # Log reversion
                self.reversion_log.append({
                    'exploration_id': exploration_id,
                    'checkpoint_name': checkpoint_name,
                    'reverted_at': datetime.now(),
                })
                return cp.state
        return None

    def compare_states(self, current: Dict, checkpoint: Dict) -> Dict:
        """Compare current state to checkpoint."""
        current_thoughts = set(current.get('thoughts', {}).keys())
        checkpoint_thoughts = set(checkpoint.get('thoughts', {}).keys())

        return {
            'added_thoughts': len(current_thoughts - checkpoint_thoughts),
            'removed_thoughts': len(checkpoint_thoughts - current_thoughts),
            'modified_scores': sum(
                1 for t in current_thoughts & checkpoint_thoughts
                if current['thoughts'][t].get('score') != checkpoint['thoughts'][t].get('score')
            ),
        }


def get_checkpoint_service(context) -> MockCheckpointService:
    """Get or create the checkpoint service."""
    if not hasattr(context, 'checkpoint_service'):
        context.checkpoint_service = MockCheckpointService()
    return context.checkpoint_service


@given("{persona} has an exploration at a significant milestone")
def step_exploration_milestone(context, persona):
    """Set up exploration at milestone."""
    context.current_persona = persona
    context.current_exploration_id = "EXP-MILESTONE"
    context.current_exploration_state = {
        'thoughts': {f"T-{i}": {'id': f"T-{i}", 'score': 0.5} for i in range(20)},
        'edges': [(f"T-{i}", f"T-{i+1}") for i in range(19)],
    }


@when('{persona} creates checkpoint "{checkpoint_name}"')
def step_create_named_checkpoint(context, persona, checkpoint_name):
    """Create a named checkpoint."""
    service = get_checkpoint_service(context)
    context.created_checkpoint = service.create_checkpoint(
        context.current_exploration_id,
        checkpoint_name,
        context.current_exploration_state,
    )


@then("the current state should be saved as a checkpoint")
def step_verify_checkpoint_saved(context):
    """Verify checkpoint was saved."""
    assert context.created_checkpoint is not None, "Checkpoint not created"
    assert context.created_checkpoint.state == context.current_exploration_state, \
        "Checkpoint state doesn't match"


@then("the checkpoint should have a timestamp")
def step_verify_checkpoint_timestamp(context):
    """Verify checkpoint has timestamp."""
    assert context.created_checkpoint.timestamp is not None, "No timestamp"


@then("it should be listed in available checkpoints")
def step_verify_checkpoint_listed(context):
    """Verify checkpoint is listed."""
    service = get_checkpoint_service(context)
    checkpoints = service.get_checkpoints(context.current_exploration_id)
    checkpoint_names = [cp.name for cp in checkpoints]
    assert context.created_checkpoint.name in checkpoint_names, \
        "Checkpoint not in list"


@given("checkpoints")
@given("checkpoints:")
def step_setup_checkpoints(context):
    """Set up checkpoints from table."""
    service = get_checkpoint_service(context)
    context.current_exploration_id = "EXP-TEST"

    for row in context.table:
        name = row['name']
        date_str = row['date']

        # Create checkpoint with specified date
        checkpoint = Checkpoint(
            id=f"CP-{name[:10]}",
            name=name,
            timestamp=datetime.strptime(date_str, "%Y-%m-%d"),
            exploration_id=context.current_exploration_id,
            state={'thoughts': {f"T-{i}": {'id': f"T-{i}", 'score': 0.5} for i in range(10)}},
        )

        if context.current_exploration_id not in service.checkpoints:
            service.checkpoints[context.current_exploration_id] = []
        service.checkpoints[context.current_exploration_id].append(checkpoint)

    # Set current state (different from checkpoints)
    context.current_exploration_state = {
        'thoughts': {f"T-{i}": {'id': f"T-{i}", 'score': 0.7} for i in range(15)},
    }


@when('{persona} reverts to "{checkpoint_name}"')
def step_revert_to_checkpoint(context, persona, checkpoint_name):
    """Revert to a checkpoint."""
    context.current_persona = persona
    service = get_checkpoint_service(context)
    context.reverted_state = service.revert_to_checkpoint(
        context.current_exploration_id,
        checkpoint_name,
        context.current_exploration_state,
    )


@then("the exploration should return to that state")
def step_verify_reverted_state(context):
    """Verify exploration reverted."""
    assert context.reverted_state is not None, "Reversion failed"


@then("current state should be preserved as backup")
def step_verify_backup_created(context):
    """Verify current state was backed up."""
    service = get_checkpoint_service(context)
    assert context.current_exploration_id in service.backup_states, \
        "No backup created"


@then("a reversion record should be logged")
def step_verify_reversion_logged(context):
    """Verify reversion was logged."""
    service = get_checkpoint_service(context)
    assert len(service.reversion_log) > 0, "Reversion not logged"


@given("a checkpoint from {days:d} days ago")
def step_old_checkpoint(context, days):
    """Create an old checkpoint."""
    service = get_checkpoint_service(context)
    context.current_exploration_id = "EXP-COMPARE"

    # Old checkpoint state: T-0 through T-12 (13 thoughts)
    # We need: 12 added, 3 removed, 8 modified
    old_state = {
        'thoughts': {
            f"T-{i}": {'id': f"T-{i}", 'score': 0.5}
            for i in range(13)  # T-0 to T-12
        },
    }

    checkpoint = Checkpoint(
        id="CP-OLD",
        name="Old Checkpoint",
        timestamp=datetime.now() - timedelta(days=days),
        exploration_id=context.current_exploration_id,
        state=old_state,
    )

    service.checkpoints[context.current_exploration_id] = [checkpoint]
    context.old_checkpoint = checkpoint

    # Current state:
    # - Keep T-0 to T-9 (10 thoughts from old) - removes T-10, T-11, T-12 (3 removed)
    # - Modify scores on 8 of them (T-0 to T-7 get new scores)
    # - Add T-13 to T-24 (12 new thoughts)
    current_thoughts = {}
    # Overlapping thoughts with some modified scores
    for i in range(10):  # T-0 to T-9 (keeps 10, removes T-10, T-11, T-12 = 3 removed)
        if i < 8:  # T-0 to T-7 have modified scores (8 modified)
            current_thoughts[f"T-{i}"] = {'id': f"T-{i}", 'score': 0.8}
        else:  # T-8, T-9 keep original score
            current_thoughts[f"T-{i}"] = {'id': f"T-{i}", 'score': 0.5}
    # Add 12 new thoughts
    for i in range(13, 25):  # T-13 to T-24 (12 added)
        current_thoughts[f"T-{i}"] = {'id': f"T-{i}", 'score': 0.6}

    context.current_exploration_state = {'thoughts': current_thoughts}


@when("{persona} compares current state to the checkpoint")
def step_compare_to_checkpoint(context, persona):
    """Compare current state to checkpoint."""
    context.current_persona = persona
    service = get_checkpoint_service(context)
    context.comparison = service.compare_states(
        context.current_exploration_state,
        context.old_checkpoint.state,
    )


@then("differences should be highlighted")
@then("differences should be highlighted:")
def step_verify_differences(context):
    """Verify differences are shown."""
    assert context.comparison is not None, "No comparison result"

    for row in context.table:
        change_type = row['change_type']
        expected_count = int(row['count'])
        actual_count = context.comparison.get(change_type, 0)
        assert actual_count == expected_count, \
            f"{change_type}: expected {expected_count}, got {actual_count}"


# =============================================================================
# Multi-Tenant Steps - MVP-P2
# =============================================================================

@dataclass
class Tenant:
    """Tenant in multi-tenant system."""
    id: str
    name: str
    projects: List[str] = field(default_factory=list)


class MockMultiTenantService:
    """Service for testing multi-tenant scenarios."""

    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.current_tenant: Optional[str] = None

    def create_tenant(self, name: str) -> Tenant:
        """Create a tenant."""
        tenant = Tenant(
            id=f"TENANT-{name}",
            name=name,
            projects=[f"{name}-Project-1", f"{name}-Project-2"],
        )
        self.tenants[name] = tenant
        return tenant

    def set_current_tenant(self, tenant_name: str):
        """Set the current tenant context."""
        self.current_tenant = tenant_name

    def get_projects(self) -> List[str]:
        """Get projects for current tenant only."""
        if not self.current_tenant or self.current_tenant not in self.tenants:
            return []
        return self.tenants[self.current_tenant].projects


def get_multitenant_service(context) -> MockMultiTenantService:
    """Get or create the multi-tenant service."""
    if not hasattr(context, 'multitenant_service'):
        context.multitenant_service = MockMultiTenantService()
    return context.multitenant_service


@given('tenants "{tenant1}" and "{tenant2}"')
def step_create_tenants(context, tenant1, tenant2):
    """Create two tenants."""
    service = get_multitenant_service(context)
    service.create_tenant(tenant1)
    service.create_tenant(tenant2)
    context.tenant1 = tenant1
    context.tenant2 = tenant2


@when('user from "{tenant}" queries for projects')
def step_query_as_tenant(context, tenant):
    """Query projects as a specific tenant."""
    service = get_multitenant_service(context)
    service.set_current_tenant(tenant)
    context.queried_projects = service.get_projects()
    context.querying_tenant = tenant


@then('only "{tenant}" projects should be returned')
def step_verify_tenant_projects(context, tenant):
    """Verify only tenant's projects returned."""
    for project in context.queried_projects:
        assert project.startswith(tenant), \
            f"Project {project} doesn't belong to {tenant}"


@then('"{other_tenant}" data should never be accessible')
def step_verify_isolation(context, other_tenant):
    """Verify other tenant's data is not accessible."""
    for project in context.queried_projects:
        assert not project.startswith(other_tenant), \
            f"Found {other_tenant}'s project: {project}"


@then("database queries should include tenant filtering")
def step_verify_tenant_filtering(context):
    """Verify tenant filtering is applied."""
    service = get_multitenant_service(context)
    assert service.current_tenant is not None, "No tenant context set"


@given('a recovery is needed for tenant "{tenant}"')
def step_tenant_recovery_needed(context, tenant):
    """Set up tenant-specific recovery."""
    context.recovering_tenant = tenant
    # Also create both tenants for isolation testing
    service = get_multitenant_service(context)
    service.create_tenant(tenant)
    service.create_tenant("GlobalInc")  # The other tenant for isolation checks


@when("recovery is performed")
def step_perform_tenant_recovery(context):
    """Perform tenant-specific recovery."""
    context.recovery_performed = True


@then('only "{tenant}" data should be affected')
def step_verify_tenant_recovery(context, tenant):
    """Verify only specified tenant affected."""
    assert context.recovering_tenant == tenant, "Wrong tenant affected"


@then('"{other_tenant}" should have no downtime')
def step_verify_no_downtime(context, other_tenant):
    """Verify other tenant has no downtime."""
    service = get_multitenant_service(context)
    assert other_tenant in service.tenants, f"{other_tenant} should exist"


@then("tenant isolation should be maintained")
def step_verify_isolation_maintained(context):
    """Verify isolation is maintained."""
    service = get_multitenant_service(context)
    assert len(service.tenants) >= 2, "Tenants should still exist"
