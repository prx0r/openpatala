# RECIPES — how to use OpenPāṭala
*Status: REFERENCE. How to use the API/MCP; reference examples.*

*2026-08-17 · Concrete how-tos for agents and humans. Each recipe is a copy-paste command.*

---

## R1 — Ingest GRETIL texts

```bash
cd /root/openpatalanew
PYTHONPATH=. python3 -c "
import asyncio, sys
sys.path.insert(0, '.')
from patala.resolver import Resolver
from patala.events import EventStore
from patala.completeness import CompletenessCompiler
from patala.adapters.gretil.adapter import GretilAdapter
from patala.ingest import IngestionPipeline
from pathlib import Path

event_store = EventStore(Path('data/events'))
resolver = Resolver()
completeness = CompletenessCompiler()
adapter = GretilAdapter()
pipeline = IngestionPipeline(adapter, event_store, resolver, completeness)
asyncio.run(pipeline.run(limit=100))
"
```
**Verify:** `PGPASSWORD=patala psql -U patala -h 127.0.0.1 -d openpatala -c "SELECT COUNT(*) FROM works;"`

## R2 — Serve the API

```bash
cd /root/openpatalanew
PYTHONPATH=. setsid nohup python3 -m uvicorn patala.api:app --host 127.0.0.1 --port 8801 > /tmp/openpatala-api.log 2>&1 &
```
**Verify:** `curl http://127.0.0.1:8801/health`

## R3 — Query the API

```bash
# List works
curl http://127.0.0.1:8801/v1/works?limit=5

# Get a work
curl http://127.0.0.1:8801/v1/works/{id}

# Get full bundle
curl http://127.0.0.1:8801/v1/bundle/{id}

# Search
curl "http://127.0.0.1:8801/v1/search?q=sanskrit"

# Resolve
curl "http://127.0.0.1:8801/v1/resolve?q=test"

# Frontier
curl "http://127.0.0.1:8801/v1/frontier/translations"
```

## R4 — Run conformance test

```bash
cd /root/openpatalanew
PYTHONPATH=. python3 patala/conformance_test.py
```
**Verify:** All 12 steps pass.

## R5 — Run hermes test

```bash
cd /root/openpatalanew
hermes -z "What is the Vigrahavyavartani?" -m mimo-v2.5 --provider opencode-go
```
**Verify:** `cat data/runs/hermes-calls.jsonl | wc -l`

## R6 — Check database state

```bash
PGPASSWORD=patala psql -U patala -h 127.0.0.1 -d openpatala -c "
SELECT 'works' as t, COUNT(*) as n FROM works
UNION ALL SELECT 'assertions', COUNT(*) FROM assertions
UNION ALL SELECT 'ext_ids', COUNT(*) FROM external_identifiers
UNION ALL SELECT 'events', COUNT(*) FROM events;
"
```

## R7 — Rebuild from events

```bash
cd /root/openpatalanew
PYTHONPATH=. python3 -c "
from patala.db import store
rebuilt = store.rebuild_from_events()
print(f'Rebuilt {rebuilt} works from event stream')
"
```
**Verify:** `PGPASSWORD=patala psql -U patala -h 127.0.0.1 -d openpatala -c "SELECT COUNT(*) FROM works;"`

## R8 — Wire Factory to OpenPāṭala

```bash
# The old project's Factory now reads from OpenPāṭala API (port 8801)
cd /root/openpatalaproject
PYTHONPATH=python:. python3 -c "
from patala_core.atlas.adapter import OpenPatalaBackend
backend = OpenPatalaBackend(api_url='http://127.0.0.1:8801')
print(f'Available: {backend.available()}')
data = backend.load()
print(f'Works: {len(data)}')
"
```
**Verify:** Works loaded from OpenPāṭala API.
