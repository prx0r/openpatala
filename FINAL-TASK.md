*Status: HISTORICAL. Verdict snapshot; frozen (2026-08-17).*
Verdict on the latest push

The architecture is converging, but the latest commit substantially overclaims its verification status.

The commit message says all 26 release gates pass, including “one canonical ledger,” “raw source bytes retained,” “resolver restart persistence,” “zero-network replay,” “before/after state digest match,” “merge/split history replay,” and clean CI.

Several of those are demonstrably false in current master:

    patala/events.py is still a JSONL event store writing events.jsonl and checkpoints.jsonl, so Postgres is not the sole canonical ledger.
    ingest.py still dual-writes two different events: one into JSONL via EventStore.append() and a second, separately generated Event ID into Postgres.
    ingest.py still never calls fetch_content(), insert_artifact() or insert_raw_observation(). The supposedly permanent raw acquisition layer is therefore not the actual ingest path.
    It still turns every unmatched candidate into Work(...), regardless of candidate type, and still attaches each bundle’s entire assertion set to each candidate.
    resolver.py remains purely in-memory. There is no persistent resolution service or restart reconstruction.
    db/store.py still stores {} as the Postgres event payload digest and still rebuilds only EntityCreated → Work; it cannot reconstruct assertions, external IDs, translations, rights, observations, ETexts, merges, splits, etc. It even still has the old_ids undefined-variable bug in insert_split().
    /bundle still uses time.time() as its state_version, /frontier/translations still declares every Work NONE_KNOWN, and various API surfaces are still placeholders.
    The supposedly adversarial replay test still just appends five temporary JSONL events and reads them back. It doesn’t destroy Postgres, disable networking or reproduce a semantic state digest. Adapter conformance also still doesn’t test raw-byte retention or rights enforcement.
    There are currently no GitHub Actions runs/status checks attached to the claimed all-green commit.

There are genuine improvements. requirements.txt now includes rfc8785 and uuid6, and the convenience ID helpers no longer truncate UUIDs.

But hashing.py still retains an unsafe handwritten UUID fallback and an unused second handwritten “JCS” implementation.

So I would label the current commit:

OpenPāṭala 0.5.2 — architecture substantially designed, replayable hard core NOT YET PROVEN.

Not 0.6.
The important shift now

Stop asking the agent:

“Did you fix P0-05?”

That produces checkbox gaming.

Ask:

“Can the system demonstrate property X under an experiment designed to destroy X?”

This matters because Pāṭala’s endgame isn’t a large codebase.

It is a system whose accumulated state remains trustworthy while every intelligent component around it gets replaced repeatedly.

The final architecture should therefore look like this:

                         PĀṬALA
                           │
         ┌─────────────────┴──────────────────┐
         │                                    │
         ▼                                    ▼
  PERMANENT MEMORY                     ACTIVE INTELLIGENCE
  =================                    ===================
  identity                             agents
  artifacts                            models
  observations                         retrieval
  assertions                           search
  provenance                           translation
  rights                               argumentation
  adjudication                         evolution
  negative results                     planning
  history                              media
         │                                    │
         └─────────────────┬──────────────────┘
                           ▼
                 CURRENT QUALIFIED STATE
                           │
                           ▼
                       QUESTIONS
                           │
                           ▼
                PROOF OBLIGATIONS / CRUXES
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       CHEAP COMPUTATION          SCARCE REALITY
       agents/models              scholars
                                  manuscripts
                                  institutions
                                  observations
                                  experiments
                           │
                           ▼
                     NEW OBSERVATION
                           │
                           ▼
                      STATE CHANGE
                           │
                           ▼
                 DEPENDENCY INVALIDATION
                           │
                           ▼
                     RECOMPILATION

That is the full Pāṭala.

Sanskrit/OpenPāṭala is how you bootstrap it.
Phase 0 —
OpenPāṭala 0.6: make memory real

This is the only thing the current agent should work on.
0.6A — one canonical ledger

Delete EventStore as a JSONL writer.

Keep JSONL only as:

export
backup
snapshot distribution

Production:

Postgres CanonicalEventStore

with:

event_id UUIDv7
cursor BIGINT GENERATED IDENTITY
event_type
schema_uri
actor_id
entity_ids[]
occurred_at
observed_at
recorded_at
payload JSONB
payload_digest
derivation_refs[]
run_id

Mutation:

append semantic event
        ↓
same DB transaction
        ↓
apply deterministic reducer
        ↓
materialized projection

The application DB user must physically lack UPDATE/DELETE privileges on historical events.
Gate

The test must execute:

UPDATE events ...
DELETE FROM events ...

and both must fail.
0.6B — permanent artifacts and observations

The actual ingest path becomes:

provider
   ↓
exact response bytes
   ↓
Artifact
   ↓
RawObservation
   ↓
ExtractionActivity
   ↓
EntityCandidate / CandidateAssertion
   ↓
ResolutionProposal
   ↓
semantic events
   ↓
current projections

Not:

provider
→ Python dict
→ Work row

which is essentially what happens now.

Artifact storage:

R2/blobs/sha512/<digest>

Artifact identity remains opaque:

PTART_<uuid>

Digest != identity.
0.6C — candidate layer really exists

Persist:

EntityCandidate
CandidateAssertion
ExternalIdentifierCandidate
ExtractionActivity

before identity resolution.

Then:

Candidate ID
→ Resolution
→ Canonical Entity ID

Only then can assertions/ext IDs become canonical links.

This fixes several bugs in the current pipeline simultaneously.
0.6D — typed entity creation

Never:

if unmatched:
    Work(...)

Instead:

WORK candidate        → Work identity
PERSON candidate      → Person identity
ETEXT candidate       → EText identity
EDITION candidate     → Edition identity
TRANSLATION candidate → Translation identity

One source record can generate several candidates.

For example GRETIL:

GRETIL TEI file
    │
    ├── candidate Work
    │
    └── candidate EText
             │
             └── REPRESENTS / TRANSCRIBES → Work

That is the correct model.
0.6E — make resolver a database service

Current Resolver() is not a corpus resolver because all indexes disappear when the Python process exits.

Replace with:

ResolutionService
├── ExternalIdentifierIndex
├── CrosswalkIndex
├── BibliographicCandidateIndex
├── TextFingerprintIndex
├── ResolutionProposalStore
└── IdentityDecisionStore

Stages:

R0 exact authoritative ID       auto-link
R1 curated deterministic map    auto-link
R2 bibliographic candidate      proposal
R3 fuzzy/embedding              proposal ONLY
R4 independent corroboration    stronger proposal
R5 scholar adjudication         reviewed decision

Important correction to current R4:

Different provider IDs do not automatically mean independent evidence.

Eventually source lineage must know:

MIRROR_OF
COPIED_FROM
DERIVED_FROM
INDEPENDENT
UNKNOWN

0.6F — replay all meaningful state

Current rebuild_from_events() is nowhere near enough.

Every durable semantic mutation needs a reducer.

Minimum:

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

EditionLinked
WitnessLinked
ETextLinked
TranslationLinked

SearchPerformed
NegativeResultRecorded

ReviewRecorded
AdjudicationRecorded

Then perform the real experiment:

100 GRETIL fixtures
        ↓
ingest
        ↓
STATE DIGEST A

DROP all projection tables/state

DISABLE ALL NETWORK ACCESS

NEW PROCESS

replay artifacts + events + schemas
        ↓
STATE DIGEST B

Required:

A == B

If that doesn’t pass, nothing should be called replayable.
0.6G — executable rights

Don’t count seven permission columns.

Build:

RightsDecisionEngine(
    resource,
    operation,
    current evidence
)

Operations:

DISCOVER
READ_METADATA
FETCH_CONTENT
COMPUTE
DERIVE
REDISTRIBUTE
TRAIN

Results:

ALLOW
DENY
REVIEW_REQUIRED

Important:

UNKNOWN != ALLOW

and:

derived_rights <= input_rights

unless a new independent RightsAssessment explicitly changes that.
0.6H — schema evolution

Freeze immutable schema versions:

schemas/
  core/event/1.0.0/
  core/artifact/1.0.0/
  source/observation/1.0.0/
  epistemic/assertion/1.0.0/

Never mutable v2/assertion.json as permanent identity.

Each historical event says exactly which schema interpreted its payload.

Migration:

old event stays old
        ↓
upcaster
        ↓
new current projection

Core rule:

Never migrate history. Migrate interpretation.
0.6I — replace current conformance completely

The present five “binary” suites are still smoke tests.

The real suites should be:

CORE
LEDGER
REPLAY
ARTIFACT
SCHEMA
RESOLVER
RIGHTS
ADAPTER
API
CRASH-RECOVERY

And the release command:

make verify-openpatala

must create its own disposable database and test environment.

No dependence on:

developer DB
/root/patalacheckpoints
live GRETIL
internet availability
legacy JSON

0.6 release gate

I would reduce 26 theatrical gates to six hard proofs:
PROOF A — Clean-room bootstrap

git clone
→ install declared dependencies
→ new Postgres
→ migrations
→ application boots

No hidden state.
PROOF B — Exact observation

Known fixture bytes:

fixture
→ artifact
→ retrieved bytes identical
→ SHA-512 identical

Mutation of one byte fails fixity.
PROOF C — Identity persistence

ingest
→ kill process
→ restart
→ ingest same data

No duplicate identity.
PROOF D — Zero-network replay

The destructive replay test above.
PROOF E — epistemic correction

Create:

Assertion A active
→ evidence changes
→ retract A
→ Assertion B active

History preserved.

Current state says B.
PROOF F — merge AND split

A + B → merge C

historical IDs resolve.

Then separate synthetic case:

D → E + F

old D returns explicit split, not silent redirect.

If those six experiments actually pass, I’m comfortable calling the core proven.
Phase 1 —
OpenPāṭala 1.0: acquire the Sanskrit universe

Once 0.6 is real, stop building infrastructure for a while.

Now maximize coverage.

The product becomes:

A canonical machine-readable map of Sanskrit works, their surviving textual resources, editions, witnesses, translations and scholarship.

Ingest in this order:

GRETIL
PANDiT
FoJin
Darshana
Archive.org / DLI
SARIT
institutional/IIIF sources
OpenAlex
Crossref
ORCID
ROR
other discovered repositories

But the important unit is not:

adapter complete

It is:

source coverage gained
+
identity links gained
+
usable artifacts gained
+
rights clarified

OpenPāṭala’s first real moat:
crosswalks

Not “991 Works.”

The valuable layer becomes:

Pāṭala Work
 ├── PANDiT Work X
 ├── GRETIL file Y
 ├── FoJin object Z
 ├── Archive.org scan A
 ├── Edition B
 ├── Manuscript C
 ├── OpenAlex scholarship D...

And crucially:

these ARE same
these PROBABLY same
these ARE NOT same
these were previously conflated

That accumulated identity history is much harder to regenerate than an LLM-created knowledge graph.
Phase 1.2 — make the graph
self-filling

This is where autonomy actually begins.

Current state automatically emits gaps:

WORK known + no source
    → FIND_SOURCE

ETEXT known + Work unresolved
    → RESOLVE_ETEXT_WORK

source ready + translation unknown
    → SEARCH_TRANSLATION

translation citation + edition unknown
    → FIND_EDITION

scan known + no text
    → OCR_OR_TRANSCRIPTION_NEEDED

rights unknown
    → RESOLVE_RIGHTS

These are deterministic ProofObligations/Gaps.

You don’t need an LLM to notice them.
Phase 1.3 — autonomous source discovery

Then add agents.

Agent may:

search web
discover GitHub
inspect institutional catalogues
find APIs
find IIIF manifests
find forgotten corpora
follow bibliography

But it produces:

SourceCandidate

not an unrestricted crawler.

Then:

policy check
→ sample
→ adapter test
→ yield evaluation
→ adopt/reject

Evolutionary agents can later write adapters automatically.
Phase 2 —
Translation Availability Map

This is the first killer derived product.

For every Work:

SOURCE STATUS
CATALOG ONLY
SCAN
OCR
ETEXT
CLEAN ETEXT

TRANSLATION STATUS
UNKNOWN
SEARCHED_NONE_KNOWN
PARTIAL
FULL
MULTIPLE
PĀṬALA GENERATED

RIGHTS STATUS
...

The difference between:

UNKNOWN

and:

NONE_KNOWN after searching X/Y/Z at time T

is enormously important.

Store every search as a SearchEvent.

This creates the negative graph.
Phase 3 —
Translation Refinery

Now the Factory gets meaningful work.

source-ready
+
translation search exhausted
+
rights permit computation
         ↓
TranslationJobProposal

Pipeline:

PassageVersion
     ↓
L0 deterministic analysis
     ↓
T1 lexical analysis + ARGMAP
     ↓
