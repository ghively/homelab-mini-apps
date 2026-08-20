"""Secure Telegram authentication with replay protection and role model.

Accepts initData only in Authorization: tma *** header.
Rejects query-string auth and does not trust initDataUnsafe.
Preserves the configured owner identity (MINIAPPS_OWNER_USER_ID) as initial owner.
"""

import hmac
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import parse_qsl
from operator import itemgetter
from fastapi import Request, HTTPException
from .config import BOT_TOKEN, ALLOWED_USER_IDS, OWNER_USER_ID
from .audit import audit_store, AuditEvent, AuditOutcome, compute_request_fingerprint


# Role definitions
class Role:
    """User roles for authorization."""

    VIEWER = "viewer"
    OPERATOR = "operator"
    OWNER = "owner"


# Role mapping (initially only the configured owner)
ROLE_MAPPING = {
    OWNER_USER_ID: [Role.OWNER, Role.VIEWER],
}

# Freshness windows in seconds
READ_FRESHNESS_SECONDS = 15 * 60  # 15 minutes
WRITE_FRESHNESS_SECONDS = 5 * 60  # 5 minutes

# Replay cache for preventing duplicate write requests
# In production, use Redis or similar with TTL
_replay_cache: dict[str, datetime] = {}


class AuthContext:
    """Authenticated user context."""

    def __init__(
        self,
        telegram_user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        roles: list[str],
        auth_time: datetime,
        expires_at: datetime,
        session_fingerprint: str,
    ):
        self.telegram_user_id = telegram_user_id
        self.username = username
        self.first_name = first_name
        self.roles = roles
        self.auth_time = auth_time
        self.expires_at = expires_at
        self.session_fingerprint = session_fingerprint
        self.is_owner = Role.OWNER in roles
        self.is_operator = Role.OPERATOR in roles
        self.is_viewer = Role.VIEWER in roles

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def is_fresh(self, for_write: bool = False) -> bool:
        """Check if authentication is fresh enough."""
        max_age = WRITE_FRESHNESS_SECONDS if for_write else READ_FRESHNESS_SECONDS
        age = (datetime.utcnow() - self.auth_time).total_seconds()
        return age <= max_age

    def is_expired(self) -> bool:
        """Check if authentication has expired."""
        return datetime.utcnow() >= self.expires_at


def validate_init_data(
    init_data: str,
    bot_token: str = BOT_TOKEN,
) -> dict | None:
    """Validate Telegram Mini App initData with HMAC-SHA256.

    Returns parsed dict or None if invalid.

    Args:
        init_data: Raw Telegram initData string
        bot_token: Telegram bot token

    Returns:
        Parsed initData dict or None if validation fails
    """
    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except Exception:
        return None

    if "hash" not in parsed:
        return None

    hash_val = parsed.pop("hash")

    # 1. Create secret key
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    # 2. Sort and create data-check-string
    items = sorted(parsed.items(), key=itemgetter(0))
    data_check_string = "\n".join(f"{k}={v}" for k, v in items)

    # 3. Compute expected hash
    computed = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # 4. Constant-time comparison
    if not hmac.compare_digest(computed, hash_val):
        return None

    # 5. Require auth_date (replay protection depends on it)
    if "auth_date" not in parsed:
        return None

    auth_time = int(parsed["auth_date"])

    # 6. Check freshness (stale data is rejected)
    age = time.time() - auth_time
    if age > READ_FRESHNESS_SECONDS:
        return None

    return parsed


def get_roles_for_user(telegram_user_id: int) -> list[str]:
    """Get roles for a Telegram user ID.

    Args:
        telegram_user_id: Telegram user ID

    Returns:
        List of role names (empty if unknown user)
    """
    return ROLE_MAPPING.get(telegram_user_id, [])


