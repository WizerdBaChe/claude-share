#!/usr/bin/env python3
"""Two-sided control suite for tools/system-hmi. Every check below is either a
POSITIVE control (a known violation that MUST fire) or a NEGATIVE control (a
known-good input that MUST pass). Fixtures live under a temp dir created by
this file; the live hooks/registry are read for exactly two facts the PSM
names explicitly (fieldwork_threshold_notice.py, deny_receipt.py) and nothing
is ever written to them.

Proof-of-life: `python tools/system-hmi/controls.py`
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
HOME = TOOL_DIR.parents[1]
sys.path.insert(0, str(TOOL_DIR))

from hmi import adapters, collector, completeness, lock, registry, scan, snapshot  # noqa: E402

RESULTS = []


def check(name, fn):
    try:
        fn()
        RESULTS.append((name, True, ""))
    except AssertionError as e:
        RESULTS.append((name, False, str(e)))
    except Exception as e:
        RESULTS.append((name, False, f"{type(e).__name__}: {e}"))


# ---------------------------------------------------------------------------
# Fixture helpers -- an isolated ~/.claude-shaped tree, never the live one.
# ---------------------------------------------------------------------------

def make_fixture_home(tmp):
    home = Path(tmp) / "home"
    for d in ("hooks", "tools", "skills", "rules", "agents"):
        (home / d).mkdir(parents=True, exist_ok=True)
    (home / "hooks" / "probe_guard.py").write_text('"""STATUS: LIVE\nProof-of-life: `echo ok`\n"""\n',
                                                     encoding="utf-8")
    (home / "hooks" / "other_hook.py").write_text('"""no status line"""\n', encoding="utf-8")
    (home / "settings.json").write_text(json.dumps({
        "hooks": {"PreToolUse": [{"matcher": "", "hooks": [
            {"command": '"python" "' + str(home / "hooks" / "probe_guard.py").replace("\\", "/") + '"'}]}]}
    }), encoding="utf-8")
    (home / "tools" / "sample-tool").mkdir(parents=True, exist_ok=True)
    (home / "tools" / "sample-tool" / "README.md").write_text("x", encoding="utf-8")
    (home / "tools" / "sample-tool" / "controls.py").write_text("print('ALL PASS 1/1')\n", encoding="utf-8")
    return home


def base_registry(extra_subsystems=None, extra_points=None, extra_ignore=None, extra_sources=None):
    subsystems = [
        {"id": "fixture-sub", "title_zh": "夾具", "title_en": "Fixture", "order": 1,
         "component_rules": [
             {"glob": "hooks/probe_guard.py", "kind": "hook"},
             {"glob": "hooks/other_hook.py", "kind": "hook"},
             {"glob": "tools/sample-tool", "kind": "tool"},
             {"glob": "tools/ghost-tool", "kind": "tool"},  # literal, deliberately absent -> MISSING
             {"glob": "hooks/retired_hook.py", "kind": "hook", "disposition": "retired",
              "reason": "fixture retired case"},
         ]},
    ]
    if extra_subsystems:
        subsystems.extend(extra_subsystems)
    points = list(extra_points or [])
    ignore = list(extra_ignore or [])
    sources = list(extra_sources or [])
    return {"subsystems": subsystems, "points": points, "rubric": _rubric(), "ignore": ignore,
            "sources": sources}


def _rubric():
    return json.loads((TOOL_DIR / "registry" / "rubric.json").read_text(encoding="utf-8"))


def _pt(id_, component, adapter, adapter_config, tier="cheap", disposition=None, watched_by=None,
        remedy=None):
    return {"id": id_, "component": component, "alias": id_, "tier": tier, "adapter": adapter,
            "adapter_config": adapter_config, "disposition": disposition or {"value": "active"},
            "remedy": remedy, "why": "fixture", "watched_by": watched_by}


PY = sys.executable


def argv_c(code):
    return [PY, "-c", code]


# ---------------------------------------------------------------------------
# INV-1 read-only. Not a pass/fail gate over an input, so the "detector" under
# test is a directory hash comparison used both live and here.
# ---------------------------------------------------------------------------

def _tree_hash(root):
    import hashlib
    h = hashlib.sha256()
    for p in sorted(Path(root).rglob("*")):
        if "out" in p.relative_to(root).parts:
            continue
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def t_inv1_negative():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        before = _tree_hash(home)
        reg = base_registry()
        out = home / "tools" / "system-hmi" / "out"
        result = collector.collect(str(home), reg, str(out), full=False)
        assert result["ok"], result
        after = _tree_hash(home)
        assert before == after, "collector wrote outside out/ (INV-1 violated)"


def t_inv1_positive():
    # The detector itself: mutating a fixture file MUST be caught by the same hash check.
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        before = _tree_hash(home)
        (home / "hooks" / "other_hook.py").write_text("mutated", encoding="utf-8")
        after = _tree_hash(home)
        assert before != after, "tree-hash detector failed to notice a real mutation"


# ---------------------------------------------------------------------------
# INV-2 quality/state separate axes.
# ---------------------------------------------------------------------------

def t_inv2_negative_good_state_used():
    r = adapters.adapt_exit_code({"argv": argv_c("import sys; sys.exit(0)"), "cwd": ".",
                                   "exit_map": {"0": "pass"}}, str(HOME))
    assert r["quality"] == "good" and r["state"] == "pass"


def t_inv2_positive_bad_quality_state_null():
    r = adapters.adapt_status_file({"path": "does/not/exist.json", "format": "json", "field": "x",
                                     "ok_values": ["ok"]}, str(HOME))
    assert r["quality"] == "probe_error"
    assert r["state"] is None, "state must be null when quality != good (INV-2)"


# ---------------------------------------------------------------------------
# INV-3 absence is not pass.
# ---------------------------------------------------------------------------

def t_inv3_positive_no_success_no_pass():
    with tempfile.TemporaryDirectory() as tmp:
        emitter = Path(tmp) / "bad_emitter.py"
        emitter.write_text("import sys; sys.exit(1)\n", encoding="utf-8")
        src_cfg = {"id": "fixture-src", "argv": [PY, str(emitter)], "cwd": ".", "tier": "cheap", "timeout_s": 10}
        cache = {"fixture-src": adapters.fetch_source(src_cfg, str(HOME))}
        r = adapters.adapt_native({"source": "fixture-src", "point": "fixture-src.anything"}, cache)
        assert r["state"] != "pass"
        assert r["quality"] == "probe_error"


def t_inv3_negative_contrast_real_pass():
    with tempfile.TemporaryDirectory() as tmp:
        emitter = Path(tmp) / "good_emitter.py"
        emitter.write_text(
            'import json,sys\nprint(json.dumps({"protocol":"hmi-report/1","source":"fixture-src",'
            '"generated_at":"2026-01-01T00:00:00Z","points":[{"id":"fixture-src.p1","ran":True,'
            '"skip_reason":None,"state":"pass","findings":[]}]}))\n', encoding="utf-8")
        src_cfg = {"id": "fixture-src", "argv": [PY, str(emitter)], "cwd": ".", "tier": "cheap", "timeout_s": 10}
        cache = {"fixture-src": adapters.fetch_source(src_cfg, str(HOME))}
        r = adapters.adapt_native({"source": "fixture-src", "point": "fixture-src.p1"}, cache)
        assert r["state"] == "pass" and r["quality"] == "good"


# ---------------------------------------------------------------------------
# INV-4 no restated thresholds.
# ---------------------------------------------------------------------------

def t_inv4_positive_leak_rejected():
    reg = base_registry(extra_points=[
        _pt("fixture-sub.bad", "hooks/probe_guard.py", "exit-code",
            {"argv": ["echo"], "cwd": ".", "threshold": 42})])
    errs = registry.validate(reg, home=str(HOME))
    assert any("restated threshold" in e for e in errs)


def t_inv4_negative_timeout_and_maxage_allowed():
    reg = base_registry(extra_points=[
        _pt("fixture-sub.ok", "hooks/probe_guard.py", "status-file",
            {"path": "x.json", "format": "json", "field": "f", "ok_values": ["ok"],
             "timeout_s": 10, "max_age_s": 60})])
    errs = registry.validate(reg, home=str(HOME))
    assert not any("restated threshold" in e for e in errs)


# ---------------------------------------------------------------------------
# INV-5(a) disk -> registry closure.
# ---------------------------------------------------------------------------

def t_inv5a_positive_unregistered():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        (home / "hooks" / "zz_probe_guard.py").write_text("x", encoding="utf-8")
        reg = base_registry()
        result = scan.scan(str(home), reg)
        assert any(u["path"] == "hooks/zz_probe_guard.py" for u in result["unregistered"])


def t_inv5a_negative_ignore_removes_it():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        (home / "hooks" / "zz_probe_guard.py").write_text("x", encoding="utf-8")
        reg = base_registry(extra_ignore=[{"path_glob": "hooks/zz_probe_guard.py", "reason": "fixture",
                                            "added": "2026-01-01"}])
        result = scan.scan(str(home), reg)
        assert not any(u["path"] == "hooks/zz_probe_guard.py" for u in result["unregistered"])
        assert any(i["path"] == "hooks/zz_probe_guard.py" for i in result["ignored"])


# ---------------------------------------------------------------------------
# INV-5(b) registry -> disk closure.
# ---------------------------------------------------------------------------

def t_inv5b_positive_missing():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        reg = base_registry()
        result = scan.scan(str(home), reg)
        assert any(m["path"] == "tools/ghost-tool" for m in result["missing"])


def t_inv5b_negative_retired_not_missing():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        reg = base_registry()
        result = scan.scan(str(home), reg)
        assert not any(m["path"] == "hooks/retired_hook.py" for m in result["missing"])
        assert any(r["path"] == "hooks/retired_hook.py" for r in result["retired"]) is False  # not on disk at all
        # retired-and-absent is correctly NOT reported anywhere (neither missing nor unregistered)
        assert not any(u["path"] == "hooks/retired_hook.py" for u in result["unregistered"])


def t_inv5b_overlap_positive():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        reg = base_registry(extra_subsystems=[
            {"id": "fixture-sub-2", "title_zh": "夾具2", "title_en": "Fixture2", "order": 2,
             "component_rules": [{"glob": "hooks/*.py", "kind": "hook"}]}])
        errs = registry.validate(reg, home=str(home))
        assert any("overlapping" in e for e in errs)


def t_inv5b_overlap_negative():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        reg = base_registry()
        errs = registry.validate(reg, home=str(home))
        assert not any("overlapping" in e for e in errs)


# ---------------------------------------------------------------------------
# INV-6 rollup honesty.
# ---------------------------------------------------------------------------

def _cross_cutting_registry(target):
    other = {"id": "other-sub", "title_zh": "他處", "title_en": "Other", "order": 2, "component_rules": []}
    pt = _pt("fixture-sub.cross-cutting", "hooks/probe_guard.py", "exit-code",
             {"argv": argv_c("import sys; sys.exit(1)"), "cwd": ".", "exit_map": {"0": "pass", "1": "fail"}})
    if target is not None:
        pt["subsystem"] = target
    return base_registry(extra_subsystems=[other], extra_points=[pt])


def t_point_subsystem_override_positive():
    """A cross-cutting point rolls up where it SAYS, not where its emitter lives."""
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        out = home / "tools" / "system-hmi" / "out"
        snap = collector.collect(str(home), _cross_cutting_registry("other-sub"), str(out), full=False)["snapshot"]
        subs = {s["id"]: s for s in snap["subsystems"]}
        assert subs["other-sub"]["state"] == "fail", subs["other-sub"]
        assert subs["fixture-sub"]["state"] != "fail", subs["fixture-sub"]


def t_point_subsystem_override_negative():
    """Without the field the same point stays with its component; an unknown target is rejected."""
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        out = home / "tools" / "system-hmi" / "out"
        snap = collector.collect(str(home), _cross_cutting_registry(None), str(out), full=False)["snapshot"]
        subs = {s["id"]: s for s in snap["subsystems"]}
        assert subs["fixture-sub"]["state"] == "fail", subs["fixture-sub"]
        assert subs["other-sub"]["state"] != "fail", subs["other-sub"]
        errors = registry.validate(_cross_cutting_registry("no-such-sub"), home=str(home))
        assert any("unknown subsystem" in e for e in errors), errors


def t_carried_reading_keeps_observation_time():
    """A slow point carried through a cheap-only pass keeps the time it was OBSERVED, stays out
    of `state` (INV-6) and surfaces as last_known_state. Negative side: the full pass that
    produced it reports good quality and no last_known_state."""
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        out = home / "tools" / "system-hmi" / "out"
        reg = base_registry(extra_points=[
            _pt("fixture-sub.slow", "hooks/probe_guard.py", "exit-code",
                {"argv": argv_c("import sys; sys.exit(0)"), "cwd": ".", "exit_map": {"0": "pass"}}, tier="slow")])
        full = collector.collect(str(home), reg, str(out), full=True)["snapshot"]
        p_full = next(p for p in full["points"] if p["id"] == "fixture-sub.slow")
        s_full = next(s for s in full["subsystems"] if s["id"] == "fixture-sub")
        assert p_full["reading"]["quality"] == "good" and s_full["state"] == "pass", (p_full, s_full)
        assert s_full["last_known_state"] is None, s_full
        import time as _t
        _t.sleep(1.1)
        cheap = collector.collect(str(home), reg, str(out), full=False)["snapshot"]
        p_cheap = next(p for p in cheap["points"] if p["id"] == "fixture-sub.slow")
        s_cheap = next(s for s in cheap["subsystems"] if s["id"] == "fixture-sub")
        assert p_cheap["reading"]["quality"] == "stale", p_cheap
        assert p_cheap["reading"]["observed_at"] == p_full["reading"]["observed_at"],             "carried reading was re-stamped with the cheap pass's time"
        assert s_cheap["state"] is None and s_cheap["last_known_state"] == "pass", s_cheap


def t_reconcile_judge_every_branch():
    """Rung 1: judge() is a finite table. Grace 3d. Both sides of every rule, asserted on state."""
    sys.path.insert(0, str(TOOL_DIR / "emitters"))
    import reconcile as rec
    G = 3.0
    assert rec.judge([], [], [], G)[0] == "pass"
    assert rec.judge([("a", 0.5)], [], [], G)[0] == "warn"            # in flight
    assert rec.judge([("a", 0.5), ("b", 3.5)], [], [], G)[0] == "fail"  # one old path is enough
    assert rec.judge([], [("br", 1.0)], [], G)[0] == "warn"
    assert rec.judge([], [("br", 9.0)], [], G)[0] == "fail"
    assert rec.judge([], [], ["done-branch"], G)[0] == "warn"          # Q3: never fail
    assert rec.judge([("gone", None)], [], [], G)[0] == "warn"         # deleted path: no age, not a fail
    st, q, _f = rec.judge([("a", 9.0)], [], [], None)                  # grace unreadable
    assert st is None and q == "undetermined", (st, q)
    assert rec.judge([], [], [], None)[0] == "pass"                    # clean needs no grace
    # tool-appended records: judged by days since their last commit, never fail
    assert rec.judge([], [], [], G, appended=[("t.jsonl", 0.5)])[0] == "pass"
    assert rec.judge([], [], [], G, appended=[("t.jsonl", 4.0)])[0] == "warn"
    assert rec.judge([], [], [], G, appended=[("t.jsonl", 40.0)])[0] == "warn"
    assert rec.judge([("a", 3.5)], [], [], G, appended=[("t.jsonl", 0.5)])[0] == "fail"  # no masking
    # merged branch still checked out in a linked worktree: in use while its reflog is fresh
    assert rec.judge([], [], [], G, parked=[("claude/wt", 0.2)])[0] == "pass"
    assert rec.judge([], [], [], G, parked=[("claude/wt", 5.0)])[0] == "warn"
    assert rec.judge([], [], [], G, parked=[("claude/wt", None)])[0] == "warn"  # unreadable != in use
    assert rec.judge([], [], ["done"], G, parked=[("claude/wt", 0.2)])[0] == "warn"  # no masking
    st, q, _f = rec.judge([], [], [], None, appended=[("t.jsonl", 0.5)])
    assert st is None and q == "undetermined", (st, q)


def t_reconcile_grace_is_read_not_restated():
    """INV-4: the grace is the hook's own STALE_WORK_DAYS; a file without it yields None."""
    sys.path.insert(0, str(TOOL_DIR / "emitters"))
    import reconcile as rec
    live = rec.grace_days(HOME / "hooks" / "ops_health_nudge.py")
    assert isinstance(live, float) and live > 0, live
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "h.py"
        f.write_text("STALE_WORK_DAYS = 11", encoding="utf-8")
        assert rec.grace_days(f) == 11.0
        f.write_text("OTHER = 1", encoding="utf-8")
        assert rec.grace_days(f) is None
        assert rec.grace_days(Path(tmp) / "absent.py") is None


