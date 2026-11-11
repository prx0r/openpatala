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
