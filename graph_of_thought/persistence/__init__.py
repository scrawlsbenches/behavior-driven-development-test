"""
Persistence backends for Graph of Thought.

This module provides persistence implementations for storing
and retrieving graph state. Add implementations as needed.

Example implementations that could be added:
- SQLitePersistence: Local SQLite database storage
- PostgresPersistence: PostgreSQL database storage  
- RedisPersistence: Redis cache storage
- S3Persistence: S3 bucket storage for checkpoints
"""

from __future__ import annotations
from typing import TypeVar, Any
import json
import os
from pathlib import Path

from ..core import (
    Thought,
    Edge,
    GraphPersistence,
    IncrementalPersistence,
    PersistenceError,
)

T = TypeVar("T")


class InMemoryPersistence:
    """
    In-memory persistence for testing and development.
    
    Data is lost when the process exits.
    """
    
    def __init__(self):
        self._graphs: dict[str, dict[str, Any]] = {}
        self._checkpoints: dict[str, dict[str, dict[str, Any]]] = {}
    
    async def save_graph(
        self,
        graph_id: str,
        thoughts: dict[str, Thought],
        edges: list[Edge],
        root_ids: list[str],
        metadata: dict[str, Any],
    ) -> None:
        self._graphs[graph_id] = {
            "thoughts": {tid: t.to_dict() for tid, t in thoughts.items()},
            "edges": [e.to_dict() for e in edges],
            "root_ids": root_ids,
            "metadata": metadata,
        }
    
    async def load_graph(
        self,
        graph_id: str,
    ) -> tuple[dict[str, Thought], list[Edge], list[str], dict[str, Any]] | None:
        if graph_id not in self._graphs:
            return None
        
        data = self._graphs[graph_id]
        thoughts = {tid: Thought.from_dict(td) for tid, td in data["thoughts"].items()}
        edges = [Edge.from_dict(ed) for ed in data["edges"]]
        return thoughts, edges, data["root_ids"], data["metadata"]
    
    async def save_checkpoint(
        self,
        graph_id: str,
        checkpoint_id: str,
        thoughts: dict[str, Thought],
        edges: list[Edge],
        root_ids: list[str],
        search_state: dict[str, Any],
    ) -> None:
        if graph_id not in self._checkpoints:
            self._checkpoints[graph_id] = {}
        
        self._checkpoints[graph_id][checkpoint_id] = {
            "thoughts": {tid: t.to_dict() for tid, t in thoughts.items()},
            "edges": [e.to_dict() for e in edges],
            "root_ids": root_ids,
            "search_state": search_state,
        }
    
    async def load_checkpoint(
        self,
        graph_id: str,
        checkpoint_id: str,
    ) -> tuple[dict[str, Thought], list[Edge], list[str], dict[str, Any]] | None:
        if graph_id not in self._checkpoints:
            return None
        if checkpoint_id not in self._checkpoints[graph_id]:
            return None
        
        data = self._checkpoints[graph_id][checkpoint_id]
        thoughts = {tid: Thought.from_dict(td) for tid, td in data["thoughts"].items()}
        edges = [Edge.from_dict(ed) for ed in data["edges"]]
        return thoughts, edges, data["root_ids"], data["search_state"]
    
    async def delete_graph(self, graph_id: str) -> bool:
        if graph_id in self._graphs:
            del self._graphs[graph_id]
            self._checkpoints.pop(graph_id, None)
            return True
        return False


class FilePersistence:
    """
    File-based persistence using JSON files.
    
    Suitable for development and small-scale usage.
    """
    
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _graph_path(self, graph_id: str) -> Path:
        return self.base_dir / f"{graph_id}.json"
    
    def _checkpoint_dir(self, graph_id: str) -> Path:
        return self.base_dir / "checkpoints" / graph_id
    
    def _checkpoint_path(self, graph_id: str, checkpoint_id: str) -> Path:
        return self._checkpoint_dir(graph_id) / f"{checkpoint_id}.json"
    
    async def save_graph(
        self,
        graph_id: str,
        thoughts: dict[str, Thought],
        edges: list[Edge],
        root_ids: list[str],
        metadata: dict[str, Any],
    ) -> None:
        data = {
            "thoughts": {tid: t.to_dict() for tid, t in thoughts.items()},
            "edges": [e.to_dict() for e in edges],
            "root_ids": root_ids,
            "metadata": metadata,
        }
        
        path = self._graph_path(graph_id)
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            raise PersistenceError("save_graph", e)
    
    async def load_graph(
        self,
        graph_id: str,
    ) -> tuple[dict[str, Thought], list[Edge], list[str], dict[str, Any]] | None:
        path = self._graph_path(graph_id)
        if not path.exists():
            return None
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            thoughts = {tid: Thought.from_dict(td) for tid, td in data["thoughts"].items()}
            edges = [Edge.from_dict(ed) for ed in data["edges"]]
            return thoughts, edges, data["root_ids"], data["metadata"]
        except Exception as e:
            raise PersistenceError("load_graph", e)
    
    async def save_checkpoint(
        self,
        graph_id: str,
        checkpoint_id: str,
        thoughts: dict[str, Thought],
        edges: list[Edge],
        root_ids: list[str],
        search_state: dict[str, Any],
    ) -> None:
        checkpoint_dir = self._checkpoint_dir(graph_id)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            "thoughts": {tid: t.to_dict() for tid, t in thoughts.items()},
            "edges": [e.to_dict() for e in edges],
            "root_ids": root_ids,
            "search_state": search_state,
        }
        
        path = self._checkpoint_path(graph_id, checkpoint_id)
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            raise PersistenceError("save_checkpoint", e)
    
    async def load_checkpoint(
        self,
        graph_id: str,
        checkpoint_id: str,
    ) -> tuple[dict[str, Thought], list[Edge], list[str], dict[str, Any]] | None:
        path = self._checkpoint_path(graph_id, checkpoint_id)
        if not path.exists():
            return None
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            thoughts = {tid: Thought.from_dict(td) for tid, td in data["thoughts"].items()}
            edges = [Edge.from_dict(ed) for ed in data["edges"]]
            return thoughts, edges, data["root_ids"], data["search_state"]
        except Exception as e:
            raise PersistenceError("load_checkpoint", e)
    
    async def delete_graph(self, graph_id: str) -> bool:
        path = self._graph_path(graph_id)
        if path.exists():
            path.unlink()
            # Also delete checkpoints
            checkpoint_dir = self._checkpoint_dir(graph_id)
            if checkpoint_dir.exists():
                import shutil
                shutil.rmtree(checkpoint_dir)
            return True
        return False


__all__ = [
    "InMemoryPersistence",
    "FilePersistence",
]
