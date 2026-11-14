*Status: HISTORICAL. Dated peer review snapshot; frozen (2026-08-17).*


I found it. prx0r/wiggly is a much better architectural direction than the earlier OpenPāṭala builds, but I would currently classify it as:

Architecturally promising prototype, not mass-ingest-safe infrastructure.

The repo has clearly absorbed the hardening design: artifacts → observations → assertions → identity → adjudication → rebuildable current state, minimal Work, separate Translation, staged resolver, schema registry, Merkle checkpoints, completeness, adapters, API, MCP.

But the implementation is substantially less complete than the README/build notes claim. Several of the exact invariants it says are proven are currently false. The good news is that I would harden this repo rather than rewrite it again.
Verdict

Area
	

Architecture
	

Implementation
	

Verdict

Core epistemic model
	

A
	

B-
	

Keep

Entity modelling
	

A-
	

B
	

Keep

Artifact/observation concept
	

A
	

D
	

Fix immediately

Event sourcing
	

A
	

D
	

Major repair

Schema evolution
	

A
	

D+
	

Major repair

Identity resolver
	

B+
	

D
	

Major repair

Hashing/IDs
	

A concept
	

F implementation
	

P0

Rights model
	

A-
	

D
	

Wire it

Adapters
	

B
	

D+/C-
	

Normalize + test

API shape
	

B+
	

D+
	

Rebuild projections

Completeness/frontier
	

A idea
	

D
	

Reimplement

Conformance/testing
	

A specification
	

F tests
	

Replace

Autonomous ingestion
	

B architecture
	

D
	

Not ready

Mass-ingestion readiness
	

—
	

—
	

NO-GO

The most important finding is that this repo suffers from spec-shaped implementation: many sophisticated concepts are present as classes/files/table names, so a superficial audit says “done,” but their actual execution paths don’t enforce the claimed properties.

That is exactly what you want this peer review to catch.
P0-01 — IDs are unsafe

This is the clearest mass-ingest blocker.

hashing.py implements its own UUIDv7 bit packing, then several helpers do this:

f"PTART_{uuid7()[:12]}"
f"PTW_{uuid7()[:12]}"

and other entity models take only the first 16 hex characters after removing hyphens.

Because UUIDv7 starts with timestamp information, chopping off the back is particularly dangerous: you are preferentially throwing away the random entropy.

Also, the handwritten UUIDv7 bit layout does not correctly implement RFC 9562.
Replace

Do not write UUIDv7 yourself.

Use a tested UUIDv7 implementation and retain all 128 bits:

def new_id(kind: EntityKind) -> str:
    return f"{PREFIX[kind]}_{uuid7()}"

or encode all 128 bits into Crockford Base32 if you want compact IDs.

For example conceptually:

PTW_01K2...

but preserve ~128 bits, not 48–64.
Binary gate

Generate 10 million IDs concurrently across multiple processes:

pytest -q tests/core/test_ids.py

PASS iff:

10,000,000 generated
10,000,000 unique
RFC9562 reference vectors PASS
timestamp monotonicity properties PASS
cross-process collision count = 0

And grep must return nothing:

grep -R "uuid7().*\[:\|uuid7().*replace.*\[:" patala

Expected:

no matches

P0-02 — the JCS implementation is not trustworthy enough

canonical_jcs_hash() claims RFC 8785 but implements JCS manually. It uses Python key sorting and Python repr(float). Those are not sufficient to guarantee RFC 8785’s ECMAScript number serialization and UTF-16 property ordering edge cases.

Yet the conformance test supposedly proving JCS correctness literally contains:

assert '"a":2' in str(test_obj) or True

which can never fail.
Replace

Use an established RFC 8785 implementation.

Make:

raw digest
canonical-record digest
semantic text fingerprint

three explicitly different types.

Never let callers supply an untyped hash.
Binary gate

Official RFC test vectors plus cross-runtime Python/JS/Rust fixture:

pytest -q tests/core/test_jcs.py

For every fixture:

python bytes == JS bytes == Rust bytes
SHA-512 identical

Include hostile fixtures:

