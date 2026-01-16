"""
Step definitions for service implementations BDD tests.
"""
from behave import given, when, then, use_step_matcher

from graph_of_thought.services.implementations import (
    InMemoryGovernanceService,
    InMemoryResourceService,
    InMemoryKnowledgeService,
    InMemoryQuestionService,
    InMemoryCommunicationService,
    SimpleGovernanceService,
    SimpleResourceService,
    SimpleKnowledgeService,
    SimpleQuestionService,
    SimpleCommunicationService,
)
from graph_of_thought.services.protocols import (
    ApprovalStatus,
    Priority,
    ResourceType,
    KnowledgeEntry,
    Decision,
)

use_step_matcher("parse")


# =============================================================================
# InMemory Services (for testing with configurable behavior)
# =============================================================================

@given("an in-memory governance service")
def step_inmemory_governance(context):
    # Configure to auto-approve everything (like the old Null behavior)
    context.governance = InMemoryGovernanceService(default_status=ApprovalStatus.APPROVED)


@given("an in-memory resource service")
def step_inmemory_resource(context):
    # Configure with unlimited resources (like the old Null behavior)
    context.resource_service = InMemoryResourceService(unlimited=True)


@given("an in-memory knowledge service")
def step_inmemory_knowledge(context):
    # Configure to not find anything on retrieve (like the old Null behavior)
    context.knowledge = InMemoryKnowledgeService(retrieval_enabled=False)


@when('I check approval for action "{action}"')
def step_check_approval(context, action):
    context.approval_status, context.approval_reason = context.governance.check_approval(
        action, {}
    )


@then('the approval status should be "{status}"')
def step_check_approval_status(context, status):
    expected = ApprovalStatus[status]
    assert context.approval_status == expected, \
        f"Expected {status}, got {context.approval_status}"


@when('I check available tokens for project "{project}"')
def step_check_available_tokens(context, project):
    context.available, context.remaining = context.resource_service.check_available(
        ResourceType.TOKENS, "project", project, 0
    )


@then("resources should be available")
def step_resources_available(context):
    assert context.available is True


@then("remaining resources should be infinite")
def step_remaining_infinite(context):
    assert context.remaining == float('inf')


@when('I store a knowledge entry "{content}"')
def step_store_knowledge(context, content):
    entry = KnowledgeEntry(
        id="",
        content=content,
        entry_type="general",
    )
    context.stored_id = context.knowledge.store(entry)


@when('I retrieve knowledge for "{query}"')
def step_retrieve_knowledge(context, query):
    context.knowledge_results = context.knowledge.retrieve(query)


@then("no knowledge entries should be found")
def step_no_knowledge_found(context):
    assert len(context.knowledge_results) == 0


# =============================================================================
# Simple Governance Service
# =============================================================================

@given("a simple governance service")
def step_simple_governance(context):
    context.governance = SimpleGovernanceService()


@given('a policy "{action}" requires review')
def step_policy_requires_review(context, action):
    context.governance.add_policy(action, ApprovalStatus.NEEDS_REVIEW)


@when('I record an audit event for action "{action}" by actor "{actor}"')
def step_record_audit(context, action, actor):
    context.governance.record_audit(action, {}, "success", actor)


@then("the audit log should have {count:d} entry")
@then("the audit log should have {count:d} entries")
def step_check_audit_count(context, count):
    logs = context.governance.get_audit_log()
    assert len(logs) == count, f"Expected {count} entries, got {len(logs)}"


@then('the audit entry should have actor "{actor}"')
def step_check_audit_actor(context, actor):
    logs = context.governance.get_audit_log()
    assert logs[0]["actor"] == actor


@when('I request approval for action "{action}" with justification "{justification}"')
def step_request_approval(context, action, justification):
    context.approval_id = context.governance.request_approval(action, {}, justification)


@then("an approval ID should be returned")
def step_approval_id_returned(context):
    assert context.approval_id is not None
    assert len(context.approval_id) > 0


@when('the approval is granted by "{approver}"')
def step_grant_approval(context, approver):
    context.governance.approve(context.approval_id, approver)


