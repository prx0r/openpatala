*Status: PROPOSED. Refined phase map; proposal.*
No—the long-term phase map is mostly right, but the current DEV-PLAN is wrong in what it tells the next agent to do first.

The latest push did two useful things: it implemented the beginnings of WorkCoverage//frontier and researched seven relevant projects, then changed the next milestone to “integrate STAM → CollateX → OpenPecha → MMM.”

That sequence would drag you back into infrastructure-land.

The actual priority is:

Make OpenPāṭala’s canonical Work dossier + cross-source identity graph + query API excellent first. Then selectively plug these external mechanisms into the places where they save enormous work.

The repo research is good. The conclusion drawn from it is too eager.
Companion blueprint: build OpenPāṭala by stealing, not rebuilding

The architecture I would now freeze is:

                       OPENPĀṬALA
             canonical textual reality graph
                         │
         ┌───────────────┼────────────────┐
         │               │                │
         ▼               ▼                ▼
   INGEST/RESOLVE      READ API        COVERAGE
         │               │                │
         │               │                ▼
         │               │            GAPS / FRONTIER
         │               │                │
         │               │                ▼
         │               │          NRAH / discovery
         │               │
         ▼               ▼
   permanent state     users/agents
         │
         ├──────── Factory / minge-farm Eval
         ├──────── Scholar / epistemic engines
         ├──────── Manuscript/collation
         ├──────── Arguments/questions
         └──────── Education/media

And the rule for every other repository becomes:

Does it solve a problem OpenPāṭala genuinely needs?

YES
  ↓
Can it be used as a library/service?
  YES → integrate it
  NO  → steal mechanism/interface

NO
  ↓
do not import it because it is interesting

1. First: the latest push itself

There is one genuinely important improvement:

WorkCoverage is now separate and intended to replace WorkCompleteness.

That is correct product direction.

But its current implementation still says approximately:

identity = RESOLVED if preferred_title else UNRESOLVED
source = ETEXT if etext_count else ...
translation = EXISTING if translation_count else NONE_KNOWN
bibliography = COMPLETE if ext_id_count else NONE

Those are counts disguised as epistemology.

A title doesn’t prove identity.

No Translation rows doesn’t mean none is known.

One external ID doesn’t make bibliography complete.

So WorkCoverage should be considered:

correct interface, placeholder inference engine.

Keep it, rewrite how each dimension is derived.
2. There is now split-brain coverage logic

This needs fixing before further expansion.

The new /frontier calls work_coverage.compute_coverage().

But /bundle still calls the old:

CompletenessCompiler()

and exposes that as "completeness". It also still uses wall-clock time as state_version.

So you now have:

/bundle
   ↓
OLD CompletenessCompiler

/frontier
   ↓
NEW WorkCoverage

That is dangerous because the two APIs can disagree about the same Work.
Fix immediately

There should be one:

CoverageCompiler

and one persisted/read model:

work_coverage_current

Everything consumes it:

/works/{id}
/bundle
/frontier
/stats
search filters
NRAH
Factory eligibility

Delete CompletenessCompiler after migration.
3.
/frontier isn’t actually implemented yet

The new endpoint accepts:

filter=

but doesn’t apply the filter.

It also does:

for wid in work_ids[:limit]

before deciding whether the Work qualifies.

Meaning:

limit=20

doesn’t mean:

give me the best 20 matching frontier Works.

It means:

inspect the first 20 database rows and return whichever happen to qualify.

This must become SQL/query-engine driven.

For example:

GET /v1/frontier?
    filter=source:ETEXT,translation.eng:SEARCHED_NONE_KNOWN
    &sort=opportunity_score:desc
    &limit=100

This is a product feature, not an in-memory loop.
4.
/snapshots currently isn’t a snapshot service

It dynamically invents a new:

PTSNAP_...

every request and returns the current cursor/count.

That’s a status endpoint pretending to be a snapshot registry.

Actual snapshots need to be immutable artifacts:

snapshot_id
created_at
state_cursor
schema version
manifest digest

works.parquet
people.parquet
texts.parquet
translations.parquet
...

stored in R2/S3.

Then:

GET /v1/snapshots

lists historical releases.

That matters if you want researchers to build on you like they build on OpenAlex.
5. The biggest correction to
DEV-PLAN

Current order is:

1.1 STAM / CollateX / OpenPecha / MMM
1.2 self-filling graph
1.3 cross-source resolution

Invert it.

The correct order is:

