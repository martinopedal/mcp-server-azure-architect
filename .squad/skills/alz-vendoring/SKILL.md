# Skill: Vendoring Third-Party Query Catalogs by SHA

## Domain
ALZ query vendoring, reproducible snapshots, third-party catalog management

## Pattern
When vendoring a curated catalog from an upstream repository (e.g., alz-checklist-queries, alz-graph-queries), establish provenance, reproducibility, and auditability using a dual-manifest approach:

1. **Human-readable manifest (MANIFEST.md)**
   - Timestamp of vendoring
   - Source repository URLs
   - Pinned commit SHAs and refs (prefer tags where available)
   - Subset scope (which items were selected, not entire catalog)
   - File count per source

2. **Machine-readable manifest (manifest.json)**
   - Structured metadata matching human manifest
   - Extensible schema for tool consumption (e.g., alz_query_by_id MCP tool)
   - Array of sources, each with: repo, commit_sha, ref, vendored_at, subset (checklist_ids + file paths), file_count

3. **Canonical naming**
   - Name each item by its authoritative identifier (e.g., checklist UUID), not slugs
   - Avoids mapping tables and enables direct lookups

4. **Provenance comments**
   - Every item includes a comment block with source URL, item ID, and vendoring timestamp
   - Makes offline traceability possible (no external database required)

5. **Organization by source type**
   - Separate subdirectories per source (checklist/, graph/, etc.)
   - Scales to domain-specific groupings if needed later

## Rationale

**Why commit SHA pinning?**
- Deterministic: produces identical snapshots on re-run
- Auditable: diff between snapshots shows exactly what changed
- Secure: cannot silently pull breaking changes from upstream
- Archival: SHAs survive upstream rebase or deletion

**Why dual manifests?**
- MANIFEST.md is Git-native (readable in diffs, no parsing required)
- manifest.json is tool-native (enables automated refresh workflows, CI gates, catalog queries)
- Both synchronized ensures consistency

**Why subset tracking?**
- Not all queries in alz-checklist-queries may be relevant to this project
- Subset field enables delta detection (which items were added, removed, updated in next refresh)
- Machine-readable subset enables selective refresh (update only identity queries, keep governance frozen)

## Example Application

This pattern was applied in PR #27 (ALZ query vendoring). The snapshot pinned:
- martinopedal/alz-checklist-queries@e7641beeda... (2 queries)
- martinopedal/alz-graph-queries@8a3fddabc... (v1.1.0 tag, 2 queries)

manifest.json schema:
```json
{
  "sources": [
    {
      "repo": "martinopedal/alz-checklist-queries",
      "commit_sha": "...",
      "ref": "commit:...",
      "vendored_at": "2026-04-22T12:35:39Z",
      "subset": {
        "source_file": "queries/alz_all_queries.json",
        "checklist_ids": ["uuid1", "uuid2"],
        "files": ["data/alz-queries/checklist/uuid1.kql", "data/alz-queries/checklist/uuid2.kql"]
      },
      "file_count": 2
    }
  ]
}
```

## Verification Steps

When auditing a snapshot:
1. Verify SHAs exist in upstream repos: `gh api repos/{owner}/{repo}/commits/{sha}` (HTTP 200 = exists)
2. Verify manifest format: JSON schema + MANIFEST.md human-readable summary
3. Verify content safety: spot-check for leaked credentials, internal IDs, or non-public identifiers
4. Verify organization: items named by authoritative ID, organized by source type
5. Verify citations: provenance comments in every item with source URL + ID + timestamp

## Tools

- GitHub CLI (`gh api repos/{owner}/{repo}/commits/{sha}`) for SHA verification
- JSON schema validation for manifest.json structure
- Regex parsing of provenance comments for consistency checks
- Git diff to detect snapshot changes between refreshes

## Related

- PR #27: Initial ALZ snapshot vendoring (sets pattern)
- Issue #6: ADR-002 (codifies pattern into policy)
- Issue #17: Vendor ALZ queries (closes with PR #27)