-0.0
1e30
Unicode supplementary characters
escaped controls
nested structures
object ordering

P0-03 — you currently have
two canonical event stores

This is probably the biggest architectural problem.

events.py writes:

data/events/events.jsonl

and computes a payload digest.

db/store.py separately writes:

Postgres.events

but stores:

payload_digest = {}

And ingest.py creates both independently, even generating different Event IDs for them.

Therefore:

JSONL history ≠ Postgres history

There is no single source of truth.
Decision

Make Postgres events the sole canonical live event ledger.

JSONL becomes:

export format
archive format
snapshot component

not a writer.

All state mutations use:

with transaction:
    event = append_event(...)
    apply_projection(event)

One Event ID.

One cursor.

One payload digest.

One schema URI.
Database cursor

Replace:

cursor SERIAL

with a proper monotonic BIGINT GENERATED ... AS IDENTITY.

No application-assigned cursor.
P0-04 — invariant #12 is currently false

The README says:

artifacts + events + schemas → rebuildable state.

But rebuild_from_events() only understands:

EntityCreated

and recreates everything as a Work.

It does not replay:

assertions
external IDs
people
institutions
editions
witnesses
e-texts
translations
rights
merges
splits
observations
adjudications

Worse, the “projection rebuild” conformance test admits:

events don't capture assertion creation yet

and then recontacts/re-ingests external sources to reconstruct the DB.

That’s not replay.

That’s re-scraping reality.
Correct requirement

This command:

patala projection destroy --all
patala projection rebuild

must use zero network access.

Then:

patala projection digest

before and after must match.
Events needed

At minimum:

EntityCreated
RawObservationRecorded
ArtifactRegistered

CandidateAssertionExtracted
AssertionRecorded
AssertionRetracted
AssertionSuperseded

ExternalIdentifierLinked
ExternalIdentifierUnlinked

IdentityProposed
EntityMerged
EntitySplit

RightsAssessmentRecorded

EditionLinked
WitnessLinked
ETextLinked
TranslationLinked

ReviewRecorded
AdjudicationRecorded

Do not create an event for every SQL implementation detail.

Create events for durable semantic state changes.
P0-05 — the ingestion pipeline does not actually preserve the observations it claims to preserve

This is surprisingly severe.

IngestionPipeline says:

SOURCE
→ RAW OBSERVATION
→ CANDIDATE ASSERTION
→ IDENTITY

But its runtime:

discover
fetch_metadata
normalize
resolve
insert Work/assertion/ext-ID

It never calls:

adapter.fetch_content()

and never invokes:

store.insert_artifact()
store.insert_raw_observation()

for the acquired source.

So the Bronze/Silver architecture mostly exists as tables/classes but is bypassed.
Replace pipeline with

DISCOVER
   ↓
FETCH EXACT BYTES
   ↓
Artifact
   ↓
RawObservation
   ↓
EXTRACT
   ↓
EntityCandidate
CandidateAssertion
   ↓
RESOLVE
   ↓
Canonical Assertion
Entity

Each arrow must create provenance.

The adapter must never pass ephemeral _meta dictionaries directly into canonical writes.
P0-06 — Archive.org isn’t preserving what it actually observed

ArchiveOrgAdapter.fetch_metadata() does not fetch and persist the original Archive.org response.

It constructs a new Python dictionary from the search result and assigns a fake-looking future artifact ID:

"payload_artifact_id": f"PTART_ia_{resource_id}"

but no corresponding immutable bytes are stored. fetch_content() returns None.

That’s not:

exact observed bytes.
Correct

Store:

search response artifact
item metadata response artifact
file manifest artifact
content artifact only when rights/policy allow

RawObservation points to actual Artifact IDs.

Then extract from those artifacts.
P0-07 — GRETIL has the right bytes but ingestion throws away the advantage

The GRETIL adapter actually reads the original TEI bytes and computes a digest. It can also return Artifact metadata.

But because the generic ingestion pipeline never calls/persists fetch_content, those bytes aren’t integrated into canonical evidence.

This is therefore an easy first vertical to make perfect.

