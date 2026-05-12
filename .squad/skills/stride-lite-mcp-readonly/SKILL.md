# Skill: STRIDE-Lite Threat Model for Read-Only MCP Servers

**Skill Name:** stride-lite-mcp-readonly
**Author:** Sentinel
**Date:** 2026-04-22
**Status:** Draft
**Reusable:** Yes (any read-only MCP server)

## Overview

A threat modeling framework for **read-only MCP servers** that emphasizes the unique attack surface of MCP protocol and Azure service integration. Adapted from Microsoft's STRIDE methodology, simplified for the read-only constraint.

## When to Use

Apply this skill when:
- Designing a new read-only MCP server that exposes Azure, AWS, GCP, or similar cloud APIs.
- Reviewing a PR that adds new tools or parameters to a read-only MCP server.
- Conducting a security audit of an existing MCP server.
- Documenting supply chain risks for a server and its companion dependencies.

**Do NOT use for:** Mutation-capable tools, hosted multi-tenant services, or fully general-purpose API servers (too broad for this framework).

## Template

### 1. Scope Definition (5 min)

Define what is **in** and **out** of your threat model:

**In scope:**
- This server's tool definitions, parameter validation, and auth flow.
- Direct dependencies (e.g., Azure SDK, MCP library).
- Vendored or recommended companion servers.
- Logging and error handling.

**Out of scope:**
- The MCP client itself (Claude Desktop, Cursor, etc.).
- Third-party cloud providers' servers (trust boundary is the tool interface).
- The MCP protocol transport (assume TLS, local IPC, or trusted network).
- User's AI agents or models that consume tool output.

Example:
```
# Threat Model for my-read-only-server

**In scope:**
- This server's tools (read-only database queries, audit log viewing, compliance checks).
- Direct deps: psycopg2 (PostgreSQL), requests (HTTPS), python-json-logger.
- Companion servers: microsoft-learn-mcp, github-mcp.
- Logging: all tool invocations, errors, and audit trail.

**Out of scope:**
- PostgreSQL server itself (trust boundary is the SELECT query).
- GitHub API (trust boundary is the tool interface).
- User's Copilot or Claude instance.
```

### 2. Trust Boundaries (10 min)

Draw a data-flow diagram (text or visual) showing:
- User → MCP Client → This Server → Target API (e.g., PostgreSQL, Azure, GitHub).
- Auth path: how credentials flow (e.g., env vars, managed identity, API key).
- Data path: tool input → server logic → target API → result → client.

**Key constraint:** Token/credential must not leave the local process.

Example:
```
User (architect)
  ↓
MCP Client (Claude Desktop)
  ↓ [stdin/stdout or HTTP]
This Server (read-only-query-mcp)
  ├─ DefaultAzureCredential (local to process)
  ├─ Tool: azure_audit_log_query(subscription_id, days)
  └─→ Azure Monitor API (HTTPS + OAuth)
```

### 3. STRIDE-Lite Analysis (30 min)

For each category, list 2–4 threats specific to read-only MCP servers:

#### S: Spoofing / Identity
**Threats:**
- Caller spoofs a subscription or tenant they don't have access to (confused-deputy).
- Tool parameter contains a fake user ID or resource name.

**Mitigations:**
- Validate all caller-supplied IDs (subscription_id, tenant_id, user_id) against the authenticated principal's scope.
- Log validation failures (after token scrubbing).
- Raise ToolException if ID is out of scope.

#### T: Tampering
**Threats:**
- Compromised transitive dependency (e.g., requests library gets backdoored) injects mutation code.
- Vendored queries (e.g., KQL snapshots) are modified post-deployment.
- MCP tool definition is altered to accept dangerous parameters.

**Mitigations:**
- Dependabot scans and dependency-review CI gate.
- Vendored content pinned by commit SHA or file hash.
- Tool schemas validated at startup.
- gitleaks config blocks real GUIDs in non-doc paths.

#### R: Repudiation
**Threats:**
- Tool execution is not logged, enabling unattributed data access.
- Audit trail is incomplete or can be modified.

**Mitigations:**
- Log all tool invocations: timestamp, tool name, parameters, caller (if available), result.
- Write logs to immutable storage (e.g., syslog, cloud audit logs).
- Rotate logs regularly; retain for >90 days.

#### I: Information Disclosure
**Threats:**
- Token leakage via verbose logging, stack traces, or error messages.
- Query results contain sensitive data (e.g., secrets in resource tags).
- Logs written to world-readable files.

