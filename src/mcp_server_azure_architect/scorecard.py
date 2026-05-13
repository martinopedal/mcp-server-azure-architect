# READ-ONLY: this module queries Azure Resource Graph via ResourceGraphClient.resources();
# no mutation methods, no Begin*, Create*, Update*, Delete*, or Set* operations per ADR-003.
"""ALZ scorecard evaluation against Azure Resource Graph.

Runs vendored ALZ checklist queries against a subscription scope and aggregates
pass/fail/unknown results. Uses alz_queries.py as the source of truth for query
definitions (ADR-002).

Design notes (Forge, PR #10):

* **Lazy import.** azure.mgmt.resourcegraph is imported inside the function call
  boundary, not at module top. This keeps cold-start overhead within the 50ms budget.
* **Read-only.** Only ResourceGraphClient.resources() is called. No LROs, no mutations.
* **Bounded concurrency.** Max 5 in-flight queries via asyncio.Semaphore to be polite
  to Azure Resource Graph rate limits.
* **25-query cap.** If the caller requests more than 25 checklist IDs (via explicit
  list or full-sweep of a source dataset), slice to the first 25 alphabetical and set
  `truncated: true` in the result.
* **Citation.** Every scorecard row includes the `citation` from the manifest so
  the caller can trace upstream ALZ source.
* **Count convention.** Queries that aggregate violations surface a `Count` column.
  If the column is missing, fall back to `len(rows)`. Treat zero violations as pass.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from mcp_server_azure_architect.alz_queries import get_query, list_query_ids
from mcp_server_azure_architect.azure_client import get_credential, validate_caller_scope

if TYPE_CHECKING:
    from azure.mgmt.resourcegraph import ResourceGraphClient

_MAX_QUERIES_PER_CALL = 25
_MAX_CONCURRENT_QUERIES = 5


class ChecklistResult(TypedDict):
    """Per-checklist result in the scorecard."""

    checklist_id: str
    source: str
    status: Literal["pass", "fail", "unknown"]
    count: int
    citation: str
    sample: list[dict[str, Any]]
    error: str | None
    next_page_token: str | None


class AggregateSummary(TypedDict):
    """Top-level aggregate summary."""

    total: int
    pass_count: int
    fail: int
    unknown: int
    by_source: dict[str, dict[str, int]]


class ScorecardResult(TypedDict):
    """Full scorecard result shape."""

    subscription_id: str
    results: list[ChecklistResult]
    aggregate: AggregateSummary
    truncated: bool


def _get_resource_graph_client() -> ResourceGraphClient:
    """Lazily import and construct ResourceGraphClient with cloud-specific endpoint.

    Constructs ResourceGraphClient with base_url and credential_scopes derived
    from AZURE_CLOUD_NAME environment variable to support sovereign clouds.

    Returns:
        ResourceGraphClient configured for the active cloud environment.

    Raises:
        ValueError: If AZURE_CLOUD_NAME is set to an unknown cloud name.
    """
    from azure.mgmt.resourcegraph import ResourceGraphClient

    from ._clouds import get_cloud_config

    cloud = get_cloud_config()
    return ResourceGraphClient(
        credential=get_credential(),
        base_url=cloud.arm_endpoint,
        credential_scopes=[cloud.arm_scope],
    )


async def _run_single_query(
    client: ResourceGraphClient,
    subscription_id: str,
    checklist_id: str,
    semaphore: asyncio.Semaphore,
    page_size: int = 1000,
    page_token: str | None = None,
) -> ChecklistResult:
    """Run one ALZ query against Resource Graph and return a ChecklistResult.

    Args:
        client: ResourceGraphClient instance.
        subscription_id: Azure subscription ID to scope the query.
        checklist_id: Vendored ALZ checklist ID.
        semaphore: Concurrency limiter.
        page_size: Maximum number of items per page (default 1000, max 5000).
        page_token: Continuation token from previous page for pagination.

    Returns:
        ChecklistResult with status (pass/fail/unknown), count, sample, and error if any.
    """
    async with semaphore:
        try:
            record = get_query(checklist_id)
            kql = record["kql"]
            citation = record["citation"]
            source = record["source"]

            # Wrap sync SDK call in asyncio.to_thread for concurrency
            def _blocking_call() -> Any:
                from azure.mgmt.resourcegraph.models import QueryRequest, QueryRequestOptions

                options = QueryRequestOptions(
                    top=page_size,
                    skip_token=page_token,
                )
                query = QueryRequest(
                    subscriptions=[subscription_id],
                    query=kql,
                    options=options,
                )
                return client.resources(query)

            # Apply 60-second timeout to prevent DoS via large query results
            try:
                response = await asyncio.wait_for(asyncio.to_thread(_blocking_call), timeout=60.0)
            except TimeoutError:
                raise Exception(
                    "Query timed out after 60s. Narrow the scope or increase pagination."
                ) from None

            rows = response.data if hasattr(response, "data") else []
            next_page_token = getattr(response, "skip_token", None)

            if not rows:
                # No violations found
                return ChecklistResult(
                    checklist_id=checklist_id,
                    source=source,
                    status="pass",
                    count=0,
                    citation=citation,
                    sample=[],
                    error=None,
                    next_page_token=next_page_token,
                )

            # Try to extract Count column, fall back to len(rows)
            count = 0
            if rows and isinstance(rows[0], dict) and "Count" in rows[0]:
                # Query aggregates; take first row's Count column
                count = int(rows[0]["Count"])
            else:
                # Query returns raw violations; count them
                count = len(rows)

            # Take first 3 rows as sample
            sample = rows[:3] if isinstance(rows, list) else []

            status: Literal["pass", "fail", "unknown"] = "fail" if count > 0 else "pass"

            return ChecklistResult(
                checklist_id=checklist_id,
                source=source,
                status=status,
                count=count,
                citation=citation,
                sample=sample,
                error=None,
                next_page_token=next_page_token,
            )

        except LookupError as e:
            # checklist_id not in vendored snapshot
            return ChecklistResult(
                checklist_id=checklist_id,
                source="unknown",
                status="unknown",
                count=0,
                citation="",
                sample=[],
                error=str(e),
                next_page_token=None,
            )
        except Exception as e:
            # ARG query failed or other error
            return ChecklistResult(
                checklist_id=checklist_id,
                source="unknown",
                status="unknown",
                count=0,
                citation="",
                sample=[],
                error=str(e),
                next_page_token=None,
            )


async def run_scorecard(
    subscription_id: str,
    source: str | None = None,
    checklist_ids: list[str] | None = None,
    page_size: int | None = None,
    page_token: str | None = None,
) -> ScorecardResult:
    """Run ALZ scorecard for a subscription.

    Args:
        subscription_id: Azure subscription ID to evaluate.
        source: Optional source dataset filter (e.g., "checklist", "graph"). If provided,
            only queries from that source are run.
        checklist_ids: Optional explicit list of checklist IDs to run. If provided,
            overrides source filter and runs only these queries.
        page_size: Maximum number of items per page in Azure Resource Graph queries
            (default 1000, max 5000). Each checklist query respects this limit.
        page_token: Continuation token from previous page for pagination. Pass the
            next_page_token from a previous result to fetch the next page.

    Returns:
        ScorecardResult with per-checklist results and aggregate summary.

    Raises:
        ValueError: if explicit checklist_ids exceeds 25 or page_size is out of bounds.
        PermissionError: if subscription_id is not in the caller's scope (Threat S1).
    """
    # Validate that subscription_id is in caller's scope (issue #57, Threat S1)
    credential = get_credential()
    if not validate_caller_scope(subscription_id, credential):
        raise PermissionError(
            "Subscription ID is not in your scope. "
            "Ensure you have access to the requested subscription."
        )

    # Validate page_size and apply default
    if page_size is None:
        page_size = 1000
    elif not (1 <= page_size <= 5000):
        raise ValueError(f"page_size must be between 1 and 5000 (got {page_size}).")

    # Determine which checklist IDs to run
    if checklist_ids is not None:
        if len(checklist_ids) > _MAX_QUERIES_PER_CALL:
            raise ValueError(
                f"checklist_ids exceeds cap of {_MAX_QUERIES_PER_CALL}. "
                f"Requested {len(checklist_ids)}."
            )
        ids_to_run = checklist_ids
        truncated = False
    else:
        # Full sweep or source-filtered sweep
        all_ids = list_query_ids()
        if source:
            # Filter by source
            filtered = []
            for cid in all_ids:
                try:
                    record = get_query(cid)
                    if record["source"] == source:
                        filtered.append(cid)
                except LookupError:
                    pass
            ids_to_run = filtered
        else:
            ids_to_run = all_ids

        # Apply cap and truncate if needed
        if len(ids_to_run) > _MAX_QUERIES_PER_CALL:
            ids_to_run = sorted(ids_to_run)[:_MAX_QUERIES_PER_CALL]
            truncated = True
        else:
            truncated = False

    # Run queries concurrently with bounded semaphore
    client = _get_resource_graph_client()
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_QUERIES)

    tasks = [
        _run_single_query(client, subscription_id, cid, semaphore, page_size, page_token)
        for cid in ids_to_run
    ]
    results = await asyncio.gather(*tasks)

    # Aggregate
    total = len(results)
    pass_count = sum(1 for r in results if r["status"] == "pass")
    fail = sum(1 for r in results if r["status"] == "fail")
    unknown = sum(1 for r in results if r["status"] == "unknown")

    # By-source breakdown
    by_source: dict[str, dict[str, int]] = {}
    for result in results:
        s = result["source"]
        if s not in by_source:
            by_source[s] = {"pass": 0, "fail": 0, "unknown": 0}
        by_source[s][result["status"]] += 1

    aggregate = AggregateSummary(
        total=total,
        pass_count=pass_count,
        fail=fail,
        unknown=unknown,
        by_source=by_source,
    )

    return ScorecardResult(
        subscription_id=subscription_id,
        results=list(results),
        aggregate=aggregate,
        truncated=truncated,
    )
