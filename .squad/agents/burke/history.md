# Burke: Session History

## Session 1: mcp-config.json v0 audit and per-client install docs (2026-04-22)

Audited the curated `mcp-config.json` and pinned all companion versions where upstream supports it. Discovered incorrect package name for mermaid (`@mermaid-js/mermaid-mcp` does not exist; corrected to `mcp-mermaid@0.4.1`). Created four per-client install guides (Copilot CLI, Claude Desktop, Cursor, VS Code Copilot) with manual merge instructions for v0. Added compatibility matrix with version rationale and testing roadmap. No security findings. Decision document in `.squad/decisions/inbox/burke-mcp-config-audit-v0.md`.
