"""Tests for verify_query_integrity.py."""

import json

# Import the functions we want to test
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import verify_query_integrity  # noqa: E402


def test_compute_sha256(tmp_path: Path) -> None:
    """Test SHA-256 computation."""
    test_file = tmp_path / "test.kql"
    test_file.write_text("SELECT * FROM resources", encoding="utf-8")

    hash_value = verify_query_integrity.compute_sha256(test_file)

    # SHA-256 should be 64-character hex string
    assert len(hash_value) == 64
    assert all(c in "0123456789abcdef" for c in hash_value)

    # Recompute should give same hash
    hash_value2 = verify_query_integrity.compute_sha256(test_file)
    assert hash_value == hash_value2


def test_verify_integrity_happy_path(tmp_path: Path) -> None:
    """Test integrity verification with matching hashes."""
    # Create test structure
    data_dir = tmp_path / "data" / "alz-queries"
    checklist_dir = data_dir / "checklist"
    checklist_dir.mkdir(parents=True)

    # Write test query file
    query_file = checklist_dir / "test-query.kql"
    query_file.write_text("SELECT * FROM resources", encoding="utf-8")

    # Compute its hash
    expected_hash = verify_query_integrity.compute_sha256(query_file)

    # Create manifest with correct hash
    manifest = {
        "sources": [
            {
                "repo": "test/repo",
                "commit_sha": "abc123",
                "ref": "commit:abc123",
                "vendored_at": "2026-01-01T00:00:00Z",
                "subset": {
                    "source_file": "queries/test.json",
                    "checklist_ids": ["test-id"],
                    "files": ["data/alz-queries/checklist/test-query.kql"],
                    "sha256": {"data/alz-queries/checklist/test-query.kql": expected_hash},
                },
                "file_count": 1,
            }
        ]
    }

    manifest_path = data_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Run verification
    result = verify_query_integrity.verify_integrity(tmp_path)

    assert result == 0


def test_verify_integrity_tampered_file(tmp_path: Path) -> None:
    """Test integrity verification with tampered file."""
    # Create test structure
    data_dir = tmp_path / "data" / "alz-queries"
    checklist_dir = data_dir / "checklist"
    checklist_dir.mkdir(parents=True)

    # Write test query file
    query_file = checklist_dir / "test-query.kql"
    query_file.write_text("SELECT * FROM resources", encoding="utf-8")

    # Create manifest with WRONG hash
    manifest = {
        "sources": [
            {
                "repo": "test/repo",
                "commit_sha": "abc123",
                "ref": "commit:abc123",
                "vendored_at": "2026-01-01T00:00:00Z",
                "subset": {
                    "source_file": "queries/test.json",
                    "checklist_ids": ["test-id"],
                    "files": ["data/alz-queries/checklist/test-query.kql"],
                    "sha256": {
                        "data/alz-queries/checklist/test-query.kql": "0" * 64  # Wrong hash
                    },
                },
                "file_count": 1,
            }
        ]
    }

    manifest_path = data_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Run verification - should fail
    result = verify_query_integrity.verify_integrity(tmp_path)

    assert result == 1


def test_verify_integrity_missing_file(tmp_path: Path) -> None:
    """Test integrity verification with missing file."""
    # Create test structure
    data_dir = tmp_path / "data" / "alz-queries"
    data_dir.mkdir(parents=True)

    # Create manifest but don't create the file
    manifest = {
        "sources": [
            {
                "repo": "test/repo",
                "commit_sha": "abc123",
                "ref": "commit:abc123",
                "vendored_at": "2026-01-01T00:00:00Z",
                "subset": {
                    "source_file": "queries/test.json",
                    "checklist_ids": ["test-id"],
                    "files": ["data/alz-queries/checklist/test-query.kql"],
                    "sha256": {"data/alz-queries/checklist/test-query.kql": "a" * 64},
                },
                "file_count": 1,
            }
        ]
    }

    manifest_path = data_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Run verification - should fail
    result = verify_query_integrity.verify_integrity(tmp_path)

    assert result == 1


