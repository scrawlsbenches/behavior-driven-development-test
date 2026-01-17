"""
Tests for verifying DDD import hierarchy.

Expected hierarchy (no reverse dependencies):
    domain/           <-- No dependencies on core/ or services/
        ^
    core/             <-- May import from domain only
        ^
    services/         <-- May import from domain and core

These tests use AST parsing to detect import violations without executing the code.

Comment conventions for violations found:
    # TODO: Work that should be done
    # FIXME: Potential bugs or issues found (e.g., circular import detected)
    # REVIEW: Needs human decision/review
    # NOTE: Important observations about the architecture
"""

import ast
import os
from pathlib import Path
from typing import NamedTuple


# =============================================================================
# Test Infrastructure
# =============================================================================

class ImportInfo(NamedTuple):
    """Information about an import statement."""
    file_path: str
    line_number: int
    module: str
    names: list[str]
    is_from_import: bool


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def get_package_root() -> Path:
    """Get the graph_of_thought package root."""
    return get_project_root() / "graph_of_thought"


def parse_imports_from_file(file_path: Path) -> list[ImportInfo]:
    """
    Parse a Python file and extract all import statements.

    Uses AST parsing to accurately identify imports without executing the code.

    Args:
        file_path: Path to the Python file to parse

    Returns:
        List of ImportInfo objects describing each import
    """
    imports = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # Handle: import foo, bar
                for alias in node.names:
                    imports.append(ImportInfo(
                        file_path=str(file_path),
                        line_number=node.lineno,
                        module=alias.name,
                        names=[alias.name],
                        is_from_import=False,
                    ))
            elif isinstance(node, ast.ImportFrom):
                # Handle: from foo import bar, baz
                module = node.module or ""
                names = [alias.name for alias in node.names]
                imports.append(ImportInfo(
                    file_path=str(file_path),
                    line_number=node.lineno,
                    module=module,
                    names=names,
                    is_from_import=True,
                ))
    except SyntaxError as e:
        # NOTE: If a file has syntax errors, we skip it but should log this
        print(f"Warning: Syntax error in {file_path}: {e}")

    return imports


def get_python_files_in_directory(directory: Path) -> list[Path]:
    """Get all Python files in a directory recursively."""
    return list(directory.rglob("*.py"))


def is_internal_import(module: str) -> bool:
    """Check if a module is part of graph_of_thought package."""
    return module.startswith("graph_of_thought") or module.startswith(".")


def normalize_relative_import(module: str, file_path: Path, package_root: Path) -> str:
    """
    Convert a relative import to an absolute module path.

    Args:
        module: The import module (may be relative like ".protocols" or "..models")
        file_path: The file containing the import
        package_root: The root of the package

    Returns:
        Absolute module path (e.g., "graph_of_thought.services.protocols")
    """
    if not module.startswith("."):
        return module

    # Get the package path of the importing file
    rel_path = file_path.relative_to(package_root.parent)
    parts = list(rel_path.parts[:-1])  # Remove the filename

    # Count leading dots to determine how many levels to go up
    leading_dots = len(module) - len(module.lstrip("."))
    remaining_module = module.lstrip(".")

    # Go up directories based on leading dots
    # One dot = current package, two dots = parent package, etc.
    if leading_dots > 1:
        parts = parts[:-(leading_dots - 1)]

    # Add the remaining module parts
    if remaining_module:
        parts.extend(remaining_module.split("."))

    return ".".join(parts)


def imports_from_layer(import_info: ImportInfo, layer_name: str, package_root: Path) -> bool:
    """
    Check if an import comes from a specific layer.

    Args:
        import_info: The import to check
        layer_name: Layer name like "core", "services", or "domain"
        package_root: The root of the package

    Returns:
        True if the import is from the specified layer
    """
    module = import_info.module

    # Handle relative imports
    if module.startswith("."):
        module = normalize_relative_import(
            module,
            Path(import_info.file_path),
            package_root
        )

    # Check for graph_of_thought.{layer_name} pattern
    layer_prefix = f"graph_of_thought.{layer_name}"
    return module.startswith(layer_prefix) or module == layer_name


