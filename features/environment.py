"""
Behave environment configuration for Graph of Thought BDD tests.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def before_all(context):
    """Set up test fixtures available to all scenarios."""
    from graph_of_thought import GraphOfThought

    # Simple evaluator for testing
    def simple_evaluator(thought: str) -> float:
        keywords = {"good": 0.3, "better": 0.5, "best": 0.8, "optimal": 1.0}
        return sum(v for k, v in keywords.items() if k in thought.lower())

    # Simple generator for testing
    def simple_generator(parent: str) -> list[str]:
        return [f"{parent} -> good", f"{parent} -> better", f"{parent} -> best"]

    context.simple_evaluator = simple_evaluator
    context.simple_generator = simple_generator

    def create_test_graph():
        return GraphOfThought[str](
            evaluator=simple_evaluator,
            generator=simple_generator,
            max_depth=5,
            beam_width=3,
        )

    context.create_test_graph = create_test_graph


def before_scenario(context, scenario):
    """Reset context before each scenario."""
    context.graph = None
    context.thoughts = {}
    context.edges = {}
    context.result = None
    context.exception = None
    context.graph_config = None  # Renamed from 'config' to avoid behave conflict
    context.persistence = None
    context.metrics = None
    context.restored_graph = None
    context.json_str = None
    context.loaded = None
    context.loaded_thoughts = None
    context.loaded_edges = None
    context.loaded_root_ids = None
    context.loaded_metadata = None
    context.loaded_search_state = None
    context.deleted = None
    context.config_dict = None
    context.validation_issues = None
    context.restored_config = None
    context.last_expanded = None
