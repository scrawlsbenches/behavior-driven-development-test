"""
Dogfood Demo: Using Graph of Thought to Build Graph of Thought

This demo models our actual development workflow - a human and AI collaborating
on building enterprise software using BDD practices.

It demonstrates:
1. Project setup with real work items from WIP.md
2. Knowledge capture from CLAUDE.md patterns
3. Session management with discoveries
4. Handoff generation for context preservation
5. Graph-based reasoning for technical decisions
"""

import asyncio
from datetime import datetime
from graph_of_thought import GraphOfThought, CollaborativeProject
from graph_of_thought.collaborative import QuestionPriority
from graph_of_thought.core import SearchConfig
from graph_of_thought.services import (
    Orchestrator,
    InMemoryKnowledgeService,
    KnowledgeEntry,
    Decision,
)


def create_got_project() -> CollaborativeProject:
    """Create a project representing our Graph of Thought development."""
    import tempfile
    import shutil

    # Use temp directory to ensure fresh project each run
    temp_dir = tempfile.mkdtemp(prefix="got_demo_")

    project = CollaborativeProject(
        name="graph-of-thought-enterprise",
        base_path=temp_dir,
        auto_save=False  # Don't save for demo
    )

    # The original request that started this project
    project.add_request("""
    Build an enterprise AI-assisted reasoning and project management platform
    with six core business capabilities:
    - AI Reasoning: Graph-based thought exploration
    - Project Management: Work chunks, session handoffs
    - Cost Management: Token budgets, consumption tracking
    - Governance & Compliance: Approval workflows, audit logging
    - Knowledge Management: Decisions, learnings, question routing
    - Platform: Observability, persistence, configuration

    Use BDD with behave framework. Follow DDD architecture principles.
    Target personas: Data Scientists, Engineering Managers, Security Officers.
    """)

    return project


def add_knowledge_from_claude_md(knowledge: InMemoryKnowledgeService):
    """Populate knowledge base with patterns from CLAUDE.md."""

    # BDD Patterns
    knowledge.store(KnowledgeEntry(
        id="pattern-bdd-personas",
        entry_type="pattern",
        content="""Persona-Driven Scenarios

Pattern: Write scenarios from specific persona perspectives.

Good:
  Scenario: Data scientist tracks token usage against sprint budget
    Given Jordan is working on project "Customer Analysis"
    And the sprint budget is 50,000 tokens
    When Jordan's analysis consumes 2,500 tokens
    Then Jordan should see 47,500 tokens remaining

Bad:
  Scenario: Track consumption
    Given a user and a budget of 50000
    When 2500 consumed
    Then remaining is 47500

Why: Personas provide business context and make scenarios readable.
        """,
        tags=["bdd", "scenarios", "personas"],
        source_project="graph-of-thought"
    ))

    knowledge.store(KnowledgeEntry(
        id="pattern-ddd-protocol-injection",
        entry_type="pattern",
        content="""Protocol-Based Dependency Injection

Pattern: Define protocols in protocols.py, implementations in implementations.py.

Rules:
- Business logic imports protocols, not implementations
- Services injected via constructor, not instantiated directly
- No global service instances

Example:
    # protocols.py
    class FileSystem(Protocol):
        def write(self, path: str, content: bytes) -> None: ...

    # implementations.py
    class InMemoryFileSystem:
        def write(self, path: str, content: bytes) -> None:
            self.files[path] = content

    # Usage - inject the dependency
    persistence = FilePersistence("/data", filesystem=InMemoryFileSystem())

Why: Enables testing with mocks, maintains clean architecture boundaries.
        """,
        tags=["architecture", "ddd", "testing"],
        source_project="graph-of-thought"
    ))

    knowledge.store(KnowledgeEntry(
        id="pattern-session-startup",
        entry_type="pattern",
        content="""Session Startup Checklist

Pattern: Run these commands at the start of every session.

1. ./scripts/setup-dev.sh  # Install deps, configure hooks
2. git status              # Check git state
3. cat docs/WIP.md         # Read current status
4. behave --dry-run 2>&1 | tail -5  # Verify test counts
5. Compare WIP.md vs actual         # Detect drift

Why: Documentation can drift from actual state between sessions.
Always verify before assuming WIP.md is accurate.
        """,
        tags=["workflow", "session", "verification"],
        source_project="graph-of-thought"
    ))

    # Add a decision record
    knowledge.record_decision(Decision(
        id="decision-inmemory-fs",
        title="Use InMemoryFileSystem for Persistence Testing",
        context="FilePersistence was doing direct file I/O, making tests slow and non-deterministic. Step definitions used mock services that bypassed the actual persistence code.",
        options=[
            "Keep using direct file I/O with temp directories",
            "Create FileSystem protocol with InMemoryFileSystem for testing",
            "Use mocking library to patch file operations",
        ],
        chosen="Create FileSystem protocol with InMemoryFileSystem for testing",
        rationale="Clean dependency injection follows our DDD principles. InMemoryFileSystem can track operations for assertions and simulate failures.",
        consequences=[
            "Tests are faster (no disk I/O)",
            "Can simulate failures (disk full, corruption)",
            "Can assert on exact file operations",
            "Backwards compatible (defaults to RealFileSystem)",
        ]
    ))


