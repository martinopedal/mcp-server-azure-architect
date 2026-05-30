# mcp-server-azure-architect

> **Not an official Microsoft product.** This is a personal community tool that **complements** the official Microsoft [`azure-mcp`](https://github.com/microsoft/azure-mcp) server, it does not replace it.

MCP server and Copilot CLI skills bundle for Azure architects. Native tools fill the architect-shaped gap above `azure-mcp`. A curated `mcp-config.json` ships alongside so an architect's "kit" (Microsoft Learn, mermaid, drawio, kubernetes, terraform companions) is one install.

## Why this exists

`azure-mcp` already exposes Azure Resource Graph, Quota, Advisor, Monitor, Policy, RBAC, AKS, App Service, and more as MCP tools. Use it directly for those.

What architects still need that `azure-mcp` does **not** ship:

- **Named ALZ checklist queries** (by checklist ID), not raw KQL.
- **ALZ readiness scorecard** that composes many queries into one ranked, scored answer.
- **Architect skills** that orchestrate the kit: a `design-review` skill that pulls current state via `azure-mcp`, gaps via this server, and renders a diagram via `mermaid-mcp`.

This server is **not a router or aggregator**. MCP clients already aggregate. We ship the missing tools and a curated companion config.

## What's in scope

- A small MCP server exposing seven native tools: `health_check`, `alz_query_by_id`, `alz_query_list`, `pricing_lookup_sku`, `pricing_compare_skus`, `pricing_estimate_workload`, and `alz_scorecard`.
- Copilot CLI skills: `design-review`, `alz-gap-check`, `ingress-migration-plan`, `policy-as-code-suggest`.
- A curated `mcp-config.json` for Copilot CLI, Claude Desktop, Cursor, and VS Code Copilot.
- Read-only by default, end to end.

The architect-specific Copilot CLI skill bundle is planned post-v0.2 work. The current release delivers the MCP server and companion client configuration, while the skill bundle remains tracked as future scope.

## What's out of scope

- Wrapping or proxying `azure-mcp`. Anything `azure-mcp` already exposes (raw KQL/ARG, quota, advisor, monitor, policy, RBAC, AKS, App Service) is **explicitly out**.
- Mutation tools (create/update/delete on Azure). Read-only stays read-only.
- Hosted multi-tenant deployment. Local-first.

## Companion servers (recommended, not bundled)

| Server | Why an architect wants it |
|--------|---------------------------|
| `azure-mcp` (Microsoft) | ARG, Advisor, Monitor, Policy, RBAC, AKS, AppService, ... |
| `microsoft-learn-mcp` | Grounded MS docs lookup |
| `github` MCP | Repo, issue, PR access for IaC reviews |
| `mermaid-mcp` | Render architecture diagrams inline |
| `drawio-mcp` | Visio-replacement diagrams, exportable |
| `kubernetes-mcp` | Live cluster inspection during design reviews |
| `terraform-mcp` (HashiCorp) | Plan, validate, registry lookup |

The default `mcp-config.json` shipped with this repo wires these up. Edit before use.

## Status

Pre-alpha. Backlog tracked as GitHub issues. See the [v0.2 roadmap](docs/planning/v0.2.md) for upcoming work. Runtime ratified per ADR-001 (Python + FastMCP).

## Stack

Python 3.11+ with FastMCP, per [ADR-001](docs/adr/0001-runtime-choice.md). Build via Hatchling, lint with ruff, types with mypy, tests with pytest. Distribution via `uvx mcp-server-azure-architect`.

Constraints:

- Local-first, single binary or single-process startup. Cold-start performance baseline (measured 8.5-9.0s) and rationale documented in [docs/perf/coldstart-investigation.md](docs/perf/coldstart-investigation.md).
- Read-only Azure SDK calls only. DefaultAzureCredential exclusively.
- Zero credentials at rest. Token-scrub on any logging.
- ALZ checklist queries source from the public `martinopedal/alz-checklist-queries` and `martinopedal/alz-graph-queries` repos (vendored snapshot, pinned by upstream commit SHA).

## Quickstart

### One-command install (recommended)

Clone the repo and run the kit installer:

```bash
git clone https://github.com/martinopedal/mcp-server-azure-architect.git
cd mcp-server-azure-architect
pip install -e .
python scripts/install_kit.py
```

The installer will:
- Check prerequisites (Python 3.11+, Node.js, Docker, GitHub CLI)
- Detect your MCP clients (Copilot CLI, Claude Desktop, Cursor, VS Code Copilot)
- Merge the curated companion kit into each client's config
- Verify Azure and GitHub authentication

See [docs/install/installer.md](docs/install/installer.md) for details.

### Manual install

For end users (once published to PyPI):

```bash
uvx mcp-server-azure-architect
```

For development (editable install):

```bash
# Install uv if not already available
pip install uv

# Install package with dev dependencies
uv pip install -e ".[dev]"
```

Then configure your MCP client manually (see [docs/install/](docs/install/) for per-client guides).

### Run

Run the server via stdio transport:

```bash
mcp-server-azure-architect
```

Test with MCP Inspector:

```bash
npx @modelcontextprotocol/inspector mcp-server-azure-architect
```

### Authentication

The server uses Azure `DefaultAzureCredential` for authentication, which supports multiple credential sources in this order:

1. Environment variables (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`)
2. Managed Identity (when running on Azure compute)
3. Azure CLI (`az login`)

All tools are read-only by design. No Azure write operations are exposed.

For more details on the runtime choice, see [docs/adr/0001-runtime-choice.md](docs/adr/0001-runtime-choice.md).

## Third-party content

Vendored content licenses are reproduced in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## License

MIT.

<!-- mcp-name: io.github.martinopedal/mcp-server-azure-architect -->
