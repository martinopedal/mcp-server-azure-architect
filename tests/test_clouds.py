"""Unit tests for Azure cloud configuration module."""

from __future__ import annotations

import pytest

from mcp_server_azure_architect._clouds import CloudConfig, get_cloud_config


class TestCloudConfig:
    """Test CloudConfig dataclass."""

    def test_cloud_config_immutable(self) -> None:
        """CloudConfig instances should be frozen (immutable)."""
        config = CloudConfig(
            name="Test",
            arm_endpoint="https://test.com",
            arm_scope="https://test.com/.default",
        )
        with pytest.raises(AttributeError):
            config.name = "Modified"  # type: ignore[misc]

    def test_cloud_config_attributes(self) -> None:
        """CloudConfig should expose name, arm_endpoint, and arm_scope."""
        config = CloudConfig(
            name="AzureCloud",
            arm_endpoint="https://management.azure.com",
            arm_scope="https://management.azure.com/.default",
        )
        assert config.name == "AzureCloud"
        assert config.arm_endpoint == "https://management.azure.com"
        assert config.arm_scope == "https://management.azure.com/.default"


class TestGetCloudConfig:
    """Test get_cloud_config function."""

    def test_default_is_azure_cloud(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When AZURE_CLOUD_NAME is unset, should default to AzureCloud."""
        monkeypatch.delenv("AZURE_CLOUD_NAME", raising=False)
        config = get_cloud_config()
        assert config.name == "AzureCloud"
        assert config.arm_endpoint == "https://management.azure.com"
        assert config.arm_scope == "https://management.azure.com/.default"

    def test_azure_us_government(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AzureUSGovernment should map to usgovcloudapi.net."""
        monkeypatch.setenv("AZURE_CLOUD_NAME", "AzureUSGovernment")
        config = get_cloud_config()
        assert config.name == "AzureUSGovernment"
        assert config.arm_endpoint == "https://management.usgovcloudapi.net"
        assert config.arm_scope == "https://management.usgovcloudapi.net/.default"

    def test_azure_china_cloud(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AzureChinaCloud should map to chinacloudapi.cn."""
        monkeypatch.setenv("AZURE_CLOUD_NAME", "AzureChinaCloud")
        config = get_cloud_config()
        assert config.name == "AzureChinaCloud"
        assert config.arm_endpoint == "https://management.chinacloudapi.cn"
        assert config.arm_scope == "https://management.chinacloudapi.cn/.default"

    def test_azure_german_cloud(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AzureGermanCloud should map to microsoftazure.de (deprecated but supported)."""
        monkeypatch.setenv("AZURE_CLOUD_NAME", "AzureGermanCloud")
        config = get_cloud_config()
        assert config.name == "AzureGermanCloud"
        assert config.arm_endpoint == "https://management.microsoftazure.de"
        assert config.arm_scope == "https://management.microsoftazure.de/.default"

    def test_unknown_cloud_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Unknown AZURE_CLOUD_NAME should raise ValueError with valid options."""
        monkeypatch.setenv("AZURE_CLOUD_NAME", "InvalidCloud")
        with pytest.raises(ValueError, match="Unknown AZURE_CLOUD_NAME 'InvalidCloud'"):
            get_cloud_config()

    def test_unknown_cloud_error_includes_valid_values(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Error message should list all valid cloud names."""
        monkeypatch.setenv("AZURE_CLOUD_NAME", "FakeCloud")
        with pytest.raises(ValueError) as exc_info:
            get_cloud_config()

        error_msg = str(exc_info.value)
        assert "AzureCloud" in error_msg
        assert "AzureUSGovernment" in error_msg
        assert "AzureChinaCloud" in error_msg
        assert "AzureGermanCloud" in error_msg

    def test_case_sensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cloud names should be case-sensitive (lowercase azurecloud should fail)."""
        monkeypatch.setenv("AZURE_CLOUD_NAME", "azurecloud")
        with pytest.raises(ValueError, match="Unknown AZURE_CLOUD_NAME 'azurecloud'"):
            get_cloud_config()
