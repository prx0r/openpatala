#!/usr/bin/env python3
"""patala/mcp_server.py — MCP server for OpenPāṭala (agent interface).

Exposes Pāṭala tools to AI agents via MCP protocol.
"Tools don't become truth. Their outputs become observations." — newbuild
"""
from __future__ import annotations

import json
import sys
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


if server:
    @server.tool()
    def resolve(q: str, type: str = "work") -> dict:
        """Resolve a Sanskrit work name to a canonical entity."""
        works = _db().list_works(10000)
        matches = [w for w in works if (w.get("preferred_title") or "").lower() == q.lower()]
        if len(matches) == 1:
            return {"status": "EXACT", "entity": matches[0]}
        elif len(matches) > 1:
            return {"status": "AMBIGUOUS", "count": len(matches)}
        return {"status": "NONE", "query": q}

    @server.tool()
    def get_bundle(entity_id: str) -> dict:
        """Get full dossier for a work (assertions, external IDs, provenance)."""
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
    def search(q: str, limit: int = 20) -> dict:
        """Legacy title-only lookup; use search_bibliography for source-aware filters."""
        works = _db().list_works(10000)
        results = [{"id": w["id"], "title": w.get("preferred_title", ""), "type": "work"}
                   for w in works if q.lower() in (w.get("preferred_title") or "").lower()]
        return {"results": results[:limit], "total": len(results)}

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
