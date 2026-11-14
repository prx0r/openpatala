*Status: PROPOSED. Long-term phase plan; proposal, not built state.*


Yes. The conversation drifted from “build the OpenAlex of Sanskrit and premodern texts” into spending most of our attention on whether an event table can survive database destruction.

That durability work matters, but it is not the product.

The clean reset is:

OpenPāṭala is the public data infrastructure. Pāṭala is everything intelligent that grows on top of it.

OpenPāṭala should become the canonical open graph/API answering:

What is this work? What other databases know it? Who wrote it? What witnesses, scans, editions, e-texts, translations and scholarship exist? Where can I access them? What is uncertain or disputed? What is still missing?

That is the product you can take to market.

And the bigger Pāṭala vision then plugs into it:

                    OPENPĀṬALA
        canonical reality/data infrastructure
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
       ▼                 ▼                  ▼
   FACTORY             SCHOLAR          EDUCATION
 translation         research OS       proof learning
 evaluation          arguments
 commentary          questions
       │                 │
       └─────────────────┼──────────────────┘
                         ▼
                PĀṬALA RESEARCH NETWORK
                         │
                    OpenQuestions
                         │
                  ProofObligations
                         │
              Agents exhaust inference
                         │
                 RealityRequests
                         │
       scholars / manuscripts / institutions
                         │
                    new evidence
                         │
                         ▼
                    OpenPāṭala

That is the full vision.
1. What
wiggly can actually do today

Ignoring README claims and judging the code itself, it is currently a prototype vertical metadata graph with the beginnings of an OpenAlex-style API.

It can already expose:

GET /v1/works
GET /v1/works/{id}
GET /v1/works/{id}/assertions
GET /v1/bundle/{id}
GET /v1/resolve?q=
GET /v1/search?q=
GET /v1/changes
GET /v1/people
GET /v1/institutions
GET /v1/editions
GET /v1/witnesses
GET /v1/etexts
...

The bundle endpoint already attempts to assemble a Work dossier containing editions, witnesses, e-texts, translations, passages, assertions, provenance and completeness. That is much closer to the real product than the replay machinery we’ve been obsessing about.

There is also an extremely important primitive hiding in plain sight: WorkCompleteness.

It already models:

identity
source
translation
alignment
evaluation
bibliography

and the idea that OpenPāṭala should become a map of holes.

That is potentially one of the core differentiators of the whole company/project.

The current ingestion system can discover records through adapters, normalize metadata into candidate assertions, run rudimentary identity matching, and populate Works/assertions/external IDs. But it currently collapses too much into Work records and doesn’t yet make Artifact → Observation → Candidate → Entity the universal ingest flow.

The repository also contains the schema vocabulary for a much richer graph—witnesses, editions, e-texts, translations, source providers, observations, candidates, identity assertions, etc.

So you are not at zero.

You have roughly:

the skeleton of OpenPāṭala, populated with some data, but not yet the actual OpenPāṭala product.
2. What it absolutely cannot do yet

If I type:

Tantrāloka

the system should eventually answer something like:

Tantrāloka
Pāṭala ID: ...

Attributed author
  Abhinavagupta
  confidence: high
  evidence: ...

Alternative titles
  ...
  
External identities
  PANDiT: ...
  GRETIL: ...
  Muktabodha: ...
  WorldCat: ...
  Archive.org: ...
  etc.

Works structure
  37 āhnikas
  ...

Manuscripts
  31 known witnesses
  18 digitized
  7 IIIF-accessible
  ...

Editions
  4

E-texts
  GRETIL ...
  Muktabodha ...
  edition relationship ...
  quality ...

Translations
  English: PARTIAL
  German: ...
  Hindi: ...
  
Scholarship
  83 relevant publications
  ...

Current best machine-readable source
  ...

Rights
  READ: yes
  COMPUTE: yes
  REDISTRIBUTE: no

OpenPāṭala coverage
  Identity        ██████████
  Sources         ████████░░
  Manuscripts     ██████░░░░
  Editions        █████████░
  Translation     ████░░░░░░
  Scholarship     ███████░░░

Missing
  English translation of āhnikas X–Y
  4 manuscript identities unresolved
  edition X has no digital surrogate

Today wiggly cannot reliably produce that.

Its /search is essentially substring matching over titles, /resolve is exact-title matching, and /frontier/translations currently labels every Work NONE_KNOWN.

