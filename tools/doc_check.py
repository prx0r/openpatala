#!/usr/bin/env python3
"""doc_check.py — openpatala documentation gate.

  python3 tools/doc_check.py [--root REPO] [--all-warns]

Reads data/docs.json. For each registered doc: exists; header `*Status: TIER*`
matches; dated tiers carry a YYYY-MM-DD; every claim's doc number equals its
live value (psql/argv/file source); every relative markdown link resolves;
geometry nodes/edges resolve. FAIL = drift/missing/mislabel. WARN (capped) =
unregistered live-looking number in a CANONICAL doc. DB claims SKIP loudly when
the box DB is unreachable (CI has none).

Exit 0 + "docs: SHARP" iff zero FAIL.
"""
from __future__ import annotations
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DB_ENV = {"PGHOST": "127.0.0.1", "PGUSER": "patala", "PGDATABASE": "openpatala",
          "PGCONNECT_TIMEOUT": "5"}
WARN_PATS = [
    re.compile(r"\b\d{2,5}\s+(?:works|assertions|passages|editions|etexts|"
               r"translations|people|witnesses|events|ext_ids|tools|tests)\b"),
    re.compile(r"(?<!\d)\d{1,5}/\d{1,5}(?!\d)"),
]


def db_up():
    try:
        p = subprocess.run(["psql", "-tA", "-c", "SELECT 1"], capture_output=True,
                           text=True, timeout=8,
                           env={**os.environ, **DB_ENV,
                                "PGPASSWORD": os.environ.get("PGPASSWORD", "patala")})
        return p.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def run(argv, timeout, env=None):
    try:
        e = dict(os.environ)
        if env:
            e.update(env)
        p = subprocess.run([str(a) for a in argv], cwd=str(REPO),
                           capture_output=True, text=True, timeout=timeout, env=e)
        return p, None
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, str(e)


def check_claim(doc, claim, text, box_db, fails, warns, skips):
    cid, pat, src = claim["id"], claim["pattern"], claim.get("source", {})
    m = re.search(pat, text)
    if not m:
        (skips if claim.get("optional") else fails).append(
            f"{doc}:{cid} " + ("pattern absent (optional)" if claim.get("optional")
                               else f"pattern not found: {pat[:70]}"))
        return
    doc_num = (m.group(1) if m.lastindex else m.group(0)).strip()
    live = None
    if "psql" in src:
        if not box_db:
            skips.append(f"{doc}:{cid} skipped: no box DB")
            return
        p, err = run(["psql", "-tA", "-c", src["psql"]], src.get("timeout", 30),
                     {**DB_ENV, "PGPASSWORD": os.environ.get("PGPASSWORD", "patala")})
        if p is None or p.returncode != 0:
            fails.append(f"{doc}:{cid} psql failed: {(p.stderr if p else err)[:150]}")
            return
        sm = re.search(src["pattern"], p.stdout, re.MULTILINE)
        live = sm.group(1) if (sm and sm.lastindex) else (sm.group(0) if sm else None)
    elif "argv" in src:
        p, err = run(src["argv"], src.get("timeout", 120))
        if p is None or p.returncode != 0:
            fails.append(f"{doc}:{cid} cmd failed: {(p.stderr if p else err)[:150]}")
            return
        sm = re.search(src["pattern"], p.stdout + p.stderr, re.MULTILINE)
        live = sm.group(1) if (sm and sm.lastindex) else (sm.group(0) if sm else None)
    elif "file" in src:
        try:
            data = (REPO / src["file"]).read_text(encoding="utf-8")
        except OSError as e:
            fails.append(f"{doc}:{cid} file unreadable: {e}")
            return
        sm = re.search(src["pattern"], data, re.MULTILINE)
        live = sm.group(1) if (sm and sm.lastindex) else (sm.group(0) if sm else None)
    else:
        fails.append(f"{doc}:{cid} unknown source")
        return
    if live is None:
        fails.append(f"{doc}:{cid} live value not found")
    elif str(doc_num) != str(live).strip():
        fails.append(f"{doc}:{cid} DRIFT doc={doc_num!r} live={live.strip()!r}")


