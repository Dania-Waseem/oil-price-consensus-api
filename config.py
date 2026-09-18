import os
from dotenv import load_dotenv

load_dotenv()

# --- Database connection ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://oiluser:oilpass@localhost:5432/oildata")

# --- Alpha Vantage (second provider) ---
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")

# --- What task we serve (Row 79: Oil & Gas / Commodity benchmark) ---
COMMODITY = "WTI"
TENOR = "spot"
CURRENCY = "USD"
UNIT = "barrel"

# How often the background worker fetches fresh prices (spec says "minutes")
POLL_INTERVAL_SECONDS = 60

# Freshness rules used in meta.freshness of every response
TTL_SECONDS = 900            # older than this -> officially "stale"
HARD_EXPIRY_SECONDS = 3600   # older than this -> refuse to serve at all (no silent stale masquerade)

# Consensus rules
SOURCE_WEIGHTS = {"yahoo": 0.5, "alphavantage": 0.5}   # equal trust between our two providers
OUTLIER_THRESHOLD_PCT = 0.05                             # >5% away from median = rejected as outlier

# Alpha Vantage free tier only allows 25 calls/day, so we don't call it every
# cycle like Yahoo - only once every N cycles (default: roughly once an hour)
ALPHA_VANTAGE_EVERY_N_CYCLES = max(1, 3600 // POLL_INTERVAL_SECONDS)

# Lifecycle: raw rows older than this get rolled into hourly summaries, then deleted
ROLLUP_AFTER_SECONDS = 24 * 3600

# API response metadata
PRODUCT_ID = "energy.commodity.price.v1"
API_VERSION = "1.0.0"
RATE_LIMIT = {"limit": 100, "window_seconds": 60}
