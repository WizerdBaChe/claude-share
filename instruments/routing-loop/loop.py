#!/usr/bin/env python3
"""routing-loop: one command for the observe half of the routing feedback loop.

    derive   transcripts -> cache/routing-loop/events.jsonl (regenerable)
    queue    events that still need a judgment (with a live excerpt)
    label    append one judgment to tools/routing-loop/labels.jsonl
    run      derive + audit --snapshot + trigger-probe, one run record
    status   hmi-report/1 document (source "routing-loop") or a human table

Design: references/routing-loop-design.md. Build spec: references/routing-loop-psm.md.
Explainer: tools/routing-loop/README.md. Stdlib only.
"""
import argparse
import datetime as dt
import io
import json
import os
import subprocess
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import events as ev_mod  # noqa: E402
import store  # noqa: E402

FRESH_PASS_DAYS, FRESH_WARN_DAYS = 14, 30
BACKLOG_WARN = 30          # unjudged GROUPS, not events
BACKLOG_WINDOW_DAYS = 30
# Backlog counts only pattern groups FIRST seen on/after this date. The
# pre-baseline history (176 groups at the first live run) was never going to be
# judged; judging is driven by new patterns or a reported misroute
# (user ruling 2026-09-26). `queue --history` still lists the old groups.
BACKLOG_BASELINE = "2026-09-26"
UNPREDICTED_WARN = 0.5
INHERITED_WINDOW_DAYS = 30
POINTS = ("freshness", "derive", "skill-backlog", "skill-unpredicted",
          "probe", "model-inherited")


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------- derive

def cmd_derive(since=None, quiet=False):
    audit = ev_mod.load_audit()
    events, stats = ev_mod.derive(since=since, audit=audit)
    store.write_events(events)
    r = store.ruler(audit.LOOKAHEAD, since)
    if not quiet:
        c = Counter((e["node"], e["outcome"]) for e in events)
        print(f"events: {len(events)}  files: {stats['files']}  "
              f"turns: {stats['turns']}  ruler: dict {r['dict_sha']}, "
              f"lookahead {r['lookahead']}, since {since or 'all'}")
        for (node, outcome), n in sorted(c.items()):
            print(f"  {node:12} {outcome:12} {n:6}")
    return events, stats, r


# ---------------------------------------------------------------- queue

def _excerpt(ev):
    """Read the matched turn at print time; nothing is persisted (INV-3)."""
    base = ev["record_uuid"].split("#")[0]
    tok = ev.get("token")
    projects = os.path.join(store.HOME_CLAUDE, "projects")
    for dirpath, _, names in os.walk(projects):
        if ev["session"] + ".jsonl" not in names:
            continue
        try:
            with io.open(os.path.join(dirpath, ev["session"] + ".jsonl"),
                         encoding="utf-8", errors="replace") as fh:
                for raw in fh:
                    if base not in raw:
                        continue
                    rec = json.loads(raw)
                    if rec.get("uuid") != base:
                        continue
                    txt = _flat_text(rec.get("message"))
                    if tok and tok in txt:
                        i = txt.index(tok)
                        return txt[max(0, i - 60):i + 60].replace("\n", " ")
                    return txt[:120].replace("\n", " ")
        except (OSError, ValueError):
            break
    return "原文已不在"


def _flat_text(msg):
    if not isinstance(msg, dict):
        return ""
    c = msg.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = []
        for b in c:
            if isinstance(b, dict):
                if b.get("type") == "text":
                    parts.append(b.get("text", ""))
                elif b.get("type") == "tool_use":
                    parts.append(json.dumps(b.get("input") or {},
                                            ensure_ascii=False)[:200])
        return " ".join(parts)
    return ""


