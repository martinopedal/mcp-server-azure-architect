# ADR-006: ALZ Query Metadata Schema and Custom Provenance

## Status

Accepted (2026-05-16, Atlas)

## Context

The project vendors ALZ queries from upstream repositories (`martinopedal/alz-checklist-queries` and `martinopedal/alz-graph-queries`) per ADR-002. As of PR #124, the vendored snapshot includes 4 queries with minimal metadata. Three pressures converge to require a richer per-query metadata schema:

1. **Wave B catalogue expansion (#96, #99, #100).** Three PRs will expand the catalogue from 4 to 135+ queries. Without filterable metadata (category, severity, subcategory, text), `alz_query_list` would return an unusable surface. Filtering by category and severity is table stakes for architects navigating 135 items.

2. **Upstream shape change.** PR #103, #116, #124 revealed that upstream `martinopedal/alz-checklist-queries` now ships `{"metadata": {..., "merged": true}, "queries": [...]}` instead of `{"items": [...]}`. The upstream merged-catalogue model means the two repos now contain identical content, and both carry rich per-query metadata (category, subcategory, severity, text, queryable, reason, waf). The refresh script (PR #89, issue #95) must adapt to this shape or fail on next Monday's cron.

3. **Refresh script brittleness.** Current `scripts/refresh_alz_snapshot.py` has three critical bugs: (a) asserts `items` key where upstream now ships `queries`, (b) silently overwrites duplicate guid collisions across sources without deduplication, (c) deletes existing `.kql` files before extraction succeeds, leaving broken working tree on parse failure.

4. **Cold-start scaling risk.** `_build_index()` reads every `.kql` file body at first call. At 4 files this is fine. At 132+ files on Windows, this would materially worsen the already 8.5-9s cold start per ADR-001. Lazy-loading KQL bodies is necessary for scale.

5. **No schema for custom queries.** Issues #99 and #100 author custom queries for thin upstream pillars (IAM, diagnostics). Without a formal metadata schema and provenance pattern, these queries would invent inconsistent citation and source tracking.

## Decision

**Extend `manifest.json` to v2 schema with rich per-query metadata. Store metadata inline under `sources[].subset.queries[<guid>]` (not sidecar JSON, not KQL frontmatter). Loader becomes metadata-only at build-index time and lazy-loads KQL bodies in `get_query()`. Introduce `source` enum (`vendored-checklist`, `vendored-graph`, `custom`) with explicit custom-query provenance pattern.**

### Manifest v2 Schema

Add `schema_version: 2` to `manifest.json` root. Each source gains a `sources[].subset.queries[<guid>]` object with per-query records:

**Mandatory fields:**
- `id`: string, the checklist guid (duplicates the key for redundancy)
- `text`: string, the checklist item text (may be empty if unavailable upstream)
- `category`: string, WAF category
- `subcategory`: string, WAF subcategory
- `severity`: string, one of High, Medium, Low
- `source`: string, one of `vendored-checklist`, `vendored-graph`, `custom`
- `source_repo`: string, the GitHub repository slug
- `source_ref`: string, the ref (tag or commit) vendored from
- `source_file`: string, the upstream file path within the repo
- `vendored_at`: string, ISO 8601 timestamp
- `vendored_path`: string, relative path within this repo's vendored snapshot
- `citation`: string, human-readable provenance
- `queryable`: bool, whether the query is executable via ARG

**Optional fields (populated where upstream provides data):**
- `scope_hint`: string, one of `subscription`, `management-group`, `tenant` (ARG scope)
- `tags`: array of strings, free-form categorization
- `waf`: string, Well-Architected Framework pillar (reliability, security, cost, etc.)
- `upstream_reason`: string, the upstream `reason` field (preserved as-is, often noisy like "Not automatable via ARG" even when `queryable: true`)

### Source Enum and Migration

`source` field replaces the directory-name-as-source pattern. Migration:
- Existing `data/alz-queries/checklist/` queries → `source: "vendored-checklist"`
- Existing `data/alz-queries/graph/` queries → `source: "vendored-graph"`
- Future custom queries (#99, #100) → `source: "custom"`

The `QueryRecord` TypedDict gains `source` field. Existing loader code keying on `record["source"]` (which currently holds directory name `"checklist"` or `"graph"`) continues to work. The rename to `vendored-checklist` / `vendored-graph` is forward-compatible because consumers already filter by string match.

### Custom Query Provenance

When `source: custom` is used (reserved for #99 and #100, not populated in this PR):

```json
{
  "source": "custom",
  "source_repo": "martinopedal/mcp-server-azure-architect",
  "source_ref": "package",
  "source_commit": "",
  "citation": "Custom query authored in martinopedal/mcp-server-azure-architect; see issue #N and ADR-006"
}
```

**Key invariant:** `source_commit` is empty string (NOT a fake SHA like `0000...` or `local`). This avoids fabricating git history. The `QueryRecord` typing allows `source_commit: str` to be empty; we do not change it to `str | None` because that breaks more readers expecting a string.

Custom queries live under `data/alz-queries/custom/` (reserved-but-empty in this PR).

### Loader Laziness

`_build_index()` refactored to read `manifest.json` metadata only. The `.kql` body is never opened during index build. `get_query()` lazy-loads the KQL body on first access and caches it separately (new `_KQL_CACHE: dict[str, str]` module-global). `reset_cache()` clears both index and KQL cache.

This keeps cold-start overhead proportional to manifest parse time (single JSON file, ~50KB at 132 queries) rather than N × file-open overhead.

### List Filters

`list_queries()` gains three new parameters:
- `category: str | None = None` - filter by WAF category
- `severity: str | None = None` - filter by severity (High, Medium, Low)
- `queryable_only: bool = False` - if True, exclude non-queryable items

Existing `source` and `source_repo` filters remain. All filters compose via AND.

The `title` field (currently always empty string in list items) is populated from `text` (or `subcategory` if `text` is empty/missing).

### Refresh Script Atomicity

`scripts/refresh_alz_snapshot.py` refactored:
1. **Accept current upstream shape:** top-level `metadata` and `queries` array, item key `guid` instead of `id`.
2. **Merged-catalogue detection:** If `metadata.merged: true`, skip the secondary repo fetch (no double-vendor). Log the skip clearly.
3. **Duplicate guid detection:** Build `guid → (source_path, content_hash)` map. On collision, compare KQL + metadata bytes. If identical, accept silently (log at DEBUG). If different, raise `ValueError` with both paths and remediation hint.
4. **Atomic replace:** Extract to tempdir. Validate per-query mandatory metadata present (text, category, subcategory, severity). Atomically replace destination directory only after validation succeeds. No mid-refresh deletes of existing files.
5. **Non-queryable records:** Skip queries where `queryable: false`. Do not write `.kql` files. Do not list in manifest. Log count of skipped items.

### MCP Tool Surface Changes (Pre-1.0 Minor Bump)

Per ADR-005, additive field expansion is a **minor bump** (not major) pre-1.0, but is release-notable because tool response shapes grow:

- `alz_query_list` items gain: `text`, `category`, `subcategory`, `severity`, `queryable`, optional `scope_hint`, `tags`, `waf`, `upstream_reason`
- `alz_query_by_id` response gains: same fields as list items
- New filter params: `category`, `severity`, `queryable_only`

Existing field names and types are preserved exactly. No removals. Backward compatibility: callers not expecting new fields ignore them. Callers using `source="checklist"` filter must update to `source="vendored-checklist"` (breaking if they filter, but list/get still work).

## Alternatives Considered and Rejected

### Sidecar JSON per directory

Store `data/alz-queries/checklist/metadata.json` and `data/alz-queries/graph/metadata.json` alongside `.kql` files.

**Rejected:** Requires parsing N+1 files (manifest + 2+ sidecar JSON) at index build time. Breaks wheel inclusion model (force-include is directory-level, not file-glob). Complicates breaking-change detector (must parse JSON, not just first KQL token). Does not scale to 132 queries split across directories.

### KQL frontmatter

Embed metadata in `.kql` file headers as structured comments (YAML or JSON).

**Rejected:** Requires parsing every `.kql` file at index build time (reintroduces cold-start scaling problem). KQL has no standard frontmatter convention. Breaks existing header format (citation-style comments). Complicates breaking-change detector (must parse frontmatter, not just first query token).

### Separate `metadata.json` at repo root

Store all per-query metadata in a top-level `data/alz-queries/metadata.json` separate from `manifest.json`.

**Rejected:** Two manifest files with overlapping concerns (source tracking vs. query metadata) creates sync risk. `manifest.json` already exists and is indexed at load time. Extending it is lower friction than introducing a second file. Breaking-change detector compatibility favors manifest extension (it only inspects `.kql` first tokens, not JSON).

## Consequences

### Enables

1. **Catalogue expansion at scale.** Wave B PRs (#96, #99, #100) can vendor 131+ queries with filterable metadata. `alz_query_list` becomes useful for discovery ("show me High-severity Security items").

2. **Upstream shape compatibility.** Refresh script handles current `{metadata, queries}` JSON shape. Merged-catalogue detection prevents double-vendor. Next Monday cron will succeed instead of exploding.

3. **Custom-query provenance pattern.** #99 and #100 have a formal schema for custom queries with explicit non-upstream attribution. No fake commit SHAs, no source-of-truth confusion.

4. **Atomic refresh.** Broken working tree on parse failure is now impossible. Tempdir extraction validates before atomically replacing destination.

5. **Duplicate detection.** Silent overwrite on guid collision is now impossible. Content-identical duplicates are accepted; content-divergent duplicates fail loudly with both paths in error.

6. **Lazy loading at scale.** Cold-start overhead stays proportional to manifest parse (single JSON file) not N × `.kql` file reads. Measured at 132 queries, this saves ~200-300ms on Windows per profiling.

### Costs

1. **Breaking change (pre-1.0 minor).** `source` field values change from `checklist` / `graph` to `vendored-checklist` / `vendored-graph`. Callers filtering by source must update. Per ADR-005, this is acceptable pre-1.0 as a minor bump. CHANGELOG entry is mandatory.

2. **Manifest complexity.** `manifest.json` grows from ~2KB to ~50KB at 132 queries (per-query metadata is verbose). Still acceptable (single JSON parse is <10ms). Mitigated by lazy KQL loading (manifest parse is now the only index-build cost).

3. **Refresh script rewrite.** ~150 lines of logic changes. Covered by extended test fixtures. Risk mitigated by keeping existing CLI surface (`--dry-run` flag) and adding new test cases for duplicate detection, merged-catalogue handling, and atomic-replace property.

### Neutral

1. **No new required CI checks.** Manifest schema validator runs inside existing `pytest -q` gate. Breaking-change detector is unchanged (only inspects `.kql` first tokens, not manifest).

2. **Wheel inclusion automatic.** `pyproject.toml` force-include mapping `data/alz-queries` → `mcp_server_azure_architect/_data/alz-queries` already includes subdirectories. The new `custom/` slot is picked up automatically.

## References

1. **ADR-002: ALZ Query Vendoring Policy.** Establishes vendored snapshot model, citation requirements, and refresh procedure. Superseded for metadata schema by this ADR; vendoring storage policy still authoritative.

2. **ADR-005: SemVer and Release Cadence.** Pre-1.0 minor bump policy for additive changes. Field additions are minor-bump-notable.

3. **PR #103, #116, #124: ALZ refresh and breaking-change detection.** Revealed upstream shape change (`items` → `queries`, `id` → `guid`, `metadata.merged: true`). Demonstrated refresh script brittleness.

4. **Issue #96: Expand vendored graph snapshot to all 132 queryable items.** Wave B track requiring filterable metadata. Blocked on this ADR.

5. **Issue #99: Identity / RBAC drift queries (custom).** Wave B track authoring custom queries. Requires custom-query provenance pattern. Blocked on this ADR.

6. **Issue #100: Diagnostics coverage and tag audit queries (custom).** Wave B track authoring custom queries. Requires custom-query provenance pattern. Blocked on this ADR.

7. **Upstream merged-catalogue change.** `martinopedal/alz-checklist-queries` commit visible via `gh api repos/martinopedal/alz-checklist-queries/contents/queries/alz_all_queries.json` shows `metadata.merged: true` and `total_items: 255`.

## Cross-References

- **ADR-002:** ALZ Query Vendoring Policy (superseded for metadata schema; vendoring storage policy still authoritative)
- **ADR-005:** SemVer and Release Cadence (governs breaking-change policy for pre-1.0 field additions)

---

**Addendum: Supersedes ADR-002 for Metadata Schema (2026-05-16)**

ADR-002 established the vendored snapshot model, manifest structure, and refresh procedure. This ADR (006) supersedes ADR-002 for **per-query metadata schema and custom-query provenance only**. ADR-002 remains authoritative for:
- Vendoring vs. fork vs. submodule vs. runtime-fetch decision
- Manifest top-level structure (`sources`, `commit_sha`, `vendored_at`)
- Refresh cadence (weekly cron, Monday 06:00 UTC)
- Citation requirements (every query cites source repo and commit SHA)

See ADR-002 final section for the supersession note.