Use GRETIL as your first hardened ingest.
P0-08 — resolver is effectively not operating across the corpus

Resolver stores its indexes entirely in process memory:

self._external_index
self._fingerprint_index
self._entities

But ingest.py calls:

self.resolver.resolve([candidate])

one candidate at a time.

This has several consequences.

R2–R5 generally expect multiple candidates and therefore won’t run.

The resolver isn’t hydrated from persisted OpenPāṭala entities.

External IDs written to Postgres don’t automatically enter the resolver’s in-memory index.

A process restart loses resolver state.

So the sophisticated R0→R5 resolver is largely disconnected from the actual corpus.
Replace

Resolver should query persisted candidate/entity indexes.

Implement:

ResolutionService

with:

R0 external-ID unique lookup
R1 curated crosswalk
R2 normalized bibliographic lookup
R3 candidate retrieval
R4 source-independence analysis
R5 adjudication

Candidate retrieval and candidate decision are separate.
P0-09 — entity typing is currently getting lost

This is a serious correctness error.

GRETIL emits:

candidate_type = "ETEXT"

but ingest.py, if unmatched, does:

w = Work(...)

for every candidate.

Thus an EText candidate can become a Work.

This collapses precisely the distinction the new ontology was supposed to fix.
Correct

Introduce typed entity creation:

EntityFactory.create(candidate_type, ...)

But even more importantly:

A GRETIL resource likely generates:

candidate Work
candidate EText
relation EText → representation/edition/work candidate

not merely one ETEXT candidate.

The ontology should represent:

GRETIL file
    =
EText

which transcribes/represents
    ↓
Work

P0-10 — assertion bundles can be attached to the wrong candidate

normalize() returns an entire ExtractionBundle.

ingest.py then attaches the whole bundle assertion list to every candidate:

for candidate in bundle["entity_candidates"]:
    ...
    "assertions": bundle["assertions"]

and later inserts all assertions against that resolved entity.

As soon as one resource produces:

Work candidate
Person candidate
Edition candidate

the author/person/title assertions can get copied onto each entity.

This will corrupt a richer ingest immediately.
Correct

CandidateAssertion already has:

subject_candidate_id

Use it.

After resolution:

candidate_id → canonical_entity_id

Then each assertion resolves its own subject independently.
P0-11 — external IDs can remain attached to candidate IDs

The current write does:

ext_id.get("entity_id", entity_id)

Adapters often explicitly set:

entity_id = candidate ID

so the fallback never fires.

That means your supposedly canonical external_identifiers may point at transient candidate IDs.
Binary invariant

Every row:

SELECT COUNT(*)
FROM external_identifiers e
LEFT JOIN entity_identity i ON i.id=e.entity_id
WHERE i.id IS NULL;

must return:

0

Always.
P0-12 —
entity_identity exists but isn’t actually the authority

The SQL has a good permanent layer:

entity_identity

But the active ingestion path inserts straight into:

works

without first creating the permanent entity identity.

So the supposedly disposable projection table is currently generating identity.

Reverse that:

EntityCreated event
     ↓
entity_identity
     ↓
work_current projection

Never:

works row
→ therefore entity exists

P0-13 — fresh DB migration is not reproducible

This one alone means I wouldn’t trust mass ingest yet.

store.insert_assertion() writes:

valid_from
valid_until
schema_uri

but the checked-in SQL does not define those assertion columns.

rebuild_from_events() writes:

works.schema_uri

but migrations don’t add it to works.

And:

insert_split(...)

uses undefined:

old_ids

rather than old_id.
Bigger problem

You have two different default DB URLs:

store.py:

postgresql://patala:patala@127.0.0.1:5432/openpatala

versus connection.py:

postgresql://localhost:5432/openpatala

So migration and runtime can point at different databases.
Fix

One:

patala.settings.DatabaseSettings

No DB defaults outside it.

And add migration history:

schema_migrations
migration_id
sha256
applied_at

Never silently edit an already-applied SQL file.
P0-14 — the schema registry is not append-only yet

The design is correct.

The implementation isn’t.

SchemaRegistry rewrites one:

schemas.json

