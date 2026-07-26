"""Wiki / Knowledge Reader — browse Hermes wiki + Outline docs."""

import asyncio
import os
import glob
import httpx
import re
from fastapi import APIRouter, Depends, HTTPException
from ..core.auth_secure import get_authenticated_user
from ..core.config import WIKI_ROOT, OUTLINE_URL, OUTLINE_TOKEN

router = APIRouter()


@router.get("/local/collections")
async def local_collections(user = Depends(get_authenticated_user)):
    """List local wiki collections (subdirectories)."""
    collections = []
    wiki_path = os.path.join(WIKI_ROOT, "wiki", "wiki")
    if os.path.isdir(wiki_path):
        for entry in sorted(os.listdir(wiki_path)):
            full = os.path.join(wiki_path, entry)
            if os.path.isfile(full) and entry.endswith(".md"):
                collections.append({"name": entry[:-3], "type": "file", "path": full})
            elif os.path.isdir(full):
                count = len(glob.glob(os.path.join(full, "**/*.md"), recursive=True))
                collections.append(
                    {"name": entry, "type": "dir", "path": full, "doc_count": count}
                )

    # Also list entities
    entities_path = os.path.join(WIKI_ROOT, "entities")
    entity_count = 0
    if os.path.isdir(entities_path):
        entity_count = len(
            glob.glob(os.path.join(entities_path, "**/*.md"), recursive=True)
        )

    return {
        "collections": collections,
        "entity_count": entity_count,
        "root": WIKI_ROOT,
    }


@router.get("/local/docs/{collection}")
async def local_docs(collection: str, user = Depends(get_authenticated_user)):
    """List docs in a local wiki collection."""
    coll_path = os.path.join(WIKI_ROOT, "wiki", "wiki", collection)

    if os.path.isfile(coll_path + ".md"):
        # Single file collection
        with open(coll_path + ".md", "r") as f:
            content = f.read()
        return {
            "docs": [
                {
                    "name": collection,
                    "content": content[:5000],
                    "full_length": len(content),
                }
            ]
        }

    if not os.path.isdir(coll_path):
        raise HTTPException(404, f"Collection '{collection}' not found")

    docs = []
    for md_file in sorted(
        glob.glob(os.path.join(coll_path, "**/*.md"), recursive=True)
    ):
        rel = os.path.relpath(md_file, coll_path)
        try:
            with open(md_file, "r") as f:
                content = f.read()
            # Extract title from first heading or frontmatter
            title = rel
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if title_match:
                title = title_match.group(1)
            elif content.startswith("---"):
                fm_title = re.search(r"title:\s*(.+)", content)
                if fm_title:
                    title = fm_title.group(1).strip()

            docs.append(
                {
                    "name": title,
                    "path": rel,
                    "preview": content[:200].replace("\n", " "),
                    "size": len(content),
                }
            )
        except Exception:
            pass

    return {"docs": docs, "collection": collection}


@router.get("/local/read")
async def read_doc(
    collection: str, doc: str = "", user = Depends(get_authenticated_user)
):
    """Read a specific document."""
    if doc:
        path = os.path.join(WIKI_ROOT, "wiki", "wiki", collection, doc)
    else:
        path = os.path.join(WIKI_ROOT, "wiki", "wiki", collection + ".md")

    if not os.path.isfile(path):
        raise HTTPException(404, "Document not found")

    with open(path, "r") as f:
        content = f.read()

    return {"content": content, "path": path, "size": len(content)}


@router.get("/local/search")
async def search_wiki(q: str, user = Depends(get_authenticated_user)):
    """Search across all wiki files."""
    import subprocess

    result = subprocess.run(
        ["grep", "-rl", "--include=*.md", q, os.path.join(WIKI_ROOT)],
        capture_output=True,
        text=True,
        timeout=10,
    )

    matches = []
    for line in result.stdout.strip().split("\n"):
        if line and os.path.isfile(line):
            rel = os.path.relpath(line, WIKI_ROOT)
            matches.append({"path": rel, "full_path": line})

    return {"query": q, "matches": matches[:30]}


# ── Outline integration ──────────────────────────────────────────────────


@router.get("/outline/collections")
async def outline_collections(user = Depends(get_authenticated_user)):
    """List Outline collections."""
    if not OUTLINE_TOKEN:
        return {"collections": [], "note": "Outline token not configured"}

    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            f"{OUTLINE_URL}/collections.list",
            headers={"Authorization": f"Bearer {OUTLINE_TOKEN}"},
            json={},
        )
        r.raise_for_status()
        data = r.json()

    return {
        "collections": [
            {
                "id": col["id"],
                "name": col["name"],
                "description": col.get("description", ""),
            }
            for col in data.get("data", [])
        ]
    }


@router.get("/outline/docs/{collection_id}")
async def outline_docs(
    collection_id: str, user = Depends(get_authenticated_user)
):
    """List docs in an Outline collection."""
    if not OUTLINE_TOKEN:
        return {"docs": []}

    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            f"{OUTLINE_URL}/documents.list",
            headers={"Authorization": f"Bearer {OUTLINE_TOKEN}"},
            json={"collectionId": collection_id},
        )
        r.raise_for_status()
        data = r.json()

    return {
        "docs": [
            {"id": d["id"], "title": d["title"], "updated": d.get("updatedAt", "")}
            for d in data.get("data", [])
        ]
    }


@router.get("/outline/read/{doc_id}")
async def read_outline_doc(doc_id: str, user = Depends(get_authenticated_user)):
    """Read an Outline document."""
    if not OUTLINE_TOKEN:
        raise HTTPException(503, "Outline token not configured")

    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(
            f"{OUTLINE_URL}/documents.info",
            headers={"Authorization": f"Bearer {OUTLINE_TOKEN}"},
            json={"id": doc_id},
        )
        r.raise_for_status()
        data = r.json()

    doc = data.get("data", {})
    return {"title": doc.get("title", ""), "text": doc.get("text", ""), "id": doc_id}
