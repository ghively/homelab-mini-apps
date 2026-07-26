"""Tests for health and readiness contracts.

Tests verify:
- /healthz returns process liveness only
- /readyz fails closed on missing mandatory config
- Readiness checks validate auth config, registry, audit store
"""

import pytest
import os
from unittest.mock import patch, Mock
from fastapi import HTTPException
from app.core.health import (
    HealthStatus,
    ReadinessStatus,
    ComponentHealth,
    HealthResponse,
    ReadinessCheck,
    ReadinessResponse,
    check_mandatory_config,
    check_registry_loaded,
    check_audit_store_available,
    check_auth_config,
    perform_readiness_checks,
    perform_health_checks,
    MANDATORY_CONFIG_KEYS,
)


class TestHealthStatus:
    """Test health status enum values."""

    def test_health_status_values(self):
        """Test health status values."""
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.DEGRADED == "degraded"


class TestReadinessStatus:
    """Test readiness status enum values."""

    def test_readiness_status_values(self):
        """Test readiness status values."""
        assert ReadinessStatus.READY == "ready"
        assert ReadinessStatus.NOT_READY == "not_ready"


class TestComponentHealth:
    """Test component health model."""

    def test_component_health_creation(self):
        """Test creating a component health check."""
        health = ComponentHealth(
            name="test-component",
            status=HealthStatus.HEALTHY,
            message="Component is healthy",
        )

        assert health.name == "test-component"
        assert health.status == HealthStatus.HEALTHY
        assert health.message == "Component is healthy"


class TestHealthResponse:
    """Test health response model."""

    def test_health_response_creation(self):
        """Test creating a health response."""
        response = HealthResponse(
            status=HealthStatus.HEALTHY,
            components=[
                ComponentHealth(
                    name="process",
                    status=HealthStatus.HEALTHY,
                    message="Process running",
                )
            ],
        )

        assert response.status == HealthStatus.HEALTHY
        assert len(response.components) == 1
        assert response.components[0].name == "process"


class TestReadinessCheck:
    """Test readiness check model."""

    def test_readiness_check_creation(self):
        """Test creating a readiness check."""
        check = ReadinessCheck(
            name="test-check",
            status=ReadinessStatus.READY,
            message="Check passed",
            is_mandatory=True,
        )

        assert check.name == "test-check"
        assert check.status == ReadinessStatus.READY
        assert check.is_mandatory is True


class TestReadinessResponse:
    """Test readiness response model."""

    def test_readiness_response_creation(self):
        """Test creating a readiness response."""
        response = ReadinessResponse(
            status=ReadinessStatus.READY,
            checks=[
                ReadinessCheck(
                    name="config-check",
                    status=ReadinessStatus.READY,
                    message="Config OK",
                    is_mandatory=True,
                )
            ],
        )

        assert response.status == ReadinessStatus.READY
        assert len(response.checks) == 1


class TestCheckMandatoryConfig:
    """Test mandatory configuration check."""

    def test_mandatory_config_missing(self):
        """Test that missing mandatory config raises exception."""
        # Clear environment
        for key in MANDATORY_CONFIG_KEYS:
            os.environ.pop(key, None)

        with pytest.raises(HTTPException) as exc_info:
            check_mandatory_config()

        assert exc_info.value.status_code == 503
        assert "Missing mandatory configuration" in str(exc_info.value.detail)

    def test_mandatory_config_present(self):
        """Test that present mandatory config passes."""
        # Set environment
        for key in MANDATORY_CONFIG_KEYS:
            os.environ[key] = "test-value"

        # Should not raise
        message = check_mandatory_config()

        assert "mandatory keys present" in message

        # Cleanup
        for key in MANDATORY_CONFIG_KEYS:
            os.environ.pop(key, None)

    def test_mandatory_config_partial(self):
        """Test that partial mandatory config fails."""
        # Set only some keys
        os.environ[MANDATORY_CONFIG_KEYS[0]] = "test-value"

        with pytest.raises(HTTPException) as exc_info:
            check_mandatory_config()

        assert exc_info.value.status_code == 503

        # Cleanup
        os.environ.pop(MANDATORY_CONFIG_KEYS[0], None)


