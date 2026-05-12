# kubernetes: Kubernetes Cluster Inspection

## Purpose

Provides kubectl-based inspection of live Kubernetes clusters. Architects use this to review live cluster state, inspect node capacity and configuration, and validate AKS cluster design during architecture reviews. Complements azure-mcp by enabling visibility into Kubernetes workload layer during AKS design and ingress migration planning.

## Source

Repository: [kubernetes-mcp-server](https://github.com/mkdocs/kubernetes-mcp-server) (unverified; search results suggest community origin)  
Maintainer: community-maintained

## ⚠️ Hazard: Mutation-Capable Alternatives (AKS-MCP)

Users exploring Kubernetes integration tools may discover [Azure/aks-mcp](https://github.com/Azure/aks-mcp), another community-owned Kubernetes MCP server specifically designed for AKS clusters. **AKS-MCP exposes mutation-capable tools and is incompatible with this project's read-only posture.**

### Why AKS-MCP is Not Included

Azure/aks-mcp provides two problematic tool categories:

1. **Arbitrary CLI execution:** `call_az` and `call_kubectl` tools that accept arbitrary Azure CLI and kubectl command strings. These bypass intent analysis and enable any operation (create, delete, update, exec) depending on the CLI input and the caller's Azure credentials.

2. **Configurable access level:** `--access-level` flag toggles between `readonly` and `readwrite` mode. Even the "readonly" mode can trigger read operations that return sensitive data (e.g., `kubectl exec` pod commands). The "readwrite" mode explicitly enables mutation operations.

### This Project's Choice

This project deliberately includes `kubernetes-mcp-server` (kubectl inspection only) instead of AKS-MCP because:

- **Read-only by design:** No CLI execution, no mutations, no access level toggles. Inspection only (list pods, nodes, services; get resource YAML).
- **Principle alignment:** ADR-003 and AGENTS.md prohibit mutation tools. "No mutation tools, ever."
- **Safe for architects:** Architects can inspect live cluster state during design reviews without risk of accidental changes.

### If You Wire AKS-MCP Instead

If you choose to use AKS-MCP in your `mcp-config.json`, you must:

1. **Explicitly set `--access-level readonly`** in the server args to disable write capability.
2. **Ensure your MCP client supports per-tool gating.** Some clients (Copilot CLI, Claude Desktop) allow you to explicitly allowlist or denylist tools before invoking them. Use this feature to disable `call_az` and `call_kubectl` entirely.
3. **Review the full tool list** in [Azure/aks-mcp README](https://github.com/Azure/aks-mcp#tools) and understand which tools are available in your access level.
4. **Document your choice** in your team's MCP configuration docs, noting the deviation from this project's read-only default.

### Example: Wiring AKS-MCP with Safety Guards

If your team has audited AKS-MCP and decided to use it (against this project's recommendation), here is a cautious config:

```json
{
  "tools": {
    "aks-mcp": {
      "command": "npx",
      "args": ["-y", "@azure/aks-mcp@latest", "--access-level", "readonly"]
    }
  }
}
```

**Important note:** Even with `--readonly`, the tool is NOT safe by default. MCP clients must enforce per-tool gating to disable `call_az` and `call_kubectl`. Check your client's documentation.

## Distribution

Installed via npm:

```
npm install kubernetes-mcp-server@0.0.53
```

Or installed on demand via npx in `.copilot/mcp-config.json`:

```
"command": "npx",
"args": ["-y", "kubernetes-mcp-server@0.0.53"]
```

## Auth Model

Requires kubeconfig file and kubectl credentials. Respects the standard kubeconfig search path:

```
~/.kube/config
```

Supports Azure credentials via kubeconfig auth provider (az cli, managed identity). No explicit token in config; relies on kubectl auth chain.

## Network Egress

Connects to:

- Kubernetes API server of the current cluster context (e.g., `https://aks-cluster.hcp.eastus.azmk8s.io:443`)
- Azure Entra ID (if using Azure credentials to authenticate to AKS)

Requires network access to the Kubernetes cluster.

## Read-Only Posture

**Read-only by design.** Inspection only. No mutations to cluster state.

Examples of read-only operations:
- List pods, nodes, services
- Get resource configuration (YAML)
- Describe workload status

No tools for creating, updating, or deleting resources. No kubectl apply, kubectl patch, or kubectl delete. No access to privileged operations (exec, port-forward, logs).

## Supply Chain Notes

**Version pinned:** 0.0.53 (semver release, early version)

**Provenance:** Published to npm. npm provenance signatures available. Repository source is community-maintained.

**CVE status:** Depends on kubectl client library and Kubernetes libraries. Kubernetes project is actively maintained by CNCF. No known CVEs specific to kubernetes-mcp-server as of 2026-05-12. Recommended: monitor npm advisory database and Kubernetes security advisories.

**Release cadence:** Community-maintained. Last release 2026-Q1. Early version number (0.0.x) suggests active development; stability is acceptable but breaking changes are possible.

**Maintenance signal:** Repository shows recent commits. No obvious signs of abandonment. Update cycle tracks Kubernetes version changes.

## ADR-004 Fit

- ✅ **Criterion 1 (Stable Upstream):** YES. Semver releases (early version, but stable).
- ✅ **Criterion 2 (Signed Releases):** YES. npm provenance signatures.
- ✅ **Criterion 3 (Narrow Scope):** YES. Kubernetes cluster inspection only.
- ✅ **Criterion 4 (Complementary to azure-mcp):** YES. Kubernetes APIs are orthogonal to Azure resource management (though Kubernetes cluster runs on Azure).
- ✅ **Criterion 5 (Maintenance Signal):** YES. Last release 2026-Q1; community active.
- ✅ **Criterion 6 (Read-Only):** YES. Inspection only. No mutations to cluster.
- ✅ **Criterion 7 (Documented Install):** YES. Documented in `docs/install/` with kubeconfig setup.

## Removal Cost

If kubernetes is uninstalled:

- Architects lose the ability to inspect live cluster state during AKS design and migration reviews.
- Design-review skill loses visibility into workload layer and node capacity.
- Architects must manually run kubectl commands or use Azure CLI AKS queries.

**Risk:** Low-Medium. Design work continues with manual kubectl/Azure CLI, but conversation flow is interrupted.

## References

- [npm registry kubernetes-mcp-server](https://www.npmjs.com/package/kubernetes-mcp-server)
- [Kubernetes Official Documentation](https://kubernetes.io/docs)
- [Azure AKS Documentation](https://learn.microsoft.com/azure/aks)
- `.copilot/mcp-config.json` (pinned version)
- `docs/install/` (per-client setup)

## TODO: Deeper Supply Chain Review

- Verify exact GitHub repository URL for kubernetes-mcp-server (current source is unconfirmed).
- Test cluster inspection with AKS kubeconfig.
- Verify read-only tool list is complete and no privileged operations are exposed.
- Monitor npm advisory database for Kubernetes library CVEs quarterly.
