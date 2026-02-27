"""
IDX Stock Screener — FastAPI Backend
Serves JSON API for BSJP, Intraday, and Swing screening.
"""

import asyncio
import json
import os
from pathlib import Path

# Load .env before any module reads os.getenv
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

from fastapi import FastAPI, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from auth import verify_google_token, create_jwt, require_auth
from database import init_db, get_or_create_user, get_user_by_id, get_holdings, save_holdings

from screener.engine import (
    STOCK_GROUPS,
    resolve_stocks,
    run_bsjp_intraday,
    run_swing,
    run_ara_hunter,
    run_night_scanner,
    run_portfolio_analysis,
)
from screener.market import get_market_status


class PortfolioItem(BaseModel):
    ticker: str
    lot: int
    avg_price: float


class PortfolioRequest(BaseModel):
    holdings: list[PortfolioItem]

app = FastAPI(
    title="IDX Stock Screener API",
    version="1.0",
    description="Auto-screening saham Indonesia: BSJP, Intraday, Swing",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:4173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/api/market-status")
async def market_status():
    """Get current IDX market status (open/closed, progress)."""
    return get_market_status()


@app.get("/api/stock-lists")
async def stock_lists():
    """Available stock groups and their counts."""
    return {name: len(stocks) for name, stocks in STOCK_GROUPS.items()}


@app.get("/api/screener/{mode}")
async def screener(
    mode: str,
    stocks: str = Query(default="lq45", description="Stock group or comma-separated tickers"),
    smallcap: bool = Query(default=False, description="Include small cap stocks with stricter rules"),
):
    """
    Run screening for given mode.
    mode: bsjp | intraday | swing
    stocks: lq45 | idx80 | all_idx | jii | jii70 | issi | BBCA,TLKM,...
    smallcap: true to add small cap stocks with stricter screening rules
    """
    stock_list = resolve_stocks(stocks)

    if mode in ("bsjp", "intraday"):
        result = await run_bsjp_intraday(mode, stock_list, smallcap_enabled=smallcap)
    elif mode == "swing":
        result = await run_swing(stock_list)
    else:
        return {"error": f"Unknown mode: {mode}. Use bsjp, intraday, or swing."}

    return result


@app.get("/api/screener/{mode}/stream")
async def screener_stream(
    mode: str,
    stocks: str = Query(default="lq45"),
    smallcap: bool = Query(default=False),
):
    """
    Server-Sent Events endpoint for real-time scanning progress.
    Sends progress events per ticker, then the complete result.
    """
    stock_list = resolve_stocks(stocks)

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()

        async def progress_cb(current, total, ticker):
            await queue.put({
                "type": "progress",
                "current": current,
                "total": total,
                "ticker": ticker,
            })

        async def result_cb(stock_result):
            await queue.put({
                "type": "result",
                "stock": stock_result,
            })

        # Start screening task
        if mode in ("bsjp", "intraday"):
            task = asyncio.create_task(
                run_bsjp_intraday(mode, stock_list, progress_cb=progress_cb, smallcap_enabled=smallcap, result_cb=result_cb)
            )
        elif mode == "swing":
            task = asyncio.create_task(
                run_swing(stock_list, progress_cb=progress_cb, result_cb=result_cb)
            )
        else:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Unknown mode: {mode}'})}\n\n"
            return

        # Stream progress + result events
        while not task.done():
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield f"data: {json.dumps(msg)}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

        # Drain remaining messages
        while not queue.empty():
            msg = await queue.get()
            yield f"data: {json.dumps(msg)}\n\n"

        # Send complete result
        result = task.result()
        yield f"data: {json.dumps({'type': 'complete', 'data': result})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/ara-hunter")
async def ara_hunter(
    stocks: str = Query(default="all_bursa", description="Stock group or comma-separated tickers"),
):
    """
    ARA Hunter — find stocks with ARA potential.
    Scans for stocks with CHG% >= 3% and volume ratio >= 1.5x.
    """
    stock_list = resolve_stocks(stocks)
    return await run_ara_hunter(stock_list)


@app.get("/api/ara-hunter/stream")
async def ara_hunter_stream(
    stocks: str = Query(default="all_bursa"),
):
    """SSE endpoint for ARA Hunter with progress events."""
    stock_list = resolve_stocks(stocks)

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()

        async def progress_cb(current, total, ticker):
            await queue.put({
                "type": "progress",
                "current": current,
                "total": total,
                "ticker": ticker,
            })

        async def result_cb(stock_result):
            await queue.put({
                "type": "result",
                "stock": stock_result,
            })

        task = asyncio.create_task(
            run_ara_hunter(stock_list, progress_cb=progress_cb, result_cb=result_cb)
        )

        while not task.done():
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield f"data: {json.dumps(msg)}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

        while not queue.empty():
            msg = await queue.get()
            yield f"data: {json.dumps(msg)}\n\n"

        result = task.result()
        yield f"data: {json.dumps({'type': 'complete', 'data': result})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/night-scanner")
