r"""Shared helpers for the handoff-snapshot pipeline (design: references/compaction-pipeline-design.md).

A handoff snapshot is the MECHANICAL counterpart of a phase checkpoint: written
by the model, without asking, into cache/handoff/<session_id>.md when context
runway is short (context_runway_shadow.py, 300k band) or when an AUTO compaction
is about to run without one (compact_bookmark.py PreCompact deny-once). It is
not a project document — workflow-checkpoint may promote it into a phase-log
section at a spoken phase boundary.

Freshness (user ruling D2, 2026-09-05): a snapshot is fresh while the main-loop
context has grown by <= FRESH_DELTA tokens since the assistant turn that wrote
it. "Context at write" is recovered from the transcript: the assistant record
whose tool_use writes the snapshot path carries the usage of that turn. Same
substring-detector style as context_runway_shadow.checkpoint_written — the
measurement and the rule share one detector.

Imported by hooks in this directory (sys.path[0] is the script dir). Pure
functions, no side effects except reading files; every reader fails toward
"no snapshot" (stale) EXCEPT is_fresh on an unreadable transcript, which fails
toward "fresh" so a probe bug can never deny a compaction.
"""
import json
import os
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
HANDOFF_DIR = CLAUDE_DIR / "cache" / "handoff"
FRESH_DELTA = 60_000        # tokens of main-loop growth after which a snapshot is stale

FLOOR = (
    "project + phase status (what is done / in flight / next)",
    "decisions taken this session, each with its one-line reason",
    "files modified + their purpose (paths)",
    "rules and constraints the continuation will need (design principles, user rulings)",
    "prior-art / consulted list BY NAME (deliverables 1..N-1, review records) — never 'already done'",
    "open questions and the exact next step",
    "reminder: replies in Traditional Chinese; machine-read output in English",
)


def snapshot_path(session_id: str) -> Path:
    return HANDOFF_DIR / f"{str(session_id)[:64]}.md"


def usage_total(rec) -> int:
    usage = ((rec.get("message") or {}).get("usage") or {})
    return (usage.get("input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0))


def context_at_last_write(transcript: Path, session_id: str) -> int | None:
    """Main-loop context of the assistant turn that last wrote the snapshot, or None.

    Scans raw lines for the snapshot filename together with a Write/Edit tool
    name; the usage on that same record is the context at write time. Returns
    None when no such write exists in this transcript (snapshot absent, or
    written in a pre-compact transcript segment that was not chained here —
    both count as 'no fresh snapshot').
    """
    needle = snapshot_path(session_id).name
    found = None
    try:
        with transcript.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if needle not in line:
                    continue
                low = line.replace(" ", "").lower()
                if '"name":"write"' not in low and '"name":"edit"' not in low:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("isSidechain") or rec.get("type") != "assistant":
                    continue
                total = usage_total(rec)
                if total:
                    found = total
    except Exception:
        return None
    return found


def is_fresh(transcript: Path, session_id: str, context_now: int) -> bool:
    """True when a snapshot exists on disk AND was written within FRESH_DELTA tokens."""
    if not snapshot_path(session_id).is_file():
        return False
    at = context_at_last_write(transcript, session_id)
    if at is None:
        # File exists but this transcript holds no write of it: it came from an
        # earlier segment. Trust file age as the fallback signal — stale if the
        # transcript has grown past FRESH_DELTA since the file's mtime cannot be
        # mapped to tokens; fail toward 'stale' so a snapshot gets refreshed.
        return False
    return context_now - at <= FRESH_DELTA


def notice(session_id: str, context_now: int, reason: str) -> str:
    """The one sanctioned wording (runway docstring): short runway, write while cheap."""
    path = snapshot_path(session_id)
    items = "; ".join(f"({i + 1}) {f}" for i, f in enumerate(FLOOR))
    # Re-arm wording (probe Pass 2, 2026-09-05): the first live snapshot was
    # refreshed by APPENDING to §6 while §1-§3 kept saying "deny active / nothing
    # committed"; the pointer card then told the continuation the snapshot
    # outranks the summary. A stale section beside a fresh one is the F8
    # misleading mode — so the refresh must REWRITE, never append.
    run_line = ""
    if (HANDOFF_DIR / f"{str(session_id)[:64]}.run.json").is_file():
        run_line = (" An [unattended-run] manifest exists for this session: carry its scope / deliverables / "
                    "acceptance / rulings / canary verbatim as their own section.")
    return (
        f"[handoff-snapshot] {reason} (main-loop context ~{context_now // 1000}k). "
        f"Write a handoff snapshot NOW to `{path}` (English, <=2k tokens) — REWRITE THE WHOLE FILE "
        "with Write, never append a section to an existing one: every section must state the "
        "CURRENT truth (a stale 'in flight' beside a fresh 'done' misleads the continuation, which "
        "is told the snapshot outranks the summary). This is NOT a phase checkpoint and needs no "
        "consent; it is the state the continuation reads after compaction. Derive it from THIS "
        f"session's shape; the floor every snapshot carries: {items}.{run_line} For floor item (2), "
        "cite the process ledger (`tools/process-ledger/ledger.py show`) and add only decisions it lacks "
        "— then log those too, so the ledger, not the snapshot, is the record. Then continue the task."
    )
