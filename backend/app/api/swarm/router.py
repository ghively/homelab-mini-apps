"""Swarm Monitor API router — read-only endpoints."""

from fastapi import APIRouter, Depends

from app.core.auth_secure import get_authenticated_user
from app.services.swarm_monitor import fetch_all

router = APIRouter()


@router.get("/")
async def swarm_overview(user: dict = Depends(get_authenticated_user)):
    """Return aggregated Swarm Monitor data from all sources."""
    return await fetch_all()


@router.get("/gitlab")
async def swarm_gitlab(user: dict = Depends(get_authenticated_user)):
    """Return GitLab pipeline source envelope."""
    from app.services.swarm_monitor import fetch_gitlab
    import httpx

    async with httpx.AsyncClient() as client:
        return await fetch_gitlab(client)


@router.get("/prometheus")
async def swarm_prometheus(user: dict = Depends(get_authenticated_user)):
    """Return Prometheus fleet metrics source envelope."""
    from app.services.swarm_monitor import fetch_prometheus
    import httpx

    async with httpx.AsyncClient() as client:
        return await fetch_prometheus(client)