dictionary.

More importantly, it keys entries by URI and its own demonstration registers:

v1
v1.1

using the same URI, overwriting the old record before freezing it.

Its verify_integrity() even says:

“In a real implementation, we’d recompute the digest…”

and doesn’t actually verify stored schema bytes.
Correct structure

schemas/
  epistemic/assertion/
    1.0.0/schema.json
    1.1.0/schema.json
    2.0.0/schema.json

URI:

https://schemas.patala.org/epistemic/assertion/1.0.0

Each immutable.

Registry itself records:

URI
digest
family
semver
supersedes
published event

Publication freezes automatically.
P0-15 — Merkle checkpointing is conceptually good, but not cryptographically mature

events.py builds Merkle leaves from a manually selected subset:

event_id
event_type
entity_ids
recorded_at
payload

using ordinary:

json.dumps(sort_keys=True)

rather than hashing the complete canonical EventEnvelope.

Therefore fields such as:

schema_uri
actor_id
observed_at
derivation_refs
run_id
payload_digest

can change without necessarily changing the Merkle leaf.
Correct

Leaf should be:

SHA-512(
    JCS(full immutable EventEnvelope)
)

excluding only fields explicitly defined as external/nonsemantic.

Checkpoint root then signs the batch.
P0-16 — “signatures” are currently just hashes

sign_checkpoint() explicitly does:

"signature": digest["value"]

and says the real key is future work.

That’s fine for a prototype.

It must not be described as cryptographic signing.
Fix

Either:

signatures = []

and call it unsigned,

or implement a real signer interface:

CheckpointSigner
  ├── Ed25519Signer
  └── future algorithm

Private key outside repo.

Verification uses public key.
P0-17 — snapshot digest currently has a self-reference semantic bug

create_snapshot_manifest() constructs a manifest where:

root_digest = {}
signatures = []

then hashes that representation and inserts the resulting digest into root_digest.

That’s not inherently invalid if formally specified as “digest of unsigned manifest without root_digest,” but it isn’t defined that way. Later signatures mutate the manifest further.

Define explicitly:

SnapshotBody
     ↓ JCS
body_digest

SnapshotEnvelope:
    body
    body_digest
    signatures

Never hash an ambiguously self-containing object.
P0-18 — the conformance suite needs to be deleted/replaced, not patched

The current 12/12 number should stop appearing in project status.

Some examples:

“Historical readability”:

assert works >= 0

“Migration determinism” doesn’t execute a migration.

“Fixity validation” merely verifies two different strings have different hashes.

“JCS cross-language” contains or True.

“Rights enforcement” only checks that columns exist.

“Projection rebuild” re-ingests internet sources.

This is precisely the anti-theatre failure mode you’ve been trying to eliminate.
New rule

A conformance test must actively violate an invariant and verify rejection.

Not merely check the corresponding class/table exists.
P0-19 — adapter validation is also theatre

adapters/validate.py labels something a “REAL API adapter” largely by regex-counting URLs in its source code.

A file containing:

https://...

is not evidence that the adapter works.
Replace with contract tests

Every adapter must pass frozen fixtures:

discover()
fetch_metadata()
fetch_content()
normalize()
rights
cursor
retry/failure

and a small optional live test.
P0-20 — current adapter-count/status docs are wrong

README claims adapters including:

IIIF
DTS
Darshana
Muktabodha

But the actual tree has no:

adapters/iiif
adapters/dts
adapters/darshana
adapters/muktabodha

Darshana actually lives in:

local_json/

and Muktabodha in:

local_zip/

This isn’t merely naming fussiness.

It means the runtime source registry isn’t yet cleanly representing its own integrations.
P0-21 — Darshana ingestion is ontologically wrong

This deserves its own finding.

The Darshana adapter currently treats each Darshana corpus verse as:

candidate_type = "WORK"

and builds a “title” from source + verse.

That will pollute OpenPāṭala with thousands of faux Works.

Darshana should enter as:

Darshana source record
      ↓

Passage/Occurrence candidate
Alignment candidate
ExternalAssertion candidate

linked to actual Work candidates.