CompletenessCompiler currently makes simplistic inferences—for example treating the presence of DOI/OpenAlex identifiers as enough to label bibliography COMPLETE.

That is what should change next.
3. What “rival OpenAlex” should mean

Do not try to rival OpenAlex at its own horizontal game.

OpenAlex currently describes a graph of hundreds of millions of scholarly entities and billions of relationships. It aggregates records from Crossref, ORCID, ROR, PubMed, repositories and web sources, disambiguates those records, and exposes the resulting graph through Web, REST API and bulk snapshots. 

Its product lesson is more important than its scale.

OpenAlex has extremely predictable developer ergonomics:

/{entity}
/{entity}/{id}

?search=
?filter=
?sort=
?select=
?group_by=
?sample=
?page=
?cursor=

plus autocomplete, external-ID resolution, snapshots and changefiles. 

Copy that discipline.

But OpenPāṭala’s graph is different.

OpenAlex:

Publication
  ↕
Author
  ↕
Institution
  ↕
Source
  ↕
Citation

OpenPāṭala:

                     WORK
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
    PERSON         EDITION        WITNESS
                      │              │
                      ▼              ▼
                    ETEXT        SURROGATE
                      │              │
                      └──────┬───────┘
                             ▼
                          PASSAGE
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
           TRANSLATION   SCHOLARSHIP   ASSERTION
                │                         │
                ▼                         ▼
           ALIGNMENT                   EVIDENCE

That is substantially richer for textual scholarship.
4. The actual OpenPāṭala positioning

I would make the public description brutally simple:

OpenPāṭala is the open graph of premodern texts.

Secondary sentence:

Search works across fragmented catalogues and discover their manuscripts, editions, digital texts, translations and scholarship through one API.

Not:

epistemic event-sourced autonomous scholarly state machine.

That can be true internally.

Nobody should need to understand it to use your API.
5. The canonical entity model

I would freeze the public domain model around about ten first-class entities.

Work
Person
Institution
Witness
Surrogate
Edition
Text
Translation
ScholarlyWork
Passage

Then infrastructure entities remain accessible through specialist endpoints:

Provider
Artifact
Observation
Assertion
Evidence
IdentityDecision
RightsAssessment
Activity

The critical distinction:

Work ≠ Edition ≠ Witness ≠ Text ≠ Translation

This is where OpenPāṭala can crush generic bibliographic systems.

For example:

Abhinavagupta's Work
        │
        ├─ Witness A
        │    └─ IIIF surrogate
        │
        ├─ Witness B
        │
        ├─ Edition 1918
        │    └─ digitized scan
        │
        ├─ Edition 1964
        │    └─ GRETIL e-text
        │
        ├─ English translation X
        │
        └─ 73 scholarly publications

6. One important correction to our previous schema obsession

Do not expose the assertion/event model as the normal API representation.

Permanent internal truth can absolutely be:

observations
+ events
+ assertions
+ provenance

But developers want:

{
  "id": "...",
  "display_name": "Tantrāloka",
  "authors": [...],
  "languages": ["san"],
  "texts_count": 4,
  "witnesses_count": 31,
  "translations_count": 3
}

OpenAlex does the same conceptual thing: consumers interact primarily with convenient entity records, not its ingestion internals. Its API and snapshot use consistent entity-shaped records. 

Therefore:

Permanent epistemic model
        ↓
Projection compiler
        ↓
Beautiful developer records

7. The canonical
Work API record

I would make /works/{id} roughly:

{
  "id": "https://patala.org/e/019...",
  "type": "work",

  "display_name": "Tantrāloka",

  "titles": [
    {
      "text": "Tantrāloka",
      "language": "san",
      "script": "Latn",
      "type": "preferred"
    }
  ],

  "authorships": [
    {
      "person": {
        "id": "...",
        "display_name": "Abhinavagupta"
      },
      "status": "supported"
    }
  ],

  "languages": ["san"],

  "date": {
    "earliest": 975,
    "latest": 1025,
    "certainty": "approximate"
  },

  "traditions": [
    {"id": "...", "display_name": "Trika"}
  ],

  "external_ids": {
    "pandit": "...",
    "gretil": "...",
    "wikidata": "..."
  },

  "counts": {
    "witnesses": 0,
    "surrogates": 0,
    "editions": 0,
    "texts": 0,
    "translations": 0,
    "scholarship": 0,
    "passages": 0
  },

  "availability": {
    "source": "etext",
    "translation": {
      "eng": "partial"
    },
    "manuscripts": "known",
    "bibliography": "partial"
  },

  "best_text": {...},
  "best_translation": {...},

  "coverage": {
    "identity": "resolved",
    "source": "etext",
    "translation": "partial",
    "bibliography": "partial"
  },

  "created_at": "...",
  "updated_at": "...",
  "state_cursor": 123456
}

