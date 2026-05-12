# ADR-002: ALZ Query Vendoring Policy

## Status

Accepted (2026-05-12, Atlas)

## Context

The project provides native tools for Azure architects, including named ALZ checklist queries, ALZ Corp scorecard, quota planner, and Advisor surfacing. These tools consume KQL queries from upstream repositories: `martinopedal/alz-checklist-queries` and `martinopedal/alz-graph-queries`.

The vendoring decision must address:

1. **Stability and offline capability.** Queries must not depend on runtime network access to upstream repos.
2. **Auditability and reproducibility.** Every query must cite the upstream source and commit SHA, enabling reproducible builds and traceability.
3. **Drift management.** Drift from upstream is explicit and reviewable via pull request, not silent.
4. **Licensing and attribution.** Source repos may carry distinct licenses (e.g., MIT). Attribution stays in the snapshot manifest.
5. **Refresh cadence.** Maintenance burden is manageable without blocking the main development cycle.

Per PR #27 (ALZ snapshot implementation), the team already vendored the snapshot under `data/alz-queries/` with a pinned manifest. This ADR ratifies that approach and documents the refresh policy.

## Decision

**Vendor ALZ queries as a snapshot under `data/alz-queries/`, pinned by upstream commit SHA in `manifest.json`. Maintain both a machine-readable manifest and a human-readable changelog. Refresh procedure is explicit and Atlas-owned.**

### Structure

```
data/alz-queries/
├── manifest.json           # Machine-readable: sources, commit SHAs, vendored_at timestamps
├── MANIFEST.md             # Human-readable: checklist IDs, file counts, changelog
├── checklist/              # Queries from alz-checklist-queries
│   └── {checklist-id}.kql  # Named by checklist UUID
└── graph/                  # Queries from alz-graph-queries
    └── {query-id}.kql      # Named by query UUID
```

### Manifest Schema

Each entry in `manifest.json` contains:

```json
{
  "repo": "martinopedal/alz-checklist-queries",
  "commit_sha": "e7641beeda0126cc78825f8b77764c379552f3e1",
  "ref": "commit:e7641beeda0126cc78825f8b77764c379552f3e1",
  "vendored_at": "2026-04-22T12:35:39Z",
  "subset": {
    "source_file": "queries/alz_all_queries.json",
    "checklist_ids": ["54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a"],
    "files": ["data/alz-queries/checklist/54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a.kql"]
  },
  "file_count": 1
}
```

### Citation Requirements

Every named query in native tools MUST cite:
- **Checklist ID:** UUID identifying the query in the ALZ framework.
- **Source commit:** The commit SHA from the upstream repo where the query originates.
- **Vendored timestamp:** When the query was copied into this snapshot.

This is non-negotiable. Citations are enforced by tooling (future CI gate) and manual review.

### Alternatives Considered and Rejected

1. **Fork the upstream repos (rejected).**  
   - Drift management nightmare. Each divergence must be manually tracked and merged.
   - No clear synchronization path back to upstream.
   - Licensing and attribution become ambiguous.

2. **Git submodule (rejected).**  
   - Poor packaging story for MCP server distribution. Tools like `uvx` or `pip` struggle with submodule initialization.
   - Increases onboarding friction for contributors.
   - Offline capability requires pre-cloning submodules.

3. **Runtime fetch from GitHub (rejected).**  
   - Network dependency breaks offline usage and auditing.
   - Breaks reproducible builds if upstream changes.
   - Adds latency to tool startup and complexity to error handling.
   - Violates "no external network calls" for read-only tooling.

4. **No vendoring at all (rejected).**  
   - Cannot ship static query catalogs without vendoring.
   - Breaks the "read-only + offline-capable" requirement.

## Consequences

### Enables

1. **Offline capability.** Native tools operate without network access to upstream repos. Deployments are self-contained.
2. **Reproducible builds.** Every artifact pins the exact query versions via commit SHA. Builds are deterministic across time and machines.
3. **Explicit drift tracking.** Upstream changes are visible via git diff. PRs include a changelog summarizing query modifications, additions, and removals.
4. **Licensing and attribution.** `MANIFEST.md` records the license and source repo for each query cohort. Users can audit compliance.
5. **Auditability.** Every query carries checklist ID and source commit. Integration with CMMC or Azure Governance frameworks is traceable.

### Costs

1. **Manual refresh discipline.** Staying in sync with upstream requires active maintenance. Automated scheduled PRs can mitigate this.
2. **Merge conflict potential.** If both this repo and upstream modify queries independently, manual resolution is required.
3. **Storage overhead.** Snapshot files in `data/alz-queries/` add ~50-100KB per 100 queries (typical KQL is 500-1000 bytes). Acceptable for source control.

### Refresh Procedure

**Cadence:** Weekly (automated via GitHub Actions, every Monday 06:00 UTC) or on-demand via workflow_dispatch.

**Automation:** The refresh is automated via `.github/workflows/refresh-alz-snapshot.yml` and `scripts/refresh_alz_snapshot.py`. The workflow:

1. Fetches latest commit SHAs from both upstream repos via GitHub API
2. Compares against pinned SHAs in `manifest.json`
3. If drift detected: clones repos (shallow), extracts queries, updates manifests, opens PR
4. If no drift: exits cleanly (no-op)

The automated PR is labeled `squad,squad:atlas,vendoring` and assigned to Atlas for review.