Its graph edges stay:

ExternalAssertion

until evidence anchored/reviewed.

This is an important ontology torture test.
P0-22 — Muktabodha adapter currently has a real code bug and a rights problem

The local ZIP adapter references:

hashlib.sha256(...)

without importing hashlib.

The broad exception catches that and silently returns None, making content extraction appear merely unavailable.

That’s exactly why adapters need executable contract tests.

Also, Muktabodha content requires resource-specific rights evidence before computation/redistribution; do not let the existence of a local archive imply permission.

The adapter should default:

metadata = allowed if established
content_fetch = BLOCKED/UNKNOWN
compute = UNKNOWN
redistribute = UNKNOWN

until the exact acquisition/license evidence says otherwise.
P0-23 — API “working” is currently too generous

There is good API shape here, but several endpoints are placeholders.

Examples:

/surrogates actually selects from etexts.

/surrogates/{id} returns a note.

/etexts/{id}/content always says unavailable.

Passage occurrence/translation/alignment endpoints return empty placeholders.

Graph endpoint returns:

"Graph traversal not yet implemented"

provider health is hardcoded.

Provider rights is a hardcoded string.

So I would report:

implemented routes: yes
implemented semantics: partial

not “21/21 API complete.”
P0-24 —
/frontier/translations is currently false

It currently does essentially:

for every work:
    translation_state = "NONE_KNOWN"

while a separate legacy JSON says some works have translations.

This endpoint is supposed to become one of the core business/product surfaces.

It must be compiled from canonical SearchEvents + Translation entities.
P0-25 — current
/bundle state version isn’t a state version

It does:

"state_version": str(int(time.time()))

That’s just request time.

Use:

max committed canonical event cursor

plus:

projection digest

Example:

{
  "state_cursor": 918273,
  "state_digest": {
    "algorithm": "sha512",
    "canonicalization": "jcs-rfc8785",
    "value": "..."
  }
}

P0-26 — completeness is not trustworthy yet

CompletenessCompiler currently marks identity resolved when:

preferred_title exists

which is not identity resolution.

It checks assertions using:

a.get("state")

while your canonical assertion table calls it:

lifecycle

It determines source readiness using fields like:

artifact_id
quality_state

on Edition rows, although those concepts belong to ETexts.

It calls bibliography complete if there is a DOI/OpenAlex ID.

Alignment/evaluation are fixed to NONE.
Rewrite completeness as pure SQL/materialized projection

Inputs:

identity assertions/adjudications
ETexts + text quality
Translations + SearchEvents
alignments
Eval results
rights
bibliographic links

Each dimension needs an explicit compiler version.
P0-27 — the old RunRecorder should not enter the new canonical layer

run_recorder.py is copied from Sanskrit eval infrastructure and still claims:

run signature = hash(gold + code + config)

then stores one file by that signature.

We’ve already seen the problem with this architecture:

same inputs/config
+
stochastic model
=
different output

but same filename/spec signature.

Use:

ExperimentSpecID
≠
RunID
≠
OutputDigest

Again.

NRAH/control infrastructure can later own execution telemetry.

OpenPāṭala only needs immutable provenance references.
What is genuinely good and should survive

I would not flatten this review into “repo bad.”

A lot of the conceptual structure is now right.

Keep:

Artifacts → Observations → Assertions → Identity → Current Projection

Keep Work deliberately small.

Keep Translation separate from Edition.

Keep LogicalPassage separate from TextOccurrence.

Keep SearchEvent/negative knowledge.

Keep multi-dimensional authority.

Keep SourceLineage.

Keep DocumentSegment instead of verse-only ontology.

Keep the adapter interface:

discover
fetch_metadata
fetch_content
normalize
changes_since

Keep /bundle.

Keep /changes.

Keep source-completeness/frontier as the product center.

Keep PROV/Annotation/IIIF/DataCite etc. as adapters.

Don’t redesign the ontology again before fixing execution.
The specific dev plan from here
WIG-P0 — make the substrate real

Do no broad ingest during this phase.

Create a branch:

git checkout -b hardening/canonical-ledger

