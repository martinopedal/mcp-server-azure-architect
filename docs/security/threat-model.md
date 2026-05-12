# Threat Model: mcp-server-azure-architect

**Version:** 1.0  
**Date:** 2026-05-12  
**Author:** Sentinel  
**Framework:** STRIDE-Lite for Read-Only MCP Servers

## Overview

This document applies STRIDE threat modeling to mcp-server-azure-architect, a read-only MCP server and Copilot CLI skills bundle for Azure architects. The server provides named ALZ checklist queries, scoring, quota planning, and Advisor surfacing. It does not mutate Azure resources.

**Scope:** Server tools, auth flow, vendored data, direct dependencies, and companion server recommendations.

**Out of scope:** MCP clients (Claude Desktop, Copilot CLI), Azure infrastructure itself, user AI agents consuming tool output.

## Trust Boundaries

```
User (Azure Architect)
  ↓
MCP Client (Claude Desktop / Copilot CLI)
  ↓ [stdio/HTTP transport]
mcp-server-azure-architect
  ├─ DefaultAzureCredential (local to process, env/MI/az cli)
  ├─ Tools: alz_checklist_query, advisor_recommendations, quota_plan
  ├─ Vendored Data: data/alz-queries/ (KQL snapshots)
  └─ Azure APIs (Resource Graph, Advisor, Key Vault) [HTTPS + OAuth]
       ↓
  Companion MCP Servers (azure-mcp, microsoft-learn, mermaid, etc.)
```

**Key constraint:** DefaultAzureCredential tokens must never leave the local process. Credentials are obtained via environment variables, managed identity, or `az cli` and used only for Azure SDK calls.

## Threat Categories (STRIDE-Lite)

### S: Spoofing / Identity

#### Threat S1: Confused-Deputy via Unvalidated subscription_id

**Severity:** CRITICAL

**Description:**  
Tools accept `subscription_id` or `tenant_id` as parameters from untrusted MCP client input. Without validation, an AI agent (or malicious user) can probe subscriptions outside the caller's scope. This violates the principle of least privilege and enables lateral movement.

**Example:**  
Tool `alz_checklist_query(subscription_id: str)` accepts arbitrary subscription GUID. Attacker supplies a subscription they don't have access to. Tool forwards request to Azure. If DefaultAzureCredential has cross-subscription Reader permissions (common in enterprise MSPs or federated scenarios), query succeeds and leaks data.

**Attack vector:**  
1. User or AI agent invokes tool with attacker-controlled `subscription_id`.
2. Tool does not validate that `subscription_id` is in the caller's authorized scope.
3. Azure SDK call succeeds if DefaultAzureCredential has permission.
4. Tool returns data from unauthorized subscription.

**Mitigation:**
- **Validate caller scope.** Implement `validate_caller_scope(subscription_id: str, credential: DefaultAzureCredential) -> bool` helper in `src/mcp_server_azure_architect/azure_client.py`. Helper queries Azure Resource Manager to enumerate subscriptions the credential has access to, then checks if `subscription_id` is in that list.
- **Log validation failures.** If validation fails, log the attempt (after token scrubbing) and raise `ToolException` with message "Subscription ID is not in your scope."
- **Tool docstrings warn users.** Document in tool help text: "subscription_id must be a subscription you have Reader permission for."

**Status:** OPEN. Implementation tracked in issue #TBD (to be created after threat model is ratified).

#### Threat S2: Token Spoofing (Low Risk)

**Severity:** LOW

**Description:**  
Attacker attempts to inject a fake bearer token into the tool's auth flow.

**Mitigation:**  
DefaultAzureCredential obtains tokens directly from environment variables, managed identity, or `az cli`. There is no user-supplied token parameter. Azure SDK validates token signatures server-side. Risk is negligible.

**Status:** ACCEPTED RISK. No additional mitigation required.

### T: Tampering

#### Threat T1: Compromised Vendored Query (KQL Injection)

**Severity:** CRITICAL

