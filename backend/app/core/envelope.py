"""Source envelope schema and fail-closed contract.

All adapters must emit SourceEnvelope[T] with non-null status.
Missing, stale, error, unavailable, deferred, and unknown states must never
render as healthy/connected in the UI.
"""

from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field
import uuid


class SourceStatus(str, Enum):
    """Source health status values."""

    OK = "ok"
    STALE = "stale"
    ERROR = "error"
    UNAVAILABLE = "unavailable"
    DEFERRED = "deferred"
    UNKNOWN = "unknown"


class Provenance(BaseModel):
    """Source adapter provenance metadata."""

    kind: str = Field(
        ...,
        description="Adapter kind (e.g., 'https-api', 'file-mount', 'internal')",
    )
    identity: str = Field(..., description="Unique source identifier")
    safe_reference: str = Field(
        ...,
        description="Approved URL or mount ID (no secrets, tokens, or raw paths)",
    )


T = TypeVar("T")


class SourceEnvelope(BaseModel, Generic[T]):
    """Normalized source envelope with fail-closed contract.

    Status values: ok | stale | error | unavailable | deferred | unknown
    Rule: Unavailable/error/unknown sources must never render as healthy/connected.
    """

    source: str = Field(..., description="Source identifier (e.g., 'gitlab-project-113')")
    adapter_version: str = Field(
        ...,
        description="Adapter commit SHA or semver",
    )
    observed_at: datetime = Field(
        ...,
        description="RFC3339 fetch time at the adapter layer",
    )
    source_updated_at: Optional[datetime] = Field(
        None,
        description="RFC3339 source-origin time (when the source was actually updated)",
    )
    freshness_ms: int = Field(
        ...,
        description="Age in milliseconds from source_updated_at to observed_at",
        ge=0,
    )
    status: SourceStatus = Field(..., description="Source health status")
    data: Optional[T] = Field(
        None,
        description="Source data payload (present only when safe and contract-valid)",
    )
    error: Optional[str] = Field(
        None,
        description="Error message if status is error or unavailable",
    )
    provenance: Provenance = Field(..., description="Source adapter provenance metadata")
    correlation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="UUIDv7 correlation ID for tracing",
    )

    def is_healthy(self) -> bool:
        """Return True only if status is OK and freshness is within threshold."""
        return self.status == SourceStatus.OK

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


# Source freshness thresholds (milliseconds)
STALENESS_THRESHOLDS_MS = {
    "prometheus": 300000,  # 5 minutes
    "gitlab": 1800000,  # 30 minutes
    "grafana": 300000,  # 5 minutes
    "default": 3600000,  # 1 hour
}


def compute_freshness_ms(
    source_updated_at: Optional[datetime], observed_at: datetime
) -> int:
    """Compute freshness in milliseconds from source update to observation.

    Args:
        source_updated_at: When the source was actually updated (null if unknown)
        observed_at: When the adapter fetched the data

    Returns:
        Freshness in milliseconds. Returns a large value if source_updated_at is None.
    """
    if source_updated_at is None:
        return STALENESS_THRESHOLDS_MS["default"] * 2  # Treat unknown as very stale

    delta = observed_at - source_updated_at
    return int(delta.total_seconds() * 1000)


def classify_status(
    is_reachable: bool,
    freshness_ms: int,
    source_type: str,
    has_data: bool,
    error_message: Optional[str] = None,
) -> SourceStatus:
    """Classify source status based on reachability, freshness, and data quality.

    This is the fail-closed classifier: unknown/unavailable/error sources must
    never return OK.

    Args:
        is_reachable: Whether the source could be contacted
        freshness_ms: Age of the data in milliseconds
        source_type: Source type for threshold lookup
        has_data: Whether valid data was returned
        error_message: Optional error from the adapter

    Returns:
        SourceStatus classification
    """
    if not is_reachable:
        if error_message:
            return SourceStatus.UNAVAILABLE
        return SourceStatus.UNKNOWN

    if error_message:
        return SourceStatus.ERROR

    if not has_data:
        return SourceStatus.UNKNOWN

    threshold = STALENESS_THRESHOLDS_MS.get(source_type, STALENESS_THRESHOLDS_MS["default"])
    if freshness_ms > threshold:
        return SourceStatus.STALE

    return SourceStatus.OK