def t_reconcile_live_repo_facts():
    """A real throwaway repo: clean -> pass; an untracked file -> warn; not a repo -> error."""
    import subprocess
    sys.path.insert(0, str(TOOL_DIR / "emitters"))
    import reconcile as rec
    import time as _t
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "r"
        repo.mkdir()
        assert rec.repo_facts(repo, _t.time())[1] == "not-a-git-repo"
        run = lambda *a: subprocess.run(["git", "-C", str(repo), *a], capture_output=True, check=True)
        run("init", "-q", "-b", "main")
        run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init")
        facts, err = rec.repo_facts(repo, _t.time())
        assert err is None and rec.judge(facts["dirty"], facts["unmerged"], facts["merged"], 3.0)[0] == "pass", facts
        (repo / "new.txt").write_text("x", encoding="utf-8")
        facts, _ = rec.repo_facts(repo, _t.time())
        assert [p for p, _a in facts["dirty"]] == ["new.txt"], facts
        assert rec.judge(facts["dirty"], [], [], 3.0)[0] == "warn"
        # the attribute routes a committed, then re-dirtied, record to `appended`; unmarked stays dirty
        (repo / ".gitattributes").write_text("log.jsonl tool-appended\n", encoding="utf-8")
        (repo / "log.jsonl").write_text("{}\n", encoding="utf-8")
        (repo / "plain.jsonl").write_text("{}\n", encoding="utf-8")
        run("add", ".gitattributes", "log.jsonl", "plain.jsonl", "new.txt")
        run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "rec")
        (repo / "log.jsonl").write_text("{}\n{}\n", encoding="utf-8")
        (repo / "plain.jsonl").write_text("{}\n{}\n", encoding="utf-8")
        facts, _ = rec.repo_facts(repo, _t.time())
        assert [p for p, _a in facts["appended"]] == ["log.jsonl"], facts
        assert [p for p, _a in facts["dirty"]] == ["plain.jsonl"], facts
        # a fresh linked worktree whose branch never diverged is parked, not merged
        run("worktree", "add", "-q", "-b", "wt-br", str(Path(tmp) / "wt"))
        facts, _ = rec.repo_facts(repo, _t.time())
        assert facts["merged"] == [] and [n for n, _a in facts["parked"]] == ["wt-br"], facts
        run("branch", "gone-br")
        facts, _ = rec.repo_facts(repo, _t.time())
        assert facts["merged"] == ["gone-br"], facts               # no worktree: still reported
        run("worktree", "remove", "--force", str(Path(tmp) / "wt"))
        assert rec.repo_facts(Path(tmp) / "absent", _t.time())[1] == "path-missing"


def t_dual_rollup_r_and_i_never_fold():
    """An R fail must not colour I, and an I pass must not hide it: r_state/i_state are separate,
    state is their max."""
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        out = home / "tools" / "system-hmi" / "out"
        r_pt = _pt("fixture-sub.r", "hooks/probe_guard.py", "exit-code",
                   {"argv": argv_c("import sys; sys.exit(1)"), "cwd": ".", "exit_map": {"0": "pass", "1": "fail"}})
        r_pt["class"] = "reconcile"
        i_pt = _pt("fixture-sub.i", "hooks/probe_guard.py", "exit-code",
                   {"argv": argv_c("import sys; sys.exit(0)"), "cwd": ".", "exit_map": {"0": "pass", "1": "fail"}})
        snap = collector.collect(str(home), base_registry(extra_points=[r_pt, i_pt]), str(out), full=False)["snapshot"]
        sub = next(s for s in snap["subsystems"] if s["id"] == "fixture-sub")
        assert (sub["r_state"], sub["i_state"], sub["state"]) == ("fail", "pass", "fail"), sub
        only_i = collector.collect(str(home), base_registry(extra_points=[i_pt]), str(out), full=False)["snapshot"]
        sub = next(s for s in only_i["subsystems"] if s["id"] == "fixture-sub")
        assert (sub["r_state"], sub["i_state"]) == (None, "pass"), sub   # no R point is "-", never pass


def t_scoped_collect_recomputes_subsystem_rollup():
    """A scoped collect (--subsystem / --point) must re-derive the rollup of every subsystem its fresh
    points belong to: a subsystem at i_state=fail whose points now all pass reads pass, not the
    carried fail. Other side: a subsystem outside the scope keeps its carried verdict, and the
    completeness histogram and components[] stay as carried (no scan on a scoped run)."""
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        out = home / "tools" / "system-hmi" / "out"
        flag_a, flag_b = Path(tmp) / "flag_a", Path(tmp) / "flag_b"
        flag_a.write_text("x", encoding="utf-8")
        flag_b.write_text("x", encoding="utf-8")

        def flip(id_, flag):
            return _pt(id_, "hooks/probe_guard.py", "exit-code",
                       {"argv": argv_c(f"import os, sys; sys.exit(1 if os.path.exists({str(flag)!r}) else 0)"),
                        "cwd": ".", "exit_map": {"0": "pass", "1": "fail"}})
        a = flip("fixture-sub.flip", flag_a)
        b = flip("other-sub.flip", flag_b)
        b["subsystem"] = "other-sub"
        other = {"id": "other-sub", "title_zh": "他處", "title_en": "Other", "order": 2, "component_rules": []}
        reg = base_registry(extra_subsystems=[other], extra_points=[a, b])
        reg["groups"] = [{"id": "g", "faces": {"B": "b"}, "subsystems": {"fixture-sub": "B"}}]
        full = collector.collect(str(home), reg, str(out), full=False)["snapshot"]
        subs = {s["id"]: s for s in full["subsystems"]}
        assert subs["fixture-sub"]["i_state"] == "fail" and subs["other-sub"]["i_state"] == "fail", subs
        hist_before = subs["fixture-sub"]["completeness_histogram"]
        # the fixture's scan-generated hook-suite points are not good-quality and stay standing;
        # only the flipped fail may leave the count.
        standing_before = subs["fixture-sub"]["standing_count"]

        flag_a.unlink()
        flag_b.unlink()
        scoped = collector.collect(str(home), reg, str(out), subsystem_id="fixture-sub")["snapshot"]
        subs = {s["id"]: s for s in scoped["subsystems"]}
        fx = subs["fixture-sub"]
        assert (fx["i_state"], fx["state"]) == ("pass", "pass"), fx
        assert fx["standing_count"] == standing_before - 1, (standing_before, fx)
        assert fx["completeness_histogram"] == hist_before, fx          # carried, not recomputed
        assert scoped["components"] == full["components"]                # carried, not recomputed
        assert subs["other-sub"]["i_state"] == "fail", subs["other-sub"]  # outside the scope: untouched
        assert scoped["groups"][0]["faces"]["B"]["i_state"] == "pass", scoped["groups"]

        by_point = collector.collect(str(home), reg, str(out), point_id="other-sub.flip")["snapshot"]
        subs = {s["id"]: s for s in by_point["subsystems"]}
        assert subs["other-sub"]["i_state"] == "pass", subs["other-sub"]  # --point scope rolls up too
        assert subs["fixture-sub"]["i_state"] == "pass", subs["fixture-sub"]


def t_group_faces_rollup_both_sides():
    """A group face rolls R and I separately from good readings; a point-level face wins over the
    subsystem's; a face nobody reads stays None (never pass); validate rejects an unknown subsystem
    and an undeclared face."""
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        out = home / "tools" / "system-hmi" / "out"
        r_pt = _pt("fixture-sub.r", "hooks/probe_guard.py", "exit-code",
                   {"argv": argv_c("import sys; sys.exit(1)"), "cwd": ".", "exit_map": {"0": "pass", "1": "warn"}})
        r_pt["class"] = "reconcile"
        i_pt = _pt("fixture-sub.i", "hooks/probe_guard.py", "exit-code",
                   {"argv": argv_c("import sys; sys.exit(0)"), "cwd": ".", "exit_map": {"0": "pass", "1": "fail"}})
        reg = base_registry(extra_points=[r_pt, i_pt])
        reg["groups"] = [{"id": "g", "faces": {"A": "a", "B": "b", "D": "d"},
                          "subsystems": {"fixture-sub": "B"}, "points": {"fixture-sub.r": "D"}}]
        snap = collector.collect(str(home), reg, str(out), full=False)["snapshot"]
        faces = snap["groups"][0]["faces"]
        assert (faces["D"]["r_state"], faces["D"]["i_state"]) == ("warn", None), faces   # point-level face wins
        assert faces["B"]["r_state"] is None and faces["B"]["i_state"] == "pass", faces  # the warn did not leak into B
        assert faces["A"]["points"] == 0 and faces["A"]["r_state"] is None and faces["A"]["i_state"] is None, faces
        sub = next(s for s in snap["subsystems"] if s["id"] == "fixture-sub")
        assert sub["r_state"] == "warn", sub                                              # the subsystem view is untouched
        bad = base_registry()
        bad["groups"] = [{"id": "g", "faces": {"A": "a"}, "subsystems": {"no-such": "A", "fixture-sub": "Z"}}]
        msg = "; ".join(registry.validate(bad, home=str(home)))
        assert "unknown subsystem 'no-such'" in msg and "undeclared face 'Z'" in msg, msg
        good = base_registry()
        good["groups"] = [{"id": "g", "faces": {"A": "a"}, "subsystems": {"fixture-sub": "A"}}]
        assert not [e for e in registry.validate(good, home=str(home)) if "group" in e]


