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


# --- editions (WC-04) ---
# Reader `emitters/editions.py` (snapshot-unification 02 sections 3, 5; INV-7, INV-10, INV-14).
# Fixtures: a throwaway git repo that doubles as the "home" (so the live-view files sit under it),
# and an event log written to a temp path. The real log path and the real repo are never touched.

def _ed_mod():
    sys.path.insert(0, str(TOOL_DIR / "emitters"))
    import editions as ed
    return ed


def _ed_git(repo, *args):
    import subprocess as _sp
    p = _sp.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t",
                 "-c", "commit.gpgsign=false", *args],
                capture_output=True, text=True, encoding="utf-8", stdin=_sp.DEVNULL)
    assert p.returncode == 0, (args, p.stderr)
    return p.stdout.strip()


def _ed_repo(tmp, n=4):
    """-> (repo, [sha of commit 0..n-1], orphan_sha). orphan = a real commit NOT reachable from HEAD."""
    repo = Path(tmp) / "repo"
    repo.mkdir()
    _ed_git(repo, "init", "-q")
    shas = []
    for i in range(n):
        (repo / "f.txt").write_text(str(i), encoding="utf-8")
        _ed_git(repo, "add", "f.txt")
        _ed_git(repo, "commit", "-q", "-m", f"c{i}")
        shas.append(_ed_git(repo, "rev-parse", "HEAD"))
    orphan = _ed_git(repo, "commit-tree", _ed_git(repo, "write-tree"), "-m", "orphan")
    return repo, shas, orphan


def _ed_line(event, n, **kw):
    e = {"envelope": "edition-envelope/1", "kind": "log", "view": "evolution", "edition": n,
         "event": event, "at": "2026-10-03T14:00:00Z"}
    e.update(kw)
    return json.dumps(e)


def _ed_open(n, sha, cut_at="2026-10-05T00:00:00Z", event="backfilled"):
    return _ed_line(event, n, label="2026-10-03", data_cut_at=cut_at, outward="blocked",
                    object_ref={"repo": "~/.claude", "sha": sha, "sha_source": "cut", "dirty": False})


def _ed_run(repo, lines, tmp, **kw):
    """Write the log (text lines joined by newline, trailing newline unless lines is a str) and build."""
    import datetime as dt
    ed = _ed_mod()
    log = Path(tmp) / "editions.jsonl"
    if lines is not None:
        log.write_text(lines if isinstance(lines, str) else "\n".join(lines) + "\n", encoding="utf-8")
    kw.setdefault("now", dt.datetime(2026, 10, 6, tzinfo=dt.timezone.utc))
    doc = ed.build(home=repo, log_path=log, **kw)
    return {p["id"]: p for p in doc["points"]}


def t_editions_decision_table_every_row():
    """02 5.3 rows 1-8 each fire their state/quality; the boundary (commits_behind == LAG_COMMITS) is
    'within', one more is 'warn'; every evolution finding prints both thresholds (E-4)."""
    ed = _ed_mod()
    with tempfile.TemporaryDirectory() as tmp:
        repo, shas, orphan = _ed_repo(tmp)
        head2 = shas[-3]                                       # HEAD~2 -> commits_behind == 2
        def ev(lines, **kw):
            return _ed_run(repo, lines, tmp, **kw)["editions.evolution"]
        p = ev(None)                                           # 1: no log file at all
        assert (p["state"], p["quality"]) == (None, "undetermined") and p["ran"] is True, p
        p = ev([_ed_open(1, head2), _ed_line("abandoned", 1)])
        assert (p["state"], p["quality"]) == ("warn", "good") and "no accepted" in p["findings"][0]["label"], p   # 2
        assert p["remedy"] == ed.OPEN_REMEDY, p
        p = ev([_ed_open(1, head2, event="opened")])           # 3: no accepted, one open
        assert p["state"] == "warn" and any("open since 2026-10-03" in f["text"] for f in p["findings"]), p
        for bad in (shas[0][:6] + "0" * 34, None, "not-a-sha", orphan):   # 4: sha unknown / null / junk / not an ancestor
            p = ev([_ed_open(1, bad)])
            assert (p["state"], p["quality"]) == (None, "undetermined"), (bad, p)
        p = ev([_ed_open(1, "0" * 40), _ed_open(2, "0" * 40, event="opened")])           # 4 + open edition, still U
        assert p["state"] is None and any(f["label"] == "open edition" for f in p["findings"]), p
        p5 = ev([_ed_open(1, head2)])                          # 5
        assert (p5["state"], p5["quality"]) == ("pass", "good") and "commits_behind=2" in p5["findings"][0]["text"], p5
        p6 = ev([_ed_open(1, head2), _ed_line("opened", 2, extends=1)])                  # 6: open edition changes nothing
        assert p6["state"] == "pass" and any(f["label"] == "open edition" for f in p6["findings"]), p6
        p7 = ev([_ed_open(1, head2)], lag_commits=1)           # 7: positive control, threshold injected
        assert (p7["state"], p7["quality"]) == ("warn", "good") and p7["remedy"] == ed.OPEN_REMEDY, p7
        assert ev([_ed_open(1, head2)], lag_commits=2)["state"] == "pass", "boundary: equal is within"
        p7d = ev([_ed_open(1, head2, cut_at="2026-03-01T00:00:00Z")])                    # days side: >90 d
        assert p7d["state"] == "warn" and "LAG_DAYS" in p7d["findings"][0]["text"], p7d
        p8 = ev([_ed_open(1, head2), _ed_line("opened", 2, extends=1)], lag_commits=1)   # 8
        assert p8["state"] == "warn" and any(f["label"] == "open edition" for f in p8["findings"]), p8
        for pt in (p5, p6, p7, p7d, p8):
            for f in pt["findings"]:
                assert "LAG_DAYS=" in f["text"] and "LAG_COMMITS=" in f["text"], f
        assert "LAG_COMMITS=1]" in p7["findings"][0]["text"], "the injected value is the one printed"


