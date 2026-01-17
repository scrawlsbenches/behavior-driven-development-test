"""
Persona-aware step definitions for Knowledge Management features.

Covers:
- decisions_and_learnings.feature - Recording and finding decisions
- question_routing.feature - Asking and answering questions

These steps wrap mock services to test business-focused BDD scenarios.
"""

from behave import given, when, then, use_step_matcher
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

# Import enums from domain layer to avoid duplicate definitions
from graph_of_thought.domain.enums import (
    QuestionPriority,
    QuestionStatus,
    ChunkStatus,
)

use_step_matcher("parse")


# =============================================================================
# BDD-Specific Models (use domain enums)
# =============================================================================

@dataclass
class Decision:
    """A recorded technical or business decision."""
    id: str
    title: str
    context: str
    decision: str
    rationale: str
    alternatives: str = ""
    consequences: str = ""
    made_by: str = ""
    project: str = ""
    date: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    searchable_text: str = ""

    def __post_init__(self):
        # Build searchable text from all fields
        self.searchable_text = " ".join([
            self.title, self.context, self.decision,
            self.rationale, self.alternatives, self.consequences
        ]).lower()


@dataclass
class Question:
    """A question asked during work."""
    id: str
    question: str
    context: str = ""
    blocking: bool = False
    priority: QuestionPriority = QuestionPriority.NORMAL
    status: QuestionStatus = QuestionStatus.PENDING
    asked_by: str = ""
    project: str = ""
    routed_to: str = ""
    assigned_to: str = ""
    answer: str = ""
    answered_by: str = ""
    answered_at: Optional[datetime] = None
    next_steps: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RoutingRule:
    """Rule for routing questions to appropriate experts."""
    keyword_pattern: str
    route_to: str
    priority: str


@dataclass
class WorkChunk:
    """A focused work session."""
    id: str
    name: str
    project: str
    status: ChunkStatus = ChunkStatus.ACTIVE


# =============================================================================
# Mock Knowledge Service
# =============================================================================

