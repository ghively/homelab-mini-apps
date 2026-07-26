"""IaC Pipeline Approval Gate — GitLab CI pipeline status and MR management."""

import asyncio
import httpx
from fastapi import APIRouter, Depends
from ..core.auth_secure import get_authenticated_user
from ..core.config import GITLAB_URL, GITLAB_TOKEN, HOMELAB_ANSIBLE_PROJECT_ID

router = APIRouter()


def _headers():
    return {"PRIVATE-TOKEN": GITLAB_TOKEN}


async def gitlab_get(path: str, params: dict = None):
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{GITLAB_URL}{path}", headers=_headers(), params=params or {})
        r.raise_for_status()
        return r.json()


async def gitlab_post(path: str, json_body: dict = None):
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            f"{GITLAB_URL}{path}", headers=_headers(), json=json_body or {}
        )
        r.raise_for_status()
        return r.json()


@router.get("/status")
async def pipeline_status(user = Depends(get_authenticated_user)):
    """Get overall pipeline status: latest pipelines + open MRs."""
    pid = HOMELAB_ANSIBLE_PROJECT_ID

    # Fetch pipelines and MRs in parallel
    pipelines_task = gitlab_get(f"/projects/{pid}/pipelines", {"per_page": 5})
    mrs_task = gitlab_get(
        f"/projects/{pid}/merge_requests", {"state": "opened", "per_page": 10}
    )

    pipelines, mrs = await asyncio.gather(
        pipelines_task, mrs_task, return_exceptions=True
    )

    # Fetch detailed info for each MR
    mr_details = []
    if not isinstance(mrs, Exception):
        for mr in mrs:
            # Get pipeline status for this MR
            try:
                mr_pipelines = await gitlab_get(
                    f"/projects/{pid}/merge_requests/{mr['iid']}/pipelines",
                    {"per_page": 1},
                )
                pipeline_status = mr_pipelines[0]["status"] if mr_pipelines else "none"
            except Exception:
                pipeline_status = "unknown"

            mr_details.append(
                {
                    "iid": mr["iid"],
                    "title": mr["title"],
                    "author": mr["author"]["username"],
                    "source_branch": mr["source_branch"],
                    "web_url": mr["web_url"],
                    "pipeline_status": pipeline_status,
                    "merge_status": mr["merge_status"],
                    "changes_count": mr.get("changes_count", "?"),
                }
            )

    pipeline_list = []
    if not isinstance(pipelines, Exception):
        for p in pipelines:
            pipeline_list.append(
                {
                    "id": p["id"],
                    "sha": p["sha"][:8],
                    "ref": p["ref"],
                    "status": p["status"],
                    "web_url": p["web_url"],
                    "created_at": p["created_at"],
                }
            )

    return {
        "pipelines": pipeline_list,
        "merge_requests": mr_details,
    }


@router.get("/mr/{iid}/diff")
async def mr_diff(iid: int, user = Depends(get_authenticated_user)):
    """Get diff for a specific MR."""
    pid = HOMELAB_ANSIBLE_PROJECT_ID
    changes = await gitlab_get(f"/projects/{pid}/merge_requests/{iid}/changes")

    diff_files = []
    for ch in changes.get("changes", []):
        diff_files.append(
            {
                "old_path": ch["old_path"],
                "new_path": ch["new_path"],
                "diff": ch["diff"],
                "new_file": ch["new_file"],
                "deleted_file": ch["deleted_file"],
                "renamed_file": ch["renamed_file"],
            }
        )

    return {
        "iid": changes["iid"],
        "title": changes["title"],
        "description": changes["description"],
        "changes": diff_files,
    }


@router.post("/mr/{iid}/merge")
async def merge_mr(iid: int, user = Depends(get_authenticated_user)):
    """Merge a merge request."""
    pid = HOMELAB_ANSIBLE_PROJECT_ID
    result = await gitlab_post(
        f"/projects/{pid}/merge_requests/{iid}/merge",
        {"should_remove_source_branch": True},
    )
    return {"success": True, "mr": result}


@router.post("/pipeline/{pipeline_id}/retry")
async def retry_pipeline(
    pipeline_id: int, user = Depends(get_authenticated_user)
):
    """Retry a failed pipeline."""
    pid = HOMELAB_ANSIBLE_PROJECT_ID
    result = await gitlab_post(f"/projects/{pid}/pipelines/{pipeline_id}/retry")
    return {"success": True, "pipeline": result}
