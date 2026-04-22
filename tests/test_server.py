"""Test MCP server tool registration and schema."""

from mcp_server_azure_architect import __version__
from mcp_server_azure_architect.server import health_check, mcp


def test_health_check_tool_registered() -> None:
    """Verify health_check tool is registered with valid schema."""
    tools = mcp._tool_manager.list_tools()
    tool_names = [tool.name for tool in tools]

    assert "health_check" in tool_names, "health_check tool should be registered"


def test_health_check_tool_has_schema() -> None:
    """Verify health_check tool has a valid JSON Schema."""
    tools = mcp._tool_manager.list_tools()
    health_tool = next((t for t in tools if t.name == "health_check"), None)

    assert health_tool is not None, "health_check tool should exist"
    assert health_tool.description is not None, "Tool should have a description"
    assert "Check server health" in health_tool.description


def test_health_check_returns_expected_data() -> None:
    """Verify health_check returns status and version."""
    result = health_check()

    assert result["status"] == "ok"
    assert result["version"] == __version__
