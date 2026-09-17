"""reflux.py tests — one test per decision-table row (design §3.7.2, twelve rows) + the write path."""
import argparse
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import reflux  # noqa: E402
import runs  # noqa: E402

GOOD = HERE / "fixtures" / "good-run"


class TestDecisionTable(unittest.TestCase):
    def test_row_1_target_does_not_resolve(self):
        for kind in reflux.KINDS:
            self.assertEqual(reflux.decide(kind, False, True, "delivered"), ("1", "REJECT"))

    def test_row_2_consumed(self):
        self.assertEqual(reflux.decide("consumed", True, False, "delivered"), ("2", "append"))

    def test_row_3_correction_delivered_ledger_key(self):
        self.assertEqual(reflux.decide("correction", True, True, "delivered"), ("3", "invalidate"))

    def test_row_3b_correction_already_invalidated_or_superseded(self):
        self.assertEqual(reflux.decide("correction", True, True, "invalidated"), ("3b", "annotate"))
        self.assertEqual(reflux.decide("correction", True, True, "superseded"), ("3b", "annotate"))

    def test_row_4_correction_background_source(self):
        self.assertEqual(reflux.decide("correction", True, False, "delivered"), ("4", "annotate"))

    def test_row_5_retraction_cited(self):
        self.assertEqual(reflux.decide("retraction", True, True, None), ("5", "invalidate-per-run"))

    def test_row_6_retraction_uncited(self):
        self.assertEqual(reflux.decide("retraction", True, False, None), ("6", "append-empty"))

    def test_row_7_handoff_delivered(self):
        self.assertEqual(reflux.decide("handoff", True, False, "delivered"), ("7", "append"))

    def test_row_7b_handoff_on_invalidated_or_superseded(self):
        self.assertEqual(reflux.decide("handoff", True, False, "invalidated"), ("7b", "annotate"))
        self.assertEqual(reflux.decide("handoff", True, False, "superseded"), ("7b", "annotate"))

    def test_row_8_rerun(self):
        self.assertEqual(reflux.decide("rerun", True, False, "delivered"), ("8", "supersede"))
        self.assertEqual(reflux.decide("rerun", True, False, "invalidated"), ("8", "supersede"))

    def test_row_8b_rerun_on_superseded(self):
        self.assertEqual(reflux.decide("rerun", True, False, "superseded"), ("8b", "annotate"))

    def test_row_9_else(self):
        self.assertEqual(reflux.decide("bogus", True, True, "delivered"), ("9", "REJECT"))


