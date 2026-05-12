# Skill: Policy-as-Code Suggestion

## Overview

Translates architectural intent and compliance requirements into Azure Policy definitions + Infrastructure-as-Code (Bicep/Terraform) manifestations. Bridges the gap between design review and governance implementation by surfacing built-in policies, evaluating custom patterns, and generating starter templates.

## When to Use

- Design review identifies governance gaps (no diagnostic settings, public access allowed, encryption missing, weak network isolation).
- Team needs to convert architectural intent into enforceable policy assignments.
- Compliance requirement arrives post-design (MCSB, NIST, sovereign data residency); need fast policy surface.
- Evaluating audit-vs-deny posture trade-off for a resource type.
- Preparing for production deployment: policy-as-guard-rails before workload provisioning.

## Context

Azure Policy offers 300+ built-in definitions and composable initiatives. Architects typically need a subset:
- **Deny policies** for hard boundaries (e.g., "no public storage").
- **Audit policies** for discovery and compliance scoring (e.g., "find unencrypted VMs").
- **DeployIfNotExists** for remediation (e.g., "add diagnostic settings if missing").

The challenge: translating "no public access to storage" into the right policy + assignment scope + exemption strategy + Infrastructure-as-Code snippet.

## Inputs

The architect provides (from prior design review or fresh analysis):

1. **Reviewed design:** list of resources (storage accounts, VMs, databases, networks) and intent.
   - Example: "All storage accounts must deny public access. All VMs must use managed disks. Databases encrypt with CMEK."

2. **Compliance bar:** regulatory context or internal standard.
   - Examples: "MCSB (Microsoft Cloud Security Benchmark)", "NIST 800-53", "PCI-DSS", "sovereign data residency (EU-only)".

3. **Preferred PaC stack:** Bicep or Terraform (or both).

4. **Scope & exemptions:** which subscriptions/resource groups, which resources exempt (if any).

## Process

1. **Map design components to ALZ policy initiatives.**
   - Run: `alz_query_by_id(checklist_id="policy-pillar-governance")` to retrieve recommended initiative IDs.
   - Retrieve: built-in initiative summaries (e.g., "Azure Security Benchmark v3", "Regulatory Compliance" initiatives).
   - Cross-reference design intent against each initiative; flag high-confidence matches.

2. **Identify gaps (compliant / missing / needs-customization).**
   - For each design component, ask: "Is there a built-in policy, or do I need custom?"
   - Classify:
     - **Compliant:** built-in policy exists, intent matches, use as-is.
     - **Missing:** no built-in matches; custom policy needed.
     - **Needs-customization:** built-in exists, but scope/parameters don't match; adapt.

3. **For each gap, suggest Azure Policy definition + assignment.**
   - Retrieve built-in policy ID from Microsoft Learn.
   - Document: policy name, description, effect (Deny/Audit/DeployIfNotExists/Modify), parameters, scope.
   - Evaluate audit-vs-deny trade-off (see below).

4. **Audit vs. Deny Posture Decision Tree.**
   - **Audit (default starting point):**
     - Use for discovery: "What resources violate this?" (no enforcement).
     - Recommended for: workload migrations, new compliance requirements, teams unfamiliar with policies.
     - Transition plan: run 4 weeks in audit mode, measure non-compliance %, then shift to deny after workload remediation.
   - **Deny (hard boundary):**
     - Use for: production security bars (e.g., "all storage public access denied").
     - Risk: may break deployments if exemptions insufficient; requires change-control process.
     - Transition: use effect: "Deny" for high-confidence items (storage public access), audit for experimental policies.

5. **Generate Infrastructure-as-Code snippets.**
   - **Bicep:** `Microsoft.Authorization/policyAssignments` + `Microsoft.Authorization/roleAssignments` (for DeployIfNotExists remediation).
   - **Terraform:** `azurerm_policy_assignment` + `azurerm_management_lock` (for enforcement).
   - Provide minimal stubs; architect fills in parameters and scope.

6. **Document exemption strategy.**
   - When are exclusions allowed? (e.g., "HIPAA workloads in spoke-02 exempt from public storage deny").
   - How to request: policy exception review board, justification template, TTL on exemption.

## Outputs

Structured policy recommendation list:

