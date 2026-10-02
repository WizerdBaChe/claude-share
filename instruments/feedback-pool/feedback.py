#!/usr/bin/env python3
r"""feedback-pool — the subsystem feedback pool as a PROJECTION over signals that already exist.

STATUS: LIVE since 2026-09-22 (claude-config; design of record
references/feedback-pool-design.md, user ruling: recommended values, built same round).
Carries `ops/rule-registry.md` key `FEEDBACK_POOL`.

WHY. Mid-task defects in a subsystem (a skill, a tool, a hook, a rule) were either
patched in passing or worked around, and the only trace was a commit diff; the only
formal feedback path was the close-out lesson. Meanwhile the machine already emits
defect signals in six places (hook false positives, go-live failures, HMI standing
alarms, lesson recurrences, open skill-gap rounds, LSE reflux corrections) that nobody
aggregates. This tool reads all of them plus the model-written `feedback` rows of the
process ledger, groups them BY TARGET, and says which targets have accumulated enough
to be worth the user's review. It never writes the sources; the pool file it emits is
a rebuildable projection (INV-3).

  python feedback.py collect            rebuild out/pool.json; one summary line
  python feedback.py report [--mine] [--json]   the table a human decides from
  python feedback.py review <target>    every event with its locator + the fold command
  python feedback.py emit               hmi-report/1 document (point feedback-pool.due)
  python feedback.py target-of <path>   derive a target label from a path under ~/.claude

Writing is NOT here (INV-2): `tools/process-ledger/ledger.py feedback` / `feedback-fold`.

Severity: the HMI point is `warn` at most — the reader is the model or the user deciding
whether to spend a review round (gate-severity-by-consumer). Promotion trigger and the
threshold live in registry key FEEDBACK_POOL; the value below is PROVISIONAL.
Fail-soft (INV-4): a missing or malformed source yields zero events and one
`sensor_errors` entry; `collect` exits 0 regardless.

Test overrides (calibration only): env FEEDBACK_HOME (the ~/.claude root to read),
LSE_RUN_HOME (already the LSE loop's own override). Production never sets FEEDBACK_HOME.

Proof-of-life: `python tools/feedback-pool/controls.py`
review-when: ledger.py changes its row shape or path; system-hmi's snapshot moves or
`hmi-report/1` bumps its major; any S-n source in SENSORS renames its file; a month with
>=3 due targets and zero folds (then the drain gate, not the pool, is the wrong design).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HOME = Path(os.environ.get("FEEDBACK_HOME") or os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
OUT = Path(__file__).resolve().parent / "out"
DRAIN_THRESHOLD = 3          # PROVISIONAL — registry key FEEDBACK_POOL
TARGET_PREFIXES = ("hook:", "skill:", "tool:", "rule:", "subsystem:", "lesson:", "project:")
SYSTEM_DIRS = ("hooks", "skills", "tools", "ops", "rules")
EXCLUDED_UNDER = (("skills", "synced"), ("ops", "lessons"), ("tools", "feedback-pool", "out"))


# --------------------------------------------------------------------------- helpers
def _iso_to_ts(s: str) -> int | None:
    try:
        s = s.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        d = dt.datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return int(d.timestamp())
    except Exception:
        return None


def _date_to_ts(s: str) -> int | None:
    try:
        return int(dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())
    except Exception:
        return None


def _jsonl(path: Path):
    """Yield parsed object rows; skip blank and malformed lines (they count as sensor noise, not errors)."""
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj


def event(ts, target, source, symptom, locator, session=None, **extra) -> dict:
    e = {"ts": int(ts or 0), "target": target, "source": source, "symptom": str(symptom)[:300],
         "locator": str(locator)[:300]}
    if session:
        e["session"] = str(session)[:36]
    e.update(extra)
    return e


def target_of(path: str, home: Path = HOME) -> str:
    """Map a path under <home>/{hooks,skills,tools,ops,rules} to a target label ('' if none)."""
    try:
        p = Path(path).resolve()
        rel = p.relative_to(home.resolve())
    except Exception:
        return ""
    parts = rel.parts
    if len(parts) < 2 or parts[0] not in SYSTEM_DIRS:
        return ""
    for ex in EXCLUDED_UNDER:
        if parts[:len(ex)] == ex:
            return ""
    top, second = parts[0], parts[1]
    if top == "hooks":
        return f"hook:{Path(second).stem}" if second.endswith(".py") else ""
    if top == "skills":
        return f"skill:{second}"
    if top == "tools":
        return f"tool:{second}"
    return f"rule:{rel.as_posix()}"          # ops/… and rules/…


# --------------------------------------------------------------------------- sensors (S-n)
def s1_ledger(home: Path):
    """S-1: feedback rows and fold rows across every session ledger.

    ledger.py's own CLI refuses an unrecognized target prefix on write, but this
    sensor reads the files directly and cannot assume every row on disk passed
    through that gate (hand-edited or legacy rows). A row whose `target` is not
    a string starting with a TARGET_PREFIXES prefix is unclassifiable (AP-62):
    it is reported once as an S-1 sensor error and excluded from every target/
    count, never folded into a target of its own."""
    events, folds, errors = [], [], []
    files = list((home / "projects").glob("*/*.ledger.jsonl")) + list((home / "cache" / "handoff").glob("*.ledger.jsonl"))
    for f in files:
        for r in _jsonl(f):
            k = r.get("kind")
            if k not in ("feedback", "feedback-fold") or not r.get("target"):
                continue
            t = r["target"]
            if not isinstance(t, str) or not t.startswith(TARGET_PREFIXES):
                errors.append({"sensor": "S-1",
                                "error": f"undetermined target (unrecognized prefix) {t!r} in {f.name}"[:200]})
                continue
            if k == "feedback":
                events.append(event(r.get("ts"), t, "S-1 ledger", r.get("symptom", ""),
                                    f"{f.name}#{r.get('id', '')}", r.get("session"),
                                    action=r.get("action", ""), proposal=r.get("proposal", ""), id=r.get("id", "")))
            else:
                folds.append({"ts": int(r.get("ts") or 0), "target": t, "outcome": r.get("outcome", ""),
                              "ref": r.get("ref", ""), "trigger": r.get("trigger", ""), "session": r.get("session", "")})
    return events, folds, errors


def s2_hook_fp(home: Path):
    p = home / "telemetry" / "hook-false-positives.jsonl"
    return [event(r.get("ts"), f"hook:{r.get('hook', '?')}", "S-2 hook false positive", r.get("why", ""),
                  f"telemetry/hook-false-positives.jsonl ts={r.get('ts')}", r.get("session"))
            for r in _jsonl(p) if r.get("hook")]


def s3_hmi_standing(home: Path):
    p = home / "tools" / "system-hmi" / "out" / "snapshot.json"
    snap = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for pt in snap.get("points") or []:
        rd = pt.get("reading") or {}
        if rd.get("state") == "fail" and rd.get("quality") == "good" and pt.get("subsystem"):
            ts = _iso_to_ts(rd.get("since") or rd.get("observed_at") or "") or 0
            out.append(event(ts, f"subsystem:{pt['subsystem']}", "S-3 hmi standing fail",
                             f"{pt.get('id')}: {pt.get('why') or ''}", f"system-hmi point {pt.get('id')}"))
    return out


# Lesson events are parsed by closeout-intake's own parser, never a local regex copy:
# a second copy of the held rule is how intake's report and this pool came to disagree
# about what "folded but recurring" means (2026-09-23).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "closeout-intake"))
import intake_core as _intake  # noqa: E402
SESS_RE = re.compile(r"session=([0-9a-f]{8})")


def s4_lessons(home: Path):
    out = []
    for f in sorted((home / "ops" / "lessons").glob("L-*.md")):
        lid = f.stem
        text = f.read_text(encoding="utf-8", errors="replace")
        if "## Events" not in text:
            continue
        fold_target = None
        for e in _intake.parse_record(text)["events"]:
            if e["kind"] == "fold":
                fold_target = e["target"]        # a re-fold moves later recurrences to the new owner
                continue
            if e["kind"] != "recurrence":
                continue
            if e.get("held") == "yes":
                continue                         # the fix held: the situation recurred, the rule worked — not a defect
            mid, _, note = e["rest"].partition(" — ")
            ts = _date_to_ts(e["date"]) or 0
            sm = SESS_RE.search(mid or "")
            sess = sm.group(1) if sm else None
            if fold_target:                      # folded: the defect belongs to the rule that was supposed to hold
                out.append(event(ts, f"rule:{fold_target}", "S-4 folded but recurring (held=no)",
                                 f"{lid} recurred after fold: {note or ''}", f"ops/lessons/{lid}.md", sess))
            else:
                out.append(event(ts, f"lesson:{lid}", "S-4 lesson recurrence (held=no)", note or "", f"ops/lessons/{lid}.md", sess))
    return out


GAP_RE = re.compile(r"^(?P<skill>.+?)-gaps-(?:round(?P<n>\d+)-)?(?P<date>\d{4}-\d{2}-\d{2})\.md$")
MERGED_RE = re.compile(r"^#{1,3} .*(disposition|處置|per-gap verdict)", re.I | re.M)


def s5_skill_gaps(home: Path):
    d = home / "outputs" / "skill-reviews"
    out = []
    for f in sorted(d.glob("*-gaps-*.md")):
        if f.name.endswith("-disposition.md"):
            continue
        m = GAP_RE.match(f.name)
        if not m:
            continue
        if (d / (f.stem + "-disposition.md")).exists():
            continue
        try:                                     # a merged round carries its disposition inside the report
            if MERGED_RE.search(f.read_text(encoding="utf-8", errors="replace")):
                continue
        except Exception:
            pass
        ts = _date_to_ts(m.group("date")) or 0
        out.append(event(ts, f"skill:{m.group('skill')}", "S-5 skill gap round without disposition",
                         f"round {m.group('n') or '1'} open", f"outputs/skill-reviews/{f.name}"))
    return out


def s6_lse_reflux(home: Path):
    lse_home = Path(os.environ.get("LSE_RUN_HOME") or (home / "lse-evidence-runs"))
    p = lse_home / "reflux.jsonl"
    out = []
    for r in _jsonl(p):
        if r.get("kind") == "correction":
            ts = r.get("ts")
            if isinstance(ts, str):
                ts = _iso_to_ts(ts)
            out.append(event(ts or 0, "skill:literature-search-extract", "S-6 LSE reflux correction",
                             r.get("note") or r.get("evidence") or "", f"reflux.jsonl run={r.get('run_id', '')}"))
    return out


def s7_golive_fail(home: Path):
    p = home / "telemetry" / "golive-check.jsonl"
    out = []
    for r in _jsonl(p):
        if r.get("kind") != "fail":
            continue
        stem = Path(str(r.get("path", ""))).stem
        last = ""
        for s in r.get("suites") or []:
            if s.get("result") != "pass":
                last = s.get("last") or s.get("cmd") or ""
                break
        out.append(event(r.get("ts"), f"hook:{stem}", "S-7 go-live proof-of-life fail", last,
                         f"telemetry/golive-check.jsonl ts={r.get('ts')}", r.get("session_id")))
    return out


SENSORS = (("S-2", s2_hook_fp), ("S-3", s3_hmi_standing), ("S-4", s4_lessons),
           ("S-5", s5_skill_gaps), ("S-6", s6_lse_reflux), ("S-7", s7_golive_fail))


# --------------------------------------------------------------------------- comparator
def collect(home: Path = HOME, threshold: int = DRAIN_THRESHOLD) -> dict:
    errors = []
    try:
        events, folds, s1_errors = s1_ledger(home)
        errors.extend(s1_errors)
    except Exception as e:                       # the core source failing is still not a crash
        events, folds = [], []
        errors.append({"sensor": "S-1", "error": repr(e)[:200]})
    for sid, fn in SENSORS:
        try:
            events.extend(fn(home))
        except FileNotFoundError as e:
            errors.append({"sensor": sid, "error": f"missing: {getattr(e, 'filename', '') or e}"[:200]})
        except Exception as e:
            errors.append({"sensor": sid, "error": repr(e)[:200]})

    last_fold: dict[str, dict] = {}
    for f in folds:
        if f["target"] not in last_fold or f["ts"] > last_fold[f["target"]]["ts"]:
            last_fold[f["target"]] = f

    targets: dict[str, dict] = {}
    for e in events:
        t = e["target"]
        fold = last_fold.get(t)
        if fold and e["ts"] <= fold["ts"]:
            continue                             # consumed (INV-5)
        targets.setdefault(t, {"target": t, "events": [], "sources": {}})
        targets[t]["events"].append(e)
        targets[t]["sources"][e["source"]] = targets[t]["sources"].get(e["source"], 0) + 1
    for t, fold in last_fold.items():            # deferred targets with nothing new stay visible
        if t not in targets and fold.get("outcome") == "deferred":
            targets[t] = {"target": t, "events": [], "sources": {}}

    rows = []
    for t, d in targets.items():
        d["events"].sort(key=lambda e: e["ts"])
        # `planned-work` answers feedback_notice with "this edit IS the task": the design
        # (feedback-pool-design §2.1, `action`) keeps it to measure the notice's noise, not as a defect.
        # Counted toward `due` until 2026-09-23, three routine registry updates made
        # rule:ops/rule-registry.md due and lit the HMI with no defect behind it.
        d["planned"] = sum(1 for e in d["events"] if e.get("action") == "planned-work")
        d["count"] = len(d["events"]) - d["planned"]
        d["due"] = d["count"] >= threshold
        d["oldest_ts"] = d["events"][0]["ts"] if d["events"] else None
        d["newest_ts"] = d["events"][-1]["ts"] if d["events"] else None
        d["last_fold"] = last_fold.get(t)
        d["state"] = "due" if d["due"] else ("deferred" if (d["count"] == 0 and d["last_fold"]) else "accumulating")
        rows.append(d)
    rows.sort(key=lambda d: (-int(d["due"]), -d["count"], d["target"]))
    pool = {"generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "home": str(home), "threshold": threshold, "targets": rows, "sensor_errors": errors,
            "totals": {"targets": len(rows), "events": sum(d["count"] for d in rows),
                       "due": sum(1 for d in rows if d["due"]),
                       "deferred": sum(1 for d in rows if d["state"] == "deferred")}}
    return pool


def write_pool(pool: dict, out_dir: Path = OUT) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "pool.json"
    p.write_text(json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def summary_line(pool: dict) -> str:
    t = pool["totals"]
    return (f"feedback-pool: {t['due']} due, {t['deferred']} deferred, {t['targets']} targets, "
            f"{t['events']} events (sensor errors: {len(pool['sensor_errors'])})")


# --------------------------------------------------------------------------- commands
def _day(ts) -> str:
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d") if ts else "-"


def cmd_collect(a) -> int:
    pool = collect()
    p = write_pool(pool)
    print(summary_line(pool) + f" -> {p}")
    return 0


def cmd_report(a) -> int:
    pool = collect()
    write_pool(pool)
    rows = pool["targets"]
    if a.mine:
        sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        rows = [dict(d, events=[e for e in d["events"] if e.get("session") and sid.startswith(e["session"])])
                for d in rows]
        rows = [d for d in rows if d["events"]]
    if a.json:
        print(json.dumps({"totals": pool["totals"], "targets": rows, "sensor_errors": pool["sensor_errors"]},
                         ensure_ascii=False, indent=1))
        return 0
    print(summary_line(pool))
    print(f"threshold {pool['threshold']} events per target since its last fold; 'left' = a defect recorded as still broken\n")
    print("| state | target | n | left | oldest | newest | sources |")
    print("|---|---|---|---|---|---|---|")
    for d in rows:
        left = sum(1 for e in d["events"] if e.get("action") == "left")
        src = ", ".join(f"{k.split(' ', 1)[0]}×{v}" for k, v in sorted(d["sources"].items()))
        fold = d.get("last_fold")
        state = d["state"] + (f" (trigger: {fold.get('trigger', '')})" if d["state"] == "deferred" and fold else "")
        print(f"| {state} | {d['target']} | {d['count']} | {left or ''} | {_day(d['oldest_ts'])} | {_day(d['newest_ts'])} | {src} |")
    if pool["sensor_errors"]:
        print("\nsensor errors (fail-soft, not counted):")
        for e in pool["sensor_errors"]:
            print(f"  {e['sensor']}: {e['error']}")
    if pool["totals"]["due"]:
        print("\nto review one: python -X utf8 tools/feedback-pool/feedback.py review <target>   (say 檢視回授 to start a review round)")
    return 0


def cmd_review(a) -> int:
    pool = collect()
    d = next((d for d in pool["targets"] if d["target"] == a.target), None)
    if not d:
        print(f"{a.target}: no unconsumed events (or unknown target). Known: "
              + ", ".join(x["target"] for x in pool["targets"][:20]))
        return 1
    print(f"# {d['target']} — {d['count']} event(s) since {'fold ' + _day(d['last_fold']['ts']) if d.get('last_fold') else 'the beginning'}")
    if d.get("last_fold"):
        f = d["last_fold"]
        print(f"last fold: {f['outcome']} ref={f.get('ref', '')}" + (f" trigger={f.get('trigger')}" if f.get("trigger") else ""))
    for e in d["events"]:
        extra = f" action={e['action']}" if e.get("action") else ""
        prop = f"\n    proposal: {e['proposal']}" if e.get("proposal") else ""
        print(f"- {_day(e['ts'])} [{e['source']}]{extra} {e['symptom']}\n    at: {e['locator']}{prop}")
    print("\nclose the review with ONE of:")
    print(f"  python -X utf8 tools/process-ledger/ledger.py feedback-fold --target \"{d['target']}\" --outcome adopted --ref \"<commit|D-nnn|L-nnn>\"")
    print(f"  python -X utf8 tools/process-ledger/ledger.py feedback-fold --target \"{d['target']}\" --outcome rejected --ref \"no change: <why>\"")
    print(f"  python -X utf8 tools/process-ledger/ledger.py feedback-fold --target \"{d['target']}\" --outcome deferred --ref \"<where noted>\" --trigger \"<event that reopens it>\"")
    return 0


def emit(pool: dict) -> dict:
    due = [d for d in pool["targets"] if d["due"]]
    deferred = [d for d in pool["targets"] if d["state"] == "deferred"]
    findings = [{"severity": "alarm", "label": d["target"],
                 "text": f"{d['count']} events since {_day(d['oldest_ts'])} ({', '.join(sorted(d['sources']))}) — awaiting the user's review"}
                for d in due]
    findings += [{"severity": "info", "label": d["target"],
                  "text": f"deferred — trigger: {(d.get('last_fold') or {}).get('trigger', '')}"} for d in deferred]
    for e in pool["sensor_errors"]:
        findings.append({"severity": "info", "label": f"sensor {e['sensor']}", "text": e["error"]})
    point = {"id": "feedback-pool.due", "alias": "回授池：待檢視的 target", "class": "reconcile", "ran": True,
             "skip_reason": None, "state": "warn" if due else "pass", "quality": "good", "findings": findings,
             "remedy": "python -X utf8 tools/feedback-pool/feedback.py report" if due else None}
    return {"protocol": "hmi-report/1", "source": "feedback-pool", "generated_at": pool["generated_at"], "points": [point]}


def cmd_emit(a) -> int:
    pool = collect()
    write_pool(pool)
    print(json.dumps(emit(pool), ensure_ascii=False))
    return 0


def cmd_target_of(a) -> int:
    t = target_of(a.path)
    print(t)
    return 0 if t else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("collect").set_defaults(fn=cmd_collect)
    p = sub.add_parser("report"); p.add_argument("--mine", action="store_true"); p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_report)
    p = sub.add_parser("review"); p.add_argument("target"); p.set_defaults(fn=cmd_review)
    sub.add_parser("emit").set_defaults(fn=cmd_emit)
    p = sub.add_parser("target-of"); p.add_argument("path"); p.set_defaults(fn=cmd_target_of)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
