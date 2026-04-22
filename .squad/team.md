# Squad Team

> mcp-server-azure-architect

## Coordinator

| Name | Role | Notes |
|------|------|-------|
| Squad | Coordinator | Routes work, enforces handoffs and reviewer gates. |

## Members

<!-- copilot-auto-assign: true -->

| Name | Role | Charter | Status |
|------|------|---------|--------|
| Lead | Team Lead and Architect | [charter](agents/lead/charter.md) | Active |
| Atlas | ARG and KQL Engineer | [charter](agents/atlas/charter.md) | Active |
| Forge | MCP Server Runtime Engineer | [charter](agents/forge/charter.md) | Active |
| Iris | Copilot Skills Author | [charter](agents/iris/charter.md) | Active |
| Burke | Companion-MCP Integration Engineer | [charter](agents/burke/charter.md) | Active |
| Sentinel | Security and Read-Only Enforcement | [charter](agents/sentinel/charter.md) | Active |
| Sage | Research and Documentation | [charter](agents/sage/charter.md) | Active |
| @copilot | 🤖 GitHub Copilot Coding Agent | n/a (uses `.github/copilot-instructions.md`) | Active |

### @copilot Capability Profile

`@copilot` runs on GitHub-hosted compute and picks up issues assigned to it. It opens draft PRs from `copilot/*` branches.

| Domain | Confidence | Notes |
|---|---|---|
| Python + FastMCP server code (small to medium scope) | 🟢 | Stack is locked per ADR-001. |
| Pytest test authoring | 🟢 | Mocked Azure SDK, offline tests. |
| Markdown docs, ADRs, READMEs | 🟢 | Honors AGENTS.md style rules (no em dashes). |
| Copilot CLI extensions in `.github/extensions/` | 🟢 | Format documented in repo. |
| Vendoring upstream files by commit SHA | 🟢 | Mechanical with clear acceptance criteria. |
| KQL composition for ALZ scoring | 🟡 | Best when the underlying queries are already vendored. |
| Reviewer gates and architecture verdicts | 🔴 | Lead retains these. Do not auto-assign reviewer issues. |
| Multi-package refactors | 🔴 | Keep scope per-PR small. |

Auto-assignment is enabled (see HTML comment above). The Lead may still re-route any issue by swapping `squad:*` labels.

## Project Context

- **Project:** mcp-server-azure-architect, MCP server + Copilot CLI skills bundle for Azure architects
- **Stack:** Python 3.11+ with FastMCP (per ADR-001, accepted 2026-04-22). Hatchling build, ruff, mypy, pytest. Distribution via `uvx mcp-server-azure-architect`.
- **Created:** 2026-04-22
