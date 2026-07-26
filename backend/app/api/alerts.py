"""Alert Triage Console — Prometheus Alertmanager + Uptime Kuma integration."""

import asyncio
import httpx
from fastapi import APIRouter, Depends, HTTPException
from ..core.auth_secure import get_authenticated_user
from ..core.config import PROMETHEUS_URL

router = APIRouter()

ALERTMANAGER_URL = "http://100.65.126.126:9093"
UPTIME_KUMA_URL = "http://100.65.126.126:3001"


@router.get("/active")
async def active_alerts(user=Depends(get_authenticated_user)):
    """Get all active alerts from Alertmanager."""
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"{ALERTMANAGER_URL}/api/v2/alerts",
                params={"active": "true", "silenced": "false", "inhibited": "false"},
            )
            r.raise_for_status()
            alerts = r.json()
    except Exception:
        alerts = []

    # Also get firing alerts from Prometheus
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{PROMETHEUS_URL}/api/v1/alerts")
            r.raise_for_status()
            data = r.json()
            prom_alerts = [
                a
                for a in data.get("data", {}).get("alerts", [])
                if a.get("state") == "firing"
            ]
    except Exception:
        prom_alerts = []

    return {
        "alertmanager": [
            {
                "name": a.get("labels", {}).get("alertname", "unknown"),
                "severity": a.get("labels", {}).get("severity", "unknown"),
                "instance": a.get("labels", {}).get("instance", ""),
                "summary": a.get("annotations", {}).get("summary", ""),
                "description": a.get("annotations", {}).get("description", ""),
                "starts_at": a.get("startsAt", ""),
                "status": a.get("status", {}).get("state", ""),
            }
            for a in alerts
        ],
        "prometheus_firing": [
            {
                "name": a.get("labels", {}).get("alertname", "unknown"),
                "severity": a.get("labels", {}).get("severity", "unknown"),
                "instance": a.get("labels", {}).get("instance", ""),
                "summary": a.get("annotations", {}).get("summary", ""),
                "state": a.get("state", ""),
                "active_at": a.get("activeAt", ""),
            }
            for a in prom_alerts
        ],
        "total": len(alerts) + len(prom_alerts),
    }


@router.get("/silences")
async def get_silences(user=Depends(get_authenticated_user)):
    """Get active silences from Alertmanager."""
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"{ALERTMANAGER_URL}/api/v2/silences", params={"active": "true"}
            )
            r.raise_for_status()
            return {"silences": r.json()}
    except Exception as e:
        raise HTTPException(502, f"Alertmanager unreachable: {e}")


@router.post("/silence")
async def create_silence(body: dict, user=Depends(get_authenticated_user)):
    """Create a silence in Alertmanager."""
    import datetime

    now = datetime.datetime.now(datetime.timezone.utc)
    duration_min = body.get("duration_minutes", 60)
    matcher_name = body.get("matcher_name", "alertname")
    matcher_value = body.get("matcher_value", "")

    payload = {
        "matchers": [{"name": matcher_name, "value": matcher_value, "isRegex": False}],
        "startsAt": now.isoformat(),
        "endsAt": (now + datetime.timedelta(minutes=duration_min)).isoformat(),
        "createdBy": user.first_name or "mini-app",
        "comment": body.get(
            "comment", f"Silenced via Mini App by {user.first_name or 'user'}"
        ),
    }

    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"{ALERTMANAGER_URL}/api/v2/silences", json=payload)
        r.raise_for_status()
        return {"success": True, "silence_id": r.json().get("silenceId")}


@router.get("/history")
async def alert_history(hours: int = 24, user=Depends(get_authenticated_user)):
    """Get alert history from Prometheus over the past N hours."""
    import time

    end = int(time.time())
    start = end - (hours * 3600)
    query = 'ALERTS{alertstate="firing"}'

    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params={
                "query": query,
                "start": start,
                "end": end,
                "step": "300s",
            },
        )
        r.raise_for_status()
        data = r.json()

    return {
        "hours": hours,
        "series": data.get("data", {}).get("result", []),
    }
