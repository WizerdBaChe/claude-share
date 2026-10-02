"""Positive/negative controls for the compaction pipeline hooks, in an isolated CLAUDE_CONFIG_DIR."""
import json, os, subprocess, sys, tempfile, time
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[2] / "hooks"
PY = sys.executable
tmp = Path(tempfile.mkdtemp(prefix="cc-hook-ctl-"))
(tmp / "telemetry").mkdir(); (tmp / "cache").mkdir()
# This suite owns its sandbox (CLAUDE_CONFIG_DIR) and asserts on telemetry written INSIDE it.
# An inherited CLAUDE_TELEMETRY_DIR (tools/hook-proof-of-life/pol.py sets one to isolate suites
# that do not) redirects the hooks' writes elsewhere and every such assertion then crashes --
# measured 2026-09-19: passes alone, FileNotFoundError under pol.py since a5a8741.
os.environ.pop("CLAUDE_TELEMETRY_DIR", None)
env = dict(os.environ, CLAUDE_CONFIG_DIR=str(tmp), CONTEXT_RUNWAY_LOG=str(tmp / "telemetry" / "runway.jsonl"))
SESSION = "ctl-session-0001"
snap = tmp / "cache" / "handoff" / f"{SESSION}.md"

# Fixture clock. The transcript timestamps must sit near the compaction row's
# ts, which the hook stamps with time.time() AT RUN TIME -- audit.find_summary
# only accepts a summary at or after (compaction ts - 120 s). Hard-coded
# "2026-09-05T10:05:00Z" therefore passed on the day it was written and has been
# failing silently ever since: by 2026-09-08 the fixture summary was three days
# older than the compaction it was supposed to follow, so C1 read 0/2 and the
# suite (which then exited 0 regardless) never said so. Same defect class as
# AP-45: the control's predicate was a POSITION in something that moves.
def _ts(offset_min=0):
    return time.strftime("%Y-%m-%dT%H:%M:%S",
                         time.gmtime(time.time() + offset_min * 60)) + ".000Z"


def rec_assistant(total, tool=None, path=None, ts=None):
    ts = ts or _ts()
    content = [{"type": "text", "text": "working"}]
    if tool:
        content.append({"type": "tool_use", "name": tool, "input": {"file_path": path, "content": "x"}})
    return {"type": "assistant", "timestamp": ts, "sessionId": SESSION, "message": {"id": f"m{total}", "role": "assistant", "model": "claude-opus-5",
            "content": content, "usage": {"input_tokens": 10, "cache_read_input_tokens": total - 10, "cache_creation_input_tokens": 0, "output_tokens": 50}}}

def rec_user(txt, ts=None, summary=False):
    ts = ts or _ts()
    r = {"type": "user", "timestamp": ts, "sessionId": SESSION, "message": {"role": "user", "content": txt}}
    if summary: r["isCompactSummary"] = True
    return r

_n=[0]
def write_transcript(recs):
    _n[0]+=1; p = tmp / f"t{_n[0]}.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
    return p

def run(hook, payload):
    r = subprocess.run([PY, str(HOOKS / hook)], input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=120)
    return r.stdout.strip(), r.returncode

results = []
def check(name, cond, detail=""):
    results.append((name, cond)); print(("PASS " if cond else "FAIL ") + name + ("  " + detail if detail else ""))

# --- runway: 160k, no snapshot -> silent (shadow) but row logged with noticed False
t = write_transcript([rec_user("start"), rec_assistant(160_000)])
out, _ = run("context_runway_shadow.py", {"session_id": SESSION, "transcript_path": str(t), "cwd": "x"})
rows = [json.loads(l) for l in (tmp / "telemetry" / "runway.jsonl").read_text().splitlines()]
check("runway 160k: canary injection only (D3 amended 2026-09-05), no snapshot notice", "[canary]" in out and "[handoff-snapshot]" not in out, out[:80])
check("runway 160k shadow: row noticed=False, canary=True", rows and rows[-1]["noticed"] is False and rows[-1]["band"] == 150_000 and rows[-1].get("canary") is True)
_cj = t.with_name(f"{SESSION}.canary.json")
check("runway 160k: canary.json beside the transcript with keep/drop", _cj.is_file() and set(json.loads(_cj.read_text()).keys()) >= {"keep", "drop"})
check("runway: current-session.json written", (tmp / "cache" / "handoff" / "current-session.json").is_file())
# Q1/Q3 (user ruling 2026-09-08): the keep text names carriers only and does NOT carry
# the drop; the drop rides one prompt later as [probe] noise, once; then silence.
_c = json.loads(_cj.read_text())
check("runway 160k: keep text names carriers only, never deliverables/code; drop absent from it",
      "handoff snapshot" in out and "Never put it into deliverables" in out and _c["drop"] not in out and _c.get("drop_pending") is True, out[:120])