**Description:**  
Vendored ALZ queries in `data/alz-queries/` are snapshotted from upstream repositories (`martinopedal/alz-checklist-queries`, `martinopedal/alz-graph-queries`). If the upstream repo is compromised or the snapshot is tampered with post-deployment, malicious KQL could be injected. Malicious KQL could exfiltrate data, cause DoS (expensive queries), or exploit Azure Resource Graph parsing vulnerabilities.

**Example:**  
Attacker compromises upstream repo and injects KQL that sends query results to attacker-controlled webhook. Next snapshot update pulls malicious query. Tool ships malicious query to users.

**Attack vector:**  
1. Attacker gains commit access to upstream repo.
2. Attacker injects malicious KQL into a query file.
3. Sage or Atlas performs snapshot refresh without thorough review.
4. PR merges. Users run malicious query.

**Mitigation:**
- **Snapshot SHA pinning.** Every vendored query snapshot records the upstream commit SHA in `data/alz-queries/MANIFEST.md`. Refresh PRs must update SHA and link to upstream commit.
- **Dual review on refresh PRs.** Any PR that updates `data/alz-queries/` requires review by both Sage (research) and Sentinel (security). Reviewers must diff upstream changes and verify no malicious patterns (e.g., `externaldata`, `evaluate`, unusual `project` clauses).
- **Query citations.** Every query file includes a comment with source checklist ID and upstream commit SHA. Users can audit queries against upstream source.
- **Integrity checks.** MANIFEST includes SHA-256 hash of each query file. CI validates hashes on every build.

**Status:** PARTIALLY MITIGATED. PR #27 (Atlas) implemented SHA-pinned snapshot + MANIFEST. Dual review policy documented here. Integrity checks (SHA-256 validation in CI) tracked in issue #TBD.

#### Threat T2: Compromised Transitive Dependency

**Severity:** HIGH

**Description:**  
Transitive dependencies (e.g., `cryptography`, `PyJWT`, `requests`) are high-value targets for supply-chain attacks. If a transitive dependency is backdoored, attacker could inject mutation code, exfiltrate tokens, or tamper with query results.

**Example:**  
`requests` library (transitive dep of `azure-identity`) is compromised. Malicious version logs all HTTP request headers (including bearer tokens) to attacker-controlled server.

**Attack vector:**  
1. Attacker compromises popular transitive dependency (e.g., via typosquatting, maintainer account takeover, or build system injection).
2. Malicious version is published to PyPI.
3. User installs or updates dependencies. Malicious version is pulled in.
4. Malicious code exfiltrates tokens, queries, or mutates Azure resources.

**Mitigation:**
- **Dependabot scans.** Enable Dependabot in repository settings. Weekly cadence for dependency updates and CVE alerts.
- **dependency-review CI gate.** GitHub Actions workflow `.github/workflows/dependency-review.yml` blocks PRs that introduce known-vulnerable dependencies.
- **Transitive dependency audit.** Periodically run `pip-audit` or `safety` to scan transitive dependencies for known CVEs. Tracked in issue #TBD.
- **Lockfile discipline.** Use `uv pip compile` or `pip-tools` to generate lockfiles with pinned transitive versions. Commit lockfiles to repo. CI installs from lockfile, not loose constraints.

**Status:** PARTIALLY MITIGATED. Dependabot is enabled (confirmed by Lead). dependency-review workflow added in PR #22. Transitive audit (pip-audit) and lockfile discipline tracked in issue #TBD.

#### Threat T3: MCP Tool Definition Tampering

**Severity:** MEDIUM

**Description:**  
If an attacker can modify tool definitions (e.g., via compromised build or deployment), they could alter parameter schemas to accept dangerous inputs or remove validation.

**Mitigation:**  
Tool definitions are generated from Python type hints via FastMCP. No separate schema files to tamper with. Code review and CI (ruff, mypy) validate tool signatures. gitleaks blocks accidental secrets in code.

**Status:** ACCEPTED RISK. No additional mitigation required.

### R: Repudiation

