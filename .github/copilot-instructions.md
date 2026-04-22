# Copilot Instructions — mcp-server-azure-architect

## Project

MCP server and Copilot CLI skills bundle for Azure architects. Native tools fill the gap above `azure-mcp` (named ALZ queries, scorecard, quota planner, Advisor surfacing). Skills orchestrate the kit. Curated `mcp-config.json` wires companion servers.

## Style

- No em dashes. Use periods or commas.
- Concise, direct prose.
- Cite MS docs or upstream MCP spec for any non-trivial choice.

## Architecture rules

- **Read-only.** No mutation tools.
- **Local-first.** No hosted multi-tenant deployment in scope.
- **Source-of-truth for ALZ queries:** vendored snapshot from `martinopedal/alz-checklist-queries` and `martinopedal/alz-graph-queries`. Track upstream commit SHA in the snapshot manifest.
- **Companion servers are not bundled.** They are recommended via `mcp-config.json`. Never proxy or wrap them.
- **Auth:** DefaultAzureCredential (env, managed identity, az cli) only. No PATs, no SPN secrets in code or config.

## Squad

Read `.squad/team.md` and `.squad/routing.md`. Use the `squad` label on issues for triage; named members pick up `squad:{name}` labels.

## Commit and PR conventions

- Commit message: imperative mood, scope prefix (`feat(server):`, `fix(skills):`, `docs:`).
- Always include the trailer `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`.
- PR body cross-links the issue (`Closes #N`) and notes which validation gates passed.
