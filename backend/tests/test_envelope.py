"""Tests for source envelope schema and fail-closed contract.

Tests verify:
- Envelope schema validation
- Status classification (ok, stale, error, unavailable, unknown)
- Freshness computation
- Fail-closed behavior (unavailable/error/unknown never render healthy)
"""

import pytest
from datetime import datetime, timedelta
from app.core.envelope import (
    SourceEnvelope,
    SourceStatus,
    Provenance,
    compute_freshness_ms,
    classify_status,
    STALENESS_THRESHOLDS_MS,
)


class TestSourceEnvelope:
    """Test SourceEnvelope schema and validation."""

    def test_minimal_envelope(self):
        """Test creating a minimal valid envelope."""
        envelope = SourceEnvelope(
            source="test-source",
            adapter_version="v1.0.0",
            observed_at=datetime.utcnow(),
            source_updated_at=None,
            freshness_ms=STALENESS_THRESHOLDS_MS["default"],
            status=SourceStatus.UNKNOWN,
            data=None,
            error="Source unreachable",
            provenance=Provenance(
                kind="https-api",
                identity="test-source",
                safe_reference="https://api.example.com/test",
            ),
        )

        assert envelope.source == "test-source"
        assert envelope.status == SourceStatus.UNKNOWN
        assert not envelope.is_healthy()

    def test_healthy_envelope(self):
        """Test creating a healthy envelope."""
        source_updated = datetime.utcnow() - timedelta(minutes=5)
        observed = datetime.utcnow()

        envelope = SourceEnvelope(
            source="gitlab-project-113",
            adapter_version="abc123",
            observed_at=observed,
            source_updated_at=source_updated,
            freshness_ms=compute_freshness_ms(source_updated, observed),
            status=SourceStatus.OK,
            data={"project_id": "113"},
            error=None,
            provenance=Provenance(
                kind="https-api",
                identity="gitlab-project-113",
                safe_reference="https://git.hively.dev/api/v4/projects/113",
            ),
        )

        assert envelope.is_healthy()
        assert envelope.status == SourceStatus.OK
        assert envelope.data is not None

    def test_stale_envelope_not_healthy(self):
        """Test that stale envelope is not healthy."""
        source_updated = datetime.utcnow() - timedelta(hours=2)
        observed = datetime.utcnow()

        envelope = SourceEnvelope(
            source="test-source",
            adapter_version="v1.0.0",
            observed_at=observed,
            source_updated_at=source_updated,
            freshness_ms=compute_freshness_ms(source_updated, observed),
            status=SourceStatus.STALE,
            data={"test": "data"},
            error=None,
            provenance=Provenance(
                kind="https-api",
                identity="test-source",
                safe_reference="https://api.example.com/test",
            ),
        )

        assert not envelope.is_healthy()
        assert envelope.status == SourceStatus.STALE

    def test_error_envelope_not_healthy(self):
        """Test that error envelope is not healthy."""
        envelope = SourceEnvelope(
            source="test-source",
            adapter_version="v1.0.0",
            observed_at=datetime.utcnow(),
            source_updated_at=None,
            freshness_ms=0,
            status=SourceStatus.ERROR,
            data=None,
            error="HTTP 500",
            provenance=Provenance(
                kind="https-api",
                identity="test-source",
                safe_reference="https://api.example.com/test",
            ),
        )

        assert not envelope.is_healthy()
        assert envelope.status == SourceStatus.ERROR
        assert envelope.error == "HTTP 500"

    def test_unavailable_envelope_not_healthy(self):
        """Test that unavailable envelope is not healthy."""
        envelope = SourceEnvelope(
            source="test-source",
            adapter_version="v1.0.0",
            observed_at=datetime.utcnow(),
            source_updated_at=None,
            freshness_ms=0,
            status=SourceStatus.UNAVAILABLE,
            data=None,
            error="Connection timeout",
            provenance=Provenance(
                kind="https-api",
                identity="test-source",
                safe_reference="https://api.example.com/test",
            ),
        )

        assert not envelope.is_healthy()
        assert envelope.status == SourceStatus.UNAVAILABLE


class TestComputeFreshness:
    """Test freshness computation."""

    def test_freshness_within_threshold(self):
        """Test freshness for recent data."""
        source_updated = datetime.utcnow() - timedelta(minutes=5)
        observed = datetime.utcnow()

        freshness = compute_freshness_ms(source_updated, observed)

        assert freshness > 0
        assert freshness < 600000  # < 10 minutes
        assert freshness == int((observed - source_updated).total_seconds() * 1000)

    def test_freshness_stale(self):
        """Test freshness for stale data."""
        source_updated = datetime.utcnow() - timedelta(hours=2)
        observed = datetime.utcnow()

        freshness = compute_freshness_ms(source_updated, observed)

        assert freshness > STALENESS_THRESHOLDS_MS["prometheus"]
        assert freshness > STALENESS_THRESHOLDS_MS["gitlab"]

    def test_freshness_null_source_time(self):
        """Test freshness when source time is unknown."""
        observed = datetime.utcnow()

        freshness = compute_freshness_ms(None, observed)

        # Should return a large value (treated as very stale)
        assert freshness >= STALENESS_THRESHOLDS_MS["default"] * 2