Normal clients get this.

Scholarly/agent clients can request:

?include=assertions,evidence,provenance

8. The killer endpoint is still
/bundle

This is where OpenPāṭala becomes more valuable than merely cloning OpenAlex.

GET /v1/works/{id}/bundle

returns:

Work
People
Titles
Identity evidence
Witnesses
Surrogates
Editions
Texts
Translations
Scholarship
Passage map
Rights
Coverage
Open gaps
Provenance

Your existing /bundle/{id} is already aiming toward exactly this.

Make it excellent.

This endpoint alone becomes spectacular for agents.
9. Copy OpenAlex’s query language almost deliberately

Don’t invent strange developer ergonomics.

OpenAlex supports search, filter, sort, select, group_by, pagination and external-ID lookup across entity endpoints. 

OpenPāṭala should support:

GET /v1/works?search=abhinavagupta

GET /v1/works?filter=language:san

GET /v1/works?filter=author.id:PT...,translation.eng:none

GET /v1/works?filter=has_text:true,translation.eng:none

GET /v1/works?filter=tradition:trika,has_witness:true

GET /v1/works?sort=scholarship_count:desc

GET /v1/works?group_by=translation.eng

GET /v1/works?select=id,display_name,availability

GET /v1/works?cursor=...

This reduces adoption friction for anyone already familiar with OpenAlex.
10. External-ID resolution should be ridiculously good

OpenAlex allows direct lookup through DOI, ORCID, ROR and related IDs. 

OpenPāṭala should do:

GET /v1/works/gretil:sa_abhinava-tantraloka
GET /v1/works/pandit:12345
GET /v1/people/orcid:...
GET /v1/institutions/ror:...

And:

GET /v1/resolve?q=Tantraloka

should search:

exact external IDs
exact normalized titles
transliteration variants
alternate titles
authors
known aliases
bibliographic fingerprints
fuzzy search
semantic search

with explicit candidates rather than pretending certainty.
11. Build proper autocomplete

OpenAlex has a dedicated autocomplete API designed for fast UI typeahead, targeting roughly 200ms behavior. 

Copy it:

GET /v1/autocomplete/works?q=tantr

Response:

{
  "results": [
    {
      "id": "...",
      "display_name": "Tantrāloka",
      "hint": "Abhinavagupta · c. 10th–11th c.",
      "entity_type": "work",
      "external_id": "pandit:..."
    }
  ]
}

This powers your site and everybody else’s.
12. Replace
WorkCompleteness with WorkCoverage

This becomes your signature innovation.

Current code already contains the idea but implements it very weakly.

Make the final object:

WorkCoverage
├─ identity
├─ authorship
├─ dating
├─ witnesses
├─ surrogates
├─ editions
├─ texts
├─ translations
│    ├─ eng
│    ├─ deu
│    ├─ fra
│    ├─ hin
│    └─ ...
├─ scholarship
├─ passage_structure
├─ rights
└─ evaluation

Each dimension gets:

{
  "state": "PARTIAL",
  "confidence": 0.83,
  "evidence_count": 7,
  "last_checked": "...",
  "next_action": "SEARCH_TRANSLATION"
}

Now OpenPāṭala is not merely:

what exists.

It knows:

what we do not yet know.

That powers autonomy.
13. This is how the internet-scouring system should actually work

Do not create one free-running “crawler agent.”

Create a self-filling graph.

                CURRENT OPENPĀṬALA
                         │
                         ▼
                 COVERAGE COMPILER
                         │
             identifies exact missing state
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
 FIND_SOURCE      FIND_TRANSLATION   FIND_WITNESS
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                   DISCOVERY TASK
                         │
                         ▼
                SOURCE DISCOVERY
                         │
                 SourceCandidate
                         │
                         ▼
                  POLICY / RIGHTS
                         │
                         ▼
                     SAMPLE
                         │
                         ▼
               EXTRACTION VALIDATION
                         │
                         ▼
                    CANARY INGEST
                         │
                         ▼
                UTILITY MEASUREMENT
                         │
                     good?
                   /      \
                 yes       no
                 │          │
            expand     NegativeResult

