"""Tests for check_breaking_changes.py script."""

import json
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    subprocess.run(["git", "init"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )

    return repo_dir


def create_kql_file(repo_dir: Path, rel_path: str, content: str) -> None:
    """Create a .kql file in the repo with the given content."""
    full_path = repo_dir / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")


def git_commit(repo_dir: Path, message: str) -> None:
    """Add all changes and commit."""
    subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo_dir, check=True, capture_output=True)


def run_detector(
    repo_dir: Path, base_ref: str, head_ref: str = "HEAD", output: str = "markdown"
) -> tuple[int, str]:
    """Run the breaking-change detector script."""
    result = subprocess.run(
        [
            "python",
            str(Path(__file__).parent.parent / "scripts" / "check_breaking_changes.py"),
            "--base-ref",
            base_ref,
            "--head-ref",
            head_ref,
            "--output",
            output,
            "--data-dir",
            "data/alz-queries",
        ],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.returncode, result.stdout


def test_unchanged_file(git_repo):
    """Test that unchanged files are classified correctly."""
    content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", content)
    git_commit(git_repo, "Initial commit")

    exit_code, output = run_detector(git_repo, "HEAD")
    assert exit_code == 0
    assert "No breaking changes detected" in output
    assert "Total files analyzed: 1" in output
    assert "Unchanged: 1" in output


def test_first_token_changed(git_repo):
    """Test that first token changes are detected as breaking."""
    initial_content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", initial_content)
    git_commit(git_repo, "Initial commit")

    updated_content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
securityresources | where type =~ 'microsoft.security/assessments'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", updated_content)
    git_commit(git_repo, "Update query")

    exit_code, output = run_detector(git_repo, "HEAD~1")
    assert exit_code == 1
    assert "1 breaking change(s) detected" in output
    assert "first_token_changed" in output
    assert "`resources`" in output
    assert "`securityresources`" in output


def test_file_removed(git_repo):
    """Test that file removal is detected as breaking."""
    content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", content)
    git_commit(git_repo, "Initial commit")

    (git_repo / "data" / "alz-queries" / "checklist" / "test.kql").unlink()
    git_commit(git_repo, "Remove file")

    exit_code, output = run_detector(git_repo, "HEAD~1")
    assert exit_code == 1
    assert "1 breaking change(s) detected" in output
    assert "removed" in output
    assert "Files removed: 1" in output


def test_file_added(git_repo):
    """Test that file addition is not breaking."""
    content1 = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id-1
// Vendored at: 2026-01-01T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test1.kql", content1)
    git_commit(git_repo, "Initial commit")

    content2 = """// Vendored from https://example.com/blob/def456/query.kql
// Source checklist ID: test-id-2
// Vendored at: 2026-01-02T00:00:00Z
securityresources | where type =~ 'microsoft.security/assessments'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test2.kql", content2)
    git_commit(git_repo, "Add new query")

    exit_code, output = run_detector(git_repo, "HEAD~1")
    assert exit_code == 0
    assert "No breaking changes detected" in output
    assert "Added: 1" in output


def test_header_only_changed(git_repo):
    """Test that header-only changes are not breaking."""
    initial_content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", initial_content)
    git_commit(git_repo, "Initial commit")

    updated_content = """// Vendored from https://example.com/blob/def456/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-02T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", updated_content)
    git_commit(git_repo, "Update header")

    exit_code, output = run_detector(git_repo, "HEAD~1")
    assert exit_code == 0
    assert "No breaking changes detected" in output
    assert "Header-only changes: 1" in output


def test_body_changed_same_token(git_repo):
    """Test that body changes with same first token are not breaking."""
    initial_content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", initial_content)
    git_commit(git_repo, "Initial commit")

    updated_content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines' | where location =~ 'eastus'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", updated_content)
    git_commit(git_repo, "Update query body")

    exit_code, output = run_detector(git_repo, "HEAD~1")
    assert exit_code == 0
    assert "No breaking changes detected" in output
    assert "Body changes (same token): 1" in output


def test_multiple_changes_mixed(git_repo):
    """Test handling multiple files with mixed change types."""
    content1 = """// Vendored from https://example.com/blob/abc/query.kql
// Source checklist ID: test-id-1
// Vendored at: 2026-01-01T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines'
"""
    content2 = """// Vendored from https://example.com/blob/def/query.kql
// Source checklist ID: test-id-2
// Vendored at: 2026-01-01T00:00:00Z
securityresources | where type =~ 'microsoft.security/assessments'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test1.kql", content1)
    create_kql_file(git_repo, "data/alz-queries/checklist/test2.kql", content2)
    git_commit(git_repo, "Initial commit")

    updated_content1 = """// Vendored from https://example.com/blob/abc/query.kql
// Source checklist ID: test-id-1
// Vendored at: 2026-01-01T00:00:00Z
policyresources | where type =~ 'microsoft.authorization/policyassignments'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test1.kql", updated_content1)
    (git_repo / "data" / "alz-queries" / "checklist" / "test2.kql").unlink()

    content3 = """// Vendored from https://example.com/blob/ghi/query.kql
// Source checklist ID: test-id-3
// Vendored at: 2026-01-01T00:00:00Z
authorizationresources | where type =~ 'microsoft.authorization/roleassignments'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test3.kql", content3)
    git_commit(git_repo, "Mixed changes")

    exit_code, output = run_detector(git_repo, "HEAD~1")
    assert exit_code == 1
    assert "2 breaking change(s) detected" in output
    assert "first_token_changed" in output
    assert "removed" in output
    assert "Added: 1" in output


def test_json_output(git_repo):
    """Test JSON output format."""
    content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", content)
    git_commit(git_repo, "Initial commit")

    updated_content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
securityresources | where type =~ 'microsoft.security/assessments'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", updated_content)
    git_commit(git_repo, "Update query")

    exit_code, output = run_detector(git_repo, "HEAD~1", output="json")
    assert exit_code == 1

    data = json.loads(output)
    assert data["breaking"] is True
    assert data["summary"]["breaking"] == 1
    assert data["summary"]["first_token_changed"] == 1
    assert len(data["changes"]) == 1
    assert data["changes"][0]["change_type"] == "first_token_changed"
    assert data["changes"][0]["base_token"] == "resources"
    assert data["changes"][0]["head_token"] == "securityresources"
    assert data["changes"][0]["breaking"] is True


def test_markdown_output_format(git_repo):
    """Test markdown output formatting."""
    content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", content)
    git_commit(git_repo, "Initial commit")

    updated_content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
securityresources | where type =~ 'microsoft.security/assessments'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", updated_content)
    git_commit(git_repo, "Update query")

    exit_code, output = run_detector(git_repo, "HEAD~1", output="markdown")
    assert exit_code == 1
    assert "## ALZ Snapshot Breaking-Change Report" in output
    assert "| File | Change Type | Base Token | Head Token |" in output
    assert "| `data/alz-queries/checklist/test.kql` |" in output
    assert "breaking-change-approved" in output


def test_no_fail_flag(git_repo):
    """Test --no-fail flag overrides exit code."""
    initial_content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", initial_content)
    git_commit(git_repo, "Initial commit")

    updated_content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
securityresources | where type =~ 'microsoft.security/assessments'
"""
    create_kql_file(git_repo, "data/alz-queries/checklist/test.kql", updated_content)
    git_commit(git_repo, "Update query")

    result = subprocess.run(
        [
            "python",
            str(Path(__file__).parent.parent / "scripts" / "check_breaking_changes.py"),
            "--base-ref",
            "HEAD~1",
            "--no-fail",
            "--data-dir",
            "data/alz-queries",
        ],
        cwd=git_repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "1 breaking change(s) detected" in result.stdout


def test_graph_directory_queries(git_repo):
    """Test detection works for graph/ subdirectory."""
    content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
ResourceContainers | where type =~ 'microsoft.resources/subscriptions'
"""
    create_kql_file(git_repo, "data/alz-queries/graph/test.kql", content)
    git_commit(git_repo, "Initial commit")

    updated_content = """// Vendored from https://example.com/blob/abc123/query.kql
// Source checklist ID: test-id
// Vendored at: 2026-01-01T00:00:00Z
resources | where type =~ 'microsoft.compute/virtualmachines'
"""
    create_kql_file(git_repo, "data/alz-queries/graph/test.kql", updated_content)
    git_commit(git_repo, "Update query")

    exit_code, output = run_detector(git_repo, "HEAD~1")
    assert exit_code == 1
    assert "1 breaking change(s) detected" in output
    assert "ResourceContainers" in output
    assert "resources" in output
