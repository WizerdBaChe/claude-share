#!/usr/bin/env python3
"""status_line.py -- write and cross-check advisory status lines (rules-usage-dict.md S7).

Born 2026-09-22 from L-119: advisory status lines were not updated when their
work landed, and a session acted on a stale "awaiting ruling". Two jobs:

  set <file> <line>   Replace the one status line in the file's first 10 lines.
                      Keeps the file's line ending and BOM (six hand-written
                      one-off scripts did this in the session that found L-119).
                      Refuses when the file has no status line or has several,
                      and refuses a DEFERRED line with no `trigger:` (T-024).
  stale               List waiting stamps whose awaited ruling id is recorded as
                      ruled in the SAME tool's registers. Advisory only.

What `stale` can determine, and what it cannot (gate-design: rule only on what
is determinable):
  - CAN: "await ... RULING OQ-1" while tools/<dir>/**.md or references/*<dir>*.md
    has a line carrying OQ-1 and a ruled word. Scoped to the owning tool on
    purpose: ids like OQ-1 recur across projects, and an unscoped search reads
    another project's ruling as this one's.
  - CANNOT: an advisory consumed by EXECUTION without a ruling id (the DIT/Prism
    case). Measured 2026-09-22: "cited by another record" does not separate a
    consumed advisory (4 citing files) from a live deferral (5 citing files), so
    no citation signal is emitted. That class is held by the S7 rule (update the
    stamp in the commit that consumes it) and by L-119's detection line.

Used by hooks/ops_health_nudge.py check 13 (import, annotation only).
Exit codes: 0 ok, 1 refused (set), 2 usage error.
"""
from __future__ import annotations

import glob
import os
import re
import sys

HOME = os.path.join(os.path.expanduser("~"), ".claude")
STATUS_RX = re.compile(r"^(?:> status:|\*\*狀態)")
SPENT_RX = re.compile(r"SPENT|已執行|否決|已裁")
AWAITED_ID_RX = re.compile(r"(?:RULING|ruling|裁決|裁定)\s*([A-Z]{1,5}-\d{1,3})\b")
RULED_RX = re.compile(r"已裁決|已裁定|\bRULED\b|\bruled\b")
WAITING_RX = re.compile(r"\bawait|待裁|待決", re.I)
# T-024: same shape hooks/ops_health_nudge.py check 13 reads at SEV_QUEUE.
DEFERRED_RX = re.compile(r"^DEFERRED\b.*?\btrigger\s*[:：][ \t]*\S[^\n]*\S")


def set_line(path: str, line: str) -> int:
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    hits = [i for i, l in enumerate(lines[:10]) if STATUS_RX.match(l)]
    if len(hits) != 1:
        print(f"status_line: refused -- {path} has {len(hits)} status lines in its "
              f"first 10 lines; S7 expects exactly one")
        return 1
    if not STATUS_RX.match(line):
        print("status_line: refused -- the new line must start with '> status:'")
        return 1
    lead = re.sub(r"^[*：:\s]+", "", STATUS_RX.sub("", line))
    if lead.startswith("DEFERRED") and not DEFERRED_RX.search(lead):
        print("status_line: refused -- a DEFERRED stamp must name its trigger: "
              "'> status: DEFERRED — trigger: <event that starts the work>'")
        return 1
    lines[hits[0]] = line.rstrip("\r\n")
    out = nl.join(lines).encode("utf-8")
    with open(path, "wb") as f:
        f.write((b"\xef\xbb\xbf" if bom else b"") + out)
    print(f"status_line: set line {hits[0] + 1} of {path}")
    return 0


def _registers(home: str, rel: str) -> list[str]:
    """Registers of the tool that owns outputs/<dir>/...; [] when unowned."""
    parts = rel.replace(os.sep, "/").split("/")
    if len(parts) < 3 or parts[0] != "outputs":
        return []
    owner = parts[1]
    found = glob.glob(os.path.join(home, "tools", owner, "**", "*.md"), recursive=True)
    found += glob.glob(os.path.join(home, "references", f"*{owner}*.md"))
    return found