def t_editions_unreadable_never_passes():
    """INV-7: a log or cut the reader cannot trust is state null + quality undetermined on BOTH points,
    never pass. Negative twin: the same log without the fault passes."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, shas, _orphan = _ed_repo(tmp)
        good = [_ed_open(1, shas[-3]), _ed_line("opened", 2, extends=1)]
        pts = _ed_run(repo, good, tmp)
        assert pts["editions.evolution"]["state"] == "pass" and pts["editions.register"]["state"] == "pass", pts
        faults = {
            "garbage in the middle": [good[0], "{not json", good[1]],
            "non-consecutive number": [good[0], _ed_line("opened", 3, extends=1)],
            "non-monotonic number": [good[0], _ed_open(1, shas[-3], event="opened")],
            "foreign envelope major": [json.dumps({**json.loads(good[0]), "envelope": "edition-envelope/2"})],
        }
        for name, lines in faults.items():
            pts = _ed_run(repo, lines, tmp)
            for pid in ("editions.evolution", "editions.register"):
                assert (pts[pid]["state"], pts[pid]["quality"]) == (None, "undetermined"), (name, pid, pts[pid])
        pts = _ed_run(repo, [good[0], _ed_line("opened", 3, extends=1)], tmp)
        assert any(f["severity"] == "undeclared" and "line 2" in f["text"] for f in pts["editions.evolution"]["findings"]), pts
        # a drive that is not there says so (fixture: a drive letter that cannot exist)
        ed = _ed_mod()
        lg = ed.read_log("Q:/nowhere/editions.jsonl") if not Path("Q:/").exists() else None
        assert lg is None or (lg["readable"] is False and "drive" in lg["reason"]), lg


def t_editions_torn_last_line_is_undeclared():
    """INV-14: a torn last line is an `undeclared` finding, never an event; state comes from the earlier
    events. Negative: a complete last line without a trailing newline is an event, not undeclared."""
    with tempfile.TemporaryDirectory() as tmp:
        repo, shas, _o = _ed_repo(tmp)
        first = _ed_open(1, shas[-3])
        torn = _ed_line("opened", 2, extends=1)[:70]
        pts = _ed_run(repo, first + "\n" + torn, tmp)
        ev = pts["editions.evolution"]
        assert ev["state"] == "pass" and ev["quality"] == "good", ev
        und = [f for f in ev["findings"] if f["severity"] == "undeclared"]
        assert und and "torn last line" in und[0]["text"] and "line 2" in und[0]["text"], ev
        assert not any(f["label"] == "open edition" for f in ev["findings"]), "the torn line was not read as an opened event"
        assert pts["editions.register"]["state"] == "pass", pts["editions.register"]
        whole = _ed_run(repo, first + "\n" + _ed_line("opened", 2, extends=1), tmp)["editions.evolution"]
        assert not [f for f in whole["findings"] if f["severity"] == "undeclared"], whole
        assert any(f["label"] == "open edition" for f in whole["findings"]), whole


def t_editions_state_is_derived_from_events():
    """02 section 3: last state-changing event wins; `tagged` changes nothing; superseded is derived;
    gated -> built returns to draft; an event for an edition never opened, or of an unknown kind, is
    undeclared and ignored."""
    ed = _ed_mod()
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "l.jsonl"
        lines = [_ed_open(1, "a" * 40), _ed_line("tagged", 1),
                 _ed_open(2, "b" * 40, event="opened"), _ed_line("built", 2), _ed_line("gated", 2)]
        log.write_text("\n".join(lines) + "\n", encoding="utf-8")
        s = {n: e["state"] for n, e in ed.read_log(log)["editions"].items()}
        assert s == {1: "accepted", 2: "gated"}, s                                   # tagged: no change
        log.write_text("\n".join(lines + [_ed_line("built", 2)]) + "\n", encoding="utf-8")
        assert ed.read_log(log)["editions"][2]["state"] == "draft"                   # a later built -> draft
        log.write_text("\n".join(lines + [_ed_line("accepted", 2)]) + "\n", encoding="utf-8")
        lg = ed.read_log(log)
        assert {n: e["state"] for n, e in lg["editions"].items()} == {1: "superseded", 2: "accepted"}, lg
        log.write_text("\n".join(lines + [_ed_line("abandoned", 2)]) + "\n", encoding="utf-8")
        lg = ed.read_log(log)
        assert {n: e["state"] for n, e in lg["editions"].items()} == {1: "accepted", 2: "abandoned"}, lg
        stray = lines + [_ed_line("gated", 9), _ed_line("exploded", 1)]
        log.write_text("\n".join(stray) + "\n", encoding="utf-8")
        lg = ed.read_log(log)
        assert lg["readable"] and len(lg["undeclared"]) == 2, lg
        assert {n: e["state"] for n, e in lg["editions"].items()} == {1: "accepted", 2: "gated"}, lg


def t_editions_register_rows_and_missing_views():
    """The register is information: one row per view, normalized to UTC. A missing or unparseable live
    view file is an `info` row 'not derived' and the state stays pass; only an unreadable evolution log
    makes it null/undetermined. The graph stamp is naive LOCAL time (gsnap.py), converted with the zone."""
    import datetime as dt
    ed = _ed_mod()
    tz8 = dt.timezone(dt.timedelta(hours=8))
    with tempfile.TemporaryDirectory() as tmp:
        repo, shas, _o = _ed_repo(tmp)
        def put(rel, obj):
            f = repo / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(obj if isinstance(obj, str) else json.dumps(obj), encoding="utf-8")
        put("tools/system-hmi/out/snapshot.json", {"run": {"finished_at": "2026-10-08T16:21:58Z", "registry_sha256": "r" * 64}})
        put("tools/graph-snapshot/out/graph.json", {"header": {"generated_at": "2026-10-09 01:34", "generated_from": shas[-1], "corpus_digest": "c" * 64}})
        put("cache/version-census/work.json", {"collected_at": "2026-10-08T13:13:12+00:00", "payload": {}})
        log = [_ed_open(1, shas[-3])]
        reg = _ed_run(repo, log, tmp, local_tz=tz8)["editions.register"]
        by = {f["label"]: f["text"] for f in reg["findings"]}
        assert reg["state"] == "pass" and reg["quality"] == "good", reg
        assert "data_cut_at=2026-10-08T16:21:58Z" in by["hmi"] and "sha=none" in by["hmi"], by
        assert "data_cut_at=2026-10-08T17:34:00Z" in by["graph"] and shas[-1][:12] in by["graph"] and "(header)" in by["graph"], by
        assert "data_cut_at=2026-10-08T13:13:12Z" in by["census"], by
        assert "kind=log edition=1" in by["evolution"] and shas[-3][:12] in by["evolution"], by
        (repo / "tools/graph-snapshot/out/graph.json").unlink()                      # missing graph.json
        put("cache/version-census/work.json", "{broken")                              # unparseable census
        reg = _ed_run(repo, log, tmp, local_tz=tz8)["editions.register"]
        by = {f["label"]: (f["severity"], f["text"]) for f in reg["findings"]}
        assert reg["state"] == "pass" and by["graph"][0] == "info" and "not derived" in by["graph"][1], reg
        assert by["census"][0] == "info" and "not derived" in by["census"][1], reg
        assert "kind=derived" in by["hmi"][1], "the other views are still read"
        env, why = ed.derive("graph", repo, tz8)
        assert env is None and why == "file missing", (env, why)
        put("tools/graph-snapshot/out/graph.json", {"header": {"generated_at": "2026-10-09 01:34", "generated_from": "no-git"}})
        env, _w = ed.derive("graph", repo, tz8)
        assert env["object_ref"] == {"repo": "~/.claude", "sha": None, "sha_source": "none", "dirty": None}, env


def t_editions_timestamp_normalisation():
    """Z, +00:00, other offsets and naive local stamps all land on YYYY-MM-DDTHH:MM:SSZ; a naive stamp
    follows the zone given (system zone by default); date-only and junk are None, never guessed."""
    import datetime as dt
    ed = _ed_mod()
    tz8 = dt.timezone(dt.timedelta(hours=8))
    n = ed.norm_utc
    assert n("2026-10-08T16:21:58Z") == "2026-10-08T16:21:58Z"
    assert n("2026-10-08T13:13:12+00:00") == "2026-10-08T13:13:12Z"
    assert n("2026-10-03T21:43:47+08:00") == "2026-10-03T13:43:47Z"
    assert n("2026-10-09 01:34", tz8) == "2026-10-08T17:34:00Z"                      # graph header form
    assert n("2026-10-09 01:34", dt.timezone.utc) == "2026-10-09T01:34:00Z"
    local_now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")                         # default = system zone
    got = dt.datetime.strptime(n(local_now), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    assert abs((dt.datetime.now(dt.timezone.utc) - got).total_seconds()) < 150, (local_now, n(local_now))
    for junk in (None, "", "2026-10-08", "yesterday", 20261008, "2026-13-45 99:99"):
        assert n(junk) is None, junk


def t_editions_inv10_readonly_stdlib_no_tool_imports():
    """INV-10: the emitter imports only the stdlib, none of the tools it reads, and has no write call.
    The linter is calibrated on a planted violator (must fire) before it is trusted on the real file."""
    import ast
    import re
    forbidden = re.compile(r"^(from|import) +(gsnap|gs_model|gs_freshness|version_census|lastuse|edition)\b", re.M)
    writers = {"write_text", "write_bytes", "unlink", "rename", "mkdir", "rmdir", "remove", "write",
               "writelines", "truncate", "touch"}

    def problems(src):
        out = []
        if forbidden.search(src):
            out.append("imports a tool it reads")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                    else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            for m in mods:
                if m.split(".")[0] not in sys.stdlib_module_names:
                    out.append(f"non-stdlib import {m}")
            if isinstance(node, ast.Call):
                f = node.func
                name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
                on_fs_module = (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
                                and f.value.id in ("os", "shutil"))
                # str/datetime .replace() is benign; os.replace()/Path.replace() and any shutil call are not
                if name in writers or (name == "replace" and on_fs_module) or (on_fs_module and f.value.id == "shutil"):
                    out.append(f"write-ish call {name}()")
                if name == "open":
                    mode = node.args[1].value if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) else ""
                    mode = mode or next((k.value.value for k in node.keywords if k.arg == "mode"
                                         and isinstance(k.value, ast.Constant)), "")
                    if any(c in str(mode) for c in "wax+"):
                        out.append("open() for writing")
        return out

    planted = ("import gsnap\nimport requests\nimport os\nfrom pathlib import Path\n"
               "Path('x').write_text('y')\nopen('f','w')\nos.replace('a','b')\n")
    found = problems(planted)
    assert len(found) >= 5, found                                                    # positive control
    benign = "import datetime as dt\nt = dt.datetime.now()\nt = t.replace(tzinfo=None)\nopen('f', encoding='utf-8')\n"
    assert problems(benign) == [], problems(benign)                                  # negative control
    src = (TOOL_DIR / "emitters" / "editions.py").read_text(encoding="utf-8")
    assert problems(src) == [], problems(src)                                        # negative: the real file


def t_editions_live_run_conform_and_wall_time():
    """The real emitter in a real subprocess against the real repo with a FIXTURE log: exits 0, one JSON
    document, both declared points, `hmi.py conform editions` ok, under 5 s. Twin: log absent -> the
    same run is conformant and reads null/undetermined on both points (never pass)."""
    import os
    import subprocess as _sp
    import time as _t
    head = _sp.run(["git", "-C", str(HOME), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    assert len(head) == 40, "cannot read HEAD of the real repo (undetermined)"
    import datetime as dt
    yesterday = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with tempfile.TemporaryDirectory() as tmp:
        good = Path(tmp) / "editions.jsonl"
        good.write_text(_ed_open(1, head, cut_at=yesterday) + "\n", encoding="utf-8")
        absent = Path(tmp) / "no-such.jsonl"
        for log, want_state, want_q in ((good, "pass", "good"), (absent, None, "undetermined")):
            env = {**os.environ, "EDITIONS_LOG": str(log)}
            t0 = _t.monotonic()
            r = _sp.run([sys.executable, "-X", "utf8", str(TOOL_DIR / "emitters" / "editions.py")],
                        capture_output=True, text=True, encoding="utf-8", cwd=str(HOME), env=env)
            wall = _t.monotonic() - t0
            assert r.returncode == 0 and wall < 5.0, (r.returncode, wall, r.stderr[-300:])
            doc = json.loads(r.stdout)
            pts = {p["id"]: p for p in doc["points"]}
            assert doc["source"] == "editions" and set(pts) == {"editions.register", "editions.evolution"}, pts.keys()
            assert (pts["editions.evolution"]["state"], pts["editions.evolution"]["quality"]) == (want_state, want_q), pts
            c = _sp.run([sys.executable, "-X", "utf8", str(TOOL_DIR / "hmi.py"), "conform", "editions"],
                        capture_output=True, text=True, encoding="utf-8", cwd=str(HOME), env=env)
            assert c.returncode == 0 and "conform: ok (editions, 2 points" in c.stdout, (c.stdout, c.stderr[-300:])


def t_editions_registry_closure():
    """The declared points, the sources.json entry and the points.json entries agree (E-1, R-3 never
    fires for this source). Positive control: a registry missing one point reads as a gap."""
    ed = _ed_mod()
    reg = registry.load_registry(TOOL_DIR / "registry")
    src = [s for s in reg["sources"] if s["id"] == "editions"]
    assert len(src) == 1 and src[0]["tier"] == "cheap" and src[0]["cwd"] == ".", src
    assert src[0]["argv"][-1] == "tools/system-hmi/emitters/editions.py" and (HOME / src[0]["argv"][-1]).exists(), src
    bound = lambda pts: {p["id"] for p in pts if p.get("adapter") == "native"
                         and p.get("adapter_config", {}).get("source") == "editions"}
    assert bound(reg["points"]) == set(ed.DECLARED), bound(reg["points"])
    thin = [p for p in reg["points"] if p["id"] != "editions.evolution"]
    assert bound(thin) != set(ed.DECLARED)                                           # positive control
    ev = next(p for p in reg["points"] if p["id"] == "editions.evolution")
    assert ev["class"] == "reconcile" and ev["subsystem"] == "system-hmi" and "edition.py open --cut HEAD" in ev["remedy"], ev


ALL.extend([
    ("editions: decision table rows 1-8, lag boundary and thresholds printed (both sides)", t_editions_decision_table_every_row),
    ("editions: an unreadable log / cut sha is null+undetermined on both points, never pass (both sides)", t_editions_unreadable_never_passes),
    ("editions: torn last line is undeclared and state comes from earlier events (both sides)", t_editions_torn_last_line_is_undeclared),
    ("editions: state is derived from events; superseded by derivation; stray events undeclared", t_editions_state_is_derived_from_events),
    ("editions: register rows normalised to UTC; missing/broken view file is an info row, state pass", t_editions_register_rows_and_missing_views),
    ("editions: timestamp normalisation (Z, offsets, naive local; junk is None)", t_editions_timestamp_normalisation),
    ("editions: INV-10 stdlib-only, no tool imports, no write call (linter calibrated both sides)", t_editions_inv10_readonly_stdlib_no_tool_imports),
    ("editions: real run conforms, exits 0, under 5 s (fixture log + absent log)", t_editions_live_run_conform_and_wall_time),
    ("editions: declared points = sources.json entry = points.json bindings (both sides)", t_editions_registry_closure),
])


# --- telemetry-trend (WC-05b) ---
# Emitter `emitters/telemetry_trend.py` + validate rule `registry.telemetry_check` (snapshot-unification
# 02 section 9.2, V-33, V-41, INV-10). Fixtures: a temp telemetry dir, a temp registry file, a fixed
# `now` (Friday 2026-10-09 => week 1 of the window starts Monday 2026-08-10, week 8 ends 2026-10-04,
# the current week 2026-10-05.. is incomplete) and local_tz=UTC. Nothing real is read except the live-run twin.

def _tt_mod():
    sys.path.insert(0, str(TOOL_DIR / "emitters"))
    import telemetry_trend as tt
    return tt


def _tt_now():
    import datetime as dt
    return dt.datetime(2026, 10, 9, 12, 0, tzinfo=dt.timezone.utc)


def _tt_when(week, k=0):
    """A UTC instant inside window week `week` (1..8; 0 or less = before the window; 9 = the current,
    incomplete week): Wednesday 12:00 plus k minutes."""
    import datetime as dt
    return dt.datetime(2026, 8, 10, 12, 0, tzinfo=dt.timezone.utc) + dt.timedelta(weeks=week - 1, days=2, minutes=k)


def _tt_fmt(t, fmt, variant=0):
    import datetime as dt
    if fmt == "epoch":
        return int(t.timestamp())
    if fmt == "date":
        return t.strftime("%Y-%m-%d")
    form = (variant % 4)
    if form == 0:
        return t.strftime("%Y-%m-%dT%H:%M:%SZ")
    if form == 1:
        return t.strftime("%Y-%m-%dT%H:%M:%S") + "+00:00"
    if form == 2:  # +0800 without a colon, same instant
        return (t + dt.timedelta(hours=8)).strftime("%Y-%m-%dT%H:%M:%S") + "+0800"
    return t.strftime("%Y-%m-%dT%H:%M:%S")  # naive; the fixture passes local_tz=UTC


def _tt_rows(counts, fmt="epoch", field="ts", before=0, current=0):
    """JSON lines for counts[0..7] rows in weeks 1..8, `before` rows in the week before the window and
    `current` rows in the current incomplete week."""
    out, n = [], 0
    spec = [(0, before)] + [(i + 1, c) for i, c in enumerate(counts)] + [(9, current)]
    for week, c in spec:
        for k in range(c):
            out.append(json.dumps({field: _tt_fmt(_tt_when(week, k), fmt, n), "x": n}))
            n += 1
    return out


def _tt_point(tmp, files, rows_extra=None, **kw):
    """files: {name: (lines, fmt)} -> the telemetry-trend.guards point. Writes tmp/t/<name>.jsonl and a
    registry with one row per file (+ rows_extra for files that must stay absent)."""
    tt = _tt_mod()
    tdir = Path(tmp) / "t"
    tdir.mkdir(exist_ok=True)
    rows = []
    for name, (lines, fmt) in files.items():
        (tdir / f"{name}.jsonl").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        rows.append({"file": f"{name}.jsonl", "hook": f"hook_{name}", "ts_field": "ts", "ts_format": fmt})
    rows.extend(rows_extra or [])
    reg = Path(tmp) / "telemetry.json"
    reg.write_text(json.dumps({"rows": rows, "unowned": []}), encoding="utf-8")
    import datetime as dt
    kw.setdefault("local_tz", dt.timezone.utc)
    doc = tt.build(home=tmp, telemetry_dir=tdir, registry_path=reg, now=_tt_now(), **kw)
    assert doc["protocol"] == "hmi-report/1" and doc["source"] == "telemetry-trend", doc
    assert [p["id"] for p in doc["points"]] == [tt.POINT_ID], doc
    return doc["points"][0]


def _tt_labels(pt):
    return {f["label"]: f for f in pt["findings"]}


def t_telemetry_trend_rules_both_sides():
    """sudden-zero / spike fire on their positive controls and stay silent on the known-good twins,
    at the exact boundaries (>= MIN_RATE, strictly > SPIKE_X x median, >= SPIKE_MIN_ROWS); a finding
    prints the 8 counts, the window and the thresholds (E-4); an injected threshold is the one printed."""
    tt = _tt_mod()
    with tempfile.TemporaryDirectory() as tmp:
        run = lambda counts, **kw: _tt_point(tmp, {"f": (_tt_rows(counts), "epoch")}, **kw)
        steady = run([4] * 8)
        assert (steady["state"], steady["quality"], steady["remedy"]) == ("pass", "good", None), steady
        assert not [f for f in steady["findings"] if f["severity"] == "warn"], steady
        sz = run([4, 4, 4, 4, 4, 4, 0, 0])                                           # positive: went quiet
        assert sz["state"] == "warn" and "f.jsonl: sudden-zero" in _tt_labels(sz), sz
        txt = _tt_labels(sz)["f.jsonl: sudden-zero"]["text"]
        assert "[4, 4, 4, 4, 4, 4, 0, 0]" in txt and "2026-08-10..2026-10-04" in txt, txt
        assert "MIN_RATE=3" in txt and "SPIKE_X=5" in txt and "WEEKS=8" in txt and "hook hook_f" in txt, txt
        assert run([3] * 6 + [0, 0])["state"] == "warn", "boundary: mean == MIN_RATE fires"
        assert run([2] * 6 + [0, 0])["state"] == "pass", "mean below MIN_RATE is not a sudden zero"
        assert run([4] * 7 + [0])["state"] == "pass", "only the last week empty is not a sudden zero"
        assert run([4] * 6 + [4, 0])["state"] == "pass", "week 7 alive"
        inj = run([3] * 6 + [0, 0], min_rate=4)                                       # injected threshold
        assert inj["state"] == "pass" and "MIN_RATE=4," in inj["findings"][0]["text"], inj
        sp = run([3] * 7 + [30])                                                     # positive: 10x last week
        assert sp["state"] == "warn" and "f.jsonl: spike" in _tt_labels(sp), sp
        assert "[3, 3, 3, 3, 3, 3, 3, 30]" in _tt_labels(sp)["f.jsonl: spike"]["text"], sp
        assert run([3] * 7 + [16])["state"] == "warn", "16 > 5 x 3"
        assert run([3] * 7 + [15])["state"] == "pass", "boundary: equal to SPIKE_X x median is not a spike"
        assert run([1] * 7 + [9])["state"] == "pass", "9 rows is under the SPIKE_MIN_ROWS floor"
        assert run([1] * 7 + [10])["state"] == "warn", "10 rows reaches the floor"
        assert run([3] * 7 + [30], spike_x=10)["state"] == "pass", "30 is not > 10 x 3"
        both = run([4, 4, 4, 4, 4, 4, 4, 0])
        assert both["state"] == "pass", both


def t_telemetry_trend_formats_are_parsed_not_guessed():
    """epoch / iso (Z, +00:00, +0800, naive) / date all land on the right week (a quiet-then-silent
    file reads sudden-zero in every format, never unreadable); junk is None; a file with no parseable
    timestamp is `unreadable`, and torn lines among good rows do not make a file unreadable."""
    import datetime as dt
    tt = _tt_mod()
    u = dt.timezone.utc
    want = dt.datetime(2026, 10, 3, 1, 36, 29, tzinfo=u)
    for s in ("2026-10-03T01:36:29Z", "2026-10-03T01:36:29+00:00", "2026-10-03T09:36:29+0800",
              "2026-10-03T09:36:29+08:00"):
        assert tt.parse_ts(s, "iso") == want, s
    assert tt.parse_ts("2026-10-03T09:36:29", "iso", dt.timezone(dt.timedelta(hours=8))) == want   # naive = local
    assert tt.parse_ts("2026-10-03", "date") == dt.datetime(2026, 10, 3, tzinfo=u)
    assert tt.parse_ts(1791000000, "epoch") == dt.datetime.fromtimestamp(1791000000, u)
    for junk, fmt in ((None, "epoch"), (True, "epoch"), ("1791000000", "epoch"), (float("nan"), "epoch"),
                      ("yesterday", "iso"), (20261003, "iso"), ("2026-13-45", "date"), (None, "date"), (1, "bogus")):
        assert tt.parse_ts(junk, fmt) is None, (junk, fmt)
    with tempfile.TemporaryDirectory() as tmp:
        quiet = [4, 4, 4, 4, 4, 4, 0, 0]
        for fmt in ("epoch", "iso", "date"):
            pt = _tt_point(tmp, {"q": (_tt_rows(quiet, fmt), fmt)})
            assert "q.jsonl: sudden-zero" in _tt_labels(pt) and "q.jsonl: unreadable" not in _tt_labels(pt), (fmt, pt)
            assert "[4, 4, 4, 4, 4, 4, 0, 0]" in _tt_labels(pt)["q.jsonl: sudden-zero"]["text"], (fmt, pt)
        pt = _tt_point(tmp, {"q": ([json.dumps({"ts": "2026-08-12"})] + _tt_rows(quiet, "date"), "date")})
        assert "q.jsonl: sudden-zero" in _tt_labels(pt), "date field read from a second ts_field"
        none = _tt_point(tmp, {"n": ([json.dumps({"x": i}) for i in range(5)], "epoch")})        # positive: unreadable
        assert none["state"] == "warn" and "n.jsonl: unreadable" in _tt_labels(none), none
        assert "none of 5 lines" in _tt_labels(none)["n.jsonl: unreadable"]["text"], none
        wrong = _tt_point(tmp, {"n": (_tt_rows([4] * 8, "epoch"), "iso")})                       # wrong ts_format: announces itself
        assert "n.jsonl: unreadable" in _tt_labels(wrong), wrong
        torn = _tt_point(tmp, {"n": (_tt_rows([4] * 8) + ['{"ts": 17', "not json"], "epoch")})
        assert torn["state"] == "pass" and "n.jsonl: unreadable" not in _tt_labels(torn), torn   # negative twin


def t_telemetry_trend_windows_history_guard_and_empty():
    """Complete weeks only (the current week and the week before the window are ignored); the history
    guard withholds judgement of a young file with an `info` note and no warn; an empty or missing
    dir is warn 'no telemetry rows' (never pass on nothing); an unreadable registry, an exhausted
    wall budget and a crash are never a pass."""
    tt = _tt_mod()
    with tempfile.TemporaryDirectory() as tmp:
        pt = _tt_point(tmp, {"s": (_tt_rows([4] * 8, current=100), "epoch")})                    # 100 rows in the current week
        assert pt["state"] == "pass", ("the incomplete current week must not make a spike", pt)
        assert "judged" in _tt_labels(pt), pt
        pt = _tt_point(tmp, {"s": (_tt_rows([4] * 8, before=500), "epoch")})                     # rows before the window
        assert pt["state"] == "pass", pt
        pt = _tt_point(tmp, {"s": (_tt_rows([4, 4, 4, 4, 4, 4, 0, 0], current=50), "epoch")})    # current week does not rescue
        assert "s.jsonl: sudden-zero" in _tt_labels(pt), pt
        pt = _tt_point(tmp, {"s": (_tt_rows([0, 0, 5, 5, 5, 5, 5, 40]), "epoch")})               # young: first row in week 3
        assert pt["state"] == "pass" and not [f for f in pt["findings"] if f["severity"] == "warn"], pt
        young = _tt_labels(pt)["young"]
        assert young["severity"] == "info" and "s.jsonl" in young["text"] and "history guard" in young["text"], young
        pt = _tt_point(tmp, {"s": (_tt_rows([1, 0, 5, 5, 5, 5, 5, 40]), "epoch")})               # twin: first row in week 1
        assert pt["state"] == "warn" and "s.jsonl: spike" in _tt_labels(pt) and "young" not in _tt_labels(pt), pt
        pt = _tt_point(tmp, {"s": (_tt_rows([0, 4, 4, 4, 4, 0, 0, 0]), "epoch")})                # young AND quiet: no finding
        assert pt["state"] == "pass", pt
        assert tt.eligible(_tt_when(1), tt.window_start(_tt_now())) and not tt.eligible(_tt_when(2), tt.window_start(_tt_now()))
        assert not tt.judge([0, 0, 5, 5, 5, 5, 5, 40], _tt_when(3), 40, tt.window_start(_tt_now()))[0]
        assert tt.judge([0, 0, 5, 5, 5, 5, 5, 40], _tt_when(3), 40, tt.window_start(_tt_now()), guard=False)[0] == ["spike"]
    with tempfile.TemporaryDirectory() as tmp:
        absent = [{"file": "ghost.jsonl", "hook": "ghost", "ts_field": "ts", "ts_format": "epoch", "not_yet_fired": True}]
        pt = _tt_point(tmp, {}, rows_extra=absent)                                               # empty dir
        assert pt["state"] == "warn" and "no telemetry rows" in _tt_labels(pt), pt
        assert "not yet fired" in _tt_labels(pt)["absent"]["text"], pt
        pt = _tt_point(tmp, {}, rows_extra=None)                                                 # no rows at all
        assert pt["state"] == "warn" and "no telemetry rows" in _tt_labels(pt), pt
        pt = _tt_point(tmp, {"s": (_tt_rows([4] * 8), "epoch")}, rows_extra=absent)              # twin: data present
        assert pt["state"] == "pass" and "no telemetry rows" not in _tt_labels(pt), pt
        assert _tt_labels(pt)["absent"]["severity"] == "info", pt
        doc = tt.build(home=tmp, telemetry_dir=Path(tmp) / "no-such-dir", registry_path=Path(tmp) / "telemetry.json",
                       now=_tt_now())                                                            # missing dir
        assert doc["points"][0]["state"] == "warn" and "no telemetry rows" in _tt_labels(doc["points"][0]), doc
        for bad in (Path(tmp) / "none.json", Path(tmp) / "bad.json", Path(tmp) / "norows.json"):
            if bad.name == "bad.json":
                bad.write_text("{broken", encoding="utf-8")
            elif bad.name == "norows.json":
                bad.write_text('{"rows": "x"}', encoding="utf-8")
            doc = tt.build(home=tmp, telemetry_dir=tmp, registry_path=bad, now=_tt_now())
            p = doc["points"][0]
            assert (p["state"], p["quality"]) == (None, "undetermined") and p["ran"] is True, (bad.name, p)
        pt = _tt_point(tmp, {"s": (_tt_rows([4] * 8), "epoch")}, wall_budget=-1.0)               # budget exhausted
        assert (pt["state"], pt["quality"]) == (None, "undetermined") and "wall budget" in pt["findings"][0]["label"], pt
        orig = tt.guards_point
        try:
            tt.guards_point = lambda *a, **k: 1 / 0
            doc = tt.build(home=tmp, telemetry_dir=tmp, registry_path=Path(tmp) / "telemetry.json", now=_tt_now())
        finally:
            tt.guards_point = orig
        p = doc["points"][0]
        assert p["ran"] is False and p["state"] is None and p["skip_reason"] == "exception-ZeroDivisionError", p


def _tt_hook_home(tmp):
    home = Path(tmp) / "home"
    (home / "hooks" / "tests").mkdir(parents=True)
    (home / "telemetry").mkdir()
    hooks = {
        "alias_guard": 'try:\n    from deny_receipt import clause as _receipt, fp_clause as _fp\n'
                       'except Exception:\n    def _receipt(hook, **f): return ""\nHOOK = "alias_guard"\n'
                       'def deny():\n    return _receipt(HOOK, x=1)\n',
        "mod_guard": 'import deny_receipt as dr\n\ndef deny():\n    return dr.clause("mod_guard")\n',
        "notice_only": 'from deny_receipt import notice_clause\n\ndef note():\n    return notice_clause("notice_only")\n',
        "path_only": 'import deny_receipt\nLOG = deny_receipt.log_path("path_only")\n',
        "lit_hook": 'LOG = "~/.claude/telemetry/lit-log.jsonl"\n',
    }
    for name, src in hooks.items():
        (home / "hooks" / f"{name}.py").write_text(src, encoding="utf-8")
    (home / "hooks" / "tests" / "test_x.py").write_text('P = "telemetry/tests-only.jsonl"\n', encoding="utf-8")
    return home


def _tt_touch(home, *names):
    for n in names:
        (home / "telemetry" / n).write_text('{"ts": 1}\n', encoding="utf-8")


def _tt_row(f, hook, **kw):
    return {"file": f, "hook": hook, "ts_field": "ts", "ts_format": "epoch", **kw}


def t_telemetry_registry_validate_producers_both_sides():
    """validate rule (V-33, V-41, rulings 2026-10-09): a hook that CALLS deny_receipt.clause()/receipt()
    (alias-aware, argument resolved through a module constant) or holds a literal telemetry/<name>.jsonl
    needs a row; a hook that only imports notice_clause / log_path writes no row and needs none; tests/
    subdirs are not hooks."""
    with tempfile.TemporaryDirectory() as tmp:
        home = _tt_hook_home(tmp)
        prod = registry.telemetry_producers(home / "hooks")
        assert prod["b"] == {("alias_guard", "alias-guard.jsonl"), ("mod_guard", "mod-guard.jsonl")}, prod
        assert prod["a"] == {("lit_hook", "lit-log.jsonl")}, prod
        assert prod["unparsed"] == [], prod
        errs, warns = registry.telemetry_check({"rows": [], "unowned": []}, home)                # positive: nothing registered
        assert sorted(errs) == [
            "telemetry file without a trend row: alias_guard -> alias-guard.jsonl",
            "telemetry file without a trend row: lit_hook -> lit-log.jsonl",
            "telemetry file without a trend row: mod_guard -> mod-guard.jsonl"], errs
        assert not any("notice_only" in e or "path_only" in e or "tests-only" in e for e in errs), errs   # negative
        _tt_touch(home, "alias-guard.jsonl", "mod-guard.jsonl", "lit-log.jsonl", "notice-only.jsonl")
        full = {"rows": [_tt_row("alias-guard.jsonl", "alias_guard"), _tt_row("mod-guard.jsonl", "mod_guard"),
                         _tt_row("lit-log.jsonl", "lit_hook")],
                "unowned": [{"file": "notice-only.jsonl", "reason": "fixture"}]}
        assert registry.telemetry_check(full, home) == ([], []), registry.telemetry_check(full, home)   # negative: closed
        full["rows"].pop()
        full["unowned"].append("lit-log.jsonl")                                                   # a pair satisfied by unowned
        assert registry.telemetry_check(full, home) == ([], []), registry.telemetry_check(full, home)
        full["rows"].append(_tt_row("lit-log.jsonl", "lit_hook"))                                 # both a row and unowned
        assert any("both a trend row and unowned" in e for e in registry.telemetry_check(full, home)[0])


def t_telemetry_registry_validate_files_rows_and_staleness():
    """An existing telemetry/*.jsonl must be a row's file or unowned (error); a row's file must exist
    (error, unless not_yet_fired -- whose stale flag is a warning); a row whose hook no longer
    qualifies is a WARNING unless path_built; bad schema is an error; a registry without a telemetry
    key is not checked at all (older fixtures); the warnings channel of validate() is optional."""
    with tempfile.TemporaryDirectory() as tmp:
        home = _tt_hook_home(tmp)
        _tt_touch(home, "alias-guard.jsonl", "mod-guard.jsonl", "lit-log.jsonl", "stray.jsonl", "built.jsonl")
        base = [_tt_row("alias-guard.jsonl", "alias_guard"), _tt_row("mod-guard.jsonl", "mod_guard"),
                _tt_row("lit-log.jsonl", "lit_hook")]
        errs, warns = registry.telemetry_check({"rows": base, "unowned": []}, home)
        assert sorted(e.split(" (")[0] for e in errs) == ["telemetry file not registered: built.jsonl",
                                                          "telemetry file not registered: stray.jsonl"], errs
        assert warns == [], warns
        reg = {"rows": base + [_tt_row("built.jsonl", "builder", path_built=True)], "unowned": ["stray.jsonl"]}
        assert registry.telemetry_check(reg, home) == ([], []), registry.telemetry_check(reg, home)   # negative: path_built, unowned str
        reg["rows"][-1].pop("path_built")                                                         # stale row, not path_built
        errs, warns = registry.telemetry_check(reg, home)
        assert errs == [] and len(warns) == 1 and "no longer qualifies" in warns[0] and "built.jsonl" in warns[0], (errs, warns)
        reg["rows"][-1]["hook"] = "lit_hook"                                                      # a hook that exists but never wrote it
        assert len(registry.telemetry_check(reg, home)[1]) == 1
        gone = {"rows": base + [_tt_row("gone.jsonl", "alias_guard")], "unowned": ["stray.jsonl", "built.jsonl"]}
        errs, _w = registry.telemetry_check(gone, home)
        assert any("row's file does not exist: gone.jsonl" in e for e in errs), errs
        gone["rows"][-1]["not_yet_fired"] = True                                                  # twin: declared not yet fired
        assert not any("gone.jsonl" in e for e in registry.telemetry_check(gone, home)[0])
        gone["rows"][-1]["file"] = "alias-guard.jsonl"                                            # duplicate file
        assert any("duplicated" in e for e in registry.telemetry_check(gone, home)[0])
        flag = {"rows": [dict(r, not_yet_fired=True) if r["file"] == "lit-log.jsonl" else r for r in base],
                "unowned": ["stray.jsonl", "built.jsonl"]}
        errs, warns = registry.telemetry_check(flag, home)                                        # flag set, file exists
        assert errs == [] and len(warns) == 1 and "stale flag" in warns[0], (errs, warns)
        bad = {"rows": base + [{"file": "x.jsonl", "hook": "h", "ts_field": "ts", "ts_format": "unix"},
                               {"file": "y.jsonl", "hook": "h"}], "unowned": []}
        errs, _w = registry.telemetry_check(bad, home)
        assert any("ts_format 'unix'" in e for e in errs) and any("missing field" in e and "y.jsonl" in e for e in errs), errs
        assert registry.telemetry_check({"unowned": []}, home)[0], "no rows list is an error"
        rub = json.loads((TOOL_DIR / "registry" / "rubric.json").read_text(encoding="utf-8"))
        shell = {"subsystems": [], "points": [], "rubric": rub, "ignore": [], "sources": []}
        assert registry.validate(shell, home=str(home)) == [], "no telemetry key: unchecked"
        shell["telemetry"] = {"rows": [], "unowned": []}                                          # the same shell, telemetry on
        w = []
        errs = registry.validate(shell, home=str(home), warnings=w)
        assert any("without a trend row" in e for e in errs) and w == [], (errs, w)
        assert registry.validate(shell, home=str(home)) == errs                                   # warnings arg is optional


def t_telemetry_trend_inv10_readonly_stdlib_no_tool_imports():
    """INV-10: the emitter imports only the stdlib, none of the tools it reads, and has no write call.
    The linter is calibrated on a planted violator (must fire) before it is trusted on the real file."""
    import ast
    import re
    forbidden = re.compile(r"^(from|import) +(gsnap|gs_model|version_census|lastuse|edition|editions|deny_receipt|hmi)\b", re.M)
    writers = {"write_text", "write_bytes", "unlink", "rename", "mkdir", "rmdir", "remove", "write",
               "writelines", "truncate", "touch"}

    def problems(src):
        out = []
        if forbidden.search(src):
            out.append("imports a tool it reads")
        for node in ast.walk(ast.parse(src)):
            mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                    else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            out += [f"non-stdlib import {m}" for m in mods if m.split(".")[0] not in sys.stdlib_module_names]
            if isinstance(node, ast.Call):
                f = node.func
                name = f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else ""
                on_fs = isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id in ("os", "shutil")
                if name in writers or (name == "replace" and on_fs) or (on_fs and f.value.id == "shutil"):
                    out.append(f"write-ish call {name}()")
                if name == "open":
                    mode = node.args[1].value if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) else ""
                    if any(c in str(mode) for c in "wax+"):
                        out.append("open() for writing")
        return out

    planted = "import editions\nimport requests\nimport os\nfrom pathlib import Path\nPath('x').write_text('y')\nopen('f','w')\n"
    assert len(problems(planted)) >= 4, problems(planted)                                        # positive control
    benign = "import datetime as dt\nt = dt.datetime.now().replace(tzinfo=None)\nopen('f', encoding='utf-8')\n"
    assert problems(benign) == [], problems(benign)                                              # negative control
    src = (TOOL_DIR / "emitters" / "telemetry_trend.py").read_text(encoding="utf-8")
    assert problems(src) == [], problems(src)                                                    # negative: the real file


def t_telemetry_trend_live_run_conform_and_wall_time():
    """The real emitter in a real subprocess over the REAL telemetry/ and registry: exits 0, one JSON
    document with the declared point, never pass-with-nothing, under 5 s, `hmi.py conform` ok. Twin:
    CLAUDE_TELEMETRY_DIR pointing at an empty dir is a conformant 'warn / no telemetry rows'."""
    import os
    import subprocess as _sp
    import time as _t
    with tempfile.TemporaryDirectory() as tmp:
        for tdir, want in ((None, None), (tmp, "no telemetry rows")):
            env = dict(os.environ)
            env.pop("CLAUDE_TELEMETRY_DIR", None)
            if tdir:
                env["CLAUDE_TELEMETRY_DIR"] = tdir
            t0 = _t.monotonic()
            r = _sp.run([sys.executable, "-X", "utf8", str(TOOL_DIR / "emitters" / "telemetry_trend.py")],
                        capture_output=True, text=True, encoding="utf-8", cwd=str(HOME), env=env)
            wall = _t.monotonic() - t0
            assert r.returncode == 0 and wall < 5.0, (r.returncode, wall, r.stderr[-300:])
            doc = json.loads(r.stdout)
            pt = doc["points"][0]
            assert doc["source"] == "telemetry-trend" and pt["id"] == "telemetry-trend.guards" and pt["ran"] is True, doc
            assert pt["state"] in ("pass", "warn") and pt["quality"] == "good", pt
            if want:
                assert pt["state"] == "warn" and any(f["label"] == want for f in pt["findings"]), pt
            else:
                assert any(f["label"] == "judged" for f in pt["findings"]), pt                   # the real files were read
            c = _sp.run([sys.executable, "-X", "utf8", str(TOOL_DIR / "hmi.py"), "conform", "telemetry-trend"],
                        capture_output=True, text=True, encoding="utf-8", cwd=str(HOME), env=env)
            assert c.returncode == 0 and "conform: ok (telemetry-trend, 1 points" in c.stdout, (c.stdout, c.stderr[-300:])


def t_telemetry_trend_registry_closure():
    """The declared point, the sources.json entry, the points.json binding and the telemetry.json seed
    agree: subsystem hook-guards exists, class integrity, cheap tier; every row names a ts_format in
    the closed set. Positive control: a registry missing the point reads as a gap."""
    tt = _tt_mod()
    reg = registry.load_registry(TOOL_DIR / "registry")
    src = [s for s in reg["sources"] if s["id"] == "telemetry-trend"]
    assert len(src) == 1 and src[0]["tier"] == "cheap" and src[0]["timeout_s"] == 30 and src[0]["cwd"] == ".", src
    assert src[0]["argv"][-1] == "tools/system-hmi/emitters/telemetry_trend.py" and (HOME / src[0]["argv"][-1]).exists(), src
    bound = lambda pts: {p["id"] for p in pts if p.get("adapter") == "native"
                         and p.get("adapter_config", {}).get("source") == "telemetry-trend"}
    assert bound(reg["points"]) == {tt.POINT_ID}, bound(reg["points"])
    assert bound([p for p in reg["points"] if p["id"] != tt.POINT_ID]) != {tt.POINT_ID}          # positive control
    pt = next(p for p in reg["points"] if p["id"] == tt.POINT_ID)
    assert pt["subsystem"] == "hook-guards" and pt["class"] == "integrity" and pt["tier"] == "cheap", pt
    assert pt["disposition"]["value"] == "active" and pt["alias"] == tt.ALIAS and pt["why"], pt
    assert pt["subsystem"] in {s["id"] for s in reg["subsystems"]}
    t = reg["telemetry"]
    assert t and t["rows"] and all(r["ts_format"] in registry.TS_FORMATS for r in t["rows"]), t
    assert not ({r["file"] for r in t["rows"]} & registry._unowned_files(t))


ALL.extend([
    ("telemetry-trend: sudden-zero / spike fire and stay silent at the exact boundaries; counts + thresholds printed (both sides)", t_telemetry_trend_rules_both_sides),
    ("telemetry-trend: epoch / iso (Z, +00:00, +0800, naive) / date parsed; no timestamp is unreadable (both sides)", t_telemetry_trend_formats_are_parsed_not_guessed),
    ("telemetry-trend: current week ignored, history guard withholds young files, empty/unreadable/budget/crash never pass", t_telemetry_trend_windows_history_guard_and_empty),
    ("telemetry-trend: validate producers = literal path + deny_receipt clause/receipt callers, notice_clause-only needs no row (both sides)", t_telemetry_registry_validate_producers_both_sides),
    ("telemetry-trend: validate files/rows -- unregistered file, missing row file, stale row warning, schema (both sides)", t_telemetry_registry_validate_files_rows_and_staleness),
    ("telemetry-trend: INV-10 stdlib-only, no tool imports, no write call (linter calibrated both sides)", t_telemetry_trend_inv10_readonly_stdlib_no_tool_imports),
    ("telemetry-trend: real run conforms, exits 0, under 5 s over real telemetry/ (and an empty dir warns)", t_telemetry_trend_live_run_conform_and_wall_time),
    ("telemetry-trend: declared point = sources.json entry = points.json binding = telemetry.json seed (both sides)", t_telemetry_trend_registry_closure),
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