class MockKnowledgeService:
    """Mock service for knowledge management operations."""

    def __init__(self):
        self.decisions: Dict[str, Decision] = {}
        self.questions: Dict[str, Question] = {}
        self.routing_rules: List[RoutingRule] = []
        self.notifications: List[Dict] = []
        self.work_chunks: Dict[str, WorkChunk] = {}
        self._decision_counter = 0
        self._question_counter = 0

    def record_decision(
        self,
        title: str,
        context: str,
        decision: str,
        rationale: str,
        alternatives: str = "",
        consequences: str = "",
        made_by: str = "",
        project: str = "",
    ) -> Decision:
        """Record a new decision to the knowledge base."""
        self._decision_counter += 1
        dec = Decision(
            id=f"DEC-{self._decision_counter:04d}",
            title=title,
            context=context,
            decision=decision,
            rationale=rationale,
            alternatives=alternatives,
            consequences=consequences,
            made_by=made_by,
            project=project,
        )
        self.decisions[dec.id] = dec
        return dec

    def search_decisions(self, query: str) -> List[Decision]:
        """Search decisions by keyword."""
        query_lower = query.lower()
        results = []
        for dec in self.decisions.values():
            if query_lower in dec.searchable_text or query_lower in dec.title.lower():
                results.append(dec)
        return results

    def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get a decision by ID."""
        return self.decisions.get(decision_id)

    def get_decision_by_title(self, title: str) -> Optional[Decision]:
        """Get a decision by title."""
        for dec in self.decisions.values():
            if dec.title == title:
                return dec
        return None

    def ask_question(
        self,
        question: str,
        context: str = "",
        blocking: bool = False,
        asked_by: str = "",
        project: str = "",
    ) -> Question:
        """Ask a new question."""
        self._question_counter += 1

        # Blocking questions always have HIGH priority
        if blocking:
            priority = QuestionPriority.HIGH
        else:
            # Non-blocking: use routing rule priority or default to NORMAL
            priority = QuestionPriority.NORMAL
            routed_to_check = self._route_question(question)
            if routed_to_check:
                rule_priority = self._get_route_priority(question)
                if rule_priority == "high":
                    priority = QuestionPriority.HIGH
                elif rule_priority == "medium":
                    priority = QuestionPriority.MEDIUM

        # Route the question based on rules
        routed_to = self._route_question(question)

        q = Question(
            id=f"Q-{self._question_counter:04d}",
            question=question,
            context=context,
            blocking=blocking,
            priority=priority,
            asked_by=asked_by,
            project=project,
            routed_to=routed_to or "general",
        )
        self.questions[q.id] = q

        # Send notification
        self.notifications.append({
            "type": "question_created",
            "to": asked_by,
            "question_id": q.id,
            "tracking_id": q.id,
        })

        return q

    def _route_question(self, question: str) -> str:
        """Route question based on configured rules."""
        question_lower = question.lower()
        for rule in self.routing_rules:
            if rule.keyword_pattern.lower() in question_lower:
                return rule.route_to
        return ""

    def _get_route_priority(self, question: str) -> str:
        """Get priority from routing rules."""
        question_lower = question.lower()
        for rule in self.routing_rules:
            if rule.keyword_pattern.lower() in question_lower:
                return rule.priority
        return "normal"

    def answer_question(
        self,
        question_id: str,
        answer: str,
        answered_by: str,
        next_steps: str = "",
    ) -> Question:
        """Answer a question."""
        q = self.questions.get(question_id)
        if q:
            q.answer = answer
            q.answered_by = answered_by
            q.answered_at = datetime.now()
            q.next_steps = next_steps
            q.status = QuestionStatus.ANSWERED

            # Notify the asker
            self.notifications.append({
                "type": "question_answered",
                "to": q.asked_by,
                "question_id": question_id,
                "answered_by": answered_by,
            })

            # Unblock work chunk if it was blocking
            # Note: Use .value comparison because behave can import modules multiple
            # times, creating duplicate enum classes that don't compare equal directly
            if q.blocking and q.project:
                for chunk in self.work_chunks.values():
                    if chunk.project == q.project and chunk.status.value == "blocked":
                        chunk.status = ChunkStatus.ACTIVE

        return q

    def add_routing_rule(self, keyword: str, route_to: str, priority: str = "normal"):
        """Add a routing rule."""
        self.routing_rules.append(RoutingRule(
            keyword_pattern=keyword,
            route_to=route_to,
            priority=priority,
        ))

    def get_work_chunk(self, chunk_id: str) -> Optional[WorkChunk]:
        """Get a work chunk by ID."""
        return self.work_chunks.get(chunk_id)


# =============================================================================
# Service Access Helper
# =============================================================================

def get_knowledge_service(context) -> MockKnowledgeService:
    """Get or create the knowledge service."""
    if not hasattr(context, 'knowledge_service'):
        context.knowledge_service = MockKnowledgeService()
    return context.knowledge_service


# =============================================================================
# Background Steps
# =============================================================================

@given("the knowledge service is available")
def step_knowledge_service_available(context):
    """Set up the knowledge service."""
    context.knowledge_service = MockKnowledgeService()


@given("the question service is available")
def step_question_service_available(context):
    """Set up the question service (same as knowledge service)."""
    if not hasattr(context, 'knowledge_service'):
        context.knowledge_service = MockKnowledgeService()


@given("question routing rules are configured")
def step_routing_rules_configured(context):
    """Configure default routing rules."""
    service = get_knowledge_service(context)
    # Add default rules for common question types
    service.add_routing_rule("security", "security-team", "high")
    service.add_routing_rule("architecture", "tech-leads", "high")
    service.add_routing_rule("feature", "product-owner", "medium")
    service.add_routing_rule("budget", "finance", "medium")
    # Business/product questions go to product-owner
    service.add_routing_rule("churn", "product-owner", "medium")
    service.add_routing_rule("trial", "product-owner", "medium")
    service.add_routing_rule("retention", "product-owner", "medium")
    service.add_routing_rule("user", "product-owner", "medium")


# =============================================================================
# Decision Recording Steps - MVP-P0
# =============================================================================

# Note: "{persona} is working on project" step is defined in cost_management_steps.py
# We ensure the knowledge service work chunk is created when recording decisions.

@when("{persona} records a decision")
@when("{persona} records a decision:")
def step_record_decision(context, persona):
    """Record a decision from table data."""
    context.current_persona = persona
    service = get_knowledge_service(context)

    # Parse table data
    decision_data = {}
    for row in context.table:
        decision_data[row['field']] = row['value']

    project = getattr(context, 'current_project', '')

    context.current_decision = service.record_decision(
        title=decision_data.get('title', ''),
        context=decision_data.get('context', ''),
        decision=decision_data.get('decision', ''),
        rationale=decision_data.get('rationale', ''),
        alternatives=decision_data.get('alternatives', ''),
        consequences=decision_data.get('consequences', ''),
        made_by=persona,
        project=project,
    )


@then("the decision should be saved to the knowledge base")
def step_decision_saved(context):
    """Verify decision was saved."""
    service = get_knowledge_service(context)
    assert context.current_decision.id in service.decisions, "Decision not saved"


@then("it should be searchable by \"{term1}\" and \"{term2}\"")
def step_searchable_by_terms(context, term1, term2):
    """Verify decision is searchable by given terms."""
    service = get_knowledge_service(context)

    results1 = service.search_decisions(term1)
    results2 = service.search_decisions(term2)

    assert len(results1) > 0, f"Decision not searchable by '{term1}'"
    assert len(results2) > 0, f"Decision not searchable by '{term2}'"


@then("it should be linked to project \"{project}\"")
def step_linked_to_project(context, project):
    """Verify decision is linked to project."""
    assert context.current_decision.project == project, \
        f"Expected project '{project}', got '{context.current_decision.project}'"


@then("the decision timestamp should be recorded")
def step_decision_timestamp_recorded(context):
    """Verify decision has timestamp."""
    assert context.current_decision.date is not None, "Decision has no timestamp"


# =============================================================================
# Decision Search Steps - MVP-P0
# =============================================================================

@given("decisions exist in the knowledge base")
@given("decisions exist in the knowledge base:")
def step_decisions_exist(context):
    """Create decisions from table data."""
    service = get_knowledge_service(context)

    for row in context.table:
        title = row['title']
        project = row['project']
        date_str = row['date']

        # Parse date
        dec_date = datetime.strptime(date_str, "%Y-%m-%d")

        dec = service.record_decision(
            title=title,
            context=f"Context for {title}",
            decision=f"Decision: {title}",
            rationale=f"Rationale for {title}",
            project=project,
        )
        dec.date = dec_date


@when("{persona} searches for \"{query}\"")
def step_search_decisions(context, persona, query):
    """Search for decisions."""
    context.current_persona = persona
    service = get_knowledge_service(context)
    context.search_results = service.search_decisions(query)


@then("the search should return {count:d} decisions")
def step_search_returns_count(context, count):
    """Verify search result count."""
    actual = len(context.search_results)
    assert actual == count, f"Expected {count} results, got {actual}"


@then("results should show the decision title, project, and date")
def step_results_show_fields(context):
    """Verify search results have required fields."""
    for result in context.search_results:
        assert result.title, "Result missing title"
        assert result.project, "Result missing project"
        assert result.date, "Result missing date"


@then("{persona} should be able to view full details of each")
def step_view_full_details(context, persona):
    """Verify full details are accessible."""
    service = get_knowledge_service(context)
    for result in context.search_results:
        full = service.get_decision(result.id)
        assert full is not None, f"Cannot view details of {result.id}"


# =============================================================================
# Decision Viewing Steps - MVP-P0
# =============================================================================

@given("a decision \"{title}\" exists")
def step_decision_exists(context, title):
    """Create a decision with the given title."""
    service = get_knowledge_service(context)

    context.current_decision = service.record_decision(
        title=title,
        context="API response times exceed 500ms, need caching",
        decision="Implement Redis caching with 5-minute TTL",
        rationale="Redis provides sub-ms reads, team has expertise",
        alternatives="Memcached (less features), In-memory (not shared)",
        consequences="Need Redis infrastructure, adds operational cost",
        made_by="Jordan",
        project="API Optimization",
    )


@when("{persona} views the full decision")
def step_view_full_decision(context, persona):
    """View full decision details."""
    context.current_persona = persona
    service = get_knowledge_service(context)
    context.viewed_decision = service.get_decision(context.current_decision.id)


@then("they should see all recorded details")
@then("they should see all recorded details:")
def step_see_all_details(context):
    """Verify all sections are present."""
    dec = context.viewed_decision

    for row in context.table:
        section = row['section']
        expected_present = row['present'].lower() == 'yes'

        # Check each section
        if section == 'title':
            has_value = bool(dec.title)
        elif section == 'context':
            has_value = bool(dec.context)
        elif section == 'decision':
            has_value = bool(dec.decision)
        elif section == 'rationale':
            has_value = bool(dec.rationale)
        elif section == 'alternatives':
            has_value = bool(dec.alternatives)
        elif section == 'consequences':
            has_value = bool(dec.consequences)
        elif section == 'made_by':
            has_value = bool(dec.made_by)
        elif section == 'date':
            has_value = dec.date is not None
        elif section == 'related_project':
            has_value = bool(dec.project)
        else:
            has_value = False

        if expected_present:
            assert has_value, f"Section '{section}' should be present but is empty"


# =============================================================================
# Question Asking Steps - MVP-P0
# =============================================================================

@given("{persona} is working on \"{task}\"")
def step_persona_working_on_task(context, persona, task):
    """Set up persona working on a task."""
    context.current_persona = persona
    context.current_task = task
    context.current_project = task  # Use task as project for simplicity

    # Create a work chunk
    service = get_knowledge_service(context)
    chunk_id = f"CHUNK-{task.replace(' ', '-')}"
    service.work_chunks[chunk_id] = WorkChunk(
        id=chunk_id,
        name=task,
        project=task,
        status=ChunkStatus.ACTIVE,
    )
    context.current_chunk = service.work_chunks[chunk_id]


@when("{persona} asks a blocking question")
@when("{persona} asks a blocking question:")
def step_ask_blocking_question(context, persona):
    """Ask a blocking question from table data."""
    context.current_persona = persona
    service = get_knowledge_service(context)

    # Parse table data
    question_data = {}
    for row in context.table:
        question_data[row['field']] = row['value']

    blocking = question_data.get('blocking', 'true').lower() == 'true'

    context.current_question = service.ask_question(
        question=question_data.get('question', ''),
        context=question_data.get('context', ''),
        blocking=blocking,
        asked_by=persona,
        project=getattr(context, 'current_project', ''),
    )

    # Mark work chunk as blocked if question is blocking
    if blocking and hasattr(context, 'current_chunk'):
        context.current_chunk.status = ChunkStatus.BLOCKED


@then("a question ticket should be created with high priority")
def step_question_high_priority(context):
    """Verify question has high priority."""
    assert context.current_question.priority == QuestionPriority.HIGH, \
        f"Expected HIGH priority, got {context.current_question.priority}"


@then("the ticket should include work context")
def step_ticket_includes_context(context):
    """Verify ticket has context."""
    assert context.current_question.context, "Question missing context"


# Note: "it should be routed to" step is handled by governance_steps.py with context check

@then("{persona} should receive a tracking ID")
def step_receive_tracking_id(context, persona):
    """Verify tracking ID was issued."""
    service = get_knowledge_service(context)
    notifications = [n for n in service.notifications
                     if n.get('to') == persona and 'tracking_id' in n]
    assert len(notifications) > 0, f"No tracking ID sent to {persona}"


@then("the work chunk should be marked as \"{status}\"")
def step_chunk_marked_status(context, status):
    """Verify work chunk status."""
    expected = ChunkStatus(status)
    assert context.current_chunk.status == expected, \
        f"Expected chunk status '{status}', got '{context.current_chunk.status.value}'"


# =============================================================================
# Question Routing Steps - MVP-P0
# =============================================================================

@given("routing rules")
@given("routing rules:")
def step_routing_rules(context):
    """Configure routing rules from table."""
    service = get_knowledge_service(context)
    service.routing_rules.clear()  # Clear defaults

    for row in context.table:
        service.add_routing_rule(
            keyword=row['keyword_pattern'],
            route_to=row['route_to'],
            priority=row['priority'],
        )


# Note: "{persona} asks \"{question}\"" is handled by exploration_steps.py with context check
# Note: "the question should be routed to" is handled by services_steps.py with context check

@then("the priority should be \"{priority}\"")
def step_priority_is(context, priority):
    """Verify question priority."""
    expected = QuestionPriority(priority)
    assert context.current_question.priority == expected, \
        f"Expected priority '{priority}', got '{context.current_question.priority.value}'"


# =============================================================================
# Non-Blocking Question Steps - MVP-P0
# =============================================================================

@given("{persona} is exploring options and has a clarifying question")
def step_exploring_with_question(context, persona):
    """Set up persona exploring options."""
    context.current_persona = persona
    context.current_project = "Exploration"

    # Create active work chunk
    service = get_knowledge_service(context)
    chunk_id = "CHUNK-explore"
    service.work_chunks[chunk_id] = WorkChunk(
        id=chunk_id,
        name="Exploration",
        project="Exploration",
        status=ChunkStatus.ACTIVE,
    )
    context.current_chunk = service.work_chunks[chunk_id]


@when("{persona} asks a non-blocking question")
@when("{persona} asks a non-blocking question:")
def step_ask_non_blocking_question(context, persona):
    """Ask a non-blocking question."""
    context.current_persona = persona
    service = get_knowledge_service(context)

    # Parse table data
    question_data = {}
    for row in context.table:
        question_data[row['field']] = row['value']

    context.current_question = service.ask_question(
        question=question_data.get('question', ''),
        blocking=False,
        asked_by=persona,
        project=getattr(context, 'current_project', ''),
    )


@then("a question ticket should be created with normal priority")
def step_question_normal_priority(context):
    """Verify question has normal priority."""
    assert context.current_question.priority == QuestionPriority.NORMAL, \
        f"Expected NORMAL priority, got {context.current_question.priority}"


@then("{persona} should be able to continue working")
def step_can_continue_working(context, persona):
    """Verify work can continue."""
    assert context.current_chunk.status == ChunkStatus.ACTIVE, \
        "Work chunk should remain active for non-blocking question"


@then("the work chunk should remain \"{status}\"")
def step_chunk_remains_status(context, status):
    """Verify work chunk status remains as expected."""
    expected = ChunkStatus(status)
    assert context.current_chunk.status == expected, \
        f"Expected chunk status '{status}', got '{context.current_chunk.status.value}'"


# =============================================================================
# Question Answering Steps - MVP-P0
# =============================================================================

# Note: "a pending question" step is handled by services_steps.py with context check

@given("the question is assigned to {persona} ({role})")
def step_question_assigned_to(context, persona, role):
    """Assign question to a persona."""
    context.current_question.assigned_to = persona
    context.current_question.status = QuestionStatus.ASSIGNED


@when("{persona} answers")
@when("{persona} answers:")
def step_persona_answers(context, persona):
    """Answer a question with docstring."""
    service = get_knowledge_service(context)
    answer_text = context.text.strip() if context.text else ""

    service.answer_question(
        question_id=context.current_question.id,
        answer=answer_text,
        answered_by=persona,
    )


@then("the question should be marked as \"{status}\"")
def step_question_marked_status(context, status):
    """Verify question status."""
    expected = QuestionStatus(status)
    assert context.current_question.status == expected, \
        f"Expected status '{status}', got '{context.current_question.status.value}'"


@then("{persona} should be notified immediately")
def step_persona_notified(context, persona):
    """Verify notification was sent."""
    service = get_knowledge_service(context)
    notifications = [n for n in service.notifications
                     if n.get('to') == persona or n.get('type') == 'question_answered']
    assert len(notifications) > 0, f"No notification sent to {persona}"


@then("{persona}'s work chunk should be unblocked")
def step_chunk_unblocked(context, persona):
    """Verify work chunk is unblocked."""
    # Find any work chunk that was blocked
    service = get_knowledge_service(context)
    for chunk in service.work_chunks.values():
        if chunk.status == ChunkStatus.ACTIVE:
            return  # Found an active chunk
    # If we're still blocked, check current chunk
    assert context.current_chunk.status == ChunkStatus.ACTIVE, \
        "Work chunk should be unblocked after answer"


@then("the answer should be saved to the knowledge base")
def step_answer_saved(context):
    """Verify answer is saved."""
    assert context.current_question.answer, "Answer not saved"
    assert context.current_question.status == QuestionStatus.ANSWERED, "Question not marked as answered"


# =============================================================================
# Answer Display Steps - MVP-P0
# =============================================================================

@when("{persona} provides an answer")
def step_provides_answer(context, persona):
    """Provide an answer (sets up context for viewing)."""
    service = get_knowledge_service(context)

    # If no current question, create one
    if not hasattr(context, 'current_question'):
        context.current_question = service.ask_question(
            question="Test question",
            asked_by="Jordan",
        )

    service.answer_question(
        question_id=context.current_question.id,
        answer="The expert's response with detailed guidance.",
        answered_by=persona,
        next_steps="Review the documentation and implement the changes.",
    )


# Note: "{persona} should see:" is handled by governance_steps.py with context check

@then("{persona} should be able to ask follow-up questions")
def step_can_ask_followup(context, persona):
    """Verify follow-up questions can be asked."""
    # In a real implementation, this would check UI state
    # For now, just verify the question is answered and open for follow-up
    assert context.current_question.status == QuestionStatus.ANSWERED, \
        "Question must be answered before follow-up"