def queued_groups(events, latest, node=None, show_all=False, window_days=None,
                  now=None, first_seen_since=None):
    """{group_id: {key, events:[...], state}} for groups with at least one
    queued (or, with show_all, parked) event, optionally only groups whose
    LATEST event falls inside the window and/or whose FIRST event (any
    state) is on/after first_seen_since."""
    groups, first = {}, {}
    for e in events:
        if node and e["node"] != node:
            continue
        gid = store.group_id(store.group_key(e))
        d = e.get("date") or ""
        if gid not in first or d < first[gid]:
            first[gid] = d
        st = store.label_state(e, latest)
        if not (st == "queued" or (show_all and st == "parked")):
            continue
        key = store.group_key(e)
        g = groups.setdefault(store.group_id(key),
                              {"key": key, "events": [], "state": st})
        g["events"].append(e)
    if window_days is not None:
        now = now or dt.datetime.now(dt.timezone.utc)
        cutoff = (now - dt.timedelta(days=window_days)).strftime("%Y-%m-%d")
        groups = {k: g for k, g in groups.items()
                  if max(x.get("date") or "" for x in g["events"]) >= cutoff}
    if first_seen_since:
        groups = {k: g for k, g in groups.items()
                  if first.get(k, "") >= first_seen_since}
    return groups


def cmd_queue(node=None, show_all=False, limit=20, per_event=False,
              window_days=BACKLOG_WINDOW_DAYS, history=False):
    """Default: groups first seen on/after BACKLOG_BASELINE (what the backlog
    point counts). history=True: pre-baseline groups too, filtered by the
    latest-event window instead."""
    events = store.read_events()
    if not events:
        print("no events — run `loop.py derive` first")
        return 0
    latest = store.latest_labels()
    if not per_event:
        if history:
            groups = queued_groups(events, latest, node, show_all, window_days)
            scope = (f", latest event within {window_days} d"
                     if window_days else ", all history")
        else:
            groups = queued_groups(events, latest, node, show_all,
                                   first_seen_since=BACKLOG_BASELINE)
            scope = (f", first seen on/after {BACKLOG_BASELINE}"
                     " (--history for older)")
        order = sorted(groups.items(), key=lambda kv: (
            -len(kv[1]["events"]), kv[1]["key"]))
        print(f"{len(groups)} pattern group(s) awaiting judgment"
              f"{' (incl. parked)' if show_all else ''}"
              f"{scope}"
              f"; showing {min(limit, len(groups))}. One verdict covers every "
              f"event of the group, now and later.")
        for gid, g in order[:limit]:
            evs = sorted(g["events"], key=lambda x: x.get("date") or "")
            print(f"\n{gid}  x{len(evs)}  {evs[0].get('date')}..{evs[-1].get('date')}"
                  f"  {g['key']}{'  [parked]' if g['state'] == 'parked' else ''}")
            print(f"    latest: {_excerpt(evs[-1])}")
        _label_hint(node)
        return 0
    rows = []
    for e in events:
        if node and e["node"] != node:
            continue
        st = store.label_state(e, latest)
        if st == "queued" or (show_all and st == "parked"):
            rows.append((e, st))
    rows.sort(key=lambda x: x[0].get("date") or "", reverse=True)
    print(f"{len(rows)} event(s) awaiting judgment"
          f"{' (incl. parked)' if show_all else ''}; showing {min(limit, len(rows))}")
    for e, st in rows[:limit]:
        who = e.get("fired") or ""
        extra = f" fired={who}" if who and who != e["subject"] else ""
        print(f"\n{e['event_id']}  {e['date']}  {e['node']}  {e['outcome']}"
              f"{' LATE' if e.get('late') else ''}  {e['subject']}{extra}"
              f"{'  token=' + e['token'] if e.get('token') else ''}"
              f"{'  [parked]' if st == 'parked' else ''}")
        print(f"    {_excerpt(e)}")
    _label_hint(node)
    return 0


def _label_hint(node):
    vocab = ({node: sorted(store.VERDICTS[node])} if node else
             {k: sorted(v) for k, v in store.VERDICTS.items()})
    print(f"\nlabel with: loop.py label <group_id|event_id> <verdict> --why \"...\""
          f"\nverdicts: {vocab}")


# ---------------------------------------------------------------- run

def _step(name, fn):
    t0 = time.time()
    try:
        detail = fn()
        return {"step": name, "state": "ok", "secs": round(time.time() - t0, 1),
                **(detail or {})}
    except Exception as exc:  # a failing step never aborts the run (PSM 2.6)
        return {"step": name, "state": "failed",
                "secs": round(time.time() - t0, 1),
                "error": f"{type(exc).__name__}: {exc}"[:400]}


