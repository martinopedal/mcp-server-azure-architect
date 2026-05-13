# READ-ONLY: this module performs static lookups against vendored data; no
# Azure or filesystem writes. Per ADR-003, native tools backed by this loader
# expose the `_query_*` verb pattern and never construct an Azure SDK client.
"""Vendored ALZ checklist query loader.

Design notes (Forge, wave 4; Atlas refactor wave 11/issue #125):

* **Pure stdlib.** Only `json` and `pathlib` are imported. No Azure SDK, no
  httpx, no Pydantic. This keeps cold-start overhead at near zero (the module
  loads in under a millisecond) and preserves the read-only invariant by
  construction.
* **Lazy parse.** The manifest is parsed on first call and cached in a
  module-level singleton. Importing this module does not touch the filesystem.
* **Manifest v2 metadata-only index (issue #125).** `_build_index()` reads
  manifest.json per-query metadata but does NOT read .kql bodies. KQL bodies
  are lazy-loaded in `get_query()` and cached separately. This keeps cold-start
  overhead proportional to manifest parse (single JSON file) not N × file reads.
* **Source of truth.** Layout follows ADR-002 / PR #27, extended by ADR-006.
  The vendored snapshot lives at `data/alz-queries/` with `manifest.json`
  indexing checklist IDs to `.kql` files. Atlas owns the data; this module is
  a read-only consumer.
* **Confused-deputy mitigation (per Sentinel threat model, S1/E1).** The only
  caller-supplied input is `checklist_id`, which is matched against the
  vendored allowlist. There is no `subscription_id` surface here, so no
  Azure-scoped authorization decision is delegated to the caller. Future tools
  that take a `subscription_id` MUST validate caller scope separately.
* **Install layouts.** The loader resolves the data root in two locations to
  cover both `pip install -e .` (data sits at the repo root) and a built wheel
  (force-included under the package as `_data/alz-queries`). See
  `[tool.hatch.build.targets.wheel.force-include]` in `pyproject.toml`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import NotRequired, TypedDict

_MANIFEST_NAME = "manifest.json"
_MAX_AVAILABLE_IDS_IN_ERROR = 10
_DATA_PREFIX = ("data", "alz-queries")


class QueryRecord(TypedDict):
    """Return shape for a single vendored ALZ query lookup.

    Extended in manifest v2 (issue #125 / ADR-006) with rich per-query metadata.
    """

    checklist_id: str
    kql: str
    source: str
    source_repo: str
    source_commit: str
    source_ref: str
    source_file: str
    vendored_at: str
    vendored_path: str
    citation: str
    # Manifest v2 fields (additive, issue #125)
    text: str
    category: str
    subcategory: str
    severity: str
    queryable: bool
    # Optional v2 fields
    scope_hint: NotRequired[str]
    tags: NotRequired[list[str]]
    waf: NotRequired[str]
    upstream_reason: NotRequired[str]


def _resolve_data_root() -> Path:
    """Locate the vendored ALZ data directory.

    Tries the wheel-install location first (force-included under the package)
    then falls back to the editable / source-checkout layout (repo root).
    """
    package_dir = Path(__file__).resolve().parent

    wheel_path = package_dir / "_data" / "alz-queries"
    if (wheel_path / _MANIFEST_NAME).is_file():
        return wheel_path

    repo_path = package_dir.parent.parent / "data" / "alz-queries"
    if (repo_path / _MANIFEST_NAME).is_file():
        return repo_path

    raise FileNotFoundError(
        f"ALZ query manifest not found. Looked in {wheel_path} and {repo_path}."
    )


def _build_index(data_root: Path) -> dict[str, QueryRecord]:
    """Parse the manifest v2 and build the checklist_id -> QueryRecord index.

    Metadata-only: does NOT read .kql bodies (lazy-loaded in get_query).
    """
    manifest_path = data_root / _MANIFEST_NAME
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Schema version guard
    schema_version = raw.get("schema_version", 1)
    if schema_version < 2:
        raise ValueError(
            f"Manifest schema version {schema_version} is not supported. "
            f"Expected version 2 or higher. Run `python scripts/refresh_alz_snapshot.py` "
            f"to upgrade the manifest."
        )

    index: dict[str, QueryRecord] = {}
    for source in raw.get("sources", []):
        subset = source.get("subset", {})
        queries = subset.get("queries", {})

        for checklist_id, meta in queries.items():
            # Mandatory fields
            record = QueryRecord(
                checklist_id=str(meta["id"]),
                kql="",  # Lazy-loaded in get_query()
                source=str(meta["source"]),
                source_repo=str(meta["source_repo"]),
                source_commit=str(source["commit_sha"]),
                source_ref=str(meta["source_ref"]),
                source_file=str(meta["source_file"]),
                vendored_at=str(meta["vendored_at"]),
                vendored_path=str(meta["vendored_path"]),
                citation=str(meta["citation"]),
                text=str(meta.get("text", "")),
                category=str(meta["category"]),
                subcategory=str(meta["subcategory"]),
                severity=str(meta["severity"]),
                queryable=bool(meta["queryable"]),
            )

            # Optional fields
            if "scope_hint" in meta:
                record["scope_hint"] = str(meta["scope_hint"])
            if "tags" in meta:
                record["tags"] = list(meta["tags"])
            if "waf" in meta:
                record["waf"] = str(meta["waf"])
            if "upstream_reason" in meta:
                record["upstream_reason"] = str(meta["upstream_reason"])

            index[checklist_id] = record

    return index


_INDEX: dict[str, QueryRecord] | None = None
_KQL_CACHE: dict[str, str] = {}


def _get_index() -> dict[str, QueryRecord]:
    """Return the parsed manifest index, building it on first call."""
    global _INDEX
    if _INDEX is None:
        _INDEX = _build_index(_resolve_data_root())
    return _INDEX


def list_query_ids() -> list[str]:
    """Return the sorted list of vendored checklist IDs.

    Useful for diagnostics and for future tools that enumerate the catalog.
    """
    return sorted(_get_index().keys())


def get_query(checklist_id: str) -> QueryRecord:
    """Return the vendored query record for a checklist ID.

    KQL body is lazy-loaded on first access and cached.

    Raises:
        LookupError: if the ID is not in the vendored allowlist. The error
            message includes a capped sample of available IDs to aid recovery
            without dumping the full catalog.
    """
    index = _get_index()
    record = index.get(checklist_id)
    if record is None:
        available = sorted(index.keys())
        sample = available[:_MAX_AVAILABLE_IDS_IN_ERROR]
        suffix = (
            f" (showing first {_MAX_AVAILABLE_IDS_IN_ERROR} of {len(available)})"
            if len(available) > _MAX_AVAILABLE_IDS_IN_ERROR
            else ""
        )
        raise LookupError(
            f"checklist_id {checklist_id!r} not found in vendored ALZ "
            f"snapshot. Available: {sample}{suffix}."
        )

    # Lazy-load KQL body if not already cached
    if checklist_id not in _KQL_CACHE:
        data_root = _resolve_data_root()
        kql_path_str = record["vendored_path"]

        # Strip data/alz-queries/ prefix if present
        parts = Path(kql_path_str).parts
        if parts[: len(_DATA_PREFIX)] == _DATA_PREFIX:
            inside = Path(*parts[len(_DATA_PREFIX) :])
        else:
            inside = Path(kql_path_str)

        kql_path = data_root / inside
        kql_text = kql_path.read_text(encoding="utf-8").strip()
        _KQL_CACHE[checklist_id] = kql_text

    # Return a copy with the KQL body populated
    result = dict(record)
    result["kql"] = _KQL_CACHE[checklist_id]
    return result  # type: ignore[return-value]


def list_queries(
    source: str | None = None,
    source_repo: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    queryable_only: bool = False,
    limit: int = 200,
) -> dict[str, object]:
    """Enumerate vendored ALZ checklist queries with optional filters.

    Args:
        source: Optional source dataset filter (e.g., "vendored-checklist",
            "vendored-graph", "custom"). If provided, only queries from that
            source are returned. Legacy values "checklist" and "graph" are
            accepted for backward compatibility and map to "vendored-checklist"
            and "vendored-graph".
        source_repo: Optional source repo filter (e.g.,
            "martinopedal/alz-checklist-queries"). If provided, only queries
            from that repo are returned.
        category: Optional category filter (e.g., "Identity and Access Management").
            If provided, only queries matching this category are returned.
        severity: Optional severity filter (e.g., "High", "Medium", "Low").
            If provided, only queries matching this severity are returned.
        queryable_only: If True, exclude queries where queryable=false.
            Default is False (include all queries).
        limit: Maximum number of items to return (default 200). If the filtered
            result set exceeds this limit, items are sliced alphabetically by
            checklist_id and truncated is set to True.

    Returns:
        A dictionary with:
        - count: int, number of matching queries (before limit applied)
        - items: list of dicts, each with checklist_id, source, source_repo,
          title (populated from text or subcategory), citation, and v2 metadata
        - manifest_commit: str, composite of source commit SHAs from manifest
        - truncated: bool, True if limit was applied
        - filters_applied: dict with all filter parameters echoed
    """
    index = _get_index()

    # Backward compatibility: map legacy source values
    if source == "checklist":
        source = "vendored-checklist"
    elif source == "graph":
        source = "vendored-graph"

    # Apply filters
    filtered = [
        record
        for record in index.values()
        if (source is None or record["source"] == source)
        and (source_repo is None or record["source_repo"] == source_repo)
        and (category is None or record.get("category") == category)
        and (severity is None or record.get("severity") == severity)
        and (not queryable_only or record.get("queryable", True))
    ]

    # Sort alphabetically by checklist_id for deterministic output
    filtered.sort(key=lambda r: r["checklist_id"])

    count = len(filtered)
    truncated = count > limit
    if truncated:
        filtered = filtered[:limit]

    # Build items with v2 metadata
    items = []
    for r in filtered:
        item = {
            "checklist_id": r["checklist_id"],
            "source": r["source"],
            "source_repo": r["source_repo"],
            "title": r.get("text", "") or r.get("subcategory", ""),
            "citation": r["citation"],
            "category": r.get("category", ""),
            "subcategory": r.get("subcategory", ""),
            "severity": r.get("severity", ""),
            "queryable": r.get("queryable", True),
        }
        # Add optional fields if present
        if "scope_hint" in r:
            item["scope_hint"] = r["scope_hint"]
        if "tags" in r:
            item["tags"] = r["tags"]
        if "waf" in r:
            item["waf"] = r["waf"]
        if "upstream_reason" in r:
            item["upstream_reason"] = r["upstream_reason"]
        items.append(item)

    # Composite manifest_commit from all sources
    manifest_commit = _build_manifest_commit()

    return {
        "count": count,
        "items": items,
        "manifest_commit": manifest_commit,
        "truncated": truncated,
        "filters_applied": {
            "source": source,
            "source_repo": source_repo,
            "category": category,
            "severity": severity,
            "queryable_only": queryable_only,
        },
    }


def _build_manifest_commit() -> str:
    """Build a composite manifest commit string from all sources.

    Returns a semicolon-separated list of repo@commit pairs.
    """
    data_root = _resolve_data_root()
    manifest_path = data_root / _MANIFEST_NAME
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))

    commits = []
    for source in raw.get("sources", []):
        repo = str(source["repo"])
        commit = str(source["commit_sha"])
        commits.append(f"{repo}@{commit[:7]}")

    return "; ".join(commits)


def reset_cache() -> None:
    """Clear the cached manifest index and KQL body cache. Intended for tests."""
    global _INDEX, _KQL_CACHE
    _INDEX = None
    _KQL_CACHE = {}
