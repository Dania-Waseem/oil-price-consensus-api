from datetime import datetime, timezone

import requests

import config
from ingestion.base import RawQuote, SourceError

AV_URL = "https://www.alphavantage.co/query"


def fetch() -> RawQuote:
    """Alpha Vantage's WTI function: dedicated daily oil price series.
    Free tier = 25 calls/day, so the worker only calls this occasionally
    (see ALPHA_VANTAGE_EVERY_N_CYCLES in worker/background_worker.py)."""
    if not config.ALPHA_VANTAGE_API_KEY:
        raise SourceError("alphavantage", "no API key set - add ALPHA_VANTAGE_API_KEY to your .env")

    params = {"function": "WTI", "interval": "daily", "apikey": config.ALPHA_VANTAGE_API_KEY}
    try:
        resp = requests.get(AV_URL, params=params, timeout=10)
    except requests.RequestException as e:
        raise SourceError("alphavantage", f"network error: {e}")

    if resp.status_code != 200:
        raise SourceError("alphavantage", f"bad status code {resp.status_code}")

    body = resp.json()

    # Alpha Vantage returns HTTP 200 even when you're out of quota - it just
    # hides a text message inside the JSON body instead of real data.
    if "Note" in body or "Information" in body:
        raise SourceError("alphavantage", body.get("Note") or body.get("Information"))

    try:
        latest = body["data"][0]
        price = float(latest["value"])
        as_of = datetime.strptime(latest["date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except (KeyError, IndexError, ValueError, TypeError) as e:
        raise SourceError("alphavantage", f"unexpected schema: {e}")

    return RawQuote(
        source_id="SRC-ALPHAVANTAGE-WTI",
        publisher="Alpha Vantage (WTI daily)",
        commodity=config.COMMODITY,
        price=price,
        currency=config.CURRENCY,
        unit=config.UNIT,
        as_of=as_of,
        retrieved_at=datetime.now(timezone.utc),
    )
