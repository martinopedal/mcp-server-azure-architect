# Skill: Architecture Design Review

## Overview

Guides an architect through a structured design review pass on a proposed Azure solution. Composes multiple MCP servers to surface reference architecture guidance, cost trade-offs, ALZ baseline compliance, and resilience posture. Produces a recommendation memo grounded in Microsoft Learn, ALZ checklists, and pricing data.

## When to Use

- Pre-deployment architecture decision gates. You have a sketch of the solution and need structured feedback.
- Comparing multiple platform options (e.g., App Gateway vs Front Door, AKS vs Container Apps). Need cost overlay and feature parity matrix.
- Validating proposed compute/network shape against ALZ baseline checks (e.g., does this design pass network security posture items).
- Surfacing architecture concerns before stakeholder reviews (resilience, security posture, operational overhead, cost).
- Bridging gap between design docs and implementation. Need to call out prerequisites and risks.

## Process

### Phase 1: Intake

The architect provides (as free-form narrative or structured list):

1. **Design summary:** one paragraph on what you are building and why.
   - Example: "Multi-region SaaS backend for financial analytics. Requires <100ms p99 latency coast-to-coast, 99.99% uptime, data residency in US/EU."

2. **Proposed topology:** list of resources and their placement.
   - Example: "App Service (US East + West Europe, active-active), Azure SQL (geo-replicated), Redis cache (global read replicas), Front Door Standard."

3. **Key constraints:** budget, regulatory, technical.
   - Example: "Budget cap: $15k/month. HIPAA compliance required. Teams have Kubernetes expertise but prefer managed services."

4. **Open questions:** what you are uncertain about.
   - Example: "Is multi-region worth the cost? Should we use App Gateway or Front Door? What failover latency should we target?"

### Phase 2: Reference Architecture Pull

Invoke `microsoft-learn` to surface canonical guidance for this problem domain.

- Query: "[domain] reference architecture" + any specific Azure service (App Service, SQL, Cache, etc.).
- Retrieve: Microsoft Learn architecture center articles with topology diagrams, design decisions, and trade-off analysis.
- Extract: cost estimates, resilience patterns (RTO/RPO targets), security baselines.

### Phase 3: Option Grid with Cost Overlay

For each major decision point in the design (e.g., ingress platform, database topology, caching strategy):

1. **List options:** alternatives the architect may not have considered.
   - Example for ingress: App Gateway Standard, App Gateway WAF, Front Door Standard, Front Door Premium.

2. **Invoke `pricing_compare_skus`** to get side-by-side cost comparison (capped at 10 options).
   - Input: SKUs, region (primary + secondary if multi-region), term (1-year reserved), currency.
   - Output: monthly cost per SKU, cumulative total for the option set.
   - Add to matrix: option name, primary SKU, monthly cost, annual cost.

3. **Build decision matrix:**

   | Option | Monthly Cost | Latency SLA Met? | Geo Footprint | WAF | Managed? | Notes |
   |---|---|---|---|---|---|---|
   | App Gateway WAF v2 (East US) | $150 | Single-region | East US | Yes | Yes | No multi-region; does not meet <100ms p99 coast-to-coast |
   | Front Door Standard | $75 + data transfer | Yes | Global | Yes | Yes | Good fit; $36k/year all-in |
   | Front Door Premium | $200 + data transfer | Yes | Global | Yes (WAF v3) | Yes | Higher cost; slightly better latency via Anycast |

4. **Highlight constraints vs options.**
   - Example: "Budget caps option set to under $20k/year. Front Door Premium is eliminated. Front Door Standard fits."

### Phase 4: ALZ Checklist Alignment

Invoke `alz_query_by_id` with relevant checklist items for the solution's domain (Network, Security, Compute, Identity, etc.).

1. **Identify applicable pillars** (Network for multi-region, Security for encryption, Compute for AKS, etc.).

2. **Run queries** to retrieve baseline compliance items.
   - Example: `alz_query_by_id(checklist_id="network-security-posture")` returns: "WAF enabled on all ingress, TLS 1.2+, DDoS Protection Standard on Front Door, NSG rules follow least privilege."

3. **Map proposed design against items:**
   - Compliant: design meets the item (e.g., "Front Door includes WAF v3 in Premium SKU; WAF enabled").
   - Non-compliant: design violates item (e.g., "No DDoS Protection Standard configured").
   - Deferred: item not applicable to this phase (e.g., "DR/backup; out of scope for initial deployment").

4. **Classify risk:**
   - Red: non-compliant on critical item (e.g., encryption, WAF). Requires redesign.
   - Yellow: non-compliant on operational item (e.g., backup frequency). Add to runbook.
   - Green: compliant or explicitly waived.

