# Contributing to ALZ Query Snapshot

This directory contains vendored Azure Landing Zone checklist queries from upstream repositories. The vendoring model is documented in ADR-002 and ADR-006.

## Manifest Schema

**Current version:** 2 (as of issue #125, ADR-006)

`manifest.json` contains:
- `schema_version`: integer, currently 2
- `sources`: array of upstream source definitions

Each source contains:
- `repo`: GitHub repository slug
- `commit_sha`: pinned commit SHA
- `ref`: ref string (tag or commit)
- `vendored_at`: ISO 8601 timestamp
- `license`: SPDX identifier and upstream license URL
- `subset.source_file`: upstream JSON file path
- `subset.checklist_ids`: array of vendored checklist guids
- `subset.files`: array of `.kql` file paths in this repo
- `subset.sha256`: SHA-256 hashes of vendored `.kql` files
- `subset.queries`: object mapping checklist guid to metadata record

### Per-Query Metadata (Manifest v2)

Each query in `subset.queries[<guid>]` has:

**Mandatory:**
- `id`: checklist guid (same as key)
- `text`: checklist item text (may be empty if unavailable upstream)
- `category`: WAF category
- `subcategory`: WAF subcategory
- `severity`: High, Medium, or Low
- `source`: one of `vendored-checklist`, `vendored-graph`, `custom`
- `source_repo`: GitHub repository slug
- `source_ref`: ref (tag or commit) vendored from
- `source_file`: upstream file path within the repo
- `vendored_at`: ISO 8601 timestamp
- `vendored_path`: relative path within this repo
- `citation`: human-readable provenance
- `queryable`: bool, whether the query is executable via ARG

**Optional (where upstream provides data):**
- `scope_hint`: `subscription`, `management-group`, or `tenant`
- `tags`: array of strings
- `waf`: Well-Architected Framework pillar
- `upstream_reason`: the upstream `reason` field (noisy, preserved for transparency)

## Adding Custom Queries

Custom queries (queries not from upstream repos) should be placed in `data/alz-queries/custom/` and must follow this provenance pattern:

```json
{
  "source": "custom",
  "source_repo": "martinopedal/mcp-server-azure-architect",
  "source_ref": "package",
  "source_commit": "",
  "citation": "Custom query authored in martinopedal/mcp-server-azure-architect; see issue #N and ADR-006"
}
```

Key invariants:
- `source_commit` is **empty string** (not a fake SHA like `0000...` or `local`)
- `citation` references the issue number and ADR-006
- Queries are named by checklist guid: `<guid>.kql`
- Each query must have all mandatory metadata fields populated in `manifest.json`

See ADR-006 for design rationale.

## Refresh Procedure

Vendored snapshots are refreshed automatically via `.github/workflows/refresh-alz-snapshot.yml` (weekly, Monday 06:00 UTC).

Manual refresh:
```bash
cd /path/to/repo
python scripts/refresh_alz_snapshot.py --dry-run  # check for drift
python scripts/refresh_alz_snapshot.py            # apply changes
```

The refresh script:
1. Fetches upstream HEAD commits via GitHub API
2. Compares against pinned SHAs in `manifest.json`
3. If drift detected: clones repos (shallow), extracts queries, updates manifests, regenerates SHA-256 hashes
4. If no drift: exits cleanly (no-op)

**Atomic replace:** The script extracts to a tempdir, validates metadata completeness, then atomically replaces the destination directory. No mid-refresh deletes of existing files.

**Duplicate detection:** If the same guid appears in multiple sources, the script compares KQL + metadata bytes. Identical duplicates are accepted (logged at DEBUG). Different duplicates raise `ValueError` with both paths and remediation hint.

**Merged-catalogue handling:** If upstream `metadata.merged: true`, the script treats the two repos as one merged catalogue and skips the secondary fetch.

## Breaking Change Detection

`.github/workflows/breaking-change-detector.yml` runs on refresh PRs and detects:
- First table reference token changed in a `.kql` file (e.g., `resources` to `securityresources`)
- Query file removed

Non-breaking: header-only changes, body changes with same first token, new queries added.

Override with `breaking-change-approved` label if intentional (e.g., upstream schema update).

## SHA-256 Integrity Verification

Each `.kql` file has a SHA-256 hash recorded in `manifest.json`. CI validates hashes on every build before tests run. Tampered files trigger build failure.

Regenerate hashes:
```bash
python scripts/verify_query_integrity.py --update
```

The weekly refresh workflow automatically regenerates hashes after pulling new queries.

## Source Enum

`source` field values:
- `vendored-checklist`: queries from `martinopedal/alz-checklist-queries`
- `vendored-graph`: queries from `martinopedal/alz-graph-queries`
- `custom`: queries authored in this repo (not from upstream)

Legacy values `checklist` and `graph` (pre-v2) are accepted by the loader for backward compatibility but map to `vendored-checklist` and `vendored-graph` internally.

## References

- ADR-002: ALZ Query Vendoring Policy (storage model, refresh cadence)
- ADR-006: ALZ Query Metadata Schema and Custom Provenance (manifest v2, custom-query pattern)
- `scripts/refresh_alz_snapshot.py`: automated refresh implementation
- `.github/workflows/refresh-alz-snapshot.yml`: weekly cron workflow
- `.github/workflows/breaking-change-detector.yml`: CI gate for refresh PRs
