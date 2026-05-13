"""Azure cloud environment configuration for sovereign cloud support.

This module provides cloud-specific endpoint and credential scope mappings
for Azure Resource Manager across public and sovereign clouds.

Environment variable:
    AZURE_CLOUD_NAME: Cloud environment name (AzureCloud, AzureUSGovernment,
                      AzureChinaCloud, AzureGermanCloud).
                      Defaults to AzureCloud if unset.

References:
    - https://learn.microsoft.com/azure/azure-government/compare-azure-government-global-azure
    - https://learn.microsoft.com/azure/china/resources-developer-guide
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CloudConfig:
    """Azure cloud configuration with ARM endpoint and credential scope.

    Attributes:
        name: Cloud environment name (e.g., "AzureCloud")
        arm_endpoint: Azure Resource Manager endpoint URL
        arm_scope: OAuth2 scope for ARM authentication
    """

    name: str
    arm_endpoint: str
    arm_scope: str


_CLOUD_MAP: dict[str, CloudConfig] = {
    "AzureCloud": CloudConfig(
        name="AzureCloud",
        arm_endpoint="https://management.azure.com",
        arm_scope="https://management.azure.com/.default",
    ),
    "AzureUSGovernment": CloudConfig(
        name="AzureUSGovernment",
        arm_endpoint="https://management.usgovcloudapi.net",
        arm_scope="https://management.usgovcloudapi.net/.default",
    ),
    "AzureChinaCloud": CloudConfig(
        name="AzureChinaCloud",
        arm_endpoint="https://management.chinacloudapi.cn",
        arm_scope="https://management.chinacloudapi.cn/.default",
    ),
    "AzureGermanCloud": CloudConfig(
        name="AzureGermanCloud",
        arm_endpoint="https://management.microsoftazure.de",
        arm_scope="https://management.microsoftazure.de/.default",
    ),
}


def get_cloud_config() -> CloudConfig:
    """Get cloud configuration from AZURE_CLOUD_NAME environment variable.

    Returns:
        CloudConfig for the specified cloud (defaults to AzureCloud).

    Raises:
        ValueError: If AZURE_CLOUD_NAME is set to an unknown cloud name.
    """
    cloud_name = os.environ.get("AZURE_CLOUD_NAME", "AzureCloud")

    if cloud_name not in _CLOUD_MAP:
        valid_clouds = ", ".join(_CLOUD_MAP.keys())
        raise ValueError(f"Unknown AZURE_CLOUD_NAME '{cloud_name}'. Valid values: {valid_clouds}")

    return _CLOUD_MAP[cloud_name]
