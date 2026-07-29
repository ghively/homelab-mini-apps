"""Media — latest movies & TV from Jellyfin, cast to Home Assistant players.

Fail-closed: when Jellyfin or Home Assistant is unreachable the endpoints
return an explicit error status; the frontend must never render an empty
library as "nothing new".
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from ..core.auth_secure import get_authenticated_user
from ..core.config import JELLYFIN_URL, JELLYFIN_API_KEY, HASS_URL, HASS_TOKEN

router = APIRouter()


def _jf_headers():
    return {"X-Emby-Token": JELLYFIN_API_KEY}


def _ha_headers():
    return {"Authorization": f"Bearer {HASS_TOKEN}", "Content-Type": "application/json"}


def _item_summary(item: dict) -> dict:
    return {
        "id": item.get("Id"),
        "name": item.get("Name"),
        "type": item.get("Type"),  # Movie | Series | Episode
        "year": item.get("ProductionYear"),
        "overview": (item.get("Overview") or "")[:400],
        "rating": item.get("CommunityRating"),
        "official_rating": item.get("OfficialRating"),
        "runtime_min": round(item["RunTimeTicks"] / 600_000_000) if item.get("RunTimeTicks") else None,
        "series": item.get("SeriesName"),
        "season": item.get("ParentIndexNumber"),
        "episode": item.get("IndexNumber"),
        "has_poster": bool(item.get("ImageTags", {}).get("Primary")) or bool(item.get("SeriesPrimaryImageTag")),
    }


@router.get("/latest")
async def latest_media(user=Depends(get_authenticated_user)):
    """Recently added movies and TV, newest first."""
    if not JELLYFIN_API_KEY:
        raise HTTPException(503, "JELLYFIN_API_KEY not configured")

    params = {
        "SortBy": "DateCreated",
        "SortOrder": "Descending",
        "Recursive": "true",
        "Limit": "24",
        "Fields": "Overview,ProductionYear,CommunityRating,OfficialRating,RunTimeTicks",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            movies_r, shows_r = None, None
            movies_r = await c.get(
                f"{JELLYFIN_URL}/Items",
                headers=_jf_headers(),
                params={**params, "IncludeItemTypes": "Movie"},
            )
            movies_r.raise_for_status()
            shows_r = await c.get(
                f"{JELLYFIN_URL}/Items",
                headers=_jf_headers(),
                params={**params, "IncludeItemTypes": "Episode", "GroupItems": "true"},
            )
            shows_r.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Jellyfin unreachable: {e}")

    movies = [_item_summary(i) for i in movies_r.json().get("Items", [])]

    # Collapse episodes into their series, keeping the newest episode per show
    shows, seen_series = [], set()
    for i in shows_r.json().get("Items", []):
        key = i.get("SeriesId") or i.get("Id")
        if key in seen_series:
            continue
        seen_series.add(key)
        s = _item_summary(i)
        s["poster_id"] = i.get("SeriesId") or i.get("Id")
        shows.append(s)

    return {"movies": movies, "shows": shows[:12]}


@router.get("/poster/{item_id}")
async def poster(item_id: str, user=Depends(get_authenticated_user)):
    """Proxy a primary poster image so the webview never talks to Jellyfin
    directly (it is not exposed publicly and <img> cannot send our auth)."""
    if not item_id.replace("-", "").isalnum():
        raise HTTPException(400, "Bad item id")
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"{JELLYFIN_URL}/Items/{item_id}/Images/Primary",
                headers=_jf_headers(),
                params={"maxWidth": "300", "quality": "85"},
            )
            r.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(404, "No poster")
    return Response(
        content=r.content,
        media_type=r.headers.get("content-type", "image/jpeg"),
        headers={"Cache-Control": "private, max-age=86400"},
    )


@router.get("/players")
async def players(user=Depends(get_authenticated_user)):
    """Home Assistant media_player entities that can receive a cast."""
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{HASS_URL}/api/states", headers=_ha_headers())
            r.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Home Assistant unreachable: {e}")

    out = []
    for s in r.json():
        if not s["entity_id"].startswith("media_player."):
            continue
        attrs = s.get("attributes", {})
        out.append(
            {
                "entity_id": s["entity_id"],
                "name": attrs.get("friendly_name", s["entity_id"]),
                "state": s["state"],
                "app": attrs.get("app_name"),
                "now_playing": attrs.get("media_title"),
            }
        )
    # Available players first, unavailable last — never hidden (fail-closed:
    # the user should see a device is unreachable rather than wonder).
    out.sort(key=lambda p: (p["state"] in ("unavailable", "unknown"), p["name"].lower()))
    return {"players": out}


@router.post("/play")
async def play(body: dict, user=Depends(get_authenticated_user)):
    """Cast a Jellyfin item to a Home Assistant media_player.

    Sends a direct Jellyfin stream URL via media_player.play_media, which
    works for Chromecast/AndroidTV/DLNA targets without requiring the HA
    Jellyfin integration.
    """
    entity_id = body.get("entity_id", "")
    item_id = body.get("item_id", "")
    if not entity_id.startswith("media_player.") or not item_id.replace("-", "").isalnum():
        raise HTTPException(400, "entity_id and item_id required")

    stream_url = f"{JELLYFIN_URL}/Videos/{item_id}/stream?static=true&api_key={JELLYFIN_API_KEY}"
    payload = {
        "entity_id": entity_id,
        "media_content_id": stream_url,
        "media_content_type": "video",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                f"{HASS_URL}/api/services/media_player/play_media",
                headers=_ha_headers(),
                json=payload,
            )
            r.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Cast failed: {e}")
    return {"success": True, "entity_id": entity_id, "item_id": item_id}
