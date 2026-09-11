#!/usr/bin/env python3
r"""Delivery gate -- SHADOW MODE (E2 phase 1). Observes, never blocks.

STATUS: SHADOW (observe-only) since 2026-08-11; graduation criterion: the rule-registry
entry that names this hook (measured false-positive rate before any deny).

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

VOCABULARY REBUILD (2026-09-08) -- the phase-2 step, done
--------------------------------------------------------
MEASURED BY REPLAY, not by projection: the extractor below was re-run over all
451 subagent transcripts on disk, so `verified` is decided by the same
tool_result pairing the live hook uses. The telemetry log alone could not answer
this -- it stores `commands` but not their results, so it can only bound the
answer. Ruler beside the rate: same extractor, same files, one line changed.

    population: 451 transcripts, 295 of them wrote something
    would_block, portable vocabulary only : 251/295 = 85.1%
    would_block, + local vocabulary       : 178/295 = 60.3%
    rescued (a real verify ran and came back clean): 73

The 73 were never unverified deliveries. They ran `python .../controls.py`,
`--selftest`, a `*_lint.py` / `*_audit.py` / gate script, or `diff` -- this
environment's actual verdict-producing shapes, none of which any framework
allowlist names. A gate whose object vocabulary misses the classes its own rule
covers reports a rate about its vocabulary, not about the work (L-044).

Of the 178 that still would_block, 140 ran something WEAK -- `git status`,
`grep`, `ls`. Those are recorded in `weak_evidence` and never promoted:
looking is not checking, and a gate that accepted `ls` would be measuring
nothing. Recording them splits the residual into "looked but ran no verdict"
(140) and "did not look at all" (38), which are different findings about very
different subagent behaviour.

NOT ADDED, deliberately: `git status|diff|log`, `grep`, `ls`, `wc`. Adding them
would have driven would_block near zero and made the gate unfalsifiable -- the
Goodhart failure this shadow phase exists to avoid.

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

Proof-of-life: `python tools/e2-gate-test/test_shadow_hook.py` (22/22, incl. 9
two-sided vocabulary cases: 5 shapes that must be rescued, 1 whose tool_result
was an error, 3 weak shapes that must stay unrescued).
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# CLAUDE_TELEMETRY_DIR redirects the whole telemetry dir (suites use a temp dir;
# production never sets it).
LOG_PATH = Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (Path.home() / ".claude" / "telemetry")) / "delivery-gate-shadow.jsonl"
MAX_BYTES = 5 * 1024 * 1024
MAX_COMMANDS = 40
CMD_TRUNC = 160

WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}

# Prose has nothing to execute, so "wrote but did not verify" is not a finding
# about it. Both organic would-block rows of the 2026-08-15 soak were subagents
# writing spec documents (verification_PSM_v0.3.md, verification_PIM_v0.5.md) --
# false positives produced by treating "wrote a file" as "wrote something a test
# run should have covered". Config formats (.json/.yaml/.toml) deliberately
# still count: a broken config IS verifiable by running something.
PROSE_EXT = (".md", ".txt", ".rst", ".adoc", ".markdown")


def is_prose(path: str) -> bool:
    return path.lower().rstrip().endswith(PROSE_EXT)
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

# Verification-looking commands, PORTABLE vocabulary: the framework names any
# repo might use. This was the original guess (see module docstring).
VERIFY_SHELL = re.compile(
    r"\b(pytest|unittest|vitest|jest|mocha|tsc|oxlint|eslint|ruff|mypy|flake8"
    r"|py_compile|cargo\s+(test|check|clippy)|go\s+(test|vet)|gradlew?\s+test"
    r"|npm\s+(test|run\s+(test|lint|build|typecheck))"
    r"|pnpm\s+(test|lint|build)|yarn\s+(test|lint|build)|make\s+(test|check|lint)"
    # .NET stack (added 2026-09-11, shadow-hook eval: 3 of 15 sampled would_block
    # rows ran `dotnet build` + an acceptance script on real .cs edits and were
    # counted as unverified — a vocabulary gap, not a missing verification)
    r"|dotnet\s+(build|test|run)|msbuild|nunit3?-console|vstest)\b",
    re.I,
)

# LOCAL vocabulary, added 2026-09-08 -- the phase-2 rebuild the docstring
# promised. This environment barely uses a test framework: it verifies by running
# a control suite, a selftest flag, a lint/audit/gate script, or a `diff`. None of
# those are in the portable list, so 73 subagents that DID verify were counted as
# unverified. That is the L-044 shape: the rule names a class the instrument has
# no word for. Numbers and method in the docstring.
VERIFY_LOCAL = re.compile(
    r"(--selftest|--controls"
    r"|python[^|;&\n]*(controls|invariants|fill_gate|pol)\.py"
    r"|python[^|;&\n]*[\\/]?test_\w+\.py"
    r"|python[^|;&\n]*tests[\\/]\S+\.py"
    r"|python[^|;&\n]*\w*(lint|audit|verify|gate)\w*\.py"
    r"|gsnap\.py\s+(verify|freshness|bench)"
    r"|(?:^|[|;&]\s*)diff\s)",
    re.I | re.M,
)

# WEAK evidence: it was LOOKED AT, not checked. `git status`, `grep`, `ls`, `cat`
# produce output for a human to judge, never a verdict -- so they must never set
# `verified`, or "I listed the directory" would close an acceptance criterion.
# They are recorded instead of discarded: 140 of the 178 still-would-block
# transcripts ran one, and that is the difference between "the subagent skipped
# verification" and "the subagent looked but ran nothing that could fail".
WEAK_SHELL = re.compile(
    r"(?:^|[|;&]\s*)(?:git\s+(?:status|diff|log)|grep|rg|ls|dir|wc|cat|head|tail)\b",
    re.I | re.M,
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
        "weak_evidence": [],
        "commands": [],
        "transcript_read": False,
    }
    if not path:
        return facts
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return facts

    pending = {}       # tool_use_id -> command string, awaiting its tool_result
    pending_weak = {}  # the same, for looked-at-but-not-checked commands
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
                        target = str(payload.get("file_path", ""))[:CMD_TRUNC]
                        if is_prose(target):
                            continue
                        facts["wrote"] = True
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
                        if VERIFY_SHELL.search(cmd) or VERIFY_LOCAL.search(cmd):
                            pending[block.get("id")] = cmd[:CMD_TRUNC]
                        elif WEAK_SHELL.search(cmd):
                            pending_weak[block.get("id")] = cmd[:CMD_TRUNC]

                elif block.get("type") == "tool_result":
                    cmd = pending.pop(block.get("tool_use_id"), None)
                    if cmd is None:
                        weak = pending_weak.pop(block.get("tool_use_id"), None)
                        # Recorded, never promoted: looking is not checking.
                        if weak is not None and block.get("is_error") is False:
                            if len(facts["weak_evidence"]) < 10:
                                facts["weak_evidence"].append(weak)
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
            "verify_evidence": [], "weak_evidence": [], "commands": [],
            "transcript_read": False,
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
