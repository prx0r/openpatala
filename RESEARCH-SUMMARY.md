# RESEARCH-SUMMARY.md — Cloned Repos Analysis
*Status: HISTORICAL. Cloned-repos analysis snapshot; frozen (2026-08-17).*

*2026-08-17 · 7 repos cloned, analyzed for OpenPāṭala integration*

---

## Repos Cloned

| Repo | Size | What it is | OpenPāṭala relevance |
|---|---|---|---|
| OpenPecha/toolkit-v2 | 6.6M | STAM-based text + stand-off annotations | TextAnchor/Annotation adapter |
| stam | 42M | Stand-off Text Annotation Model | Annotation substrate for passages |
| explorehomer-atlas | 52M | Perseus ATLAS annotation/alignment | Passage annotation reference |
| mmm-data-conversion | 1.5M | Bodleian TEI → CIDOC-CRM → RDF | TEI ingestion pipeline model |
| bibma-metadata | 1.1M | Biblissima ontologies/RDF templates | Ingestion mapping reference |
| collatex | 5.5M | Align multiple witnesses | Variant graph apparatus |
| pairwise-light | 2.3G | Text-reuse analysis (KITAB) | DERIVED_FROM goldmine |

## Key Findings

### STAM + OpenPecha (highest priority)
- STAM assumes "information about a text is an annotation"
- Annotations can target text spans OR other annotations
- OpenPecha toolkit-v2 uses STAM for Buddhist textual corpora
- Separates base text from stand-off annotations
- **Directly relevant to Pāṭala TextAnchor/Annotation model**

### Explore Homer ATLAS
- ATLAS = Aligned Text and Linguistic Annotation Server
- Perseus 6 integrates morphology, syntax, named entities, alignments, annotations
- Structurally close to Pāṭala's passage-level annotation
- **But Pāṭala goes deeper: assertion → evidence → adjudication → dependency**

### MMM Data Conversion
- Bodleian TEI → CIDOC-CRM/FRBRoo → RDF pipeline
- Explicit transformation scripts
- **Model for how to ingest TEI into shared ontology**
- Pāṭala approach is stronger: observation → assertion → identity → projection

### Pairwise-light (KITAB)
- Massive text-reuse analysis across historical literature
- Pairwise reuse relationships
- **Potential DERIVED_FROM goldmine for Pāṭala**
- Could generate textual derivation/intertextuality graph

## Integration Points

| System | How to integrate with Pāṭala |
|---|---|
| STAM | TextAnchor adapter for stand-off annotations |
| OpenPecha | Collaborative annotation → Pāṭala assertions |
| ATLAS | Ingest annotations as EvidenceUse |
| MMM | TEI ingestion pipeline model |
| CollateX | Witness alignment → VariantGraph |
| KITAB | Text-reuse → DERIVED_FROM edges |
| Biblissima | Federated authority reconciliation |