class TestWritePath(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="lse-reflux-"))
        (self.tmp / "literature").mkdir()
        os.environ["LSE_RUN_HOME"] = str(self.tmp / "literature" / "EvidenceRuns")
        os.environ["LSE_RUN_UNFILED"] = str(self.tmp / "unfiled")
        with contextlib.redirect_stdout(io.StringIO()):
            runs.cmd_init(argparse.Namespace())
        self.h = runs.home()
        self.run_id = "20260903_reflux-fixture"
        d = self.h / self.run_id
        shutil.copytree(GOOD, d)
        run = runs.load_run(d)
        run["run"]["id"], run["run"]["home"], run["run"]["state"] = self.run_id, str(self.h), "checked"
        runs.save_run(d, run)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runs.cmd_register(argparse.Namespace(run_dir=str(d))), 0)
        self.d = d
        self.key = runs.load_run(d)["keys"][0]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k in ("LSE_RUN_HOME", "LSE_RUN_UNFILED"):
            os.environ.pop(k, None)

    def size(self):
        return (self.h / "reflux.jsonl").stat().st_size

    def test_forged_run_id_rejected_and_nothing_appended(self):
        before = self.size()
        with self.assertRaises(ValueError):
            reflux.append_event(self.h, reflux.new_event("consumed", "t", run_id="20260903_nope", artifact="x"))
        self.assertEqual(self.size(), before)

    def test_malformed_event_rejected(self):
        before = self.size()
        with self.assertRaises(ValueError):
            reflux.append_event(self.h, {"event_id": "short", "at": "2026", "kind": "consumed", "actor": ""})
        with self.assertRaises(ValueError):   # correction needs evidence
            reflux.append_event(self.h, reflux.new_event("correction", "t", run_id=self.run_id, key=self.key))
        self.assertEqual(self.size(), before)

    def test_consumed_then_correction_invalidates_and_affected_lists_consumer(self):
        ev = reflux.append_event(self.h, reflux.new_event("consumed", "scientific-research-guide", run_id=self.run_id,
                                                          key=self.key, artifact="plasmonic_waveguide.md#7b [Park2022]"))
        self.assertEqual(ev["decision"], "2")
        ev = reflux.append_event(self.h, reflux.new_event("correction", "user", run_id=self.run_id, key=self.key,
                                                          evidence="Table 2 re-read: 22 -> 12 um", note="span misread"))
        self.assertEqual(ev["decision"], "3")
        run = runs.load_run(self.d)
        self.assertEqual(run["run"]["state"], "invalidated")
        self.assertEqual(run["invalidation"]["wasInvalidatedBy"], ev["event_id"])
        self.assertIn("C1", run["invalidation"]["claims"])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            runs.cmd_affected(argparse.Namespace(key=self.key, scan_srg=False, scan_papersurvey=False, json=True))
        res = json.loads(buf.getvalue())
        self.assertEqual([r["run_id"] for r in res["runs"]], [self.run_id])
        self.assertIn("scientific-research-guide", res["consumers"])
        # a second correction on the already-invalidated run is annotate-only (row 3b)
        ev = reflux.append_event(self.h, reflux.new_event("correction", "user", run_id=self.run_id, key=self.key,
                                                          evidence="second notice"))
        self.assertEqual(ev["decision"], "3b")
        self.assertEqual(runs.load_run(self.d)["run"]["state"], "invalidated")

    def test_retraction_uncited_key_accepted_with_empty_affected(self):
        ev = reflux.append_event(self.h, reflux.new_event("retraction", "a3-retraction-sweep",
                                                          key="doi:10.9999/nobody-cites-this", evidence="Crossref update-to"))
        self.assertEqual(ev["decision"], "6")
        self.assertEqual(ev["affected"], [])

    def test_retraction_on_cited_key_invalidates_per_run(self):
        ev = reflux.append_event(self.h, reflux.new_event("retraction", "a3-retraction-sweep", key=self.key,
                                                          evidence="Crossref update-to: retraction notice"))
        self.assertEqual(ev["decision"], "5")
        self.assertEqual(ev["affected"][0]["state"], "invalidated")
        # a second retraction on the now-invalidated run annotates (B-7): state unchanged, event id recorded
        ev2 = reflux.append_event(self.h, reflux.new_event("retraction", "user", key=self.key, evidence="second notice"))
        run = runs.load_run(self.d)
        self.assertEqual(run["run"]["state"], "invalidated")
        self.assertIn(ev2["event_id"], run["invalidation"]["claims"])

    def test_log_is_written_before_the_views(self):
        # build-verification B-1: the event line must exist in reflux.jsonl even if applying the views fails
        import unittest.mock as mock
        with mock.patch.object(runs, "save_run", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                reflux.append_event(self.h, reflux.new_event("correction", "user", run_id=self.run_id, key=self.key,
                                                             evidence="e", note="crash test"))
        lines = (self.h / "reflux.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertTrue(any('"note": "crash test"' in ln for ln in lines))   # log ahead of the views, never behind
        self.assertEqual(runs.load_run(self.d)["run"]["state"], "delivered")   # view untouched by the failed apply

    def test_rerun_supersedes_old_run(self):
        # open + complete a successor declaring wasRevisionOf
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            runs.cmd_open(argparse.Namespace(question="template-stripped Ag SPP propagation length 633 nm", caller="user",
                                             preset="", depth="quick", mode="1", purpose="", source_types="", scope="",
                                             output_format="", language="", domain="", slug="successor", model="",
                                             was_revision_of=self.run_id))
        new = json.loads(buf.getvalue())
        nd = Path(new["path"])
        run = runs.load_run(nd)
        run["result"]["findings"] = "L_spp re-measured: 20 ± 2 μm at 633 nm (Park 2022, Table 2) [full]"
        shutil.copy(GOOD / "ledger.jsonl", nd / "ledger.jsonl")
        shutil.copy(GOOD / "citecheck.json", nd / "citecheck.json")
        runs.save_run(nd, run)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runs.cmd_register(argparse.Namespace(run_dir=str(nd))), 0)
        ev = reflux.append_event(self.h, reflux.new_event("rerun", "user", run_id=self.run_id, artifact=new["run_id"]))
        self.assertEqual(ev["decision"], "8")
        self.assertEqual(runs.load_run(self.d)["run"]["state"], "superseded")
        # rerun on an already superseded run is annotate-only (row 8b)
        ev = reflux.append_event(self.h, reflux.new_event("rerun", "user", run_id=self.run_id, artifact=new["run_id"]))
        self.assertEqual(ev["decision"], "8b")

    def test_human_and_tool_share_one_path(self):
        # the same function serves the A3 sweep and a person: identical code path, only `actor` differs
        e1 = reflux.append_event(self.h, reflux.new_event("retraction", "user", key="doi:10.9999/x1", evidence="e"))
        e2 = reflux.append_event(self.h, reflux.new_event("retraction", "a3-retraction-sweep", key="doi:10.9999/x2", evidence="e"))
        self.assertEqual((e1["decision"], e2["decision"]), ("6", "6"))

    def test_selftest_calibrated(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(reflux.selftest(), 0)


if __name__ == "__main__":
    unittest.main()