### Phase 5: Resilience / Security / Cost / Operability Scoring

For each pillar, assign a score and notes.

- **Resilience:** Can the design absorb a region failure, data center outage, or dependency degradation? Score 1-5 (1 = single point of failure, 5 = multi-region with auto-failover).
  - Example: "Multi-region active-active with Front Door auto-failover. SQL geo-replication with failover groups. Score: 5."

- **Security:** Does the design enforce least privilege, encryption in transit and at rest, identity controls? Score 1-5 (1 = unencrypted public endpoints, 5 = end-to-end encryption, RBAC, compliance scanned).
  - Example: "TLS 1.2+ enforced, Azure AD RBAC, SQL encryption at rest with CMEK. WAF v3 on Front Door. Score: 5."

- **Cost:** Is the estimated monthly/annual cost within budget? Normalized to per-unit value (e.g., $/transaction, $/user, $/GB). Score 1-5 (1 = 2x budget, 5 = <50% of budget).
  - Example: "Estimated $12k/year multi-region active-active. Budget: $15k/year. Score: 4 (95% utilization)."

- **Operability:** How much human-in-the-loop is required? Can the design scale, patch, and upgrade with minimal toil? Score 1-5 (1 = manual scaling, quarterly maintenance windows, 5 = fully auto-scaled, gitops-driven, no manual gates).
  - Example: "App Service auto-scale, SQL managed patch windows, Front Door no manual failover. Score: 4 (logging/alerting setup required)."

### Phase 6: Recommendation Memo

Synthesize into a memo format:

```
# Design Review: {solution name}

## Summary

{One-sentence verdict: Approved / Approved with conditions / Revisit / Rejected}

## Proposed Topology

{Recap of Phase 1 intake}

## Reference Guidance

- [Microsoft Learn article: {domain} reference architecture]({url})
- [ALZ Checklist: {pillar} baseline]({url})

## Option Analysis

### Decision Point 1: {Ingress platform}

| Option | Cost | Latency | GeoSpan | Verdict |
|---|---|---|---|---|
| App Gateway WAF v2 | $X/mo | Single-region | US East | Ruled out; no multi-region |
| Front Door Standard | $Y/mo | <50ms p99 | Global | **Recommended** |
| Front Door Premium | $Z/mo | <30ms p99 | Global | Over-spec for requirement |

**Recommendation:** Use Front Door Standard. Meets latency SLA at acceptable cost.

## ALZ Checklist Alignment

| Pillar | Checklist Item | Status | Notes |
|---|---|---|---|
| Network | WAF enabled | ✓ Compliant | Front Door WAF v3 in all SKUs |
| Network | DDoS Protection | ✓ Compliant | Included with Front Door Standard |
| Security | TLS 1.2+ | ✓ Compliant | Front Door enforces TLS 1.2+ |
| Security | Encryption at rest | ✓ Compliant | SQL CMEK, blob encryption enabled |
| Compute | RBAC on App Service | ✓ Compliant | Managed identity + role assignments in place |

**Overall:** 5/5 pillars green. No blockers.

## Pillar Scores

| Pillar | Score | Notes |
|---|---|---|
| Resilience | 5/5 | Multi-region active-active, auto-failover groups, no SPOFs |
| Security | 5/5 | End-to-end encryption, WAF, RBAC, compliance scanned |
| Cost | 4/5 | $12k/year, 95% of budget; reserve for elasticity |
| Operability | 4/5 | Auto-scaling enabled; alerting/runbooks needed for edge cases |

## Risks & Mitigations

1. [Risk] Multi-region latency variance during failover may spike p99 to 500ms for 30 seconds.
   [Mitigation] Run chaos test with regional partition; document SLA exception window. Alert after 60s to on-call.

2. [Risk] CMEK key rotation requires application-aware invalidation of blob leases.
   [Mitigation] Test key rotation in staging monthly; add to runbook.

## Prerequisites

- [ ] SQL Database geo-replication configured and tested.
- [ ] Front Door routing rules validated against application traffic patterns.
- [ ] Certificates imported to Key Vault with auto-renewal.
- [ ] Chaos tests: region failure, dependency degradation.
- [ ] Alerts configured for cross-region latency spike.

## Approval

Recommend proceeding to implementation with prerequisites checklist signed off.

---

**Review Date:** YYYY-MM-DD  
**Reviewer:** {name}  
**Next Gate:** Implementation plan + prerequisites sign-off.
```

## Cross-Repo Contract: Companion Servers

This skill composes:

1. **`microsoft-learn` (hosted, no local setup):** Retrieves canonical architecture guidance and compliance baselines. No refresh cycle needed; queries live documentation.

2. **`mermaid`:** Renders architecture diagrams from text (optional, for as-is/to-be visualization). Invoke via: "Draw as-is topology: {list of resources} → to-be topology: {improved list}".

3. **`pricing_lookup_sku` / `pricing_compare_skus` (this server):** Azure retail pricing for SKU comparison. Capped at 10 SKUs per call. When SKU catalog changes or new SKU sizes are released, architect re-runs comparison (no skill code change needed).

4. **`alz_query_by_id` (this server):** ALZ checklist queries by UUID. Consumes snapshot pinned in `data/alz-queries/manifest.json`. When upstream ALZ checklist repos update, trigger snapshot refresh (Atlas owns this; Iris consumes the output).

5. **`azure-mcp` (optional, live env inspection):** For deeper resource inspection or cost analysis against actual deployed resources. Optional; not required for design-review flow.

## Worked Example

**Scenario:** Financial services firm planning multi-region SaaS backend. Current: single App Service in East US. Target: active-active across US and EU, 99.99% uptime, <100ms p99 latency, HIPAA compliance, $15k/year budget.

### Phase 1: Intake

```
Design Name: Multi-Region Financial SaaS Backend

Current State:
- Single App Service (East US), no geo-redundancy
- SQL Database (single-region, local redundancy only)
- Redis (single-region, no replicas)
- Traffic routed via DNS round-robin (manual failover)

Proposed State:
- App Service (East US + West Europe, active-active)
- SQL Database (geo-replicated with failover groups)
- Redis (geo-distributed replicas)
- Front Door routing and failover

Constraints:
- Budget: $15k/year all-in
- Compliance: HIPAA (encryption, audit logging, data residency)
- SLA: 99.99% availability, <100ms p99 latency coast-to-coast
- Team: 2 SREs, familiar with IaC

Open Questions:
- Is multi-region premium warranted vs cost?
- Front Door Standard or Premium?
- How to handle HIPAA audit logging at scale?
```

### Phase 2: Reference Architecture Pull

```
Query 1: "multi-region app service reference architecture"
-> Microsoft Learn: "Build a geographically distributed application with Azure Traffic Manager"
   https://learn.microsoft.com/azure/app-service/app-service-web-tutorial-custom-domain
   Guidance: use Front Door (not Traffic Manager) for global routing; auto-failover on probe.

Query 2: "HIPAA compliance reference architecture"
-> Microsoft Learn: "HIPAA compliance reference architecture"
   https://learn.microsoft.com/compliance/regulatory/hipaa
   Requirements: encryption at rest + in transit, audit logging to immutable store, access controls.

Query 3: "Azure Cache for Redis geo-replication"
-> Microsoft Learn: "Azure Cache for Redis geo-replication"
   https://learn.microsoft.com/azure/azure-cache-for-redis/cache-how-to-geo-replication
   Guidance: Premium tier supports geo-replication with < 1 second latency to replica.
```

### Phase 3: Option Grid with Cost Overlay

```
Ingress Platform Options:

| Option | Monthly Cost | Latency SLA | Geo | WAF | Managed? | Notes |
|---|---|---|---|---|---|---|
| Traffic Manager + App Gateway v2 | $100 | Single-region | US only | Yes | Yes | No multi-region; does not meet latency SLA |
| Front Door Standard | $75 | <100ms p99 | Global | Yes | Yes | **Recommended** |
| Front Door Premium | $200 | <50ms p99 | Global | WAF v3 | Yes | Over-spec; premium WAF not needed for HIPAA |

Database Options:

| Option | Monthly Cost | RTO | RPO | Compliance | Notes |
|---|---|---|---|---|---|
| SQL Standard geo-replication | $300 | 5 min | <5 sec | HIPAA-ready | Passive secondary; manual failover |
| SQL Standard failover groups | $350 | <30 sec | 1-5 sec | HIPAA-ready | **Recommended**; auto-failover |

Cache Options:

| Option | Monthly Cost | Latency | Replication | Notes |
|---|---|---|---|---|
| Redis Standard | $200 | 1-2 ms | No | No multi-region; single point of failure |
| Redis Premium (no geo) | $600 | 1-2 ms | Within-region | HIPAA-ready but no cross-region |
| Redis Premium + geo-replication | $1200 | <1 ms to replica | Cross-region | **Recommended**; meets resilience SLA |

**Total Monthly Estimate:**
- Front Door Standard: $75
- SQL Standard + failover groups: $350
- Redis Premium + geo-replication: $1200
- App Service (East US + West Europe): $400 (estimated)
- Log Analytics (HIPAA audit logging): $150
- Total: ~$2,175/month = $26,100/year

**Budget Analysis:**
Target: $15k/year. Estimate: $26k/year. Over budget by 73%.

**Recommendation:**
Revisit Cache strategy. Evaluate Redis Standard with manual cross-region failover (cost $400/mo). Tradeoff: longer failover, but meets budget target.

Revised Total: ~$1,375/month = $16,500/year (within 10% of budget).
```