@then('the pending approval status should be "{status}"')
def step_check_pending_approval_status(context, status):
    approval = context.governance._pending_approvals.get(context.approval_id)
    assert approval["status"] == status


# =============================================================================
# Simple Resource Service
# =============================================================================

@given("a simple resource service")
def step_simple_resource(context):
    context.resource_service = SimpleResourceService()


@when('I set a token budget of {amount:d} for project "{project}"')
def step_set_token_budget(context, amount, project):
    context.resource_service.set_budget(
        ResourceType.TOKENS, "project", project, amount, "tokens"
    )


@given('a token budget of {amount:d} for project "{project}"')
def step_given_token_budget(context, amount, project):
    context.resource_service.set_budget(
        ResourceType.TOKENS, "project", project, amount, "tokens"
    )


@then('the token budget for project "{project}" should be {amount:d}')
def step_check_token_budget(context, project, amount):
    budget = context.resource_service.get_budget(ResourceType.TOKENS, "project", project)
    assert budget.allocated == amount, f"Expected {amount}, got {budget.allocated}"


@when('I consume {amount:d} tokens for project "{project}" with description "{desc}"')
def step_consume_tokens_with_desc(context, amount, project, desc):
    context.consume_result = context.resource_service.consume(
        ResourceType.TOKENS, "project", project, amount, desc
    )


@when('I consume {amount:d} tokens for project "{project}"')
def step_consume_tokens(context, amount, project):
    context.consume_result = context.resource_service.consume(
        ResourceType.TOKENS, "project", project, amount
    )


@then('the remaining tokens for project "{project}" should be {amount:d}')
def step_check_remaining_tokens(context, project, amount):
    budget = context.resource_service.get_budget(ResourceType.TOKENS, "project", project)
    assert budget.remaining == amount, f"Expected {amount}, got {budget.remaining}"


@when('I try to consume {amount:d} tokens for project "{project}"')
def step_try_consume_tokens(context, amount, project):
    context.consume_result = context.resource_service.consume(
        ResourceType.TOKENS, "project", project, amount
    )


@then("the consumption should be rejected")
def step_consumption_rejected(context):
    assert context.consume_result is False


@when('I get the consumption report for project "{project}"')
def step_get_consumption_report(context, project):
    context.consumption_report = context.resource_service.get_consumption_report(
        "project", project
    )


@then("the report should show {count:d} consumption events")
def step_check_consumption_events(context, count):
    assert context.consumption_report["total_events"] == count


@then("the report should show {amount:d} total tokens consumed")
def step_check_total_consumed(context, amount):
    tokens = context.consumption_report["by_resource"].get("TOKENS", 0)
    assert tokens == amount, f"Expected {amount}, got {tokens}"


# =============================================================================
# Simple Knowledge Service
# =============================================================================

@given("a simple knowledge service")
def step_simple_knowledge(context):
    context.knowledge = SimpleKnowledgeService()


@when('I store knowledge "{content}" with tags "{tags}"')
def step_store_knowledge_with_tags(context, content, tags):
    tag_list = [t.strip() for t in tags.split(",")]
    entry = KnowledgeEntry(
        id="",
        content=content,
        entry_type="general",
        tags=tag_list,
    )
    context.stored_id = context.knowledge.store(entry)


@given('a knowledge entry "{content}" of type "{entry_type}"')
def step_given_knowledge_entry(context, content, entry_type):
    entry = KnowledgeEntry(
        id="",
        content=content,
        entry_type=entry_type,
    )
    context.knowledge.store(entry)


@when('I search knowledge for "{query}" filtering by type "{entry_type}"')
def step_retrieve_with_type(context, query, entry_type):
    context.knowledge_results = context.knowledge.retrieve(
        query, entry_types=[entry_type]
    )


@then("{count:d} knowledge entry should be found")
@then("{count:d} knowledge entries should be found")
def step_check_knowledge_count(context, count):
    assert len(context.knowledge_results) == count, \
        f"Expected {count}, got {len(context.knowledge_results)}"


@then('the entry should contain "{text}"')
def step_check_entry_content(context, text):
    assert any(text in e.content for e in context.knowledge_results)


