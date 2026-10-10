r"""Unattended-run carrier: three hook entry points over ONE run manifest.

STATUS: LIVE since 2026-09-05 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).

Design: a long-run probe design note (§3 carriers, §2 F3/F7, extensions
2-3 approved 2026-09-05). Severity: the two guards are FAIL-class (deny / block)
because both rule ONLY on determinable facts; everything else in that design
stays advisory (audit.py --run).

Modes (argv[1]):
  kickoff   UserPromptSubmit. When the prompt carries `[unattended-run]`, parse
            the template into cache/handoff/<session>.run.json (the manifest),
            point cache/handoff/current-run.json at it (so ledger.py needs no
            session id), and inject the run obligations as context. Re-tagging
            in the same session REPLACES the manifest (the user re-scoped) and
            resets counters.
            Without the tag: if this session has an ACTIVE manifest and the
            prompt carries human text (anything left after harness-injected
            `<task-notification>`/`<system-reminder>`/`<local-command-*>`
            blocks are stripped), the user is back — the run ENDS: the manifest
            gets `ended: {ts, by: "user-prompt"}` and stays on disk for
            run_audit, both guards disarm, the pointer is dropped, and one
            context line says so. (2026-09-06: one session stayed armed
            for 2h42m after the user returned and denied a write the user had
            just asked for; the model read the deny as "the mechanism works"
            and routed around it. There was no exit transition at all.)
  scope     PreToolUse Write|Edit|NotebookEdit. With an active manifest, deny a
            write whose path matches neither a scope glob, a deliverable, the
            always-allowed carriers (cache/handoff, reports, telemetry under
            CLAUDE_DIR), nor the session scratchpad under
            %LOCALAPPDATA%/Temp/claude (the system prompt tells the model to
            use it; 2 of the 3 real denies were scratchpad writes). Bash-side
            writes are NOT covered — forwarded to run_audit F3, never guessed.
  stop      Stop. With an active manifest, block the stop (max STOP_BLOCKS
            times per manifest) when the last main-loop assistant text ends
            with a question mark, or the run report the template promised does
            not exist on disk. `stop_hook_active` true + counter exhausted →
            allow, so a broken run can always end. An ALLOWED stop removes
            current-run.json when it names this session (2026-09-05): the
            pointer is global, and a run that kept it after finishing made
            ledger.py file other sessions' rows under it.

Pointer contract (2026-09-06): ONLY kickoff writes current-run.json. Deny and
block update the manifest's counters without touching the pointer — the old
save_manifest re-pointed it on every deny, so a finished run re-claimed the
pointer a day later.

Why one file: the guards are meaningless without the manifest, and the manifest
is meaningless without the guards; splitting them invites one being registered
without the other. Fail-open everywhere: any exception → exit 0, no output.

Not covered (named, forwarded): writes via shell; scope expressed as prose
instead of globs (stored raw, not enforced); a question buried mid-text; a
human prompt that consists ONLY of pasted hyphenated XML (read as harness
noise → the run stays armed one prompt longer).
review-when: Claude Code changes the Stop hook contract (`decision: block`), the
PreToolUse `permissionDecision` shape, or the tag names it injects into prompts.

Telemetry: telemetry/unattended-run.jsonl — kickoff / deny / block / end /
stop-allowed (one per allowed stop while armed) / stop-nosession (a Stop
payload without session_id: 2026-09-06 the real stops after the user's return
did not clear the pointer although isolated replay does; this row is the
production-side evidence the next run will leave).
Proof-of-life: `python tools/process-ledger/controls.py` (positive AND negative
controls). Backticked and prefixed with `python` on purpose: that is the shape
`tools/hook-proof-of-life/pol.py` executes, and this hook is the reason the tool
exists (a missing import made every deny raise NameError, and a crashing hook
fails open, for a day).
"""
import fnmatch
import json
import os
import re
import sys
import time
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
HANDOFF_DIR = CLAUDE_DIR / "cache" / "handoff"
CURRENT = HANDOFF_DIR / "current-run.json"
# CLAUDE_TELEMETRY_DIR redirects the whole telemetry dir (suites use a temp dir;
# production never sets it).
LOG_PATH = Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (CLAUDE_DIR / "telemetry")) / "unattended-run.jsonl"
SCRATCH_ROOT = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")) / "Temp" / "claude"
try:                        # receipt + misfire exit (rules/hook-deny-message.md)
    from deny_receipt import clause as _receipt, fp_clause as _fp
