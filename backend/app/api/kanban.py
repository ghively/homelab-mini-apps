"""Jira OPS Kanban Board — Jira + Vikunja integration."""

import asyncio
import base64
import httpx
from fastapi import APIRouter, Depends
from ..core.auth_secure import get_authenticated_user
from ..core.config import (
    JIRA_URL,
    JIRA_EMAIL,
    JIRA_API_TOKEN,
    VIKUNJA_URL,
    VIKUNJA_TOKEN,
)

router = APIRouter()


def _jira_headers():
    token = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _vikunja_headers():
    return {"Authorization": f"Bearer {VIKUNJA_TOKEN}"}


@router.get("/jira/board")
async def jira_board(user = Depends(get_authenticated_user)):
    """Get all OPS issues grouped by status."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(
            f"{JIRA_URL}/rest/api/3/search",
            headers=_jira_headers(),
            params={
                "jql": "project = OPS ORDER BY updated DESC",
                "fields": "summary,status,assignee,labels,priority,updated,created",
                "maxResults": 50,
            },
        )
        r.raise_for_status()
        data = r.json()

    columns = {}
    for issue in data.get("issues", []):
        status_name = issue["fields"]["status"]["name"]
        col = columns.setdefault(status_name, [])
        col.append(
            {
                "key": issue["key"],
                "summary": issue["fields"]["summary"],
                "labels": issue["fields"].get("labels", []),
                "priority": issue["fields"].get("priority", {}).get("name", "None"),
                "assignee": issue["fields"]
                .get("assignee", {})
                .get("displayName", "Unassigned"),
                "updated": issue["fields"].get("updated", ""),
            }
        )

    return {"columns": columns, "total": data.get("total", 0)}


@router.post("/jira/transition/{issue_key}")
async def jira_transition(
    issue_key: str, body: dict, user = Depends(get_authenticated_user)
):
    """Transition a Jira issue to a new status."""
    transition_id = body.get("transition_id")
    if not transition_id:
        raise ValueError("transition_id required")

    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions",
            headers=_jira_headers(),
            json={"transition": {"id": transition_id}},
        )
        r.raise_for_status()

    return {"success": True, "issue": issue_key, "transitioned_to": transition_id}


@router.get("/jira/transitions/{issue_key}")
async def jira_get_transitions(
    issue_key: str, user = Depends(get_authenticated_user)
):
    """Get available transitions for an issue."""
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(
            f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions",
            headers=_jira_headers(),
        )
        r.raise_for_status()
        data = r.json()

    return {
        "transitions": [
            {"id": t["id"], "name": t["name"], "to": t["to"]["name"]}
            for t in data.get("transitions", [])
        ]
    }


@router.post("/jira/comment/{issue_key}")
async def jira_comment(
    issue_key: str, body: dict, user = Depends(get_authenticated_user)
):
    """Add a comment to a Jira issue."""
    text = body.get("text", "")
    if not text:
        raise ValueError("text required")

    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": text}]}
            ],
        }
    }

    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            f"{JIRA_URL}/rest/api/3/issue/{issue_key}/comment",
            headers=_jira_headers(),
            json=payload,
        )
        r.raise_for_status()

    return {"success": True}


@router.get("/vikunja/tasks")
async def vikunja_tasks(user = Depends(get_authenticated_user)):
    """Get Vikunja tasks (Gregory's board)."""
    if not VIKUNJA_TOKEN:
        return {"tasks": [], "note": "Vikunja token not configured"}

    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.get(
            f"{VIKUNJA_URL}/tasks", headers=_vikunja_headers(), params={"sort": "done"}
        )
        r.raise_for_status()
        tasks = r.json()

    return {"tasks": tasks[:50] if isinstance(tasks, list) else []}
