# Squad Decisions

## Active Decisions

### ADR-001: Runtime Choice

**Decision:** APPROVE WITH NITS

**Runtime locked:** Python with FastMCP.

**Rationale:** Cold start <1s, lowest contributor friction, mature Azure SDK, auto-generates JSON Schema from type hints, and uvx distribution fits the tool model.

**Details:** Sage's ADR is sound. All project constraints respected. Cold-start, auth, read-only boundary, and CI gates are addressed with citations. Two minor documentation nits (benchmark URL, uvx inline link) to address in follow-up. Forge can proceed with Python implementation.

**Status:** Accepted (2026-04-22, Lead)

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
