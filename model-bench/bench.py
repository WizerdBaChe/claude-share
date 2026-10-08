#!/usr/bin/env python3
"""model-bench — measure which dispatch-table rows a model tier can carry.

Subject: the model × effort table in `claude-ops/ops/20-dispatch.md` §4 and
the tier→model mapping in `claude-ops/ops/environment.md`. Every task in
`tasks/` is one row of that table (or one 5th-generation capability the table
does not yet name), with a MACHINE gate: no LLM judges anything here.

    python bench.py list                       # task table
    python bench.py selftest                   # two-sided calibration of every gate
    python bench.py run  --models haiku,sonnet --effort medium --repeats 2 \
                         --parallel 4 --out results/runs.jsonl
    python bench.py summarize --runs results/runs.jsonl --out results/summary.md

Each run shells out to `claude -p --output-format json` in a fresh scratch
working directory that the task's `setup()` populated. The CLI's JSON carries
`total_cost_usd`, per-iteration usage (input / output / cache_read /
cache_creation), `duration_ms` and `num_turns`; the gate reads the final text
and the working directory and returns pass/fail with a reason.

Records are de-identified at write time: no session ids, no absolute paths,
no account names (the share gate's leak scan would reject them; see
`tools/sharelib.py`). Stdlib only.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS_DIR = HERE / "tasks"
sys.path.insert(0, str(TASKS_DIR))  # tasks share `_common.py`
PRICING = json.loads((HERE / "pricing.json").read_text(encoding="utf-8"))

ALIAS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5",
         "opus": "claude-opus-5-5"}


# --------------------------------------------------------------------------
# task loading
# --------------------------------------------------------------------------
REQUIRED = ("ID", "CATEGORY", "DISPATCH_ROW", "EXPECTED_TIER", "PROMPT",
            "TOOLS", "MAX_TURNS", "TIMEOUT_S", "setup", "check", "CONTROLS")


def load_tasks(only: set[str] | None = None):
    tasks = []
    for p in sorted(TASKS_DIR.glob("t[0-9][0-9]_*.py")):
        spec = importlib.util.spec_from_file_location(p.stem, p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        missing = [a for a in REQUIRED if not hasattr(mod, a)]
        if missing:
            raise SystemExit(f"{p.name}: missing {missing}")
        if only and mod.ID not in only and p.stem not in only:
            continue
        tasks.append(mod)
    return tasks


# --------------------------------------------------------------------------
# de-identification of anything that reaches the record
# --------------------------------------------------------------------------
_UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_HOME = re.compile(r"(?i)(?:[A-Z]:[\\/]+Users[\\/]+|/home/|/Users/|/c/Users/)[A-Za-z][A-Za-z0-9._-]*")
_HEX32 = re.compile(r"\b[0-9a-fA-F]{32,}\b")


def scrub(text: str, workdir: Path | None = None) -> str:
    if workdir is not None:
        text = text.replace(str(workdir), "<WORKDIR>")
    text = _UUID.sub("<UUID>", text)
    text = _HOME.sub("<HOME>", text)
    text = _HEX32.sub("<HEX>", text)
    return text


# --------------------------------------------------------------------------
# pricing cross-check
# --------------------------------------------------------------------------
def list_cost(model: str, inp: int, out: int, cread: int, cwrite: int) -> float | None:
    p = PRICING["models"].get(model)
    if not p:
        return None
    per = 1e-6
    return (inp * p["input"] + out * p["output"]
            + cread * p["input"] * p["cache_read_mult"]
            + cwrite * p["input"] * p["cache_write_mult"]) * per


def nocache_cost(model: str, inp: int, out: int, cread: int, cwrite: int) -> float | None:
    """What the same tokens would cost if every cached token were billed as plain input."""
    p = PRICING["models"].get(model)
    if not p:
        return None
    return ((inp + cread + cwrite) * p["input"] + out * p["output"]) * 1e-6


# --------------------------------------------------------------------------
# one run
# --------------------------------------------------------------------------
@dataclass
class Row:
    run_id: str
    ts: str
    task: str
    category: str
    dispatch_row: str
    expected_tier: str
    model_alias: str
    model: str
    effort: str
    rep: int
    passed: bool
    score: float
    details: str
    is_error: bool
    stop_reason: str | None
    terminal_reason: str | None
    num_turns: int
    duration_ms: int
    duration_api_ms: int
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    cache_hit_ratio: float
    cost_usd: float
    cost_list_usd: float | None
    cost_nocache_usd: float | None
    result_chars: int
    result_head: str
    rejudged: bool = False  # set by `rejudge`: the gate was re-run on the kept workdir after a gate fix


def run_one(task, model_alias: str, effort: str, rep: int, scratch: Path,
            keep: bool) -> Row:
    workdir = Path(tempfile.mkdtemp(prefix=f"{task.ID}-{model_alias}-r{rep}-", dir=scratch))
    task.setup(workdir)
    cmd = ["claude", "-p", "--model", model_alias, "--effort", effort,
           "--output-format", "json", "--max-turns", str(task.MAX_TURNS),
           "--no-session-persistence", "--session-id", str(uuid.uuid4()),
           "--dangerously-skip-permissions"]
    if task.TOOLS == "none":
        cmd += ["--tools", ""]
    env = dict(os.environ)
    # a child `claude -p` otherwise attaches itself to the parent session
    for k in ("CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_EFFORT"):
        env.pop(k, None)
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, input=task.PROMPT, capture_output=True, text=True,
                              cwd=workdir, env=env, timeout=task.TIMEOUT_S)
        raw = proc.stdout
    except subprocess.TimeoutExpired:
        raw = ""
    wall = int((time.time() - t0) * 1000)
    try:
        j = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        j = {}
    result = j.get("result") or ""
    usage = j.get("usage") or {}
    mu = j.get("modelUsage") or {}
    canon = next(iter(mu.values()), {}).get("canonicalModel") if mu else None
    model = canon or ALIAS.get(model_alias, model_alias)
    inp = int(usage.get("input_tokens") or 0)
    out = int(usage.get("output_tokens") or 0)
    cread = int(usage.get("cache_read_input_tokens") or 0)
    cwrite = int(usage.get("cache_creation_input_tokens") or 0)
    think = int((usage.get("output_tokens_details") or {}).get("thinking_tokens") or 0)
    denom = inp + cread + cwrite
    try:
        verdict = task.check(result, workdir) if j else {"pass": False, "score": 0.0,
                                                          "details": "no JSON from CLI (timeout or crash)"}
    except Exception as e:  # a gate that crashes is a gate failure, recorded as such
        verdict = {"pass": False, "score": 0.0, "details": f"GATE CRASH: {type(e).__name__}: {e}"}
    row = Row(
        run_id=f"{task.ID}-{model_alias}-{effort}-r{rep}",
        ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
        task=task.ID, category=task.CATEGORY, dispatch_row=task.DISPATCH_ROW,
        expected_tier=task.EXPECTED_TIER,
        model_alias=model_alias, model=model, effort=effort, rep=rep,
        passed=bool(verdict["pass"]), score=float(verdict.get("score", 1.0 if verdict["pass"] else 0.0)),
        details=scrub(str(verdict.get("details", ""))[:400], workdir),
        is_error=bool(j.get("is_error", not j)),
        stop_reason=j.get("stop_reason"), terminal_reason=j.get("terminal_reason"),
        num_turns=int(j.get("num_turns") or 0),
        duration_ms=int(j.get("duration_ms") or wall),
        duration_api_ms=int(j.get("duration_api_ms") or 0),
        input_tokens=inp, output_tokens=out, thinking_tokens=think,
        cache_read_tokens=cread, cache_creation_tokens=cwrite,
        cache_hit_ratio=round(cread / denom, 4) if denom else 0.0,
        cost_usd=float(j.get("total_cost_usd") or 0.0),
        cost_list_usd=list_cost(model, inp, out, cread, cwrite),
        cost_nocache_usd=nocache_cost(model, inp, out, cread, cwrite),
        result_chars=len(result),
        result_head=scrub(result[:160].replace("\n", "\\n"), workdir),
    )
    if keep:
        (workdir / "_result.txt").write_text(result, encoding="utf-8")
        (workdir / "_cli.json").write_text(raw, encoding="utf-8")
    else:
        shutil.rmtree(workdir, ignore_errors=True)
    return row


# --------------------------------------------------------------------------
# subcommands
# --------------------------------------------------------------------------
def cmd_list(args):
    print(f"{'id':<22} {'category':<26} {'expected':<9} {'tools':<7} {'turns':>5}  dispatch row")
    for t in load_tasks():
        print(f"{t.ID:<22} {t.CATEGORY:<26} {t.EXPECTED_TIER:<9} {t.TOOLS:<7} {t.MAX_TURNS:>5}  {t.DISPATCH_ROW}")


def cmd_selftest(args):
    """Two-sided calibration: every gate must accept its known-pass control and
    reject its known-fail control. A gate that only ever passes is not a gate."""
    bad = 0
    total = 0
    for t in load_tasks(set(args.tasks.split(",")) if args.tasks else None):
        pos = neg = 0
        for i, ctl in enumerate(t.CONTROLS):
            total += 1
            wd = Path(tempfile.mkdtemp(prefix=f"ctl-{t.ID}-"))
            try:
                t.setup(wd)
                if ctl.get("mutate"):
                    ctl["mutate"](wd)
                v = t.check(ctl["result"], wd)
            finally:
                shutil.rmtree(wd, ignore_errors=True)
            ok = bool(v["pass"]) == bool(ctl["expect"])
            pos += ctl["expect"]
            neg += not ctl["expect"]
            if not ok:
                bad += 1
            print(f"{'ok ' if ok else 'BAD'} {t.ID} control#{i} expect={'pass' if ctl['expect'] else 'fail'} "
                  f"got={'pass' if v['pass'] else 'fail'} :: {str(v.get('details',''))[:90]}")
        if pos == 0 or neg == 0:
            bad += 1
            print(f"BAD {t.ID}: controls are one-sided (pass={pos}, fail={neg})")
    print(f"\nselftest: {total} controls, {bad} problem(s)")
    sys.exit(1 if bad else 0)


def cmd_run(args):
    tasks = load_tasks(set(args.tasks.split(",")) if args.tasks else None)
    models = args.models.split(",")
    scratch = Path(args.scratch) if args.scratch else Path(tempfile.mkdtemp(prefix="model-bench-"))
    scratch.mkdir(parents=True, exist_ok=True)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    jobs = [(t, m, r) for r in range(1, args.repeats + 1) for t in tasks for m in models]
    print(f"{len(jobs)} runs → {out}  (scratch {scratch.name}, parallel {args.parallel})", flush=True)
    done = 0
    # rep 1 for every (task, model) runs before any rep 2 so the first run of a
    # pair is the cold-cache one and the second is warm — the cache-hit
    # comparison the summary reports depends on this ordering.
    with out.open("a", encoding="utf-8") as fh, cf.ThreadPoolExecutor(args.parallel) as ex:
        for rep in range(1, args.repeats + 1):
            futs = {ex.submit(run_one, t, m, args.effort, rep, scratch, args.keep): (t, m)
                    for (t, m, r) in jobs if r == rep}
            for fut in cf.as_completed(futs):
                row = fut.result()
                fh.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")
                fh.flush()
                done += 1
                print(f"[{done}/{len(jobs)}] {row.run_id:<34} {'PASS' if row.passed else 'fail'} "
                      f"{row.duration_ms/1000:6.1f}s  ${row.cost_usd:.4f}  turns={row.num_turns} "
                      f"cache={row.cache_hit_ratio:.2f}  {row.details[:70]}", flush=True)


def cmd_rejudge(args):
    """Re-run a task's (fixed) gate over KEPT workdirs and rewrite those rows in place.

    Exists because a gate can be wrong and the first live round proves it: T10's
    digest counted `tests/__pycache__`, so running the suite looked like editing
    the tests. The model's run is a sunk cost and its workdir is exactly the
    post-run state, so the honest repair is to re-judge, mark the row, and keep
    every measured number. The result text is read back from `_result.txt`."""
    tasks = {t.ID: t for t in load_tasks(set(args.tasks.split(",")))}
    scratch = Path(args.scratch)
    path = Path(args.runs)
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    changed = 0
    for r in rows:
        t = tasks.get(r["task"])
        if not t:
            continue
        prefix = f"{t.ID}-{r['model_alias']}-r{r['rep']}-"
        wds = [d for d in scratch.iterdir() if d.is_dir() and d.name.startswith(prefix)]
        if len(wds) != 1:
            print(f"skip {r['run_id']}: {len(wds)} workdir(s) match {prefix}*")
            continue
        wd = wds[0]
        result = (wd / "_result.txt").read_text(encoding="utf-8") if (wd / "_result.txt").exists() else ""
        v = t.check(result, wd)
        before = (r["passed"], r["details"])
        r["passed"] = bool(v["pass"]); r["score"] = float(v.get("score", 1.0 if v["pass"] else 0.0))
        r["details"] = scrub(str(v.get("details", ""))[:400], wd); r["rejudged"] = True
        changed += (before != (r["passed"], r["details"]))
        print(f"{r['run_id']}: {before[0]} -> {r['passed']} :: {r['details'][:80]}")
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"rejudged; {changed} row(s) changed verdict or details")


def _med(xs):
    return statistics.median(xs) if xs else 0.0


def cmd_summarize(args):
    rows = [json.loads(l) for l in Path(args.runs).read_text(encoding="utf-8").splitlines() if l.strip()]
    if not rows:
        raise SystemExit("no rows")
    models = sorted({r["model"] for r in rows})
    tasks = sorted({r["task"] for r in rows})
    by = {}
    for r in rows:
        by.setdefault((r["task"], r["model"]), []).append(r)
    meta = {r["task"]: r for r in rows}
    L = []
    L.append("# model-bench summary\n")
    L.append(f"runs: {len(rows)} · models: {', '.join(models)} · effort: "
             f"{', '.join(sorted({r['effort'] for r in rows}))} · generated from `{Path(args.runs).name}`\n")
    L.append("Every verdict below is a MACHINE gate (`tasks/*.py` `check()`); no LLM judged anything. "
             "`n` is the number of runs per cell — with n=2 a 50% is one failure, not a rate.\n")
    # per-task table
    L.append("## Per task\n")
    hdr = "| task | dispatch row | expected | " + " | ".join(
        f"{m.replace('claude-','')} pass | med s | mean $ | cache" for m in models) + " |"
    L.append(hdr)
    L.append("|" + "---|" * (3 + 4 * len(models)))
    for t in tasks:
        cells = [t, meta[t]["dispatch_row"], meta[t]["expected_tier"]]
        for m in models:
            rs = by.get((t, m), [])
            if not rs:
                cells += ["—", "—", "—", "—"]
                continue
            p = sum(r["passed"] for r in rs)
            cells += [f"{p}/{len(rs)}", f"{_med([r['duration_ms'] for r in rs])/1000:.1f}",
                      f"{statistics.mean(r['cost_usd'] for r in rs):.4f}",
                      f"{statistics.mean(r['cache_hit_ratio'] for r in rs):.2f}"]
        L.append("| " + " | ".join(cells) + " |")
    # per-model totals
    L.append("\n## Per model\n")
    L.append("| model | runs | pass | med s | total $ | $ if uncached | cache tokens read | cache hit (mean) | rep1 hit | rep2+ hit |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for m in models:
        rs = [r for r in rows if r["model"] == m]
        r1 = [r for r in rs if r["rep"] == 1]
        r2 = [r for r in rs if r["rep"] > 1]
        tot = sum(r["cost_usd"] for r in rs)
        noc = sum(r["cost_nocache_usd"] or 0 for r in rs)
        L.append(f"| {m} | {len(rs)} | {sum(r['passed'] for r in rs)}/{len(rs)} | "
                 f"{_med([r['duration_ms'] for r in rs])/1000:.1f} | {tot:.4f} | {noc:.4f} | "
                 f"{sum(r['cache_read_tokens'] for r in rs)} | "
                 f"{statistics.mean(r['cache_hit_ratio'] for r in rs):.2f} | "
                 f"{statistics.mean(r['cache_hit_ratio'] for r in r1) if r1 else 0:.2f} | "
                 f"{statistics.mean(r['cache_hit_ratio'] for r in r2) if r2 else 0:.2f} |")
    # routing verdicts
    L.append("\n## Routing verdict per task (mechanical rule)\n")
    L.append("Rule: the CHEAPEST model whose pass count is n/n takes the row; a model with any failure "
             "is `not clean`. Where no model is clean the row is `escalate / redesign gate`. "
             "A verdict with n<3 is a hypothesis to re-run, not a ruling.\n")
    L.append("| task | expected | verdict | cheapest clean | sonnet/haiku cost × | sonnet/haiku time × |")
    L.append("|---|---|---|---|---|---|")
    order = ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]
    for t in tasks:
        clean = None
        for m in order:
            rs = by.get((t, m))
            if rs and all(r["passed"] for r in rs):
                clean = m
                break
        h = by.get((t, "claude-haiku-5-5"), [])
        s = by.get((t, "claude-sonnet-5-5"), [])
        cx = (statistics.mean(r["cost_usd"] for r in s) / max(statistics.mean(r["cost_usd"] for r in h), 1e-9)) if h and s else None
        tx = (_med([r["duration_ms"] for r in s]) / max(_med([r["duration_ms"] for r in h]), 1)) if h and s else None
        exp = meta[t]["expected_tier"]
        if clean is None:
            verdict = "escalate / redesign gate"
        else:
            tier = {"claude-haiku-5-5": "cheap", "claude-sonnet-5-5": "mid", "claude-opus-5-5": "top"}[clean]
            verdict = "as expected" if tier == exp else (f"DOWNGRADE candidate → {tier}" if order.index(clean) < ["cheap", "mid", "top"].index(exp) else f"UPGRADE needed → {tier}")
        L.append(f"| {t} | {exp} | {verdict} | {clean.replace('claude-','') if clean else '—'} | "
                 f"{cx:.1f} | {tx:.2f} |" if cx is not None else
                 f"| {t} | {exp} | {verdict} | {clean or '—'} | — | — |")
    # failures
    fails = [r for r in rows if not r["passed"]]
    L.append(f"\n## Failures ({len(fails)})\n")
    for r in fails:
        L.append(f"- `{r['run_id']}` · {r['details']}")
    Path(args.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    s = sub.add_parser("selftest"); s.add_argument("--tasks"); s.set_defaults(fn=cmd_selftest)
    r = sub.add_parser("run")
    r.add_argument("--models", default="haiku,sonnet")
    r.add_argument("--effort", default="medium")
    r.add_argument("--repeats", type=int, default=2)
    r.add_argument("--parallel", type=int, default=4)
    r.add_argument("--tasks", help="comma-separated task ids (default all)")
    r.add_argument("--out", default=str(HERE / "results" / "runs.jsonl"))
    r.add_argument("--scratch", help="scratch dir for workdirs (default: a temp dir)")
    r.add_argument("--keep", action="store_true", help="keep workdirs with _result.txt/_cli.json")
    r.set_defaults(fn=cmd_run)
    j = sub.add_parser("rejudge")
    j.add_argument("--tasks", required=True)
    j.add_argument("--scratch", required=True)
    j.add_argument("--runs", default=str(HERE / "results" / "runs.jsonl"))
    j.set_defaults(fn=cmd_rejudge)
    m = sub.add_parser("summarize")
    m.add_argument("--runs", default=str(HERE / "results" / "runs.jsonl"))
    m.add_argument("--out", default=str(HERE / "results" / "summary.md"))
    m.set_defaults(fn=cmd_summarize)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