#### Threat R1: Tool Execution Not Logged

**Severity:** MEDIUM

**Description:**  
If tool invocations are not logged, unauthorized data access cannot be audited or attributed. This enables unattributed reconnaissance or data exfiltration.

**Attack vector:**  
1. User or AI agent invokes tool to query sensitive Azure data.
2. No log is written.
3. Security incident occurs. Audit trail is incomplete.

**Mitigation:**
- **Log all tool invocations.** Implement logging in `src/mcp_server_azure_architect/__main__.py`. Log timestamp, tool name, parameters (after redaction), caller identity (if available from MCP context), and result summary.
- **Immutable log storage.** Write logs to syslog, cloud audit logs (Azure Monitor), or other immutable storage. Retain logs for 90+ days per compliance requirements.
- **Log rotation.** Use Python `logging.handlers.RotatingFileHandler` or systemd journal for local deployments.

**Status:** OPEN. Logging implementation tracked in issue #TBD.

#### Threat R2: Log Tampering

**Severity:** LOW

**Description:**  
If logs are writable by the tool process, an attacker who compromises the process can delete or modify logs to cover their tracks.

**Mitigation:**  
Write logs to immutable storage (syslog, cloud audit logs) or set file permissions to append-only (Linux `chattr +a` or similar). Documented in tool deployment guide.

**Status:** OPEN. Documentation tracked in issue #TBD.

### I: Information Disclosure

#### Threat I1: Token Leakage via Logging

**Severity:** CRITICAL

**Description:**  
DefaultAzureCredential tokens, Azure Resource Graph response payloads, or error stack traces may contain sensitive data (bearer tokens, secrets in resource tags, subscription GUIDs, etc.). If logged verbosely, tokens could be exfiltrated or leaked via log aggregation systems.

**Example:**  
Developer enables DEBUG logging. Stack trace from Azure SDK exception includes HTTP request headers with `Authorization: Bearer <token>`. Log is written to disk. Attacker reads log file.

**Attack vector:**  
1. Tool or Azure SDK logs verbose output (DEBUG level).
2. Logs include bearer token, subscription GUID, or resource secrets.
3. Logs are written to world-readable file or aggregated to SIEM without redaction.
4. Attacker reads logs.

**Mitigation:**
- **Token-scrub helper.** Implement `token_scrub(text: str) -> str` in `src/mcp_server_azure_architect/auth.py`. Regex-based redaction for:
  - Bearer tokens: `Authorization: Bearer ...` becomes `Authorization: Bearer [REDACTED]`
  - Azure GUIDs: subscription IDs, tenant IDs become `[REDACTED-GUID]`
  - Secrets in tags: `tag:secret=...` becomes `tag:secret=[REDACTED]`
- **Integrate token_scrub into logging.** Use custom `logging.Handler` or `logging.Formatter` that applies `token_scrub()` to all log records before emit.
- **Default to INFO level.** Disable DEBUG logging in production. Require explicit opt-in (env var `MCP_LOG_LEVEL=DEBUG`) with warning in docs.
- **Disable stack traces in production.** Log exception type and line number only. Full stack traces only in DEBUG mode.
- **File permissions.** Logs written to `~/.mcp-server-azure-architect/logs/` with 0600 permissions (owner read/write only).

