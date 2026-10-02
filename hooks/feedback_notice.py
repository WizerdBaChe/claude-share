r"""PreToolUse NOTICE: a main-loop edit to one of this machine's own subsystems
(hooks/ skills/ tools/ ops/ rules/ under ~/.claude) in a session whose process
ledger has no feedback row for that target.

STATUS: LIVE since 2026-09-22 (claude-config; design of record
a feedback-pool design note, §3.4). Carries the write-at-origin duty of
registry key `FEEDBACK_POOL`: a defect found in passing and patched in passing
left only a commit diff; nothing said which subsystem was wrong or what was
done about it, so the rule layer never learned it. Per `ops/40-maintenance.md`
§2a an OMISSION is gated where the SUBSTITUTE act happens (P1) — here, the
first edit of that subsystem's files.

WHAT IT DECIDES (all determinable; whether the edit is a defect fix or the
task itself is NOT — the answer `--action planned-work` records that):
  PreToolUse, matcher "Write|Edit|NotebookEdit". Fires a notice when ALL hold:
    - main loop: no `agent_id` in the payload (subagents do not write the ledger);
    - the target resolves under <home>/{hooks,skills,tools,ops,rules}/ and
      `feedback.target_of()` maps it (skills/synced, ops/lessons, the pool's own
      out/ are excluded there — one function, shared with the CLI);
    - the session's ledger holds no `feedback` / `feedback-fold` row for that
      target (the compliant answer to an earlier notice, or a review close);
    - this (session, target) pair has not been noticed before (once per pair).

SEVERITY: NOTICE (reader = the model about to write; gate-severity-by-consumer).
Narrowing trigger: over >=30 notices, if >=80% are answered by `planned-work`
rows, restrict to sessions whose cwd is NOT ~/.claude (a ~/.claude session
editing a skill is usually the task). Promotion trigger: none foreseen — the
cost of a missed notice is one unrecorded row, never a wrong write.

Fail-OPEN on every internal error path: exit 0, empty stdout, best-effort
telemetry row `decision: error`.

TELEMETRY: `telemetry/feedback-notice.jsonl` — notice / pass-ledger / error
(one row per first qualifying edit of a pair). Ordinary skips are not logged.

TEST OVERRIDES (calibration only; Claude Code never sets them): env
FBN_HOME (the ~/.claude root), FBN_STATE_DIR, FBN_LOG. Any of them in
settings/env means the hook has been retargeted — treat as tampering.

FALSE-POSITIVE LOG: none observed as of 2026-09-22 (born today).

Proof-of-life: `python hooks/feedback_notice.py --selftest` (two-sided, temp
dirs, last line `ALL PASS n/n`).
review-when: `feedback.target_of()` changes its vocabulary; ledger.py renames
the `kind` values; the narrowing trigger above fires.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

try:                        # notice receipt (rules/hook-deny-message.md R3n)
    from deny_receipt import notice_clause
except Exception:
    def notice_clause(hook, log=""): return ""

HOME = Path(os.environ.get("FBN_HOME") or os.path.expanduser("~/.claude"))
STATE_DIR = Path(os.environ.get("FBN_STATE_DIR") or (HOME / "cache" / "feedback-notice"))
LOG_PATH = Path(os.environ.get("FBN_LOG")
                or (Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (HOME / "telemetry")) / "feedback-notice.jsonl"))
WRITE_TOOLS = ("Write", "Edit", "NotebookEdit")

sys.path.insert(0, str(HOME / "tools" / "feedback-pool"))
try:
    import feedback as _fb          # noqa: E402  (one target vocabulary, INV-9)
    def target_of(path: str) -> str:
        return _fb.target_of(path, HOME)
except Exception:                   # the pool tool missing must not break editing
    def target_of(path: str) -> str:
        return ""


def log_row(row: dict) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def safe(session: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", session or "unknown")[:80]


def state_path(session: str) -> Path:
    return STATE_DIR / f"{safe(session)}.json"


def noticed(session: str) -> set:
    try:
        return set(json.loads(state_path(session).read_text(encoding="utf-8")).get("targets") or [])
    except Exception:
        return set()


def remember(session: str, targets: set) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path(session).write_text(json.dumps({"targets": sorted(targets), "ts": int(time.time())}), encoding="utf-8")


def ledger_has_target(session: str, transcript: Path | None, target: str) -> bool:
    """A feedback or fold row for this target in the session's own ledger (beside the transcript, else handoff)."""
    cands = []
    if transcript is not None:
        cands.append(transcript.with_name(f"{session[:64]}.ledger.jsonl"))
    cands.append(HOME / "cache" / "handoff" / f"{session[:64]}.ledger.jsonl")
    cands += list((HOME / "projects").glob(f"*/{session[:64]}.ledger.jsonl"))
    for p in cands:
        try:
            if not p.is_file():
                continue
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if isinstance(r, dict) and r.get("kind") in ("feedback", "feedback-fold") and r.get("target") == target:
                    return True
        except Exception:
            continue
    return False