That is the autonomous OpenPāṭala.
14. Structured harvesting before AI crawling

This matters enormously.

The agent should first look for machine-readable protocols.

Priority:

native API
↓
DTS
↓
IIIF
↓
OAI-PMH
↓
TEI repository
↓
JSON-LD / structured HTML
↓
sitemap
↓
ordinary HTML extraction
↓
LLM-assisted extraction

DTS 1.0 was published in February 2026 specifically as a standard API for navigating and retrieving machine-actionable text collections. 

IIIF Presentation 3 exposes structured digital-object manifests, canvases and annotations suitable for manuscripts and scans. 

OAI-PMH exists specifically for metadata harvesting between repositories. 

TEI remains the obvious interoperability representation for textual editions, including manuscript transcription and critical apparatus structures. 

Therefore OpenPāṭala shouldn’t write bespoke scrapers for everything.
15. Build generic protocol adapters

Instead of:

pandit.py
university_x.py
university_y.py
university_z.py

build:

OaiPmhAdapter
IiifAdapter
DtsAdapter
TeiRepositoryAdapter
SitemapAdapter
JsonApiAdapter
GithubCorpusAdapter
HtmlCatalogAdapter

Then individual providers become mostly configuration.

Example:

provider: example_library
transport: oai_pmh

endpoint:
  base_url: ...

mapping:
  title: dc:title
  creator: dc:creator
  identifier: dc:identifier

entity_policy:
  default_type: witness

rights:
  metadata_fetch: allow
  content_fetch: review

This is a major scaling trick.
16. Let agents discover providers, not directly create truth

Your discovery agent can scour:

web search results
bibliographies
repository links
GitHub
institution sites
IIIF collections
OAI registries
DTS endpoints
sitemaps
known references in existing records

But the result is:

SourceCandidate

not:

new canonical Works

Schema:

SourceCandidate
  id
  discovered_by
  discovery_run
  url
  possible_provider
  protocol_candidates[]
  sample_urls[]
  reason
  target_gaps[]
  confidence
  status

Then automatically test it.
17. Source adoption should itself be evaluated

You already have the right idea in source_utilities.

Give every provider:

novelty_yield
works_per_request
identity_link_rate
artifact_yield
metadata_quality
structuredness
rights_clarity
authority_value
target_gap_match
failure_rate
cost_per_useful_record

Then:

SourceUtility ≈
    novelty
  × target_gap_match
  × authority
  × structuredness
  × rights_clarity
  × identity_link_rate
  / acquisition_cost

Don’t obsess about the exact equation.

Use the dimensions independently as well.

Now autonomous discovery becomes economically rational.
18. The key autonomous loop

This should literally run forever:

for each Work:
    compute coverage

coverage emits gaps

rank gaps by:
    importance
    likely resolution
    downstream impact
    cost

attempt cheap deterministic resolution

attempt known structured sources

attempt web discovery

if source discovered:
    register candidate
    inspect terms/robots/protocol
    sample
    extract
    evaluate
    ingest if allowed

if no evidence found:
    record SearchPerformed
    record NegativeResult

schedule next search only when:
    sufficient time passes
    source changes
    new lead appears
    new model/tool capability appears

That negative-search history is part of the long-term moat.
19. A source search should leave evidence

Never merely set:

translation = NONE

Instead:

SearchEvent
  target: Tantrāloka
  objective: FIND_ENGLISH_TRANSLATION

  searched:
    Crossref
    OpenAlex
    Internet Archive
    WorldCat-like source
    Google Books-like source
    relevant catalogs
    bibliographic databases
    web search

  queries:
    ...

  timestamp:
    ...

  candidates_found:
    ...

  conclusion:
    NONE_CONFIRMED | CANDIDATE_FOUND | PARTIAL_FOUND

Then the API can distinguish:

UNKNOWN

from:

SEARCHED_NO_TRANSLATION_FOUND

That distinction is extremely valuable.
20. The canonical ingestion pipeline

Final ingestion should be:

DISCOVERY
   │
   ▼
