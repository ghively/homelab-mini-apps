"""Swarm Monitor service — read-only GitLab and Prometheus adapters.

Both adapters emit SourceEnvelope[T] via the fail-closed contract.
Missing/unreachable sources never render healthy.
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.core.envelope import (
    SourceEnvelope,
    SourceStatus,
    Provenance,
    classify_status,
    compute_freshness_ms,
    STALENESS_THRESHOLDS_MS,
)


ADAPTER_VERSION = "swarm-monitor-v1"


# ─── GitLab adapter ───────────────────────────────────────────────────────


async def fetch_gitlab(
    client: httpx.AsyncClient,
    project_id: int = 113,
) -> SourceEnvelope:
    """Fetch latest pipeline status from GitLab project."""
    token = os.environ.get("GITLAB_TOKEN")
    base_url = os.environ.get("GITLAB_API_URL", "https://git.hively.dev/api/v4")
    observed_at = datetime.now(timezone.utc)

    if not token:
        return SourceEnvelope[dict](
            source=f"gitlab-project-{project_id}",
            adapter_version=ADAPTER_VERSION,
            observed_at=observed_at,
            freshness_ms=STALENESS_THRESHOLDS_MS["default"] * 2,
            status=SourceStatus.UNAVAILABLE,
            error="GITLAB_TOKEN not configured",
            provenance=Provenance(
                kind="https-api",
                identity=f"gitlab-project-{project_id}",
                safe_reference=f"{base_url}/projects/{project_id}",
            ),
        )

    try:
        # Fetch latest pipeline
        resp = await client.get(
            f"{base_url}/projects/{project_id}/pipelines",
            headers={"PRIVATE-TOKEN": token},
            params={"per_page": 5, "sort": "desc"},
            timeout=10,
        )
        resp.raise_for_status()
        pipelines = resp.json()

        if not pipelines:
            return SourceEnvelope[dict](
                source=f"gitlab-project-{project_id}",
                adapter_version=ADAPTER_VERSION,
                observed_at=observed_at,
                freshness_ms=compute_freshness_ms(None, observed_at),
                status=SourceStatus.UNKNOWN,
                error="No pipelines found",
                provenance=Provenance(
                    kind="https-api",
                    identity=f"gitlab-project-{project_id}",
                    safe_reference=f"{base_url}/projects/{project_id}",
                ),
            )

        latest = pipelines[0]
        source_updated_at = None
        if latest.get("updated_at"):
            source_updated_at = datetime.fromisoformat(
                latest["updated_at"].replace("Z", "+00:00")
            )

        freshness = compute_freshness_ms(source_updated_at, observed_at)
        status = classify_status(
            is_reachable=True,
            freshness_ms=freshness,
            source_type="gitlab",
            has_data=True,
        )

        return SourceEnvelope[dict](
            source=f"gitlab-project-{project_id}",
            adapter_version=ADAPTER_VERSION,
            observed_at=observed_at,
            source_updated_at=source_updated_at,
            freshness_ms=freshness,
            status=status,
            data={
                "latest_pipeline": {
                    "id": latest.get("id"),
                    "sha": latest.get("sha", "")[:12],
                    "ref": latest.get("ref"),
                    "status": latest.get("status"),
                    "web_url": latest.get("web_url"),
                },
                "recent_pipelines": [
                    {
                        "id": p.get("id"),
                        "ref": p.get("ref"),
                        "status": p.get("status"),
                    }
                    for p in pipelines
                ],
            },
            provenance=Provenance(
                kind="https-api",
                identity=f"gitlab-project-{project_id}",
                safe_reference=f"{base_url}/projects/{project_id}",
            ),
        )

    except httpx.HTTPStatusError as exc:
        return SourceEnvelope[dict](
            source=f"gitlab-project-{project_id}",
            adapter_version=ADAPTER_VERSION,
            observed_at=observed_at,
            freshness_ms=STALENESS_THRESHOLDS_MS["default"] * 2,
            status=SourceStatus.ERROR,
            error=f"HTTP {exc.response.status_code}",
            provenance=Provenance(
                kind="https-api",
                identity=f"gitlab-project-{project_id}",
                safe_reference=f"{base_url}/projects/{project_id}",
            ),
        )
    except Exception as exc:
        return SourceEnvelope[dict](
            source=f"gitlab-project-{project_id}",
            adapter_version=ADAPTER_VERSION,
            observed_at=observed_at,
            freshness_ms=STALENESS_THRESHOLDS_MS["default"] * 2,
            status=SourceStatus.UNAVAILABLE,
            error=str(exc),
            provenance=Provenance(
                kind="https-api",
                identity=f"gitlab-project-{project_id}",
                safe_reference=f"{base_url}/projects/{project_id}",
            ),
        )


# ─── Prometheus adapter ────────────────────────────────────────────────────


async def fetch_prometheus(
    client: httpx.AsyncClient,
    prometheus_url: str = "http://gh-arm:9090",
) -> SourceEnvelope:
    """Fetch fleet health metrics from Prometheus."""
    observed_at = datetime.now(timezone.utc)

    try:
        # Query: up == 1 for all node_exporter targets
        resp = await client.get(
            f"{prometheus_url}/api/v1/query",
            params={"query": "up{job=~'node_exporter|node-exporter'}"},
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("status") != "success":
            return SourceEnvelope[dict](
                source="prometheus-fleet",
                adapter_version=ADAPTER_VERSION,
                observed_at=observed_at,
                freshness_ms=compute_freshness_ms(None, observed_at),
                status=SourceStatus.ERROR,
                error="Prometheus query not successful",
                provenance=Provenance(
                    kind="https-api",
                    identity="prometheus-fleet",
                    safe_reference=f"{prometheus_url}/api/v1/query",
                ),
            )

        metrics = result.get("data", {}).get("result", [])
        hosts_up = sum(1 for m in metrics if m.get("value", [0, "0"])[1] == "1")
        hosts_total = len(metrics)

        # Get timestamp from the query result
        source_updated_at = None
        if metrics:
            ts = metrics[0].get("value", [None])[0]
            if ts:
                source_updated_at = datetime.fromtimestamp(ts, tz=timezone.utc)

        freshness = compute_freshness_ms(source_updated_at, observed_at)
        status = classify_status(
            is_reachable=True,
            freshness_ms=freshness,
            source_type="prometheus",
            has_data=True,
        )

        return SourceEnvelope[dict](
            source="prometheus-fleet",
            adapter_version=ADAPTER_VERSION,
            observed_at=observed_at,
            source_updated_at=source_updated_at,
            freshness_ms=freshness,
            status=status,
            data={
                "hosts_up": hosts_up,
                "hosts_total": hosts_total,
                "hosts": [
                    {
                        "instance": m.get("metric", {}).get("instance", "unknown"),
                        "status": "up"
                        if m.get("value", [0, "0"])[1] == "1"
                        else "down",
                    }
                    for m in metrics
                ],
            },
            provenance=Provenance(
                kind="https-api",
                identity="prometheus-fleet",
                safe_reference=f"{prometheus_url}/api/v1/query",
            ),
        )

    except Exception as exc:
        return SourceEnvelope[dict](
            source="prometheus-fleet",
            adapter_version=ADAPTER_VERSION,
            observed_at=observed_at,
            freshness_ms=STALENESS_THRESHOLDS_MS["default"] * 2,
            status=SourceStatus.UNAVAILABLE,
            error=str(exc),
            provenance=Provenance(
                kind="https-api",
                identity="prometheus-fleet",
                safe_reference=f"{prometheus_url}/api/v1/query",
            ),
        )


# ─── Aggregator ─────────────────────────────────────────────────────────────


async def fetch_all() -> dict:
    """Fetch all Swarm Monitor sources concurrently and return envelopes."""
    async with httpx.AsyncClient() as client:
        gitlab_task = fetch_gitlab(client)
        prometheus_task = fetch_prometheus(client)
        gitlab_envelope, prometheus_envelope = await asyncio.gather(
            gitlab_task, prometheus_task
        )

    return {
        "sources": [gitlab_envelope, prometheus_envelope],
        "summary": {
            "healthy_sources": sum(
                1 for e in [gitlab_envelope, prometheus_envelope] if e.is_healthy()
            ),
            "total_sources": 2,
        },
    }
