"""
Service Implementations - InMemory and simple implementations for all services.

These provide working defaults that can be replaced with production implementations.

ARCHITECTURE NOTE:
    InMemory implementations provide testable defaults with configurable behavior.
    Simple implementations use in-memory storage and basic business logic.
    Production implementations would connect to real systems (databases, APIs, etc.)

    Upgrade path:
    1. Start with InMemory (testable, configurable defaults)
    2. Move to Simple (features work, in-memory storage)
    3. Move to Production (persistent, integrated)
"""

# Governance implementations
from .governance import (
    InMemoryGovernanceService,
    SimpleGovernanceService,
)

# Project management implementations
from .project import (
    InMemoryProjectManagementService,
)

# Resource implementations
from .resources import (
    InMemoryResourceService,
    SimpleResourceService,
)

# Knowledge implementations
from .knowledge import (
    InMemoryKnowledgeService,
    SimpleKnowledgeService,
)

# Question implementations
from .questions import (
    InMemoryQuestionService,
    SimpleQuestionService,
)

# Communication implementations
from .communication import (
    IntentRecord,
    FeedbackRecord,
    InMemoryCommunicationService,
    SimpleCommunicationService,
)


__all__ = [
    # Governance
    "InMemoryGovernanceService",
    "SimpleGovernanceService",
    # Project Management
    "InMemoryProjectManagementService",
    # Resources
    "InMemoryResourceService",
    "SimpleResourceService",
    # Knowledge
    "InMemoryKnowledgeService",
    "SimpleKnowledgeService",
    # Questions
    "InMemoryQuestionService",
    "SimpleQuestionService",
    # Communication
    "IntentRecord",
    "FeedbackRecord",
    "InMemoryCommunicationService",
    "SimpleCommunicationService",
]