except Exception:           # a guard must not stop guarding if telemetry breaks
    def _receipt(hook, **fields): return ""
    def _fp(hook): return ""

TAG = "[unattended-run]"
STOP_BLOCKS = 2
KEYS = ("scope", "deliverables", "acceptance", "rulings", "budget", "stop", "canary", "report", "slug")
ALWAYS_ALLOWED = ("cache/handoff", "reports", "telemetry")
# Harness-injected blocks: tag names with a hyphen or underscore (task-notification,
# system-reminder, local-command-stdout, command-name, ide_opened_file, ...).
# A human's own text never arrives wrapped in one of these.
HARNESS_BLOCK = re.compile(r"<([a-zA-Z][a-zA-Z0-9]*(?:[-_][a-zA-Z0-9]+)+)(?:\s[^>]*)?>.*?</\1\s*>", re.S)
HARNESS_EMPTY = re.compile(r"<[a-zA-Z][a-zA-Z0-9]*(?:[-_][a-zA-Z0-9]+)+(?:\s[^>]*)?/?>")


# ----------------------------------------------------------------- manifest
def manifest_path(session: str) -> Path:
    return HANDOFF_DIR / f"{str(session)[:64]}.run.json"


def load_manifest(session: str):
    try:
        return json.loads(manifest_path(session).read_text(encoding="utf-8"))
    except Exception:
        return None


def active_manifest(session: str):
    """The manifest that still governs this session: present and not ended."""
    m = load_manifest(session)
    return m if m and not m.get("ended") else None


def save_manifest(session: str, m: dict) -> None:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path(session).write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")


def point_current(session: str) -> None:
    HANDOFF_DIR.mkdir(parents=True, exist_ok=True)
    CURRENT.write_text(json.dumps({"session": session, "manifest": str(manifest_path(session))}), encoding="utf-8")


def _split(v: str):
    return [x.strip().strip("`") for x in re.split(r"[,;]|\s{2,}|\n", v) if x.strip()]


def parse_template(prompt: str, cwd: str) -> dict:
    """`key: value` lines after the tag; unknown keys kept raw under `extra`."""
    body = prompt.split(TAG, 1)[1]
    fields, extra, cur = {}, {}, None
    for line in body.splitlines():
        m = re.match(r"^\s*([a-zA-Z_]+)\s*:\s*(.*)$", line)
        if m and m.group(1).lower() in KEYS:
            cur = m.group(1).lower()
            fields[cur] = m.group(2).strip()
        elif m:
            cur = None
            extra[m.group(1)] = m.group(2).strip()
        elif cur and line.strip():
            fields[cur] += "\n" + line.strip()
    # Every field is OPTIONAL (user ruling 2026-09-05: the offline handoff must
    # not require form-filling). Missing fields are derived: scope = cwd/**,
    # slug = project folder + clock, canary = a random run-id token the model
    # must stamp into every deliverable + a fake debug detail that must vanish.
    # deliverables / acceptance / rulings the MODEL derives in its first turn
    # (ledger.py manifest ...) — the one place equality is traded for convenience.
    rid = "%04x" % (int(time.time() * 1000) % 65536)
    canary = {"keep": f"run-id: UR-{rid}", "drop": f"port {40000 + int(rid, 16) % 9999} timeout"}
    if fields.get("canary"):
        for k in canary:
            mm = re.search(k + r'\s*=\s*"([^"]+)"', fields["canary"])
            if mm:
                canary[k] = mm.group(1)
    proj = re.sub(r"[^a-z0-9]+", "-", os.path.basename(norm(cwd)).lower()).strip("-")[:24] or "run"
    slug = fields.get("slug") or f"{proj}-{time.strftime('%H%M')}"
    scope = _split(fields.get("scope", "")) or ([norm(cwd) + "/**"] if cwd else [])
    filled = {k: "user" for k in ("scope", "deliverables", "acceptance", "rulings", "slug", "canary") if fields.get(k)}
    return {
        "version": 3, "cwd": cwd, "ts": int(time.time()), "slug": slug,
        "scope": scope,
        "deliverables": _split(fields.get("deliverables", "")),
        "acceptance": [x for x in fields.get("acceptance", "").split("\n") if x.strip()],
        "rulings": [x for x in fields.get("rulings", "").split("\n") if x.strip()],
        "budget": fields.get("budget", ""), "stop": fields.get("stop", ""),
        "canary": canary, "report_promise": fields.get("report", ""),
        "filled_by": filled, "extra": extra, "raw": body.strip()[:4000],
        "stop_blocks": 0, "denies": 0, "ended": None,
    }