def ruled_hint(home: str, rel: str, body: str) -> str | None:
    """-> 'OQ-1 @ tools/x/docs/PSM.md:34' when the awaited id is ruled, else None."""
    ids = AWAITED_ID_RX.findall(body)
    if not ids:
        return None
    for reg in _registers(home, rel):
        try:
            with open(reg, encoding="utf-8", errors="replace") as f:
                for n, l in enumerate(f, 1):
                    if WAITING_RX.search(l) or not RULED_RX.search(l):
                        continue
                    for i in ids:
                        if re.search(rf"\b{re.escape(i)}\b", l):
                            r = os.path.relpath(reg, home).replace(os.sep, "/")
                            return f"{i} @ {r}:{n}"
        except OSError:
            continue
    return None


def waiting_stamps(home: str):
    for p in glob.glob(os.path.join(home, "outputs", "**", "*.md"), recursive=True):
        rel = os.path.relpath(p, home).replace(os.sep, "/")
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                head = [next(f, "") for _ in range(10)]
        except OSError:
            continue
        line = next((l for l in head if STATUS_RX.match(l)), None)
        if line and not SPENT_RX.search(line):
            yield rel, line.strip()


def selftest() -> int:
    import tempfile
    ok = 0
    with tempfile.TemporaryDirectory() as h:
        docs = os.path.join(h, "tools", "probe", "docs")
        os.makedirs(docs)
        with open(os.path.join(docs, "PSM.md"), "w", encoding="utf-8") as f:
            f.write("- **OQ-1 (exit) -- 已裁決 2026-08-17: provisional pass**\n"
                    "- OQ-2 await user ruling\n")
        cases = [
            ("outputs/probe/r.md", "OPEN; await USER RULING OQ-1", True, "ruled id, owning tool"),
            ("outputs/probe/r.md", "OPEN; await USER RULING OQ-2", False, "id only on a waiting line"),
            ("outputs/probe/r.md", "OPEN; await USER RULING OQ-9", False, "id never ruled"),
            ("outputs/other/r.md", "OPEN; await USER RULING OQ-1", False, "same id, another tool"),
            ("outputs/probe/r.md", "OPEN; deferred-pending-second-customer", False, "no id at all"),
        ]
        for rel, body, want, name in cases:
            got = ruled_hint(h, rel, body) is not None
            ok += got == want
            print(f"[{'PASS' if got == want else 'FAIL'}] {name}")
        f1 = os.path.join(h, "crlf.md")
        with open(f1, "wb") as f:
            f.write(b"\xef\xbb\xbf# t\r\n> status: OPEN -- x\r\nbody\r\n")
        set_line(f1, "> status: SPENT -- y")
        raw = open(f1, "rb").read()
        good = raw == b"\xef\xbb\xbf# t\r\n> status: SPENT -- y\r\nbody\r\n"
        ok += good
        print(f"[{'PASS' if good else 'FAIL'}] set keeps CRLF and BOM")
        f2 = os.path.join(h, "none.md")
        with open(f2, "w", encoding="utf-8") as f:
            f.write("# no stamp\n")
        refused = set_line(f2, "> status: SPENT") == 1
        ok += refused
        print(f"[{'PASS' if refused else 'FAIL'}] set refuses a file without a stamp")
        f3 = os.path.join(h, "defer.md")
        with open(f3, "w", encoding="utf-8") as f:
            f.write("> status: OPEN -- x\n")
        bare = set_line(f3, "> status: DEFERRED — later") == 1
        named = set_line(f3, "> status: DEFERRED — trigger: a second project") == 0
        ok += bare and named
        print(f"[{'PASS' if bare and named else 'FAIL'}] set refuses DEFERRED "
              f"without a trigger, accepts it with one")
    total = len(cases) + 3
    print(f"\n{ok}/{total} cases behaved as specified")
    return 0 if ok == total else 1


def main(argv: list[str]) -> int:
    if argv[:1] == ["set"] and len(argv) == 3:
        return set_line(argv[1], argv[2])
    if argv[:1] == ["stale"]:
        n = 0
        for rel, line in waiting_stamps(HOME):
            hint = ruled_hint(HOME, rel, line)
            if hint:
                n += 1
                print(f"{rel}\n    awaits a ruling already recorded: {hint}")
        print(f"{n} waiting stamp(s) with a ruled id")
        return 0
    if argv[:1] == ["--selftest"]:
        return selftest()
    print(__doc__.split("\n\n")[1])
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
