# OPENPATALA-FORMAL-SPEC — documentation as a formal system (2026-11-14)
*Status: CANONICAL. This spec (2026-11-14); self-describing.*

`tools/doc_check.py` and the registry in `data/docs.json`, both of which exist
and run. Mirrors the trika-x system so the two repos are legible the same way.*

## The problem

openpatala is the estate's identity root, but its docs describe three different
eras at once: the 2026-08-17 build (1099 works / 247 assertions / 2181 events),
the 2026-11-07 honest state (555 works / 0 witnesses), and the 2026-11-14 state
(1034 works / 1559 assertions / 0 witnesses). Nothing re-checked which was
current. Identity is the one layer where a wrong count poisons everything
downstream.

## The rule (one sentence)

**Every live number a CANONICAL doc asserts is gate-verified against the box
database, or the doc is not CANONICAL.**

## Status tiers (same vocabulary as trika-x)

| Tier | Meaning | Example |
|---|---|---|
| CANONICAL | live truth, gate-verified numbers | OPENPATALA.md, README.md |
| REFERENCE | stable background (rules, schema, conformance) | AGENTS.md, NAVIGATION.md |
| PROPOSED | spec, unbuilt by design | PATALAPATH*.md |
| HISTORICAL | dated snapshot, frozen, never edited | BUILD-NOTES-*, HANDSOVER-* |
| SUPERSEDED | do not build on; names its successor | DEV-PLAN.md, P0-FIX-PLAN.md |
| RECEIPT | dated review/log, append-only | PEER-REVIEW-*.md |

## File format (headers)

First 15 lines carry:

```
# TITLE — one-line what
```

## Registry (`data/docs.json`) and claim kinds

One entry per in-scope root doc. Claim sources, all fail-closed:
- `{"psql": "SELECT count(*) FROM works", "pattern": "one capture group"}` —
  run against the box DB; doc number must equal the live number. Skips loudly
  when the DB is unreachable (CI has none) — never silent.
- `{"argv": [...], "pattern": "..."}` — any command (e.g. MCP tool-list count).
- `{"file": "<repo-relative>", "pattern": "..."}` — a committed file.

Verdict: FAIL on unregistered doc, header/status mismatch, missing date for a
dated tier, claim drift, dead internal link, geometry break. WARN (capped,
`--all-warns`) on unregistered live-looking numbers in CANONICAL docs. Dated
lines are dated claims.

## Geometry (`data/docs-geometry.json`)

Nodes: the estate repos + data/code artifacts. Edges carry `kind`
(`consumes`/`cites`/`feeds`) and the reason each is believed. openpatala is the
identity root: translation-work, trika-x and svread all cite it; it consumes
none of them for identity (it is upstream). The checker verifies every node
path exists and every edge endpoint resolves.

## MCP for agents (the reason this layer exists)

openpatala's whole public value is that other systems can ask "which
work/edition/passage is this?" without owning its data. The MCP server
(`patala/mcp_server.py`) exposes 8 read tools. Their contract is documented in
`MCP-FOR-AGENTS.md` and proven by `tools/mcp_acceptance_run.py` — an agent
runs the suite and gets PASS/FAIL with observed values, the same discipline as
trika-x's ChatGPT acceptance.

## Lifecycle

PROPOSED → DRAFT → VERIFY (`tools/doc_check.py` green) → REVIEW (re-measure if
older than the DB's last ingest) → MERGE → MAINTAIN (corrections are new dated
content, never quiet swaps). A doc whose claims fail is demoted, not patched to
look current.

## What this does NOT do

No LLM prose scoring. No auto-rewrite. No coverage quotas. It checks numbers,
labels, links, geometry, and the MCP contract — the parts a machine can settle.
