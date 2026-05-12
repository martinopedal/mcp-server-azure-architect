# drawio: Draw.io Diagram Creation and Export

## Purpose

Provides diagram creation and export capabilities via Draw.io. Architects use this to design complex architecture diagrams, create Visio-replacement visuals, and export diagrams for stakeholder presentations. Complements mermaid by enabling more elaborate and customizable diagram creation beyond Mermaid's syntax-driven approach.

## Source

Repository: [lgazo/drawio-mcp-server](https://github.com/lgazo/drawio-mcp-server)  
Maintainer: lgazo (community-maintained)

## Distribution

Installed via npm:

```
npm install drawio-mcp-server@2.0.4
```

Or installed on demand via npx in `.copilot/mcp-config.json`:

```
"command": "npx",
"args": ["-y", "drawio-mcp-server@2.0.4"]
```

## Auth Model

No authentication required. Rendering is local; no external credentials needed.

## Network Egress

None. Draw.io rendering is local to the client. No external endpoints contacted. (Note: Some versions of Draw.io may contact draw.io servers for storage; this companion does not enable cloud storage integration.)

## Read-Only Posture

**Fully read-only.** Diagram creation and export only. No mutations to external systems.

Tools are diagram creation and export functions. Output is SVG, PNG, or PDF. Diagrams are created in memory and exported; no persistent storage is modified.

## Supply Chain Notes

**Version pinned:** 2.0.4 (semver release)

**Provenance:** Published to npm by lgazo. Verified in npm registry at [npmjs.com/drawio-mcp-server](https://www.npmjs.com/package/drawio-mcp-server). npm provenance signatures available.

**CVE status:** Depends on draw.io and export libraries (mxgraph, pdf-lib, etc.). These are actively maintained. No known CVEs specific to drawio-mcp-server as of 2026-05-12. Recommended: monitor npm advisory database for transitive dependency updates.

**Release cadence:** Community-maintained. Last release 2026-Q1. Stable for 6+ months.

**Maintenance signal:** Repository shows recent commits and active maintenance. License is clear (MIT). No signs of abandonment. Updates track draw.io spec changes.

## ADR-004 Fit

- ✓ **Criterion 1 (Stable Upstream):** YES. Semver releases with release notes.
- ✓ **Criterion 2 (Signed Releases):** YES. npm provenance signatures.
- ✓ **Criterion 3 (Narrow Scope):** YES. Diagram creation and export only.
- ✓ **Criterion 4 (Complementary to azure-mcp):** YES. Diagrams are orthogonal to Azure resource queries.
- ✓ **Criterion 5 (Maintenance Signal):** YES. Last release 2026-Q1; active community.
- ✓ **Criterion 6 (Read-Only):** YES. Creation and export only. No mutations to external systems.
- ✓ **Criterion 7 (Documented Install):** YES. Documented in `docs/install/`.

## Removal Cost

If drawio is uninstalled:

- Architects lose the ability to create elaborate architecture diagrams within design reviews.
- Architects must use external Draw.io editor (draw.io web app) or alternative tools.
- Stakeholder presentation deck creation is interrupted; must export separately.

**Risk:** Low. Design work continues with external tools, but conversation flow is interrupted.

## References

- [lgazo/drawio-mcp-server](https://github.com/lgazo/drawio-mcp-server)
- [npm registry drawio-mcp-server](https://www.npmjs.com/package/drawio-mcp-server)
- [draw.io](https://www.drawio.com)
- `.copilot/mcp-config.json` (pinned version)
- `docs/install/` (per-client setup)

## TODO: Deeper Supply Chain Review

- Monitor lgazo/drawio-mcp-server repository for any inactivity signals.
- Test SVG and PDF export to verify output quality.
- Review transitive dependency CVE database quarterly.