async def night_scanner(
    stocks: str = Query(default="all_stocks", description="Stock group or comma-separated tickers"),
):
    """Night Scanner — predict next-day top gainer candidates."""
    stock_list = resolve_stocks(stocks)
    return await run_night_scanner(stock_list)


@app.get("/api/night-scanner/stream")
async def night_scanner_stream(
    stocks: str = Query(default="all_stocks"),
):
    """SSE endpoint for Night Scanner with progress + per-stock result events."""
    stock_list = resolve_stocks(stocks)

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()

        async def progress_cb(current, total, ticker):
            await queue.put({
                "type": "progress",
                "current": current,
                "total": total,
                "ticker": ticker,
            })

        async def result_cb(stock_result):
            await queue.put({
                "type": "result",
                "stock": stock_result,
            })

        task = asyncio.create_task(
            run_night_scanner(stock_list, progress_cb=progress_cb, result_cb=result_cb)
        )

        while not task.done():
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield f"data: {json.dumps(msg)}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

        while not queue.empty():
            msg = await queue.get()
            yield f"data: {json.dumps(msg)}\n\n"

        result = task.result()
        yield f"data: {json.dumps({'type': 'complete', 'data': result})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/portfolio/analyze")
async def portfolio_analyze(req: PortfolioRequest):
    """Non-streaming portfolio analysis. Used for background auto-scan."""
    holdings = [h.model_dump() for h in req.holdings]
    result = await run_portfolio_analysis(holdings)
    return result


@app.post("/api/portfolio/analyze/stream")
async def portfolio_analyze_stream(req: PortfolioRequest):
    """
    Analyze portfolio holdings with SSE streaming.
    Runs swing analysis per stock and generates HOLD/JUAL/CUT LOSS signals.
    """
    holdings = [h.model_dump() for h in req.holdings]

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()

        async def progress_cb(current, total, ticker):
            await queue.put({
                "type": "progress",
                "current": current,
                "total": total,
                "ticker": ticker,
            })

        async def result_cb(stock_result):
            await queue.put({
                "type": "result",
                "stock": stock_result,
            })

        task = asyncio.create_task(
            run_portfolio_analysis(holdings, progress_cb=progress_cb, result_cb=result_cb)
        )

        while not task.done():
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield f"data: {json.dumps(msg)}\n\n"
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

        while not queue.empty():
            msg = await queue.get()
            yield f"data: {json.dumps(msg)}\n\n"

        result = task.result()
        yield f"data: {json.dumps({'type': 'complete', 'data': result})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Telegram Notifications ──────────────────────────────────────

from telegram import is_configured as tg_configured, send_alert as tg_send


class TelegramAlertItem(BaseModel):
    ticker: str
    signalCode: str
    signalLabel: str
    reason: str
    pnlPct: float


class TelegramAlertRequest(BaseModel):
    alerts: list[TelegramAlertItem]


@app.get("/api/telegram/status")
async def telegram_status():
    return {"configured": tg_configured()}


@app.post("/api/telegram/send-alert")
async def telegram_send_alert(req: TelegramAlertRequest):
    ok, msg = await tg_send([a.model_dump() for a in req.alerts])
    return {"success": ok, "message": msg}


# ── Auth + User Portfolio ──────────────────────────────────────


class GoogleLoginRequest(BaseModel):
    credential: str


class UserPortfolioRequest(BaseModel):
    holdings: list[PortfolioItem]


@app.post("/api/auth/google")
async def auth_google(req: GoogleLoginRequest):
    """Verify Google ID token, create/update user, return JWT + user info."""
    try:
        google_info = verify_google_token(req.credential)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user = get_or_create_user(
        google_id=google_info["sub"],
        email=google_info.get("email", ""),
        name=google_info.get("name", ""),
        picture=google_info.get("picture", ""),
    )

    token = create_jwt(user["id"], user["email"])

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user["picture"],
        },
    }


@app.get("/api/auth/me")
async def auth_me(user_id: int = Depends(require_auth)):
    """Get current user info from JWT."""
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "picture": user["picture"],
    }


@app.get("/api/user/portfolio")
async def user_portfolio_get(user_id: int = Depends(require_auth)):
    """Get user's saved portfolio holdings."""
    holdings = get_holdings(user_id)
    return {"holdings": holdings}


@app.put("/api/user/portfolio")
async def user_portfolio_save(req: UserPortfolioRequest, user_id: int = Depends(require_auth)):
    """Save (full replace) user's portfolio holdings."""
    holdings_data = [h.model_dump() for h in req.holdings]
    save_holdings(user_id, holdings_data)
    return {"ok": True, "count": len(holdings_data)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
