#!/usr/bin/env python
"""judge.py — the user's verdict on one observer finding (FO-R-4).

    python judge.py <finding-id> right|wrong [--note TEXT]
    python judge.py --list            # findings not yet judged, newest first
    python judge.py --stats           # judged n, precision, and whether FO-R-4 is met

Verdicts append to mods/feedback-observer/verdicts.jsonl (one row per call; the latest
row for an id wins). `feedback.py report` reads the same file for the "observer (shadow)"
block. The flip to counted mode is NOT done here: when --stats says "FO-R-4 met", the
user edits ops/rule-registry.md FEEDBACK_OBSERVER to `counted-from:<date>` by hand.

Finding rows live in <home>/projects/*/*.observer.jsonl (fallback telemetry/feedback-observer/).
STATUS: instrument of a SHADOW sensor; writes only its own verdicts file.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = Path(os.environ.get("CLAUDE_CONFIG_DIR") or HERE.parents[1])
VERDICTS = HERE / "verdicts.jsonl"
MIN_JUDGED = 10
MIN_PRECISION = 0.60


def record_files(home: Path = HOME):
    yield from (home / "projects").glob("*/*.observer.jsonl")
    yield from (home / "telemetry" / "feedback-observer").glob("*.jsonl")


def findings(home: Path = HOME) -> list[dict]:
    out = []
    for f in record_files(home):
        try:
            for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("kind") == "finding" and r.get("id"):
                    r["_file"] = str(f)
                    out.append(r)
        except OSError:
            continue
    out.sort(key=lambda r: r.get("ts") or 0, reverse=True)
    return out


def verdicts(path: Path = VERDICTS) -> dict[str, dict]:
    latest: dict[str, dict] = {}
    if not path.is_file():
        return latest
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("id") and r.get("verdict") in ("right", "wrong"):
            latest[r["id"]] = r
    return latest


def stats(home: Path = HOME, path: Path = VERDICTS) -> dict:
    v = verdicts(path)
    judged = len(v)
    right = sum(1 for r in v.values() if r["verdict"] == "right")
    precision = (right / judged) if judged else None
    return {"judged": judged, "right": right, "wrong": judged - right, "precision": precision,
            "fo_r4_met": judged >= MIN_JUDGED and precision is not None and precision >= MIN_PRECISION,
            "unjudged": sum(1 for f in findings(home) if f["id"] not in v)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("finding_id", nargs="?")
    ap.add_argument("verdict", nargs="?", choices=["right", "wrong"])
    ap.add_argument("--note", default="")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--home", type=Path, default=HOME)
    a = ap.parse_args(argv)
    if a.stats:
        s = stats(a.home)
        print(json.dumps(s, ensure_ascii=False))
        print(("FO-R-4 met" if s["fo_r4_met"] else f"FO-R-4 not met (need >= {MIN_JUDGED} judged and precision >= {MIN_PRECISION:.0%})")
              + " — flip FEEDBACK_OBSERVER in ops/rule-registry.md by hand when met")
        return 0
    if a.list or not a.finding_id:
        v = verdicts()
        rows = [f for f in findings(a.home) if f["id"] not in v]
        if not rows:
            print("no unjudged findings")
            return 0
        for f in rows:
            print(f"{f['id']}  {f.get('target','?')}  [{f.get('kind','?')}/{f.get('confidence','?')}]  {f.get('symptom','')}")
            print(f"    evidence: {str(f.get('evidence',''))[:200]}")
        return 0
    if not a.verdict:
        print("verdict required: right|wrong", file=sys.stderr)
        return 2
    known = {f["id"] for f in findings(a.home)}
    if a.finding_id not in known:
        print(f"unknown finding id {a.finding_id} (not in any observer record under {a.home})", file=sys.stderr)
        return 2
    row = {"ts": int(time.time()), "id": a.finding_id, "verdict": a.verdict, "note": a.note}
    with VERDICTS.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    s = stats(a.home)
    print(f"recorded {a.verdict} for {a.finding_id}; judged {s['judged']}, precision "
          f"{'-' if s['precision'] is None else format(s['precision'], '.0%')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
