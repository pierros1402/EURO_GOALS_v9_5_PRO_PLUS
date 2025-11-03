from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy import text
from .smartmoney_notifier import register_client, engine

import time

router = APIRouter(prefix="/smartmoney", tags=["SmartMoney PRO"])

@router.get("/events")
def events(request: Request):
    """
    Server-Sent Events stream for live SmartMoney alerts.
    """
    client_q = register_client()

    def gen():
        # initial hello
        yield "retry: 5000\n\n"
        while True:
            if await_disconnected(request):
                break
            try:
                msg = client_q.get(timeout=15)
                yield msg
            except Exception:
                # keep-alive
                yield ":\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")

def await_disconnected(request: Request) -> bool:
    try:
        return await_heartbeat(request)
    except Exception:
        return False

def await_heartbeat(request: Request) -> bool:
    # Starlette exposes client disconnect via is_disconnected
    return request.is_disconnected()

@router.get("/history")
def history(limit: int = 50):
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT ts_utc, source, sport_key, match_id, home, away, market, bookmaker, selection, old_price, new_price, change_pct, note
            FROM smartmoney_alerts
            ORDER BY id DESC
            LIMIT :l
        """), {"l": limit}).mappings().all()
        return JSONResponse({"items": list(rows)})