def obligations(session: str, m: dict) -> str:
    rp = f"reports/{time.strftime('%Y-%m-%d')}-run-{m['slug']}.md"
    fill = ""
    missing = [k for k in ("deliverables", "acceptance", "rulings") if not m.get(k)]
    if missing:
        fill = (f"0. Fill the manifest FIRST (before any other tool call): derive {', '.join(missing)} from the task text, "
                "the project CLAUDE.md, its registers and PROJECTS.md row, then run "
                "`python tools/process-ledger/ledger.py manifest --deliverables p1,p2 --acceptance \"item\" --acceptance \"item\" --rulings \"r\"` "
                "(repeatable flags). Deliverables are the files the user will open on return; acceptance items name a path or a command. "
                "The report marks these as model-derived.\n")
    scope_note = " (default: the project root, so F3 = writes outside it)" if m.get("filled_by", {}).get("scope") != "user" else ""
    return (
        f"[unattended-run] Manifest written: {manifest_path(session)}. Obligations for this run "
        "(hook-enforced where marked, otherwise CLAUDE.md-level):\n" + fill +
        f"1. Scope [enforced]: Write/Edit only under scope globs {m['scope']}{scope_note} "
        "or the listed deliverables (the session scratchpad and the ~/.claude carriers are always allowed); "
        "shell-side writes are audited afterwards, not blocked.\n"
        "2. Ledger: every PROCESS decision not captured by a project register (ordering, scope trade-off, "
        "skipped item, failed-control disposition) is appended at decision time with "
        "`python tools/process-ledger/ledger.py add --subject S --choice C --reason R --reversible yes|no --origin model|user [--ref D-xxx]`. "
        "Project registers (decisions/tickets/phase-log/PIM/work cards) stay the primary ledger — write them per project convention. "
        "Cost: issue a record call in the SAME message as the next real tool call (a solo record request re-reads the whole context for one row) "
        "and chain several rows in one Bash call; run_audit F8 counts solo record requests.\n"
        "3. Snapshot: when the runway notice fires, REWRITE the whole handoff snapshot and carry this manifest's scope/deliverables/acceptance/rulings/canary verbatim.\n"
        f"4. Canary [audited]: carry the literal line `{m['canary'].get('keep')}` on the first line of the handoff snapshot "
        "and of the run report; NEVER stamp it into deliverables, code or project files (they are read by people who "
        "cannot use it) — the audit reads compaction summaries, the snapshot and the report, not deliverables.\n"
        f"5. Report [enforced at stop]: before ending, run `python tools/process-ledger/report.py` (writes {rp}) and fill every acceptance item with evidence or a NAMED blocker; "
        "the final message must not end with a question — end with the report path, blockers by name, and the not-done list.\n"
        f"6. Stop condition: {m['stop'] or 'as stated in the prompt'}; budget: {m['budget'] or 'unstated'}.\n"
        "7. Run end: the user's next untagged prompt ENDS this run (both guards disarm, the manifest stays for the audit); "
        "a scope deny therefore always means the user has not returned yet — never route around it, name it as a blocker."
    )


