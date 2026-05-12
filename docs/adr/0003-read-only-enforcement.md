# ADR-003: Read-Only Enforcement Mechanism

## Status

Accepted (2026-05-12, Sentinel)

## Context

mcp-server-azure-architect is a read-only tool for Azure architects. It fills the gap above raw `azure-mcp` by providing named ALZ checklist queries, scoring, quota planning, and Advisor surfacing. The server enables design, gap analysis, and compliance review, not mutation.

### Why Read-Only Matters

1. **Safety.** Azure architects operate in production environments. A read-only tool cannot inadvertently delete resources, update configurations, or trigger cascading changes. This reduces blast radius and enables architects to confidently explore Azure state without risk.

2. **Audit story.** Read-only operations are easier to audit and comply with separation-of-duty principles. Architects review and design. Engineers execute changes. This tool respects that boundary.

3. **Trust.** AI-driven tools that can mutate cloud infrastructure require rigorous guardrails, testing, and approval workflows. Read-only tools sidestep this complexity. Users trust the tool because its scope is constrained.

4. **Project charter.** AGENTS.md establishes read-only as a non-negotiable: "Server, skills, and examples must be read-only against Azure. No mutation tools, ever." This ADR ratifies the enforcement mechanism that backs that commitment.

### What "Read-Only" Means

For this project, read-only means:

- **No Azure SDK mutation methods.** Tools must not import, instantiate, or invoke `Begin*`, `Create*`, `Update*`, `Delete*`, or `Set*` methods from `azure.mgmt.*`, `azure.storage.*`, or similar SDKs.
- **No long-running operations (LROs).** Azure SDK LROs (via `Begin*` methods) are inherently mutation-capable. They are disallowed even if ostensibly read-only (e.g., long-running exports).
- **No credential writes.** DefaultAzureCredential tokens must never be logged, persisted, or transmitted outside the local process.
- **Resource Graph and read-only APIs only.** Tools may query Azure Resource Graph, Key Vault (read secrets the caller has permission for), Storage (read blobs the caller has permission for), and similar read APIs. Write APIs are out of scope.

### Threat Model Context

ADR-003 enforcement reduces the attack surface for STRIDE threats, specifically:

- **Tampering (T):** Even if a dependency is compromised, mutation methods are blocked at multiple layers.
- **Elevation of Privilege (E):** Tools cannot escalate beyond read permissions granted to DefaultAzureCredential.

See `docs/security/threat-model.md` for full STRIDE-lite analysis.

## Options Considered

### Option A: Trust and Code Review Only

**Approach:** Rely on PR review and naming conventions. No automated enforcement.

**Pros:**
- Zero implementation cost.
- Flexible: reviewers can make judgment calls.

**Cons:**
- Does not scale. As the tool grows, subtle mutation imports can slip through.
- Human error: reviewers may not catch dynamic dispatch, transitive imports, or indirect mutation methods.
- No CI gate: no automated feedback for contributors.

**Verdict:** Rejected. Trust-only does not meet the project's safety bar.

### Option B: Static Analysis (AST-Based Import Allowlist)

**Approach:** CI script walks Python AST, scans imports in `src/mcp_server_azure_architect/`, rejects any import of mutation-capable SDK modules or methods.

**Pros:**
- Catches 95% of mutation imports automatically.
- Fast: AST walk is O(n) in source lines, runs in <1 second.
- No false positives if allowlist is well-tuned.
- Transparent: contributors see CI failure with actionable error message.

**Cons:**
- Requires maintenance: Azure SDK evolves, allowlist must track new packages.
- Misses dynamic dispatch: `getattr(client, "create_resource")()` bypasses static analysis.
- Misses imports in test fixtures or utility scripts outside `src/`.

**Verdict:** Strong candidate. Forms layer 1 of defense-in-depth.

### Option C: Runtime Guard (Proxy Wrapper for Azure Clients)

**Approach:** Wrap all Azure SDK clients in a proxy that intercepts method calls. Reject invocations of `create*`, `update*`, `delete*`, `begin*`, or `set*` methods at runtime.

**Pros:**
- Catches dynamic dispatch and reflection-based calls.
- Defense-in-depth: works even if static analysis is bypassed.
- Can log attempted mutation calls for auditing.

**Cons:**
- High maintenance: proxy must mirror Azure SDK client interfaces.
- Performance overhead: method interception adds latency.
- Complexity: hard to implement correctly for async methods, context managers, paginators.
- May break if Azure SDK changes client structure.

**Verdict:** Aspirational. Useful as layer 3 in defense-in-depth, but implementation cost is high relative to risk.

### Option D: RBAC Scope Restriction at Azure Level

**Approach:** Rely on Azure RBAC. Run the tool with a credential scoped to Reader role only.

**Pros:**
- Enforced by Azure platform, not by tool code.
- No implementation cost for this project.

