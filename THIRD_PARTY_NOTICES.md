# Third-Party Notices

This repository invokes, references, or depends on the following open-source projects. Companion MCP servers listed in `.copilot/mcp-config.json` are **recommended, not bundled**. Each must be installed separately and is governed by its own license.

---

## Model Context Protocol

- **Specification:** https://modelcontextprotocol.io/
- **Source:** https://github.com/modelcontextprotocol
- **Copyright:** Copyright (c) Anthropic, PBC and contributors
- **License:** MIT License
- **Usage:** This server implements the MCP server interface.

---

## Azure MCP (Microsoft)

- **Source:** https://github.com/microsoft/azure-mcp
- **Copyright:** Copyright (c) Microsoft Corporation
- **License:** MIT License
- **Usage:** Recommended companion server in `.copilot/mcp-config.json`. Source of truth for raw Azure Resource Graph, Quota, Advisor, Monitor, Policy, RBAC, AKS, and App Service tools. This server complements `azure-mcp`, it does not wrap or replace it.

---

## Microsoft Learn MCP

- **Source:** https://learn.microsoft.com/api/mcp
- **Copyright:** Copyright (c) Microsoft Corporation
- **Usage:** Recommended companion server. Grounded Microsoft Learn doc lookup.

---

## GitHub MCP Server

- **Source:** https://github.com/github/github-mcp-server
- **Copyright:** Copyright (c) GitHub, Inc.
- **License:** MIT License
- **Usage:** Recommended companion server. Repo, issue, PR access for IaC reviews.

---

## Mermaid MCP

- **Source:** https://github.com/mermaid-js/mermaid-mcp
- **Copyright:** Copyright (c) Mermaid contributors
- **License:** MIT License
- **Usage:** Recommended companion server. Renders architecture diagrams inline during design reviews.

---

## drawio-mcp-server

- **Source:** https://github.com/drawio-mcp/drawio-mcp-server (verify exact upstream before pin)
- **License:** MIT License (typical for the ecosystem; verify per release)
- **Usage:** Recommended companion server. Visio-replacement diagrams, exportable.

---

## kubernetes-mcp-server

- **Source:** https://github.com/manusa/kubernetes-mcp-server (verify exact upstream before pin)
- **License:** Apache License 2.0 (typical; verify per release)
- **Usage:** Recommended companion server. Live cluster inspection during AKS design reviews.

---

## Terraform MCP (HashiCorp)

- **Source:** https://github.com/hashicorp/terraform-mcp-server
- **Copyright:** Copyright (c) HashiCorp, Inc.
- **License:** MPL-2.0
- **Usage:** Recommended companion server. Terraform registry lookup, plan, validate.

---

## ALZ Checklist Queries (martinopedal)

- **Source:** https://github.com/martinopedal/alz-checklist-queries (and/or `alz-graph-queries`)
- **Copyright:** Copyright (c) Microsoft Corporation (original ALZ checklist data, derived), Copyright (c) 2026 martinopedal (KQL adaptations)
- **License:** MIT License
- **Usage:** Vendored snapshot under `data/alz-queries/`. Pinned by commit SHA in `data/alz-queries/MANIFEST.md`. Refreshed quarterly.

---

## Azure Review Checklists (Microsoft, upstream)

- **Source:** https://github.com/Azure/review-checklists
- **Copyright:** Copyright (c) Microsoft Corporation
- **License:** MIT License
- **Usage:** Original upstream source of the ALZ checklist items referenced by the ID-based queries this server exposes.

---

## Azure SDK clients

- **Source:** https://github.com/Azure (per-runtime SDK)
- **Copyright:** Copyright (c) Microsoft Corporation
- **License:** MIT License
- **Usage:** Used to issue read-only ARG queries via `DefaultAzureCredential`. Specific SDK packages are pinned once the runtime ADR lands.

---

## Squad

- **Source:** https://github.com/bradygaster/squad
- **Copyright:** Copyright (c) Brady Gaster
- **License:** MIT License
- **Usage:** Provides the agentic team orchestration scaffolding under `.squad/`.

---

## gitleaks

- **Source:** https://github.com/gitleaks/gitleaks
- **Copyright:** Copyright (c) Zachary Rice and gitleaks contributors
- **License:** MIT License
- **Usage:** Invoked in CI to scan for committed secrets.

---

# First-Party Components (mcp-server-azure-architect)

The following components are developed as part of this repository and licensed under the MIT License in [LICENSE](LICENSE).

## Native MCP tools (first-party)

- **Source:** `src/server/tools/` (planned)
- **Tools:** `alz_query_by_id`, `alz_scorecard`
- **Copyright:** Copyright (c) 2026 martinopedal
- **License:** MIT License (see [LICENSE](LICENSE))

## Copilot CLI skills (first-party)

- **Source:** `.copilot/skills/`
- **Skills:** `design-review`, `alz-gap-check`, `ingress-migration-plan`, `policy-as-code-suggest`
- **Copyright:** Copyright (c) 2026 martinopedal
- **License:** MIT License (see [LICENSE](LICENSE))

## Curated MCP client config (first-party)

- **Source:** `.copilot/mcp-config.json`
- **Copyright:** Copyright (c) 2026 martinopedal
- **License:** MIT License (see [LICENSE](LICENSE))
- **Note:** The configuration file itself is first-party. The MCP servers it references are third-party and listed above. Each retains its own license.

## Kit installer (first-party)

- **Source:** `scripts/install.ps1`, `scripts/install.sh` (planned)
- **Copyright:** Copyright (c) 2026 martinopedal
- **License:** MIT License (see [LICENSE](LICENSE))

Copyright (c) 2026 martinopedal. See [LICENSE](LICENSE) for the full text.
