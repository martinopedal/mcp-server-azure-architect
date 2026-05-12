# azure-mcp: Official Azure REST APIs

## Purpose

Exposes official Microsoft Azure REST APIs via the Model Context Protocol. Covers Azure Resource Graph (ARG), Advisor recommendations, Monitor insights, Policy compliance, RBAC role assignments, AKS cluster management, and App Service configuration. This is the source of truth for all Azure resource queries in the kit. Architects use it to audit infrastructure state, detect compliance gaps, and inform design decisions.

## Source

Repository: [microsoft/mcp](https://github.com/microsoft/azure-mcp)  
Maintainer: Microsoft (official product)

## Distribution

Installed via npm:

```
npm install @azure/mcp@2.0.1
```

Or installed on demand via npx in `.copilot/mcp-config.json`:

```
"command": "npx",
"args": ["-y", "@azure/mcp@2.0.1"]
```

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

- ✓ **Criterion 1 (Stable Upstream):** YES. Semver releases with release notes.
- ✓ **Criterion 2 (Signed Releases):** YES. npm provenance, official Microsoft registry.
- ✓ **Criterion 3 (Narrow Scope):** YES. Azure REST APIs only.
- ✓ **Criterion 4 (Complementary to azure-mcp):** N/A (azure-mcp itself is the source of truth).
- ✓ **Criterion 5 (Maintenance Signal):** YES. Microsoft maintains; last release 2026-Q1.
- ✓ **Criterion 6 (Read-Only):** YES. All tools are read-only queries.
- ✓ **Criterion 7 (Documented Install):** YES. Per-client guides in `docs/install/`.

## Removal Cost

If azure-mcp is uninstalled:

- All ARG queries are unavailable (no workaround; azure-mcp is authoritative).
- Advisor insights, quota planning, and policy compliance checks all fail.
- Architect loses visibility into Azure resource state during design reviews.
- Copilot skills (`alz-gap-check`, `design-review`) become non-functional.

**Risk:** High. Core to the kit.

## References

- [microsoft/azure-mcp](https://github.com/microsoft/azure-mcp)
- [npm registry @azure/mcp](https://www.npmjs.com/package/@azure/mcp)
- `.copilot/mcp-config.json` (pinned version)
- `docs/install/` (per-client setup)
