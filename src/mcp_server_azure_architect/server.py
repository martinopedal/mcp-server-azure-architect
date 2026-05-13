"""FastMCP server instance and tool definitions."""

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from mcp_server_azure_architect import __version__
from mcp_server_azure_architect.alz_queries import get_query, list_queries
from mcp_server_azure_architect.audit import audit_log_tool
from mcp_server_azure_architect.pricing import (
    WorkloadSpec,
)
from mcp_server_azure_architect.pricing import (
    pricing_compare_skus as _pricing_compare_skus,
)
from mcp_server_azure_architect.pricing import (
    pricing_estimate_workload as _pricing_estimate_workload,
)
from mcp_server_azure_architect.pricing import (
    pricing_lookup_sku as _pricing_lookup_sku,
)
from mcp_server_azure_architect.scorecard import run_scorecard

mcp = FastMCP("azure-architect")


@mcp.tool(
    annotations=ToolAnnotations(
        title="Server: health check",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
)
@audit_log_tool
def health_check() -> dict[str, str]:
    """Check server health and version.

    Returns:
        A dictionary with status and version information.
    """
    return {
        "status": "ok",
        "version": __version__,
    }


@mcp.tool(
    annotations=ToolAnnotations(
        title="ALZ: get query by checklist ID",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
@audit_log_tool
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
        A dictionary with `checklist_id`, `kql`, `source`, `source_repo`,
        `source_commit`, `source_ref`, `source_file`, `vendored_at`,
        `vendored_path`, and `citation`.

    Raises:
        LookupError: if the checklist ID is not in the vendored snapshot.

    Note: Results may contain sensitive data (resource tags with secrets, connection
        strings in configurations, private IPs). Treat results as sensitive. Do not log,
        share, or persist results without review per your organization's data handling
        policy.
    """
    record = get_query(checklist_id)
    return {key: str(value) for key, value in record.items()}


@mcp.tool(
    annotations=ToolAnnotations(
        title="Azure Pricing: look up SKU retail price",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
@audit_log_tool
def pricing_lookup_sku(
    sku: str,
    region: str,
    term: Literal["ondemand", "1yr", "3yr"] = "ondemand",
    currency: str = "USD",
) -> dict[str, Any]:
    """Look up Azure retail pricing for a single SKU in a region.

    Calls the public Azure Retail Prices API. No auth, no Azure SDK, read-only.
    Results cached for 24h. Caveats: retail only (no EA/CSP), USD default,
    no real-time freshness SLA.
    """
    return _pricing_lookup_sku(sku=sku, region=region, term=term, currency=currency)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Azure Pricing: compare multiple SKUs",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
@audit_log_tool
def pricing_compare_skus(
    skus: list[str],
    region: str,
    term: str = "ondemand",
    currency: str = "USD",
) -> dict[str, Any]:
    """Compare retail pricing for multiple Azure SKUs side by side in one region.

    Wraps pricing_lookup_sku per SKU. Capped at 10 SKUs per call. Useful for
    sizing trade-off review. Raises ValueError if the cap is exceeded or skus
    is empty.
    """
    return _pricing_compare_skus(skus=skus, region=region, term=term, currency=currency)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Azure Pricing: estimate workload cost",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
@audit_log_tool
def pricing_estimate_workload(spec: dict[str, Any]) -> dict[str, Any]:
    """Estimate monthly cost for a structured workload specification.

    Composes pricing_lookup_sku results into a multi-line cost estimate with
    VM count, region, hours/month, and storage. Returns total_monthly (Decimal),
    currency, line_items, assumptions, and warnings. Retail prices only
    (no EA/CSP). Designed for sizing trade-off analysis and to feed alz_scorecard
    cost guardrail.
    """
    workload = WorkloadSpec.model_validate(spec)
    return _pricing_estimate_workload(spec=workload)


@mcp.tool(
    annotations=ToolAnnotations(
        title="ALZ: list available queries",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
@audit_log_tool
def alz_query_list(
    source: str | None = None,
    source_repo: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    """List vendored Azure Landing Zone (ALZ) checklist queries.

    Enumerate the vendored ALZ snapshot with optional filters by source dataset or
    source repository. Returns metadata for each query (checklist ID, source,
    source repo, citation) but not the full KQL text. Use alz_query_by_id to
    retrieve the full query.

    Read-only: this tool performs static enumeration of the vendored ALZ
    snapshot under `data/alz-queries/`. It does not call Azure and does not
    accept a subscription ID.

    Args:
        source: Optional source dataset filter (e.g., "checklist", "graph"). If provided,
            only queries from that source are returned.
        source_repo: Optional source repo filter (e.g.,
            "martinopedal/alz-checklist-queries"). If provided, only queries
            from that repo are returned.
        limit: Maximum number of items to return (default 200). If the filtered
            result set exceeds this limit, items are sliced alphabetically and
            truncated is set to True.

    Returns:
        A dictionary with `count` (int, total matching queries), `items` (list
        of dicts with checklist_id, source, source_repo, title, citation),
        `manifest_commit` (str, composite of source commits), `truncated` (bool),
        and `filters_applied` (dict with source and source_repo).

    Note: Results may contain sensitive data (resource tags with secrets, connection
        strings in configurations, private IPs). Treat results as sensitive. Do not log,
        share, or persist results without review per your organization's data handling
        policy.
    """
    result = list_queries(source=source, source_repo=source_repo, limit=limit)
    return result


@mcp.tool(
    annotations=ToolAnnotations(
        title="ALZ: run scorecard against subscription",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
@audit_log_tool
async def alz_scorecard(
    subscription_id: str,
    source: str | None = None,
    checklist_ids: list[str] | None = None,
    page_size: int | None = None,
    page_token: str | None = None,
) -> dict[str, Any]:
    """Run Azure Landing Zone (ALZ) scorecard for a subscription.

    Executes vendored ALZ checklist queries against Azure Resource Graph and
    returns a structured scorecard with per-checklist pass/fail/unknown status
    plus aggregate summary by source dataset.

    Read-only: calls ResourceGraphClient.resources() only. No mutations, no
    Begin*/Create*/Update*/Delete* operations per ADR-003.

    Security: Validates that subscription_id is in the caller's authorized scope
    by querying Azure Resource Manager (ARM) for accessible subscriptions. Rejects
    out-of-scope subscription IDs to defend against confused-deputy attacks (issue #57).
    Applies 60-second timeout to all Azure Resource Graph queries to prevent DoS via
    large result sets (issue #62).

    Args:
        subscription_id: Azure subscription ID to evaluate.
        source: Optional source dataset filter (e.g., "checklist", "graph"). If provided,
            only queries from that source are run.
        checklist_ids: Optional explicit list of checklist IDs to run. If provided,
            overrides source filter. Capped at 25 queries per call.
        page_size: Maximum number of items per page in Azure Resource Graph queries
            (default 1000, max 5000). Each checklist query respects this limit.
        page_token: Continuation token from previous page for pagination. Pass the
            next_page_token from a previous result to fetch the next page.

    Returns:
        ScorecardResult with `subscription_id`, `results` (list of per-checklist
        ChecklistResult with `next_page_token` if more results available), `aggregate`
        (total/pass/fail/unknown counts plus by_source breakdown), and `truncated`
        (bool, true if cap was applied).

    Raises:
        ValueError: if explicit checklist_ids exceeds 25 or page_size is out of bounds.
        PermissionError: if subscription_id is not in caller's scope.

    Note: Results may contain sensitive data (resource tags with secrets, connection
        strings in configurations, private IPs). Treat results as sensitive. Do not log,
        share, or persist results without review per your organization's data handling
        policy.
    """
    result = await run_scorecard(
        subscription_id=subscription_id,
        source=source,
        checklist_ids=checklist_ids,
        page_size=page_size,
        page_token=page_token,
    )
    return dict(result)
