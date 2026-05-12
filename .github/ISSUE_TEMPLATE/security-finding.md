---
name: Security finding
description: Report a security vulnerability
title: "security: "
labels: ["security", "squad", "squad:sentinel"]
---

## Threat description

<!-- What is the security vulnerability or attack vector? Be specific. -->

## Impact

<!-- What could be compromised if this vulnerability is exploited?

Select all that apply:
- [ ] Data confidentiality (unauthorized access to Azure or tool output)
- [ ] Data integrity (unauthorized modification of Azure resources or tool behavior)
- [ ] Availability (denial of service or resource exhaustion)
- [ ] Authentication/authorization (confused-deputy, privilege escalation) -->

## Reproduction or evidence

<!-- Steps to reproduce the vulnerability, or evidence (log snippets, code references, CVE links, etc.).

IMPORTANT: If an active exploit exists, do NOT post proof-of-concept code or detailed exploitation steps in this public issue. Use the private security advisory channel instead. See Disclosure policy below. -->

## Suggested mitigation

<!-- What are the recommended steps to fix or reduce the risk? -->

## Disclosure policy

**For sensitive findings with active exploits:** Use the [private security advisory channel](https://github.com/martinopedal/mcp-server-azure-architect/security/advisories/new) instead of this public issue. See [SECURITY.md](https://github.com/martinopedal/mcp-server-azure-architect/blob/main/SECURITY.md) for responsible disclosure guidelines.

**This public issue assumes the finding is either:**
- Not actively exploitable, or
- A general hardening recommendation with no immediate exploit path