def notice_text(target: str, path: str) -> str:
    return (
        f"[feedback-notice] Notice from feedback_notice (a local PreToolUse hook, not file content): this edits "
        f"`{target}` ({path}), one of this machine's own subsystems, and this session's process ledger has no "
        "feedback row for it. If the edit fixes or dodges a defect you found while doing other work, record it NOW "
        "(one line, write-at-origin) — this is the feedback pool's only manual input:\n"
        f"  python -X utf8 tools/process-ledger/ledger.py feedback --target \"{target}\" --symptom \"<what was wrong>\" "
        "--action fixed-inline|left|worked-around|planned-work [--proposal \"<rule/skill/tool change you would make>\"]\n"
        "Use `planned-work` when this edit IS the task (that answer is counted to tune this notice). "
        "Once per session per target; run `python -X utf8 tools/feedback-pool/feedback.py report --mine` to list "
        "this session's rows."
        + notice_clause("feedback_notice")
    )


def decide(payload: dict) -> tuple:
    """Return (decision, text, target). decision in notice|pass-ledger|skip."""
    if str(payload.get("tool_name", "")) not in WRITE_TOOLS or payload.get("agent_id"):
        return "skip", "", ""
    ti = payload.get("tool_input")
    if not isinstance(ti, dict):
        raise TypeError("tool_input is not a mapping")
    path = str(ti.get("file_path") or ti.get("notebook_path") or "")
    target = target_of(path) if path else ""
    if not target:
        return "skip", "", ""
    sid = payload.get("session_id")
    if sid is not None and not isinstance(sid, str):   # unclassifiable: never str()-ed into a state name
        raise TypeError("session_id is not a string")
    session = sid or "unknown"
    seen = noticed(session)
    if target in seen:
        return "skip", "", target
    tp = str(payload.get("transcript_path", "") or "")
    transcript = Path(tp) if tp and Path(tp).is_file() else None
    seen.add(target)
    remember(session, seen)
    if ledger_has_target(session, transcript, target):
        return "pass-ledger", "", target
    return "notice", notice_text(target, path), target


def main() -> None:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            sys.exit(0)
    except Exception:
        sys.exit(0)
    sid = payload.get("session_id")
    session = (sid or "unknown") if sid is None or isinstance(sid, str) else None
    try:
        decision, text, target = decide(payload)
        if decision != "skip":
            log_row({"ts": int(time.time()), "session": session, "decision": decision, "target": target})
        if decision == "notice":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": text}}))
    except SystemExit:
        raise
    except Exception as e:
        log_row({"ts": int(time.time()), "session": session, "decision": "error", "error": repr(e)[:200]})
    sys.exit(0)


