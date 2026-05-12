"""Tests for the vendored ALZ query loader and the alz_query_by_id tool."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from mcp_server_azure_architect import alz_queries
from mcp_server_azure_architect.server import alz_query_by_id, alz_query_list, mcp

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "alz-queries" / "manifest.json"


def _known_checklist_id() -> str:
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return str(raw["sources"][0]["subset"]["checklist_ids"][0])


def test_load_manifest_smoke() -> None:
    """Manifest loads cleanly and the cache is populated on first call."""
    alz_queries.reset_cache()
    ids = alz_queries.list_query_ids()
    assert isinstance(ids, list)
    assert ids, "vendored snapshot should expose at least one checklist ID"
    assert all(isinstance(item, str) for item in ids)


def test_get_query_known_id() -> None:
    """A known checklist ID returns a record with non-empty KQL and citation."""
    checklist_id = _known_checklist_id()
    record = alz_queries.get_query(checklist_id)

    assert record["checklist_id"] == checklist_id
    assert record["kql"].strip(), "KQL body must be non-empty"
    assert record["source_repo"], "source_repo must be populated"
    assert record["source_commit"], "source_commit must be populated"
    assert record["citation"].startswith(record["source_repo"])
    assert checklist_id in record["citation"]
    assert record["pillar"] in {"checklist", "graph"}


def test_get_query_unknown_id_raises_lookup_error() -> None:
    """Unknown IDs surface a LookupError with a helpful message."""
    with pytest.raises(LookupError) as excinfo:
        alz_queries.get_query("not-a-real-checklist-id")

    msg = str(excinfo.value)
    assert "not-a-real-checklist-id" in msg
    assert "Available" in msg


def test_list_query_ids_returns_strings() -> None:
    """list_query_ids returns a sorted list of unique string IDs."""
    ids = alz_queries.list_query_ids()
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))


def test_loader_does_not_import_azure_sdk() -> None:
    """Importing the loader must not pull in the Azure SDK (cold-start guard)."""
    for name in list(sys.modules):
        if name.startswith(("azure.identity", "azure.mgmt", "azure.core")):
            sys.modules.pop(name, None)
    sys.modules.pop("mcp_server_azure_architect.alz_queries", None)

    import mcp_server_azure_architect.alz_queries  # noqa: F401

    leaked = [
        name
        for name in sys.modules
        if name.startswith(("azure.identity", "azure.mgmt"))
    ]
    assert leaked == [], f"loader leaked Azure SDK imports: {leaked}"


def test_alz_query_by_id_tool_registered_with_schema() -> None:
    """FastMCP registers alz_query_by_id with the expected JSON Schema."""
    tools = mcp._tool_manager.list_tools()
    tool = next((t for t in tools if t.name == "alz_query_by_id"), None)

    assert tool is not None, "alz_query_by_id should be registered"
    assert tool.description is not None
    assert "ALZ" in tool.description or "Azure Landing Zone" in tool.description

    schema = tool.parameters
    assert schema["type"] == "object"
    assert "checklist_id" in schema["properties"]
    assert schema["properties"]["checklist_id"]["type"] == "string"
    assert "checklist_id" in schema.get("required", [])


def test_alz_query_by_id_function_returns_record() -> None:
    """Direct invocation returns a dict with the expected keys."""
    checklist_id = _known_checklist_id()
    result = alz_query_by_id(checklist_id)

    assert isinstance(result, dict)
    for key in ("checklist_id", "kql", "source_repo", "source_commit", "citation"):
        assert key in result, f"missing key {key} in tool output"
    assert result["checklist_id"] == checklist_id


async def test_alz_query_by_id_invocation_via_mcp() -> None:
    """End-to-end roundtrip through FastMCP's tool dispatcher."""
    checklist_id = _known_checklist_id()
    result = await mcp._tool_manager.call_tool(
        "alz_query_by_id", {"checklist_id": checklist_id}
    )

    assert isinstance(result, dict)
    assert result["checklist_id"] == checklist_id
    assert result["kql"].strip()


async def test_alz_query_by_id_unknown_id_via_mcp_raises() -> None:
    """Unknown IDs surface as errors through the MCP dispatcher too."""
    with pytest.raises(Exception) as excinfo:
        await mcp._tool_manager.call_tool(
            "alz_query_by_id", {"checklist_id": "definitely-not-a-real-id"}
        )

    assert "definitely-not-a-real-id" in str(excinfo.value)


# -------------------------------------------------------------------------
# list_queries() / alz_query_list tool tests (wave 6, issue #51)
# -------------------------------------------------------------------------


def test_list_queries_no_filters() -> None:
    """No filters returns full count, items sorted, manifest_commit echoed."""
    result = alz_queries.list_queries()

    assert isinstance(result, dict)
    assert "count" in result
    assert "items" in result
    assert "manifest_commit" in result
    assert "truncated" in result
    assert "filters_applied" in result

    count = result["count"]
    items = result["items"]

    assert count > 0, "vendored snapshot should have at least one query"
    assert len(items) <= 200, "default limit is 200"
    assert result["truncated"] is False or count > 200

    # Check items are sorted alphabetically by checklist_id
    checklist_ids = [item["checklist_id"] for item in items]
    assert checklist_ids == sorted(checklist_ids)

    # Each item has all 5 keys
    for item in items:
        assert "checklist_id" in item
        assert "pillar" in item
        assert "source_repo" in item
        assert "title" in item
        assert "citation" in item

    # manifest_commit is non-empty
    assert result["manifest_commit"], "manifest_commit must be non-empty"
    assert "@" in result["manifest_commit"], "manifest_commit should have repo@commit format"

    # filters_applied reflects defaults
    assert result["filters_applied"]["pillar"] is None
    assert result["filters_applied"]["source_repo"] is None


