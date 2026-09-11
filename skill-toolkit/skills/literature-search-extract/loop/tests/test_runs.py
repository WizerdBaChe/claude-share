"""runs.py tests — LSEL-04 / LSEL-08 acceptance (two-sided fixtures, F-1 gate, init refusal, adopt, bridge)."""
import argparse
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import runs  # noqa: E402

GOOD = HERE / "fixtures" / "good-run"
BAD = HERE / "fixtures" / "bad-run"


def ns(**kw):
    return argparse.Namespace(**kw)


class TempHome(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="lse-runs-"))
        (self.tmp / "literature").mkdir()
        os.environ["LSE_RUN_HOME"] = str(self.tmp / "literature" / "EvidenceRuns")
        os.environ["LSE_RUN_UNFILED"] = str(self.tmp / "unfiled")
        os.environ["LSE_BRIDGE_PATH"] = str(self.tmp / "bridge.md")
        self.reg = self.tmp / "registry.json"
        shutil.copy(runs.SKILL_DIR / "consumers" / "registry.json", self.reg)
        os.environ["LSE_REGISTRY_PATH"] = str(self.reg)
        self.assertEqual(runs.cmd_init(ns()), 0)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k in ("LSE_RUN_HOME", "LSE_RUN_UNFILED", "LSE_BRIDGE_PATH", "LSE_REGISTRY_PATH"):
            os.environ.pop(k, None)

    def open_args(self, q="template-stripped Ag 薄膜在 633 nm 的 SPP 傳播長度 (propagation length)", **kw):
        base = dict(question=q, caller="user", preset="", depth="quick", mode="1", purpose="", source_types="",
                    scope="", output_format="", language="", domain="", slug="", model="", was_revision_of="")
        base.update(kw)
        return ns(**base)

    def place_good(self, run_id="20260903_good-copy"):
        h = runs.home()
        d = h / run_id
        shutil.copytree(GOOD, d)
        run = runs.load_run(d)
        run["run"]["id"] = run_id
        run["run"]["home"] = str(h)
        run["run"]["state"] = "checked"
        runs.save_run(d, run)
        return d


