#!/usr/bin/env python3
"""patala/mcp_server.py — MCP server for OpenPāṭala (agent interface).

Exposes Pāṭala tools to AI agents via MCP protocol.
"Tools don't become truth. Their outputs become observations." — newbuild
"""
from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from patala.db import store

try:
    from mcp.server.mcpserver import MCPServer
    server = MCPServer(name="openpatala")
except ImportError:
    # Fallback: define server as None if MCP SDK not installed
    server = None
    print("MCP SDK not installed. Install with: pip install mcp")


def _db():
    return store


_TRIKA = Path("/root/trika-x/formal-trika")
_SVREAD_DATA = Path("/root/svread/data")


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _evidence_locators() -> set:
    ev = _load_json(_TRIKA / "EVIDENCE.json", {})
    out = set()
    for entry in (ev.get("entries") or {}).values():
        for chunk in entry.get("chunks") or []:
            if chunk.get("locator"):
                out.add(chunk["locator"])
    return out


def _trace_rows(work_id: str) -> list:
    idx = _load_json(_TRIKA / "data" / "traces" / "index.json", {})
    rows = []
    for entry in idx.get("entries") or []:
        if entry.get("work") != work_id:
            continue
        rows.append({
            "target": entry.get("target"),
            "verdict": entry.get("verdict"),
            "theorems": entry.get("theorems") or [],
            "gaps": entry.get("gaps") or [],
            "caveats": entry.get("caveats") or [],
            "sha256": entry.get("sha256"),
        })
    return rows


def _plain(value):
    """Coerce DB row values (datetime etc.) to JSON-safe primitives."""
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _layer_state(work_id: str) -> dict:
    idx = _load_json(_SVREAD_DATA / "layers-index.json", {})
    rows = idx.get("works") or []
    if isinstance(rows, dict):
        row = rows.get(work_id)
    else:
        row = next((r for r in rows
                    if work_id in (r.get("work"), r.get("site_bundle"))), None)
    if row is None:
        return {"state": "NOT_INDEXED",
                "note": "work is absent from the layer index; layer presence "
                        "is UNKNOWN here, not denied"}
    return {"state": "INDEXED", "registry_status": row.get("registry_status"),
            "gold": row.get("gold"), "songs": row.get("songs")}