def test_verify_integrity_missing_hash(tmp_path: Path) -> None:
    """Test integrity verification with missing hash in manifest."""
    # Create test structure
    data_dir = tmp_path / "data" / "alz-queries"
    checklist_dir = data_dir / "checklist"
    checklist_dir.mkdir(parents=True)

    # Write test query file
    query_file = checklist_dir / "test-query.kql"
    query_file.write_text("SELECT * FROM resources", encoding="utf-8")

    # Create manifest without sha256 field
    manifest = {
        "sources": [
            {
                "repo": "test/repo",
                "commit_sha": "abc123",
                "ref": "commit:abc123",
                "vendored_at": "2026-01-01T00:00:00Z",
                "subset": {
                    "source_file": "queries/test.json",
                    "checklist_ids": ["test-id"],
                    "files": ["data/alz-queries/checklist/test-query.kql"],
                    # No sha256 field
                },
                "file_count": 1,
            }
        ]
    }

    manifest_path = data_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Run verification - should fail
    result = verify_query_integrity.verify_integrity(tmp_path)

    assert result == 1


def test_update_hashes(tmp_path: Path) -> None:
    """Test hash regeneration with --update mode."""
    # Create test structure
    data_dir = tmp_path / "data" / "alz-queries"
    checklist_dir = data_dir / "checklist"
    checklist_dir.mkdir(parents=True)

    # Write test query file
    query_file = checklist_dir / "test-query.kql"
    query_file.write_text("SELECT * FROM resources", encoding="utf-8")

    # Create manifest without hashes
    manifest = {
        "sources": [
            {
                "repo": "test/repo",
                "commit_sha": "abc123",
                "ref": "commit:abc123",
                "vendored_at": "2026-01-01T00:00:00Z",
                "subset": {
                    "source_file": "queries/test.json",
                    "checklist_ids": ["test-id"],
                    "files": ["data/alz-queries/checklist/test-query.kql"],
                },
                "file_count": 1,
            }
        ]
    }

    manifest_path = data_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Run update
    result = verify_query_integrity.update_hashes(tmp_path)

    assert result == 0

    # Load updated manifest
    updated_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Check that sha256 was added
    assert "sha256" in updated_manifest["sources"][0]["subset"]
    file_path = "data/alz-queries/checklist/test-query.kql"
    assert file_path in updated_manifest["sources"][0]["subset"]["sha256"]

    # Check that MANIFEST.md was created
    manifest_md_path = data_dir / "MANIFEST.md"
    assert manifest_md_path.exists()
    assert "test/repo" in manifest_md_path.read_text(encoding="utf-8")


def test_update_hashes_missing_file(tmp_path: Path) -> None:
    """Test hash regeneration fails on missing file."""
    # Create test structure
    data_dir = tmp_path / "data" / "alz-queries"
    data_dir.mkdir(parents=True)

    # Create manifest but don't create the file
    manifest = {
        "sources": [
            {
                "repo": "test/repo",
                "commit_sha": "abc123",
                "ref": "commit:abc123",
                "vendored_at": "2026-01-01T00:00:00Z",
                "subset": {
                    "source_file": "queries/test.json",
                    "checklist_ids": ["test-id"],
                    "files": ["data/alz-queries/checklist/missing.kql"],
                },
                "file_count": 1,
            }
        ]
    }

    manifest_path = data_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Run update - should fail
    result = verify_query_integrity.update_hashes(tmp_path)

    assert result == 1


def test_generate_markdown_manifest(tmp_path: Path) -> None:
    """Test MANIFEST.md generation."""
    manifest = {
        "sources": [
            {
                "repo": "test/repo",
                "commit_sha": "abc123def456",
                "ref": "commit:abc123def456",
                "vendored_at": "2026-04-22T12:00:00Z",
                "subset": {
                    "source_file": "queries/test.json",
                    "checklist_ids": ["id1", "id2"],
                    "files": ["data/alz-queries/checklist/id1.kql"],
                    "sha256": {"data/alz-queries/checklist/id1.kql": "a" * 64},
                },
                "file_count": 2,
            }
        ]
    }

    markdown = verify_query_integrity.generate_markdown_manifest(manifest, tmp_path)

    # Check key content
    assert "# ALZ query snapshot manifest" in markdown
    assert "test/repo" in markdown
    assert "abc123def456" in markdown
    assert "id1, id2" in markdown
    assert "file_count: `2`" in markdown


def test_load_manifest_missing_file(tmp_path: Path) -> None:
    """Test load_manifest with missing file exits with error."""
    manifest_path = tmp_path / "missing.json"

    with pytest.raises(SystemExit) as exc_info:
        verify_query_integrity.load_manifest(manifest_path)

    assert exc_info.value.code == 1
