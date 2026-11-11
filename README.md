# OpenPāṭala — The Scholarly State Machine for Premodern Texts

**Repository:** https://github.com/prx0r/openpatala
**Status:** current live-box state is recorded in [`OPENPATALA.md`](OPENPATALA.md); the counts below are an archived Phase 1.0 snapshot.
**Branch:** master

---

## What it is

OpenPāṭala is the identity, provenance, and epistemic memory layer across fragmented Sanskrit databases. It doesn't own scans, OCR, or translations — it owns the connections between them.

> "OpenPāṭala is not the archive. It is the memory and research protocol over the archives."

## Quick start

```bash
# Clone
git clone https://github.com/prx0r/openpatala.git
cd openpatala

# Install
pip install -r requirements.txt

# Start API
python -m uvicorn patala.api:app --port 8801

# Query
curl http://127.0.0.1:8801/health
curl http://127.0.0.1:8801/v1/works?limit=5
curl http://127.0.0.1:8801/v1/bundle/{id}
curl http://127.0.0.1:8801/v1/bibliography/facets
# Use only values reported by the facets response.
curl "http://127.0.0.1:8801/v1/bibliography/search?work_type=TANTRA&limit=20"

# Run conformance
PYTHONPATH=. python3 patala/tests/conformance.py
```

### MCP bibliography workflow

The stdio server uses the same database search helpers as the REST API. The
read-only sequence is `bibliography_facets` → `search_bibliography` →
`get_bundle`. This source branch adds the first two tools. The live-box report
in [`OPENPATALA.md`](OPENPATALA.md) is a dated 2026-11-07 snapshot; update the
deployed endpoint and verify its tool list before describing these tools as live.

In the Svatantrya federation, this child is named `openpatala_mcp`, so the
federated names are `openpatala_mcp__bibliography_facets` and
`openpatala_mcp__search_bibliography`. The gateway discovers child tools from
`tools/list`; these names appear there after this child version is deployed.
The current MCP endpoint uses a shared bearer credential. Keep that credential
out of plugin manifests and repositories; use a user-scoped connection when the
estate's OAuth/read-sheaf auth is available.

## Architecture

```
PERMANENT MEMORY          ACTIVE INTELLIGENCE
identity, artifacts,      agents, models, retrieval,
observations, assertions, search, translation,
provenance, rights,       argumentation, evolution,
adjudication, history     planning, media
         │                        │
         └────────────┬───────────┘
                      ▼
            CURRENT QUALIFIED STATE
                      │
                      ▼
                  QUESTIONS
                      │
                      ▼
           PROOF OBLIGATIONS / CRUXES
```

## What's built — archived Phase 1.0 snapshot

The following counts describe the historical build snapshot; they are not the
current production database totals. For the dated live-box state, see
[`OPENPATALA.md`](OPENPATALA.md).

- **1099 works** from GRETIL, Sanskritree, Archive.org, Crossref, PANDiT
- **247 assertions** linked to canonical entities
- **108 external IDs** all resolving to canonical entities
- **2181 events** in append-only ledger
- **11 adapters** (GRETIL, Sanskritree, Archive.org, Crossref, PANDiT, OpenAlex, Darshana, Muktabodha, ORCID, ROR, WikiData)
- **7 serializers** (PROV-O, Web Annotation, DataCite, CIDOC CRM, RO-Crate, C2PA, HuggingFace)
- **22 JSON schemas** (v2)
- **34 Postgres tables**

## Verified — archived Phase 1.0 snapshot

- 6 Proofs (A-F): all PASS
- 26 Release Gates: all PASS
- 5/5 Conformance suites: PASS
- End-to-end red team: 4/4 PASS (hermes-verified)
- Phase 0.6: Replayable Hard Core ✓
- Phase 1.0: OpenPāṭala Corpus ✓

## Evidence

Machine-produced, not markdown claims:
- `data/evidence/evidence-bundle.json`
- `data/runs/e2e-redteam.jsonl`
- `data/runs/gates-verified.jsonl`

**Anti-cheat:** "Nothing written in README, commit messages or markdown counts as evidence."

## Status — archived Phase 1.0 snapshot

```
works: 1099
assertions: 247
ext_ids: 108
events: 2181
state_cursor: 3315
state_digest: 6477eadca1de1ab54eb5265e4d1ab929...
```

## Next

See `DEV-PLAN.md` — Phase 1.2 (self-filling source graph).
