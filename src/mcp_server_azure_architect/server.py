"""FastMCP server instance and tool definitions."""

from mcp.server.fastmcp import FastMCP

from mcp_server_azure_architect import __version__

mcp = FastMCP("azure-architect")


@mcp.tool()
def health_check() -> dict[str, str]:
    """Check server health and version.

    Returns:
        A dictionary with status and version information.
    """
    return {
        "status": "ok",
        "version": __version__,
    }
