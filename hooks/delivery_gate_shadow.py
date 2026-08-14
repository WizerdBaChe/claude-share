#!/usr/bin/env python3
r"""Delivery gate -- SHADOW MODE (E2 phase 1). Observes, never blocks.

WHAT THIS IS
------------
`ops/30-judgment.md` R2 says a deliverable is done only when every acceptance
criterion has evidence. That is a rule the model may skip. This hook is the
first step toward making it a mechanism -- but it does NOT enforce anything
yet. For one week it only records what it WOULD have blocked, so the
false-positive rate is measured before any subagent is ever stopped.

Enforcement is deliberately absent, not unfinished:
- SubagentStop only. The main session's Stop event is untouched (smaller blast
  radius; a bad main Stop gate can wedge a session).
- exit 0 with empty stdout, unconditionally. An empty stdout is "no decision"
  for this event, so nothing can be blocked by accident.

WHAT IT RECORDS
---------------
One JSON line per subagent completion, into
%USERPROFILE%\.claude\telemetry\delivery-gate-shadow.jsonl:

    event_kind       which population this row belongs to (see below)
    wrote            did the subagent modify anything (Edit/Write/NotebookEdit,
                     or a Bash command that looks write-shaped)
    verified         did a verification-looking command run and come back clean
    would_block      wrote and not verified
    commands         every Bash/PowerShell command it ran (truncated)

EVENT_KIND -- added 2026-08-12, why the first 57 rows were 94.7% empty
-----------------------------------------------------------------------
SubagentStop fires far more often than subagent transcripts are written. Of the
first 57 rows, 54 had no readable transcript, and for all 54 the expected file
did not exist ANYWHERE under projects/ (checked against the whole tree, not
just the session dir); the sessions themselves did exist, and the counts do not
line up either -- one session emitted 19 events against 1 subagent file.
So those events are not Agent-tool dispatches at all, and averaging them into
the phase-2 numbers would read as "94.7% of subagents are unverifiable" when
the truth is "94.7% of these rows are not subagents".

    dispatch            transcript resolved -- the only rows phase 2 may count
    no-transcript       agent_id present, expected file absent (not a dispatch,
                        or the file had not been flushed yet -- `subagents_dir`
                        separates those: dir exists ⇒ this session does produce
                        them ⇒ a race is live; dir absent ⇒ it never did)
    no-agent-id         payload carried no agent_id
    no-transcript-path  payload carried no transcript_path

Phase-2 analysis MUST filter to event_kind == "dispatch". Rows written before
2026-08-12 have no such field; treat a missing event_kind as "unknown" and
exclude it -- do not backfill by re-deriving, the files it would look for have
had two more days to disappear.

`commands` is the point of the shadow phase: the verification allowlist below
is a GUESS, and a guessed allowlist is exactly how a gate becomes Goodhart-able.
Phase 2 rebuilds it from the commands this log actually collects.

PROXIES USED (named on purpose -- see ops/lessons.md L-012)
-----------------------------------------------------------
- `is_error: False` on a tool_result is Claude Code's TOOL-level error flag. It
  is a proxy for "exit code 0", not the exit code itself. If phase-2 analysis
  shows the two diverge, the gate needs a PostToolUse(Bash) recorder that
  captures the real exit status instead.
- A command MATCHING the allowlist is a proxy for "the change was actually
  verified". `echo pytest` matches and verifies nothing. Shadow mode cannot
  close that hole; it exists to size it.
- Reading the transcript is a proxy for observing the run. A tool call the
  transcript does not record is invisible here.

CONTRACT: stdin = hook payload JSON; stdout = nothing; exit = always 0.
Fail-open by construction: any exception is swallowed. A gate that can break a
delivery is worse than a delivery that was not gated.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "telemetry" / "delivery-gate-shadow.jsonl"
MAX_BYTES = 5 * 1024 * 1024
MAX_COMMANDS = 40
CMD_TRUNC = 160

WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
SHELL_TOOLS = {"Bash", "PowerShell"}

# Bash that changes state. Heuristic -- deliberately broad; a false "wrote"
# only produces a would_block line for review, never a denial.
WRITE_SHELL = re.compile(
    r"(^|[\s;&|])(rm|mv|cp|mkdir|touch|tee|chmod|chown|ln)\s"
    r"|>>?\s*[^\s|&]"
    r"|\bsed\s+-i\b|\bgit\s+(add|commit|checkout|reset|revert|merge|push)\b"
    r"|\bnpm\s+(i|install|ci)\b|\bpip\s+install\b|\bSet-Content\b|\bOut-File\b",
    re.I,
)

# Verification-looking commands. A GUESS (see module docstring) -- phase 2
# rebuilds this from the collected `commands` field.
VERIFY_SHELL = re.compile(
    r"\b(pytest|unittest|vitest|jest|mocha|tsc|oxlint|eslint|ruff|mypy|flake8"
    r"|py_compile|cargo\s+(test|check|clippy)|go\s+(test|vet)|gradlew?\s+test"
    r"|npm\s+(test|run\s+(test|lint|build|typecheck))"
    r"|pnpm\s+(test|lint|build)|yarn\s+(test|lint|build)|make\s+(test|check|lint))\b",
    re.I,
)


def resolve_transcript(payload):
    """Find the SUBAGENT's transcript. Returns (path_or_None, kind, why).

    `why` is the event_kind documented in the module docstring -- it says which
    POPULATION the row belongs to, so phase 2 can drop the events that were
    never subagent dispatches instead of scoring them as unverified deliveries.

    Measured 2026-08-11: SubagentStop hands over the MAIN session's
    `transcript_path`, not the subagent's. The subagent's own transcript lives
    beside it at <main_stem>/subagents/agent-<agent_id>.jsonl. Scanning the
    main transcript instead would mark every row wrote=True and verified=True
    (the main session almost always did both) -- silent garbage, so on failure
    this returns kind='main-fallback' and the caller SKIPS classification
    rather than guessing.
    """
    raw = payload.get("transcript_path")
    agent_id = payload.get("agent_id")
    if not raw:
        return None, "none", "no-transcript-path"
    main = Path(str(raw))
    if main.name.startswith("agent-"):
        return main, "subagent-direct", "dispatch"
    if agent_id:
        candidate = main.parent / main.stem / "subagents" / f"agent-{agent_id}.jsonl"
        if candidate.exists():
            return candidate, "subagent-resolved", "dispatch"
        return main, "main-fallback", "no-transcript"
    return main, "main-fallback", "no-agent-id"


def subagents_dir_exists(payload):
    """Does this session have a subagents/ directory at all?

    Separates "SubagentStop fired for something that is not a dispatch" from
    "the dispatch transcript had not been flushed when the hook ran". Cheap
    (one stat) and it is the only thing in the row that can refute the
    not-a-dispatch reading.
    """
    raw = payload.get("transcript_path")
    if not raw:
        return None
    try:
        main = Path(str(raw))
        return (main.parent / main.stem / "subagents").is_dir()
    except OSError:
        return None


def rotate_if_needed(path):
    try:
        if path.exists() and path.stat().st_size > MAX_BYTES:
            backup = path.with_suffix(".jsonl.1")
            if backup.exists():
                backup.unlink()
            path.rename(backup)
    except OSError:
        pass


def scan_transcript(path):
    """Walk a transcript, pairing tool_use calls with their tool_result."""
    facts = {
        "wrote": False,
        "write_evidence": [],
        "verified": False,
        "verify_evidence": [],
        "commands": [],
        "transcript_read": False,
    }
    if not path:
        return facts
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return facts

    pending = {}  # tool_use_id -> command string, for shell calls awaiting a result
    with fh:
        facts["transcript_read"] = True
        for line in fh:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            content = (rec.get("message") or {}).get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue

                if block.get("type") == "tool_use":
                    name = block.get("name")
                    payload = block.get("input") or {}
                    if name in WRITE_TOOLS:
                        facts["wrote"] = True
                        target = str(payload.get("file_path", ""))[:CMD_TRUNC]
                        if target and len(facts["write_evidence"]) < 10:
                            facts["write_evidence"].append(f"{name}:{target}")
                    elif name in SHELL_TOOLS:
                        cmd = str(payload.get("command", ""))
                        if len(facts["commands"]) < MAX_COMMANDS:
                            facts["commands"].append(cmd[:CMD_TRUNC])
                        if WRITE_SHELL.search(cmd):
                            facts["wrote"] = True
                            if len(facts["write_evidence"]) < 10:
                                facts["write_evidence"].append(f"shell:{cmd[:80]}")
                        if VERIFY_SHELL.search(cmd):
                            pending[block.get("id")] = cmd[:CMD_TRUNC]

                elif block.get("type") == "tool_result":
                    cmd = pending.pop(block.get("tool_use_id"), None)
                    if cmd is None:
                        continue
                    # is_error is the TOOL-level flag, a proxy for exit status.
                    if block.get("is_error") is False:
                        facts["verified"] = True
                        if len(facts["verify_evidence"]) < 10:
                            facts["verify_evidence"].append(cmd)

    return facts


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw else {}
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        return 0

    try:
        tpath, kind, event_kind = resolve_transcript(payload)
        # Only classify when the source is genuinely the subagent's transcript.
        # A wrong source is reported as such, never silently scanned.
        facts = scan_transcript(tpath) if kind.startswith("subagent") else {
            "wrote": None, "write_evidence": [], "verified": None,
            "verify_evidence": [], "commands": [], "transcript_read": False,
        }
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "mode": "shadow",
            "session_id": payload.get("session_id"),
            "agent_id": payload.get("agent_id"),
            "agent_type": payload.get("agent_type"),
            "event_kind": event_kind,
            "subagents_dir": subagents_dir_exists(payload),
            "transcript_kind": kind,
            "transcript_name": Path(str(tpath)).name if tpath else "",
            "cwd": payload.get("cwd"),
            "would_block": bool(facts["wrote"]) and not facts["verified"] if kind.startswith("subagent") else False,
            **facts,
        }
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        rotate_if_needed(LOG_PATH)
        with open(LOG_PATH, "a", encoding="utf-8", newline="\n") as out:
            out.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass  # fail-open: observability never costs a delivery

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