def _run_py(argv, timeout=900):
    # The audit and the probe resolve `~/.claude` themselves. Point the child's
    # home at HOME_CLAUDE's parent so a fixture home (tests) can never reach
    # the live corpus or append to live telemetry; in normal use this is the
    # user's own profile, i.e. a no-op.
    env = dict(os.environ)
    parent = os.path.dirname(store.HOME_CLAUDE)
    env["USERPROFILE"] = env["HOME"] = parent
    p = subprocess.run([sys.executable, "-X", "utf8"] + argv,
                       cwd=store.HOME_CLAUDE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout,
                       env=env)
    if p.returncode not in (0,):
        raise RuntimeError(f"exit {p.returncode}: {(p.stderr or p.stdout)[-300:]}")
    return p.stdout


def parse_probe_stdout(stdout):
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)
    raise ValueError("no JSON line in trigger_probe output")


def cmd_run(since=None, probe=True, snapshot=True):
    record = {"ts": _now(), "since": since, "steps": []}
    box = {}

    def do_derive():
        events, stats, r = cmd_derive(since, quiet=True)
        box["ruler"] = r
        return {"events": len(events), **stats}

    record["steps"].append(_step("derive", do_derive))

    if snapshot:
        argv = [store.AUDIT, "--snapshot"] + (["--since", since] if since else [])
        record["steps"].append(_step("audit-snapshot",
                                     lambda: (_run_py(argv), None)[1]))
    else:
        record["steps"].append({"step": "audit-snapshot", "state": "skipped"})

    if probe:
        def do_probe():
            p = parse_probe_stdout(_run_py([store.PROBE, "run", "--json",
                                            "--no-report"]))
            keep = {k: p.get(k) for k in ("suites", "probes", "verdicts",
                                          "fails", "scorer_version",
                                          "calibration_id")}
            box["probe"] = {"scorer_version": keep["scorer_version"],
                            "calibration_id": keep["calibration_id"]}
            return {"probe": keep}
        record["steps"].append(_step("probe", do_probe))
    else:
        record["steps"].append({"step": "probe", "state": "skipped"})

    record["ruler"] = store.ruler((box.get("ruler") or {}).get("lookahead"),
                                  since, box.get("probe"))
    store.write_run(record)
    for s in record["steps"]:
        print(f"  {s['step']:15} {s['state']:8} {s.get('secs', '')}"
              f"{'  ' + s['error'] if s.get('error') else ''}")
    print(f"run recorded: {store.LAST_RUN}")
    return 1 if all(s["state"] == "failed" for s in record["steps"]) else 0


# ---------------------------------------------------------------- status

def _point(slug, state, findings=None, remedy=None, ran=True, skip=None):
    p = {"id": f"routing-loop.{slug}", "ran": ran,
         "state": state if ran else None}
    if not ran:
        p["skip_reason"] = skip
    if findings:
        p["findings"] = findings
    if remedy:
        p["remedy"] = remedy
    return p


def _f(sev, label, text):
    return {"severity": sev, "label": label, "text": text}


def _step_of(run, name):
    for s in (run or {}).get("steps", []):
        if s.get("step") == name:
            return s
    return None


