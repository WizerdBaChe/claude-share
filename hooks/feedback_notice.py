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
  SECOND TRIGGER (2026-10-05), matcher "Bash|PowerShell": the command names a script
  listed in tools/feedback-pool/gate-overrides.json AND carries one of its override flags
  (`override_hit`, also the hook-backtest predicate) -> `notice-override`, same ledger and
  once-per-pair rules under the state key `override:<target>`. Why: lab-skill-sync was
  forced through 4 times on 2026-10-04/05 because the tool itself was wrong, and nothing
  reached the pool — overriding a gate is the substitute act for reporting it (§2a P1).
  Whether THIS override is a legitimate exception or a dodge of a wrong check is NOT
  determinable here; the notice asks, it never assumes.

SEVERITY: NOTICE (reader = the model about to write; gate-severity-by-consumer).
Narrowing trigger: over >=30 notices, if >=80% are answered by `planned-work`
rows, restrict to sessions whose cwd is NOT ~/.claude (a ~/.claude session
editing a skill is usually the task). Promotion trigger: none foreseen — the
cost of a missed notice is one unrecorded row, never a wrong write.

Fail-OPEN on every internal error path: exit 0, empty stdout, best-effort
telemetry row `decision: error`.

TELEMETRY: `telemetry/feedback-notice.jsonl` — notice / notice-override /
pass-ledger / error (one row per first qualifying edit or override of a pair). Ordinary skips are not logged.

TEST OVERRIDES (calibration only; Claude Code never sets them): env
FBN_HOME (the ~/.claude root), FBN_STATE_DIR, FBN_LOG. Any of them in
settings/env means the hook has been retargeted — treat as tampering.

FALSE-POSITIVE LOG: none observed as of 2026-09-22 (born today).

Proof-of-life: `python hooks/feedback_notice.py --selftest` (two-sided, temp
dirs, last line `ALL PASS n/n`).
review-when: `feedback.target_of()` changes its vocabulary; ledger.py renames
the `kind` values; the narrowing trigger above fires; gate-overrides.json changes
its schema.
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

SHELL_TOOLS = ("Bash", "PowerShell")
OVERRIDES = HOME / "tools" / "feedback-pool" / "gate-overrides.json"


def load_overrides(path: Path = OVERRIDES) -> list:
    """-> [(script, flag, token_re, flag_re)] from the register; [] when unreadable (fail-open)."""
    try:
        rows = json.loads(path.read_text(encoding="utf-8")).get("overrides") or []
    except Exception:
        return []
    out = []
    for r in rows:
        script = str(r.get("script") or "")
        parts = Path(script).parts
        if len(parts) < 2:
            continue
        token = re.compile(re.escape(parts[-2]) + r"[\\/]+" + re.escape(parts[-1]) + r"(?![\w.])", re.I)
        for flag in r.get("flags") or []:
            out.append((script, flag, token, re.compile(r"(?<![\w-])" + re.escape(flag) + r"(?![\w-])")))
    return out


def override_hit(tool, inp, overrides=None):
    """(tool, input) -> 'override:<target>' when a shell call carries a registered override flag of a
    registered script, else None. One predicate for the hook and for tools/hook-backtest."""
    if tool not in SHELL_TOOLS or not isinstance(inp, dict):
        return None
    cmd = str(inp.get("command") or "")
    if "--" not in cmd:
        return None
    for script, flag, token, flag_re in (load_overrides() if overrides is None else overrides):
        if token.search(cmd) and flag_re.search(cmd):
            target = target_of(str(HOME / script))
            if target:
                return f"override:{target}:{flag}"
    return None


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


def override_text(target: str, flag: str) -> str:
    return (
        f"[feedback-notice] Notice from feedback_notice (a local PreToolUse hook, not command output): this call "
        f"passes `{flag}`, which sets aside a check of `{target}`, one of this machine's own subsystems, and this "
        "session's process ledger has no feedback row for it. If you are overriding because the CHECK IS WRONG "
        "(it misjudged this case), record that now, so a defective gate is not just routed around:\n"
        f"  python -X utf8 tools/process-ledger/ledger.py feedback --target \"{target}\" --symptom \"<what the check "
        "got wrong>\" --action worked-around [--proposal \"<fix>\"]\n"
        "If the check was right to stop you and this case genuinely needs no compliance, nothing to do: the reason "
        "you pass belongs in the tool's own log. Once per session per target."
        + notice_clause("feedback_notice")
    )


