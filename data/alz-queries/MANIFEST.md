# ALZ query snapshot manifest

Refreshed automatically; see .github/workflows/refresh-alz-snapshot.yml

Vendored at: 2026-05-12T21:52:10Z

This snapshot is pinned to commit SHAs. No `main` or `latest` references are used for source content.

## Refresh cadence

Vendored snapshots are refreshed automatically on a **weekly cadence** (Monday 06:00 UTC) via `.github/workflows/refresh-alz-snapshot.yml`. The workflow:

1. Fetches each upstream `commit_sha` listed in `manifest.json`.
2. Runs `scripts/refresh_alz_snapshot.py` to extract queryable items.
3. Recomputes SHA-256 integrity hashes per file.
4. Opens a PR if any content changed.

**Pinning to a snapshot:** Consumers who need reproducible builds should pin to a specific release tag (`pip install mcp-server-azure-architect==X.Y.Z`) rather than tracking `main`. Each release embeds the manifest snapshot active at release time.

**Manual refresh:** Maintainers can trigger an out-of-band refresh by running `python scripts/refresh_alz_snapshot.py` locally and committing the result.

## Sources

### martinopedal/alz-checklist-queries

- commit_sha: `e7641beeda0126cc78825f8b77764c379552f3e1`
- ref: `commit:e7641beeda0126cc78825f8b77764c379552f3e1`
- vendored_at: `2026-04-22T12:35:39Z`
- source_file: `queries/alz_all_queries.json`
- checklist_ids: `54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a, 348ef254-c27d-442e-abba-c7571559ab91`
- file_count: `2`

### martinopedal/alz-graph-queries

- commit_sha: `448998d01000e7f863d3c1f8876787fd2234a77b`
- ref: `commit:448998d01000e7f863d3c1f8876787fd2234a77b`
- vendored_at: `2026-05-12T21:52:10Z`
- source_file: `queries/alz_additional_queries.json`
- checklist_ids: `e8aa1e41-870d-4968-94c6-77be14f510ac, 667313b4-f566-44b5-b984-a859c773e7d2`
- file_count: `2`
