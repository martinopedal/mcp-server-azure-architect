# AGENTS.md: mcp-server-azure-architect

Read this first. Then read `.github/copilot-instructions.md` and `.squad/team.md`.

## Mission

Ship an MCP server + Copilot CLI skills bundle that fills the architect-shaped gap above `azure-mcp` with named ALZ checklist queries and ALZ Corp scorecard composition (pricing retail SKU lookups, not quota/Advisor generics which `azure-mcp` already covers per ADR-004). Architect-specific Copilot skills orchestrate the kit. Curated `mcp-config.json` wires read-only companion servers (mermaid, drawio, microsoft-learn, kubernetes, terraform).

## Project conventions

- **No em dashes.** Use periods or commas.
- **Read-only.** Server, skills, and examples must be read-only against Azure. No mutation tools, ever.
- **No credentials at rest.** Token-scrub on any logging or persistence.
- **Source-of-truth for ALZ queries:** `martinopedal/alz-checklist-queries` and `martinopedal/alz-graph-queries`. Vendor a snapshot, do not fork.
- **Companion servers stay companions.** We do not proxy or wrap `azure-mcp`. Do not duplicate its tools.
- **Citations required.** Every ALZ checklist query references its checklist ID and the source query commit.

## Squad workflow

1. Issues labeled `squad` go to **Lead** for triage.
2. Lead adds a `squad:{member}` label and a triage comment.
3. The named member picks up the issue in their next session.
4. PRs require at least one non-author reviewer and clean CI.

## Agent quick reference

| Domain | Owner |
|---|---|
| MCP server runtime, tool registration | Forge |
| ARG / KQL queries (vendored from alz-* repos) | Atlas |
| Copilot CLI skill authoring | Iris |
| Companion-MCP integration, `mcp-config.json`, client docs | Burke |
| Read-only enforcement, auth, secret scrubbing | Sentinel |
| Research, runtime selection, examples, docs | Sage |
| Triage, design, PR sign-off | Lead |

## Validation gates before merge

- Ruff lint and format clean.
- Mypy type check passes.
- Pytest unit tests pass (Python 3.11, 3.12).
- MCP Inspector smoke test: server starts, all tools enumerate with valid JSON Schema (Forge issue #19).
- Read-only AST gate enforced: no Azure SDK `Begin*`, `Create*`, `Update*`, or `Delete*` calls in the call graph (Sentinel issue #7).
- gitleaks scan passes (no embedded secrets).
- CodeQL scan passes (security analysis).
- Dependency-review check passes (supply chain).
- Branch protection: all required checks pass, strict mode enforced on main.

## Related

- [.github/copilot-instructions.md](.github/copilot-instructions.md)
- [.squad/team.md](.squad/team.md)
- [.squad/routing.md](.squad/routing.md)
- [docs/adr/0004-companion-server-bar.md](docs/adr/0004-companion-server-bar.md). Authoritative scope decision on companion vs native tools.
