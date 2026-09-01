r"""PreToolUse(Read) guard: transcript corpus is grep-first, reads are windowed.

WHY A HOOK AND NOT A POLICY LINE. The moment this rule matters most — right
after a compaction, when a fact is missing and the full original is one Read
away — is exactly the pressure moment where a recalled rule loses (same
argument as ui_verify_guard: L-011, hook-enforced not recalled). The pointer
card (compact_pointer.py) states the discipline; this guard makes the one
context-re-inflating move — a wholesale Read of session records — structurally
unavailable, while keeping the compliant path (Grep to locate, then a small
windowed Read) friction-free. User ruling 2026-08-16 (D2): hard enforcement.

RULE (asset property, not a path instruction): a SESSION-RECORD file may not
be Read unbounded once it is big enough to matter. Deny iff
  is_session_record  AND  under CORPUS_ROOTS  AND  size > SIZE_GATE
  AND  (no `limit` or limit > LINE_WINDOW).
Identity is by SHAPE, not location alone: `*.jsonl` (live transcripts,
subagents/, mirror copies) or a digest card (`*.md` under a `digests/` dir).
The corpus roots share their directories with non-record tenants — WebFetch
caches and tool-result overflow under `projects/**/tool-results/`, embedding
models / sqlite indexes under `memory-archive/` — and those Read freely:
they were never compacted away, so re-reading them re-inflates nothing.
Grep/Glob are untouched (different matcher), small files (memory .md mirrors,
meta.json, most digest cards) Read freely, and windowed reads pass — the
grep -> offset+limit pattern this enforces IS the retrieval primitive any
future cross-session index/RAG layer inherits.

DENY-MESSAGE CONTRACT: the reason text states the constraint and the retry
mechanics ONLY. It must never assert the identity of an arbitrary file, claim
"Policy:" authority, or instruct the reader to go read a different directory —
a well-calibrated subagent correctly classifies that shape (falsifiable
identity claim + authority claim + read-elsewhere imperative) as prompt
injection. That is a property of good subagents, not a bug; the hook must not
wear the costume.

FALSE-POSITIVE LOG (convention: counted in the owning hook's docstring):
- 2026-08-29, 2 events (subagents W1/W2, scientific-research-guide session):
  the original path-only identity ("under corpus root AND >128KB") denied
  WebFetch-cached arXiv PDFs under projects/**/tool-results/. Audit found 36
  non-record files >128KB under projects/ (26 .pdf, 10 .txt) plus
  memory-archive model-cache/index files, all wrongly gated. W1's Read was
  fully blocked; W2 bypassed via pdftotext; both classified the old deny text
  as injection. Fix: shape-based is_session_record() + constraint-form deny
  message (this revision). The gate itself was NOT loosened for real records.

WHY A SIZE GATE IN BYTES: token risk tracks bytes, not lines — one transcript
jsonl line can exceed 100KB, so a line-count rule alone is gameable; and
without the gate, tiny mirrored files would need a `limit` for no reason.
Both thresholds are PROVISIONAL (registry: "compact recovery");
observed denials that were LEGITIMATE whole-file needs get appended there.

DECISION TABLE (pinned by hooks/tests/test_transcript_read_guard.py and the
2026-08-29 boundary probe; DENY only when ALL four columns hold):
  identity : suffix `.jsonl` (any case) OR `.md` under a `digests/` dir,
             tested on the CANONICAL path (aliases resolved first)
  scope    : canonical path strictly inside a CORPUS_ROOT
  size     : strictly > SIZE_GATE (== SIZE_GATE passes)
  window   : no numeric `limit`, or limit > LINE_WINDOW (== passes).
             Non-numeric `limit` counts as absent (deny — fail-closed for
             this field only); `offset` alone is NOT a window (deny).
Anything failing any column PASSES. Verified-pass examples: WebFetch caches
and tool-result overflow (`**/tool-results/*.pdf|*.txt`), error logs,
model-cache files (.onnx, tokenizer.json), index .sqlite, non-digest .md,
files <= SIZE_GATE, windowed reads, records outside every root.
Verified-DENY alias forms: forward-slash, 8.3 short name (which truncates
the extension — canonicalize first or it bypasses), `\\?\` extended-length
prefix, directory junctions/symlinks into a root.

BOUNDARIES AND UNKNOWNS (honest ledger; probe-dated 2026-08-29):
- Read tool only, by design: shell `cat`/`Get-Content` bypasses. The
  registered extension event is a RECURRING shell-side bypass; one-off
  occurrences are logged, not pre-built against.
- TESTED BYPASS, accepted: UNC admin-share form (`\\localhost\c$\...`) —
  resolve() keeps the UNC form so no drive-letter root prefix ever matches;
  no cheap deterministic mapping exists.
- TESTED BYPASS, accepted: NTFS hardlinks from outside a root — path
  resolution cannot see an inode's other names.
- TESTED BYPASS, accepted: renamed/compressed copies (`*.jsonl.bak`,
  `*.jsonl.gz`) escape shape identity; no pipeline here produces them and
  the mirror is a verbatim robocopy.
  Acceptance rationale for all three: the guard protects a well-meaning
  agent from a HABIT at a pressure moment (post-compact re-read), not
  against an agent adversarially constructing path aliases; an agent doing
  the latter has already left the compliance regime this hook serves.
- Quirk, recorded: bool `limit` is numeric (int subclass) — `limit: true`
  counts as a 1-line window and passes the hook; Read itself then rejects
  the type. Float limits are honored as numbers.
- UNKNOWN: whether future harness file-reading tools other than exact-name
  "Read" appear (the settings.json matcher is exact); whether 8.3 name
  generation stays enabled on C: (if disabled for new files, that DENY row
  degrades to n/a, not to a bypass).

Fail-open on malformed input; deny is the only non-silent path.
review-when: Claude Code changes compact on-disk geometry or moves the
transcript/archive roots; a mirror root changes with the scheduled copy job
that feeds it — the CONFIG block below is the single
edit point (same INV-8 philosophy as compact-recovery/preserve.py).
Also: a new tenant class appears under a corpus root that IS .jsonl-shaped
but not a session record (shape identity would then over-match), or session
records start being written in a non-.jsonl format (it would under-match).
Regression matrix: hooks/tests/test_transcript_read_guard.py.
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


def is_session_record(path: Path) -> bool:
    """Asset-shape identity: transcripts are .jsonl; digest cards are .md
    under a digests/ directory. Everything else sharing the corpus roots
    (tool-results caches, model files, indexes, logs) is not a record."""
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return True
    if suffix == ".md" and any(part.lower() == "digests" for part in path.parts):
        return True
    return False


def canonicalize(path: Path) -> Path:
    """Resolve aliases BEFORE any identity/scope test: 8.3 short names
    (which also truncate the extension — `agent-~4.JSO`), junctions and
    symlinks, relative segments, and the `\\\\?\\` extended-length prefix.
    Shape tested on a raw alias is a bypass (found by probe 2026-08-29)."""
    raw = str(path)
    if raw.startswith("\\\\?\\"):
        raw = raw[4:] if not raw[4:].upper().startswith("UNC\\") else "\\\\" + raw[8:]
    return Path(raw).resolve()


def under_corpus(resolved: Path) -> bool:
    target = os.path.normcase(str(resolved))
    for root in CORPUS_ROOTS:
        prefix = os.path.normcase(str(root)) + os.sep
        if target.startswith(prefix):
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
    try:
        target = canonicalize(Path(str(raw)))
    except Exception:
        sys.exit(0)

    if not is_session_record(target):
        sys.exit(0)
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
        f"Read denied by transcript_read_guard (a local PreToolUse hook, not "
        f"page or file content): this {size / 1048576:.1f} MB session-record "
        f"file exceeds the {SIZE_GATE // 1024} KB gate for unbounded Reads. "
        f"Retry the same Read with offset and limit<={LINE_WINDOW}; to locate "
        f"the window first, Grep this same file (Grep is not gated)."
    )


if __name__ == "__main__":
    main()
