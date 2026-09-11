r"""PreToolUse NOTICE (plus dispatch bookkeeping) for a `git commit` without a
pathspec while this session still has a dispatched agent outstanding.

STATUS: LIVE since 2026-09-09 (claude-config). Carries `ops/rule-registry.md`
key `DISPATCH_COMMIT_PATHSPEC` — the asset property `ops/references/
shared-tree-git.md` §4 states for "a main-loop commit while a dispatched agent
of this session has not reported stopped". Born from commit a272c58
(2026-09-08): the main loop ran a bare `git commit -m` while a sonnet work-card
agent had four files staged; the agent's files rode into the wrong commit and
the agent reported "another session took the index" — from its position that
was the only explanation. The index is ONE object shared by every process in
the checkout; the dispatcher lacked exactly one fact at exactly one moment:
"an agent of yours is still running" when a commit is about to read that index.

  PreToolUse (matcher "Agent|Workflow"): records one outstanding dispatch for
    this session in `cache/dispatch-commit-notice/<session>.json` (FIFO of
    {ts, tool, type}). Silent.
  SubagentStop (matcher ""): pops the oldest outstanding dispatch; deletes the
    file when none remain. Silent.
  PreToolUse (matcher "Bash|PowerShell"): when the command runs `git commit`
    WITHOUT a `-- <pathspec>` and WITHOUT the marker [dispatch-ok], and this
    session has an outstanding dispatch younger than TTL, injects a NOTICE
    (`hookSpecificOutput.additionalContext`, the transport appdata_view_guard
    uses) naming the count, the age of the oldest dispatch and the two ways to
    proceed. The tool call itself is never blocked.

SEVERITY: NOTICE, not DENY (gate-severity-by-consumer, user ruling 2026-08-26:
the reader of this text is the LLM about to commit, so WARN plus a NAMED
promotion trigger). Promotion trigger to DENY: a second swallowed-stage incident
with this notice present in the transcript (registry review-when (d)). Fail-OPEN
on every internal error path (unparsable stdin, unwritable state dir, any
exception): exit 0, empty stdout, best-effort telemetry row `decision: error`.

WHAT IT DOES NOT DO: it does not attribute staged files — uncommitted work is
unidentifiable from outside (shared-tree-git §4 scope limit); only the
committer can scope what it commits. It does not see a positional pathspec
without `--` (`git commit -m x file.txt`) — that form is treated as unscoped and
produces a notice the reader can dismiss with the marker; accepted, labelled.

ESCAPES (each leaves a trace): the marker [dispatch-ok] in the command
(self-certified: the reader checked `git diff --cached --name-only`); logged as
`pass-marker` so habituation is watchable. A `-- <pathspec>` is not an escape,
it is the rule being followed, logged as `pass-pathspec`.

TTL: an outstanding dispatch older than TTL_SECONDS (4 h) is dropped on every
event — SubagentStop is the primary clear, the TTL is the backstop for a stop
that never fired (agent killed, session crashed mid-dispatch).

TEST OVERRIDES (calibration only; Claude Code never sets them): env
DCN_STATE_DIR redefines the state dir, DCN_LOG the telemetry path, DCN_NOW the
clock. If any appears in settings/env the hook has been retargeted — treat as
tampering.

TELEMETRY: `telemetry/dispatch-commit-notice.jsonl` — one row per dispatch,
stop, notice, pass-marker, pass-pathspec or error. Non-git commands are not
logged.

FALSE-POSITIVE LOG: none observed as of 2026-09-09 (born today). At 3 observed
misfires narrow the condition (e.g. ignore dispatches whose subagent_type is a
read-only agent — Explore, code-reviewer, security-engineer) rather than
widening the escape. A hook with no log has never been measured, which is not
the same as never having misfired.

Proof-of-life: `python hooks/dispatch_commit_notice.py --selftest` (two-sided,
temp state dir, last line `ALL PASS n/n`). The U-* cases pin the AP-62 half: an
input belonging to no decision class lands in the declared `error` row, so it is
counted as itself and never folded into `skip` (invisible) or `notice` (false).
review-when: (a) Claude Code gives every subagent its own worktree/index by
default (the shared index disappears → retire, keep the §4 property as history);
(b) SubagentStop stops firing once per dispatch (counts drift → notices with no
dispatch in the transcript; shorten TTL, do not widen the marker); (c) the Agent
or Workflow tool is renamed (matcher + TOOLS below); (d) a second swallowed-stage
incident with the notice present → promote to DENY with a deny_receipt.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

try:                        # notice receipt (rules/hook-deny-message.md R3n)
    from deny_receipt import notice_clause
except Exception:           # a hook must not stop noticing if telemetry breaks
    def notice_clause(hook, log=""): return ""

HOME = Path(os.path.expanduser("~/.claude"))
STATE_DIR = Path(os.environ.get("DCN_STATE_DIR") or (HOME / "cache" / "dispatch-commit-notice"))
# Precedence: DCN_LOG (per-hook override) > CLAUDE_TELEMETRY_DIR (suite
# redirect; production never sets it) > default.
LOG_PATH = Path(os.environ.get("DCN_LOG")
                or (Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (HOME / "telemetry")) / "dispatch-commit-notice.jsonl"))
TTL_SECONDS = 4 * 3600
DISPATCH_TOOLS = ("Agent", "Workflow")
SHELL_TOOLS = ("Bash", "PowerShell")
MARKER = "[dispatch-ok]"

# `git commit`, allowing `git -C <dir>` / `git -c k=v` between git and commit.
GIT_COMMIT = re.compile(r"(?<![\w./-])git\s+(?:-[Cc]\s+\S+\s+)*commit\b")
# a `-- <pathspec>` after `commit`, inside the same shell segment
PATHSPEC = re.compile(r"\bcommit\b[^|;&\n]*?(?:^|\s)--\s+[^-\s]")


def now() -> int:
    return int(os.environ.get("DCN_NOW") or time.time())


def log_row(row: dict) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def state_path(session: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session or "unknown")[:80]
    return STATE_DIR / f"{safe}.json"


def load_state(session: str) -> list:
    p = state_path(session)
    try:
        agents = json.loads(p.read_text(encoding="utf-8")).get("agents", [])
    except Exception:
        agents = []
    cutoff = now() - TTL_SECONDS
    return [a for a in agents if isinstance(a, dict) and int(a.get("ts", 0)) >= cutoff]


def save_state(session: str, agents: list) -> None:
    p = state_path(session)
    if not agents:
        try:
            p.unlink()
        except Exception:
            pass
        return
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"agents": agents}), encoding="utf-8")


def notice_text(agents: list) -> str:
    oldest = min(int(a.get("ts", now())) for a in agents)
    mins = max(0, (now() - oldest) // 60)
    kinds = sorted({str(a.get("type") or a.get("tool") or "agent") for a in agents})
    return (
        "[dispatch-commit-notice] Notice from dispatch_commit_notice, a local PreToolUse hook "
        f"(not file or page content): this session has {len(agents)} dispatched agent(s) not yet "
        f"reported stopped (oldest started {mins} min ago: {', '.join(kinds)}). The git index is "
        "shared with them, so a commit without a pathspec commits whatever they have staged as "
        "well. Scope the commit with `git commit -- <this session's paths>`; or check "
        "`git diff --cached --name-only` and, if every staged path is yours, repeat the command "
        f"with the marker {MARKER}."
        + notice_clause("dispatch_commit_notice")
    )


def decide(payload: dict) -> tuple:
    """Return (decision, text). decision in dispatch|stop|notice|pass-marker|pass-pathspec|skip."""
    event = str(payload.get("hook_event_name", ""))
    tool = str(payload.get("tool_name", ""))
    session = str(payload.get("session_id", "") or "unknown")
    agents = load_state(session)

    if event == "SubagentStop":
        if agents:
            agents.pop(0)
        save_state(session, agents)
        return "stop", ""

    if tool in DISPATCH_TOOLS:
        ti = payload.get("tool_input") or {}
        agents.append({"ts": now(), "tool": tool,
                       "type": str(ti.get("subagent_type") or ti.get("workflow") or "")[:40]})
        save_state(session, agents)
        return "dispatch", ""

    if tool in SHELL_TOOLS:
        cmd = str((payload.get("tool_input") or {}).get("command") or "")
        if not GIT_COMMIT.search(cmd):
            return "skip", ""
        save_state(session, agents)          # persists the TTL prune
        if MARKER in cmd:
            return "pass-marker", ""
        if PATHSPEC.search(cmd):
            return "pass-pathspec", ""
        if not agents:
            return "skip", ""
        return "notice", notice_text(agents)

    return "skip", ""


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            sys.exit(0)
    except Exception:
        sys.exit(0)
    session = str(payload.get("session_id", "") or "unknown")
    try:
        decision, text = decide(payload)
        if decision != "skip":
            row = {"ts": now(), "session": session, "event": str(payload.get("hook_event_name", "")),
                   "decision": decision, "n_active": len(load_state(session))}
            if decision in ("notice", "pass-marker", "pass-pathspec"):
                row["cmd"] = str((payload.get("tool_input") or {}).get("command") or "")[:160]
            log_row(row)
        if decision == "notice":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                     "additionalContext": text}}))
    except SystemExit:
        raise
    except Exception as e:                                   # fail-open, but visible
        log_row({"ts": now(), "session": session, "decision": "error", "error": repr(e)[:200]})
    sys.exit(0)


# --------------------------------------------------------------------------- selftest
def _selftest() -> int:
    import subprocess
    import tempfile

    results = []

    def check(name, ok):
        results.append((name, bool(ok)))
        print(("PASS " if ok else "FAIL ") + name)

    with tempfile.TemporaryDirectory() as td:
        os.environ["DCN_STATE_DIR"] = os.path.join(td, "state")
        os.environ["DCN_LOG"] = os.path.join(td, "log.jsonl")
        global STATE_DIR, LOG_PATH
        STATE_DIR = Path(os.environ["DCN_STATE_DIR"])
        LOG_PATH = Path(os.environ["DCN_LOG"])
        sid = "selftest-session"

        def pre(tool, ti, session=sid):
            return {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": ti, "session_id": session}

        def stop(session=sid):
            return {"hook_event_name": "SubagentStop", "session_id": session}

        # negative side: nothing outstanding
        d, _ = decide(pre("Bash", {"command": "git commit -m 'x'"}))
        check("N-1 bare commit with no dispatch -> skip", d == "skip")
        d, _ = decide(pre("Bash", {"command": "ls -la"}))
        check("N-2 non-git command -> skip", d == "skip")

        # dispatch bookkeeping
        d, _ = decide(pre("Agent", {"subagent_type": "work-card-executor", "prompt": "x"}))
        check("P-1 Agent dispatch recorded", d == "dispatch" and len(load_state(sid)) == 1)
        d, _ = decide(pre("Workflow", {"workflow": "review"}))
        check("P-2 Workflow dispatch recorded", d == "dispatch" and len(load_state(sid)) == 2)

        # positive side: notice
        d, text = decide(pre("Bash", {"command": "git add a.py && git commit -m 'feat: x'"}))
        check("P-3 bare commit with 2 outstanding -> notice", d == "notice" and "2 dispatched agent(s)" in text)
        check("P-3b notice names both ways forward", "git commit -- " in text and MARKER in text)
        d, _ = decide(pre("PowerShell", {"command": "git -C C:/x commit --amend --no-edit"}))
        check("P-4 amend without pathspec (git -C form) -> notice", d == "notice")
        d, _ = decide(pre("Bash", {"command": "git commit -a -m 'x'"}))
        check("P-5 commit -a -> notice", d == "notice")

        # negative side with dispatch outstanding
        d, _ = decide(pre("Bash", {"command": "git commit -m 'x' -- ops/a.md hooks/b.py"}))
        check("N-3 pathspec -> pass-pathspec", d == "pass-pathspec")
        d, _ = decide(pre("Bash", {"command": "git commit -F msg.txt -- references/"}))
        check("N-4 pathspec after -F -> pass-pathspec", d == "pass-pathspec")
        d, _ = decide(pre("Bash", {"command": "git commit -m 'x' [dispatch-ok]"}))
        check("N-5 marker -> pass-marker", d == "pass-marker")
        d, _ = decide(pre("Bash", {"command": "git log --oneline -5 && git status"}))
        check("N-6 git without commit -> skip", d == "skip")
        d, _ = decide(pre("Bash", {"command": "echo 'do not git commit here'"}))
        check("N-7 the words inside echo still count as a commit form (accepted over-match, notice)", d == "notice")
        d, _ = decide(pre("Bash", {"command": "git commit -m 'x'"}, session="other-session"))
        check("N-8 another session's commit -> skip (state is per session)", d == "skip")

        # stop bookkeeping
        d, _ = decide(stop())
        check("P-6 SubagentStop pops one", d == "stop" and len(load_state(sid)) == 1)
        d, _ = decide(pre("Bash", {"command": "git commit -m 'x'"}))
        check("P-7 one still outstanding -> notice", d == "notice")
        d, _ = decide(stop())
        check("P-8 second stop clears the file", d == "stop" and not state_path(sid).exists())
        d, _ = decide(pre("Bash", {"command": "git commit -m 'x'"}))
        check("N-9 all stopped -> skip", d == "skip")
        d, _ = decide(stop())
        check("N-10 stop with nothing outstanding is harmless", d == "stop" and not state_path(sid).exists())

        # TTL backstop
        decide(pre("Agent", {"subagent_type": "Explore"}))
        os.environ["DCN_NOW"] = str(now() + TTL_SECONDS + 60)
        d, _ = decide(pre("Bash", {"command": "git commit -m 'x'"}))
        check("N-11 dispatch older than TTL is dropped -> skip", d == "skip" and not state_path(sid).exists())
        os.environ.pop("DCN_NOW", None)

        # telemetry rows
        rows = [json.loads(l) for l in LOG_PATH.read_text(encoding="utf-8").splitlines()] if LOG_PATH.exists() else []
        check("T-1 selftest wrote no telemetry via decide() (rows are main()'s job)", rows == [])

        # subprocess: the real stdin path
        env = dict(os.environ)
        py = sys.executable
        me = os.path.abspath(__file__)
        r = subprocess.run([py, me], input=json.dumps(pre("Agent", {"subagent_type": "backend-architect"})),
                           capture_output=True, text=True, env=env)
        check("S-1 subprocess dispatch: exit 0, silent", r.returncode == 0 and r.stdout.strip() == "")
        r = subprocess.run([py, me], input=json.dumps(pre("Bash", {"command": "git commit -m 'x'"})),
                           capture_output=True, text=True, env=env)
        try:
            out = json.loads(r.stdout)
            ok = out["hookSpecificOutput"]["hookEventName"] == "PreToolUse" and \
                "[dispatch-commit-notice]" in out["hookSpecificOutput"]["additionalContext"]
        except Exception:
            ok = False
        check("S-2 subprocess bare commit: additionalContext JSON", r.returncode == 0 and ok)
        rows = [json.loads(l) for l in LOG_PATH.read_text(encoding="utf-8").splitlines()]
        check("S-3 telemetry rows dispatch + notice", [x["decision"] for x in rows] == ["dispatch", "notice"])
        r = subprocess.run([py, me], input="not json", capture_output=True, text=True, env=env)
        check("S-4 subprocess garbage stdin: exit 0, silent", r.returncode == 0 and r.stdout.strip() == "")
        r = subprocess.run([py, me], input=json.dumps(stop()), capture_output=True, text=True, env=env)
        check("S-5 subprocess SubagentStop: exit 0, silent, state cleared",
              r.returncode == 0 and r.stdout.strip() == "" and not state_path(sid).exists())

        # U-*: input that belongs to no decision class (AP-62). `decide` reads a
        # mapping tool_input; anything else is undetermined. The property to pin
        # is not just silence -- a silent skip would make it invisible -- but
        # that it lands in the DECLARED `error` row, so an unclassifiable input
        # is counted as itself and never as a notice or a skip.
        before = len(LOG_PATH.read_text(encoding="utf-8").splitlines())
        r = subprocess.run([py, me],
                           input=json.dumps({"hook_event_name": "PreToolUse",
                                             "tool_name": "Bash",
                                             "tool_input": ["git commit -m x"],
                                             "session_id": sid}),
                           capture_output=True, text=True, env=env)
        rows = [json.loads(l) for l in LOG_PATH.read_text(encoding="utf-8").splitlines()]
        check("U-1 non-mapping tool_input: exit 0, silent",
              r.returncode == 0 and r.stdout.strip() == "")
        check("U-1b and recorded as `error`, not folded into skip or notice",
              len(rows) == before + 1 and rows[-1]["decision"] == "error")
        for cid, raw in (("U-2", "[1, 2]"), ("U-3", '"a string payload"'), ("U-4", "null")):
            r = subprocess.run([py, me], input=raw, capture_output=True, text=True, env=env)
            check(f"{cid} payload that parses but is not an object: exit 0, silent",
                  r.returncode == 0 and r.stdout.strip() == "")
        # Negative control: without it, U-1b would also pass on a hook that
        # errored on everything.
        after_u = len(LOG_PATH.read_text(encoding="utf-8").splitlines())
        r = subprocess.run([py, me], input=json.dumps(pre("Bash", {"command": "ls -la"})),
                           capture_output=True, text=True, env=env)
        rows = [json.loads(l) for l in LOG_PATH.read_text(encoding="utf-8").splitlines()]
        check("U-5 a well-formed non-git command still skips silently and logs "
              "nothing (the negative control for U-1b)",
              r.returncode == 0 and r.stdout.strip() == "" and len(rows) == after_u)

    n_ok = sum(1 for _, ok in results if ok)
    print(f"{'ALL PASS' if n_ok == len(results) else 'FAILED'} {n_ok}/{len(results)}")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()
