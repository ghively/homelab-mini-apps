"""GitLab source adapter for Swarm Monitor.

Fetches pipeline and merge request data from GitLab and emits
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
from ..core.config import GITLAB_URL, GITLAB_TOKEN, HOMELAB_ANSIBLE_PROJECT_ID


class GitLabPipelineData(BaseModel):
    """Normalized GitLab pipeline data."""

    pipeline_id: int
    sha: str
    ref: str
    status: str
    web_url: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class GitLabMergeRequestData(BaseModel):
    """Normalized GitLab merge request data."""

    iid: int
    title: str
    author: str
    source_branch: str
    web_url: str
    merge_status: str
    pipeline_status: Optional[str] = None
    updated_at: datetime


class GitLabSourceData(BaseModel):
    """Aggregated GitLab source data."""

    project_id: str
    project_name: str
    pipelines: List[GitLabPipelineData]
    merge_requests: List[GitLabMergeRequestData]
    last_activity_at: datetime


class GitLabAdapter:
    """GitLab source adapter with fail-closed envelope contract."""

    SOURCE_ID = f"gitlab-project-{HOMELAB_ANSIBLE_PROJECT_ID}"
    SOURCE_TYPE = "gitlab"
    TIMEOUT_SECONDS = 15
    MAX_PIPELINES = 5
    MAX_MRS = 10

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with GitLab token."""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=self.TIMEOUT_SECONDS)
        return self.client

    async def _close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with GitLab token."""
        return {"PRIVATE-TOKEN": GITLAB_TOKEN}

    async def _fetch_with_timeout(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Fetch from GitLab API with timeout handling.

        Args:
            path: API path (e.g., "/projects/113/pipelines")
            params: Query parameters

        Returns:
            JSON response dict

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPError: For other HTTP errors
        """
        client = await self._get_client()
        url = f"{GITLAB_URL}{path}"

        response = await client.get(
            url, headers=self._get_headers(), params=params or {}
        )
        response.raise_for_status()
        return response.json()

    async def _fetch_project(self) -> Dict[str, Any]:
        """Fetch project metadata."""
        return await self._fetch_with_timeout(f"/projects/{HOMELAB_ANSIBLE_PROJECT_ID}")

    async def _fetch_pipelines(self) -> List[Dict[str, Any]]:
        """Fetch recent pipelines."""
        return await self._fetch_with_timeout(
            f"/projects/{HOMELAB_ANSIBLE_PROJECT_ID}/pipelines",
            {"per_page": self.MAX_PIPELINES},
        )

    async def _fetch_merge_requests(self) -> List[Dict[str, Any]]:
        """Fetch open merge requests."""
        return await self._fetch_with_timeout(
            f"/projects/{HOMELAB_ANSIBLE_PROJECT_ID}/merge_requests",
            {"state": "opened", "per_page": self.MAX_MRS},
        )

    async def _fetch_mr_pipeline(self, mr_iid: int) -> Optional[Dict[str, Any]]:
        """Fetch pipeline status for a specific MR."""
        try:
            pipelines = await self._fetch_with_timeout(
                f"/projects/{HOMELAB_ANSIBLE_PROJECT_ID}/merge_requests/{mr_iid}/pipelines",
                {"per_page": 1},
            )
            return pipelines[0] if pipelines else None
        except Exception:
            return None

    def _parse_pipeline(self, raw: Dict[str, Any]) -> GitLabPipelineData:
        """Parse raw GitLab pipeline data into normalized format."""
        return GitLabPipelineData(
            pipeline_id=raw["id"],
            sha=raw["sha"][:8],
            ref=raw["ref"],
            status=raw["status"],
            web_url=raw["web_url"],
            created_at=datetime.fromisoformat(raw["created_at"].replace("Z", "+00:00")),
            updated_at=(
                datetime.fromisoformat(raw["updated_at"].replace("Z", "+00:00"))
                if "updated_at" in raw
                else None
            ),
        )

    def _parse_merge_request(
        self, raw: Dict[str, Any], pipeline_status: Optional[str]
    ) -> GitLabMergeRequestData:
        """Parse raw GitLab MR data into normalized format."""
        return GitLabMergeRequestData(
            iid=raw["iid"],
            title=raw["title"],
            author=raw["author"]["username"],
            source_branch=raw["source_branch"],
            web_url=raw["web_url"],
            merge_status=raw["merge_status"],
            pipeline_status=pipeline_status,
            updated_at=datetime.fromisoformat(raw["updated_at"].replace("Z", "+00:00")),
        )

    async def fetch(self) -> SourceEnvelope[GitLabSourceData]:
        """Fetch GitLab data and return normalized envelope.

        This method implements the fail-closed contract:
        - Always returns a SourceEnvelope, never throws
        - Unreachable sources return status=unavailable with error message
        - Credential errors return status=error with redacted error
        - Malformed responses return status=error
        - Missing timestamps result in stale/unknown status, never ok

        Returns:
            SourceEnvelope containing GitLab data or error state
        """
        observed_at = datetime.now(timezone.utc)
        error_message = None
        is_reachable = False
        source_data: Optional[GitLabSourceData] = None
        source_updated_at: Optional[datetime] = None

        try:
            # Fetch project metadata
            project = await self._fetch_project()
            project_name = project.get("name", f"project-{HOMELAB_ANSIBLE_PROJECT_ID}")
            last_activity_str = project.get("last_activity_at")

            # Fetch pipelines and MRs in parallel
            pipelines_task = self._fetch_pipelines()
            mrs_task = self._fetch_merge_requests()

            pipelines_raw, mrs_raw = await asyncio.gather(
                pipelines_task, mrs_task, return_exceptions=True
            )

            # Handle fetch failures
            if isinstance(pipelines_raw, Exception):
                raise pipelines_raw
            if isinstance(mrs_raw, Exception):
                raise mrs_raw

            # Parse pipelines
            pipelines = [self._parse_pipeline(p) for p in pipelines_raw]

            # Fetch and parse MRs with their pipeline status
            mrs = []
            for mr_raw in mrs_raw:
                mr_pipeline = await self._fetch_mr_pipeline(mr_raw["iid"])
                pipeline_status = mr_pipeline["status"] if mr_pipeline else None
                mrs.append(self._parse_merge_request(mr_raw, pipeline_status))

            # Determine last update time
            if last_activity_str:
                source_updated_at = datetime.fromisoformat(
                    last_activity_str.replace("Z", "+00:00")
                )
            elif pipelines:
                source_updated_at = max(p.created_at for p in pipelines)
            elif mrs:
                source_updated_at = max(mr.updated_at for mr in mrs)

            # Build source data
            source_data = GitLabSourceData(
                project_id=HOMELAB_ANSIBLE_PROJECT_ID,
                project_name=project_name,
                pipelines=pipelines,
                merge_requests=mrs,
                last_activity_at=source_updated_at or observed_at,
            )

            is_reachable = True

        except httpx.TimeoutException:
            error_message = f"GitLab API timeout after {self.TIMEOUT_SECONDS}s"
            is_reachable = False
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                error_message = "GitLab credential error: invalid or expired token"
            elif e.response.status_code == 403:
                error_message = "GitLab access denied: insufficient permissions"
            elif e.response.status_code == 404:
                error_message = (
                    f"GitLab project {HOMELAB_ANSIBLE_PROJECT_ID} not found"
                )
            else:
                error_message = f"GitLab HTTP error: {e.response.status_code}"
            is_reachable = False
        except httpx.HTTPError as e:
            error_message = f"GitLab network error: {str(e)}"
            is_reachable = False
        except (KeyError, ValueError, TypeError) as e:
            error_message = f"GitLab response parsing error: {str(e)}"
            is_reachable = True  # We reached the source but got bad data
        except Exception as e:
            error_message = f"GitLab unexpected error: {str(e)}"
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
        safe_url = f"{GITLAB_URL.split('/api/v4')[0]}/projects/{HOMELAB_ANSIBLE_PROJECT_ID}"
        provenance = Provenance(
            kind="https-api",
            identity=self.SOURCE_ID,
            safe_reference=safe_url,
        )

        # Create and return envelope
        return SourceEnvelope[GitLabSourceData](
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
_gitlab_adapter: Optional[GitLabAdapter] = None


async def get_gitlab_adapter() -> GitLabAdapter:
    """Get or create GitLab adapter singleton."""
    global _gitlab_adapter
    if _gitlab_adapter is None:
        _gitlab_adapter = GitLabAdapter()
    return _gitlab_adapter