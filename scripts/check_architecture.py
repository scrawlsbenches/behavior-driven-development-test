#!/usr/bin/env python3
"""
Architecture Enforcement Script

Fast checks that run in CI before the full test suite.
Catches common violations that would otherwise slip through.

Usage:
    python scripts/check_architecture.py

Exit codes:
    0 - All checks passed
    1 - Violations found

Add to CI:
    - name: Check Architecture
      run: python scripts/check_architecture.py
"""

import ast
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Callable


@dataclass
class Violation:
    """A single architecture violation."""
    rule: str
    file: Path
    line: int | None
    message: str


class ArchitectureChecker:
    """Checks codebase for architecture violations."""

    def __init__(self, project_root: Path):
        self.root = project_root
        self.violations: list[Violation] = []

    def check_all(self) -> list[Violation]:
        """Run all architecture checks."""
        self.violations = []

        # Run each check
        self._check_protocols_in_correct_location()
        self._check_implementations_in_correct_location()
        self._check_no_global_service_instances()
        self._check_no_service_instantiation_outside_factories()
        self._check_imports_use_protocols_not_implementations()

        return self.violations

    def _check_protocols_in_correct_location(self):
        """Protocols must be defined in protocols.py only."""
        services_dir = self.root / "graph_of_thought" / "services"
        if not services_dir.exists():
            return

        for py_file in services_dir.glob("*.py"):
            if py_file.name == "protocols.py":
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        base_name = self._get_name(base)
                        if base_name == "Protocol":
                            self.violations.append(Violation(
                                rule="PROTOCOL_LOCATION",
                                file=py_file,
                                line=node.lineno,
                                message=f"Protocol '{node.name}' must be defined in protocols.py, not {py_file.name}",
                            ))

    def _check_implementations_in_correct_location(self):
        """Service implementations must be in implementations.py."""
        services_dir = self.root / "graph_of_thought" / "services"
        if not services_dir.exists():
            return

        for py_file in services_dir.glob("*.py"):
            if py_file.name in ("implementations.py", "protocols.py", "__init__.py", "orchestrator.py"):
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    name = node.name
                    # Check for service implementation naming patterns
                    if self._looks_like_service_impl(name):
                        self.violations.append(Violation(
                            rule="IMPL_LOCATION",
                            file=py_file,
                            line=node.lineno,
                            message=f"Service implementation '{name}' must be in implementations.py, not {py_file.name}",
                        ))

    def _check_no_global_service_instances(self):
        """No module-level service instantiation."""
        services_dir = self.root / "graph_of_thought" / "services"
        if not services_dir.exists():
            return

        for py_file in services_dir.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)
            except SyntaxError:
                continue

            # Only check module-level statements
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    if isinstance(node.value, ast.Call):
                        func_name = self._get_name(node.value.func)
                        if func_name and "Service" in func_name:
                            var_names = [self._get_name(t) for t in node.targets]
                            self.violations.append(Violation(
                                rule="GLOBAL_SERVICE",
                                file=py_file,
                                line=node.lineno,
                                message=f"Global service instance: {var_names} = {func_name}(). Use DI instead.",
                            ))

    def _check_no_service_instantiation_outside_factories(self):
        """
        Services should only be instantiated in:
        - __init__ (as default values)
        - Factory methods (from_registry, create_simple, etc.)
        - Test files
        """
        graph_dir = self.root / "graph_of_thought"
        if not graph_dir.exists():
            return

        allowed_files = {"implementations.py", "orchestrator.py"}
        allowed_methods = {"__init__", "from_registry", "create_simple", "create_default"}
        allowed_dirs = {"examples", "tests"}  # Composition roots are allowed

        for py_file in graph_dir.rglob("*.py"):
            if py_file.name in allowed_files:
                continue
            if "test" in py_file.name.lower():
                continue
            if any(d in py_file.parts for d in allowed_dirs):
                continue  # Examples and tests can wire things up

            try:
                content = py_file.read_text()
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name in allowed_methods:
                        continue

                    # Check function body for service instantiation
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Call):
                            func_name = self._get_name(subnode.func)
                            if func_name and self._looks_like_service_impl(func_name):
                                self.violations.append(Violation(
                                    rule="DIRECT_INSTANTIATION",
                                    file=py_file,
                                    line=subnode.lineno,
                                    message=f"Direct service instantiation in {node.name}(): {func_name}(). Inject via constructor.",
                                ))

    def _check_imports_use_protocols_not_implementations(self):
        """
        Business logic should import protocols, not implementations.

        Implementations should only be imported in:
        - Factory/composition code
        - Tests
        - __init__.py for re-export
        """
        graph_dir = self.root / "graph_of_thought"
        if not graph_dir.exists():
            return

        # Files that are allowed to import implementations
        allowed_to_import_impls = {
            "orchestrator.py",  # Factory code
            "__init__.py",      # Re-exports
            "implementations.py",  # Self
        }

        for py_file in graph_dir.rglob("*.py"):
            if py_file.name in allowed_to_import_impls:
                continue
            if "test" in str(py_file).lower():
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and "implementations" in node.module:
                        imported = [alias.name for alias in node.names]
                        # Allow importing base classes or utilities
                        service_imports = [n for n in imported if "Service" in n]
                        if service_imports:
                            self.violations.append(Violation(
                                rule="IMPL_IMPORT",
                                file=py_file,
                                line=node.lineno,
                                message=f"Import from implementations in business logic: {service_imports}. Import protocols instead.",
                            ))

    def _get_name(self, node: ast.AST | None) -> str | None:
        """Extract name from various AST node types."""
        if node is None:
            return None
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _looks_like_service_impl(self, name: str | None) -> bool:
        """Check if a name looks like a service implementation."""
        if not name:
            return False
        prefixes = ("InMemory", "Simple", "Mock", "Fake", "Stub")
        return any(name.startswith(p) for p in prefixes) and "Service" in name


def main():
    """Run architecture checks and report violations."""
    project_root = Path(__file__).parent.parent

    print("=" * 60)
    print("Architecture Check")
    print("=" * 60)
    print()

    checker = ArchitectureChecker(project_root)
    violations = checker.check_all()

    if not violations:
        print("All architecture checks passed.")
        print()
        print("Rules enforced:")
        print("  - Protocols defined in protocols.py only")
        print("  - Implementations defined in implementations.py only")
        print("  - No global service instances")
        print("  - No direct service instantiation outside factories")
        print("  - Business logic imports protocols, not implementations")
        return 0

    # Group violations by rule
    by_rule: dict[str, list[Violation]] = {}
    for v in violations:
        by_rule.setdefault(v.rule, []).append(v)

    print(f"Found {len(violations)} architecture violation(s):")
    print()

    for rule, rule_violations in by_rule.items():
        print(f"[{rule}] ({len(rule_violations)} violation(s))")
        for v in rule_violations:
            rel_path = v.file.relative_to(project_root)
            line_info = f":{v.line}" if v.line else ""
            print(f"  {rel_path}{line_info}")
            print(f"    {v.message}")
        print()

    print("-" * 60)
    print("Fix these violations before merging.")
    print()
    print("If you believe a violation is a false positive, either:")
    print("  1. Add the file to the allowed list in check_architecture.py")
    print("  2. Discuss with the team to update the architecture rules")
    print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
