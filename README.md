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

- A small MCP server exposing two native tool families: `alz_query_by_id` (catalog lookup) and `alz_scorecard` (composition + scoring).
- Copilot CLI skills: `design-review`, `alz-gap-check`, `ingress-migration-plan`, `policy-as-code-suggest`.
- A curated `mcp-config.json` for Copilot CLI, Claude Desktop, Cursor, and VS Code Copilot.
- Read-only by default, end to end.

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

Pre-alpha. Backlog tracked as GitHub issues with the `squad` label. Runtime decision (Python vs TypeScript vs .NET) is itself an issue.

## Stack

To be decided as part of issue triage. Constraints:

- Local-first, single binary or single-process startup.
- Read-only Azure SDK calls only.
- Zero credentials at rest. Token-scrub on any logging.
- ALZ checklist queries source from the public `martinopedal/alz-checklist-queries` and `martinopedal/alz-graph-queries` repos.

## Squad

Multi-agent dev via [Squad by Brady Gaster](https://github.com/bradygaster/squad). Team in `.squad/team.md`. Routing in `.squad/routing.md`. Open `squad`-labeled issues are the live backlog.

## Quickstart

### Install

For end users:

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

## License

MIT.
