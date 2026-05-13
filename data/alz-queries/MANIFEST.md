# ALZ query snapshot manifest

Refreshed automatically; see .github/workflows/refresh-alz-snapshot.yml

This snapshot is pinned to commit SHAs. No `main` or `latest` references are used for source content.

## Sources

### martinopedal/alz-checklist-queries

- commit_sha: `e7641beeda0126cc78825f8b77764c379552f3e1`
- ref: `commit:e7641beeda0126cc78825f8b77764c379552f3e1`
- vendored_at: `2026-05-13T09:27:15+00:00`
- source_file: `queries/alz_all_queries.json`
- file_count: `173`
- query_count: `173`

### martinopedal/mcp-server-azure-architect

- commit_sha: (none - custom queries)
- ref: `custom`
- vendored_at: `2026-05-16T<timestamp>`
- source_file: `custom/`
- file_count: `5`
- query_count: `5`

Custom identity/RBAC queries:
- `06f994c5-0074-437a-8fe7-76ad7270c02b`: Custom RBAC roles enumeration (Medium)
- `464f1e97-148f-4250-a716-d22b289bac41`: Classic administrators detection (High)
- `decc6b2b-9a5b-4261-a2f7-eac632b550fe`: Orphaned managed identities (Medium)
- `fe60141f-7d13-4ad5-90f0-cbf5d2ee249f`: Privileged role assignments audit (High)
- `bc5a2107-737a-4f9a-bd70-680c9ed28b8b`: Service principals with RBAC (Medium)
