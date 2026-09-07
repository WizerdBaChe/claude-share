r"""PreCompact side-effect hook: bookmark the pre-compact transcript, refresh digests.

WHY. Compaction replaces resident context with a lossy summary; the full record
survives on disk (verified 2026-08-16: boundary records are appended IN-PLACE,
multi-compact sessions stack several in one file), but the post-compact model no
longer knows where that record lives or how far it ran. This hook, paired with
compact_pointer.py (SessionStart, matcher "compact"), closes the gap: it writes
{transcript_path, line_count, size, trigger, ts} BEFORE the summary lands, so
the pointer card can name the pre-compact region precisely ("lines 1..N").

PreCompact is side-effect-only by platform contract — its stdout is NOT
injected into context (only UserPromptSubmit/SessionStart get that; verified
2026-08-16 against code.claude.com hooks.md + Agent SDK PreCompactHookInput).
The context-facing half therefore lives in compact_pointer.py, and the bookmark
file is the bridge between the two events.

DIGEST REFRESH (user ruling 2026-08-16, D3: mid-session compaction is common).
The digest card for THIS session is otherwise generated only at SessionEnd
(tools/memory-pipeline/preserve.py), so recall right after a mid-session
compact would find no digest and fall through to the raw jsonl. After the
bookmark is safely written, this hook runs preserve.py once (incremental).
Ordering is the contract: bookmark FIRST (cheap, must survive), digest refresh
second (best-effort, bounded by PRESERVE_TIMEOUT_S; its failure never voids
the bookmark).

Transcript internals are NOT parsed (standing ruling: the jsonl format is
unstable, treat it as opaque); this hook counts raw
newlines only.

SECOND JOB — AUTO-COMPACT BOUNDED DENY (user ruling D1, 2026-09-05; design:
references/compaction-pipeline-design.md). PreCompact MAY block a compaction
(`permissionDecision: deny`, verified code.claude.com hooks.md 2026-09-05), and
that turn is the one "note-writing moment" the auto path never had. When
trigger == "auto" and no FRESH handoff snapshot exists
(handoff_snapshot.is_fresh), this hook denies with an additionalContext that
asks the model to write cache/handoff/<session>.md; repeated on every attempt
until a fresh snapshot exists, at most MAX_DENIES per session (state:
cache/handoff/<session>.deny.json) — see deny_auto_once for why one-shot failed. Manual compactions are never denied — the user is in control
there and workflow-checkpoint §B already carries the note. The bookmark is
written on BOTH branches (a denied attempt still marks where the record was).
Thrash guard: the changelog documents a circuit breaker after repeated auto-
compact failures; MAX_DENIES bounds our contribution. Platform behaviour is
recorded in deny_auto_once's docstring and design §7 as each control runs;
degradation order: drop the deny, keep the notice + instructions.

Fail-open, silent: any error exits 0 with no output. Living proof: the
bookmark file, cache/compact-recovery/<session_id>.json.
review-when: a Claude Code update changes compact on-disk geometry (boundary
no longer appended in-place) or renames PreCompact stdin fields — the re-check
recipe lives in compact-recovery/README (platform-contract notes).
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
BOOKMARK_DIR = CLAUDE_DIR / "cache" / "compact-recovery"
PRESERVE = CLAUDE_DIR / "tools" / "memory-pipeline" / "preserve.py"
PRESERVE_TIMEOUT_S = 45     # settings.json gives this hook 60s; the digest pass
                            # must never be able to starve the bookmark write.


def count_lines(path: Path) -> int:
    """Raw newline count in binary chunks — no jsonl parsing (standing ruling)."""
    n = 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            n += chunk.count(b"\n")
    return n


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    raw = payload.get("transcript_path")
    if not raw:
        sys.exit(0)
    transcript = Path(str(raw))
    if not transcript.is_file():
        sys.exit(0)
    session = str(payload.get("session_id", "unknown"))[:64]

    try:
        BOOKMARK_DIR.mkdir(parents=True, exist_ok=True)
        (BOOKMARK_DIR / f"{session}.json").write_text(json.dumps({
            "session_id": session,
            "transcript_path": str(transcript),
            "trigger": payload.get("trigger", ""),
            "ts": int(time.time()),
            "line_count": count_lines(transcript),
            "size_bytes": transcript.stat().st_size,
        }, ensure_ascii=False), encoding="utf-8")
    except Exception:
        sys.exit(0)

    try:    # best-effort digest refresh; the bookmark above is already safe
        subprocess.run([sys.executable, str(PRESERVE)],
                       capture_output=True, timeout=PRESERVE_TIMEOUT_S)
    except Exception:
        pass

    if str(payload.get("trigger", "")) == "auto":
        try:
            deny_auto_once(transcript, session)
        except Exception:
            pass
    sys.exit(0)


MAX_DENIES = 3              # per session while no fresh snapshot exists; then allow unconditionally
DENY_ENABLED = False        # DISABLED 2026-09-05 after platform control #3 (see deny_auto_once docstring).
                            # review-when: Claude Code changelog mentions PreCompact deny/block on
                            # auto-compaction, or a version bump past 2.1.257 — re-run
                            # tools/compact-loss-audit/hook_controls.py + the platform control.


def deny_auto_once(transcript: Path, session: str) -> None:
    """Deny auto-compaction while no fresh snapshot exists, at most MAX_DENIES times per session.

    PLATFORM CONTROLS 2026-09-05 (Claude Code 2.1.257, haiku, window 100k via env):
      #2 one session — ONE deny: compaction began 0.5 s after the deny, no
         model turn in between.
      #3 another session — deny on EVERY attempt (count reached 3/3): three
         auto compactions, each starting within a second of its deny; no model
         turn, no snapshot written, and the additionalContext/systemMessage
         never appeared in the transcript.
    Verdict: on this build the auto path does not honour a PreCompact deny (the
    docs say it can block; observed: it does not), so no note-writing moment can
    be manufactured here. DENY_ENABLED=False keeps the code for a re-test; the
    pipeline degrades to: 300k runway notice (live-verified the same day in
    one session) + CLAUDE.md Compact Instructions + 400k window + recorder.
    Also observed: with a 100k window compaction fired at ~62k main-loop context
    (preTokens ~75k incl. the pending tool result) — the platform keeps a
    reserve below the configured window, so 400k should fire around 330–370k.
    """
    if not DENY_ENABLED:
        return
    import handoff_snapshot as hs
    import context_runway_shadow as runway
    total = runway.context_total(transcript)
    state = hs.HANDOFF_DIR / f"{session}.deny.json"
    if hs.is_fresh(transcript, session, total):
        try:
            state.unlink()  # fresh snapshot: reset the budget for the next cycle
        except Exception:
            pass
        return
    try:
        st = json.loads(state.read_text(encoding="utf-8"))
        count = int(st.get("count", 0))
    except Exception:
        count = 0
    if count >= MAX_DENIES:
        return              # budget spent: allow (degradation: summary + Compact Instructions)
    hs.HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"count": count + 1, "last_deny": int(time.time()), "context": total}),
                     encoding="utf-8")
    msg = hs.notice(
        session, total,
        f"Auto-compaction is imminent and was deferred ({count + 1}/{MAX_DENIES}) so state can be saved first")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreCompact",
            "permissionDecision": "deny",
            "permissionDecisionReason": "auto-compact deferred: no fresh handoff snapshot",
            "additionalContext": msg,
        },
        "additionalContext": msg,
        "systemMessage": msg,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