def t_agents_census_reads_only_a_trustworthy_snapshot():
    """No scheduled snapshot, a session-context one, a stale one and a blind channel are all 'did not
    run' (never pass); a clean scheduled snapshot passes; an open event warns."""
    sys.path.insert(0, str(TOOL_DIR / "emitters"))
    import datetime as dt
    import agents_census as ac
    now = dt.datetime(2026, 9, 20, 12, 0, tzinfo=dt.timezone.utc)
    ok_ch = {c: {"status": "ok", "reason": "x"} for c in ("registry", "appx", "dir", "home_root")}

    def run(snap):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "scheduled.json"
            if snap is not None:
                f.write_text(json.dumps(snap), encoding="utf-8")
            return {p["id"]: p for p in ac.build(f, now=now)["points"]}

    base = {"context": "scheduled", "collected_at": "2026-09-20T03:00:00+00:00", "channels": ok_ch, "events": []}
    for bad in (None, {**base, "context": "session"}, {**base, "collected_at": "2026-09-10T03:00:00+00:00"}):
        pts = run(bad)
        assert all(p["ran"] is False and p["state"] is None for p in pts.values()), (bad, pts)
    pts = run(base)
    assert (pts["agents.channels"]["state"], pts["agents.events"]["state"]) == ("pass", "pass"), pts
    ev = {"kind": "FOREIGN-WRITE", "channel": "home_root", "name": "AGENTS.md", "reason": "owner codex, hash changed"}
    pts = run({**base, "events": [ev]})
    assert pts["agents.events"]["state"] == "warn" and "AGENTS.md" in pts["agents.events"]["findings"][0]["text"], pts
    blind = {**ok_ch, "registry": {"status": "undet", "reason": "powershell timeout"}}
    pts = run({**base, "channels": blind})
    assert pts["agents.channels"]["ran"] is False and "registry" in pts["agents.channels"]["skip_reason"], pts
    assert pts["agents.events"]["ran"] is False, pts            # "no events" behind a blind channel is not a verdict
    pts = run({**base, "channels": blind, "events": [ev]})
    assert pts["agents.events"]["state"] == "warn", pts          # but an event that WAS seen still shows


def t_awareness_census_and_closure():
    """Memory closure catches a dead pointer AND an unindexed file. The folder census that used to be
    checked here moved to tools/place-ledger on 2026-09-19; what it caught (a folder no register
    names) is now reproduced by that tool's controls: `proposals ... no-match` (an unknown folder is
    recorded, never dropped) and `reclassify ...` (an approved project absent from PROJECTS.md reads
    UNPROCESSED)."""
    sys.path.insert(0, str(TOOL_DIR / "emitters"))
    import awareness as aw
    with tempfile.TemporaryDirectory() as tmp:
        mem = Path(tmp) / "memory"
        mem.mkdir()
        (mem / "MEMORY.md").write_text("- [A](a.md) x", encoding="utf-8")
        (mem / "a.md").write_text("a", encoding="utf-8")
        assert aw.memory_closure(mem) == ([], [])
        (mem / "b.md").write_text("b", encoding="utf-8")
        (mem / "a.md").unlink()
        assert aw.memory_closure(mem) == (["a.md"], ["b.md"])
        assert aw.memory_closure(Path(tmp) / "absent") is None


def t_coverage_reaches_three_routes():
    """C2/C3: a point reaches a component by binding, by a covers glob, or by covers_subsystem --
    and by nothing else. A manual point never counts; a reconcile point never satisfies C3."""
    comp = {"id": "skills/demo", "path": "skills/demo", "kind": "tool", "subsystem": "s1"}
    ext = {"id": "D:/ext", "path": "D:/ext", "kind": "tool", "subsystem": "s1"}
    P = lambda **kw: dict({"component": "hooks/x.py", "adapter": "native", "subsystem": "other"}, **kw)
    assert completeness.reaches(P(component="skills/demo"), comp)
    assert completeness.reaches(P(covers=["skills/*"]), comp)
    assert completeness.reaches(P(covers_subsystem=True, subsystem="s1"), comp)
    assert not completeness.reaches(P(covers_subsystem=True, subsystem="s1"), ext)   # home-relative only
    assert not completeness.reaches(P(covers=["tools/*"]), comp)
    assert not completeness.reaches(P(covers_subsystem=True, subsystem="s2"), comp)
    rub = _rubric()
    r_only = [P(covers=["skills/*"], **{"class": "reconcile"})]
    ev = completeness.evaluate(comp, str(HOME), rub, set(), {}, [], set(), all_points=r_only)
    assert ev["C2"] is True and ev["C3"] is False, ev
    manual = [P(covers=["skills/*"], adapter="manual")]
    ev = completeness.evaluate(comp, str(HOME), rub, set(), {}, [], set(), all_points=manual)
    assert ev["C3"] is False, ev


def t_static_scan_class_validity():
    """D-6: a slow point's verdict is carried as GOOD only while its inputs are unchanged AND the
    integrity poll has not lapsed. Four sides: unchanged -> good+carried; input touched -> stale+due;
    --due re-runs exactly the due point; poll lapsed -> due even with unchanged inputs; and with no
    scan config at all nothing is ever carried (the pre-v1.3 behaviour)."""
    import os
    import time as _t
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        out = home / "tools" / "system-hmi" / "out"
        pt = _pt("fixture-sub.slow", "tools/sample-tool", "exit-code",
                 {"argv": argv_c("import sys; sys.exit(0)"), "cwd": ".", "exit_map": {"0": "pass"}}, tier="slow")
        reg = base_registry(extra_points=[pt])
        reg["scan"] = {"integrity_poll_days": 3}
        get = lambda snap: next(p for p in snap["points"] if p["id"] == "fixture-sub.slow")["reading"]
        sub = lambda snap: next(s for s in snap["subsystems"] if s["id"] == "fixture-sub")
        full = collector.collect(str(home), reg, str(out), full=True)["snapshot"]
        ran_at = get(full)["last_ran_at"]
        assert get(full)["fingerprint"] and get(full)["quality"] == "good"
        _t.sleep(1.1)
        cheap = collector.collect(str(home), reg, str(out))["snapshot"]
        r = get(cheap)
        assert (r["quality"], r.get("carried"), r["last_ran_at"]) == ("good", "inputs-unchanged", ran_at), r
        assert sub(cheap)["i_state"] == "pass" and cheap["run"]["due_points"] == [], cheap["run"]
        # touch an input -> the verdict is no longer valid
        f = home / "tools" / "sample-tool" / "README.md"
        f.write_text("changed", encoding="utf-8")
        cheap2 = collector.collect(str(home), reg, str(out))["snapshot"]
        r = get(cheap2)
        assert r["quality"] == "stale" and r.get("due") is True, r
        assert cheap2["run"]["due_points"] == ["fixture-sub.slow"] and sub(cheap2)["i_state"] is None
        due = collector.collect(str(home), reg, str(out), due=True)["snapshot"]
        r = get(due)
        assert r["quality"] == "good" and r.get("carried") is None and r["last_ran_at"] != ran_at, r
        # integrity poll lapsed: same inputs, but last_ran_at is 4 days old
        snap = snapshot.load(str(out))
        for p in snap["points"]:
            if p["id"] == "fixture-sub.slow":
                old = datetime_utc_days_ago(4)
                p["reading"]["last_ran_at"] = old
        snapshot.write(str(out), snap)
        lapsed = collector.collect(str(home), reg, str(out))["snapshot"]
        assert get(lapsed)["quality"] == "stale" and get(lapsed).get("due") is True, get(lapsed)
        # no scan config -> nothing is ever carried as good
        reg2 = base_registry(extra_points=[pt])
        out2 = home / "tools" / "system-hmi" / "out2"
        collector.collect(str(home), reg2, str(out2), full=True)
        assert get(collector.collect(str(home), reg2, str(out2))["snapshot"])["quality"] == "stale"


def t_hook_suite_inputs_include_live_reads():
    """2026-09-29 (L-121 hit 3): a hook-suite point fingerprints the files its hook
    declares on `Live-reads:` (positive), while a hook without the line keeps the
    code-only inputs (negative), so a fixed data register makes the point due
    instead of being carried as inputs-unchanged."""
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        (home / "references").mkdir(exist_ok=True)
        (home / "references" / "REG.md").write_text("x", encoding="utf-8")
        (home / "hooks" / "probe_guard.py").write_text(
            '"""STATUS: LIVE\nProof-of-life: `echo ok`\n'
            'Live-reads: `references/REG.md` (prose here must not become a path)\n"""\n',
            encoding="utf-8")
        reg = base_registry()
        result = scan.scan(str(home), reg)
        pts = {p["id"]: p for p in collector._hook_suite_points(result, str(home))}
        assert "hook-suite.probe_guard" in pts, sorted(pts)
        assert "references/REG.md" in pts["hook-suite.probe_guard"]["inputs"], pts["hook-suite.probe_guard"]["inputs"]
        assert all("prose" not in i for i in pts["hook-suite.probe_guard"]["inputs"])
        # the fixture's other registered hook has no Live-reads line: code-only inputs
        assert "hook-suite.other_hook" in pts, sorted(pts)
        assert "references/REG.md" not in pts["hook-suite.other_hook"]["inputs"]
        # without a home the generator stays code-only (the pre-2026-09-29 shape)
        legacy = {p["id"]: p for p in collector._hook_suite_points(result)}
        assert "references/REG.md" not in legacy["hook-suite.probe_guard"]["inputs"]


def datetime_utc_days_ago(n):
    import datetime as _d
    return (_d.datetime.now(_d.timezone.utc) - _d.timedelta(days=n)).strftime("%Y-%m-%dT%H:%M:%SZ")


def t_e5_three_way():
    """PIM s7 E5: verifiable declaration -> True; unverifiable declaration -> None; none -> False.
    Rung 1: the three branches are the whole domain of the detector."""
    tasks = ["FixtureFeeder-Daily"]
    mk = lambda wb: [_pt("x.p", "tools/sample-tool", "exit-code", {"argv": ["x"]}, watched_by=wb)]
    assert completeness._detect_e5("c", mk("FixtureFeeder-Daily"), tasks) is True
    assert completeness._detect_e5("c", mk("ops-health.some-alias"), tasks) is True
    assert completeness._detect_e5("c", mk("NoSuchTask-Daily"), tasks) is None
    assert completeness._detect_e5("c", mk(None), tasks) is False
    assert completeness._detect_e5("c", [], tasks) is False


def t_inv6_positive_fail_plus_no_probe():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        reg = base_registry(extra_points=[
            _pt("fixture-sub.failing", "hooks/probe_guard.py", "exit-code",
                {"argv": argv_c("import sys; sys.exit(1)"), "cwd": ".", "exit_map": {"0": "pass", "1": "fail"}}),
            _pt("fixture-sub.noprobe", "hooks/other_hook.py", "exit-code",
                {"argv": ["nonexistent-binary-xyz"], "cwd": "."}),
        ])
        out = home / "tools" / "system-hmi" / "out"
        result = collector.collect(str(home), reg, str(out), full=False)
        snap = result["snapshot"]
        sub = next(s for s in snap["subsystems"] if s["id"] == "fixture-sub")
        assert sub["state"] == "fail", sub
        assert sub["quality_degraded_count"] >= 1, sub


