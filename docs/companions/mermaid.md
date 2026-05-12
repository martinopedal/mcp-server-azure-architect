# mermaid: Mermaid Diagram Rendering

## Purpose

Renders Mermaid diagrams inline from design review conversations. Architects use this to visualize architecture topologies, sequence flows, state machines, and dependency graphs during design discussions with Copilot. Complements azure-mcp by enabling visual communication of infrastructure designs without leaving the chat context.

## Source

Repository: [hustcc/mcp-mermaid](https://github.com/hustcc/mcp-mermaid)  
Maintainer: hustcc (community-maintained)

## Distribution

Installed via npm:

```
npm install mcp-mermaid@0.4.1
```

Or installed on demand via npx in `.copilot/mcp-config.json`:

```
"command": "npx",
"args": ["-y", "mcp-mermaid@0.4.1"]
```

## Auth Model

No authentication required. Rendering is local; no external credentials needed.

## Network Egress

None. Mermaid rendering is local to the client. No external endpoints contacted.

## Read-Only Posture

**Fully read-only.** Rendering only. No mutation capability.

Tools are diagram rendering functions. Output is SVG or PNG; no external systems are modified.

## Supply Chain Notes

**Version pinned:** 0.4.1 (semver release)

**Provenance:** Published to npm by hustcc. Verified in npm registry at [npmjs.com/mcp-mermaid](https://www.npmjs.com/package/mcp-mermaid). npm provenance signatures available.

**CVE status:** Depends on mermaid library (js-based rendering engine). Mermaid is widely used and actively maintained. No known CVEs specific to mcp-mermaid as of 2026-05-12. Recommended: monitor npm advisory database for transitive dependency updates.

**Release cadence:** Community-maintained. Last release 2026-Q1. Stable for 6+ months.

**Maintenance signal:** Repository shows steady commits and active maintenance. No signs of abandonment. Update cycle aligns with mermaid spec changes.

## ADR-004 Fit

- ✅ **Criterion 1 (Stable Upstream):** YES. Semver releases with release notes.
- ✅ **Criterion 2 (Signed Releases):** YES. npm provenance signatures.
- ✅ **Criterion 3 (Narrow Scope):** YES. Diagram rendering only.
- ✅ **Criterion 4 (Complementary to azure-mcp):** YES. Diagrams are orthogonal to Azure resource queries.
- ✅ **Criterion 5 (Maintenance Signal):** YES. Last release 2026-Q1; active community.
- ✅ **Criterion 6 (Read-Only):** YES. Rendering only. No mutations.
- ✅ **Criterion 7 (Documented Install):** YES. Documented in `docs/install/`.

## Removal Cost

If mermaid is uninstalled:

- Architects lose the ability to render diagrams inline during design reviews.
- Design-review skill loses visualization capability.
- Architects must manually render or export diagrams via external mermaid editor (mermaid.live).

**Risk:** Low. Design work continues with external tools, but conversation flow is interrupted.

## References

- [hustcc/mcp-mermaid](https://github.com/hustcc/mcp-mermaid)
- [npm registry mcp-mermaid](https://www.npmjs.com/package/mcp-mermaid)
- [Mermaid Specification](https://mermaid.js.org)
- `.copilot/mcp-config.json` (pinned version)
- `docs/install/` (per-client setup)

## TODO: Deeper Supply Chain Review

- Monitor hustcc/mcp-mermaid repository for any inactivity signals.
- Review mermaid library CVE database quarterly.
