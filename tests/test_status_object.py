#!/usr/bin/env python3
"""test_status_object.py — N2/N3: openpatala__status is one call, loud absences."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import patala.mcp_server as mm  # noqa: E402


class StatusObjectShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = mm.status("tantrasara-a08")

    def test_is_one_call_object(self):
        self.assertEqual(self.out["format"], "svatantrya.status/1")
        self.assertEqual(self.out["work_id"], "tantrasara-a08")

    def test_json_serialisable(self):
        json.dumps(self.out)  # must not raise (no datetime leaks)

    def test_required_sections(self):
        for key in ("identity", "rights", "witnesses", "counts", "passages",
                    "formal", "traces", "layers", "review_state", "provenance",
                    "base_edition"):
            self.assertIn(key, self.out)

    def test_base_edition_is_named_or_loudly_bare(self):
        be = self.out["base_edition"]
        self.assertIn(be.get("state"), ("NAMED", "UNNAMED", "NONE"))
        if be.get("state") == "NONE":
            return
        self.assertTrue(be.get("edition_note") or be.get("title"),
                        "an edition without any name is not a status")
        if be.get("state") == "UNNAMED":
            self.assertIn("bare work id", be.get("note", ""))

    def test_counts_carry_denominators(self):
        formal = self.out["formal"]
        self.assertIn("/", formal["coverage"])
        self.assertEqual(formal["covered"] + len(formal["gaps"]),
                         formal["total"])

    def test_absences_are_loud(self):
        self.assertEqual(self.out["witnesses"]["count"], 0)
        self.assertEqual(self.out["witnesses"]["state"], "UNPINNED")
        self.assertEqual(self.out["review_state"], "UNREVIEWED")
        self.assertIn(self.out["rights"]["state"], ("SET", "NULL"))
        if self.out["rights"]["state"] == "NULL":
            self.assertIn("not publishable", self.out["rights"]["note"])

    def test_trace_complete_does_not_hide_blocked_gate(self):
        traces = self.out["traces"]
        self.assertIn("note", traces)
        self.assertIn("blocked_gates", traces)
        if traces["verdicts"].get("COMPLETE"):
            self.assertGreaterEqual(traces["with_blocked_gate"], 0)


class StatusObjectUnknown(unittest.TestCase):
    def test_missing_work_is_stated_not_invented(self):
        out = mm.status("no-such-work-xyz")
        self.assertIn(out["status"], ("NOT_FOUND",
                                      "NOT_FOUND_IN_BIBLIOGRAPHY"))


if __name__ == "__main__":
    unittest.main()