class TestOpenAndRegister(TempHome):
    def test_open_writes_reuse_check_and_folder(self):
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(runs.cmd_open(self.open_args()), 0)
        out = json.loads(buf.getvalue())
        run = runs.load_run(Path(out["path"]))
        self.assertTrue(run["reuse_check"]["trail_line"].startswith("reuse check: "))
        self.assertEqual(run["run"]["state"], "open")
        self.assertTrue(run["run"]["filed"])
        self.assertIn(run["reuse_check"]["trail_line"], run["result"]["search_trail"])

    def test_register_refuses_without_reuse_check(self):
        d = self.place_good("20260903_no-reuse")
        run = runs.load_run(d)
        run["reuse_check"] = {"ran_at": "", "terms": [], "matches": [], "trail_line": "reuse check: "}
        runs.save_run(d, run)
        (d / "record.md").unlink()
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = runs.cmd_register(ns(run_dir=str(d)))
        self.assertEqual(rc, 2)
        self.assertFalse((d / "record.md").exists())          # nothing written
        self.assertEqual(runs.load_index(runs.home())["entries"], [])
        self.assertIn("reuse_check", buf.getvalue())

    def test_register_good_then_find_both_languages(self):
        d = self.place_good()
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runs.cmd_register(ns(run_dir=str(d))), 0)
        run = runs.load_run(d)
        self.assertEqual(run["run"]["state"], "delivered")
        idx = runs.load_index(runs.home())
        self.assertEqual([e["run_id"] for e in idx["entries"]], ["20260903_good-copy"])
        self.assertIn("doi:10.0000/fake.2022.234", idx["entries"][0]["keys"])
        for term in ("傳播長度", "propagation"):
            hits = runs.find_entries(runs.home(), [runs.fold(term)])
            self.assertEqual(len(hits), 1, term)
        self.assertTrue((runs.home() / "README.md").read_text(encoding="utf-8").startswith("---\nxi: 1"))
        rec = (d / "record.md").read_text(encoding="utf-8")
        self.assertIn("kind: literature", rec)
        self.assertIn("閉路 (loop)", rec)

    def test_pure_chinese_rephrasing_finds_the_first(self):
        # build-verification B-4: a pure-Chinese question (no Latin) must still hit a same-topic run via CJK bigrams
        d = self.place_good()
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            runs.cmd_register(ns(run_dir=str(d)))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                runs.cmd_open(self.open_args(q="銀薄膜的表面電漿子傳播長度大概是多少"))
        out = json.loads(buf.getvalue())
        self.assertIn("20260903_good-copy", out["matches"], out)
        self.assertGreater(len(runs.terms_of("銀薄膜的表面電漿子傳播長度大概是多少")), 5)

    def test_backslash_in_question_keeps_the_card_valid_yaml(self):
        # build-verification B-5: a question carrying a backslash (regex, LaTeX, Windows path) must not break the card
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML not installed")
        d = self.place_good()
        run = runs.load_run(d)
        run["request"]["question"] = r"為什麼 \mu m 與 C:\path 的 \d+ 會出錯"
        runs.save_run(d, run)
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runs.cmd_register(ns(run_dir=str(d))), 0)
        text = (d / "record.md").read_text(encoding="utf-8")
        fm = text.split("---")[1]
        card = yaml.safe_load(fm)
        self.assertIn("\\mu", card["what"])

    def test_second_open_finds_the_first(self):
        d = self.place_good()
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            runs.cmd_register(ns(run_dir=str(d)))
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                runs.cmd_open(self.open_args())
        out = json.loads(buf.getvalue())
        self.assertEqual(out["matches"], ["20260903_good-copy"])
        self.assertIn("1 prior run(s) matched", out["reuse_check"])


class TestCheck(TempHome):
    def test_fixtures_two_sided(self):
        good = runs.check_run(GOOD)
        self.assertEqual([f for f in good if f[0] == "FAIL"], [], good)
        bad = runs.check_run(BAD)
        rules = {r for s, r, _ in bad if s == "FAIL"}
        self.assertTrue({"V1", "V2", "V3", "V4", "V7", "V8", "V9"} <= rules, bad)
        self.assertGreaterEqual(len([f for f in bad if f[0] == "FAIL"]), 6)
        # the good fixture predates the fetch instrument: V9 must WARN there, never FAIL
        self.assertTrue(any(s == "WARN" and r == "V9" for s, r, _ in good), good)

    def test_v9_promotes_to_fail_after_the_cutoff(self):
        d = self.place_good("20260903_post-cutoff")
        run = runs.load_run(d)
        run["run"]["created"] = "2026-10-01T10:00:00+08:00"
        runs.save_run(d, run)
        f = runs.check_run(d)
        self.assertTrue(any(s == "FAIL" and r == "V9" and "access_route" in m for s, r, m in f), f)
        self.assertTrue(any(s == "FAIL" and r == "V9" and "manifest.json is absent" in m for s, r, m in f), f)

    def test_v9_unparseable_created_is_unknown_and_stays_warn(self):
        # QA 2026-09-11 F-14: "not-a-date" sorts after the cutoff lexicographically; it must NOT promote to FAIL
        d = self.place_good("20260903_bad-date")
        run = runs.load_run(d)
        run["run"]["created"] = "not-a-date-at-all"
        runs.save_run(d, run)
        f = runs.check_run(d)
        self.assertFalse(any(s == "FAIL" and r == "V9" for s, r, m in f), f)
        self.assertTrue(any(s == "WARN" and r == "V9" for s, r, m in f), f)

    def test_v9_pending_excerpt_and_v8_gate_fail(self):
        d = self.place_good("20260903_pending")
        (d / "sources" / "manifest.json").write_text(json.dumps({"schema": "lse-sources-manifest@1", "entries": {
            "park2022": {"file": "sources/park2022.txt", "route": "script", "retention_policy": "excerpt",
                         "retention_state": "pending-excerpt"}}}), encoding="utf-8")
        (d / "citecheck.json").write_text(json.dumps([{"claim_id": "C1", "claim": "x", "checks": [
            ["support", "FAIL", "support_span is NOT in park2022.txt"]]}]), encoding="utf-8")
        f = runs.check_run(d)
        self.assertTrue(any(s == "FAIL" and r == "V9" and "pending-excerpt" in m for s, r, m in f), f)
        self.assertTrue(any(s == "FAIL" and r == "V8" and "C1:support" in m for s, r, m in f), f)

    def test_selftest_calibrated(self):
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runs.selftest(), 0)