### Phase 4: ALZ Checklist Alignment

```
Running: alz_query_by_id(checklist_id="network-security-posture")

Results:
- WAF enabled on all ingress: ✓ Front Door includes WAF v3
- TLS 1.2+ enforced: ✓ Front Door enforces min TLS 1.2
- DDoS Protection Standard on public endpoints: ✓ Included with Front Door
- NSG rules follow least privilege: ✓ App Service VNET integration + NSG rules in place
- Private endpoints for PaaS: ✓ SQL Database private endpoint configured

Running: alz_query_by_id(checklist_id="identity-access-control")

Results:
- RBAC on all resources: ✓ Managed identity on App Service, role assignments in place
- MFA on admin access: ✓ Azure AD conditional access policy enforced
- No public credentials in app settings: ✓ Using Key Vault + managed identity

Overall: 8/8 Network + Identity items compliant. No blockers.

Running: alz_query_by_id(checklist_id="data-encryption")

Results:
- Encryption in transit: ✓ TLS 1.2+ on all paths
- Encryption at rest: ✓ SQL CMEK, blob encryption enabled
- Key rotation automated: ✓ Key Vault auto-rotation enabled

Overall: 3/3 Encryption items compliant.
```

### Phase 5: Resilience / Security / Cost / Operability Scoring

```
Resilience: 4/5
- Multi-region active-active for App Service and front-end routing.
- SQL failover groups auto-switch on heartbeat failure (<30 sec RTO).
- Redis Standard (no geo-replication) is a single point of failure in cache layer.
  Mitigation: monitor cache hit ratio; acceptable risk for session/transient data.
- **Gap:** No chaos test scheduled yet. Add to runbook.

Security: 5/5
- End-to-end encryption: TLS 1.2+ on all paths, SQL/Blob encryption at rest with CMEK.
- WAF v3 on Front Door: protects against OWASP top 10 exploits.
- RBAC + managed identities: no app-level credentials.
- Audit logging: diagnostic settings log all activity to Log Analytics (immutable by HIPAA requirement).
- **Compliant:** HIPAA baseline verified.

Cost: 3/5
- Estimated $16.5k/year (revised with budget trade-offs).
- Budget target: $15k/year. 10% over.
- **Tradeoff:** Deferred multi-region Redis replication. Acceptable for MVP; revisit if cache hit ratio > 80%.

Operability: 3/5
- App Service auto-scaling enabled. ✓
- SQL failover is automatic. ✓
- Patch windows managed by Azure. ✓
- **Gaps:**
  - Alerts not yet configured for latency spikes, failover events.
  - Runbook for emergency failover (manual cache flush) not written.
  - Log Analytics queries for HIPAA audit not finalized.
- **To-do:** Add alerting + runbook setup to prerequisites.
```

### Phase 6: Recommendation Memo

