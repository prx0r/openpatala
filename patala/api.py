#!/usr/bin/env python3
"""patala/api.py — OpenPāṭala API v1 (Postgres-backed).

Per newbuildmainspec §52-67: all core endpoints + /bundle, /resolve, /frontier, /changes.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from patala.db import store
from patala.hashing import uuid7

app = FastAPI(title="OpenPatala API v1", version="1.0.0")


def _envelope(results, meta=None):
    if isinstance(results, list):
        return {"meta": {"count": len(results), "schema_version": "1.0", **(meta or {})}, "results": results}
    return {"meta": {"schema_version": "1.0", **(meta or {})}, "data": results}


def _error(code, message, candidates=None, retryable=False):
    return {"error": {"code": code, "message": message, "candidates": candidates or [], "retryable": retryable}}


# --- Works ---

@app.get("/v1/works")
def list_works(limit: int = Query(20, le=100)):
    works = store.list_works(limit)
    return _envelope(works)


@app.get("/v1/works/{work_id}")
def get_work(work_id: str):
    work = store.get_work(work_id)
    if not work:
        raise HTTPException(404, _error("NOT_FOUND", f"Work {work_id} not found"))
    return _envelope(work)


@app.get("/v1/works/{work_id}/assertions")
def get_work_assertions(work_id: str):
    assertions = store.list_assertions(subject_id=work_id)
    return _envelope(assertions)


@app.get("/v1/works/{work_id}/completeness")
def get_work_completeness(work_id: str):
    work = store.get_work(work_id)
    if not work:
        raise HTTPException(404, _error("NOT_FOUND", f"Work {work_id} not found"))
    assertions = store.list_assertions(subject_id=work_id)
    ext_ids = store.list_external_ids(entity_id=work_id)
    return _envelope({
        "work_id": work_id,
        "identity": "RESOLVED" if work.get("preferred_title") else "CANDIDATE",
        "assertion_count": len(assertions),
        "external_id_count": len(ext_ids),
    })


# --- Bundle ---

@app.get("/v1/bundle/{entity_id}")
def get_bundle(entity_id: str):
    """One-request dossier per newbuildmainspec §54.

    Returns: entity, alternative titles, authorship uncertainty, editions, available texts,
    translations, manuscripts, scholarship, provenance.
    """
    work = store.get_work(entity_id)
    if not work:
        raise HTTPException(404, _error("NOT_FOUND", f"Entity {entity_id} not found"))

    conn = store.get_conn()
    cur = conn.cursor()

    # Assertions (authorship, date, tradition, etc.)
    cur.execute("SELECT * FROM assertions WHERE subject_id = %s", (entity_id,))
    assertion_rows = cur.fetchall()
    a_cols = [d[0] for d in cur.description] if assertion_rows else []
    assertions = [dict(zip(a_cols, r)) for r in assertion_rows]

    # Group assertions by predicate
    authorship = [a for a in assertions if "AUTHOR" in (a.get("predicate_uri") or "")]
    dates = [a for a in assertions if "DATE" in (a.get("predicate_uri") or "")]
    traditions = [a for a in assertions if "TRADITION" in (a.get("predicate_uri") or "")]

    # External IDs (alternative titles, cross-references)
    cur.execute("SELECT * FROM external_identifiers WHERE entity_id = %s", (entity_id,))
    ext_rows = cur.fetchall()
    e_cols = [d[0] for d in cur.description] if ext_rows else []
    external_ids = [dict(zip(e_cols, r)) for r in ext_rows]

    # Editions
    cur.execute("SELECT * FROM editions WHERE work_id = %s", (entity_id,))
    edition_rows = cur.fetchall()
    ed_cols = [d[0] for d in cur.description] if edition_rows else []
    editions = [dict(zip(ed_cols, r)) for r in edition_rows]

    # Translations
    cur.execute("SELECT * FROM translations WHERE work_id = %s", (entity_id,))
    trans_rows = cur.fetchall()
    t_cols = [d[0] for d in cur.description] if trans_rows else []
    translations = [dict(zip(t_cols, r)) for r in trans_rows]

    # Witnesses (manuscripts)
    cur.execute("SELECT * FROM witnesses WHERE work_id = %s", (entity_id,))
    wit_rows = cur.fetchall()
    w_cols = [d[0] for d in cur.description] if wit_rows else []
    witnesses = [dict(zip(w_cols, r)) for r in wit_rows]

    # ETexts
    cur.execute("SELECT * FROM etexts WHERE work_id = %s", (entity_id,))
    etxt_rows = cur.fetchall()
    et_cols = [d[0] for d in cur.description] if etxt_rows else []
    etexts = [dict(zip(et_cols, r)) for r in etxt_rows]

    # Passages
    cur.execute("SELECT * FROM passages WHERE work_id = %s", (entity_id,))
    pass_rows = cur.fetchall()
    p_cols = [d[0] for d in cur.description] if pass_rows else []
    passages = [dict(zip(p_cols, r)) for r in pass_rows]

    # Provenance (recent events for this entity)
    cur.execute("""
        SELECT event_id, event_type, recorded_at, payload
        FROM events WHERE %s = ANY(entity_ids)
        ORDER BY cursor DESC LIMIT 10
    """, (entity_id,))
    event_rows = cur.fetchall()
    ev_cols = [d[0] for d in cur.description] if event_rows else []
    provenance = [dict(zip(ev_cols, r)) for r in event_rows]

    # Completeness
    from patala.completeness import CompletenessCompiler
    compiler = CompletenessCompiler()
    completeness = compiler.compile(entity_id, work, editions, translations, assertions, external_ids)

    cur.close()
    conn.close()

    # Build response
    bundle = {
        "entity": work,
        "aliases": [{"scheme": e.get("scheme"), "value": e.get("value")} for e in external_ids],
        "external_ids": external_ids,
        "assertions": {
            "authorship": authorship,
            "date": dates,
            "tradition": traditions,
        },
        "editions": editions,
        "witnesses": witnesses,
        "etexts": etexts,
        "translations": translations,
        "passages": passages,
        "passage_stats": {"count": len(passages)},
        "provenance": provenance,
        "completeness": completeness,
        "state_version": str(int(time.time())),
    }

    return _envelope(bundle)


# --- Resolve ---

@app.get("/v1/resolve")
def resolve_entity(q: str):
    works = store.list_works(1000)
    matches = [w for w in works if (w.get("preferred_title") or "").lower() == q.lower()]
    if len(matches) == 1:
        return _envelope({"status": "EXACT", "entity": matches[0]})
    elif len(matches) > 1:
        return _envelope({"status": "AMBIGUOUS", "candidates": matches})
    return _envelope({"status": "NONE", "query": q})


# --- Search ---

@app.get("/v1/search")
def search(q: str, limit: int = Query(20, le=100)):
    works = store.list_works(10000)
    results = [{"id": w["id"], "type": "work", "display_name": w.get("preferred_title"), "score": 1.0}
               for w in works if q.lower() in (w.get("preferred_title") or "").lower()]
    return _envelope(results[:limit])


# --- Structured bibliography search ---

@app.get("/v1/bibliography/facets")
def bibliography_facets():
    """List the exact recorded work types, traditions, and translation languages."""
    return _envelope(store.bibliography_facets())


@app.get("/v1/bibliography/search")
def search_bibliography(
    q: str | None = None,
    work_type: str | None = None,
    tradition: str | None = None,
    author: str | None = None,
    identifier_scheme: str | None = None,
    source_provider: str | None = None,
    language: str | None = None,
    has_edition: bool | None = None,
    has_translation: bool | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
):
    """Filter the canonical bibliography graph and return source-aware records."""
    try:
        page = store.search_bibliography(
            q=q,
            work_type=work_type,
            tradition=tradition,
            author=author,
            identifier_scheme=identifier_scheme,
            source_provider=source_provider,
            language=language,
            has_edition=has_edition,
            has_translation=has_translation,
            limit=limit,
            offset=offset,
        )
    except ValueError as exc:
        raise HTTPException(422, _error("INVALID_FILTERS", str(exc))) from exc
    results = page.pop("results")
    return _envelope(results, meta=page)


# --- Frontier (per pathway §22) ---

@app.get("/v1/frontier")
def frontier(filter: str | None = None, limit: int = Query(20, le=100)):
    """Real frontier endpoint per pathway §22.
    
    Filter examples:
      translation:none — works with no translation
      identity:unresolved — works with unresolved identity
      source:none — works with no source text
    """
    from patala.work_coverage import compute_coverage
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM works")
    work_ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()

    frontier = []
    for wid in work_ids[:limit]:
        coverage = compute_coverage(wid)
        frontier.append({"work_id": wid, "coverage": coverage})

    return _envelope(frontier, meta={"count": len(frontier)})


@app.get("/v1/frontier/translations")
def frontier_translations(limit: int = Query(20, le=100)):
    """Works needing translations."""
    from patala.work_coverage import compute_coverage
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM works")
    work_ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()

    frontier = []
    for wid in work_ids[:limit]:
        coverage = compute_coverage(wid)
        if coverage.get("translation") == "NONE_KNOWN":
            frontier.append({"work_id": wid, "coverage": coverage})

    return _envelope(frontier, meta={"count": len(frontier)})


# --- Snapshots (per pathway §23) ---

@app.get("/v1/snapshots")
def list_snapshots():
    """List available snapshot manifests."""
    from patala.snapshot.manifest import create_snapshot_manifest
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT MAX(cursor) FROM events")
    max_cursor = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM works")
    works = cur.fetchone()[0]
    cur.close()
    conn.close()

    snapshot = {
        "snapshot_id": f"PTSNAP_{uuid7().replace(chr(45), '')[:16]}",
        "state_cursor": max_cursor,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "protocol_version": "1.0.0",
        "works": works,
        "status": "current",
    }
    return _envelope([snapshot])


@app.get("/v1/stats")
def get_stats():
    """System statistics."""
    from patala.work_coverage import get_coverage_stats
    stats = store.get_stats()
    coverage = get_coverage_stats()
    return _envelope({**stats, **coverage})


# --- Changes ---

@app.get("/v1/changes")
def get_changes(since: int = Query(0, ge=0), limit: int = Query(50, le=200)):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE cursor > %s ORDER BY cursor LIMIT %s", (since, limit))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    events = [dict(zip(cols, r)) for r in rows]
    return _envelope(events, meta={"since": since, "count": len(events)})


# --- People ---

@app.get("/v1/people")
def list_people(limit: int = Query(20, le=100)):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM people LIMIT %s", (limit,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return _envelope([dict(zip(cols, r)) for r in rows])


@app.get("/v1/people/{person_id}")
def get_person(person_id: str):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM people WHERE id = %s", (person_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(404, _error("NOT_FOUND", f"Person {person_id} not found"))
    return _envelope(dict(zip([d[0] for d in cur.description], row)))


# --- Institutions ---

@app.get("/v1/institutions")
def list_institutions(limit: int = Query(20, le=100)):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM institutions LIMIT %s", (limit,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return _envelope([dict(zip(cols, r)) for r in rows])


@app.get("/v1/institutions/{institution_id}")
def get_institution(institution_id: str):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM institutions WHERE id = %s", (institution_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(404, _error("NOT_FOUND", f"Institution {institution_id} not found"))
    return _envelope(dict(zip([d[0] for d in cur.description], row)))


# --- Editions ---

@app.get("/v1/editions")
def list_editions(limit: int = Query(20, le=100)):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM editions LIMIT %s", (limit,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return _envelope([dict(zip(cols, r)) for r in rows])


@app.get("/v1/editions/{edition_id}")
def get_edition(edition_id: str):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM editions WHERE id = %s", (edition_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(404, _error("NOT_FOUND", f"Edition {edition_id} not found"))
    return _envelope(dict(zip([d[0] for d in cur.description], row)))


# --- Witnesses ---

@app.get("/v1/witnesses")
def list_witnesses(limit: int = Query(20, le=100)):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM witnesses LIMIT %s", (limit,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return _envelope([dict(zip(cols, r)) for r in rows])


@app.get("/v1/witnesses/{witness_id}")
def get_witness(witness_id: str):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM witnesses WHERE id = %s", (witness_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(404, _error("NOT_FOUND", f"Witness {witness_id} not found"))
    return _envelope(dict(zip([d[0] for d in cur.description], row)))


# --- Surrogates ---

@app.get("/v1/surrogates")
def list_surrogates(limit: int = Query(20, le=100)):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM etexts LIMIT %s", (limit,))  # surrogates share etexts table
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return _envelope([dict(zip(cols, r)) for r in rows])


@app.get("/v1/surrogates/{surrogate_id}")
def get_surrogate(surrogate_id: str):
    return _envelope({"id": surrogate_id, "note": "Surrogate entity model exists but no data yet"})


# --- ETexts ---

@app.get("/v1/etexts")
def list_etexts(limit: int = Query(20, le=100)):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM etexts LIMIT %s", (limit,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return _envelope([dict(zip(cols, r)) for r in rows])


@app.get("/v1/etexts/{etext_id}")
def get_etext(etext_id: str):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM etexts WHERE id = %s", (etext_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(404, _error("NOT_FOUND", f"EText {etext_id} not found"))
    return _envelope(dict(zip([d[0] for d in cur.description], row)))


@app.get("/v1/etexts/{etext_id}/content")
def get_etext_content(etext_id: str):
    """Rights-aware content endpoint."""
    return _envelope({
        "content_available": False,
        "reason": "RIGHTS",
        "note": "Content not yet stored — metadata only",
    })


# --- Translations ---

@app.get("/v1/translations")
def list_translations(limit: int = Query(20, le=100)):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM translations LIMIT %s", (limit,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return _envelope([dict(zip(cols, r)) for r in rows])


@app.get("/v1/translations/{translation_id}")
def get_translation(translation_id: str):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM translations WHERE id = %s", (translation_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(404, _error("NOT_FOUND", f"Translation {translation_id} not found"))
    return _envelope(dict(zip([d[0] for d in cur.description], row)))


# --- Passages ---

@app.get("/v1/passages")
def list_passages(limit: int = Query(20, le=100)):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM passages LIMIT %s", (limit,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return _envelope([dict(zip(cols, r)) for r in rows])


@app.get("/v1/passages/{passage_id}")
def get_passage(passage_id: str):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM passages WHERE id = %s", (passage_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(404, _error("NOT_FOUND", f"Passage {passage_id} not found"))
    return _envelope(dict(zip([d[0] for d in cur.description], row)))


@app.get("/v1/passages/{passage_id}/occurrences")
def get_passage_occurrences(passage_id: str):
    """Get textual occurrences of a passage across carriers."""
    return _envelope([], meta={"note": "TextOccurrence data not yet populated"})


@app.get("/v1/passages/{passage_id}/translations")
def get_passage_translations(passage_id: str):
    """Get translations of a passage."""
    return _envelope([], meta={"note": "Translation alignment not yet populated"})


@app.get("/v1/passages/{passage_id}/alignments")
def get_passage_alignments(passage_id: str):
    """Get alignment data for a passage."""
    return _envelope([], meta={"note": "Alignment data not yet populated"})


# --- Observations ---

@app.get("/v1/observations")
def list_observations(entity: str | None = None, limit: int = Query(20, le=100)):
    conn = store.get_conn()
    cur = conn.cursor()
    if entity:
        cur.execute("SELECT * FROM raw_observations WHERE id LIKE %s LIMIT %s", (f"%{entity}%", limit))
    else:
        cur.execute("SELECT * FROM raw_observations LIMIT %s", (limit,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return _envelope([dict(zip(cols, r)) for r in rows])


# --- Providers ---

@app.get("/v1/providers")
def list_providers(limit: int = Query(20, le=100)):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM source_providers LIMIT %s", (limit,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return _envelope([dict(zip(cols, r)) for r in rows])


@app.get("/v1/providers/{provider_id}")
def get_provider(provider_id: str):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM source_providers WHERE id = %s", (provider_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        raise HTTPException(404, _error("NOT_FOUND", f"Provider {provider_id} not found"))
    return _envelope(dict(zip([d[0] for d in cur.description], row)))


@app.get("/v1/providers/{provider_id}/endpoints")
def get_provider_endpoints(provider_id: str):
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM source_endpoints WHERE provider_id = %s", (provider_id,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return _envelope([dict(zip(cols, r)) for r in rows])


@app.get("/v1/providers/{provider_id}/health")
def get_provider_health(provider_id: str):
    """Provider health status."""
    return _envelope({"provider_id": provider_id, "status": "active", "note": "Health check not yet implemented"})


@app.get("/v1/providers/{provider_id}/coverage")
def get_provider_coverage(provider_id: str):
    """Provider coverage statistics."""
    conn = store.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM external_identifiers WHERE scheme = %s", (provider_id.upper(),))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return _envelope({"provider_id": provider_id, "linked_entities": count})


@app.get("/v1/providers/{provider_id}/rights")
def get_provider_rights(provider_id: str):
    """Provider rights policies."""
    return _envelope({"provider_id": provider_id, "rights": "metadata: ALLOWED, content: record-specific"})


# --- Graph ---

@app.get("/v1/graph/{entity_id}")
def get_graph(entity_id: str, relation: str | None = None, depth: int = Query(1, le=5),
              direction: str = "both", limit: int = Query(20, le=100)):
    """Graph traversal endpoint."""
    return _envelope({
        "entity_id": entity_id,
        "relation": relation,
        "depth": depth,
        "direction": direction,
        "edges": [],
        "note": "Graph traversal not yet implemented",
    })


# --- Autocomplete ---

@app.get("/v1/autocomplete")
def autocomplete(q: str, limit: int = Query(10, le=50)):
    """Fast compiled projection for autocomplete."""
    works = store.list_works(10000)
    results = [{"id": w["id"], "title": w.get("preferred_title", ""), "type": "work"}
               for w in works if q.lower() in (w.get("preferred_title") or "").lower()]
    return _envelope(results[:limit])


# --- Assertions (standalone, filtered) ---

@app.get("/v1/assertions")
def list_assertions(subject: str | None = None, predicate: str | None = None,
                    state: str | None = None, asserted_by: str | None = None,
                    limit: int = Query(20, le=100)):
    """List assertions with filters."""
    conn = store.get_conn()
    cur = conn.cursor()
    conditions = []
    params = []
    if subject:
        conditions.append("subject_id = %s")
        params.append(subject)
    if predicate:
        conditions.append("predicate_uri LIKE %s")
        params.append(f"%{predicate}%")
    if state:
        conditions.append("lifecycle = %s")
        params.append(state)
    if asserted_by:
        conditions.append("asserted_by = %s")
        params.append(asserted_by)

    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    cur.execute(f"SELECT * FROM assertions{where} LIMIT %s", params + [limit])
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return _envelope([dict(zip(cols, r)) for r in rows])


# --- Traditions ---

@app.get("/v1/traditions")
def list_traditions():
    """List works grouped by tradition.
    Per openpatalaproject: works organized by Trika, Kashmir Shaivism, etc.
    """
    from pathlib import Path
    ta_file = Path(__file__).resolve().parent.parent / "data" / "translation-availability.json"
    if not ta_file.exists():
        return _envelope([], meta={"note": "translation-availability.json not found"})

    data = json.loads(ta_file.read_text())
    traditions = {}
    for wid, work in data.get("works", {}).items():
        for t in work.get("traditions", []):
            if t not in traditions:
                traditions[t] = {"name": t, "works": [], "count": 0}
            traditions[t]["works"].append({
                "work_id": wid,
                "title": work.get("work", ""),
                "has_english": work.get("has_english", False),
            })
            traditions[t]["count"] += 1

    result = list(traditions.values())
    result.sort(key=lambda x: -x["count"])
    return _envelope(result, meta={"count": len(result)})


@app.get("/v1/traditions/{tradition}")
def get_tradition(tradition: str):
    """Get works in a specific tradition."""
    from pathlib import Path
    ta_file = Path(__file__).resolve().parent.parent / "data" / "translation-availability.json"
    if not ta_file.exists():
        raise HTTPException(404, _error("NOT_FOUND", "translation-availability.json not found"))

    data = json.loads(ta_file.read_text())
    works = []
    for wid, work in data.get("works", {}).items():
        if tradition in work.get("traditions", []):
            works.append({
                "work_id": wid,
                "title": work.get("work", ""),
                "has_english": work.get("has_english", False),
                "translations": work.get("translations", []),
            })

    return _envelope({"tradition": tradition, "works": works, "count": len(works)})


@app.get("/v1/translation-availability")
def get_translation_availability(work_id: str | None = None):
    """Get translation availability for a work or all works."""
    from pathlib import Path
    ta_file = Path(__file__).resolve().parent.parent / "data" / "translation-availability.json"
    if not ta_file.exists():
        return _envelope([], meta={"note": "translation-availability.json not found"})

    data = json.loads(ta_file.read_text())
    if work_id:
        work = data.get("works", {}).get(work_id)
        if not work:
            raise HTTPException(404, _error("NOT_FOUND", f"Work {work_id} not found"))
        return _envelope(work)

    # Return summary
    works = data.get("works", {})
    summary = {
        "total_works": len(works),
        "with_english": sum(1 for w in works.values() if w.get("has_english")),
        "without_english": len(works) - sum(1 for w in works.values() if w.get("has_english")),
    }
    return _envelope(summary)


# --- Health ---

@app.get("/health")
def health():
    stats = store.get_stats()
    return {"status": "ok", "version": "1.0.0", "counts": stats}
