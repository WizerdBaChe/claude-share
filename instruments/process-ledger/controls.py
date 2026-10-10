r"""Regression controls for the unattended-run carrier (hook + tools), isolated.

Runs every hook mode and the audit against fabricated transcripts inside a
temporary CLAUDE_CONFIG_DIR, so nothing touches the live ~/.claude. Each case
is a positive control (must fire) or a negative control (must stay silent);
a set where both sides pass identically is an instrument fault (CLAUDE.md
gate rule). Exit code 1 on any failure.

    python tools/unattended-run/controls.py
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
HOOK = ROOT / "hooks" / "unattended_run.py"
PY = sys.executable
# This suite builds its own sandbox per case (CLAUDE_CONFIG_DIR) and asserts on telemetry
# written inside it. An inherited CLAUDE_TELEMETRY_DIR (tools/hook-proof-of-life/pol.py sets
# one) sends the hook's rows elsewhere -- measured 2026-09-19: passes alone, FileNotFoundError
# under pol.py since a5a8741. The sandbox wins.
os.environ.pop("CLAUDE_TELEMETRY_DIR", None)
FAILS = []


def run_hook(mode: str, payload: dict, env: dict) -> str:
    p = subprocess.run([PY, str(HOOK), mode], input=json.dumps(payload), capture_output=True, text=True, env=env, encoding="utf-8")
    return p.stdout.strip()


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  -- ' + detail) if detail and not cond else ''}")
    if not cond:
        FAILS.append(name)


def rec(kind, line_no, **kw):
    base = {"type": kind, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()), "isSidechain": False}
    base.update(kw)
    return base


def assistant(text=None, tool=None, inp=None, model="claude-sonnet-5"):
    content = []
    if text:
        content.append({"type": "text", "text": text})
    if tool:
        content.append({"type": "tool_use", "name": tool, "input": inp or {}})
    return rec("assistant", 0, message={"role": "assistant", "model": model, "content": content,
                                        "usage": {"input_tokens": 1000, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}})


def write_transcript(cfg: Path, session: str, recs) -> Path:
    d = cfg / "projects" / "ctl"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{session}.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    return p


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="ur-ctl-"))
    cfg = tmp / "claude"
    (cfg / "hooks").mkdir(parents=True)
    (cfg / "reports").mkdir()
    proj = tmp / "proj"
    (proj / "src").mkdir(parents=True)
    # The sandbox simulates a session through the POINTER files, so it must not inherit
    # the real session identity of whatever process is running the controls. Dropping it
    # here is the same lesson the 2026-09-07 ledger fix is about: identity must come from
    # the thing being simulated, never from ambient state. (Without this, every ledger
    # case files under the live session id and the isolated tree never sees the row.)
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(cfg), LOCALAPPDATA=str(tmp / "lad"))   # scratchpad root under the sandbox
    env.pop("CLAUDE_CODE_SESSION_ID", None)
    S = "ctl-session-0001"
    prompt = ("[unattended-run]\nscope: src/**, docs/*.md\ndeliverables: docs/OUT.md\n"
              "acceptance: docs/OUT.md exists\nrulings: never edit README.md\nbudget: 1h\nstop: missing input\n"
              'canary: keep="frame-not-帧" drop="port 48123 timeout"\nreport: ledger + evidence\nslug: ctl')

    print("[kickoff]")
    out = run_hook("kickoff", {"session_id": S, "cwd": str(proj), "prompt": "hello, no tag"}, env)
    check("negative: untagged prompt → silent, no manifest", out == "" and not (cfg / "cache/handoff" / f"{S}.run.json").exists())
    out = run_hook("kickoff", {"session_id": S, "cwd": str(proj), "prompt": prompt}, env)
    mp = cfg / "cache/handoff" / f"{S}.run.json"
    check("positive: tagged prompt → manifest + obligations", mp.is_file() and "Obligations" in out, out[:120])
    m = json.loads(mp.read_text(encoding="utf-8"))
    check("parse: scope/deliverables/canary/slug", m["scope"] == ["src/**", "docs/*.md"] and m["deliverables"] == ["docs/OUT.md"]
          and m["canary"] == {"keep": "frame-not-帧", "drop": "port 48123 timeout"} and m["slug"] == "ctl", json.dumps(m["scope"]) + json.dumps(m["canary"]))

    print("[quoted tag is not a tag (2026-10-02 misfire)]")
    S8 = "ctl-session-0008"
    quoted = (
        ("task-notification quoting the tag",
         "<task-notification>\n<task-id>a1</task-id>\n<status>completed</status>\n<summary>Review done. Note: "
         "`[unattended-run]` is a prompt tag the kickoff hook keys on; the design should name it.</summary>\n</task-notification>"),
        ("inline code span in the user's own text", "請看一下 `[unattended-run]` 這個標籤的 hook 行為，先不要啟動"),
        ("fenced block in the user's own text", "這段是引用：\n```\n[unattended-run]\nscope: src/**\n```\n先別跑，只評估。"),
        ("pasted block (closing tag carries an id, 2026-10-06 probe)",
         "看看這段 <pasted_content id=\"ab12\">他們用 [unattended-run] 跑整晚</pasted_content id=\"ab12\"> 你覺得呢"),
    )
    for name, p in quoted:
        out = run_hook("kickoff", {"session_id": S8, "cwd": str(proj), "prompt": p}, env)
        check(f"negative: {name} → no manifest, silent", out == "" and not (cfg / "cache/handoff" / f"{S8}.run.json").exists(), out[:120])
    S9 = "ctl-session-0009"
    out = run_hook("kickoff", {"session_id": S9, "cwd": str(proj), "prompt":
                   "參考 <pasted_content id=\"cd34\">他們用 [unattended-run] 跑整晚</pasted_content id=\"cd34\">\n[unattended-run]\nscope: src/**\nslug: ctl9"}, env)
    m9p = cfg / "cache/handoff" / f"{S9}.run.json"
    check("positive: a tag spoken AFTER a pasted block still arms, template parsed from the spoken tag",
          m9p.is_file() and json.loads(m9p.read_text(encoding="utf-8")).get("slug") == "ctl9", out[:120])
    out = run_hook("kickoff", {"session_id": S8, "cwd": str(proj), "prompt": "先引用：`[unattended-run]` 是標籤。\n[unattended-run]\nscope: src/**\nslug: ctl8"}, env)
    m8p = cfg / "cache/handoff" / f"{S8}.run.json"
    check("positive: the same tag spoken outside a code span still arms (slug parsed from the spoken block)",
          m8p.is_file() and "Obligations" in out and json.loads(m8p.read_text(encoding="utf-8")).get("slug") == "ctl8", out[:120])

    print("[minimal template]")
    S2 = "ctl-session-0002"
    out = run_hook("kickoff", {"session_id": S2, "cwd": str(proj), "prompt": "請把 W7 證據表整理成簡報 [unattended-run] 回來再看"}, env)
    m2 = json.loads((cfg / "cache/handoff" / f"{S2}.run.json").read_text(encoding="utf-8"))
    check("tag-only prompt → scope defaults to cwd/**, auto canary, project slug, fill obligation injected",
          m2["scope"] == [str(proj).replace("\\", "/") + "/**"] and m2["canary"]["keep"].startswith("run-id: UR-")
          and m2["slug"].startswith("proj-") and "0. Fill the manifest FIRST" in out and not m2["filled_by"], json.dumps(m2["scope"]) + m2["slug"] + json.dumps(m2["filled_by"]))
    check("tag-only: write inside project allowed, outside denied",
          '"deny"' not in run_hook("scope", {"session_id": S2, "cwd": str(proj), "tool_input": {"file_path": str(proj / "deep" / "x.md")}}, env)
          and '"deny"' in run_hook("scope", {"session_id": S2, "cwd": str(proj), "tool_input": {"file_path": str(tmp / "elsewhere.md")}}, env))
    r = subprocess.run([PY, str(HERE / "ledger.py"), "manifest", "--session", S2, "--deliverables", "docs/A.md, docs/B.md", "--acceptance", "docs/A.md exists", "--acceptance", "gate passes", "--rulings", "no README edits"],
                       capture_output=True, text=True, env=env, encoding="utf-8")
    m2 = json.loads((cfg / "cache/handoff" / f"{S2}.run.json").read_text(encoding="utf-8"))
    check("ledger.py manifest fills model-derived fields and marks provenance",
          r.returncode == 0 and m2["deliverables"] == ["docs/A.md", "docs/B.md"] and len(m2["acceptance"]) == 2
          and m2["filled_by"] == {"deliverables": "model", "acceptance": "model", "rulings": "model"}, r.stdout + r.stderr + json.dumps(m2.get("filled_by")))
    # re-arm the main control manifest (S) so the rest of the suite is unaffected
    run_hook("kickoff", {"session_id": S, "cwd": str(proj), "prompt": prompt}, env)

    print("[scope guard]")
    def deny(path):
        o = run_hook("scope", {"session_id": S, "cwd": str(proj), "tool_name": "Write", "tool_input": {"file_path": path}}, env)
        return '"deny"' in o
    check("positive: write outside scope denied", deny(str(proj / "README.md")))
    check("negative: write inside glob allowed", not deny(str(proj / "src" / "a" / "b.py")))
    check("negative: deliverable allowed", not deny(str(proj / "docs" / "OUT.md")))
    check("negative: carrier cache/handoff allowed", not deny(str(cfg / "cache" / "handoff" / "x.md")))
    check("negative: reports carrier allowed", not deny(str(cfg / "reports" / "r.md")))
    check("negative: no manifest → silent", '"deny"' not in run_hook("scope", {"session_id": "other", "cwd": str(proj), "tool_input": {"file_path": str(proj / "README.md")}}, env))

    print("[stop guard]")
    t = write_transcript(cfg, S, [assistant("Done. Should I also update the README?")])
    o = run_hook("stop", {"session_id": S, "transcript_path": str(t), "stop_hook_active": False}, env)
    check("positive: question ending + no report → block", '"block"' in o and "question" in o and "run report" in o, o[:160])
    (cfg / "reports" / "2026-09-05-run-ctl.md").write_text("# report\nblockers: none\n", encoding="utf-8")
    t = write_transcript(cfg, S, [assistant("Report at reports/2026-09-05-run-ctl.md. Blocked on: user must run Ollama locally.")])
    o = run_hook("stop", {"session_id": S, "transcript_path": str(t), "stop_hook_active": True}, env)
    check("negative: named blocker + report → allowed", o == "", o[:120])
    t = write_transcript(cfg, S, [assistant("要我繼續嗎？")])
    o1 = run_hook("stop", {"session_id": S, "transcript_path": str(t), "stop_hook_active": True}, env)
    o2 = run_hook("stop", {"session_id": S, "transcript_path": str(t), "stop_hook_active": True}, env)
    check("bound: second block fires, third is allowed", '"block"' in o1 and o2 == "", f"{o1[:60]} | {o2[:60]}")
    check("negative: no manifest → never blocks", run_hook("stop", {"session_id": "other", "transcript_path": str(t)}, env) == "")

    print("[ledger + audit]")
    sub = lambda *a: subprocess.run([PY, *a], capture_output=True, text=True, env=env, encoding="utf-8")
    # The allowed stop above dropped the pointer and a block never re-creates it
    # (pointer contract 2026-09-06); re-arm so the pointer path is what gets tested.
    run_hook("kickoff", {"session_id": S, "cwd": str(proj), "prompt": prompt}, env)
    r = sub(str(HERE / "ledger.py"), "add", "--subject", "order", "--choice", "A-first", "--reason", "dep", "--reversible", "yes", "--origin", "model")
    check("ledger add uses current-run pointer", r.returncode == 0 and "ledger +1" in r.stdout, r.stdout + r.stderr)
    sub(str(HERE / "ledger.py"), "add", "--subject", "order", "--choice", "B-first", "--reason", "changed mind", "--reversible", "yes", "--origin", "model")
    sub(str(HERE / "ledger.py"), "add", "--subject", "skip-tests", "--choice", "skip", "--reason", "no runner", "--reversible", "yes", "--origin", "model")
    (proj / "docs").mkdir(exist_ok=True)
    # Q2 (2026-09-08): keep is graded on carriers, so the deliverable stays CLEAN and the
    # report fixture carries the token the way report.py stamps it (line 2).
    (proj / "docs" / "OUT.md").write_text("deliverable content, no token\n", encoding="utf-8")
    (cfg / "reports" / "2026-09-05-run-ctl.md").write_text("# report\nframe-not-帧\nblockers: none\n", encoding="utf-8")
    bad = [
        assistant(tool="Read", inp={"file_path": str(proj / "big.md")}),
        assistant(tool="Edit", inp={"file_path": str(proj / "README.md"), "new_string": "D-101 decided"}),
        rec("user", 0, isCompactSummary=True, message={"role": "user", "content": "summary ... constraint frame-not-帧 ... port 48123 timeout ..."}),
        assistant(tool="Read", inp={"file_path": str(proj / "big.md")}),
        assistant("全部完成，已驗證。還要什麼嗎？"),
    ]
    write_transcript(cfg, S, bad)
    r = sub(str(HERE / "run_audit.py"), S, "--json")
    check("run_audit runs", r.returncode == 0, r.stderr[-300:])
    v = json.loads(r.stdout) if r.returncode == 0 else {}
    check("F1 positive: planted re-decision caught (1/2)", v.get("F1", {}).get("hits") == 1 and v["F1"]["denominator"] == 2, json.dumps(v.get("F1")))
    check("F3 positive: README write is drift (1/1)", v.get("F3", {}).get("hits") == 1, json.dumps(v.get("F3")))
    check("F4 positive: full re-read after compaction caught", v.get("F4", {}).get("hits") == 1, json.dumps(v.get("F4")))
    check("F7 positive: question ending detected", v.get("F7", {}).get("ends_with_question") is True, json.dumps(v.get("F7")))
    cm = next((c for c in (v.get("canary") or []) if isinstance(c, dict) and c.get("source") == "manifest"), {})
    check("canary (manifest): keep passes on carriers (summary + report), drop leaks in summary",
          cm.get("keep_pass") is True and set(cm.get("keep_hits", {})) == {"summary#1", "run report"} and "summary#1" in cm.get("drop_leaks", []), json.dumps(v.get("canary")))
    good = [
        assistant(tool="Read", inp={"file_path": str(proj / "big.md")}),
        assistant(tool="Edit", inp={"file_path": str(proj / "src" / "m.py"), "new_string": "x"}),
        rec("user", 0, isCompactSummary=True, message={"role": "user", "content": "summary clean; constraint frame-not-帧 carried"}),
        assistant(tool="Read", inp={"file_path": str(proj / "big.md"), "offset": 1, "limit": 100}),
        assistant("Report at reports/2026-09-05-run-ctl.md. Blocked on: none."),
    ]
    write_transcript(cfg, S, good)
    r = sub(str(HERE / "run_audit.py"), S, "--json")
    g = json.loads(r.stdout) if r.returncode == 0 else {}
    gm = next((c for c in (g.get("canary") or []) if isinstance(c, dict) and c.get("source") == "manifest"), {})
    check("known-good: F3 0, F4 0, F7 no question, drop clean", g.get("F3", {}).get("hits") == 0 and g.get("F4", {}).get("hits") == 0
          and g.get("F7", {}).get("ends_with_question") is False and gm.get("drop_pass") is True, json.dumps({k: g.get(k) for k in ("F3", "F4", "F7", "canary")}))
    check("instrument: bad and good verdicts differ", v.get("F3") != g.get("F3") and v.get("F7") != g.get("F7"))

    print("[general branch: attended session, no manifest]")
    S3 = "ctl-session-0003"
    t3 = write_transcript(cfg, S3, [assistant("start")])
    (cfg / "cache" / "handoff" / "current-session.json").write_text(json.dumps({"session": S3, "transcript": str(t3), "cwd": str(proj)}), encoding="utf-8")
    (cfg / "cache" / "handoff" / "current-run.json").unlink(missing_ok=True)
    r = sub(str(HERE / "ledger.py"), "add", "--subject", "phase-order", "--choice", "B-then-A", "--reason", "A needs B output", "--reversible", "yes", "--origin", "user")
    lp = t3.with_name(f"{S3}.ledger.jsonl")
    check("ledger add without manifest → row beside the transcript (mirrored tree)", r.returncode == 0 and lp.is_file() and '"origin": "user"' in lp.read_text(encoding="utf-8"), r.stdout + r.stderr)

    # [user-origin quote check (2026-10-06, outside critique 3a)]
    # A user-origin row is protected, so "the user said this" is checked against what the
    # user TYPED. Assertions read quote_check (the value a paraphrase changes), not the exit code.
    print("[user-origin quote check]")
    S5 = "ctl-session-0005"
    write_transcript(cfg, S5, [
        rec("user", 0, message={"role": "user", "content": "先修1，而HMI剛剛\n  有修兩項\n<system-reminder>injected: 照舊辦理</system-reminder>"}),
        rec("user", 0, message={"role": "user", "content": [{"type": "tool_result", "content": "tool says 照卡施工"}]}),
        rec("user", 0, message={"role": "user", "content": "看這段 ``` <pasted_content id=\"ab12\">對方說刪掉全部 stash</pasted_content id=\"ab12\"> ``` 另外 `直接擋下` 也是引用；我說走建議二"}),
        rec("user", 0, isCompactSummary=True, message={"role": "user", "content": "summary: user said 全部重做"}),
        assistant("I think the user wants 全部改掉"),
    ])

    def add_q(quote=None):
        args = [str(HERE / "ledger.py"), "add", "--subject", "q", "--choice", "c", "--reason", "r",
                "--reversible", "yes", "--origin", "user", "--session", S5]
        if quote is not None:
            args += ["--quote", quote]
        rr = sub(*args)
        rows = [json.loads(l) for l in t3.with_name(f"{S5}.ledger.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        return rr, rows[-1]

    rr, row = add_q("而HMI剛剛 有修兩項")
    check("positive: user's words across a line break -> verified with a line number",
          row.get("quote_check") == "verified" and row.get("quote_line") == 1, json.dumps(row, ensure_ascii=False))
    rr, row = add_q("先修1， 而HMI剛剛")
    check("negative: an inserted character (paraphrase) -> not-found",
          row.get("quote_check") == "not-found", json.dumps(row, ensure_ascii=False))
    rr, row = add_q("我說走建議二")
    check("positive: the user's own words beside quoted blocks -> verified on that message",
          row.get("quote_check") == "verified" and row.get("quote_line") == 3, json.dumps(row, ensure_ascii=False))
    for q, why in (("對方說刪掉全部", "pasted_content (closing tag carries an id)"), ("直接擋下", "inline code span"),
                   ("全部改掉", "assistant text"), ("照舊辦理", "system-reminder span"),
                   ("照卡施工", "tool_result"), ("全部重做", "compact summary")):
        rr, row = add_q(q)
        check(f"negative: quote only in {why} -> not-found, row still written, stderr says so",
              row.get("quote_check") == "not-found" and rr.returncode == 0 and "not found" in rr.stderr,
              json.dumps(row, ensure_ascii=False) + rr.stderr)
    rr, row = add_q()
    check("negative: no --quote -> quote_check=absent", row.get("quote_check") == "absent" and "absent" in rr.stderr,
          json.dumps(row, ensure_ascii=False))
    rr = sub(str(HERE / "ledger.py"), "add", "--subject", "m", "--choice", "c", "--reason", "r", "--reversible", "yes",
             "--origin", "model", "--session", S5)
    mrow = json.loads(t3.with_name(f"{S5}.ledger.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    check("negative: origin=model rows carry no quote_check", "quote_check" not in mrow, json.dumps(mrow))

    # [concurrency: env identity beats the shared pointer (2026-09-07 fix)]
    # The pointer is a GLOBAL single file rewritten by whichever session prompted last,
    # so on 2026-09-07 five of one session's eight rows landed in two siblings' ledgers.
    # current_session() now prefers this process's own CLAUDE_CODE_SESSION_ID. The pointer
    # here still names S3, so a pass proves the env WON rather than merely agreeing.
    S4 = "68cb6011-aaaa-4bbb-8ccc-ddddeeeeffff"          # valid UUID shape, != pointer
    t4 = write_transcript(cfg, S4, [assistant("start")])
    env4 = dict(env, CLAUDE_CODE_SESSION_ID=S4)
    r4 = subprocess.run([PY, str(HERE / "ledger.py"), "add", "--subject", "concurrency", "--choice", "env-first",
                         "--reason", "pointer belongs to a sibling", "--reversible", "yes", "--origin", "model"],
                        capture_output=True, text=True, env=env4, encoding="utf-8")
    lp4 = t4.with_name(f"{S4}.ledger.jsonl")
    before = lp.read_text(encoding="utf-8") if lp.is_file() else ""
    check("positive: env session id beats a pointer naming a concurrent session",
          r4.returncode == 0 and lp4.is_file() and "env-first" in lp4.read_text(encoding="utf-8")
          and "env-first" not in before, r4.stdout + r4.stderr)
    check("positive: the disagreement is reported, not silent", "concurrent session" in r4.stderr, r4.stderr)

    # Negative control: a malformed value must NOT be trusted — it falls back to the
    # pointer. Without this, any junk in the variable would mint a junk ledger path.
    env5 = dict(env, CLAUDE_CODE_SESSION_ID="not-a-uuid")
    r5 = subprocess.run([PY, str(HERE / "ledger.py"), "add", "--subject", "shape-check", "--choice", "fallback",
                         "--reason", "malformed env value", "--reversible", "yes", "--origin", "model"],
                        capture_output=True, text=True, env=env5, encoding="utf-8")
    junk = list((cfg / "projects").glob("*/not-a-uuid.ledger.jsonl"))
    check("negative: malformed env value falls back to the pointer (no junk path minted)",
          r5.returncode == 0 and lp.is_file() and "fallback" in lp.read_text(encoding="utf-8") and not junk,
          r5.stdout + r5.stderr)
    t3.with_name(f"{S3}.canary.json").write_text(json.dumps({"keep": "UR-beef", "drop": "port 41234 timeout"}), encoding="utf-8")
    write_transcript(cfg, S3, [
        assistant("start"),
        rec("user", 0, isCompactSummary=True, message={"role": "user", "content": "summary: constraint UR-beef on new files; decisions ..."}),
        assistant("下一步要不要先跑 gate？"),
    ])
    r = sub(str(HERE / "run_audit.py"), S3, "--json")
    a3 = json.loads(r.stdout) if r.returncode == 0 else {}
    c3 = next((c for c in (a3.get("canary") or []) if isinstance(c, dict) and c.get("source") == "runway-150k"), {})
    check("attended audit: runway canary keep survives summary, drop clean, calibrated", c3.get("keep_pass") is True and c3.get("drop_pass") is True and c3.get("summarizer_calibrated") is True, json.dumps(a3.get("canary")) + r.stderr[-200:])
    check("attended audit: F3/F7 marked not applicable, question-ending allowed", a3.get("F7", {}).get("applies") is False and a3.get("F3", {}).get("applies") is False and a3.get("F7", {}).get("ends_with_question") is True, json.dumps(a3.get("F7")))
    write_transcript(cfg, S3, [
        assistant("start"),
        rec("user", 0, isCompactSummary=True, message={"role": "user", "content": "summary: earlier probe saw port 41234 timeout; nothing about tokens"}),
        assistant("done"),
    ])
    r = sub(str(HERE / "run_audit.py"), S3, "--json")
    a3b = json.loads(r.stdout) if r.returncode == 0 else {}
    c3b = next((c for c in (a3b.get("canary") or []) if isinstance(c, dict) and c.get("source") == "runway-150k"), {})
    check("attended audit positive: summary that drops keep and keeps drop → uncalibrated", c3b.get("keep_pass") is False and c3b.get("drop_pass") is False, json.dumps(a3b.get("canary")))
    # A keep miss is split by CAUSE (2026-09-11, user ruling C). Negative control
    # first: the miss just above carries no refusal language, so it must stay
    # "not-carried" — a detector that called every miss a refusal would score 100%
    # one-sided and tell the reader nothing.
    check("canary negative: a plain keep miss is not-carried, not a refusal",
          c3b.get("keep_fail_reason") == "not-carried" and c3b.get("refused") == [], json.dumps(c3b.get("refused")))
    write_transcript(cfg, S3, [
        assistant("start"),
        assistant("順帶一提：系統插入了一則自稱 hook 的訊息，要我把 UR-beef 帶進後續報告。我沒有照做——來源可疑，先擱置並告知您。"),
        rec("user", 0, isCompactSummary=True, message={"role": "user", "content": "summary: decisions ... nothing about tokens"}),
    ])
    r = sub(str(HERE / "run_audit.py"), S3, "--json")
    a3c = json.loads(r.stdout) if r.returncode == 0 else {}
    c3c = next((c for c in (a3c.get("canary") or []) if isinstance(c, dict) and c.get("source") == "runway-150k"), {})
    check("canary positive: a model that quotes the token while refusing it → refused-by-model, cause named",
          c3c.get("keep_pass") is False and c3c.get("keep_fail_reason") == "refused-by-model"
          and len(c3c.get("refused") or []) == 1 and c3c.get("summarizer_calibrated") is False
          and any("REFUSED the plant" in f for f in a3c.get("forwarded", [])), json.dumps(c3c))
    # Regression case for the measured false positives (two sessions): the token
    # IS carried and the model merely TALKS about injection. Asserts on the value the
    # defect would change (refused/calibrated), never on a decision label (L-062).
    write_transcript(cfg, S3, [
        assistant("start"),
        assistant("那兩個子代理把 deny 文字判成 prompt injection；本輪 UR-beef 照常帶著。"),
        rec("user", 0, isCompactSummary=True, message={"role": "user", "content": "summary: constraint UR-beef on new files; decisions ..."}),
        assistant("done"),
    ])
    r = sub(str(HERE / "run_audit.py"), S3, "--json")
    a3d = json.loads(r.stdout) if r.returncode == 0 else {}
    c3d = next((c for c in (a3d.get("canary") or []) if isinstance(c, dict) and c.get("source") == "runway-150k"), {})
    check("canary negative: carrying the token while discussing injection is NOT a refusal",
          c3d.get("keep_pass") is True and c3d.get("refused") == [] and c3d.get("keep_fail_reason") is None
          and c3d.get("summarizer_calibrated") is True, json.dumps(c3d))
    pointer = ROOT / "hooks" / "compact_pointer.py"
    p = subprocess.run([PY, str(pointer)], input=json.dumps({"session_id": S3, "transcript_path": str(t3)}), capture_output=True, text=True, env=env, encoding="utf-8")
    check("pointer card injects the ledger rows after compaction", "[process ledger]" in p.stdout and "phase-order → B-then-A" in p.stdout, p.stdout[:200] + p.stderr[-200:])

    # [AP-62: a write F3 cannot classify at all]
    # F3's classes are in-scope / drift, and BOTH are read off the manifest. An attended
    # session has no manifest, so a write belongs to neither: `hits` is None, not 0. The
    # fold would be silent and reassuring — "0/1 writes drifted" is what a clean run
    # prints, so a session nobody could grade would report itself compliant. The write is
    # still ENUMERATED in the denominator, which is what makes the None readable as
    # "1 observed, 0 ruled on" rather than "nothing happened".
    write_transcript(cfg, S3, [
        assistant(tool="Edit", inp={"file_path": str(proj / "README.md"), "new_string": "attended edit"}),
        assistant("done"),
    ])
    r = sub(str(HERE / "run_audit.py"), S3, "--json")
    au = json.loads(r.stdout) if r.returncode == 0 else {}
    f3u = au.get("F3") or {}
    check("attended write is UNDETERMINED: hits None (never folded into 0 drift), still counted in the denominator",
          f3u.get("hits") is None and f3u.get("denominator") == 1 and f3u.get("applies") is False
          and "scope unknown" in (f3u.get("note") or ""), json.dumps(f3u) + r.stderr[-200:])
    # The same README write under a manifest scored 1/1 drift above ("F3 positive"), so
    # None here is the third outcome and not a checker that has stopped ruling on anything.
    rr = subprocess.run([PY, str(HERE / "run_audit.py"), S3], capture_output=True, text=True, env=env, encoding="utf-8")
    check("undetermined survives into the rendered report as None/1, not 0/1",
          "F3 scope drift: None/1 writes" in rr.stdout, rr.stdout[:300] + rr.stderr[-200:])
    r = sub(str(HERE / "report.py"), "--force", "--session", S)
    check("report.py writes skeleton with ledger + canary + compactions", r.returncode == 0 and "run-ctl.md" in r.stdout
          and "1b. 過程決策附錄（3 筆）" in Path(r.stdout.strip()).read_text(encoding="utf-8"), r.stdout + r.stderr[-300:])

    print("[run end: the user comes back (2026-09-06)]")
    S4 = "ctl-session-0004"
    run_hook("kickoff", {"session_id": S4, "cwd": str(proj), "prompt": prompt}, env)
    mp4 = cfg / "cache/handoff" / f"{S4}.run.json"
    cur = cfg / "cache/handoff/current-run.json"
    check("kickoff points current-run.json at the run", cur.is_file() and json.loads(cur.read_text(encoding="utf-8")).get("session") == S4)

    def deny4(path):
        return '"deny"' in run_hook("scope", {"session_id": S4, "cwd": str(proj), "tool_name": "Write", "tool_input": {"file_path": path}}, env)
    scratch = tmp / "lad" / "Temp" / "claude" / "proj" / S4 / "scratchpad" / "m1.txt"
    check("negative: session scratchpad allowed while armed", not deny4(str(scratch)))
    cur.unlink()
    check("positive: README still denied while armed", deny4(str(proj / "README.md")))
    check("negative: a deny does not re-create current-run.json", not cur.exists())
    injected = (("task-notification", "<task-notification>\n<task-id>abc</task-id>\n<status>completed</status>\n</task-notification>"),
                ("system-reminder + slash command", "<system-reminder>\nnote\n</system-reminder>\n<command-name>/compact</command-name>\n<command-message>compact</command-message>\n<command-args></command-args>"),
                ("self-closing", "<ide_opened_file path=\"x\"/>"))
    for name, p in injected:
        out = run_hook("kickoff", {"session_id": S4, "cwd": str(proj), "prompt": p}, env)
        m4 = json.loads(mp4.read_text(encoding="utf-8"))
        check(f"negative: harness-injected prompt ({name}) does not end the run", out == "" and not m4.get("ended") and deny4(str(proj / "README.md")), out[:80])
    t4 = write_transcript(cfg, S4, [assistant("要我繼續嗎？")])
    check("positive: while armed, a question ending is still blocked", '"block"' in run_hook("stop", {"session_id": S4, "transcript_path": str(t4), "stop_hook_active": False}, env))
    out = run_hook("kickoff", {"session_id": S4, "cwd": str(proj), "prompt": "我回來了，先看一下狀況。\n<system-reminder>x</system-reminder>"}, env)
    m4 = json.loads(mp4.read_text(encoding="utf-8"))
    check("positive: untagged human prompt ends the run (context line, manifest.ended, file kept)",
          "ENDED" in out and (m4.get("ended") or {}).get("by") == "user-prompt" and mp4.is_file(), out[:100] + json.dumps(m4.get("ended")))
    check("after end: write outside scope allowed", not deny4(str(proj / "README.md")))
    check("after end: question ending no longer blocked", run_hook("stop", {"session_id": S4, "transcript_path": str(t4), "stop_hook_active": False}, env) == "")
    check("after end: a second human prompt is silent (no double end)", run_hook("kickoff", {"session_id": S4, "cwd": str(proj), "prompt": "再問一個"}, env) == "")
    out = run_hook("kickoff", {"session_id": S4, "cwd": str(proj), "prompt": prompt}, env)
    m4 = json.loads(mp4.read_text(encoding="utf-8"))
    check("re-tag re-arms: fresh manifest, pointer back, README denied again",
          "Obligations" in out and not m4.get("ended") and cur.is_file() and json.loads(cur.read_text(encoding="utf-8")).get("session") == S4 and deny4(str(proj / "README.md")))
    check("stop without session_id → silent + stop-nosession telemetry row",
          run_hook("stop", {"transcript_path": str(t4)}, env) == "" and '"stop-nosession"' in (cfg / "telemetry" / "unattended-run.jsonl").read_text(encoding="utf-8"))
    # audit window: what the model wrote after the user's return is not drift
    run_hook("kickoff", {"session_id": S4, "cwd": str(proj), "prompt": "回來了"}, env)
    m4 = json.loads(mp4.read_text(encoding="utf-8"))
    late = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(m4["ended"]["ts"] + 120))
    write_transcript(cfg, S4, [
        assistant(tool="Edit", inp={"file_path": str(proj / "README.md"), "new_string": "x"}),      # inside the run: drift
        rec("assistant", 0, timestamp=late, message={"role": "assistant", "content": [{"type": "tool_use", "name": "Write", "input": {"file_path": str(proj / "LICENSE"), "content": "y"}}], "usage": {}}),
        rec("assistant", 0, timestamp=late, message={"role": "assistant", "content": [{"type": "text", "text": "還要什麼嗎？"}], "usage": {}}),
    ])
    r = sub(str(HERE / "run_audit.py"), S4, "--json")
    v4 = json.loads(r.stdout) if r.returncode == 0 else {}
    check("run_audit window: F3 counts the in-run drift (1/1), not the write after the user's return",
          v4.get("F3", {}).get("hits") == 1 and v4["F3"]["denominator"] == 1 and (v4.get("window") or {}).get("to") == m4["ended"]["ts"]
          and v4["window"]["tool_uses_outside"] == 1, json.dumps({k: v4.get(k) for k in ("F3", "window")}) + r.stderr[-200:])
    check("run_audit window: F7 reads the last in-run message, not the post-return question", v4.get("F7", {}).get("ends_with_question") is False, json.dumps(v4.get("F7")))

    print("[F8 record overhead + canary grading + report drop token (2026-09-06)]")
    S6 = "ctl-session-0006"
    run_hook("kickoff", {"session_id": S6, "cwd": str(proj), "prompt": prompt}, env)
    usage = {"input_tokens": 1000, "cache_read_input_tokens": 100000, "cache_creation_input_tokens": 0, "output_tokens": 200}
    led = {"type": "tool_use", "name": "Bash", "input": {"command": "python tools/process-ledger/ledger.py add --subject s --choice c --reason r --reversible yes --origin model"}}
    rd = {"type": "tool_use", "name": "Read", "input": {"file_path": str(proj / "big.md")}}
    write_transcript(cfg, S6, [
        rec("assistant", 0, requestId="req-solo", message={"role": "assistant", "content": [led], "usage": usage}),
        rec("assistant", 0, requestId="req-bundled", message={"role": "assistant", "content": [dict(led), rd], "usage": usage}),
        rec("assistant", 0, requestId="req-work", message={"role": "assistant", "content": [dict(rd)], "usage": usage}),
        assistant("Report at reports/x. Blocked on: none."),
    ])
    r = sub(str(HERE / "run_audit.py"), S6, "--json")
    v6 = json.loads(r.stdout) if r.returncode == 0 else {}
    f8 = v6.get("F8") or {}
    check("F8 positive: one solo + one bundled record request found, WARN", f8.get("solo_requests") == 1 and f8.get("bundled_requests") == 1
          and f8.get("record_calls") == 2 and f8.get("severity") == "WARN" and f8.get("by_cat", {}).get("ledger") == 2, json.dumps(f8) + r.stderr[-200:])
    check("F8: the solo request's context re-read outweighs its record output (opus ratios)",
          (f8.get("cost", {}).get("opus", {}).get("solo_ctx_pct") or 0) > (f8.get("cost", {}).get("opus", {}).get("record_out_pct") or 0), json.dumps(f8.get("cost")))
    write_transcript(cfg, S6, [rec("assistant", 0, requestId="req-a", message={"role": "assistant", "content": [dict(rd)], "usage": usage}), assistant("done")])
    r = sub(str(HERE / "run_audit.py"), S6, "--json")
    f8n = (json.loads(r.stdout) if r.returncode == 0 else {}).get("F8") or {}
    check("F8 negative: no record calls → solo 0, ok", f8n.get("solo_requests") == 0 and f8n.get("record_calls") == 0 and f8n.get("severity") == "ok", json.dumps(f8n))
    # canary (Q1–Q4, user ruling 2026-09-08): keep is graded on CARRIERS (summaries,
    # snapshot, report) and never on deliverables; report.py stamps itself; the drop
    # token rides apart from the obligations block; a re-tag keeps the run id.
    S7 = "ctl-session-0007"
    k7 = run_hook("kickoff", {"session_id": S7, "cwd": str(proj), "prompt": "[unattended-run]\ndeliverables: docs/OUT.md, src\nslug: ctl7\ncanary: keep=\"KEEP-7\" drop=\"port 47777 timeout\""}, env)
    check("kickoff: obligations never ask for a token in deliverables; drop rides as a separate [probe] line",
          "NEVER stamp it into deliverables" in k7 and "[probe] transient" in k7 and "port 47777 timeout" not in k7.split("[probe]")[0], k7[-300:])
    (proj / "docs" / "OUT.md").write_text("deliverable content, no token\n", encoding="utf-8")
    write_transcript(cfg, S7, [assistant("Report at reports/x. Blocked on: none.")])
    r = sub(str(HERE / "report.py"), "--force", "--session", S7)
    rep7 = Path(r.stdout.strip()) if r.returncode == 0 else None
    rep7_txt = rep7.read_text(encoding="utf-8") if rep7 and rep7.is_file() else ""
    check("report.py withholds the drop token", rep7 is not None and rep7.is_file() and "port 47777 timeout" not in rep7_txt, r.stdout + r.stderr[-200:])
    check("report.py stamps keep on line 2 and does not grade deliverables", rep7_txt.splitlines()[1:2] == ["KEEP-7"] and "not deliverables" in rep7_txt, rep7_txt[:300])
    r = sub(str(HERE / "run_audit.py"), S7, "--json")
    c7 = next((c for c in ((json.loads(r.stdout) if r.returncode == 0 else {}).get("canary") or []) if c.get("source") == "manifest"), {})
    check("canary negative: clean deliverables, stamped report → keep_pass on the carrier alone, report clean",
          c7.get("keep_pass") is True and set(c7.get("keep_hits", {})) == {"run report"} and "run report" not in c7.get("drop_leaks", []), json.dumps(c7) + r.stderr[-200:])
    snap7 = cfg / "cache" / "handoff" / f"{S7}.md"
    snap7.write_text("# handoff snapshot without the token\n", encoding="utf-8")
    r = sub(str(HERE / "run_audit.py"), S7, "--json")
    c7s = next((c for c in ((json.loads(r.stdout) if r.returncode == 0 else {}).get("canary") or []) if c.get("source") == "manifest"), {})
    check("canary positive: a snapshot that dropped the token fails keep", c7s.get("keep_pass") is False and c7s.get("keep_hits", {}).get("handoff snapshot") is False, json.dumps(c7s.get("keep_hits")))
    snap7.unlink()
    rep7.write_text(rep7_txt + "\nport 47777 timeout\n", encoding="utf-8")
    r = sub(str(HERE / "run_audit.py"), S7, "--json")
    c7b = next((c for c in ((json.loads(r.stdout) if r.returncode == 0 else {}).get("canary") or []) if c.get("source") == "manifest"), {})
    check("canary positive: a report that carries the drop token is a leak", "run report" in c7b.get("drop_leaks", []), json.dumps(c7b.get("drop_leaks")))
    k7b = run_hook("kickoff", {"session_id": S7, "cwd": str(proj), "prompt": "[unattended-run]\nscope: docs/**, src/**\ndeliverables: docs/OUT.md, docs/NOPE.md\nslug: ctl7"}, env)
    m7b = json.loads((cfg / "cache" / "handoff" / f"{S7}.run.json").read_text(encoding="utf-8"))
    check("re-tag while live keeps the run id (canary + slug) and does not re-send the drop line",
          m7b.get("canary", {}).get("keep") == "KEEP-7" and m7b.get("slug") == "ctl7" and m7b.get("retagged") == 1 and "[probe]" not in k7b, json.dumps(m7b.get("canary")) + k7b[-120:])
    r = sub(str(HERE / "run_audit.py"), S7, "--json")
    a7c = json.loads(r.stdout) if r.returncode == 0 else {}
    c7c = next((c for c in (a7c.get("canary") or []) if c.get("source") == "manifest"), {})
    check("a missing file deliverable is F3's finding, not the canary's", "NOPE.md" in json.dumps(a7c.get("F3", {}).get("deliverables_missing")) and "NOPE.md" not in json.dumps(c7c.get("keep_hits")), json.dumps(a7c.get("F3", {}).get("deliverables_missing")))

    print("[runway pointer on a first prompt (L-053 candidate a)]")
    S9 = "ctl-session-0009"
    (cfg / "cache" / "handoff" / "current-session.json").write_text(json.dumps({"session": "stale-previous", "ts": 1}), encoding="utf-8")
    p = subprocess.run([PY, str(ROOT / "hooks" / "context_runway_shadow.py")],
                       input=json.dumps({"session_id": S9, "transcript_path": str(cfg / "projects" / "ctl" / f"{S9}.jsonl"), "cwd": str(proj)}),
                       capture_output=True, text=True, env=env, encoding="utf-8")
    cs = json.loads((cfg / "cache" / "handoff" / "current-session.json").read_text(encoding="utf-8"))
    check("positive: first prompt (no transcript on disk yet) still writes current-session.json", p.returncode == 0 and cs.get("session") == S9, json.dumps(cs) + p.stderr[-200:])
    p = subprocess.run([PY, str(ROOT / "hooks" / "context_runway_shadow.py")], input=json.dumps({"session_id": "ctl-none", "cwd": str(proj)}),
                       capture_output=True, text=True, env=env, encoding="utf-8")
    cs = json.loads((cfg / "cache" / "handoff" / "current-session.json").read_text(encoding="utf-8"))
    check("negative: a payload without transcript_path leaves the pointer alone", cs.get("session") == S9, json.dumps(cs))

    print("[--session short id (L-053 recurrence 2026-09-11)]")
    SA = "7a1c0e55-1111-4222-8333-444455556666"
    SB = "7a1c0e99-1111-4222-8333-444455556666"
    ta = write_transcript(cfg, SA, [assistant("start")])
    write_transcript(cfg, SB, [assistant("start")])
    def add_as(sid: str, tag: str):
        return sub(str(HERE / "ledger.py"), "add", "--session", sid, "--subject", "short-id", "--choice", tag,
                   "--reason", "prefix resolution", "--reversible", "yes", "--origin", "model")
    r = add_as("7a1c0e55", "unique-prefix")
    la = ta.with_name(f"{SA}.ledger.jsonl")
    check("positive: a unique short prefix expands to the full id and files beside that transcript",
          r.returncode == 0 and la.is_file() and "unique-prefix" in la.read_text(encoding="utf-8") and "expanded" in r.stderr,
          r.stdout + r.stderr)
    r = add_as("7a1c0e", "ambiguous")
    check("positive: an ambiguous prefix is refused, nothing written",
          r.returncode != 0 and "ambiguous" in r.stderr and not list((cfg / "cache" / "handoff").glob("7a1c0e*.ledger.jsonl")),
          r.stdout + r.stderr)
    r = add_as("deadbeef", "no-match")
    check("positive: a prefix matching no transcript is refused (the 2026-09-11 silent handoff-dir fallback)",
          r.returncode != 0 and not (cfg / "cache" / "handoff" / "deadbeef.ledger.jsonl").exists(), r.stdout + r.stderr)
    r = add_as(SA, "full-id")
    check("negative: a full UUID passes through unchanged and silently",
          r.returncode == 0 and "full-id" in la.read_text(encoding="utf-8") and "expanded" not in r.stderr, r.stdout + r.stderr)

    print(f"\n{'ALL PASS' if not FAILS else 'FAILED: ' + ', '.join(FAILS)}  (isolated dir {tmp})")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
