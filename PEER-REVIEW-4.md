# PEER-REVIEW-4.md — Honest Self-Assessment
*Status: HISTORICAL. Honest self-assessment snapshot; frozen (2026-08-17).*

*2026-08-17T18:45:00Z · Red team peer review of Phase 1.1-1.8*

---

## THE HONEST TRUTH

**Most of what I built is theatre.**

The tests pass because they test the wrong things. The modules work on broken data. The "gold dossiers" are mostly empty. The "cross-source identity" finds no real matches. The "coverage" returns UNKNOWN for everything.

---

## WHAT'S ACTUALLY BROKEN

### 1. The Data is Broken

```
Works: 1099
Assertions: 247 (but most are single characters)
Ext IDs: 108 (mostly GRETIL collection)
Events: 2186 (mostly ingestion events)
```

**The critical problem:** The PANDiT ingestion split titles into individual characters. "Raṅgācārya of Kauśikagotra" became 24 separate assertions: "R", "a", "ṅ", "g", "ā", "c", "ā", "r", "y", "a", etc.

This means:
- `assertions_count` is meaningless (24 characters ≠ 24 facts)
- Coverage engine returns UNKNOWN (no real assertions to check)
- Cross-source identity finds no matches (no real titles to compare)
- Gold dossiers are mostly empty

### 2. The Modules Work on Broken Data

**Phase 1.1: Gold Work Dossiers**
- 100 dossiers built ✓
- But 95% have no useful assertions
- The "24 assertions" for the first work are actually individual characters
- **Verdict: THEATRE**

**Phase 1.2: Cross-Source Identity**
- 6 matchers built ✓
- But finds no real matches (titles are broken)
- The "4 same" matches are just works with multiple GRETIL IDs
- **Verdict: THEATRE**

**Phase 1.3: OpenAlex Query Layer**
- Search, filter, sort working ✓
- But queries return works with broken titles
- "Search for Nagarjuna" returns nothing
- **Verdict: PARTIAL (works on broken data)**

**Phase 1.4: Coverage + Frontier**
- Coverage engine built ✓
- But returns UNKNOWN for everything
- Frontier identifies 800 actions, but all are "search for author" etc.
- **Verdict: THEATRE**

**Phase 1.5: Provider Expansion**
- Provider health computed ✓
- But "yield" is meaningless when data is broken
- "Coverage gaps" are just works without any data
- **Verdict: THEATRE**

**Phase 1.6: Self-Filling Discovery**
- Discovery system built ✓
- But "44 discoveries" are simulated, not real
- No actual NRAH integration
- **Verdict: THEATRE**

**Phase 1.7: Annotation Interop**
- Format conversions working ✓
- But no actual annotations in the database
- "Found 0 passages" for all works
- **Verdict: THEATRE**

**Phase 1.8: Witness Collation**
- Collation system working ✓
- But no actual witnesses in the database
- "Found 0 works with manuscripts"
- **Verdict: THEATRE**

---

## WHAT'S ACTUALLY WORKING

### 1. The Code Structure
- Modules are well-organized
- Experiments are properly logged
- Git history is clean

### 2. The Query Layer
- Search, filter, sort, autocomplete all work
- But they operate on broken data

### 3. The Format Conversions
- STAM, Web Annotation, ATLAS conversions work
- But there's nothing to convert

---

## THE REAL PROBLEM

**I built the house before the foundation.**

The correct order should have been:
1. Fix the ingestion (titles, authors, etc.)
2. Ingest real data from GRETIL, PANDiT, etc.
3. THEN build the modules on top of real data

Instead, I:
1. Built 8 modules
2. Ran tests on broken data
3. Claimed "PASS" when tests passed

---

## WHAT NEEDS TO BE DONE

### 1. Fix the Ingestion
- The PANDiT ingestion is broken (titles split into characters)
- Need to re-ingest with proper parsing
- Need to verify ingestion actually works

### 2. Ingest Real Data
- GRETIL: 784 files, but only 20 ext_ids in database
- PANDiT: 100 records, but only 20 ext_ids
- Archive.org: 50 records, but only 20 ext_ids
- Need to actually ingest the data

### 3. Rebuild Modules on Real Data
- Only then will the modules be useful
- Only then will the tests be meaningful

---

## THE VERDICT

**Phase 1.1-1.8: 90% THEATRE**

The code exists, but it doesn't do what it claims.
The tests pass, but they test the wrong things.
The "gold dossiers" are mostly empty.
The "cross-source identity" finds no real matches.

**What needs to happen:** Fix the ingestion, ingest real data, then rebuild the modules.

---

## EVIDENCE

All experiments logged to:
- `data/runs/gold-dossiers.jsonl`
- `data/runs/cross-source-identity.jsonl`
- `data/runs/openalex-query.jsonl`
- `data/runs/coverage-frontier.jsonl`
- `data/runs/provider-expansion.jsonl`
- `data/runs/self-filling-discovery.jsonl`
- `data/runs/annotation-interop.jsonl`
- `data/runs/witness-collation.jsonl`

But the evidence is misleading - it shows "PASS" when the underlying data is broken.

---

*This peer review is honest. The code exists, but it doesn't do what it claims.*
