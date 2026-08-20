"""Homelab Mini Apps Hub — unified Telegram Mini App platform.

Serves 10 mini apps under a single FastAPI backend:
  1. Swarm Monitor (GitLab + Prometheus fail-closed source envelopes)
  2. IaC Pipeline Approval Gate
  3. Fleet Health Dashboard
  4. Jira OPS Kanban Board
  5. Alert Triage Console
  6. Quick Ops Remote
  7. 1Password Vault Browser
  8. Smart Home Control
  9. Cost/Quota Monitor
  10. Wiki/Knowledge Reader
"""

import os
import sys

from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.auth_secure import get_authenticated_user, AuthContext
from app.core.config import MINIAPPS_PUBLIC_ORIGIN
from app.api import (
    fleet,
    pipeline,
    kanban,
    alerts,
    ops_remote,
    onepassword,
    smarthome,
    cost,
    wiki,
    swarm,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Homelab Mini Apps Hub starting up...")
    yield
    print("Homelab Mini Apps Hub shutting down...")


app = FastAPI(
    title="Homelab Mini Apps Hub",
    description="Unified Telegram Mini App platform for a homelab",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — restrict to Telegram webview origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        MINIAPPS_PUBLIC_ORIGIN,
        "https://web.telegram.org",
        "https://k.web.telegram.org",
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["Authorization", "Content-Type"],
)


# ─── Health ────────────────────────────────────────────────────────────────


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "apps": [
            "pipeline",
            "fleet",
            "kanban",
            "alerts",
            "ops-remote",
            "1password",
            "smarthome",
            "cost",
            "wiki",
            "swarm",
        ],
    }


@app.get("/api/me")
async def whoami(user: AuthContext = Depends(get_authenticated_user)):
    return {
        "telegram_user_id": user.telegram_user_id,
        "username": user.username,
        "first_name": user.first_name,
        "roles": user.roles,
        "is_owner": user.is_owner,
        "is_viewer": user.is_viewer,
    }


# ─── App Routers ───────────────────────────────────────────────────────────

app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(fleet.router, prefix="/api/fleet", tags=["fleet"])
app.include_router(kanban.router, prefix="/api/kanban", tags=["kanban"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(ops_remote.router, prefix="/api/ops-remote", tags=["ops-remote"])
app.include_router(onepassword.router, prefix="/api/1password", tags=["1password"])
app.include_router(smarthome.router, prefix="/api/smarthome", tags=["smarthome"])
app.include_router(cost.router, prefix="/api/cost", tags=["cost"])
app.include_router(wiki.router, prefix="/api/wiki", tags=["wiki"])
app.include_router(swarm.router, prefix="/api/swarm", tags=["swarm"])


# ─── Static Frontend ────────────────────────────────────────────────────────

# Frontend is at /app/frontend/ (same level as app/)
frontend_dir = "/app/frontend"

if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.get("/{path:path}")
async def serve_spa(path: str = ""):
    """Serve the SPA — any non-API path returns index.html."""
    index = os.path.join(frontend_dir, "index.html")
    if os.path.isfile(index):
        return FileResponse(index)
    return JSONResponse({"error": "Frontend not built"}, status_code=404)