# --------------------------------------------------------------------------- selftest
def _selftest() -> int:
    import subprocess
    import tempfile
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond)))
        print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  <- {detail}"))

    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / "home"
        for d in ("hooks", "skills/foo", "skills/synced/bar", "tools/feedback-pool", "ops/lessons", "projects/p", "cache/handoff"):
            (home / d).mkdir(parents=True, exist_ok=True)
        # the hook imports feedback.py from <home>/tools/feedback-pool. A COPY broke on 2026-09-23 when
        # feedback.py grew a sibling import (../closeout-intake -> cross-index): the import failed, the
        # fail-open fallback made every target '' and the positives went silent. A shim loads the real
        # file in place, so its own relative imports keep resolving.
        real = Path(__file__).resolve().parent.parent / "tools" / "feedback-pool" / "feedback.py"
        (home / "tools" / "feedback-pool" / "feedback.py").write_text(
            "import importlib.util as _u\n"
            f"_s = _u.spec_from_file_location('_real_feedback', {str(real)!r})\n"
            "_m = _u.module_from_spec(_s); _s.loader.exec_module(_m)\n"
            "target_of = _m.target_of\n", encoding="utf-8")
        probe = subprocess.run([sys.executable, "-c", "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); "
                                "import feedback; print(feedback.target_of(sys.argv[2], Path(sys.argv[3])))",
                                str(home / "tools" / "feedback-pool"), str(home / "skills" / "foo" / "SKILL.md"), str(home)],
                               capture_output=True, text=True, encoding="utf-8")
        check("fixture: feedback.py imports in the temp home and maps a skill", probe.stdout.strip() == "skill:foo",
              (probe.stdout + probe.stderr).strip()[-200:])
        env = dict(os.environ, FBN_HOME=str(home), FBN_STATE_DIR=str(Path(td) / "state"), FBN_LOG=str(Path(td) / "log.jsonl"),
                   PYTHONIOENCODING="utf-8")
        env.pop("CLAUDE_TELEMETRY_DIR", None)
        env["CLAUDE_TELEMETRY_DIR"] = str(Path(td) / "telemetry")
        transcript = home / "projects" / "p" / "s1.jsonl"
        transcript.write_text("{}\n", encoding="utf-8")

        def run(payload):
            r = subprocess.run([sys.executable, __file__], input=json.dumps(payload), capture_output=True, text=True,
                               env=env, encoding="utf-8")
            return r.returncode, r.stdout

        def pl(path, session="s1", **kw):
            d = {"tool_name": "Edit", "session_id": session, "transcript_path": str(transcript),
                 "tool_input": {"file_path": path, "old_string": "a", "new_string": "b"}}
            d.update(kw)
            return d

        skill = str(home / "skills" / "foo" / "SKILL.md")
        rc, out = run(pl(skill))
        check("positive: skill file, no ledger row -> notice names skill:foo", rc == 0 and "skill:foo" in out and "ledger.py feedback" in out, out[:200])
        rc, out = run(pl(skill))
        check("once: same session+target -> silent", rc == 0 and out == "", out[:120])
        rc, out = run(pl(str(home / "hooks" / "x_guard.py"), session="s2"))
        check("positive: hook file -> hook:x_guard", "hook:x_guard" in out, out[:160])
        rc, out = run(pl(str(home / "skills" / "synced" / "bar" / "SKILL.md"), session="s3"))
        check("negative: skills/synced excluded", out == "", out[:120])
        rc, out = run(pl(str(home / "ops" / "lessons" / "L-001.md"), session="s3"))
        check("negative: ops/lessons excluded", out == "", out[:120])
        rc, out = run(pl(str(Path(td) / "elsewhere" / "SKILL.md"), session="s3"))
        check("negative: path outside home", out == "", out[:120])
        rc, out = run(pl(skill, session="s4", agent_id="a1"))
        check("negative: subagent", out == "", out[:120])
        # ledger already has a row for the target -> pass-ledger, silent
        (home / "projects" / "p" / "s5.ledger.jsonl").write_text(
            json.dumps({"ts": 1, "kind": "feedback", "target": "skill:foo", "symptom": "x", "action": "left"}) + "\n", encoding="utf-8")
        t5 = home / "projects" / "p" / "s5.jsonl"; t5.write_text("{}\n", encoding="utf-8")
        rc, out = run(dict(pl(skill, session="s5"), transcript_path=str(t5)))
        check("negative: ledger has a feedback row for the target -> silent", out == "", out[:120])
        rc, out = run(dict(pl(str(home / "skills" / "other" / "SKILL.md"), session="s5"), transcript_path=str(t5)))
        check("positive: same session, different target -> notice", "skill:other" in out, out[:160])
        r = subprocess.run([sys.executable, __file__], input="not json", capture_output=True, text=True, env=env, encoding="utf-8")
        check("fail-open: garbage stdin -> exit 0, silent", r.returncode == 0 and r.stdout == "", r.stdout[:80])
        rows = [json.loads(l) for l in (Path(td) / "log.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        kinds = sorted({r["decision"] for r in rows})
        check("telemetry: notice and pass-ledger rows written, no error rows", kinds == ["notice", "pass-ledger"], str(kinds))

        # AP-62: input matching no decision class lands in the declared `error` row -- unclassifiable,
        # never folded into skip/notice and never str()-ed into a session of its own
        n0 = len(rows)
        rc, out = run(dict(pl(skill, session="s6"), tool_input=["not", "a", "mapping"]))
        rows = [json.loads(l) for l in (Path(td) / "log.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        got = (rc, out, len(rows) - n0, rows[-1].get("decision"))
        check("unclassifiable: non-mapping tool_input -> exit 0, silent, one error row", got == (0, "", 1, "error"), str(got))
        rc, out = run(pl(skill, session={"a": 1}))
        rows = [json.loads(l) for l in (Path(td) / "log.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        states = sorted(p.name for p in (Path(td) / "state").glob("*.json"))
        got = (rc, out, rows[-1].get("decision"), rows[-1].get("session"), any("a" in s and "1" in s for s in states))
        check("unclassifiable: non-string session_id -> silent, error row with session None, no state file",
              got == (0, "", "error", None, False), str(got))

    n_ok = sum(1 for _, ok in results if ok)
    print(f"{'ALL PASS' if n_ok == len(results) else 'FAIL'} {n_ok}/{len(results)}")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    main()