```
# Policy Recommendations: {design name}

## Compliance Bar: {MCSB / NIST / Custom}

### Gap 1: Storage Account Public Access
- **Intent:** No storage account may allow public blob access.
- **Status:** Missing built-in (recommend custom or use MCSB v3 initiative).
- **Built-in Policy ID:** Storage.Deny.PublicAccess
- **Scope:** Subscription {subId}, Resource Group {rg}
- **Effect:** Deny (hard boundary; recommended for production)
- **Parameters:** None
- **Exceptions:** None initially; file exception request if pilot needed.

### Gap 2: Diagnostic Settings to Log Analytics
- **Intent:** All resources must log to Log Analytics workspace {wsId}.
- **Status:** Partial (MCSB includes audit trigger; use DeployIfNotExists).
- **Built-in Policy ID:** Deploy.Diagnostic.Settings.LogAnalytics
- **Scope:** Subscription {subId}
- **Effect:** DeployIfNotExists (creates diagnostic settings if missing)
- **Parameters:** logAnalyticsWorkspaceId={wsId}
- **Remediation:** Manual: Scope + Resource Group. Auto: role assignment required (see IaC).

## Bicep Snippets

### Gap 1: Storage Public Access Deny
\`\`\`bicep
resource policyAssignment 'Microsoft.Authorization/policyAssignments@2023-04-01' = {
  name: 'storage-public-access-deny'
  location: resourceGroup().location
  properties: {
    policyDefinitionId: '/subscriptions/${subscription().subscriptionId}/providers/Microsoft.Authorization/policyDefinitions/storagePublicAccessDeny'
    scope: resourceGroup().id
    parameters: {}
    enforcementMode: 'Default' // or 'DoNotEnforce' for audit mode
    description: 'Deny public access to storage accounts per MCSB v3'
    displayName: 'Storage Account Public Access Denied'
  }
}
\`\`\`

### Gap 2: Diagnostic Settings (DeployIfNotExists)
\`\`\`bicep
resource policyAssignment 'Microsoft.Authorization/policyAssignments@2023-04-01' = {
  name: 'deploy-diagnostic-settings'
  location: resourceGroup().location
  properties: {
    policyDefinitionId: '/subscriptions/${subscription().subscriptionId}/providers/Microsoft.Authorization/policyDefinitions/deployDiagnosticSettings'
    scope: subscription().id
    parameters: {
      logAnalyticsWorkspaceId: {
        value: '/subscriptions/${subscription().subscriptionId}/resourceGroups/shared-svc/providers/Microsoft.OperationalInsights/workspaces/central-logs'
      }
    }
    enforcementMode: 'Default'
    description: 'Deploy diagnostic settings to Log Analytics for all resources'
    displayName: 'Deploy Diagnostic Settings'
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// For DeployIfNotExists, grant role assignment for remediation
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(subscription().id, policyAssignment.name, 'Contributor')
  properties: {
    roleDefinitionId: '/subscriptions/${subscription().subscriptionId}/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c'
    principalId: policyAssignment.identity.principalId
    principalType: 'ServicePrincipal'
  }
}
\`\`\`

## Terraform Snippets

### Gap 1: Storage Public Access Deny
\`\`\`hcl
resource "azurerm_policy_assignment" "storage_public_access_deny" {
  name                = "storage-public-access-deny"
  scope               = azurerm_resource_group.example.id
  policy_definition_id = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/providers/Microsoft.Authorization/policyDefinitions/storagePublicAccessDeny"
  
  description = "Deny public access to storage accounts per MCSB v3"
  display_name = "Storage Account Public Access Denied"
  
  enforcement_mode = "Default" # or "DoNotEnforce" for audit
}
\`\`\`

### Gap 2: Diagnostic Settings (DeployIfNotExists)
\`\`\`hcl
resource "azurerm_policy_assignment" "deploy_diagnostic_settings" {
  name                = "deploy-diagnostic-settings"
  scope               = data.azurerm_client_config.current.subscription_id
  policy_definition_id = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/providers/Microsoft.Authorization/policyDefinitions/deployDiagnosticSettings"
  
  description = "Deploy diagnostic settings to Log Analytics for all resources"
  display_name = "Deploy Diagnostic Settings"
  
  parameters = jsonencode({
    logAnalyticsWorkspaceId = {
      value = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/shared-svc/providers/Microsoft.OperationalInsights/workspaces/central-logs"
    }
  })

  enforcement_mode = "Default"
  
  identity {
    type = "SystemAssigned"
  }
}

# For DeployIfNotExists, grant role assignment for remediation
resource "azurerm_role_assignment" "policy_remediation" {
  scope              = data.azurerm_client_config.current.subscription_id
  role_definition_name = "Contributor"
  principal_id       = azurerm_policy_assignment.deploy_diagnostic_settings.identity[0].principal_id
}
\`\`\`

## Exemption Policy Template

When requesting exemptions:
```
Resource: {storage-account-id}
Policy: Storage Public Access Deny
Justification: Test/dev environment; data is non-sensitive.
Duration: 30 days (until production cutover).
Approver: {security-team}.
```

## Confidence

**Low** (first capture). Based on ALZ policy library and known governance patterns. Refinement pending: (1) tested feedback from architects adopting this skill, (2) ALZ Policy pillar query stability, (3) real exemption workflows.

## Related Skills

- **design-review** (#11): Surfaces governance gaps; feeds this skill's input.
- **alz-gap-check** (#12): Runs ALZ checklist queries; can extract Policy pillar items.

## Citations

- [Azure Policy - Microsoft Learn](https://learn.microsoft.com/azure/governance/policy/)
- [Azure Policy Built-in Definitions - Microsoft Learn](https://learn.microsoft.com/azure/governance/policy/samples/built-in-policies)
- [Microsoft Cloud Security Benchmark - Microsoft Learn](https://learn.microsoft.com/security/benchmark/azure/)
- [Bicep Policy Definitions - Microsoft Learn](https://learn.microsoft.com/azure/azure-resource-manager/bicep/deployment-template-structure)
- [AzureRM Terraform Provider Policy Resources](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/policy_assignment)
- ALZ Policy Pillar: `martinopedal/alz-checklist-queries` (Network + Security pillars; pinned commit in manifest.json)
