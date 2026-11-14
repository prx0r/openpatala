# BUILD-NOTES-2026-08-17.md — Timestamped Build Notes
*Status: HISTORICAL. Timestamped build log; frozen.*

*2026-08-17T19:15:00Z · Session pause point*

---

## SESSION SUMMARY

### What Was Done
1. **Phase 1.1-1.8 Built**: All modules from PATALAPATH2 §18 completed
2. **Honest Peer Review**: Discovered most work was theatre (broken data)
3. **Ingestion Fixed**: PANDiT adapter bug fixed (aka field was string, not list)
4. **Data Re-ingested**: PANDiT (200 entities), GRETIL (100 entities)

### Database State (Current)
```
Works: 1399
Assertions: 605
External IDs: 368
Single-character assertions: 0
```

### Experiment Logs
All experiments logged to `data/runs/`:
- `gold-dossiers.jsonl` — 100 dossiers built
- `cross-source-identity.jsonl` — 13 works with matches
- `openalex-query.jsonl` — Query layer working
- `coverage-frontier.jsonl` — Coverage returns UNKNOWN (needs fix)
- `provider-expansion.jsonl` — Provider health computed
- `self-filling-discovery.jsonl` — Discovery simulated
- `annotation-interop.jsonl` — Format conversions working
- `witness-collation.jsonl` — Collation working

---

## HOW TO CONTINUE

### Step 1: Ingest More Data
The following sources need re-ingestion:
- **Archive.org**: 50 records, only 20 ext_ids
- **OpenAlex**: 50 records, no ext_ids
- **Sanskritree**: 44 records, no ext_ids

```bash
# Check current state
PGPASSWORD=patala psql -U patala -h 127.0.0.1 -d openpatala -c "SELECT scheme, COUNT(*) FROM external_identifiers GROUP BY scheme;"

# Re-ingest Archive.org
cd /root/openpatalanew
PYTHONPATH=. python3 -c "
import asyncio
from patala.adapters.archiveorg.adapter import ArchiveOrgAdapter
adapter = ArchiveOrgAdapter()
result = asyncio.run(adapter.discover(limit=50))
print(f'Found {len(result[\"items\"])} items')
"
```

### Step 2: Link Works to Assertions
1035 works don't have assertions. Need to create assertions for these works.

```bash
# Check works without assertions
PGPASSWORD=patala psql -U patala -h 127.0.0.1 -d openpatala -c "
SELECT COUNT(*) FROM works w
WHERE NOT EXISTS (
    SELECT 1 FROM assertions a WHERE a.subject_id = w.id
);
"

# Create assertions for works with titles
PYTHONPATH=. python3 -c "
import psycopg2
from datetime import datetime, timezone

conn = psycopg2.connect('postgresql://patala:patala@localhost:5432/openpatala')
cur = conn.cursor()

# Get works without assertions
cur.execute('''
    SELECT w.id, w.preferred_title
    FROM works w
    WHERE NOT EXISTS (
        SELECT 1 FROM assertions a WHERE a.subject_id = w.id
    )
    AND w.preferred_title IS NOT NULL
    AND LENGTH(w.preferred_title) > 5
    LIMIT 100
''')
works = cur.fetchall()

for work_id, title in works:
    # Create TITLE assertion
    cur.execute('''
        INSERT INTO assertions (id, subject_id, predicate_uri, literal, epistemic_mode, evidence_use_ids, asserted_by, recorded_at, lifecycle, created_from_event, schema_uri)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        f'PTCAS_manual_{work_id[:20]}_title',
        work_id,
        'TITLE',
        title,
        'observed',
        '{}',
        'MANUAL',
        datetime.now(timezone.utc),
        'ACTIVE',
        'PTEVT_manual_link',
        'https://patala.org/schemas/v2/assertion.json',
    ))

conn.commit()
print(f'Created {len(works)} assertions')
"
```

### Step 3: Fix Coverage Engine
Coverage engine returns UNKNOWN for most works. Need to fix coverage computation.

```bash
# Check coverage for a work with assertions
PYTHONPATH=. python3 -c "
import sys
sys.path.insert(0, '/root/openpatalanew')
from patala.coverage import CoverageEngine
import psycopg2

conn = psycopg2.connect('postgresql://patala:patala@localhost:5432/openpatala')
engine = CoverageEngine(conn)

# Get a work with assertions
cur = conn.cursor()
cur.execute('''
    SELECT w.id, w.preferred_title
    FROM works w
    JOIN assertions a ON a.subject_id = w.id
    WHERE a.predicate_uri = 'TITLE'
    LIMIT 1
''')
work_id, title = cur.fetchone()

coverage = engine.compute_coverage(work_id)
print(f'Work: {work_id[:25]}  title={title[:40]}')
print(f'  Identity: {coverage.identity.state.value}')
print(f'  Author: {coverage.author.state.value}')
print(f'  Title: {coverage.title.state.value}')
print(f'  Text: {coverage.text.state.value}')
"
```

### Step 4: Re-run Experiments
After fixing data, re-run all experiments:

```bash
cd /root/openpatalanew

# Re-run all experiments
PYTHONPATH=. python3 patala/experiments/gold_dossiers.py
PYTHONPATH=. python3 patala/experiments/cross_source_identity.py
PYTHONPATH=. python3 patala/experiments/openalex_query.py
PYTHONPATH=. python3 patala/experiments/coverage_frontier.py
PYTHONPATH=. python3 patala/experiments/provider_expansion.py
PYTHONPATH=. python3 patala/experiments/self_filling_discovery.py
PYTHONPATH=. python3 patala/experiments/annotation_interop.py
PYTHONPATH=. python3 patala/experiments/witness_collation.py
```

### Step 5: Update Handover
After completing steps, update `HANDSOVER-2026-08-17.md` with new state.

---

## KEY FILES TO READ FIRST

1. `AGENTS.md` — Rules for agents
2. `HANDSOVER-2026-08-17.md` — Current state
3. `PEER-REVIEW-4.md` — Honest self-assessment
4. `PATALAPATH2.md` — Corrected phase map
5. `DEV-PLAN.md` — Updated build plan

---

## GIT STATE

```
Branch: master
Remote: https://github.com/prx0r/wiggly
Commits: 26
Latest: 2783c12
```

---

## THE ANTI-CHEAT RULE

**"Nothing written in README, commit messages or markdown counts as evidence."**

Evidence must be machine-produced from actual code execution.

---

*Session paused at 2026-08-17T19:15:00Z*
