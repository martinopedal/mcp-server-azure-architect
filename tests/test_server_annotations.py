"""Test MCP tool annotations for all registered tools.

Verifies that every tool has proper MCP annotations per issue #97 and
enforces the read-only invariant from ADR-003.
"""

from mcp_server_azure_architect.server import mcp


def test_all_tools_have_annotations() -> None:
    """Verify all tools have non-None annotations."""
    tools = mcp._tool_manager.list_tools()

    assert len(tools) == 7, f"Expected 7 tools, got {len(tools)}"

    for tool in tools:
        assert tool.annotations is not None, f"Tool {tool.name} missing annotations"


def test_all_tools_are_read_only() -> None:
    """Verify all tools have readOnlyHint=True (ADR-003 enforcement)."""
    tools = mcp._tool_manager.list_tools()

    for tool in tools:
        assert tool.annotations is not None, f"Tool {tool.name} missing annotations"
        assert tool.annotations.readOnlyHint is True, (
            f"Tool {tool.name} must have readOnlyHint=True per ADR-003, "
            f"got {tool.annotations.readOnlyHint}"
        )


def test_all_tools_are_non_destructive() -> None:
    """Verify all tools have destructiveHint=False (ADR-003 enforcement)."""
    tools = mcp._tool_manager.list_tools()

    for tool in tools:
        assert tool.annotations is not None, f"Tool {tool.name} missing annotations"
        assert tool.annotations.destructiveHint is False, (
            f"Tool {tool.name} must have destructiveHint=False per ADR-003, "
            f"got {tool.annotations.destructiveHint}"
        )


def test_all_tools_have_titles() -> None:
    """Verify all tools have non-empty human-readable titles."""
    tools = mcp._tool_manager.list_tools()

    for tool in tools:
        assert tool.annotations is not None, f"Tool {tool.name} missing annotations"
        assert tool.annotations.title, f"Tool {tool.name} must have a non-empty title"
        assert len(tool.annotations.title) > 0, f"Tool {tool.name} title is empty"


def test_tool_annotation_completeness() -> None:
    """Verify all annotation fields are populated for every tool."""
    tools = mcp._tool_manager.list_tools()

    for tool in tools:
        assert tool.annotations is not None, f"Tool {tool.name} missing annotations"

        # Check all expected fields are not None
        assert tool.annotations.title is not None, f"Tool {tool.name} missing title"
        assert (
            tool.annotations.readOnlyHint is not None
        ), f"Tool {tool.name} missing readOnlyHint"
        assert (
            tool.annotations.destructiveHint is not None
        ), f"Tool {tool.name} missing destructiveHint"
        assert (
            tool.annotations.idempotentHint is not None
        ), f"Tool {tool.name} missing idempotentHint"
        assert (
            tool.annotations.openWorldHint is not None
        ), f"Tool {tool.name} missing openWorldHint"


def test_expected_tool_titles() -> None:
    """Verify each tool has the expected human-readable title."""
    expected_titles = {
        "health_check": "Server: health check",
        "alz_query_by_id": "ALZ: get query by checklist ID",
        "alz_query_list": "ALZ: list available queries",
        "pricing_lookup_sku": "Azure Pricing: look up SKU retail price",
        "pricing_compare_skus": "Azure Pricing: compare multiple SKUs",
        "pricing_estimate_workload": "Azure Pricing: estimate workload cost",
        "alz_scorecard": "ALZ: run scorecard against subscription",
    }

    tools = mcp._tool_manager.list_tools()
    tool_map = {tool.name: tool for tool in tools}

    for tool_name, expected_title in expected_titles.items():
        assert tool_name in tool_map, f"Tool {tool_name} not registered"
        tool = tool_map[tool_name]
        assert tool.annotations is not None, f"Tool {tool_name} missing annotations"
        assert tool.annotations.title == expected_title, (
            f"Tool {tool_name} title mismatch: "
            f"expected '{expected_title}', got '{tool.annotations.title}'"
        )


def test_alz_and_pricing_tools_are_idempotent_and_open_world() -> None:
    """Verify ALZ and pricing tools have idempotentHint=True, openWorldHint=True."""
    # ALZ tools read vendored data + call Azure Resource Graph
    # Pricing tools call Azure Retail Prices API
    # Both are idempotent and interact with external systems
    alz_and_pricing_tools = {
        "alz_query_by_id",
        "alz_query_list",
        "alz_scorecard",
        "pricing_lookup_sku",
        "pricing_compare_skus",
        "pricing_estimate_workload",
    }

    tools = mcp._tool_manager.list_tools()

    for tool in tools:
        if tool.name in alz_and_pricing_tools:
            assert tool.annotations is not None
            assert (
                tool.annotations.idempotentHint is True
            ), f"Tool {tool.name} should have idempotentHint=True"
            assert (
                tool.annotations.openWorldHint is True
            ), f"Tool {tool.name} should have openWorldHint=True"


def test_health_check_is_closed_world() -> None:
    """Verify health_check has openWorldHint=False (no external calls)."""
    tools = mcp._tool_manager.list_tools()
    health_tool = next((t for t in tools if t.name == "health_check"), None)

    assert health_tool is not None, "health_check tool not found"
    assert health_tool.annotations is not None
    assert (
        health_tool.annotations.openWorldHint is False
    ), "health_check should have openWorldHint=False (no external calls)"
    assert (
        health_tool.annotations.idempotentHint is True
    ), "health_check should have idempotentHint=True (always returns same result)"
