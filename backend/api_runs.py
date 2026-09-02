"""REST API routes for active command runs."""

from __future__ import annotations

from fastapi import APIRouter, Request

from backend.models import RunOut

router = APIRouter(prefix="/api", tags=["runs"])


@router.get("/runs", response_model=list[RunOut])
async def list_runs(request: Request) -> list[RunOut]:
  manager = request.app.state.run_manager
  return manager.list_runs()
