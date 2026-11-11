#!/usr/bin/env python3
"""patala/db/store.py — Postgres store for all entities.

Production-grade: writes to Postgres, reads from Postgres.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import unicodedata
from typing import Any

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://patala:patala@127.0.0.1:5432/openpatala")


def _response_sha256(payload: dict) -> str:
    """Hash a stable UTF-8 JSON representation of a read response."""
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_conn():
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    return conn


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# --- Works ---

def insert_work(work_id: str, preferred_title: str, work_type: str = "TEXT",
                external_ids: list | None = None, created_at: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO works (id, preferred_title, work_type, external_ids, created_at) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET preferred_title = EXCLUDED.preferred_title",
        (work_id, preferred_title, work_type, json.dumps(external_ids or []), created_at or _now())
    )
    conn.commit()
    cur.close()
    conn.close()


def get_work(work_id: str) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM works WHERE id = %s", (work_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    return None


def list_works(limit: int = 100) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM works LIMIT %s", (limit,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


def bibliography_facets() -> dict:
    """Return recorded filter values for the canonical bibliography graph."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    cur.execute(
        "SELECT COALESCE(NULLIF(BTRIM(work_type), ''), 'UNKNOWN') AS value, "
        "COUNT(*) AS work_count FROM works GROUP BY 1 "
        "ORDER BY 1"
    )
    work_types = [dict(zip([d[0] for d in cur.description], row))
                  for row in cur.fetchall()]

    cur.execute(
        "SELECT BTRIM(literal) AS value, COUNT(DISTINCT subject_id) AS work_count "
        "FROM assertions WHERE lifecycle = 'ACTIVE' "
        "AND predicate_uri ILIKE %s AND NULLIF(BTRIM(literal), '') IS NOT NULL "
        "GROUP BY BTRIM(literal) ORDER BY 1",
        ("%TRADITION%",),
    )
    traditions = [dict(zip([d[0] for d in cur.description], row))
                  for row in cur.fetchall()]

    cur.execute(
        "SELECT COALESCE(NULLIF(BTRIM(p.preferred_name), ''), "
        "NULLIF(BTRIM(a.literal), '')) AS value, "
        "COUNT(DISTINCT a.subject_id) AS work_count "
        "FROM assertions a LEFT JOIN people p ON p.id = a.object_id "
        "WHERE a.lifecycle = 'ACTIVE' AND a.predicate_uri ILIKE %s "
        "AND COALESCE(NULLIF(BTRIM(p.preferred_name), ''), "
        "NULLIF(BTRIM(a.literal), '')) IS NOT NULL "
        "GROUP BY 1 ORDER BY 1",
        ("%AUTHOR%",),
    )
    authors = [dict(zip([d[0] for d in cur.description], row))
               for row in cur.fetchall()]

    cur.execute(
        "SELECT LOWER(BTRIM(scheme)) AS value, "
        "COUNT(DISTINCT entity_id) AS work_count FROM external_identifiers "
        "WHERE NULLIF(BTRIM(scheme), '') IS NOT NULL "
        "GROUP BY LOWER(BTRIM(scheme)) ORDER BY value"
    )
    identifier_schemes = [dict(zip([d[0] for d in cur.description], row))
                          for row in cur.fetchall()]

    cur.execute(
        "SELECT LOWER(BTRIM(target_language)) AS value, "
        "COUNT(DISTINCT work_id) AS work_count FROM translations "
        "WHERE NULLIF(BTRIM(target_language), '') IS NOT NULL "
        "GROUP BY LOWER(BTRIM(target_language)) ORDER BY value"
    )
    translation_languages = [dict(zip([d[0] for d in cur.description], row))
                             for row in cur.fetchall()]

    cur.execute("SELECT COALESCE(MAX(cursor), 0) FROM events")
    state_cursor = cur.fetchone()[0]
    cur.close()
    conn.close()
    response = {
        "result_schema": "patala.bibliography-facets/1",
        "catalogue": "OpenPāṭala canonical bibliography graph",
        "state_cursor": state_cursor,
        "classification_policy": (
            "Only recorded work types and active tradition assertions are listed; "
            "titles are not automatically classified."
        ),
        "facets": {
            "work_types": work_types,
            "traditions": traditions,
            "authors": authors,
            "identifier_schemes": identifier_schemes,
            "translation_languages": translation_languages,
        },
    }
    response["response_sha256"] = _response_sha256(response)
    return response