def build_status(now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    run = store.read_last_run()
    events = store.read_events()
    latest = store.latest_labels()
    RUN_CMD = "python -X utf8 tools/routing-loop/loop.py run"
    pts = []

    # freshness — determinable, may fail
    if run is None:
        pts.append(_point("freshness", "fail",
                          [_f("alarm", "never run", "the loop has no run record")],
                          RUN_CMD))
    else:
        ts = dt.datetime.strptime(run["ts"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=dt.timezone.utc)
        age = (now - ts).days
        st = ("pass" if age <= FRESH_PASS_DAYS else
              "warn" if age <= FRESH_WARN_DAYS else "fail")
        pts.append(_point("freshness", st,
                          [_f("info", "last run", f"{run['ts']} ({age} d ago; "
                              f"pass ≤{FRESH_PASS_DAYS} d, fail >{FRESH_WARN_DAYS} d)")],
                          RUN_CMD if st != "pass" else None))

    # derive — determinable
    if run is None:
        pts.append(_point("derive", None, ran=False, skip="never-run"))
    else:
        s = _step_of(run, "derive") or {}
        bad = s.get("state") != "ok" or not s.get("events")
        pts.append(_point("derive", "fail" if bad else "pass",
                          [_f("alarm" if bad else "info", "derive",
                              s.get("error") or f"{s.get('events', 0)} events, "
                              f"{s.get('files', 0)} files, "
                              f"{s.get('parse_skipped', 0)} lines unparsable")],
                          "check tools/skill-routing-audit.py path" if bad else None))

    skill = [e for e in events if e["node"] == "skill-route"]
    ruler_txt = f"ruler dict {((run or {}).get('ruler') or {}).get('dict_sha')}"

    # skill-backlog — advisory, warn max
    if run is None:
        pts.append(_point("skill-backlog", None, ran=False, skip="never-run"))
        pts.append(_point("skill-unpredicted", None, ran=False, skip="never-run"))
    else:
        states = Counter(store.label_state(e, latest) for e in skill)
        q = len(queued_groups(skill, latest,
                              first_seen_since=BACKLOG_BASELINE))
        h = len(queued_groups(skill, latest)) - q
        pts.append(_point(
            "skill-backlog", "pass" if q <= BACKLOG_WARN else "warn",
            [_f("info" if q <= BACKLOG_WARN else "warning", "judgment queue",
                f"{q} unjudged pattern group(s) first seen on/after "
                f"{BACKLOG_BASELINE} (pre-baseline history {h} group(s), not "
                f"counted: `queue --history`); all-time events queued "
                f"{states.get('queued', 0)}, parked {states.get('parked', 0)}, "
                f"judged {states.get('judged', 0)}, orphan labels "
                f"{len(store.orphans(events, latest))} (warn >{BACKLOG_WARN} "
                f"groups; promotion trigger: group count grows across 3 "
                f"consecutive runs)")],
            "python -X utf8 tools/routing-loop/loop.py queue" if q > BACKLOG_WARN else None))
        auto = [e for e in skill if e["outcome"] in ("HIT", "BYPASS", "UNPREDICTED")]
        unp = sum(1 for e in auto if e["outcome"] == "UNPREDICTED")
        share = unp / len(auto) if auto else 0.0
        pts.append(_point(
            "skill-unpredicted", "pass" if share < UNPREDICTED_WARN else "warn",
            [_f("info" if share < UNPREDICTED_WARN else "warning",
                "fires the dict did not predict",
                f"{unp}/{len(auto)} = {share:.0%} ({ruler_txt}; warn ≥"
                f"{UNPREDICTED_WARN:.0%}; promotion trigger: a user-ruled "
                f"coverage target)")]))

    # probe
    ps = _step_of(run, "probe")
    if run is None:
        pts.append(_point("probe", None, ran=False, skip="never-run"))
    elif ps is None or ps.get("state") == "skipped":
        pts.append(_point("probe", None, ran=False, skip="skipped"))
    elif ps.get("state") == "failed":
        pts.append(_point("probe", "fail", [_f("alarm", "probe failed",
                                                ps.get("error", ""))],
                          "python -X utf8 tools/trigger-probe/trigger_probe.py run"))
    else:
        fails = (ps.get("probe") or {}).get("fails")
        prev = _previous_comparable(run)
        pf = ((_step_of(prev, "probe") or {}).get("probe") or {}).get("fails") \
            if prev else None
        worse = fails is not None and pf is not None and fails > pf
        pts.append(_point("probe", "warn" if worse else "pass",
                          [_f("warning" if worse else "info", "predicted fails",
                              f"{fails} (previous comparable run: "
                              f"{pf if pf is not None else 'none'}; promotion "
                              f"trigger: none — prediction is advisory)")]))

    # model-inherited — advisory
    if run is None:
        pts.append(_point("model-inherited", None, ran=False, skip="never-run"))
    else:
        cutoff = (now - dt.timedelta(days=INHERITED_WINDOW_DAYS)).strftime("%Y-%m-%d")
        inh = [e for e in events if e["node"] == "model-route"
               and e["outcome"] == "INHERITED" and (e.get("date") or "") >= cutoff]
        pts.append(_point("model-inherited", "warn" if inh else "pass",
                          [_f("warning" if inh else "info", "inherited dispatches",
                              f"{len(inh)} Agent dispatch(es) without a model "
                              f"in the last {INHERITED_WINDOW_DAYS} d (promotion "
                              f"trigger: none — the cap hook is the enforcement)")]))

    return {"protocol": "hmi-report/1", "source": "routing-loop",
            "generated_at": _now(), "points": pts, "tree": TREE}


def _previous_comparable(run):
    # By position, not timestamp: two runs can share a second. The last line of
    # the run log is the run being judged (write_run appends it).
    runs = store.previous_runs()
    prior = runs[:-1] if runs and runs[-1] == run else runs
    for r in reversed(prior):
        if store.comparable(r.get("ruler"), run.get("ruler")) is None:
            return r
    return None


TREE = {"id": "routing-loop", "title_zh": "路由回饋迴圈", "children": [
    {"id": "skill-route", "title_zh": "Skill 路由", "stages": {
        "SPEC": ["ops-health.dict-sync"],
        "PREDICT": ["routing-loop.probe"],
        "OBSERVE": ["routing-loop.derive", "routing-loop.freshness"],
        "CLASSIFY": [],
        "JUDGE": ["routing-loop.skill-backlog", "routing-loop.skill-unpredicted"],
        "CONSTRAIN": ["ops-health.skill-preload-budgets"]}},
    {"id": "model-route", "title_zh": "模型路由", "stages": {
        "SPEC": [], "PREDICT": [],
        "OBSERVE": ["routing-loop.derive"],
        "JUDGE": ["routing-loop.model-inherited"],
        "CONSTRAIN": []}}]}


def cmd_status(as_json=False):
    doc = build_status()
    if as_json:
        print(json.dumps(doc, ensure_ascii=False, indent=1))
        return 0
    for p in doc["points"]:
        st = p["state"] if p["ran"] else f"— ({p.get('skip_reason')})"
        text = "; ".join(f["text"] for f in p.get("findings", []))
        print(f"{p['id']:34} {st:18} {text}")
        if p.get("remedy"):
            print(f"{'':34} → {p['remedy']}")
    return 0


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("derive"); d.add_argument("--since")
    q = sub.add_parser("queue")
    q.add_argument("--node", choices=store.NODES)
    q.add_argument("--all", action="store_true")
    q.add_argument("--limit", type=int, default=20)
    q.add_argument("--events", action="store_true",
                   help="one row per event instead of per pattern group")
    q.add_argument("--window", type=int, default=BACKLOG_WINDOW_DAYS,
                   help="with --history: groups whose latest event is within "
                        "N days (0 = all)")
    q.add_argument("--history", action="store_true",
                   help="include groups first seen before BACKLOG_BASELINE")
    lb =sub.add_parser("label")
    lb.add_argument("target", help="group id (g...) or event id")
    lb.add_argument("verdict")
    lb.add_argument("--why", required=True)
    lb.add_argument("--origin", default="model", choices=("user", "model"))
    lb.add_argument("--orphan-ok", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("--since")
    r.add_argument("--no-probe", action="store_true")
    r.add_argument("--no-audit-snapshot", action="store_true")
    s = sub.add_parser("status"); s.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    if a.cmd == "derive":
        cmd_derive(a.since)
        return 0
    if a.cmd == "queue":
        return cmd_queue(a.node, a.all, a.limit, a.events, a.window or None,
                         a.history)
    if a.cmd == "label":
        try:
            row = store.add_label(a.target, a.verdict, a.why, a.origin,
                                  a.orphan_ok)
        except store.ValidationError as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 2
        print(f"labelled {row.get('group_id') or row.get('event_id')} -> {row['verdict']}")
        return 0
    if a.cmd == "run":
        return cmd_run(a.since, not a.no_probe, not a.no_audit_snapshot)
    if a.cmd == "status":
        return cmd_status(a.json)
    return 2


if __name__ == "__main__":
    sys.exit(main())
