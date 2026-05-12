"""Tests for the ALZ scorecard tool."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import Mock, patch

import pytest

from mcp_server_azure_architect.scorecard import run_scorecard
from mcp_server_azure_architect.server import mcp


@pytest.fixture(autouse=True)
def reset_alz_cache() -> None:
    """Reset the ALZ query cache before each test."""
    from mcp_server_azure_architect import alz_queries

    alz_queries.reset_cache()


def _mock_arg_response(rows: list[dict[str, Any]]) -> Mock:
    """Build a mock ARG response."""
    mock_response = Mock()
    mock_response.data = rows
    return mock_response


@pytest.mark.asyncio
async def test_scorecard_all_pass_no_violations() -> None:
    """All queries return zero violations; scorecard shows all pass."""
    with patch(
        "mcp_server_azure_architect.scorecard._get_resource_graph_client"
    ) as mock_client_factory:
        mock_client = Mock()
        mock_client.resources = Mock(return_value=_mock_arg_response([]))
        mock_client_factory.return_value = mock_client

        result = await run_scorecard(subscription_id="sub-123")

        assert result["subscription_id"] == "sub-123"
        assert result["truncated"] is False
        assert result["aggregate"]["total"] > 0
        assert result["aggregate"]["pass_count"] == result["aggregate"]["total"]
        assert result["aggregate"]["fail"] == 0
        assert result["aggregate"]["unknown"] == 0


@pytest.mark.asyncio
async def test_scorecard_some_violations_fail_status() -> None:
    """Queries with violations return fail status."""
    violation_rows = [
        {"id": "res-1", "name": "resource1"},
        {"id": "res-2", "name": "resource2"},
    ]

    with patch(
        "mcp_server_azure_architect.scorecard._get_resource_graph_client"
    ) as mock_client_factory:
        mock_client = Mock()
        # First query returns violations, second returns none
        mock_client.resources = Mock(
            side_effect=[
                _mock_arg_response(violation_rows),
                _mock_arg_response([]),
            ]
        )
        mock_client_factory.return_value = mock_client

        # Run with explicit checklist_ids to control which queries run
        result = await run_scorecard(
            subscription_id="sub-123",
            checklist_ids=[
                "54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a",
                "348ef254-c27d-442e-abba-c7571559ab91",
            ],
        )

        assert result["aggregate"]["total"] == 2
        assert result["aggregate"]["fail"] == 1
        assert result["aggregate"]["pass_count"] == 1

        # Find the failing result
        fail_results = [r for r in result["results"] if r["status"] == "fail"]
        assert len(fail_results) == 1
        assert fail_results[0]["count"] == 2
        assert len(fail_results[0]["sample"]) == 2


@pytest.mark.asyncio
async def test_scorecard_query_error_marks_unknown() -> None:
    """ARG query error surfaces as status=unknown with error field."""
    with patch(
        "mcp_server_azure_architect.scorecard._get_resource_graph_client"
    ) as mock_client_factory:
        mock_client = Mock()
        mock_client.resources = Mock(side_effect=Exception("ARG quota exceeded"))
        mock_client_factory.return_value = mock_client

        result = await run_scorecard(
            subscription_id="sub-123",
            checklist_ids=["54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a"],
        )

        assert result["aggregate"]["total"] == 1
        assert result["aggregate"]["unknown"] == 1
        assert result["results"][0]["status"] == "unknown"
        error_msg = result["results"][0]["error"]
        assert error_msg is not None
        assert "ARG quota exceeded" in error_msg


@pytest.mark.asyncio
async def test_scorecard_count_column_aggregation() -> None:
    """Query with Count column uses that value instead of len(rows)."""
    with patch(
        "mcp_server_azure_architect.scorecard._get_resource_graph_client"
    ) as mock_client_factory:
        mock_client = Mock()
        # Return a single row with Count=42
        mock_client.resources = Mock(
            return_value=_mock_arg_response([{"Count": 42}])
        )
        mock_client_factory.return_value = mock_client

        result = await run_scorecard(
            subscription_id="sub-123",
            checklist_ids=["54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a"],
        )

        assert result["results"][0]["count"] == 42
        assert result["results"][0]["status"] == "fail"


@pytest.mark.asyncio
async def test_scorecard_sample_truncates_to_three() -> None:
    """Sample is capped at 3 rows even if more violations exist."""
    many_rows = [{"id": f"res-{i}"} for i in range(10)]

    with patch(
        "mcp_server_azure_architect.scorecard._get_resource_graph_client"
    ) as mock_client_factory:
        mock_client = Mock()
        mock_client.resources = Mock(return_value=_mock_arg_response(many_rows))
        mock_client_factory.return_value = mock_client

        result = await run_scorecard(
            subscription_id="sub-123",
            checklist_ids=["54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a"],
        )

        assert result["results"][0]["count"] == 10
        assert len(result["results"][0]["sample"]) == 3


@pytest.mark.asyncio
async def test_scorecard_pillar_filter() -> None:
    """Pillar filter limits queries to one pillar."""
    with patch(
        "mcp_server_azure_architect.scorecard._get_resource_graph_client"
    ) as mock_client_factory:
        mock_client = Mock()
        mock_client.resources = Mock(return_value=_mock_arg_response([]))
        mock_client_factory.return_value = mock_client

        result = await run_scorecard(
            subscription_id="sub-123",
            pillar="checklist",
        )

        # All results should be from checklist pillar
        for r in result["results"]:
            assert r["pillar"] == "checklist"


@pytest.mark.asyncio
async def test_scorecard_cap_at_25_queries() -> None:
    """Explicit checklist_ids exceeding 25 raises ValueError."""
    with pytest.raises(ValueError) as excinfo:
        await run_scorecard(
            subscription_id="sub-123",
            checklist_ids=[f"id-{i}" for i in range(30)],
        )

    assert "exceeds cap of 25" in str(excinfo.value)


@pytest.mark.asyncio
async def test_scorecard_truncates_full_sweep_over_25() -> None:
    """Full sweep over 25 queries slices to first 25 alphabetical and sets truncated=True."""
    # This test relies on the vendored snapshot having fewer than 25 queries;
    # if that changes, mock list_query_ids to return 30 fake IDs.
    with patch(
        "mcp_server_azure_architect.scorecard.list_query_ids"
    ) as mock_list:
        mock_list.return_value = [f"id-{i:03d}" for i in range(30)]

        with patch(
            "mcp_server_azure_architect.scorecard.get_query"
        ) as mock_get:
            mock_get.return_value = {
                "kql": "resources | project id",
                "pillar": "checklist",
                "citation": "test",
            }

            with patch(
                "mcp_server_azure_architect.scorecard._get_resource_graph_client"
            ) as mock_client_factory:
                mock_client = Mock()
                mock_client.resources = Mock(return_value=_mock_arg_response([]))
                mock_client_factory.return_value = mock_client

                result = await run_scorecard(subscription_id="sub-123")

                assert result["truncated"] is True
                assert result["aggregate"]["total"] == 25


@pytest.mark.asyncio
async def test_scorecard_by_pillar_breakdown() -> None:
    """Aggregate includes by_pillar breakdown."""
    with patch(
        "mcp_server_azure_architect.scorecard._get_resource_graph_client"
    ) as mock_client_factory:
        mock_client = Mock()
        mock_client.resources = Mock(return_value=_mock_arg_response([]))
        mock_client_factory.return_value = mock_client

        result = await run_scorecard(
            subscription_id="sub-123",
            checklist_ids=[
                "54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a",  # checklist pillar
                "e8aa1e41-870d-4968-94c6-77be14f510ac",  # graph pillar
            ],
        )

        by_pillar = result["aggregate"]["by_pillar"]
        assert "checklist" in by_pillar
        assert "graph" in by_pillar
        assert by_pillar["checklist"]["pass"] == 1
        assert by_pillar["graph"]["pass"] == 1


@pytest.mark.asyncio
async def test_scorecard_citation_included() -> None:
    """Each result includes citation from the vendored manifest."""
    with patch(
        "mcp_server_azure_architect.scorecard._get_resource_graph_client"
    ) as mock_client_factory:
        mock_client = Mock()
        mock_client.resources = Mock(return_value=_mock_arg_response([]))
        mock_client_factory.return_value = mock_client

        result = await run_scorecard(
            subscription_id="sub-123",
            checklist_ids=["54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a"],
        )

        assert result["results"][0]["citation"]
        assert "martinopedal" in result["results"][0]["citation"]
        assert "54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a" in result["results"][0]["citation"]


def test_scorecard_no_azure_sdk_at_module_import() -> None:
    """Importing scorecard module must not pull in azure-mgmt-resourcegraph (cold-start guard)."""
    # Pop the module if already loaded
    sys.modules.pop("mcp_server_azure_architect.scorecard", None)
    for name in list(sys.modules):
        if name.startswith("azure.mgmt.resourcegraph"):
            sys.modules.pop(name, None)

    import mcp_server_azure_architect.scorecard  # noqa: F401

    leaked = [
        name for name in sys.modules if name.startswith("azure.mgmt.resourcegraph")
    ]
    assert leaked == [], f"scorecard module leaked Azure SDK imports: {leaked}"


@pytest.mark.asyncio
async def test_alz_scorecard_tool_registered() -> None:
    """alz_scorecard tool is registered with FastMCP with expected schema."""
    tools = mcp._tool_manager.list_tools()
    tool = next((t for t in tools if t.name == "alz_scorecard"), None)

    assert tool is not None, "alz_scorecard should be registered"
    assert tool.description is not None
    assert "scorecard" in tool.description.lower()

    schema = tool.parameters
    assert "subscription_id" in schema["properties"]
    assert schema["properties"]["subscription_id"]["type"] == "string"
    assert "subscription_id" in schema.get("required", [])
