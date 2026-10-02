r"""Sweep the transcript corpus for shell-tool errors and recompute the rates.

This is the instrument behind the source environment's shell-command error audit (2026-08-18)
and `ops/lessons.md` L-024. Re-run it when a registered review-when fires (see
README.md), or whenever a claim in that report needs re-checking.

WHY IT LIVES HERE AND NOT IN A SCRATCHPAD
`cleanupPeriodDays` (default 30) deletes the transcripts this reads. The daily
mirror keeps them, so pass `--root <mirror-dir>` once the live
copies have aged out. A measurement whose instrument was thrown away is a
number nobody can ever re-derive.

    python sweep.py                                  # last 10 days, live transcripts
    python sweep.py --since 2026-08-08               # explicit window
    python sweep.py --root <mirror-dir> --since 2026-08-08
    python sweep.py --json errors.json               # dump the deduplicated records

DEDUPLICATION IS NOT OPTIONAL. Sidechain/compaction rewrites repeat a call
verbatim (observed up to 6x); the 2026-08-18 run was 472 raw rows for 370 real
errors, a 27% inflation concentrated in the longest sessions.
"""
import argparse
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta

SHELL_TOOLS = ("Bash", "PowerShell")
DEDICATED = ("Write", "Edit", "Read", "Grep", "Glob")

# Recorded 2026-08-19 baseline. A later run prints its own numbers beside these
# so drift is visible without digging up the report.
BASELINE = {
    "window": "2026-08-08..2026-08-18",
    "calls": {"Bash": 4848, "PowerShell": 1696},
    "errors": {"Bash": 154, "PowerShell": 216},
    "tool_rates": {"Write": 0.1, "Grep": 0.9, "Read": 1.1, "Edit": 2.4,
                   "Bash": 3.2, "PowerShell": 12.9},
    "largest_ok_bash_bytes": 7688,
    "size_ceiling_bytes": 7700,
}

SHAPE = [
    ("A write-file", re.compile(r"<<\s*['\"]?\w+|(^|[;&|]\s*)(cat|tee)\s[^|;]*>>?"
                                r"|>>?\s*['\"]?[^\s'\"|;&]+\.(md|py|ts|tsx|js|cs|json|txt|html|ps1|sh|toml|ya?ml)\b")),
    ("B read-file", re.compile(r"(^|[;&|]\s*)(cat|head|tail|sed -n|Get-Content|type)\s")),
    ("C search", re.compile(r"(^|[;&|]\s*)(grep|rg|Select-String|findstr|find)\s")),
    ("D in-place edit", re.compile(r"(^|[;&|]\s*)sed -i\b|-Replace\b")),
    ("E git", re.compile(r"(^|[;&|]\s*)git\s")),
    ("F run-program", re.compile(r"(^|[;&|]\s*)[.\\/\w:]*\b(python3?|node|npm|npx|dotnet|pytest|cargo|go)\b")),
]
ALT = {"A write-file": "Write", "B read-file": "Read", "C search": "Grep/Glob",
       "D in-place edit": "Edit", "E git": "(none)", "F run-program": "(none)",
       "G other": "(none)"}

BACKSLASH_RUN = re.compile(r"\\{2,}")


def shape_of(cmd):
    for name, pat in SHAPE:
        if pat.search(cmd):
            return name
    return "G other"


def collect(root, since):
    """Return {(ts, tool, cmd_prefix): (tool, cmd, is_error, out)} — deduplicated."""
    files = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            if f.endswith(".jsonl"):
                files.append(os.path.join(dp, f))
    seen = {}
    for path in files:
        uses = {}
        try:
            lines = io.open(path, encoding="utf-8", errors="replace").readlines()
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
            t, ts = d.get("type"), d.get("timestamp", "")
            if t == "assistant":
                c = d.get("message", {}).get("content")
                if not isinstance(c, list):
                    continue
                for b in c:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        uses[b.get("id")] = {"tool": b.get("name"), "ts": ts,
                                             "input": b.get("input") or {}}
            elif t == "user":
                c = d.get("message", {}).get("content")
                if not isinstance(c, list):
                    continue
                for b in c:
                    if not (isinstance(b, dict) and b.get("type") == "tool_result"):
                        continue
                    u = uses.get(b.get("tool_use_id"))
                    if not u:
                        continue
                    if not (u["ts"] >= since or ts >= since):
                        continue
                    cmd = u["input"].get("command", "") or u["input"].get("file_path", "") or ""
                    key = (u["ts"], u["tool"], cmd[:400])
                    if key in seen:
                        continue
                    out = b.get("content")
                    if isinstance(out, list):
                        out = " ".join(x.get("text", "") for x in out if isinstance(x, dict))
                    seen[key] = (u["tool"], cmd, bool(b.get("is_error")),
                                 out if isinstance(out, str) else "", u["ts"], path)
    return seen


