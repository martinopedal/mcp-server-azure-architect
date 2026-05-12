# Skill: ALZ Gap Check

## Overview

Walks a subscription through Azure Landing Zone (ALZ) checklist conformance item-by-item, surfacing compliance gaps and remediation guidance. Orchestrates ALZ checklist queries by pillar (Network, Security, Identity, Compute, Governance, Operations) and correlates gaps with Azure resources. Produces a conformance memo with severity classification and Microsoft Learn remediation links.

## When to Use

- Assessing whether a subscription or resource group aligns with ALZ baseline controls.
- Post-migration conformance audit. Move a workload to Azure and validate it passes ALZ checks.
- Compliance audit cycle. Need to run ALZ scorecard and drill into failures by pillar.
- Operational readiness gate. Design review passed; now verify live infrastructure is ALZ-aligned before handoff.
- Regulatory/audit prep. Need documented evidence of ALZ compliance per pillar (Network, Security, Identity, etc.).

## Process

### Phase 1: Scope Intake

The architect or operator provides:

1. **Subscription ID and/or resource group(s)** to be scanned.
   - Example: `/subscriptions/{subscription-id}` or `/subscriptions/{subscription-id}/resourceGroups/{resource-group}`.

2. **Pillar(s) to review** (if not all).
   - Example: "Focus on Security + Identity pillars for this audit. Skip Governance for now."
   - Default: all pillars (Network, Security, Identity, Compute, Governance, Operations).

3. **Severity threshold** (optional).
   - Example: "Show only items rated 'Critical' or 'High'. Skip 'Informational' items."
   - Default: all.

4. **Resource types to focus on** (optional).
   - Example: "Check only App Service and SQL Database. Skip Storage and Networking."
   - Default: all resource types.

### Phase 2: Pillar Selection and Query Iteration

For each selected pillar:

1. **Run `alz_query_by_id`** to retrieve checklist items for that pillar.
   - The vendored ALZ snapshot (pinned in `data/alz-queries/manifest.json`) provides pre-baked queries by checklist UUID.
   - Query returns: checklist item ID, resource count scanned, compliant count, non-compliant count, example non-compliant resources.

2. **Iterate over queries** for this pillar.
   - Each query focuses on one control area (e.g., "WAF enabled on all ingress" or "MFA enforced on admin access").

3. **Invoke live resource inspection** via `azure-mcp` if needed for deeper diagnostics.
   - Example: if "Encryption at rest" query shows 10 non-compliant storage accounts, query azure-mcp for the 10 storage account details (encryption settings, access tiers, etc.).
   - Optional; `alz_query_by_id` output often suffices for high-level conformance.

### Phase 3: Categorize Failures by Severity

As results come back, classify each non-compliant item:

- **Critical:** Security or compliance blocker. Example: "Public endpoint enabled on SQL Database with no firewall rule." Remediates before production.
- **High:** Operational or security concern. Example: "Diagnostic settings not configured; no audit trail." Remediates within 1-2 sprints.
- **Medium:** Best-practice gap. Example: "Resource not tagged with cost center." Remediates in next tagging pass.
- **Low:** Informational. Example: "Older API version used; newer version available." Remediates during next upgrade cycle.

### Phase 4: Remediation Memo

Generate structured output:

```
# ALZ Conformance Report: {subscription name}

## Summary

- **Subscription:** {subId}
- **Scan Date:** {date}
- **Pillars Scanned:** {Network, Security, Identity, Compute, Governance, Operations}
- **Overall Compliance:** {X}% ({Y compliant items} / {Z total items})
- **Status:** Green / Yellow / Red

## Pillar Breakdown

| Pillar | Compliant | Non-Compliant | Critical | High | Medium | Low |
|---|---|---|---|---|---|---|
| Network | 15 | 2 | 0 | 2 | 0 | 0 |
| Security | 20 | 5 | 1 | 2 | 2 | 0 |
| Identity | 12 | 1 | 0 | 0 | 1 | 0 |
| Compute | 18 | 3 | 0 | 1 | 2 | 0 |
| Governance | 10 | 4 | 0 | 1 | 3 | 0 |
| Operations | 8 | 2 | 0 | 1 | 1 | 0 |
| **Total** | **83** | **17** | **1** | **7** | **9** | **0** |

**Overall Compliance:** 83% (83/100 items)  
**Verdict:** Yellow (High-severity items exist; plan remediation)

## Critical Items

### 1. Security: SQL Database Public Endpoint

**Checklist Item:** `sql-public-endpoint-deny` (vendored from alz-checklist-queries, commit SHA: e7641beeda0126cc78825f8b77764c379552f3e1)

**Finding:** SQL Database {dbName} in {resourceGroup} has public endpoint enabled with no firewall deny rule.

**Impact:** High-risk. Public internet access to database exposes credentials, data exfiltration vectors.

**Remediation:**
1. Set `public endpoint access = Denied` on SQL Database.
2. Ensure application connectivity via private endpoint or VNET service endpoint.
3. Validate application connectivity before disabling public endpoint.

**References:**
- [Azure SQL Database Private Link](https://learn.microsoft.com/azure/azure-sql/database/private-endpoint-overview)
- [Azure SQL Database Firewall Rules](https://learn.microsoft.com/azure/azure-sql/database/firewall-configure)

**Estimated Effort:** 2 hours (includes testing)  
**Owner:** DBA / Infrastructure Team  
**Target Date:** Within 2 weeks

---

## High-Priority Items

### 1. Network: No WAF on App Gateway

**Checklist Item:** `network-waf-appgw` (vendored from alz-checklist-queries, commit SHA: e7641beeda0126cc78825f8b77764c379552f3e1)

**Finding:** App Gateway {gwName} in {resourceGroup} has WAF disabled.

**Impact:** Medium-risk. OWASP top-10 attacks (SQL injection, XSS) not blocked at ingress.

**Remediation:**
1. Upgrade App Gateway to v2 if not already.
2. Attach WAF policy (Azure-managed or custom rules).
3. Start in Detection mode; switch to Prevention after 2 weeks of tuning.

**References:**
- [Azure Application Gateway WAF](https://learn.microsoft.com/azure/web-application-firewall/ag/overview)
- [WAF Policy Creation and Assignment](https://learn.microsoft.com/azure/web-application-firewall/ag/create-custom-waf-rules)

**Estimated Effort:** 4 hours (includes WAF rule tuning)  
**Owner:** Security / Operations Team  
**Target Date:** Within 1 month

---

### 2. Security: Diagnostic Settings Missing

**Checklist Item:** `security-diagnostic-settings` (vendored from alz-checklist-queries, commit SHA: e7641beeda0126cc78825f8b77764c379552f3e1)

**Finding:** Storage accounts {storageNames} have no diagnostic settings configured. No audit trail of access attempts.

**Impact:** Medium-risk. Compliance audit cannot verify who accessed data; HIPAA/PCI-DSS audit fails.

**Remediation:**
1. Create or identify Log Analytics workspace for centralized logging.
2. For each storage account, enable diagnostic settings:
   - Send all logs (StorageRead, StorageWrite, StorageDelete) to Log Analytics.
   - Set retention to 90 days minimum (or meet compliance requirement).
3. Test log ingestion: access storage; verify log appears in Log Analytics within 5 minutes.

**References:**
- [Azure Storage Diagnostic Settings](https://learn.microsoft.com/azure/storage/common/storage-diagnostic-logging)
- [Create Log Analytics Workspace](https://learn.microsoft.com/azure/azure-monitor/logs/quick-create-workspace)

**Estimated Effort:** 1 hour per storage account (bulk policy assignment can reduce to 15 min total)  
**Owner:** Security / Operations Team  
**Target Date:** Within 2 weeks

---

## Medium-Priority Items

### 1. Governance: Resource Tagging Incomplete

**Checklist Item:** `governance-resource-tags` (vendored from alz-checklist-queries, commit SHA: e7641beeda0126cc78825f8b77764c379552f3e1)

**Finding:** {N} resources missing required tags: cost-center, environment, owner.

**Impact:** Low-to-medium risk. Cost allocation inaccurate; chargeback and governance reports incomplete.

**Remediation:**
1. Audit: List all resources missing tags.
2. Bulk tag via Azure Policy (DeployIfNotExists effect) or Azure CLI script.
3. Enforce tagging on new resources via policy (Deny effect if tags missing).

**References:**
- [Azure Resource Tagging Best Practices](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/resource-tagging)
- [Azure Policy for Tagging](https://learn.microsoft.com/azure/governance/policy/samples/built-in-policies)

**Estimated Effort:** 2 hours (includes policy setup + testing)  
**Owner:** Governance / FinOps Team  
**Target Date:** Within 1 quarter

---

## Compliant Items (by Pillar)

### Network (15/17 compliant)

- ✓ NSG rules follow least privilege
- ✓ Network Security Groups applied to all subnets
- ✓ Private endpoints configured for PaaS services
- ✓ Service endpoints enabled for Key Vault, Storage, SQL
- ✓ Network watcher enabled for flow logging
- ✓ DDoS Protection Standard enabled on Front Door
- ✓ Application Gateway has WAF enabled (3/5 instances; see High-Priority for non-compliant)
- (more...)

### Security (20/25 compliant)

- ✓ Encryption at rest enabled on all storage
- ✓ TLS 1.2+ enforced on all public endpoints
- ✓ Key Vault soft-delete and purge protection enabled
- ✓ RBAC enforced on Key Vault access
- (more...)

### Identity (12/13 compliant)

- ✓ Azure AD is identity provider
- ✓ MFA enforced on privileged accounts
- ✓ Managed identities used for App Service authentication
- (more...)

## Remediation Timeline

**Week 1-2 (Critical):**
- [ ] SQL Database: Disable public endpoint, enable private endpoint

**Week 3-4 (High):**
- [ ] App Gateway: Enable WAF v2, configure rules, test in Detection mode
- [ ] Storage: Enable diagnostic settings, configure Log Analytics ingestion

**Month 2 (Medium):**
- [ ] Resource tagging: Bulk tag via policy or script
- [ ] Key rotation: Test and schedule for compliant items

**Ongoing:**
- [ ] Monitor compliance score monthly
- [ ] Update checklist as new Azure features/policies land

## Compliance Trends

(Optional: if historical data available)

| Scan Date | Overall % | Critical | High | Trend |
|---|---|---|---|---|
| 2026-04-01 | 70% | 2 | 8 | Baseline |
| 2026-05-01 | 83% | 1 | 7 | Improving |
| 2026-06-01 | 88% | 0 | 4 | On track |

## Appendix: Query Details

Each checklist item below includes the vendored query ID, source repository commit SHA, and guidance.

### Network Pillar

| Query ID | Item | Source Commit | Guidance |
|---|---|---|---|
| e8aa1e41-870d-4968-94c6-77be14f510ac | NSG coverage | alz-graph-queries@8a3fddabcbf | NSGs on all subnets required |
| 54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a | Budget alerts configured | alz-checklist-queries@e7641bee | Budgets with spend alerts on all subscriptions |
| (more...) | | | |

---

**Report Generated:** {date}  
**Next Review Date:** {date + 30 days}  
**Owner:** {team}  
**Distribution:** {stakeholders}
```