Implement in this dependency order:

P0.1 ID implementation
        ↓
P0.2 RFC8785 implementation
        ↓
P0.3 unified DB settings
        ↓
P0.4 fresh-schema migrations
        ↓
P0.5 single Postgres EventStore
        ↓
P0.6 event vocabulary + reducers
        ↓
P0.7 Artifact/RawObservation persistence
        ↓
P0.8 candidate persistence
        ↓
P0.9 persistent resolver
        ↓
P0.10 replay
        ↓
P0.11 real conformance suite

Do not touch advanced agent autonomy yet.
P0 canonical transaction pattern

This is what every ingest should eventually do.

Artifact bytes first:

FETCH
↓
calculate digests
↓
write immutable blob
↓
verify blob

Then one Postgres transaction:

INSERT Artifact metadata
INSERT RawObservation

INSERT Event(RawObservationRecorded)

INSERT ExtractionActivity
INSERT EntityCandidate
INSERT CandidateAssertion

resolve

INSERT canonical semantic event(s)

apply projection reducer(s)

COMMIT

If DB transaction fails, an orphaned content-addressed blob is harmless and can be garbage-collected later.

If the blob write fails, no observation may claim it exists.
Event architecture I’d freeze

DomainEvent {
    id: UUID

    cursor: DB-generated BIGINT

    type: EventType

    schema_uri

    actor_id

    entity_ids[]

    occurred_at?
    observed_at?
    recorded_at

    payload

    payload_digest

    derivation_refs[]

    run_id?
}

Events immutable at DB level.

Add Postgres trigger preventing:

UPDATE events
DELETE FROM events

for application role.

That is much stronger than promising append-only behavior in Python comments.
Binary event immutability gate

pytest -q tests/conformance/test_event_immutability.py

Test literally executes:

UPDATE events ...
DELETE FROM events ...

using normal application credentials.

Both must fail.
WIG-P1 — make one corpus vertical perfect

Do GRETIL first.

Not all 13 sources.

The acceptance path:

TEI bytes
→ Artifact
→ RawObservation
→ ExtractionActivity
→ WorkCandidate
→ ETextCandidate
→ CandidateAssertions
→ Resolution
→ Work + EText
→ Passage/DocumentSegment
→ completeness
→ API

For 100 GRETIL texts.

Then destroy Postgres projections.

Replay.

Everything returns identically.

Only then ingest all GRETIL.
P1 GRETIL binary gate

For 100 frozen test resources:

100 source artifacts
100 observations
0 missing payload artifacts
0 dangling assertions
0 dangling external IDs

all Work/EText relations trace to observations
all rights states explicit

destroy projections
replay

same Work IDs
same EText IDs
same assertions
same completeness
same /bundle state digest

Then:

pytest -q tests/integration/test_gretil_vertical.py

must pass twice on clean DBs and produce identical semantic snapshots.
WIG-P2 — persistent resolver

Do not make Resolver a mutable Python object holding the corpus.

Create persisted indexes:

external_identifier_index
normalized_title_index
bibliographic_signature_index
text_fingerprint_index

Resolution:

candidate
  ↓
retrieve candidates
  ↓
feature extraction
  ↓
ResolutionProposal
  ↓
policy
  ├── exact safe link
  ├── probable link
  └── review

No fuzzy automatic merge.
Resolver binary adversarial suite

Create ~500 frozen identity cases:

same Work / different spelling
same title / different Work
commentary vs root Work
edition vs Work
translation vs Work
recension
part/volume
different authors same title
mirrored catalogue
bad source metadata

Required:

R0 exact external ID:
precision = 1.000

R2/R3 fuzzy:
automatic merge count = 0

known false-merge adversaries:
0 auto merges

repeated ingest:
0 duplicate canonical entities

This becomes one of your most valuable permanent evals.
WIG-P3 — fix Darshana as the ontology torture test

Do not ingest its 2,321 records as 2,321 Works.

Build:

Darshana source record
    ↓
ExternalPassageCandidate

Darshana graph edge
    ↓
ExternalAssertion

Darshana source quotation
    ↓