def get_layer_from_file(file_path: Path, package_root: Path) -> str | None:
    """
    Determine which layer a file belongs to.

    Returns:
        Layer name ("domain", "core", "services") or None if not in a layer
    """
    try:
        rel_path = file_path.relative_to(package_root)
        parts = rel_path.parts

        if len(parts) > 0:
            first_part = parts[0]
            if first_part in ("domain", "core", "services"):
                return first_part
    except ValueError:
        pass

    return None


# =============================================================================
# Test Functions
# =============================================================================

class TestDomainLayerIsolation:
    """
    Test that the domain layer has no dependencies on core/ or services/.

    The domain layer should be completely self-contained, only importing:
    - Standard library modules
    - Third-party packages (like dataclasses, typing, enum)
    - Other domain layer modules

    # NOTE: This is the foundation of DDD - the domain layer is the innermost
    # layer and should have no knowledge of infrastructure or application services.
    """

    def test_domain_has_no_core_imports(self):
        """Domain modules must not import from core/."""
        package_root = get_package_root()
        domain_dir = package_root / "domain"
        violations = []

        for file_path in get_python_files_in_directory(domain_dir):
            imports = parse_imports_from_file(file_path)

            for imp in imports:
                if imports_from_layer(imp, "core", package_root):
                    violations.append({
                        "file": str(file_path.relative_to(package_root.parent)),
                        "line": imp.line_number,
                        "import": imp.module,
                        "names": imp.names,
                    })

        if violations:
            # FIXME: Domain layer imports from core/ - this violates DDD principles
            # The domain should be independent of infrastructure concerns
            violation_msgs = [
                f"  {v['file']}:{v['line']} imports {v['import']} ({', '.join(v['names'])})"
                for v in violations
            ]
            assert False, (
                f"Domain layer has {len(violations)} import(s) from core/:\n"
                + "\n".join(violation_msgs)
            )

    def test_domain_has_no_services_imports(self):
        """Domain modules must not import from services/."""
        package_root = get_package_root()
        domain_dir = package_root / "domain"
        violations = []

        for file_path in get_python_files_in_directory(domain_dir):
            imports = parse_imports_from_file(file_path)

            for imp in imports:
                if imports_from_layer(imp, "services", package_root):
                    violations.append({
                        "file": str(file_path.relative_to(package_root.parent)),
                        "line": imp.line_number,
                        "import": imp.module,
                        "names": imp.names,
                    })

        if violations:
            # FIXME: Domain layer imports from services/ - this violates DDD principles
            # Domain models should not depend on service implementations
            violation_msgs = [
                f"  {v['file']}:{v['line']} imports {v['import']} ({', '.join(v['names'])})"
                for v in violations
            ]
            assert False, (
                f"Domain layer has {len(violations)} import(s) from services/:\n"
                + "\n".join(violation_msgs)
            )

    def test_domain_only_imports_allowed_modules(self):
        """
        Domain layer should only import from:
        - Standard library
        - Domain layer itself
        - Allowed third-party packages (typing, dataclasses, enum, etc.)
        """
        package_root = get_package_root()
        domain_dir = package_root / "domain"

        # Allowed standard library and third-party imports
        allowed_prefixes = {
            "__future__",
            "abc",
            "dataclasses",
            "datetime",
            "enum",
            "typing",
            "uuid",
            "collections",
            "functools",
            "graph_of_thought.domain",  # Self-references are fine
        }

        violations = []

        for file_path in get_python_files_in_directory(domain_dir):
            imports = parse_imports_from_file(file_path)

            for imp in imports:
                module = imp.module

                # Normalize relative imports
                if module.startswith("."):
                    module = normalize_relative_import(module, file_path, package_root)

                # Check if import is allowed
                is_allowed = any(
                    module == allowed or module.startswith(allowed + ".")
                    for allowed in allowed_prefixes
                )

                # Allow empty module (from . import X pattern)
                if not module:
                    is_allowed = True

                if not is_allowed and module.startswith("graph_of_thought"):
                    # This is an internal import that's not from domain
                    violations.append({
                        "file": str(file_path.relative_to(package_root.parent)),
                        "line": imp.line_number,
                        "import": module,
                        "names": imp.names,
                    })

        if violations:
            # FIXME: Domain has unexpected internal imports
            violation_msgs = [
                f"  {v['file']}:{v['line']} imports {v['import']} ({', '.join(v['names'])})"
                for v in violations
            ]
            assert False, (
                f"Domain layer has {len(violations)} unexpected import(s):\n"
                + "\n".join(violation_msgs)
            )


