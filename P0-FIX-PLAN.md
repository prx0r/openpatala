# P0 FIX PLAN — Based on Peer Review
*Status: SUPERSEDED. P0 fixes from peer review; superseded by later work (2026-08-17).*

*2026-08-17 · Fix all 27 P0 issues from peer review.*

## Priority 1: Core correctness (P0-01, P0-02, P0-03)

### P0-01: Fix UUIDv7 implementation
- Replace custom bit packing with proper uuid7 library
- Use full 128-bit UUIDs (not truncated)
- Add binary gate test: 10M IDs, all unique

### P0-02: Fix JCS implementation
- Use established RFC 8785 library
- Remove `or True` from conformance test
- Add hostile fixtures (-0.0, 1e30, Unicode)

### P0-03: Unify event store
- Make Postgres the sole canonical ledger
- JSONL becomes export/archive only
- Single Event ID, single cursor, single payload digest

## Priority 2: Ingestion correctness (P0-05, P0-06, P0-07, P0-09, P0-10)

### P0-05: Fix ingestion pipeline
- Call fetch_content() for every observation
- Persist artifacts and raw_observations
- Never pass ephemeral _meta dicts to canonical writes

### P0-06: Fix Archive.org adapter
- Store actual API responses as artifacts
- RawObservation points to real Artifact IDs

### P0-07: Wire GRETIL bytes into canonical evidence
- Use GRETIL as first hardened vertical
- Persist TEI bytes as artifacts

### P0-09: Fix entity typing
- ETEXT stays ETEXT, not promoted to Work
- EntityFactory.create() for typed creation

### P0-10: Fix assertion bundles
- Use subject_candidate_id to attach assertions to correct candidate
- Resolve candidate_id → canonical_entity_id independently

## Priority 3: Identity correctness (P0-08, P0-11, P0-12)

### P0-08: Persistent resolver
- Query persisted indexes, not in-memory
- Hydrate from Postgres on startup

### P0-11: External IDs resolve to canonical entities
- Binary invariant: every ext_id joins to entity_identity

### P0-12: entity_identity is the authority
- EntityCreated event → entity_identity → work_current projection
- Never: works row → therefore entity exists

## Priority 4: Schema/replay correctness (P0-13, P0-14, P0-15, P0-17)

### P0-13: Reproducible migrations
- Single DatabaseSettings, no defaults outside it
- Migration history table

### P0-14: Append-only schema registry
- Directory-based: schemas/family/version/schema.json
- Each version immutable

### P0-15: Cryptographic Merkle checkpoints
- Leaf = SHA-512(JCS(full EventEnvelope))
- Real signatures or explicitly unsigned

### P0-17: Snapshot digest self-reference bug
- Define SnapshotBody vs SnapshotEnvelope explicitly

## Priority 5: Testing (P0-18, P0-19, P0-20)

### P0-18: Replace conformance suite
- 5 test suites: CORE, REPLAY, RESOLVER, ADAPTER, API
- Each must actively violate invariant and verify rejection

### P0-19: Contract tests for adapters
- Frozen fixtures, not regex validation
- Live test optional

### P0-20: Fix adapter count/status docs
- Match actual adapter tree

## Priority 6: Product correctness (P0-24, P0-25, P0-26)

### P0-24: /frontier/translations from canonical state
- Compile from SearchEvents + Translation entities
- Distinguish UNKNOWN vs NONE_KNOWN

### P0-25: Real state_version in /bundle
- Use max committed event cursor + projection digest

### P0-26: Trustworthy completeness
- Pure SQL/materialized projection
- Each dimension has explicit compiler version
