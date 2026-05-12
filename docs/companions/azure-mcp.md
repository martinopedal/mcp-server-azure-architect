# azure-mcp: Official Azure REST APIs

## Purpose

Exposes official Microsoft Azure REST APIs via the Model Context Protocol. Covers Azure Resource Graph (ARG), Advisor recommendations, Monitor insights, Policy compliance, RBAC role assignments, AKS cluster management, and App Service configuration. This is the source of truth for all Azure resource queries in the kit. Architects use it to audit infrastructure state, detect compliance gaps, and inform design decisions.

## Source

Repository: [microsoft/mcp](https://github.com/microsoft/mcp/tree/main/servers/Azure.Mcp.Server) (moved from Azure/azure-mcp on 2026-02-06, now archived)  
Maintainer: Microsoft (official product)

## Distribution

Installed via npm:

```
npm install @azure/mcp@2.0.1
```

Or installed on demand via npx in `.copilot/mcp-config.json`:

```
"command": "npx",
"args": ["-y", "@azure/mcp@2.0.1", "server", "start", "--read-only"]
```

## Recommended Client Flags

The Azure MCP Server supports several configuration flags that control tool surface and read-only posture:

- `--read-only`: Enables read-only mode. All tools that could potentially mutate Azure resources are disabled. **Recommended for all architect workflows.** This flag is included in the curated `.copilot/mcp-config.json`.
- `--mode namespace`: Returns only top-level namespace tools (e.g., `azure_arg`, `azure_advisor`) instead of all 40+ granular service tools. Reduces context cost in MCP clients with limited context windows. Use when you need compact tool lists.
- `--namespace <name>`: Whitelist specific namespaces to load (e.g., `--namespace arg --namespace advisor`). Combine with `--mode namespace` for fine-grained control. Use when you know which Azure services you need and want to minimize noise.

Example config with namespace filtering:

```
"command": "npx",
"args": ["-y", "@azure/mcp@2.0.1", "server", "start", "--read-only", "--mode", "namespace", "--namespace", "arg", "--namespace", "advisor"]
```

For full flag documentation, see [Azure MCP Server README](https://github.com/microsoft/mcp/blob/main/servers/Azure.Mcp.Server/README.md).

## Auth Model

Requires Azure credentials at runtime. Supports:

- Azure CLI authentication (az login)
- Environment variables (AZURE_SUBSCRIPTION_ID, AZURE_TENANT_ID, etc.)
- Managed identity (when running in Azure compute)
- DefaultAzureCredential chain

No hardcoded secrets in code or config.

## Network Egress

Connects to:

- `https://management.azure.com` (Azure Resource Manager)
- `https://login.microsoftonline.com` (Microsoft Entra ID for token refresh)
- Regional Azure endpoints as directed by ARM (e.g., `https://graph.windows.net`)

Requires internet access to Azure public cloud.

## Read-Only Posture

**Fully read-only.** All tools are query endpoints. No mutation tools exposed.

Examples of read-only tools:
- `arg_query` (ARG KQL queries)
- `list_advisor_recommendations`
- `get_resource_quota`
- `list_role_assignments`

No tools for creating, updating, or deleting Azure resources.

## Supply Chain Notes

**Version pinned:** 2.0.1 (semver release)

**Provenance:** Published to npm by @azure org with npm provenance signatures. Official Microsoft package. Verified in npm registry at [npmjs.com/@azure/mcp](https://www.npmjs.com/package/@azure/mcp).

**CVE status:** Reviewed by Sentinel per ADR-003. No known CVEs as of 2026-05-12. Depends on Azure SDK (nodejs) which is actively maintained by Microsoft.

**Release cadence:** Microsoft publishes semver releases quarterly. Last release 2026-Q1.

## ADR-004 Fit

- ✅ **Criterion 1 (Stable Upstream):** YES. Semver releases with release notes.
- ✅ **Criterion 2 (Signed Releases):** YES. npm provenance, official Microsoft registry.
- ✅ **Criterion 3 (Narrow Scope):** YES. Azure REST APIs only.
- ✅ **Criterion 4 (Complementary to azure-mcp):** N/A (azure-mcp itself is the source of truth).
- ✅ **Criterion 5 (Maintenance Signal):** YES. Microsoft maintains; last release 2026-Q1.
- ✅ **Criterion 6 (Read-Only):** YES. All tools are read-only queries.
- ✅ **Criterion 7 (Documented Install):** YES. Per-client guides in `docs/install/`.

## Removal Cost

If azure-mcp is uninstalled:

- All ARG queries are unavailable (no workaround; azure-mcp is authoritative).
- Advisor insights, quota planning, and policy compliance checks all fail.
- Architect loses visibility into Azure resource state during design reviews.
- Copilot skills (`alz-gap-check`, `design-review`) become non-functional.

**Risk:** High. Core to the kit.

## References

- [microsoft/mcp Azure MCP Server](https://github.com/microsoft/mcp/tree/main/servers/Azure.Mcp.Server)
- [Azure MCP Server README](https://github.com/microsoft/mcp/blob/main/servers/Azure.Mcp.Server/README.md)
- [npm registry @azure/mcp](https://www.npmjs.com/package/@azure/mcp)
- [Azure/azure-mcp (archived 2026-02-06)](https://github.com/Azure/azure-mcp)
- `.copilot/mcp-config.json` (pinned version with --read-only)
- `docs/install/` (per-client setup)