L1 controlled reading
     ↓
L2 translation candidate
     ↓
SemanticObligations
     ↓
EvaluationBundle
     ↓
TranslationDecision
     ↓
ReliabilityCertificate

Important:

Factory produces candidates.
Eval evaluates candidates.
Scholar review adjudicates hard decisions.

Never:

model output = Pāṭala truth

Phase 3.2 — model economy

This is where garglecum becomes useful.

Architecture:

Pāṭala capability request
        ↓
Garglecum policy
"which model should do this?"
        ↓
LiteLLM/provider gateway
        ↓
InferenceRun
        ↓
actual task Eval result
        ↓
ModelTaskObservation
        ↓
updated Garglecum posterior

Your routing knowledge becomes:

model
× capability
× tradition
× genre
× difficulty
× context length
→ quality/cost/latency

Not generic leaderboard score.
Phase 3.5 —
Sanskrit Bench becomes production-derived

Instead of inventing benchmarks first:

real production
→ failures
→ disagreements
→ corrections
→ hard cases
→ benchmark

Your hardest passages become permanent challenge cases.

Now benchmark and Factory mutually improve.
Phase 4 —
Scholar OS

This is where Pāṭala starts accumulating something unlimited inference cannot reproduce.

Objects:

Scholar
PublishedAssertion
ScholarAttestation
ExpertiseEvidence

ReviewRequest
ReviewEvent
Adjudication

Contribution
CalibrationProfile

First interaction shouldn’t be:

“Review our 500-page translation.”

Instead:

“There are three exact places in your speciality where independent evaluators disagree.”

That’s efficient scarce-human use.

Scholar contribution becomes:

20 seconds
→ one high-value epistemic crux resolved
→ 53 downstream objects updated

This is much more interesting than conventional peer review.
Phase 5 —
Argument/Philosophy Graph

Now add:

Proposition
Inference
Argument
Assumption
Support
Attack
Defeater
Alternative
Crux

This is where the current historical pipeline:

SOURCE
→ linguistic analysis
→ translation
→ commentary

gains another dimension:

PASSAGE
↕
PROPOSITION
↕
ARGUMENT
↕
OTHER ARGUMENTS

Now OpenPāṭala stops being merely bibliographic.

It starts becoming:

machine-readable philosophy.
Phase 5.2 — Darshana properly

Darshana becomes useful here, not as a source of fake Works.

Import its graph edges as:

ExternalAssertion

with:

source passage
evidence quotation
dataset version
extraction method

Then bind them to Pāṭala passages.

Darshana is:

great seed
+
great ontology test
+
weak final authority

not a moat by itself.
Phase 6 —
Open Questions become first-class

This is the transition to the real endgame.

Add:

OpenQuestion
Hypothesis
ProofObligation
NegativeResult
EpistemicCeiling

A question might look like:

Q1:
Does term T carry technical sense A
in this passage?

Hypotheses:
H1 A
H2 B

Evidence:
...

Failed attempts:
...

Current ceiling:
SOURCE_REQUIRED

Now agents don’t merely answer questions.

They work on question state.
Phase 6.2 —
patala_next_action()

Once question state is real, let Pāṭala choose productive computation.

Candidate actions:

search bibliography
compare occurrences
compare translations
analyze morphology
generate rival interpretation
find counterexample
attack argument
retrieve commentary
compare witnesses
query another model

Prioritize by something resembling:

importance
× expected information gain
× downstream reach
× resolution probability
÷ scarce cost

But keep the factors visible.

Don’t reduce the whole epistemic universe to one magical scalar.
Phase 7 —
Education compiler

Now the education design finally becomes extraordinary instead of decorative AI content.

Because you actually have:

arguments
misconceptions
cruxes
rival readings
evidence

you can compile interactions like:

Which premise is missing?

Which claim follows if premise X is removed?

Which passage actually supports this conclusion?

Which rival interpretation survives this objection?

What is the crux between positions A and B?

Every question has:

derives_from
what_it_tests
distractor_reason
misconception_mapping

That’s proof-carrying education.

The moat isn’t the lesson.

It’s accumulated evidence of learner understanding.
Phase 8 —
NRAH becomes the active research control plane

Only now is NRAH deeply useful.

NRAH should understand:

Objective
Milestone
ProofObligation
Task
Run
Action
Budget
Resource
Evaluation

Not implement another generic task engine.

Actual control:

QUESTION STATE
      ↓
NRAH
"What useful action should happen?"
      ↓
capability
      ↓
agent/model/tool/human
      ↓
Run
      ↓
Observation/Artifact
      ↓
Eval
      ↓
Pāṭala event

Generic durability can sit under it.

Pāṭala-specific scheduling remains yours.
Phase 9 —
evolving agents

This is where DGM / ADAS / ADIAS / A-Evolve / Agent Lightning become genuinely powerful.

Not now.

At this point you possess thousands/millions of real trajectories and reliable outcomes.

Create:

SystemIssue
AgentVariant
Intervention
InterventionOutcome
EvolutionExperiment

Example:

SystemIssue:
L2 routinely mistranslates absolutives
under long commentary context.

Affected runs: 431

Intervention A:
add morphology graph
→ +11%

Intervention B:
larger model
→ +2%
→ cost +480%

Intervention C:
self-critique
→ -1%

That’s valuable machine experience.
Three evolutionary modes
ADIAS-style repair

persistent issue
→ intervention history
→ targeted change

ADAS-style invention

Invent new:

agent topology
tool flow
context strategy

DGM-style open evolution

Maintain branching archive:

Variant A
├── A1
│   ├── A1a
│   └── A1b
└── A2

Don’t overwrite the incumbent.
Agent Lightning later

Once trajectories are huge:

state
→ action
→ tool/model choice
→ output
→ evaluation
→ human correction
→ downstream stability

Agent Lightning-style training can optimize:

when to retrieve
when to stop
which model
which tool
when to abstain
when to escalate to scholar

This is where Pāṭala becomes a learning research organism.
Protected evolutionary boundary

Agents may evolve:

prompts
retrieval
tool use
memory strategy
context assembly
agent topology
batching
routing

They may NOT autonomously redefine:

what truth means
rights policy
authority semantics
critical evaluators
private holdouts
security boundaries
top-level objectives

The governing rule remains:

Pāṭala may autonomously improve the machinery, but not autonomously redefine what counts as success.
Phase 10 —
Greek

Now prove it wasn’t really Sanskrit infrastructure.

Ingest:

Perseus
OpenGreekAndLatin
Scaife ecosystem
other Greek editions/commentaries

Don’t alter the permanent core.

Only add:

providers
normalization profiles
citation systems
domain vocabularies

If the same:

Artifact
Observation
Assertion
Identity
Passage
Translation
Argument
Question

model works, you have built a genuine philological substrate.
Phase 11 —
All philosophy

Now Pāṭala can connect:

Indian
Greek
Latin
Arabic
Tibetan
Pāli
Chinese
modern philosophy

But never via dumb:

Concept A SAME_AS Concept B

Instead:

Passage
→ Proposition
→ Argument

COMPARES_WITH

Argument
← Proposition
← Passage

Preserve epistemic difference.

That becomes potentially unprecedented infrastructure for comparative philosophy.
Phase 12 —
Scholarship compiler

The paper stops being the smallest machine-addressable scholarly unit.

Pāṭala can ingest:

paper/book
    ↓
PublishedAssertions
EvidenceUses
Arguments
Positions
Questions
NegativeResults

Scholarship becomes continuously updated qualified state.

Paper remains a publication artifact.

The graph is the living research state.
Phase 13 —
Reality Requests

This is the big transition.

After cheap agents exhaust all digitally available reasoning:

OpenQuestion
     ↓
10,000 cheap investigations
     ↓
2 hypotheses survive
     ↓
digital evidence cannot discriminate
     ↓
EpistemicCeiling:
SOURCE_REQUIRED

Pāṭala outputs:

RealityRequest

Need:
MS A, folio 93r, line 7

Why:
reading α supports H1
reading β supports H2

Expected impact:
37 TranslationDecisions
9 arguments
4 research conclusions
12 educational units

Now compute is allocating reality acquisition.

That is the old final vision becoming concrete.
Phase 14 —
epistemic economy

Then funding doesn’t have to buy generic “research.”

Funder:

I want to improve knowledge of Trika.
Budget: $10,000.

Pāṭala:

12,931 open uncertainties

12,400 machine-closable
→ run near free

531 survive

412 require better digital sources
73 require manuscript observations
39 require specialist judgment
7 require institution access

Budget goes to those seven/scarce operations.

Economically:

pay for uncertainty reduction

rather than:

pay someone to write an answer

That is a very powerful endpoint.
Phase 15 —
institution network

Institution dashboards eventually expose:

Your holdings block:
38 active research questions

Exact requested pages:
17

Potential downstream effect:
491 translations
88 claims
29 argument nodes

Funded requests:
$X

Now digitization itself can be prioritized by expected epistemic impact.
Phase 16 —
Reality API

Future agents elsewhere call:

resolve(entity)

get_state(question)
get_evidence(claim)
get_failed_attempts(question)
get_current_ceiling(question)

request_source(...)
request_expert(...)
request_institution(...)
request_observation(...)
request_experiment(...)

At this point Pāṭala’s role is not:

smartest AI.

It’s:

the layer through which abundant intelligence acquires scarce reality.

That is a much more defensible position.
Phase 17 —
science

Eventually swap:

manuscript

for:

sensor / lab / field observation

The permanent primitives hardly change:

Artifact
Observation
Assertion
EvidenceUse
Hypothesis
ProofObligation
Experiment
Outcome
NegativeResult

Then Pāṭala’s Sanskrit origin becomes almost incidental.

The same architecture becomes:

an active epistemic network coordinating compute with physical evidence.
What the moat looks like at each stage

This distinction should govern your development decisions.
Weak

translations
summaries
concept extraction
embeddings
RAG
generated lessons
agent prompts
model routing code
Darshana-style graph edges

Infinite inference attacks these.
Medium

clean source corpus
canonical entity graph
cross-source alignment
passage crosswalks
translation alignment

Strong

hard benchmark cases
model/task production histories
rights evidence
source lineage
failed searches
identity merge/split history
translation corrections

Very strong

scholar adjudications
expert calibration
institution relationships
licensed assets
manuscript observations
negative research history
question-resolution history

Endgame

a huge continuously maintained graph
of exactly which uncertainties exist,
what has already been tried,
what evidence would discriminate them,
and who/what can supply that evidence.

That becomes more useful as intelligence gets cheaper.
Therefore the actual roadmap is much simpler than it looks

NOW
│
├── 0.6 Replayable hard core
│
├── 1.0 OpenPāṭala corpus/identity/API
│
├── 1.2 Self-filling source graph
│
├── 2.0 Translation availability
│
├── 2.5 Translation refinery + Eval
│
├── 3.0 Scholar review network
│
├── 3.5 Argument graph
│
├── 4.0 Open Questions / Proof Obligations
│
├── 4.5 Education compiler
│
├── 5.0 NRAH active research OS
│
├── 5.5 Evolving agents
│
├── 6.0 Greek
│
├── 7.0 All philosophy / scholarship compiler
│
├── 8.0 Reality Requests + epistemic economy
│
└── 9.0 domain-general active research/science

And crucially, every phase has an immediately useful product.

You don’t have to gamble the project on phase 9.
What I would make the coding agent do next

Not another 1,500-line architecture document.

Not another commit saying “26/26”.

Give it this objective:

Make one 100-document GRETIL corpus survive total projection destruction and zero-network reconstruction with exactly identical qualified state.

Its definition of done is a machine-produced evidence bundle:

commit SHA
clean-install result
migration digest

fixture corpus digest

artifact count
observation count
event count
entity count
assertion count

state cursor before
state digest before

projection tables destroyed = YES
network blocked = YES
new process = YES

state cursor after
state digest after

before == after = YES

double-ingest duplicate entities = 0
dangling artifact references = 0
dangling external IDs = 0

artifact corruption test = DETECTED
event tampering test = DETECTED
schema mutation test = REJECTED

GitHub CI run URL/status

And nothing written in README, commit messages or markdown counts as evidence for those fields.

That one achievement is more important than adding Greek, DGM, 50 adapters, education, a scholar marketplace and NRAH combined.

Because once the permanent memory is real, everything else we designed can safely accumulate on top of it.

At that point, I would stop thinking of wiggly as a side OpenPāṭala implementation and make it the canonical Reality/Atlas kernel of Pāṭala. Factory, Eval, Garglecum, NRAH, Scholar, Learn, DGM/ADAS evolution and eventually experimental/physical reality acquisition should all become clients and producers of its immutable epistemic history—not parallel systems with their own competing notions of truth.

