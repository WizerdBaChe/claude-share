r"""Break down `telemetry/rule-loads.jsonl`: what loads, when, and how often.

The instrument behind `ops/rule-registry.md` -> "instruction carriers that
reduce startup cost". That entry's `review-when` is "any Claude Code upgrade",
and in 2026-08 it fired 13 builds before anyone noticed, because re-running the
breakdown meant rewriting the parser from scratch each time. This file is the
fix for that.

    python rule_loads.py
    python rule_loads.py --since 2026-08-10

Read the RATES with care. Absolute fires and session-rates move in opposite
directions as the corpus grows: between 2026-08-14 and 2026-08-19 the
denominator grew 4.5x while `frontend-layering` went 7 -> 8 fires, so its rate
fell 3.3% -> 0.7% describing identical behaviour. Compare absolute counts across
runs; use the rate only within one run.

A LOW rate is not automatically a defect and not automatically accuracy — for a
rule dispatched by file extension it is accuracy only if the rule's globs can
actually reach its subject. `tools/glob-fitness.py` is the check for that.
"""
import argparse
import io
import json
import os
import sys
from collections import Counter, defaultdict

DEFAULT = os.path.join(os.path.expanduser("~"), ".claude", "telemetry", "rule-loads.jsonl")

# Recorded runs, so a later one can be compared without digging up the registry.
BASELINES = [
    ("2026-08-14", 332, 241, {"CLAUDE.md": 241, "frontend-layering.md": 7,
                              "shader-failure-modes.md": 1}),
    ("2026-08-19", 1590, 1094, {"CLAUDE.md": 1094, "frontend-layering.md": 8,
                                "shader-failure-modes.md": 1}),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=DEFAULT)
    ap.add_argument("--since", default="")
    a = ap.parse_args()

    if not os.path.isfile(a.path):
        print("not found: %s" % a.path)
        return 2

    rows = []
    for line in io.open(a.path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if a.since and d.get("ts", "") < a.since:
            continue
        rows.append(d)
    if not rows:
        print("no events in window")
        return 1

    sessions, by_file, sess_by_file, reason_by_file = set(), Counter(), defaultdict(set), defaultdict(Counter)
    for r in rows:
        p = r.get("payload") or {}
        sid = p.get("session_id") or r.get("session_id")
        sessions.add(sid)
        name = os.path.basename(str(p.get("file_path") or "?"))
        by_file[name] += 1
        sess_by_file[name].add(sid)
        reason_by_file[name][p.get("load_reason", "?")] += 1

    tot = len(sessions)
    print("file   : %s" % a.path)
    print("window : %s .. %s" % (min(r["ts"] for r in rows)[:16], max(r["ts"] for r in rows)[:16]))
    print("events : %d over %d distinct sessions" % (len(rows), tot))
    print()
    print("  %-30s %7s %9s %8s  load reasons" % ("file", "events", "sessions", "session%"))
    for f, c in by_file.most_common(15):
        n = len(sess_by_file[f])
        print("  %-30s %7d %9d %7.1f%%  %s"
              % (f, c, n, 100.0 * n / tot, dict(reason_by_file[f])))

    print()
    print("== against recorded runs (compare ABSOLUTE fires, not rates) ==")
    print("  %-12s %8s %9s  %s" % ("run", "events", "sessions", "per-file session counts"))
    for when, ev, ss, counts in BASELINES:
        print("  %-12s %8d %9d  %s" % (when, ev, ss, counts))
    now = {f: len(sess_by_file[f]) for f in
           ("CLAUDE.md", "frontend-layering.md", "shader-failure-modes.md") if f in sess_by_file}
    print("  %-12s %8d %9d  %s" % ("this run", len(rows), tot, now))

    cm = len(sess_by_file.get("CLAUDE.md", set()))
    print()
    print("  CLAUDE.md at session_start in %.1f%% of sessions  %s"
          % (100.0 * cm / tot, "OK" if cm / tot > 0.99 else "<-- CHANGED, the carrier claim rests on this"))
    ops = sum(v for k, v in by_file.items() if k.startswith(("OPS", "05-", "10-", "20-", "30-", "40-", "50-", "60-", "70-")))
    print("  ops/*.md events: %d  (expected 0 — InstructionsLoaded does not cover" % ops)
    print("                   Read-tool loads, so this is UNINSTRUMENTED, never")
    print("                   evidence that ops/ failed to load)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
