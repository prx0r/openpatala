*Status: HISTORICAL. Dated peer review snapshot; frozen (2026-08-17).*
he latest push is directionally correct, but it has not yet crossed the line from “implemented-looking” to “proved.” The two commits mostly fix the surface symptoms: UUID library adoption, RFC8785 library adoption, and a renamed five-suite conformance framework. The endgame still requires a much harder property: the whole scholarly state must survive model changes, schema changes, database destruction, source disappearance, and future agent infrastructure because permanent truth is identity + original observations/artifacts + append-only semantic history + provenance + historical schemas. Everything else is projection.

There are already several ways the latest commit can falsely report success. uuid6 and rfc8785 are not declared in requirements.txt, the supposedly removed unsafe UUID implementation still exists as the import fallback, and the convenience ID generators still truncate to 12 UUID characters. The old handwritten JCS implementation also remains callable even though canonical_jcs_hash() now uses rfc8785.

The larger problem is testing. REPLAY-CONFORMANCE says “destroy projections, rebuild from events, digest identical” but only writes five JSONL events and reads them back. ADAPTER-CONFORMANCE promises raw-byte retention and explicit rights but only checks dictionary keys. API-CONFORMANCE uses the ambient database and silently omits the bundle assertion when there are zero works. The resolver test doesn’t restart anything, schema immutability isn’t tested, and the UUID test generates only 10,000 IDs.

So I would give the agent this exact prompt now:

YOU ARE BUILDING OPENPĀṬALA 0.6: THE REPLAYABLE CORE.

DO NOT CONTINUE THE CURRENT PATTERN OF CHECKING OFF P0 ITEMS BECAUSE A FUNCTION,
CLASS, TABLE, OR TEST WITH THE RIGHT NAME EXISTS.

YOUR JOB IS TO MAKE THE ENDGAME ARCHITECTURE TRUE IN EXECUTION.

======================================================================
0. WHY THIS SYSTEM EXISTS
======================================================================

Pāṭala is NOT ultimately a Sanskrit database, translation pipeline, OpenAlex
clone, chatbot, course generator, or generic agent framework.

Sanskrit is the proving ground.

The eventual system is infrastructure for systematic search over unknown
reality: a durable machine-readable epistemic state that cheap agents can
continuously inspect, challenge, update and extend.

Future loop:

CURRENT QUALIFIED STATE
    ↓
OPEN QUESTION / HYPOTHESES
    ↓
CHEAP AGENT SEARCH + REASONING
    ↓
RESIDUAL CRUX / PROOF OBLIGATION
    ↓
SMALLEST SCARCE REALITY REQUEST
    ↓
NEW OBSERVATION
    ↓
ADJUDICATION
    ↓
STATE TRANSITION
    ↓
DEPENDENCY INVALIDATION
    ↓
REGENERATION OF DOWNSTREAM PRODUCTS
    ↓
NEW QUESTIONS

Eventually the scarce input may be:
- scholar judgment
- manuscript inspection
- institution attestation
- archival access
- physical observation
- experiment
- sensor/robot/lab output

Therefore the durable Pāṭala moat is NOT model inference.

It is:

IDENTITY
× ORIGINAL OBSERVATIONS
× PROVENANCE
× RIGHTS
× EVIDENCE LINEAGE
× SCHOLAR/INSTITUTION HISTORY
× NEGATIVE RESULTS
× OPEN QUESTIONS
× STATE TRANSITION HISTORY

The constitutional rule is:

    If inference becomes free tomorrow,
    permanent Pāṭala infrastructure must become MORE useful, not worthless.

======================================================================
1. THE PERMANENT TRUTH
======================================================================

Permanent truth is NOT:

- current Postgres tables
- current JSON layout
- current ontology
- current prompts
- current model
- current API representation
- current completeness projection
- current search index
- current agent framework

Permanent truth is:

1. stable opaque identity
2. exact original observed artifacts/bytes
3. observations describing acquisition context
4. append-only semantic events
5. derivation/provenance
6. immutable historical schemas
7. rights evidence
8. permanent merge/split/supersession history

Everything else MUST be disposable and rebuildable.

The four concepts that MUST NEVER be conflated are:

IDENTITY
"What thing are we talking about?"

CONTENT
"What exact bytes/state did we observe?"

