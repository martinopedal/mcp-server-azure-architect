"""CLI module for mcp-server-azure-architect."""

from mcp_server_azure_architect.server import server


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()