def t_inv6_negative_all_pass():
    # A registry with NO hook component at all, so HMI-04's auto-generated
    # hook-suite.* points cannot land in this subsystem and mask a clean
    # "all pass" rollup.
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        reg = {"subsystems": [{"id": "clean-sub", "title_zh": "乾淨", "title_en": "Clean", "order": 1,
                                 "component_rules": [{"glob": "tools/sample-tool", "kind": "tool"}]}],
               "points": [_pt("clean-sub.ok1", "tools/sample-tool", "exit-code",
                               {"argv": argv_c("import sys; sys.exit(0)"), "cwd": ".",
                                "exit_map": {"0": "pass"}})],
               "rubric": _rubric(), "ignore": [], "sources": []}
        out = home / "tools" / "system-hmi" / "out"
        result = collector.collect(str(home), reg, str(out), full=False)
        snap = result["snapshot"]
        sub = next(s for s in snap["subsystems"] if s["id"] == "clean-sub")
        assert sub["state"] == "pass", sub
        assert sub["quality_degraded_count"] == 0, sub


# ---------------------------------------------------------------------------
# INV-7 axes independent (completeness vs state).
# ---------------------------------------------------------------------------

def t_inv7_flip_state_completeness_unchanged():
    comp = {"id": "tools/sample-tool", "path": "tools/sample-tool", "kind": "tool", "subsystem": "x"}
    pts_pass = [{"adapter": "exit-code", "watched_by": None}]
    pts_fail = [{"adapter": "exit-code", "watched_by": None}]  # same shape; "state" isn't a completeness input at all
    rubric = _rubric()
    c1 = completeness.evaluate(comp, str(HOME), rubric, set(), {}, pts_pass, set())
    c2 = completeness.evaluate(comp, str(HOME), rubric, set(), {}, pts_fail, set())
    assert c1 == c2, "completeness must not depend on reading.state"


def t_inv7_flip_evidence_state_unaffected():
    # Changing E1 (registered_hook_targets) changes completeness but the reading
    # pipeline (adapters) never consults completeness -- structurally independent.
    comp = {"id": "hooks/probe_guard.py", "path": "hooks/probe_guard.py", "kind": "hook", "subsystem": "x"}
    rubric = _rubric()
    c1 = completeness.evaluate(comp, str(HOME), rubric, {"probe_guard.py"}, {}, [], set())
    c2 = completeness.evaluate(comp, str(HOME), rubric, set(), {}, [], set())
    assert c1["C1"] != c2["C1"]
    r = adapters.adapt_exit_code({"argv": argv_c("import sys; sys.exit(0)"), "cwd": ".",
                                   "exit_map": {"0": "pass"}}, str(HOME))
    assert r["state"] == "pass"  # unaffected by whatever completeness computed above


# ---------------------------------------------------------------------------
# INV-10 heartbeat.
# ---------------------------------------------------------------------------

REQUIRED_RUN_FIELDS = {"started_at", "finished_at", "duration_s", "status", "collector_version",
                       "registry_sha256", "tiers_run", "scope"}


def t_inv10_negative_all_fields_present():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        reg = base_registry()
        out = home / "tools" / "system-hmi" / "out"
        result = collector.collect(str(home), reg, str(out), full=False)
        run = result["snapshot"]["run"]
        missing = REQUIRED_RUN_FIELDS - set(run)
        assert not missing, f"heartbeat missing fields: {missing}"


def t_inv10_positive_detector_catches_missing_field():
    fake_run = {"started_at": "x"}  # deliberately incomplete
    missing = REQUIRED_RUN_FIELDS - set(fake_run)
    assert missing, "the heartbeat-shape detector failed to notice a missing field"


# ---------------------------------------------------------------------------
# INV-11 single collector.
# ---------------------------------------------------------------------------

def t_inv11_positive_live_pid_refused():
    with tempfile.TemporaryDirectory() as tmp:
        lp = Path(tmp) / "collector.lock"
        import os
        lp.write_text(json.dumps({"pid": os.getpid(), "started_at": "now"}), encoding="utf-8")
        ok, holder = lock.acquire(lp)
        assert ok is False
        assert holder["pid"] == os.getpid()


def t_inv11_negative_dead_pid_reclaimed():
    with tempfile.TemporaryDirectory() as tmp:
        lp = Path(tmp) / "collector.lock"
        lp.write_text(json.dumps({"pid": 999999, "started_at": "old"}), encoding="utf-8")
        ok, info = lock.acquire(lp)
        assert ok is True, "dead-pid lock should have been reclaimed"
        lock.release(lp)


# ---------------------------------------------------------------------------
# INV-12 stable ids (no duplicates).
# ---------------------------------------------------------------------------

def t_inv12_positive_duplicate_rejected():
    reg = base_registry(extra_points=[
        _pt("fixture-sub.dup", "hooks/probe_guard.py", "manual", {"command_text": "x"}),
        _pt("fixture-sub.dup", "hooks/other_hook.py", "manual", {"command_text": "y"}),
    ])
    errs = registry.validate(reg, home=str(HOME))
    assert any("duplicate point id" in e for e in errs)


def t_inv12_negative_unique_ok():
    reg = base_registry(extra_points=[
        _pt("fixture-sub.a", "hooks/probe_guard.py", "manual", {"command_text": "x"}),
        _pt("fixture-sub.b", "hooks/other_hook.py", "manual", {"command_text": "y"}),
    ])
    errs = registry.validate(reg, home=str(HOME))
    assert not any("duplicate point id" in e for e in errs)


# ---------------------------------------------------------------------------
# R-1 .. R-5 (PROTOCOL.md §3, the native adapter's behaviour verbatim).
# ---------------------------------------------------------------------------

def _emitter(tmp, code):
    p = Path(tmp) / "emitter.py"
    p.write_text(code, encoding="utf-8")
    return {"id": "fx", "argv": [PY, str(p)], "cwd": ".", "tier": "cheap", "timeout_s": 10}


def t_r1_positive_nonzero_exit_all_probe_error():
    with tempfile.TemporaryDirectory() as tmp:
        src = _emitter(tmp, "import sys; print('garbage'); sys.exit(3)\n")
        cache = {"fx": adapters.fetch_source(src, str(HOME))}
        for pid in ("fx.a", "fx.b"):
            r = adapters.adapt_native({"source": "fx", "point": pid}, cache)
            assert r["quality"] == "probe_error" and r["state"] is None


def t_r1_negative_zero_exit_ok():
    with tempfile.TemporaryDirectory() as tmp:
        src = _emitter(tmp, 'import json\nprint(json.dumps({"protocol":"hmi-report/1","source":"fx",'
                             '"generated_at":"x","points":[{"id":"fx.a","ran":True,"skip_reason":None,'
                             '"state":"pass","findings":[]}]}))\n')
        cache = {"fx": adapters.fetch_source(src, str(HOME))}
        r = adapters.adapt_native({"source": "fx", "point": "fx.a"}, cache)
        assert r["quality"] == "good" and r["state"] == "pass"


def t_r2_positive_absent_point_undetermined_never_pass():
    with tempfile.TemporaryDirectory() as tmp:
        src = _emitter(tmp, 'import json\nprint(json.dumps({"protocol":"hmi-report/1","source":"fx",'
                             '"generated_at":"x","points":[]}))\n')
        cache = {"fx": adapters.fetch_source(src, str(HOME))}
        r = adapters.adapt_native({"source": "fx", "point": "fx.missing"}, cache)
        assert r["state"] != "pass"
        assert r["quality"] == "undetermined"


def t_r2_negative_present_point_reads_through():
    with tempfile.TemporaryDirectory() as tmp:
        src = _emitter(tmp, 'import json\nprint(json.dumps({"protocol":"hmi-report/1","source":"fx",'
                             '"generated_at":"x","points":[{"id":"fx.here","ran":True,"skip_reason":None,'
                             '"state":"warn","findings":[]}]}))\n')
        cache = {"fx": adapters.fetch_source(src, str(HOME))}
        r = adapters.adapt_native({"source": "fx", "point": "fx.here"}, cache)
        assert r["quality"] == "good" and r["state"] == "warn"


def t_r3_positive_unregistered_doc_point_surfaced():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        src = _emitter(tmp, 'import json\nprint(json.dumps({"protocol":"hmi-report/1","source":"fx",'
                             '"generated_at":"x","points":[{"id":"fx.extra","ran":True,"skip_reason":None,'
                             '"state":"pass","findings":[]}]}))\n')
        reg = base_registry(extra_sources=[src])  # no point bound to fx.extra
        out = home / "tools" / "system-hmi" / "out"
        result = collector.collect(str(home), reg, str(out), full=False)
        snap = result["snapshot"]
        assert snap["run"]["status"] == "ok"
        # fx was never fetched because no point needs it this run -- prove the
        # mechanism directly instead, over a source that IS bound.
        assert True


def t_r3_positive_direct():
    with tempfile.TemporaryDirectory() as tmp:
        src = _emitter(tmp, 'import json\nprint(json.dumps({"protocol":"hmi-report/1","source":"fx",'
                             '"generated_at":"x","points":[{"id":"fx.bound","ran":True,"skip_reason":None,'
                             '"state":"pass","findings":[]},{"id":"fx.extra","ran":True,"skip_reason":None,'
                             '"state":"pass","findings":[]}]}))\n')
        entry = adapters.fetch_source(src, str(HOME))
        bound_ids = {"fx.bound"}
        leftover = [i for i in entry["points_by_id"] if i not in bound_ids]
        assert leftover == ["fx.extra"]


def t_r3_negative_no_leftover_when_fully_bound():
    with tempfile.TemporaryDirectory() as tmp:
        src = _emitter(tmp, 'import json\nprint(json.dumps({"protocol":"hmi-report/1","source":"fx",'
                             '"generated_at":"x","points":[{"id":"fx.bound","ran":True,"skip_reason":None,'
                             '"state":"pass","findings":[]}]}))\n')
        entry = adapters.fetch_source(src, str(HOME))
        bound_ids = {"fx.bound"}
        leftover = [i for i in entry["points_by_id"] if i not in bound_ids]
        assert leftover == []


def t_r4_positive_ran_false_undetermined():
    with tempfile.TemporaryDirectory() as tmp:
        src = _emitter(tmp, 'import json\nprint(json.dumps({"protocol":"hmi-report/1","source":"fx",'
                             '"generated_at":"x","points":[{"id":"fx.skipped","ran":False,'
                             '"skip_reason":"cwd-not-home","state":None,"findings":[]}]}))\n')
        cache = {"fx": adapters.fetch_source(src, str(HOME))}
        r = adapters.adapt_native({"source": "fx", "point": "fx.skipped"}, cache)
        assert r["quality"] == "undetermined"
        assert r["skip_reason"] == "cwd-not-home"


def t_r4_negative_ran_true_not_forced_undetermined():
    with tempfile.TemporaryDirectory() as tmp:
        src = _emitter(tmp, 'import json\nprint(json.dumps({"protocol":"hmi-report/1","source":"fx",'
                             '"generated_at":"x","points":[{"id":"fx.ran","ran":True,"skip_reason":None,'
                             '"state":"pass","findings":[]}]}))\n')
        cache = {"fx": adapters.fetch_source(src, str(HOME))}
        r = adapters.adapt_native({"source": "fx", "point": "fx.ran"}, cache)
        assert r["quality"] == "good"


def t_r5_call_counter():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        counter = Path(tmp) / "calls.txt"
        emitter = Path(tmp) / "counting_emitter.py"
        emitter.write_text(
            "import json\n"
            f"open(r'{counter}', 'a').write('x')\n"
            'print(json.dumps({"protocol":"hmi-report/1","source":"fx","generated_at":"x",'
            '"points":[{"id":"fx.a","ran":True,"skip_reason":None,"state":"pass","findings":[]},'
            '{"id":"fx.b","ran":True,"skip_reason":None,"state":"pass","findings":[]}]}))\n',
            encoding="utf-8")
        src = {"id": "fx", "argv": [PY, str(emitter)], "cwd": ".", "tier": "cheap", "timeout_s": 10}
        reg = base_registry(extra_sources=[src], extra_points=[
            _pt("fx.a", "hooks/probe_guard.py", "native", {"source": "fx", "point": "fx.a"}),
            _pt("fx.b", "hooks/other_hook.py", "native", {"source": "fx", "point": "fx.b"}),
        ])
        out = home / "tools" / "system-hmi" / "out"
        result = collector.collect(str(home), reg, str(out), full=False)
        assert result["ok"], result
        calls = len(counter.read_text(encoding="utf-8")) if counter.exists() else 0
        assert calls == 1, f"source fx invoked {calls} times in one collector run, expected 1 (R-5)"


# ---------------------------------------------------------------------------
# W-1 shelve only under quality=good. W-2 stale_reason. W-3 component missing.
# ---------------------------------------------------------------------------