out2, _ = run("context_runway_shadow.py", {"session_id": SESSION, "transcript_path": str(t), "cwd": "x"})
check("runway 160k second prompt: the drop token arrives alone as [probe] noise (no keep re-plant)",
      out2.startswith("[probe] transient") and _c["drop"] in out2 and "[canary]" not in out2 and json.loads(_cj.read_text()).get("drop_pending") is False, out2[:80])
out3, _ = run("context_runway_shadow.py", {"session_id": SESSION, "transcript_path": str(t), "cwd": "x"})
check("runway 160k third prompt: silent (canary once, drop once)", out3 == "", out3[:80])
# Q4: a session governed by a live [unattended-run] manifest is NOT given a second pair
S4 = "ctl-session-0004"; _mf = tmp / "cache" / "handoff" / f"{S4}.run.json"; _mf.parent.mkdir(parents=True, exist_ok=True)
_mf.write_text(json.dumps({"slug": "ctl", "canary": {"keep": "run-id: UR-ctl4", "drop": "port 40004 timeout"}, "ended": None}), encoding="utf-8")
t4 = write_transcript([dict(rec_user("start"), sessionId=S4), dict(rec_assistant(160_000), sessionId=S4)])
out4, _ = run("context_runway_shadow.py", {"session_id": S4, "transcript_path": str(t4), "cwd": "x"})
check("runway 160k under a live run manifest: no second canary pair (run id already calibrates)",
      "[canary]" not in out4 and not t4.with_name(f"{S4}.canary.json").is_file(), out4[:80])
_mf.write_text(json.dumps({"slug": "ctl", "canary": {"keep": "run-id: UR-ctl4", "drop": "port 40004 timeout"}, "ended": {"ts": 1, "by": "ctl"}}), encoding="utf-8")
S5 = "ctl-session-0005"
t5 = write_transcript([dict(rec_user("start"), sessionId=S5), dict(rec_assistant(160_000), sessionId=S5)])
(tmp / "cache" / "handoff" / f"{S5}.run.json").write_text(_mf.read_text(), encoding="utf-8")
out5, _ = run("context_runway_shadow.py", {"session_id": S5, "transcript_path": str(t5), "cwd": "x"})
check("runway 160k under an ENDED run manifest: canary planted as usual (positive control for the skip)",
      "[canary]" in out5 and t5.with_name(f"{S5}.canary.json").is_file(), out5[:80])
# --- runway: 320k, no snapshot -> notice
t = write_transcript([rec_user("start"), rec_assistant(160_000), rec_assistant(320_000)])
out, _ = run("context_runway_shadow.py", {"session_id": SESSION, "transcript_path": str(t), "cwd": "x"})
check("runway 320k no snapshot: visible notice", "[handoff-snapshot]" in out and str(snap) in out, out[:100])
# --- runway: fresh snapshot present -> silent (new session id to reset bands)
S2 = "ctl-session-0002"; snap2 = tmp / "cache" / "handoff" / f"{S2}.md"; snap2.parent.mkdir(parents=True, exist_ok=True); snap2.write_text("# snap", encoding="utf-8")
recs = [rec_user("s"), rec_assistant(300_000, "Write", str(snap2)), rec_assistant(330_000)]
for r in recs: r["sessionId"] = S2
for r in recs:
    if r["type"] == "assistant": r["message"]["id"] += S2
t2 = write_transcript(recs)
out, _ = run("context_runway_shadow.py", {"session_id": S2, "transcript_path": str(t2), "cwd": "x"})
check("runway 330k with fresh snapshot (delta 30k): no snapshot notice (canary may print: first crossing of 150k)", "[handoff-snapshot]" not in out, out[:80])
# --- stale snapshot (delta 100k) -> notice
S3 = "ctl-session-0003"; snap3 = tmp / "cache" / "handoff" / f"{S3}.md"; snap3.write_text("# snap", encoding="utf-8")
recs = [rec_user("s"), rec_assistant(250_000, "Write", str(snap3)), rec_assistant(350_000)]
for r in recs: r["sessionId"] = S3
t3 = write_transcript(recs)
out, _ = run("context_runway_shadow.py", {"session_id": S3, "transcript_path": str(t3), "cwd": "x"})
check("runway 350k with stale snapshot (delta 100k): notice", "[handoff-snapshot]" in out)


