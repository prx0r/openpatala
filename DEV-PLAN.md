# DEV-PLAN.md — Build Plan (Aligned with PATALAPATH + PATALAPATH2)
*Status: SUPERSEDED. Superseded 2026-11-10 by OPENPATALA.md live state; kept as reference (2026-08-17).*

> SUPERSEDED 2026-11-10 (banner only, no content changed): the 08-17 phase
> map and counts (1099/247/2181) are stale. Canonical live state:
> `OPENPATALA.md` (verified 2026-11-07; `check.py` GREEN + 2 recorded
> BLOCKED; box DB 555/909). Phase 1.1–1.8 remain reference, not a work
> queue. Do not build from the phase map below without re-verifying.

*2026-08-17T17:45:00Z · Canonical reference: PATALAPATH.md + PATALAPATH2.md*

---

## Current State

```
Phase 0.6: Replayable Hard Core ✓
Phase 1.0: OpenPāṭala Corpus ✓
  1099 works, 247 assertions, 108 ext_ids, 2181 events
  13 adapters, 7 serializers, 22 schemas, 34 tables
  5/5 conformance PASS, 12/12 conformance PASS
```

## What PATALAPATH2 Says

> "The actual priority is: Make OpenPāṭala's canonical Work dossier + cross-source identity graph + query API excellent first. Then selectively plug these external mechanisms into the places where they save enormous work."

> "Autonomous discovery before strong identity resolution produces autonomous duplicate generation."

> "CollateX before you have multiple resolved witnesses is machinery with nothing valuable to collate."

## Correct Phase Map (from PATALAPATH2 §18)

```
Phase 1.1 — GOLD WORK DOSSIERS
  Pick 100 representative Works
  Each produces excellent /works/{id}, /bundle, /coverage
  Exit: 100 useful human-readable + agent-readable dossiers

Phase 1.2 — CROSS-SOURCE IDENTITY
  Integrate GRETIL, PANDiT, Sanskritree, Archive, OpenAlex
  Build: ExactIdentifierMatcher, NormalizedTitleMatcher,
         AuthorTitleMatcher, TextFingerprintMatcher,
         CandidateRanker, ResolutionProposal
  Output: same / probably same / possibly same / not same / unresolved

Phase 1.3 — OPENALEX-CLASS QUERY LAYER
  search, filter, sort, select, group_by, cursor
  autocomplete, external-ID lookup, batch resolve
  Current api.py uses substring search — fix this

Phase 1.4 — COVERAGE + FRONTIER
  Rewrite WorkCoverage into genuine projection
  Each dimension: state, confidence, evidence_count, last_checked
  /frontier from real SQL/projected state

Phase 1.5 — PROVIDER EXPANSION
  Steal Garglecum + MMM mechanisms
  Every provider: adapter, mapping, fixtures, health, canary,
  freshness, yield, rights policy, crosswalk rate

Phase 1.6 — SELF-FILLING DISCOVERY
  Connect NRAH: Coverage → Gap → GapAction → NRAH → Discovery

Phase 1.7 — TEXT/PASSAGE ANNOTATION INTEROP
  STAM, OpenPecha, ATLAS, Web Annotation for passages/linguistics

Phase 1.8 — WITNESS COLLATION
  CollateX + manuscript intelligence
  Witness → Surrogate → Transcription → Collation → VariantGraph
```

## What to Do Now

**Phase 1.1: GOLD WORK DOSSIERS**

Pick 100 representative Works:
- major famous
- minor obscure
- multiple spellings
- multiple authorship claims
- with/without GRETIL
- with/without translation
- commentaries
- root texts
- bundled works

Each must produce an excellent:
- `/works/{id}`
- `/bundle`
- `/coverage`

Exit condition: 100 useful human-readable + agent-readable dossiers

## What NOT to Do

- Don't integrate STAM/CollateX/OpenPeka yet (Phase 1.7+)
- Don't build self-filling discovery yet (Phase 1.6)
- Don't expand providers yet (Phase 1.5)
- Don't build annotation interop yet (Phase 1.7)
- Don't build witness collation yet (Phase 1.8)
- Don't add 20 more adapters before fixing the core
- Don't rebuild what exists in the old project

## Priority Order

```
NOW: Phase 1.1 (Gold Work Dossiers)
THEN: Phase 1.2 (Cross-Source Identity)
THEN: Phase 1.3 (OpenAlex-Class Query Layer)
THEN: Phase 1.4 (Coverage + Frontier)
THEN: Phase 1.5 (Provider Expansion)
THEN: Phase 1.6 (Self-Filling Discovery)
THEN: Phase 1.7 (Annotation Interop)
THEN: Phase 1.8 (Witness Collation)
```