## Cross-Repo Contract: ALZ Vendoring

This skill consumes queries vendored from:

- `martinopedal/alz-checklist-queries` (Network, Security, Identity, Compute, Governance, Operations pillar baseline queries)
- `martinopedal/alz-graph-queries` (ARG-based graph analysis queries for topology and blast-radius analysis)

Snapshot is pinned in `data/alz-queries/manifest.json` with commit SHAs. To refresh snapshot:

1. Atlas (ARG/KQL Engineer) runs vendoring process against upstream repos.
2. New manifest.json and query files land on `main`.
3. Iris (Copilot Skills Author) re-runs `alz_query_by_id` calls to verify no query contract breakage.
4. If upstream adds new pillar queries, update Phase 2 iteration logic if needed (mechanical change).

**Note on `alz_scorecard` (forthcoming from Forge):**  
When Forge completes `alz_scorecard` tool (sweeps all ALZ queries in one call, returns aggregated score), this skill will prefer `alz_scorecard` for high-level conformance snapshots. Until then, skill iterates `alz_query_by_id` by pillar. No code change needed when `alz_scorecard` lands; skill auto-detects tool availability.

## Worked Example

**Scenario:** Financial services firm's Azure subscription post-migration. Infrastructure team needs to verify ALZ alignment before handing to Operations.

### Phase 1: Scope Intake

```
Subscription: /subscriptions/{subId}
Name: prod-fintech-backend
Resource Groups: prod-fintech-rg, prod-shared-svc-rg

Pillars: All (default)
Severity Threshold: All
Resource Focus: All (default)

Timeline: 1-hour conformance check needed for handoff meeting.
```

### Phase 2: Query Iteration

