#!/usr/bin/env python3
"""feedback-pool controls — two-sided, on a temp home; last line `ALL PASS n/n` (exit 0) or `FAIL k/n` (exit 1).

Covers: ledger.py feedback / feedback-fold (row shape, closed target vocabulary, deferred needs trigger);
every sensor S-1..S-7 with a positive and a negative fixture; the comparator (threshold, fold consumes by
time, deferred stays visible); missing sources are fail-soft; emit speaks hmi-report/1 (warn when due,
pass when not); target_of vocabulary. Nothing here touches the real ~/.claude.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
LEDGER = ROOT / "tools" / "process-ledger" / "ledger.py"
PY = sys.executable
RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  <- {str(detail)[:300]}"))


def run(args, env, inp=None):
    return subprocess.run([PY, "-X", "utf8", *map(str, args)], capture_output=True, text=True, env=env, input=inp, encoding="utf-8")


def main() -> int:
    sys.path.insert(0, str(HERE))
    import feedback as fb

    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / "home"
        for d in ("projects/proj", "cache/handoff", "telemetry", "tools/system-hmi/out", "ops/lessons",
                  "outputs/skill-reviews", "hooks", "skills/alpha", "skills/synced/z", "lse"):
            (home / d).mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, CLAUDE_CONFIG_DIR=str(home), FEEDBACK_HOME=str(home), LSE_RUN_HOME=str(home / "lse"),
                   PYTHONIOENCODING="utf-8")
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        os.environ["LSE_RUN_HOME"] = str(home / "lse")      # in-process collect() reads it too
        S = "ctl-session-a"
        (home / "projects" / "proj" / f"{S}.jsonl").write_text("{}\n", encoding="utf-8")

        print("[ledger writer]")
        r = run([LEDGER, "feedback", "--session", S, "--target", "skill:alpha", "--symptom", "step 3 wrong", "--action", "left",
                 "--proposal", "fix step 3"], env)
        lp = home / "projects" / "proj" / f"{S}.ledger.jsonl"
        rows = [json.loads(l) for l in lp.read_text(encoding="utf-8").splitlines()] if lp.is_file() else []
        check("feedback row appended beside the transcript with kind/id/target/action", r.returncode == 0 and rows and rows[-1]["kind"] == "feedback"
              and len(rows[-1]["id"]) == 8 and rows[-1]["action"] == "left" and rows[-1]["proposal"] == "fix step 3", r.stdout + r.stderr)
        r = run([LEDGER, "feedback", "--session", S, "--target", "widget:alpha", "--symptom", "x", "--action", "left"], env)
        check("negative: unknown target prefix refused", r.returncode != 0 and "prefix" in (r.stdout + r.stderr), r.stdout + r.stderr)
        r = run([LEDGER, "feedback", "--session", S, "--target", "skill:", "--symptom", "x", "--action", "left"], env)
        check("negative: empty target name refused", r.returncode != 0, r.stdout + r.stderr)
        r = run([LEDGER, "feedback-fold", "--session", S, "--target", "skill:alpha", "--outcome", "deferred", "--ref", "x"], env)
        check("negative: deferred fold without --trigger refused", r.returncode != 0 and "trigger" in (r.stdout + r.stderr), r.stdout + r.stderr)
        r = run([LEDGER, "add", "--session", S, "--subject", "s", "--choice", "c", "--reason", "r", "--reversible", "yes", "--origin", "model"], env)
        check("legacy decision row still writes (no kind)", r.returncode == 0 and "kind" not in json.loads(lp.read_text(encoding="utf-8").splitlines()[-1]), r.stdout + r.stderr)

        print("[S-1: unclassifiable target]")
        with tempfile.TemporaryDirectory() as td2:
            home2 = Path(td2) / "home"
            (home2 / "projects" / "p").mkdir(parents=True, exist_ok=True)
            lp2 = home2 / "projects" / "p" / "s.ledger.jsonl"
            # a row that never went through ledger.py's own prefix gate (hand-edited /
            # legacy jsonl): `target` matches none of TARGET_PREFIXES. The instrument
            # must call this undetermined and exclude it, never fold it into a target
            # of its own (AP-62).
            lp2.write_text(
                json.dumps({"kind": "feedback", "ts": 100, "target": "not-a-known-prefix",
                            "symptom": "x", "id": "aaaaaaaa", "action": "left"}) + "\n"
                + json.dumps({"kind": "feedback", "ts": 101, "target": "skill:alpha",
                              "symptom": "y", "id": "bbbbbbbb", "action": "left"}) + "\n",
                encoding="utf-8")
            pool2 = fb.collect(home2)
            check("undetermined: a ledger row whose target matches no TARGET_PREFIXES is excluded "
                  "from every target/count and reported as an S-1 sensor error, never folded into a "
                  "target of its own",
                  all(d["target"] != "not-a-known-prefix" for d in pool2["targets"])
                  and any(e["sensor"] == "S-1" and "undetermined" in e["error"] for e in pool2["sensor_errors"])
                  and pool2["totals"]["targets"] == 1 and pool2["totals"]["events"] == 1,
                  json.dumps({"targets": [d["target"] for d in pool2["targets"]], "errors": pool2["sensor_errors"]}))

        print("[sensors: empty home is fail-soft]")
        pool = fb.collect(home)
        check("collect on a home with one S-1 row: 1 target, 0 due, exit path clean", pool["totals"]["targets"] == 1 and pool["totals"]["due"] == 0, json.dumps(pool["totals"]))
        errs = {e["sensor"] for e in pool["sensor_errors"]}
        check("missing S-2/S-3/S-6/S-7 sources reported as sensor errors, not raised", {"S-2", "S-3", "S-6", "S-7"} <= errs, sorted(errs))
        check("S-4/S-5 empty dirs are not errors", not ({"S-4", "S-5"} & errs), sorted(errs))

        print("[sensors: positive fixtures]")
        (home / "telemetry" / "hook-false-positives.jsonl").write_text(
            json.dumps({"ts": 100, "hook": "x_guard", "why": "fp1", "session": "s"}) + "\n" + "garbage line\n"
            + json.dumps({"ts": 101, "hook": "x_guard", "why": "fp2"}) + "\n" + json.dumps({"ts": 102, "nohook": True}) + "\n", encoding="utf-8")
        snap = {"points": [
            {"id": "a.b", "subsystem": "graph-snapshot", "why": "w", "reading": {"state": "fail", "quality": "good", "since": "2026-09-20T00:00:00Z"}},
            {"id": "a.c", "subsystem": "memory", "reading": {"state": "fail", "quality": "stale"}},
            {"id": "a.d", "subsystem": "memory", "reading": {"state": "warn", "quality": "good"}}]}
        (home / "tools" / "system-hmi" / "out" / "snapshot.json").write_text(json.dumps(snap), encoding="utf-8")
        (home / "ops" / "lessons" / "L-001.md").write_text(
            "---\nwhat: x\n---\n## Events\n- 2026-09-01 born session=aaaaaaaa\n- 2026-09-02 recurrence session=bbbbbbbb project=P held=no — again\n"
            "- 2026-09-03 recurrence session=cccccccc project=P held=yes — held\n", encoding="utf-8")
        (home / "ops" / "lessons" / "L-002.md").write_text(
            "---\nwhat: y\n---\n## Events\n- 2026-09-01 born session=aaaaaaaa\n- 2026-09-02 fold → ops/20-dispatch.md §3 — reason\n"
            "- 2026-09-05 recurrence session=dddddddd project=P held=no — did not hold\n"
            "- 2026-09-06 recurrence session=eeeeeeee project=P held=yes — held this time\n", encoding="utf-8")
        (home / "ops" / "lessons" / "L-003.md").write_text("---\nwhat: z\n---\nno events section\n", encoding="utf-8")
        sr = home / "outputs" / "skill-reviews"
        (sr / "alpha-gaps-round1-2026-09-01.md").write_text("# gaps\n## Findings\n", encoding="utf-8")
        (sr / "alpha-gaps-round2-2026-09-02.md").write_text("# gaps\n## Findings\n", encoding="utf-8")
        (sr / "alpha-gaps-round2-2026-09-02-disposition.md").write_text("# disp\n", encoding="utf-8")
        (sr / "alpha-gaps-round3-2026-09-03.md").write_text("# gaps\n## Findings\n## Disposition (merged)\n", encoding="utf-8")
        (sr / "beta-gaps-2026-08-16.md").write_text("# legacy round 1\n", encoding="utf-8")
        (home / "lse" / "reflux.jsonl").write_text(
            json.dumps({"kind": "correction", "ts": "2026-09-10T00:00:00Z", "run_id": "r1", "note": "wrong value"}) + "\n"
            + json.dumps({"kind": "consumed", "ts": "2026-09-10T00:00:00Z", "run_id": "r1"}) + "\n", encoding="utf-8")
        (home / "telemetry" / "golive-check.jsonl").write_text(
            json.dumps({"ts": 200, "kind": "pass", "path": "hooks/ok.py", "suites": []}) + "\n"
            + json.dumps({"ts": 201, "kind": "fail", "path": "hooks/bad_hook.py", "session_id": "s", "suites": [{"cmd": "c", "result": "fail", "last": "FAIL 1/2"}]}) + "\n", encoding="utf-8")

        pool = fb.collect(home)
        by = {d["target"]: d for d in pool["targets"]}
        check("S-2: two fp rows -> hook:x_guard n=2; garbage and hook-less rows ignored", by.get("hook:x_guard", {}).get("count") == 2, json.dumps(by.get("hook:x_guard", {}).get("sources")))
        check("S-3: only fail+good points count (1 of 3) -> subsystem:graph-snapshot", by.get("subsystem:graph-snapshot", {}).get("count") == 1 and "subsystem:memory" not in by, sorted(by))
        check("S-4: unfolded held=no -> lesson:L-001 (held=yes ignored)", by.get("lesson:L-001", {}).get("count") == 1, sorted(by))
        check("S-4: folded then held=no -> rule:<fold target>, not lesson", by.get("rule:ops/20-dispatch.md §3", {}).get("count") == 1 and "lesson:L-002" not in by, sorted(by))
        check("S-5: open rounds only (round1 + legacy beta); disposition sibling and merged heading excluded",
              by.get("skill:alpha", {}).get("sources", {}).get("S-5 skill gap round without disposition") == 1 and by.get("skill:beta", {}).get("count") == 1, json.dumps({k: v.get("sources") for k, v in by.items() if k.startswith("skill:")}))
        check("S-6: correction counted, consumed not", by.get("skill:literature-search-extract", {}).get("count") == 1, sorted(by))
        check("S-7: fail row -> hook:bad_hook; pass row ignored", by.get("hook:bad_hook", {}).get("count") == 1 and "hook:ok" not in by, sorted(by))
        check("no sensor errors once every source exists", pool["sensor_errors"] == [], json.dumps(pool["sensor_errors"]))

        print("[comparator]")
        for i in range(2):
            run([LEDGER, "feedback", "--session", S, "--target", "skill:alpha", "--symptom", f"more {i}", "--action", "fixed-inline"], env)
        pool = fb.collect(home)
        alpha = next(d for d in pool["targets"] if d["target"] == "skill:alpha")
        check("threshold: skill:alpha has 3 S-1 + 1 S-5 = 4 >= 3 -> due, listed first", alpha["due"] and alpha["count"] == 4 and pool["targets"][0]["target"] == "skill:alpha", json.dumps(alpha["sources"]))
        # planned-work = "this edit IS the task" (notice-noise data, not a defect): 3 of them alone
        # must not make a target due; the same target with 3 defect rows must (value pair: 0 vs 3)
        for i in range(3):
            run([LEDGER, "feedback", "--session", S, "--target", "rule:ops/gamma.md", "--symptom", f"routine {i}", "--action", "planned-work"], env)
        gamma = next(d for d in fb.collect(home)["targets"] if d["target"] == "rule:ops/gamma.md")
        check("planned-work x3 alone: count 0, planned 3, not due", gamma["count"] == 0 and gamma["planned"] == 3 and not gamma["due"],
              json.dumps({k: gamma[k] for k in ("count", "planned", "due")}))
        for i in range(3):
            run([LEDGER, "feedback", "--session", S, "--target", "rule:ops/gamma.md", "--symptom", f"broken {i}", "--action", "left"], env)
        pool = fb.collect(home)
        gamma = next(d for d in pool["targets"] if d["target"] == "rule:ops/gamma.md")
        check("same target + 3 defect rows: count 3, due (planned rows do not mask defects)", gamma["count"] == 3 and gamma["due"],
              json.dumps({k: gamma[k] for k in ("count", "planned", "due")}))
        r = run([LEDGER, "feedback-fold", "--session", S, "--target", "rule:ops/gamma.md", "--outcome", "adopted", "--ref", "commit def"], env)
        pool = fb.collect(home)
        doc = fb.emit(pool)
        check("emit: hmi-report/1, point warn with one alarm finding per due target", doc["protocol"] == "hmi-report/1" and doc["points"][0]["state"] == "warn"
              and sum(1 for f in doc["points"][0]["findings"] if f["severity"] == "alarm") == pool["totals"]["due"], json.dumps(doc)[:300])
        time.sleep(1.1)
        r = run([LEDGER, "feedback-fold", "--session", S, "--target", "skill:alpha", "--outcome", "adopted", "--ref", "commit abc"], env)
        pool = fb.collect(home)
        check("fold consumes: skill:alpha gone from the pool", r.returncode == 0 and all(d["target"] != "skill:alpha" for d in pool["targets"]), [d["target"] for d in pool["targets"]])
        time.sleep(1.1)
        run([LEDGER, "feedback", "--session", S, "--target", "skill:alpha", "--symptom", "after fold", "--action", "worked-around"], env)
        pool = fb.collect(home)
        alpha = next((d for d in pool["targets"] if d["target"] == "skill:alpha"), None)
        check("new event after fold starts a fresh count (1, accumulating)", alpha and alpha["count"] == 1 and alpha["state"] == "accumulating", json.dumps(alpha and alpha["sources"]))
        time.sleep(1.1)
        run([LEDGER, "feedback-fold", "--session", S, "--target", "skill:alpha", "--outcome", "deferred", "--ref", "T-9", "--trigger", "next paper-story run"], env)
        pool = fb.collect(home)
        alpha = next((d for d in pool["targets"] if d["target"] == "skill:alpha"), None)
        doc = fb.emit(pool)
        check("deferred fold: target stays visible as deferred with its trigger; emit lists it as info", alpha and alpha["state"] == "deferred"
              and any(f["severity"] == "info" and "next paper-story run" in f["text"] for f in doc["points"][0]["findings"]), json.dumps(alpha and alpha["state"]))
        # every remaining due target folded -> emit pass
        for d in list(pool["targets"]):
            if d["due"]:
                run([LEDGER, "feedback-fold", "--session", S, "--target", d["target"], "--outcome", "rejected", "--ref", "no change: ctl"], env)
        time.sleep(1.1)
        pool = fb.collect(home)
        doc = fb.emit(pool)
        check("emit: pass when nothing is due", pool["totals"]["due"] == 0 and doc["points"][0]["state"] == "pass" and doc["points"][0]["remedy"] is None, json.dumps(pool["totals"]))

        print("[cli + target_of]")
        r = run([HERE / "feedback.py", "collect"], env)
        check("collect CLI: summary line + pool.json written", r.returncode == 0 and r.stdout.startswith("feedback-pool:") and (HERE / "out" / "pool.json").is_file(), r.stdout + r.stderr)
        r = run([HERE / "feedback.py", "review", "skill:nonexistent"], env)
        check("review of an unknown target exits 1 with the known list", r.returncode == 1 and "no unconsumed events" in r.stdout, r.stdout[:120])
        r = run([HERE / "feedback.py", "report", "--json"], env)
        check("report --json parses", r.returncode == 0 and "totals" in json.loads(r.stdout), r.stdout[:120] + r.stderr[-200:])
        cases = {str(home / "skills" / "alpha" / "SKILL.md"): "skill:alpha", str(home / "hooks" / "x.py"): "hook:x",
                 str(home / "tools" / "t" / "a.py"): "tool:t", str(home / "ops" / "20-dispatch.md"): "rule:ops/20-dispatch.md",
                 str(home / "skills" / "synced" / "z" / "SKILL.md"): "", str(home / "ops" / "lessons" / "L-1.md"): "",
                 str(home / "memory" / "x.md"): "", str(Path(td) / "elsewhere.py"): "", str(home / "hooks" / "notes.md"): ""}
        bad = {p: (fb.target_of(p, home), want) for p, want in cases.items() if fb.target_of(p, home) != want}
        check("target_of: 9 cases (5 mapped, 4 excluded)", not bad, json.dumps(bad))

    # the real home still collects (read-only smoke; never asserts on its content)
    r = run([HERE / "feedback.py", "collect"], dict(os.environ, PYTHONIOENCODING="utf-8"))
    check("smoke: collect on the real home exits 0", r.returncode == 0 and r.stdout.startswith("feedback-pool:"), r.stdout + r.stderr[-300:])

    n_ok = sum(RESULTS)
    print(f"{'ALL PASS' if n_ok == len(RESULTS) else 'FAIL'} {n_ok}/{len(RESULTS)}")
    return 0 if n_ok == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