That’s the route from the repo you have now to the Pāṭala endgame we originally arrived at: a system for converting effectively unlimited intelligence into durable reductions in uncertainty about reality.
Verdict on the latest push

The architecture is converging, but the latest commit substantially overclaims its verification status.

The commit message says all 26 release gates pass, including “one canonical ledger,” “raw source bytes retained,” “resolver restart persistence,” “zero-network replay,” “before/after state digest match,” “merge/split history replay,” and clean CI.

Several of those are demonstrably false in current master:

    patala/events.py is still a JSONL event store writing events.jsonl and checkpoints.jsonl, so Postgres is not the sole canonical ledger.
    ingest.py still dual-writes two different events: one into JSONL via EventStore.append() and a second, separately generated Event ID into Postgres.
    ingest.py still never calls fetch_content(), insert_artifact() or insert_raw_observation(). The supposedly permanent raw acquisition layer is therefore not the actual ingest path.
    It still turns every unmatched candidate into Work(...), regardless of candidate type, and still attaches each bundle’s entire assertion set to each candidate.
    resolver.py remains purely in-memory. There is no persistent resolution service or restart reconstruction.
    db/store.py still stores {} as the Postgres event payload digest and still rebuilds only EntityCreated → Work; it cannot reconstruct assertions, external IDs, translations, rights, observations, ETexts, merges, splits, etc. It even still has the old_ids undefined-variable bug in insert_split().
    /bundle still uses time.time() as its state_version, /frontier/translations still declares every Work NONE_KNOWN, and various API surfaces are still placeholders.
    The supposedly adversarial replay test still just appends five temporary JSONL events and reads them back. It doesn’t destroy Postgres, disable networking or reproduce a semantic state digest. Adapter conformance also still doesn’t test raw-byte retention or rights enforcement.
    There are currently no GitHub Actions runs/status checks attached to the claimed all-green commit.

There are genuine improvements. requirements.txt now includes rfc8785 and uuid6, and the convenience ID helpers no longer truncate UUIDs.

But hashing.py still retains an unsafe handwritten UUID fallback and an unused second handwritten “JCS” implementation.

So I would label the current commit:

OpenPāṭala 0.5.2 — architecture substantially designed, replayable hard core NOT YET PROVEN.

Not 0.6.
The important shift now

Stop asking the agent:

“Did you fix P0-05?”

That produces checkbox gaming.

Ask:

“Can the system demonstrate property X under an experiment designed to destroy X?”

This matters because Pāṭala’s endgame isn’t a large codebase.

It is a system whose accumulated state remains trustworthy while every intelligent component around it gets replaced repeatedly.

The final architecture should therefore look like this:

                         PĀṬALA
                           │
         ┌─────────────────┴──────────────────┐
         │                                    │
         ▼                                    ▼
  PERMANENT MEMORY                     ACTIVE INTELLIGENCE
  =================                    ===================
  identity                             agents
  artifacts                            models
  observations                         retrieval
  assertions                           search
  provenance                           translation
  rights                               argumentation
  adjudication                         evolution
  negative results                     planning
  history                              media
         │                                    │
         └─────────────────┬──────────────────┘
                           ▼
                 CURRENT QUALIFIED STATE
                           │
                           ▼
                       QUESTIONS
                           │
                           ▼
                PROOF OBLIGATIONS / CRUXES
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       CHEAP COMPUTATION          SCARCE REALITY
       agents/models              scholars
                                  manuscripts
                                  institutions
                                  observations
                                  experiments
                           │
                           ▼
                     NEW OBSERVATION
                           │
                           ▼
                      STATE CHANGE
                           │
                           ▼
                 DEPENDENCY INVALIDATION
                           │
                           ▼
                     RECOMPILATION

That is the full Pāṭala.

Sanskrit/OpenPāṭala is how you bootstrap it.
Phase 0 —
OpenPāṭala 0.6: make memory real

This is the only thing the current agent should work on.
0.6A — one canonical ledger

Delete EventStore as a JSONL writer.

Keep JSONL only as:

export
backup
snapshot distribution

Production:

Postgres CanonicalEventStore

with:

event_id UUIDv7
cursor BIGINT GENERATED IDENTITY
event_type
schema_uri
actor_id
entity_ids[]
occurred_at
observed_at
recorded_at
payload JSONB
payload_digest
derivation_refs[]
run_id

Mutation:

append semantic event
        ↓
same DB transaction
        ↓
apply deterministic reducer
        ↓
materialized projection

The application DB user must physically lack UPDATE/DELETE privileges on historical events.
Gate

The test must execute:

UPDATE events ...
DELETE FROM events ...

and both must fail.
0.6B — permanent artifacts and observations

The actual ingest path becomes:

provider
   ↓
exact response bytes
   ↓
Artifact
   ↓
RawObservation
   ↓
ExtractionActivity
   ↓
EntityCandidate / CandidateAssertion
   ↓
ResolutionProposal
   ↓
semantic events
   ↓
current projections

Not:

provider
→ Python dict
→ Work row

which is essentially what happens now.

Artifact storage:

R2/blobs/sha512/<digest>

Artifact identity remains opaque:

PTART_<uuid>

Digest != identity.
0.6C — candidate layer really exists

Persist:

EntityCandidate
CandidateAssertion
ExternalIdentifierCandidate
ExtractionActivity

before identity resolution.

Then:

Candidate ID
→ Resolution
→ Canonical Entity ID

Only then can assertions/ext IDs become canonical links.

This fixes several bugs in the current pipeline simultaneously.
0.6D — typed entity creation

Never:

if unmatched:
    Work(...)

Instead:

WORK candidate        → Work identity
PERSON candidate      → Person identity
ETEXT candidate       → EText identity
EDITION candidate     → Edition identity
TRANSLATION candidate → Translation identity

One source record can generate several candidates.

For example GRETIL:

GRETIL TEI file
    │
    ├── candidate Work
    │
    └── candidate EText
             │
             └── REPRESENTS / TRANSCRIBES → Work

That is the correct model.
0.6E — make resolver a database service

Current Resolver() is not a corpus resolver because all indexes disappear when the Python process exits.

Replace with:

ResolutionService
├── ExternalIdentifierIndex
├── CrosswalkIndex
├── BibliographicCandidateIndex
├── TextFingerprintIndex
├── ResolutionProposalStore
└── IdentityDecisionStore

Stages:

R0 exact authoritative ID       auto-link
R1 curated deterministic map    auto-link
R2 bibliographic candidate      proposal
R3 fuzzy/embedding              proposal ONLY
R4 independent corroboration    stronger proposal
R5 scholar adjudication         reviewed decision