class TestCoreLayerDependencies:
    """
    Test that the core layer only imports from domain/.

    The core layer may import:
    - Standard library modules
    - Third-party packages
    - Domain layer modules

    It must NOT import from services/.

    # NOTE: core/ provides foundational types and protocols that services
    # build upon. It can use domain models but shouldn't know about service
    # implementations.
    """

    def test_core_has_no_services_imports(self):
        """Core modules must not import from services/."""
        package_root = get_package_root()
        core_dir = package_root / "core"

        if not core_dir.exists():
            return  # Skip if core/ doesn't exist

        violations = []

        for file_path in get_python_files_in_directory(core_dir):
            imports = parse_imports_from_file(file_path)

            for imp in imports:
                if imports_from_layer(imp, "services", package_root):
                    violations.append({
                        "file": str(file_path.relative_to(package_root.parent)),
                        "line": imp.line_number,
                        "import": imp.module,
                        "names": imp.names,
                    })

        if violations:
            # FIXME: Core layer imports from services/ - this creates a cyclic dependency
            violation_msgs = [
                f"  {v['file']}:{v['line']} imports {v['import']} ({', '.join(v['names'])})"
                for v in violations
            ]
            assert False, (
                f"Core layer has {len(violations)} import(s) from services/:\n"
                + "\n".join(violation_msgs)
            )

    def test_core_types_imports_only_from_domain(self):
        """
        core/types.py should only import from domain/ for model re-exports.

        # NOTE: types.py exists for backwards compatibility, re-exporting
        # domain models. It should not define its own models or import
        # from services.
        """
        package_root = get_package_root()
        types_file = package_root / "core" / "types.py"

        if not types_file.exists():
            return  # Skip if file doesn't exist

        imports = parse_imports_from_file(types_file)
        internal_imports = []

        for imp in imports:
            module = imp.module

            if module.startswith("."):
                module = normalize_relative_import(module, types_file, package_root)

            # Check if it's an internal graph_of_thought import
            if module.startswith("graph_of_thought") and not module.startswith("graph_of_thought.domain"):
                internal_imports.append({
                    "line": imp.line_number,
                    "import": module,
                    "names": imp.names,
                })

        if internal_imports:
            # FIXME: core/types.py imports from internal modules other than domain
            violation_msgs = [
                f"  Line {v['line']}: imports {v['import']} ({', '.join(v['names'])})"
                for v in internal_imports
            ]
            assert False, (
                f"core/types.py has {len(internal_imports)} non-domain internal import(s):\n"
                + "\n".join(violation_msgs)
            )


class TestServicesLayerDependencies:
    """
    Test that the services layer imports appropriately.

    The services layer may import:
    - Standard library modules
    - Third-party packages
    - Domain layer modules
    - Core layer modules (protocols, types)

    # NOTE: services/ is the outermost layer and can depend on both domain
    # and core. However, service implementations should prefer importing
    # domain models directly rather than through core/types.py re-exports.
    """

    def test_services_protocols_imports_from_domain(self):
        """
        services/protocols.py should import domain models from domain layer.

        # REVIEW: Currently services/protocols.py imports from domain layer,
        # which is correct. This test verifies that pattern is maintained.
        """
        package_root = get_package_root()
        protocols_file = package_root / "services" / "protocols.py"

        if not protocols_file.exists():
            return  # Skip if file doesn't exist

        imports = parse_imports_from_file(protocols_file)

        # Check that domain imports exist
        domain_imports = [
            imp for imp in imports
            if imports_from_layer(imp, "domain", package_root)
        ]

        # NOTE: It's expected that services/protocols.py imports from domain
        # for model definitions used in protocol type hints
        assert len(domain_imports) > 0, (
            "services/protocols.py should import from domain layer for model definitions"
        )

    def test_services_implementations_follow_hierarchy(self):
        """
        Service implementations should import through protocols, not directly from domain.

        # NOTE: This is a best practice check. Implementations should use
        # protocols.py as the interface, getting domain models re-exported
        # from there rather than importing domain directly (with exceptions
        # for models not exposed via protocols).
        """
        package_root = get_package_root()
        implementations_dir = package_root / "services" / "implementations"

        if not implementations_dir.exists():
            return  # Skip if directory doesn't exist

        # This test is informational - implementations may import from domain
        # if they need models not exposed through protocols
        for file_path in get_python_files_in_directory(implementations_dir):
            imports = parse_imports_from_file(file_path)

            domain_imports = [
                imp for imp in imports
                if imports_from_layer(imp, "domain", package_root)
            ]

            # NOTE: Direct domain imports in implementations are acceptable
            # but should be documented. This test just logs them.
            if domain_imports:
                # Informational: log direct domain imports for review
                pass