SourceResource
   │
   ▼
FETCH
   │
   ├──── exact bytes ────→ Artifact
   │
   ▼
RawObservation
   │
   ▼
ExtractionActivity
   │
   ▼
CandidateAssertions
   │
   ▼
EntityCandidates
   │
   ▼
Identity Resolution
   │
   ├─ exact match
   ├─ probable match
   ├─ ambiguous
   └─ genuinely new
   │
   ▼
Semantic Event
   │
   ▼
Canonical Assertions
   │
   ▼
Projection Compiler
   │
   ├─ WorkRecord
   ├─ PersonRecord
   ├─ WorkCoverage
   ├─ Search index
   └─ API changefile

This is where the hard-core replay work belongs: underneath this flow.

It should receive perhaps 10–15% of engineering attention now, not 90%.
21. The actual API surface I would ship

CORE GRAPH

GET /works
GET /works/{id}

GET /people
GET /people/{id}

GET /institutions
GET /institutions/{id}

GET /witnesses
GET /witnesses/{id}

GET /surrogates
GET /surrogates/{id}

GET /editions
GET /editions/{id}

GET /texts
GET /texts/{id}

GET /translations
GET /translations/{id}

GET /scholarship
GET /scholarship/{id}

GET /passages/{id}


DISCOVERY

GET /search
GET /autocomplete/{type}
GET /resolve
POST /resolve/batch


DEEP GRAPH

GET /works/{id}/bundle
GET /works/{id}/relations
GET /works/{id}/sources
GET /works/{id}/witnesses
GET /works/{id}/editions
GET /works/{id}/texts
GET /works/{id}/translations
GET /works/{id}/scholarship
GET /works/{id}/coverage
GET /works/{id}/history


EPISTEMIC

GET /assertions/{id}
GET /assertions/{id}/evidence
GET /entities/{id}/assertions
GET /observations/{id}
GET /provenance/{id}


GAPS

GET /frontier
GET /frontier/sources
GET /frontier/translations
GET /frontier/witnesses
GET /frontier/identity
GET /frontier/rights


DATA INFRA

GET /changes
GET /changes/{date}

GET /snapshots
GET /stats
GET /providers
GET /providers/{id}

That’s enough.

Do not make 200 endpoints.
22. Make
/frontier a real API product

This is where you become something OpenAlex isn’t.

Examples:

GET /v1/frontier?filter=has_text:true,translation.eng:none

means:

show me Sanskrit works with usable e-texts but no known English translation.

Or:

GET /v1/frontier?filter=witnesses:>0,surrogates:0

manuscripts known but no known digitization.

Or:

GET /v1/frontier?filter=identity:contested

unresolved scholarly identities.

That endpoint is gold for:

researchers
translation projects
digital humanities teams
AI agents
funders
institutions
your own Factory

23. Public changefiles and snapshots

Copy another great OpenAlex mechanism.

OpenAlex makes its dataset available as bulk snapshots and exposes incremental changefiles; its current snapshot is partitioned by entity and update date in JSONL, and changefiles are also offered in JSONL/Parquet. 

OpenPāṭala should publish:

snapshots/
  2026-09-01/
    works.parquet
    people.parquet
    witnesses.parquet
    editions.parquet
    texts.parquet
    translations.parquet
    scholarship.parquet
    assertions.parquet

plus:

changes/
  2026-09-02/
  2026-09-03/

JSONL + Parquet.

Now other researchers can mirror you.

That is how you become infrastructure.
24. Your public data and raw source data must remain separate

This matters because unlike OpenAlex, your raw material includes scans, texts and translations with heterogeneous rights.

Expose openly:

canonical metadata
Pāṭala IDs
crosswalks
relationships
public-domain assertions
provenance metadata
coverage state
search history where safe

Raw content stays governed independently:

READ
COMPUTE
DERIVE
REDISTRIBUTE
TRAIN

IIIF itself is designed to reference distributed resources rather than forcing every institution’s content into one central store. 

So OpenPāṭala can know about a manuscript and deeply integrate it without owning the scan.
25. Search architecture: don’t overengineer yet

For the current size:

Postgres
+ pg_trgm
+ PostgreSQL full-text

is enough.

Build search documents:

work_search
  id
  preferred_title
  normalized_titles[]
  transliteration_forms[]
  author_names[]
  external_ids[]
  traditions[]
  languages[]
  search_vector