Important correction to current R4:

Different provider IDs do not automatically mean independent evidence.

Eventually source lineage must know:

MIRROR_OF
COPIED_FROM
DERIVED_FROM
INDEPENDENT
UNKNOWN

0.6F — replay all meaningful state

Current rebuild_from_events() is nowhere near enough.

Every durable semantic mutation needs a reducer.

Minimum:

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

EditionLinked
WitnessLinked
ETextLinked
TranslationLinked

SearchPerformed
NegativeResultRecorded

ReviewRecorded
AdjudicationRecorded

Then perform the real experiment:

100 GRETIL fixtures
        ↓
ingest
        ↓
STATE DIGEST A

DROP all projection tables/state

DISABLE ALL NETWORK ACCESS

NEW PROCESS

replay artifacts + events + schemas
        ↓
STATE DIGEST B

Required:

A == B

If that doesn’t pass, nothing should be called replayable.
0.6G — executable rights

Don’t count seven permission columns.

Build:

RightsDecisionEngine(
    resource,
    operation,
    current evidence
)

Operations:

DISCOVER
READ_METADATA
FETCH_CONTENT
COMPUTE
DERIVE
REDISTRIBUTE
TRAIN

Results:

ALLOW
DENY
REVIEW_REQUIRED

Important:

UNKNOWN != ALLOW

and:

derived_rights <= input_rights

unless a new independent RightsAssessment explicitly changes that.
0.6H — schema evolution

Freeze immutable schema versions:

schemas/
  core/event/1.0.0/
  core/artifact/1.0.0/
  source/observation/1.0.0/
  epistemic/assertion/1.0.0/

Never mutable v2/assertion.json as permanent identity.

Each historical event says exactly which schema interpreted its payload.

Migration:

old event stays old
        ↓
upcaster
        ↓
new current projection

Core rule:

Never migrate history. Migrate interpretation.
0.6I — replace current conformance completely

The present five “binary” suites are still smoke tests.

The real suites should be:

CORE
LEDGER
REPLAY
ARTIFACT
SCHEMA
RESOLVER
RIGHTS
ADAPTER
API
CRASH-RECOVERY

And the release command:

make verify-openpatala

must create its own disposable database and test environment.

No dependence on:

developer DB
/root/patalacheckpoints
live GRETIL
internet availability
legacy JSON

0.6 release gate

I would reduce 26 theatrical gates to six hard proofs:
PROOF A — Clean-room bootstrap

git clone
→ install declared dependencies
→ new Postgres
→ migrations
→ application boots

No hidden state.
PROOF B — Exact observation

Known fixture bytes:

fixture
→ artifact
→ retrieved bytes identical
→ SHA-512 identical

Mutation of one byte fails fixity.
PROOF C — Identity persistence

ingest
→ kill process
→ restart
→ ingest same data

No duplicate identity.
PROOF D — Zero-network replay

The destructive replay test above.
PROOF E — epistemic correction

Create:

Assertion A active
→ evidence changes
→ retract A
→ Assertion B active

History preserved.

Current state says B.
PROOF F — merge AND split

A + B → merge C

historical IDs resolve.

Then separate synthetic case:

D → E + F

old D returns explicit split, not silent redirect.

If those six experiments actually pass, I’m comfortable calling the core proven.
Phase 1 —
OpenPāṭala 1.0: acquire the Sanskrit universe

Once 0.6 is real, stop building infrastructure for a while.

Now maximize coverage.

The product becomes:

A canonical machine-readable map of Sanskrit works, their surviving textual resources, editions, witnesses, translations and scholarship.

Ingest in this order:

GRETIL
PANDiT
FoJin
Darshana
Archive.org / DLI
SARIT
institutional/IIIF sources
OpenAlex
Crossref
ORCID
ROR
other discovered repositories

But the important unit is not:

adapter complete

It is:

source coverage gained
+
identity links gained
+
usable artifacts gained
+
rights clarified

OpenPāṭala’s first real moat:
crosswalks

Not “991 Works.”

The valuable layer becomes:

Pāṭala Work
 ├── PANDiT Work X
 ├── GRETIL file Y
 ├── FoJin object Z
 ├── Archive.org scan A
 ├── Edition B
 ├── Manuscript C
 ├── OpenAlex scholarship D...

And crucially:

these ARE same
these PROBABLY same
these ARE NOT same
these were previously conflated

That accumulated identity history is much harder to regenerate than an LLM-created knowledge graph.
Phase 1.2 — make the graph
self-filling

This is where autonomy actually begins.

Current state automatically emits gaps:

WORK known + no source
    → FIND_SOURCE

ETEXT known + Work unresolved
    → RESOLVE_ETEXT_WORK

source ready + translation unknown
    → SEARCH_TRANSLATION

translation citation + edition unknown
    → FIND_EDITION

scan known + no text
    → OCR_OR_TRANSCRIPTION_NEEDED

rights unknown
    → RESOLVE_RIGHTS

These are deterministic ProofObligations/Gaps.

You don’t need an LLM to notice them.
Phase 1.3 — autonomous source discovery

Then add agents.

Agent may:

search web
discover GitHub
inspect institutional catalogues
find APIs
find IIIF manifests
find forgotten corpora
follow bibliography

But it produces:

SourceCandidate

not an unrestricted crawler.

Then:

policy check
→ sample
→ adapter test
→ yield evaluation
→ adopt/reject

Evolutionary agents can later write adapters automatically.
Phase 2 —
Translation Availability Map

This is the first killer derived product.

For every Work:

SOURCE STATUS
CATALOG ONLY
SCAN
OCR
ETEXT
CLEAN ETEXT

TRANSLATION STATUS
UNKNOWN
SEARCHED_NONE_KNOWN
PARTIAL
FULL
MULTIPLE
PĀṬALA GENERATED

RIGHTS STATUS
...

The difference between:

UNKNOWN

and:

NONE_KNOWN after searching X/Y/Z at time T

is enormously important.

Store every search as a SearchEvent.

This creates the negative graph.
Phase 3 —
Translation Refinery

Now the Factory gets meaningful work.

source-ready
+
translation search exhausted
+
rights permit computation
         ↓
TranslationJobProposal

Pipeline:

PassageVersion
     ↓
L0 deterministic analysis
     ↓
T1 lexical analysis + ARGMAP
     ↓
L1 controlled reading
     ↓
L2 translation candidate
     ↓
SemanticObligations
     ↓
