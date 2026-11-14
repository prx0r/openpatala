# OPENPATALA × TRIKA-X — the identity→proof join

*Status: CANONICAL. How the two repos compose, verified 2026-11-14. This is the
seam that makes essays checkable: openpatala answers "which work/passage", trika-x
answers "does it check out", and the trace bundle is where the two meet.*

## The division (one line each)

- **openpatala** = identity. Work / Edition / EText / Passage. It never proves.
- **translation-work** = evidence. Layers T1→L4 per chunk. It never proves.
- **trika-x** = proof + trace. Lean theorems, evidence rows, trace bundles. It
  joins identity to evidence to proof.
- **svread** = surface. Reader, evidence view, publish gate.

## The exact join (verified by running it)

```
chunk locator (e.g. tsa08-p03)
   │  trika-x bridge_resolve.py --db
   ▼
openpatala rows: work_id, edition, etext, passage.citation_value
   │  recorded in the trace bundle's `identity` hop
   ▼
trika-trace/1 bundle  (source bytes → layers → proofs → theorems → essays)
   │  verdict COMPLETE / PARTIAL; identity rows present
   ▼
svread emit_verify.py  (re-hashes exact bytes; refuses on any mismatch)
```

## What trika-x reads from openpatala (and what it must never do)

- `bridge_resolve.py` maps a `chunk:<locator>` → the DB's work/edition/etext
  rows keyed by the passage `citation_value`. The trace compiler writes those
  rows into `identity`.
- It records `witness: UNPINNED` and `status: UNRESOLVED` where the DB has no
  row — it never invents an edition or witness.
- trika-x does **not** write to the openpatala DB, mint IDs, or alter rows.
  openpatala is the root; trika-x is a read-mostly consumer.

## What the join buys an agent

Ask openpatala `resolve` → get `work_id`. Ask trika-x `formal__trace` with
`work_id` + locator → get a bundle whose `identity` hop *is* the openpatala
rows. So a single chain proves: "this passage belongs to this work (identity),
these are its bytes (evidence), this is what structurally holds (proof)." If
`resolve` returns `CANDIDATES`/`NONE`, the trace cannot be COMPLETE — the
identity hop is UNRESOLVED, stated not hidden.

## Live check (both sides, same work)

```sh
# identity (openpatala MCP)
python3 -c "import asyncio;from patala.mcp_server import server as s;print(asyncio.run(s.call_tool('resolve',{'q':'tantrasara'})).content[0].text[:120])"
# proof (trika-x trace, federated)
curl -s -X POST https://formal.svatantrya.net/mcp -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' -H 'MCP-Protocol-Version: 2025-06-18' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"formal__trace","arguments":{"work":"tantrasara-a08","target":"tsa08-p03"}}}'
# → verdict COMPLETE; identity hop carries the same work_id
```

## Known boundaries (honest)

- `witnesses` = 0 corpus-wide; the join proves identity + structure, never a
  manuscript. The trace's source hop says `UNPINNED`.
- Editions are CANDIDATE strings (dossier/GRETIL), not collations.
- 479 Muktabodha works are identity shells (rights NULL, no assertions) — they
  resolve, but downstream claims about them stay draft-only until enriched.
