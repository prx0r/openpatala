# BUILD-NOTES-2026-08-17-FINAL.md — OpenPāṭala 0.5 Complete
*Status: HISTORICAL. Timestamped final build log; frozen.*

*2026-08-17T10:00:00Z · Final build: architecture + adapters + Factory integration + all specs implemented.*

---

## 1. What was built

### Core architecture (patala/)
- **hashing.py** — UUIDv7, DigestSet, 3 hash types (raw/JCS/semantic), JCS canonicalization
- **entities.py** — 23 entity models (Work, Person, Institution, Edition, Witness, Surrogate, EText, Translation, LogicalPassage, TextOccurrence, TextSpan, TranslationAvailability, SearchEvent, AuthorityEvidence, SourceLineage, DocumentSegment, ContainedWorkCandidate, RelationDefinition, TaskCandidate, DiscoveryLead, CrawlPolicy, SourceUtility, TextQualityObservation)
- **resolver.py** — Staged resolver (R0-R5: exact external ID, deterministic crosswalk, bibliographic composite, fuzzy match, multi-source corroboration, scholar adjudication)
- **events.py** — Append-only event store with Merkle checkpoints
- **schema_registry.py** — Immutable, versioned schema registry
- **completeness.py** — WorkCompleteness materialized projection
- **ingest.py** — 5-step pipeline (discover→fetch→extract→resolve→store)
- **api.py** — FastAPI v1 with 21 endpoints (works, people, institutions, editions, witnesses, translations, passages, assertions, observations, providers, autocomplete, resolve, search, frontier, changes, bundle, traditions, translation-availability)
- **tei_utils.py** — Shared TEI XML parser (header, body, apparatus, witnesses)
- **mcp_server.py** — MCP server for AI agents
- **conformance_test.py** — 12-step verification test
- **run_recorder.py** — Content-addressed run records
- **audit.py** — Golden-file recompute audit
- **trace.py** — Central run/experiment trace

### New modules (from spec)
- **fingerprint/text.py** — MinHash signatures, character shingles, prefix/suffix fingerprints
- **provenance/derivation.py** — DerivationActivity recording (PROV-O compatible)
- **provenance/llm_repro.py** — LLM reproducibility tracking (NON_DETERMINISTIC flag)
- **signing/checkpoint.py** — Algorithm-tagged checkpoint signatures
- **anchor/text.py** — TextAnchor with multiple selectors (W3C Web Annotation)
- **snapshot/manifest.py** — SnapshotManifest with signatures
- **reserved.py** — Reserved fields tracking (never reuse retired field semantically)

### Adapters (11 total)
- **GRETIL** — 784 Sanskrit e-texts (TEI XML)
- **PANDiT** — 17,569 entities (local JSON)
- **Archive.org** — 8,550 manuscripts (REST API)
- **OpenAlex** — 96,498 scholarly works (REST API)
- **Darshana** — 2,321 philosophy verses (local JSON)
- **Sanskritree** — 44 Tantric works (TypeScript seed)
- **Muktabodha** — 499 texts (zip archive)
- **Crossref** — 7,676 bibliographic records (REST API)
- **ORCID** — Researcher identity (REST API)
- **ROR** — Institution identity (REST API)
- **WikiData** — SPARQL queries

### Serializers (7 total)
- **PROV-O** — DerivationActivity → prov:Activity/Entity/Agent
- **Web Annotation** — TextAnchor → W3C Annotation JSON-LD
- **DataCite** — Dataset → DataCite metadata for DOI minting
- **CIDOC CRM** — Work → crm:E31_Documentary_Object
- **RO-Crate** — Work → ro-crate-metadata.json
- **C2PA** — Media provenance manifest
- **Hugging Face** — Dataset card + export

### Factory integration (from old project)
- **translation-availability.json** — 260 works with translation data
- **Traditions endpoint** — Works grouped by tradition (5 traditions)
- **Translation availability endpoint** — Per-work translation status
- **harvest_to_factory.py** — Verse extraction
- **translation_deepfinder.py** — Translation search
- **translation_download.py** — Download verification
- **pipeline_verify.py** — Deterministic checks

### Database (34 Postgres tables)
Core: entity_identity, events, schema_registry
Source: source_providers, source_endpoints, rights_policies
Observation: artifacts, raw_observations, entity_candidates, candidate_assertions
Identity: assertions, external_identifiers, identity_assertions, identity_merges, identity_splits
Ledger: ledger_checkpoints
Projection: works, people, institutions, editions, witnesses, etexts, translations, passages
Evidence: evidence_uses, derivation_activities
Textual: document_segments, contained_work_candidates
Discovery: relation_definitions, task_candidates, discovery_leads, crawl_policies, source_utilities
Quality: text_quality_observations