TextAnchor

Try to resolve:

Darshana Work
→ existing OpenPāṭala Work

and:

Darshana passage
→ logical/occurrence passage

Binary gate

number of Works cannot increase by number of Darshana verses

every Darshana edge retains:
dataset version
source passage
evidence quote
extraction method

0 graph edge promoted to adjudicated truth

WIG-P4 — translation availability becomes real canonical state

Delete API dependence on:

data/translation-availability.json

That file should become a migration source only.

Canonical inputs:

Translation entities
TranslationOf assertions
SearchEvents
source/bibliography observations
rights

Projection:

TranslationAvailability

Then:

GET /v1/frontier/translations

becomes genuinely useful.
Binary translation-frontier gate

Construct:

Work A → no translation search run
Work B → searched, none found
Work C → partial translation
Work D → full translation
Work E → Pāṭala translation

API must distinguish:

UNKNOWN
NONE_KNOWN
PARTIAL
FULL_EXISTING
PATALA_MACHINE

UNKNOWN and NONE_KNOWN cannot be conflated.
WIG-P5 — rights become executable policy

At present rights exist structurally but the tests merely check columns.

Create:

RightsDecisionEngine

Input:

resource
provider
requested operation
rights assessments

Output:

ALLOW
DENY
REVIEW_REQUIRED

Operations:

DISCOVER
FETCH_METADATA
FETCH_CONTENT
COMPUTE
CREATE_DERIVATIVE
REDISTRIBUTE
TRAIN

Critical property test

A derived object can never have broader rights than its input unless a new independent RightsAssessment explicitly justifies it.
WIG-P6 — make
/bundle the real product

The bundle should eventually return:

identity
aliases
external IDs

current asserted metadata
conflicts

editions
witnesses
surrogates
ETexts
passages

translations
translation availability

scholarship

rights

provenance
source coverage

open conflicts

completeness

state_cursor
state_digest

No wall of every raw event by default.

Add expansion:

?include=evidence,history,observations

for agents.
WIG-P7 — snapshots and real cryptographic checkpoints

After canonical events work:

events
   ↓
contiguous cursor range
   ↓
JCS full Event envelopes
   ↓
Merkle root
   ↓
real signature

Snapshot:

ledger checkpoint
+
schema registry digest
+
projection files
+
file digests
+
state cursor

Export Parquet.

Then you have an actual reproducible OpenPāṭala release.
WIG-P8 — autonomy

Only once P0–P7 are green.

Then bring in NRAH.

OpenPāṭala deterministically emits gaps:

SOURCE_MISSING
TRANSLATION_UNKNOWN
IDENTITY_CONFLICT
RIGHTS_UNKNOWN
ETEXT_MISSING
ALIGNMENT_MISSING

These become:

TaskCandidate

NRAH schedules:

FIND_SOURCE
SEARCH_TRANSLATION
RESOLVE_IDENTITY
RESOLVE_RIGHTS
BUILD_ADAPTER

Agents do not directly mutate canonical state.

They produce:

Observation
CandidateAssertion
ResolutionProposal

Pāṭala does the promotion.
The new conformance suite

I would replace “12/12” with five suites.
CORE-CONFORMANCE

ID uniqueness
RFC UUID
RFC JCS
schema immutability
rights non-broadening
event append-only

REPLAY-CONFORMANCE

fresh DB
ingest frozen fixtures
snapshot semantic digest

destroy projections

network disabled

replay

digest identical

RESOLVER-CONFORMANCE

dedupe
merge
split
false merge
external ID
cross-source

ADAPTER-CONFORMANCE

raw bytes retained
metadata retained
rights explicit
assertions anchored
failure behavior
cursor behavior

API-CONFORMANCE

stable IDs
301 merge
409 split
cursor pagination
state cursor
bundle correctness
frontier correctness
rights enforcement

The one master binary command

Eventually this should be the only claim you need:

make verify-openpatala

It should provision an empty disposable Postgres instance, no dependence on your existing live DB.

Pseudo-sequence:

docker compose -f infra/test-postgres.yml up -d

patala db migrate

