"""1Password Vault Browser — list/search items in the Gregory vault."""

import asyncio
import json
import shutil
import subprocess
from fastapi import APIRouter, Depends, HTTPException
from ..core.auth_secure import get_authenticated_user
from ..core.config import OP_VAULT

router = APIRouter()


async def _op(*args: str) -> str:
    """Run op CLI command asynchronously."""
    cmd = ["op"] + list(args)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
    if proc.returncode != 0:
        raise RuntimeError(stderr.decode())
    return stdout.decode()


@router.get("/vaults")
async def list_vaults(user = Depends(get_authenticated_user)):
    """List available 1Password vaults."""
    out = await _op("vault", "list", "--format=json")
    vaults = json.loads(out)
    return {"vaults": [{"id": v["id"], "name": v["name"]} for v in vaults]}


@router.get("/items")
async def list_items(query: str = "", user = Depends(get_authenticated_user)):
    """List items in the Gregory vault."""
    args = ["item", "list", "--vault", OP_VAULT, "--format=json"]
    out = await _op(*args)
    items = json.loads(out)

    if query:
        q = query.lower()
        items = [i for i in items if q in i.get("title", "").lower()]

    return {
        "items": [
            {
                "id": i["id"],
                "title": i["title"],
                "category": i.get("category", ""),
                "vault": i.get("vault", {}).get("name", ""),
                "updated": i.get("updated_at", ""),
            }
            for i in items[:100]
        ],
        "total": len(items),
    }


@router.get("/items/{item_id}")
async def get_item(item_id: str, user = Depends(get_authenticated_user)):
    """Get full details of an item — including fields."""
    out = await _op("item", "get", item_id, "--vault", OP_VAULT, "--format=json")
    item = json.loads(out)

    fields = []
    for f in item.get("fields", []):
        fields.append(
            {
                "id": f.get("id", ""),
                "label": f.get("label", ""),
                "value": f.get("value", ""),
                "type": f.get("type", ""),
                "purpose": f.get("purpose", ""),
                "reference": f.get("reference", ""),
            }
        )

    urls = [
        {
            "label": u.get("label", ""),
            "primary": u.get("primary", False),
            "href": u.get("href", ""),
        }
        for u in item.get("urls", [])
    ]

    return {
        "id": item["id"],
        "title": item["title"],
        "category": item.get("category", ""),
        "fields": fields,
        "urls": urls,
        "notes": item.get("notes", ""),
    }
