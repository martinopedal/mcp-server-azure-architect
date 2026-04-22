# Contributing

This is a solo-maintained repository. Contributions are welcome but the maintainer reviews and merges everything.

## Project posture

This repo is a **read-only** MCP server that complements [`azure-mcp`](https://github.com/microsoft/azure-mcp). It is **not an official Microsoft product**.

The wedge is:

- a **named ALZ checklist query catalog** (`alz_query_by_id`)
- a **scorecard composition** that synthesizes multiple raw queries into one ranked result (`alz_scorecard`)
- **architect-specific Copilot skills** (`design-review`, `alz-gap-check`, `ingress-migration-plan`)

We do **not** ship generic quota wrappers, generic advisor wrappers, or generic Azure SDK aggregators. `azure-mcp` already covers those.

## Process

1. Fork the repo
2. Create a branch: `git checkout -b feat/your-change`
3. Make your changes
4. Sign off your commit: `git commit -s -m "feat: describe your change"`
5. Open a pull request against `main`

## Style

- No em dashes in any markdown or code comments.
- Authentication: `DefaultAzureCredential` only. No PATs in code.
- Read-only: no Azure SDK call may invoke a method on the `Begin*`, `Create*`, `Update*`, `Delete*` surface.

## Validation gates

Every PR runs:

- Build, lint, and unit tests for the chosen runtime
- A read-only static analysis test that proves no Azure write call exists in the call graph
- gitleaks
- CodeQL
- MCP Inspector smoke test (server starts, tools enumerate, schemas validate)

## Identifier provenance

Any hard-coded Azure identifier (policy ID, initiative ID, role definition ID, recommendation ID, ALZ checklist item ID) must be tagged with one of:

- `# provenance: public-builtin`
- `# provenance: public-source <repo or doc URL>` (e.g., `martinopedal/alz-checklist-queries@<sha>`)
- `# provenance: must-not-ship`

The vendored ALZ checklist snapshot lives in `data/alz-queries/` with a `MANIFEST.md` that records the source repo and pinned commit SHA.

## Companion MCP servers

The shipped `mcp-config.json` lists recommended companion servers. Adding a companion requires:

1. A Sage research note in `docs/companions/<name>.md` justifying inclusion (gap filled, alternatives considered, license, supply chain).
2. A Sentinel review of the source (signed releases, maintainer reputation, repo activity).
3. A version pin.

## AI-assisted contributions

AI-assisted contributions are welcome. Disclose AI use in the PR description.

## Commit sign-off

All commits must include a `Signed-off-by` trailer (`git commit -s`). Co-authorship by Copilot is recorded with `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` when applicable.
