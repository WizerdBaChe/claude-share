#!/usr/bin/env python3
"""telemetry framing — count JSONL rows that no reader can parse.

Status: live 2026-09-08 | severity: WARN when the unparseable count matches the
recorded baseline, FAIL when it EXCEEDS it (the consumer is the human/LLM reading
the sweep; a new corruption event is the thing worth stopping for) | controls:
`controls.py` (two-sided, `ALL PASS n/n`) | wired:
`ops/references/integrity-sweep.md` check 32.

WHY THIS EXISTS, AND WHY IT IS A DETECTOR RATHER THAN A FIX
-----------------------------------------------------------
Measured 2026-09-08: 16 rows across 2 of 22 telemetry files cannot be parsed.
Their shape is the tell -- `telemetry/fieldwork-shadow.jsonl` L58 is the 14-byte
fragment `b.meta.json"]}` and L73 is `]}`. Those are TAILS of records whose heads
are gone, which is what a partially overwritten append looks like.

The mechanism is NOT established, and this file says so rather than implying a
cause it cannot show. A concurrency harness (12 writers x 120 rows, 6 trials)
failed to reproduce any loss at all, and an earlier noisier run lost up to 20% of
rows in EVERY write mode -- including two candidate fixes. A positive control that
does not fire is not a control, so the harness was measuring machine load, not the
write path. Changing a live telemetry writer on that evidence would be iterating
on an unproven model.

So this measures instead. Every rate this environment publishes -- deny rates,
shadow-gate would_block, the model-effort audit -- is computed from these files,
and a row that vanished leaves nothing behind to notice. Counting the rows that
merely got MANGLED is the one visible edge of that, and a rising count is the
evidence a fix would need.

BASELINE: recorded below as a VALUE, not a position. Growth beyond it is a new
event; the check does not care where in the file it happened.

EXTENDING (PH-11 / AP-61): a new telemetry file is covered automatically -- the
glob is the vocabulary. A new FRAMING (a telemetry file that is not JSONL) needs
a class here and a specimen in controls.py; it must not be quietly skipped.

SUITE-SESSION ALLOWLIST (O-2, ruling 2026-09-11): `suite-sessions.json` beside
this file names rows already identified as suite/selftest traffic (2026-09-10
inventory). Two shapes, and the difference is the point: `literals` are
synthetic session_id VALUES (skipped in every file); `session_files` maps a
REAL session id to the files its suite runs polluted -- skipped only there,
because every such session also wrote genuine rows to a dozen other files and
a session-wide skip would hide them (measured 2026-09-11). Skipped rows are
excluded from `rows`/`unparseable` and counted separately as `skipped` -- no
.jsonl is edited, this only changes what a CLEAN reading of production counts.
The list only grows retroactively; the real fix going forward is the writer
honouring CLAUDE_TELEMETRY_DIR (deny_receipt.py and the per-hook LOG_PATH
guards), so new suite runs should not need new entries here at all.
Controls C-10..C-12 in controls.py pin both sides of the skip.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HOME = Path(__file__).resolve().parents[2]
SUITE_SESSIONS_PATH = Path(__file__).resolve().parent / "suite-sessions.json"


def load_suite_sessions(path: Path = SUITE_SESSIONS_PATH) -> tuple[frozenset, dict]:
    """-> (literals, session_files). `literals`: frozenset of synthetic
    session ids skipped everywhere. `session_files`: {session_id: frozenset of
    telemetry file names} skipped only in those files. Missing/unreadable file
    = empty allowlist (fail toward counting MORE rows, never silently fewer)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return frozenset(), {}
    files = data.get("session_files") or {}
    if not isinstance(files, dict):
        files = {}
    return (frozenset(data.get("literals") or ()),
            {str(k): frozenset(v or ()) for k, v in files.items()})

# Measured 2026-09-08 over telemetry/*.jsonl: fieldwork-shadow 2, rule-loads 14.
# review-when: a telemetry file is deliberately truncated or rotated (the count
# can only fall, so re-record it), or a writer is changed (re-measure, and say in
# the commit whether the count moved).
BASELINE = 16
BASELINE_DATE = "2026-09-08"


def scan(root: Path | None = None,
         suite_path: Path = SUITE_SESSIONS_PATH) -> list[tuple[str, int, int, int]]:
    """-> [(name, rows, unparseable, skipped)] for every telemetry JSONL, sorted.
    `skipped` rows (session id on the suite allowlist FOR THAT FILE) are
    excluded from both `rows` and `unparseable` -- they are still real bytes in
    the file, just not counted toward a production reading."""
    root = root or (HOME / "telemetry")
    literals, session_files = load_suite_sessions(suite_path)
    out = []
    for path in sorted(root.glob("*.jsonl")):
        rows = bad = skipped = 0
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            # Unreadable is not "clean": say so instead of counting it as zero.
            out.append((path.name, -1, -1, 0))
            print(f"  [UNREADABLE] {path.name}: {exc}", file=sys.stderr)
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except Exception:
                rows += 1
                bad += 1
                continue
            sid = parsed.get("session") if isinstance(parsed, dict) else None
            if sid is None and isinstance(parsed, dict):
                sid = parsed.get("session_id")
            if sid in literals or path.name in session_files.get(sid, ()):
                skipped += 1
                continue
            rows += 1
        out.append((path.name, rows, bad, skipped))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verbose", action="store_true",
                    help="list every file, not only the damaged ones")
    args = ap.parse_args()

    rows = scan()
    unreadable = [n for n, r, _b, _s in rows if r < 0]
    total_rows = sum(r for _n, r, _b, _s in rows if r >= 0)
    total_bad = sum(b for _n, _r, b, _s in rows if b >= 0)
    total_skipped = sum(s for _n, _r, _b, s in rows)
    damaged = [(n, r, b, s) for n, r, b, s in rows if b > 0]

    print(f"telemetry framing: {len(rows)} file(s), {total_rows} row(s), "
          f"{total_bad} unparseable (baseline {BASELINE} on {BASELINE_DATE})")
    if total_skipped:
        print(f"  skipped {total_skipped} suite-session row(s) "
              f"(tools/telemetry-framing/suite-sessions.json) -- not counted above")
    for name, r, b, s in (rows if args.verbose else damaged):
        print(f"  {b:4} bad / {r:6} rows   {name}"
              + (f"   ({s} suite-session row(s) skipped)" if s else ""))
    if unreadable:
        print(f"  UNDETERMINED: {len(unreadable)} file(s) could not be read: "
              f"{', '.join(unreadable)} — this count is a floor, not a total")

    if total_bad > BASELINE:
        # AP-64: name the repair site, not just the symptom.
        print(f"telemetry framing: FAIL — {total_bad - BASELINE} NEW unparseable "
              f"row(s) since {BASELINE_DATE}. Find them with: python "
              f"tools/telemetry-framing/framing.py --verbose, then read the "
              f"damaged rows' neighbours — a tail fragment means a record was "
              f"overwritten mid-append, which is the event this baseline exists "
              f"to catch. Re-record BASELINE only after that is explained.")
        return 1
    if total_bad:
        print(f"telemetry framing: WARN — {total_bad} unparseable row(s), all "
              f"pre-dating {BASELINE_DATE}. Cause NOT established (see the "
              f"docstring: the concurrency harness's positive control never "
              f"fired). Promotion trigger: the count rises, which is the "
              f"reproduction a writer fix would need.")
        return 0
    print("telemetry framing: PASS — every row parses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