1.1 GOLD WORK DOSSIERS
1.2 CROSS-SOURCE IDENTITY
1.3 OPENALEX-CLASS API
1.4 COVERAGE + FRONTIER
1.5 HIGH-YIELD SOURCE INGESTION
1.6 SELF-FILLING DISCOVERY
1.7 TEXT/PASSAGE ANNOTATION INTEROP
1.8 WITNESS COLLATION

Because autonomous discovery before strong identity resolution produces:

autonomous duplicate generation.

And CollateX before you have multiple resolved witnesses is machinery with nothing valuable to collate.
6. What to steal from
Garglecum

This is one of the most directly reusable repos.

garglecum already has the architecture:

many heterogeneous upstream sources
       ↓
normalization
       ↓
one canonical DB
       ↓
freshness / validation / canaries
       ↓
API
MCP
web

It exposes compact responses, ETags/caching, provider validation, measured-vs-estimated provenance, and agent-oriented MCP tools.

That is almost exactly the source-provider plane OpenPāṭala needs.
Steal directly

Create:

patala/providers/
    registry.py
    normalize.py
    refresh.py
    health.py
    canary.py
    coverage.py

Model:

ProviderStatus {
    provider_id

    last_discovery_success
    last_metadata_success
    last_content_success

    response_latency
    error_rate

    records_seen
    canonical_links_created
    new_entities_created

    metadata_yield
    artifact_yield
    duplicate_rate

    freshness
    rights_clarity

    last_checked
}

Then every provider gets:

HEALTHY
DEGRADED
STALE
BLOCKED
RETIRED

Steal Garglecum’s key distinction

Garglecum distinguishes:

measured
vs
estimated

for quality.

OpenPāṭala should similarly distinguish:

OBSERVED
INFERRED
ESTIMATED
ASSERTED
ADJUDICATED

Never collapse them.

This is immediately useful.

Priority: P0/P1.
7. What to steal from
ER / The Library

er has two mechanisms I would pull over now.

Its source graph already threads:

source → research object → essay → render → publication

and CONTROL tracks source-graph freshness/staleness.
Steal A: staleness

OpenPāṭala needs:

ProviderStaleness
WorkCoverageStaleness
TranslationSearchStaleness
IdentityResolutionStaleness
RightsReviewStaleness

Example:

{
  "dimension": "translation.eng",
  "state": "SEARCHED_NONE_KNOWN",
  "checked_at": "...",
  "search_protocol": "translation-search/4",
  "freshness": "STALE"
}

A claim of absence should expire.

That’s an excellent reuse of ER’s staleness idea.
Steal B: producer bridge

ER’s producer bridge turns one subsystem’s manifest into a downstream registered object.

OpenPāṭala needs exactly this for Pāṭala subsystems.

Define:

ContributionEnvelope

so:

Factory
Minge Eval
Scholar
Collation worker
Argument engine
Education engine

don’t write directly into OpenPāṭala internals.

They submit:

{
  "producer": "patala-factory",
  "producer_version": "...",

  "subject": "PTW_...",
  "contribution_type": "TRANSLATION_CANDIDATE",

  "inputs": [...],
  "artifacts": [...],
  "assertions": [...],
  "provenance": {...}
}

OpenPāṭala validates and admits it.

That becomes your universal inter-repo seam.

Priority: P1.
8. What to steal from
NRAH

NRAH already implements the valuable part:

vision
→ checkpoint DAG
→ objective/value-cost prioritization
→ deterministic gate
→ advance

Do not merge NRAH into OpenPāṭala.

OpenPāṭala produces tasks.

NRAH schedules them.

Boundary:

OpenPāṭala

WorkCoverage
    ↓
Gap
    ↓
TaskCandidate
    ↓
──────── API boundary ────────
    ↓
NRAH
    ↓
Task / Run
    ↓
agent
    ↓
ContributionEnvelope
    ↓
OpenPāṭala

Steal exactly

NRAH’s:

effect
gate
after
value
cost

becomes:

GapAction {
    action_type
    target_id

    expected_effect
    completion_gate

    dependencies[]

    estimated_value
    estimated_cost
}

This is basically the precursor of:

patala_next_action()

Do this only after WorkCoverage is trustworthy.

Priority: P1.6, not next week.
9. What to steal from
Minge Farm

This should not be rebuilt inside wiggly.

minge-farm already exposes a clean service boundary:

/audit
/translate
/bench

That is a good separation.

The current individual deterministic “proof” heuristics are much weaker than their names imply—for example source binding currently relies partly on candidate/source length ratio and coverage on relative token length.

