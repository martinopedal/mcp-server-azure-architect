"""FastMCP server instance and tool definitions."""

from mcp.server.fastmcp import FastMCP

from mcp_server_azure_architect import __version__
from mcp_server_azure_architect.alz_queries import get_query

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


@mcp.tool()
def alz_query_by_id(checklist_id: str) -> dict[str, str]:
    """Look up a vendored Azure Landing Zone (ALZ) checklist query by ID.

    Returns the KQL query text plus source metadata (repo, commit SHA, ref,
    citation) so the caller can run the query against Azure Resource Graph
    and reference the upstream ALZ checklist item.

    Read-only: this tool performs a static lookup against the vendored ALZ
    snapshot under `data/alz-queries/`. It does not call Azure and does not
    accept a subscription ID, so there is no confused-deputy surface here.

    Args:
        checklist_id: The ALZ checklist item ID (matches the vendored
            `.kql` filename stem).

    Returns:
        A dictionary with `checklist_id`, `kql`, `pillar`, `source_repo`,
        `source_commit`, `source_ref`, `source_file`, `vendored_at`,
        `vendored_path`, and `citation`.

    Raises:
        LookupError: if the checklist ID is not in the vendored snapshot.
    """
    record = get_query(checklist_id)
    return {key: str(value) for key, value in record.items()}