**Manual Steps (if needed):**

1. **Check upstream HEAD:**
   ```bash
   cd data/alz-queries/
   gh api repos/martinopedal/alz-checklist-queries/commits/main \
     --jq '.sha | .[0:12]' > /tmp/upstream_sha.txt
   ```

2. **Run refresh script:**
   ```bash
   python scripts/refresh_alz_snapshot.py --dry-run  # check for drift
   python scripts/refresh_alz_snapshot.py            # apply changes
   ```

3. **Review changes:**
   ```bash
   git diff data/alz-queries/
   ```

4. **Commit and open PR:**
   ```bash
   git add data/alz-queries/
   git commit -m "chore(alz-queries): refresh snapshot to {short-sha}

   Updated manifest.json and MANIFEST.md. Summary:
   - alz-checklist-queries: {changes}
   - alz-graph-queries: {changes}

   Upstream diff: {link to github.com diff}
   Breaking changes: {none|list}
   
   Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
   git push -u origin chore/alz-refresh-{date}
   gh pr create --title "chore(alz-queries): refresh snapshot to {short-sha}" ...
   ```

5. **PR body MUST include:**
   - Per-source diff summary (new/changed/removed checklist IDs).
   - Breaking change callouts (e.g., if a query logic changed and affects results).
   - Query count delta (before/after).
   - Link to the upstream commit range.

6. **Review and merge:**  
   - Lead or designee reviews the diff and changelog for accuracy.
   - Once approved, merge to main.

### Validation and CI Gates

**Future:** Implement CI checks:

1. **Manifest schema validation:**  
   `manifest.json` must validate against JSON Schema. Each entry must have `repo`, `commit_sha`, `vendored_at`, `subset.checklist_ids`, `file_count`.

2. **Citation verification:**  
   Every KQL file header or metadata must reference its source checklist ID and commit SHA. A linter ensures no queries are "orphaned" (missing citations).

3. **Commit SHA resolution:**  
   For each pinned commit in `manifest.json`, validate that the commit exists in the upstream repo via `git ls-remote` or GitHub API.

4. **Snapshot integrity:**  
   Checksum each query file and record in a `CHECKSUM` manifest. On refresh, diff the checksums to detect accidental corruptions.

## References

1. **PR #27: ALZ Snapshot and Vendoring Implementation**  
   [github.com/martinopedal/mcp-server-azure-architect/pull/27](https://github.com/martinopedal/mcp-server-azure-architect/pull/27)  
   Demonstrates the vendoring structure and manifest format in practice.

2. **Issue #6: ADR-002 Vendoring Policy**  
   [github.com/martinopedal/mcp-server-azure-architect/issues/6](https://github.com/martinopedal/mcp-server-azure-architect/issues/6)  
   Requests formal documentation of the vendoring approach.

3. **Issue #17: ALZ Vendoring (merged via PR #27)**  
   [github.com/martinopedal/mcp-server-azure-architect/issues/17](https://github.com/martinopedal/mcp-server-azure-architect/issues/17)  
   Original spike on vendoring, concluded via PR #27.

4. **Upstream Source Repos:**
   - `martinopedal/alz-checklist-queries`: [github.com/martinopedal/alz-checklist-queries](https://github.com/martinopedal/alz-checklist-queries)
   - `martinopedal/alz-graph-queries`: [github.com/martinopedal/alz-graph-queries](https://github.com/martinopedal/alz-graph-queries)

5. **Azure Governance and Compliance:**  
   CMMC and Azure Governance frameworks rely on consistent query evaluation and auditability. Vendoring with citations supports compliance.

6. **MCP Specification: Read-Only Stance**  
   [modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification)  
   Companion servers are read-only by design. Vendoring reinforces this constraint.

## Attendants to This Decision

- **Atlas (ARG/KQL & ALZ Query Curator):** Owns refresh procedure and manifest maintenance.
- **Forge (MCP Server Runtime Engineer):** Ensures native tools register queries from the snapshot correctly.
- **Sentinel (Read-Only Enforcement):** Validates that no tool writes to upstream repos or modifies the snapshot at runtime.
- **Sage (Research & Examples):** Documents the refresh procedure in contributor guides.

## Lead Review

**Verdict:** APPROVE

**Rationale:** ADR-002 correctly ratifies the vendoring approach demonstrated in PR #27. The decision is well-founded:

- **Stability:** Pinning by commit SHA ensures reproducible builds and offline capability.
- **Auditability:** Citations to checklist IDs and source commits support compliance frameworks.
- **Maintainability:** Explicit refresh procedure with changelog avoids silent drift.
- **Alternatives considered:** Submodule, fork, and runtime-fetch options are correctly rejected with reasoning.
- **Consequences:** Clearly stated, with refresh procedure detailed enough for implementation.

The only follow-up (non-blocking):

- [ ] Implement CI gates for manifest schema and citation verification once baseline tooling is stable (ADR-003 or later).

---

## Addendum: Refresh Milestone Tracking (2026-05-12)

**First refresh target:** 2026-06-12 (one month post-acceptance)

The initial snapshot in PR #27 pins:
- `alz-checklist-queries`: commit `e7641beeda0126cc78825f8b77764c379552f3e1`
- `alz-graph-queries`: commit `8a3fddabcbf272a19a627770a0d33de5f4ace8ee`

**Assigned to:** Atlas  
**Status:** Pending (scheduled for next maintenance window)