```
Pillar: Network
------

Query 1: alz_query_by_id("e8aa1e41-870d-4968-94c6-77be14f510ac")
Result: NSG coverage
  - Total subnets: 12
  - Compliant (NSG attached): 11
  - Non-compliant: 1 (subnet: subnet-app-01)
  - Recommendation: Attach NSG to app-subnet; copy rules from app-subnet-prod

Query 2: alz_query_by_id("54f0d8b1-22a3-4c0d-8ce2-58b9e086c93a")
Result: Budget alerts
  - Budgets configured: 1 (subscription-level budget at 90% threshold)
  - Alert destination: email + SMS
  - Status: Compliant

Query 3: alz_query_by_id("667313b4-f566-44b5-b984-a859c773e7d2")
Result: DDoS Protection
  - Front Door Standard enabled: Yes
  - DDoS Protection status: Basic (included with Front Door)
  - Recommendation: Upgrade to DDoS Protection Standard for critical workloads

(more queries for Network pillar...)

Pillar: Security
------

Query 1: alz_query_by_id("{security-encryption-at-rest}")
Result: Storage account encryption
  - Total storage accounts: 5
  - Encrypted at rest: 5
  - Status: Compliant

Query 2: alz_query_by_id("{security-public-endpoints}")
Result: Public endpoint exposure
  - SQL Databases: 1 with public endpoint enabled (NON-COMPLIANT)
  - App Services: 0 with public endpoints
  - Storage: 0 with public blob access
  - Recommendation: SQL Database {dbName} requires remediation (CRITICAL)

Query 3: alz_query_by_id("{security-tls-version}")
Result: TLS enforcement
  - Front Door: TLS 1.2+ enforced
  - App Service: TLS 1.2 enforced, TLS 1.0/1.1 disabled
  - Status: Compliant

(more queries...)

Pillar: Identity
------

Query 1: alz_query_by_id("{identity-rbac}")
Result: Role assignments
  - Subscription-level RBAC: 12 role assignments
  - Resource-level RBAC: 45 role assignments
  - Privileged roles (Owner, Contributor): 3 (users)
  - Recommendation: Review 3 privileged role holders; consider PIM enrollment

(more queries...)
```

### Phase 3: Categorize Failures

```
Critical (1):
1. SQL Database public endpoint enabled. No firewall rule. 

High (3):
1. Subnet without NSG (potential blast radius).
2. TLS 1.0/1.1 still accepted on legacy API endpoint.
3. Diagnostic settings not configured on Key Vault.

Medium (2):
1. Resource tagging incomplete (20% of resources missing tags).
2. Role assignments lack Just-In-Time (JIT) governance.

Low (1):
1. Azure Advisor suggests VM resize opportunity.
```

### Phase 4: Remediation Memo (extract)

