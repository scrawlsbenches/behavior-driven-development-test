"""
Services package - Pluggable services for governance, resources, knowledge, etc.

This package provides:
1. Protocol definitions (interfaces) in protocols.py
2. Null and simple implementations in implementations.py
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
        NullKnowledgeService,  # Skip knowledge for now
    )
    
    orchestrator = Orchestrator(
        governance=SimpleGovernanceService(),
        resources=SimpleResourceService(),
        knowledge=NullKnowledgeService(),
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
    # Null implementations
    NullGovernanceService,
    NullProjectManagementService,
    NullResourceService,
    NullKnowledgeService,
    NullQuestionService,
    NullCommunicationService,

    # InMemory implementations (for testing)
    InMemoryGovernanceService,
    InMemoryProjectManagementService,
    InMemoryResourceService,
    InMemoryKnowledgeService,
    InMemoryQuestionService,
    InMemoryCommunicationService,

    # Simple implementations
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
    
    # Null implementations
    "NullGovernanceService",
    "NullProjectManagementService",
    "NullResourceService",
    "NullKnowledgeService",
    "NullQuestionService",
    "NullCommunicationService",

    # InMemory implementations (for testing)
    "InMemoryGovernanceService",
    "InMemoryProjectManagementService",
    "InMemoryResourceService",
    "InMemoryKnowledgeService",
    "InMemoryQuestionService",
    "InMemoryCommunicationService",

    # Simple implementations
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