class TestClassifyStatus:
    """Test status classification with fail-closed behavior."""

    def test_unreachable_source(self):
        """Test unreachable source is UNAVAILABLE."""
        status = classify_status(
            is_reachable=False,
            freshness_ms=0,
            source_type="prometheus",
            has_data=False,
            error_message="Connection refused",
        )

        assert status == SourceStatus.UNAVAILABLE

    def test_unreachable_source_no_error(self):
        """Test unreachable source without error is UNKNOWN."""
        status = classify_status(
            is_reachable=False,
            freshness_ms=0,
            source_type="prometheus",
            has_data=False,
            error_message=None,
        )

        assert status == SourceStatus.UNKNOWN

    def test_error_with_message(self):
        """Test error with message is ERROR status."""
        status = classify_status(
            is_reachable=True,
            freshness_ms=0,
            source_type="prometheus",
            has_data=False,
            error_message="HTTP 500 Internal Server Error",
        )

        assert status == SourceStatus.ERROR

    def test_no_data_reachable(self):
        """Test reachable but no data is UNKNOWN."""
        status = classify_status(
            is_reachable=True,
            freshness_ms=0,
            source_type="prometheus",
            has_data=False,
            error_message=None,
        )

        assert status == SourceStatus.UNKNOWN

    def test_fresh_within_threshold(self):
        """Test fresh data within threshold is OK."""
        status = classify_status(
            is_reachable=True,
            freshness_ms=100000,  # 100 seconds
            source_type="prometheus",
            has_data=True,
            error_message=None,
        )

        assert status == SourceStatus.OK

    def test_stale_data(self):
        """Test stale data beyond threshold is STALE."""
        status = classify_status(
            is_reachable=True,
            freshness_ms=600000,  # 10 minutes
            source_type="prometheus",  # 5-minute threshold
            has_data=True,
            error_message=None,
        )

        assert status == SourceStatus.STALE

    def test_fail_closed_unavailable_never_ok(self):
        """Test fail-closed: unavailable sources never return OK."""
        # Various failure scenarios
        scenarios = [
            (False, 0, "prometheus", False, "Connection refused"),  # Unreachable
            (False, 0, "prometheus", False, None),  # Unreachable no error
            (True, 0, "prometheus", False, "HTTP 500"),  # Error
            (True, 0, "prometheus", False, None),  # No data
        ]

        for reachable, freshness, source_type, has_data, error in scenarios:
            status = classify_status(reachable, freshness, source_type, has_data, error)
            assert status != SourceStatus.OK, f"Failed for {reachable, freshness, source_type, has_data, error}"

    def test_thresholds_by_source_type(self):
        """Test that different source types use appropriate thresholds."""
        # Fresh data for GitLab (30-min threshold)
        status_gitlab = classify_status(
            is_reachable=True,
            freshness_ms=1800000 - 1000,  # Just under 30 min
            source_type="gitlab",
            has_data=True,
            error_message=None,
        )
        assert status_gitlab == SourceStatus.OK

        # Same freshness for Prometheus (5-min threshold) should be stale
        status_prometheus = classify_status(
            is_reachable=True,
            freshness_ms=1800000 - 1000,
            source_type="prometheus",
            has_data=True,
            error_message=None,
        )
        assert status_prometheus == SourceStatus.STALE

    def test_default_threshold(self):
        """Test default threshold for unknown source types."""
        # Fresh data under default threshold (1 hour)
        status = classify_status(
            is_reachable=True,
            freshness_ms=1800000,  # 30 minutes
            source_type="unknown_type",
            has_data=True,
            error_message=None,
        )
        assert status == SourceStatus.OK

        # Stale data over default threshold
        status = classify_status(
            is_reachable=True,
            freshness_ms=3700000,  # 61 minutes
            source_type="unknown_type",
            has_data=True,
            error_message=None,
        )
        assert status == SourceStatus.STALE


class TestFailClosedContract:
    """Test fail-closed contract enforcement."""

    def test_only_ok_status_is_healthy(self):
        """Test that only OK status returns True from is_healthy()."""
        non_ok_statuses = [
            SourceStatus.STALE,
            SourceStatus.ERROR,
            SourceStatus.UNAVAILABLE,
            SourceStatus.DEFERRED,
            SourceStatus.UNKNOWN,
        ]

        for status in non_ok_statuses:
            envelope = SourceEnvelope(
                source="test",
                adapter_version="v1.0.0",
                observed_at=datetime.utcnow(),
                source_updated_at=None,
                freshness_ms=0,
                status=status,
                data=None,
                error=None,
                provenance=Provenance(
                    kind="test",
                    identity="test",
                    safe_reference="test",
                ),
            )

            assert not envelope.is_healthy(), f"{status} should not be healthy"

    def test_correlation_id_present(self):
        """Test that correlation ID is automatically generated."""
        envelope1 = SourceEnvelope(
            source="test",
            adapter_version="v1.0.0",
            observed_at=datetime.utcnow(),
            source_updated_at=None,
            freshness_ms=0,
            status=SourceStatus.OK,
            data={},
            error=None,
            provenance=Provenance(
                kind="test",
                identity="test",
                safe_reference="test",
            ),
        )

        envelope2 = SourceEnvelope(
            source="test",
            adapter_version="v1.0.0",
            observed_at=datetime.utcnow(),
            source_updated_at=None,
            freshness_ms=0,
            status=SourceStatus.OK,
            data={},
            error=None,
            provenance=Provenance(
                kind="test",
                identity="test",
                safe_reference="test",
            ),
        )

        assert envelope1.correlation_id
        assert envelope2.correlation_id
        assert envelope1.correlation_id != envelope2.correlation_id