**Cons:**
- Does not prevent the tool from calling write methods. It only prevents those methods from succeeding.
- Tool author can still write mutation logic. The tool is not provably read-only; it is merely denied permission at runtime.
- Credential misconfiguration (e.g., Contributor role assigned by accident) breaks the guarantee.
- Does not address the project's "read-only by design" charter.

**Verdict:** Rejected. RBAC is a safety net, not a substitute for read-only enforcement in code.

### Option E: Combination (Static Analysis + Convention + Runtime Guard)

**Approach:** Defense-in-depth with three layers:

1. **Layer 1: AST-based import allowlist (CI gate).** Immediate. Blocks mutation imports at CI time.
2. **Layer 2: Convention + code review.** Tools named `_get_*`, `_list_*`, `_query_*`. No `_create_*`, `_update_*`, `_delete_*` allowed. CODEOWNERS routing ensures Sentinel-equivalent review on any `src/mcp_server_azure_architect/**/*.py` change.
3. **Layer 3: Runtime guard (aspirational).** Proxy wrapper in `src/mcp_server_azure_architect/azure_client.py` that rejects mutation method invocations at the call site.

**Pros:**
- Defense-in-depth: multiple independent layers.
- Immediate value: layer 1 (AST check) is implementable in <1 day.
- Layers 2 and 3 add safety incrementally as the codebase grows.
- Transparent: CI failures guide contributors toward read-only patterns.

**Cons:**
- Higher maintenance burden: three layers to keep synchronized.
- Layer 3 (runtime guard) is complex and deferred to v0.2+.

**Verdict:** Recommended. Best balance of safety, cost, and transparency.

## Decision

**Choose Option E: Combination (Static Analysis + Convention + Runtime Guard).**

### Layer 1: AST-Based Import Allowlist (Immediate)

CI script at `.github/scripts/check_readonly.py` scans `src/mcp_server_azure_architect/` for Python imports. The script rejects any import of mutation-capable Azure SDK modules or methods.

**Deny list (indicative, to be refined during implementation):**
- `azure.mgmt.*.operations.*Client.begin_*` (all LROs)
- `azure.mgmt.*.operations.*Client.create_or_update`
- `azure.mgmt.*.operations.*Client.delete`
- `azure.storage.blob.BlobClient.upload_blob`
- `azure.storage.blob.BlobClient.delete_blob`
- `azure.keyvault.secrets.SecretClient.set_secret`
- `azure.keyvault.secrets.SecretClient.delete_secret`

**Allow list (indicative, to be refined during implementation):**
- `azure.identity.DefaultAzureCredential` (auth only, no mutations)
- `azure.mgmt.resourcegraph.ResourceGraphClient.resources` (read-only query)
- `azure.mgmt.advisor.AdvisorManagementClient.recommendations.list` (read-only)
- `azure.storage.blob.BlobClient.download_blob` (read-only)
- `azure.keyvault.secrets.SecretClient.get_secret` (read-only)

**Implementation:**
- Script uses Python `ast` module to parse all `.py` files in `src/`.
- For each `import` or `from ... import` statement, check imported names against deny list.
- Exit with status 1 and print actionable error if mutation import detected.
- Suppressions via `# noqa: sentinel-readonly` in exceptional cases (to be reviewed by Sentinel).

**CI integration:**
- New workflow job in `.github/workflows/ci.yml`: `readonly-check`.
- Runs on all PRs that touch `src/**/*.py`.
- Blocks merge if check fails.

### Layer 2: Convention + Code Review (Immediate)

**Naming convention:**
- Read-only tools: `_get_*`, `_list_*`, `_query_*`, `_describe_*`, `_fetch_*`.
- Mutation tools (disallowed): `_create_*`, `_update_*`, `_delete_*`, `_set_*`, `_begin_*`.

**CODEOWNERS routing:**
- Add `.github/CODEOWNERS` entry: `src/mcp_server_azure_architect/**/*.py @martinopedal` (or Sentinel-equivalent reviewer).
- Ensures any tool addition or modification is reviewed by someone with read-only enforcement context.

### Layer 3: Runtime Guard (Aspirational, Tracked as Follow-Up Issue)

**Approach:**
- Create `src/mcp_server_azure_architect/azure_client.py` with a `ReadOnlyClientProxy` class.
- Wrap all Azure SDK clients (`ResourceGraphClient`, `AdvisorManagementClient`, etc.) in the proxy.
- Proxy intercepts method calls via `__getattr__` or similar.
- If method name matches mutation pattern (`create*`, `update*`, `delete*`, `begin*`, `set*`), raise `ReadOnlyViolationError` with actionable message.

**Implementation status:**
- Deferred to issue #TBD (to be created after ADR-003 is ratified).
- Target: v0.2 or when tool count exceeds 10.
- Complexity: medium to high. Requires careful design to avoid breaking async clients, context managers, paginators.

## Consequences

### Enables

