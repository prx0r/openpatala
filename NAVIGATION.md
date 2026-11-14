# NAVIGATION — resolve anything in OpenPāṭala
*Status: REFERENCE. How to resolve anything; reference.*

*2026-08-17 · Quick reference for finding anything in the project.*

---

## "I want to..."

| Goal | Go to |
|---|---|
| Understand the architecture | `README.md` → §Architecture |
| Check current bibliography/MCP rollout | `HANDSOVER-2026-11-12.md` |
| See what was built | `BUILD-NOTES-2026-08-17.md` |
| Check implementation status | `NEWBUILDCHECKLIST.md` |
| Run the system | `recipes.md` → R1-R8 |
| Drive with Hermes | `agentic.md` |
| Navigate the codebase | `MASTER.md` |
| Find a specific module | See table below |

## Module reference

| Module | Purpose | Key functions |
|---|---|---|
| `hashing.py` | Identity & hashing | `uuid7()`, `make_digest_set()`, `canonical_jcs_hash()` |
| `entities.py` | Entity models | `Work`, `Person`, `Edition`, `Translation`, etc. |
| `resolver.py` | Identity resolution | `Resolver.resolve()`, R0-R5 stages |
| `events.py` | Event store | `EventStore.append()`, `build_merkle_checkpoint()` |
| `ingest.py` | Ingestion pipeline | `IngestionPipeline.run()` |
| `api.py` | REST API | `/v1/works`, `/v1/bundle/{id}`, `/v1/resolve` |
| `completeness.py` | State computation | `CompletenessCompiler.compile()` |
| `db/store.py` | Database operations | `insert_work()`, `list_works()`, etc. |
| `conformance_test.py` | Verification | 12-step test suite |
| `factory/deepfinder.py` | Translation discovery | `run_deepfind()` |
| `factory/download.py` | Download verification | `enrich_translation()` |
| `factory/proof.py` | Translation proof | `prove_translation()` |

## Database tables (34)

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
