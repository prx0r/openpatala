# MASTER — OpenPāṭala project index

> SUPERSEDED 2026-11-10 (banner only): paths reference `openpatalanew/`;
> checkout is `/root/openpatala`. Canonical live state: `OPENPATALA.md`.
> Kept as reference; verify paths before running any command below.

*2026-08-17 · Master index for navigating the project.*

---

## Project structure

```
openpatalanew/
├── patala/
│   ├── hashing.py          UUIDv7, DigestSet, JCS, 3 hash types
│   ├── entities.py          23 entity models
│   ├── resolver.py          R0-R5 staged resolver
│   ├── events.py            Append-only + Merkle checkpoints
│   ├── schema_registry.py   Immutable, versioned
│   ├── completeness.py      WorkCompleteness projection
│   ├── ingest.py            5-step pipeline
│   ├── api.py               FastAPI v1 (18 endpoints)
│   ├── tei_utils.py         Shared TEI parser
│   ├── mcp_server.py        Agent interface
│   ├── conformance_test.py  12-step verification
│   ├── run_recorder.py      Content-addressed records
│   ├── audit.py             Golden-file audit
│   ├── trace.py             Run trace
│   ├── db/
│   │   ├── connection.py    Postgres connection
│   │   ├── migrate.py       Migration runner
│   │   ├── store.py         Database operations
│   │   └── schemas.py       Data validators
│   ├── adapters/            13 adapters
│   ├── serializers/         7 serializers
│   └── factory/             Translation pipeline
├── migrations/              SQL migrations
├── data/                    Event store + hermes logs
├── *.md                     Documentation
```

## Key files by concern

| Concern | File |
|---|---|
| Identity | `hashing.py` (UUIDv7, DigestSet) |
| Entities | `entities.py` (23 models) |
| Resolution | `resolver.py` (R0-R5) |
| Events | `events.py` (append-only, Merkle) |
| Schemas | `schema_registry.py`, `schemas/v2/*.json` |
| API | `api.py` (18 endpoints) |
| Ingestion | `ingest.py` (5-step pipeline) |
| Factory | `factory/` (deepfinder, download, proof, availability) |
| Database | `db/store.py`, `migrations/` |
| Testing | `conformance_test.py` (12 steps) |
| Hermes | `data/runs/hermes-calls.jsonl` |

## Commands

```bash
# Ingest
cd /root/openpatalanew && PYTHONPATH=. python3 -c "import asyncio; ..."

# Serve
PYTHONPATH=. python3 -m uvicorn patala.api:app --port 8801

# Test
PYTHONPATH=. python3 patala/conformance_test.py

# Database
PGPASSWORD=patala psql -U patala -h 127.0.0.1 -d openpatala
```