def pct(n, d):
    return (100.0 * n / d) if d else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.join(os.path.expanduser("~"), ".claude", "projects"))
    ap.add_argument("--since", default=str(date.today() - timedelta(days=10)))
    ap.add_argument("--json", dest="dump")
    a = ap.parse_args()

    if not os.path.isdir(a.root):
        print("root not found: %s" % a.root)
        return 2
    seen = collect(a.root, a.since)
    rows = list(seen.values())
    if not rows:
        print("no resolved tool calls in window %s under %s" % (a.since, a.root))
        return 1

    print("root   : %s" % a.root)
    print("window : %s ..  (%d deduplicated tool results)" % (a.since, len(rows)))
    print("baseline for comparison: %s" % BASELINE["window"])
    print()

    print("== per tool ==")
    print("  %-12s %7s %7s %8s   %s" % ("tool", "calls", "errors", "rate", "2026-08-19"))
    agg = defaultdict(lambda: [0, 0])
    for tool, cmd, err, out, ts, path in rows:
        agg[tool][0] += 1
        if err:
            agg[tool][1] += 1
    for tool in sorted(agg, key=lambda t: -agg[t][0]):
        n, e = agg[tool]
        base = BASELINE["tool_rates"].get(tool)
        print("  %-12s %7d %7d %7.1f%%   %s" % (tool, n, e, pct(e, n),
              ("%.1f%%" % base) if base is not None else "-"))

    print()
    print("== shell calls by task shape (is a dedicated tool available?) ==")
    print("  %-12s %-16s %6s %6s %8s  %s" % ("tool", "shape", "calls", "err", "rate", "alternative"))
    seg = defaultdict(lambda: [0, 0])
    for tool, cmd, err, out, ts, path in rows:
        if tool not in SHELL_TOOLS:
            continue
        s = shape_of(cmd)
        seg[(tool, s)][0] += 1
        if err:
            seg[(tool, s)][1] += 1
    for (tool, s), (n, e) in sorted(seg.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        print("  %-12s %-16s %6d %6d %7.1f%%  %s" % (tool, s, n, e, pct(e, n), ALT[s]))

    print()
    print("== Bash command size vs failure (the ceiling: %d B) ==" % BASELINE["size_ceiling_bytes"])
    bash = [r for r in rows if r[0] == "Bash"]
    buckets = [(0, 2000), (2000, 4000), (4000, 6000), (6000, 7000),
               (7000, 7700), (7700, 8192), (8192, 10 ** 9)]
    strict_eof = re.compile(r"/usr/bin/bash: (?:-c|eval): line \d+: unexpected EOF while looking for matching")
    for lo, hi in buckets:
        sub = [r for r in bash if lo <= len(r[1].encode("utf-8", "replace")) < hi]
        if not sub:
            continue
        err = [r for r in sub if r[2]]
        eof = [r for r in sub if r[2] and strict_eof.search(r[3])]
        print("  %6d-%-9d n=%-5d err=%-4d %6.1f%%   strict-EOF=%d"
              % (lo, hi, len(sub), len(err), pct(len(err), len(sub)), len(eof)))
    ok = [r for r in bash if not r[2]]
    if ok:
        print("  largest SUCCESSFUL Bash command: %d B   (2026-08-19 baseline: %d B)"
              % (max(len(r[1].encode("utf-8", "replace")) for r in ok),
                 BASELINE["largest_ok_bash_bytes"]))

    print()
    print("== backslash exposure (the transport collapse, L-024) ==")
    for tool in SHELL_TOOLS:
        sub = [r for r in rows if r[0] == tool]
        w = [r for r in sub if BACKSLASH_RUN.search(r[1])]
        o = [r for r in sub if not BACKSLASH_RUN.search(r[1])]
        print("  %-12s carries a backslash run: n=%-5d err=%-4d %6.1f%%  |  without: n=%-5d err=%-4d %6.1f%%"
              % (tool, len(w), sum(1 for r in w if r[2]), pct(sum(1 for r in w if r[2]), len(w)),
                 len(o), sum(1 for r in o if r[2]), pct(sum(1 for r in o if r[2]), len(o))))
    print("  NOTE: a high rate here is exposure, not damage. The collapse is SILENT —")
    print("        the calls that did NOT error are where corrupted bytes reached disk.")

    if a.dump:
        recs = [{"ts": ts, "tool": tool, "cmd": cmd, "is_error": err,
                 "out": out, "file": os.path.basename(path)}
                for tool, cmd, err, out, ts, path in rows if err]
        io.open(a.dump, "w", encoding="utf-8").write(
            json.dumps(recs, ensure_ascii=False, indent=1))
        print()
        print("wrote %d error records -> %s" % (len(recs), a.dump))
    return 0


if __name__ == "__main__":
    sys.exit(main())
