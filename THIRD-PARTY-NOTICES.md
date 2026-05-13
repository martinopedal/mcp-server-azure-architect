# Third-Party Notices

This project includes vendored content from third-party sources, and recommends (but does not bundle) companion MCP servers via `mcp-config.json`. Each source retains its own license. Notices for vendored content are reproduced verbatim as required by their licenses. Companion server attributions are summarized; their full licenses live with their upstream projects.

---

## Vendored content (bundled in the wheel)

### ALZ Checklist Queries (`data/alz-queries/checklist/`)

- **Source:** https://github.com/martinopedal/alz-checklist-queries
- **License:** MIT
- **Pinned commit:** `e7641beeda0126cc78825f8b77764c379552f3e1`
- **Vendored:** `2026-04-22T12:35:39Z`

```
MIT License

Copyright (c) 2026 martinopedal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

### ALZ Graph Queries (`data/alz-queries/graph/`)

- **Source:** https://github.com/martinopedal/alz-graph-queries
- **License:** MIT
- **Pinned commit:** `448998d01000e7f863d3c1f8876787fd2234a77b`
- **Vendored:** `2026-05-12T21:52:10Z`

```
MIT License

Copyright (c) 2026 martinopedal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Companion MCP servers (recommended via `mcp-config.json`, not bundled)

### Model Context Protocol

- **Specification:** https://modelcontextprotocol.io/
- **Source:** https://github.com/modelcontextprotocol
- **Copyright:** Copyright (c) Anthropic, PBC and contributors
- **License:** MIT License
- **Usage:** This server implements the MCP server interface.

---

### Azure MCP (Microsoft)

- **Source:** https://github.com/microsoft/azure-mcp
- **Copyright:** Copyright (c) Microsoft Corporation
- **License:** MIT License
- **Usage:** Recommended companion server in `.copilot/mcp-config.json`. Source of truth for raw Azure Resource Graph, Quota, Advisor, Monitor, Policy, RBAC, AKS, and App Service tools. This server complements `azure-mcp`, it does not wrap or replace it.

---

### Microsoft Learn MCP

- **Source:** https://learn.microsoft.com/api/mcp
- **Copyright:** Copyright (c) Microsoft Corporation
- **Usage:** Recommended companion server. Grounded Microsoft Learn doc lookup.

---

### GitHub MCP Server

- **Source:** https://github.com/github/github-mcp-server
- **Copyright:** Copyright (c) GitHub, Inc.
- **License:** MIT License
- **Usage:** Recommended companion server. Repo, issue, PR access for IaC reviews.

---

### Mermaid MCP

- **Source:** https://github.com/mermaid-js/mermaid-mcp
- **Copyright:** Copyright (c) Mermaid contributors
- **License:** MIT License
- **Usage:** Recommended companion server. Renders architecture diagrams inline during design reviews.

---

### drawio-mcp-server

- **Source:** https://github.com/drawio-mcp/drawio-mcp-server (verify exact upstream before pin)
- **License:** MIT License (typical for the ecosystem; verify per release)
- **Usage:** Recommended companion server. Visio-replacement diagrams, exportable.

---

### kubernetes-mcp-server

- **Source:** https://github.com/manusa/kubernetes-mcp-server (verify exact upstream before pin)
- **License:** Apache License 2.0 (typical; verify per release)
- **Usage:** Recommended companion server. Live cluster inspection during AKS design reviews.

---

### Terraform MCP (HashiCorp)

- **Source:** https://github.com/hashicorp/terraform-mcp-server
- **Copyright:** Copyright (c) HashiCorp, Inc.
- **License:** MPL-2.0
- **Usage:** Recommended companion server. Terraform registry lookup, plan, validate.

---

### Azure Review Checklists (Microsoft, upstream)

- **Source:** https://github.com/Azure/review-checklists
- **Copyright:** Copyright (c) Microsoft Corporation
- **License:** MIT License
- **Usage:** Original upstream source of the ALZ checklist items referenced by the ID-based queries this server exposes.

---

### Azure SDK clients

- **Source:** https://github.com/Azure (per-runtime SDK)
- **Copyright:** Copyright (c) Microsoft Corporation
- **License:** MIT License
- **Usage:** Used to issue read-only ARG queries via `DefaultAzureCredential`. Specific SDK packages are pinned once the runtime ADR lands.

---

### Squad

- **Source:** https://github.com/bradygaster/squad
- **Copyright:** Copyright (c) Brady Gaster
- **License:** MIT License
- **Usage:** Provides the agentic team orchestration scaffolding under `.squad/`.

---

### gitleaks

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