def test_list_queries_pillar_filter() -> None:
    """Pillar filter returns only matching items."""
    # Get all queries first to find a pillar
    all_queries = alz_queries.list_queries()
    if all_queries["count"] == 0:
        pytest.skip("No queries in snapshot")

    pillar = all_queries["items"][0]["pillar"]

    result = alz_queries.list_queries(pillar=pillar)

    assert result["count"] > 0
    assert all(item["pillar"] == pillar for item in result["items"])
    assert result["filters_applied"]["pillar"] == pillar
    assert result["filters_applied"]["source_repo"] is None


def test_list_queries_source_repo_filter() -> None:
    """Source_repo filter returns only matching items."""
    all_queries = alz_queries.list_queries()
    if all_queries["count"] == 0:
        pytest.skip("No queries in snapshot")

    source_repo = all_queries["items"][0]["source_repo"]

    result = alz_queries.list_queries(source_repo=source_repo)

    assert result["count"] > 0
    assert all(item["source_repo"] == source_repo for item in result["items"])
    assert result["filters_applied"]["pillar"] is None
    assert result["filters_applied"]["source_repo"] == source_repo


def test_list_queries_both_filters() -> None:
    """Both filters applied with AND semantics."""
    all_queries = alz_queries.list_queries()
    if all_queries["count"] == 0:
        pytest.skip("No queries in snapshot")

    first = all_queries["items"][0]
    pillar = first["pillar"]
    source_repo = first["source_repo"]

    result = alz_queries.list_queries(pillar=pillar, source_repo=source_repo)

    assert result["count"] > 0
    assert all(
        item["pillar"] == pillar and item["source_repo"] == source_repo
        for item in result["items"]
    )
    assert result["filters_applied"]["pillar"] == pillar
    assert result["filters_applied"]["source_repo"] == source_repo


def test_list_queries_nonexistent_pillar() -> None:
    """Non-existent pillar returns empty items, count=0, no exception."""
    result = alz_queries.list_queries(pillar="nonexistent-pillar-xyz")

    assert result["count"] == 0
    assert result["items"] == []
    assert result["truncated"] is False
    assert result["filters_applied"]["pillar"] == "nonexistent-pillar-xyz"


def test_list_queries_limit_applied() -> None:
    """Limit parameter caps items and sets truncated=True if exceeded."""
    all_queries = alz_queries.list_queries()
    total_count = all_queries["count"]

    if total_count <= 5:
        pytest.skip("Need more than 5 queries to test limit")

    result = alz_queries.list_queries(limit=5)

    assert result["count"] == total_count  # count is pre-limit
    assert len(result["items"]) == 5
    assert result["truncated"] is True

    # Items should still be sorted
    checklist_ids = [item["checklist_id"] for item in result["items"]]
    assert checklist_ids == sorted(checklist_ids)


def test_list_queries_items_sorted_alphabetically() -> None:
    """Items are always sorted alphabetically by checklist_id."""
    result = alz_queries.list_queries()

    checklist_ids = [item["checklist_id"] for item in result["items"]]
    assert checklist_ids == sorted(checklist_ids), "items must be sorted"


def test_list_queries_item_schema() -> None:
    """Each item has all 5 required keys with correct types."""
    result = alz_queries.list_queries()

    if result["count"] == 0:
        pytest.skip("No queries in snapshot")

    for item in result["items"]:
        assert isinstance(item["checklist_id"], str)
        assert isinstance(item["pillar"], str)
        assert isinstance(item["source_repo"], str)
        assert isinstance(item["title"], str)  # may be empty
        assert isinstance(item["citation"], str)
        assert item["checklist_id"], "checklist_id must not be empty"
        assert item["pillar"], "pillar must not be empty"
        assert item["source_repo"], "source_repo must not be empty"
        assert item["citation"], "citation must not be empty"


def test_alz_query_list_tool_registered() -> None:
    """FastMCP registers alz_query_list with the expected JSON Schema."""
    tools = mcp._tool_manager.list_tools()
    tool = next((t for t in tools if t.name == "alz_query_list"), None)

    assert tool is not None, "alz_query_list should be registered"
    assert tool.description is not None
    assert "ALZ" in tool.description or "Azure Landing Zone" in tool.description

    schema = tool.parameters
    assert schema["type"] == "object"
    assert "pillar" in schema["properties"]
    assert "source_repo" in schema["properties"]
    assert "limit" in schema["properties"]


async def test_alz_query_list_invocation_via_mcp() -> None:
    """End-to-end roundtrip through FastMCP's tool dispatcher."""
    result = await mcp._tool_manager.call_tool("alz_query_list", {})

    assert isinstance(result, dict)
    assert "count" in result
    assert "items" in result
    assert "manifest_commit" in result
    assert "truncated" in result
    assert "filters_applied" in result


def test_alz_query_list_function_direct() -> None:
    """Direct invocation via alz_query_list tool function."""
    result = alz_query_list()

    assert isinstance(result, dict)
    assert "count" in result
    assert result["count"] >= 0
