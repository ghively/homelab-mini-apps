"""Cost / Quota Monitor — track API usage, model costs, and resource quotas."""

import asyncio
import httpx
import os
import glob
from fastapi import APIRouter, Depends
from ..core.auth_secure import get_authenticated_user
from ..core.config import PROMETHEUS_URL, SESSION_DB

# Instance-label match for the host tracked by the OCI free-tier endpoint below.
# Set via env var — no real instance/IP fragment ships as a default.
OCI_INSTANCE_MATCH = os.environ.get("OCI_INSTANCE_MATCH", ".*oci-host.*")

router = APIRouter()


async def prom_query_all(query: str) -> list:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
        r.raise_for_status()
        data = r.json()
        if data["status"] == "success":
            return data["data"]["result"]
    return []


async def prom_query(query: str) -> str:
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
        r.raise_for_status()
        data = r.json()
        if data["status"] == "success" and data["data"]["result"]:
            return data["data"]["result"][0]["value"][1]
    return "0"


@router.get("/overview")
async def cost_overview(user = Depends(get_authenticated_user)):
    """Get cost/quota overview."""

    # Container resource usage
    containers = await prom_query_all(
        'sum(container_memory_usage_bytes{name!=""}) by (name)'
    )

    # Per-host resource summary
    host_cpu = await prom_query_all(
        '100 - (avg by(instance) (rate(node_cpu_seconds_total{job="node_exporter",mode="idle"}[5m])) * 100)'
    )
    host_mem = await prom_query_all(
        "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"
    )

    # Docker container count
    container_count = await prom_query(
        'count(count(container_last_seen{name!=""}) by (name))'
    )

    # Network traffic (rough daily estimate from rate)
    net_rx = await prom_query("sum(rate(node_network_receive_bytes_total[1h]))")
    net_tx = await prom_query("sum(rate(node_network_transmit_bytes_total[1h]))")

    return {
        "containers": [
            {
                "name": c["metric"].get("name", "?"),
                "memory_mb": round(float(c["value"][1]) / 1e6, 1),
            }
            for c in containers[:20]
        ],
        "host_cpu": [
            {
                "instance": h["metric"].get("instance", "?"),
                "cpu_pct": round(float(h["value"][1]), 1),
            }
            for h in host_cpu
        ],
        "host_mem": [
            {
                "instance": h["metric"].get("instance", "?"),
                "mem_pct": round(float(h["value"][1]), 1),
            }
            for h in host_mem
        ],
        "container_count": int(float(container_count)),
        "network": {
            "rx_mbps": round(float(net_rx) * 8 / 1e6, 2),
            "tx_mbps": round(float(net_tx) * 8 / 1e6, 2),
        },
    }


@router.get("/models")
async def model_usage(user = Depends(get_authenticated_user)):
    """Get Hermes model usage stats from session logs."""
    # Read Hermes session DB for recent usage
    import sqlite3
    import json
    from datetime import datetime, timedelta

    db_path = SESSION_DB
    if not os.path.exists(db_path):
        return {"usage": [], "note": "Session DB not found"}

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        # Try to get recent model usage
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        rows = conn.execute(
            "SELECT model, provider, COUNT(*) as count, "
            "SUM(total_tokens) as tokens "
            "FROM messages WHERE created_at > ? "
            "GROUP BY model ORDER BY count DESC LIMIT 20",
            (cutoff,),
        ).fetchall()
        conn.close()

        return {
            "usage": [
                {
                    "model": r["model"],
                    "provider": r["provider"],
                    "requests": r["count"],
                    "tokens": r["tokens"] or 0,
                }
                for r in rows
            ],
            "period": "24h",
        }
    except Exception as e:
        return {"usage": [], "error": str(e)}


@router.get("/oci")
async def oci_resources(user = Depends(get_authenticated_user)):
    """Get OCI free tier resource usage for the configured host."""
    # Disk is the constrained resource on OCI free tier
    disk = await prom_query(
        f'100 * (1 - (node_filesystem_avail_bytes{{instance=~"{OCI_INSTANCE_MATCH}",mountpoint="/"}} / node_filesystem_size_bytes{{instance=~"{OCI_INSTANCE_MATCH}",mountpoint="/"}}))'
    )
    cpu = await prom_query(
        f'100 - (avg(rate(node_cpu_seconds_total{{instance=~"{OCI_INSTANCE_MATCH}",mode="idle"}}[5m])) * 100)'
    )
    mem = await prom_query(
        f'100 * (1 - (node_memory_MemAvailable_bytes{{instance=~"{OCI_INSTANCE_MATCH}"}} / node_memory_MemTotal_bytes{{instance=~"{OCI_INSTANCE_MATCH}"}}))'
    )

    return {
        "oci-host": {
            "disk_pct": round(float(disk), 1),
            "cpu_pct": round(float(cpu), 1),
            "mem_pct": round(float(mem), 1),
            "disk_limit_gb": 200,
            "compute_limit": "4 OCPU / 24GB RAM (free tier)",
        },
        "note": "OCI free tier: 2×AMD Micro + 1×A1.Flex (4 OCPU/24GB). Storage capped at 200GB.",
    }
