# terraform: Terraform Registry Lookup and Validation

## Purpose

Provides Terraform registry lookups, plan generation, and configuration validation. Architects use this to research Terraform modules and providers, validate IaC syntax, and review Terraform plans during infrastructure-as-code design reviews. Complements azure-mcp by enabling IaC validation and design reviews before deployment.

## Source

Repository: [hashicorp/terraform-mcp-server](https://github.com/hashicorp/terraform-mcp-server)  
Maintainer: HashiCorp (ALLOWED-VENDOR)

## Distribution

Installed via Docker:

```
docker run -i --rm hashicorp/terraform-mcp-server:v0.5.1
```

Configured in `.copilot/mcp-config.json` with Docker container transport.

## Auth Model

Terraform credentials (API tokens for Terraform Cloud, private registry auth) are read from:

- `~/.terraformrc` file
- `TF_TOKEN_*` environment variables
- Terraform Cloud credentials stored locally

No hardcoded tokens in config. Follows standard Terraform credential chain.

## Network Egress

Connects to:

- `https://registry.terraform.io` (official Terraform registry)
- `https://app.terraform.io` (Terraform Cloud, if using remote state or runs)
- Private registries (if configured in terraformrc)
- GitHub, GitLab, or other source control systems (if resolving module sources)

Requires internet access to Terraform registry and potentially private registries.

## Read-Only Posture

**Read-only by design.** Only provides `terraform plan` and `terraform validate` operations.

Examples of read-only operations:
- List available modules and providers
- Validate Terraform configuration syntax
- Generate and review terraform plans
- Query registry metadata

**Not exposed:** `terraform apply` is explicitly not available. No mutations to cloud infrastructure. Write operations are blocked.

## Supply Chain Notes

**Version pinned:** v0.5.1 (semver release)

**Provenance:** Published by HashiCorp to Docker Hub and GHCR. Docker images are signed via Docker Content Trust (DCT). Official HashiCorp product.

**CVE status:** HashiCorp maintains the terraform-mcp-server as part of their official tooling. Security updates are published when available. Depends on Terraform CLI (actively maintained by HashiCorp). No known CVEs specific to terraform-mcp-server as of 2026-05-12.

**Release cadence:** HashiCorp publishes semver releases. Last release 2026-Q1. Active maintenance with regular security updates.

**Maintenance signal:** HashiCorp (ALLOWED-VENDOR) maintains. Terraform ecosystem is stable and widely adopted.

## ADR-004 Fit

- ✅ **Criterion 1 (Stable Upstream):** YES. Semver releases with release notes.
- ✅ **Criterion 2 (Signed Releases):** YES. Docker images signed via DCT. Official HashiCorp product.
- ✅ **Criterion 3 (Narrow Scope):** YES. Terraform tooling only (plan, validate, registry lookup).
- ✅ **Criterion 4 (Complementary to azure-mcp):** YES. IaC design is orthogonal to live resource queries. (Terraform can manage Azure, but this server only exposes read-only operations.)
- ✅ **Criterion 5 (Maintenance Signal):** YES. HashiCorp maintains; last release 2026-Q1.
- ✅ **Criterion 6 (Read-Only):** YES. Plan and validate only; no apply.
- ✅ **Criterion 7 (Documented Install):** YES. Documented in `docs/install/` with Docker setup.

## Removal Cost

If terraform is uninstalled:

- Architects lose the ability to validate Terraform configurations and review plans within design reviews.
- Design-review skill loses IaC validation capability.
- Architects must run terraform validate and terraform plan manually from the command line.

**Risk:** Low-Medium. Design work continues with manual terraform CLI, but conversation flow is interrupted.

## References

- [hashicorp/terraform-mcp-server](https://github.com/hashicorp/terraform-mcp-server)
- [Terraform Registry](https://registry.terraform.io)
- [Terraform Security Release Process](https://www.hashicorp.com/security)
- `.copilot/mcp-config.json` (pinned version)
- `docs/install/` (per-client setup)

## TODO: Deeper Supply Chain Review

- Verify Docker image signature using cosign and HashiCorp's public key.
- Test terraform plan generation with sample Azure Terraform code.
- Confirm read-only configuration prevents terraform apply from being callable.
- Monitor HashiCorp security advisories quarterly.