**Mitigations:**
- Token-scrub helper on all logging paths (regex-based redaction).
- Log only at INFO level by default; require explicit opt-in for DEBUG (verbose logs leak more).
- Disable stack traces in production; log exception type and line number only.
- Logs written to restricted files (0600 permissions).
- User warned in tool docstrings about query scope (e.g., "may return sensitive data; use responsibly").

#### D: Denial of Service
**Threats:**
- Large query result overwhelms MCP channel or client memory.
- Crafted query causes backend service to throttle or hang.
- Malicious tool input causes server to crash (e.g., infinite loop, OOM).

**Mitigations:**
- Query result size limit; paginate if needed.
- Tool docstrings warn about scope and rate limits.
- Input validation: bounds checks, regex, type validation.
- Timeouts on all external API calls.

#### E: Elevation of Privilege
**Threats:**
- Tool parameter lets caller access a resource or subscription they don't have permission for.
- Mutation method is accidentally exposed (reads only, but writes via side effect).

**Mitigations:**
- ADR/decision document: read-only enforcement strategy (static analysis, convention, runtime guard).
- CI gate: static analysis check that blocks imports of mutation methods.
- No long-running operations (`Begin*` methods) exposed as tools.

### 4. Supply Chain Risk Matrix (20 min)

Create a table for each category:

#### Direct Dependencies

| Package | Version | Latest | Risk Level | Notes | Mitigation |
|---------|---------|--------|-----------|-------|-----------|
| `X` | A.B.C | A.B.D | Low | Official, actively maintained | Dependabot |
| `Y` | X.Y.Z | X.Y.W | Medium | Community, last update 2 months ago | Pin version, quarterly review |

**Risk Levels:**
- **Low:** Official (Microsoft, HashiCorp, GitHub), actively maintained, no known CVEs.
- **Medium:** Community, mature (>1 year old, >100 stars), occasional updates.
- **High:** Unmaintained (>1 year without update), unknown provenance, known CVEs, or single-person maintainer.

#### Transitive Dependencies

List the high-value targets in your transitive tree (e.g., cryptography, requests, PyJWT). Mitigation: Dependabot + dependency-review CI gate.

#### Vendored Content

| Source | Pinning | Integrity Check | Reviewed By | Cadence |
|--------|---------|-----------------|-------------|---------|
| `alz-checklist-queries` | Commit SHA | SHA-256 hash in manifest | Sage | On-demand |

#### Companion Servers

| Server | Source | Trust | Version Pin | Recommendation |
|--------|--------|-------|------------|---|
| `azure-mcp` | Microsoft (official) | High | Pin major.minor | Auto-update quarterly |
| `mermaid-mcp` | npm (community) | Medium | Pin major.minor | Manual quarterly review |

### 5. Mitigations Checklist (5 min)

Create a list of controls and their implementation status:

- [ ] Token-scrub helper on all logging.
- [ ] Caller scope validation for all ID parameters.
- [ ] Input validation (bounds, regex, type checks).
- [ ] Dependabot scans + dependency-review CI gate.
- [ ] Static analysis gate (read-only enforcement, if applicable).
- [ ] gitleaks config (blocks secrets).
- [ ] Vendored content pinned by SHA.
- [ ] Tool schemas validated at startup.
- [ ] Log rotation and retention policy.
- [ ] Timeout on external API calls.

## Example Output (mcp-server-azure-architect)

See: [.squad/decisions/inbox/sentinel-threat-model-outline.md](../../decisions/inbox/sentinel-threat-model-outline.md)

This skeleton documents the full threat model for the Azure architect MCP server, including STRIDE-lite, supply chain matrix, and mitigations.

## Related Skills

- **ADR-003 Template:** Read-only enforcement strategy (decision options, recommended approach, consequences).
- **CI Gates Checklist:** Required status checks for read-only servers (dependency-review, gitleaks, static-analysis, mypy, pytest).
- **Token-Scrub Helper:** Implementation of the logging gate (regex-based redaction for tokens, secrets).

## Maintenance

Update this skill if:
- A new STRIDE category relevant to MCP emerges (e.g., MCP protocol transport weaknesses).
- A supply chain attack occurs in a commonly-used dependency (lessons learned).
- A new threat is discovered in Azure, AWS, or other cloud platforms.

Last updated: 2026-04-22
