"""Test fixtures for source adapter failure modes.

Provides seeded fixtures for timeout, malformed responses, poisoned data,
and credential errors. Fixtures are deterministic and designed to fail closed.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, Mock
import httpx
import pytest


# ============================================================================
# TIMEOUT FIXTURES
# ============================================================================

@pytest.fixture
async def mock_gitlab_timeout():
    """Fixture simulating GitLab API timeout."""
    async def mock_fetch():
        raise httpx.TimeoutException("GitLab API timeout after 15s")

    return mock_fetch


@pytest.fixture
async def mock_prometheus_timeout():
    """Fixture simulating Prometheus API timeout."""
    async def mock_fetch():
        raise httpx.TimeoutException("Prometheus API timeout after 10s")

    return mock_fetch


# ============================================================================
# CREDENTIAL ERROR FIXTURES
# ============================================================================

@pytest.fixture
async def mock_gitlab_401_error():
    """Fixture simulating GitLab 401 credential error."""
    response = Mock(spec=httpx.Response)
    response.status_code = 401

    async def mock_fetch():
        raise httpx.HTTPStatusError(
            "GitLab credential error: invalid or expired token",
            request=Mock(),
            response=response,
        )

    return mock_fetch


@pytest.fixture
async def mock_gitlab_403_error():
    """Fixture simulating GitLab 403 access denied error."""
    response = Mock(spec=httpx.Response)
    response.status_code = 403

    async def mock_fetch():
        raise httpx.HTTPStatusError(
            "GitLab access denied: insufficient permissions",
            request=Mock(),
            response=response,
        )

    return mock_fetch


@pytest.fixture
async def mock_gitlab_404_error():
    """Fixture simulating GitLab 404 project not found error."""
    response = Mock(spec=httpx.Response)
    response.status_code = 404

    async def mock_fetch():
        raise httpx.HTTPStatusError(
            "GitLab project 113 not found",
            request=Mock(),
            response=response,
        )

    return mock_fetch


@pytest.fixture
async def mock_prometheus_401_error():
    """Fixture simulating Prometheus 401 credential error."""
    response = Mock(spec=httpx.Response)
    response.status_code = 401

    async def mock_fetch():
        raise httpx.HTTPStatusError(
            "Prometheus credential error: invalid or expired token",
            request=Mock(),
            response=response,
        )

    return mock_fetch


@pytest.fixture
async def mock_prometheus_403_error():
    """Fixture simulating Prometheus 403 access denied error."""
    response = Mock(spec=httpx.Response)
    response.status_code = 403

    async def mock_fetch():
        raise httpx.HTTPStatusError(
            "Prometheus access denied: insufficient permissions",
            request=Mock(),
            response=response,
        )

    return mock_fetch


# ============================================================================
# MALFORMED RESPONSE FIXTURES
# ============================================================================

@pytest.fixture
async def mock_gitlab_malformed_json():
    """Fixture simulating GitLab malformed JSON response."""
    async def mock_fetch():
        # Simulate malformed JSON that causes parsing error
        raise ValueError("Expecting value: line 1 column 1 (char 0)")

    return mock_fetch


@pytest.fixture
async def mock_gitlab_missing_required_fields():
    """Fixture simulating GitLab response missing required fields."""
    async def mock_fetch():
        # Simulate response missing 'id' field
        project_data = {"name": "homelab-infra"}  # Missing 'last_activity_at'
        raise KeyError("last_activity_at")

    return mock_fetch


@pytest.fixture
async def mock_prometheus_malformed_response():
    """Fixture simulating Prometheus malformed response."""
    async def mock_fetch():
        # Simulate malformed query response
        result = {"status": "error"}  # Missing 'data' field
        raise KeyError("data")

    return mock_fetch


@pytest.fixture
async def mock_prometheus_invalid_metric_value():
    """Fixture simulating Prometheus invalid metric value."""
    async def mock_fetch():
        # Simulate non-numeric metric value
        raise ValueError("could not convert string to float: 'not-a-number'")

    return mock_fetch


# ============================================================================
# POISONED DATA FIXTURES
# ============================================================================

@pytest.fixture
async def mock_gitlab_poisoned_pipeline():
    """Fixture simulating GitLab poisoned pipeline data with script injection."""
    async def mock_fetch():
        # Simulate malicious data in pipeline name
        return {
            "id": 123,
            "sha": "<script>alert('xss')</script>abc12345",
            "ref": "main-$(rm -rf /)",
            "status": "success",
            "web_url": "https://gitlab.example.com/pipelines/123",
            "created_at": "2026-07-26T12:00:00Z",
        }

    return mock_fetch


@pytest.fixture
async def mock_gitlab_poisoned_mr_title():
    """Fixture simulating GitLab poisoned MR title with SQL injection."""
    async def mock_fetch():
        # Simulate malicious data in MR title
        return {
            "iid": 456,
            "title": "'; DROP TABLE pipelines; --",
            "author": {"username": "attacker"},
            "source_branch": "malicious",
            "web_url": "https://gitlab.example.com/merge_requests/456",
            "merge_status": "can_be_merged",
            "updated_at": "2026-07-26T12:00:00Z",
        }

    return mock_fetch


@pytest.fixture
async def mock_prometheus_poisoned_alert():
    """Fixture simulating Prometheus poisoned alert data."""
    async def mock_fetch():
        # Simulate malicious data in alert labels
        return {
            "alertname": "HighCPU",
            "state": "firing",
            "severity": "critical",
            "labels": {
                "instance": "server-1;rm -rf /;#",
                "job": "node-exporter</script>",
            },
            "summary": "CPU usage above 90%",
            "startsAt": "2026-07-26T12:00:00Z",
        }

    return mock_fetch


@pytest.fixture
async def mock_prometheus_poisoned_metric():
    """Fixture simulating Prometheus poisoned metric data."""
    async def mock_fetch():
        # Simulate malicious data in metric name
        return {
            "metric": {
                "__name__": "up; DROP DATABASE; #",
                "instance": "server-1",
            },
            "value": [1721980800, "1"],
        }

    return mock_fetch


# ============================================================================
# NETWORK ERROR FIXTURES
# ============================================================================

@pytest.fixture
async def mock_gitlab_connection_error():
    """Fixture simulating GitLab network connection error."""
    async def mock_fetch():
        raise httpx.ConnectError("Failed to establish connection to gitlab.example.com")

    return mock_fetch


@pytest.fixture
async def mock_prometheus_connection_error():
    """Fixture simulating Prometheus network connection error."""
    async def mock_fetch():
        raise httpx.ConnectError("Failed to establish connection to 192.0.2.50:9090")

    return mock_fetch


# ============================================================================
# SUCCESS FIXTURES (for comparison and baseline testing)
# ============================================================================

@pytest.fixture
def mock_gitlab_success_response():
    """Fixture for successful GitLab response."""
    now = datetime.now(timezone.utc)
    return {
        "id": 12345,
        "sha": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
        "ref": "main",
        "status": "success",
        "web_url": "https://gitlab.example.com/pipelines/12345",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


@pytest.fixture
def mock_prometheus_success_response():
    """Fixture for successful Prometheus response."""
    now = datetime.now(timezone.utc)
    return {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"__name__": "up", "instance": "localhost:9090"},
                    "value": [int(now.timestamp()), "1"],
                }
            ],
        },
    }


@pytest.fixture
def mock_gitlab_project_metadata():
    """Fixture for GitLab project metadata."""
    now = datetime.now(timezone.utc)
    return {
        "id": 113,
        "name": "homelab-infra",
        "last_activity_at": now.isoformat(),
    }


@pytest.fixture
def mock_prometheus_health_response():
    """Fixture for Prometheus health check response."""
    return {
        "status": "success",
        "data": {
            "yaml": "global:\n  scrape_interval: 15s\n",
        },
    }


# ============================================================================
# STALENESS FIXTURES
# ============================================================================

@pytest.fixture
def mock_gitlab_stale_data():
    """Fixture simulating stale GitLab data (old timestamp)."""
    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    return {
        "id": 12345,
        "sha": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
        "ref": "main",
        "status": "success",
        "web_url": "https://gitlab.example.com/pipelines/12345",
        "created_at": old_time.isoformat(),
        "updated_at": old_time.isoformat(),
    }


@pytest.fixture
def mock_prometheus_stale_data():
    """Fixture simulating stale Prometheus data (old timestamp)."""
    old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    return {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"__name__": "up", "instance": "localhost:9090"},
                    "value": [int(old_time.timestamp()), "1"],
                }
            ],
        },
    }


# ============================================================================
# NULL/MISSING TIMESTAMP FIXTURES
# ============================================================================

@pytest.fixture
def mock_gitlab_missing_timestamp():
    """Fixture simulating GitLab data with missing timestamp."""
    return {
        "id": 12345,
        "sha": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
        "ref": "main",
        "status": "success",
        "web_url": "https://gitlab.example.com/pipelines/12345",
        # Missing created_at/updated_at
    }


@pytest.fixture
def mock_prometheus_missing_timestamp():
    """Fixture simulating Prometheus data with missing timestamp."""
    return {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"__name__": "up", "instance": "localhost:9090"},
                    "value": [0, "1"],  # Invalid timestamp
                }
            ],
        },
    }