r"""Run audit for an unattended session: F1/F3/F4/F6/F7 + canary, determinable parts only.

Severity: WARN advisory (reader = the user). Every line prints hits / denominator
+ evidence (transcript line numbers); anything the tool cannot determine is
FORWARDED under "forwarded", never scored (CLAUDE.md gate rule). Reached also
via `python tools/compact-loss-audit/audit.py --run <session>`.

  F1 re-decision    appendix rows sharing a subject with >1 distinct choice
                    (register-level re-decision is forwarded: needs a reader)
  F3 scope drift    main-loop Write/Edit paths outside manifest scope ∪
                    deliverables ∪ carriers; deliverables missing on disk
  F4 rework         after each compaction line: full-file Read (no offset/limit)
                    of a path already Read before that compaction
  F6 report fidelity ledger subjects (appendix + register ids D-/T-/INV-) absent
                    from the run report; report sentences claiming 已驗證/verified
                    without a nearby evidence token (path, sha, count, command)
  F7 stop shape     last main-loop assistant text ends with '?'/'？'; run report
                    exists; number of compactions and stop-hook blocks
  canary            keep must hit every deliverable; drop must miss the
                    compaction summaries + the report; a keep miss is split by
                    CAUSE — the model refused the plant vs it was simply not
                    carried (2026-09-11, user ruling C)

Calibration (design §5): known-bad = a short session with a planted F1 pair and
an out-of-scope write (controls.py does this); known-good = a clean control;
identical verdicts on both = instrument fault.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ledger  # noqa: E402

CLAUDE_DIR = ledger.CLAUDE_DIR
HANDOFF_DIR = ledger.HANDOFF_DIR
LOSS_LOG = CLAUDE_DIR / "telemetry" / "compact-loss.jsonl"
RUN_LOG = CLAUDE_DIR / "telemetry" / "unattended-run.jsonl"
CLAIM = re.compile(r"(已驗證|已確認|verified|confirmed|passed|通過)")
EVIDENCE = re.compile(r"([A-Za-z]:[\\/]|/|\.py|\.md|\b[0-9a-f]{7,40}\b|\d+\s*(筆|次|/|%)|`)")


def load(transcript: Path):
    recs = []
    with transcript.open("r", encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            try:
                r = json.loads(line)
            except Exception:
                continue
            r["_line"] = i
            recs.append(r)
    return recs


def main_tool_uses(recs):
    for r in recs:
        if r.get("type") != "assistant" or r.get("isSidechain"):
            continue
        for b in ((r.get("message") or {}).get("content") or []):
            if isinstance(b, dict) and b.get("type") == "tool_use":
                yield r["_line"], b.get("name"), (b.get("input") or {})


def compaction_lines(recs):
    # One compaction leaves two records (a system row carrying compactMetadata and
    # the summary row flagged isCompactSummary); count the summary rows only, and
    # fall back to the metadata rows for transcripts that carry no summary row.
    lines = [r["_line"] for r in recs if r.get("isCompactSummary")]
    return lines or [r["_line"] for r in recs if (r.get("compactMetadata") or {}).get("trigger")]


def refusal_evidence(recs, keep):
    """Assistant text blocks that quote `keep` AND carry a refusal marker.

    Returns [{line, quote}]. Sidechains count: a subagent refusing the plant is the
    same failure. The quote is trimmed to 160 chars — the audit names evidence, it
    does not reproduce transcripts.
    """
    out = []
    if not keep:
        return out
    for r in recs:
        if r.get("type") != "assistant":
            continue
        t = text_of(r)
        if keep not in t:
            continue
        m = REFUSAL.search(t)
        if m:
            s = max(0, m.start() - 60)
            out.append({"line": r["_line"], "quote": t[s:m.start() + 100].replace("\n", " ")})
    return out


def text_of(r):
    c = (r.get("message") or {}).get("content")
    if isinstance(c, str):
        return c
    return "\n".join(b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text")


# A keep miss has two causes that look identical in the carriers: the summarizer
# dropped the token, or the model REFUSED to carry it (it read the plant as a
# prompt injection). Until 2026-09-11 only the first was representable, so the
# second was invisible on every report — a session refused a plant, said so
# to the user, and the audit would still have called it "not carried".
# Determinable part only: an assistant text block that QUOTES the keep token and
# carries a refusal marker in the same block. A refusal that never echoes the token
# cannot be seen from here and is forwarded, not scored (CLAUDE.md gate rule); this
# never flips keep_pass, it only names the cause of a miss.
REFUSAL = re.compile(r"prompt.?injection|注入|冒充|偽裝|來源不明|沒有照做|未照做|不確定是真實|可疑|"
                     r"refus|declin|not a genuine|did not comply|suspicious", re.I)

REC_CMD = re.compile(r"ledger\.py\s+(add|manifest)|process-ledger[/\\]report\.py|run_audit\.py|\.ledger\.jsonl")
REC_PATH = re.compile(r"/cache/handoff/|-session-digest\.md|/telemetry/|\.ledger\.jsonl|-phase-log\.md|-decisions\.md|-tickets\.md|/reports/[^/]*-run-[^/]*\.md$", re.I)
REC_CATS = (("ledger", re.compile(r"ledger\.py\s+add")), ("manifest", re.compile(r"ledger\.py\s+manifest")),
            ("report", re.compile(r"report\.py|/reports/[^/]*-run-", re.I)), ("snapshot", re.compile(r"/cache/handoff/[^/]*\.md$", re.I)),
            ("digest", re.compile(r"-session-digest\.md", re.I)), ("register", re.compile(r"-phase-log\.md|-decisions\.md|-tickets\.md", re.I)))
# Price RATIOS relative to uncached input, per model family (absolute prices and the
# cache-read multipliers: reports/2026-09-06-auto-compact-cost-audit.md — cite, do not re-derive).
COST_WEIGHTS = {"opus": {"in": 1.0, "cr": 0.1, "cw": 1.25, "out": 5.0}, "fable": {"in": 1.0, "cr": 0.025, "cw": 1.25, "out": 5.0}}


def record_category(name, inp) -> str | None:
    """Which record-keeping kind a tool call is, or None for real work."""
    if name in ("Bash", "PowerShell"):
        s = inp.get("command", "")
        if REC_CMD.search(s):
            return next((c for c, rx in REC_CATS if rx.search(s)), "other-record")
        return None
    if name in ("Write", "Edit", "NotebookEdit"):
        p = (inp.get("file_path") or "").replace("\\", "/")
        if REC_PATH.search(p):
            return next((c for c, rx in REC_CATS if rx.search(p)), "other-record")
    return None


def overhead(recs, in_window) -> dict:
    """F8: the cost of keeping records, from the emitted transcript.

    One API request = one assistant `requestId`; its usage is the whole context
    (input + cache read + cache write) plus output. A request whose ONLY tool calls
    are record-keeping is SOLO: the session paid its entire context for the record
    alone — avoidable by issuing the record call in the same message as a real
    tool call. A record call bundled with real work costs only its output tokens.
    Severity: WARN (an LLM reads this) — promotion trigger: a solo share above the
    measured 2026-09-06 baseline (0–5.7% of cost-weighted spend) two audits running.
    """
    reqs = {}
    for r in recs:
        if r.get("type") != "assistant" or r.get("isSidechain") or not in_window(r["_line"]):
            continue
        rid = r.get("requestId") or r.get("uuid")
        msg = r.get("message") or {}
        if rid not in reqs:
            u = msg.get("usage") or {}
            reqs[rid] = {"in": u.get("input_tokens") or 0, "cr": u.get("cache_read_input_tokens") or 0,
                         "cw": u.get("cache_creation_input_tokens") or 0, "out": u.get("output_tokens") or 0, "tools": [], "cats": []}
        for b in msg.get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                reqs[rid]["tools"].append(b.get("name"))
                c = record_category(b.get("name"), b.get("input") or {})
                if c:
                    reqs[rid]["cats"].append(c)
    solo = [x for x in reqs.values() if x["cats"] and len(x["cats"]) == len(x["tools"])]
    bundled = [x for x in reqs.values() if x["cats"] and len(x["cats"]) < len(x["tools"])]
    by_cat = {}
    for x in reqs.values():
        for c in x["cats"]:
            by_cat[c] = by_cat.get(c, 0) + 1

    def cost(u, w, out=True):
        return u["in"] * w["in"] + u["cr"] * w["cr"] + u["cw"] * w["cw"] + (u["out"] * w["out"] if out else 0)
    costs = {}
    for fam, w in COST_WEIGHTS.items():
        total = sum(cost(x, w) for x in reqs.values())
        solo_ctx = sum(cost(x, w, out=False) for x in solo)
        rec_out = sum(x["out"] * w["out"] for x in solo) + sum(x["out"] * w["out"] * len(x["cats"]) / max(len(x["tools"]), 1) for x in bundled)
        costs[fam] = {"total_Meq": round(total / 1e6, 2), "solo_ctx_pct": round(100 * solo_ctx / max(total, 1), 1),
                      "record_out_pct": round(100 * rec_out / max(total, 1), 1), "overhead_pct": round(100 * (solo_ctx + rec_out) / max(total, 1), 1)}
    return {"requests": len(reqs), "record_calls": sum(len(x["cats"]) for x in reqs.values()),
            "solo_requests": len(solo), "bundled_requests": len(bundled), "by_cat": by_cat,
            "solo_avg_context_k": round(sum(x["in"] + x["cr"] + x["cw"] for x in solo) / max(len(solo), 1) / 1e3),
            "solo_out_k": round(sum(x["out"] for x in solo) / 1e3, 1), "cost": costs,
            "severity": "WARN" if solo else "ok",
            "rule": "a solo record request re-reads the whole context for one row: issue the record call in the same message as the next real tool call, chain several rows in one Bash call"}


def audit(session: str, m: dict | None, transcript: Path, report: Path | None) -> dict:
    # The hook module lives beside this tool in the repo, not under CLAUDE_CONFIG_DIR
    # (controls run in an isolated config dir whose hooks/ is empty).
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hooks"))
    import unattended_run as ur  # in_scope, ends_with_question
    recs = load(transcript)
    uses = list(main_tool_uses(recs))
    out = {"session": session, "forwarded": []}

    # Run window (2026-09-06): records before the kickoff and after the user's return
    # (manifest.ended, written by the kickoff hook on the first untagged human prompt)
    # are interactive work, not the run. Every transcript-side metric reads only
    # inside the window; the audit says how much of the file it left out.
    from datetime import datetime

    def ts_of(r):
        try:
            return datetime.fromisoformat(str(r.get("timestamp", "")).replace("Z", "+00:00")).timestamp()
        except Exception:
            return None
    line_ts = {r["_line"]: ts_of(r) for r in recs}
    w_from = (m or {}).get("ts")
    w_to = ((m or {}).get("ended") or {}).get("ts")

    def in_window(line):
        t = line_ts.get(line)
        if t is None or not m:
            return True
        return (w_from is None or t >= w_from - 1) and (w_to is None or t <= w_to + 1)
    if m:
        total = len(uses)
        uses = [u for u in uses if in_window(u[0])]
        out["window"] = {"from": w_from, "to": w_to, "ended_by": ((m or {}).get("ended") or {}).get("by"),
                         "tool_uses_outside": total - len(uses)}

    # F1 (ledger rows outside the run window are interactive work, not the run's decisions)
    app_all = ledger.read_appendix(session)
    app = [r for r in app_all if not m or ((w_from is None or r.get("ts", 0) >= w_from - 1) and (w_to is None or r.get("ts", 0) <= w_to + 1))]
    if m:
        out["window"]["ledger_rows_outside"] = len(app_all) - len(app)
    by_subj = {}
    for r in app:
        by_subj.setdefault(r["subject"], set()).add(r["choice"])
    f1 = [(s, sorted(c)) for s, c in by_subj.items() if len(c) > 1]
    out["F1"] = {"hits": len(f1), "denominator": len(by_subj), "evidence": f1}
    out["forwarded"].append("F1 at register level (D-xxx text changed after compaction) — reader compares register diff")

    # F3
    writes = [(l, i.get("file_path", "")) for l, n, i in uses if n in ("Write", "Edit", "NotebookEdit")]
    if m:
        drift = [(l, p) for l, p in writes if p and not ur.in_scope(p, m)]
        missing = [d for d in m.get("deliverables", []) if not (Path(d) if Path(d).is_absolute() else Path(m.get("cwd", "")) / d).is_file()]
        out["F3"] = {"hits": len(drift), "denominator": len(writes), "evidence": drift[:20], "deliverables_missing": missing}
        out["forwarded"].append("F3 shell-side writes (Bash/PowerShell redirections) — not parsed")
    else:
        out["F3"] = {"hits": None, "denominator": len(writes), "evidence": [], "note": "no manifest → scope unknown"}

    # F4
    comps = compaction_lines(recs)
    f4 = []
    reads = [(l, i.get("file_path", ""), i) for l, n, i in uses if n == "Read"]
    for c in comps:
        before = {p for l, p, _ in reads if l < c}
        for l, p, i in reads:
            if l > c and p in before and not i.get("offset") and not i.get("limit"):
                f4.append((c, l, p))
    out["F4"] = {"hits": len(f4), "denominator": sum(1 for l, p, _ in reads if comps and l > comps[0]), "evidence": f4[:20], "compactions": len(comps)}

    # F6
    rep_txt = report.read_text(encoding="utf-8", errors="replace") if report and report.is_file() else ""
    subjects = [r["subject"] for r in app]
    reg_ids = set()
    for l, n, i in uses:
        if n in ("Write", "Edit") and ledger.REGISTER_PATTERNS.search(i.get("file_path", "")):
            reg_ids |= set(re.findall(r"\b(?:D|T|INV|P)-\d{2,4}\b", (i.get("new_string") or i.get("content") or "")))
    absent = [s for s in subjects if s not in rep_txt] + [x for x in sorted(reg_ids) if x not in rep_txt]
    claims = []
    for sent in re.split(r"(?<=[。.!\n])", rep_txt):
        if CLAIM.search(sent) and not EVIDENCE.search(sent):
            claims.append(sent.strip()[:120])
    out["F6"] = {"absent_from_report": absent, "denominator": len(subjects) + len(reg_ids),
                 "claims_without_evidence": claims[:20], "report": str(report) if report else None}
    out["forwarded"].append("F6 intent-vs-delivery (交辦意圖對交付) — reader only")

    # F7
    last = ""
    for r in reversed(recs):
        if r.get("type") == "assistant" and not r.get("isSidechain") and text_of(r).strip() and in_window(r["_line"]):
            last = text_of(r).strip()
            break
    blocks = 0
    if RUN_LOG.is_file():
        blocks = sum(1 for l in RUN_LOG.read_text(encoding="utf-8").splitlines() if session in l and '"block"' in l)
    out["F7"] = {"ends_with_question": ur.ends_with_question(last), "report_exists": bool(rep_txt),
                 "compactions": len(comps), "stop_blocks": blocks, "tail": last[-200:]}
    if not m:
        out["F7"]["applies"] = False
        out["F7"]["note"] = "attended session: a question-ending is legitimate and no run report is owed — informational only"
        out["F3"]["applies"] = False

    # F8 — what keeping the records cost (2026-09-06, user question: does writing a
    # record at every step burn the heavy main model's budget?)
    out["F8"] = overhead(recs, in_window)
    out["forwarded"].append("F8 record output inside a bundled request is apportioned by call count, not measured")

    # canary — two sources: the unattended-run manifest (keep must hit every
    # deliverable) and the 150k runway plant beside the transcript (keep must
    # survive into every compaction summary). Both: drop must leak nowhere.
    summaries = [text_of(r) for r in recs if r.get("isCompactSummary")]
    snap_txt = ""
    sp = HANDOFF_DIR / f"{session[:64]}.md"
    if sp.is_file():
        snap_txt = sp.read_text(encoding="utf-8", errors="replace")
    sources = []
    if m and (m.get("canary") or {}).get("keep"):
        sources.append(("manifest", m["canary"].get("keep"), m["canary"].get("drop")))
    c150 = ledger.read_canary(session)
    if c150:
        sources.append(("runway-150k", c150.get("keep"), c150.get("drop")))
    if not sources:
        out["canary"] = {"note": "no canary planted (session never crossed 150k and carried no manifest)"}
        out["forwarded"].append("canary: none planted — summarizer uncalibrated for this session")
        return out
    res = []
    for src, keep, drop in sources:
        if src == "manifest":
            # Q2 (user ruling 2026-09-08): keep is graded on the PROCESS CARRIERS —
            # compaction summaries, the handoff snapshot and the run report — never on
            # deliverables. Grading deliverables (until 2026-09-08) stamped run ids into
            # project code, a public README and two claude-share manifests the run had
            # to fail on purpose. Deliverable existence is F3's job, not the canary's.
            keep_hits = {f"summary#{i + 1}": (keep in s) for i, s in enumerate(summaries)}
            if snap_txt:
                keep_hits["handoff snapshot"] = keep in snap_txt
            if rep_txt:
                keep_hits["run report"] = keep in rep_txt
            keep_pass = bool(keep_hits) and all(v is True for v in keep_hits.values())
            keep_note = ("every carrier that exists (summaries, snapshot, report) carries the token; deliverables are not graded"
                         if keep_hits else "no carrier yet (no compaction, snapshot or report) — keep undetermined")
        else:
            keep_hits = {f"summary#{i + 1}": (keep in s) for i, s in enumerate(summaries)}
            keep_pass = bool(keep_hits) and all(keep_hits.values())
            keep_note = "every compaction summary carries the token" if summaries else "no compaction yet — keep undetermined"
        leaks = []
        if drop:
            leaks += [f"summary#{i + 1}" for i, s in enumerate(summaries) if drop in s]
            if drop in rep_txt:
                leaks.append("run report")
            if drop in snap_txt:
                leaks.append("handoff snapshot")
        # Only a MISS needs a cause. Carrying the token is direct disconfirming
        # evidence of refusal, and skipping the scan there removes the measured
        # false-positive class: two of the three sessions the first hand-run of this
        # detector flagged had carried the token and merely
        # discussed injection — of hook deny text, and of a mutant into a gate.
        refused = [] if keep_pass else refusal_evidence(recs, keep)
        if keep_pass:
            why = None
        elif refused:
            why = "refused-by-model"
        elif not keep_hits:
            why = "undetermined — no carrier exists yet"
        else:
            why = "not-carried"
        # A refusal measures the READER, not the summarizer: the token never entered
        # the carriers because the model declined to put it there, so this session
        # says nothing about compaction fidelity either way.
        calibrated = keep_pass and bool(drop) and not leaks and bool(summaries) and not refused
        if refused:
            out["forwarded"].append(
                f"canary ({src}): the model REFUSED the plant at line(s) "
                f"{', '.join(str(e['line']) for e in refused)} — the keep miss is not a summarizer "
                "result, and the plant's wording is the finding to act on, not this session's compliance")
        res.append({"source": src, "keep": keep, "keep_hits": keep_hits, "keep_pass": keep_pass, "keep_rule": keep_note,
                    "keep_fail_reason": why, "refused": refused,
                    "drop": drop, "drop_leaks": leaks, "drop_pass": bool(drop) and not leaks,
                    "summarizer_calibrated": calibrated})
    out["canary"] = res
    return out


def render(v: dict) -> str:
    L = [f"# run audit — {v['session'][:8]}", ""]
    L.append(f"F1 re-decision: {v['F1']['hits']}/{v['F1']['denominator']} subjects  {v['F1']['evidence']}")
    f3 = v["F3"]
    L.append(f"F3 scope drift: {f3['hits']}/{f3['denominator']} writes  {f3.get('evidence')}  deliverables missing: {f3.get('deliverables_missing', 'n/a')}")
    L.append(f"F4 rework after compaction: {v['F4']['hits']}/{v['F4']['denominator']} post-compact reads  (compactions={v['F4']['compactions']})  {v['F4']['evidence'][:5]}")
    f6 = v["F6"]
    L.append(f"F6 report fidelity: absent {len(f6['absent_from_report'])}/{f6['denominator']} {f6['absent_from_report'][:10]}; claims without evidence: {len(f6['claims_without_evidence'])}")
    for c in f6["claims_without_evidence"][:5]:
        L.append(f"    - {c}")
    f7 = v["F7"]
    L.append(f"F7 stop shape: ends_with_question={f7['ends_with_question']} report_exists={f7['report_exists']} compactions={f7['compactions']} stop_blocks={f7['stop_blocks']}")
    f8 = v.get("F8") or {}
    if f8:
        L.append(f"F8 record overhead [{f8['severity']}]: solo {f8['solo_requests']} / bundled {f8['bundled_requests']} of {f8['requests']} requests "
                 f"({f8['record_calls']} record calls {f8['by_cat']}); overhead {f8['cost']['opus']['overhead_pct']}% of cost-weighted spend at opus ratios "
                 f"({f8['cost']['opus']['solo_ctx_pct']}% solo context + {f8['cost']['opus']['record_out_pct']}% record output), {f8['cost']['fable']['overhead_pct']}% at fable ratios; "
                 f"solo requests re-read {f8['solo_avg_context_k']}k context on average")
    if v.get("window"):
        L.append(f"window: {v['window']}")
    L.append(f"canary: {json.dumps(v['canary'], ensure_ascii=False)}")
    L.append("forwarded (not scored): " + " | ".join(v["forwarded"]))
    return "\n".join(L)


def run(session: str) -> dict:
    t = ledger.find_transcript(session)
    if not t:
        sys.exit(f"transcript for {session} not found")
    mp = HANDOFF_DIR / f"{session[:64]}.run.json"
    m = json.loads(mp.read_text(encoding="utf-8")) if mp.is_file() else None
    rep = None
    if m:
        cands = sorted((CLAUDE_DIR / "reports").glob(f"*-run-{m['slug']}.md"))
        rep = cands[-1] if cands else None
    return audit(session, m, t, rep)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session", nargs="?")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    session = ledger.current_session(a.session)
    v = run(session)
    print(json.dumps(v, ensure_ascii=False, indent=1) if a.json else render(v))


if __name__ == "__main__":
    main()
