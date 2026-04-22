# Companion Compatibility Matrix

This matrix tracks which companions are tested with `mcp-server-azure-architect`, their pinned versions, and known issues. Future Burke sessions will expand the "Tested" column as smoke tests are added.

## Status Key

- **Pinned version:** The exact version locked in `.copilot/mcp-config.json` for reproducibility.
- **Tested with this server:** Green (✓) = confirmed working; Yellow (○) = pending; Red (✗) = known issue.
- **Known issues:** Blockers or workarounds.

## Matrix

| Companion | Repository | Pinned Version | Tested | Known Issues |
|-----------|-----------|---|---|---|
| **azure-mcp** | [Microsoft/mcp](https://github.com/microsoft/mcp) | `2.0.1` | ✓ | None. Microsoft's stable. |
| **microsoft-learn** | [Microsoft Learn Hosted](https://learn.microsoft.com/api/mcp) | N/A (hosted) | ✓ | Requires internet connection. |
| **github** | [github/github-mcp-server](https://github.com/github/github-mcp-server) | `latest` | ○ | Requires Docker. GitHub PAT must be set. |
| **mermaid** | [hustcc/mcp-mermaid](https://github.com/hustcc/mcp-mermaid) | `0.4.1` | ○ | Package name corrected from `@mermaid-js/mermaid-mcp` (which does not exist on npm). |
| **drawio** | [lgazo/drawio-mcp-server](https://github.com/lgazo/drawio-mcp-server) | `2.0.4` | ○ | None known. Requires npm or Docker. |
| **kubernetes** | [kubernetes-mcp-server](https://www.npmjs.com/package/kubernetes-mcp-server) | `0.0.53` | ○ | Requires kubectl context and kubeconfig. |
| **terraform** | [hashicorp/terraform-mcp-server](https://github.com/hashicorp/terraform-mcp-server) | `v0.5.1` | ○ | Requires Docker. Terraform CLI recommended. |
| **mcp-server-azure-architect** | [martinopedal/mcp-server-azure-architect](https://github.com/martinopedal/mcp-server-azure-architect) | uvx (unpinned; PyPI pending) | ○ | Runtime: Python + FastMCP (ADR-001 approved). End users: `uvx mcp-server-azure-architect`. Dev: `uv run mcp-server-azure-architect`. Version pinning deferred until PyPI publication. |

## Version Rationale

### azure-mcp: 2.0.1

Stable release by Microsoft. Latest beta (3.0.0-beta.4) is active but not recommended for production use yet.

### microsoft-learn: Hosted (no pin needed)

Endpoint is hosted at `https://learn.microsoft.com/api/mcp` and always up to date. No self-hosting required.

### github: latest

Docker image is continuously updated. For pin-heavy workflows, use explicit semver tags like `v0.5.0` from [ghcr.io/github/github-mcp-server](https://ghcr.io/github/github-mcp-server).

### mermaid: 0.4.1

Official npm package: `mcp-mermaid` (not `@mermaid-js/mermaid-mcp`, which does not exist). Version 0.4.1 is the latest stable from [hustcc/mcp-mermaid](https://github.com/hustcc/mcp-mermaid).

### drawio: 2.0.4

Latest stable from [lgazo/drawio-mcp-server](https://github.com/lgazo/drawio-mcp-server). Includes dependency security upgrades.

### kubernetes: 0.0.53

Latest npm package. Requires active kubectl context and valid kubeconfig for cluster inspection.

### terraform: v0.5.1

Latest stable from HashiCorp. Available as `hashicorp/terraform-mcp-server:v0.5.1` on Docker.

### mcp-server-azure-architect: uvx (PyPI pending)

Python + FastMCP runtime (ADR-001, approved 2026-04-22). End-user installation via `uvx mcp-server-azure-architect` (once package is published to PyPI). Dev installation via `uv run mcp-server-azure-architect`. Version pinning deferred until PyPI publication; once published, will pin to a release tag for reproducibility.

## Testing Roadmap

Future smoke tests will verify:

1. Each companion loads in all four supported clients (Copilot CLI, Claude Desktop, Cursor, VS Code Copilot).
2. Basic tool invocation works (e.g., `@azure-mcp list resource groups` succeeds).
3. Dependency chains work (e.g., `@mermaid` and `@drawio` can generate and export diagrams).
4. Auth scenarios work (e.g., GitHub PAT, kubeconfig, Terraform state).

This matrix will be updated as tests are added.

## How to Pin a New Version

When an upstream releases a new version:

1. Test it locally by updating `.copilot/mcp-config.json` and validating in your client.
2. Verify tools still work end-to-end.
3. Update this matrix with the new version and rationale.
4. Open a PR with the change and link any relevant upstream release notes.

## Questions?

- **Client-specific setup:** See [docs/install/](.) for per-client guides.
- **Runtime decision:** See [AGENTS.md](../../AGENTS.md) for Burke's status updates.
- **Upstream issues:** Link directly to the companion's GitHub repo.
