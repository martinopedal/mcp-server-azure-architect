"""Entry point for the MCP server."""

from mcp_server_azure_architect.server import mcp


def main() -> None:
    """Run the MCP server via stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
