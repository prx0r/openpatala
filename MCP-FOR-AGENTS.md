# MCP FOR AGENTS — openpatala identity, callable
*Status: CANONICAL. MCP contract for agents: 8 read tools, schemas, examples, failure modes (2026-11-14).*

other MCP clients) that needs to answer "which work/edition/passage is this?"
and hand a stable identity to the rest of the estate. Measured 2026-11-14.*

openpatala is the **identity root**. It does not translate, formalize, or
render. An agent calls it first, gets a stable `work_id` / passage locator, and
passes that identity downstream — to trika-x's `formal__trace`, to svread's
`scholar__passage_evidence`, to the factories. Without a resolved openpatala
identity, downstream output is draft-only.

## Transport

- **stdio** (local): `python3 patala/mcp_server.py` — 8 tools.
- **Federated** (public): the tools are also exposed inside the svread
  federation at `https://mcp.svatantrya.net/mcp` (prefixed `openpatala__*`) and
  the owner console `https://mcp.sanskrit.help/mcp`. Protocol `2025-06-18`.
- No auth on reads; every tool here is **read-only**.

## The 8 tools (schemas)

| Tool | Args | Returns |
|---|---|---|
| `resolve` | `q` (req), `type="work"` | `EXACT`/`AMBIGUOUS`/`CANDIDATES`/`NONE` + entity + record + `response_sha256` |
| `get_bundle` | `entity_id` (req) | full work dossier (editions, etexts, passages, assertions) |
| `get_bibliography_dossier` | `work_id` (req) | dossier + source-aware bibliography record |
| `search` | `q` (req), `limit=20` | works matching query |
| `bibliography_facets` | — | recorded work types, traditions, identifier schemes, providers, languages |
| `search_bibliography` | `q`, `work_type`, `tradition`, `author`, `identifier_scheme`, `source_provider`, `language`, `has_edition`, `has_translation`, `limit`, `offset` | paginated bibliography results + counts + state cursor + `response_sha256` |
| `get_frontier` | `limit=20` | coverage frontier (what's unbridged/todo) |
| `get_health` | — | box DB counts (works, passages, witnesses, …) |

## The identity contract (what an agent must preserve)

A resolved entity carries `work_id`. Downstream, identity is the pair
**`work_id` + locator** (e.g. `tantrasara-a08` + `tsa08-p03`). When passing to
trika-x/svread, keep both; never substitute a title string for an id. `UNKNOWN`,
`CANDIDATES`, `NONE` are honest states — a candidate is not an edition, and a
title match is not a proof.

## Example: agent resolves, then hands identity to trika-x

```jsonc
// 1. identity (openpatala)
{"name":"resolve","arguments":{"q":"tantrasara"}}
// → {"status":"EXACT","entity":{"id":"tantrasara", ...}, "response_sha256": "..."}
// 2. that work_id + a locator feeds the formal chain (trika-x, federated)
{"name":"formal__trace","arguments":{"work":"tantrasara-a08","target":"tsa08-p03"}}
// → {"verdict":"COMPLETE", "formal":{"theorems":[ ... ]}, "identity":{...openpatala rows...}}
```

The `formal__trace` bundle's `identity` block is openpatala rows for the same
`work_id` — that is the join. If `resolve` returns `CANDIDATES`/`NONE`, the
trace's identity hop records `UNRESOLVED` and the verdict cannot be COMPLETE.

## Failure modes (fail-closed, honest)

- `NONE` / `CANDIDATES` / `AMBIGUOUS` — never guessed into an entity.
- Invalid target id → clean error, never a partial success.
- DB unreachable → the tool errors; it does not return an empty "success".
- `witnesses` is **0 corpus-wide**; `get_health` says so. A printed edition is
  not a witness; the resolver enforces `UNPINNED` rather than invent a siglum.

## Verify the surface yourself (agent-runnable)

```sh
python3 tools/mcp_acceptance_run.py       # 8 checks, PASS/FAIL with values
```

The suite (`tools/mcp_acceptance.json`) exercises every tool with a live call
and asserts shape, the EXACT-vs-NONE distinction, the sha, and the
fail-closed cases. It skips loudly (never passes) without the box DB.

## Federation note (how trika-x uses openpatala)

trika-x's `formation` chain calls openpatala for identity:
`bridge_resolve.py` maps a chunk locator → work/edition/etext rows; the trace
compiler records those rows in the bundle's `identity` hop. So the exact
division is: **openpatala owns identity; trika-x owns proof; translation-work
owns layers; svread owns surface.** None dups another's IDs.
