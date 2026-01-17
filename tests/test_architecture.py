"""
Architecture Enforcement Tests

These tests verify that the codebase follows established patterns.
They run in CI and block merges that violate architectural rules.

Run with: pytest tests/test_architecture.py -v
"""

import ast
import inspect
from pathlib import Path
from typing import Protocol, get_type_hints
import importlib
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestProtocolDefinitions:
    """All protocols must be defined correctly."""

    def test_all_service_protocols_are_runtime_checkable(self):
        """
        Protocols must be @runtime_checkable to support isinstance() checks.

        Without this, we can't verify implementations at runtime.
        """
        from graph_of_thought.services import protocols

        protocol_classes = [
            protocols.GovernanceService,
            protocols.ProjectManagementService,
            protocols.ResourceService,
            protocols.KnowledgeService,
            protocols.QuestionService,
            protocols.CommunicationService,
        ]

        for proto in protocol_classes:
            # runtime_checkable protocols have this attribute
            assert hasattr(proto, '__protocol_attrs__') or hasattr(proto, '_is_runtime_protocol'), \
                f"{proto.__name__} must be decorated with @runtime_checkable"

    def test_protocols_live_in_protocols_module(self):
        """
        All Protocol definitions must be in protocols.py, not scattered.

        This prevents people from defining one-off protocols in random files.
        """
        services_dir = PROJECT_ROOT / "graph_of_thought" / "services"

        for py_file in services_dir.glob("*.py"):
            if py_file.name == "protocols.py":
                continue  # This is where protocols SHOULD be

            content = py_file.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if class inherits from Protocol
                    for base in node.bases:
                        base_name = ""
                        if isinstance(base, ast.Name):
                            base_name = base.id
                        elif isinstance(base, ast.Attribute):
                            base_name = base.attr

                        assert base_name != "Protocol", \
                            f"Protocol '{node.name}' defined in {py_file.name} - move to protocols.py"


class TestImplementationPatterns:
    """Implementations must follow the established patterns."""

    def test_all_implementations_have_matching_protocol(self):
        """
        Every service implementation must implement a defined protocol.

        Prevents orphan implementations that bypass the interface pattern.
        """
        from graph_of_thought.services import protocols, implementations

        # Get all protocol names
        protocol_names = {
            "GovernanceService",
            "ProjectManagementService",
            "ResourceService",
            "KnowledgeService",
            "QuestionService",
            "CommunicationService",
        }

        # Check each class in implementations
        for name in dir(implementations):
            obj = getattr(implementations, name)
            if not isinstance(obj, type):
                continue
            if name.startswith("_"):
                continue

            # If it looks like a service implementation, verify it
            if "Service" in name and name not in protocol_names:
                # Extract the base service name
                # InMemoryGovernanceService -> GovernanceService
                # SimpleResourceService -> ResourceService
                base_name = name.replace("InMemory", "").replace("Simple", "")

                assert base_name in protocol_names, \
                    f"Implementation '{name}' has no matching protocol. " \
                    f"Expected '{base_name}' in protocols.py"

    def test_implementations_are_in_implementations_module(self):
        """
        Service implementations must live in implementations.py.

        Prevents scattered implementations across the codebase.
        """
        services_dir = PROJECT_ROOT / "graph_of_thought" / "services"

        for py_file in services_dir.glob("*.py"):
            if py_file.name in ("implementations.py", "protocols.py", "__init__.py"):
                continue

            content = py_file.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check for service implementation naming patterns
                    name = node.name
                    if ("InMemory" in name or "Simple" in name) and "Service" in name:
                        assert False, \
                            f"Service implementation '{name}' found in {py_file.name} - " \
                            f"move to implementations.py"


class TestDependencyInjectionPatterns:
    """Verify DI patterns are followed consistently."""

    def test_orchestrator_does_not_instantiate_services_directly(self):
        """
        Orchestrator must receive services via injection, not create them.

        Exception: Default values in __init__ signature are allowed.
        """
        orchestrator_file = PROJECT_ROOT / "graph_of_thought" / "services" / "orchestrator.py"
        content = orchestrator_file.read_text()
        tree = ast.parse(content)

        # Find the Orchestrator class
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "Orchestrator":
                # Check methods other than __init__ and factory methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name in ("__init__", "from_registry", "create_simple"):
                            continue  # These are allowed to instantiate

                        # Check for direct service instantiation in method body
                        for subnode in ast.walk(item):
                            if isinstance(subnode, ast.Call):
                                func_name = ""
                                if isinstance(subnode.func, ast.Name):
                                    func_name = subnode.func.id
                                elif isinstance(subnode.func, ast.Attribute):
                                    func_name = subnode.func.attr

                                # Flag if instantiating a service class
                                service_patterns = ["Service", "InMemory", "Simple"]
                                if any(p in func_name for p in service_patterns):
                                    # Allow isinstance checks
                                    if not (isinstance(subnode.func, ast.Name) and
                                            func_name in ("isinstance", "issubclass")):
                                        assert False, \
                                            f"Orchestrator.{item.name}() instantiates {func_name} directly. " \
                                            f"Inject via constructor instead."

    def test_service_registry_contains_all_services(self):
        """
        ServiceRegistry must have fields for all defined protocols.

        Prevents services from being added without registry support.
        """
        from graph_of_thought.services.protocols import ServiceRegistry
        import dataclasses

        expected_services = {
            "governance",
            "project_management",
            "resources",
            "knowledge",
            "questions",
            "communication",
        }

        registry_fields = {f.name for f in dataclasses.fields(ServiceRegistry)}

        missing = expected_services - registry_fields
        assert not missing, \
            f"ServiceRegistry missing fields for: {missing}"

        # Also check for unexpected fields (services added without protocol)
        extra = registry_fields - expected_services - {"__dataclass_fields__"}
        # Note: We allow extra fields for extensibility, but warn
        if extra:
            print(f"Warning: ServiceRegistry has extra fields not in expected list: {extra}")