Index:

GIN(search_vector)
GIN(normalized_titles)
pg_trgm title indexes
B-tree external IDs

Only add a separate OpenSearch-like search cluster when measurement shows Postgres is the limiting factor.
26. But build the query layer independently of storage

Create:

QueryAST

Example:

filter=language:san,translation.eng:none

becomes:

AND(
  Eq(language, "san"),
  Eq(translation.eng, NONE)
)

Then compile to Postgres today.

Later:

PostgresCompiler
OpenSearchCompiler
ClickHouseCompiler

without changing the API.

That is actual future-proofing.
27. Read models are disposable

Do not make API performance query the assertion graph dynamically for every request.

Compile:

work_current
person_current
witness_current
translation_current
work_coverage
work_counts
search_documents

These are denormalized.

Disposable.

Rebuildable.

Fast.

Permanent truth remains underneath.
28. Add analytical
group_by

This sounds boring but is hugely important for market usability.

Examples:

GET /works?group_by=tradition
GET /works?group_by=century
GET /works?group_by=source.state
GET /works?group_by=translation.eng
GET /witnesses?group_by=institution.id

OpenAlex makes filtering and grouping first-class throughout its API, which is why researchers can use it directly rather than downloading everything. 

Pāṭala should do the same.
29. Every web page uses the public API

This is another OpenAlex lesson: its public web interface sits directly over the same data/API product. 

Do:

patala.org/work/...
patala.org/person/...
patala.org/witness/...

But the frontend fetches:

api.patala.org/v1/...

No secret parallel backend.

Dogfood everything.
30. What the actual website should look like

Homepage:

Search  [ Tantrāloka                         ]

23,842 works
...

Search result:

Tantrāloka
Abhinavagupta · Sanskrit · Trika

TEXT       ✓
MANUSCRIPT 31
TRANSLATION partial
SCHOLARSHIP 84

Work page:

OVERVIEW
TEXTS
MANUSCRIPTS
EDITIONS
TRANSLATIONS
SCHOLARSHIP
ARGUMENTS             ← later Pāṭala
HISTORY

And very visibly:

WHAT'S MISSING

That last tab is uniquely yours.
31. Agent-native from day one

OpenAlex now even publishes an LLM-oriented quick reference for agents. 

Do better.

Ship:

/openapi.json
/llms.txt
/docs
/mcp

MCP tools:

patala_search
patala_resolve
patala_get_work
patala_get_bundle
patala_get_sources
patala_get_translations
patala_get_evidence
patala_get_frontier
patala_changes

An agent should need one sentence:

“Find all source-ready untranslated Śaiva works.”

And be able to query OpenPāṭala directly.
32. SDKs

Generate from OpenAPI:

patala-python
@patala/client

Developer experience:

from patala import Patala

p = Patala()

works = p.works.list(
    filter="has_text:true,translation.eng:none"
)

and:

work = p.works.get("...")
bundle = work.bundle()

33. The API business model

OpenAlex’s current model is instructive: underlying data remains free, while its API is freemium and higher-frequency snapshots/change services are commercial services. 

I would do an even more aggressive adoption strategy initially:

PUBLIC
metadata API
small/medium usage
snapshots
basic changefeed
MCP
non-commercial + academic use

PAID
high QPS
bulk entity resolution
large batch export
fresh changefeeds
private corpora
private institution reconciliation
custom ingest
SLA
advanced provenance/evidence API
commercial embeddings/search
benchmark/evaluation datasets

Do not sell access to copyrighted source content you don’t control.

Sell the infrastructure.
34. The actual moat

Not API code.

Not FastAPI.

Not search.

Not LLMs.

Not even the event ledger.

The moat becomes:

                 PĀṬALA ID
                     │
    ┌────────────────┼─────────────────┐
    │                │                 │
  PANDiT           GRETIL            IIIF
    │                │                 │
 Archive          Edition           Witness
    │                │                 │
Translation      Scholarship        Scan

plus years of:

identity corrections
false-match history
expert decisions
translation-existence searches
failed searches
rights determinations
institution relationships
source lineage
source quality measurements
scholar contributions

A future model can regenerate your embeddings.

It cannot cheaply regenerate that history.
35. The thing to maximize is not Work count

Stop dashboarding:

1099 Works

as the main success metric.