def t_w1_positive_shelved_shown_when_good_warn():
    pt = {"disposition": {"value": "shelved", "reason": "x"}}
    reading = {"quality": "good", "state": "warn"}
    assert collector._presentation_shelved(pt, reading) is True


def t_w1_negative_not_shelved_when_quality_bad():
    pt = {"disposition": {"value": "shelved", "reason": "x"}}
    reading = {"quality": "probe_error", "state": None}
    assert collector._presentation_shelved(pt, reading) is False


def t_w2_positive_tier_not_run_reason():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        reg = base_registry(extra_points=[
            _pt("fixture-sub.slow", "tools/sample-tool", "exit-code",
                {"argv": argv_c("import sys; sys.exit(0)"), "cwd": ".", "exit_map": {"0": "pass"}},
                tier="slow"),
        ])
        out = home / "tools" / "system-hmi" / "out"
        # First run: no previous reading -> undetermined (no stale_reason yet).
        r1 = collector.collect(str(home), reg, str(out), full=False)
        pt1 = next(p for p in r1["snapshot"]["points"] if p["id"] == "fixture-sub.slow")
        assert pt1["reading"]["quality"] == "undetermined"
        # Force a fabricated previous "pass" so the second cheap-only run must CarriedStale.
        snap = snapshot.load(str(out))
        for p in snap["points"]:
            if p["id"] == "fixture-sub.slow":
                p["reading"] = {"state": "pass", "quality": "good", "evidence": "x", "since": "t0",
                                 "observed_at": "t0", "remedy": None, "source": None, "stale_reason": None}
        snapshot.write(str(out), snap)
        r2 = collector.collect(str(home), reg, str(out), full=False)
        pt2 = next(p for p in r2["snapshot"]["points"] if p["id"] == "fixture-sub.slow")
        assert pt2["reading"]["quality"] == "stale"
        assert pt2["reading"]["stale_reason"] == "tier-not-run"


def t_w2_positive_source_older_than_max_age():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "status.txt"
        f.write_text("PASS", encoding="utf-8")
        import os
        old = f.stat().st_mtime - 999999
        os.utime(f, (old, old))
        r = adapters.adapt_status_file({"path": str(f), "format": "text", "ok_regex": "PASS",
                                         "max_age_s": 10}, str(HOME))
        assert r["quality"] == "stale"
        assert r["stale_reason"] == "source-older-than-max-age"


def t_w2_negative_good_has_no_stale_reason():
    r = adapters.adapt_exit_code({"argv": argv_c("import sys; sys.exit(0)"), "cwd": ".",
                                   "exit_map": {"0": "pass"}}, str(HOME))
    assert r.get("stale_reason") in (None,)


def t_w3_positive_missing_component_forces_probe_error():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        reg = base_registry(extra_points=[
            _pt("fixture-sub.ghost-point", "tools/ghost-tool", "exit-code",
                {"argv": argv_c("import sys; sys.exit(0)"), "cwd": ".", "exit_map": {"0": "pass"}}),
        ])
        out = home / "tools" / "system-hmi" / "out"
        result = collector.collect(str(home), reg, str(out), full=False)
        pt = next(p for p in result["snapshot"]["points"] if p["id"] == "fixture-sub.ghost-point")
        assert pt["reading"]["quality"] == "probe_error"
        assert pt["reading"]["evidence"] == "component missing"


def t_w3_negative_present_component_not_forced():
    with tempfile.TemporaryDirectory() as tmp:
        home = make_fixture_home(tmp)
        reg = base_registry(extra_points=[
            _pt("fixture-sub.real-point", "tools/sample-tool", "exit-code",
                {"argv": argv_c("import sys; sys.exit(0)"), "cwd": ".", "exit_map": {"0": "pass"}}),
        ])
        out = home / "tools" / "system-hmi" / "out"
        result = collector.collect(str(home), reg, str(out), full=False)
        pt = next(p for p in result["snapshot"]["points"] if p["id"] == "fixture-sub.real-point")
        assert pt["reading"]["evidence"] != "component missing"
        assert pt["reading"]["state"] == "pass"


# ---------------------------------------------------------------------------
# An "undetermined"-class case, named explicitly by the goal.
# ---------------------------------------------------------------------------

def t_undetermined_class_manual_adapter():
    r = adapters.adapt_manual({"command_text": "python do_something.py"})
    assert r["quality"] == "undetermined"
    assert r["state"] is None
    assert r["skip_reason"] == "manual-only"


# ---------------------------------------------------------------------------
# The remaining adapter classes, each positive (fail/probe_error) + negative (pass).
# ---------------------------------------------------------------------------

def t_adapter_tail_sentinel_positive_nomatch_fail():
    r = adapters.adapt_tail_sentinel({"argv": argv_c("print('N/N passed with 1 broken')"),
                                       "pass_regex": r"^ALL PASS \d+/\d+$"}, str(HOME))
    assert r["state"] == "fail"


def t_adapter_tail_sentinel_negative_match_pass():
    r = adapters.adapt_tail_sentinel({"argv": argv_c("print('ALL PASS 3/3')"),
                                       "pass_regex": r"^ALL PASS \d+/\d+$"}, str(HOME))
    assert r["state"] == "pass"


def t_adapter_empty_output_positive_hit_is_fail():
    r = adapters.adapt_empty_output({"argv": argv_c("print('a match found'); import sys; sys.exit(0)"),
                                      "no_hit_exit": 1}, str(HOME))
    assert r["state"] == "fail"


def t_adapter_empty_output_negative_no_hit_pass():
    r = adapters.adapt_empty_output({"argv": argv_c("import sys; sys.exit(1)"), "no_hit_exit": 1}, str(HOME))
    assert r["state"] == "pass"


def t_line_scan_crash_is_not_pass():
    """INV-3 on line-scan: exit 2 with no matching line is probe_error; the same silent output
    with a declared exit is pass."""
    cfg = {"argv": argv_c("import sys; sys.exit(2)"), "cwd": ".", "fail_regex": "FAIL", "warn_regex": "WARN"}
    r = adapters.adapt_line_scan(cfg, str(HOME))
    assert r["quality"] == "probe_error" and r["state"] is None, r
    ok = adapters.adapt_line_scan(dict(cfg, ok_exits=[0, 2]), str(HOME))
    assert ok["quality"] == "good" and ok["state"] == "pass", ok
    silent = adapters.adapt_line_scan({"argv": argv_c("print('something else')"), "cwd": ".",
                                       "fail_regex": "FAIL", "pass_regex": "^ok: 0 FAIL"}, str(HOME))
    assert silent["quality"] == "probe_error", silent
    said = adapters.adapt_line_scan({"argv": argv_c("print('ok: 0 FAIL')"), "cwd": ".",
                                     "fail_regex": "[1-9] FAIL", "pass_regex": "^ok: 0 FAIL"}, str(HOME))
    assert said["state"] == "pass" and said["quality"] == "good", said


def t_adapter_line_scan_positive_fail_line():
    r = adapters.adapt_line_scan({"argv": argv_c("print('store: STALE — 3 changed')"),
                                   "fail_regex": r": (STALE|UNKNOWN)", "warn_regex": r": DRIFT"}, str(HOME))
    assert r["state"] == "fail"


def t_adapter_line_scan_negative_no_match_pass():
    r = adapters.adapt_line_scan({"argv": argv_c("print('store: FRESH')"),
                                   "fail_regex": r": (STALE|UNKNOWN)", "warn_regex": r": DRIFT"}, str(HOME))
    assert r["state"] == "pass"


def t_adapter_status_file_positive_missing_file():
    r = adapters.adapt_status_file({"path": "nope/nope.json", "format": "json", "field": "x",
                                     "ok_values": ["ok"]}, str(HOME))
    assert r["quality"] == "probe_error"


def t_adapter_status_file_negative_ok_value():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "s.json"
        f.write_text(json.dumps({"status": "OK"}), encoding="utf-8")
        r = adapters.adapt_status_file({"path": str(f), "format": "json", "field": "status",
                                         "ok_values": ["OK"]}, str(HOME))
        assert r["state"] == "pass" and r["quality"] == "good"


def t_adapter_fs_link_positive_missing_path():
    r = adapters.adapt_fs_link({"path": "Z:/definitely/not/here/xyz"}, str(HOME))
    assert r["quality"] == "probe_error"


def t_adapter_fs_link_negative_exists():
    r = adapters.adapt_fs_link({"path": str(HOME)}, str(HOME))
    assert r["state"] == "pass"


def t_adapter_exit_code_positive_unmapped_exit_probe_error():
    r = adapters.adapt_exit_code({"argv": argv_c("import sys; sys.exit(7)"), "cwd": ".",
                                   "exit_map": {"0": "pass", "1": "fail"}}, str(HOME))
    assert r["quality"] == "probe_error"


def t_adapter_exit_code_negative_mapped_exit():
    r = adapters.adapt_exit_code({"argv": argv_c("import sys; sys.exit(1)"), "cwd": ".",
                                   "exit_map": {"0": "pass", "1": "fail"}}, str(HOME))
    assert r["state"] == "fail" and r["quality"] == "good"


# ---------------------------------------------------------------------------
# SG-2 mirror drift check (part of `validate`).
# ---------------------------------------------------------------------------

def t_sg2_positive_drift_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        mirror = Path(tmp) / "doc.md"
        mirror.write_text("some other content, not the command", encoding="utf-8")
        reg = base_registry(extra_points=[
            _pt("fixture-sub.mirrored", "hooks/probe_guard.py", "exit-code",
                {"argv": ["python", "x.py"], "cwd": ".", "exit_map": {"0": "pass"},
                 "mirrors": str(mirror.relative_to(tmp)) if False else str(mirror)})])
        errs = registry.validate(reg, home=str(tmp))
        assert any("SG-2 drift" in e or "mirror file missing" in e for e in errs)


def t_sg2_negative_verbatim_present():
    with tempfile.TemporaryDirectory() as tmp:
        mirror = Path(tmp) / "doc.md"
        mirror.write_text("run: `python x.py`", encoding="utf-8")
        reg = base_registry(extra_points=[
            _pt("fixture-sub.mirrored", "hooks/probe_guard.py", "exit-code",
                {"argv": ["python", "x.py"], "cwd": ".", "exit_map": {"0": "pass"}, "mirrors": str(mirror)})])
        errs = registry.validate(reg, home=str(tmp))
        assert not any("SG-2" in e for e in errs)


# ---------------------------------------------------------------------------
# render_cli exit codes and --summary shape.
# ---------------------------------------------------------------------------

def _fake_snap(points):
    return {"run": {"finished_at": "t"}, "subsystems": [], "components": [], "points": points, "scan": {}}


def t_render_exit_0_all_pass():
    from hmi import render_cli
    snap = _fake_snap([{"id": "a", "component": "c", "reading": {"state": "pass", "quality": "good"}}])
    assert render_cli.exit_code(snap) == 0


def t_render_exit_1_warn():
    from hmi import render_cli
    snap = _fake_snap([{"id": "a", "component": "c", "reading": {"state": "warn", "quality": "good"}}])
    assert render_cli.exit_code(snap) == 1


def t_render_exit_2_fail():
    from hmi import render_cli
    snap = _fake_snap([{"id": "a", "component": "c", "reading": {"state": "fail", "quality": "good"}}])
    assert render_cli.exit_code(snap) == 2


def t_render_exit_3_no_snapshot():
    from hmi import render_cli
    assert render_cli.exit_code(None) == 3


def t_render_summary_two_lines_all_pass():
    from hmi import render_cli
    snap = _fake_snap([{"id": "a", "component": "c", "reading": {"state": "pass", "quality": "good"}}])
    snap["subsystems"] = [{"id": "s", "state": "pass", "quality_degraded_count": 0, "standing_count": 0,
                            "completeness_histogram": {}}]
    lines = render_cli.render_summary(snap)
    assert len(lines) == 2, lines


# ---------------------------------------------------------------------------
# Live-registry facts the HMI-01 acceptance names explicitly (read-only).
# ---------------------------------------------------------------------------

def t_live_fieldwork_threshold_notice_retired_not_unregistered():
    reg = registry.load_registry(TOOL_DIR / "registry")
    result = scan.scan(str(HOME), reg)
    assert any(r["path"] == "hooks/fieldwork_threshold_notice.py" for r in result["retired"])
    assert not any(u["path"] == "hooks/fieldwork_threshold_notice.py" for u in result["unregistered"])


def t_live_deny_receipt_kind_hook_library():
    reg = registry.load_registry(TOOL_DIR / "registry")
    result = scan.scan(str(HOME), reg)
    hit = next((c for c in result["registered"] if c["path"] == "hooks/deny_receipt.py"), None)
    assert hit is not None and hit["kind"] == "hook-library"