def decide(payload: dict) -> tuple:
    """Return (decision, text, target). decision in notice|notice-override|pass-ledger|skip."""
    tool = str(payload.get("tool_name", ""))
    if payload.get("agent_id") or tool not in WRITE_TOOLS + SHELL_TOOLS:
        return "skip", "", ""
    ti = payload.get("tool_input")
    if not isinstance(ti, dict):
        raise TypeError("tool_input is not a mapping")
    flag = ""
    if tool in SHELL_TOOLS:
        hit = override_hit(tool, ti)
        if not hit:
            return "skip", "", ""
        _, _, rest = hit.partition(":")
        target, _, flag = rest.rpartition(":")
        path = ""
    else:
        path = str(ti.get("file_path") or ti.get("notebook_path") or "")
        target = target_of(path) if path else ""
    if not target:
        return "skip", "", ""
    sid = payload.get("session_id")
    if sid is not None and not isinstance(sid, str):   # unclassifiable: never str()-ed into a state name
        raise TypeError("session_id is not a string")
    session = sid or "unknown"
    seen = noticed(session)
    key = f"override:{target}" if flag else target   # an edit notice does not answer an override
    if key in seen:
        return "skip", "", target
    tp = str(payload.get("transcript_path", "") or "")
    transcript = Path(tp) if tp and Path(tp).is_file() else None
    seen.add(key)
    remember(session, seen)
    if ledger_has_target(session, transcript, target):
        return "pass-ledger", "", target
    if flag:
        return "notice-override", override_text(target, flag), target
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
        if decision in ("notice", "notice-override"):
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

        # second trigger: a shell call carrying a registered override flag (2026-10-05)
        (home / "tools" / "feedback-pool" / "gate-overrides.json").write_text(json.dumps({"overrides": [
            {"script": "tools/lab-skill-sync/sync.py", "flags": ["--no-writeback"]}]}), encoding="utf-8")

        def sh(cmd, session, tool="Bash", **kw):
            d = {"tool_name": tool, "session_id": session, "transcript_path": str(transcript),
                 "tool_input": {"command": cmd}}
            d.update(kw)
            return d

        ov = 'cd ~/.claude && python -X utf8 tools/lab-skill-sync/sync.py mark case-library --no-writeback "x"'
        rc, out = run(sh(ov, "o1"))
        check("override positive: registered script + flag -> notice names target and flag",
              rc == 0 and "tool:lab-skill-sync" in out and "--no-writeback" in out and "worked-around" in out, out[:200])
        rc, out = run(sh(ov, "o1"))
        check("override once: same session+target -> silent", out == "", out[:120])
        rc, out = run(sh(r'python C:\Users\x\.claude\tools\lab-skill-sync\sync.py mark t --no-writeback=why', "o2",
                         tool="PowerShell"))
        check("override positive: PowerShell, backslash path, --flag=value", "tool:lab-skill-sync" in out, out[:160])
        rc, out = run(sh("python -X utf8 tools/lab-skill-sync/sync.py mark case-library", "o3"))
        check("override negative: registered script without the flag", out == "", out[:120])
        rc, out = run(sh("python tools/other/sync.py --no-writeback x", "o3"))
        check("override negative: the flag on an unregistered script", out == "", out[:120])
        rc, out = run(sh("python tools/lab-skill-sync/sync.py mark t --no-writeback-dry", "o3"))
        check("override negative: a longer flag sharing the prefix", out == "", out[:120])
        rc, out = run(sh(ov, "o4", agent_id="a1"))
        check("override negative: subagent", out == "", out[:120])
        rc, out = run(dict(sh(ov, "s5"), transcript_path=str(t5)))   # s5 ledger holds only skill:foo
        check("override positive: a feedback row for ANOTHER target does not answer it", "tool:lab-skill-sync" in out, out[:120])
        (home / "projects" / "p" / "o6.ledger.jsonl").write_text(
            json.dumps({"ts": 1, "kind": "feedback", "target": "tool:lab-skill-sync", "symptom": "x",
                        "action": "worked-around"}) + "\n", encoding="utf-8")
        t6 = home / "projects" / "p" / "o6.jsonl"; t6.write_text("{}\n", encoding="utf-8")
        rc, out = run(dict(sh(ov, "o6"), transcript_path=str(t6)))
        check("override negative: ledger already has a feedback row for the target", out == "", out[:120])
        rc, out = run(pl(str(home / "tools" / "lab-skill-sync" / "sync.py"), session="o7"))
        rc2, out2 = run(sh(ov, "o7"))
        check("override: an earlier EDIT notice on the same target does not silence the override notice",
              "tool:lab-skill-sync" in out and "--no-writeback" in out2, (out[:80], out2[:80]))

    # the LIVE register: every row must still point at a real flag of a real, mappable script
    rows = json.loads(OVERRIDES.read_text(encoding="utf-8")).get("overrides") or [] if OVERRIDES.is_file() else []
    check("register: live gate-overrides.json has rows", len(rows) > 0, str(OVERRIDES))
    for r in rows:
        src = HOME / r["script"]
        body = src.read_text(encoding="utf-8", errors="replace") if src.is_file() else ""
        missing = [f for f in r.get("flags") or [] if f not in body]
        check(f"register: {r['script']} exists, maps to a target, carries {r.get('flags')}",
              bool(body) and bool(target_of(str(src))) and not missing, f"missing={missing} target={target_of(str(src))!r}")
    hits = load_overrides()
    check("register: live predicate fires on its own first row",
          bool(hits) and override_hit("Bash", {"command": f"python {rows[0]['script']} {hits[0][1]} x"}) is not None)

    n_ok = sum(1 for _, ok in results if ok)
    print(f"{'ALL PASS' if n_ok == len(results) else 'FAIL'} {n_ok}/{len(results)}")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    main()
