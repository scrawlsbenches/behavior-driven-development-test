#!/usr/bin/env python3
"""
Example: Using CollaborativeProject with full orchestrator integration.

This demonstrates:
- Governance policies and approvals
- Resource budgeting and tracking  
- Knowledge capture and retrieval
- Question routing
- Cross-service coordination

Run with: python3 -m graph_of_thought.examples.orchestrated_usage
"""

from __future__ import annotations
import os
import shutil
from datetime import datetime

from graph_of_thought import (
    CollaborativeProject,
    QuestionPriority,
    ChunkStatus,
)
from graph_of_thought.services import (
    Orchestrator,
    SimpleGovernanceService,
    SimpleResourceService,
    SimpleKnowledgeService,
    SimpleQuestionService,
    SimpleCommunicationService,
    ApprovalStatus,
    ResourceType,
    Priority,
    KnowledgeEntry,
)


def main():
    """Demonstrate orchestrated project workflow."""
    
    # Clean up from previous runs
    project_path = "./projects/orchestrated_example"
    knowledge_path = "./knowledge"
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
    if os.path.exists(knowledge_path):
        shutil.rmtree(knowledge_path)
    
    print("=" * 70)
    print("ORCHESTRATED COLLABORATIVE PROJECT EXAMPLE")
    print("=" * 70)
    
    # =========================================================================
    # Set up orchestrator with configured services
    # =========================================================================
    
    print("\n--- Setting up Orchestrator ---")
    
    # Governance with custom policies
    governance = SimpleGovernanceService()
    governance.add_policy("deploy_production", ApprovalStatus.NEEDS_REVIEW)
    governance.add_policy("delete_data", ApprovalStatus.DENIED)
    print("  Governance: Added policies for deploy and delete")
    
    # Resources with budgets
    resources = SimpleResourceService()
    print("  Resources: Service initialized")
    
    # Knowledge for cross-project learning
    knowledge = SimpleKnowledgeService(persist_path=knowledge_path)
    print("  Knowledge: Service initialized with persistence")
    
    # Pre-populate knowledge with a pattern
    knowledge.store(KnowledgeEntry(
        id="pattern-auth-jwt",
        content="Pattern: JWT Authentication\n\nFor REST APIs, use JWT tokens with:\n"
               "- Short expiry (15 min) for access tokens\n"
               "- Longer expiry (7 days) for refresh tokens\n"
               "- Store refresh tokens in httpOnly cookies",
        entry_type="pattern",
        tags=["auth", "jwt", "security", "api"],
    ))
    print("  Knowledge: Pre-populated with JWT auth pattern")
    
    # Questions with knowledge-backed routing
    questions = SimpleQuestionService(knowledge_service=knowledge)
    print("  Questions: Service initialized with knowledge integration")
    
    # Communication for handoffs
    communication = SimpleCommunicationService(
        knowledge_service=knowledge,
        question_service=questions,
    )
    print("  Communication: Service initialized")
    
    # Create orchestrator
    orchestrator = Orchestrator(
        governance=governance,
        resources=resources,
        knowledge=knowledge,
        questions=questions,
        communication=communication,
    )
    print("  Orchestrator: All services connected")
    
    # =========================================================================
    # Set up project with orchestrator
    # =========================================================================
    
    print("\n--- Creating Project with Orchestrator ---")
    
    project = CollaborativeProject(
        "orchestrated_example",
        orchestrator=orchestrator,
    )
    
    # Set token budget for the project
    budget = orchestrator.set_token_budget("orchestrated_example", 50000)
    print(f"  Token budget: {budget.allocated} tokens allocated")
    
    # Add initial request
    project.add_request(
        "Build a REST API for user management with authentication"
    )
    print("  Request: Added")
    
    # =========================================================================
    # Ask questions (orchestrator routes them)
    # =========================================================================
    
    print("\n--- Asking Questions (orchestrator routes) ---")
    
    q1 = project.ask_question(
        "Should we use JWT or session-based authentication?",
        priority=QuestionPriority.BLOCKING,
        context="Affects security implementation and statelessness",
    )
    
    # Check how orchestrator routed the question
    pending = orchestrator.get_pending_questions()
    if pending:
        q = pending[0]
        print(f"  Question routed to: {q.routed_to}")
        print(f"  Routing reason: {q.routing_reason}")
    
    # Answer the question
    project.answer_question(q1.id, "Use JWT with refresh tokens")
    
    # Check if knowledge has anything relevant
    results = knowledge.retrieve("JWT authentication", limit=1)
    if results:
        print(f"\n  Knowledge base suggestion found: {results[0].id}")
        print(f"  Content preview: {results[0].content[:100]}...")
    
    # =========================================================================
    # Plan and work on chunks
    # =========================================================================
    
    print("\n--- Planning Chunks ---")
    
    chunk1 = project.plan_chunk(
        name="User Data Model",
        description="Define User entity with SQLAlchemy, including auth fields",
        estimated_hours=2.0,
        acceptance_criteria=[
            "User model with email, password_hash, created_at",
            "Migration script generated",
            "Basic tests pass",
        ],
    )
    print(f"  Chunk planned: {chunk1.metadata['name']}")
    
    chunk2 = project.plan_chunk(
        name="JWT Auth Implementation",
        description="Implement JWT token generation and validation",
        estimated_hours=3.0,
        depends_on=[chunk1.id],
        acceptance_criteria=[
            "Token generation works",
            "Token validation works",
            "Refresh token flow works",
        ],
    )
    print(f"  Chunk planned: {chunk2.metadata['name']}")
    
    # =========================================================================
    # Start work (orchestrator checks resources)
    # =========================================================================
    
    print("\n--- Starting Chunk (orchestrator checks resources) ---")
    
    try:
        project.start_chunk(chunk1.id, goal="Create User model with all auth fields")
        print(f"  Chunk started: {chunk1.metadata['name']}")
        
        # Check if any patterns were suggested
        chunk1_node = project._nodes[chunk1.id]
        if "suggested_patterns" in chunk1_node.metadata:
            print(f"  Suggested patterns: {chunk1_node.metadata['suggested_patterns']}")
        
    except ValueError as e:
        print(f"  Could not start: {e}")
    
    # Simulate some work with token consumption
    resources.consume(
        ResourceType.TOKENS,
        "project",
        "orchestrated_example",
        5000,
        "User model generation",
    )
    
    # =========================================================================
    # Complete chunk with discoveries
    # =========================================================================
    
    print("\n--- Completing Chunk with Discoveries ---")
    
    project.complete_chunk(
        chunk1.id,
        actual_hours=2.5,
        produced_files=["models/user.py", "migrations/001_user.py"],
        discoveries=[
            "SQLAlchemy 2.0 requires explicit async session handling",
            "Password hashing should use bcrypt with cost factor 12",
        ],
        tokens_used=5000,
    )
    print(f"  Chunk completed: {chunk1.metadata['name']}")
    
    # Check knowledge captured
    knowledge_entries = knowledge.retrieve("password hashing bcrypt")
    if knowledge_entries:
        print(f"  Discovery captured in knowledge base: {knowledge_entries[0].id}")
    
    # =========================================================================
    # Check resource consumption
    # =========================================================================
    
    print("\n--- Resource Report ---")
    
    report = resources.get_consumption_report("project", "orchestrated_example")
    print(f"  Total events: {report['total_events']}")
    print(f"  By resource: {report['by_resource']}")
    
    budget = resources.get_budget(ResourceType.TOKENS, "project", "orchestrated_example")
    if budget:
        print(f"  Token budget: {budget.consumed}/{budget.allocated} ({budget.percent_used:.1f}% used)")
    
    # =========================================================================
    # Check orchestrator metrics
    # =========================================================================
    
    print("\n--- Orchestrator Metrics ---")
    
    metrics = orchestrator.get_metrics()
    for key, value in sorted(metrics.items()):
        print(f"  {key}: {value}")
    
    # =========================================================================
    # Generate resumption context
    # =========================================================================
    
    print("\n--- Resumption Context ---")
    print("(This is what a new Claude context would see)")
    print("-" * 50)
    
    context = project.get_resumption_context()
    # Print first 1000 chars
    print(context[:1000])
    if len(context) > 1000:
        print(f"... ({len(context) - 1000} more characters)")
    
    # =========================================================================
    # Demonstrate governance (try a blocked action)
    # =========================================================================
    
    print("\n--- Governance Demo ---")
    
    status, reason = governance.check_approval(
        "delete_data",
        {"project_id": "orchestrated_example"}
    )
    print(f"  delete_data: {status.name} - {reason}")
    
    status, reason = governance.check_approval(
        "deploy_production",
        {"project_id": "orchestrated_example"}
    )
    print(f"  deploy_production: {status.name} - {reason}")
    
    # =========================================================================
    # Check audit log
    # =========================================================================
    
    print("\n--- Audit Log (last 5 entries) ---")
    
    audit = governance.get_audit_log(limit=5)
    for entry in audit[-5:]:
        action = entry["action"]
        result = entry["result"][:50]
        print(f"  {action}: {result}")
    
    # =========================================================================
    # Cleanup
    # =========================================================================
    
    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)
    
    # Clean up
    shutil.rmtree(project_path)
    shutil.rmtree(knowledge_path)


if __name__ == "__main__":
    main()
