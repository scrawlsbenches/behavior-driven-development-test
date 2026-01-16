#!/usr/bin/env python3
"""
Example: Using CollaborativeProject for human-AI software development.

This demonstrates the "questions first" pattern where the AI asks clarifying
questions before diving into implementation, and work is broken into
manageable chunks that survive context loss.
"""

from __future__ import annotations
import os
import shutil
from graph_of_thought import (
    CollaborativeProject,
    QuestionPriority,
    ChunkStatus,
)


def simulate_session():
    """Simulate a collaborative development session."""
    
    # Clean up any existing project
    if os.path.exists("./projects/cms_example"):
        shutil.rmtree("./projects/cms_example")
    
    print("=" * 60)
    print("SESSION 1: Initial Request and Planning")
    print("=" * 60)
    
    # Start a new project
    project = CollaborativeProject("cms_example")
    
    # User makes initial request
    project.add_request(
        "Build me a content management system for my company's documentation"
    )
    
    # AI asks clarifying questions (this is the key pattern)
    q1 = project.ask_question(
        "Will this be multi-tenant (multiple companies) or single-tenant (just your company)?",
        priority=QuestionPriority.BLOCKING,
        context="This fundamentally affects the data model and auth architecture",
        suggested_default="Single-tenant for simplicity",
    )
    
    q2 = project.ask_question(
        "What's the expected content structure?",
        priority=QuestionPriority.BLOCKING,
        context="Need to know if it's flat pages, hierarchical docs, or wiki-style",
    )
    
    q3 = project.ask_question(
        "What authentication method do you need?",
        priority=QuestionPriority.IMPORTANT,
        context="Affects security implementation",
        suggested_default="Email/password with optional SSO later",
    )
    
    q4 = project.ask_question(
        "Do you need version history for documents?",
        priority=QuestionPriority.NICE_TO_HAVE,
        suggested_default="Yes, basic versioning",
    )
    
    # Check project status
    print("\n--- Project Status After Questions ---")
    status = project.get_project_status()
    print(f"Blocking questions: {status['questions']['blocking_unanswered']}")
    
    can_proceed, reason = project.can_proceed()
    print(f"Can proceed: {can_proceed}")
    print(f"Reason: {reason}")
    
    # User answers questions
    print("\n--- User Answers Questions ---")
    project.answer_question(q1.id, "Single-tenant, just our company for now")
    project.answer_question(q2.id, "Hierarchical docs, like a tree with sections and pages")
    project.answer_question(q3.id, "Start with email/password, we'll add SSO later")
    project.answer_question(q4.id, "Yes, need to see who changed what and when")
    
    # Now AI can plan chunks
    print("\n--- Planning Work Chunks ---")
    
    chunk1 = project.plan_chunk(
        name="Data Models",
        description="Define core entities: User, Document, Section, Version",
        estimated_hours=2.0,
        depends_on=[],
        acceptance_criteria=[
            "All models defined with SQLAlchemy",
            "Migrations created",
            "Basic tests pass",
        ],
        not_in_scope=[
            "Auth logic (separate chunk)",
            "API endpoints (separate chunk)",
        ],
    )
    
    chunk2 = project.plan_chunk(
        name="Authentication",
        description="Implement email/password auth with JWT tokens",
        estimated_hours=3.0,
        depends_on=[chunk1.id],
        acceptance_criteria=[
            "Register endpoint works",
            "Login returns valid JWT",
            "Protected routes require auth",
        ],
    )
    
    chunk3 = project.plan_chunk(
        name="Document CRUD API",
        description="REST endpoints for creating, reading, updating, deleting documents",
        estimated_hours=4.0,
        depends_on=[chunk1.id, chunk2.id],
        acceptance_criteria=[
            "All CRUD endpoints implemented",
            "Proper auth on all endpoints",
            "Version history recorded on updates",
            "API tests pass",
        ],
    )
    
    # Check status again
    print("\n--- Project Status After Planning ---")
    status = project.get_project_status()
    print(f"Chunks: {status['chunks']}")
    print(f"Estimated hours remaining: {status['estimated_hours_remaining']}")
    
    can_proceed, reason = project.can_proceed()
    print(f"\nCan proceed: {can_proceed}")
    print(f"Reason: {reason}")
    
    # Start first chunk
    print("\n--- Starting Work on Data Models ---")
    project.start_chunk(chunk1.id, goal="Define all SQLAlchemy models")
    project.add_session_note("Starting with User model first")
    project.add_session_note("Decided to use UUID for all primary keys")
    
    # Simulate context loss and recovery
    print("\n" + "=" * 60)
    print("SESSION 2: Resuming After Context Loss")
    print("=" * 60)
    
    # Fresh project instance (simulates new Claude context)
    project2 = CollaborativeProject("cms_example")  # Loads from disk
    
    print("\n--- Resumption Context (what new Claude context sees) ---")
    print(project2.get_resumption_context())
    
    # Complete the chunk
    print("\n--- Completing Data Models Chunk ---")
    project2.complete_chunk(
        chunk1.id,
        actual_hours=2.5,
        produced_files=[
            "models/user.py",
            "models/document.py",
            "models/section.py",
            "migrations/001_initial.py",
        ],
        discoveries=[
            "SQLite doesn't support array types, need JSON field for tags",
            "Document versioning needs careful foreign key design",
        ],
        notes="Took slightly longer due to versioning complexity",
    )
    
    # Check what's next
    print("\n--- What's Ready Now ---")
    ready = project2.get_ready_chunks()
    for chunk in ready:
        print(f"  - {chunk.metadata['name']} ({chunk.estimated_hours}h)")
    
    # Export full project
    print("\n" + "=" * 60)
    print("PROJECT MARKDOWN EXPORT")
    print("=" * 60)
    print(project2.to_markdown())
    
    # Cleanup
    shutil.rmtree("./projects/cms_example")


if __name__ == "__main__":
    simulate_session()
