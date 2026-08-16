r"""PreToolUse(Read) guard: transcript corpus is grep-first, reads are windowed.

WHY A HOOK AND NOT A POLICY LINE. The moment this rule matters most — right
after a compaction, when a fact is missing and the full original is one Read
away — is exactly the pressure moment where a recalled rule loses (same
argument as ui_verify_guard: L-011, hook-enforced not recalled). The pointer
card (compact_pointer.py) states the discipline; this guard makes the one
context-re-inflating move — a wholesale Read of session records — structurally
unavailable, while keeping the compliant path (Grep to locate, then a small
windowed Read) friction-free. User ruling 2026-08-16 (D2): hard enforcement.

RULE (asset property, not a path instruction): a file under a transcript-corpus
root may not be Read unbounded once it is big enough to matter. Deny iff
  under CORPUS_ROOTS  AND  size > SIZE_GATE  AND  (no `limit` or limit > LINE_WINDOW).
Grep/Glob are untouched (different matcher), small files (memory .md mirrors,
meta.json, most digest cards) Read freely, and windowed reads pass — the
grep -> offset+limit pattern this enforces IS the retrieval primitive any
future cross-session index/RAG layer inherits.

WHY A SIZE GATE IN BYTES: token risk tracks bytes, not lines — one transcript
jsonl line can exceed 100KB, so a line-count rule alone is gameable; and
without the gate, tiny mirrored files would need a `limit` for no reason.
Both thresholds are PROVISIONAL (record their fate in your own rule registry);
observed denials that were LEGITIMATE whole-file needs are the settling data.

KNOWN BOUNDARY: covers the Read tool only. A recurring shell-side bypass
(`cat`/`Get-Content` on corpus files) is the registered event that extends
coverage, not a reason to pre-build it.

Fail-open on malformed input; deny is the only non-silent path.
review-when: Claude Code changes compact on-disk geometry or moves the
transcript/archive roots; a mirror root moves together with whatever
scheduled copy job feeds it — the CONFIG block below is the single
edit point (same INV-8 philosophy as compact-recovery/preserve.py).
"""
import json
import os
import sys
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))

# --- CONFIG: single edit point ---------------------------------------------
CORPUS_ROOTS = (
    CLAUDE_DIR / "projects",              # live transcripts (+ subagents/)
    CLAUDE_DIR / "memory-archive",        # preserve.py raw copies + digests
    # add any transcript mirror/backup roots of your own here (absolute Paths)
)
SIZE_GATE = 128 * 1024      # PROVISIONAL — below this, any Read passes
LINE_WINDOW = 120           # PROVISIONAL — max `limit` for a windowed Read
# ---------------------------------------------------------------------------


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def under_corpus(path: Path) -> bool:
    try:
        resolved = os.path.normcase(str(path.resolve()))
    except Exception:
        return False
    for root in CORPUS_ROOTS:
        prefix = os.path.normcase(str(root)) + os.sep
        if resolved.startswith(prefix):
            return True
    return False


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if payload.get("tool_name") != "Read":
        sys.exit(0)

    tool_input = payload.get("tool_input") or {}
    raw = tool_input.get("file_path")
    if not raw:
        sys.exit(0)
    target = Path(str(raw))

    if not under_corpus(target):
        sys.exit(0)
    try:
        size = target.stat().st_size
    except Exception:
        sys.exit(0)          # missing file: let Read produce its own error
    if size <= SIZE_GATE:
        sys.exit(0)

    limit = tool_input.get("limit")
    if isinstance(limit, (int, float)) and limit <= LINE_WINDOW:
        sys.exit(0)

    deny(
        f"Transcript-corpus file ({size / 1048576:.1f} MB of session record): "
        f"an unbounded Read re-ingests what compaction/digesting saved. "
        f"Locate first — Grep a specific term (<=3 hits, small -C) in the "
        f"digest card under {CLAUDE_DIR / 'memory-archive' / 'digests'} or in "
        f"this file — then Read just the located window with offset and "
        f"limit<={LINE_WINDOW}. Policy: the [compact-recovery] card at session "
        f"start; compact-recovery/README."
    )


if __name__ == "__main__":
    main()
