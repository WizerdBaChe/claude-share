r"""Notice→snapshot compliance, by main-loop model (extension 1, 2026-09-05).

Question it answers: when the runway hook INJECTS the 300k notice (tier B —
mechanical trigger, model executes), does the model actually write the handoff
snapshot? Tier B robustness against a cheaper main-loop model is an assumption
until this prints a rate per model with its denominator.

Method: every telemetry row with noticed=true → open the transcript, find the
first main-loop assistant record after the row's ts, count assistant turns
until a Write/Edit whose path is cache/handoff/<session>.md appears (or the
transcript ends / a compaction intervenes). Group by the model id on the
assistant records. Prints rate, denominator, and per-row evidence lines.

Severity: WARN advisory. Calibration: the idle baseline is "rows with
noticed=false" (must produce no snapshot write — they were silent) — printed
as the negative control; the positive control is any session known to have
complied (one recorded session, 2026-09-05).
"""
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
LOG = CLAUDE_DIR / "telemetry" / "context-runway-shadow.jsonl"
WINDOW_TURNS = 3


def ts_of(rec) -> float:
    t = rec.get("timestamp")
    if not t:
        return 0.0
    try:
        return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def transcript_for(session: str):
    for p in (CLAUDE_DIR / "projects").glob(f"*/{session}.jsonl"):
        return p
    return None


def check(row: dict):
    t = transcript_for(row["session"])
    if not t:
        return {"status": "no-transcript"}
    needle = f"{row['session'][:64]}.md"
    turns, model, wrote_at, compacted = 0, None, None, False
    with t.open("r", encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            if '"assistant"' not in line and "compactMetadata" not in line and "isCompactSummary" not in line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if ts_of(r) < row["ts"]:
                continue
            if r.get("isCompactSummary") or (r.get("compactMetadata") or {}).get("trigger"):
                compacted = True
                break
            if r.get("type") != "assistant" or r.get("isSidechain"):
                continue
            model = model or (r.get("message") or {}).get("model")
            content = (r.get("message") or {}).get("content") or []
            if any(isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ("Write", "Edit")
                   and needle in str((b.get("input") or {}).get("file_path", "")) for b in content):
                wrote_at = (turns, i)
                break
            if any(isinstance(b, dict) and b.get("type") == "text" for b in content):
                turns += 1
            if turns > WINDOW_TURNS:
                break
    return {"status": "complied" if wrote_at else ("compacted-first" if compacted else "no-write"),
            "model": model or "?", "turns": wrote_at[0] if wrote_at else turns, "line": wrote_at[1] if wrote_at else None}


def main() -> None:
    if not LOG.is_file():
        print("no runway telemetry"); return
    rows = [json.loads(l) for l in LOG.read_text(encoding="utf-8").splitlines() if l.strip()]
    noticed = [r for r in rows if r.get("noticed")]
    silent = [r for r in rows if not r.get("noticed")]
    by_model = defaultdict(lambda: {"n": 0, "complied": 0, "rows": []})
    for r in noticed:
        v = check(r)
        g = by_model[v.get("model", "?")]
        g["n"] += 1
        g["complied"] += v["status"] == "complied"
        g["rows"].append((r["session"][:8], r["band"], v["status"], v["turns"], v["line"]))
    print(f"notice→snapshot compliance (window {WINDOW_TURNS} assistant turns); noticed rows: {len(noticed)}, silent rows (negative control): {len(silent)}")
    for m, g in sorted(by_model.items()):
        print(f"  {m}: {g['complied']}/{g['n']}")
        for s, b, st, tu, ln in g["rows"]:
            print(f"    {s} band={b} {st} turns={tu} line={ln}")
    if not noticed:
        print("  (no noticed rows yet — the rate is undefined, not 100%)")
    # negative control: silent rows must show no snapshot write attributable to a notice
    leak = 0
    for r in silent[-20:]:
        v = check(r)
        leak += v.get("status") == "complied"
    print(f"negative control (last {min(20, len(silent))} silent rows): {leak} snapshot write(s) within the window — expected 0 unless the model wrote one unprompted")


if __name__ == "__main__":
    main()
