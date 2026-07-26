"""App registry with fail-closed routing.

Unknown, disabled, malformed, or unauthorized app IDs return 404
to avoid existence disclosure.
"""

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class AppStatus(str, Enum):
    """App status values."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    DEFERRED = "deferred"


class AppCapability(str, Enum):
    """App capability values."""

    READ_ONLY = "read-only"
    GUARDED_WRITE = "guarded-write"


class AppRegistryEntry(BaseModel):
    """App registry entry."""

    id: str = Field(..., description="App identifier (e.g., 'swarm-monitor')")
    title: str = Field(..., description="Human-readable title")
    owner: str = Field(..., description="Owner profile or team")
    status: AppStatus = Field(..., description="App status")
    route: str = Field(..., description="API route (e.g., '/apps/swarm-monitor')")
    startapp: str = Field(..., description="Telegram startapp parameter")
    required_roles: list[str] = Field(
        default_factory=list,
        description="Roles required to access this app",
    )
    capability: AppCapability = Field(..., description="App capability")
    min_client_version: str = Field(
        default="1.0.0",
        description="Minimum client version",
    )
    required_features: list[str] = Field(
        default_factory=list,
        description="Required Telegram Mini App features",
    )
    data_contract_version: str = Field(
        default="1",
        description="Data contract version",
    )
    documentation_url: Optional[str] = Field(
        None,
        description="Approved documentation URL",
    )


# App registry (initially empty - apps are added explicitly)
APP_REGISTRY: dict[str, AppRegistryEntry] = {
    # Example Swarm Monitor entry (not enabled in this phase)
    # "swarm-monitor": AppRegistryEntry(
    #     id="swarm-monitor",
    #     title="Swarm Monitor",
    #     owner="orchestrator",
    #     status=AppStatus.ENABLED,
    #     route="/apps/swarm-monitor",
    #     startapp="swarm-monitor",
    #     required_roles=["viewer"],
    #     capability=AppCapability.READ_ONLY,
    #     min_client_version="1.0.0",
    #     required_features=["themeParams", "safeAreaInset", "viewportStableHeight"],
    #     data_contract_version="1",
    #     documentation_url="https://wiki.hively.dev/swarm-monitor",
    # ),
}


def get_app(app_id: str) -> Optional[AppRegistryEntry]:
    """Get an app by ID.

    Args:
        app_id: App identifier

    Returns:
        AppRegistryEntry or None if not found
    """
    return APP_REGISTRY.get(app_id)


def list_apps(
    status_filter: Optional[AppStatus] = None,
) -> list[AppRegistryEntry]:
    """List apps, optionally filtered by status.

    Args:
        status_filter: Optional status filter

    Returns:
        List of app registry entries
    """
    apps = list(APP_REGISTRY.values())

    if status_filter:
        apps = [app for app in apps if app.status == status_filter]

    return apps


def is_app_enabled(app_id: str) -> bool:
    """Check if an app is enabled.

    Args:
        app_id: App identifier

    Returns:
        True if app exists and is enabled
    """
    app = APP_REGISTRY.get(app_id)
    return app is not None and app.status == AppStatus.ENABLED


def validate_app_id(app_id: str) -> bool:
    """Validate app ID format.

    Args:
        app_id: App identifier to validate

    Returns:
        True if valid format
    """
    import re

    # Match: lowercase alphanumeric and hyphens, 1-64 chars, starts with alphanumeric
    pattern = r'^[a-z0-9][a-z0-9-]{0,63}$'
    return bool(re.match(pattern, app_id))


def register_app(app: AppRegistryEntry) -> None:
    """Register an app.

    Args:
        app: App registry entry to register

    Raises:
        ValueError: If app ID is invalid or already exists
    """
    if not validate_app_id(app.id):
        raise ValueError(f"Invalid app ID: {app.id}")

    if app.id in APP_REGISTRY:
        raise ValueError(f"App already registered: {app.id}")

    APP_REGISTRY[app.id] = app


def unregister_app(app_id: str) -> bool:
    """Unregister an app.

    Args:
        app_id: App identifier

    Returns:
        True if app was removed, False if not found
    """
    if app_id in APP_REGISTRY:
        del APP_REGISTRY[app_id]
        return True
    return False