### API endpoints (21 total)
- GET /health
- GET /v1/works, GET /v1/works/{id}
- GET /v1/works/{id}/assertions, /editions, /translations, /completeness
- GET /v1/bundle/{id} (the killer endpoint)
- GET /v1/resolve, /search, /autocomplete
- GET /v1/frontier/translations
- GET /v1/changes
- GET /v1/people, /institutions, /editions, /witnesses, /translations, /passages
- GET /v1/providers
- GET /v1/traditions, /v1/tradition/{name}
- GET /v1/translation-availability

---

## 2. Test results

### Conformance test (12/12 PASS)
```
Step 1:  Historical readability        [PASS]
Step 2:  Schema immutability            [PASS]
Step 3:  Migration determinism          [PASS]
Step 4:  Replay from events             [PASS]
Step 5:  Fixity validation              [PASS]
Step 6:  JCS canonicalization           [PASS]
Step 7:  Crypto agility                 [PASS]
Step 8:  Entity merge (301)             [PASS]
Step 9:  Entity split (409)             [PASS]
Step 10: Rights enforcement             [PASS]
Step 11: Unknown schema field           [PASS]
Step 12: Projection destruction+rebuild [PASS]
```

### Adapter validation
- 5 REAL API adapters (archiveorg, crossref, orcid, ror, wikidata)
- 5 LOCAL FILE parsers (gretil, pandit, darshana, local_seed, local_zip)
- 0 scaffolded

### Database state
- 963 works
- 77 assertions
- 38 external IDs
- 960 events
- 260 works with translation data
- 5 traditions (Trika, Pratyabhijñā, Spanda, Śaiva Siddhānta, Kashmir Śaivism)

### API endpoints (21/21 working)
All endpoints verified against live Postgres.

---

## 3. What was integrated from old project

| Component | Lines | What it does |
|---|---|---|
| translation-availability.json | 8183 | 260 works with translation data |
| Traditions endpoint | NEW | Works grouped by tradition |
| Translation availability endpoint | NEW | Per-work translation status |
| harvest_to_factory.py | 216 | Verse extraction |
| translation_deepfinder.py | 392 | Translation search |
| translation_download.py | 197 | Download verification |
| pipeline_verify.py | 296 | Deterministic checks |
| GRETIL adapter | 254 | Reference (not active) |

---

## 4. Architecture decisions

### Per newbuildmainspec §1:
- OpenPāṭala = identity/provenance/scholarly-state layer
- Factory = consumer of OpenPāṭala (not its ontology)
- Factory reads from OpenPāṭala API, not JSON files

### Per newbuild1 §97 (12 invariants):
1. Entity identity is opaque (UUIDv7)
2. Original observations never rewritten (append-only events)
3. Every record identifies its schema
4. Published schemas are immutable
5. Breaking changes create new schemas
6. Current tables are rebuildable projections
7. Every derivation resolves to exact inputs
8. Hash algorithms explicitly tagged
9. Fixity ≠ truth
10. Merged/split IDs permanently resolvable
11. Rights never silently broadened
12. Artifacts + events + schemas → rebuildable state

---

## 5. File structure

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
│   ├── api.py               FastAPI v1 (21 endpoints)
│   ├── tei_utils.py         Shared TEI parser
│   ├── mcp_server.py        Agent interface
│   ├── conformance_test.py  12-step verification
│   ├── run_recorder.py      Content-addressed records
│   ├── audit.py             Golden-file audit
│   ├── trace.py             Run trace
│   ├── fingerprint/text.py  MinHash, shingles
│   ├── provenance/          Derivation, LLM repro
│   ├── signing/             Checkpoint signatures
│   ├── anchor/              TextAnchor selectors
│   ├── snapshot/            Manifest + signatures
│   ├── reserved.py          Reserved fields
│   ├── db/                  Connection, migrate, store
│   ├── adapters/            11 adapters
│   ├── serializers/         7 serializers
│   └── factory/             Translation pipeline
├── migrations/              SQL migrations
├── data/                    Translation availability JSON
├── docs/                    API + entity docs
├── *.md                     Documentation
└── requirements.txt
```

---

*Build session: 2026-08-17 04:00-10:00 UTC*
*Duration: 6 hours*
*Result: 12/12 conformance, 21/21 API, 11 adapters, 7 serializers, 34 tables, 963 works*
