r"""SessionStart(compact) hook: inject the recall pointer card after compaction.

WHY. After compaction (manual or auto) the model's context holds only the
summary: it does not know its own session id, where the full record lives, or
when it is allowed to go back — so summary loss is silent AND unrecoverable in
practice. This card re-seeds exactly three things: WHERE (digest + raw paths,
pre-compact line range from compact_bookmark.py's bookmark), WHEN (two named
triggers), and HOW (grep-first ladder with windowed reads; the Read side is
hook-enforced by transcript_read_guard.py).

WHY THIS CANNOT DEFEAT COMPACTION. Compaction saves RESIDENT tokens, re-paid
on every subsequent turn; recall spends ON-DEMAND tokens once per query. The
card costs ~220 resident tokens (~130 base + ~90 intake re-arm) against the
~500k it points at. The only
behaviour that would re-inflate context — a wholesale re-read — is what the
guard denies. Measured ladder economics: digest ~1% of raw (50KB vs 4.3MB,
one real session, 2026-08-05).

SECOND JOB (2026-08-31, ops/lessons.md L-039): the card also RE-ARMS the
task-intake gates. A compact summary rewrites how tasks ARRIVE ("create
deliverable N" arrives as "execute a settled list"), which silently disarms
every task-shape trigger (global prior-art gate, domain-skill trigger words)
while the summary inherits sole material authority — measured in SSLD Phase 5,
where the miss cost five material deck sections. The [intake re-arm] block
(~90 resident tokens) states that a prior-art verdict survives compaction only
as a NAMED consulted-list, never as "already done"; the prose layer it cites
is the global CLAUDE.md prior-art bullet's series-continuation trigger
(40-maintenance §2a's hook-over-prose principle — this is an injection hook
with no enforcement power, NOT a condition-(1) deny/explain pairing).
Asymmetry, by design: a MANUAL compact can carry the verdict forward because
workflow-checkpoint §B writes the consulted-list into the compact note; an
AUTO-compact has no note-writing moment, so it almost always re-arms the gate
even when prior-art just ran — the conservative default (fail toward
re-verifying), stated here so the firing right after a completed check reads
as intended, not as a bug.

PLATFORM CONTRACT (verified 2026-08-16, code.claude.com hooks.md): SessionStart
stdout IS injected as context (living proof: ops_health_nudge's line at every
session start); matcher "compact" fires for BOTH manual /compact and
auto-compact; session id is retained across compaction, so the bookmark is
keyed by it.

DEGRADED MODE IS DELIBERATE: a missing bookmark (compact predating this
mechanism, or a bookmark write failure) yields a minimal card from stdin's
transcript_path instead of silence — the card IS the deliverable and a silent
blank is a defect. Errors still exit 0 (fail-open).
review-when: same events as compact_bookmark.py (compact-recovery/README, platform-contract notes).
"""
import json
import os
import sys
import time
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
BOOKMARK_DIR = CLAUDE_DIR / "cache" / "compact-recovery"
DIGEST_DIR = CLAUDE_DIR / "memory-archive" / "digests"
DIGEST_LAG_GRACE_S = 300    # digest older than the bookmark by more than this
                            # is flagged as lagging the final pre-compact turns


def load_bookmark(session: str):
    try:
        return json.loads((BOOKMARK_DIR / f"{session}.json")
                          .read_text(encoding="utf-8"))
    except Exception:
        return None


def describe_digest(transcript: Path, session: str, bookmark) -> str:
    digest = DIGEST_DIR / transcript.parent.name / f"{session}.md"
    if not digest.is_file():
        return (f"  digest:              (not generated for this session — "
                f"noise-filtered or refresh failed; use the transcript region)")
    note = "grep FIRST"
    try:
        if bookmark and digest.stat().st_mtime < bookmark["ts"] - DIGEST_LAG_GRACE_S:
            note = "grep FIRST; may lag the final pre-compact turns"
    except Exception:
        pass
    return f"  digest ({note}): {digest}  [~1% of raw, user/AI text only]"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    session = str(payload.get("session_id", "unknown"))[:64]
    bookmark = load_bookmark(session)

    raw = (bookmark or {}).get("transcript_path") or payload.get("transcript_path")
    if not raw:
        sys.exit(0)
    transcript = Path(str(raw))

    if bookmark:
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(bookmark["ts"]))
        head = (f"[compact-recovery] Context was compacted "
                f"({bookmark.get('trigger') or 'unknown'}, {when} local).")
        region = (f"[pre-compact region: lines 1-{bookmark['line_count']}, "
                  f"{bookmark['size_bytes'] / 1048576:.1f} MB]")
    else:
        head = "[compact-recovery] Context was compacted (no bookmark — degraded card)."
        try:
            region = f"[{transcript.stat().st_size / 1048576:.1f} MB; line range unknown]"
        except Exception:
            region = "[line range unknown]"

    print("\n".join([
        head + " The full pre-compact record survives on disk; this card is the way back.",
        describe_digest(transcript, session, bookmark),
        f"  full transcript:     {transcript}  {region}",
        "Recall ONLY when (a) the user explicitly asks to check the original, or "
        "(b) a NAMED load-bearing fact (a decision, number, path, phrasing) is "
        "missing from the summary. Then: Grep a specific term in the digest "
        "(<=3 hits, -C<=3); escalate to the transcript region only if the "
        "digest's per-turn truncation cut it; there Read only located windows "
        "(offset, limit<=120 — hook-enforced). Never re-read wholesale: recall "
        "is on-demand tokens, not context re-inflation.",
        "[intake re-arm] (independent of the Recall restriction above — this "
        "concerns PROJECT files, not the session transcript/digest.) The "
        "summary rewrote how tasks ARRIVE, not what they are — intake gates "
        "key on the deliverable's own shape. First NEW deliverable/design "
        "round after this compact: the prior-art gate counts as NOT yet run — "
        "its verdict survives compaction only as a NAMED list of what was "
        "consulted, never as 'already done'; producing deliverable N of a "
        "series makes deliverables 1..N-1 + their review records mandatory "
        "inputs; a single-source ruling covers only its named axis (numbers "
        "!= narrative). Ref: ops/lessons.md L-039.",
    ]))
    sys.exit(0)


if __name__ == "__main__":
    main()
