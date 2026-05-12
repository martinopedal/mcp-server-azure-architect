# Skill: Ingress Migration Plan

## Overview

Guides an architect through migrating between Azure ingress platforms (App Gateway, Azure Front Door, Application Gateway for Containers, AGIC, NGINX-on-AKS) using a structured decision framework. Consumes ALZ Network pillar checklist queries to establish current state and target compliance bar.

## When to Use

- Current ingress is aging or misaligned with workload SLO (multi-region, sub-50ms latency, WAF posture).
- Evaluating AGIC deprecation path or migrating from open-source ingress (NGINX, Traefik) to managed services.
- Modernizing a hub-spoke network topology and need to assess ingress co-location (hub vs spoke).
- Need to surface TLS termination, WAF, DNS integration, AKS routing costs for a design review.

## Context

Azure ingress tooling has fragmented into overlapping generations:
- **App Gateway v1 (Classic):** WAF capable, HTTP only; sunset path documented.
- **App Gateway v2:** SKU-based, WAF v2, HTTP/HTTPS, multi-site routing.
- **Front Door Standard/Premium:** Global, multi-region, DDoS, WAF v3, rules engine.
- **AGIC:** AKS-native Ingress class, drives App Gateway config declaratively; deprecation path ongoing.
- **Application Gateway for Containers:** ALB-style, lightweight, Kubernetes-first, emerging.
- **NGINX-on-AKS:** Community, full control, operational burden (security patching, scaling).

An architect must reason about these trade-offs: latency SLA, regional footprint, security posture, cost, operational overhead.

## Inputs

The architect provides (as free-form or structured input):

1. **Current ingress topology:**
   - What platform(s) are in use today (App Gateway, ALB, NGINX, etc.).
   - How many instances, SKU, region(s), TLS mode.
   - Routing rules (host-based, path-based, regex).
   - WAF status (enabled, mode, custom rules).
   - Integration with DNS (Azure DNS, external).

2. **Target SLO:**
   - Latency percentile (p50, p99 in milliseconds).
   - Availability (% uptime, RTO/RPO if region fails).
   - Geographic footprint (single-region, multi-region, global).
   - DDoS/WAF posture (deny-all, allow-known, detect-log).

3. **Workload profile:**
   - Protocol mix (HTTP % vs HTTPS %).
   - Request rate (RPS).
   - Payload size (median, p99).
   - Multi-tenant or single-tenant.

## Process

1. **Surface current ingress state** (via `alz_query_by_id` on Network pillar: "ingress-topology-audit").
   - Query returns: ingress resource type, SKU, region, TLS cert rotation, WAF mode, backend health.

2. **Identify ALZ checklist gaps** (via `alz_query_by_id` on Network: "network-security-posture").
   - Checklist items: WAF enabled, TLS 1.2+, Azure DDoS Protection, Azure Private Link egress.
   - Classify each: compliant, missing, needs-upgrade.

3. **Evaluate platform fit against SLO.**
   - Build a decision matrix: platform vs (latency, regions, WAF, cost, AKS integration).
   - Example: "AGIC → App Gateway for Containers: lower latency in hub-spoke, AKS-native routing, cost reduction 30-40%."

4. **Map migration risks.**
   - **TLS cert rotation:** App Gateway can auto-renew from Key Vault; open-source ingress requires sidecar.
   - **Session affinity:** some platforms sticky by cookie, others by IP; application may rely on one.
   - **Rate limiting:** Front Door Rate Limiting differs from App Gateway rules; need to rewrite.
   - **Custom WAF rules:** cannot directly port between platforms; re-evaluate intent.

5. **Document prerequisites.**
   - Network: private endpoints, NSGs, service endpoints to be created.
   - DNS: CNAME/alias records to be updated.
   - Certificates: import, validate expiry, rotation plan.
   - Readiness: no pending workload updates during cutover.

6. **Suggest validation steps.**
   - Dry-run routing in canary region.
   - A/B test latency: old vs new platform against production traffic profile.
   - Validate WAF false-positive rate (% of legitimate requests blocked).
   - Smoke tests: health checks, TLS handshake, end-to-end transaction.

## Outputs

Structured migration plan document:

```
# Ingress Migration Plan: {workload} → {target platform}

## Current State
- Platform: {current}
- Instances: {count}, SKU: {sku}, Region(s): {regions}
- TLS: {mode}, Certs: {rotation method}
- WAF: {enabled/disabled}, Mode: {detect/prevent}
- Gaps: {list of ALZ checklist non-compliant items}

## Target State
- Platform: {target}
- SKU: {recommended}
- Regions: {planned}
- TLS: {managed via Key Vault, auto-renew}
- WAF: {enabled, mode: prevent}
- Compliance: {meets all Network pillar items}

## Delta
- Cost delta: {estimated monthly change}
- Latency delta: {p50, p99 improvement}
- Operational overhead: {manage from +X to -Y ops per quarter}

## Risks & Mitigations
1. [Risk]: [Mitigation]
2. [Risk]: [Mitigation]

## Prerequisites
- [ ] Network readiness (endpoints, NSGs)
- [ ] DNS staging
- [ ] Certificate import & validation
- [ ] No production changes during cutover

## Validation Plan
- Canary: {region/traffic %}
- A/B metrics: latency, error rate, WAF match rate
- Smoke tests: {list}
```

## Cross-Repo Contract: ALZ Vendoring

This skill consumes queries vendored from `martinopedal/alz-checklist-queries` (Network pillar, commit SHAs pinned in `data/alz-queries/checklist/manifest.json`).

When upstream contracts shift (e.g., new ingress pattern, new checklist item), refresh this skill:
- Run: `alz_query_by_id(checklist_id="network-security-posture")`
- Compare output to prior run.
- Update "Identify ALZ checklist gaps" step if item list changes.

## Worked Example

**Scenario:** Hub-spoke topology, currently on AGIC + App Gateway v1 (deprecated, WAF disabled), target is multi-region with AppGw for Containers.

```
## Current State
- Platform: AGIC → App Gateway v1
- Region: East US (single)
- TLS: Manual cert rotation (quarterly)
- WAF: Disabled
- Gaps: [WAF not enabled, TLS rotation not automated, no multi-region]

## Target State
- Platform: Application Gateway for Containers + Azure Front Door Standard
- Region: East US, West Europe (active-active)
- TLS: Key Vault managed, auto-renew
- WAF: Front Door WAF v3, managed rules
- Compliance: All Network items met

## Delta
- Cost: +15% (App Gateway for Containers + Front Door Premium → Standard)
- Latency: p50 -10ms (multi-region), p99 -50ms (caching)
- Ops: -20 hours/year (cert automation, no AGIC deprecation risk)

## Risks
1. [Risk] Existing AGIC Ingress manifests must be rewritten as Kubernetes Gateway API
   [Mitigation] Staged migration: run both 6 weeks, validate routing equivalence
2. [Risk] Front Door rate limiting differs from App Gateway throttle rules
   [Mitigation] Simulate load test; compare log patterns in canary

## Prerequisites
- [x] Spoke networks have private endpoint for App Gateway for Containers backend
- [x] DNS CNAME updated to Front Door endpoint in staging
- [ ] Certs imported to Key Vault with expiry validation
- [ ] Load test: 10k RPS simulated against new platform

## Validation
- Canary: 5% of US production traffic to new platform, 1 week
- Metrics: latency (AWS CloudWatch equivalent), error rate < 0.01%, WAF match rate <5% false positives
```

## Citations

- [Application Gateway for Containers - Microsoft Learn](https://learn.microsoft.com/azure/application-gateway/for-containers/)
- [Azure Application Gateway - Microsoft Learn](https://learn.microsoft.com/azure/application-gateway/)
- [Azure Front Door - Microsoft Learn](https://learn.microsoft.com/azure/frontdoor/)
- [Application Gateway Ingress Controller - Microsoft Learn](https://learn.microsoft.com/azure/application-gateway/ingress-controller-overview)
- [ALZ Network pillar - Azure Architecture Center](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/landing-zone/design-area-network-topology)
- ALZ vendored query: `martinopedal/alz-checklist-queries` (pinned commit in manifest.json)

## Confidence

**Low** (first capture). This is a distillation of known Azure ingress patterns, not a tested workflow yet. Refinement pending: (1) real-world migration logs from architect sessions, (2) ALZ Network checklist item stability.

## Related Skills

- **design-review** (#11): Surfaces current topology; feeds this skill's input.
- **alz-gap-check** (#12): Runs ALZ checklist queries; this skill consumes the output.
- **quota-plan** (future): Estimates instance counts and costs for target platform.
