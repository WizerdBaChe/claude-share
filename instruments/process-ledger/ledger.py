r"""Process ledger — decisions with reasons, written at decision time, beside the transcript.

Irreducible principle (user ruling 2026-09-05, references/long-run-probe-design.md §0):
process data is written at its ORIGIN in distilled form, and every later reader
(post-compaction card, new session, human) reaches it mechanically; no washing
step (summary, truncation, overwrite, cache cleanup) may remove it. Hence:
  * global, not offline-only — any session may `add`; the unattended run is a branch
  * append-only JSONL, one row per decision
  * stored NEXT TO THE TRANSCRIPT under ~/.claude/projects/<proj>/<session>.ledger.jsonl —
    the one tree the daily archive mirror copies (tools/claude-session-transcript-mirror.ps1);
    cache/ and telemetry/ are cleanup targets and therefore NOT durable enough
  * the project's own registers (decisions D-xxx, tickets, phase-log, PIM, work cards)
    remain the primary ledger for project decisions; this file holds what belongs to
    no register: ordering, scope trade-offs, skipped items, failed-control dispositions,
    and user rulings spoken in chat (origin: user) that would otherwise live only in
    the conversation.

  * NOT a wash (boundary, user ruling 2026-09-05): a row that a RESOLUTION DEFECT filed
    into another session's file was never that session's record — it is moved to where
    it belongs, and a correction row naming what moved and why stays in BOTH files. The
    principle protects records from summaries and cleanups, not misfiles from repair.

Subcommands
  add        append one row. Session resolves from --session, else the process's own
             CLAUDE_CODE_SESSION_ID (authoritative; the only concurrency-safe source),
             else cache/handoff/current-run.json (unattended run) WHEN it agrees with
             cache/handoff/current-session.json (written every prompt by the runway hook)
             or the latter is absent, else current-session.json. Both pointer files are
             GLOBAL, so they are a fallback only — see current_session().
  registers  this session's register writes extracted from the transcript (denominator for F6)
  manifest   fill unattended-run manifest fields the user left out (marks filled_by: model)
  show       print the rows
  feedback   append one FEEDBACK row (2026-09-22, feedback-pool design
             references/feedback-pool-design.md §2.1): a subsystem defect noticed
             mid-task — target (closed prefix vocabulary), symptom, the action
             taken (fixed-inline | left | worked-around | planned-work), optional
             proposal. This is the write-at-origin entry of the feedback pool;
             tools/feedback-pool/feedback.py READS these rows, never writes them.
  feedback-fold  append one FOLD row: the outcome of a user-approved review of a
             target (adopted | rejected | deferred + --trigger); it consumes every
             pool event of that target dated before it (design INV-5).

Row: {ts, subject, choice, reason, reversible, origin, register_ref?, quote?, quote_check?, quote_line?}
     origin=user rows always carry quote_check: verified (the --quote is a substring of a
     message the user typed, reminders and tool output excluded) | not-found | no-transcript
     | absent (no --quote). Only `verified` means "the user's own words"; the rest mean
     "recorded as a user ruling by the model" (2026-10-06, outside critique 3a).
Feedback row: {ts, kind: feedback, id, target, symptom, action, proposal?, origin, session}
Fold row:     {ts, kind: feedback-fold, target, outcome, ref, trigger?, session}
Legacy decision rows carry no `kind`.
Severity: none — a recorder; it judges nothing.
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
HANDOFF_DIR = CLAUDE_DIR / "cache" / "handoff"
CURRENT_RUN = HANDOFF_DIR / "current-run.json"
CURRENT_SESSION = HANDOFF_DIR / "current-session.json"
REGISTER_PATTERNS = re.compile(
    r"(-decisions(\.seed)?\.md|-tickets\.md|phase-log\.md|PIM|施工卡|work[-_ ]?card|HANDOFF|00_INDEX|盤點|\.ledger\.jsonl)", re.I)


def _pointer(p: Path) -> str | None:
    try:
        s = json.loads(p.read_text(encoding="utf-8")).get("session")
        return str(s) if s else None
    except Exception:
        return None


UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def _env_session() -> str | None:
    """This process's OWN session id, from the harness environment.

    2026-09-07: the authoritative source, and the only one immune to concurrency.
    Both Bash and PowerShell subprocesses inherit CLAUDE_CODE_SESSION_ID from the
    session that spawned them, so a shell call cannot be captured by a sibling
    session no matter what any shared file says. Shape-checked so a truncated or
    placeholder value falls through to the pointers rather than creating a junk
    ledger path.
    review-when: `env | grep CLAUDE_CODE_SESSION_ID` comes back empty in a shell
    call (harness renamed or dropped it) — the pointer fallback below still works,
    but the concurrency bug returns with it, so re-probe for the new variable.
    """
    v = (os.environ.get("CLAUDE_CODE_SESSION_ID") or "").strip()
    return v if UUID_RE.match(v) else None


HEX_PREFIX_RE = re.compile(r"^[0-9a-f]{4,35}$", re.I)


def _expand_explicit(explicit: str) -> str:
    """Resolve an abbreviated --session id, or refuse it.

    2026-09-19 (L-053 recurrence, SSLD 2026-09-11): the card's own habit line said
    "pass --session explicitly"; an 8-char short id matched no transcript, so
    ledger_path() fell back to cache/handoff/ and filed 3 rows there, silently. A
    hex string shorter than a UUID is now read as a PREFIX: exactly one transcript
    stem starting with it -> expand (and say so); none or several -> exit non-zero.
    A full UUID, or any non-hex id (the controls' synthetic `ctl-*` ids), passes
    through unchanged.
    """
    if UUID_RE.match(explicit) or not HEX_PREFIX_RE.match(explicit):
        return explicit
    stems = sorted({p.stem for p in (CLAUDE_DIR / "projects").glob(f"*/{explicit}*.jsonl")
                    if UUID_RE.match(p.stem)})
    if len(stems) == 1:
        print(f"ledger: --session {explicit} expanded to {stems[0]}", file=sys.stderr)
        return stems[0]
    if not stems:
        sys.exit(f"--session {explicit}: no transcript id starts with it — pass the full id, or omit "
                 "--session (the process's own CLAUDE_CODE_SESSION_ID is authoritative)")
    sys.exit(f"--session {explicit}: ambiguous prefix ({len(stems)} transcripts: "
             f"{', '.join(s[:13] for s in stems[:5])}) — pass the full id")


def current_session(explicit: str | None) -> str:
    if explicit:
        return _expand_explicit(explicit)

    env = _env_session()
    run, cur = _pointer(CURRENT_RUN), _pointer(CURRENT_SESSION)

    # ENV FIRST (2026-09-07). Both pointer files are GLOBAL single files: whichever
    # session prompted last owns current-session.json, so a shell `add` from a
    # concurrent session used to file under a SIBLING. Measured that day: 5 of 8 rows
    # from one session landed in two other sessions' ledgers, across three different
    # project dirs. The 2026-09-05 fix below only reconciled run-vs-session; it could
    # not see this case, because from the pointer's side nothing looks wrong.
    # The README's earlier diagnosis ("the pointer went stale") was wrong: the pointer
    # was FRESH and correct — for somebody else.
    if env:
        if cur and cur != env:
            print(f"ledger: current-session.json names {cur[:8]} but this process is {env[:8]} "
                  "(concurrent session); filing under this process", file=sys.stderr)
        return env

    if run and (cur is None or cur == run):
        return run
    if cur:
        if run:
            print(f"ledger: current-run.json names {run[:8]} but the prompting session is {cur[:8]}; "
                  "filing under the latter (pass --session to override)", file=sys.stderr)
        return cur
    sys.exit("no session id: CLAUDE_CODE_SESSION_ID unset and no pointer in cache/handoff/ — pass --session")


def find_transcript(session: str) -> Path | None:
    try:
        cur = json.loads(CURRENT_SESSION.read_text(encoding="utf-8"))
        if cur.get("session") == session and Path(cur.get("transcript", "")).is_file():
            return Path(cur["transcript"])
    except Exception:
        pass
    for p in (CLAUDE_DIR / "projects").glob(f"*/{session}.jsonl"):
        return p
    return None


def ledger_path(session: str) -> Path:
    t = find_transcript(session)
    if t:
        return t.with_name(f"{session[:64]}.ledger.jsonl")
    # no transcript yet (fresh session, or a controls run): fall back beside the handoff cache
    return HANDOFF_DIR / f"{session[:64]}.ledger.jsonl"


def canary_path(session: str) -> Path | None:
    t = find_transcript(session)
    return t.with_name(f"{session[:64]}.canary.json") if t else None


def read_appendix(session: str):
    p = ledger_path(session)
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def read_canary(session: str) -> dict | None:
    p = canary_path(session)
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p and p.is_file() else None
    except Exception:
        return None


REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
# Text the user QUOTED rather than spoke (L-138 principle; outside feedback 2026-10-06):
# pasted blocks — the harness writes the closing tag WITH its id attribute, so a
# `</\1>` backreference never matches it — and fenced blocks / inline code spans.
PASTED_RE = re.compile(r"<pasted_content\b[^>]*>.*?</pasted_content\b[^>]*>", re.S)
CODE_SPAN_RE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def human_messages(transcript: Path):
    """(line, text) for every message the USER typed in the main loop.

    Kept: type=user records outside a sidechain that are not a compact summary or
    meta record, string content or `text` blocks only. Dropped: tool_result blocks
    (tool output is data, not a ruling), <system-reminder> spans (harness and
    hook injections ride inside user records), and quoted text — <pasted_content>
    blocks, fenced blocks and inline code spans (someone else's words, L-138).
    """
    out = []
    with transcript.open("r", encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            if '"user"' not in line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if (rec.get("type") != "user" or rec.get("isSidechain") or rec.get("isCompactSummary")
                    or rec.get("isMeta")):
                continue
            c = (rec.get("message") or {}).get("content")
            if isinstance(c, str):
                parts = [c]
            elif isinstance(c, list):
                parts = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
            else:
                parts = []
            text = REMINDER_RE.sub(" ", "\n".join(parts))
            text = CODE_SPAN_RE.sub(" ", PASTED_RE.sub(" ", text))
            if text.strip():
                out.append((i, text))
    return out


def quote_check(session: str, quote: str) -> tuple[str, int | None]:
    """verified | not-found | no-transcript — whether `quote` is a substring of a
    message the user typed (whitespace-normalised). Mechanical: the model's own
    paraphrase of a ruling does not pass, which is the point (2026-10-06)."""
    t = find_transcript(session)
    if not t:
        return "no-transcript", None
    q = _norm(quote)
    for line, text in human_messages(t):
        if q and q in _norm(text):
            return "verified", line
    return "not-found", None


def cmd_add(a) -> None:
    session = current_session(a.session)
    row = {"ts": int(time.time()), "subject": a.subject, "choice": a.choice, "reason": a.reason,
           "reversible": a.reversible, "origin": a.origin}
    if a.ref:
        row["register_ref"] = a.ref
    if a.quote is not None:
        row["quote"] = a.quote
    if a.origin == "user":
        # User-origin rows are protected (05-authority §4: changed only via question +
        # evidence), so the claim "the user said this" is checked against the transcript
        # rather than taken from the writer. The row is written whatever the result —
        # persist first, label second; only `verified` counts as the user's own words.
        if a.quote is None:
            row["quote_check"] = "absent"
            print("ledger: --origin user without --quote — row labelled quote_check=absent "
                  "(not mechanically the user's words)", file=sys.stderr)
        else:
            state, line = quote_check(session, a.quote)
            row["quote_check"] = state
            if line:
                row["quote_line"] = line
            if state != "verified":
                print(f"ledger: --quote not found in any user message of this session's transcript "
                      f"(quote_check={state}) — copy the user's words exactly, or log --origin model",
                      file=sys.stderr)
    p = ledger_path(session)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"ledger +1 -> {p} ({len(read_appendix(session))} rows)")


TARGET_PREFIXES = ("hook:", "skill:", "tool:", "rule:", "subsystem:", "lesson:", "project:")
FEEDBACK_ACTIONS = ("fixed-inline", "left", "worked-around", "planned-work")
FOLD_OUTCOMES = ("adopted", "rejected", "deferred")


def check_target(target: str) -> str:
    """A feedback target carries one of the closed prefixes (design INV-9); refuse anything else."""
    t = (target or "").strip()
    if not t.startswith(TARGET_PREFIXES) or len(t) <= t.index(":") + 1:
        sys.exit(f"--target {t!r}: must be <prefix><name> with prefix in {', '.join(TARGET_PREFIXES)} "
                 "(derive one from a path with tools/feedback-pool/feedback.py target-of <path>)")
    return t


def _append(session: str, row: dict) -> Path:
    p = ledger_path(session)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return p


def cmd_feedback(a) -> None:
    import hashlib
    session = current_session(a.session)
    target = check_target(a.target)
    ts = int(time.time())
    row = {"ts": ts, "kind": "feedback",
           "id": hashlib.sha1(f"{ts}|{target}|{session}".encode("utf-8")).hexdigest()[:8],
           "target": target, "symptom": a.symptom.strip(), "action": a.action,
           "origin": a.origin, "session": session}
    if a.proposal:
        row["proposal"] = a.proposal.strip()
    p = _append(session, row)
    print(f"ledger feedback +1 [{row['id']}] {target} ({a.action}) -> {p}")


def cmd_feedback_fold(a) -> None:
    session = current_session(a.session)
    target = check_target(a.target)
    if a.outcome == "deferred" and not (a.trigger or "").strip():
        sys.exit("--outcome deferred needs --trigger \"<the event that reopens it>\" (same rule as the "
                 "DEFERRED advisory status line, rules-usage-dict.md S7)")
    row = {"ts": int(time.time()), "kind": "feedback-fold", "target": target, "outcome": a.outcome,
           "ref": a.ref.strip(), "session": session}
    if a.trigger:
        row["trigger"] = a.trigger.strip()
    p = _append(session, row)
    print(f"ledger feedback-fold +1 {target} ({a.outcome}) -> {p}")


def register_writes(transcript: Path):
    """(line, ts, tool, path, excerpt) for every main-loop Write/Edit to a register."""
    out = []
    with transcript.open("r", encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            if '"tool_use"' not in line or ('"Write"' not in line and '"Edit"' not in line):
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("type") != "assistant" or rec.get("isSidechain"):
                continue
            for b in ((rec.get("message") or {}).get("content") or []):
                if not (isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in ("Write", "Edit")):
                    continue
                inp = b.get("input") or {}
                path = inp.get("file_path", "")
                if not REGISTER_PATTERNS.search(path):
                    continue
                excerpt = (inp.get("new_string") or inp.get("content") or "").strip().splitlines()
                out.append({"line": i, "ts": rec.get("timestamp", ""), "tool": b["name"], "path": path,
                            "excerpt": (excerpt[0] if excerpt else "")[:160]})
    return out


def cmd_registers(a) -> None:
    session = current_session(a.session)
    t = find_transcript(session)
    if not t:
        sys.exit(f"transcript for {session} not found under {CLAUDE_DIR / 'projects'}")
    rows = register_writes(t)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return
    print("| # | line | tool | path | excerpt |\n|---|---|---|---|---|")
    for n, r in enumerate(rows, 1):
        print(f"| {n} | {r['line']} | {r['tool']} | `{r['path']}` | {r['excerpt'].replace('|', '/')} |")
    print(f"\n{len(rows)} register write(s)")


def cmd_manifest(a) -> None:
    """Model-side fill of the fields the user did not type (user ruling: no form-filling)."""
    session = current_session(a.session)
    mp = HANDOFF_DIR / f"{session[:64]}.run.json"
    m = json.loads(mp.read_text(encoding="utf-8"))
    filled = m.setdefault("filled_by", {})
    changed = []
    if a.deliverables:
        m["deliverables"] = [x.strip() for x in a.deliverables.split(",") if x.strip()]
        filled["deliverables"] = "model"; changed.append("deliverables")
    if a.acceptance:
        m["acceptance"] = list(a.acceptance); filled["acceptance"] = "model"; changed.append("acceptance")
    if a.rulings:
        m["rulings"] = list(a.rulings); filled["rulings"] = "model"; changed.append("rulings")
    if a.scope:
        m["scope"] = [x.strip() for x in a.scope.split(",") if x.strip()]
        filled["scope"] = "model"; changed.append("scope")
    mp.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"manifest updated ({', '.join(changed) or 'nothing'}) -> {mp}")


def cmd_show(a) -> None:
    session = current_session(a.session)
    print(f"# {ledger_path(session)}")
    for r in read_appendix(session):
        print(json.dumps(r, ensure_ascii=False))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    p.add_argument("--subject", required=True)
    p.add_argument("--choice", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--reversible", choices=("yes", "no"), required=True)
    p.add_argument("--origin", choices=("model", "user"), required=True)
    p.add_argument("--ref", help="register id this row points at (D-xxx, T-xxx), if any")
    p.add_argument("--quote", help="with --origin user: the user's words copied exactly from their message; "
                                   "checked against the transcript -> quote_check verified|not-found|no-transcript")
    p.add_argument("--session")
    p.set_defaults(fn=cmd_add)
    p = sub.add_parser("registers")
    p.add_argument("--session")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_registers)
    p = sub.add_parser("manifest", help="fill unattended-run fields the user left out (model-derived; the report marks them)")
    p.add_argument("--deliverables", help="comma-separated paths")
    p.add_argument("--acceptance", action="append", help="repeatable: one acceptance item (name a path or a command)")
    p.add_argument("--rulings", action="append", help="repeatable")
    p.add_argument("--scope", help="comma-separated globs (only to NARROW the default cwd/**)")
    p.add_argument("--session")
    p.set_defaults(fn=cmd_manifest)
    p = sub.add_parser("show")
    p.add_argument("--session")
    p.set_defaults(fn=cmd_show)
    p = sub.add_parser("feedback", help="record a subsystem defect noticed mid-task (feedback pool, write-at-origin)")
    p.add_argument("--target", required=True, help="hook:<stem> | skill:<name> | tool:<dir> | rule:<path> | subsystem:<hmi id> | lesson:L-nnn | project:<name>")
    p.add_argument("--symptom", required=True, help="what was wrong, one sentence")
    p.add_argument("--action", choices=FEEDBACK_ACTIONS, required=True,
                   help="fixed-inline: patched on the spot | left: still broken | worked-around | planned-work: this edit IS the task")
    p.add_argument("--proposal", help="the rule/skill/tool adjustment you would propose, if any")
    p.add_argument("--origin", choices=("model", "user"), default="model")
    p.add_argument("--session")
    p.set_defaults(fn=cmd_feedback)
    p = sub.add_parser("feedback-fold", help="close a user-approved review of one target; consumes its pool events")
    p.add_argument("--target", required=True)
    p.add_argument("--outcome", choices=FOLD_OUTCOMES, required=True)
    p.add_argument("--ref", required=True, help="where the outcome landed: commit sha, D-nnn, L-nnn, ticket, or 'no change: <why>'")
    p.add_argument("--trigger", help="required with deferred: the event that reopens the review")
    p.add_argument("--session")
    p.set_defaults(fn=cmd_feedback_fold)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
