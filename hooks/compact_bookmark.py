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

Fail-open, silent: any error exits 0 with no output. Living proof: the
bookmark file, cache/compact-recovery/<session_id>.json.
review-when: a Claude Code update changes compact on-disk geometry (boundary
no longer appended in-place) or renames PreCompact stdin fields — the
re-check recipe lives in compact-recovery/README (platform-contract notes).
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
    sys.exit(0)


if __name__ == "__main__":
    main()
