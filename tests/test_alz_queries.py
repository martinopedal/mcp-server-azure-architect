"""Tests for the vendored ALZ query loader and the alz_query_by_id tool."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from mcp_server_azure_architect import alz_queries
from mcp_server_azure_architect.server import alz_query_by_id, mcp

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