```
# Design Review: Multi-Region Financial SaaS Backend

## Summary

**Approved with Conditions.** Design meets HIPAA compliance, ALZ baseline, and resilience SLA (99.99% uptime, <100ms p99 latency). Budget is 10% over target due to Redis Premium costs. Recommend deferring cross-region Redis replication to Phase 2 (post-MVP); use Standard Redis with manual failover.

## Proposed Topology

- **Ingress:** Azure Front Door Standard (active-active routing, global)
- **Compute:** App Service (East US + West Europe, active-active)
- **Database:** Azure SQL Standard + failover groups (geo-replicated, automatic failover)
- **Cache:** Azure Cache for Redis Standard (single-region with manual failover strategy)
- **Logging:** Log Analytics (HIPAA audit trail, immutable retention)

## Reference Guidance

- [Azure App Service multi-region deployment](https://learn.microsoft.com/azure/app-service/app-service-web-tutorial-custom-domain)
- [HIPAA compliance baseline](https://learn.microsoft.com/compliance/regulatory/hipaa)
- [Azure Cache for Redis - Geo replication](https://learn.microsoft.com/azure/azure-cache-for-redis/cache-how-to-geo-replication)
- ALZ Checklist: Network, Identity, Data Encryption baselines (all compliant).

## Option Analysis

### Decision Point 1: Ingress Platform

| Option | Cost | Latency | Verdict |
|---|---|---|---|
| Traffic Manager + App Gateway | $100 | Single-region | Ruled out |
| Front Door Standard | $75 | <100ms p99 | **Recommended** |
| Front Door Premium | $200 | <50ms p99 | Over-spec |

**Recommendation:** Front Door Standard saves $125/mo vs Premium without sacrificing SLA.

### Decision Point 2: Cache Tier

| Option | Cost | Failover | Verdict |
|---|---|---|---|
| Redis Standard | $200 | Manual | **Phase 1 choice** |
| Redis Premium + geo-replication | $1200 | Automatic | Phase 2 upgrade |

**Recommendation:** Phase 1 uses Standard with manual failover. Post-MVP, evaluate hit ratio; if > 80%, upgrade to Premium + geo-replication.

## ALZ Checklist Alignment

| Pillar | Items | Status | Notes |
|---|---|---|---|
| Network | WAF, DDoS, TLS, NSG | ✓ 5/5 | All Front Door + App Service network items compliant |
| Security | Encryption, RBAC, audit logging | ✓ 3/3 | End-to-end encryption, HIPAA audit trail enabled |
| Identity | RBAC, MFA, no credentials | ✓ 3/3 | Managed identity + Azure AD conditional access |

**Overall:** 11/11 items compliant. No blockers.

## Pillar Scores

| Pillar | Score | Notes |
|---|---|---|
| Resilience | 4/5 | Multi-region active-active; single cache SPOF acceptable for MVP |
| Security | 5/5 | HIPAA baseline verified; end-to-end encryption |
| Cost | 3/5 | $16.5k/year (10% over budget); Phase 2 optimization opportunity |
| Operability | 3/5 | Auto-scaling + failover OK; alerting + runbooks needed |

## Risks & Mitigations

1. [Risk] Cache failover requires manual intervention if Redis Standard goes down in primary region.
   [Mitigation] Document cache flush procedure in runbook. Monitor cache hit ratio. Escalate to Phase 2 if hit ratio > 80%.

2. [Risk] Multi-region App Service costs $200/mo extra; may not justify for this workload.
   [Mitigation] Monitor usage patterns for 3 months. If traffic is 80/20 US/EU, consolidate to single-region + CDN.

3. [Risk] HIPAA audit logging at scale may exceed Log Analytics quota ($150/mo estimate).
   [Mitigation] Implement sampling for non-sensitive logs. Set budget alert at $175/mo.

## Prerequisites

- [ ] SQL Database geo-replication and failover groups tested (RTO < 30s verified)
- [ ] Front Door routing rules validated against application traffic patterns
- [ ] Certificates imported to Key Vault with auto-renewal
- [ ] Alerting configured: latency spike (>150ms p99), failover events, cache miss spike
- [ ] Runbook written: emergency failover (cache flush), certificate renewal, diagnostics
- [ ] HIPAA audit logging queries finalized and logged to immutable store
- [ ] Chaos test: simulate East US region failure; verify Front Door failover < 30s

## Approval

Recommend proceeding to implementation with prerequisites checklist signed off by SRE team lead.

---

**Review Date:** 2026-05-15  
**Reviewer:** Architect  
**Status:** Ready for implementation  
**Next Gate:** Prerequisite sign-off + chaos test results
```

## Confidence

**Low** (first capture). This distills known Azure design-review patterns from ALZ and Microsoft Learn. Refinement pending: (1) feedback from real architect sessions using this skill, (2) ALZ checklist item stability as snapshot refreshes, (3) pricing data fidelity over time.

## Related Skills

- **alz-gap-check** (#12): Runs ALZ checklist queries; design-review consumes alz_query_by_id output.
- **policy-as-code-suggest**: Translates design governance decisions into Azure Policy.
- **ingress-migration-plan**: Specialized design-review for networking changes.

## Citations

- [Microsoft Learn Architecture Center](https://learn.microsoft.com/azure/architecture/)
- [Azure Well-Architected Framework](https://learn.microsoft.com/azure/architecture/framework/)
- [Azure pricing calculator](https://azure.microsoft.com/pricing/calculator/)
- [HIPAA compliance in Azure](https://learn.microsoft.com/compliance/regulatory/hipaa)
- [Azure Front Door](https://learn.microsoft.com/azure/frontdoor/)
- [Azure SQL Database geo-replication](https://learn.microsoft.com/azure/azure-sql/database/geo-distributed-transactional-consistency-with-sql-database)
- ALZ Checklist: Network, Identity, Data Encryption pillars (vendored snapshot commit SHAs in `data/alz-queries/manifest.json`)
