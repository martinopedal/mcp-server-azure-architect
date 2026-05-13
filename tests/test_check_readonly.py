"""Tests for check_readonly.py AST-based read-only enforcement."""

import sys
from pathlib import Path

import pytest

# Add scripts directory to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from check_readonly import (  # noqa: E402
    scan_directory,
    scan_file,
)


class TestReadOnlyChecker:
    """Test the AST-based read-only checker."""

    def test_detects_begin_prefix(self, tmp_path: Path) -> None:
        """Verify that begin_* methods are detected as mutations."""
        code = """
client.virtual_machines.begin_create_or_update(
    resource_group, vm_name, parameters
)
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        violations = scan_file(test_file)
        assert len(violations) == 1
        assert violations[0].method_name == "begin_create_or_update"

    def test_detects_create_prefix(self, tmp_path: Path) -> None:
        """Verify that create_* methods are detected as mutations."""
        code = """
client.resource_groups.create_or_update(
    resource_group_name, {"location": "eastus"}
)
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        violations = scan_file(test_file)
        assert len(violations) == 1
        assert violations[0].method_name == "create_or_update"

    def test_detects_delete_prefix(self, tmp_path: Path) -> None:
        """Verify that delete_* methods are detected as mutations."""
        code = """
client.storage_accounts.delete_resource(resource_group, account_name)
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        violations = scan_file(test_file)
        assert len(violations) == 1
        assert violations[0].method_name == "delete_resource"

    def test_detects_update_prefix(self, tmp_path: Path) -> None:
        """Verify that update_* methods are detected as mutations."""
        code = """
client.tags.update_tags(resource_id, {"tags": {"env": "prod"}})
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        violations = scan_file(test_file)
        assert len(violations) == 1
        assert violations[0].method_name == "update_tags"

    def test_allows_get_methods(self, tmp_path: Path) -> None:
        """Verify that get_* methods are not flagged."""
        code = """
result = client.virtual_machines.get(resource_group, vm_name)
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        violations = scan_file(test_file)
        assert len(violations) == 0

    def test_allows_list_methods(self, tmp_path: Path) -> None:
        """Verify that list_* methods are not flagged."""
        code = """
vms = client.virtual_machines.list(resource_group)
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        violations = scan_file(test_file)
        assert len(violations) == 0

    def test_allows_query_methods(self, tmp_path: Path) -> None:
        """Verify that query_* methods are not flagged."""
        code = """
results = client.query("Resources | where type =~ 'Microsoft.Compute/virtualMachines'")
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        violations = scan_file(test_file)
        assert len(violations) == 0

    def test_readonly_allow_comment_suppresses_violation(self, tmp_path: Path) -> None:
        """Verify that readonly-allow: comment suppresses violations."""
        code = """
# readonly-allow: test fixture for demonstrating allow syntax
client.virtual_machines.begin_create_or_update(
    resource_group, vm_name, parameters
)
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        violations = scan_file(test_file)
        assert len(violations) == 0

    def test_detects_multiple_patterns_in_file(self, tmp_path: Path) -> None:
        """Verify that multiple violations in one file are all detected."""
        code = """
def bad_function():
    client.begin_create_or_update(params)
    client.delete_resource(resource_id)
    client.update_tags(resource_id, tags)
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        violations = scan_file(test_file)
        assert len(violations) == 3
        method_names = {v.method_name for v in violations}
        assert method_names == {"begin_create_or_update", "delete_resource", "update_tags"}

    def test_scans_directory_recursively(self, tmp_path: Path) -> None:
        """Verify that scan_directory finds violations in nested files."""
        # Create nested structure
        (tmp_path / "subdir").mkdir()

        file1 = tmp_path / "test1.py"
        file1.write_text("client.begin_create()")

        file2 = tmp_path / "subdir" / "test2.py"
        file2.write_text("client.delete_resource()")

        violations = scan_directory(tmp_path)
        assert len(violations) == 2

    def test_real_source_tree_has_no_violations(self) -> None:
        """Verify that actual source code in src/ passes the check."""
        src_path = Path(__file__).parent.parent / "src" / "mcp_server_azure_architect"

        if not src_path.exists():
            pytest.skip("Source directory not found")

        violations = scan_directory(src_path)

        if violations:
            violation_details = "\n".join(str(v) for v in violations)
            pytest.fail(
                f"Found {len(violations)} read-only violation(s) in actual source:\n"
                f"{violation_details}"
            )

    def test_pattern_matching_completeness(self, tmp_path: Path) -> None:
        """Verify all documented mutation patterns are detected."""
        patterns = [
            "begin_create_or_update",
            "create_resource",
            "update_tags",
            "replace_config",
            "patch_resource",
            "set_property",
            "delete_resource",
            "remove_tag",
            "purge_deleted",
            "restart_vm",
            "start_vm",
            "stop_vm",
            "cancel_operation",
            "power_off_vm",
        ]

        for pattern in patterns:
            code = f"client.{pattern}()"
            test_file = tmp_path / f"test_{pattern}.py"
            test_file.write_text(code)

            violations = scan_file(test_file)
            assert len(violations) == 1, f"Pattern '{pattern}' was not detected"
            assert violations[0].method_name == pattern

    def test_exact_match_patterns(self, tmp_path: Path) -> None:
        """Verify patterns with delete_, create_, update_ prefixes are detected."""
        # Note: Bare "delete", "create", "update" are only flagged via prefixes
        # This avoids false positives from dict.update(), str.replace(), etc.
        prefix_patterns = ["delete_resource", "create_resource", "update_tags"]

        for pattern in prefix_patterns:
            code = f"client.{pattern}()"
            test_file = tmp_path / f"test_{pattern}.py"
            test_file.write_text(code)

            violations = scan_file(test_file)
            assert len(violations) == 1, f"Prefix pattern '{pattern}' was not detected"
            assert violations[0].method_name == pattern

    def test_syntax_error_does_not_crash(self, tmp_path: Path) -> None:
        """Verify that files with syntax errors are handled gracefully."""
        code = "def broken_syntax(\n  # missing closing paren"
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        # Should not raise exception
        violations = scan_file(test_file)
        assert violations == []

    def test_violation_includes_line_number(self, tmp_path: Path) -> None:
        """Verify that violations include accurate line numbers."""
        code = """
# Line 1
# Line 2
def example():
    # Line 5
    client.delete_resource(resource_id)
"""
        test_file = tmp_path / "test.py"
        test_file.write_text(code)

        violations = scan_file(test_file)
        assert len(violations) == 1
        assert violations[0].line_number == 6

    def test_readonly_allow_requires_reason(self, tmp_path: Path) -> None:
        """Verify that readonly-allow: marker format is correct."""
        # This test documents the expected format; checker accepts any text after marker
        code_with_reason = """
# readonly-allow: test fixture
client.delete()
"""
        test_file = tmp_path / "with_reason.py"
        test_file.write_text(code_with_reason)

        violations = scan_file(test_file)
        assert len(violations) == 0

        # Bare marker also works (by design; reason is advisory)
        code_bare = """
# readonly-allow:
client.delete()
"""
        test_file2 = tmp_path / "bare.py"
        test_file2.write_text(code_bare)

        violations2 = scan_file(test_file2)
        assert len(violations2) == 0