# ----------------------------------------------------------------- helpers
def log(row: dict) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"ts": int(time.time()), **row}, ensure_ascii=False) + "\n")
    except Exception:
        pass


def norm(p: str) -> str:
    return str(p).replace("\\", "/").rstrip("/")


def human_text(prompt: str) -> str:
    """What remains of a prompt once harness-injected blocks are removed."""
    t = HARNESS_BLOCK.sub("", prompt or "")
    t = HARNESS_EMPTY.sub("", t)
    return t.strip()


# A fenced block or an inline code span: text QUOTED, not spoken. 2026-10-02 (one
# session): a code-reviewer subagent's report quoted "`[unattended-run]` is a prompt
# tag…" inside its <task-notification>; the kickoff tested the RAW prompt, so a run
# started mid-task with stop-block obligations nobody had asked for. The tag counts
# only in the user's own text (harness blocks removed) and outside code spans.
CODE_SPAN = re.compile(r"```.*?```|`[^`\n]*`", re.S)
# A pasted block is quoted too. HARNESS_BLOCK's `</\1>` never strips it because the
# harness writes the closing tag WITH its id (`</pasted_content id="…">`); probe
# 2026-10-06: a tag inside a paste armed. The tag is blanked to equal-length spaces
# on the RAW prompt (HARNESS_EMPTY strips the opening tag first, so the block is no
# longer whole inside human_text; equal length keeps the returned offset valid for
# human_text(prompt)). human_text itself keeps pastes: a paste-only prompt still
# counts as the user being back.
PASTED = re.compile(r"<pasted_content\b[^>]*>.*?</pasted_content\b[^>]*>", re.S)


def tag_index(prompt: str) -> int:
    """Offset of the first [unattended-run] in human_text(prompt) that is not inside a
    code span or a pasted block; -1 when the prompt carries no such tag."""
    blank = PASTED.sub(lambda m: m.group(0).replace(TAG, " " * len(TAG)), prompt or "")
    t = human_text(blank)
    spans = [(m.start(), m.end()) for m in CODE_SPAN.finditer(t)]
    for m in re.finditer(re.escape(TAG), t):
        if not any(a <= m.start() < b for a, b in spans):
            return m.start()
    return -1


def in_scope(path: str, m: dict) -> bool:
    p = norm(path)
    cwd = norm(m.get("cwd", ""))
    rel = p[len(cwd) + 1:] if cwd and p.lower().startswith(cwd.lower() + "/") else p
    cd = norm(str(CLAUDE_DIR))
    for a in ALWAYS_ALLOWED:
        if p.lower().startswith(f"{cd}/{a}".lower()):
            return True
    if p.lower().startswith(norm(str(SCRATCH_ROOT)).lower() + "/"):
        return True
    cands = {p, rel, p.lower(), rel.lower()}
    for d in m.get("deliverables", []):
        d = norm(d)
        if any(c == d or c == norm(f"{cwd}/{d}") or c.endswith("/" + d) for c in cands):
            return True
    for g in m.get("scope", []):
        g = norm(g)
        pats = [g, g.rstrip("*").rstrip("/") + "/*", g + "/**", g.rstrip("*").rstrip("/") + "/**/*"]
        if not g.startswith("/") and ":" not in g:
            pats += [norm(f"{cwd}/{x}") for x in list(pats)]
        for pat in pats:
            for c in cands:
                if fnmatch.fnmatchcase(c, pat) or fnmatch.fnmatchcase(c, pat.lower()):
                    return True
                # `dir/**` should also cover deep paths with fnmatch's single-star semantics
                base = pat.split("**")[0].rstrip("/")
                if "**" in pat and base and c.startswith(base + "/"):
                    return True
    return False