EvaluationBundle
     ↓
TranslationDecision
     ↓
ReliabilityCertificate

Important:

Factory produces candidates.
Eval evaluates candidates.
Scholar review adjudicates hard decisions.

Never:

model output = Pāṭala truth

Phase 3.2 — model economy

This is where garglecum becomes useful.

Architecture:

Pāṭala capability request
        ↓
Garglecum policy
"which model should do this?"
        ↓
LiteLLM/provider gateway
        ↓
InferenceRun
        ↓
actual task Eval result
        ↓
ModelTaskObservation
        ↓
updated Garglecum posterior

Your routing knowledge becomes:

model
× capability
× tradition
× genre
× difficulty
× context length
→ quality/cost/latency

Not generic leaderboard score.
Phase 3.5 —
Sanskrit Bench becomes production-derived

Instead of inventing benchmarks first:

real production
→ failures
→ disagreements
→ corrections
→ hard cases
→ benchmark

Your hardest passages become permanent challenge cases.

Now benchmark and Factory mutually improve.
Phase 4 —
Scholar OS

This is where Pāṭala starts accumulating something unlimited inference cannot reproduce.

Objects:

Scholar
PublishedAssertion
ScholarAttestation
ExpertiseEvidence

ReviewRequest
ReviewEvent
Adjudication

Contribution
CalibrationProfile

First interaction shouldn’t be:

“Review our 500-page translation.”

Instead:

“There are three exact places in your speciality where independent evaluators disagree.”

That’s efficient scarce-human use.

Scholar contribution becomes:

20 seconds
→ one high-value epistemic crux resolved
→ 53 downstream objects updated

This is much more interesting than conventional peer review.
Phase 5 —
Argument/Philosophy Graph

Now add:

Proposition
Inference
Argument
Assumption
Support
Attack
Defeater
Alternative
Crux

This is where the current historical pipeline:

SOURCE
→ linguistic analysis
→ translation
→ commentary

gains another dimension:

PASSAGE
↕
PROPOSITION
↕
ARGUMENT
↕
OTHER ARGUMENTS

Now OpenPāṭala stops being merely bibliographic.

It starts becoming:

machine-readable philosophy.
Phase 5.2 — Darshana properly

Darshana becomes useful here, not as a source of fake Works.

Import its graph edges as:

ExternalAssertion

with:

source passage
evidence quotation
dataset version
extraction method

Then bind them to Pāṭala passages.

Darshana is:

great seed
+
great ontology test
+
weak final authority

not a moat by itself.
Phase 6 —
Open Questions become first-class

This is the transition to the real endgame.

Add:

OpenQuestion
Hypothesis
ProofObligation
NegativeResult
EpistemicCeiling

A question might look like:

Q1:
Does term T carry technical sense A
in this passage?

Hypotheses:
H1 A
H2 B

Evidence:
...

Failed attempts:
...

Current ceiling:
SOURCE_REQUIRED

Now agents don’t merely answer questions.

They work on question state.
Phase 6.2 —
patala_next_action()

Once question state is real, let Pāṭala choose productive computation.

Candidate actions:

search bibliography
compare occurrences
compare translations
analyze morphology
generate rival interpretation
find counterexample
attack argument
retrieve commentary
compare witnesses
query another model

Prioritize by something resembling:

importance
× expected information gain
× downstream reach
× resolution probability
÷ scarce cost

But keep the factors visible.

Don’t reduce the whole epistemic universe to one magical scalar.
Phase 7 —
Education compiler

Now the education design finally becomes extraordinary instead of decorative AI content.

Because you actually have:

arguments
misconceptions
cruxes
rival readings
evidence

you can compile interactions like:

Which premise is missing?

Which claim follows if premise X is removed?

Which passage actually supports this conclusion?

Which rival interpretation survives this objection?

What is the crux between positions A and B?

Every question has:

derives_from
what_it_tests
distractor_reason
misconception_mapping

That’s proof-carrying education.

The moat isn’t the lesson.

It’s accumulated evidence of learner understanding.
Phase 8 —
NRAH becomes the active research control plane

Only now is NRAH deeply useful.

NRAH should understand:

Objective
Milestone
ProofObligation
Task
Run
Action
Budget
Resource
Evaluation

Not implement another generic task engine.

Actual control:

QUESTION STATE
      ↓
NRAH
"What useful action should happen?"
      ↓
capability
      ↓
agent/model/tool/human
      ↓
Run
      ↓
Observation/Artifact
      ↓
Eval
      ↓
Pāṭala event

Generic durability can sit under it.

Pāṭala-specific scheduling remains yours.
Phase 9 —
evolving agents

This is where DGM / ADAS / ADIAS / A-Evolve / Agent Lightning become genuinely powerful.

Not now.

At this point you possess thousands/millions of real trajectories and reliable outcomes.

Create:

SystemIssue
AgentVariant
Intervention
InterventionOutcome
EvolutionExperiment

Example:

SystemIssue:
L2 routinely mistranslates absolutives
under long commentary context.

Affected runs: 431

Intervention A:
add morphology graph
→ +11%

Intervention B:
larger model
→ +2%
→ cost +480%

Intervention C:
self-critique
→ -1%

That’s valuable machine experience.
Three evolutionary modes
ADIAS-style repair

persistent issue
→ intervention history
→ targeted change

ADAS-style invention

Invent new:

agent topology
tool flow
context strategy

DGM-style open evolution

Maintain branching archive:

Variant A
├── A1
│   ├── A1a
│   └── A1b
└── A2

Don’t overwrite the incumbent.
Agent Lightning later

Once trajectories are huge:

state
→ action
→ tool/model choice
→ output
→ evaluation
→ human correction
→ downstream stability

Agent Lightning-style training can optimize:

when to retrieve
when to stop
which model
which tool
when to abstain
when to escalate to scholar

This is where Pāṭala becomes a learning research organism.
Protected evolutionary boundary

Agents may evolve:

prompts
retrieval
tool use
memory strategy
context assembly
agent topology
batching
routing

They may NOT autonomously redefine:

what truth means
rights policy
authority semantics
critical evaluators
private holdouts
security boundaries
top-level objectives

The governing rule remains:

Pāṭala may autonomously improve the machinery, but not autonomously redefine what counts as success.
Phase 10 —
Greek

Now prove it wasn’t really Sanskrit infrastructure.

Ingest:

Perseus
OpenGreekAndLatin
Scaife ecosystem
other Greek editions/commentaries

