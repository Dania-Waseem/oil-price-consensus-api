import time

import psycopg2
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

import config
from api.dashboard_html import DASHBOARD_HTML
from api.response_builder import build_envelope
from storage import db_manager

app = FastAPI(title="Energy Commodity Price Agent API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """A simple, pastel-styled page that shows the live price - open in a browser."""
    return DASHBOARD_HTML


@app.get("/v1/energy/commodity/price")
def get_commodity_price(commodity: str = Query(...), tenor: str = Query("spot")):
    start = time.perf_counter()

    if commodity.upper() != config.COMMODITY:
        raise HTTPException(status_code=404, detail=f"commodity '{commodity}' not supported here")

    try:
        conn = db_manager.get_conn()
        row = db_manager.get_latest_consensus(conn, config.COMMODITY, tenor)
        conn.close()
    except psycopg2.OperationalError as e:
        raise HTTPException(status_code=503, detail=f"storage layer unavailable: {e}")

    if row is None:
        raise HTTPException(status_code=503, detail="no consensus data available yet, try again shortly")

    latency_ms = round((time.perf_counter() - start) * 1000, 1)
    envelope = build_envelope(row, latency_ms)

    if envelope["meta"]["freshness"]["age_seconds"] > config.HARD_EXPIRY_SECONDS:
        raise HTTPException(status_code=503, detail="data too stale to serve, no fresh consensus available")

    return JSONResponse(content=envelope)