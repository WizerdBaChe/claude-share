"""Two-sided suite for hooks/golive_check.py (design 17 R-3).

Telemetry of every subprocess case is redirected to a temp dir (CLAUDE_TELEMETRY_DIR), so no
row lands in production. Run: python hooks/tests/test_golive_check.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "golive_check.py"
HOME = HOOK.parents[1]
sys.path.insert(0, str(HOOK.parent))
import golive_check as g  # noqa: E402

RESULTS = []
DECLARED = {
    "a_guard.py": "python tools/a-test/controls.py",
    "b_notice.py": "python hooks/tests/test_b_notice.py",
    "c_gist.py": "python hooks/c_gist.py --selftest",
}


def case(name, fn):
    try:
        fn()
        RESULTS.append((name, True, ""))
    except AssertionError as e:
        RESULTS.append((name, False, str(e)))
    except Exception as e:
        RESULTS.append((name, False, f"{type(e).__name__}: {e}"))


def t_map_the_hook_itself():
    assert g.suites_for("hooks/c_gist.py", DECLARED) == ["python hooks/c_gist.py --selftest"]


def t_map_a_named_test_file():
    assert g.suites_for("hooks/tests/test_b_notice.py", DECLARED) == [DECLARED["b_notice.py"]]


def t_map_a_file_in_the_named_tool_dir():
    assert g.suites_for("tools/a-test/fixtures/case.json", DECLARED) == [DECLARED["a_guard.py"]]


def t_unmapped_code_file_is_silent():  # negative
    assert g.suites_for("tools/other/x.py", DECLARED) == []
    assert g.suites_for("hooks/unregistered.py", DECLARED) == []


def t_non_code_file_is_silent():  # negative
    assert g.suites_for("tools/a-test/README.md", DECLARED) == []


READS = {"c_gist.py": ["references/REG.md"]}


def t_live_read_md_maps_to_its_reader():  # positive: a non-code file the hook declared
    assert g.suites_for("references/REG.md", DECLARED, READS) == [DECLARED["c_gist.py"]]


def t_undeclared_md_stays_silent():  # negative on the same shape: same suffix, not declared
    assert g.suites_for("references/OTHER.md", DECLARED, READS) == []
    assert g.suites_for("references/REG.md", DECLARED) == []   # no declarations -> old behaviour


def t_live_reads_parses_backticked_paths_only():
    with tempfile.TemporaryDirectory() as tmp:
        h = Path(tmp) / "h.py"
        h.write_text('"""x.\n\nLive-reads: `references/A.md` `tools/t/r.json` (prose, not/a/path)\n'
                     'Live-reads: `references/B.md`\n"""\n', encoding="utf-8")
        assert g.live_reads(h) == ["references/A.md", "tools/t/r.json", "references/B.md"]
        h.write_text('"""no declaration here"""\n', encoding="utf-8")
        assert g.live_reads(h) == []


def t_live_reads_real_declarations():
    # the hook whose suite checks a live register must keep declaring it (the source
    # also pinned a second reader, a personal-profile hook, which is not shipped)
    assert g.live_reads(HOME / "hooks" / "project_registry_gist.py") == ["references/PROJECTS.md"]


def t_suite_cap():
    many = {f"h{i}.py": f"python tools/t/s{i}.py" for i in range(5)}
    assert len(g.suites_for("tools/t/x.py", many)) == g.MAX_SUITES


def t_rel_in_home_outside_is_none():
    with tempfile.TemporaryDirectory() as tmp:
        assert g.rel_in_home(str(Path(tmp) / "x.py")) is None
    assert g.rel_in_home(str(HOME / "hooks" / "golive_check.py")) == "hooks/golive_check.py"


def t_run_one_three_results():
    with tempfile.TemporaryDirectory() as tmp:
        for name, code in (("ok.py", 0), ("bad.py", 1), ("undet.py", 3)):
            (Path(tmp) / name).write_text(f"print('last {name}')\nraise SystemExit({code})\n",
                                          encoding="utf-8")
        assert g.run_one("python ok.py", home=Path(tmp))[0] == "pass"
        r, last, _ = g.run_one("python bad.py", home=Path(tmp))
        assert r == "fail" and last == "last bad.py", (r, last)
        assert g.run_one("python undet.py", home=Path(tmp))[0] == "inconclusive"


