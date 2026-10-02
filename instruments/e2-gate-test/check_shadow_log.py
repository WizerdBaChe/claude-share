#!/usr/bin/env python3
r"""Read the E2 shadow-gate log and report what it would have blocked.

    python check_shadow_log.py            # last 10 DISPATCH records
    python check_shadow_log.py -n 40
    python check_shadow_log.py --commands # also dump harvested shell commands
    python check_shadow_log.py --all      # include the non-dispatch events

`-n` COUNTS DISPATCHES, not log lines (changed 2026-08-12). SubagentStop fires
for much more than Agent-tool dispatches: of the first 57 rows, 54 were events
with no subagent transcript anywhere on disk. Slicing the last N lines would
have handed the T-009 soak gate "40 samples" that contained 2 real ones.

Two things this report exists to answer, in order of importance:

1. **Is `transcript_kind` `subagent`?** If it says `main-or-unknown`, the hook
   was handed the MAIN session's transcript and every `wrote`/`verified` value
   in the log is meaningless (a main session almost always "wrote"). That
   invalidates the whole shadow run -- check it before reading anything else.

2. **What is the false-positive rate?** A `would_block` row whose subagent was
   in fact fine is a false positive. Enforcement stays off until that rate is
   known and small. The denominator is DISPATCHES; the header prints it, and it
   is the number the soak gate is about, not the log's line count.

The `commands` column is the raw material for phase 2: the verification
allowlist in `hooks/delivery_gate_shadow.py` is currently a GUESS, and it must
be rebuilt from commands real subagents actually run.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "telemetry" / "delivery-gate-shadow.jsonl"


def event_kind(row):
    """Which population a row belongs to, tolerating pre-2026-08-12 rows.

    Legacy rows carry no `event_kind`, but the COARSE split is still recoverable
    from `transcript_kind` -- a resolved subagent transcript is a dispatch by
    construction. Only the finer reason a non-dispatch was not one (no agent_id
    vs missing file) is unrecoverable, and that is what "legacy" means here.
    """
    kind = row.get("event_kind")
    if kind:
        return kind
    return "dispatch" if str(row.get("transcript_kind")).startswith("subagent") \
        else "legacy-unclassified"


def load(limit, keep_all=False):
    if not LOG_PATH.exists():
        print(f"no shadow log yet: {LOG_PATH}")
        print("The gate has never fired. Dispatch a subagent, then re-run.")
        return [], Counter()
    rows = []
    for line in LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    census = Counter(event_kind(r) for r in rows)
    if not keep_all:
        rows = [r for r in rows if event_kind(r) == "dispatch"]
    return rows[-limit:], census


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=10, help="number of DISPATCHES to show")
    ap.add_argument("--commands", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="include non-dispatch SubagentStop events")
    args = ap.parse_args()

    rows, census = load(args.n, keep_all=args.all)
    total = sum(census.values())
    n_dispatch = census.get("dispatch", 0)
    print(f"\nlog population: {total} events -> {n_dispatch} dispatches")
    for k, v in census.most_common():
        if k != "dispatch":
            print(f"  excluded  {k:<22}{v}")
    if not rows:
        if total:
            print("\nNo dispatch rows yet. SubagentStop has fired, but never for an")
            print("Agent-tool dispatch -- the soak has collected 0 usable samples.")
        return 1
    if n_dispatch < args.n:
        print(f"\n!! asked for {args.n}, only {n_dispatch} dispatches exist. "
              f"Do NOT read this as an {args.n}-sample result.")

    kinds = Counter(r.get("transcript_kind") for r in rows)
    bad_kind = sum(v for k, v in kinds.items() if not str(k).startswith("subagent"))
    print(f"\ntranscript_kind: {dict(kinds)}")
    if bad_kind:
        print("  !! rows whose source was not the subagent's own transcript --")
        print("     those rows are not classified (wrote/verified are null) by design.")

    print(f"\n{'ts':<21}{'agent_type':<20}{'wrote':<7}{'verified':<10}{'BLOCK?':<8}kind")
    for r in rows:
        print(
            f"{str(r.get('ts'))[:19]:<21}"
            f"{str(r.get('agent_type'))[:19]:<20}"
            f"{str(r.get('wrote')):<7}"
            f"{str(r.get('verified')):<10}"
            f"{('WOULD-BLOCK' if r.get('would_block') else '-'):<13}"
            f"{r.get('transcript_kind')}"
        )

    blocked = [r for r in rows if r.get("would_block")]
    print(f"\nwould_block: {len(blocked)}/{len(rows)}")
    for r in blocked:
        ev = ", ".join(r.get("write_evidence") or [])[:150]
        print(f"  - {str(r.get('agent_type'))[:18]:<20} wrote: {ev}")

    if args.commands:
        seen = Counter()
        for r in rows:
            for c in r.get("commands") or []:
                # Split on && / ; and drop the cd prefix agents open with.
                # Counting raw heads reported "36x cd" and nothing else, which
                # would have made the phase-2 allowlist noise (found 2026-08-12).
                # NOT on `|`: pipes live inside quoted grep patterns far more
                # often than they chain a command, and splitting there emits
                # regex fragments as if they were command names.
                for part in re.split(r"&&|;", c):
                    tok = part.strip().split()
                    if not tok or tok[0] in ("cd", "pushd", "popd"):
                        continue
                    seen[tok[0]] += 1
        print("\nharvested command heads (phase-2 allowlist input):")
        for cmd, n in seen.most_common(30):
            print(f"  {n:>3}x  {cmd}")

    print("\nreminder: shadow mode NEVER blocks. Enforcement is off by design.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
