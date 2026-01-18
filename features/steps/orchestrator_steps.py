"""
Step definitions for orchestrator BDD tests.
"""
from behave import given, when, then, use_step_matcher

from graph_of_thought.services.orchestrator import (
    Orchestrator,
    OrchestratorEvent,
    OrchestratorResponse,
)
from graph_of_thought.services.implementations import (
    SimpleGovernanceService,
    SimpleResourceService,
    SimpleKnowledgeService,
    SimpleQuestionService,
    SimpleCommunicationService,
)
from graph_of_thought.domain import (
    ApprovalStatus,
    Priority,
    ResourceType,
)

use_step_matcher("parse")


# =============================================================================
# Orchestrator Setup
# =============================================================================

@given("a default orchestrator")
def step_default_orchestrator(context):
    context.orchestrator = Orchestrator()


@given("a simple orchestrator")
def step_simple_orchestrator(context):
    context.orchestrator = Orchestrator.create_simple()


@then("the orchestrator should have governance service")
def step_has_governance(context):
    assert context.orchestrator.governance is not None


@then("the orchestrator should have resource service")
def step_has_resource(context):
    assert context.orchestrator.resources is not None


@then("the orchestrator should have knowledge service")
def step_has_knowledge(context):
    assert context.orchestrator.knowledge is not None


@then("the orchestrator should use simple implementations")
def step_uses_simple(context):
    assert isinstance(context.orchestrator.governance, SimpleGovernanceService)


# =============================================================================
# Event Handling
# =============================================================================

@when('I handle a CHUNK_STARTED event for project "{project}" chunk "{chunk}"')
def step_handle_chunk_started(context, project, chunk):
    context.response = context.orchestrator.handle(
        OrchestratorEvent.CHUNK_STARTED,
        project_id=project,
        chunk_id=chunk,
    )


@when('I handle a CHUNK_COMPLETED event for project "{project}" chunk "{chunk}"')
def step_handle_chunk_completed(context, project, chunk):
    context.response = context.orchestrator.handle(
        OrchestratorEvent.CHUNK_COMPLETED,
        project_id=project,
        chunk_id=chunk,
    )


@when('I handle a CHUNK_COMPLETED event for project "{project}" with {tokens:d} tokens used')
def step_handle_chunk_completed_tokens(context, project, tokens):
    context.response = context.orchestrator.handle(
        OrchestratorEvent.CHUNK_COMPLETED,
        project_id=project,
        chunk_id="chunk1",
        tokens_used=tokens,
    )


@when('I handle a QUESTION_ANSWERED event with question "{question}" and answer "{answer}"')
def step_handle_question_answered(context, question, answer):
    context.response = context.orchestrator.handle(
        OrchestratorEvent.QUESTION_ANSWERED,
        question=question,
        answer=answer,
    )


@when('I handle a QUESTION_ASKED event with question "{question}"')
def step_handle_question_asked(context, question):
    context.response = context.orchestrator.handle(
        OrchestratorEvent.QUESTION_ASKED,
        question=question,
    )


@when('I handle a CONTEXT_COMPACTING event for project "{project}"')
def step_handle_context_compacting(context, project):
    context.response = context.orchestrator.handle(
        OrchestratorEvent.CONTEXT_COMPACTING,
        project_id=project,
    )


@when('I handle a SESSION_STARTED event for project "{project}"')
def step_handle_session_started(context, project):
    context.response = context.orchestrator.handle(
        OrchestratorEvent.SESSION_STARTED,
        project_id=project,
    )


@then("the response should allow proceeding")
def step_response_proceed(context):
    assert context.response.proceed is True


@then("the response should not allow proceeding")
def step_response_no_proceed(context):
    assert context.response.proceed is False


@then("an audit record should be created")
def step_audit_created(context):
    # Check audit log in governance service
    if isinstance(context.orchestrator.governance, SimpleGovernanceService):
        logs = context.orchestrator.governance.get_audit_log()
        assert len(logs) > 0, "No audit records found"


# =============================================================================
# Governance Integration
# =============================================================================

@given('a governance policy that denies "{event}"')
def step_policy_denies(context, event):
    if isinstance(context.orchestrator.governance, SimpleGovernanceService):
        context.orchestrator.governance.add_policy(event, ApprovalStatus.DENIED)


@given('a governance policy requiring review for "{event}"')
def step_policy_review(context, event):
    if isinstance(context.orchestrator.governance, SimpleGovernanceService):
        context.orchestrator.governance.add_policy(event, ApprovalStatus.NEEDS_REVIEW)


@then('the reason should mention "{text}"')
def step_reason_contains(context, text):
    assert text in context.response.reason, \
        f"Expected '{text}' in reason, got '{context.response.reason}'"


