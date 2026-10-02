#!/usr/bin/env python3
r"""InstructionsLoaded logger -- rule-load observability (E1 instrument).

STATUS: LIVE since 2026-08-11 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).

WHY THIS EXISTS
---------------
`~/.claude/CLAUDE.md` is loaded in full into every session (official docs:
"CLAUDE.md files are loaded into the context window at the start of every
session"). Trimming it is the only lever that lowers the fixed per-session
cost -- but @-imports and `.claude/rules/*.md` WITHOUT `paths:` frontmatter
are also loaded at launch, so splitting a file that way saves nothing.
Only two things actually reduce startup context: deleting/merging text, and
moving path-triggered rules into `~/.claude/rules/*.md` WITH `paths:`
frontmatter so they load on demand.

Deciding what may safely move needs evidence about which instruction files
load, when, and why. `InstructionsLoaded` is the only event that reports it.
This hook does nothing but record that. It never blocks, never injects
context, and never writes to stdout.

CONTRACT
--------
- stdin : hook payload JSON (schema is version-dependent -- recorded verbatim,
          truncated, precisely because we are discovering it)
- stdout: nothing (an empty stdout is "no decision" for every hook event)
- exit  : always 0 -- fail-open by construction. A logger that can break a
          session is worse than no logger.
- output: %USERPROFILE%\.claude\telemetry\rule-loads.jsonl (gitignored),
          size-capped with one rotation so it cannot grow without bound.
- concurrency: one exclusive append per row. The desktop app starts 2-4 CLI
          processes within a second, each firing this hook. Windows emulates
          O_APPEND as seek-to-end + write, which is not atomic across
          processes: measured 2026-09-14 with the old `open(path, "a")`, 8
          processes x 60 events kept 410/480 small rows (3 torn) and 362/480
          large ones -- rows are OVERWRITTEN, not merely interleaved, and the
          live log had 17/6,069 torn fragments. Each row is now one
          `os.write` under a byte-range lock placed past EOF (so readers of the
          log are never blocked). If the lock is not obtained within
          LOCK_WAIT_S the row is written anyway: fail-open beats a lost row.

Proof-of-life: `python hooks/tests/test_instructions_loaded_logger.py`
--------------------------------------------------------------------
Executed by integrity-sweep check 31. Counting rows in the live log is NOT a
proof of life for the writer: a logger that stopped writing and a week with no
sessions leave the same file, so that number can only be read once the writer
is known good. The suite pins the writer (redaction, truncation, rotation,
fail-open) and REPORTS the live row count without scoring it -- an empty or
missing file after a fresh session means the event does not fire in this Claude
Code version, which is a real finding about Claude Code, not a hook bug: record
it and fall back to reading `/context` by hand.

Related: ops/lessons.md L-011 (enforcement layer chosen by trigger shape);
this file is OBSERVATION only, it enforces nothing.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import msvcrt
except ImportError:  # non-Windows
    msvcrt = None
    import fcntl

# CLAUDE_TELEMETRY_DIR redirects the whole telemetry dir (suites use a temp dir;
# production never sets it).
LOG_PATH = Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (Path.home() / ".claude" / "telemetry")) / "rule-loads.jsonl"
MAX_BYTES = 5 * 1024 * 1024  # rotate once past this; bounded disk use
MAX_PAYLOAD_CHARS = 4000  # truncate pathological payloads, keep the shape
# The lock covers one byte far past any real EOF (the log rotates at MAX_BYTES), so it serialises
# writers without ever overlapping data a reader wants; below 2**31 for the CRT's 32-bit lock offset.
LOCK_OFFSET = 0x7FFFFFF0
LOCK_WAIT_S = 2.0  # well inside the hook's 5 s timeout in settings.json


def _lock(fd):
    """Try to take the writer lock until LOCK_WAIT_S; -> True if held."""
    deadline = time.monotonic() + LOCK_WAIT_S
    while True:
        try:
            if msvcrt:
                os.lseek(fd, LOCK_OFFSET, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB, 1, LOCK_OFFSET, os.SEEK_SET)
            return True
        except OSError:
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.005)


def _unlock(fd):
    try:
        if msvcrt:
            os.lseek(fd, LOCK_OFFSET, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            fcntl.lockf(fd, fcntl.LOCK_UN, 1, LOCK_OFFSET, os.SEEK_SET)
    except OSError:
        pass  # closing the descriptor releases it anyway


def append_row(path, data):
    """Append `data` (bytes, one whole row) as a single write under the writer lock."""
    fd = os.open(str(path), os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o644)
    try:
        locked = _lock(fd)
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(fd, view):]
        finally:
            if locked:
                _unlock(fd)
    finally:
        os.close(fd)


def rotate_if_needed(path):
    """Keep at most two generations. Best-effort: never raises."""
    try:
        if path.exists() and path.stat().st_size > MAX_BYTES:
            backup = path.with_suffix(".jsonl.1")
            if backup.exists():
                backup.unlink()
            path.rename(backup)
    except OSError:
        pass


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        return 0
    if not raw:
        return 0

    try:
        payload = json.loads(raw)
    except Exception:
        payload = {"_unparsed": raw[:MAX_PAYLOAD_CHARS]}

    if not isinstance(payload, dict):
        payload = {"_nonobject": str(payload)[:MAX_PAYLOAD_CHARS]}

    # Drop the two fields that are large and already known, keep everything
    # else verbatim -- the point of this logger is schema discovery.
    body = {k: v for k, v in payload.items() if k not in ("transcript_path",)}
    # Loader classification (added 2026-09-10, O-1 of the rules-debt audit):
    # 2,726 of 4,204 CLAUDE.md session_start loads in one month matched no
    # archived transcript. The full transcript_path stays redacted (W-3);
    # what classification needs is only its parent dir name, whether it
    # exists at load time, the CLI entrypoint and the parent pid. Keys never
    # start with "_" (that prefix is reserved for undetermined markers, U-2),
    # and an undetermined payload stays the bare marker (U-1b): nothing is
    # merged beside it that could read as a real event.
    if not any(k.startswith("_") for k in body):
        tp = payload.get("transcript_path")
        try:
            body["transcript_dir"] = Path(str(tp)).parent.name if tp else None
            body["transcript_exists"] = os.path.exists(str(tp)) if tp else None
        except Exception:
            body["transcript_dir"] = body["transcript_exists"] = None
        body["entrypoint"] = os.environ.get("CLAUDE_CODE_ENTRYPOINT")
        body["ppid"] = os.getppid()
    encoded = json.dumps(body, ensure_ascii=False, default=str)
    if len(encoded) > MAX_PAYLOAD_CHARS:
        encoded = encoded[:MAX_PAYLOAD_CHARS] + "...<truncated>"
        body = {"_truncated": encoded}

    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session_id": payload.get("session_id"),
        "cwd": payload.get("cwd"),
        "event": payload.get("hook_event_name"),
        "payload": body,
    }

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        rotate_if_needed(LOG_PATH)
        append_row(LOG_PATH, (json.dumps(record, ensure_ascii=False, default=str) + "\n").encode("utf-8"))
    except Exception:
        pass  # fail-open: observability must never cost a session

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