class TestCheckAuthConfig:
    """Test auth configuration check."""

    def test_auth_config_missing_bot_token(self):
        """Test that missing bot token fails."""
        with patch('app.core.config.BOT_TOKEN', ''):
            with pytest.raises(HTTPException) as exc_info:
                check_auth_config()

            assert exc_info.value.status_code == 503
            assert "TELEGRAM_BOT_TOKEN not configured" in str(exc_info.value.detail)

    def test_auth_config_missing_allowed_users(self):
        """Test that missing allowed users fails."""
        with patch('app.core.config.BOT_TOKEN', 'test-token'):
            with patch('app.core.config.ALLOWED_USER_IDS', []):
                with pytest.raises(HTTPException) as exc_info:
                    check_auth_config()

                assert exc_info.value.status_code == 503
                assert "MINIAPPS_ALLOWED_USERS not configured" in str(exc_info.value.detail)

    def test_auth_config_missing_owner(self):
        """Test that missing owner ID fails."""
        with patch('app.core.config.BOT_TOKEN', 'test-token'):
            with patch('app.core.config.ALLOWED_USER_IDS', [9999999999]):
                with pytest.raises(HTTPException) as exc_info:
                    check_auth_config()

                assert exc_info.value.status_code == 503
                assert "Owner identity 8971338885 not in ALLOWED_USER_IDS" in str(exc_info.value.detail)

    def test_auth_config_valid(self):
        """Test that valid auth config passes."""
        with patch('app.core.config.BOT_TOKEN', 'test-token'):
            with patch('app.core.config.ALLOWED_USER_IDS', [8971338885]):
                # Should not raise
                message = check_auth_config()

                assert "Auth configured" in message


class TestCheckRegistryLoaded:
    """Test registry loaded check."""

    def test_registry_loaded(self):
        """Test that registry check passes."""
        # Should not raise
        message = check_registry_loaded()

        assert "Registry loaded" in message


class TestCheckAuditStoreAvailable:
    """Test audit store available check."""

    def test_audit_store_available(self):
        """Test that audit store check passes."""
        # Should not raise
        message = check_audit_store_available()

        assert "Audit store available" in message


class TestPerformReadinessChecks:
    """Test readiness check execution."""

    def test_readiness_checks_all_pass(self):
        """Test that readiness checks pass when all configured."""
        with patch('app.core.health.check_mandatory_config', return_value="Config OK"):
            with patch('app.core.health.check_auth_config', return_value="Auth OK"):
                with patch('app.core.health.check_registry_loaded', return_value="Registry OK"):
                    with patch('app.core.health.check_audit_store_available', return_value="Audit OK"):
                        result = perform_readiness_checks()

                        assert result.status == ReadinessStatus.READY
                        assert len(result.checks) == 4
                        for check in result.checks:
                            assert check.status == ReadinessStatus.READY

    def test_readiness_checks_mandatory_fail(self):
        """Test that readiness fails when mandatory check fails."""
        with patch('app.core.health.check_mandatory_config', side_effect=HTTPException(503, "Config missing")):
            with patch('app.core.health.check_auth_config', return_value="Auth OK"):
                with patch('app.core.health.check_registry_loaded', return_value="Registry OK"):
                    with patch('app.core.health.check_audit_store_available', return_value="Audit OK"):
                        result = perform_readiness_checks()

                        assert result.status == ReadinessStatus.NOT_READY
                        # At least one check should be NOT_READY
                        not_ready_checks = [c for c in result.checks if c.status == ReadinessStatus.NOT_READY]
                        assert len(not_ready_checks) >= 1


class TestPerformHealthChecks:
    """Test health check execution."""

    def test_health_checks_pass(self):
        """Test that health checks pass."""
        result = perform_health_checks()

        assert result.status == HealthStatus.HEALTHY
        assert len(result.components) >= 1
        assert result.components[0].name == "process"


class TestMandatoryConfigKeys:
    """Test mandatory config keys definition."""

    def test_mandatory_config_keys_defined(self):
        """Test that mandatory config keys are defined."""
        assert len(MANDATORY_CONFIG_KEYS) > 0
        assert "TELEGRAM_BOT_TOKEN" in MANDATORY_CONFIG_KEYS
        assert "MINIAPPS_ALLOWED_USERS" in MANDATORY_CONFIG_KEYS


class TestFailClosedReadiness:
    """Test fail-closed behavior for readiness."""

    def test_readiness_fail_closed_on_missing_config(self):
        """Test that readiness fails closed when mandatory config is missing."""
        # Clear environment
        original_env = {}
        for key in MANDATORY_CONFIG_KEYS:
            original_env[key] = os.environ.get(key)
            os.environ.pop(key, None)

        try:
            result = perform_readiness_checks()

            assert result.status == ReadinessStatus.NOT_READY
            # Check that mandatory config check failed
            config_check = next((c for c in result.checks if c.name == "mandatory_config"), None)
            assert config_check is not None
            assert config_check.status == ReadinessStatus.NOT_READY

        finally:
            # Restore environment
            for key, value in original_env.items():
                if value is not None:
                    os.environ[key] = value
                else:
                    os.environ.pop(key, None)