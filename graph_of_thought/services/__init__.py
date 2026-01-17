"""
Services package - Pluggable services for governance, resources, knowledge, etc.

This package provides:
1. Protocol definitions (interfaces) in protocols.py
2. InMemory (testable) and simple implementations in implementations.py
3. The Orchestrator in orchestrator.py

Quick Start:
    # Use orchestrator with simple implementations
    from graph_of_thought.services import Orchestrator

    orchestrator = Orchestrator.create_simple()

    # Or build custom configuration
    from graph_of_thought.services import (
        Orchestrator,
        SimpleGovernanceService,
        SimpleResourceService,
        InMemoryKnowledgeService,  # Testable in-memory storage
    )

    orchestrator = Orchestrator(
        governance=SimpleGovernanceService(),
        resources=SimpleResourceService(),
        knowledge=InMemoryKnowledgeService(),
    )

Integration with CollaborativeProject:
    from graph_of_thought import CollaborativeProject
    from graph_of_thought.services import Orchestrator

    orchestrator = Orchestrator.create_simple()
    project = CollaborativeProject("my_project", orchestrator=orchestrator)
"""

from __future__ import annotations

# Protocols
from .protocols import (
    # Enums
    ApprovalStatus,
    Priority,
    ResourceType,
    
    # Data classes
    ResourceBudget,
    Decision,
    KnowledgeEntry,
    QuestionTicket,
    HandoffPackage,
    
    # Service protocols
    GovernanceService,
    ProjectManagementService,
    ResourceService,
    KnowledgeService,
    QuestionService,
    CommunicationService,
    
    # Registry
    ServiceRegistry,
)

# Implementations
from .implementations import (
    # InMemory implementations (testable defaults)
    InMemoryGovernanceService,
    InMemoryProjectManagementService,
    InMemoryResourceService,
    InMemoryKnowledgeService,
    InMemoryQuestionService,
    InMemoryCommunicationService,

    # Simple implementations (with business logic)
    SimpleGovernanceService,
    SimpleResourceService,
    SimpleKnowledgeService,
    SimpleQuestionService,
    SimpleCommunicationService,
)

# Orchestrator
from .orchestrator import (
    Orchestrator,
    OrchestratorEvent,
    OrchestratorResponse,
)

__all__ = [
    # Enums
    "ApprovalStatus",
    "Priority", 
    "ResourceType",
    
    # Data classes
    "ResourceBudget",
    "Decision",
    "KnowledgeEntry",
    "QuestionTicket",
    "HandoffPackage",
    
    # Protocols
    "GovernanceService",
    "ProjectManagementService",
    "ResourceService",
    "KnowledgeService",
    "QuestionService",
    "CommunicationService",
    "ServiceRegistry",
    
    # InMemory implementations (testable defaults)
    "InMemoryGovernanceService",
    "InMemoryProjectManagementService",
    "InMemoryResourceService",
    "InMemoryKnowledgeService",
    "InMemoryQuestionService",
    "InMemoryCommunicationService",

    # Simple implementations (with business logic)
    "SimpleGovernanceService",
    "SimpleResourceService",
    "SimpleKnowledgeService",
    "SimpleQuestionService",
    "SimpleCommunicationService",
    
    # Orchestrator
    "Orchestrator",
    "OrchestratorEvent",
    "OrchestratorResponse",
]
