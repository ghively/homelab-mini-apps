"""Security audit primitives for auth, session, and envelope events.

Every security-relevant event is logged without raw auth data, tokens, headers,
or secret-bearing content.
"""

import hashlib
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class AuditOutcome(str, Enum):
    """Audit event outcomes."""

    ALLOWED = "allowed"
    DENIED = "denied"
    FAILED = "failed"
    PARTIAL = "partial"


class AuditEvent(BaseModel):
    """Security-relevant audit event.

    Audit events never contain raw init data, tokens, authorization headers,
    full request bodies, prompts, tool output, cookie values, or client storage.
    """

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = Field(..., description="Correlation ID for request tracing")
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    actor_id: str = Field(..., description="Actor identifier (e.g., 'telegram:111111111' or 'system')")
    actor_roles: list[str] = Field(default_factory=list, description="Actor roles at time of event")
    action: str = Field(..., description="Action performed (e.g., 'source.read', 'auth.validate')")
    target_type: str = Field(..., description="Target type (e.g., 'source', 'app', 'user')")
    target_id: Optional[str] = Field(None, description="Target identifier")
    outcome: AuditOutcome = Field(..., description="Event outcome")
    reason_code: Optional[str] = Field(None, description="Policy or error reason code")
    source_ip_hash: Optional[str] = Field(None, description="Optional keyed hash of source IP")
    request_fingerprint: str = Field(..., description="Nonsecret hash of request metadata")
    details: dict = Field(default_factory=dict, description="Additional sanitized details")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AuditStore:
    """In-memory audit store for demonstration.

    Production should use a persistent, append-only store with rotation policy.
    Initial retention: 90 days.
    """

    def __init__(self):
        self._events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        """Record an audit event."""
        self._events.append(event)

    def query(
        self,
        actor_id: Optional[str] = None,
        target_type: Optional[str] = None,
        outcome: Optional[AuditOutcome] = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Query audit events with filters."""
        filtered = self._events

        if actor_id:
            filtered = [e for e in filtered if e.actor_id == actor_id]
        if target_type:
            filtered = [e for e in filtered if e.target_type == target_type]
        if outcome:
            filtered = [e for e in filtered if e.outcome == outcome]

        # Return most recent first
        return list(reversed(filtered[-limit:]))

    def get_recent(self, limit: int = 100) -> list[AuditEvent]:
        """Get most recent audit events."""
        return list(reversed(self._events[-limit:]))


def compute_request_fingerprint(
    method: str,
    path: str,
    headers: dict[str, str],
) -> str:
    """Compute a nonsecret hash of request metadata for audit fingerprinting.

    Excludes authorization headers and sensitive values.
    """
    # Filter out sensitive headers
    safe_headers = {
        k: v
        for k, v in headers.items()
        if k.lower() not in ("authorization", "cookie", "x-telegram-init-data")
    }

    # Create normalized string for hashing
    normalized = f"{method}:{path}:{sorted(safe_headers.items())}"

    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def hash_source_ip(ip: str, secret: str) -> str:
    """Compute a privacy-preserving keyed hash of a source IP address."""
    return hashlib.sha256((ip + secret).encode()).hexdigest()[:16]


# Global audit store instance (production should be injected)
audit_store = AuditStore()