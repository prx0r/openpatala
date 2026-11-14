#!/usr/bin/env python3
"""test_doc_check.py — the openpatala doc gate is itself gated.

Hermetic fixtures (temp dirs): a well-formed tree passes; each failure mode
fails. DB-backed psql claims skip without a DB. Mirrors trika-x's test.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE.parent / "tools" / "doc_check.py"

GOOD = "# A doc — thing (2026-11-14)\n*Status: CANONICAL. real.*\n\nlive 7 works.\n"
REG = {"A.md": {"status": "CANONICAL", "note": "x"}}


def build(root, docs, reg, geo=None):
    (root / "data").mkdir(parents=True)
    (root / "data" / "docs.json").write_text(json.dumps({"format": "openpatala-docs-registry/1", "docs": reg}))
    (root / "data" / "docs-geometry.json").write_text(json.dumps(geo or {"format": "x", "nodes": [], "edges": []}))
    for n, t in docs.items():
        (root / n).write_text(t)


def run(root):
    return subprocess.run([sys.executable, str(CHECKER), "--root", str(root)],
                          capture_output=True, text=True, timeout=120)


class T(unittest.TestCase):
    def test_good_passes(self):
        with tempfile.TemporaryDirectory() as t:
            build(Path(t), {"A.md": GOOD}, REG)
            r = run(Path(t)); self.assertEqual(r.returncode, 0, r.stdout); self.assertIn("SHARP", r.stdout)

    def test_unregistered_fails(self):
        with tempfile.TemporaryDirectory() as t:
            build(Path(t), {"A.md": GOOD, "B.md": "# B\n*Status: REFERENCE. x.*\n"}, REG)
            r = run(Path(t)); self.assertNotEqual(r.returncode, 0); self.assertIn("unregistered doc: B.md", r.stdout)

    def test_status_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as t:
            build(Path(t), {"A.md": GOOD.replace("CANONICAL", "REFERENCE")}, REG)
            r = run(Path(t)); self.assertNotEqual(r.returncode, 0); self.assertIn("header status", r.stdout)

    def test_missing_date_fails(self):
        with tempfile.TemporaryDirectory() as t:
            build(Path(t), {"A.md": GOOD.replace(" (2026-11-14)", "")}, {"A.md": {"status": "CANONICAL", "note": "x"}})
            r = run(Path(t)); self.assertNotEqual(r.returncode, 0); self.assertIn("requires a date", r.stdout)

    def test_claim_drift_fails(self):
        with tempfile.TemporaryDirectory() as t:
            reg = {"A.md": {"status": "CANONICAL", "note": "x", "claims": [
                {"id": "n", "pattern": r"(\d+) works", "source": {"argv": [sys.executable, "-c", "print(999)"], "pattern": r"(\d+)"}}]}}
            build(Path(t), {"A.md": GOOD}, reg)
            r = run(Path(t)); self.assertNotEqual(r.returncode, 0); self.assertIn("DRIFT", r.stdout)

    def test_dead_link_fails(self):
        with tempfile.TemporaryDirectory() as t:
            build(Path(t), {"A.md": GOOD + "\n[gone](nope.md)\n"}, REG)
            r = run(Path(t)); self.assertNotEqual(r.returncode, 0); self.assertIn("dead link", r.stdout)

    def test_geometry_missing_node_fails(self):
        with tempfile.TemporaryDirectory() as t:
            geo = {"format": "x", "nodes": [{"id": "data/missing.json", "kind": "data"}], "edges": []}
            build(Path(t), {"A.md": GOOD}, REG, geo)
            r = run(Path(t)); self.assertNotEqual(r.returncode, 0); self.assertIn("node missing", r.stdout)

    def test_dated_line_suppresses_warn(self):
        with tempfile.TemporaryDirectory() as t:
            doc = ("# A — x (2026-11-14)\n*Status: CANONICAL. real.*\n\n"
                   "2026-08-17 baseline: 1099 works (archived snapshot).\n")
            build(Path(t), {"A.md": doc}, REG)
            r = run(Path(t)); self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