def t_run_one_timeout_is_inconclusive_not_fail():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "slow.py").write_text("import time\ntime.sleep(5)\n", encoding="utf-8")
        r, last, _ = g.run_one("python slow.py", home=Path(tmp), timeout=1)
        assert r == "inconclusive" and "timed out" in last, (r, last)


def t_notice_shape():
    text = g.notice_text("hooks/x.py", [("python hooks/tests/t.py", "fail", "0/3 passed")])
    assert text.startswith("Notice from golive_check (a local PostToolUse hook")
    assert "Nothing was blocked" in text and "telemetry/golive-check.jsonl" in text
    for bad in ("Policy:", "tell the user", "in your reply", "Detail:", "see "):
        assert bad not in text, bad


def _hook(payload, tel):
    env = dict(os.environ, CLAUDE_TELEMETRY_DIR=tel)
    return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload),
                          capture_output=True, text=True, encoding="utf-8", env=env, timeout=150)


def t_e2e_real_registered_hook_passes_silently():
    # view_launcher_gist declares a fast --selftest; a pass must print nothing and log one row
    with tempfile.TemporaryDirectory() as tel:
        proc = _hook({"tool_name": "Edit", "tool_input": {
            "file_path": str(HOME / "hooks" / "view_launcher_gist.py")}}, tel)
        rows = (Path(tel) / "golive-check.jsonl").read_text(encoding="utf-8").splitlines()
        assert proc.returncode == 0 and proc.stdout.strip() == "", proc.stdout
        assert len(rows) == 1 and json.loads(rows[0])["kind"] == "pass", rows


def t_e2e_unrelated_tool_and_bad_stdin_fail_open():
    with tempfile.TemporaryDirectory() as tel:
        p1 = _hook({"tool_name": "Read", "tool_input": {"file_path": str(HOOK)}}, tel)
        env = dict(os.environ, CLAUDE_TELEMETRY_DIR=tel)
        p2 = subprocess.run([sys.executable, str(HOOK)], input="{not json", capture_output=True,
                            text=True, env=env, timeout=30)
        assert p1.returncode == 0 and p1.stdout == "" and p2.returncode == 0 and p2.stdout == ""
        assert not (Path(tel) / "golive-check.jsonl").exists(), "unmapped events log nothing"


def t_e2e_positive_control_failing_suite_emits_notice():
    # fixture home with the REAL pol.py and deny_receipt.py, one registered hook whose
    # declared suite fails: the whole chain must fire a notice and log a notice row
    import shutil
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as tel:
        home = Path(tmp)
        (home / "hooks" / "tests").mkdir(parents=True)
        (home / "tools" / "hook-proof-of-life").mkdir(parents=True)
        shutil.copy(HOME / "tools" / "hook-proof-of-life" / "pol.py", home / "tools" / "hook-proof-of-life")
        shutil.copy(HOME / "hooks" / "deny_receipt.py", home / "hooks")
        (home / "hooks" / "x_guard.py").write_text(
            '"""x.\n\nProof-of-life: `python hooks/tests/test_x_guard.py`\n"""\n', encoding="utf-8")
        (home / "hooks" / "tests" / "test_x_guard.py").write_text(
            "print('0/2 passed')\nraise SystemExit(1)\n", encoding="utf-8")
        (home / "settings.json").write_text(json.dumps({"hooks": {"PreToolUse": [{"hooks": [
            {"type": "command", "command": "python hooks/x_guard.py"}]}]}}), encoding="utf-8")
        env = dict(os.environ, CLAUDE_TELEMETRY_DIR=tel, GOLIVE_HOME=str(home))
        proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({
            "tool_name": "Edit", "tool_input": {"file_path": str(home / "hooks" / "x_guard.py")}}),
            capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)
        ctx = json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]
        assert "FAIL: `python hooks/tests/test_x_guard.py` -> 0/2 passed" in ctx, ctx
        rows = (Path(tel) / "golive-check.jsonl").read_text(encoding="utf-8").splitlines()
        assert json.loads(rows[-1])["kind"] == "notice", rows
        # negative on the same fixture: make the suite pass -> silent
        (home / "hooks" / "tests" / "test_x_guard.py").write_text("print('2/2')\n", encoding="utf-8")
        proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({
            "tool_name": "Edit", "tool_input": {"file_path": str(home / "hooks" / "x_guard.py")}}),
            capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)
        assert proc.stdout.strip() == "", proc.stdout