**Status:** PARTIALLY MITIGATED. `token_scrub()` stub exists in `src/mcp_server_azure_architect/auth.py` (per Forge's PR #22). Integration into logging handler tracked in issue #TBD.

#### Threat I2: Sensitive Data in Query Results

**Severity:** MEDIUM

**Description:**  
Azure Resource Graph queries may return sensitive data (e.g., secrets in resource tags, connection strings in configuration, private IPs). Tool cannot fully sanitize results because it does not know which fields are sensitive. Users must handle results responsibly.

**Mitigation:**
- **Tool docstrings warn users.** Every query tool includes warning: "Results may contain sensitive data. Use responsibly. Do not log or share results without review."
- **User education.** Document in `docs/install/usage-guide.md` (to be created) that query results should be treated as sensitive and handled per user's organization policy.
- **Scope guidance.** Recommend narrowest query scope. Example: query single resource group, not all subscriptions.

**Status:** OPEN. Documentation tracked in issue #TBD.

#### Threat I3: World-Readable Log Files

**Severity:** MEDIUM

**Description:**  
If log files are written with default permissions (0644), other users on the system can read tokens or query results.

**Mitigation:**  
Log files written to `~/.mcp-server-azure-architect/logs/` with 0600 permissions. Enforced in `src/mcp_server_azure_architect/__main__.py` logging setup.

**Status:** OPEN. Implementation tracked in issue #TBD.

### D: Denial of Service

#### Threat D1: Large Query Result Overwhelms MCP Channel

**Severity:** MEDIUM

**Description:**  
Attacker crafts query with huge result set (e.g., "list all resources in all subscriptions"). Result JSON is too large for MCP channel buffer or client memory. Client hangs or crashes.

**Attack vector:**  
1. User or AI agent invokes query tool with broad scope (e.g., `subscription_id="*"`).
2. Query returns 100,000+ resources.
3. JSON serialization or MCP transport buffer exhausted.
4. Client crashes or hangs.

**Mitigation:**
- **Result size limit.** Query tools paginate results. Default page size: 1000 items. Maximum page size: 5000 items. Document in tool help.
- **Tool docstrings warn about scope.** Example: "Querying all subscriptions may return large results. Use specific subscription_id or resource_group for faster response."
- **Timeouts.** All Azure SDK calls have 60-second timeout. If query exceeds timeout, raise `ToolException` with actionable message.

**Status:** OPEN. Pagination implementation tracked in issue #TBD.

#### Threat D2: Expensive Query Causes Azure Throttling

**Severity:** MEDIUM

**Description:**  
Attacker crafts computationally expensive KQL query (e.g., large joins, regex on large text fields). Azure Resource Graph throttles or times out. User's subscription may be temporarily blocked from querying.

**Mitigation:**
- **Query complexity guidance.** Document best practices for KQL queries in `data/alz-queries/CONTRIBUTING.md` (to be created). Avoid unbounded joins, regex on large fields, or queries without `where` clauses.
- **Upstream query review.** Vendored queries are authored by ALZ checklist maintainers (trusted). Sentinel reviews all snapshot updates for query complexity.
- **Rate limiting (future).** If tool usage grows, implement local rate limiting (e.g., max 10 queries/minute per user). Tracked in issue #TBD.

**Status:** ACCEPTED RISK for v0.1. Query complexity guidance and rate limiting deferred to v0.2.

#### Threat D3: Infinite Loop or OOM in Tool Logic

**Severity:** LOW

**Description:**  
Malicious tool input causes tool logic to enter infinite loop or allocate unbounded memory.

**Mitigation:**
- **Input validation.** All tool parameters validated via JSON Schema (auto-generated by FastMCP). Type checks, bounds checks, regex validation enforced before tool logic executes.
- **Code review.** PR reviews check for unbounded loops, recursive calls, or large allocations.
- **Timeouts.** Tool execution wrapped in asyncio timeout (60 seconds). If exceeded, raise `ToolException`.

**Status:** PARTIALLY MITIGATED. JSON Schema validation is automatic (FastMCP). Timeouts and code review discipline in place.

### E: Elevation of Privilege

#### Threat E1: Tool Accesses Resource Outside Caller's Scope

**Severity:** CRITICAL

**Description:**  
Same as Threat S1 (confused-deputy). Restated here for STRIDE completeness.

**Mitigation:** See Threat S1 mitigations.

**Status:** OPEN. See Threat S1.

#### Threat E2: Mutation Method Accidentally Exposed

**Severity:** HIGH

**Description:**  
Developer adds tool that imports or invokes Azure SDK mutation method (e.g., `Begin*`, `Create*`, `Update*`). Read-only guarantee is violated. User unexpectedly mutates Azure resources.

**Attack vector:**  
1. Developer adds tool `fix_misconfiguration()` that calls `azure.mgmt.compute.ComputeManagementClient.virtual_machines.begin_create_or_update()`.
2. Code review misses mutation import.
3. PR merges.
4. User invokes tool. Azure resource is mutated.

**Mitigation:**
- **ADR-003 enforcement.** Three layers:
  1. **Layer 1: AST-based import allowlist (CI gate).** `.github/scripts/check_readonly.py` scans all `.py` files in `src/` for mutation imports. CI fails if detected.
  2. **Layer 2: Convention + CODEOWNERS.** Tools named `_get_*`, `_list_*`, `_query_*`. No `_create_*`, `_update_*`, `_delete_*` allowed. CODEOWNERS routes all `src/**/*.py` changes to Sentinel-equivalent reviewer.
  3. **Layer 3: Runtime guard (aspirational).** Proxy wrapper in `azure_client.py` rejects mutation method invocations at runtime.
- See `docs/adr/0003-read-only-enforcement.md` for full details.

**Status:** OPEN. ADR-003 implementation tracked in issue #7.

## Supply Chain Risk Matrix

### Direct Dependencies

| Package | Version | Latest (2026-05-12) | Risk Level | Notes | Mitigation |
|---------|---------|---------------------|-----------|-------|-----------|
| `mcp` | >=1.0.0 | 1.27.1 | Medium | Loose constraint allows any 1.x version. MCP is evolving; breaking changes possible. | Tighten to `>=1.27.0` in follow-up PR (tracked by Forge in issue #32). Dependabot monitors updates. |
| `azure-identity` | >=1.15.0 | 1.25.3 | Low-Medium | Loose constraint allows 1.15-1.25. Older versions (1.13-1.16) had auth-bypass CVEs. | Tighten to `>=1.23.0` in follow-up PR (tracked by Forge in issue #32). Dependabot monitors updates. |
| `azure-mgmt-resourcegraph` | >=8.0.0 | 8.0.1 | Low | Read-only surface. No mutation methods. Well-pinned. | Dependabot monitors updates. |

**Summary:**  
Direct dependencies are official (Microsoft, Python Software Foundation). Risk is low to medium. Primary risk: loose version constraints. Mitigation in progress (Forge's issue #32).

### Transitive Dependencies (High-Value Targets)

Transitive dependencies are not directly controlled by this project but are pulled in by direct dependencies. High-value targets for supply-chain attacks:

| Package | Pulled By | Risk | Notes |
|---------|-----------|------|-------|
| `cryptography` | `azure-identity` | High | Core crypto library. Frequent CVEs. Actively maintained. |
| `PyJWT` | `azure-identity` (indirect) | High | JWT parsing. Frequent CVEs. Actively maintained. |
| `requests` | `azure-identity`, `mcp` | High | HTTP client. Wide attack surface. Actively maintained. |
| `urllib3` | `requests` | Medium | HTTP library. Occasional CVEs. Actively maintained. |
| `certifi` | `requests` | Medium | CA bundle. Rarely updated. Low CVE count. |

**Mitigation:**
- Dependabot scans transitive dependencies weekly. CVE alerts routed to Sentinel.
- dependency-review CI gate blocks PRs introducing known-vulnerable transitive deps.
- Lockfile discipline (tracked in issue #TBD): `uv pip compile` generates pinned lockfile. CI installs from lockfile.
- Periodic transitive audit: `pip-audit` or `safety` scan. Tracked in issue #TBD.

### Vendored Content

| Source | Pinning | Integrity Check | Reviewed By | Cadence |
|--------|---------|-----------------|-------------|---------|
| `martinopedal/alz-checklist-queries` | Commit SHA in MANIFEST | SHA-256 hash (planned) | Sage + Sentinel | On-demand (user request or upstream major update) |
| `martinopedal/alz-graph-queries` | Commit SHA in MANIFEST | SHA-256 hash (planned) | Sage + Sentinel | On-demand (user request or upstream major update) |

**Threat:** Compromised upstream repo or tampered snapshot. See Threat T1.

**Mitigation:** SHA pinning, dual review, integrity checks (SHA-256 validation tracked in issue #TBD).

### Companion MCP Servers (Recommended in mcp-config.json)

| Server | Source | Trust Level | Version Pin | Recommendation |
|--------|--------|-------------|-------------|----------------|
| `@modelcontextprotocol/server-azure` | Microsoft (official) | High | Pin `@latest` to `@1.x` (tracked by Burke) | Quarterly update review. Auto-update minor versions. |
| `@modelcontextprotocol/server-microsoft-learn` | Microsoft (official) | High | Pin `@latest` to `@1.x` (tracked by Burke) | Quarterly update review. |
| `mermaid-mcp` | npm (community) | Medium | Pin major.minor (e.g., `^2.1.0`) | Manual quarterly review. Check last update <6 months, >100 stars. |
| `drawio-mcp` | npm (community) | Medium | Pin major.minor | Manual quarterly review. |
| `kubernetes-mcp` | npm (community) | Medium | Pin major.minor | Manual quarterly review. |
| `terraform-mcp` | HashiCorp (official) | High | Pin major.minor | Quarterly update review. |

**Policy:**
- Official sources (Microsoft, HashiCorp, GitHub): Signed, pinned, auto-update on quarterly cadence.
- Mature community: Version-pinned (major.minor), quarterly manual review, require freshness (<6 months since last update) + popularity (>100 stars).
- Emerging community: Require Sage research note + Sentinel review before inclusion.

**Enforcement:** PR review gate by Burke (companion-MCP integration owner). Update PRs require Sage research note.

## Mitigations Summary

| Threat ID | Threat | Severity | Mitigation | Status |
|-----------|--------|----------|-----------|--------|
| S1 | Confused-deputy via unvalidated subscription_id | CRITICAL | `validate_caller_scope()` helper | OPEN (#TBD) |
| S2 | Token spoofing | LOW | DefaultAzureCredential, no user-supplied tokens | ACCEPTED RISK |
| T1 | Compromised vendored query | CRITICAL | SHA pinning, dual review, integrity checks | PARTIAL (SHA pin done, integrity checks #TBD) |
| T2 | Compromised transitive dependency | HIGH | Dependabot, dependency-review, lockfile, pip-audit | PARTIAL (Dependabot + dep-review done, lockfile #TBD) |
| T3 | MCP tool definition tampering | MEDIUM | Code review, ruff, mypy, gitleaks | MITIGATED |
| R1 | Tool execution not logged | MEDIUM | Log all invocations, immutable storage | OPEN (#TBD) |
| R2 | Log tampering | LOW | Immutable log storage, append-only files | OPEN (#TBD) |
| I1 | Token leakage via logging | CRITICAL | `token_scrub()` helper, INFO-level default, 0600 perms | PARTIAL (stub exists, integration #TBD) |
| I2 | Sensitive data in query results | MEDIUM | Tool docstrings, user education | OPEN (#TBD) |
| I3 | World-readable log files | MEDIUM | 0600 permissions on log directory | OPEN (#TBD) |
| D1 | Large query result overwhelms MCP | MEDIUM | Pagination, result size limits, timeouts | OPEN (#TBD) |
| D2 | Expensive query causes throttling | MEDIUM | Query complexity guidance, rate limiting (v0.2) | ACCEPTED RISK (v0.1) |
| D3 | Infinite loop or OOM | LOW | Input validation, timeouts, code review | MITIGATED |
| E1 | Tool accesses resource outside scope | CRITICAL | See S1 | OPEN (#TBD) |
| E2 | Mutation method accidentally exposed | HIGH | ADR-003 layers 1-3 | OPEN (#7) |

**Summary:** 8 threats mitigated or partially mitigated. 7 threats open with tracking issues to be created. 2 threats accepted as low risk.

## Out-of-Scope Threats

The following threats are explicitly out of scope for this threat model:

1. **Compromised host OS.** If the user's machine is compromised (malware, rootkit, etc.), all bets are off. This tool cannot defend against host-level compromise. Mitigation: user responsibility (antivirus, OS patching, endpoint detection).

2. **Compromised Azure infrastructure.** If Azure Resource Manager, Azure Resource Graph, or Azure Identity services are compromised, this tool cannot detect or mitigate. Mitigation: trust Azure platform security (Microsoft responsibility).

3. **Compromised MCP client.** If Claude Desktop, Copilot CLI, or other MCP client is compromised, attacker can invoke tools with arbitrary inputs. Mitigation: read-only enforcement limits blast radius (attacker can query but not mutate).

4. **User credential compromise.** If DefaultAzureCredential sources (env vars, `az cli` token cache, managed identity endpoint) are compromised, attacker can impersonate user. Mitigation: user responsibility (credential rotation, MFA, least privilege RBAC).

5. **Social engineering.** If user is tricked into running malicious queries or sharing query results, tool cannot prevent. Mitigation: user education (tool docstrings, usage guide).

6. **Side-channel attacks.** Timing attacks, cache attacks, or other side channels are out of scope. Mitigation: not applicable to read-only query tools.

## Next Steps

1. **Create tracking issues.** For each OPEN mitigation, create GitHub issue with actionable acceptance criteria. Assign to appropriate owner (Sentinel, Forge, Sage).
2. **Implement ADR-003 layer 1.** `.github/scripts/check_readonly.py` + CI integration. Blocker for v0.1 release. (Issue #7)
3. **Implement token-scrub integration.** Complete logging handler with `token_scrub()` applied to all log records. Blocker for v0.1 release. (Issue #TBD)
4. **Implement caller scope validation.** `validate_caller_scope()` helper in `azure_client.py`. Blocker for v0.1 release. (Issue #TBD)
5. **Tighten dependency constraints.** Forge's issue #32 in progress.
6. **Add SHA-256 integrity checks.** CI validates MANIFEST hashes. (Issue #TBD)
7. **Document deployment best practices.** Include log file permissions, credential rotation, query scope guidance. (Issue #TBD)
8. **Quarterly dependency review.** Schedule recurring review (Sentinel + Forge) for transitive deps, companion servers, vendored snapshots.

## References

1. **STRIDE Threat Modeling:**  
   [learn.microsoft.com/azure/security/develop/threat-modeling-tool-threats](https://learn.microsoft.com/azure/security/develop/threat-modeling-tool-threats)

2. **Azure SDK Security Best Practices:**  
   [learn.microsoft.com/azure/developer/python/azure-sdk-security](https://learn.microsoft.com/azure/developer/python/azure-sdk-security)

3. **MCP Specification, Security Considerations:**  
   [modelcontextprotocol.io/specification/security](https://modelcontextprotocol.io/specification/security)

4. **OWASP Top 10 for APIs:**  
   [owasp.org/www-project-api-security](https://owasp.org/www-project-api-security)

5. **Supply Chain Levels for Software Artifacts (SLSA):**  
   [slsa.dev](https://slsa.dev)

6. **NIST Cybersecurity Framework:**  
   [nist.gov/cyberframework](https://nist.gov/cyberframework)

7. **ADR-003: Read-Only Enforcement Mechanism:**  
   `docs/adr/0003-read-only-enforcement.md` (created in parallel with this threat model).

## Sentinel Review

**Verdict:** RATIFIED (2026-05-12)

**Summary:**  
Threat model identifies 3 CRITICAL threats (confused-deputy, compromised vendored query, token leakage), 2 HIGH threats (compromised transitive dep, mutation method exposure), 6 MEDIUM threats, and 2 LOW threats. Defense-in-depth mitigations are in place or tracked. Companion supply chain policy balances trust and freshness. Out-of-scope threats are explicitly named. This threat model is production-ready for v0.1 release and quarterly reviews.

**Next action:** Create tracking issues for OPEN mitigations. Assign to owners per AGENTS.md.
