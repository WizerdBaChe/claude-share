r"""Backtest `hooks/ps_pipeline_close_guard.py` against the real transcript corpus.

This is the instrument behind the fire-rate numbers in `ops/rule-registry.md`
(key: `ps_pipeline_close_guard`). It ran BEFORE the hook was registered, because
L-011's fifth shape is that a hook pointed at the wrong SURFACE is as silent as
prose, and only the corpus can say which surface the failure actually arrives
on. The neighbouring guard's ticket asked for a check on the PowerShell tool
when 47 of 53 real payloads came through Write; the answer is not transferable,
it is measured per trap.

It imports `analyze()` and `payload_for()` from the shipped hook rather than
reimplementing them. A copy drifts, and then the reported rate describes a
detector nobody runs - that happened to the ps-errorpref backtest on its first
day.

    python backtest.py                       # live transcripts + the daily mirror
    python backtest.py --sample 12           # print 12 hits in full
    python backtest.py --root <dir> [...]    # override the corpus roots
    python backtest.py --json hits.json      # dump every hit for reading

WHAT "FIRE RATE" MEANS HERE, and it is not one number. The guard sits on tools
with wildly different volumes, and only a sliver of Write/Edit traffic is
PowerShell at all. So the report prints, per tool: total calls (the PreToolUse
tax), PowerShell-language payloads (what the guard actually inspects), and
fires. Quoting the middle column as the denominator flatters the guard; quoting
the first hides that it does real work. It also splits fires by TIER - `work`
(an interpreter or builder that may still have work to do) versus `report` (a
native that normally prints and exits) - because that split is the registration
decision, and it should be made from rows rather than from taste.
"""
import argparse
import io
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "hooks"))
import ps_pipeline_close_guard as guard  # noqa: E402

# SHARE EDITION: the source also listed an offline session-archive directory on a
# second drive here. It is machine-specific, so it is dropped; pass further
# corpus roots with --root (repeatable).
DEFAULT_ROOTS = [
    os.path.join(os.path.expanduser("~"), ".claude", "projects"),
]

# Measured 2026-08-21 over live transcripts + the offline session archive, in the
# state the corpus was in BEFORE this hook existed. A later run prints its own
# numbers beside these and they will not match exactly: the session doing the
# measuring writes into the corpus it is measuring, so `calls` drifts upward
# every run, and this guard's own calibration suite and proof-of-life probe are
# real tool calls too. Named rather than filtered - a filter is a place for a
# real hit to hide.
# THE ONE NAMED EXTRA: expect one additional PowerShell fire from now on. The
# hook's live proof-of-life is `python --version | Select-Object -First 1`, run
# as a real PowerShell tool call in a local session on 2026-08-21 - the first
# organic fire, and the R2.2 "living proof" this batch's own ruling demands
# (editing the code is not the same as fixing the problem). It is telemetry row
# 1 of telemetry/ps-pipeline-close.jsonl, so that log needs no "discount the
# first N rows" caveat: row 1 is genuine, the suite and the sweep probe redirect
# elsewhere.
BASELINE = {
    "window": "2026-06-22..2026-08-20 (56 days, 726 transcript files)",
    "calls": {"PowerShell": 3411, "Write": 3548, "Edit": 7668, "Bash": 11367},
    "payloads": {"PowerShell": 3411, "Write": 85, "Edit": 142, "Bash": 226},
    # As shipped (FIRE_TIERS = ("work",)). The detector also found 66 report-tier
    # hazards (git x64, gh x2) that are deliberately not annotated; the run
    # reprints them under SUPPRESSED so the decision stays re-openable.
    "fires": {"PowerShell": 100, "Write": 0, "Edit": 0, "Bash": 0},
    "registered": ("PowerShell",),
}

# Measured 2026-08-21 for the sibling guard (median of 15 subprocess round-trips)
# and reused: 105 ms, essentially all of it Python start-up, so a payload that
# FIRES is no slower than one that exits on the first branch. Used only to price
# the tax in seconds/day.
MS_PER_CALL = 105


