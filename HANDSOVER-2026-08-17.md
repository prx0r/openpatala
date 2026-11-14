# HANDSOVER-2026-08-17.md — Complete Session Handover
*Status: HISTORICAL. Session handover snapshot; frozen.*

*2026-08-17T19:00:00Z · Full handover for next agent.*

---

## 1. THE BIG PICTURE

**OpenPāṭala is the public data infrastructure. Pāṭala is everything intelligent that grows on top of it.**

The product answers: "What is this work? What other databases know it? Who wrote it? What witnesses, scans, editions, e-texts, translations and scholarship exist? Where can I access them? What is uncertain or disputed? What is still missing?"

---

## 2. WHAT WAS FIXED

### Ingestion Fixed
- PANDiT adapter: `aka` field was string, not list (was splitting into characters)
- Re-ingested PANDiT: 200 entities
- Re-ingested GRETIL: 100 entities

### Database State (After Fix)
```
Works: 1399 (up from 1099)
Assertions: 605 (up from 247)
External IDs: 368 (up from 108)
Single-character assertions: 0 (down from 71)
```

### Data Quality
- 408 TITLE assertions (proper titles now)
- 73 AUTHOR assertions
- 100 LANGUAGE assertions
- 364 works have assertions
- 1035 works don't have assertions

---

## 3. WHAT WAS BUILT

### Core (57 Python files)
- `hashing.py` — UUIDv7, DigestSet, JCS, 3 hash types
- `entities.py` — 23 entity models
- `resolver.py` — Staged resolver R0-R5
- `events.py` — Postgres-only event ledger
- `schema_registry.py` — Immutable schema registry
- `work_coverage.py` — Coverage from canonical state
- `ingest.py` — 5-step pipeline
- `api.py` — FastAPI v1 (21 endpoints)
- `tests/conformance.py` — 5 binary test suites
- `conformance_test.py` — 12-step verification
- + 8 more modules (fingerprint, provenance, signing, etc.)

### Adapters (13)
GRETIL, Sanskritree, Archive.org, Crossref, PANDiT, OpenAlex, Darshana, Muktabodha, ORCID, ROR, WikiData, STAM, CollateX

### New Modules (Phase 1.1-1.8)
- `identity.py` — Cross-source identity resolution
- `query.py` — OpenAlex-class query layer
- `coverage.py` — Coverage + Frontier system
- `providers.py` — Provider expansion system
- `discovery.py` — Self-filling discovery system
- `annotation.py` — Text/Passage Annotation Interop
- `witness.py` — Witness Collation system

---

## 4. EXPERIMENT RESULTS (After Fix)

### Gold Dossiers
- 100 dossiers built
- 243 assertions (proper titles and authors)
- 136 external IDs (GRETIL and PANDiT)
- 42 works with author
- 65 works with GRETIL

### Cross-Source Identity
- 13 works with matches
- 13 proposals all marked as "same"

### Coverage
- Still returns UNKNOWN for most works
- 364 works have assertions
- 1035 works don't have assertions

---

## 5. WHAT STILL NEEDS TO BE DONE

### 1. Ingest More Data
- Archive.org: 50 records, but only 20 ext_ids
- OpenAlex: 50 records, but no ext_ids
- Sanskritree: 44 records, but no ext_ids

### 2. Link Works to Assertions
- 1035 works don't have assertions
- Need to create assertions for these works

### 3. Rebuild Coverage Engine
- Coverage engine returns UNKNOWN for most works
- Need to fix coverage computation

---

## 6. KEY FILES

| File | What it tells you |
|---|---|
| `FINAL-TASK.md` | Full roadmap (17 phases) |
| `PATALAPATH.md` | Strategic positioning |
| `PATALAPATH2.md` | Corrected phase map + what to steal |
| `DEV-PLAN.md` | Updated build plan |
| `RESEARCH-SUMMARY.md` | What we found in repos |
| `PEER-REVIEW-3.md` | Latest peer review |
| `PEER-REVIEW-4.md` | Honest self-assessment |
| `AGENTS.md` | Rules for agents |
| `README.md` | Project overview |
| `HANDSOVER-2026-08-17.md` | This file |

---

## 7. GIT STATE

```
Branch: master
Remote: https://github.com/prx0r/wiggly
Commits: 25
Latest: 5542bcf
```

---

## 8. THE ANTI-CHEAT RULE

**"Nothing written in README, commit messages or markdown counts as evidence."**

Evidence must be machine-produced from actual code execution.
Evidence bundle at `data/evidence/evidence-bundle.json` is the only valid proof.

---

## 9. HOW TO RUN

```bash
cd /root/openpatalanew

# Run conformance
PYTHONPATH=. python3 patala/tests/conformance.py

# Run experiments
PYTHONPATH=. python3 patala/experiments/gold_dossiers.py
PYTHONPATH=. python3 patala/experiments/cross_source_identity.py
PYTHONPATH=. python3 patala/experiments/openalex_query.py
PYTHONPATH=. python3 patala/experiments/coverage_frontier.py
PYTHONPATH=. python3 patala/experiments/provider_expansion.py
PYTHONPATH=. python3 patala/experiments/self_filling_discovery.py
PYTHONPATH=. python3 patala/experiments/annotation_interop.py
PYTHONPATH=. python3 patala/experiments/witness_collation.py

# Run API
python3 -m uvicorn patala.api:app --port 8801

# Check database
PGPASSWORD=patala psql -U patala -h 127.0.0.1 -d openpatala

# Check experiment logs
cat data/runs/gold-dossiers.jsonl
```

---

## 10. WHAT NOT TO DO

- Don't trust markdown claims — only machine evidence counts
- Don't add 20 more adapters before fixing the core
- Don't rebuild what exists in the old project
- Don't skip the anti-cheat rule
- Don't work on 10 things at once
- Don't build modules on broken data