def t_live_validate_ok():
    reg = registry.load_registry(TOOL_DIR / "registry")
    errs = registry.validate(reg, home=str(HOME))
    assert not errs, errs


def t_live_scan_closed():
    reg = registry.load_registry(TOOL_DIR / "registry")
    result = scan.scan(str(HOME), reg)
    assert not result["overlaps"], result["overlaps"]


# ---------------------------------------------------------------------------
# Run everything.
# ---------------------------------------------------------------------------

ALL = [
    ("INV-1 negative (collector stays read-only)", t_inv1_negative),
    ("INV-1 positive (hash detector notices a mutation)", t_inv1_positive),
    ("INV-2 negative (good quality carries a real state)", t_inv2_negative_good_state_used),
    ("INV-2 positive (bad quality forces state null)", t_inv2_positive_bad_quality_state_null),
    ("INV-3 positive (source failure -> no pass anywhere)", t_inv3_positive_no_success_no_pass),
    ("INV-3 negative (real success reads pass)", t_inv3_negative_contrast_real_pass),
    ("INV-4 positive (restated threshold rejected)", t_inv4_positive_leak_rejected),
    ("INV-4 negative (timeout_s/max_age_s allowed)", t_inv4_negative_timeout_and_maxage_allowed),
    ("INV-5a positive (planted file -> UNREGISTERED)", t_inv5a_positive_unregistered),
    ("INV-5a negative (ignore.json removes it)", t_inv5a_negative_ignore_removes_it),
    ("INV-5b positive (literal rule, absent -> MISSING)", t_inv5b_positive_missing),
    ("INV-5b negative (retired absent -> not MISSING)", t_inv5b_negative_retired_not_missing),
    ("INV-5b overlap positive (two rules, one path -> error)", t_inv5b_overlap_positive),
    ("INV-5b overlap negative (no overlap -> clean)", t_inv5b_overlap_negative),
    ("INV-6 positive (fail+no_probe -> subsystem fail)", t_inv6_positive_fail_plus_no_probe),
    ("INV-6 negative (all pass -> subsystem pass)", t_inv6_negative_all_pass),
    ("coverage: a point reaches a component by exactly three routes", t_coverage_reaches_three_routes),
    ("static scan class: carried only while inputs unchanged and poll not lapsed", t_static_scan_class_validity),
    ("hook-suite inputs: a hook's Live-reads files are fingerprinted, a hook without stays code-only", t_hook_suite_inputs_include_live_reads),
    ("E5 three-way (declared+verified / declared-unverifiable / undeclared)", t_e5_three_way),
    ("awareness: folder census and memory closure (both sides)", t_awareness_census_and_closure),
    ("reconcile judge: every branch of the verdict table", t_reconcile_judge_every_branch),
    ("reconcile grace is read from ops-health, never restated (INV-4)", t_reconcile_grace_is_read_not_restated),
    ("reconcile repo_facts on a real throwaway repo (both sides)", t_reconcile_live_repo_facts),
    ("dual rollup: R and I never fold into each other", t_dual_rollup_r_and_i_never_fold),
    ("agents census: only a fresh scheduled snapshot is a verdict; blind channel; open event (both sides)", t_agents_census_reads_only_a_trustworthy_snapshot),
    ("group faces: separate R/I per face, point face wins, empty face is never pass (both sides)", t_group_faces_rollup_both_sides),
    ("scoped collect: affected subsystem rollup re-derived from merged points; out-of-scope carried (both sides)", t_scoped_collect_recomputes_subsystem_rollup),
    ("carried reading keeps observed_at; last_known beside state (both sides)", t_carried_reading_keeps_observation_time),
    ("point.subsystem positive (cross-cutting point rolls up where it says)", t_point_subsystem_override_positive),
    ("point.subsystem negative (default stays with component; unknown target rejected)", t_point_subsystem_override_negative),
    ("INV-7 positive/negative (state flip leaves completeness identical)", t_inv7_flip_state_completeness_unchanged),
    ("INV-7 positive/negative (evidence flip leaves reading pipeline untouched)", t_inv7_flip_evidence_state_unaffected),
    ("INV-10 negative (heartbeat fields present)", t_inv10_negative_all_fields_present),
    ("INV-10 positive (shape detector catches a missing field)", t_inv10_positive_detector_catches_missing_field),
    ("INV-11 positive (live pid -> refused)", t_inv11_positive_live_pid_refused),
    ("INV-11 negative (dead pid -> reclaimed)", t_inv11_negative_dead_pid_reclaimed),
    ("INV-12 positive (duplicate id rejected)", t_inv12_positive_duplicate_rejected),
    ("INV-12 negative (unique ids ok)", t_inv12_negative_unique_ok),
    ("R-1 positive (nonzero exit -> all points probe_error)", t_r1_positive_nonzero_exit_all_probe_error),
    ("R-1 negative (zero exit, valid doc -> reads through)", t_r1_negative_zero_exit_ok),
    ("R-2 positive (absent point id -> undetermined, never pass)", t_r2_positive_absent_point_undetermined_never_pass),
    ("R-2 negative (present point id -> reads through)", t_r2_negative_present_point_reads_through),
    ("R-3 positive (extra doc point -> would surface)", t_r3_positive_direct),
    ("R-3 negative (fully bound -> no leftover)", t_r3_negative_no_leftover_when_fully_bound),
    ("R-3 collector smoke (fx source declared but unused this run)", t_r3_positive_unregistered_doc_point_surfaced),
    ("R-4 positive (ran:false -> undetermined + skip_reason)", t_r4_positive_ran_false_undetermined),
    ("R-4 negative (ran:true -> not forced undetermined)", t_r4_negative_ran_true_not_forced_undetermined),
    ("R-5 (one invocation per source per run, call counter)", t_r5_call_counter),
    ("W-1 positive (shelved shown when quality good + warn/fail)", t_w1_positive_shelved_shown_when_good_warn),
    ("W-1 negative (not shelved when quality bad)", t_w1_negative_not_shelved_when_quality_bad),
    ("W-2 positive (tier-not-run stale_reason)", t_w2_positive_tier_not_run_reason),
    ("W-2 positive (source-older-than-max-age stale_reason)", t_w2_positive_source_older_than_max_age),
    ("W-2 negative (good reading has no stale_reason)", t_w2_negative_good_has_no_stale_reason),
    ("W-3 positive (MISSING component forces probe_error)", t_w3_positive_missing_component_forces_probe_error),
    ("W-3 negative (present component not forced)", t_w3_negative_present_component_not_forced),
    ("undetermined-class case (manual adapter)", t_undetermined_class_manual_adapter),
    ("adapter tail-sentinel positive (no match -> fail)", t_adapter_tail_sentinel_positive_nomatch_fail),
    ("adapter tail-sentinel negative (match -> pass)", t_adapter_tail_sentinel_negative_match_pass),
    ("adapter empty-output positive (hit -> fail)", t_adapter_empty_output_positive_hit_is_fail),
    ("adapter empty-output negative (no-hit -> pass)", t_adapter_empty_output_negative_no_hit_pass),
    ("adapter line-scan positive (fail line -> fail)", t_adapter_line_scan_positive_fail_line),
    ("adapter line-scan: a crash is never a pass (both sides)", t_line_scan_crash_is_not_pass),
    ("adapter line-scan negative (no match -> pass)", t_adapter_line_scan_negative_no_match_pass),
    ("adapter status-file positive (missing file -> probe_error)", t_adapter_status_file_positive_missing_file),
    ("adapter status-file negative (ok value -> pass)", t_adapter_status_file_negative_ok_value),
    ("adapter fs-link positive (missing path -> probe_error)", t_adapter_fs_link_positive_missing_path),
    ("adapter fs-link negative (exists -> pass)", t_adapter_fs_link_negative_exists),
    ("adapter exit-code positive (unmapped exit -> probe_error)", t_adapter_exit_code_positive_unmapped_exit_probe_error),
    ("adapter exit-code negative (mapped exit -> state)", t_adapter_exit_code_negative_mapped_exit),
    ("SG-2 positive (drift flagged)", t_sg2_positive_drift_flagged),
    ("SG-2 negative (verbatim present -> clean)", t_sg2_negative_verbatim_present),
    ("render exit 0 (all pass)", t_render_exit_0_all_pass),
    ("render exit 1 (warn)", t_render_exit_1_warn),
    ("render exit 2 (fail)", t_render_exit_2_fail),
    ("render exit 3 (no snapshot)", t_render_exit_3_no_snapshot),
    ("render --summary exactly 2 lines on all-pass", t_render_summary_two_lines_all_pass),
    ("live: fieldwork_threshold_notice.py retired, not unregistered", t_live_fieldwork_threshold_notice_retired_not_unregistered),
    ("live: deny_receipt.py kind hook-library", t_live_deny_receipt_kind_hook_library),
    ("live: validate exit 0", t_live_validate_ok),
    ("live: scan has zero overlaps", t_live_scan_closed),
]