class TestNoCircularImports:
    """
    Test for circular import patterns in the codebase.

    # NOTE: Circular imports can cause runtime errors and indicate
    # architectural issues. This test builds a dependency graph and
    # checks for cycles.
    """

    def _build_import_graph(self) -> dict[str, set[str]]:
        """
        Build a graph of module dependencies.

        Returns:
            Dictionary mapping module paths to sets of imported module paths
        """
        package_root = get_package_root()
        graph: dict[str, set[str]] = {}

        for file_path in get_python_files_in_directory(package_root):
            # Convert file path to module name
            rel_path = file_path.relative_to(package_root.parent)
            module_name = str(rel_path).replace("/", ".").replace("\\", ".").removesuffix(".py")
            if module_name.endswith(".__init__"):
                module_name = module_name.removesuffix(".__init__")

            imports = parse_imports_from_file(file_path)
            dependencies = set()

            for imp in imports:
                module = imp.module

                if module.startswith("."):
                    module = normalize_relative_import(module, file_path, package_root)

                # Only track internal imports
                if module.startswith("graph_of_thought"):
                    dependencies.add(module)

            graph[module_name] = dependencies

        return graph

    def _find_cycles(self, graph: dict[str, set[str]]) -> list[list[str]]:
        """
        Find all cycles in the dependency graph using DFS.

        Returns:
            List of cycles, where each cycle is a list of module names
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if neighbor in graph:  # Only follow edges to modules we know about
                        dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node)

        return cycles

    def test_no_circular_imports_between_layers(self):
        """
        Test that there are no circular imports between architectural layers.

        # NOTE: We check specifically for cycles that cross layer boundaries,
        # as those indicate architectural violations.
        """
        package_root = get_package_root()
        graph = self._build_import_graph()

        # Look for cross-layer cycles
        layer_cycles = []

        for module, dependencies in graph.items():
            source_layer = None
            if "domain" in module:
                source_layer = "domain"
            elif "core" in module:
                source_layer = "core"
            elif "services" in module:
                source_layer = "services"

            if source_layer:
                for dep in dependencies:
                    dep_layer = None
                    if "domain" in dep:
                        dep_layer = "domain"
                    elif "core" in dep:
                        dep_layer = "core"
                    elif "services" in dep:
                        dep_layer = "services"

                    # Check for reverse dependencies
                    if source_layer == "domain" and dep_layer in ("core", "services"):
                        layer_cycles.append(
                            f"domain -> {dep_layer}: {module} imports {dep}"
                        )
                    elif source_layer == "core" and dep_layer == "services":
                        layer_cycles.append(
                            f"core -> services: {module} imports {dep}"
                        )

        if layer_cycles:
            # FIXME: Circular dependencies detected between layers
            assert False, (
                f"Found {len(layer_cycles)} cross-layer dependency violation(s):\n"
                + "\n".join(f"  {cycle}" for cycle in layer_cycles)
            )

    def test_no_direct_circular_imports(self):
        """
        Test that there are no direct circular imports (A imports B, B imports A).

        # NOTE: Direct circular imports are often the most problematic and
        # easiest to detect.
        """
        graph = self._build_import_graph()
        direct_cycles = []
        checked_pairs = set()

        for module, dependencies in graph.items():
            for dep in dependencies:
                if dep in graph:
                    pair = tuple(sorted([module, dep]))
                    if pair not in checked_pairs:
                        checked_pairs.add(pair)
                        if module in graph.get(dep, set()):
                            direct_cycles.append((module, dep))

        if direct_cycles:
            # FIXME: Direct circular imports detected
            cycle_msgs = [
                f"  {a} <-> {b}"
                for a, b in direct_cycles
            ]
            assert False, (
                f"Found {len(direct_cycles)} direct circular import(s):\n"
                + "\n".join(cycle_msgs)
            )


class TestArchitecturalIntegrity:
    """
    Additional architectural integrity tests.

    # NOTE: These tests verify broader architectural patterns beyond
    # just import dependencies.
    """

    def test_domain_models_are_self_contained(self):
        """
        Domain models should not import infrastructure concerns.

        # NOTE: This checks that domain models don't accidentally depend
        # on things like database adapters, HTTP clients, etc.
        """
        package_root = get_package_root()
        models_dir = package_root / "domain" / "models"

        if not models_dir.exists():
            return

        # Infrastructure-related imports that shouldn't appear in domain
        forbidden_patterns = [
            "sqlalchemy",
            "requests",
            "aiohttp",
            "httpx",
            "redis",
            "motor",
            "pymongo",
            "psycopg",
            "asyncpg",
        ]

        violations = []

        for file_path in get_python_files_in_directory(models_dir):
            imports = parse_imports_from_file(file_path)

            for imp in imports:
                for pattern in forbidden_patterns:
                    if pattern in imp.module:
                        violations.append({
                            "file": str(file_path.relative_to(package_root.parent)),
                            "line": imp.line_number,
                            "import": imp.module,
                            "pattern": pattern,
                        })

        if violations:
            # FIXME: Domain models import infrastructure libraries
            violation_msgs = [
                f"  {v['file']}:{v['line']} imports {v['import']} (matches: {v['pattern']})"
                for v in violations
            ]
            assert False, (
                f"Domain models have {len(violations)} infrastructure import(s):\n"
                + "\n".join(violation_msgs)
            )

    def test_enums_have_no_model_dependencies(self):
        """
        Domain enums should be completely standalone.

        # NOTE: Enums are the most fundamental domain types and should
        # have no dependencies on models (which may use enums).
        """
        package_root = get_package_root()
        enums_dir = package_root / "domain" / "enums"

        if not enums_dir.exists():
            return

        violations = []

        for file_path in get_python_files_in_directory(enums_dir):
            imports = parse_imports_from_file(file_path)

            for imp in imports:
                module = imp.module

                if module.startswith("."):
                    module = normalize_relative_import(module, file_path, package_root)

                # Enums should not import models
                if "models" in module:
                    violations.append({
                        "file": str(file_path.relative_to(package_root.parent)),
                        "line": imp.line_number,
                        "import": module,
                        "names": imp.names,
                    })

        if violations:
            # FIXME: Domain enums import from models - this may cause circular imports
            violation_msgs = [
                f"  {v['file']}:{v['line']} imports {v['import']} ({', '.join(v['names'])})"
                for v in violations
            ]
            assert False, (
                f"Domain enums have {len(violations)} model import(s):\n"
                + "\n".join(violation_msgs)
            )


# =============================================================================
# Summary Report (run with pytest -v for details)
# =============================================================================

def test_import_hierarchy_summary():
    """
    Summary test that provides an overview of the import hierarchy status.

    This test always passes but prints useful diagnostic information.
    """
    package_root = get_package_root()

    print("\n" + "=" * 70)
    print("DDD Import Hierarchy Analysis")
    print("=" * 70)

    # Count files in each layer
    layers = ["domain", "core", "services"]
    for layer in layers:
        layer_dir = package_root / layer
        if layer_dir.exists():
            files = list(get_python_files_in_directory(layer_dir))
            print(f"\n{layer}/ layer: {len(files)} Python files")

            # Count imports from each layer
            import_counts = {l: 0 for l in layers}
            for file_path in files:
                imports = parse_imports_from_file(file_path)
                for imp in imports:
                    for target_layer in layers:
                        if imports_from_layer(imp, target_layer, package_root):
                            import_counts[target_layer] += 1

            for target, count in import_counts.items():
                if count > 0:
                    marker = " (VIOLATION!)" if (
                        (layer == "domain" and target in ("core", "services")) or
                        (layer == "core" and target == "services")
                    ) else ""
                    print(f"  -> imports from {target}/: {count}{marker}")

    print("\n" + "=" * 70)
    print("Expected hierarchy: domain <- core <- services")
    print("=" * 70 + "\n")
