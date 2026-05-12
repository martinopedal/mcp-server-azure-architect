# ADR-005: SemVer and Release Cadence

## Status

Accepted (2026-05-15, Burke)

## Context

The mcp-server-azure-architect project is approaching its first tagged release (v0.1.0). We need a clear policy on semantic versioning, what constitutes the public surface, and how frequently we cut releases.

The project ships three distinct layers:
1. **MCP tools** registered in the server (the primary public API)
2. **Copilot CLI skills** that orchestrate MCP tools
3. **Vendored ALZ queries** that power ALZ-related tools

Each layer evolves at a different pace. MCP tools must follow a stable contract with downstream MCP clients. Skills are orchestration logic and can evolve more freely. Vendored queries change whenever we refresh the upstream snapshot.

### Pre-1.0 Stability Expectations

Per SemVer 2.0.0 section 4: "Major version zero (0.y.z) is for initial development. Anything MAY change at any time. The public API SHOULD NOT be considered stable." However, we want to minimize churn for early adopters while retaining flexibility to iterate quickly.

### Distribution Model

The server is distributed via PyPI as `mcp-server-azure-architect` and installed with `uvx mcp-server-azure-architect`. Users pin versions in their MCP client config (e.g., `mcp-config.json`). Frequent breaking changes create upgrade friction.

## Decision

### Public Surface Definition

The **public surface** governed by SemVer is:

1. **MCP tool registrations:** Tool names, parameter names, parameter types, return value shape, docstrings (which act as inline schema documentation).
2. **`mcp-config.json` schema:** The structure of the curated companion kit config.
3. **ALZ manifest pinning policy:** The contract that `data/alz-queries/manifest.json` exists and tracks upstream commit SHAs.

**Not part of the public surface:**

- Copilot CLI skills (free to evolve in any release, including renames, signature changes, or removal).
- Internal Python module structure.
- Private functions and classes not exposed via MCP tools.
- CI/CD workflow definitions.

### SemVer Interpretation (Pre-1.0)

Given `0.y.z`:

- **MAJOR (to 1.0.0):** When the tool surface is stable enough for production use and we commit to backward compatibility.
- **MINOR (`y`):** Breaking changes to tool names, parameters, or return shapes. New tools. Vendored ALZ snapshot refreshes (queries may change behavior). Changes to `mcp-config.json` schema.
- **PATCH (`z`):** Bug fixes to existing tools. Documentation updates. Internal refactors. Security patches. No user-visible behavior changes.

### SemVer Interpretation (Post-1.0)

Once we reach 1.0.0, strict SemVer applies:

- **MAJOR:** Breaking changes to any tool name, parameter, or return shape. Removal of tools. Incompatible `mcp-config.json` schema changes.
- **MINOR:** New tools. New optional parameters with defaults. Backward-compatible changes to `mcp-config.json`.
- **PATCH:** Bug fixes. Documentation. Internal refactors. Security patches.

### ALZ Query Refresh Policy

Vendored ALZ query refreshes count as **MINOR** bumps because:
- Query content changes can alter scorecard results.
- New queries may be added or removed.
- Downstream tooling (like `alz_scorecard`) sees different outputs.

However, the *mechanism* of query vendoring (manifest structure, lookup by checklist ID) is part of the public surface and cannot break without a MAJOR bump.

### Release Cadence

**Pre-1.0:** As-needed, no fixed window. Cut a release when:
- A new tool lands.
- A bug fix merits immediate distribution.
- An ALZ query snapshot refresh is due.
- A security patch lands.

**Post-1.0:** Monthly or quarterly cadence, depending on change volume. Patch releases as-needed for critical fixes.

### Version Bump and Tag Process

Documented in `docs/release.md`. Summary:
1. Update `CHANGELOG.md` (move Unreleased to versioned section with date).
2. Bump `version` in `pyproject.toml`.
3. Commit with message `chore(release): vX.Y.Z`.
4. Tag with `vX.Y.Z` and push.
5. GitHub Actions workflow builds, tests, publishes to PyPI, and creates GitHub Release.

## Consequences

### Positive

- **Clear contract.** Users know what to expect from version bumps.
- **Fast iteration pre-1.0.** We can refine the tool surface based on early feedback without strict backward compatibility burden.
- **Skill flexibility.** Skills remain experimental and can be reworked without version implications.
- **ALZ refresh transparency.** Users see that query refreshes = minor bumps and can review changelogs before upgrading.

### Negative

- **Pre-1.0 churn risk.** Minor bumps may break downstream automations. Mitigated by clear changelog and migration notes.
- **Skill instability signal.** Excluding skills from public surface means they may disappear without warning. Acceptable for now, given v0 status. Revisit post-1.0.

### Neutral

- **PyPI publishing.** First release to a new package name requires one-time PyPI trusted publishing setup (documented in `docs/release.md`). Subsequent releases are automatic.

## References

- [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)
- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- ADR-002: ALZ Query Vendoring Policy (defines refresh procedure)
- `docs/release.md` (operator runbook)