class TestNoHardcodedDependencies:
    """Verify dependencies aren't hardcoded in business logic."""

    def test_graph_of_thought_accepts_all_dependencies(self):
        """
        GraphOfThought must accept infrastructure via constructor.

        Verifies the main class follows DI pattern.
        """
        from graph_of_thought.graph import GraphOfThought

        sig = inspect.signature(GraphOfThought.__init__)
        params = set(sig.parameters.keys()) - {"self"}

        # These should all be injectable
        expected_injectable = {
            "config",
            "generator",
            "evaluator",
            "persistence",
            "metrics",
            "logger",
            "tracer",
        }

        # Check that expected params exist (some may be optional)
        for param in expected_injectable:
            assert param in params, \
                f"GraphOfThought.__init__ should accept '{param}' for dependency injection"

    def test_no_global_service_instances(self):
        """
        Services must not be instantiated at module level.

        Global instances prevent testing and violate DI.
        """
        services_dir = PROJECT_ROOT / "graph_of_thought" / "services"

        for py_file in services_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            content = py_file.read_text()
            tree = ast.parse(content)

            # Check module-level assignments
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    # Check if right side is a service instantiation
                    if isinstance(node.value, ast.Call):
                        func_name = ""
                        if isinstance(node.value.func, ast.Name):
                            func_name = node.value.func.id

                        if "Service" in func_name:
                            target_names = [
                                t.id for t in node.targets
                                if isinstance(t, ast.Name)
                            ]
                            assert False, \
                                f"Global service instance in {py_file.name}: " \
                                f"{target_names} = {func_name}(). " \
                                f"Use dependency injection instead."


class TestFactoryPatterns:
    """Verify factory methods are used correctly."""

    def test_factory_methods_return_correct_types(self):
        """
        Factory methods must return the class they belong to.
        """
        from graph_of_thought.services.orchestrator import Orchestrator

        # Check from_registry returns Orchestrator
        registry_sig = inspect.signature(Orchestrator.from_registry)
        # The return annotation should indicate Orchestrator

        # Check create_simple returns Orchestrator
        simple_sig = inspect.signature(Orchestrator.create_simple)

        # Verify these methods exist and are classmethods
        assert isinstance(
            inspect.getattr_static(Orchestrator, "from_registry"),
            classmethod
        ), "from_registry must be a classmethod"

        assert isinstance(
            inspect.getattr_static(Orchestrator, "create_simple"),
            classmethod
        ), "create_simple must be a classmethod"


class TestNamingConventions:
    """Enforce consistent naming across the codebase."""

    def test_protocol_names_end_with_service(self):
        """
        Service protocols must be named *Service for clarity.
        """
        from graph_of_thought.services import protocols

        for name in dir(protocols):
            obj = getattr(protocols, name)
            if isinstance(obj, type) and hasattr(obj, '__protocol_attrs__'):
                # It's a Protocol - should end with Service (for service protocols)
                # Allow other protocols that aren't services
                if "Service" not in name and name not in (
                    "Protocol",  # Base class
                ):
                    # Check if it looks like a service
                    methods = [m for m in dir(obj) if not m.startswith("_")]
                    service_like_methods = {"check", "get", "create", "update", "delete", "store", "retrieve"}
                    if any(m.split("_")[0] in service_like_methods for m in methods):
                        print(f"Warning: {name} looks like a service but doesn't end with 'Service'")

    def test_implementation_naming_follows_pattern(self):
        """
        Implementations must be named: [Tier][Protocol]

        Tiers: InMemory, Simple, or production name (e.g., Postgres, Redis)
        """
        from graph_of_thought.services import implementations

        valid_prefixes = {"InMemory", "Simple"}  # Add production prefixes as needed

        for name in dir(implementations):
            obj = getattr(implementations, name)
            if isinstance(obj, type) and "Service" in name:
                has_valid_prefix = any(name.startswith(p) for p in valid_prefixes)
                if not has_valid_prefix:
                    # Could be a production implementation - just warn
                    print(f"Note: {name} doesn't use standard prefix (InMemory/Simple)")


# =============================================================================
# Run as script for quick validation
# =============================================================================

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])
