# API Overview

The OpenPāṭala API is the primary way to get scholarly data programmatically. It's free and requires no authentication. The API is REST-based and returns JSON.

## Base URL

```
http://127.0.0.1:8801
```

This is the local development default. The live box snapshot in
[`OPENPATALA.md`](../../OPENPATALA.md) uses loopback port `8821`; it is not a
public REST origin.

## Endpoints

### Core entities
- `GET /v1/works` — List/search works
- `GET /v1/works/{id}` — Get a single work
- `GET /v1/people` — List people
- `GET /v1/institutions` — List institutions
- `GET /v1/editions` — List editions
- `GET /v1/witnesses` — List witnesses
- `GET /v1/etexts` — List e-texts
- `GET /v1/translations` — List translations
- `GET /v1/passages` — List passages

### Work subresources
- `GET /v1/works/{id}/assertions` — Get assertions about a work
- `GET /v1/works/{id}/editions` — Get editions of a work
- `GET /v1/works/{id}/translations` — Get translations of a work
- `GET /v1/works/{id}/completeness` — Get completeness status
- `GET /v1/bundle/{id}` — Get full dossier (the killer endpoint)

### Resolution and search
- `GET /v1/resolve?q=...` — Resolve a work name (EXACT/AMBIGUOUS/NONE)
- `GET /v1/search?q=...` — Search for works
- `GET /v1/autocomplete?q=...` — Fast autocomplete
- `GET /v1/bibliography/facets` — Recorded work types, active tradition/author assertions, identifier schemes, and translation languages
- `GET /v1/bibliography/search` — Filter canonical records by title/ID, author, work type, tradition, identifier scheme, edition, or translation

Use `/v1/bibliography/search` for agent and research workflows. `/v1/search`
remains a lightweight, title-only compatibility endpoint.

### Frontier and changes
- `GET /v1/frontier/translations` — Works needing translations
- `GET /v1/changes?since=<cursor>` — Event feed

### Providers
- `GET /v1/providers` — List data providers
- `GET /v1/providers/{id}` — Get provider details

### Other
- `GET /v1/assertions?subject=...&predicate=...` — Filtered assertions
- `GET /v1/observations?entity=...` — Raw observations
- `GET /health` — System health

## Response format

All endpoints return a standard envelope:

```json
{
  "meta": {
    "count": 10,
    "schema_version": "1.0"
  },
  "results": [...]
}
```

For single entities:

```json
{
  "meta": {
    "schema_version": "1.0"
  },
  "data": { ... }
}
```

Errors:

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Work xyz not found",
    "retryable": false
  }
}
```

## Example: Get a work bundle

```bash
curl http://127.0.0.1:8801/v1/bundle/PTW_00068039f45a7fe5
```

Response:

```json
{
  "meta": { "schema_version": "1.0" },
  "data": {
    "entity": { "id": "PTW_...", "preferred_title": "A Sanskrit-English Dictionary", ... },
    "aliases": [...],
    "external_ids": [...],
    "assertions": { "authorship": [...], "date": [...], "tradition": [...] },
    "editions": [...],
    "translations": [...],
    "witnesses": [...],
    "etexts": [...],
    "passages": [...],
    "provenance": [...],
    "completeness": { "identity": "RESOLVED", "translation": "NONE_KNOWN", ... }
  }
}
```

## Example: Resolve a work

```bash
curl "http://127.0.0.1:8801/v1/resolve?q=Vigrahavyavartani"
```

Response:

```json
{
  "meta": { "schema_version": "1.0" },
  "data": { "status": "EXACT", "entity": { "id": "PTW_...", "preferred_title": "Vigrahavyāvartanī" } }
}
```

## Example: Search for works

```bash
curl "http://127.0.0.1:8801/v1/search?q=sanskrit&limit=5"
```

## Tantra bibliography discovery

Use the facets endpoint first to see the values actually recorded in the
canonical database. The search endpoint accepts `q`, `work_type`, `tradition`,
`author`, `identifier_scheme`, `language`, `has_edition`, and `has_translation`, with `limit` and `offset` for
pagination. Only use taxonomy values shown by the facets response; the example
below returns records only if those labels are actually present. For example:

```bash
curl "http://127.0.0.1:8801/v1/bibliography/facets"
curl "http://127.0.0.1:8801/v1/bibliography/search?work_type=TANTRA&tradition=Trika&limit=20"
```

Search returns stable OpenPāṭala work IDs, title/alias assertions, recorded work
type, external catalogue identifiers, active tradition assertions with their
evidence references, edition/translation/witness/e-text counts, translation
languages, a dossier path, and a `state_cursor` for the database view. `q` is normalized to
Unicode NFC, then matched as a case-insensitive literal substring over
preferred titles, active title/alias assertions, canonical IDs, and external
identifiers. Work type and language filters are exact; tradition filters match
recorded active assertion text, and author filters match active authorship
assertions and linked person names. Nothing is classified as Tantra from its
title alone. At least one search term or filter is required. `response_sha256` hashes
the query, result page, and cursor so a bibliography response can be cited and
compared alongside a saved response. Use `/v1/bundle/{work_id}` for the full dossier and its
provenance.

The existing `/v1/traditions` route reads the older translation-availability
projection. `/v1/bibliography/facets` and `/v1/bibliography/search` read the
canonical database graph; keep those scopes distinct until the older projection
is retired or reconciled.

The MCP server exposes the same read-only path as `bibliography_facets` and
`search_bibliography`. The MCP search tool requires at least one query or filter;
it does not imply that the current catalogue is exhaustive for Tantra.

## Client libraries

Currently no third-party client libraries. Use curl, Python requests, or any HTTP client.

## Rate limits

No rate limits currently. The API is local and designed for agent use.
