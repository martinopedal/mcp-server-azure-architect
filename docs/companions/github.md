# github: GitHub Repository and Issue Access

## Purpose

Provides read-only access to GitHub repositories, issues, pull requests, and workflow information. Architects use this to review IaC pull requests, understand design intent diffs, and validate infrastructure-as-code changes before merge. Complements azure-mcp by enabling code review and intent tracking in the IaC repository.

## Source

Repository: [github/github-mcp-server](https://github.com/github/github-mcp-server)  
Maintainer: GitHub (official product)

## Distribution

Installed via Docker:

```
docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN \
  ghcr.io/github/github-mcp-server:latest
```

Configured in `.copilot/mcp-config.json` with environment variable passthrough.

## Auth Model

Requires GitHub Personal Access Token (PAT) at runtime:

```
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_XXXX
```

No token in config files. Token must be set in the caller's environment. Follows project constraint: DefaultAzureCredential model; no hardcoded secrets.

## Network Egress

Connects to:

- `https://api.github.com` (GitHub REST API)
- `https://github.com` (web interface for OAuth, if needed)

Requires internet access to GitHub (public or GitHub Enterprise).

## Read-Only Posture

**Read-only by design.** Exposes queries and read operations only.

Examples of read-only tools:
- Search repositories
- Fetch pull request details
- List issues
- Retrieve workflow run history

No tools for creating, updating, deleting repositories or issues. No push, merge, or delete capabilities. Write operations (e.g., commenting on issues) are not exposed.

## Supply Chain Notes

**Version pinned:** latest (Docker image tag)

**Provenance:** Published by GitHub to ghcr.io registry. Docker images are signed via Docker Content Trust (DCT). Official GitHub product.

**CVE status:** GitHub maintains the server as part of their official tooling. Security updates are published to the `latest` tag as they become available. No known CVEs specific to the github-mcp-server as of 2026-05-12.

**Release cadence:** GitHub publishes updates to the `latest` Docker image continuously. Semantic versioning is not used; image updates are identified by SHA.

**Note:** Using `latest` tag means architects get security updates automatically but may see behavior changes without advance notice. Consider pinning to a specific image SHA if stability is critical.

## ADR-004 Fit

- ✅ **Criterion 1 (Stable Upstream):** YES. Official GitHub product with stable API.
- ✅ **Criterion 2 (Signed Releases):** YES. Docker images signed via Docker Content Trust.
- ✅ **Criterion 3 (Narrow Scope):** YES. GitHub API only; no compute, no cloud platforms.
- ✅ **Criterion 4 (Complementary to azure-mcp):** YES. Version control APIs are orthogonal to Azure resource management.
- ✅ **Criterion 5 (Maintenance Signal):** YES. GitHub maintains; actively updated.
- ✅ **Criterion 6 (Read-Only):** YES. Read-only query surface. No mutation tools.
- ✅ **Criterion 7 (Documented Install):** YES. Documented in `docs/install/` with PAT setup.

## Removal Cost

If github is uninstalled:

- Architects lose the ability to inspect pull request details and workflow history during IaC reviews.
- Design-review skill loses the ability to cross-reference commit history and intent.
- Architects must manually navigate to GitHub to review code changes.

**Risk:** Medium. Design work continues with manual GitHub browsing, but skill efficiency is reduced.

## References

- [github/github-mcp-server](https://github.com/github/github-mcp-server)
- [GitHub Container Registry (ghcr.io)](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- `.copilot/mcp-config.json` (Docker configuration)
- `docs/install/` (per-client setup)

## TODO: Deeper Supply Chain Review

- Verify GitHub PAT security policy and token rotation best practices.
- Test image signature verification locally using cosign.
- Clarify image update frequency and breaking change notifications.