So don’t import those heuristics as OpenPāṭala truth.

Steal:

TranslationCandidate
        ↓
Eval service
        ↓
EvaluationBundle
        ↓
qualified ContributionEnvelope

Not:

minge deterministic PASS
=
verified translation

Final boundary

OpenPāṭala
    ↓
source-ready untranslated Work

Factory
    ↓
TranslationCandidate

Minge/Eval
    ↓
EvaluationBundle

OpenPāṭala
    ↓
Translation entity
+ provenance
+ evaluation state

Priority: Phase 2.5.
10. What to steal from
Patalacheckpoints / Brownman

This is where the current DEV-PLAN risks massive duplication.

The canonical reference says the existing stack already has engines for:

translation proof
claim
argument
crux
comparison
research packet
evidence independence
tension finder
context bundle
passage
terminology

review queue
scholar identity
review workbench
scholar profile
review policy
scholar review
scholar publication

manuscript routing
manuscript ingest
collation

So don’t build those again in wiggly.
Wiggly owns

stable entities
sources
texts
passages
observations
assertions
provenance
rights
coverage

Patalacheckpoints owns

argument construction
claim checking
cruxes
scholar workflow
manuscript processing
translation evaluation

Then communicate with IDs.

This separation becomes:

OpenPāṭala = database of reality

Patalacheckpoints =
engines operating on reality

That is clean.
11. STAM:
yes, but not the way DEV-PLAN says

The research agent currently proposes:

STAM integration: TextAnchor → STAM annotation adapter.

That’s broadly right.

But do not adopt STAM as OpenPāṭala’s internal universal object model.

STAM deliberately models stand-off textual annotations; it supports annotations over spans, higher-order annotations over annotations, reverse indices and extensions for text alignment/transposition, but it explicitly isn’t intended as a generic knowledge graph. 

That boundary fits Pāṭala perfectly.
Use STAM for

TextOccurrence
TextAnchor
segmentation
lemma
morphology
translation alignment
commentary alignment
named entities
text reuse
annotation-over-annotation

Example mapping:

Pāṭala EText
      ↕
STAM TextResource

Pāṭala TextAnchor
      ↕
STAM TextSelector

Pāṭala linguistic annotation
      ↕
STAM Annotation

Pāṭala annotation-on-analysis
      ↕
STAM higher-order Annotation

Do NOT use STAM for

Work identity
Person identity
manuscript identity
rights
institutional authority
scholar adjudication
OpenQuestion
funding
RealityRequest

Those remain native Pāṭala.
Build

integrations/stam/
    export.py
    import.py
    mapping.py

Not:

OpenPāṭala database = STAM store

Priority: after passage/text layer is populated.
12. OpenPecha: steal the pattern more than the code

OpenPecha Toolkit V2 uses a very useful model:

Pecha
├── metadata
├── base/
│   └── base text
└── layers/
    ├── segmentation
    ├── alignment
    ├── pagination
    └── footnotes

and explicitly keeps base text separate from stand-off annotation layers.

This is excellent for Pāṭala.
Adopt conceptually

Artifact
  exact bytes

EText
  normalized/reference text

AnnotationLayer
  independent annotation namespace

Annotations
  immutable-ish derived overlays

For example:

GRETIL TEI
     ↓
Artifact

normalized Sanskrit
     ↓
EText

layers:
  segmentation
  morphology
  translation alignment
  ARGMAP anchors
  commentary

This protects the base text from annotation churn.

That’s the important steal.

OpenPecha also already supports alignments between root texts/commentaries/translations.

So later build an:

OpenPechaImporter
OpenPechaExporter

rather than redesigning Tibetan/Pāli interoperability if Pāṭala expands there.

Priority: P1.7.
13. CollateX: useful, but DEV-PLAN has it far too early

CollateX aligns two or more textual witnesses, identifies variants/transpositions and can output material useful for critical apparatus/stemmatical work. 

That’s exactly useful for:

Witness A
Witness B
Witness C
    ↓
CollationTask
    ↓
Alignment/VariantGraph

But right now you don’t yet possess a large, clean:

Work
→ multiple Witnesses
→ transcriptions
→ comparable passages

graph.

So integrating CollateX now creates a demo, not leverage.
Final use

Pāṭala Witness/EText occurrences
          ↓
Collation Worker
          ↓
CollationProposal {
    witnesses[]
    alignment
    variants[]
    transpositions[]
    algorithm
    parameters
}
          ↓
