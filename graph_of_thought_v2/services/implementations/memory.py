"""
In-Memory Implementations - For Testing and Development
========================================================

These implementations store everything in memory. They're perfect for:

1. UNIT TESTING
   - Fast (no I/O)
   - Deterministic (no external dependencies)
   - Inspectable (check internal state in assertions)

2. INTEGRATION TESTING
   - Full application flow without external services
   - Verify behavior, not just mocks

3. LOCAL DEVELOPMENT
   - No setup required
   - Works offline
   - Quick iteration

DESIGN PRINCIPLES
-----------------

1. MATCH THE PROTOCOL EXACTLY
   Every method in the protocol is implemented. No extras.

2. SIMPLE DATA STRUCTURES
   Lists and dicts. No complex state machines.

3. INSPECTABLE STATE
   Public attributes allow tests to check internal state.

4. NO SIDE EFFECTS OUTSIDE THE OBJECT
   No file I/O, no network calls, no globals.

TESTING PATTERN
---------------

    def test_search_persists_graph():
        # Arrange
        persistence = InMemoryPersistence()
        app = ApplicationBuilder().with_persistence(persistence).build()

        # Act
        graph = app.create_graph()
        graph.add(Thought(content="test"))
        graph_id = await app.save(graph)

        # Assert
        assert graph_id in persistence.graphs  # Inspect internal state
        assert len(persistence.graphs[graph_id]) == 1

"""

from typing import Any, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from graph_of_thought_v2.core import Graph, Thought

T = TypeVar("T")


# =============================================================================
# IN-MEMORY LOGGER
# =============================================================================

@dataclass
class LogEntry:
    """A single log entry."""
    timestamp: datetime
    level: str
    message: str
    data: dict[str, Any]


class InMemoryLogger:
    """
    Logger that stores entries in memory.

    Perfect for testing - you can assert on logged messages.

    Attributes:
        entries: All log entries, in order.
        context: Bound context for this logger.

    Example:
        logger = InMemoryLogger()
        logger.info("Something happened", key="value")

        assert len(logger.entries) == 1
        assert logger.entries[0].message == "Something happened"
        assert logger.entries[0].data["key"] == "value"
    """

    def __init__(self, context: dict[str, Any] | None = None) -> None:
        self.entries: list[LogEntry] = []
        self.context: dict[str, Any] = context or {}

    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        """Internal logging method."""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            message=message,
            data={**self.context, **kwargs},
        )
        self.entries.append(entry)

    def debug(self, message: str, **kwargs: Any) -> None:
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log("ERROR", message, **kwargs)

    def bind(self, **kwargs: Any) -> "InMemoryLogger":
        """Create child logger with additional context."""
        child = InMemoryLogger(context={**self.context, **kwargs})
        child.entries = self.entries  # Share log storage
        return child

    # -------------------------------------------------------------------------
    # Testing helpers (not part of protocol)
    # -------------------------------------------------------------------------

    def clear(self) -> None:
        """Clear all entries. Useful between tests."""
        self.entries.clear()

    def get_messages(self, level: str | None = None) -> list[str]:
        """Get all messages, optionally filtered by level."""
        if level is None:
            return [e.message for e in self.entries]
        return [e.message for e in self.entries if e.level == level]

    def has_message(self, message: str, level: str | None = None) -> bool:
        """Check if a message was logged."""
        return message in self.get_messages(level)


# =============================================================================
# IN-MEMORY METRICS
# =============================================================================

class InMemoryMetrics:
    """
    Metrics collector that stores in memory.

    Stores counters, gauges, and histograms for inspection in tests.

    Attributes:
        counters: Counter name → total value.
        gauges: Gauge name → current value.
        histograms: Histogram name → list of recorded values.

    Example:
        metrics = InMemoryMetrics()
        metrics.increment("requests", tags={"endpoint": "/api"})
        metrics.histogram("latency_ms", 150)

        assert metrics.counters["requests"] == 1
        assert 150 in metrics.histograms["latency_ms"]
    """

    def __init__(self) -> None:
        self.counters: dict[str, int] = {}
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, list[float]] = {}
        # Store tags separately for inspection
        self.counter_tags: dict[str, list[dict[str, str]]] = {}

    def increment(self, name: str, value: int = 1, **tags: str) -> None:
        """Increment a counter."""
        self.counters[name] = self.counters.get(name, 0) + value
        if name not in self.counter_tags:
            self.counter_tags[name] = []
        self.counter_tags[name].append(tags)

    def gauge(self, name: str, value: float, **tags: str) -> None:
        """Set a gauge value."""
        self.gauges[name] = value

    def histogram(self, name: str, value: float, **tags: str) -> None:
        """Record a histogram value."""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)

    # -------------------------------------------------------------------------
    # Testing helpers (not part of protocol)
    # -------------------------------------------------------------------------

    def clear(self) -> None:
        """Clear all metrics. Useful between tests."""
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.counter_tags.clear()

    def get_counter(self, name: str) -> int:
        """Get counter value, defaulting to 0."""
        return self.counters.get(name, 0)

    def get_histogram_avg(self, name: str) -> float | None:
        """Get average of histogram values."""
        values = self.histograms.get(name, [])
        if not values:
            return None
        return sum(values) / len(values)


# =============================================================================
# IN-MEMORY PERSISTENCE
# =============================================================================

class InMemoryPersistence(Generic[T]):
    """
    Persistence that stores graphs in memory.

    Graphs are stored as-is (no serialization). This is fast but
    graphs don't survive process restart.

    Attributes:
        graphs: Graph ID → Graph object.
        metadata: Graph ID → metadata dict.

    Example:
        persistence = InMemoryPersistence()

        graph_id = await persistence.save(graph, context)
        loaded = await persistence.load(graph_id, context)

        assert loaded is not None
        assert len(loaded) == len(graph)
    """

    def __init__(self) -> None:
        self.graphs: dict[str, Graph[T]] = {}
        self.metadata: dict[str, dict[str, Any]] = {}

    async def save(self, graph: Graph[T], context: Any) -> str:
        """Save graph and return ID."""
        graph_id = str(uuid4())

        # Store the graph directly (no serialization in memory impl)
        self.graphs[graph_id] = graph

        # Store metadata from context
        self.metadata[graph_id] = {
            "saved_at": datetime.now().isoformat(),
            "user_id": getattr(context, "user_id", None),
            "project_id": getattr(context, "project_id", None),
            "thought_count": len(graph),
        }

        return graph_id

    async def load(self, graph_id: str, context: Any) -> Graph[T] | None:
        """Load graph by ID."""
        return self.graphs.get(graph_id)

    async def delete(self, graph_id: str, context: Any) -> bool:
        """Delete graph by ID."""
        if graph_id in self.graphs:
            del self.graphs[graph_id]
            del self.metadata[graph_id]
            return True
        return False

    async def list_graphs(self, context: Any) -> list[str]:
        """List all graph IDs."""
        # In a real implementation, this would filter by user/project
        return list(self.graphs.keys())

    # -------------------------------------------------------------------------
    # Testing helpers (not part of protocol)
    # -------------------------------------------------------------------------

    def clear(self) -> None:
        """Clear all stored graphs. Useful between tests."""
        self.graphs.clear()
        self.metadata.clear()

    def count(self) -> int:
        """Get number of stored graphs."""
        return len(self.graphs)
