import requests
from datetime import datetime, timezone

import config
from ingestion.base import RawQuote, SourceError

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/CL=F"


def fetch() -> RawQuote:
    """CL=F = Yahoo's ticker for WTI crude oil futures (front-month = our 'spot' proxy)."""
    try:
        resp = requests.get(YAHOO_URL, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
    except requests.RequestException as e:
        raise SourceError("yahoo", f"network error: {e}")

    if resp.status_code != 200:
        raise SourceError("yahoo", f"bad status code {resp.status_code}")

    try:
        body = resp.json()
        result = body["chart"]["result"][0]
        price = result["meta"]["regularMarketPrice"]
        ts = result["meta"]["regularMarketTime"]
    except (KeyError, IndexError, TypeError) as e:
        raise SourceError("yahoo", f"unexpected schema: {e}")

    if not price or price <= 0:
        raise SourceError("yahoo", "invalid price value")

    return RawQuote(
        source_id="SRC-YAHOO-CLF",
        publisher="Yahoo Finance (CL=F futures)",
        commodity=config.COMMODITY,
        price=float(price),
        currency=config.CURRENCY,
        unit=config.UNIT,
        as_of=datetime.fromtimestamp(ts, tz=timezone.utc),
        retrieved_at=datetime.now(timezone.utc),
    )
