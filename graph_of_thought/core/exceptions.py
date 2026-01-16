from __future__ import annotations
"""
Custom exceptions for Graph of Thought.
"""


class GraphError(Exception):
    """Base exception for Graph of Thought errors."""
    pass


class NodeNotFoundError(GraphError):
    """Raised when a thought ID is not found in the graph."""
    
    def __init__(self, thought_id: str):
        self.thought_id = thought_id
        super().__init__(f"Thought '{thought_id}' not found in graph")


class CycleDetectedError(GraphError):
    """Raised when an operation would create an invalid cycle."""
    
    def __init__(self, source_id: str, target_id: str):
        self.source_id = source_id
        self.target_id = target_id
        super().__init__(f"Edge {source_id} -> {target_id} would create a cycle")


class ResourceExhaustedError(GraphError):
    """Raised when a resource limit is exceeded."""
    
    def __init__(self, resource_type: str, limit: int | float | None = None):
        self.resource_type = resource_type
        self.limit = limit
        msg = f"Resource '{resource_type}' exhausted"
        if limit is not None:
            msg += f" (limit: {limit})"
        super().__init__(msg)


class TimeoutError(GraphError):
    """Raised when an operation times out."""
    
    def __init__(self, operation: str, timeout_seconds: float):
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Operation '{operation}' timed out after {timeout_seconds}s")


class GenerationError(GraphError):
    """Raised when thought generation fails."""
    
    def __init__(self, message: str, cause: Exception | None = None):
        self.cause = cause
        super().__init__(message)


class EvaluationError(GraphError):
    """Raised when thought evaluation fails."""
    
    def __init__(self, message: str, cause: Exception | None = None):
        self.cause = cause
        super().__init__(message)


class PersistenceError(GraphError):
    """Raised when persistence operations fail."""
    
    def __init__(self, operation: str, cause: Exception | None = None):
        self.operation = operation
        self.cause = cause
        super().__init__(f"Persistence operation '{operation}' failed: {cause}")


class ConfigurationError(GraphError):
    """Raised when configuration is invalid."""
    pass