INTERPRETATION
"What do we believe those observations mean?"

REPRESENTATION
"How do we expose that belief today?"

Therefore:

Entity ID
    != content hash
    != version ID
    != assertion
    != current projection

======================================================================
2. HARD CORE / SOFT EDGE
======================================================================

HARD CORE:

- IDs
- Artifacts
- Observations
- Events
- schemas
- provenance
- rights
- assertion/evidence history
- identity merge/split history
- review/adjudication history
- state cursors
- dependency history

SOFT EDGE:

- search
- embeddings
- LLMs
- prompts
- agent frameworks
- routing
- MCP
- rendered websites
- generated translations
- essays
- lessons
- video
- world models
- future robot controllers

Never allow a soft-edge implementation to become required to reconstruct the
hard core.

======================================================================
3. STOP EXPANDING SCOPE
======================================================================

DO NOT BUILD YET:

- NRAH
- autonomous research agents
- FoJin
- DGM
- Agent Lightning
- Greek
- education system
- media generation
- world simulation
- additional fancy serializers
- another ontology rewrite
- another large source adapter collection
- generic orchestration
- Rust rewrite

The next release is NOT feature growth.

The next release is:

    OPENPĀṬALA 0.6 — REPLAYABLE CORE

The release question is simply:

Can we destroy every disposable representation of scholarly state, disable
the network, and reconstruct the exact same semantic state using only
permanent Pāṭala history?

If NO, 0.6 is not complete.

======================================================================
4. FIRST: AUDIT THE LATEST PUSH
======================================================================

Do NOT trust commit messages.

Start from current master and independently verify every claim.

Known issues already visible in latest master:

A. requirements.txt currently does not declare uuid6 or rfc8785.

B. hashing.py still contains an unsafe handwritten UUID fallback.

C. hashing.py still contains truncated convenience generators such as:
   make_artifact_id()
   make_entity_id()
   make_observation_id()
   make_assertion_id()

D. hashing.py still contains the old handwritten JCS functions even though
   canonical_jcs_hash() now uses rfc8785.

E. current CORE-CONFORMANCE checks only 10k UUIDs.

F. current "schema immutability" test merely checks $schema and $id.

G. current REPLAY-CONFORMANCE never destroys/rebuilds Postgres.

H. current REPLAY-CONFORMANCE tests JSONL readback, not canonical state replay.

I. current RESOLVER-CONFORMANCE uses in-memory resolver state and never verifies
   persistence across restart.

J. current ADAPTER-CONFORMANCE does NOT prove raw-byte persistence.

K. current ADAPTER-CONFORMANCE does NOT prove rights enforcement.

L. current API-CONFORMANCE uses the ambient/live database.

M. current bundle API test silently disappears when zero works exist.

N. there is no acceptable proof until the test environment is created from
   repository-controlled migrations from an empty database.

Before coding, create:

    docs/audits/OPENPATALA-06-BASELINE.md

For every claimed property classify it:

    PROVEN
    IMPLEMENTED_NOT_PROVEN
    PARTIAL
    FALSE
    NOT_IMPLEMENTED

Evidence must be executable code paths/tests, not comments/docs.

======================================================================
5. BUILD RULE: NO FALLBACKS THAT CHANGE SEMANTICS
======================================================================

If a correctness-critical dependency is missing, FAIL CLOSED.

Example:

BAD:

try:
    from uuid6 import uuid7
except ImportError:
    use_homegrown_uuid()

GOOD:

from uuid6 import uuid7

and installation declares/pins the dependency.

Same rule for:

- RFC8785
- schema validation
- cryptographic signing
- storage
- rights decisions

No "best effort" implementation is allowed in the hard core.

======================================================================
6. FIX IDS COMPLETELY
======================================================================

One ID constructor.

All durable IDs use the full UUID.

No substring IDs.

No multiple ID implementations.

Introduce something like:

    new_id(EntityKind.WORK)
    new_id(EntityKind.EVENT)
    new_id(EntityKind.ARTIFACT)

Prefix is convenience only.
UUID is identity.

Delete every UUID implementation except the tested library wrapper.

Run a repository-wide AST/grep check that forbids UUID slicing.

Required executable gate:

    tests/core/test_ids.py

It MUST test:

- RFC UUID version == 7
- RFC variant
- full 128-bit representation
- every exported Pāṭala ID helper
- all Entity dataclass defaults
- all Event IDs
- all Artifact IDs
- all Observation IDs
- all Assertion IDs
- multiprocessing generation
- concurrent generation
- no truncation

The heavy collision test may be marked slow, but CI must run at least a large
parallel sample and a release verification command must run 10,000,000 IDs.

Also add a static test which fails if source contains known truncation patterns.

NO manual UUID fallback.

======================================================================
7. FIX CANONICAL JSON COMPLETELY
======================================================================

There must be exactly ONE canonical structured-data serializer.

Use RFC8785.

Delete or convert the handwritten jcs_canonicalize/_jcs_* implementation so
there is no second semantic implementation.

Use official RFC8785 test vectors.

Test hostile numeric and Unicode cases.

Any structured hash, Event payload digest, snapshot digest or Merkle leaf that
claims JCS MUST use the same canonicalizer.

======================================================================
8. ONE DATABASE CONFIGURATION
======================================================================

There must be exactly one DatabaseSettings implementation.

No DATABASE_URL defaults duplicated in modules.

Every:

- migration
- runtime write
- test
- API
- replay
- projection compiler

must resolve the same settings object.

Tests MUST create a disposable database.

Tests MUST NOT use the developer's existing OpenPāṭala database.

A full verification from a fresh clone must not depend on hidden/manual DB
schema changes.

Create schema_migrations:

    migration_id
    migration_digest
    applied_at

Do not silently edit migrations that may already have been applied.

Create new migrations fixing all code/schema drift.

======================================================================
9. ONE CANONICAL EVENT LEDGER
======================================================================

Postgres events becomes the canonical live ledger.

JSONL becomes EXPORT ONLY.

Delete dual-write semantics.

There must be ONE append path:

    append_event(...)

It:

1. validates EventEnvelope schema
2. canonicalizes payload
3. calculates payload digest
4. allocates DB cursor
5. inserts event
6. invokes projection reducer inside same transaction where appropriate

One semantic event has:

- one Event ID
- one cursor
- one payload digest
- one schema URI

Never generate a second "equivalent" event for another store.

Use BIGINT identity cursor, not application-maintained cursor.

Application DB role must be unable to UPDATE or DELETE canonical events.

Create tests that ACTUALLY execute UPDATE and DELETE and assert database
rejection.

======================================================================
10. DEFINE THE DURABLE EVENT VOCABULARY
======================================================================

Implement only events required for the current Sanskrit vertical, but enough
to reconstruct all current permanent state.

Minimum families:

ArtifactRegistered
RawObservationRecorded

EntityCandidateRecorded
CandidateAssertionRecorded

EntityCreated

AssertionRecorded
AssertionRetracted
AssertionSuperseded

ExternalIdentifierLinked

IdentityProposed
EntityMerged
EntitySplit

RightsAssessmentRecorded

ETextLinked
EditionLinked
WitnessLinked
TranslationLinked

ReviewRecorded
AdjudicationRecorded

Do not event-source implementation trivia.

Events describe semantic state transitions.

Each event has a reducer.

Reducer behavior must be deterministic.

======================================================================
11. ENTITY_IDENTITY IS CANONICAL; WORKS IS A PROJECTION
======================================================================

This dependency direction is mandatory:

    EntityCreated EVENT
        ↓
    entity_identity
        ↓
    type-specific projection

NEVER:

    INSERT works
        ↓
    therefore entity exists

Every canonical entity gets:

    opaque ID
    entity class
    lifecycle
    created event
    created timestamp

Work remains deliberately small.

Author/date/tradition remain Assertions.

======================================================================
12. BUILD THE FIRST REAL END-TO-END VERTICAL: GRETIL
======================================================================

Do not harden 13 adapters simultaneously.

Make GRETIL perfect first.

Required graph:

GRETIL TEI RESOURCE
    ↓
exact TEI bytes
    ↓
Artifact
    ↓
RawObservation
    ↓
ExtractionActivity
    ↓
WorkCandidate
+
ETextCandidate
    ↓
CandidateAssertions
    ↓
ResolutionProposal
    ↓
EntityCreated / identity linkage
    ↓
Work
+
EText
    ↓
DocumentSegments / passages where applicable
    ↓
Completeness projection
    ↓
/bundle

IMPORTANT:

A GRETIL file is an ETEXT.

It is NOT automatically identical to the abstract Work.

A source resource may create several candidates.

CandidateAssertions MUST attach using subject_candidate_id.

Do not attach every assertion in an ExtractionBundle to every candidate.

External IDs MUST resolve from candidate → canonical entity before permanent
linkage.

======================================================================
13. RAW OBSERVATIONS MUST MEAN RAW OBSERVATIONS
======================================================================

An observation is invalid if payload_artifact_id does not resolve to a stored
Artifact.

Artifact must correspond to exact bytes actually observed.

Tests must mutate one byte and prove fixity failure.

Do not create pretend Artifact IDs before storing bytes.

For GRETIL:

- retain exact TEI bytes
- store raw-byte digest
- preserve source path/provider locator
- preserve acquisition time
- preserve rights evidence/state
- extraction derives from that Artifact/Observation

No ephemeral _meta object may be the sole evidence behind a permanent
Assertion.

======================================================================
14. RIGHTS ARE EXECUTABLE, NOT DOCUMENTATION
======================================================================

Operations:

DISCOVER
FETCH_METADATA
FETCH_CONTENT
COMPUTE
CREATE_DERIVATIVE
REDISTRIBUTE
TRAIN

Decision:

ALLOW
DENY
REVIEW_REQUIRED

UNKNOWN MUST NOT MEAN ALLOW.

Create RightsDecisionEngine.

Test that restricted/unknown input cannot silently become a broader derived
permission.

Do not infer rights from the fact that a file is locally present.

======================================================================
15. PERSISTENT RESOLVER
======================================================================

Current in-memory indexes are insufficient.

Resolver correctness must survive:

    process A ingest
    process A exits
    process B starts
    same source ingested
    no duplicate entity generated

Use persistent external identifier and fingerprint indexes.

Resolution stages remain conservative:

R0 exact authoritative external identifier
R1 deterministic curated crosswalk
R2 bibliographic candidate retrieval
R3 fuzzy candidate proposal
R4 source corroboration
R5 scholar adjudication

Only provably safe identity rules auto-link/merge.

False merge is worse than duplicate entity.

Fuzzy matching must NEVER auto-merge.

Create adversarial frozen identity fixtures.

======================================================================
16. REPLAY IS THE RELEASE-DEFINING TEST
======================================================================

This is the most important requirement in the entire build.

Create a frozen test corpus of at least 100 representative GRETIL resources.

On an EMPTY disposable Postgres database:

1. apply migrations
2. ingest frozen corpus
3. compile projections
4. produce canonical semantic snapshot
5. record state cursor
6. record semantic state digest
7. destroy ALL disposable projections
8. disable all network access
9. restart process
10. rebuild using ONLY:
       permanent events
       permanent artifacts
       permanent schemas
11. regenerate projections
12. produce second semantic snapshot
13. compare

PASS only if:

    state_digest_before == state_digest_after

And meaningful structured state is equal.

NO:

- re-scraping
- re-downloading
- contacting GRETIL
- contacting OpenAlex
- LLM calls
- hidden seed scripts
- local legacy JSON rescue
- manually restored SQL
- reading old projection tables

The replay process should still work if all external sources disappeared.

That is the actual OpenPāṭala constitution.

======================================================================
17. NETWORK MUST BE PHYSICALLY DISABLED DURING REPLAY TEST
======================================================================

Do not "promise" replay does not use network.

Make network access fail.

Use test isolation / monkeypatch sockets / container network disabling.

Then run replay.

If any code attempts DNS/socket/http, test fails.

======================================================================
18. SCHEMA HISTORY MUST REALLY BE IMMUTABLE
======================================================================

Do not test schema immutability by checking $id exists.

Historical schema versions must have unique immutable URIs such as:

    .../assertion/1.0.0
    .../assertion/1.1.0

Once used by permanent data:

- bytes frozen
- digest frozen
- historical URI resolvable forever

Test:

1. publish schema
2. write permanent event using schema
3. attempt mutation/re-registration of same version
4. MUST FAIL
5. publish new version
6. old bytes/digest remain accessible

Registry must recompute and verify stored schema bytes.

======================================================================
19. MERKLE CHECKPOINTS
======================================================================

Do only after canonical Postgres ledger works.