def t_e2e_live_read_edit_runs_the_readers_suite():
    # the 2026-09-23 incident shape: a register (.md) the suite checks live is edited so the
    # suite fails -> notice naming the failing line; repaired register -> silent
    import shutil
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as tel:
        home = Path(tmp)
        (home / "hooks" / "tests").mkdir(parents=True)
        (home / "references").mkdir()
        (home / "tools" / "hook-proof-of-life").mkdir(parents=True)
        shutil.copy(HOME / "tools" / "hook-proof-of-life" / "pol.py", home / "tools" / "hook-proof-of-life")
        shutil.copy(HOME / "hooks" / "deny_receipt.py", home / "hooks")
        (home / "hooks" / "r_gist.py").write_text(
            '"""r.\n\nProof-of-life: `python hooks/tests/test_r_gist.py`\n'
            'Live-reads: `references/REG.md`\n"""\n', encoding="utf-8")
        (home / "hooks" / "tests" / "test_r_gist.py").write_text(
            "from pathlib import Path\n"
            "t = Path('references/REG.md').read_text(encoding='utf-8')\n"
            "bad = [ln for ln in t.splitlines() if 'unclassified' in ln]\n"
            "print('unclassified: ' + ', '.join(bad) if bad else 'all classified')\n"
            "raise SystemExit(1 if bad else 0)\n", encoding="utf-8")
        (home / "settings.json").write_text(json.dumps({"hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": "python hooks/r_gist.py"}]}]}}), encoding="utf-8")
        reg = home / "references" / "REG.md"
        env = dict(os.environ, CLAUDE_TELEMETRY_DIR=tel, GOLIVE_HOME=str(home))

        def edit():
            return subprocess.run([sys.executable, str(HOOK)], input=json.dumps({
                "tool_name": "Edit", "tool_input": {"file_path": str(reg)}}),
                capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)

        reg.write_text("| NewProj unclassified |\n", encoding="utf-8")
        ctx = json.loads(edit().stdout)["hookSpecificOutput"]["additionalContext"]
        assert "FAIL: `python hooks/tests/test_r_gist.py` -> unclassified: | NewProj" in ctx, ctx
        reg.write_text("| NewProj | build |\n", encoding="utf-8")
        assert edit().stdout.strip() == ""
        rows = [json.loads(r)["kind"] for r in
                (Path(tel) / "golive-check.jsonl").read_text(encoding="utf-8").splitlines()]
        assert rows == ["notice", "pass"], rows


