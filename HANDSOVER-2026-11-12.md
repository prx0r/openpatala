# OpenPāṭala bibliography/MCP handover

*2026-11-12. Status note for consolidating the OpenPāṭala, Svatantrya, and
Sanskrit Help MCP work. This records observed state; it is not a deployment
receipt.*

## Source branch

- Repository: `prx0r/openpatala`
- Branch: `codex/tantra-bibliography-mcp-api-2026-11-11`
- Pull request: https://github.com/prx0r/openpatala/pull/2
- Last pushed commit at note creation: `9361316dc771cb2f9ee0b878109aad7c948870ff`
- PR state: open; no GitHub Actions runs or status checks were reported for the
  head commit.

## What this branch adds

- Canonical bibliography facets and filtered REST/MCP search for recorded work
  type, tradition, author, identifier scheme, linked source provider, language,
  editions, and translations.
- Search results resolve linked evidence uses and external-ID observations to
  source URLs, providers, observation dates, and recorded rights fields. Missing
  links remain explicitly unresolved.
- MCP compatibility `search` now returns canonical source-aware summaries;
  `resolve` reports exact identity matches separately from substring
  candidates.
- `get_bibliography_dossier` combines the full REST work bundle with the
  source-aware bibliography record.
- Direct names after deployment: `openpatala__bibliography_facets`,
  `openpatala__search_bibliography`, and
  `openpatala__get_bibliography_dossier`. Nested child names use
  `openpatala_mcp__`.

## Tests and limits

- `git diff --check`: passed.
- AST parse of `patala/mcp_server.py`: passed.
- Stubbed MCP wrapper smoke check: passed 12 assertions covering title/alias/
  catalogue-ID resolution, ambiguous/candidate/no-match states, compatibility
  search fields, and dossier composition.
- `python3 check.py --status`: red in this workspace. Conformance lacks
  `rfc8785`; the MCP SDK import is unavailable; the seeded-DB gate lacks
  `psycopg2`. API import and the checked-in evidence-bundle gate passed.
- The SQL was not exercised against OpenPāṭala's PostgreSQL database, and the
  new child tools were not called on the live gateway.

## Live MCP observations

- The live estate index names `https://mcp.sanskrit.help/mcp` as the canonical
  Streamable HTTP endpoint and records bearer authentication, 198 tools, and
  7 servers. The index still describes OpenPāṭala with the older
  `resolve/search/get_bundle` tool set and its bibliography recipe uses the
  older names.
- `https://mcp.sanskrit.help/health` returned HTTP 200 with `ok 7 servers`.
- An unauthenticated `tools/list` request to the canonical endpoint returned
  HTTP 401, as the index says it should. This ChatGPT session had no callable
  `openpatala__*`, `openpatala_mcp__*`, or estate `workspace__*` tools, so it
  could not make an authenticated child-tool call.
- The separate Svatantrya Sanskrit ChatGPT connector responded to Scholar-list
  and wheel-harness calls. It is working, but it does not expose OpenPāṭala.
- `https://mcp.svatantrya.net/mcp` accepted the route but the proper
  Streamable HTTP initialize request was blocked by Cloudflare 1010
  (`browser_signature_banned`). The response said not to retry. This does not
  establish whether that hostname works for an approved client.

## Deployment state and next actions

- The source PR remains open. This repository has no automatic deployment
  workflow; merging alone does not update the live child checkout.
- The estate operations notes identify the live child path as
  `/root/openpatala/patala/mcp_server.py`, spawned by the Sanskrit Help gateway.
  The host checkout must be updated before the new tools can be discovered.
- Deployment access was not available in the ChatGPT session that produced
  this note: no authenticated estate workspace tools or SSH route were exposed.
  Do not place the shared MCP bearer in this repository, a plugin manifest, or
  chat text.
- After the live checkout is updated, verify the authenticated `tools/list`
  includes the three bibliography tools; call `get_health`, `bibliography_facets`,
  and a bounded `search_bibliography` query; inspect source URLs/rights fields;
  then update the generated estate index, MCP registry/catalog, and plugin
  recipe to the deployed names.