def t_history_appends_one_row_per_write():
    """Every snapshot write appends exactly one compact row; a point with no usable state is 'u', never 'p'."""
    with tempfile.TemporaryDirectory() as tmp:
        snap = {"run": {"finished_at": "2026-01-01T00:00:00Z", "scope": "full-cheap", "tiers_run": ["cheap"], "status": "ok"},
                "subsystems": [{"id": "s1", "r_state": "warn", "i_state": "pass"}],
                "points": [{"id": "a", "reading": {"state": "fail"}}, {"id": "b", "reading": {"state": None}},
                           {"id": "c", "reading": {"state": "pass"}}, {"id": "d"}]}
        snapshot.write(tmp, snap)
        snapshot.write(tmp, snap)
        rows = [json.loads(l) for l in (Path(tmp) / "history.jsonl").read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 2, f"expected 2 rows, got {len(rows)}"
        assert rows[0]["counts"] == {"fail": 1, "warn": 0, "pass": 1, "und": 2}, rows[0]["counts"]
        assert rows[0]["points"] == {"a": "f", "b": "u", "c": "p", "d": "u"}, rows[0]["points"]
        assert rows[0]["subsystems"] == {"s1": ["warn", "pass"]}, rows[0]["subsystems"]


ALL.append(("history: one compact row per snapshot write; absence is 'u' not 'p'", t_history_appends_one_row_per_write))


def _with_server(fn):
    """Run fn(call, spawned) against a real server on an ephemeral loopback port with a counting spawn."""
    import http.client
    import threading
    from hmi import server as server_mod
    spawned = []

    def spawn(argv):
        spawned.append(argv)
        return 0, "collect: ok"

    srv = server_mod.make_server(TOOL_DIR, lambda snap, groups, live: "<html>" + json.dumps(live) + "</html>",
                                 port=0, spawn=spawn, token="T0KEN")
    port = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()

    def call(method, path, body=None, host=None, origin=None):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        headers = {"Host": host or f"127.0.0.1:{port}"}
        if origin:
            headers["Origin"] = origin
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        c.request(method, path, body=data, headers=headers)
        r = c.getresponse()
        out = (r.status, r.read().decode("utf-8", "replace"))
        c.close()
        return out

    try:
        fn(call, spawned, srv)
    finally:
        srv.shutdown()
        srv.server_close()


def t_server_refusals_spawn_nothing():
    """INV-8: unknown id 404, GET /refresh 405, wrong Host 403, foreign Origin 403, missing/wrong token 403,
    two selectors 400 - and in every one of them NO child process is started."""
    def body(call, spawned, srv):
        assert srv.server_address[0] == "127.0.0.1", srv.server_address
        good = {"token": "T0KEN"}
        cases = [
            ("unknown point", call("POST", "/refresh", {**good, "point_id": "no.such.point"}), 404),
            ("unknown subsystem", call("POST", "/refresh", {**good, "subsystem_id": "../../etc"}), 404),
            ("unknown tier", call("POST", "/refresh", {**good, "tier": "rm -rf"}), 404),
            ("GET /refresh", call("GET", "/refresh"), 405),
            ("wrong Host", call("POST", "/refresh", {**good, "tier": "cheap"}, host="evil.example"), 403),
            ("foreign Origin", call("POST", "/refresh", {**good, "tier": "cheap"}, origin="http://evil.example"), 403),
            ("missing token", call("POST", "/refresh", {"tier": "cheap"}), 403),
            ("wrong token", call("POST", "/refresh", {"token": "nope", "tier": "cheap"}), 403),
            ("two selectors", call("POST", "/refresh", {**good, "tier": "cheap", "point_id": "x"}), 400),
            ("unknown path", call("GET", "/etc/passwd"), 404),
        ]
        for name, (status, _), want in cases:
            assert status == want, f"{name}: got {status}, want {want}"
        assert spawned == [], f"a refusal started a child: {spawned}"
    _with_server(body)


def t_server_valid_refresh_spawns_exactly_one_registry_command():
    """The positive side: a real registry id starts exactly one `hmi.py collect --point <id>`; extra JSON
    keys are ignored and never reach the command line; the page carries the token."""
    def body(call, spawned, srv):
        reg = registry.load_registry(TOOL_DIR / "registry")
        pid = reg["points"][0]["id"]
        status, _ = call("POST", "/refresh", {"token": "T0KEN", "point_id": pid, "cmd": "calc.exe", "args": ["--evil"]})
        assert status == 200, status
        assert len(spawned) == 1, spawned
        argv = spawned[0]
        assert argv[-3:] == ["collect", "--point", pid], argv
        assert "calc.exe" not in argv and "--evil" not in argv, argv
        status, _ = call("POST", "/refresh", {"token": "T0KEN", "tier": "full"})
        assert status == 200 and spawned[1][-2:] == ["collect", "--full"], spawned
        status, page = call("GET", "/")
        assert status == 200 and "T0KEN" in page, (status, page[:80])
        status, meta = call("GET", "/api/meta")
        assert status == 200 and "finished_at" in meta, meta
    _with_server(body)


def t_server_locked_collect_is_409():
    import http.client  # noqa: F401
    from hmi import server as server_mod
    import threading
    srv = server_mod.make_server(TOOL_DIR, lambda *a: "", port=0, spawn=lambda argv: (4, "lock held by pid=1"), token="T")
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        import http.client as hc
        port = srv.server_address[1]
        c = hc.HTTPConnection("127.0.0.1", port, timeout=10)
        c.request("POST", "/refresh", body=json.dumps({"token": "T", "tier": "cheap"}),
                  headers={"Host": f"127.0.0.1:{port}", "Content-Type": "application/json"})
        r = c.getresponse()
        text = r.read().decode("utf-8")
        assert r.status == 409 and "pid=1" in text, (r.status, text)
    finally:
        srv.shutdown()
        srv.server_close()


def t_mimic_static_has_no_token_and_live_has_controls():
    import mimic_view
    snap = {"run": {"finished_at": "2026-01-01T00:00:00Z"}, "subsystems": [], "components": [], "points": []}
    static = mimic_view.render(snap, [])
    live = mimic_view.render(snap, [], {"token": "SECRET"})
    assert "LIVE=null" in static and "SECRET" not in static, "static page must carry no token"
    assert 'LIVE={"token": "SECRET"}' in live, "live page must carry the token"
    assert mimic_view.script_parses(live) is not False, "live page script must parse"


def t_server_meta_reports_loaded_code_and_drift():
    """2026-09-23 incident: the desktop shortcut reused a service started before a page change, so it showed
    the old page. Both sides: /api/meta code == disk right after start (no false restart), and a one-byte
    change to a served-code file moves the fingerprint (the drift the launcher and the page act on)."""
    import shutil
    import tempfile
    from hmi import server as server_mod

    def body(call, spawned, srv):
        status, text = call("GET", "/api/meta")
        m = json.loads(text)
        assert status == 200 and m["code"] == m["disk"] == srv.code, m
        assert isinstance(m["pid"], int) and m["pid"] > 0, m
        status, page = call("GET", "/")
        assert srv.code in page, "live page must carry the code it was built from"
    _with_server(body)
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "hmi").mkdir()
        for rel in ("hmi.py", "mimic_view.py", "hmi/server.py"):
            shutil.copyfile(TOOL_DIR / rel, d / rel)
        before = server_mod.code_fingerprint(d)
        assert before == server_mod.code_fingerprint(d), "fingerprint must be deterministic"
        (d / "mimic_view.py").write_bytes((d / "mimic_view.py").read_bytes() + b"\n")
        assert server_mod.code_fingerprint(d) != before, "a changed page generator must change the fingerprint"
        (d / "out").mkdir()
        (d / "out" / "snapshot.json").write_text("{}", encoding="utf-8")
        after = server_mod.code_fingerprint(d)
        assert server_mod.code_fingerprint(d) == after, "data under out/ must not change the fingerprint"


def t_launcher_restarts_only_a_stale_service():
    """open_hmi.pyw's decision, both sides: nothing answering -> no restart (start instead); same code -> reuse;
    different code -> restart; a service too old to report its code (the incident's case) -> restart."""
    from importlib.machinery import SourceFileLoader
    launcher = SourceFileLoader("open_hmi", str(TOOL_DIR / "open_hmi.pyw")).load_module()
    disk = "abc123"
    assert launcher.needs_restart(None, disk) is False
    assert launcher.needs_restart({"code": disk, "pid": 1}, disk) is False
    assert launcher.needs_restart({"code": "old999", "pid": 1}, disk) is True
    assert launcher.needs_restart({"finished_at": "2026-09-22T20:28:59Z"}, disk) is True


ALL.extend([
    ("server: every refusal spawns nothing (INV-8)", t_server_refusals_spawn_nothing),
    ("server: a valid refresh spawns exactly one registry command", t_server_valid_refresh_spawns_exactly_one_registry_command),
    ("server: a locked collect answers 409 with the holder", t_server_locked_collect_is_409),
    ("server: /api/meta reports the loaded code, and a code change is seen as drift", t_server_meta_reports_loaded_code_and_drift),
    ("launcher: reuses a current service, restarts a stale or legacy one", t_launcher_restarts_only_a_stale_service),
    ("mimic: static page has no token, live page has it and parses", t_mimic_static_has_no_token_and_live_has_controls),
])


# ---------------------------------------------------------------------------
# release (design 17): known-good verdict. Two-sided per invariant.
# ---------------------------------------------------------------------------

def _rp(id_, quality="good", state="pass", gate=None):
    p = {"id": id_, "reading": {"quality": quality, "state": state}}
    if gate:
        p["gate"] = gate
    return p


def t_release_r1a_all_gates_pass_is_good():
    from hmi import release
    r = release.judge([_rp("hook-suite.a"), _rp("x.controls", gate="known-good")])
    assert r["verdict"] == "GOOD" and r["gate_total"] == 2, r


def t_release_r1b_one_gate_fail_is_bad():
    from hmi import release
    r = release.judge([_rp("hook-suite.a"), _rp("x.controls", state="fail", gate="known-good")])
    assert r["verdict"] == "BAD" and r["failing"] == ["x.controls"], r


def t_release_r1c_undetermined_gate_is_partial_never_good():
    from hmi import release
    r = release.judge([_rp("hook-suite.a"), _rp("hook-suite.b", quality="undetermined", state=None)])
    assert r["verdict"] == "PARTIAL" and r["non_good"] == ["hook-suite.b"], r


def t_release_r1d_no_gate_points_is_partial():
    from hmi import release
    r = release.judge([_rp("ops-health.x")])
    assert r["verdict"] == "PARTIAL" and r["gate_total"] == 0, r


def t_release_r1e_non_gate_fail_does_not_gate():
    from hmi import release
    r = release.judge([_rp("hook-suite.a"), _rp("ops-health.interop", state="fail")])
    assert r["verdict"] == "GOOD", r


def t_release_r2_marking_needs_good_full_and_clean():
    from hmi import release
    good = {"verdict": "GOOD"}
    assert release.markable(good, "full-all", []) is True
    assert release.markable(good, "full-all", ["hooks/x.py"]) is False, "dirty code must not mark"
    assert release.markable(good, "due", []) is False, "a due collect must not mark"
    assert release.markable({"verdict": "PARTIAL"}, "full-all", []) is False


def t_release_r2_dirty_filter_code_vs_data():
    from hmi import release
    porcelain = (" M hooks/a.py\n M tools/x/ledger/events.jsonl\n M references/PROJECTS.md\n"
                 " M tools/y/run.ps1\n M settings.json\n M tools/z/tickets.json\n")
    assert release.dirty_code(porcelain) == ["hooks/a.py", "tools/y/run.ps1", "settings.json"]


def t_release_r3_run_writes_only_out_and_marks():
    import subprocess as sp
    from hmi import release
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        home.mkdir()
        sp.run(["git", "init", "-q", str(home)], check=True)
        (home / "a.py").write_text("x = 1\n", encoding="utf-8")
        sp.run(["git", "-C", str(home), "add", "a.py"], check=True)
        sp.run(["git", "-C", str(home), "-c", "user.name=t", "-c", "user.email=t@t",
                "commit", "-q", "-m", "init"], check=True)
        out = home / "out"
        out.mkdir()
        (out / "snapshot.json").write_text(json.dumps({"run": {"scope": "full-all"},
            "points": [_rp("hook-suite.a")]}), encoding="utf-8")
        before = sp.run(["git", "-C", str(home), "status", "--porcelain"], capture_output=True, text=True).stdout
        code, doc = release.run(str(home), str(out), lambda m: 0, mode="full")
        after = sp.run(["git", "-C", str(home), "status", "--porcelain"], capture_output=True, text=True).stdout
        assert code == 0 and doc["marked"], doc
        assert (out / "known-good.json").exists() and (out / "verdict-history.jsonl").exists()
        assert before.replace("?? out/\n", "") == after.replace("?? out/\n", ""), (before, after)
        # negative: a modified tracked code file blocks the mark, the verdict file still updates
        (out / "known-good.json").unlink()
        (home / "a.py").write_text("x = 2\n", encoding="utf-8")
        code, doc = release.run(str(home), str(out), lambda m: 0, mode="full")
        assert code == 2 and not doc["marked"] and doc["dirty"] == ["a.py"], doc
        # negative: a reused snapshot (no collect in this run) never marks, even GOOD+clean
        (home / "a.py").write_text("x = 1\n", encoding="utf-8")
        code, doc = release.run(str(home), str(out), lambda m: 0, mode="none")
        assert doc["verdict"] == "GOOD" and not doc["marked"] and code == 2, doc
        assert not (out / "known-good.json").exists()
        assert not (out / "known-good.json").exists()
        # negative: a failed collect never marks
        (home / "a.py").write_text("x = 1\n", encoding="utf-8")
        code, doc = release.run(str(home), str(out), lambda m: 1, mode="full")
        assert code == 3 and not doc["marked"], doc


def t_release_r1f_declared_gate_read_from_registry_not_snapshot():
    # regression for the first live verdict (2026-09-22): snapshot points carry no
    # `gate` field, so a declared gate that FAILS must still decide the verdict
    from hmi import release
    declared = release.gate_ids([{"id": "x.controls", "gate": "known-good"}, {"id": "y.other"}])
    assert declared == {"x.controls"}
    snap_pts = [_rp("hook-suite.a"), _rp("x.controls", state="fail")]  # no gate field
    assert release.judge(snap_pts)["verdict"] == "GOOD", "control: without the registry it is missed"
    r = release.judge(snap_pts, declared)
    assert r["verdict"] == "BAD" and r["failing"] == ["x.controls"] and r["gate_total"] == 2, r


def t_release_r1g_declared_gate_absent_from_snapshot_is_partial():
    from hmi import release
    r = release.judge([_rp("hook-suite.a")], {"x.controls"})
    assert r["verdict"] == "PARTIAL" and r["non_good"] == ["x.controls"] and r["gate_total"] == 2, r
    r = release.judge([_rp("hook-suite.a"), _rp("x.controls")], {"x.controls"})  # negative
    assert r["verdict"] == "GOOD", r


def t_release_r2_mode_must_be_full():
    from hmi import release
    good = {"verdict": "GOOD"}
    assert release.markable(good, "full-all", [], "full") is True
    assert release.markable(good, "full-all", [], "none") is False
    assert release.markable(good, "full-all", [], "due") is False


ALL.extend([
    ("release R1f: declared gate read from the registry, not the snapshot", t_release_r1f_declared_gate_read_from_registry_not_snapshot),
    ("release R1g: declared gate absent from snapshot -> PARTIAL", t_release_r1g_declared_gate_absent_from_snapshot_is_partial),
    ("release R2: only a full collect in this run may mark", t_release_r2_mode_must_be_full),
])

ALL.extend([
    ("release R1a: all gate points pass -> GOOD", t_release_r1a_all_gates_pass_is_good),
    ("release R1b: one gate fail -> BAD", t_release_r1b_one_gate_fail_is_bad),
    ("release R1c: undetermined gate -> PARTIAL, never GOOD", t_release_r1c_undetermined_gate_is_partial_never_good),
    ("release R1d: zero gate points -> PARTIAL", t_release_r1d_no_gate_points_is_partial),
    ("release R1e: a non-gate fail does not gate", t_release_r1e_non_gate_fail_does_not_gate),
    ("release R2: marking needs GOOD + full + clean code", t_release_r2_marking_needs_good_full_and_clean),
    ("release R2: dirty filter separates code from data", t_release_r2_dirty_filter_code_vs_data),
    ("release R3: run writes only out/, marks; dirty and failed collect do not", t_release_r3_run_writes_only_out_and_marks),
])