@when('I record a decision "{title}" with rationale "{rationale}"')
def step_record_decision(context, title, rationale):
    decision = Decision(
        id="",
        title=title,
        context="Test context",
        options=["Option A", "Option B"],
        chosen="Option A",
        rationale=rationale,
        consequences=["Expected outcome"],
    )
    context.decision_id = context.knowledge.record_decision(decision)


@then("the decision should be stored")
def step_decision_stored(context):
    assert context.decision_id is not None


@then('retrieving "{query}" should find the decision')
def step_retrieve_decision(context, query):
    results = context.knowledge.retrieve(query, entry_types=["decision"])
    assert len(results) > 0, "Decision not found"


# =============================================================================
# Simple Question Service
# =============================================================================

@given("a simple question service")
def step_simple_question(context):
    context.question_service = SimpleQuestionService()


@when('I ask a question "{question}" with priority "{priority}"')
def step_ask_question_with_priority(context, question, priority):
    context.ticket = context.question_service.ask(
        question, priority=Priority[priority]
    )


@when('I ask a question "{question}"')
def step_ask_question(context, question):
    context.ticket = context.question_service.ask(question)


@then("a question ticket should be created")
def step_ticket_created(context):
    assert context.ticket is not None
    assert context.ticket.id is not None


@then('the ticket should have status "{status}"')
def step_check_ticket_status(context, status):
    assert context.ticket.status == status


@then('the ticket should have priority "{priority}"')
def step_check_ticket_priority(context, priority):
    assert context.ticket.priority == Priority[priority]


@then('the question should be routed to "{target}"')
def step_check_routing(context, target):
    assert context.ticket.routed_to == target


@given('a pending question "{question}"')
def step_pending_question(context, question):
    context.ticket = context.question_service.ask(question)


@given('a question "{question}" with priority "{priority}"')
def step_question_with_priority(context, question, priority):
    context.question_service.ask(question, priority=Priority[priority])


@when('I provide answer "{answer}" from "{answerer}"')
def step_answer_question(context, answer, answerer):
    context.ticket = context.question_service.answer(
        context.ticket.id, answer, answerer
    )


@then('the ticket should have answer "{answer}"')
def step_check_answer(context, answer):
    assert context.ticket.answer == answer


@when("I get pending questions")
def step_get_pending(context):
    context.pending_questions = context.question_service.get_pending()


@then('the first question should have priority "{priority}"')
def step_check_first_priority(context, priority):
    assert context.pending_questions[0].priority == Priority[priority]


# =============================================================================
# Simple Communication Service
# =============================================================================

@given("a simple communication service")
def step_simple_communication(context):
    context.communication = SimpleCommunicationService()


@when('I create a handoff for project "{project}" of type "{handoff_type}"')
def step_create_handoff(context, project, handoff_type):
    context.handoff = context.communication.create_handoff(
        handoff_type, project
    )


@then("a handoff package should be created")
def step_handoff_created(context):
    assert context.handoff is not None
    assert context.handoff.id is not None


@then('the handoff should have type "{handoff_type}"')
def step_check_handoff_type(context, handoff_type):
    assert context.handoff.handoff_type == handoff_type


@when('I record intent "{intent}" for project "{project}"')
def step_record_intent(context, intent, project):
    context.communication.record_intent(project, None, intent, [])


@given('a recorded intent "{intent}" for project "{project}"')
def step_given_recorded_intent(context, intent, project):
    context.communication.record_intent(project, None, intent, [])


@when('I get resumption context for project "{project}"')
def step_get_resumption_context(context, project):
    context.resumption_context = context.communication.get_resumption_context(project)


@then('the context should contain "{text}"')
def step_context_contains(context, text):
    assert text in context.resumption_context


@when('I compress history for project "{project}" with max tokens {max_tokens:d}')
def step_compress_history(context, project, max_tokens):
    context.compressed = context.communication.compress_history(project, max_tokens)


@then("the compressed history should not exceed {max_chars:d} characters")
def step_check_compressed_length(context, max_chars):
    assert len(context.compressed) <= max_chars, \
        f"Compressed history too long: {len(context.compressed)} > {max_chars}"