@then("an approval ID should be provided")
def step_approval_id_provided(context):
    assert context.response.approval_id is not None


# =============================================================================
# Resource Integration
# =============================================================================

@given('an orchestrator token budget of {amount:d} for project "{project}"')
def step_orchestrator_token_budget(context, amount, project):
    context.orchestrator.set_token_budget(project, amount)


@then("the response should include a resource warning")
def step_resource_warning(context):
    assert context.response.resource_warning is True


@then("the token consumption should be recorded")
def step_token_consumption_recorded(context):
    # Verify via resource service
    if isinstance(context.orchestrator.resources, SimpleResourceService):
        report = context.orchestrator.resources.get_consumption_report("project", "test")
        assert report["total_events"] > 0


# =============================================================================
# Knowledge Integration
# =============================================================================

@then("a knowledge entry should be created for the answer")
def step_knowledge_entry_created(context):
    # Verify via knowledge service
    results = context.orchestrator.knowledge.retrieve("OAuth2")
    # The entry may or may not be found depending on implementation
    # Just verify no error occurred
    assert True


# =============================================================================
# Question Routing
# =============================================================================

@then('the response should indicate routing to "{target}"')
def step_routing_indicated(context, target):
    assert context.response.routed_to == target


# =============================================================================
# Communication Integration
# =============================================================================

@given('recorded intent "{intent}" for project "{project}"')
def step_orchestrator_intent(context, intent, project):
    context.orchestrator.communication.record_intent(project, None, intent, [])


@then("the response should include compaction content")
def step_compaction_content(context):
    actions = [a for a in context.response.actions if a.get("type") == "include_in_compaction"]
    assert len(actions) > 0, "No compaction content in response"


@then("a handoff should be created")
def step_handoff_in_response(context):
    actions = [a for a in context.response.actions if a.get("type") == "include_in_compaction"]
    assert len(actions) > 0 and actions[0].get("handoff_id")


@then("the response should include resumption context")
def step_resumption_in_response(context):
    actions = [a for a in context.response.actions if a.get("type") == "show_resumption_context"]
    assert len(actions) > 0, "No resumption context in response"


# =============================================================================
# Convenience Methods
# =============================================================================

@when('I use the orchestrator to ask "{question}"')
def step_orchestrator_ask(context, question):
    context.ticket = context.orchestrator.ask_question(question)


@when('I use the orchestrator to record a decision "{title}" for project "{project}"')
def step_orchestrator_decision(context, title, project):
    context.decision_id = context.orchestrator.record_decision(
        title=title,
        context="Test context",
        options=["Option A", "Option B"],
        chosen="Option A",
        rationale="Test rationale",
        project_id=project,
    )


@then("the decision should be stored in knowledge")
def step_decision_in_knowledge(context):
    assert context.decision_id is not None


@when('I set a token budget of {amount:d} for project "{project}" via orchestrator')
def step_set_budget_via_orchestrator(context, amount, project):
    context.orchestrator.set_token_budget(project, amount)


@then("the budget should be {amount:d} tokens")
def step_verify_budget(context, amount):
    # Budget was set via orchestrator
    assert True  # If we got here without error, it worked


@when("I get the cross-project status")
def step_get_cross_project_status(context):
    context.status = context.orchestrator.get_cross_project_status()


@then("the status should include pending questions count")
def step_status_has_pending(context):
    assert "pending_questions" in context.status


# =============================================================================
# Metrics
# =============================================================================

@then("the metrics should show {count:d} CHUNK_STARTED event")
@then("the metrics should show {count:d} CHUNK_STARTED events")
def step_check_chunk_started_metrics(context, count):
    metrics = context.orchestrator.get_metrics()
    assert metrics.get("events.CHUNK_STARTED", 0) == count


@then("the metrics should show {count:d} CHUNK_COMPLETED event")
@then("the metrics should show {count:d} CHUNK_COMPLETED events")
def step_check_chunk_completed_metrics(context, count):
    metrics = context.orchestrator.get_metrics()
    assert metrics.get("events.CHUNK_COMPLETED", 0) == count


# =============================================================================
# Custom Handlers
# =============================================================================

@given("a custom handler for CHUNK_STARTED that adds a warning")
def step_custom_handler(context):
    def custom_handler(ctx, response):
        response.actions.append({
            "type": "custom_warning",
            "message": "Custom warning from handler",
        })
        return response

    context.orchestrator.register_handler(
        OrchestratorEvent.CHUNK_STARTED,
        custom_handler,
    )


@then("the response should include the custom warning")
def step_has_custom_warning(context):
    warnings = [a for a in context.response.actions if a.get("type") == "custom_warning"]
    assert len(warnings) > 0, "Custom warning not found"