pytest -q tests/unit
pytest -q tests/conformance
pytest -q tests/integration

patala fixture ingest tests/fixtures/corpus-v1

patala snapshot semantic-digest \
  > /tmp/before.digest

patala projection destroy --yes

PATALA_NETWORK=disabled \
patala projection rebuild

patala snapshot semantic-digest \
  > /tmp/after.digest

diff /tmp/before.digest /tmp/after.digest

patala ledger checkpoint
patala ledger verify --all

patala integrity verify --artifacts
patala integrity verify --schemas

patala api smoke-test

Any non-zero exit:

NO-GO

No “mostly passed.”
The exact MASS-INGEST gate

I would forbid the autonomous crawler from exceeding perhaps a 1,000-record canary until every row here is green:

Gate
	

Required

Full 128-bit safe IDs
	

PASS

RFC JCS vectors
	

PASS

Clean DB migrations from repository only
	

PASS

One canonical event ledger
	

PASS

Events immutable at DB permission level
	

PASS

Raw bytes actually retained
	

PASS

RawObservation→Artifact referential integrity
	

PASS

CandidateAssertions persisted before resolution
	

PASS

Typed entities preserved
	

PASS

External IDs resolve only to canonical entities
	

PASS

Resolver survives process restart
	

PASS

Re-ingest same corpus produces zero duplicate entities
	

PASS

Ambiguous identity never auto-merges
	

PASS

Rights unknown blocks restricted operations
	

PASS

Projection rebuild requires zero network
	

PASS

Before/after replay semantic digest equal
	

PASS

Merge old ID resolves correctly
	

PASS

Split old ID remains explicitly ambiguous
	

PASS

Historical schema bytes immutable
	

PASS

Schema migrations actually tested
	

PASS

Artifact byte mutation detected
	

PASS

Merkle checkpoint includes full EventEnvelope
	

PASS

Real signature or explicitly unsigned
	

PASS

/bundle derived only from canonical state
	

PASS

Translation frontier distinguishes UNKNOWN/NONE
	

PASS

No placeholder endpoint reported as production
	

PASS

CI runs entire suite on clean infrastructure
	

PASS

Current verdict: NO-GO.
What I would not build next

Do not respond to this review by adding:

FoJin
20 more adapters
NRAH
DGM
Agent Lightning
Greek
education
more serializers
another ontology layer

yet.

You already have enough architecture.

The bottleneck has changed.

The next challenge is:

Can one GRETIL document pass through the exact architecture you claim, survive a complete projection deletion, and emerge identically from immutable history?

Then:

100 GRETIL documents.

Then all GRETIL.

Then PANDiT identity joins.

Then Darshana.

Then OpenAlex scholarship.

Then autonomous internet discovery.

That order is vastly more valuable than making the tree look even more sophisticated.
A more honest status after this audit

I would rewrite the status to:

OpenPāṭala 0.5

ARCHITECTURE:
strong prototype

ONTOLOGY:
usable

EVENT SOURCING:
designed, not yet authoritative

REPLAYABILITY:
not yet proven

ARTIFACT PRESERVATION:
not yet wired end-to-end

RESOLUTION:
prototype / nonpersistent

RIGHTS:
schema present, enforcement incomplete

API:
partial functional projection

ADAPTERS:
experimental; contract validation required

MASS INGEST:
BLOCKED

NEXT RELEASE TARGET:
0.6 — REPLAYABLE CORE

That’s not a downgrade of the project.

It’s exactly the kind of honesty that makes the next version much stronger.

The crucial thing is that the architectural ideas in wiggly are finally good enough that I would stop redesigning OpenPāṭala. The main work now is making those ideas true in execution: one ledger, exact source bytes, typed resolution, real schema immutability, deterministic replay, executable rights, and adversarial tests.

Once make verify-openpatala can destroy the entire read database, disable the internet, rebuild from preserved artifacts/events/schemas, and reproduce the same state digest, then I would open the floodgates and let the autonomous ingestion system ingest everything you can legitimately acquire.

That is the binary line between a clever prototype and infrastructure you could reasonably expect to still trust after ten million records.