# --- re-arm: snapshot written at 300k, context now 380k (delta 80k, stale) -> notice again at a 340k/380k band
S4 = "ctl-session-0004"; snap4 = tmp / "cache" / "handoff" / f"{S4}.md"; snap4.write_text("# snap", encoding="utf-8")
recs = [rec_user("s"), rec_assistant(300_000, "Write", str(snap4)), rec_assistant(320_000)]
for r in recs: r["sessionId"] = S4
t4 = write_transcript(recs)
out, _ = run("context_runway_shadow.py", {"session_id": S4, "transcript_path": str(t4), "cwd": "x"})
check("re-arm: 320k with fresh snapshot: no snapshot notice (300k band retired silently; canary may print)", "[handoff-snapshot]" not in out, out[:80])
recs.append(rec_assistant(380_000)); t4 = write_transcript(recs)
out, _ = run("context_runway_shadow.py", {"session_id": S4, "transcript_path": str(t4), "cwd": "x"})
check("re-arm: 380k with stale snapshot (delta 80k): notice again", "[handoff-snapshot]" in out, out[:80])
out, _ = run("context_runway_shadow.py", {"session_id": S4, "transcript_path": str(t4), "cwd": "x"})
check("re-arm: same 380k again: silent (band retired)", out == "", out[:80])

# --- PreCompact deny-once (session 1: no snapshot)
t = write_transcript([rec_user("start"), rec_assistant(160_000), rec_assistant(400_000)])
pc = {"session_id": SESSION, "transcript_path": str(t), "cwd": "x", "hook_event_name": "PreCompact", "trigger": "auto"}
out, _ = run("compact_bookmark.py", pc)
check("PreCompact auto, no snapshot: ALLOW (deny DISABLED after platform control #3)", out == "", out[:120])
check("PreCompact: bookmark written on deny branch", (tmp / "cache" / "compact-recovery" / f"{SESSION}.json").is_file())
out, _ = run("compact_bookmark.py", pc)
check("PreCompact auto, repeat: still silent", out == "", out[:80])
out, _ = run("compact_bookmark.py", dict(pc, trigger="manual"))
check("PreCompact manual, no snapshot: ALLOW", out == "")
pc2 = {"session_id": S2, "transcript_path": str(t2), "cwd": "x", "hook_event_name": "PreCompact", "trigger": "auto"}
out, _ = run("compact_bookmark.py", pc2)
check("PreCompact auto with fresh snapshot: ALLOW", out == "", out[:80])

# --- SessionStart(compact) pointer includes snapshot
snap.write_text("# Handoff\n- project: ctl\n- next: verify", encoding="utf-8")
out, _ = run("compact_pointer.py", {"session_id": SESSION, "transcript_path": str(t), "source": "compact"})
check("pointer card carries snapshot body", "[handoff snapshot]" in out and "next: verify" in out, out[:120])
out, _ = run("compact_pointer.py", {"session_id": S3, "transcript_path": str(t3), "source": "compact"})
check("pointer card without snapshot: degraded line", "none on disk" in out or "[handoff snapshot]" in out)

# --- PostCompact recorder: 5 auto rows -> notice on the 5th
t = write_transcript([rec_user("start"), rec_assistant(100_000, "Write", "D:/proj/a.py"), rec_assistant(200_000, "Edit", "D:/proj/b.md"),
                      rec_assistant(400_000), rec_user("summary text mentions a.py", ts=_ts(5), summary=True),
                      rec_assistant(80_000, ts=_ts(6)), rec_user("你漏了 b.md 的規則", ts=_ts(7))])
outs = []
for i in range(5):
    out, _ = run("compact_loss_record.py", {"session_id": SESSION, "transcript_path": str(t), "cwd": "x", "hook_event_name": "PostCompact", "trigger": "auto"})
    outs.append(out)
log = (tmp / "telemetry" / "compact-loss.jsonl").read_text().splitlines()
check("PostCompact: 5 rows recorded", len(log) == 5)
check("PostCompact: paths_pre captured", '"D:/proj/a.py"' in log[0] and '"D:/proj/b.md"' in log[0])
check("PostCompact: rows 1-4 silent, 5th emits additionalContext", all(o == "" for o in outs[:4]) and "additionalContext" in outs[4], outs[4][:80])