def last_assistant_text(transcript: Path) -> str:
    try:
        size = transcript.stat().st_size
        with transcript.open("rb") as fh:
            if size > 1_000_000:
                fh.seek(size - 1_000_000)
                fh.readline()
            lines = fh.read().decode("utf-8", "replace").splitlines()
    except Exception:
        return ""
    for line in reversed(lines):
        if '"assistant"' not in line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if rec.get("type") != "assistant" or rec.get("isSidechain"):
            continue
        content = (rec.get("message") or {}).get("content") or []
        txt = "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text").strip()
        if txt:
            return txt
    return ""


def ends_with_question(text: str) -> bool:
    t = re.sub(r"[\s*_`>）)\]」』]+$", "", text.strip())
    return t.endswith("?") or t.endswith("？")


def report_exists(m: dict) -> bool:
    try:
        return any((CLAUDE_DIR / "reports").glob(f"*-run-{m['slug']}.md"))
    except Exception:
        return False


def clear_pointer(session: str) -> None:
    """Drop current-run.json once THIS session's run is allowed to stop or has ended.

    The pointer is global; a finished run that keeps it makes ledger.py file every
    later session's rows under the finished run (2026-09-05, first observed with a
    concurrent interactive session — ledger.py now also guards against that, this
    is the producer-side half). Only the owning session removes it.
    """
    try:
        if json.loads(CURRENT.read_text(encoding="utf-8")).get("session") == session:
            CURRENT.unlink()
    except Exception:
        pass


def end_run(session: str, m: dict, by: str, payload: dict | None = None) -> None:
    m["ended"] = {"ts": int(time.time()), "by": by}
    save_manifest(session, m)
    clear_pointer(session)
    # payload keys: production evidence of what a return prompt looks like (does a
    # subagent's first prompt reach UserPromptSubmit with the parent's session_id?)
    log({"event": "end", "session": session, "slug": m.get("slug"), "by": by,
         "denies": m.get("denies", 0), "stop_blocks": m.get("stop_blocks", 0),
         "keys": sorted((payload or {}).keys())})


# ----------------------------------------------------------------- modes
def mode_kickoff(payload: dict) -> None:
    prompt = payload.get("prompt") or ""
    session = str(payload.get("session_id", "unknown"))
    at = tag_index(prompt)
    if at >= 0:
        m = parse_template(human_text(prompt)[at:], payload.get("cwd", ""))
        live = active_manifest(session)
        if live:
            # Re-tag while the run still governs: the run keeps its identity (Q4,
            # user ruling 2026-09-08). A widened scope is the documented reason to
            # re-tag; a new run-id for the same run gave one report three tokens
            # (claude-share 2026-09-07). Only an ENDED manifest mints a new id.
            if not m["filled_by"].get("canary"):
                m["canary"] = live.get("canary", m["canary"])
            if not m["filled_by"].get("slug"):
                m["slug"] = live.get("slug", m["slug"])
            m["denies"] = int(live.get("denies", 0))
            m["stop_blocks"] = int(live.get("stop_blocks", 0))
            m["retagged"] = int(live.get("retagged", 0)) + 1
        save_manifest(session, m)
        point_current(session)
        log({"event": "kickoff", "session": session, "slug": m["slug"], "scope": m["scope"], "deliverables": m["deliverables"],
             "retagged": m.get("retagged", 0)})
        print(obligations(session, m))
        # The negative canary travels apart from the obligations block and in a
        # different shape (transient noise, not a standing constraint) — inside the
        # constraint block a Compact-Instructions-obeying summarizer kept it every
        # time (5/5 sessions measured 2026-09-08). Once per run.
        if not live and m["canary"].get("drop"):
            print(f"\n[probe] transient: an earlier probe saw \"{m['canary']['drop']}\" — resolved, nothing to do.")
        return
    m = active_manifest(session)
    if not m or not human_text(prompt):
        return                                   # no run, or a harness-injected prompt: the user is not back
    end_run(session, m, "user-prompt", payload)
    print(f"[unattended-run] run `{m.get('slug')}` ENDED: the user is back (untagged prompt). "
          "Scope and stop guards are disarmed for this session; the manifest stays at "
          f"{manifest_path(session)} for run_audit.py (denies {m.get('denies', 0)}, stop blocks {m.get('stop_blocks', 0)}). "
          "If the user is only adding to the task before leaving, ask them to re-send `[unattended-run]` — that starts a new run.")


