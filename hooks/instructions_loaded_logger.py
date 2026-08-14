#!/usr/bin/env python3
r"""InstructionsLoaded logger -- rule-load observability (E1 instrument).

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

PROOF OF LIFE (ops/40-maintenance.md section 4.2)
-------------------------------------------------
    python -c "import json;print(sum(1 for _ in open(r'~/.claude/telemetry/rule-loads.jsonl'.replace('~',__import__('os').path.expanduser('~')),encoding='utf-8')))"
An empty or missing file after a fresh session means the event does not fire
in this Claude Code version -- that is a real finding, not a hook bug: record
it and fall back to reading `/context` by hand.

Related: ops/lessons.md L-011 (enforcement layer chosen by trigger shape);
this file is OBSERVATION only, it enforces nothing.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "telemetry" / "rule-loads.jsonl"
MAX_BYTES = 5 * 1024 * 1024  # rotate once past this; bounded disk use
MAX_PAYLOAD_CHARS = 4000  # truncate pathological payloads, keep the shape


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
        with open(LOG_PATH, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass  # fail-open: observability must never cost a session

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
