# OPENPATALA — what it is, what actually works, what does not

*2026-11-07. Written against the live box. Every claim below was run.*

Openpatala is the **identity layer**: it answers "which work/edition/passage is
this?" Its job is not to translate, render, or publish. Everything downstream
(svread, trika-x traces, factories) cites it as the root.

Repo: `prx0r/openpatala` · checkout `/root/openpatala` · API `127.0.0.1:8821`

## Gate

```sh
cd /root/openpatala && python3 check.py
```

Reports PASS / FAIL / BLOCKED per suite. BLOCKED is never PASS.

Current state (verified 2026-11-07):

| Suite | Status | Meaning |
|---|---|---|
| conformance | BLOCKED | adapter suite finds no items — see "Known blockers" |
| api-import | PASS | FastAPI app imports |
| mcp-server | PASS | MCP server constructs (5 tools) |
| evidence-bundle | PASS | machine evidence present |
| db-seeded | PASS | 1034 works live in Postgres (555 enriched + 479 Muktabodha shells) |
| witnesses | BLOCKED | 0 witnesses corpus-wide (structural) |

## What is real

- **Box DB** (`postgresql://patala:patala@localhost:5432/openpatala`):
  **1034 works** · 909 passages · 581 editions · 566 etexts · 1559 assertions ·
  121 external ids · 121 translations · 20 people · **0 witnesses**.
  Of the 1034, **479 are Muktabodha identity shells** (provider
  `PT_PROVIDER_muktabodha`, loaded 2026-11-11, 0 assertions/translations,
  **rights NULL → not publishable**) — see trika-x
  `docs/log/DB-PROVENANCE-2026-11-14.md`. The 555 enriched works are unchanged.
- **API** on `:8821` — `/health`, `/v1/works`, `/v1/works/{id}`, `/v1/bundle/{id}`.
  Start: `PYTHONPATH=. nohup python3 -m uvicorn patala.api:app --port 8821 --host 127.0.0.1 &`
  (Port note: 8801–8806 are squatted on this box by an unrelated old
  `http.server` fleet.)
- **MCP** — `patala/mcp_server.py`, stdio, 5 tools (resolve, bundle, search,
  frontier, health). Needs the `mcp` package (`pip install mcp`); imports
  `mcp.server.mcpserver.MCPServer` (mcp 2.x).
- **Schema** — `patala/schemas/v2/` 22 JSON schemas for identity/ledger
  plumbing, `migrations/001_create_all_tables.sql` (34 tables).

## Known blockers (recorded, not faked)

1. **Adapters discover nothing** in this checkout (`No items discovered`).
   This is the peer-review finding, not a regression we introduced. Fixing it
   means giving adapters real data or real fetch paths.
2. **Witnesses are 0 everywhere.** A printed edition is not a witness. The
   resolver enforces UNPINNED rather than invent a siglum. Needs manuscript
   records (NGMPP / microfilm eyes).
3. **`patala/schemas/v2/assertion.json` does not describe live rows** — the id
   pattern `^PTASS_`, `predicate_uri` URI format and `asserted_by` enum all
   differ from what the DB holds. The DB de-facto conventions win in practice;
   reconciling the schema is open work.
4. **`translations.schema_uri` points at a nonexistent v2 file** (dangling).
5. **R2 `openpatala.dump` needs PG18**; the PG15-readable dump is
   `patala/openpatala/box-2026-11-06/`.

## Reproduce from scratch

```sh
# schema
su postgres -c "createdb openpatala"
su postgres -c "psql -d openpatala -f migrations/001_create_all_tables.sql"
su postgres -c "psql -d openpatala -f migrations/002_add_missing_tables.sql"
# data, in order (idempotent; loaders live in trika-x)
python3 /root/trika-x/formal-trika/tools/openpatala_seed.py
python3 /root/trika-x/formal-trika/tools/openpatala_ingest.py
python3 /root/trika-x/formal-trika/tools/seed_atlas_biblio.py --apply
python3 /root/trika-x/formal-trika/tools/seed_abhinavagupta.py --apply
python3 check.py
```

## Rules

- Identity is not philological truth. A work ID plus a shared GRETIL string is
  a candidate mapping, never a proven edition or witness.
- **Nothing is "real" because a file exists.** A claim needs a logged,
  reproducible gate.
- Never invent a witness, edition, or DOI. UNPINNED / UNKNOWN are valid states.
