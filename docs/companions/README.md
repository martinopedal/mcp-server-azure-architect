# Companion MCP Servers

This directory contains supply chain audit notes for all recommended companion MCP servers shipped in `.copilot/mcp-config.json`.

Each companion is evaluated against the criteria defined in `docs/adr/0004-companion-server-bar.md`: stable upstream, signed releases, narrow scope, complementary to `azure-mcp`, maintenance signal, read-only posture, and documented install paths.

## Index

| Companion | Purpose | Version | Maintainer |
|-----------|---------|---------|-----------|
| [azure-mcp](azure-mcp.md) | Official Azure REST APIs, ARG, Advisor, Monitor, Policy, RBAC, AKS, AppService | 2.0.1 | Microsoft |
| [drawio](drawio.md) | Draw.io diagram creation and export for architecture designs | 2.0.4 | lgazo |
| [github](github.md) | GitHub API access: repos, issues, PRs, actions for IaC review | latest | GitHub |
| [kubernetes](kubernetes.md) | kubectl-based cluster inspection for AKS design and migration review | 0.0.53 | community |
| [mermaid](mermaid.md) | Mermaid diagram rendering for inline architecture visualization | 0.4.1 | hustcc |
| [microsoft-learn](microsoft-learn.md) | Microsoft Learn documentation lookup for grounded architect guidance | hosted | Microsoft |
| [terraform](terraform.md) | Terraform registry lookup, plan, validate for IaC design | v0.5.1 | HashiCorp |

## Audit Process

Each entry documents:

1. **Purpose.** Architecture workflow served.
2. **Source.** Maintainer and repository.
3. **Distribution.** Installation method (npm, docker, uvx, etc.).
4. **Auth model.** Credentials required at runtime.
5. **Network egress.** External endpoints accessed.
6. **Read-only posture.** Mutation capabilities and constraints.
7. **Supply chain notes.** Versioning, provenance, CVE status.
8. **ADR-004 fit.** Which criteria are satisfied.
9. **Removal cost.** Architect capabilities lost if uninstalled.

## Adding a Companion

Follow the triage process in `docs/adr/0004-companion-server-bar.md`, section "Companion Triage Process". New companions must:

1. Pass all 7 criteria (stable upstream, signed releases, narrow scope, complementary, maintenance signal, read-only, documented install).
2. Be vetted by Sentinel (security review).
3. Include a version pin in `.copilot/mcp-config.json`.
4. Include an audit note in this directory.

## Quarterly Maintenance

Burke reviews the companion kit quarterly to ensure:

- All companions are still actively maintained (last release within 6 months).
- No new CVEs are unaddressed.
- Each companion's documentation in `docs/install/` remains current.
