"""Smart Home Control — Home Assistant integration."""

import httpx
from fastapi import APIRouter, Depends, HTTPException
from ..core.auth_secure import get_authenticated_user
from ..core.config import HASS_URL, HASS_TOKEN

router = APIRouter()


def _headers():
    return {"Authorization": f"Bearer {HASS_TOKEN}", "Content-Type": "application/json"}


@router.get("/states")
async def get_states(user = Depends(get_authenticated_user)):
    """Get all entity states, filtered to useful domains."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{HASS_URL}/api/states", headers=_headers())
        r.raise_for_status()
        states = r.json()

    # Filter to interesting domains
    domains = {
        "light",
        "switch",
        "sensor",
        "binary_sensor",
        "climate",
        "media_player",
        "automation",
        "script",
        "scene",
        "input_boolean",
    }
    filtered = []
    for s in states:
        domain = s["entity_id"].split(".")[0]
        if domain in domains:
            filtered.append(
                {
                    "entity_id": s["entity_id"],
                    "state": s["state"],
                    "attributes": s.get("attributes", {}),
                    "friendly_name": s.get("attributes", {}).get(
                        "friendly_name", s["entity_id"]
                    ),
                    "domain": domain,
                }
            )

    # Group by domain
    grouped = {}
    for e in filtered:
        grouped.setdefault(e["domain"], []).append(e)

    return {"entities": grouped, "total": len(filtered)}


@router.post("/call/{domain}/{service}")
async def call_service(
    domain: str, service: str, body: dict, user = Depends(get_authenticated_user)
):
    """Call a Home Assistant service."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            f"{HASS_URL}/api/services/{domain}/{service}",
            headers=_headers(),
            json=body.get("service_data", {}),
        )
        r.raise_for_status()
        return {"success": True, "response": r.json()}


@router.get("/config")
async def get_ha_config(user = Depends(get_authenticated_user)):
    """Get HA config info."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{HASS_URL}/api/config", headers=_headers())
        r.raise_for_status()
        return r.json()
