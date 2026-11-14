#!/usr/bin/env python3
"""mcp_acceptance_run.py — an agent proves the openpatala identity surface.

Runs tools/mcp_acceptance.json: each step calls a live MCP tool (through the
in-process `server`) and asserts shape, the EXACT-vs-NONE distinction, the
response hash, and fail-closed behavior. Skips loudly (never passes) when the
box DB is unreachable.

  python3 tools/mcp_acceptance_run.py [--suite PATH] [--json]
"""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEFAULT = HERE / "mcp_acceptance.json"


def db_up():
    try:
        import psycopg2
        psycopg2.connect(dbname="openpatala", user="patala", password="patala",
                         host="127.0.0.1", connect_timeout=3).close()
        return True
    except Exception:  # noqa: BLE001
        return False


def get(obj, path):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
        if cur is None:
            return None
    return cur


def check(a, ctx):
    op, actual = a["op"], a.get("actual")
    val = get(ctx, actual) if actual != "call" else ctx.get("call")
    if op == "exists":
        ok = (val is not None) == a.get("expect_exists", True)
        return ok, f"{actual}={'present' if val is not None else 'MISSING'}"
    exp = a.get("expect")
    if op == "equals":
        return val == exp, f"{actual}={val!r} (want {exp!r})"
    if op == "gte":
        return (isinstance(val, (int, float)) and val >= exp), f"{actual}={val} (want >= {exp})"
    if op == "regex":
        return (isinstance(val, str) and re.search(exp, val) is not None), f"{actual} matches /{exp}/"
    return False, f"unknown op {op}"


async def run_step(server, step):
    req = step["request"]
    r = await server.call_tool(req["tool"], req.get("args", {}))
    txt = ""
    if hasattr(r, "content") and r.content:
        txt = getattr(r.content[0], "text", "") or ""
    try:
        call = json.loads(txt)
    except ValueError:
        call = {"_raw": txt[:200]}
    ctx = {"call": call}
    fails = []
    for a in step.get("assert", []):
        ok, detail = check(a, ctx)
        if not ok:
            fails.append(detail)
    return (not fails), fails


async def main_async(suite_path, as_json):
    if not db_up():
        print("SKIP: box DB unreachable — acceptance not run (never a pass)")
        return 0
    from patala.mcp_server import server
    spec = json.loads(suite_path.read_text(encoding="utf-8"))
    results = []
    for step in spec["steps"]:
        try:
            ok, fails = await run_step(server, step)
        except Exception as e:  # noqa: BLE001
            ok, fails = False, [f"EXCEPTION {type(e).__name__}: {str(e)[:150]}"]
        results.append({"id": step["id"], "pass": ok, "detail": fails})
    passed = sum(1 for r in results if r["pass"])
    if as_json:
        print(json.dumps({"passed": passed, "total": len(results), "results": results}, indent=1))
    else:
        for r in results:
            print(("PASS " if r["pass"] else "FAIL ") + r["id"]
                  + ("" if r["pass"] else "  :: " + " | ".join(r["detail"])))
        print(f"\n{passed}/{len(results)} checks passed")
    return 0 if passed == len(results) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default=str(DEFAULT))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    return asyncio.run(main_async(Path(a.suite), a.json))


if __name__ == "__main__":
    raise SystemExit(main())