async def get_authenticated_user(
    request: Request,
    for_write: bool = False,
) -> AuthContext:
    """FastAPI dependency: extract and validate initData from Authorization header.

    Accepts initData ONLY in Authorization: tma *** header.
    Rejects query-string auth for security.

    Args:
        request: FastAPI request
        for_write: Whether this is a write operation (5-min freshness vs 15-min)

    Returns:
        AuthContext with user info and roles

    Raises:
        HTTPException: 401 if authentication missing/invalid, 403 if unauthorized
    """
    # Extract initData from Authorization header ONLY
    auth = request.headers.get("Authorization", "")

    if not auth.startswith("tma "):
        raise HTTPException(401, "Missing or invalid authentication header")

    init_data = auth[4:].strip()  # Remove "tma " prefix

    if not init_data:
        raise HTTPException(401, "Missing authentication data")

    # Validate HMAC and freshness
    validated = validate_init_data(init_data)
    if not validated:
        # Record audit event for failed auth
        audit_store.record(AuditEvent(
            correlation_id=compute_request_fingerprint(
                request.method,
                str(request.url.path),
                dict(request.headers),
            ),
            actor_id="unknown",
            actor_roles=[],
            action="auth.validate",
            target_type="session",
            target_id=None,
            outcome=AuditOutcome.FAILED,
            reason_code="invalid_hmac_or_stale",
            source_ip_hash=None,
            request_fingerprint=compute_request_fingerprint(
                request.method,
                str(request.url.path),
                dict(request.headers),
            ),
        ))
        raise HTTPException(401, "Invalid or stale authentication")

    # Parse user info
    user_info = json.loads(validated.get("user", "{}"))
    telegram_user_id = user_info.get("id")

    if not telegram_user_id:
        raise HTTPException(401, "Missing user identifier")

    # Check allowlist
    if telegram_user_id not in ALLOWED_USER_IDS:
        audit_store.record(AuditEvent(
            correlation_id=compute_request_fingerprint(
                request.method,
                str(request.url.path),
                dict(request.headers),
            ),
            actor_id=f"telegram:{telegram_user_id}",
            actor_roles=[],
            action="auth.validate",
            target_type="session",
            target_id=None,
            outcome=AuditOutcome.DENIED,
            reason_code="unauthorized_user",
            source_ip_hash=None,
            request_fingerprint=compute_request_fingerprint(
                request.method,
                str(request.url.path),
                dict(request.headers),
            ),
        ))
        raise HTTPException(403, "User not authorized")

    # Get roles
    roles = get_roles_for_user(telegram_user_id)

    # Create replay identifier for write operations
    session_fingerprint = hashlib.sha256(
        (validated.get("hash", "") + str(telegram_user_id)).encode()
    ).hexdigest()[:16]

    # Check replay for write operations
    if for_write:
        # Write operations must be very fresh (5 minutes)
        auth_time = int(validated["auth_date"])
        if time.time() - auth_time > WRITE_FRESHNESS_SECONDS:
            raise HTTPException(401, "Authentication too stale for write operations")

        # Check for replay
        if session_fingerprint in _replay_cache:
            # Existing session, check if still valid
            cached_time = _replay_cache[session_fingerprint]
            if datetime.utcnow() - cached_time < timedelta(minutes=WRITE_FRESHNESS_SECONDS / 60):
                raise HTTPException(403, "Duplicate write request rejected")

    # Update replay cache
    _replay_cache[session_fingerprint] = datetime.utcnow()

    # Clean up old replay cache entries
    _cleanup_replay_cache()

    # Create auth context
    auth_time = datetime.fromtimestamp(int(validated["auth_date"]))
    expires_at = auth_time + timedelta(seconds=READ_FRESHNESS_SECONDS)

    context = AuthContext(
        telegram_user_id=telegram_user_id,
        username=user_info.get("username"),
        first_name=user_info.get("first_name"),
        roles=roles,
        auth_time=auth_time,
        expires_at=expires_at,
        session_fingerprint=session_fingerprint,
    )

    # Record successful auth audit event
    audit_store.record(AuditEvent(
        correlation_id=compute_request_fingerprint(
            request.method,
            str(request.url.path),
            dict(request.headers),
        ),
        actor_id=f"telegram:{telegram_user_id}",
        actor_roles=roles,
        action="auth.validate",
        target_type="session",
        target_id=session_fingerprint,
        outcome=AuditOutcome.ALLOWED,
        reason_code="policy_match",
        source_ip_hash=None,
        request_fingerprint=compute_request_fingerprint(
            request.method,
            str(request.url.path),
            dict(request.headers),
        ),
    ))

    return context


def require_role(role: str):
    """Create a dependency that requires a specific role.

    Args:
        role: Required role name

    Returns:
        FastAPI dependency function
    """
    from fastapi import Depends

    async def dependency(
        auth: AuthContext = Depends(get_authenticated_user),
    ):
        if not auth.has_role(role):
            raise HTTPException(403, f"Role '{role}' required")
        return auth

    return dependency


def _cleanup_replay_cache() -> None:
    """Clean up expired entries from replay cache."""
    cutoff = datetime.utcnow() - timedelta(seconds=READ_FRESHNESS_SECONDS)
    expired = [k for k, v in _replay_cache.items() if v < cutoff]
    for key in expired:
        del _replay_cache[key]