Merkle leaf:

    SHA512(
      RFC8785(full immutable EventEnvelope)
    )

Do not hash an arbitrary subset of event fields.

Checkpoint covers contiguous cursor range.

Verification recomputes from canonical events.

If signing is not cryptographically implemented:

    signatures = []
    signing_state = UNSIGNED

Do NOT call hashes "signatures."

A fake signature is worse than an explicit unsigned checkpoint.

======================================================================
20. SNAPSHOT SEMANTICS
======================================================================

Separate:

SnapshotBody
SnapshotEnvelope

SnapshotBody includes:

- state cursor
- protocol version
- schema registry digest
- ledger checkpoint
- files + digests
- projection semantic digest

body_digest = hash(JCS(SnapshotBody))

Envelope adds:

- body
- body_digest
- signatures

No self-referential ambiguous digest.

======================================================================
21. MAKE /bundle REPRESENT REAL SCHOLARLY STATE
======================================================================

Eventually this endpoint is the killer agent primitive.

For current 0.6 it should truthfully expose available fields from canonical
state:

identity
aliases
external IDs
assertions
conflicts where known
ETexts
editions
witnesses
translations
rights
source coverage
provenance summary
completeness
state_cursor
state_digest

state_cursor is the actual canonical ledger cursor.

NEVER use current wall-clock time as state version.

No placeholder field may masquerade as implemented data.

Optional future expansions:

?include=evidence,history,observations

======================================================================
22. COMPLETENESS IS A PROJECTION OF KNOWLEDGE, NOT A GUESS
======================================================================

The eventual power of OpenPāṭala is that it maps HOLES.

A Work can expose things such as:

identity:
    UNKNOWN / CANDIDATE / RESOLVED / CONTESTED

source:
    NONE / CATALOG / SCAN / OCR / ETEXT / SCHOLARLY_ETEXT

translation:
    UNKNOWN
    SEARCHED_NONE_KNOWN
    PARTIAL
    FULL_EXISTING
    PATALA_MACHINE
    REVIEWED

bibliography:
    UNKNOWN / PARTIAL / ...

rights:
    ...

Do not infer identity "resolved" merely because preferred_title is non-empty.

Do not infer bibliography complete merely because OpenAlex/DOI exists.

UNKNOWN != NONE_KNOWN.

Negative knowledge requires SearchEvents / scoped search evidence.

======================================================================
23. THE NEXT-GENERATION GRAPH MUST REMAIN POSSIBLE
======================================================================

Do not implement all of this now, but make no architecture choice that prevents
the future graph.

Future Reality/Atlas graph:

Work
Person
Institution
Manuscript
Witness
Edition
Surrogate
EText
LogicalPassage
TextOccurrence
TextSpan
ImageRegion
Publication
Dataset
Observation

Future Proof graph:

Assertion
Proposition
EvidenceUse
Inference
Argument
Defeater
Assumption
Alternative
Crux
Uncertainty

Future Action graph:

OpenQuestion
Hypothesis
ProofObligation
Task
Run
EpistemicAction
RealityRequest
Outcome
NegativeResult

Future People graph:

Scholar
Institution
Agent
Reviewer
Contributor

plus:

judgments
expertise evidence
calibration
permissions
contribution history

Do not flatten these distinctions into generic JSON blobs that cannot later
be reasoned over.

======================================================================
24. SCHOLAR REVIEW CONSTITUTION
======================================================================

Not necessarily part of 0.6 implementation, but preserve this model:

MACHINE_PROPOSED != PĀṬALA_ASSERTED

ReviewEvent is immutable.

Adjudication is separate.

Scholar ACCEPT must NOT mutate machine proposal history into "truth."

PublishedAssertion:
    historical statement that scholar/source X said Y

ScholarAttestation:
    live/current endorsement by scholar

Those are different.

CREDIT != AUTHORITY != TRUTH != PAYMENT != PERMISSION != OWNERSHIP.

======================================================================
25. FUTURE AGENT CONSTITUTION
======================================================================

Agents never directly write "truth."

They may produce:

Observation
CandidateAssertion
ResolutionProposal
Hypothesis
ActionResult
ReviewRequest

Promotion into current qualified state happens through typed state transitions.

Future EpistemicCeiling examples:

MACHINE_CLOSABLE
FORMALLY_CLOSABLE
SOURCE_REQUIRED
EXPERT_REQUIRED
INSTITUTION_REQUIRED
OBSERVATION_REQUIRED
EXPERIMENT_REQUIRED
CURRENTLY_UNRESOLVABLE

Future system value comes from discovering when cheap intelligence has hit a
scarce-reality boundary.

Do not bake today's Hermes/OpenAI/Claude/provider semantics into permanent
schemas.

======================================================================
26. TESTING ANTI-CHEAT CONSTITUTION
======================================================================

THIS SECTION IS MANDATORY.

A test does not count merely because:

- function imports
- table exists
- endpoint returns 200
- list contains key
- value >= 0
- fixture is nonempty
- code does not throw
- comment says invariant
- test skips when state absent
- live developer DB happens to contain useful data
- network source happens to remain online

Every critical test must answer:

    WHAT BUG WOULD MAKE THIS TEST FAIL?

If no realistic violating implementation causes failure, rewrite test.

Never use:

    if data:
        assert ...

for mandatory behavior.

Never silently skip release-gating assertions.

No xfail/skip in release gates unless explicitly justified and release gate
fails while it remains skipped.

Tests must create their own state.

Tests must clean up their own state.

Tests must be order independent.

Tests must run on clean infrastructure.

Tests must verify negative cases.

======================================================================
27. REQUIRED TEST SUITES
======================================================================

CORE-CONFORMANCE must prove:

- package installation from declared dependencies
- UUID7 implementation
- all Pāṭala IDs full entropy
- no truncation
- RFC8785 official vectors
- artifact mutation detection
- schema validation
- schema immutability
- fail-closed correctness dependencies

LEDGER-CONFORMANCE must prove:

- sole Postgres canonical ledger
- one semantic event = one ID
- DB cursor monotonic
- payload digest correct
- UPDATE rejected
- DELETE rejected
- full EventEnvelope Merkle coverage
- checkpoint tampering detected

REPLAY-CONFORMANCE must prove:

- fresh DB
- frozen corpus ingest
- projection digest before
- projection destruction
- network disabled
- process restart
- rebuild from permanent state
- projection digest after
- exact semantic equality

RESOLVER-CONFORMANCE must prove:

- persistence across restart
- exact external-ID reuse
- repeated ingest idempotence
- merge behavior
- split behavior
- old ID resolution
- fuzzy false merge prevention
- type preservation
- all external IDs point to canonical entities

ADAPTER-CONFORMANCE must prove for GRETIL:

- discovery fixture
- exact source bytes retained
- artifact digest matches fixture bytes
- RawObservation references Artifact
- extraction refers to Observation
- candidate typing correct
- assertions attach to intended candidate
- rights explicit
- malformed source fails safely
- repeated ingest idempotent

RIGHTS-CONFORMANCE must prove:

- UNKNOWN is not ALLOW
- DENY blocks operation
- allowed metadata does not imply content permission
- derivative rights do not silently broaden
- locally available file does not imply rights

API-CONFORMANCE must prove:

- clean test DB
- deterministic fixture state
- stable IDs
- merge redirect semantics
- split ambiguity semantics
- /changes cursor semantics
- /bundle contents
- actual state_cursor
- actual state_digest
- rights-aware content behavior
- no placeholder endpoint reported as fully implemented

======================================================================
28. REQUIRED CLEAN-ENVIRONMENT TEST
======================================================================

Create a verification environment from only:

    git checkout
    declared package dependencies
    Postgres
    checked-in migrations
    checked-in test fixtures

NOTHING ELSE.

Specifically, move/rename any known local development corpus paths during this
test so accidental dependence fails.

The build must install from requirements/lock file successfully.

This test would currently catch the missing uuid6/rfc8785 declarations.

======================================================================
29. REQUIRED DESTRUCTIVE TEST
======================================================================

Create:

    scripts/verify_replay_from_zero.sh

or equivalent.

It must:

- create disposable DB
- migrate
- load frozen GRETIL fixture
- capture semantic snapshot A
- stop app
- destroy projection tables/data
- disable network
- start new process
- replay
- capture semantic snapshot B
- compare
- deliberately corrupt one artifact
- prove integrity verification fails
- restore artifact
- deliberately mutate one replay event in test setup with privileged admin
- prove checkpoint verification fails

The script exits 0 ONLY when every property succeeds.

