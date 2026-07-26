"""Telegram initData validation — HMAC-SHA256."""

import hmac
import hashlib
import json
import time
from urllib.parse import parse_qsl
from operator import itemgetter
from fastapi import Request, HTTPException
from .config import BOT_TOKEN, ALLOWED_USER_IDS


def validate_init_data(init_data: str, bot_token: str = BOT_TOKEN) -> dict | None:
    """Validate Telegram Mini App initData. Returns parsed dict or None."""
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

    # 5. Check auth_date freshness (24h window)
    if "auth_date" in parsed:
        auth_time = int(parsed["auth_date"])
        if time.time() - auth_time > 86400:
            return None

    return parsed


async def get_authenticated_user(request: Request) -> dict:
    """FastAPI dependency: extract and validate initData from request.

    Accepts initData in one of:
    - Authorization: Bearer <initData>
    - X-Telegram-Init-Data: <initData>
    - Body field 'initData' (fallback)

    Returns the validated user info dict.
    """
    init_data = None

    # Try header first
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        init_data = auth[7:]
    elif request.headers.get("X-Telegram-Init-Data"):
        init_data = request.headers["X-Telegram-Init-Data"]

    # Fallback to query param
    if not init_data:
        init_data = request.query_params.get("initData")

    if not init_data:
        raise HTTPException(401, "Missing authentication")

    validated = validate_init_data(init_data)
    if not validated:
        raise HTTPException(401, "Invalid authentication")

    user_info = json.loads(validated.get("user", "{}"))

    # Check allowlist
    if user_info.get("id") not in ALLOWED_USER_IDS:
        raise HTTPException(403, "User not authorized")

    return user_info
