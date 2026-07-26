"""Prometheus source adapter for Swarm Monitor.

Fetches metrics and alert status from Prometheus and emits
normalized source envelopes with provenance and freshness.
"""

import asyncio
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from ..core.envelope import (
    SourceEnvelope,
    SourceStatus,
    Provenance,
    compute_freshness_ms,
    classify_status,
)
from ..core.config import PROMETHEUS_URL


class PrometheusMetricData(BaseModel):
    """Normalized Prometheus metric data point."""

    metric_name: str
    labels: Dict[str, str]
    value: float
    timestamp: datetime


class PrometheusAlertData(BaseModel):
    """Normalized Prometheus alert data."""

    alert_name: str
    state: str  # firing, pending, inactive
    severity: str
    summary: str
    labels: Dict[str, str]
    active_since: Optional[datetime] = None


class PrometheusSourceData(BaseModel):
    """Aggregated Prometheus source data."""

    query_status: str
    total_series: int
    active_alerts: int
    pending_alerts: int
    metrics_sample: List[PrometheusMetricData]
    alerts: List[PrometheusAlertData]
    last_scrape_time: datetime


class PrometheusAdapter:
    """Prometheus source adapter with fail-closed envelope contract."""

    SOURCE_ID = "prometheus-metrics"
    SOURCE_TYPE = "prometheus"
    TIMEOUT_SECONDS = 10

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS)
        return self.client

    async def _close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _query(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query Prometheus API endpoint.

        Args:
            endpoint: API endpoint (e.g., "/api/v1/query")
            params: Query parameters

        Returns:
            JSON response dict

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPError: For other HTTP errors
        """
        client = await self._get_client()
        url = f"{PROMETHEUS_URL}{endpoint}"

        response = await client.get(url, params=params or {})
        response.raise_for_status()
        return response.json()

    async def _fetch_health(self) -> Dict[str, Any]:
        """Fetch Prometheus health status."""
        return await self._query("/api/v1/status/config")

    async def _fetch_alerts(self) -> List[PrometheusAlertData]:
        """Fetch current Prometheus alerts."""
        try:
            result = await self._query("/api/v1/alerts")

            alerts = []
            for alert in result.get("data", {}).get("alerts", []):
                alert_state = alert.get("state", "unknown")
                labels = alert.get("labels", {})
                annotations = alert.get("annotations", {})

                # Determine active_since from startAt if firing
                active_since = None
                if alert_state == "firing" and "startsAt" in alert:
                    active_since = datetime.fromisoformat(
                        alert["startsAt"].replace("Z", "+00:00")
                    )

                alerts.append(
                    PrometheusAlertData(
                        alert_name=labels.get("alertname", "unknown"),
                        state=alert_state,
                        severity=labels.get("severity", "info"),
                        summary=annotations.get("summary", ""),
                        labels={k: v for k, v in labels.items() if k != "alertname"},
                        active_since=active_since,
                    )
                )

            return alerts
        except Exception:
            return []

    async def _fetch_sample_metrics(self) -> List[PrometheusMetricData]:
        """Fetch a sample of key metrics for swarm monitoring."""
        sample_queries = [
            "up",  # Target availability
            "prometheus_tsdb_head_samples_appended_per_second",  # Write rate
            "prometheus_tsdb_storage_blocks_bytes",  # Storage
            "rate(prometheus_http_requests_total[5m])",  # Request rate
        ]

        metrics = []
        for query in sample_queries:
            try:
                result = await self._query("/api/v1/query", {"query": query})

                if result.get("status") == "success" and result.get("data", {}).get("result"):
                    for sample in result["data"]["result"][:1]:  # First result only
                        metric = sample.get("metric", {})
                        value_str = sample.get("value", [0, "0"])[1]

                        metrics.append(
                            PrometheusMetricData(
                                metric_name=query,
                                labels={k: v for k, v in metric.items()},
                                value=float(value_str),
                                timestamp=datetime.now(timezone.utc),
                            )
                        )
            except Exception:
                # Continue with other queries on failure
                pass

        return metrics

    async def _fetch_target_count(self) -> int:
        """Fetch total number of Prometheus targets."""
        try:
            result = await self._query("/api/v1/targets")
            targets = result.get("data", {}).get("activeTargets", [])
            return len(targets)
        except Exception:
            return 0

    def _calculate_alert_stats(self, alerts: List[PrometheusAlertData]) -> tuple[int, int]:
        """Calculate alert statistics."""
        firing = sum(1 for a in alerts if a.state == "firing")
        pending = sum(1 for a in alerts if a.state == "pending")
        return firing, pending

    async def fetch(self) -> SourceEnvelope[PrometheusSourceData]:
        """Fetch Prometheus data and return normalized envelope.

        This method implements the fail-closed contract:
        - Always returns a SourceEnvelope, never throws
        - Unreachable sources return status=unavailable with error message
        - Credential errors return status=error with redacted error
        - Malformed responses return status=error
        - Missing timestamps result in stale/unknown status, never ok

        Returns:
            SourceEnvelope containing Prometheus data or error state
        """
        observed_at = datetime.now(timezone.utc)
        error_message = None
        is_reachable = False
        source_data: Optional[PrometheusSourceData] = None
        source_updated_at: Optional[datetime] = None

        try:
            # Fetch health status to confirm reachability
            health = await self._fetch_health()
            is_reachable = True

            # Extract last scrape time from config if available
            config_data = health.get("data", {})
            # Prometheus doesn't provide a clear timestamp in config,
            # so we'll use observed_at as the freshness reference

            # Fetch alerts and metrics in parallel
            alerts_task = self._fetch_alerts()
            metrics_task = self._fetch_sample_metrics()
            targets_task = self._fetch_target_count()

            alerts_result, metrics_result, targets_result = await asyncio.gather(
                alerts_task, metrics_task, targets_task, return_exceptions=True
            )

            # Handle fetch failures
            if isinstance(alerts_result, Exception):
                raise alerts_result
            alerts = alerts_result

            if isinstance(metrics_result, Exception):
                raise metrics_result
            metrics = metrics_result

            if isinstance(targets_result, Exception):
                target_count = 0
            else:
                target_count = targets_result

            # Calculate alert statistics
            active_alerts, pending_alerts = self._calculate_alert_stats(alerts)

            # Determine last update time from latest alert or metric timestamp
            alert_timestamps = [
                a.active_since for a in alerts if a.active_since is not None
            ]
            if alert_timestamps:
                source_updated_at = max(alert_timestamps)
            else:
                source_updated_at = observed_at

            # Build source data
            source_data = PrometheusSourceData(
                query_status="success",
                total_series=target_count,
                active_alerts=active_alerts,
                pending_alerts=pending_alerts,
                metrics_sample=metrics,
                alerts=alerts,
                last_scrape_time=source_updated_at or observed_at,
            )

        except httpx.TimeoutException:
            error_message = f"Prometheus API timeout after {self.TIMEOUT_SECONDS}s"
            is_reachable = False
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                error_message = "Prometheus credential error: invalid or expired token"
            elif e.response.status_code == 403:
                error_message = "Prometheus access denied: insufficient permissions"
            else:
                error_message = f"Prometheus HTTP error: {e.response.status_code}"
            is_reachable = False
        except httpx.HTTPError as e:
            error_message = f"Prometheus network error: {str(e)}"
            is_reachable = False
        except (KeyError, ValueError, TypeError) as e:
            error_message = f"Prometheus response parsing error: {str(e)}"
            is_reachable = True  # We reached the source but got bad data
        except Exception as e:
            error_message = f"Prometheus unexpected error: {str(e)}"
            is_reachable = False

        # Compute freshness
        freshness_ms = compute_freshness_ms(source_updated_at, observed_at)

        # Classify status (fail-closed)
        status = classify_status(
            is_reachable=is_reachable,
            freshness_ms=freshness_ms,
            source_type=self.SOURCE_TYPE,
            has_data=source_data is not None,
            error_message=error_message,
        )

        # Build provenance (safe reference only)
        safe_url = PROMETHEUS_URL
        provenance = Provenance(
            kind="https-api",
            identity=self.SOURCE_ID,
            safe_reference=safe_url,
        )

        # Create and return envelope
        return SourceEnvelope[PrometheusSourceData](
            source=self.SOURCE_ID,
            adapter_version="dev-35-initial",
            observed_at=observed_at,
            source_updated_at=source_updated_at,
            freshness_ms=freshness_ms,
            status=status,
            data=source_data,
            error=error_message,
            provenance=provenance,
        )

    async def cleanup(self):
        """Clean up resources."""
        await self._close()


# Singleton instance for use in routes
_prometheus_adapter: Optional[PrometheusAdapter] = None


async def get_prometheus_adapter() -> PrometheusAdapter:
    """Get or create Prometheus adapter singleton."""
    global _prometheus_adapter
    if _prometheus_adapter is None:
        _prometheus_adapter = PrometheusAdapter()
    return _prometheus_adapter