def t_e2e_suite_born_without_unclassifiable_case_is_named_at_save():
    # the 2026-09-23 BUG8 shape: a control suite saved with no case it must call undetermined.
    # Fixture home with the REAL pol.py and closure.py; no registered hooks, so the notice can
    # only come from closure_gap. Positive: lacking suite -> notice + row closure_lacks=True.
    # Negative on the same file: the case added -> silent, no row. A non-suite .py -> silent.
    import shutil
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as tel:
        home = Path(tmp)
        for sub in ("hooks", "tools/hook-proof-of-life", "tools/class-closure", "tools/z"):
            (home / sub).mkdir(parents=True, exist_ok=True)
        shutil.copy(HOME / "tools" / "hook-proof-of-life" / "pol.py", home / "tools" / "hook-proof-of-life")
        shutil.copy(HOME / "tools" / "class-closure" / "closure.py", home / "tools" / "class-closure")
        shutil.copy(HOME / "hooks" / "deny_receipt.py", home / "hooks")
        (home / "settings.json").write_text(json.dumps({"hooks": {}}), encoding="utf-8")
        suite, helper = home / "tools" / "z" / "controls.py", home / "tools" / "z" / "helper.py"
        env = dict(os.environ, CLAUDE_TELEMETRY_DIR=tel, GOLIVE_HOME=str(home))

        def edit(p):
            return subprocess.run([sys.executable, str(HOOK)], input=json.dumps({
                "tool_name": "Write", "tool_input": {"file_path": str(p)}}),
                capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)

        suite.write_text("print('ALL PASS 1/1')\n", encoding="utf-8")
        proc = edit(suite)
        ctx = json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]
        assert ctx.startswith("Notice from golive_check (a local PostToolUse hook"), ctx
        assert "this save touched tools/z/controls.py, which the class-closure check" in ctx, ctx
        assert "telemetry/golive-check.jsonl" in ctx, ctx
        rows = [json.loads(r) for r in (Path(tel) / "golive-check.jsonl").read_text(encoding="utf-8").splitlines()]
        assert [(r["kind"], r["closure_lacks"]) for r in rows] == [("notice", True)], rows
        suite.write_text("check('unclassifiable row is reported undetermined', f([]), 'error')\n",
                         encoding="utf-8")
        assert edit(suite).stdout.strip() == ""
        helper.write_text("print('not a suite')\n", encoding="utf-8")
        assert edit(helper).stdout.strip() == ""
        rows = (Path(tel) / "golive-check.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(rows) == 1, rows


def t_closure_gap_real_tree():
    # every suite in the live tree carries the case since 2026-09-23; a non-suite path is never a gap
    assert g.closure_gap("hooks/tests/test_golive_check.py") is False
    assert g.closure_gap("hooks/golive_check.py") is False
    assert g.closure_gap("tools/class-closure/closure.py") is False
    assert g.closure_gap(None) is False and g.closure_gap("references/PROJECTS.md") is False


def t_registry_gap_real_tree():
    # every scanned component in the live tree is registered since 2026-09-29 (scan: UNREGISTERED 0);
    # a path outside the scan roots is never a gap
    assert g.registry_gap("hooks/golive_check.py") == ""
    assert g.registry_gap("tools/class-closure/closure.py") == ""
    assert g.registry_gap("references/PROJECTS.md") == "" and g.registry_gap(None) == ""


def t_registry_gap_fixture_two_sided():
    # the REAL scan.py over a fixture registry: a newborn hook and a newborn tool dir are
    # named (positive), a registered hook and a reasoned-ignored one are not (negative), and
    # a tree without system-hmi answers "" -- fail-open, undetermined, never a false gap.
    with tempfile.TemporaryDirectory(prefix="golive-reg-") as td:
        home = Path(td)
        (home / "tools" / "system-hmi" / "hmi").mkdir(parents=True)
        (home / "tools" / "system-hmi" / "registry").mkdir(parents=True)
        shutil.copy(HOME / "tools" / "system-hmi" / "hmi" / "scan.py", home / "tools" / "system-hmi" / "hmi")
        (home / "tools" / "system-hmi" / "registry" / "subsystems.json").write_text(json.dumps([
            {"id": "s", "title_zh": "s", "title_en": "s", "order": 1, "component_rules": [
                {"glob": "hooks/known.py", "kind": "hook"}, {"glob": "tools/system-hmi", "kind": "tool"}]}]),
            encoding="utf-8")
        (home / "tools" / "system-hmi" / "registry" / "ignore.json").write_text(json.dumps([
            {"path_glob": "hooks/quiet.py", "reason": "fixture", "added": "2026-09-29"}]), encoding="utf-8")
        (home / "settings.json").write_text("{}", encoding="utf-8")
        (home / "hooks").mkdir()
        for n in ("known.py", "quiet.py", "newborn.py"):
            (home / "hooks" / n).write_text("# x\n", encoding="utf-8")
        (home / "tools" / "newtool").mkdir()
        (home / "tools" / "newtool" / "x.py").write_text("# x\n", encoding="utf-8")
        assert g.registry_gap("hooks/newborn.py", home) == "hooks/newborn.py"
        assert g.registry_gap("tools/newtool/x.py", home) == "tools/newtool"
        assert g.registry_gap("hooks/known.py", home) == ""
        assert g.registry_gap("hooks/quiet.py", home) == ""
        assert g.registry_gap("tools/system-hmi/hmi/scan.py", home) == ""
        txt = g.notice_text("hooks/newborn.py", [], False, "hooks/newborn.py")
        assert "registered in no system-hmi subsystem" in txt and "hooks/newborn.py" in txt \
            and txt.startswith("Notice from golive_check"), txt
    with tempfile.TemporaryDirectory(prefix="golive-nohmi-") as td:
        assert g.registry_gap("hooks/newborn.py", Path(td)) == ""   # undetermined: no scan to ask


CASES =[(n[2:], f) for n, f in sorted(globals().items()) if n.startswith("t_") and callable(f)]

if __name__ == "__main__":
    for name, fn in CASES:
        case(name, fn)
    for name, ok, detail in RESULTS:
        print(("PASS" if ok else "FAIL") + "  " + name + ("" if ok else f"  :: {detail}"))
    failed = [r for r in RESULTS if not r[1]]
    print(f"{len(RESULTS) - len(failed)}/{len(RESULTS)} passed" + (" -- ALL PASS" if not failed else ""))
    sys.exit(1 if failed else 0)
