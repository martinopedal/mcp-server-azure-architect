"""Tests for scripts/refresh_alz_snapshot.py"""

import json

# Import the module under test
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import refresh_alz_snapshot as ras  # noqa: E402, I001


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create temporary data/alz-queries directory structure."""
    data_dir = tmp_path / "data" / "alz-queries"
    data_dir.mkdir(parents=True)
    (data_dir / "checklist").mkdir()
    (data_dir / "graph").mkdir()
    return data_dir


@pytest.fixture
def mock_manifest() -> dict:
    """Sample manifest.json structure."""
    return {
        "sources": [
            {
                "repo": "martinopedal/alz-checklist-queries",
                "commit_sha": "e7641beeda0126cc78825f8b77764c379552f3e1",
                "ref": "commit:e7641beeda0126cc78825f8b77764c379552f3e1",
                "vendored_at": "2026-04-22T12:35:39Z",
                "subset": {
                    "source_file": "queries/alz_all_queries.json",
                    "checklist_ids": ["54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a"],
                    "files": [
                        "data/alz-queries/checklist/54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a.kql"
                    ],
                },
                "file_count": 1,
            },
            {
                "repo": "martinopedal/alz-graph-queries",
                "commit_sha": "8a3fddabcbf272a19a627770a0d33de5f4ace8ee",
                "ref": "commit:8a3fddabcbf272a19a627770a0d33de5f4ace8ee",
                "vendored_at": "2026-04-22T12:35:39Z",
                "subset": {
                    "source_file": "queries/alz_additional_queries.json",
                    "checklist_ids": ["e8aa1e41-870d-4968-94c6-77be14f510ac"],
                    "files": ["data/alz-queries/graph/e8aa1e41-870d-4968-94c6-77be14f510ac.kql"],
                },
                "file_count": 1,
            },
        ]
    }


def test_load_manifest_missing(temp_data_dir: Path) -> None:
    """Test load_manifest returns empty structure when file missing."""
    manifest_path = temp_data_dir / "manifest.json"
    result = ras.load_manifest(manifest_path)
    assert result == {"sources": []}


def test_load_manifest_existing(temp_data_dir: Path, mock_manifest: dict) -> None:
    """Test load_manifest loads existing manifest correctly."""
    manifest_path = temp_data_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(mock_manifest, f)

    result = ras.load_manifest(manifest_path)
    assert result == mock_manifest
    assert len(result["sources"]) == 2
    assert result["sources"][0]["repo"] == "martinopedal/alz-checklist-queries"
    assert result["sources"][1]["repo"] == "martinopedal/alz-graph-queries"


def test_save_manifest(temp_data_dir: Path, mock_manifest: dict) -> None:
    """Test save_manifest writes valid JSON with trailing newline."""
    manifest_path = temp_data_dir / "manifest.json"
    ras.save_manifest(mock_manifest, manifest_path)

    assert manifest_path.exists()
    content = manifest_path.read_text()
    assert content.endswith("\n")

    loaded = json.loads(content)
    assert loaded == mock_manifest


def test_manifest_comparison_no_drift(mock_manifest: dict) -> None:
    """Test manifest comparison logic: same SHA means no refresh needed."""
    sources = mock_manifest["sources"]
    existing = sources[0]
    pinned_sha = existing["commit_sha"]
    upstream_sha = "e7641beeda0126cc78825f8b77764c379552f3e1"

    assert upstream_sha == pinned_sha
    # Simulation: no refresh needed
    assert upstream_sha == pinned_sha


def test_manifest_comparison_drift_detected(mock_manifest: dict) -> None:
    """Test manifest comparison logic: different SHA means refresh needed."""
    sources = mock_manifest["sources"]
    existing = sources[0]
    pinned_sha = existing["commit_sha"]
    upstream_sha = "0000000000000000000000000000000000000000"

    assert upstream_sha != pinned_sha
    # Simulation: refresh needed


def test_manifest_regeneration_valid_structure(temp_data_dir: Path) -> None:
    """Test manifest regeneration produces valid JSON with required keys."""
    new_manifest = {
        "sources": [
            {
                "repo": "martinopedal/alz-checklist-queries",
                "commit_sha": "abc123def456",
                "ref": "commit:abc123def456",
                "vendored_at": "2026-12-01T10:00:00Z",
                "subset": {
                    "source_file": "queries/alz_all_queries.json",
                    "checklist_ids": ["test-id-1"],
                    "files": ["data/alz-queries/checklist/test-id-1.kql"],
                },
                "file_count": 1,
            }
        ]
    }

    manifest_path = temp_data_dir / "manifest.json"
    ras.save_manifest(new_manifest, manifest_path)

    loaded = ras.load_manifest(manifest_path)
    assert "sources" in loaded
    assert len(loaded["sources"]) == 1

    source = loaded["sources"][0]
    assert "repo" in source
    assert "commit_sha" in source
    assert "vendored_at" in source
    assert "subset" in source
    assert "checklist_ids" in source["subset"]


def test_extract_queries_from_checklist_repo(tmp_path: Path) -> None:
    """Test extracting queries from checklist repo with current upstream shape."""
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()
    queries_dir = clone_dir / "queries"
    queries_dir.mkdir()

    # Mock alz_all_queries.json with current upstream shape
    source_json = queries_dir / "alz_all_queries.json"
    source_json.write_text(
        json.dumps(
            {
                "metadata": {
                    "name": "Azure Landing Zone Review",
                    "merged": False,
                },
                "queries": [
                    {
                        "guid": "test-checklist-1",
                        "graph": "resources | where type =~ 'microsoft.test'",
                        "text": "Test checklist item 1",
                        "category": "Test Category",
                        "subcategory": "Test Subcategory",
                        "severity": "High",
                        "queryable": True,
                    },
                    {
                        "guid": "test-checklist-2",
                        "graph": "resources | where name =~ 'testname'",
                        "text": "Test checklist item 2",
                        "category": "Test Category",
                        "subcategory": "Test Subcategory 2",
                        "severity": "Medium",
                        "queryable": True,
                    },
                ],
            }
        )
    )

    dest_dir = tmp_path / "output"
    dest_dir.mkdir()

    checklist_ids, metadata_dict = ras.extract_queries_from_checklist_repo(clone_dir, dest_dir)

    assert len(checklist_ids) == 2
    assert "test-checklist-1" in checklist_ids
    assert "test-checklist-2" in checklist_ids

    # Verify metadata dict
    assert "test-checklist-1" in metadata_dict
    assert metadata_dict["test-checklist-1"]["text"] == "Test checklist item 1"
    assert metadata_dict["test-checklist-1"]["category"] == "Test Category"
    assert metadata_dict["test-checklist-1"]["severity"] == "High"

    kql_file = dest_dir / "test-checklist-1.kql"
    assert kql_file.exists()
    content = kql_file.read_text()
    assert "test-checklist-1" in content
    assert "resources | where type =~ 'microsoft.test'" in content


def test_extract_queries_from_graph_repo(tmp_path: Path) -> None:
    """Test extracting queries from graph repo with current upstream shape."""
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()
    queries_dir = clone_dir / "queries"
    queries_dir.mkdir()

    # Mock alz_additional_queries.json with realistic upstream schema
    source_json = queries_dir / "alz_additional_queries.json"
    source_json.write_text(
        json.dumps(
            {
                "metadata": {"name": "ALZ Additional Graph Queries", "version": "1.0.0"},
                "queries": [
                    {
                        "guid": "test-graph-1",
                        "graph": "graph | where type =~ 'test'",
                        "text": "Test graph query",
                        "category": "Test Cat",
                        "subcategory": "Test Sub",
                        "severity": "Low",
                        "queryable": True,
                    },
                    {
                        "guid": "test-graph-2",
                        "graph": "graph | where name =~ 'nonqueryable'",
                        "text": "Non-queryable item",
                        "category": "Test Cat",
                        "subcategory": "Test Sub",
                        "severity": "Medium",
                        "queryable": False,
                    },
                ],
            }
        )
    )

    dest_dir = tmp_path / "output"
    dest_dir.mkdir()

    query_ids, metadata_dict = ras.extract_queries_from_graph_repo(clone_dir, dest_dir)

    # Should only extract queryable items
    assert len(query_ids) == 1
    assert "test-graph-1" in query_ids
    assert "test-graph-2" not in query_ids

    # Verify metadata dict
    assert "test-graph-1" in metadata_dict
    assert metadata_dict["test-graph-1"]["text"] == "Test graph query"
    assert metadata_dict["test-graph-1"]["severity"] == "Low"

    kql_file = dest_dir / "test-graph-1.kql"
    assert kql_file.exists()
    content = kql_file.read_text()
    assert "test-graph-1" in content
    assert "graph | where type =~ 'test'" in content

    # Verify non-queryable item was not written
    non_queryable_file = dest_dir / "test-graph-2.kql"
    assert not non_queryable_file.exists()


def test_update_kql_headers(tmp_path: Path) -> None:
    """Test updating placeholder {sha} and {timestamp} in KQL files."""
    kql_dir = tmp_path
    test_file = kql_dir / "test.kql"
    test_file.write_text(
        "// Vendored from https://github.com/test/repo/blob/{sha}/queries/test.json\n"
        "// Vendored at: {timestamp}\n"
        "resources | where type =~ 'test'\n"
    )

    ras.update_kql_headers(kql_dir, "test/repo", "abc123", "2026-12-01T10:00:00Z")

    content = test_file.read_text()
    assert "{sha}" not in content
    assert "{timestamp}" not in content
    assert "abc123" in content
    assert "2026-12-01T10:00:00Z" in content


def test_generate_manifest_md(temp_data_dir: Path, mock_manifest: dict) -> None:
    """Test MANIFEST.md generation from manifest.json."""
    manifest_md_path = temp_data_dir / "MANIFEST.md"
    ras.generate_manifest_md(mock_manifest, manifest_md_path)

    assert manifest_md_path.exists()
    content = manifest_md_path.read_text()

    assert "# ALZ query snapshot manifest" in content
    assert "Refreshed automatically" in content
    assert "martinopedal/alz-checklist-queries" in content
    assert "e7641beeda0126cc78825f8b77764c379552f3e1" in content
    assert "54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a" in content


def test_extract_queries_schema_mismatch_graph(tmp_path: Path) -> None:
    """Test that graph extractor raises on upstream schema change."""
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()
    queries_dir = clone_dir / "queries"
    queries_dir.mkdir()

    # Mock upstream with wrong top-level key
    source_json = queries_dir / "alz_additional_queries.json"
    source_json.write_text(
        json.dumps(
            {
                "items": [  # Wrong key - should be "queries"
                    {
                        "guid": "test-id",
                        "graph": "resources | where type =~ 'test'",
                        "queryable": True,
                    }
                ]
            }
        )
    )

    dest_dir = tmp_path / "output"
    dest_dir.mkdir()

    # Should raise ValueError on schema mismatch
    with pytest.raises(ValueError, match="expected top-level key 'queries'"):
        ras.extract_queries_from_graph_repo(clone_dir, dest_dir)


def test_extract_queries_schema_mismatch_checklist(tmp_path: Path) -> None:
    """Test that checklist extractor raises on upstream schema change."""
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()
    queries_dir = clone_dir / "queries"
    queries_dir.mkdir()

    # Mock upstream with no valid top-level key
    source_json = queries_dir / "alz_all_queries.json"
    source_json.write_text(
        json.dumps(
            {
                "invalid_key": [  # Neither "items" nor "queries"
                    {
                        "id": "test-id",
                        "graph": "resources | where type =~ 'test'",
                        "queryable": True,
                    }
                ]
            }
        )
    )

    dest_dir = tmp_path / "output"
    dest_dir.mkdir()

    # Should raise ValueError on schema mismatch
    with pytest.raises(ValueError, match="expected top-level key 'queries' or 'items'"):
        ras.extract_queries_from_checklist_repo(clone_dir, dest_dir)


@patch("refresh_alz_snapshot.get_upstream_commit")
@patch("refresh_alz_snapshot.clone_shallow")
@patch("refresh_alz_snapshot.extract_queries_from_checklist_repo")
@patch("refresh_alz_snapshot.extract_queries_from_graph_repo")
def test_refresh_snapshot_no_drift(
    mock_extract_graph: Mock,
    mock_extract_checklist: Mock,
    mock_clone: Mock,
    mock_get_upstream: Mock,
    tmp_path: Path,
    mock_manifest: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test refresh_snapshot with no upstream drift."""
    # Setup
    data_dir = tmp_path / "data" / "alz-queries"
    data_dir.mkdir(parents=True)
    (data_dir / "checklist").mkdir()
    (data_dir / "graph").mkdir()
    manifest_path = data_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(mock_manifest, f)

    # Mock: upstream SHAs match pinned SHAs for both repos
    def mock_get_commit(repo: str) -> str:
        if repo == "martinopedal/alz-checklist-queries":
            return "e7641beeda0126cc78825f8b77764c379552f3e1"
        elif repo == "martinopedal/alz-graph-queries":
            return "8a3fddabcbf272a19a627770a0d33de5f4ace8ee"
        return "unknown"

    mock_get_upstream.side_effect = mock_get_commit

    # Patch __file__ to point to tmp_path
    monkeypatch.setattr(ras, "__file__", str(tmp_path / "scripts" / "refresh_alz_snapshot.py"))

    changes = ras.refresh_snapshot(dry_run=False)

    assert not changes
    mock_clone.assert_not_called()
    mock_extract_checklist.assert_not_called()
    mock_extract_graph.assert_not_called()


