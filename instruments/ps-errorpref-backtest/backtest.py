r"""Backtest `hooks/ps_errorpref_guard.py` against the real transcript corpus.

This is the instrument behind the fire-rate numbers in `ops/rule-registry.md`
(key: `ps_errorpref_guard`). It exists because the transport guard's first
design was WRONG and only a backtest said so: it flagged 112 real Bash calls of
which 89 had succeeded. A detector that has never met the corpus is a guess.

It imports `analyze()` from the shipped hook rather than reimplementing it. A
copy would drift, and then the reported rate would describe a detector nobody
is running.

    python backtest.py                       # live transcripts + the daily mirror
    python backtest.py --sample 12           # print 12 hits in full
    python backtest.py --root <dir> [...]    # override the corpus roots
    python backtest.py --json hits.json      # dump every hit for reading

WHAT "FIRE RATE" MEANS HERE, and it is not one number. This guard sits on four
tools with wildly different volumes, and only a sliver of Write/Edit traffic is
PowerShell at all. So the report prints, per tool: total calls (the PreToolUse
tax), PowerShell-language payloads (what the guard actually inspects), and
fires. Quoting the middle column as the denominator would flatter the guard;
quoting the first would hide that it does real work.
"""
import argparse
import io
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "hooks"))
import ps_errorpref_guard as guard  # noqa: E402

# SHARE EDITION: the source also listed an offline session-archive directory on a
# second drive here. It is machine-specific, so it is dropped; pass further
# corpus roots with --root (repeatable).
DEFAULT_ROOTS = [
    os.path.join(os.path.expanduser("~"), ".claude", "projects"),
]

# Measured 2026-08-21 over live transcripts + the offline session archive, in the
# state the corpus was in BEFORE this hook existed. A later run prints its own
# numbers beside these, and they will not match exactly -- the session doing the
# measuring writes into the corpus it is measuring, so `calls` drifts upward
# every run. Expect ONE extra Write fire on re-run from now on: the hook's own
# live proof-of-life (`liveprobe.ps1`, a local session, 2026-08-21) is a real
# annotated Write and is counted like any other. It is named here rather than
# filtered out, because a filter is a place for a real hit to hide.
BASELINE = {
    "window": "2026-06-22..2026-08-20 (56 days)",
    "calls": {"PowerShell": 3405, "Write": 3503, "Edit": 7549, "Bash": 11149},
    "payloads": {"PowerShell": 3405, "Write": 83, "Edit": 124, "Bash": 209},
    "fires": {"PowerShell": 1, "Write": 20, "Edit": 0, "Bash": 1},
    # Which surfaces settings.json actually registers. Everything else is
    # measured but not enforced -- see the hook docstring for the prices.
    "registered": ("PowerShell", "Write"),
}

# NOTE ON THE ROUTING. Which text a tool call carries is `guard.payload_for`,
# IMPORTED, never restated here. The first version of this file kept its own
# copy and diverged from the hook the same day: it fed analyze() the whole Bash
# command where the hook feeds only the heredoc body, so the reported hits
# included a `powershell.exe ... 2>&1` line the hook never sees. A comment
# promising the two would stay in step is what failed; one function is what
# fixes it.


# Measured 2026-08-21 (median of 15 subprocess round-trips): 105 ms, essentially
# all of it Python start-up -- a payload that FIRES is no slower than one that
# exits on the first branch. Used only to price the tax in seconds/day.
MS_PER_CALL = 105


def registered_tools():
    """Which tools settings.json actually wires this hook to -> (set, source).

    DERIVED, never restated. A second mechanism holding its own copy of a value
    the owner also holds is the defect class of integrity-sweep check 10 -- the
    dashboard printed a breach that did not exist for 12 days that way. If the
    parse fails, say so and fall back to the declared baseline rather than
    silently reverting to it.
    """
    path = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
    try:
        d = json.load(io.open(path, encoding="utf-8"))
        for entry in d.get("hooks", {}).get("PreToolUse", []):
            for h in entry.get("hooks", []):
                if "ps_errorpref_guard" in h.get("command", ""):
                    m = str(entry.get("matcher", ""))
                    return set(t for t in m.split("|") if t), "settings.json"
        return set(), "settings.json (NOT REGISTERED)"
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
    ap.add_argument("--sample", type=int, default=6)
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
    print("baseline for comparison: %s" % BASELINE["window"])
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
    print("  %-11s %4s %8s %8s %10s %7s   %s"
          % ("tool", "reg?", "calls", "payloads", "tax/day", "FIRES", "2026-08-21"))
    for tool in ("PowerShell", "Write", "Edit", "Bash"):
        n, p, fr = calls[tool], per_tool_payloads[tool], fires[tool]
        on = tool in reg
        print("  %-11s %4s %8d %8d %9.1fs %7d   %s"
              % (tool, "yes" if on else " - ", n, p,
                 (n / nday) * MS_PER_CALL / 1000.0, fr,
                 BASELINE["fires"].get(tool, "-")))
    tot_calls = sum(calls[t] for t in ("PowerShell", "Write", "Edit", "Bash"))
    tot_pay = sum(per_tool_payloads.values())
    print("  %-11s %4s %8d %8d %9.1fs %7d"
          % ("TOTAL(all)", " - ", tot_calls, tot_pay,
             (tot_calls / nday) * MS_PER_CALL / 1000.0, len(hits)))

    # The numbers that describe what is actually RUNNING. Reporting only the
    # all-surfaces figures would credit the hook with fires it is not wired to
    # catch -- the shape of over-claim L-012 is about.
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
    print("== what the hits look like (the noise question) ==")
    armed = [h for h in hits if h[5]["redirected"]]
    noexit = [h for h in hits if not h[5]["checks_lastexit"]]
    print("  hits where a governed call ALREADY redirects stderr (half A live) : %d"
          % len(armed))
    print("  hits with no $LASTEXITCODE read anywhere (half B live)            : %d"
          % len(noexit))
    print("  hits with neither                                                 : %d"
          % len([h for h in hits if not h[5]["redirected"] and h[5]["checks_lastexit"]]))
    print()
    by_file = defaultdict(int)
    for ts, tool, label, text, proj, f in hits:
        by_file[os.path.basename(label)] += 1
    print("  distinct target files: %d" % len(by_file))
    for k, v in sorted(by_file.items(), key=lambda kv: -kv[1]):
        print("    %-46s %d" % (k, v))

    print()
    print("== sample (%d of %d), read these before believing the rate ==" % (
        min(a.sample, len(hits)), len(hits)))
    for ts, tool, label, text, proj, f in sorted(hits, key=lambda h: h[0])[:a.sample]:
        print("-" * 74)
        print("%s  %s  %s" % (ts[:19], tool, label))
        print("  governed native calls : %d   first: %s" % (f["n"], f["first"][:70]))
        print("  first line            : %s" % f["first_line"][:120])
        print("  stderr redirected     : %d" % len(f["redirected"]))
        print("  reads $LASTEXITCODE   : %s" % f["checks_lastexit"])

    if a.dump:
        io.open(a.dump, "w", encoding="utf-8").write(json.dumps(
            [{"ts": h[0], "tool": h[1], "label": h[2], "project": h[4],
              "finding": {k: (v if k != "redirected" else [x[2] for x in v])
                          for k, v in h[5].items()},
              "text": h[3]} for h in hits], ensure_ascii=False, indent=1))
        print()
        print("wrote %d hits -> %s" % (len(hits), a.dump))
    return 0


if __name__ == "__main__":
    sys.exit(main())