def search_bibliography(
    q: str | None = None,
    work_type: str | None = None,
    tradition: str | None = None,
    author: str | None = None,
    identifier_scheme: str | None = None,
    language: str | None = None,
    has_edition: bool | None = None,
    has_translation: bool | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Search canonical works and return source-aware bibliographic summaries.

    Search normalizes the query to Unicode NFC, then uses case-insensitive
    literal substring matching on preferred titles, title/alias assertions,
    canonical IDs, and recorded external identifiers. Facets are exact recorded
    values; they do not infer a tradition from title words.
    """
    query = unicodedata.normalize("NFC", (q or "").strip())
    work_type = unicodedata.normalize("NFC", (work_type or "").strip())
    tradition = unicodedata.normalize("NFC", (tradition or "").strip())
    author = unicodedata.normalize("NFC", (author or "").strip())
    identifier_scheme = (identifier_scheme or "").strip().lower()
    language = (language or "").strip().lower()

    if not any((query, work_type, tradition, author, identifier_scheme, language,
                has_edition is not None, has_translation is not None)):
        raise ValueError("Provide q or at least one bibliography filter.")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")
    if not 0 <= offset <= 100000:
        raise ValueError("offset must be between 0 and 100000.")

    conditions: list[str] = []
    params: list[Any] = []
    if query:
        conditions.append(
            "(POSITION(LOWER(%s) IN LOWER(w.preferred_title)) > 0 "
            "OR POSITION(LOWER(%s) IN LOWER(w.id)) > 0 "
            "OR POSITION(LOWER(%s) IN LOWER(w.external_ids::text)) > 0 "
            "OR EXISTS (SELECT 1 FROM external_identifiers x "
            "WHERE x.entity_id = w.id AND "
            "(POSITION(LOWER(%s) IN LOWER(x.scheme)) > 0 "
            "OR POSITION(LOWER(%s) IN LOWER(x.value)) > 0)) "
            "OR EXISTS (SELECT 1 FROM assertions ta WHERE ta.subject_id = w.id "
            "AND ta.lifecycle = 'ACTIVE' "
            "AND (ta.predicate_uri ILIKE '%TITLE%' OR ta.predicate_uri ILIKE '%ALIAS%') "
            "AND POSITION(LOWER(%s) IN LOWER(COALESCE(ta.literal, ''))) > 0))"
        )
        params.extend([query] * 6)
    if work_type:
        conditions.append("LOWER(BTRIM(w.work_type)) = LOWER(BTRIM(%s))")
        params.append(work_type)
    if tradition:
        conditions.append(
            "EXISTS (SELECT 1 FROM assertions a WHERE a.subject_id = w.id "
            "AND a.lifecycle = 'ACTIVE' AND a.predicate_uri ILIKE %s "
            "AND POSITION(LOWER(%s) IN LOWER(COALESCE(a.literal, ''))) > 0)"
        )
        params.extend(["%TRADITION%", tradition])
    if author:
        conditions.append(
            "EXISTS (SELECT 1 FROM assertions a "
            "LEFT JOIN people p ON p.id = a.object_id "
            "WHERE a.subject_id = w.id AND a.lifecycle = 'ACTIVE' "
            "AND a.predicate_uri ILIKE %s AND ("
            "POSITION(LOWER(%s) IN LOWER(COALESCE(a.literal, ''))) > 0 "
            "OR POSITION(LOWER(%s) IN LOWER(COALESCE(p.preferred_name, ''))) > 0 "
            "OR POSITION(LOWER(%s) IN LOWER(COALESCE(a.object_id, ''))) > 0))"
        )
        params.extend(["%AUTHOR%", author, author, author])
    if identifier_scheme:
        conditions.append(
            "EXISTS (SELECT 1 FROM external_identifiers x "
            "WHERE x.entity_id = w.id AND LOWER(BTRIM(x.scheme)) = LOWER(%s))"
        )
        params.append(identifier_scheme)
    if language:
        conditions.append(
            "EXISTS (SELECT 1 FROM translations t WHERE t.work_id = w.id "
            "AND LOWER(BTRIM(t.target_language)) = LOWER(%s))"
        )
        params.append(language)
    if has_edition is not None:
        conditions.append(
            ("EXISTS" if has_edition else "NOT EXISTS")
            + " (SELECT 1 FROM editions e WHERE e.work_id = w.id)"
        )
    if has_translation is not None:
        conditions.append(
            ("EXISTS" if has_translation else "NOT EXISTS")
            + " (SELECT 1 FROM translations t WHERE t.work_id = w.id)"
        )

    where_sql = " WHERE " + " AND ".join(conditions)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
    cur.execute("SELECT COUNT(*) FROM works w" + where_sql, params)
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT w.id, w.preferred_title, w.work_type, w.current_title_assertion_id, "
        "w.external_ids, "
        "(SELECT COUNT(*) FROM editions e WHERE e.work_id = w.id) AS edition_count, "
        "(SELECT COUNT(*) FROM translations t WHERE t.work_id = w.id) AS translation_count, "
        "(SELECT COUNT(*) FROM witnesses wi WHERE wi.work_id = w.id) AS witness_count, "
        "(SELECT COUNT(*) FROM etexts et WHERE et.work_id = w.id) AS etext_count, "
        "COALESCE((SELECT ARRAY_AGG(DISTINCT LOWER(t.target_language) "
        "ORDER BY LOWER(t.target_language)) FROM translations t WHERE t.work_id = w.id), "
        "ARRAY[]::text[]) AS translation_languages "
        "FROM works w" + where_sql +
        " ORDER BY CASE WHEN %s <> '' AND LOWER(w.preferred_title) = LOWER(%s) "
        "THEN 0 WHEN %s <> '' AND POSITION(LOWER(%s) IN LOWER(w.preferred_title)) = 1 "
        "THEN 1 ELSE 2 END, LOWER(w.preferred_title), w.id LIMIT %s OFFSET %s",
        params + [query, query, query, query, limit, offset],
    )
    rows = cur.fetchall()
    work_columns = [d[0] for d in cur.description]
    works = [dict(zip(work_columns, row)) for row in rows]
    ids = [work["id"] for work in works]

    identifiers_by_work: dict[str, list[dict]] = {work_id: [] for work_id in ids}
    traditions_by_work: dict[str, list[dict]] = {work_id: [] for work_id in ids}
    titles_by_work: dict[str, list[dict]] = {work_id: [] for work_id in ids}
    authors_by_work: dict[str, list[dict]] = {work_id: [] for work_id in ids}
    if ids:
        cur.execute(
            "SELECT entity_id, scheme, value, source_observation_id, "
            "relation_confidence FROM external_identifiers "
            "WHERE entity_id = ANY(%s) ORDER BY entity_id, scheme, value",
            (ids,),
        )
        columns = [d[0] for d in cur.description]
        for row in cur.fetchall():
            identifier = dict(zip(columns, row))
            identifiers_by_work[identifier.pop("entity_id")].append(identifier)

        cur.execute(
            "SELECT id, subject_id, predicate_uri, literal, epistemic_mode, "
            "evidence_use_ids, asserted_by, lifecycle, created_from_event, recorded_at "
            "FROM assertions WHERE subject_id = ANY(%s) AND lifecycle = 'ACTIVE' "
            "AND predicate_uri ILIKE %s ORDER BY subject_id, predicate_uri, id",
            (ids, "%TRADITION%"),
        )
        columns = [d[0] for d in cur.description]
        for row in cur.fetchall():
            assertion = dict(zip(columns, row))
            for key, value in assertion.items():
                if hasattr(value, "isoformat"):
                    assertion[key] = value.isoformat()
            traditions_by_work[assertion.pop("subject_id")].append(assertion)

        cur.execute(
            "SELECT id, subject_id, predicate_uri, literal, epistemic_mode, "
            "evidence_use_ids, asserted_by, lifecycle, created_from_event, recorded_at "
            "FROM assertions WHERE subject_id = ANY(%s) AND lifecycle = 'ACTIVE' "
            "AND (predicate_uri ILIKE '%TITLE%' OR predicate_uri ILIKE '%ALIAS%') "
            "ORDER BY subject_id, predicate_uri, id",
            (ids,),
        )
        columns = [d[0] for d in cur.description]
        for row in cur.fetchall():
            assertion = dict(zip(columns, row))
            for key, value in assertion.items():
                if hasattr(value, "isoformat"):
                    assertion[key] = value.isoformat()
            titles_by_work[assertion.pop("subject_id")].append(assertion)

        cur.execute(
            "SELECT a.id, a.subject_id, a.object_id, p.preferred_name AS person_name, "
            "a.predicate_uri, a.literal, a.epistemic_mode, a.evidence_use_ids, "
            "a.asserted_by, a.lifecycle, a.created_from_event, a.recorded_at "
            "FROM assertions a LEFT JOIN people p ON p.id = a.object_id "
            "WHERE a.subject_id = ANY(%s) AND a.lifecycle = 'ACTIVE' "
            "AND a.predicate_uri ILIKE %s ORDER BY a.subject_id, a.predicate_uri, a.id",
            (ids, "%AUTHOR%"),
        )
        columns = [d[0] for d in cur.description]
        for row in cur.fetchall():
            assertion = dict(zip(columns, row))
            for key, value in assertion.items():
                if hasattr(value, "isoformat"):
                    assertion[key] = value.isoformat()
            authors_by_work[assertion.pop("subject_id")].append(assertion)

    cur.execute("SELECT COALESCE(MAX(cursor), 0) FROM events")
    state_cursor = cur.fetchone()[0]
    cur.close()
    conn.close()

    results = []
    for work in works:
        result = {
            "work_id": work["id"],
            "dossier_path": f"/v1/bundle/{work['id']}",
            "preferred_title": work["preferred_title"],
            "work_type": work["work_type"],
            "current_title_assertion_id": work["current_title_assertion_id"],
            "embedded_external_ids": work["external_ids"],
            "catalogue_identifiers": identifiers_by_work[work["id"]],
            "title_assertions": titles_by_work[work["id"]],
            "tradition_assertions": traditions_by_work[work["id"]],
            "authorship_assertions": authors_by_work[work["id"]],
            "edition_count": work["edition_count"],
            "translation_count": work["translation_count"],
            "translation_languages": work["translation_languages"],
            "witness_count": work["witness_count"],
            "etext_count": work["etext_count"],
        }
        if query:
            matched_by = []
            if query.casefold() in (work["preferred_title"] or "").casefold():
                matched_by.append("preferred_title")
            if query.casefold() in work["id"].casefold():
                matched_by.append("canonical_work_id")
            if query.casefold() in json.dumps(work["external_ids"], ensure_ascii=False).casefold():
                matched_by.append("embedded_external_identifier")
            if any(query.casefold() in (x["scheme"] or "").casefold()
                   or query.casefold() in (x["value"] or "").casefold()
                   for x in identifiers_by_work[work["id"]]):
                matched_by.append("catalogue_identifier")
            if any(query.casefold() in (x["literal"] or "").casefold()
                   for x in titles_by_work[work["id"]]):
                matched_by.append("title_assertion")
            result["matched_by"] = matched_by
        results.append(result)

    response = {
        "result_schema": "patala.bibliography-search/1",
        "catalogue": "OpenPāṭala canonical bibliography graph",
        "state_cursor": state_cursor,
        "filters": {
            "q": query or None,
            "work_type": work_type or None,
            "tradition": tradition or None,
            "author": author or None,
            "identifier_scheme": identifier_scheme or None,
            "language": language or None,
            "has_edition": has_edition,
            "has_translation": has_translation,
        },
        "search_semantics": (
            "q is NFC-normalized and matched as a case-insensitive literal "
            "substring on preferred titles, active title/alias assertions, "
            "canonical IDs, and external identifiers; work type and language "
            "are exact; tradition and author filters use active recorded assertions."
        ),
        "total": total,
        "limit": limit,
        "offset": offset,
        "next_offset": offset + len(results) if offset + len(results) < total else None,
        "results": results,
    }
    response["response_sha256"] = _response_sha256(response)
    return response


# --- Assertions ---

def insert_assertion(assertion_id: str, subject_id: str, predicate_uri: str,
                     literal: str = "", asserted_by: str = "PROVIDER",
                     lifecycle: str = "ACTIVE", created_from_event: str = "",
                     valid_from: str = "", valid_until: str = "",
                     schema_uri: str = "https://patala.org/schemas/v2/assertion.json"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO assertions (id, subject_id, predicate_uri, literal, epistemic_mode, asserted_by, recorded_at, lifecycle, created_from_event, valid_from, valid_until, schema_uri) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        (assertion_id, subject_id, predicate_uri, literal, "observed", asserted_by,
         _now(), lifecycle, created_from_event, valid_from or None, valid_until or None, schema_uri)
    )
    conn.commit()
    cur.close()
    conn.close()


def list_assertions(subject_id: str | None = None, limit: int = 100) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    if subject_id:
        cur.execute("SELECT * FROM assertions WHERE subject_id = %s LIMIT %s", (subject_id, limit))
    else:
        cur.execute("SELECT * FROM assertions LIMIT %s", (limit,))
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


# --- External Identifiers ---

def insert_external_id(ext_id: str, entity_id: str, scheme: str, value: str,
                       source_observation_id: str = "", confidence: float = 1.0):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO external_identifiers (id, entity_id, scheme, value, source_observation_id, relation_confidence, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        (ext_id, entity_id, scheme, value, source_observation_id, confidence, _now())
    )
    conn.commit()
    cur.close()
    conn.close()


def list_external_ids(entity_id: str | None = None) -> list[dict]:
    conn = get_conn()
    cur = conn.cursor()
    if entity_id:
        cur.execute("SELECT * FROM external_identifiers WHERE entity_id = %s", (entity_id,))
    else:
        cur.execute("SELECT * FROM external_identifiers LIMIT 100")
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return [dict(zip(cols, r)) for r in rows]


# --- Events ---

def insert_event(event_id: str, event_type: str, entity_ids: list,
                 payload: dict, recorded_at: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (event_id, event_type, entity_ids, schema_uri, payload, payload_digest, recorded_at) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (event_id) DO NOTHING",
        (event_id, event_type, entity_ids,
         "https://patala.org/schemas/v2/event-envelope.json",
         json.dumps(payload), json.dumps({}), recorded_at or _now())
    )
    conn.commit()
    cur.close()
    conn.close()


def count_events() -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM events")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count


# --- Source Providers ---

def insert_provider(provider_id: str, slug: str, name: str, provider_type: str,
                    status: str = "ACTIVE"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO source_providers (id, slug, name, provider_type, status, discovered_at) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        (provider_id, slug, name, provider_type, status, _now())
    )
    conn.commit()
    cur.close()
    conn.close()


# --- Artifacts ---

def insert_artifact(artifact_id: str, digests: dict, media_type: str,
                    byte_length: int, storage_uri: str = "",
                    availability_state: str = "PRESENT"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO artifacts (id, digests, media_type, byte_length, storage_uri, availability_state, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        (artifact_id, json.dumps(digests), media_type, byte_length, storage_uri, availability_state, _now())
    )
    conn.commit()
    cur.close()
    conn.close()


def get_artifact(artifact_id: str) -> dict | None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM artifacts WHERE id = %s", (artifact_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    return None


# --- Raw Observations ---

def insert_raw_observation(obs_id: str, provider_id: str, endpoint_id: str,
                           requested_uri: str, payload_artifact_id: str,
                           rights_assessment_id: str, status: str = "FETCHED",
                           observed_at: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO raw_observations (id, provider_id, endpoint_id, requested_uri, payload_artifact_id, rights_assessment_id, observed_at, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        (obs_id, provider_id, endpoint_id, requested_uri, payload_artifact_id,
         rights_assessment_id, observed_at or _now(), status)
    )
    conn.commit()
    cur.close()
    conn.close()


# --- Entity Merges ---

def insert_merge(merge_id: str, from_ids: list, into_id: str, evidence: str,
                 event_id: str, performed_by: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO identity_merges (id, from_ids, into_id, evidence, event_id, performed_by) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        (merge_id, from_ids, into_id, evidence, event_id, performed_by)
    )
    # Update lifecycle of merged entities
    for fid in from_ids:
        cur.execute("UPDATE works SET schema_uri = schema_uri WHERE id = %s", (fid,))
    conn.commit()
    cur.close()
    conn.close()


def find_merge_target(entity_id: str) -> str | None:
    """Follow merge chains: if entity was merged into another, return the target."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT into_id FROM identity_merges WHERE %s = ANY(from_ids)", (entity_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]
    return None


# --- Entity Splits ---

def insert_split(split_id: str, old_id: str, new_ids: list, evidence: str,
                 event_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO identity_splits (id, old_id, new_ids, allocation_evidence, event_id) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
        (split_id, old_ids, new_ids, evidence, event_id)
    )
    conn.commit()
    cur.close()
    conn.close()


def find_split(entity_id: str) -> dict | None:
    """Check if entity was split. Returns split info or None."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM identity_splits WHERE old_id = %s", (entity_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))
    return None


# --- Rebuild from events ---

def rebuild_from_events():
    """Destroy all projections and rebuild from event stream."""
    conn = get_conn()
    cur = conn.cursor()

    # Clear projection tables
    for table in ["works", "people", "institutions", "editions", "witnesses",
                   "etexts", "translations", "passages", "assertions",
                   "external_identifiers", "identity_assertions"]:
        cur.execute(f"TRUNCATE {table} CASCADE")

    # Read all events
    cur.execute("SELECT * FROM events ORDER BY cursor")
    events = cur.fetchall()
    cols = [d[0] for d in cur.description]

    rebuilt = 0
    for event_row in events:
        event = dict(zip(cols, event_row))
        event_type = event.get("event_type", "")
        payload = event.get("payload", {})
        if isinstance(payload, str):
            payload = json.loads(payload)

        if event_type == "EntityCreated":
            entity_id = event.get("entity_ids", [None])[0]
            if entity_id and not entity_id.startswith("PTCND_"):
                title = payload.get("title", "")
                cur.execute(
                    "INSERT INTO works (id, preferred_title, schema_uri, created_at) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
                    (entity_id, title, "https://patala.org/schemas/atlas/work/1.0.0", event.get("recorded_at", ""))
                )
                rebuilt += 1

    conn.commit()
    cur.close()
    conn.close()
    return rebuilt


# --- Stats ---

def get_stats() -> dict:
    conn = get_conn()
    cur = conn.cursor()
    stats = {}
    for table in ["works", "people", "institutions", "editions", "witnesses",
                   "etexts", "translations", "assertions", "external_identifiers", "events"]:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        stats[table] = cur.fetchone()[0]
    cur.close()
    conn.close()
    return stats