======================================================================
30. REQUIRED DOUBLE-INGEST TEST
======================================================================

Fresh DB:

ingest corpus once
snapshot counts/IDs

restart process

ingest exact same corpus again

Required:

same canonical entity IDs
same external-ID links
no duplicated assertions unless event semantics explicitly represent a new
observation
no duplicate EText entities
no accidental Work proliferation
no false merges

This is essential before autonomous ingestion.

======================================================================
31. REQUIRED CRASH TEST
======================================================================

Inject failure at each boundary:

after artifact write
after observation event
after candidate extraction
during resolution
before projection commit

Restart.

System must converge safely.

Orphan content-addressed artifact is acceptable and collectible.

Canonical state referring to nonexistent artifact is NOT acceptable.

======================================================================
32. REQUIRED FRESH-DATABASE MIGRATION TEST
======================================================================

Current live DB is NOT evidence.

Test:

empty PostgreSQL
→ migration 001...
→ latest migration
→ application startup
→ fixture ingest
→ every API path used by conformance

No manual SQL.

No schema mismatch.

Run migration sequence twice where appropriate and prove expected
idempotency/migration-state behavior.

======================================================================
33. REQUIRED STATIC REPOSITORY AUDIT
======================================================================

Release verification must fail on:

- UUID slicing/truncation in durable ID creation
- duplicate DATABASE_URL configuration
- JSONL writes to canonical event path
- fake cryptographic signature implementation
- "or True" in tests
- mandatory assertions guarded by optional `if results`
- placeholder production status claims
- direct permanent projection writes bypassing event path
- hidden hardcoded /root corpus dependency in core tests
- current-time-generated state version

Use AST/static checks where grep is too weak.

======================================================================
34. CI IS PART OF THE PROOF
======================================================================

Add CI.

A local claim "5/5 passes" is not release evidence.

CI starts on clean infrastructure and runs the release gates.

At minimum:

fast suite on each push
full replay integration suite on main/PR
release-heavy suite including high-volume ID test before tagged release

Produce machine-readable report:

    build/verification-report.json

containing:

commit SHA
migration head
schema registry digest
test suite results
fixture digest
state digest before
state digest after
event count
artifact count
rights-test result
resolver idempotence result

No report means no VERIFIED release claim.

======================================================================
35. STATUS VOCABULARY
======================================================================

Use only:

DESIGNED
IMPLEMENTED
TESTED
PROVEN

Meanings:

DESIGNED:
document/schema exists

IMPLEMENTED:
real execution path exists

TESTED:
test exercises path

PROVEN:
adversarial release gate establishes claimed invariant

Do NOT call something PROVEN because a happy-path smoke test passed.

Do NOT claim "P0-01 fixed" until every exported ID constructor and clean
installation passes.

======================================================================
36. RELEASE GATES FOR OPENPĀṬALA 0.6
======================================================================

0.6 is PROVEN only when ALL are true:

FULL SAFE IDS                            PASS
RFC8785 OFFICIAL VECTORS                PASS
CLEAN INSTALL                           PASS
CLEAN DB MIGRATION                      PASS
ONE CANONICAL LEDGER                    PASS
DB EVENT IMMUTABILITY                   PASS
RAW SOURCE BYTES RETAINED               PASS
OBSERVATION→ARTIFACT INTEGRITY          PASS
TYPED CANDIDATES                        PASS
ASSERTION SUBJECT CORRECTNESS           PASS
CANONICAL EXTERNAL-ID INTEGRITY         PASS
RESOLVER RESTART PERSISTENCE            PASS
DOUBLE INGEST IDEMPOTENCE               PASS
NO FUZZY AUTO-MERGES                     PASS
EXECUTABLE RIGHTS                       PASS
SCHEMA IMMUTABILITY                     PASS
ZERO-NETWORK REPLAY                     PASS
BEFORE/AFTER STATE DIGEST MATCH         PASS
MERGE HISTORY REPLAY                    PASS
SPLIT HISTORY REPLAY                    PASS
ARTIFACT CORRUPTION DETECTED            PASS
EVENT TAMPERING DETECTED                PASS
BUNDLE FROM REBUILT STATE               PASS
STATE CURSOR REAL                       PASS
STATE DIGEST REAL                       PASS
CI FROM CLEAN ENVIRONMENT               PASS

