"""Fleet Health Dashboard — Prometheus queries for all hosts."""

import asyncio
import datetime
import httpx
from fastapi import APIRouter, Depends
from ..core.auth_secure import get_authenticated_user
from ..core.config import PROMETHEUS_URL

router = APIRouter()


async def prom_query(query: str) -> str:
    """Run an instant query against Prometheus."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
        r.raise_for_status()
        data = r.json()
        if data["status"] == "success" and data["data"]["result"]:
            return data["data"]["result"][0]["value"][1]
    return "0"


async def prom_query_all(query: str) -> list:
    """Run a query returning multiple series."""
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
        r.raise_for_status()
        data = r.json()
        if data["status"] == "success":
            return data["data"]["result"]
    return []


def _extract_ip(instance: str) -> str:
    """Extract IP from Prometheus instance label (strip port)."""
    return instance.split(":")[0] if ":" in instance else instance


# IP → friendly hostname mapping
IP_MAP = {
    "100.92.162.32": "gh-ai",
    "100.65.126.126": "gh-arm",
    "100.116.221.84": "gh-git",
    "100.97.166.81": "gh-mac",
    "100.116.139.100": "gh-media",
    "100.88.26.95": "gh-nvidia",
    "192.168.0.165": "gh-media",
    "192.168.0.167": "gh-mac",
    "192.168.0.196": "gh-storage",
    "localhost": "gh-ai",
}


@router.get("/overview")
async def fleet_overview(user = Depends(get_authenticated_user)):
    """Get fleet-wide health overview."""
    queries = {
        "up_hosts": prom_query_all('up{job="node_exporter"}'),
        "cpu_usage": prom_query_all(
            '100 - (avg by(instance) (rate(node_cpu_seconds_total{job="node_exporter",mode="idle"}[5m])) * 100)'
        ),
        "mem_usage": prom_query_all(
            "100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))"
        ),
        "disk_usage": prom_query_all(
            '100 * (1 - (node_filesystem_avail_bytes{mountpoint="/",fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{mountpoint="/",fstype!~"tmpfs|overlay"}))'
        ),
        "load": prom_query_all("node_load1"),
    }

    keys = list(queries.keys())
    values = await asyncio.gather(*queries.values())
    results = dict(zip(keys, values))

    hosts = {}
    for entry in results.get("up_hosts", []):
        ip = _extract_ip(entry["metric"].get("instance", ""))
        hosts[ip] = {
            "ip": ip,
            "name": IP_MAP.get(ip, ip),
            "up": entry["value"][1] == "1",
        }

    for metric_key, label in [
        ("cpu_usage", "cpu"),
        ("mem_usage", "mem"),
        ("disk_usage", "disk"),
        ("load", "load1"),
    ]:
        for entry in results.get(metric_key, []):
            ip = _extract_ip(entry["metric"].get("instance", ""))
            if ip in hosts:
                hosts[ip][label] = round(float(entry["value"][1]), 1)

    return {
        "hosts": list(hosts.values()),
        "total_hosts": len(hosts),
        "hosts_up": sum(1 for h in hosts.values() if h["up"]),
        "hosts_down": sum(1 for h in hosts.values() if not h["up"]),
        "timestamp": datetime.datetime.now().isoformat(),
    }


@router.get("/host/{ip}")
async def host_detail(ip: str, user = Depends(get_authenticated_user)):
    """Get detailed metrics for a single host."""
    inst = f"{ip}.*"
    q_cpu = prom_query(
        f'100 - (avg(rate(node_cpu_seconds_total{{job="node_exporter",instance=~"{inst}",mode="idle"}}[5m])) * 100)'
    )
    q_mem = prom_query(
        f'100 * (1 - (node_memory_MemAvailable_bytes{{instance=~"{inst}"}} / node_memory_MemTotal_bytes{{instance=~"{inst}"}}))'
    )
    q_disk = prom_query(
        f'100 * (1 - (node_filesystem_avail_bytes{{instance=~"{inst}",mountpoint="/"}} / node_filesystem_size_bytes{{instance=~"{inst}",mountpoint="/"}}))'
    )
    q_load = prom_query(f'node_load1{{instance=~"{inst}"}}')
    q_uptime = prom_query(f'time() - node_boot_time_seconds{{instance=~"{inst}"}}')
    q_net_rx = prom_query(
        f'rate(node_network_receive_bytes_total{{instance=~"{inst}",device=~"eth.*|ens.*|enp.*"}}[5m])'
    )
    q_net_tx = prom_query(
        f'rate(node_network_transmit_bytes_total{{instance=~"{inst}",device=~"eth.*|ens.*|enp.*"}}[5m])'
    )

    cpu, mem, disk, load, uptime, net_rx, net_tx = await asyncio.gather(
        q_cpu, q_mem, q_disk, q_load, q_uptime, q_net_rx, q_net_tx
    )

    containers = await prom_query_all(
        f'count(container_last_seen{{instance=~"{inst}"}}) by (instance)'
    )

    return {
        "ip": ip,
        "name": IP_MAP.get(ip, ip),
        "cpu_pct": float(cpu),
        "mem_pct": float(mem),
        "disk_pct": float(disk),
        "load1": float(load),
        "uptime_seconds": float(uptime),
        "net_rx_bps": float(net_rx),
        "net_tx_bps": float(net_tx),
        "container_count": len(containers),
    }