def add_work_chunks(project: CollaborativeProject):
    """Add work chunks based on WIP.md status."""

    # Completed work
    chunk1 = project.plan_chunk(
        name="FileSystem Protocol & InMemoryFileSystem",
        description="Add dependency injection for file operations in persistence layer",
        estimated_hours=2.0,
        acceptance_criteria=[
            "FileSystem protocol defined in protocols.py",
            "InMemoryFileSystem implementation with operation tracking",
            "RealFileSystem implementation for production",
            "FilePersistence accepts optional filesystem parameter",
            "All existing tests pass",
        ]
    )
    project.start_chunk(chunk1.id, goal="Implement FileSystem abstraction")
    project.complete_chunk(chunk1.id, notes="Implemented FileSystem protocol with DI")

    chunk2 = project.plan_chunk(
        name="Data Persistence Step Definitions",
        description="Implement step definitions for data_persistence.feature MVP-P0/P1 scenarios",
        estimated_hours=3.0,
        acceptance_criteria=[
            "Auto-save scenarios pass",
            "Recovery scenarios pass",
            "Storage backend scenarios pass",
            "Backup/recovery scenarios pass",
            "Checkpoint scenarios pass",
        ]
    )
    project.start_chunk(chunk2.id, goal="Implement persistence steps")
    project.complete_chunk(chunk2.id, notes="22 data persistence scenarios now pass")

    # Ready to start
    project.plan_chunk(
        name="Decisions and Learnings Step Definitions",
        description="Implement step definitions for decisions_and_learnings.feature",
        estimated_hours=3.0,
        acceptance_criteria=[
            "Decision record creation scenarios pass",
            "Learning capture scenarios pass",
            "Decision search scenarios pass",
        ]
    )

    project.plan_chunk(
        name="Question Routing Step Definitions",
        description="Implement step definitions for question_routing.feature",
        estimated_hours=2.5,
        acceptance_criteria=[
            "Question creation scenarios pass",
            "Routing to experts scenarios pass",
            "Knowledge base suggestion scenarios pass",
        ]
    )

    # Current work
    chunk_current = project.plan_chunk(
        name="Dogfood Demo - Real Workflow",
        description="Create demo that models our actual development workflow",
        estimated_hours=2.0,
        acceptance_criteria=[
            "Demo runs successfully",
            "Shows project/session management",
            "Captures knowledge from CLAUDE.md",
            "Generates useful handoff context",
        ]
    )
    project.start_chunk(chunk_current.id, goal="Build demo showing our workflow")


def add_session_questions(project: CollaborativeProject):
    """Add questions that might arise in a development session."""

    # A blocking question
    project.ask_question(
        question="Should we persist session state automatically or require explicit save?",
        context="For dogfooding, we need state to survive between conversations",
        priority=QuestionPriority.BLOCKING
    )

    # Answered questions
    q1 = project.ask_question(
        question="Should InMemoryFileSystem be in core/defaults.py or a separate file?",
        context="Need to decide where filesystem implementations live",
        priority=QuestionPriority.IMPORTANT
    )
    project.answer_question(q1.id, "Put in core/defaults.py alongside other default implementations")

    q2 = project.ask_question(
        question="How should we handle @wip tags on scenarios without step definitions?",
        context="WIP.md claimed features were ready for @wip removal but they weren't",
        priority=QuestionPriority.IMPORTANT
    )
    project.answer_question(q2.id, "Keep @wip on scenarios without steps. Update WIP.md to reflect reality.")


def simulate_reasoning_session(project: CollaborativeProject):
    """Simulate a Graph of Thought reasoning session for a technical decision."""

    print("\n" + "=" * 70)
    print("REASONING SESSION: Designing the Dogfood Workflow")
    print("=" * 70)

    # Create a graph to explore the design space
    def evaluator(thought_content):
        """Score based on keywords indicating good design."""
        content = thought_content.lower()
        score = 0.3  # Base score

        if "simple" in content or "minimal" in content:
            score += 0.2
        if "automatic" in content or "seamless" in content:
            score += 0.15
        if "persist" in content or "save" in content:
            score += 0.1
        if "resume" in content or "handoff" in content:
            score += 0.15
        if "complex" in content or "manual" in content:
            score -= 0.1

        return min(1.0, max(0.0, score))

    def generator(thought_content):
        """Generate follow-up thoughts based on the current thought content."""
        expansions = {
            "How should session state be managed for dogfooding?": [
                "Automatic persistence: Save state after every significant action",
                "Explicit save: Require user to trigger save before ending session",
                "Hybrid: Auto-save drafts, explicit save for milestones",
            ],
            "Automatic persistence: Save state after every significant action": [
                "Use hooks to trigger save on chunk completion, question answered",
                "Implement write-ahead log for crash recovery",
                "Keep it simple: just save to JSON file on each mutation",
            ],
            "Keep it simple: just save to JSON file on each mutation": [
                "PROJECT.json in repo root - easy to find and version control",
                ".got/state.json in hidden directory - cleaner but less visible",
                "Both: working state in .got/, exportable snapshot as PROJECT.json",
            ],
        }
        return expansions.get(thought_content, [])

    graph = GraphOfThought(evaluator=evaluator, generator=generator)

    # Start exploration
    root = graph.add_thought("How should session state be managed for dogfooding?")

    # Expand a few levels
    config = SearchConfig(
        max_expansions=6,
        beam_width=2,
        max_depth=3
    )
    result = asyncio.run(graph.beam_search(config=config))

    print(f"\nExploration completed: {result.termination_reason}")
    print(f"Thoughts explored: {len(graph.thoughts)}")

    # Show the best path
    if result.best_path:
        print("\nBest reasoning path:")
        for i, thought in enumerate(result.best_path):
            indent = "  " * i
            score = f"[{thought.score:.2f}]" if thought.score else ""
            content = thought.content[:55] + "..." if len(thought.content) > 55 else thought.content
            print(f"{indent}-> {score} {content}")

    # Show the graph
    print("\nFull exploration graph:")
    print(graph.visualize())

    # Record the decision as a discovery
    if result.best_path and len(result.best_path) > 1:
        best_thought = result.best_path[-1]
        project.record_discovery(
            f"Design decision explored: {best_thought.content}"
        )

    return graph