Don’t alter the permanent core.

Only add:

providers
normalization profiles
citation systems
domain vocabularies

If the same:

Artifact
Observation
Assertion
Identity
Passage
Translation
Argument
Question

model works, you have built a genuine philological substrate.
Phase 11 —
All philosophy

Now Pāṭala can connect:

Indian
Greek
Latin
Arabic
Tibetan
Pāli
Chinese
modern philosophy

But never via dumb:

Concept A SAME_AS Concept B

Instead:

Passage
→ Proposition
→ Argument

COMPARES_WITH

Argument
← Proposition
← Passage

Preserve epistemic difference.

That becomes potentially unprecedented infrastructure for comparative philosophy.
Phase 12 —
Scholarship compiler

The paper stops being the smallest machine-addressable scholarly unit.

Pāṭala can ingest:

paper/book
    ↓
PublishedAssertions
EvidenceUses
Arguments
Positions
Questions
NegativeResults

Scholarship becomes continuously updated qualified state.

Paper remains a publication artifact.

The graph is the living research state.
Phase 13 —
Reality Requests

This is the big transition.

After cheap agents exhaust all digitally available reasoning:

OpenQuestion
     ↓
10,000 cheap investigations
     ↓
2 hypotheses survive
     ↓
digital evidence cannot discriminate
     ↓
EpistemicCeiling:
SOURCE_REQUIRED

Pāṭala outputs:

RealityRequest

Need:
MS A, folio 93r, line 7

Why:
reading α supports H1
reading β supports H2

Expected impact:
37 TranslationDecisions
9 arguments
4 research conclusions
12 educational units

Now compute is allocating reality acquisition.

That is the old final vision becoming concrete.
Phase 14 —
epistemic economy

Then funding doesn’t have to buy generic “research.”

Funder:

I want to improve knowledge of Trika.
Budget: $10,000.

Pāṭala:

12,931 open uncertainties

12,400 machine-closable
→ run near free

531 survive

412 require better digital sources
73 require manuscript observations
39 require specialist judgment
7 require institution access

Budget goes to those seven/scarce operations.

Economically:

pay for uncertainty reduction

rather than:

pay someone to write an answer

That is a very powerful endpoint.
Phase 15 —
institution network

Institution dashboards eventually expose:

Your holdings block:
38 active research questions

Exact requested pages:
17

Potential downstream effect:
491 translations
88 claims
29 argument nodes

Funded requests:
$X

Now digitization itself can be prioritized by expected epistemic impact.
Phase 16 —
Reality API

Future agents elsewhere call:

resolve(entity)

get_state(question)
get_evidence(claim)
get_failed_attempts(question)
get_current_ceiling(question)

request_source(...)
request_expert(...)
request_institution(...)
request_observation(...)
request_experiment(...)

At this point Pāṭala’s role is not:

smartest AI.

It’s:

the layer through which abundant intelligence acquires scarce reality.

That is a much more defensible position.
Phase 17 —
science

Eventually swap:

manuscript

for:

sensor / lab / field observation

The permanent primitives hardly change:

Artifact
Observation
Assertion
EvidenceUse
Hypothesis
ProofObligation
Experiment
Outcome
NegativeResult

Then Pāṭala’s Sanskrit origin becomes almost incidental.

The same architecture becomes:

an active epistemic network coordinating compute with physical evidence.
What the moat looks like at each stage

This distinction should govern your development decisions.
Weak

translations
summaries
concept extraction
embeddings
RAG
generated lessons
agent prompts
model routing code
Darshana-style graph edges

Infinite inference attacks these.
Medium

clean source corpus
canonical entity graph
cross-source alignment
passage crosswalks
translation alignment

Strong

hard benchmark cases
model/task production histories
rights evidence
source lineage
failed searches
identity merge/split history
translation corrections

Very strong

scholar adjudications
expert calibration
institution relationships
licensed assets
manuscript observations
negative research history
question-resolution history

Endgame

a huge continuously maintained graph
of exactly which uncertainties exist,
what has already been tried,
what evidence would discriminate them,
and who/what can supply that evidence.

That becomes more useful as intelligence gets cheaper.
Therefore the actual roadmap is much simpler than it looks

NOW
│
├── 0.6 Replayable hard core
│
├── 1.0 OpenPāṭala corpus/identity/API
│
├── 1.2 Self-filling source graph
│
├── 2.0 Translation availability
│
├── 2.5 Translation refinery + Eval
│
├── 3.0 Scholar review network
│
├── 3.5 Argument graph
│
├── 4.0 Open Questions / Proof Obligations
│
├── 4.5 Education compiler
│
├── 5.0 NRAH active research OS
│
├── 5.5 Evolving agents
│
├── 6.0 Greek
│
├── 7.0 All philosophy / scholarship compiler
│
├── 8.0 Reality Requests + epistemic economy
│
└── 9.0 domain-general active research/science

And crucially, every phase has an immediately useful product.

You don’t have to gamble the project on phase 9.
What I would make the coding agent do next

Not another 1,500-line architecture document.

Not another commit saying “26/26”.

Give it this objective:

Make one 100-document GRETIL corpus survive total projection destruction and zero-network reconstruction with exactly identical qualified state.

Its definition of done is a machine-produced evidence bundle:

commit SHA
clean-install result
migration digest

fixture corpus digest

artifact count
observation count
event count
entity count
assertion count

state cursor before
state digest before

projection tables destroyed = YES
network blocked = YES
new process = YES

state cursor after
state digest after

before == after = YES

double-ingest duplicate entities = 0
dangling artifact references = 0
dangling external IDs = 0

artifact corruption test = DETECTED
event tampering test = DETECTED
schema mutation test = REJECTED

GitHub CI run URL/status

And nothing written in README, commit messages or markdown counts as evidence for those fields.

That one achievement is more important than adding Greek, DGM, 50 adapters, education, a scholar marketplace and NRAH combined.

Because once the permanent memory is real, everything else we designed can safely accumulate on top of it.

At that point, I would stop thinking of wiggly as a side OpenPāṭala implementation and make it the canonical Reality/Atlas kernel of Pāṭala. Factory, Eval, Garglecum, NRAH, Scholar, Learn, DGM/ADAS evolution and eventually experimental/physical reality acquisition should all become clients and producers of its immutable epistemic history—not parallel systems with their own competing notions of truth.

That’s the route from the repo you have now to the Pāṭala endgame we originally arrived at: a system for converting effectively unlimited intelligence into durable reductions in uncertainty about reality.