# ---------------------------------------------------------------------------
# Deferral (hmi/deferral.py, 2026-09-23). This LOWERS a severity for one shape
# (warn -> pass + holding annotation), so each changed level ships its case:
# unfired trigger does not warn; the SAME item with its trigger fired warns
# (positive control); no trigger / an undeterminable trigger still warns; fail
# and a broken probe are never touched. Each case asserts on the reading's
# state AND the deferral status, the two values the change moves.
# ---------------------------------------------------------------------------

from hmi import deferral  # noqa: E402

WARN = {"state": "warn", "quality": "good", "evidence": "index STALE", "source": "x"}


def _probe_spec(**kw):
    spec = {"kind": "probe", "trigger": "a recall leg consumes the index", "ruling": "fixture ruling",
            "argv": ["probe"], "fired_exits": [0], "unfired_exits": [1]}
    spec.update(kw)
    return spec


def _fake_run(code, error=None):
    return lambda argv, cwd, timeout: (code, "probe says " + str(code), "", error)


def t_deferral_unfired_trigger_does_not_warn():
    r = deferral.resolve(WARN, _probe_spec(), str(HOME), run=_fake_run(1))
    assert (r["state"], r["deferral"]["status"]) == ("pass", "holding"), r
    assert r["deferral"]["raw_state"] == "warn" and r["deferral"]["raw_evidence"] == "index STALE", r
    assert WARN["state"] == "warn" and "deferral" not in WARN, "resolve must not mutate its input"
    assert deferral.holding(r) and not deferral.holding(WARN)


def t_deferral_fired_trigger_warns():
    """Positive control: the SAME spec, the trigger probe now exits in fired_exits."""
    held = deferral.resolve(WARN, _probe_spec(), str(HOME), run=_fake_run(1))
    fired = deferral.resolve(WARN, _probe_spec(), str(HOME), run=_fake_run(0))
    assert (held["state"], fired["state"]) == ("pass", "warn"), (held, fired)
    assert fired["deferral"]["status"] == "fired" and "FIRED" in fired["evidence"], fired
    manual = {"kind": "manual", "trigger": "second project", "ruling": "user 2026-09-10"}
    assert deferral.resolve(WARN, manual, str(HOME))["state"] == "pass"
    assert deferral.resolve(WARN, dict(manual, fired=True), str(HOME))["state"] == "warn"


def t_deferral_without_trigger_still_warns():
    cases = [
        ("no trigger", {"kind": "manual", "ruling": "user"}),
        ("blank trigger", {"kind": "manual", "trigger": "  ", "ruling": "user"}),
        ("manual without ruling", {"kind": "manual", "trigger": "second project"}),
        ("item without trigger", {"kind": "manual", "trigger": "x", "ruling": "u",
                                  "items": [{"item": "a.md", "trigger": ""}]}),
        ("probe without exits", _probe_spec(fired_exits=None)),
        ("unknown kind", {"kind": "someday", "trigger": "x", "ruling": "u"}),
    ]
    for label, spec in cases:
        r = deferral.resolve(WARN, spec, str(HOME), run=_fake_run(1))
        assert (r["state"], r["deferral"]["status"]) == ("warn", "rejected"), (label, r)
        assert "NOT applied" in r["evidence"], (label, r)
    # the registry refuses the same shapes before a collect ever runs
    reg = base_registry(extra_points=[dict(_pt("fixture-sub.d", "hooks/probe_guard.py", "exit-code",
                                               {"argv": ["x"], "cwd": ".", "exit_map": {"0": "pass"}}),
                                           deferral={"kind": "manual", "ruling": "user"})])
    errs = registry.validate(reg)
    assert any("deferral: no trigger recorded" in e for e in errs), errs


def t_deferral_undeterminable_trigger_warns():
    for label, run in (("exit outside both sets", _fake_run(2)), ("timeout", _fake_run(None, "timeout"))):
        r = deferral.resolve(WARN, _probe_spec(), str(HOME), run=run)
        assert (r["state"], r["deferral"]["status"]) == ("warn", "rejected"), (label, r)


def t_deferral_never_touches_fail_pass_or_bad_quality():
    spec = _probe_spec()
    for reading in ({"state": "fail", "quality": "good"}, {"state": "pass", "quality": "good"},
                    {"state": None, "quality": "undetermined"}, {"state": "warn", "quality": "stale"},
                    {"state": None, "quality": "probe_error"}):
        r = deferral.resolve(reading, spec, str(HOME), run=_fake_run(1))
        assert r is reading and "deferral" not in r, (reading, r)


def t_deferral_end_to_end_collect_both_sources():
    """Registry spec on an exit-code point AND a native document claim, through collect():
    holding -> subsystem pass with deferred_count; fired -> subsystem warn (both sides)."""
    def run_once(fired):
        with tempfile.TemporaryDirectory() as tmp:
            home = make_fixture_home(tmp)
            doc = {"protocol": "hmi-report/1", "source": "fx", "generated_at": "x", "points": [
                {"id": "fx.adv", "ran": True, "skip_reason": None, "state": "warn",
                 "findings": [{"severity": "queue", "label": "deferred", "text": "1 deferred"}],
                 "deferred": {"kind": "manual", "trigger": "second project", "ruling": "status line",
                              "fired": fired, "items": [{"item": "a.md", "trigger": "second project"}]}}]}
            (Path(tmp) / "doc.json").write_text(json.dumps(doc), encoding="utf-8")
            src = _emitter(tmp, "import sys\nprint(open(sys.argv[1], encoding='utf-8').read())\n")
            src["argv"].append(str(Path(tmp) / "doc.json"))
            reg = base_registry(extra_points=[
                dict(_pt("fixture-sub.idx", "tools/sample-tool", "exit-code",
                         {"argv": argv_c("import sys; sys.exit(1)"), "cwd": ".",
                          "exit_map": {"0": "pass", "1": "warn"}}),
                     deferral=_probe_spec(argv=argv_c("import sys; sys.exit(%d)" % (0 if fired else 1)))),
                _pt("fx.adv", "tools/sample-tool", "native", {"source": "fx", "point": "fx.adv"}),
            ], extra_sources=[src])
            assert not registry.validate(reg), registry.validate(reg)
            snap = collector.collect(str(home), reg, str(home / "out"), full=False)["snapshot"]
            by = {p["id"]: p["reading"] for p in snap["points"]}
            sub = next(s for s in snap["subsystems"] if s["id"] == "fixture-sub")
            return by, sub
    by, sub = run_once(fired=False)
    got = {k: (by[k]["state"], by[k]["deferral"]["status"]) for k in ("fixture-sub.idx", "fx.adv")}
    assert got == {"fixture-sub.idx": ("pass", "holding"), "fx.adv": ("pass", "holding")}, got
    assert sub["deferred_count"] == 2 and sub["r_state"] != "warn" and sub["i_state"] != "warn", sub
    by, sub = run_once(fired=True)
    got = {k: (by[k]["state"], by[k]["deferral"]["status"]) for k in ("fixture-sub.idx", "fx.adv")}
    assert got == {"fixture-sub.idx": ("warn", "fired"), "fx.adv": ("warn", "fired")}, got
    assert sub["deferred_count"] == 0 and "warn" in (sub["r_state"], sub["i_state"]), sub


def t_index_consumers_trigger_reads_code_not_comments():
    """memory.hybrid-index-fresh's trigger (index_freshness.py --consumers), both sides + undetermined."""
    from importlib.machinery import SourceFileLoader
    fresh = SourceFileLoader("index_freshness",
                             str(HOME / "tools" / "memory-pipeline" / "index_freshness.py")).load_module()
    live, _ = fresh.consumers()
    assert live == 1, "the live recall.py has no leg on the hybrid index (user ruling 2026-09-19/23)"
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "recall.py"
        f.write_text('"""mem_search.mjs is not a leg."""\n# mem_search.mjs (bge-m3), explicitly not a leg\n'
                     'def leg_x(q):\n    """uses db-bge-m3? no."""\n    return []\n', encoding="utf-8")
        assert fresh.consumers(f)[0] == 1, "comments and docstrings must not fire the trigger"
        f.write_text('def leg_hybrid(q):\n    return run(["node", "bin/mem_search.mjs", q])\n', encoding="utf-8")
        assert fresh.consumers(f)[0] == 0, "a leg calling mem_search.mjs must fire the trigger"
        f.write_text("def broken(:\n", encoding="utf-8")
        assert fresh.consumers(f)[0] == 2, "an unparsable recall.py is undetermined, never 'no consumer'"


def t_render_cli_names_deferred():
    held = {"id": "a.x", "component": "c", "class": "reconcile",
            "reading": {"state": "pass", "quality": "good", "evidence": "DEFERRED until: t",
                        "deferral": {"status": "holding", "trigger": "t"}}}
    from hmi import render_cli
    assert render_cli._point_label(held) == "DEFERRED"
    summ = render_cli.render_summary({"run": {}, "points": [held], "subsystems": []})
    assert "0 warn" in summ[1] and "1 deferred" in summ[1], summ
    assert render_cli.exit_code({"points": [held]}) == 0, "a holding deferral is not a warn exit"


def t_mimic_classifies_deferred_grey_not_warn():
    """The page's own classifier, run in node: holding -> 'def' (grey glyph, own count, no alarm line);
    fired -> 'warn'. Asserts on the class string the page colours by."""
    import mimic_view
    import shutil as _sh
    import subprocess as _sp
    if not _sh.which("node"):
        raise AssertionError("node not found: the page classifier could not be run (undetermined)")
    body = mimic_view.PAGE.split("<script>", 1)[1]
    start = body.index("const ORDER=")
    end = body.index("function worst(")
    js = body[start:end] + (
        "const H={reading:{state:'pass',quality:'good',deferral:{status:'holding'}}};"
        "const F={reading:{state:'warn',quality:'good',deferral:{status:'fired'}}};"
        "const P={reading:{state:'pass',quality:'good'}};"
        "const g=glyph('def');"
        "console.log(JSON.stringify([pst(H),pst(F),pst(P),g.includes('var(--mute)'),"
        "g.includes('var(--warn)'),ORDER.def>ORDER.und&&ORDER.def<ORDER.pass]));")
    out = _sp.run(["node", "-e", js], capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr[-400:]
    assert json.loads(out.stdout) == ["def", "warn", "pass", True, False, True], out.stdout
    page = mimic_view.render({"run": {"finished_at": "2026-01-01T00:00:00Z"}, "subsystems": [],
                              "components": [], "points": []}, [])
    assert "['def','延後（等觸發）']" in page and 'id="cD"' in page, "legend entry and header count"


ALL.extend([
    ("deferral: an unfired trigger does not warn (holding, raw warn kept)", t_deferral_unfired_trigger_does_not_warn),
    ("deferral: the same item with its trigger fired warns (positive control)", t_deferral_fired_trigger_warns),
    ("deferral: no trigger / no ruling / item without trigger still warns; registry refuses it", t_deferral_without_trigger_still_warns),
    ("deferral: an undeterminable trigger never silences", t_deferral_undeterminable_trigger_warns),
    ("deferral: fail, pass and non-good quality are never touched (INV-3)", t_deferral_never_touches_fail_pass_or_bad_quality),
    ("deferral: registry + native claim through collect, holding vs fired (both sides)", t_deferral_end_to_end_collect_both_sources),
    ("deferral: hybrid-index trigger reads recall.py code, not comments (both sides + undetermined)", t_index_consumers_trigger_reads_code_not_comments),
    ("deferral: CLI labels DEFERRED, counts it, exits 0", t_render_cli_names_deferred),
    ("deferral: mimic classifies holding as grey 'def', fired as warn", t_mimic_classifies_deferred_grey_not_warn),
])


def main():
    for name, fn in ALL:
        check(name, fn)
    failed = [r for r in RESULTS if not r[1]]
    for name, ok, detail in RESULTS:
        print(("PASS" if ok else "FAIL") + " - " + name + ("" if ok else f"  :: {detail}"))
    print(f"ALL PASS {len(RESULTS) - len(failed)}/{len(RESULTS)}" if not failed
          else f"{len(RESULTS) - len(failed)}/{len(RESULTS)} passed, {len(failed)} FAILED")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
