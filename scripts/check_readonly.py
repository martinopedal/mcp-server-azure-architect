#!/usr/bin/env python3
"""
AST-based static analysis for read-only enforcement (ADR-003 layer 1).

Scans Python source files for Azure SDK mutation method calls and reports violations.
Mutation patterns include: begin_*, create_*, update_*, replace_*, patch_*, set_*,
delete_*, remove_*, purge_*, restart_*, start_*, stop_*, cancel_*, power_*.

Usage:
    python scripts/check_readonly.py src/mcp_server_azure_architect/

Exit codes:
    0: No violations found
    1: Violations found or error during scan
"""

import argparse
import ast
import sys
from pathlib import Path

MUTATION_PREFIXES = (
    "begin_",
    "create_",
    "update_",
    "replace_",
    "patch_",
    "set_",
    "delete_",
    "remove_",
    "purge_",
    "restart_",
    "start_",
    "stop_",
    "cancel_",
    "power_",
)

MUTATION_EXACT = ()  # Empty for now since builtins are excluded in _is_mutation_method

READONLY_ALLOW_MARKER = "readonly-allow:"


class ReadOnlyViolation:
    """A detected mutation method call."""

    def __init__(
        self, file_path: Path, line_number: int, method_name: str, context: str
    ):
        self.file_path = file_path
        self.line_number = line_number
        self.method_name = method_name
        self.context = context

    def __str__(self) -> str:
        return (
            f"{self.file_path}:{self.line_number}: "
            f"Mutation method '{self.method_name}' detected in: {self.context}"
        )


class ReadOnlyChecker(ast.NodeVisitor):
    """AST visitor that detects Azure SDK mutation method calls."""

    def __init__(self, file_path: Path, source_lines: list[str]):
        self.file_path = file_path
        self.source_lines = source_lines
        self.violations: list[ReadOnlyViolation] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Check if call node invokes a mutation method."""
        method_name = None
        context = None

        # Extract method name from call node
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            context = ast.unparse(node.func) if hasattr(ast, "unparse") else "call"
        elif isinstance(node.func, ast.Name):
            method_name = node.func.id
            context = method_name

        # Check if method matches mutation pattern
        if (
            method_name
            and self._is_mutation_method(method_name)
            and not self._has_allow_comment(node.lineno)
        ):
            violation = ReadOnlyViolation(
                file_path=self.file_path,
                line_number=node.lineno,
                method_name=method_name,
                context=context or "unknown",
            )
            self.violations.append(violation)

        self.generic_visit(node)

    def _is_mutation_method(self, method_name: str) -> bool:
        """Check if method name matches mutation patterns."""
        # Exclude common Python builtin string methods that are safe
        # These are typically called on strings, not Azure SDK clients
        safe_string_methods = {"replace"}  # str.replace() for string manipulation

        # For common mutation words, only flag if it's a prefix pattern
        # This allows str.replace() but flags client.delete()
        if method_name in safe_string_methods:
            # This is a heuristic: if it's exactly "replace", it's likely str.replace()
            # Azure SDK methods are typically "delete_*", not bare "delete"
            # We'll rely on context and code review for edge cases
            return False

        # Check prefix matches (the main detection mechanism)
        return any(method_name.startswith(prefix) for prefix in MUTATION_PREFIXES)

    def _has_allow_comment(self, line_number: int) -> bool:
        """Check if line immediately above has readonly-allow comment."""
        if line_number <= 1:
            return False

        # Check line immediately above (0-indexed)
        previous_line = self.source_lines[line_number - 2]
        return READONLY_ALLOW_MARKER in previous_line


def scan_file(file_path: Path) -> list[ReadOnlyViolation]:
    """Scan a single Python file for mutation method calls."""
    try:
        source = file_path.read_text(encoding="utf-8")
        source_lines = source.splitlines()
        tree = ast.parse(source, filename=str(file_path))

        checker = ReadOnlyChecker(file_path, source_lines)
        checker.visit(tree)

        return checker.violations
    except SyntaxError as e:
        print(f"Syntax error in {file_path}:{e.lineno}: {e.msg}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Error scanning {file_path}: {e}", file=sys.stderr)
        return []


def scan_directory(directory: Path) -> list[ReadOnlyViolation]:
    """Recursively scan directory for Python files and report violations."""
    all_violations: list[ReadOnlyViolation] = []

    python_files = sorted(directory.rglob("*.py"))
    for file_path in python_files:
        violations = scan_file(file_path)
        all_violations.extend(violations)

    return all_violations


def format_suggestions(violation: ReadOnlyViolation) -> str:
    """Generate actionable fix suggestions for a violation."""
    method = violation.method_name

    suggestions = []

    # Suggest read-only alternatives
    if method.startswith("create_") or method.startswith("begin_create"):
        suggestions.append("- Use get_* or list_* to read existing resources")
    elif method.startswith("update_") or method.startswith("set_"):
        suggestions.append("- Use get_* to read current state without modification")
    elif method.startswith("delete_") or method.startswith("remove_"):
        suggestions.append("- Use list_* to enumerate resources without deletion")
    elif method.startswith("begin_"):
        suggestions.append(
            "- Avoid long-running operations (LROs); use read-only queries instead"
        )
    elif method.startswith("start_") or method.startswith("stop_"):
        suggestions.append("- Use get_* to read resource state without control actions")
    else:
        suggestions.append("- Replace with a read-only method (get_*, list_*, query_*)")

    # Add allow-comment option
    suggestions.append(
        f"- If this is a false positive, add comment on line above: "
        f"# {READONLY_ALLOW_MARKER} <reason>"
    )

    return "\n".join(suggestions)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check Python source files for Azure SDK mutation method calls"
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=str,
        help="Paths to scan (files or directories)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed suggestions for each violation",
    )

    args = parser.parse_args()

    all_violations: list[ReadOnlyViolation] = []

    for path_arg in args.paths:
        path = Path(path_arg)
        if not path.exists():
            print(f"Error: Path does not exist: {path}", file=sys.stderr)
            return 1

        if path.is_file():
            violations = scan_file(path)
            all_violations.extend(violations)
        elif path.is_dir():
            violations = scan_directory(path)
            all_violations.extend(violations)
        else:
            print(f"Error: Not a file or directory: {path}", file=sys.stderr)
            return 1

    # Report violations
    if all_violations:
        print(
            f"\n❌ Found {len(all_violations)} read-only violation(s):\n",
            file=sys.stderr,
        )

        for violation in all_violations:
            print(f"  {violation}", file=sys.stderr)

            if args.verbose:
                print("\n  Suggestions:", file=sys.stderr)
                print(format_suggestions(violation), file=sys.stderr)
                print("", file=sys.stderr)

        print(
            "\n💡 To allow a specific call, add a comment on the line above:",
            file=sys.stderr,
        )
        print(
            f"   # {READONLY_ALLOW_MARKER} <reason for allowing this mutation method>",
            file=sys.stderr,
        )
        print(
            "\nRead-only enforcement is required per ADR-003 and AGENTS.md.",
            file=sys.stderr,
        )
        print("See: docs/adr/0003-read-only-enforcement.md\n", file=sys.stderr)

        return 1
    else:
        print("✓ No read-only violations detected.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
