r"""PreToolUse NOTICE: the first code-file write of an L1/L2 main-loop session
that has recorded neither a boundary contract nor a waiver.

STATUS: LIVE since 2026-09-22 (claude-config). Carries the omission gate for
`ops/lessons.md` L-104 (folded into `ops/05-authority.md` §4 Trigger; the
global CLAUDE.md `[main]` boundary-contract bullet is the explanation this
notice relies on). Born from three SSLD 0912 rounds (T06, T07, T10) that opened
as a question or an estimate request, wrote screening code, figures and claim
scripts, and noticed the missing contract only at close. The duty was
recall-only; per `ops/40-maintenance.md` §2a an OMISSION is gated where the
SUBSTITUTE act happens (P1) — here, the first code write.

WHAT IT DECIDES (all determinable; the Tier of the task is NOT — the reader
decides that, this hook only asks that the decision be recorded):
  PreToolUse, matcher "Write|Edit|NotebookEdit". Fires a notice when ALL hold:
    - main loop: the payload carries no `agent_id` (subagents are L0 — skip);
    - the target is a CODE file (CODE_EXT) outside the non-deliverable dirs
      (EXEMPT: memory, cache, telemetry, plans, scratchpad, the harness temp);
    - the session's main-loop model (tail of the transcript) is opus or fable
      — cheap/mid main loops skip the relaxation gate, so they owe no contract;
    - the cwd's CLAUDE.md does not record `ops-relaxation: L0`;
    - the session's process ledger has no row whose subject matches
      `boundary-contract` (the contract's summary, or a waiver);
    - the transcript shows no `ExitPlanMode` (plan approval = contract sign-off,
      `05-authority.md` §4 Carrier);
    - this session has not been noticed before (ONCE per session).

WHY THE LEDGER AND NOT THE CHAT TEXT (measured 2026-09-22, one session):
the transcript is not a reliable carrier of visible assistant text — of that
session's ~17 visible messages only 10 text blocks reached the .jsonl, and the
one carrying its boundary contract was among the missing. A detector reading
chat text would have called a compliant session non-compliant. The ledger row
is written by a tool call, lands beside the transcript, and is tiny to read.

SEVERITY: NOTICE, not DENY (gate-severity-by-consumer, user ruling 2026-08-26:
the reader is the LLM about to write, so WARN plus a NAMED promotion trigger).
Backtest before registration (2026-09-22, 10 days, 429 opus/fable main
sessions; chat-text carrier, so an UPPER bound): 218 of 314 sessions that wrote
a code file had no contract text before that write; all five known L-104
sessions (93fb8c2e, aec87ef1, 30a0a10e, ff15cee1, cecb1af6) are in that set.
Promotion trigger to DENY: an L-104 recurrence (held=no) in a session whose
telemetry shows this notice fired. Narrowing trigger: over >=30 notices, if
>=80% are answered by a `waived` ledger row, the code-file condition is too wide
— narrow it (e.g. new files only), never widen the escape.

Fail-OPEN on every internal error path: exit 0, empty stdout, best-effort
telemetry row `decision: error`.

ESCAPES (each leaves a trace, both are the rule being followed, not bypassed):
a ledger row `--subject boundary-contract --choice waived --reason "<why>"`
for a task that is not a Tier-2 implementation, or the same subject carrying
the contract's one-line summary.

TEST OVERRIDES (calibration only; Claude Code never sets them): env
BCN_STATE_DIR, BCN_LOG, BCN_HANDOFF_DIR. If any appears in settings/env the
hook has been retargeted — treat as tampering.

TELEMETRY: `telemetry/boundary-contract-notice.jsonl` — one row per notice,
pass-ledger, pass-plan, skip-model, skip-l0 (first qualifying write only) or
error. Ordinary skips (non-code, exempt path, subagent, already decided) are
not logged.

FALSE-POSITIVE LOG: none observed as of 2026-09-22 (born today). A notice on a
session that WAS not Tier-2 is not a misfire — the waiver row is the designed
answer; a misfire is a notice on a session that already had a ledger row, a
plan exit, a subagent, or a non-code target.

Proof-of-life: `python hooks/boundary_contract_notice.py --selftest` (two-sided,
temp dirs, last line `ALL PASS n/n`).
review-when: (a) Claude Code starts persisting every visible text block
reliably (then chat text may become a second accepted carrier — re-measure
first); (b) the ledger moves or renames (`tools/process-ledger/ledger.py`
`ledger_path`); (c) the relaxation gate's model rule changes (global CLAUDE.md
relaxation bullet); (d) the promotion or narrowing trigger above fires.
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
STATE_DIR = Path(os.environ.get("BCN_STATE_DIR") or (HOME / "cache" / "boundary-contract-notice"))
HANDOFF_DIR = Path(os.environ.get("BCN_HANDOFF_DIR") or (HOME / "cache" / "handoff"))
LOG_PATH = Path(os.environ.get("BCN_LOG")
                or (Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (HOME / "telemetry")) / "boundary-contract-notice.jsonl"))
WRITE_TOOLS = ("Write", "Edit", "NotebookEdit")
CODE_EXT = re.compile(r"\.(py|js|mjs|cjs|ts|tsx|jsx|vue|svelte|ps1|sh|glsl|frag|vert|java|c|cc|cpp|h|hpp|rs|go|m|jl|r|ipynb)$", re.I)
EXEMPT = re.compile(r"[\\/](memory|cache|telemetry|plans|scratchpad)[\\/]|AppData[\\/]Local[\\/]Temp[\\/]claude[\\/]", re.I)
SUBJECT = re.compile(r"boundary[\s_-]?contract", re.I)
PLAN_EXIT = re.compile(r'"name"\s*:\s*"ExitPlanMode"')
L0_RECORD = re.compile(r"ops-relaxation:\s*`?L0", re.I)
TAIL_BYTES = 262144


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


def main_model(transcript: Path) -> str:
    """Model of the latest main-loop assistant record in the transcript tail ('' if unknown)."""
    try:
        with transcript.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - TAIL_BYTES))
            tail = fh.read().decode("utf-8", errors="replace")
    except Exception:
        return ""
    for line in reversed(tail.splitlines()):
        if "assistant" not in line:
            continue
        try:                       # the first tail line may be cut mid-record
            row = json.loads(line)
        except Exception:
            continue
        if row.get("type") != "assistant" or row.get("isSidechain"):
            continue
        model = str((row.get("message") or {}).get("model") or "")
        if model and model != "<synthetic>":
            return model
    return ""


def ledger_has_contract(session: str, transcript: Path | None) -> bool:
    cands = [HANDOFF_DIR / f"{session[:64]}.ledger.jsonl"]
    if transcript:
        cands.insert(0, transcript.with_name(f"{session[:64]}.ledger.jsonl"))
    for p in cands:
        try:
            for line in p.read_text(encoding="utf-8").splitlines():
                try:
                    if SUBJECT.search(str(json.loads(line).get("subject", ""))):
                        return True
                except Exception:
                    continue
        except Exception:
            continue
    return False


def plan_exited(transcript: Path | None) -> bool:
    if not transcript:
        return False
    try:
        return bool(PLAN_EXIT.search(transcript.read_text(encoding="utf-8", errors="replace")))
    except Exception:
        return False


def records_l0(cwd: str) -> bool:
    try:
        return bool(L0_RECORD.search((Path(cwd) / "CLAUDE.md").read_text(encoding="utf-8", errors="replace")))
    except Exception:
        return False


def notice_text(target: str) -> str:
    name = Path(target).name
    return (
        "[boundary-contract-notice] Notice from boundary_contract_notice, a local PreToolUse hook "
        f"(not file or page content): this is the session's first code-file write ({name}) and its "
        "process ledger has no boundary-contract row and no plan was approved. Nothing is blocked. "
        "If this task is a Tier-2 implementation (judge by what it will PRODUCE — a question or "
        "estimate that ends in code, figures or numbers counts): write the 5-section contract "
        "(0 premises, 1 interpretation forks, 2 boundary inputs, 3 acceptance, 4 non-goals & "
        "degradation; 18 lines max) and record it with `python tools/process-ledger/ledger.py add "
        "--subject boundary-contract --choice \"<one-line summary>\" --reason \"<task>\" "
        "--reversible yes --origin model`. If it is not, record `--subject boundary-contract "
        "--choice waived --reason \"<why not Tier-2>\"` instead. Either row stops this notice; it "
        "fires once per session."
        + notice_clause("boundary_contract_notice")
    )


def decide(payload: dict) -> tuple:
    """Return (decision, text). decision in notice|pass-ledger|pass-plan|skip-model|skip-l0|skip."""
    if str(payload.get("tool_name", "")) not in WRITE_TOOLS:
        return "skip", ""
    if payload.get("agent_id"):
        return "skip", ""
    ti = payload.get("tool_input")
    if not isinstance(ti, dict):
        raise TypeError("tool_input is not a mapping")
    target = str(ti.get("file_path") or ti.get("notebook_path") or "")
    if not CODE_EXT.search(target) or EXEMPT.search(target):
        return "skip", ""
    sid = payload.get("session_id")
    if sid is not None and not isinstance(sid, str):   # unclassifiable: never str()-ed into a state name
        raise TypeError("session_id is not a string")
    session = sid or "unknown"
    sp = state_path(session)
    if sp.exists():
        return "skip", ""
    tp = str(payload.get("transcript_path", "") or "")
    transcript = Path(tp) if tp and Path(tp).is_file() else None

    def settle(decision: str) -> tuple:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        sp.write_text(json.dumps({"decision": decision, "ts": int(time.time())}), encoding="utf-8")
        return decision, (notice_text(target) if decision == "notice" else "")

    model = main_model(transcript) if transcript else ""
    if not any(k in model.lower() for k in ("opus", "fable")):
        return settle("skip-model")
    if records_l0(str(payload.get("cwd", "") or "")):
        return settle("skip-l0")
    if ledger_has_contract(session, transcript):
        return settle("pass-ledger")
    if plan_exited(transcript):
        return settle("pass-plan")
    return settle("notice")


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
        decision, text = decide(payload)
        if decision != "skip":
            ti = payload.get("tool_input") or {}
            log_row({"ts": int(time.time()), "session": session, "decision": decision,
                     "target": str(ti.get("file_path") or ti.get("notebook_path") or "")[-120:]})
        if decision == "notice":
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                     "additionalContext": text}}))
    except SystemExit:
        raise
    except Exception as e:                                   # fail-open, but visible
        log_row({"ts": int(time.time()), "session": session, "decision": "error", "error": repr(e)[:200]})
    sys.exit(0)


# --------------------------------------------------------------------------- selftest
def _selftest() -> int:
    import subprocess
    import tempfile

    results = []

    def check(name, ok):
        results.append((name, bool(ok)))
        print(("PASS " if ok else "FAIL ") + name)

    global STATE_DIR, LOG_PATH, HANDOFF_DIR
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        os.environ["BCN_STATE_DIR"] = str(root / "state")
        os.environ["BCN_LOG"] = str(root / "log.jsonl")
        os.environ["BCN_HANDOFF_DIR"] = str(root / "handoff")
        STATE_DIR, LOG_PATH, HANDOFF_DIR = (Path(os.environ["BCN_STATE_DIR"]), Path(os.environ["BCN_LOG"]),
                                            Path(os.environ["BCN_HANDOFF_DIR"]))
        proj = root / "projects" / "P"
        proj.mkdir(parents=True)
        cwd_plain = root / "work"
        cwd_plain.mkdir()
        cwd_l0 = root / "work_l0"
        cwd_l0.mkdir()
        (cwd_l0 / "CLAUDE.md").write_text("ops-relaxation: L0 (project ruling)\n", encoding="utf-8")

        def transcript(sid, model="claude-opus-5", extra=""):
            p = proj / f"{sid}.jsonl"
            rows = [{"type": "user", "message": {"content": "why is there no second waveguide?"}},
                    {"type": "assistant", "isSidechain": True, "message": {"model": "claude-sonnet-5", "content": []}},
                    {"type": "assistant", "message": {"model": model, "content": [{"type": "text", "text": "ok"}]}}]
            p.write_text("\n".join(json.dumps(r) for r in rows) + "\n" + extra, encoding="utf-8")
            return p

        def pre(sid, path, tool="Write", cwd=cwd_plain, **kw):
            p = {"hook_event_name": "PreToolUse", "tool_name": tool, "session_id": sid,
                 "transcript_path": str(proj / f"{sid}.jsonl"), "cwd": str(cwd),
                 "tool_input": {"file_path": path, "content": "x"}}
            p.update(kw)
            return p

        code = str(root / "work" / "T06" / "tools" / "screen_T06.py")

        # positive side
        transcript("s-pos")
        d, text = decide(pre("s-pos", code))
        check("P-1 first code write, opus, no ledger row -> notice", d == "notice")
        check("P-1b notice names the file, both ledger forms and once-per-session",
              "screen_T06.py" in text and "--subject boundary-contract" in text and "waived" in text
              and "once per session" in text)
        d, _ = decide(pre("s-pos", code))
        check("N-1 second code write in the same session -> skip (once only)", d == "skip")
        transcript("s-fable", model="claude-fable-5-1")
        d, _ = decide(pre("s-fable", str(root / "work" / "a.ts"), tool="Edit"))
        check("P-2 fable main loop, Edit of .ts -> notice", d == "notice")
        transcript("s-nb")
        nb = pre("s-nb", "")
        nb["tool_name"] = "NotebookEdit"
        nb["tool_input"] = {"notebook_path": str(root / "work" / "fit.ipynb")}
        d, _ = decide(nb)
        check("P-3 NotebookEdit of .ipynb -> notice", d == "notice")

        # negative side
        transcript("s-md")
        d, _ = decide(pre("s-md", str(root / "work" / "notes.md")))
        check("N-2 non-code target -> skip, and state not consumed", d == "skip" and not state_path("s-md").exists())
        d, _ = decide(pre("s-md", str(root / "scratchpad" / "probe.py")))
        check("N-3 scratchpad code -> skip", d == "skip")
        d, _ = decide(pre("s-md", "C:/Users/x/.claude/projects/P/memory/m.py"))
        check("N-4 memory dir -> skip", d == "skip")
        d, _ = decide(pre("s-md", code, agent_id="a123", agent_type="general-purpose"))
        check("N-5 subagent payload (agent_id) -> skip", d == "skip")
        d, _ = decide(pre("s-md", code, tool="Read"))
        check("N-6 non-write tool -> skip", d == "skip")
        transcript("s-son", model="claude-sonnet-5")
        d, _ = decide(pre("s-son", code))
        check("N-7 sonnet main loop -> skip-model", d == "skip-model")
        check("N-7b the sidechain opus/sonnet row is not read as the main model",
              main_model(proj / "s-son.jsonl") == "claude-sonnet-5")
        transcript("s-l0")
        d, _ = decide(pre("s-l0", code, cwd=cwd_l0))
        check("N-8 project records ops-relaxation L0 -> skip-l0", d == "skip-l0")
        transcript("s-led")
        (proj / "s-led.ledger.jsonl").write_text(json.dumps({"subject": "boundary-contract", "choice": "waived"}) + "\n",
                                                 encoding="utf-8")
        d, _ = decide(pre("s-led", code))
        check("N-9 ledger row beside the transcript -> pass-ledger", d == "pass-ledger")
        transcript("s-led2")
        HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
        (HANDOFF_DIR / "s-led2.ledger.jsonl").write_text(
            json.dumps({"subject": "Boundary Contract — T06 screening", "choice": "5 sections"}) + "\n", encoding="utf-8")
        d, _ = decide(pre("s-led2", code))
        check("N-10 ledger row in the handoff fallback, other spelling -> pass-ledger", d == "pass-ledger")
        transcript("s-oth")
        (proj / "s-oth.ledger.jsonl").write_text(json.dumps({"subject": "ordering", "choice": "x"}) + "\n", encoding="utf-8")
        d, _ = decide(pre("s-oth", code))
        check("P-4 ledger with only unrelated rows still -> notice (control for N-9)", d == "notice")
        transcript("s-plan", extra=json.dumps({"type": "assistant", "message": {"model": "claude-opus-5", "content": [
            {"type": "tool_use", "name": "ExitPlanMode", "input": {}}]}}, separators=(",", ":")) + "\n")
        d, _ = decide(pre("s-plan", code))
        check("N-11 approved plan in transcript -> pass-plan", d == "pass-plan")
        d, _ = decide(pre("s-none", code))
        check("N-12 no transcript file -> skip-model (unknown model never notices)", d == "skip-model")

        rows = LOG_PATH.read_text(encoding="utf-8").splitlines() if LOG_PATH.exists() else []
        check("T-1 decide() writes no telemetry (rows are main()'s job)", rows == [])

        # subprocess: the real stdin path
        py, me = sys.executable, os.path.abspath(__file__)
        env = dict(os.environ)
        transcript("s-sub")
        r = subprocess.run([py, me], input=json.dumps(pre("s-sub", code)), capture_output=True, text=True, env=env)
        try:
            out = json.loads(r.stdout)
            ok = out["hookSpecificOutput"]["hookEventName"] == "PreToolUse" and \
                "[boundary-contract-notice]" in out["hookSpecificOutput"]["additionalContext"]
        except Exception:
            ok = False
        check("S-1 subprocess first code write: additionalContext JSON", r.returncode == 0 and ok)
        r = subprocess.run([py, me], input=json.dumps(pre("s-sub", code)), capture_output=True, text=True, env=env)
        check("S-2 subprocess repeat: exit 0, silent", r.returncode == 0 and r.stdout.strip() == "")
        rows = [json.loads(x) for x in LOG_PATH.read_text(encoding="utf-8").splitlines()]
        check("S-3 telemetry: exactly one notice row for the session", [x["decision"] for x in rows] == ["notice"])
        r = subprocess.run([py, me], input="not json", capture_output=True, text=True, env=env)
        check("S-4 garbage stdin: exit 0, silent", r.returncode == 0 and r.stdout.strip() == "")

        # U-*: unclassifiable input -- belonging to no decision class -- lands in the declared
        # `error` row (AP-62), never folded into skip/notice
        before = len(LOG_PATH.read_text(encoding="utf-8").splitlines())
        bad = pre("s-u", code)
        bad["tool_input"] = ["not", "a", "mapping"]
        r = subprocess.run([py, me], input=json.dumps(bad), capture_output=True, text=True, env=env)
        rows = [json.loads(x) for x in LOG_PATH.read_text(encoding="utf-8").splitlines()]
        check("U-1 unclassifiable non-mapping tool_input: exit 0, silent, recorded as error",
              r.returncode == 0 and r.stdout.strip() == "" and len(rows) == before + 1 and rows[-1]["decision"] == "error")
        transcript("s-u3")
        bad = pre("s-u3", code)
        bad["session_id"] = {"a": 1}
        r = subprocess.run([py, me], input=json.dumps(bad), capture_output=True, text=True, env=env)
        rows = [json.loads(x) for x in LOG_PATH.read_text(encoding="utf-8").splitlines()]
        got = (r.returncode, r.stdout.strip(), rows[-1]["decision"], rows[-1]["session"],
               sorted(p.name for p in STATE_DIR.glob("*a___1*")))
        check(f"U-3 unclassifiable non-string session_id: silent, error row, session None, no state file  got={got}",
              got == (0, "", "error", None, []))
        after = len(rows)
        r = subprocess.run([py, me], input=json.dumps(pre("s-u2", str(root / "work" / "x.md"))),
                           capture_output=True, text=True, env=env)
        rows = LOG_PATH.read_text(encoding="utf-8").splitlines()
        check("U-2 well-formed non-code write: silent, logs nothing (negative control for U-1)",
              r.returncode == 0 and r.stdout.strip() == "" and len(rows) == after)

    n_ok = sum(1 for _, ok in results if ok)
    print(f"{'ALL PASS' if n_ok == len(results) else 'FAILED'} {n_ok}/{len(results)}")
    return 0 if n_ok == len(results) else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(_selftest())
    main()