def registered_tools():
    """Which tools settings.json actually wires this hook to -> (set, source).

    DERIVED, never restated. A second mechanism holding its own copy of a value
    the owner also holds is integrity-sweep check 10's defect class. If the parse
    fails, say so rather than silently reverting to the declared baseline.
    """
    path = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
    try:
        d = json.load(io.open(path, encoding="utf-8"))
        for entry in d.get("hooks", {}).get("PreToolUse", []):
            for h in entry.get("hooks", []):
                if "ps_pipeline_close_guard" in h.get("command", ""):
                    m = str(entry.get("matcher", ""))
                    return set(t for t in m.split("|") if t), "settings.json"
        return set(), "settings.json (NOT REGISTERED YET)"
    except Exception as e:
        return set(BASELINE["registered"]), "declared fallback (settings.json unreadable: %s)" % e


def collect(roots):
    calls = Counter()
    payloads = []            # (ts, tool, label, text, project)
    seen = set()
    days = set()
    nfiles = 0
    for root in roots:
        if not os.path.isdir(root):
            print("  (root not found, skipped: %s)" % root)
            continue
        for dp, dn, fn in os.walk(root):
            for f in fn:
                if not f.endswith(".jsonl"):
                    continue
                nfiles += 1
                try:
                    lines = io.open(os.path.join(dp, f), encoding="utf-8",
                                    errors="replace").readlines()
                except Exception:
                    continue
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except Exception:
                        continue
                    if d.get("type") != "assistant":
                        continue
                    ts = d.get("timestamp", "")
                    c = d.get("message", {}).get("content")
                    if not isinstance(c, list):
                        continue
                    for b in c:
                        if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                            continue
                        tool = b.get("name")
                        inp = b.get("input") or {}
                        if not isinstance(inp, dict):
                            continue
                        fp = str(inp.get("file_path", "") or "")
                        cmd = str(inp.get("command", "") or "")
                        # Sidechain/compaction rewrites repeat a call verbatim
                        # (up to 6x); dedupe or every rate is inflated.
                        key = (ts, tool, (cmd or fp)[:400])
                        if key in seen:
                            continue
                        seen.add(key)
                        calls[tool] += 1
                        if ts:
                            days.add(ts[:10])
                        text, label = guard.payload_for(tool, inp)
                        if text:
                            payloads.append((ts, tool, label, text,
                                             os.path.basename(dp)))
    return calls, payloads, days, nfiles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", action="append", dest="roots")
    ap.add_argument("--sample", type=int, default=8)
    ap.add_argument("--json", dest="dump")
    a = ap.parse_args()
    roots = a.roots or DEFAULT_ROOTS

    print("roots  : %s" % ", ".join(roots))
    calls, payloads, days, nfiles = collect(roots)
    if not payloads:
        print("no PowerShell-language payloads found")
        return 1
    nday = len(days) or 1
    print("corpus : %d transcript files, %d distinct days (%s .. %s)"
          % (nfiles, nday, min(days), max(days)))
    print()

    hits = []
    per_tool_payloads = Counter()
    for ts, tool, label, text, proj in payloads:
        per_tool_payloads[tool] += 1
        if guard.MARKER in text:
            continue
        f = guard.analyze(text)
        if f:
            hits.append((ts, tool, label, text, proj, f))

    reg, reg_src = registered_tools()
    fires = Counter(h[1] for h in hits)
    print("== fire rate, three denominators (see the module docstring) ==")
    print("  registration read from: %s -> %s" % (reg_src, "|".join(sorted(reg)) or "NONE"))
    print("  %-11s %4s %8s %8s %10s %7s"
          % ("tool", "reg?", "calls", "payloads", "tax/day", "FIRES"))
    for tool in ("PowerShell", "Write", "Edit", "Bash"):
        n, p, fr = calls[tool], per_tool_payloads[tool], fires[tool]
        print("  %-11s %4s %8d %8d %9.1fs %7d"
              % (tool, "yes" if tool in reg else " - ", n, p,
                 (n / nday) * MS_PER_CALL / 1000.0, fr))
    tot_calls = sum(calls[t] for t in ("PowerShell", "Write", "Edit", "Bash"))
    tot_pay = sum(per_tool_payloads.values())
    print("  %-11s %4s %8d %8d %9.1fs %7d"
          % ("TOTAL(all)", " - ", tot_calls, tot_pay,
             (tot_calls / nday) * MS_PER_CALL / 1000.0, len(hits)))

    # The split that decides what SPEAKS: `work` is the L-027 damage (a process
    # with work left to do is killed); `report` costs only a misleading exit
    # code and is deliberately silent. The silent tier is re-measured here on
    # purpose - a class that is suppressed and no longer counted is a class
    # nobody can ever re-open, and `rule-registry.md`'s review-when for this
    # rule is written against these exact rows.
    tier_tool = defaultdict(Counter)
    for ts, tool, label, text, proj, f in hits:
        for t in f["tiers"]:
            tier_tool[t][tool] += 1
    print()
    print("== fires by tier, AS SHIPPED (FIRE_TIERS = %r) ==" % (guard.FIRE_TIERS,))
    for t in ("work", "report"):
        tot = sum(tier_tool[t].values())
        detail = ", ".join("%s=%d" % (k, v) for k, v in sorted(tier_tool[t].items()))
        print("  %-7s %4d   %s" % (t, tot, detail or "-"))

    shipped = guard.FIRE_TIERS
    guard.FIRE_TIERS = ("work", "report")
    try:
        sup = Counter()
        sup_up = Counter()
        for ts, tool, label, text, proj_ in [(p[0], p[1], p[2], p[3], p[4]) for p in payloads]:
            if guard.MARKER in text:
                continue
            f = guard.analyze(text)
            if not f:
                continue
            for h in f["all"]:
                if h["tier"] not in shipped:
                    sup[tool] += 1
                    sup_up[h["upstream"]] += 1
    finally:
        guard.FIRE_TIERS = shipped
    print("  SUPPRESSED (detected, deliberately not annotated): %d   %s"
          % (sum(sup.values()),
             ", ".join("%s=%d" % kv for kv in sorted(sup.items())) or "-"))
    print("    upstreams: %s"
          % (", ".join("%s x%d" % kv for kv in sup_up.most_common(12)) or "-"))
    print("    ACT ON: any upstream in that list that can MUTATE something "
          "(cloud CLIs, registry, scheduled tasks, signing, package publish) -> "
          "it is mis-tiered; move it to TIER_WORK.")

    r_calls = sum(calls[t] for t in reg)
    r_pay = sum(per_tool_payloads[t] for t in reg)
    r_fires = sum(fires[t] for t in reg)
    print()
    print("  AS REGISTERED (%s):" % ("|".join(sorted(reg)) or "nothing"))
    print("    fires / inspected payload : %d/%d = %.2f%%   (%.3f / day)"
          % (r_fires, r_pay, 100.0 * r_fires / max(1, r_pay), r_fires / nday))
    print("    fires / hooked tool call  : %d/%d = %.3f%%"
          % (r_fires, r_calls, 100.0 * r_fires / max(1, r_calls)))
    print("    PreToolUse tax            : %.0f invocations/day = %.1f s/day at %d ms"
          % (r_calls / nday, (r_calls / nday) * MS_PER_CALL / 1000.0, MS_PER_CALL))
    print("  MEASURED BUT NOT REGISTERED: %d fires on %s"
          % (len(hits) - r_fires,
             ", ".join(t for t in ("PowerShell", "Write", "Edit", "Bash")
                       if t not in reg) or "nothing"))

    print()
    by_up = Counter()
    for ts, tool, label, text, proj, f in hits:
        for h in f["all"]:
            by_up[(h["tier"], h["upstream"])] += 1
    print("== distinct upstream commands, most frequent first ==")
    for (t, up), v in sorted(by_up.items(), key=lambda kv: -kv[1])[:25]:
        print("  %-7s %-40s %d" % (t, up[:40], v))

    print()
    print("== sample (%d of %d), read these before believing the rate ==" % (
        min(a.sample, len(hits)), len(hits)))
    for ts, tool, label, text, proj, f in sorted(hits, key=lambda h: h[0])[:a.sample]:
        print("-" * 74)
        print("%s  %s  %s  [%s]" % (ts[:19], tool, label, ",".join(f["tiers"])))
        print("  upstream : %s" % f["first"]["upstream"])
        print("  consumer : %s" % f["first"]["consumer"])
        print("  statement: %s" % f["first"]["statement"][:150])

    if a.dump:
        io.open(a.dump, "w", encoding="utf-8").write(json.dumps(
            [{"ts": h[0], "tool": h[1], "label": h[2], "project": h[4],
              "finding": h[5], "text": h[3]} for h in hits],
            ensure_ascii=False, indent=1))
        print()
        print("wrote %d hits -> %s" % (len(hits), a.dump))
    return 0


if __name__ == "__main__":
    sys.exit(main())
