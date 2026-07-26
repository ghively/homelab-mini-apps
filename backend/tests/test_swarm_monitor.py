"""Tests for Swarm Monitor adapters — fail-closed contract verification."""

import os
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.envelope import SourceStatus
from app.services.swarm_monitor import (
    fetch_gitlab,
    fetch_prometheus,
    fetch_all,
    ADAPTER_VERSION,
)


class TestGitLabAdapterFailClosed:
    """GitLab adapter must fail closed when token is missing."""

    def test_gitlab_unavailable_without_token(self):
        """Missing GITLAB_TOKEN returns UNAVAILABLE, not OK."""
        with patch.dict(os.environ, {}, clear=True):

            async def run():
                async with httpx.AsyncClient() as client:
                    envelope = await fetch_gitlab(client)
                    return envelope

            result = asyncio.run(run())
        assert result.status == SourceStatus.UNAVAILABLE
        assert "GITLAB_TOKEN" in result.error
        assert not result.is_healthy()
        assert result.data is None

    def test_gitlab_envelope_has_provenance(self):
        """Every envelope must include provenance metadata."""
        with patch.dict(os.environ, {}, clear=True):

            async def run():
                async with httpx.AsyncClient() as client:
                    return await fetch_gitlab(client)

            result = asyncio.run(run())
        assert result.provenance is not None
        assert result.provenance.kind == "https-api"
        assert "gitlab" in result.provenance.identity

    def test_gitlab_adapter_version_set(self):
        """Adapter must declare its version."""
        with patch.dict(os.environ, {}, clear=True):

            async def run():
                async with httpx.AsyncClient() as client:
                    return await fetch_gitlab(client)

            result = asyncio.run(run())
        assert result.adapter_version == ADAPTER_VERSION


class TestPrometheusAdapterFailClosed:
    """Prometheus adapter must fail closed when unreachable."""

    def test_prometheus_unreachable_returns_unavailable(self):
        """Unreachable Prometheus returns UNAVAILABLE, not OK."""

        async def run():
            async with httpx.AsyncClient() as client:
                # Point at a port nothing is on
                return await fetch_prometheus(client, "http://127.0.0.1:39999")

        result = asyncio.run(run())
        assert result.status == SourceStatus.UNAVAILABLE
        assert not result.is_healthy()
        assert result.data is None

    def test_prometheus_envelope_has_provenance(self):
        """Every envelope must include provenance metadata."""

        async def run():
            async with httpx.AsyncClient() as client:
                return await fetch_prometheus(client, "http://127.0.0.1:39999")

        result = asyncio.run(run())
        assert result.provenance is not None
        assert result.provenance.kind == "https-api"
        assert "prometheus" in result.provenance.identity


class TestAggregator:
    """Aggregator must return all envelopes even on failure."""

    def test_fetch_all_returns_two_sources(self):
        """Aggregator must return exactly two source envelopes."""
        result = asyncio.run(fetch_all())
        assert len(result["sources"]) == 2
        assert result["summary"]["total_sources"] == 2

    def test_fetch_all_never_crashes(self):
        """Aggregator must return even when both sources fail."""
        result = asyncio.run(fetch_all())
        # Both may fail, but must not crash
        assert "sources" in result
        assert "summary" in result

    def test_unhealthy_never_reports_healthy(self):
        """When sources are unavailable, is_healthy() must return False."""
        result = asyncio.run(fetch_all())
        for envelope in result["sources"]:
            if envelope.status in (
                SourceStatus.UNAVAILABLE,
                SourceStatus.ERROR,
                SourceStatus.UNKNOWN,
            ):
                assert not envelope.is_healthy()


class TestEnvelopeContract:
    """Verify the source envelope contract is met by all adapters."""

    def test_gitlab_envelope_is_serializable(self):
        """Envelopes must be JSON serializable for API responses."""
        with patch.dict(os.environ, {}, clear=True):

            async def run():
                async with httpx.AsyncClient() as client:
                    return await fetch_gitlab(client)

            result = asyncio.run(run())
        # Pydantic models are serializable
        data = result.model_dump(mode="json")
        assert "source" in data
        assert "status" in data
        assert "provenance" in data

    def test_prometheus_envelope_is_serializable(self):
        """Envelopes must be JSON serializable for API responses."""

        async def run():
            async with httpx.AsyncClient() as client:
                return await fetch_prometheus(client, "http://127.0.0.1:39999")

        result = asyncio.run(run())
        data = result.model_dump(mode="json")
        assert "source" in data
        assert "status" in data
        assert "provenance" in data