def show_project_status(project: CollaborativeProject):
    """Display current project status."""

    print("\n" + "=" * 70)
    print("PROJECT STATUS: graph-of-thought-enterprise")
    print("=" * 70)

    status = project.get_project_status()

    print(f"\nWork Chunks: {status['chunks']}")
    print(f"  Total estimate: {status.get('estimated_hours_remaining', 'N/A')} hours remaining")

    # Questions
    print(f"\nQuestions: {status['questions']}")

    blocking = project.get_blocking_questions()
    if blocking:
        print("\n  Blocking Questions:")
        for q in blocking:
            print(f"    - {q.content[:60]}...")

    # Ready chunks
    ready = project.get_ready_chunks()
    if ready:
        print("\n  Ready to Start:")
        for c in ready:
            print(f"    - {c.content}")

    # Can we proceed?
    can_proceed, reason = project.can_proceed()
    print(f"\nCan proceed: {can_proceed}")
    print(f"Reason: {reason}")


def show_knowledge_base(knowledge: InMemoryKnowledgeService):
    """Display knowledge base contents."""

    print("\n" + "=" * 70)
    print("KNOWLEDGE BASE")
    print("=" * 70)

    entries = knowledge.get_all_entries()
    decisions = knowledge.get_all_decisions()

    print(f"\nPatterns: {len(entries)}")
    for e in entries:
        # Get first line of content as title
        title = e.content.strip().split('\n')[0][:50]
        print(f"  - {title}")
        if e.tags:
            print(f"    Tags: {', '.join(e.tags)}")

    print(f"\nDecisions: {len(decisions)}")
    for d in decisions:
        date_str = d.created_at.strftime("%Y-%m-%d") if d.created_at else "N/A"
        print(f"  - [{date_str}] {d.title}")


def generate_handoff(project: CollaborativeProject):
    """Generate handoff context for the next session."""

    print("\n" + "=" * 70)
    print("HANDOFF CONTEXT (for next session)")
    print("=" * 70)

    context = project.get_resumption_context()
    print(context)

    return context


def main():
    """Run the dogfood demo."""

    print("=" * 70)
    print("DOGFOOD DEMO: Building Graph of Thought with Graph of Thought")
    print("=" * 70)
    print("\nThis demo models our actual development workflow.")
    print("It uses the collaborative and services modules to track")
    print("our work on building the Graph of Thought enterprise platform.")

    # Setup
    print("\n--- Setting up project and services ---")

    knowledge = InMemoryKnowledgeService()
    project = create_got_project()

    # Populate from our actual docs
    add_knowledge_from_claude_md(knowledge)
    add_work_chunks(project)
    add_session_questions(project)

    print("  Project created: graph-of-thought-enterprise")
    print(f"  Knowledge base: {len(knowledge.get_all_entries())} patterns, {len(knowledge.get_all_decisions())} decisions")
    print("  Work chunks loaded from WIP.md")
    print("  Session questions added")

    # Show current state
    show_project_status(project)
    show_knowledge_base(knowledge)

    # Simulate a reasoning session
    graph = simulate_reasoning_session(project)

    # Generate handoff
    generate_handoff(project)

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\nThis demo shows how we could use Graph of Thought to:")
    print("  1. Track our development work (chunks, questions, progress)")
    print("  2. Capture knowledge (patterns, decisions from CLAUDE.md)")
    print("  3. Reason about design decisions (graph exploration)")
    print("  4. Generate handoffs for session continuity")
    print("\nNext steps:")
    print("  - Add persistence to save state between sessions")
    print("  - Create CLI for easier interaction")
    print("  - Integrate with git for chunk<->commit tracking")


if __name__ == "__main__":
    main()