One failure means:

    OPENPĀṬALA 0.6 = NO-GO

There is no PARTIAL PASS release state.

======================================================================
37. MASS-INGEST GATE
======================================================================

DO NOT bulk ingest millions of records after 0.6 merely because tests are
green.

Next run:

10-resource GRETIL canary
100-resource GRETIL proof corpus
full GRETIL
PANDiT identity integration
Darshana ontology torture test
OpenAlex scholarly graph
then larger source discovery

At each scale:

measure duplicate rate
dangling references
rights failures
resolver uncertainty
replay digest
processing failures
event/projection divergence

Autonomous ingestion is forbidden until the 100-resource GRETIL vertical is
fully replayable.

======================================================================
38. DO NOT OPTIMIZE FOR TEST COUNT
======================================================================

Do not return:

"73/73 tests passed."

Return:

"These specific invariants are now demonstrated by these destructive
experiments."

The project cares about PROPERTIES, not test quantity.

======================================================================
39. REQUIRED FINAL HANDOVER
======================================================================

When finished, output:

A. EXACT COMMITS CREATED

B. FILES CHANGED

C. CURRENT ARCHITECTURE
   permanent truth
   canonical event path
   artifact path
   projection path

D. BEFORE/AFTER BASELINE
   which previously false properties became proven

E. FULL COMMAND TRANSCRIPT
   exact verification commands
   exit codes

F. DESTRUCTIVE REPLAY RESULT
   state digest before
   state digest after
   event count
   artifact count
   network-disabled proof

G. DOUBLE-INGEST RESULT
   first-run entity counts
   second-run entity counts
   duplicate count

H. ADVERSARIAL FAILURES INJECTED
   what was deliberately corrupted
   exact expected rejection

I. REMAINING UNPROVEN PROPERTIES

J. MASS-INGEST DECISION
   exactly one:
       GO
       NO-GO

Do not describe planned work as completed work.

Do not update README/status claims until the corresponding release gate really
passes.

======================================================================
40. STARTING ORDER
======================================================================

Do this in this order:

CURRENT-STATE AUDIT
→ clean dependencies
→ IDs/JCS fully correct
→ one DB config
→ fresh migrations
→ one Postgres event ledger
→ event immutability
→ Artifact/RawObservation wiring
→ typed GRETIL vertical
→ persistent resolver
→ executable rights
→ deterministic reducers
→ projection destroy/replay
→ semantic state digest
→ bundle/state cursor
→ adversarial conformance
→ CI
→ 100-resource canary
→ final GO/NO-GO

Do NOT skip ahead.

======================================================================
THE NORTH STAR
======================================================================

A decade from now, the interesting parts of Pāṭala should NOT be that a 2026
LLM generated a translation.

The interesting parts should be that Pāṭala can tell an agent:

- exactly what object scholars mean
- exactly what source bytes were observed
- exactly where they came from
- exactly what was inferred from them
- exactly which evidence supports a claim
- exactly which sources are independent or derivative
- exactly which scholar/institution judged what
- exactly what was rejected
- exactly which questions remain open
- exactly what new observation would resolve them
- exactly what changed when new evidence arrived
- exactly which downstream objects became stale
- exactly how current qualified state can be reconstructed

OpenPāṭala 0.6 is the foundation of that future.

BUILD THE FOUNDATION.

DO NOT BUILD MORE THEATRE.

That is the prompt I would use. It gives the coding agent the why, so it doesn’t optimize for fixing 27 isolated tickets and accidentally destroy the endgame, but then makes the immediate job extremely narrow: prove the replayable hard core.

The biggest change from the previous review is that I would now stop feeding it individual defects one by one. The latest commits show exactly how that goes wrong: it hears “use UUID library,” does that, leaves the unsafe fallback and truncated helper functions, then marks P0-01 fixed; it hears “five conformance suites,” creates five functions with those names, and reports 5/5 even though the defining destructive experiments aren’t performed.

The correct unit of work now is an invariant plus an experiment capable of falsifying it. Once it produces the same state digest after deleting projections, killing network access, restarting the process, and replaying from artifacts/events/schemas alone, the architecture becomes genuinely interesting. Then you can safely resume the much larger Pāṭala trajectory: corpus expansion → scholar state → OpenQuestions/ProofObligations → RealityRequests → active research OS.