1. **Provable read-only boundary.** CI gate provides automated verification. Contributors get immediate feedback.
2. **Reduced attack surface.** Even if a transitive dependency is compromised, mutation imports are blocked at layer 1.
3. **Audit confidence.** External auditors can review `.github/scripts/check_readonly.py` and verify that mutation methods are CI-blocked.
4. **Contributor clarity.** Naming convention and CI feedback guide contributors toward read-only patterns without ambiguity.

### Costs

1. **Maintenance burden.** Azure SDK evolves. Allowlist and deny list must be updated as new SDK versions introduce new methods or packages.
2. **False positives (potential).** Legitimate read-only methods that match mutation naming patterns (e.g., `update_query_cache` for local caching) may be blocked. Mitigation: `# noqa: sentinel-readonly` suppression + Sentinel review.
3. **Layer 3 complexity.** Runtime guard implementation is non-trivial. Deferred to avoid blocking immediate progress.

### Risks Mitigated

Per `docs/security/threat-model.md`:

- **T (Tampering):** Compromised dependency cannot inject mutation code without triggering CI gate.
- **E (Elevation of Privilege):** Tool cannot escalate beyond read permissions even if attacker controls tool input.

### Open Questions Resolved from Wave 1 Outline

1. **Coverage threshold for tests?** Not in scope of ADR-003. Separate CI gate (TBD).
2. **CodeQL severity threshold?** Block on Error + Warning, advisory on Note. Implemented in `.github/workflows/codeql.yml`.
3. **Read-only script location?** `.github/scripts/check_readonly.py` (ratified in this ADR).
4. **Concurrent vs. chained CI execution?** Parallel workflow jobs. GitHub Actions schedules automatically.

## Implementation Status

- **Layer 1 (AST-based import allowlist):** PENDING. Implementation tracked in issue #7. Estimated effort: 1-2 days. Blocker for v0.1 release.
- **Layer 2 (convention + CODEOWNERS):** PENDING. Can be implemented in parallel with layer 1. Estimated effort: 1 hour.
- **Layer 3 (runtime guard):** DEFERRED. Tracked as follow-up issue (to be created). Target: v0.2 or when tool count exceeds 10.

## Alternatives Considered

See Options A-E above. Option E (combination) selected as best balance of safety, transparency, and implementation cost.

## Revisit If

1. **Azure SDK introduces read-only client variants.** If Azure SDK ships clients with compile-time or runtime read-only guarantees, re-evaluate whether layer 1 (AST check) is sufficient or whether layers 2 and 3 can be simplified.
2. **Tool count exceeds 20.** At scale, layer 3 (runtime guard) becomes more valuable as a defense-in-depth measure. Revisit implementation cost vs. risk.
3. **Dynamic dispatch becomes common.** If tool implementations rely heavily on `getattr`, reflection, or metaprogramming, layer 1 (static analysis) may miss violations. Layer 3 (runtime guard) becomes essential.

## References

1. **AGENTS.md, Read-Only Constraint:**  
   "Server, skills, and examples must be read-only against Azure. No mutation tools, ever."

2. **Threat Model (STRIDE-Lite):**  
   `docs/security/threat-model.md` (created in parallel with this ADR).

3. **Azure SDK for Python, Azure Identity:**  
   [learn.microsoft.com/python/api/azure-identity](https://learn.microsoft.com/python/api/azure-identity)  
   DefaultAzureCredential design and supported credential chains.

4. **Azure Resource Graph SDK:**  
   [learn.microsoft.com/python/api/azure-mgmt-resourcegraph](https://learn.microsoft.com/python/api/azure-mgmt-resourcegraph)  
   Read-only query surface.

5. **Python AST Module:**  
   [docs.python.org/3/library/ast.html](https://docs.python.org/3/library/ast.html)  
   Used for static import analysis in layer 1.

6. **STRIDE Threat Modeling:**  
   [learn.microsoft.com/azure/security/develop/threat-modeling-tool-threats](https://learn.microsoft.com/azure/security/develop/threat-modeling-tool-threats)  
   Adapted for MCP read-only servers.

7. **MCP Specification, Tool Safety:**  
   [modelcontextprotocol.io/specification/tools](https://modelcontextprotocol.io/specification/tools)  
   MCP protocol does not enforce read-only; this is a server-side implementation choice.

## Sentinel Review

**Verdict:** RATIFIED (2026-05-12)

**Summary:**  
ADR-003 establishes defense-in-depth for read-only enforcement. Layer 1 (AST-based CI gate) provides immediate, automated verification. Layers 2 (convention) and 3 (runtime guard) add incremental safety as the project matures. This approach balances safety, transparency, and implementation cost. Companion threat model in `docs/security/threat-model.md` provides STRIDE-lite context for read-only enforcement.

**Next steps:**
1. Implement layer 1: `.github/scripts/check_readonly.py` + CI integration (issue #7).
2. Implement layer 2: CODEOWNERS + naming convention enforcement in PR reviews.
3. Create follow-up issue for layer 3 (runtime guard), target v0.2.
