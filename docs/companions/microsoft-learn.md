# microsoft-learn: Microsoft Learn Documentation Lookup

## Purpose

Provides grounded Microsoft Learn documentation lookup. Architects use this to reduce hallucination and ground design decisions in current Microsoft guidance. Examples: cost optimization patterns, security best practices, Azure governance design, and product capability research. Complements azure-mcp by providing authoritative conceptual guidance rather than live resource state.

## Source

Hosted service: Microsoft Learn MCP endpoint  
URL: `https://learn.microsoft.com/api/mcp`  
Maintainer: Microsoft

## Distribution

Accessed via hosted endpoint. No local installation required. Configured directly in `.copilot/mcp-config.json`:

```
"url": "https://learn.microsoft.com/api/mcp"
```

No npm, pip, or docker setup needed.

## Auth Model

No authentication required. Public API endpoint. No credentials in config or code.

## Network Egress

Connects to:

- `https://learn.microsoft.com` (Microsoft Learn API)

Requires internet access to Microsoft's hosted services.

## Read-Only Posture

**Fully read-only.** Search and document retrieval only. No mutation capability.

Tools are read-only search operations over published Microsoft documentation.

## Supply Chain Notes

**Version pinned:** hosted (endpoint URL is stable)

**Provenance:** Hosted by Microsoft. Infrastructure is Microsoft's responsibility. No package to sign; endpoint availability is guaranteed by Microsoft SLA.

**CVE status:** Endpoint is managed by Microsoft. No self-hosted supply chain risk. HTTP client libraries are standard (curl, nodejs http). No known CVEs in the endpoint itself as of 2026-05-12.

**Release cadence:** Microsoft maintains continuously. Documentation updates are immediate; API schema is stable.

## ADR-004 Fit

- ✓ **Criterion 1 (Stable Upstream):** YES. Hosted endpoint with stable URL.
- ✓ **Criterion 2 (Signed Releases):** N/A (hosted endpoint; Microsoft infrastructure is trust boundary).
- ✓ **Criterion 3 (Narrow Scope):** YES. Documentation lookup only.
- ✓ **Criterion 4 (Complementary to azure-mcp):** YES. Docs, not APIs. No overlap with resource queries.
- ✓ **Criterion 5 (Maintenance Signal):** YES. Microsoft maintains continuously.
- ✓ **Criterion 6 (Read-Only):** YES. Search and retrieval only.
- ✓ **Criterion 7 (Documented Install):** YES. Documented in `docs/install/`.

## Removal Cost

If microsoft-learn is uninstalled:

- Architects lose access to grounded Microsoft guidance during design reviews.
- Design-review skill loses the ability to reference current best practices.
- Increased reliance on generic internet search or potentially outdated documentation.

**Risk:** Medium. Important for quality guidance, but design work continues with generic web search or manual navigation to docs.

## References

- [Microsoft Learn](https://learn.microsoft.com)
- `.copilot/mcp-config.json` (hosted URL)
- `docs/install/` (per-client setup)

## TODO: Deeper Supply Chain Review

- Verify Learn API SLA and availability guarantees.
- Test fallback behavior if endpoint is unavailable.