def _has_exact_identifier(value, needle: str) -> bool:
    """Match a legacy embedded identifier without treating surrounding JSON as a hit."""
    if isinstance(value, dict):
        scheme = str(value.get("scheme") or "").strip().casefold()
        for key in ("value", "id", "identifier"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                candidate = candidate.strip().casefold()
                if candidate == needle or (scheme and f"{scheme}:{candidate}" == needle):
                    return True
        return any(_has_exact_identifier(item, needle) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_has_exact_identifier(item, needle) for item in value)
    return isinstance(value, str) and value.strip().casefold() == needle


if server:
    @server.tool()
    def resolve(q: str, type: str = "work") -> dict:
        """Resolve a work by preferred title, alias, canonical ID, or catalogue ID.

        Exact matches are distinguished from substring candidates. Candidate
        records include their source-aware bibliography summaries.
        """
        query = unicodedata.normalize("NFC", (q or "").strip())
        if not query:
            return {"status": "NONE", "query": q}
        try:
            page = _db().search_bibliography(q=query, limit=100)
        except ValueError as exc:
            return {"status": "INVALID_QUERY", "error": str(exc)}

        records = page["results"]
        needle = query.casefold()
        exact_matches = []
        for record in records:
            exact_on = []
            if needle == (record.get("preferred_title") or "").strip().casefold():
                exact_on.append("preferred_title")
            if needle == (record.get("work_id") or "").strip().casefold():
                exact_on.append("canonical_work_id")
            if _has_exact_identifier(record.get("embedded_external_ids"), needle):
                exact_on.append("embedded_external_identifier")
            if any(needle == (item.get("literal") or "").strip().casefold()
                   for item in record.get("title_assertions", [])):
                exact_on.append("title_assertion")
            for identifier in record.get("catalogue_identifiers", []):
                value = (identifier.get("value") or "").strip().casefold()
                scheme = (identifier.get("scheme") or "").strip().casefold()
                if needle == value or (scheme and needle == f"{scheme}:{value}"):
                    exact_on.append("catalogue_identifier")
                    break
            if exact_on:
                exact_matches.append((record, exact_on))

        if len(exact_matches) == 1:
            record, exact_on = exact_matches[0]
            return {
                "status": "EXACT",
                "entity": {
                    "id": record["work_id"],
                    "preferred_title": record["preferred_title"],
                    "work_type": record["work_type"],
                },
                "record": record,
                "matched_exactly_by": exact_on,
                "response_sha256": page["response_sha256"],
            }
        if exact_matches:
            return {
                "status": "AMBIGUOUS",
                "count": len(exact_matches),
                "candidates": [
                    {"record": record, "matched_exactly_by": exact_on}
                    for record, exact_on in exact_matches
                ],
                "response_sha256": page["response_sha256"],
            }
        if records:
            return {
                "status": "CANDIDATES",
                "count": page["total"],
                "candidates": records,
                "next_offset": page["next_offset"],
                "response_sha256": page["response_sha256"],
            }
        return {"status": "NONE", "query": query, "response_sha256": page["response_sha256"]}

    @server.tool()
    def get_bundle(entity_id: str) -> dict:
        """Get the legacy compact dossier (assertions and external identifiers).

        Use get_bibliography_dossier for the complete REST bundle plus linked
        source observations, URLs, and recorded rights metadata.
        """
        work = _db().get_work(entity_id)
        if not work:
            return {"error": f"Entity {entity_id} not found"}
        assertions = _db().list_assertions(subject_id=entity_id)
        ext_ids = _db().list_external_ids(entity_id=entity_id)
        return {
            "entity": work,
            "assertions": assertions,
            "external_ids": ext_ids,
        }

    @server.tool()
    def status(work_id: str) -> dict:
        """One-call status object for a work: identity, rights, witnesses,
        passages, formal coverage, trace verdicts, review state, provenance.

        This is NORTHSTAR turn 1. Absences are stated, never omitted:
        witnesses 0 -> UNPINNED, rights null -> NULL, review -> UNREVIEWED.
        Counts carry denominators. Nothing here is a translation or a reading.
        """
        try:
            from fastapi import HTTPException
            from patala.api import get_bundle as get_api_bundle

            response = get_api_bundle(work_id)
        except HTTPException as exc:
            if exc.status_code == 404:
                return {"status": "NOT_FOUND", "work_id": work_id}
            raise
        dossier = response.get("data", response)
        page = _db().search_bibliography(q=work_id, limit=1)
        record = next((item for item in page["results"]
                       if item.get("work_id") == work_id), None)
        if record is None:
            return {"status": "NOT_FOUND_IN_BIBLIOGRAPHY",
                    "work_id": work_id,
                    "note": "dossier exists but no bibliography row matched; "
                            "do not invent counts"}

        locators = [p.get("citation_value") for p in (dossier.get("passages") or [])
                    if p.get("citation_scheme") == "chunk-locator"
                    and p.get("citation_value")]
        covered_all = _evidence_locators()
        covered = [loc for loc in locators if loc in covered_all]
        gaps = [loc for loc in locators if loc not in covered_all]
        traces = _trace_rows(work_id)
        verdicts: dict = {}
        blocked: list = []
        for row in traces:
            verdicts[row["verdict"]] = verdicts.get(row["verdict"], 0) + 1
            for caveat in row["caveats"]:
                if "BLOCKED" in caveat:
                    blocked.append({"target": row["target"], "caveat": caveat})

        rights = sorted({r for r in
                         [(e or {}).get("rights_policy_id")
                          for key in ("editions", "etexts", "translations")
                          for e in (dossier.get(key) or [])] if r})
        witnesses = dossier.get("witnesses") or []

        return {
            "format": "svatantrya.status/1",
            "status": "OK",
            "work_id": work_id,
            "identity": {
                "preferred_title": record.get("preferred_title"),
                "work_type": record.get("work_type"),
                "entity": _plain(dossier.get("entity")),
                "completeness": _plain(dossier.get("completeness")),
            },
            "rights": {
                "policies": rights,
                "state": "SET" if rights else "NULL",
                "note": ("null rights = not publishable" if not rights
                         else "rights recorded per edition/etext/translation"),
            },
            "witnesses": {
                "count": len(witnesses),
                "state": "UNPINNED" if not witnesses else "RECORDED",
                "note": ("no manuscript witness; editions are candidate "
                         "strings until a witness is verified"
                         if not witnesses else ""),
            },
            "counts": {
                "editions": len(dossier.get("editions") or []),
                "etexts": len(dossier.get("etexts") or []),
                "translations": len(dossier.get("translations") or []),
                "passages": len(locators),
            },
            "passages": {"locators": locators},
            "formal": {
                "covered": len(covered),
                "total": len(locators),
                "coverage": (f"{len(covered)}/{len(locators)}"
                             if locators else "unknown"),
                "gaps": gaps,
                "note": "coverage counts passages with an EVIDENCE registry "
                        "reference; registry refs are not entailments",
            },
            "traces": {
                "count": len(traces),
                "verdicts": verdicts,
                "with_blocked_gate": len(blocked),
                "blocked_gates": blocked,
                "note": ("COMPLETE means every applicable hop resolved; it "
                         "does not mean a gate passed. blocked_gates lists "
                         "the gates that did not."),
                "rows": traces,
            },
            "layers": _layer_state(work_id),
            "review_state": "UNREVIEWED",
            "review_note": "no human sign-off is bound to this work; "
                           "UNREVIEWED is a state, not a verdict",
            "provenance": {
                "bibliography_response_sha256":
                    page["response_sha256"],
                "sources": [
                    "openpatala dossier (DB)",
                    "/root/trika-x/formal-trika/EVIDENCE.json",
                    "/root/trika-x/formal-trika/data/traces/index.json",
                    "/root/svread/data/layers-index.json",
                ],
            },
        }

    @server.tool()
    def get_bibliography_dossier(work_id: str) -> dict:
        """Get the complete work dossier with linked source and rights records.

        Returns editions, translations, witnesses, e-texts, passages,
        provenance, completeness, and the source-aware bibliography record.
        """
        try:
            from fastapi import HTTPException
            from patala.api import get_bundle as get_api_bundle

            response = get_api_bundle(work_id)
        except HTTPException as exc:
            if exc.status_code == 404:
                return {"status": "NOT_FOUND", "work_id": work_id}
            raise

        dossier = response.get("data", response)
        page = _db().search_bibliography(q=work_id, limit=1)
        record = next((item for item in page["results"]
                       if item.get("work_id") == work_id), None)
        if not record:
            return {
                "status": "PARTIAL",
                "work_id": work_id,
                "dossier": dossier,
                "source_record_status": "NOT_FOUND_IN_BIBLIOGRAPHY_SEARCH",
                "bibliography_response_sha256": page["response_sha256"],
            }
        return {
            "status": "OK",
            "work_id": work_id,
            "dossier": dossier,
            "bibliography_record": record,
            "bibliography_state_cursor": page["state_cursor"],
            "bibliography_response_sha256": page["response_sha256"],
        }

    @server.tool()
    def search(q: str, limit: int = 20) -> dict:
        """Compatibility search returning source-aware bibliography summaries.

        Use search_bibliography when you need filters or pagination.
        """
        try:
            page = _db().search_bibliography(q=q, limit=limit)
        except ValueError as exc:
            return {"status": "INVALID_QUERY", "error": str(exc)}
        results = [
            {
                "id": record["work_id"],
                "title": record["preferred_title"],
                "type": "work",
                **record,
            }
            for record in page["results"]
        ]
        return {
            "status": "OK",
            "results": results,
            "total": page["total"],
            "result_schema": page["result_schema"],
            "state_cursor": page["state_cursor"],
            "next_offset": page["next_offset"],
            "response_sha256": page["response_sha256"],
        }

    @server.tool()
    def bibliography_facets() -> dict:
        """List recorded types, traditions, authors, ID schemes, source providers, and languages.

        Facets reflect explicit database records only; titles are not auto-classified.
        """
        return {"status": "OK", **_db().bibliography_facets()}

    @server.tool()
    def search_bibliography(
        q: str = "",
        work_type: str = "",
        tradition: str = "",
        author: str = "",
        identifier_scheme: str = "",
        source_provider: str = "",
        language: str = "",
        has_edition: bool | None = None,
        has_translation: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Search by title/ID, author, type, tradition, catalogue ID scheme, source provider, or translation.

        Returns stable work IDs, title/alias assertions, edition/translation
        counts, languages, catalogue identifiers, source URLs, rights metadata,
        and active tradition/authorship assertions with evidence links.
        Classification comes only from recorded work types and assertions; a
        title keyword is not proof.
        Use bibliography_facets first to discover the exact available filters,
        then get_bundle for a full dossier.
        """
        try:
            return {"status": "OK", **_db().search_bibliography(
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
            )}
        except ValueError as exc:
            return {"status": "INVALID_FILTERS", "error": str(exc)}

    @server.tool()
    def get_frontier(limit: int = 20) -> dict:
        """List works needing translations or sources."""
        stats = _db().get_stats()
        works = _db().list_works(limit)
        return {"stats": stats, "works": works}

    @server.tool()
    def get_health() -> dict:
        """Check system health."""
        return _db().get_stats()


def main():
    if server is None:
        print("MCP SDK not installed. Run: pip install mcp")
        return
    import anyio
    anyio.run(server.run_stdio_async)


if __name__ == "__main__":
    main()