Instead track:

Canonical Works
External records ingested
Cross-source links
Average providers / Work
Works with ≥2 sources
Works with usable e-text
Works with known witness
Works with translation status checked
Works with scholarship linked
Conflicting identities discovered
Conflicts resolved
Negative searches preserved
Freshness

The killer metric eventually is something like:

% of important Sanskrit works for which OpenPāṭala can reliably answer the full source/translation/manuscript/scholarship question.
36. The next 90 days

This is where I’d radically alter the previous roadmap.
Weeks 1–2 — Product spine

Stop adding infrastructure.

Make one 100-work gold corpus perfect.

For each:

canonical Work
at least one provider observation
correct external ID
correct Work/Text distinction
real source availability
real translation status
bundle
coverage

Fix only as much replay/history infrastructure as necessary to make that data safe.

Exit gate:

100 / 100 works return factually useful bundles.

Not “event test PASS.”
Weeks 3–4 — OpenAlex-class API ergonomics

Implement:

search
filter
sort
select
group_by
cursor
external-ID lookup
autocomplete
batch resolve

Delete placeholders.

/frontier/translations must use actual indexed evidence.

Exit gate:

A third-party developer can answer:

all source-ready Sanskrit works
with no known English translation
by tradition

with one API request.
Weeks 5–8 — Corpus acquisition

Now unleash structured ingestion.

Priority isn’t “11 adapters.”

Priority is:

number of useful canonical crosswalks

Bring in your strongest sources.

Each source record produces:

Observation
→ Candidate
→ identity link
→ coverage gain

Use generic IIIF/DTS/OAI-PMH/TEI adapters where possible instead of bespoke crawlers. DTS and IIIF already give you standard interoperability surfaces for texts and digitized objects. 

Target:

thousands → tens of thousands
of properly resolved Works,
not merely rows.

Weeks 9–12 — Launchable OpenPāṭala

Ship:

api.patala.org
patala.org search UI
OpenAPI docs
Python SDK
JS SDK
MCP
llms.txt
daily stats
snapshot
changefeed
public coverage dashboard

Then announce:

OpenPāṭala: an open graph and API for Sanskrit texts.

That is a real launch.
37. Then autonomous OpenPāṭala

Only after the API/data product works:

Coverage gaps
      ↓
TaskCandidates
      ↓
NRAH
      ↓
SourceDiscoveryAgent
      ↓
structured-source detection
      ↓
adapter selection/generation
      ↓
canary
      ↓
evaluation
      ↓
ingest
      ↓
coverage improves

Then it genuinely starts filling itself.
38. And then translation

At that point the existing Factory becomes enormously more powerful.

OpenPāṭala says:

Work X
source = CLEAN_ETEXT
English translation = SEARCHED_NONE_FOUND
rights.compute = ALLOW

Automatically emits:

GENERATE_TRANSLATION

Factory:

SOURCE
→ L0
→ T1/ARGMAP
→ L1
→ L2
→ Eval
→ TranslationVersion

and writes its outputs back into OpenPāṭala as derived objects.

Now your translation system isn’t a separate toy.

It’s a consumer/producer of the graph.
39. Scholar product follows naturally

The system eventually identifies:

translation disagreement
identity ambiguity
manuscript ambiguity
interpretive crux

and generates tiny review tasks.

Scholar says:

accept
reject
qualify
uncertain

That becomes permanent epistemic capital.

This is where the Scholar Workbench we’ve spent all that time designing finally has a concrete reason to exist.
40. Then the argument/research graph

Once thousands of works have:

stable identity
passages
translations
scholarship

you can reliably compile:

Propositions
Arguments
Objections
Replies
Cruxes
Interpretations
OpenQuestions

Now Pāṭala stops being merely a catalog.

But OpenPāṭala remains underneath it.
41. Greek should be a proof of generality, not another startup

Once Sanskrit works end-to-end:

PĀṬALA CORE
      │
      ├── Sanskrit profile
      │
      └── Greek profile

OpenGreekAndLatin/Perseus-like corpora become another provider family.

If you’ve modeled:

Work
Witness
Edition
Text
Passage
Translation
Scholarship

correctly, Greek should require:

new adapters
new resolver rules
new vocabularies
new evaluation profiles

not a new architecture.

That’s the test that OpenPāṭala really became generic.
42. The eventual architecture

