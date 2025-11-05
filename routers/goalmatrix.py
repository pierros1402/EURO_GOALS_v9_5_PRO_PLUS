# ============================================================
# GOALMATRIX ROUTER v1.0.0
# ============================================================

from fastapi import APIRouter
from app.services.goalmatrix_engine import cache, refresh_goalmatrix_once

router = APIRouter(prefix="/api/goalmatrix", tags=["goalmatrix"])

@router.get("/summary")
async def get_summary():
    if not cache.is_fresh:
        await refresh_goalmatrix_once()
    return cache.get_summary()

@router.get("/items")
async def get_items():
    if not cache.is_fresh:
        await refresh_goalmatrix_once()
    return {"items": cache.get_items()}