class TestInitAndUnfiled(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="lse-unfiled-"))
        os.environ["LSE_RUN_UNFILED"] = str(self.tmp / "unfiled")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for k in ("LSE_RUN_HOME", "LSE_RUN_UNFILED"):
            os.environ.pop(k, None)

    def test_init_refuses_missing_vault(self):
        os.environ["LSE_RUN_HOME"] = str(self.tmp / "nowhere" / "EvidenceRuns")
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runs.cmd_init(ns()), 1)
        self.assertFalse((self.tmp / "nowhere").exists())

    def test_open_unfiled_then_adopt(self):
        os.environ["LSE_RUN_HOME"] = str(self.tmp / "nowhere" / "EvidenceRuns")
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            runs.cmd_open(ns(question="unfiled run question about SPP", caller="user", preset="", depth="quick",
                             mode="1", purpose="", source_types="", scope="", output_format="", language="",
                             domain="", slug="", model="", was_revision_of=""))
        out = json.loads(buf.getvalue())
        self.assertFalse(out["filed"])
        self.assertIn("home unavailable", out["reuse_check"])
        self.assertTrue(Path(out["path"]).is_relative_to(self.tmp / "unfiled"))
        # the vault comes back
        (self.tmp / "literature").mkdir()
        os.environ["LSE_RUN_HOME"] = str(self.tmp / "literature" / "EvidenceRuns")
        with contextlib.redirect_stdout(io.StringIO()):
            runs.cmd_init(ns())
            self.assertEqual(runs.cmd_adopt(ns(run_dir=out["path"])), 0)
        moved = runs.home() / out["run_id"]
        self.assertTrue(moved.exists())
        self.assertTrue(runs.load_run(moved)["run"]["filed"])
        self.assertEqual(runs.load_index(runs.home())["entries"], [])   # still open -> not indexed until delivered


class TestRegistryAndBridge(TempHome):
    def test_bridge_idempotent_and_stale_detection(self):
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(runs.cmd_bridge(ns()), 0)
            first = Path(os.environ["LSE_BRIDGE_PATH"]).read_bytes()
            self.assertEqual(runs.cmd_bridge(ns()), 0)
            second = Path(os.environ["LSE_BRIDGE_PATH"]).read_bytes()
        self.assertEqual(first, second)
        self.assertEqual([f for f in runs.check_registry() if f[0] == "FAIL"], [])
        reg = json.loads(self.reg.read_text(encoding="utf-8"))
        reg["consumers"][0]["why_it_matters_here"] += " (edited)"
        self.reg.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
        rules = {r for s, r, _ in runs.check_registry() if s == "FAIL"}
        self.assertIn("R4", rules)

    def test_illegal_status_transition_fails(self):
        reg = json.loads(self.reg.read_text(encoding="utf-8"))
        reg["consumers"][0]["history"] = [{"status": "retired", "at": "2026-01-01"}]
        reg["consumers"][0]["status"] = "planned"
        self.reg.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
        rules = {r for s, r, _ in runs.check_registry() if s == "FAIL"}
        self.assertIn("R3", rules)


if __name__ == "__main__":
    unittest.main()