scholar/editor review
          ↓
accepted apparatus assertions

Crucially:

CollateX output is evidence/proposal, never an Edition automatically.

Also, its repository is GPL-3.0. 

So if licensing simplicity matters for OpenPāṭala’s own code, I would run it as an optional isolated worker/service rather than vendoring/copying CollateX internals into your canonical core.

Priority: after manuscript/witness corpus exists.
14. MMM: steal their pipeline doctrine, not their RDF stack

MMM’s conversion pipeline does something very relevant:

multiple independent source databases
          ↓
load independently
          ↓
source-specific transformation
          ↓
unified data model
          ↓
entity reconciliation
          ↓
validation
          ↓
shared graph

That’s basically OpenPāṭala.

But MMM implements it through RDF/SPARQL/Fuseki transformations.

You do not need to copy that infrastructure.

Steal:

source-specific transformation files
explicit mappings
reconciliation tables
manual-link overrides
validation
repeatable conversion

Build equivalent

adapters/pandit/
    mapping.yaml
    fixtures/
    adapter.py

adapters/gretil/
    mapping.yaml
    fixtures/
    adapter.py

reconciliation/
    deterministic_crosswalks.csv
    rejected_matches.csv
    overrides.csv

This is a very good pattern.

Priority: now, but as a coding convention—not a new subsystem.
15. Pairwise-light / KITAB: later, but strategically huge

The KITAB ecosystem exposes text-reuse relations across historical corpora. Its public Explore system lets users browse works and inspect text-reuse relationships. 

This should inspire a later Pāṭala service:

Passage A
Passage B

REUSES
PARAPHRASES
QUOTES
DERIVES_FROM
PARALLEL_TO

The detector outputs:

TextReuseCandidate

not immediately:

DERIVED_FROM truth

That could eventually become extremely valuable for:

    commentary dependence;
    textual borrowing;
    quotation/source tracing;
    source independence;
    detecting supposedly “independent” evidence that actually descends from one textual source.

This directly connects to Pāṭala’s evidence independence moat.

Priority: Phase 3+, not OpenPāṭala launch.
16. ATLAS / Perseus

Keep as a read/API reference, not a dependency.

The useful thing to steal is the concept that:

stable passage identity
+
annotations
+
alignments
+
linguistic data

can become a first-class API layer.

Your analogous architecture eventually:

GET /passages/{id}

GET /passages/{id}/occurrences
GET /passages/{id}/translations
GET /passages/{id}/annotations
GET /passages/{id}/arguments
GET /passages/{id}/evidence

But don’t build it until actual passages are populated.
17. Biblissima/MMM authority reconciliation

The research summary correctly notes Biblissima’s usefulness as a reconciliation/ontology reference.

Take the authority reconciliation pattern:

source person A
source person B
source person C

        ↓

Canonical Person

        ↓

links retain provenance

Do not simply flatten all names into one Person row.

This belongs in your upcoming cross-source resolution phase.
18. The correct new OpenPāṭala phase map

I would rewrite DEV-PLAN.md like this.
Phase 1.1 — Golden Product Vertical

Forget STAM temporarily.

Pick 100 representative Works:

major famous
minor obscure
multiple spellings
multiple authorship claims
with/without GRETIL
with/without translation
commentaries
root texts
bundled works

Each must produce an excellent:

/works/{id}
/bundle
/coverage

Exit condition:

100 useful human-readable + agent-readable dossiers

Phase 1.2 — Cross-source identity

Move current Phase 1.3 here.

Integrate:

GRETIL
PANDiT
Sanskritree
Archive
OpenAlex/Crossref

into the same 100 gold Works first.

Build:

ExactIdentifierMatcher
NormalizedTitleMatcher
AuthorTitleMatcher
TextFingerprintMatcher
CandidateRanker
ResolutionProposal

Hard output:

same
probably same
possibly same
not same
unresolved

Never only:

match/no match

Phase 1.3 — OpenAlex-class query layer

This is completely missing from current DEV-PLAN.

Implement:

search
filter
sort
select
group_by
cursor
autocomplete
external-ID lookup
batch resolve

The current api.py still uses in-memory substring search and exact title resolution.

Build this before any advanced annotation system.
Phase 1.4 — WorkCoverage + Frontier

Rewrite the new module into a genuine projection.

Each dimension gets:

state
confidence/authority
evidence_count
last_checked
search_protocol?
next_action

Translation example:

UNKNOWN
SEARCH_INCOMPLETE
SEARCHED_NONE_KNOWN
PARTIAL
FULL
MULTIPLE
PATALA_MACHINE
REVIEWED

Then:

/frontier

is generated from real SQL/projected state.

This becomes your unique product.
Phase 1.5 — provider expansion

Now steal Garglecum + MMM mechanisms.

Every provider gets:

adapter mapping
fixtures
health
canary
freshness
yield
rights policy
crosswalk rate

Goal isn’t:

25 adapters

Goal is:

median providers per Work ↑
coverage holes ↓

Phase 1.6 — self-filling discovery

Now connect NRAH.

Coverage
   ↓
Gap
   ↓
GapAction
   ↓
NRAH
   ↓
Discovery / resolve / ingest

Not before.
Phase 1.7 — annotation interoperability

Now use:

STAM
OpenPecha pattern
ATLAS patterns
Web Annotation

for:

passages
linguistics
alignments
annotations

No new permanent identity model.
Phase 1.8 — manuscript/witness intelligence

Now connect existing Pāṭala manuscript engines plus optional CollateX.

Witness
Surrogate
Transcription
       ↓
Collation service
       ↓
VariantGraph
       ↓
scholar adjudication

Phase 2 — Translation Availability

Then the current plan resumes:

SearchEvent
negative graph
translation frontier

But connect er staleness:

SEARCHED_NONE_KNOWN

has a freshness horizon.

This is important.
Phase 2.5 — Factory + Eval

Reuse:

patalacheckpoints Factory
minge-farm Eval
garglecum model routing

Do not port their implementation into OpenPāṭala.

They are clients.
Phase 3 — Scholar network

Reuse the scholar engines already documented in brownman/patalacheckpoints.

OpenPāṭala only adds:

Scholar identity
ContributionEnvelope
ReviewEvent
Attestation

as durable graph objects.
Phase 3.5+ — argument / question / education

Again:

Patalacheckpoints engines
     ↓
ContributionEnvelope
     ↓
OpenPāṭala permanent graph

Don’t duplicate.
19. The universal inter-repo contract

This is probably the most valuable new thing to build.

Every Pāṭala subsystem should speak:

Pāṭala Contribution Protocol

Something like:

{
  "schema": "patala.contribution/1",

  "producer": {
    "system": "minge-eval",
    "version": "...",
    "run_id": "..."
  },

  "subject_ids": [
    "PTW_...",
    "PTET_..."
  ],

  "type": "EVALUATION",

  "inputs": [
    {
      "entity_id": "...",
      "version": "...",
      "digest": "..."
    }
  ],

  "artifacts": [],

  "claims": [],

  "relations": [],

  "metrics": {},

  "provenance": {},

  "requested_action": "REGISTER"
}

Then the ecosystem becomes:

                      OPENPĀṬALA
                           ▲
                           │
                   ContributionEnvelope
                           │
       ┌──────────┬────────┼─────────┬─────────┐
       │          │        │         │         │
   Factory      Eval    Scholar   Collation   Args
       │          │        │         │         │
       └──────────┴────────┴─────────┴─────────┘

This is much better than merging repositories.
20. The universal outward task contract

Other direction:

{
  "schema": "patala.task/1",

  "task_id": "...",

  "type": "SEARCH_TRANSLATION",

  "target_ids": ["PTW_..."],

  "context": {...},

  "completion_gate": {...},

  "priority": {
    "value": 0.9,
    "cost": 0.2
  }
}

OpenPāṭala emits it.

NRAH routes it.

That’s enough coupling.
21. Which repos should physically become dependencies?

Very few.
In OpenPāṭala runtime

Potentially:

rfc8785
UUID7 implementation
FastAPI/Postgres stack
STAM Python/Rust bindings later
generic protocol clients

Separate services

CollateX
minge-farm
Factory
NRAH
Garglecum
Scholar engines

Patterns only

MMM
OpenPecha architecture
ATLAS
KITAB
Biblissima

This is important.

“Steal” mostly means steal interfaces and invariants, not copy repositories into a monolith.
22. What I would delete/stop from current
wiggly

Stop spending time on:

7 serializers being a headline metric
34 tables being a headline metric
number of adapters
number of schemas
number of tests
cloned research repos

None are product metrics.

And don’t implement:

C2PA
RO-Crate
CIDOC CRM
STAM
CollateX

simply because serializers/files already exist.

They become useful when a real client/use case requires them.
23. New success dashboard

OpenPāṭala development should show:

CANONICAL WORKS
24,802

SOURCE RECORDS
81,441

CROSS-SOURCE LINKS
62,310

MEAN PROVIDERS / WORK
3.28

WORKS WITH ≥2 PROVIDERS
68%

WORKS WITH USABLE TEXT
42%

WORKS WITH MANUSCRIPT DATA
17%

TRANSLATION STATUS CHECKED
31%

WORKS WITH SCHOLARSHIP
57%

IDENTITY CONFLICTS
1,218

RESOLVED THIS WEEK
74

SOURCE HEALTH
18 healthy
2 degraded
1 stale

COVERAGE FRONTIER
source gaps       8,411
translation gaps 11,921
witness gaps      17,219
identity gaps       823

That’s an OpenAlex competitor dashboard.
24. The strongest combined architecture from everything you’ve built

This is the companion to the previous roadmap:

                           OPENPĀṬALA
                    ─────────────────────
                    IDENTITY + REALITY API
                              │
             ┌────────────────┼─────────────────┐
             │                │                 │
             ▼                ▼                 ▼
       Provider Plane     Text Plane       Coverage Plane
       --------------     ----------       --------------
       Garglecum-like     OpenPecha        WorkCoverage
       registry           base/layers      ER staleness
       refresh            STAM adapters    negative graph
       canary
       source utility
             │                │                 │
             └────────────────┼─────────────────┘
                              ▼
                       Canonical Work Graph
                              │
                 ┌────────────┼─────────────┐
                 │            │             │
                 ▼            ▼             ▼
             Factory       Scholar       Research
                 │            │             │
                 ▼            ▼             ▼
              Minge       existing       argument/crux
               Eval       scholar        Pāṭala engines
                 │        engines            │
                 └────────────┼──────────────┘
                              │
                    Contribution Protocol
                              │
                              ▼
                         OpenPāṭala
                              │
                              ▼
                        Coverage changes
                              │
                              ▼
                             NRAH
                              │
                       value/cost scheduler
                              │
                  ┌───────────┼───────────┐
                  ▼           ▼           ▼
              discovery    agents      humans

Now almost every repo you built has one job.

That’s what was missing.
25. Exact immediate build order

I would give the next agent only these tasks:
OP-M1 — consolidate product state

Delete old Completeness usage.

Make:

WorkCoverage

the single canonical read projection.

Wire:

/bundle
/work
/frontier
/stats

to it.
OP-M2 — create 100 golden Work dossiers

Pick representative Works.

For every one, manually/algorithmically reconcile:

GRETIL
PANDiT
Archive
bibliography

as available.

This becomes resolver gold.
OP-M3 — cross-source resolver

Before adding more sources.
OP-M4 — query AST/API

Implement:

search
filter
sort
select
group_by
cursor
autocomplete
resolve/batch

OP-M5 — Garglecum-style provider registry

Add:

refresh
health
canary
staleness
source utility

OP-M6 — real frontier

SQL/materialized work_coverage_current.

No Python loop through Works.
OP-M7 — ContributionEnvelope

Make this the boundary to all other Pāṭala repositories.
OP-M8 — TaskEnvelope

Make this the boundary to NRAH.
OP-M9 — bulk source expansion

Now scale the corpus.
OP-M10 — STAM/OpenPecha adapter

Only after actual passage data needs it.
OP-M11 — CollateX worker

Only after actual multi-witness cases exist.
Final assessment of the current DEV-PLAN

Vision: 9/10.

Research choices: 9/10.

Mechanism discoveries: excellent.

Immediate sequencing: 5/10.

The core mistake is treating:

“we found a useful repo”

as:

“we should integrate it next.”

Instead the question should always be:

What is preventing OpenPāṭala from being a useful public API today, and does an existing mechanism eliminate that bottleneck?

Right now the bottlenecks are:

cross-source identity
high-quality Work dossiers
query ergonomics
real coverage semantics
source freshness
API distribution

not textual collation or stand-off annotation.

The repo discoveries are still valuable—you’ve effectively assembled an excellent library of future components. But use them just in time:

Garglecum → now
MMM transformation discipline → now
ER staleness → now
NRAH → once gaps are real
STAM/OpenPecha → once passages are real
CollateX → once witnesses are real
KITAB reuse → once corpus size is large
Minge → once translation frontier is real
Scholar/argument engines → once users begin correcting state

That path keeps the whole Pāṭala endgame intact while finally making OpenPāṭala itself into something developers can adopt.