```
# ALZ Conformance Report: prod-fintech-backend

## Summary

- Subscription: prod-fintech-backend (/subscriptions/{subId})
- Scan Date: 2026-05-15T14:30:00Z
- Pillars Scanned: Network, Security, Identity, Compute, Governance, Operations
- Overall Compliance: 85% (86/101 items)
- Status: Yellow (1 Critical, 3 High items require remediation before production handoff)

## Pillar Breakdown

| Pillar | Compliant | Non-Compliant | Critical | High | Medium | Low |
|---|---|---|---|---|---|---|
| Network | 15 | 2 | 0 | 1 | 1 | 0 |
| Security | 18 | 5 | 1 | 2 | 2 | 0 |
| Identity | 14 | 2 | 0 | 0 | 1 | 1 |
| Compute | 16 | 2 | 0 | 0 | 2 | 0 |
| Governance | 12 | 3 | 0 | 0 | 2 | 1 |
| Operations | 11 | 2 | 0 | 0 | 0 | 2 |
| **Total** | **86** | **16** | **1** | **3** | **8** | **4** |

## Critical Items

### 1. Security: SQL Database Public Endpoint

**Checklist Item:** sql-public-endpoint-deny  
**Source:** martinopedal/alz-checklist-queries@e7641beeda0126cc78825f8b77764c379552f3e1

**Finding:** Database {dbName} in prod-fintech-rg has public endpoint enabled. Zero firewall rules; internet-accessible.

**Remediation Steps:**
1. In Azure Portal: SQL Database > Networking > Public endpoint: Deny
2. Verify App Service can connect via private endpoint (pre-configured)
3. Run integration tests against database
4. Disable public endpoint

**Target:** Before production handoff (48 hours)

---

## High-Priority Items

### 1. Network: Unprotected Subnet

**Checklist Item:** network-nsg-coverage  
**Source:** martinopedal/alz-graph-queries@8a3fddabcbf272a19a627770a0d33de5f4ace8ee

**Finding:** Subnet 'app-subnet-01' in prod-fintech-rg has no NSG. Blast radius: 3 App Service instances, 1 App Gateway backend pool.

**Remediation Steps:**
1. Create NSG 'app-subnet-01-nsg' with least-privilege rules (copy from prod-fintech-app-nsg)
2. Attach to app-subnet-01
3. Verify traffic still flows (App Service health checks should pass)

**Target:** Within 1 week

---

### 2. Security: TLS 1.0/1.1 on Legacy API

**Checklist Item:** security-tls-min-version  
**Source:** martinopedal/alz-checklist-queries@e7641beeda0126cc78825f8b77764c379552f3e1

**Finding:** API endpoint {endpointName} still accepts TLS 1.0 and 1.1. Clients may be outdated.

**Remediation Steps:**
1. Audit: Identify clients sending TLS <1.2 (check logs in Application Insights)
2. Issue deprecation notice to consuming teams (30-day sunset)
3. Set App Service: .NET Framework version to 4.8+; disable TLS <1.2 via SSL/TLS settings
4. Monitor for client connection failures

**Target:** Within 2 weeks

---

### 3. Security: Missing Diagnostic Settings

**Checklist Item:** security-diagnostic-settings  
**Source:** martinopedal/alz-checklist-queries@e7641beeda0126cc78825f8b77764c379552f3e1

**Finding:** Key Vault has no diagnostic settings. No audit trail of secret access.

**Remediation Steps:**
1. Identify Log Analytics workspace (prod-shared-svc-rg/logs-prod)
2. Enable diagnostic settings on Key Vault: send AuditEvent logs to Log Analytics
3. Set retention to 90 days
4. Verify logs appear within 5 minutes

**Target:** Within 1 week

---

## Medium-Priority Items

### 1. Governance: Resource Tagging

**Checklist Item:** governance-required-tags  
**Source:** martinopedal/alz-checklist-queries@e7641beeda0126cc78825f8b77764c379552f3e1

**Finding:** 18 resources missing required tags: cost-center, environment, owner.

**Remediation Steps:**
1. Use Azure Policy (DeployIfNotExists): tag-missing-cost-center, tag-missing-environment
2. Bulk tag via Azure CLI: `az resource tag --resource-type "Microsoft.Compute/virtualMachines" ...`
3. Enforce tagging on new resources (Deny policy)

**Target:** Within 1 quarter (non-critical for handoff)

---

## Remediation Timeline

| Date Range | Item | Owner | Status |
|---|---|---|---|
| By 2026-05-17 (48h) | SQL public endpoint | DBA | In progress |
| By 2026-05-22 (1w) | App subnet NSG | Infrastructure | Scheduled |
| By 2026-05-22 (1w) | Key Vault diagnostics | Security | Scheduled |
| By 2026-05-29 (2w) | TLS 1.0/1.1 sunset | AppDev | Planned |
| By 2026-08-15 (3mo) | Resource tagging | FinOps | Backlog |

## Approval for Production Handoff

**Prerequisites:**
- [ ] SQL Database public endpoint disabled (Critical)
- [ ] App subnet NSG attached (High)
- [ ] Key Vault diagnostic settings enabled (High)
- [ ] TLS 1.0/1.1 deprecation plan documented (High)

**Verdict:** Recommend conditional handoff. Operations team acknowledges High-priority items and commits to remediation schedule. Block only if Critical items unresolved.

---

**Report Date:** 2026-05-15  
**Next Review:** 2026-06-15 (30 days)  
**Owner:** Infrastructure / Security team  
**Approved By:** {Lead}
```

## Confidence

**Low** (first capture). This distills ALZ checklist conformance patterns. Refinement pending: (1) feedback from real operator sessions using this skill, (2) ALZ checklist item stability as snapshot refreshes, (3) severity classification accuracy refined with real-world incident data.

## Related Skills

- **design-review** (#11): Surfaces proposed topology; this skill validates live infrastructure after deployment.
- **policy-as-code-suggest**: Translates ALZ gaps into Azure Policy remediations.

## Citations

- [Azure Landing Zone - Microsoft Learn](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/)
- [Azure Well-Architected Framework](https://learn.microsoft.com/azure/architecture/framework/)
- [ALZ Checklist - Cloud Adoption Framework](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/enterprise-scale/eslz-management-and-monitoring)
- ALZ Checklist and Graph Queries (vendored snapshot SHAs in `data/alz-queries/manifest.json`)
- [Azure Security Benchmark](https://learn.microsoft.com/security/benchmark/azure/)
- [NIST Cybersecurity Framework](https://learn.microsoft.com/compliance/regulatory/offering-nist-sp-800-53)