# --- audit tool on the temp telemetry
r = subprocess.run([PY, str(Path(__file__).resolve().parent / "audit.py"), "--out", str(tmp / "reports")], capture_output=True, text=True, env=env, timeout=120)
rep = list((tmp / "reports").glob("*.md"))
check("audit: report written", bool(rep) and "audited 5" in r.stdout, r.stdout[:120] + r.stderr[:200])
if rep:
    body = rep[0].read_text(encoding="utf-8")
    check("audit C1: a.py named, b.md missing (1/2)", "| 1/2 |" in body)
    check("audit M2: correction phrase caught", "你漏了" in body and "M2 使用者更正語句" in body)
log2 = [json.loads(l) for l in (tmp / "telemetry" / "compact-loss.jsonl").read_text().splitlines()]
check("audit: rows marked audited", all(x["audited"] for x in log2))

# --- AP-62: a compaction whose post-side carries no evidence at all -----------
# M1's declared classes are "gate touched before the first write" (True) and "not
# touched" (False) -- the second is a MISLEADING-candidate finding. A compaction with
# no post-compact tool call belongs to neither: there was no first write to be early
# or late for. audit.py already answers None there, and the same holds for T1 (no
# post-compact assistant turn -> no usage to read). The fold is the dangerous one:
# False would put a finding in the report against a session that did nothing wrong,
# and 0k would publish a context measurement nobody took. render() must print them as
# `None` and `?`, never as a number.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit as _audit  # noqa: E402

def _row(recs):
    p = write_transcript(recs)
    return {"session": "ctl-noevidence-01", "trigger": "auto", "ts": time.time(), "cwd": "x",
            "transcript_path": str(p), "paths_pre": [], "snapshot": {"exists": False}}

_blank = _row([rec_user("start"), rec_assistant(100_000), rec_user("summary text", summary=True)])
v_u, p_u = _audit.audit_row(_blank, 8)
check("AP-62: no post-compact tool call -> M1 undetermined (None), not False",
      v_u["summary_found"] is True and v_u["M1_gate_touched_before_first_write"] is None,
      json.dumps({k: v_u[k] for k in ("summary_found", "M1_gate_touched_before_first_write")}))
# Calibration: the same audit on a post-compact Write with no gate touch must say False,
# or "None" above would only mean the check never fires.
_after = _row([rec_user("start"), rec_assistant(100_000), rec_user("summary text", ts=_ts(1), summary=True),
               rec_assistant(120_000, "Write", "D:/proj/late.py", ts=_ts(2))])
v_f, _ = _audit.audit_row(_after, 8)
check("AP-62 calibration: a post-compact Write with no gate touch IS classified (False)",
      v_f["M1_gate_touched_before_first_write"] is False, json.dumps(v_f["M1_gate_touched_before_first_write"]))
check("AP-62: T1 post-compact context undetermined (None), not 0",
      v_u["T1_post_prompt_actual"] is None and v_u["T1_post_first_cache_write"] is None,
      json.dumps([v_u["T1_post_prompt_actual"], v_u["T1_post_first_cache_write"]]))
_rep_u = _audit.render([(v_u, p_u)], tmp / "reports-undet")
_body_u = _rep_u.read_text(encoding="utf-8")
check("AP-62: the report prints the undetermined cells as None / ?, never as a measured number",
      "| None |" in _body_u and "| ? (?) |" in _body_u and "| 0k " not in _body_u, _body_u[:0])

# --- settings.json parses
_sj = Path(__file__).resolve().parents[2] / "settings.json"
if not _sj.is_file():
    print("SKIP settings.json valid JSON (no settings.json beside hooks/)")
else: json.load(open(_sj, encoding="utf-8-sig")); check("settings.json valid JSON", True)  # utf-8-sig: a BOM-prefixed settings.json is still valid to Claude Code (2026-09-06 crash)
failed = [n for n, c in results if not c]
print("\n", len(results) - len(failed), "/", len(results), "passed;  tmp:", tmp)
# Exit code, not just a printed count. Until 2026-09-08 this file ended on the
# print above and returned 0 with cases failing -- a proof-of-life that reports
# success while its own controls are red is the failure it exists to catch
# (PH-11 / AP-63). The names below are the repair site (AP-64), not a symptom.
if failed:
    print("FAILING CONTROLS -- fix the hook each one names, or the control if the")
    print("contract changed; re-run: python tools/compact-loss-audit/hook_controls.py")
    for name in failed:
        print("  FAIL " + name)
sys.exit(1 if failed else 0)
