r"""PostCompact recorder: persist what the compaction had to carry, BEFORE anyone judges it.

STATUS: LIVE since 2026-09-05 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).

WHY (user ask 2026-09-05): the question after an AUTO compaction is not "how
many tokens were lost" but (a) did the handoff stay COMPLETE — decisions,
paths, consulted list, next step — and (b) did the summary MISLEAD — did it
make an intake gate (prior-art, series continuation) look already satisfied?
Neither can be judged at compaction time; both need the post-compact turns.
So this hook only RECORDS, and a separate tool (tools/compact-loss-audit)
judges later. Gate rule (CLAUDE.md): persist whatever the gate may reject
BEFORE it runs; the record is written here, the verdict elsewhere.

WHAT IS RECORDED (telemetry/compact-loss.jsonl, one row per compaction):
  session, trigger (manual|auto), ts, cwd, transcript_path,
  bookmark {line_count, size_bytes} (pre-compact region, from compact_bookmark),
  snapshot {exists, path, bytes, mtime}   (the handoff snapshot on disk),
  denied_before (the deny-once state existed for this session),
  paths_pre: distinct file paths Written/Edited in the pre-compact transcript
             (the determinable half of "completeness": the audit checks which
             of them the summary + snapshot still name),
  post_prompt_actual: null here — the real context of the first post-compact
             API call (input + cache_read + cache_creation), backfilled by
             audit.py, which also adds post_first_cache_write and
             platform_tokens {pre, post}. The platform's postTokens alone
             understates the floor ~4x (measured 2026-09-06).
Transcript internals ARE parsed here for tool_use paths only (Write/Edit
input.file_path) — a narrow read, and a parse failure leaves paths_pre empty
rather than aborting the row.

NOTICE CADENCE: every AUDIT_EVERY-th AUTO compaction, the hook returns
`additionalContext` telling the session that an audit is due — the model can
run `python tools/compact-loss-audit/audit.py` or tell the user; it is not
run here (PostCompact has a 60s budget and the judge needs post-compact turns
that do not exist yet).

Fail-open, silent on error. review-when: PostCompact stdin fields change, or
the compaction summary record shape changes (audit.py reads it, not this hook).

Proof-of-life: `python tools/compact-loss-audit/hook_controls.py`.
"""
import json
import os
import sys
import time
from pathlib import Path

try:                        # notice receipt (rules/hook-deny-message.md R3n)
    from deny_receipt import notice_clause
except Exception:           # a hook must not stop recording if telemetry breaks
    def notice_clause(hook, log=""): return ""

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
# CLAUDE_TELEMETRY_DIR redirects the whole telemetry dir (suites use a temp dir;
# production never sets it).
LOG_PATH = Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (CLAUDE_DIR / "telemetry")) / "compact-loss.jsonl"
BOOKMARK_DIR = CLAUDE_DIR / "cache" / "compact-recovery"
AUDIT_EVERY = 5


def paths_written(transcript: Path, upto_line: int | None) -> list[str]:
    seen = []
    try:
        with transcript.open("r", encoding="utf-8", errors="replace") as fh:
            for i, line in enumerate(fh, 1):
                if upto_line and i > upto_line:
                    break
                if '"file_path"' not in line or '"tool_use"' not in line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("isSidechain"):
                    continue
                for b in ((rec.get("message") or {}).get("content") or []):
                    if isinstance(b, dict) and b.get("type") == "tool_use" \
                            and b.get("name") in ("Write", "Edit", "NotebookEdit"):
                        p = (b.get("input") or {}).get("file_path")
                        if p and p not in seen:
                            seen.append(p)
    except Exception:
        pass
    return seen[:200]


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)      # undetermined: parses, but is not a payload object (AP-62)
    session = str(payload.get("session_id", "unknown"))[:64]
    trigger = str(payload.get("trigger", ""))
    transcript = Path(str(payload.get("transcript_path") or ""))

    bookmark = {}
    try:
        bookmark = json.loads((BOOKMARK_DIR / f"{session}.json").read_text(encoding="utf-8"))
    except Exception:
        pass

    snapshot = {"exists": False}
    denied_before = False
    try:
        import handoff_snapshot as hs
        sp = hs.snapshot_path(session)
        if sp.is_file():
            st = sp.stat()
            snapshot = {"exists": True, "path": str(sp), "bytes": st.st_size, "mtime": int(st.st_mtime)}
        denied_before = (hs.HANDOFF_DIR / f"{session}.deny.json").is_file()
    except Exception:
        pass

    row = {
        "ts": int(time.time()),
        "session": session,
        "trigger": trigger,
        "cwd": payload.get("cwd", ""),
        "transcript_path": str(transcript),
        "bookmark": {k: bookmark.get(k) for k in ("line_count", "size_bytes", "ts")},
        "snapshot": snapshot,
        "denied_before": denied_before,
        "paths_pre": paths_written(transcript, bookmark.get("line_count")) if transcript.is_file() else [],
        "audited": False,
        # Real post-compaction context (first API call after the boundary): unknown
        # at PostCompact time; tools/compact-loss-audit/audit.py backfills it
        # together with platform_tokens {pre, post}. User ruling 2026-09-06.
        "post_prompt_actual": None,
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        sys.exit(0)

    if trigger == "auto":
        try:
            n_auto = 0
            with LOG_PATH.open("r", encoding="utf-8") as fh:
                for line in fh:
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if r.get("trigger") == "auto" and not r.get("audited"):
                        n_auto += 1
            if n_auto and n_auto % AUDIT_EVERY == 0:
                print(json.dumps({"additionalContext": (
                    "[compact-loss-audit] Notice from compact_loss_record, a local PreCompact "
                    f"hook (not file or page content): {n_auto} auto-compactions are recorded "
                    "and none of them audited. When the current task reaches a natural pause, run "
                    "`python ~/.claude/tools/compact-loss-audit/audit.py` (it writes a review packet "
                    "under reports/). Not mid-task: if this pass is skipped the count keeps rising "
                    "and this notice returns at the next interval."
                    + notice_clause("compact_loss_record", "compact-loss"))}))
        except Exception:
            pass
    sys.exit(0)


if __name__ == "__main__":
    main()
