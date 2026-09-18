# WTI Consensus Oracle

A live WTI crude oil price feed built for autonomous agents. It pulls the price from two
independent sources, cross-verifies them into a single trusted consensus value with a
confidence/quality score, stores it in PostgreSQL with a TTL-based lifecycle, and serves it
through a standardized REST API - with an automated test suite covering latency, freshness,
availability, and source failover.

## Endpoint
GET /v1/energy/commodity/price?commodity=WTI&tenor=spot

Returns a standardized envelope: the price plus full metadata on freshness, provenance, and trust.

## Architecture

<img width="2720" height="2064" alt="wti_oracle_architecture" src="https://github.com/user-attachments/assets/5f193f66-816f-4360-8b92-bfc15b942947" />

- **Two independent sources** (Yahoo Finance, Alpha Vantage) each fetch the current price on their own.
- A **consensus engine** averages them and rejects any reading that disagrees too far from the rest.
- The agreed value is written to **PostgreSQL** (JSONB), with raw readings, consensus history, and rolled-up summaries kept in separate tables.
- A **FastAPI service** reads only the latest row from Postgres and serves it - it never talks to the internet on a live request, which keeps every response fast.
- **Ingestion and serving only communicate through the database** - one provider failing never takes the API down; it just serves the most recent good result and reports its age honestly.

## Tech stack

Python - FastAPI - PostgreSQL (JSONB) - pytest


## Running it

```bash
docker compose up -d              # Postgres
cp .env.example .env              # add your Alpha Vantage key (free, instant)
pip install -r requirements.txt
python main.py                    # sets up DB, runs worker + API + tests
```

Then open `http://localhost:8000/dashboard` for a live view, or query the endpoint directly.

## What it satisfies

| Requirement | Where |
|---|---|
| Multi-source ingestion | `ingestion/source_yahoo.py`, `ingestion/source_alphavantage.py` |
| Consensus + confidence/quality score | `consensus/consensus_engine.py` |
| No silent fallbacks | `SourceError` / `ConsensusError` raised explicitly, never caught-and-ignored |
| Standardized payload | `api/response_builder.py` |
| PostgreSQL + JSONB storage | `db/schema.sql`, `storage/db_manager.py` |
| TTL purge / rollup | `storage/db_manager.py::purge_and_rollup` |
| SLA tests | `tests/` |

## Sample outputs
<img width="1202" height="706" alt="image" src="https://github.com/user-attachments/assets/79b234cd-f5db-427a-968a-4f91b6b77fe3" />