def main() -> int:
    root = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else REPO
    show_all = "--all-warns" in sys.argv
    reg = json.loads((root / "data" / "docs.json").read_text(encoding="utf-8"))
    docs = reg["docs"]
    box_db = db_up()
    fails, warns, skips, checked = [], [], [], 0
    on_disk = {p.name for p in root.glob("*.md")}
    for f in sorted(on_disk):
        if f not in docs:
            fails.append(f"unregistered doc: {f} (register, move, or delete)")
    for name, spec in docs.items():
        p = root / name
        if not p.is_file():
            fails.append(f"registered but missing: {name}")
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        head = "\n".join(text.split("\n")[:15])
        m = re.search(r"\*Status:\s*([A-Z_]+)", head)
        if not m or m.group(1) != spec["status"]:
            fails.append(f"{name}: header status {m.group(1) if m else None!r} != registry {spec['status']!r}")
            continue
        if spec["status"] in ("CANONICAL", "HISTORICAL", "SUPERSEDED"):
            if not (re.search(r"\d{4}-\d{2}-\d{2}", head) or re.search(r"\d{4}-\d{2}-\d{2}", name)):
                fails.append(f"{name}: {spec['status']} requires a date")
        for claim in spec.get("claims", []):
            check_claim(name, claim, text, box_db, fails, warns, skips)
            checked += 1
        if spec["status"] == "CANONICAL":
            allows = [re.compile(a) for a in spec.get("allow_stale", [])]
            for wp in WARN_PATS:
                for wm in wp.finditer(text):
                    ls = text.rfind("\n", 0, wm.start()) + 1
                    le = text.find("\n", wm.end()); le = len(text) if le == -1 else le
                    pn = text.rfind("\n", 0, max(0, ls - 1)); nn = text.find("\n", le + 1)
                    window = text[pn + 1:(len(text) if nn == -1 else (text.find("\n", nn + 1) if text.find("\n", nn + 1) != -1 else len(text)))]
                    if re.search(r"\d{4}-\d{2}-\d{2}", window):
                        continue
                    ctx = text[max(0, wm.start() - 50):wm.end() + 20].replace("\n", " ")
                    if not any(a.search(ctx) for a in allows):
                        warns.append(f"{name}: unregistered live-looking number {wm.group(0)!r} (…{ctx.strip()[:80]}…)")
        for lm in re.finditer(r"\[[^\]]*\]\(([^)#\s][^)\s]*)\)", text):
            tgt = lm.group(1).split("#", 1)[0]
            if not tgt or tgt.startswith(("http://", "https://", "mailto:")) or "@" in tgt:
                continue
            if not ((root / tgt).exists() or (p.parent / tgt).exists()):
                fails.append(f"{name}: dead link → {tgt}")
    try:
        geo = json.loads((root / "data" / "docs-geometry.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        fails.append(f"geometry unreadable: {e}"); geo = {"nodes": [], "edges": []}
    ids = set()
    for n in geo.get("nodes", []):
        ids.add(n["id"])
        k = n.get("kind")
        if k in ("doc", "code", "data"):
            if not (root / n["id"]).is_file():
                fails.append(f"geometry: {k} node missing: {n['id']}")
        elif k == "repo":
            if not os.path.isdir(f"/root/{n['id']}"):
                skips.append(f"geometry: repo absent (skipped): {n['id']}")
        else:
            fails.append(f"geometry: unknown node kind {k!r}")
    for e in geo.get("edges", []):
        for end in (e.get("from"), e.get("to")):
            if end not in ids and end not in docs:
                fails.append(f"geometry: edge endpoint unknown: {end}")
    print(f"checked {len(docs)} docs, {checked} claims: {len(fails)} FAIL, {len(warns)} warn, {len(skips)} skip")
    for s in skips:
        print("  SKIP:", s)
    for w in (warns if show_all else warns[:10]):
        print("  WARN:", w)
    if not show_all and len(warns) > 10:
        print(f"  … {len(warns) - 10} more warnings (--all-warns)")
    for f in fails:
        print("  FAIL:", f)
    print("docs: " + ("DRIFT" if fails else "SHARP"))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