I would finally converge the repository to:

openpatala/

packages/
  protocol/
    ids/
    schemas/
    relations/
    query/

services/
  ingest/
  identity/
  projection/
  search/
  coverage/
  discovery/
  api/

adapters/
  protocols/
    oai_pmh/
    iiif/
    dts/
    tei/
    sitemap/

  providers/
    gretil/
    pandit/
    ...
    
apps/
  web/
  docs/

integrations/
  mcp/
  python-sdk/
  js-sdk/

infra/
  postgres/
  object-storage/
  snapshots/
  observability/

proof/
  developer-tests/

Then keep the independent release verifier outside this repository.
43. Storage

Simple final stack:

Postgres
  canonical entities
  assertions
  relations
  projections
  coverage
  source registry
  queues

R2 / S3-compatible object storage
  exact observations
  TEI
  permitted scans
  JSON snapshots
  Parquet snapshots
  large evaluator outputs

Postgres search initially
  FTS
  trigram

Redis
  optional hot caching only

Cloudflare/CDN
  cache public GET endpoints
  snapshots/content delivery

And later, only if needed:

OpenSearch
→ giant full-text search

ClickHouse
→ huge analytics/group-bys

Not now.
44. The final boundary between OpenPāṭala and Pāṭala

This is probably the most important thing to lock after this entire conversation.
OpenPāṭala owns

IDENTITY

SOURCE REALITY

ARTIFACTS

OBSERVATIONS

PROVENANCE

RIGHTS

WORKS / PEOPLE / WITNESSES / EDITIONS

TEXT AVAILABILITY

TRANSLATION AVAILABILITY

SCHOLARSHIP INDEX

PASSAGE ADDRESSING

CROSSWALKS

CURRENT COVERAGE

CHANGE HISTORY

Pāṭala proper owns

translation generation

translation evaluation

arguments

interpretations

cruxes

OpenQuestions

agent research

scholar adjudication

education

media

self-improving agents

RealityRequests

OpenPāṭala may expose outputs from all those systems, but does not need to implement their intelligence.

That keeps it comprehensible.
45. The market attack

The sequence is:

1. Become the easiest API for Sanskrit textual discovery.

2. Become the canonical crosswalk between existing Sanskrit databases.

3. Become the canonical place to answer:
   "is there a text / manuscript / edition / translation?"

4. Get developers and researchers using Pāṭala IDs.

5. Publish snapshots so other projects build on them.

6. Give institutions simple reconciliation:
   their ID ↔ Pāṭala ID.

7. Give scholars correction/attestation tools.

8. Use your own Factory to fill missing translations.

9. Use accumulated gaps to drive research.

10. Add adjacent textual traditions.

The moment datasets start including:

patala_id

you are beginning to lock the graph.

That matters much more than having 50 fancy subsystems.
46. The single build objective I would give the agent now

Not:

finish OpenPāṭala 0.6 replay infrastructure.

And not:

implement the whole final Pāṭala vision.

Give it:

Turn wiggly into a market-usable OpenAlex-style API for Sanskrit textual resources. Make 100 curated Works genuinely excellent end-to-end, then generalize that path to bulk ingestion. Infrastructure work is permitted only when required to make those records trustworthy.

And the binary product test is:

Given a Sanskrit work name unknown to the caller:

1. /search finds it.
2. /resolve identifies it.
3. /works/{id} returns a stable useful record.
4. /bundle returns all known source types.
5. every external resource has provenance.
6. source/text/translation availability is evidence-backed.
7. /coverage accurately says what's missing.
8. /frontier can query those missing dimensions.
9. re-ingestion enriches rather than duplicates it.
10. another developer can reproduce the query through public docs.

That is OpenPāṭala 1.0.

Not an event ledger with 26 green gates.
The north star

OpenAlex is currently an enormous graph of scholarship; its official docs say it indexes over 240 million works and exposes them through a standardized API, snapshots and related services. 

You do not need 240 million records.

You need to become the place where, for premodern textual traditions:

one Pāṭala ID resolves the chaos.

Then the much bigger vision we developed starts to matter:

OpenAlex tells an agent:

what scholarship exists?

OpenPāṭala tells it:

what textual reality exists?

Pāṭala eventually tells it:

what do we currently know,
why do we believe it,
what remains unresolved,
and what should intelligence do next?

That’s the path.