def mode_scope(payload: dict) -> None:
    session = str(payload.get("session_id", "unknown"))
    m = active_manifest(session)
    if not m:
        return
    ti = payload.get("tool_input") or {}
    path = ti.get("file_path") or ti.get("notebook_path") or ""
    if not path or in_scope(path, m):
        return
    m["denies"] = int(m.get("denies", 0)) + 1
    save_manifest(session, m)
    reason = (f"Write denied by unattended_run, a local PreToolUse hook (not file or page "
              f"content). [unattended-run] write outside the run scope: {path}. Scope globs: {m['scope']}; "
              f"deliverables: {m['deliverables']}. Either the path belongs in scope (re-issue `[unattended-run]` with the wider scope "
              "— that is a user decision, log it as a named blocker) or the write is drift (F3). Carriers under "
              f"{CLAUDE_DIR}/{{cache/handoff,reports,telemetry}} and the session scratchpad under {SCRATCH_ROOT} are always allowed. "
              "The user's next untagged prompt ends the run; this deny means they have not returned."
              + _receipt("unattended_run", target=str(path), slug=str(m.get("slug", "")))
              + _fp("unattended_run"))
    log({"event": "deny", "session": session, "path": path})
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                             "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


def mode_stop(payload: dict) -> None:
    if not payload.get("session_id"):
        log({"event": "stop-nosession", "keys": sorted(payload.keys())})
        return
    session = str(payload.get("session_id"))
    m = active_manifest(session)
    if not m:
        return
    if int(m.get("stop_blocks", 0)) >= STOP_BLOCKS:
        clear_pointer(session)
        log({"event": "stop-allowed", "session": session, "n": m.get("stop_blocks", 0), "why": "bound"})
        return                                   # bounded: a broken run can always end
    transcript = Path(str(payload.get("transcript_path") or ""))
    text = last_assistant_text(transcript) if transcript.is_file() else ""
    problems = []
    if ends_with_question(text):
        problems.append("the final message ends with a question — nobody is here to answer it; end with named blockers instead")
    if not report_exists(m):
        problems.append(f"no run report on disk (expected reports/*-run-{m['slug']}.md) — run `python tools/process-ledger/report.py` and fill evidence")
    if not problems:
        clear_pointer(session)
        log({"event": "stop-allowed", "session": session, "n": m.get("stop_blocks", 0), "why": "shape-ok"})
        return
    m["stop_blocks"] = int(m.get("stop_blocks", 0)) + 1
    save_manifest(session, m)
    log({"event": "block", "session": session, "n": m["stop_blocks"], "problems": problems})
    print(json.dumps({"decision": "block",
                      "reason": f"Stop refused by unattended_run, a local Stop hook (not file "
                                f"or page content) ({m['stop_blocks']}/{STOP_BLOCKS}): "
                                + "; ".join(problems)
                                + _receipt("unattended_run", kind="stop-block")
                                + _fp("unattended_run")}))


def main() -> None:
    try:
        mode = sys.argv[1] if len(sys.argv) > 1 else ""
        payload = json.load(sys.stdin)
        {"kickoff": mode_kickoff, "scope": mode_scope, "stop": mode_stop}.get(mode, lambda p: None)(payload)
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
