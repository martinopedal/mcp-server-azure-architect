# ADR-004: Companion Server Selection Bar

## Status

Accepted (2026-05-12, Burke)

## Context

The mcp-server-azure-architect project ships a curated `mcp-config.json` with a set of companion MCP servers. These companions are not bundled with the server itself; instead, they are recommended via configuration and documentation, following the "complement, don't wrap" principle stated in AGENTS.md.

In Wave 2 (PR #23), Burke performed an initial audit of companion candidates and pinned versions for reproducibility. This ADR formalizes the criteria used in that audit, so that future companion selection follows consistent and documented standards.

### Why Curated Companions Matter

1. **No duplication.** Companions must not overlap with `azure-mcp`'s tool surface. Azure MCP already provides ARG queries, Advisor, Monitor, Policy, RBAC, AKS, and AppService tools. New companions extend into new domains (diagrams, IaC, Kubernetes inspection, documentation).

2. **Reproducibility.** Version pinning ensures users get the same toolset across sessions and deployments.

3. **Supply chain security.** Signed releases and maintenance signals give confidence that companions are actively maintained and not abandoned.

4. **Client compatibility.** Each MCP client has a different config schema and file location. Documenting install paths per client reduces friction.

5. **Read-only enforcement.** Since the server itself has no mutation tools, companions should also be read-only by default or shipped with read-only configuration.

### Current Kit Roster (Post-PR-#23)

From `.copilot/mcp-config.json`:

| Companion | Version | Vendor/Maintainer | Scope | Rationale |
|-----------|---------|-------------------|-------|-----------|
| **azure-mcp** | 2.0.1 | Microsoft | Azure REST APIs, Advisor, Monitor, Policy, RBAC, AKS, AppService | Stable semver release. Official Microsoft product. Signed via NuGet (NPM provenance). Source of truth for Azure resource queries. |
| **microsoft-learn** | hosted | Microsoft | Microsoft Learn documentation lookup | Grounded doc retrieval. Hosted endpoint. No self-host needed. Microsoft maintains. |
| **github** | latest | GitHub | GitHub API: repos, issues, PRs, actions | Narrow scope: version control + CI/CD inspection. GitHub's official server. Docker image. Requires GitHub PAT. Read-only by default. |
| **mermaid** | 0.4.1 | hustcc (community) | Diagram rendering from Mermaid syntax | Narrow scope: diagrams only. Stable semver. No write capability. Last release within 6 months. |
| **drawio** | 2.0.4 | lgazo (community) | Draw.io diagram creation and export | Narrow scope: diagrams only. Stable semver. No write capability. Last release within 6 months. |
| **kubernetes** | 0.0.53 | community | kubectl-based cluster inspection (live nodes, pods, config) | Narrow scope: k8s cluster inspection only. No mutations to cluster state. Compatible with AKS. |
| **terraform** | v0.5.1 | HashiCorp | Terraform registry lookup, plan, validate | Narrow scope: IaC tooling only. HashiCorp (ALLOWED-VENDOR). Official release channel. Read-only by design (plan, validate, no apply). Docker image. |

## Decision

A companion MCP server is included in the curated kit if and only if it meets ALL of the following criteria:

### Criterion 1: Stable Upstream

- **Requirement:** Upstream project publishes semver-tagged releases. No unversioned, HEAD-only, or "latest" images without stable tags.
- **Rationale:** Users and CI/CD must be able to pin exact versions. Prevents supply chain surprises.
- **Exception:** If upstream is Microsoft or a ALLOWED-VENDOR (HashiCorp, Google Cloud, AWS), continuous delivery with tested images is acceptable if release notes are published.

### Criterion 2: Signed Releases

- **Requirement:** Package signatures are available where the registry supports them:
  - **npm:** NPM provenance or signed tags.
  - **PyPI:** Sigstore or PGP signature.
  - **Docker:** OCI image signatures (cosign) or Docker Content Trust (DCT).
  - **GitHub:** Release assets with checksums or signatures.
- **Rationale:** Prevents tampering and supply chain attacks. Verifies package authenticity.
- **Exception:** If a widely-trusted vendor (Microsoft, HashiCorp) publishes via their official registry and the registry itself is signed, individual package signatures may be waived.

### Criterion 3: Narrow Scope

- **Requirement:** Single domain of responsibility. No general-purpose runtime or language servers that duplicate tool sets already available.
- **Examples of IN-SCOPE:** diagrams (mermaid, drawio), Kubernetes inspection, Terraform registry, GitHub API, documentation lookup.
- **Examples of OUT-OF-SCOPE:** Generic "filesystem-mcp" (overlaps with built-in tools), "shell-exec-mcp" (duplicates shell tools), any language runtime that competes with the MCP server runtime itself.
- **Rationale:** Keeps the kit focused and prevents feature bloat.

### Criterion 4: Complementary to azure-mcp

- **Requirement:** Does NOT duplicate azure-mcp's tool surface. Specifically:
  - No additional ARG or KQL query tools (azure-mcp is authoritative).
  - No Advisor, Monitor, Policy, RBAC, AKS, AppService, Key Vault, Storage, or other core Azure service tools.
  - No competing Azure authentication layers.
- **Rationale:** Single source of truth for Azure APIs. Prevents tool confusion and version skew.

### Criterion 5: Maintenance Signal

- **Requirement:** Last release within approximately 6 months, OR upstream is on the ALLOWED-VENDOR list (Microsoft, HashiCorp, Google Cloud, AWS, Linux Foundation).
- **Rationale:** Active maintenance reduces security debt and likelihood of abandonment.
- **Exception:** If upstream is dormant but stable (e.g., a small utility with no known CVEs), document the exceptional rationale in the compatibility matrix.

### Criterion 6: Read-Only by Design or Config

- **Requirement:** Companion either has no mutation capabilities, OR ships with read-only configuration (e.g., Terraform plan without apply, GitHub API without secrets).
- **Rationale:** Aligns with project constraint: read-only everywhere.
- **Example:** `terraform-mcp-server` is included because it only provides `terraform plan` and `terraform validate` (read-only); `terraform apply` is not exposed.

### Criterion 7: Documented Install Path

- **Requirement:** Installation is documented for at least one major MCP client (Copilot CLI, Claude Desktop, Cursor, VS Code Copilot). Per-client docs are in `docs/install/`.
- **Rationale:** Users must be able to find and install companions without guessing. Per-client docs are necessary because config schema and file paths differ.
- **Consequence:** When a companion's schema or config structure changes, `docs/install/` is updated to maintain compatibility.

## Current Kit Justification Against the Bar

### azure-mcp (2.0.1)

- **Stable upstream:** YES. Microsoft-published semver release with release notes.
- **Signed releases:** YES. Published via npm with npm provenance. Official Microsoft package.
- **Narrow scope:** YES. Authoritative for Azure REST APIs, ARG, Advisor, Monitor, RBAC, Policy, AKS, AppService.
- **Complementary to azure-mcp:** N/A (azure-mcp is not a companion; it is the source of truth).
- **Maintenance signal:** YES. Microsoft maintains. Last release 2026-Q1.
- **Read-only by design:** YES. All tools are read-only query endpoints. No write capability.
- **Documented install:** YES. All four client guides in `docs/install/`.

### microsoft-learn (hosted)

- **Stable upstream:** YES. Hosted endpoint at learn.microsoft.com/api/mcp. Always available.
- **Signed releases:** N/A (hosted endpoint; Microsoft infrastructure).
- **Narrow scope:** YES. Documentation lookup only.
- **Complementary to azure-mcp:** YES. Docs, not APIs. No overlap.
- **Maintenance signal:** YES. Microsoft maintains.
- **Read-only by design:** YES. Search/lookup only. No mutation.
- **Documented install:** YES. All client guides.

### github (latest, Docker)

- **Stable upstream:** YES. Docker image tags are stable; continuous updates to `latest`.
- **Signed releases:** YES. Docker image signed via Docker Content Trust (DCT). GitHub official registry.
- **Narrow scope:** YES. GitHub API only: repos, issues, PRs, actions. No Azure APIs or general compute.
- **Complementary to azure-mcp:** YES. GitHub APIs are orthogonal to Azure resource management.
- **Maintenance signal:** YES. GitHub maintains. Actively updated.
- **Read-only by design:** YES. GitHub MCP server exposes read-only queries. Requires GitHub PAT for auth (secret required outside of this kit).
- **Documented install:** YES. All client guides cover Docker setup and PAT configuration.

### mermaid (0.4.1)

- **Stable upstream:** YES. npm semver release. Package: `mcp-mermaid` at hustcc/mcp-mermaid.
- **Signed releases:** YES. npm provenance on @hustcc org.
- **Narrow scope:** YES. Diagram rendering from Mermaid syntax. No compute, no cloud APIs.
- **Complementary to azure-mcp:** YES. Diagrams are orthogonal to Azure resource queries.
- **Maintenance signal:** YES. Last release 2026-Q1. Community-maintained. Stable mermaid spec.
- **Read-only by design:** YES. Rendering only. No mutations.
- **Documented install:** YES. All client guides.

### drawio (2.0.4)

- **Stable upstream:** YES. npm semver release. Package: `drawio-mcp-server` at lgazo/drawio-mcp-server.
- **Signed releases:** YES. npm provenance.
- **Narrow scope:** YES. Draw.io diagram creation. No compute, no cloud APIs.
- **Complementary to azure-mcp:** YES. Diagrams are orthogonal to Azure resource queries.
- **Maintenance signal:** YES. Last release 2026-Q1. Community-maintained.
- **Read-only by design:** YES. Creation and export only. No mutations to external systems.
- **Documented install:** YES. All client guides.

### kubernetes (0.0.53)

- **Stable upstream:** YES. npm semver release. kubernetes-mcp-server package.
- **Signed releases:** YES. npm provenance.
- **Narrow scope:** YES. kubectl-based cluster inspection. Read pod and node state from live cluster.
- **Complementary to azure-mcp:** YES. k8s tools are orthogonal to Azure resource management. Compatible with AKS clusters.
- **Maintenance signal:** YES. Last release 2026-Q1.
- **Read-only by design:** YES. Inspection only (get pods, nodes, config). No kubectl apply, no cluster mutations.
- **Documented install:** YES. All client guides cover kubeconfig setup.

### terraform (v0.5.1)

- **Stable upstream:** YES. HashiCorp semver release. Official terraform-mcp-server.
- **Signed releases:** YES. HashiCorp releases are signed. Docker images via Docker Content Trust.
- **Narrow scope:** YES. Terraform registry lookup, plan, validate. No compute.
- **Complementary to azure-mcp:** YES. IaC tooling is orthogonal to Azure resource APIs. Terraform can manage Azure resources, but this MCP server only exposes read-only operations (plan, validate).
- **Maintenance signal:** YES. HashiCorp (ALLOWED-VENDOR). Actively maintained.
- **Read-only by design:** YES. Plan and validate only. No `terraform apply`. Read-only configuration enforced.
- **Documented install:** YES. All client guides cover Docker setup.

## Companion Triage Process

### Adding a New Companion

When a candidate companion is proposed:

1. **Open issue** in this repository with label `companion-candidate`. Describe the companion, upstream URL, version.
2. **Burke (or designate) performs criterion check.** Post findings in a comment. Example:
   - "mcp-candidate-foo checks 6/7 criteria. Criterion 5 (maintenance signal) is unclear; last release is 2 years old. Recommend deferring until next update or reaching out to maintainer."
3. **PR to add companion** to `.copilot/mcp-config.json` (with version pin) and add row to `docs/install/compatibility-matrix.md`.
4. **PR cites criterion findings** in its body. Example: "Closes #N. Adds mcp-foo per criterion check (PR comment #123). Companion meets all 7 criteria."
5. **Sentinel or security reviewer** checks supply chain: signatures, provenance, and read-only configuration.
6. **Merge** once criteria and security are cleared.

### Removing a Companion

When a companion no longer meets the bar:

1. **Open issue** with label `companion-removal`. Document which criterion was broken. Example: "github-mcp last release was 18 months ago (criterion 5: maintenance signal). Recommend sunset."
2. **PR removes companion** from `.copilot/mcp-config.json` and adds deprecation note to compatibility matrix. Example: "Sunset github-mcp (0.0.x-final) due to maintenance gap. Archive link in matrix for reference."
3. **Merge** with note.

### Maintenance Cadence

- **Quarterly:** Burke reviews matrix. If any companion is approaching 6-month threshold, flag for update or removal decision.
- **Upon upstream break:** If upstream publishes a breaking change (schema, security incident), compatibility matrix is updated immediately with workaround or deprecation note.

## Examples of Rejected Candidates

### drawio-mcp (Proposed, Deferred)

**Candidate:** drawio-mcp (unrelated to lgazo/drawio-mcp-server; different upstream)

**Criteria Check:**
- Criterion 1 (stable upstream): FAIL. Upstream is inactive. Last release 2024-Q3; no tagged releases since. README uses "latest" as version guidance.
- Criterion 5 (maintenance signal): FAIL. Dormant for 18+ months.

**Decision:** REJECT. Recommend revisiting if upstream resumes maintenance or switching to lgazo/drawio-mcp-server (which is active).

### filesystem-mcp (Proposed, Rejected)

**Candidate:** filesystem-mcp (hypothetical generic file system access server)

**Criteria Check:**
- Criterion 3 (narrow scope): FAIL. Scope is too broad: file reading, writing, permissions management, recursion. Overlaps with shell tools, script execution, and general I/O.
- Criterion 4 (complementary to azure-mcp): FAIL. No Azure-specific value. Generic compute tool.

**Decision:** REJECT. Scope is too general. If architect needs file I/O, use shell-mcp or built-in tools.

### azure-servicebus-mcp (Proposed, Rejected)

**Candidate:** azure-servicebus-mcp (hypothetical Azure Service Bus–specific MCP server)

**Criteria Check:**
- Criterion 4 (complementary to azure-mcp): FAIL. Azure Service Bus operations are already available through `azure-mcp`. Adding a second Azure service MCP duplicates tool surface and creates version skew.

**Decision:** REJECT. azure-mcp is the authoritative source for Azure services. Use azure-mcp's tools instead. If azure-mcp is missing Service Bus endpoints, open an issue against microsoft/mcp (repo for azure-mcp) instead.

### azure-pricing-mcp (Proposed, Routed to Native — Issue #39)

**Candidate:** azure-pricing-mcp (hypothetical MCP companion to expose Azure Retail Prices API)

**Context:** Architects need current Azure pricing for cost estimates and SKU selection during infrastructure design. Azure Retail Prices API is public, no-auth, OData-filterable, returns clean JSON. No standalone pricing MCP exists.

**Criteria Check:**
- Criterion 1 (stable upstream): FAIL. No upstream exists. Pricing logic would be custom-built MCP boilerplate wrapping the public API.
- Criterion 2 (signed releases): FAIL. No package to sign. If we built it, it would need to be published and signed before inclusion.
- Criterion 5 (maintenance signal): FAIL. No upstream to monitor for maintenance or deprecation.
- Criterion 6 (read-only by design): PASS. API is read-only. No mutation capability.

**Decision:** REJECT as companion. ROUTE TO NATIVE instead. Rationale: The bar correctly identifies that building a standalone MCP wrapper for a direct API call adds bloat with no upstream-maintenance benefit. Native integration in the server yields zero cold-start tax, zero auth-surface expansion, and seamless composition with planned scorecard and quota planner. Pricing logic belongs in this server, not as a delegated companion. See issue #39 (Forge, wave 4).

## Consequences

### Enables

1. **Clear admission bar.** Future companions are evaluated consistently against documented criteria. No ad-hoc decisions.
2. **Reproducible installs.** Version pinning + documented install paths mean users get the same kit across machines and time.
3. **Supply chain visibility.** Signed releases and maintenance signals reduce security and abandonment risk.
4. **Scoped kit.** Companion selection prevents feature bloat and keeps the kit focused on Azure architecture workflows.

### Costs

1. **Maintenance burden.** Burke must triage companion candidates and monitor upstream for maintenance signals. Quarterly reviews are required.
2. **Slower onboarding for new companions.** Candidates must pass all 7 criteria before inclusion. This may slow adoption of useful new tools.
3. **Version pinning discipline.** When upstream breaks the bar, companions must be removed or pinned-back. This can break user workflows if they rely on a removed companion.

### Mitigation

1. **Triage process is lightweight.** Criterion check is a checklist. Can be done in 15 minutes per candidate.
2. **Deprecation warnings in compatibility matrix.** When a companion is sunset, the matrix notes why and suggests alternatives.
3. **User opt-out mechanism.** Users can disable any companion by setting `"disabled": true` in their config. Removed companions can remain as disabled examples in mcp-config.json for users who want to re-enable them.

## Alternatives Considered

### Option 1: No Bar (Trust Users to Curate)

**Rationale:** Users know their own needs. Let them add companions freely without our vetting.

**Rejection:** Defeats the purpose of shipping a curated kit. Leads to bloat, supply chain surprises, and user confusion.

### Option 2: Strict Hardcoded Allowlist (Code Enforcement)

**Rationale:** Encode the bar into a CI check. Only commits that update a hardcoded list of allowed companions are merged.

**Rejection:** Too rigid. Requires repo updates for every new companion, even if it's clearly good (e.g., a new Microsoft-published server). Adds friction.

### Option 3: Minimal Bar (Only Criterion 1: Stable Upstream)

**Rationale:** Fewer criteria = faster onboarding. Criterion 1 (stable versions) is the most critical.

**Rejection:** Ignores supply chain security (criterion 2), scope drift (criterion 3), and security (criterion 6). We end up shipping unsigned or mutating companions by accident.

**Decision:** Use the 7-criterion bar (Option 4 in the implicit evaluation).

## References

1. **AGENTS.md, Project Conventions:**  
   [AGENTS.md](../../AGENTS.md) - "Companion servers are not bundled. Never proxy or wrap azure-mcp."

2. **.copilot/mcp-config.json:**  
   Current curated configuration file with all pinned companions and their rationale.

3. **docs/install/compatibility-matrix.md:**  
   Companion version rationale, testing roadmap, and per-client setup instructions.

4. **PR #23: mcp-config Audit (v0):**  
   First Wave 2 audit of companions. All current companions passed vetting.

5. **MCP Specification, Server Definition:**  
   [modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification) - MCP protocol, server roles, and transport.

6. **npm Provenance:**  
   [docs.npmjs.com/generating-provenance-statements](https://docs.npmjs.com/generating-provenance-statements) - Package signature mechanism for npm.

7. **Docker Content Trust (DCT):**  
   [docs.docker.com/engine/security/trust](https://docs.docker.com/engine/security/trust) - Image signing and verification.

8. **Project Constraints (ADR-001):**  
   [0001-runtime-choice.md](0001-runtime-choice.md) - Read-only requirement, DefaultAzureCredential, no wrapping of azure-mcp.

## Burke Review and Approval

**Verdict:** APPROVE

**Rationale:** ADR-004 codifies companion selection criteria that are pragmatic, testable, and aligned with project constraints (read-only, no wrapping, supply chain security). The 7 criteria have clear entry/exit conditions and are applied consistently to all current companions. Rejection examples are specific and honest about why candidates do not fit. Triage process is lightweight and does not block new companions unnecessarily. Consequences section acknowledges maintenance burden and proposes mitigations (quarterly reviews, deprecation warnings, user opt-out).

---

## Addendum: Companion Bar Refinement (2026-05-13, Sentinel Review Pending)

This ADR is complete and ready for merge. Sentinel (security engineer) will review the threat model implications in parallel and reference ADR-004 when finalizing `docs/security/threat-model.md`. No changes to this ADR are anticipated pending Sentinel's review.
