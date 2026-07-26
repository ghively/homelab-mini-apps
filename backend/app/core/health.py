"""Health and readiness contracts.

- /healthz: unauthenticated process liveness only; no dependency or secret metadata
- /readyz: internal/IaC use; non-200 unless mandatory auth config, registry,
  audit store, and configured mandatory adapters initialize
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import HTTPException
from enum import Enum


class HealthStatus(str, Enum):
    """Health status values."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ReadinessStatus(str, Enum):
    """Readiness status values."""

    READY = "ready"
    NOT_READY = "not_ready"


class ComponentHealth(BaseModel):
    """Health status of a single component."""

    name: str = Field(..., description="Component name")
    status: HealthStatus = Field(..., description="Component health status")
    message: Optional[str] = Field(None, description="Health check message")
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    """Health check response."""

    status: HealthStatus = Field(..., description="Overall health status")
    components: list[ComponentHealth] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class ReadinessCheck(BaseModel):
    """Single readiness check."""

    name: str = Field(..., description="Check name")
    status: ReadinessStatus = Field(..., description="Check status")
    message: Optional[str] = Field(None, description="Check message")
    is_mandatory: bool = Field(
        default=True,
        description="Whether this check is mandatory (failure means not ready)",
    )


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: ReadinessStatus = Field(..., description="Overall readiness status")
    checks: list[ReadinessCheck] = Field(default_factory=list)
    checked_at: datetime = Field(default_factory=datetime.utcnow)


# Mandatory configuration checks
MANDATORY_CONFIG_KEYS = [
    "TELEGRAM_BOT_TOKEN",
    "MINIAPPS_ALLOWED_USERS",
]


def check_component_health(component_name: str, check_func) -> ComponentHealth:
    """Check health of a single component.

    Args:
        component_name: Name of the component
        check_func: Function that performs the health check

    Returns:
        ComponentHealth result
    """
    try:
        message = check_func()
        return ComponentHealth(
            name=component_name,
            status=HealthStatus.HEALTHY,
            message=message,
        )
    except Exception as e:
        return ComponentHealth(
            name=component_name,
            status=HealthStatus.UNHEALTHY,
            message=str(e),
        )


def check_readiness(
    checks: list[tuple[str, callable, bool]],
) -> ReadinessResponse:
    """Perform readiness checks.

    Args:
        checks: List of (name, check_func, is_mandatory) tuples

    Returns:
        ReadinessResponse with overall status
    """
    readiness_checks = []
    all_mandatory_passed = True

    for name, check_func, is_mandatory in checks:
        try:
            message = check_func()
            status = ReadinessStatus.READY
        except Exception as e:
            message = str(e)
            status = ReadinessStatus.NOT_READY
            if is_mandatory:
                all_mandatory_passed = False

        readiness_checks.append(
            ReadinessCheck(
                name=name,
                status=status,
                message=message,
                is_mandatory=is_mandatory,
            )
        )

    overall_status = ReadinessStatus.READY if all_mandatory_passed else ReadinessStatus.NOT_READY

    return ReadinessResponse(
        status=overall_status,
        checks=readiness_checks,
    )


# Check functions for specific components

def check_mandatory_config() -> str:
    """Check that all mandatory configuration keys are present."""
    import os

    missing = []
    for key in MANDATORY_CONFIG_KEYS:
        value = os.environ.get(key)
        if not value:
            missing.append(key)

    if missing:
        raise HTTPException(
            503,
            f"Missing mandatory configuration: {', '.join(missing)}",
        )

    return f"All {len(MANDATORY_CONFIG_KEYS)} mandatory keys present"


def check_registry_loaded() -> str:
    """Check that app registry is loaded."""
    from .registry import APP_REGISTRY

    # Registry can be empty but must be accessible
    return f"Registry loaded ({len(APP_REGISTRY)} apps)"


def check_audit_store_available() -> str:
    """Check that audit store is available."""
    from .audit import audit_store

    # Audit store should be initialized
    return "Audit store available"


def check_auth_config() -> str:
    """Check that authentication is configured."""
    from .config import BOT_TOKEN, ALLOWED_USER_IDS

    if not BOT_TOKEN:
        raise HTTPException(503, "TELEGRAM_BOT_TOKEN not configured")

    if not ALLOWED_USER_IDS:
        raise HTTPException(503, "MINIAPPS_ALLOWED_USERS not configured")

    if 8971338885 not in ALLOWED_USER_IDS:
        raise HTTPException(
            503,
            "Owner identity 8971338885 not in ALLOWED_USER_IDS",
        )

    return f"Auth configured for {len(ALLOWED_USER_IDS)} users"


def perform_readiness_checks() -> ReadinessResponse:
    """Perform all readiness checks.

    Returns:
        ReadinessResponse with overall status
    """
    checks = [
        ("mandatory_config", check_mandatory_config, True),
        ("auth_config", check_auth_config, True),
        ("registry_loaded", check_registry_loaded, True),
        ("audit_store_available", check_audit_store_available, True),
    ]

    return check_readiness(checks)


def perform_health_checks() -> HealthResponse:
    """Perform all health checks.

    Returns:
        HealthResponse with overall status
    """
    # Basic health check - just confirm process is running
    return HealthResponse(
        status=HealthStatus.HEALTHY,
        components=[
            ComponentHealth(
                name="process",
                status=HealthStatus.HEALTHY,
                message="Process running",
            ),
        ],
    )


# FastAPI response constructors

def health_response() -> HealthResponse:
    """Get health response for /healthz endpoint."""
    return perform_health_checks()


def readiness_response() -> ReadinessResponse:
    """Get readiness response for /readyz endpoint."""
    return perform_readiness_checks()