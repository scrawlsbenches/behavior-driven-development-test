"""
Configuration management for Graph of Thought.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import os
import json


@dataclass
class ResourceLimits:
    """Resource limits for graph operations."""
    max_thoughts: int = 10_000
    max_depth: int = 20
    max_tokens: int | None = None
    timeout_seconds: float | None = None
    max_concurrent_expansions: int = 10
    checkpoint_interval: int | None = 100  # Checkpoint every N expansions


@dataclass
class SearchDefaults:
    """Default search parameters."""
    beam_width: int = 3
    max_expansions: int = 100
    score_threshold: float = 0.0  # Minimum score to explore


@dataclass
class GraphConfig:
    """
    Complete configuration for Graph of Thought.
    
    Can be loaded from environment variables, JSON files, or constructed directly.
    """
    # Core settings
    allow_cycles: bool = False
    auto_checkpoint: bool = True
    
    # Resource limits
    limits: ResourceLimits = field(default_factory=ResourceLimits)
    
    # Search defaults
    search: SearchDefaults = field(default_factory=SearchDefaults)
    
    # Feature flags
    enable_metrics: bool = True
    enable_tracing: bool = False
    enable_persistence: bool = False
    
    # Custom metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls, prefix: str = "GOT_") -> GraphConfig:
        """
        Load configuration from environment variables.
        
        Environment variables:
            GOT_ALLOW_CYCLES: bool
            GOT_MAX_THOUGHTS: int
            GOT_MAX_DEPTH: int
            GOT_MAX_TOKENS: int
            GOT_TIMEOUT_SECONDS: float
            GOT_BEAM_WIDTH: int
            GOT_ENABLE_METRICS: bool
            GOT_ENABLE_TRACING: bool
            GOT_ENABLE_PERSISTENCE: bool
        """
        def get_bool(key: str, default: bool) -> bool:
            val = os.environ.get(f"{prefix}{key}", "").lower()
            if val in ("true", "1", "yes"):
                return True
            elif val in ("false", "0", "no"):
                return False
            return default
        
        def get_int(key: str, default: int | None) -> int | None:
            val = os.environ.get(f"{prefix}{key}")
            if val is not None:
                try:
                    return int(val)
                except ValueError:
                    pass
            return default
        
        def get_float(key: str, default: float | None) -> float | None:
            val = os.environ.get(f"{prefix}{key}")
            if val is not None:
                try:
                    return float(val)
                except ValueError:
                    pass
            return default
        
        limits = ResourceLimits(
            max_thoughts=get_int("MAX_THOUGHTS", 10_000) or 10_000,
            max_depth=get_int("MAX_DEPTH", 20) or 20,
            max_tokens=get_int("MAX_TOKENS", None),
            timeout_seconds=get_float("TIMEOUT_SECONDS", None),
            max_concurrent_expansions=get_int("MAX_CONCURRENT_EXPANSIONS", 10) or 10,
            checkpoint_interval=get_int("CHECKPOINT_INTERVAL", 100),
        )
        
        search = SearchDefaults(
            beam_width=get_int("BEAM_WIDTH", 3) or 3,
            max_expansions=get_int("MAX_EXPANSIONS", 100) or 100,
            score_threshold=get_float("SCORE_THRESHOLD", 0.0) or 0.0,
        )
        
        return cls(
            allow_cycles=get_bool("ALLOW_CYCLES", False),
            auto_checkpoint=get_bool("AUTO_CHECKPOINT", True),
            limits=limits,
            search=search,
            enable_metrics=get_bool("ENABLE_METRICS", True),
            enable_tracing=get_bool("ENABLE_TRACING", False),
            enable_persistence=get_bool("ENABLE_PERSISTENCE", False),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> GraphConfig:
        """Load configuration from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def from_file(cls, path: str) -> GraphConfig:
        """Load configuration from JSON file."""
        with open(path, "r") as f:
            return cls.from_json(f.read())
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphConfig:
        """Load configuration from dictionary."""
        limits_data = data.get("limits", {})
        limits = ResourceLimits(
            max_thoughts=limits_data.get("max_thoughts", 10_000),
            max_depth=limits_data.get("max_depth", 20),
            max_tokens=limits_data.get("max_tokens"),
            timeout_seconds=limits_data.get("timeout_seconds"),
            max_concurrent_expansions=limits_data.get("max_concurrent_expansions", 10),
            checkpoint_interval=limits_data.get("checkpoint_interval", 100),
        )
        
        search_data = data.get("search", {})
        search = SearchDefaults(
            beam_width=search_data.get("beam_width", 3),
            max_expansions=search_data.get("max_expansions", 100),
            score_threshold=search_data.get("score_threshold", 0.0),
        )
        
        return cls(
            allow_cycles=data.get("allow_cycles", False),
            auto_checkpoint=data.get("auto_checkpoint", True),
            limits=limits,
            search=search,
            enable_metrics=data.get("enable_metrics", True),
            enable_tracing=data.get("enable_tracing", False),
            enable_persistence=data.get("enable_persistence", False),
            metadata=data.get("metadata", {}),
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "allow_cycles": self.allow_cycles,
            "auto_checkpoint": self.auto_checkpoint,
            "limits": {
                "max_thoughts": self.limits.max_thoughts,
                "max_depth": self.limits.max_depth,
                "max_tokens": self.limits.max_tokens,
                "timeout_seconds": self.limits.timeout_seconds,
                "max_concurrent_expansions": self.limits.max_concurrent_expansions,
                "checkpoint_interval": self.limits.checkpoint_interval,
            },
            "search": {
                "beam_width": self.search.beam_width,
                "max_expansions": self.search.max_expansions,
                "score_threshold": self.search.score_threshold,
            },
            "enable_metrics": self.enable_metrics,
            "enable_tracing": self.enable_tracing,
            "enable_persistence": self.enable_persistence,
            "metadata": self.metadata,
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert configuration to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    def validate(self) -> list[str]:
        """
        Validate configuration and return list of issues.
        
        Returns empty list if valid.
        """
        issues = []
        
        if self.limits.max_thoughts < 1:
            issues.append("max_thoughts must be >= 1")
        
        if self.limits.max_depth < 1:
            issues.append("max_depth must be >= 1")
        
        if self.limits.max_tokens is not None and self.limits.max_tokens < 1:
            issues.append("max_tokens must be >= 1 or None")
        
        if self.limits.timeout_seconds is not None and self.limits.timeout_seconds <= 0:
            issues.append("timeout_seconds must be > 0 or None")
        
        if self.search.beam_width < 1:
            issues.append("beam_width must be >= 1")
        
        if self.search.max_expansions < 1:
            issues.append("max_expansions must be >= 1")
        
        return issues