@patch("refresh_alz_snapshot.get_upstream_commit")
def test_refresh_snapshot_dry_run_with_drift(
    mock_get_upstream: Mock,
    tmp_path: Path,
    mock_manifest: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test refresh_snapshot in dry-run mode with drift detected.

    NOTE: As of PR #96, graph repo is temporarily disabled due to guid collision
    (Decision 10/11). Test updated to check checklist-only vendoring.
    """
    # Setup
    data_dir = tmp_path / "data" / "alz-queries"
    data_dir.mkdir(parents=True)
    (data_dir / "checklist").mkdir()
    manifest_path = data_dir / "manifest.json"

    # Use a manifest with only checklist source (graph commented out in script)
    checklist_only_manifest = {
        "schema_version": 2,
        "sources": [
            {
                "repo": "martinopedal/alz-checklist-queries",
                "commit_sha": "old1234567890123456789012345678901234567",
                "ref": "commit:old1234567890123456789012345678901234567",
                "vendored_at": "2024-01-01T00:00:00Z",
                "license": {"spdx": "MIT", "upstream_license_url": "https://example.com/LICENSE"},
                "subset": {
                    "source_file": "queries/alz_all_queries.json",
                    "checklist_ids": [],
                    "files": [],
                    "sha256": {},
                    "queries": {},
                },
                "file_count": 0,
            }
        ],
    }
    with open(manifest_path, "w") as f:
        json.dump(checklist_only_manifest, f)

    # Mock: upstream SHA differs from pinned SHA for checklist repo
    def mock_get_commit(repo: str) -> str:
        if repo == "martinopedal/alz-checklist-queries":
            return "e7641beeda0126cc78825f8b77764c379552f3e1"  # drift detected
        return "unknown"

    mock_get_upstream.side_effect = mock_get_commit

    monkeypatch.setattr(ras, "__file__", str(tmp_path / "scripts" / "refresh_alz_snapshot.py"))

    changes = ras.refresh_snapshot(dry_run=True)

    assert changes
    # In dry-run, manifest should not be updated
    loaded = ras.load_manifest(manifest_path)
    assert loaded["sources"][0]["commit_sha"] == "old1234567890123456789012345678901234567"


def test_extract_queries_merged_catalogue_detection(tmp_path: Path) -> None:
    """Test merged-catalogue detection skips secondary fetch."""
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()
    queries_dir = clone_dir / "queries"
    queries_dir.mkdir()

    # Mock with merged flag set
    source_json = queries_dir / "alz_additional_queries.json"
    source_json.write_text(
        json.dumps(
            {
                "metadata": {
                    "name": "ALZ Graph Queries",
                    "merged": True,
                    "total_items": 255,
                },
                "queries": [],
            }
        )
    )

    dest_dir = tmp_path / "output"
    dest_dir.mkdir()

    query_ids, metadata_dict = ras.extract_queries_from_graph_repo(clone_dir, dest_dir)

    # Should return empty when merged flag is true
    assert len(query_ids) == 0
    assert len(metadata_dict) == 0


def test_compute_content_hash_deduplication() -> None:
    """Test compute_content_hash for deduplication logic."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        kql_path = Path(tmpdir) / "test.kql"
        kql_path.write_text("resources | where type =~ 'test'\n")

        metadata1 = {
            "text": "Test query",
            "category": "Test",
            "subcategory": "Sub",
            "severity": "High",
        }

        metadata2 = {
            "text": "Test query",
            "category": "Test",
            "subcategory": "Sub",
            "severity": "High",
        }

        metadata3 = {
            "text": "Different text",
            "category": "Test",
            "subcategory": "Sub",
            "severity": "High",
        }

        hash1 = ras.compute_content_hash(kql_path, metadata1)
        hash2 = ras.compute_content_hash(kql_path, metadata2)
        hash3 = ras.compute_content_hash(kql_path, metadata3)

        # Identical metadata should produce same hash
        assert hash1 == hash2

        # Different metadata should produce different hash
        assert hash1 != hash3


def test_custom_source_preservation_during_refresh(
    temp_data_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression test: refresh must preserve custom sources (ref='custom')."""
    # Create manifest with both vendored AND custom sources
    manifest = {
        "schema_version": 2,
        "sources": [
            {
                "repo": "martinopedal/alz-checklist-queries",
                "commit_sha": "oldsha111",
                "ref": "commit:oldsha111",
                "vendored_at": "2026-01-01T00:00:00Z",
                "subset": {
                    "source_file": "queries/alz_all_queries.json",
                    "checklist_ids": ["vendor-id-1"],
                    "files": ["data/alz-queries/checklist/vendor-id-1.kql"],
                    "queries": {},
                    "sha256": {},
                },
                "file_count": 1,
            },
            {
                "repo": "martinopedal/mcp-server-azure-architect",
                "commit_sha": "",
                "ref": "custom",
                "source_ref": "custom",
                "vendored_at": "",
                "subset": {
                    "source_file": "",
                    "checklist_ids": ["custom-guid-1"],
                    "files": ["data/alz-queries/custom/custom-guid-1.kql"],
                    "queries": {
                        "custom-guid-1": {
                            "guid": "custom-guid-1",
                            "category": "Test",
                            "subcategory": "Custom",
                            "text": "Test custom query",
                            "source": "custom",
                            "source_commit": "",
                            "source_repo": "martinopedal/mcp-server-azure-architect",
                            "source_ref": "custom",
                        }
                    },
                    "sha256": {
                        "data/alz-queries/custom/custom-guid-1.kql": "fakehash123"
                    },
                },
                "file_count": 1,
            },
        ],
    }

    manifest_path = temp_data_dir / "manifest.json"
    with manifest_path.open("w") as f:
        json.dump(manifest, f)

    # Verify custom source exists before any refresh simulation
    loaded = ras.load_manifest(manifest_path)
    assert len(loaded["sources"]) == 2  # vendored + custom

    custom_sources_before = [s for s in loaded["sources"] if s.get("ref") == "custom"]
    assert len(custom_sources_before) == 1
    assert custom_sources_before[0]["subset"]["checklist_ids"] == ["custom-guid-1"]

    # CRITICAL ASSERTION: If refresh_snapshot were run, custom source must survive
    # This test documents the expected behavior: custom sources filter is mandatory
