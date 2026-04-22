# AGENTS.md: mcp-server-azure-architect

Read this first. Then read `.github/copilot-instructions.md` and `.squad/team.md`.

## Mission

Ship an MCP server + Copilot CLI skills bundle that fills the architect-shaped gap above raw `azure-mcp`: named ALZ checklist queries, ALZ Corp scorecard, quota planner, Advisor surfacing, and orchestration skills. Plus a curated `mcp-config.json` that turns on the companion kit (mermaid, drawio, microsoft-learn, kubernetes, terraform).

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

To be defined once runtime is selected. Placeholder set:

- Lint and format clean for the chosen runtime.
- All tools list in MCP Inspector with valid JSON Schema.
- Read-only smoke test passes (no Azure write calls anywhere in the call graph).
- `mcp-config.json` validates against the MCP client config schema for at least one client.

## Related

- [.github/copilot-instructions.md](.github/copilot-instructions.md)
- [.squad/team.md](.squad/team.md)
- [.squad/routing.md](.squad/routing.md)
