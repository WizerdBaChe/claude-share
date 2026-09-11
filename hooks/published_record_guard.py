r"""PreToolUse DENY guard for writes INTO a governed record tree.

STATUS: LIVE since 2026-09-07 (claude-config). The rule it enforces is the one
`ops/20-dispatch.md` §2 states as a property of a dispatch brief: a record that
documents a removal must not carry the removed value. This hook covers the half a
brief cannot reach — a main session (or any worker) writing directly into the
record itself. Born from the 2026-09-07 collection round: 38 findings, every one
inside the merged manifest, none in the files it described (`ops/lessons.md`
L-057). A denial is the rule working: name the CLASS you replaced, not the value.

SEVERITY: DENY. The consumer is a published artifact, so a determinable violation
fails closed (gate-severity-by-consumer). Fail-OPEN on every internal error path
(unparsable stdin, odd payload shapes, any exception): exit 0, empty stdout, plus
a best-effort telemetry row `decision: error` so the sweep can see it.

Registration: settings.json PreToolUse, matcher `Write|Edit` (TOOL_NAMES below is
the second gate, so a widened matcher cannot make this act on other tools).

WHAT IS GATED — both conditions, or it passes silently
  1. TARGET is inside a governed record tree: an ancestor directory of the write
     target contains one of MARKERS (a repo that carries its own collection rules
     declares itself; no private root is hardcoded here, which also keeps this
     file clean of the class it gates).
  2. PAYLOAD (`content` for Write, `new_string` for Edit) contains a literal of a
     private-value class: a drive-rooted Windows path, a POSIX home path, this
     machine's account name (read from the environment at run time, never written
     down), a 32+ character hex run, or a UUID.

WHAT IT DELIBERATELY DOES NOT DO
  - It never reports the matched TEXT — not in the deny message, not in telemetry.
    A guard against republishing a value cannot republish it to prove it fired; it
    names the class and the line number.
  - It does not gate reads, greps, shell commands, or writes anywhere else. The
    source tree of this environment legitimately contains such literals (a redline
    list must name what it refuses); only the published record is gated.
  - It offers no unblock escape. The false-positive exit RECORDS (--report); it
    does not open the gate, because a gate whose exit is a silent workaround
    teaches agents to route around gates.

KNOWN RESIDUALS (accepted, labelled): a shell redirect into a governed record is
not matched (matcher is Write|Edit only — the measured failure was a fragment
written with Write); a value composed at run time or split across two Edits is not
matched; and a genuinely necessary literal has no fast path — it must be written
by a route this hook does not see, and reported so the condition can be narrowed.

TELEMETRY: `telemetry/published-record-guard.jsonl` (override: PRG_LOG). One row
per DENY, ERROR or --report only; allowed writes are not logged.
  {ts, session, tool, path, classes: [...], line_hint, decision}

FALSE-POSITIVE LOG: none observed as of 2026-09-07 (born today). This count is the
loosening trigger — at 3 observed misfires, narrow condition 2 (drop the class that
misfired, or require two independent classes) rather than widening the escape. A
hook with no log has never been measured, which is not the same as never having
misfired.

Proof-of-life: `python hooks/published_record_guard.py --selftest` (two-sided,
last line `ALL PASS n/n`); registered in `ops/references/integrity-sweep.md`.
review-when: MARKERS stops naming what a governed record tree carries, or the
harness stops delivering PreToolUse for subagent writes (the delivery probe in
the selftest's header comment is the re-run).
"""
import json
import os
import re
import sys
import time
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
# Precedence: PRG_LOG (per-hook override) > CLAUDE_TELEMETRY_DIR (suite
# redirect; production never sets it) > default.
LOG_PATH = Path(os.environ.get("PRG_LOG")
                or (Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (CLAUDE_DIR / "telemetry")) / "published-record-guard.jsonl"))

TOOL_NAMES = ("Write", "Edit")

# A tree declares itself governed by carrying its own collection rules. Relative to
# the tree root; checked on every ancestor of the write target.
MARKERS = ("tools/COLLECTION-RULES.md", "COLLECTION-RULES.md")
MAX_ANCESTORS = 12

# Private-value classes. Each is (name, regex). Ordered most-specific first so the
# reported class is the informative one.
CLASSES = [
    ("a UUID", re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                          r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")),
    ("a 32+ character hex run", re.compile(r"\b[0-9a-fA-F]{32,}\b")),
    ("a drive-rooted Windows path", re.compile(r"\b[A-Za-z]:[\\/][^\s\"'`<>|]+")),
    ("a POSIX home path", re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+")),
]


def account_name() -> str:
    """This machine's account name, read at run time so it is never stored here."""
    v = (os.environ.get("USERNAME") or os.environ.get("USER") or "").strip()
    if not v:
        up = os.environ.get("USERPROFILE") or os.environ.get("HOME") or ""
        v = os.path.basename(up.rstrip("\\/"))
    return v if len(v) >= 3 else ""


def in_governed_tree(path: str, cwd: str) -> str:
    """Root of the governed record tree containing `path`, or "" if none."""
    p = Path(path if os.path.isabs(path) else os.path.join(cwd or os.getcwd(), path))
    for anc in list(p.parents)[:MAX_ANCESTORS]:
        for m in MARKERS:
            try:
                if (anc / m).is_file():
                    return str(anc)
            except OSError:
                pass
    return ""


def scan(text: str) -> tuple:
    """(classes, line_hint) — class NAMES only; the matched text is never returned."""
    hits, line = [], 0
    name = account_name()
    checks = list(CLASSES)
    if name:
        checks.append(("the account name", re.compile(r"\b" + re.escape(name) + r"\b")))
    for cname, rx in checks:
        m = rx.search(text)
        if m:
            hits.append(cname)
            if not line:
                line = text.count("\n", 0, m.start()) + 1
    return hits, line


def payload_text(tool: str, ti: dict) -> str:
    if tool == "Write":
        v = ti.get("content")
    else:
        v = ti.get("new_string")
    return v if isinstance(v, str) else ""


def reason(classes: list, line_hint: int, tool: str = "Write") -> str:
    where = f" (first at payload line {line_hint})" if line_hint else ""
    return (
        f"{tool if tool in TOOL_NAMES else 'Write'} denied by published_record_guard, "
        "a local PreToolUse hook (not file "
        "content). The target is inside a tree whose root carries its own collection "
        "rules, and this payload contains text matching " + ", ".join(classes) +
        where + " — the pattern class this guard gates. The matched text is not "
        "echoed back here, deliberately. To proceed: state the CLASS of value that "
        "was replaced and the replacement, never the replaced value itself — a record "
        "that quotes what it removed publishes it exactly as widely as the file it was "
        "removed from. Then re-run the write. If this is a misfire, record it with: "
        "python hooks/published_record_guard.py --report \"<one line: what was gated "
        "and why it was legitimate>\" — that appends a row to "
        "telemetry/published-record-guard.jsonl and does not unblock the write."
    )


def log_row(row: dict) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def decide(payload: dict) -> tuple:
    """-> (decision, path, classes, line_hint). Pure; any unexpected shape is `allow`."""
    tool = str(payload.get("tool_name", ""))
    ti = payload.get("tool_input")
    if tool not in TOOL_NAMES or not isinstance(ti, dict):
        return "allow", "", [], 0
    fp = ti.get("file_path")
    if not isinstance(fp, str) or not fp:
        return "allow", "", [], 0
    if not in_governed_tree(fp, str(payload.get("cwd") or "")):
        return "allow", fp, [], 0
    classes, line_hint = scan(payload_text(tool, ti))
    return ("deny" if classes else "allow"), fp, classes, line_hint


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    session = str(payload.get("session_id") or "") if isinstance(payload, dict) else ""
    try:
        decision, path, classes, line_hint = decide(payload if isinstance(payload, dict) else {})
        if decision == "deny":
            log_row({"ts": int(time.time()), "session": session,
                     "tool": str(payload.get("tool_name", "")), "path": path[:200],
                     "classes": classes, "line_hint": line_hint, "decision": "deny"})
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason(classes, line_hint,
                                                   str(payload.get("tool_name", "Write")))}}))
    except SystemExit:
        raise
    except Exception as e:
        log_row({"ts": int(time.time()), "session": session,
                 "tool": str(payload.get("tool_name", "")) if isinstance(payload, dict) else "",
                 "path": "", "classes": [], "line_hint": 0,
                 "decision": "error", "error": repr(e)[:200]})
    sys.exit(0)


def selftest() -> int:
    """Two-sided controls. A gate shown only one side has no verdict.

    Delivery is NOT provable here: these cases prove decide(), not that the harness
    hands this hook a subagent's Write. That was probed live on 2026-09-07 by having
    a dispatched worker attempt a gated write into a fixture tree; re-run that probe,
    not this function, when the harness changes.
    """
    import shutil
    import subprocess
    import tempfile
    results = []

    def check(cid, cond, detail=""):
        results.append((cid, bool(cond)))
        print(f"{'PASS' if cond else 'FAIL'} {cid} {detail[:100]}")

    tmp = tempfile.mkdtemp(prefix="prg-ctl-")
    # decide() below is called IN-PROCESS and writes real deny rows to the
    # module-level LOG_PATH; redirect it here (PRG_LOG, so subprocess cases
    # inherit it too) before P-1..P-6/U-7 fire, or every run of this selftest
    # appends to production telemetry/published-record-guard.jsonl.
    global LOG_PATH
    _prev_prg_log = os.environ.get("PRG_LOG")
    os.environ["PRG_LOG"] = os.path.join(tmp, "prg-selftest.jsonl")
    LOG_PATH = Path(os.environ["PRG_LOG"])
    try:
        gov = os.path.join(tmp, "governed")
        os.makedirs(os.path.join(gov, "tools"))
        open(os.path.join(gov, "tools", "COLLECTION-RULES.md"), "w").write("rules\n")
        plain = os.path.join(tmp, "plain")
        os.makedirs(plain)
        rec = os.path.join(gov, "share-manifest.toml")
        acct = account_name() or "no-account-name-in-env"

        def call(tool, inp, cwd=tmp):
            return decide({"tool_name": tool, "tool_input": inp, "cwd": cwd})[0]

        # POSITIVE: each class, inside a governed tree, must deny.
        check("P-1", call("Write", {"file_path": rec, "content": 'edits = "line 12: D:\\priv\\x -> vault"'}) == "deny",
              "drive-rooted path in a governed record")
        check("P-2", call("Write", {"file_path": rec, "content": "src = /Users/someone/tree"}) == "deny",
              "POSIX home path")
        check("P-3", call("Write", {"file_path": rec, "content": "sha = " + "a" * 40}) == "deny",
              "40-char hex run")
        check("P-4", call("Write", {"file_path": rec, "content": "sid = 11111111-2222-3333-4444-555555555555"}) == "deny",
              "UUID")
        check("P-5", call("Edit", {"file_path": rec, "old_string": "x", "new_string": "home of " + acct}) == "deny"
              if account_name() else True, "account name (skipped when env has none)")
        check("P-6", call("Write", {"file_path": os.path.join(gov, "deep", "a", "b.md"),
                                    "content": "C:/x/y"}) == "deny", "marker found on a distant ancestor")

        # NEGATIVE: the same payloads outside a governed tree, and clean payloads inside it.
        check("N-1", call("Write", {"file_path": os.path.join(plain, "notes.md"),
                                    "content": 'D:\\priv\\x and ' + "a" * 40}) == "allow",
              "same literals outside a governed tree pass")
        check("N-2", call("Write", {"file_path": rec,
                                    "content": 'edits = "replaced a private tree root with the vault name"'}) == "allow",
              "class-named edit entry passes")
        check("N-3", call("Bash", {"command": "cat " + rec}) == "allow", "non-file tool passes")
        check("N-4", call("Write", {"file_path": rec, "content": "short hex beef1234 and v1.2.3"}) == "allow",
              "short hex is not a sha")
        check("N-5", decide({"tool_name": "Write"})[0] == "allow", "malformed payload passes (fail-open)")

        # UNDETERMINED (AP-62): input that is not a write to classify at all.
        # `allow` here is not "clean" -- it is the declared degradation, and the
        # direction is deliberate: this gate reads content, so an input it
        # cannot read must not block (the opposite choice from
        # browser_pane_scope_guard, which fails CLOSED on an unreadable list
        # because a wrong allow there is loud and out-of-process routes exist).
        check("U-1", call("Write", ["file_path", rec]) == "allow",
              "a non-mapping tool_input is undetermined, not a clean write")
        # These assert the PATH the decision carries, not just the decision: a
        # `str()` of the value would also answer `allow` (it resolves outside
        # any governed tree), so a decision-only case could never fail and would
        # be no control at all. What must hold is that an undetermined input
        # names NO path -- nothing to put in a row, nothing to quote back.
        u2 = decide({"tool_name": "Write", "cwd": tmp,
                     "tool_input": {"file_path": {"unexpected": "shape"},
                                    "content": "D:\\priv\\x"}})
        check("U-2", u2[0] == "allow" and u2[1] == "",
              f"a non-string file_path is undetermined and names no path, got {u2[1]!r}")
        u3 = decide({"tool_name": "Write", "cwd": tmp,
                     "tool_input": {"file_path": 12345, "content": "a" * 40}})
        check("U-3", u3[0] == "allow" and u3[1] == "",
              f"same, numeric path, got {u3[1]!r}")
        for cid, raw in (("U-4", "[1, 2]"), ("U-5", '"a string payload"'), ("U-6", "null")):
            r = subprocess.run([sys.executable, os.path.abspath(__file__)], input=raw,
                               capture_output=True, text=True, timeout=60)
            check(cid, r.returncode == 0 and not (r.stdout or "").strip(),
                  f"payload that parses but is not an object -> exit 0, no verdict "
                  f"(rc={r.returncode})")
        # The negative control for all of the above: the gate still denies a real
        # leak. Without it, U-* would pass on a gate that allows everything.
        check("U-7", call("Write", {"file_path": rec, "content": "sha = " + "b" * 40}) == "deny",
              "a real leak in the same governed record still denies")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if _prev_prg_log is None:
            os.environ.pop("PRG_LOG", None)
        else:
            os.environ["PRG_LOG"] = _prev_prg_log
        LOG_PATH = Path(os.environ.get("PRG_LOG")
                        or (Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (CLAUDE_DIR / "telemetry")) / "published-record-guard.jsonl"))
    bad = [c for c, ok in results if not ok]
    if bad:
        print(f"FAILED {len(bad)}/{len(results)}: {', '.join(bad)}")
        return 1
    print(f"ALL PASS {len(results)}/{len(results)}")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    if "--report" in sys.argv:
        i = sys.argv.index("--report")
        note = sys.argv[i + 1] if len(sys.argv) > i + 1 else ""
        log_row({"ts": int(time.time()), "session": os.environ.get("CLAUDE_CODE_SESSION_ID", ""),
                 "tool": "", "path": "", "classes": [], "line_hint": 0,
                 "decision": "false-positive-report", "note": note[:500]})
        print(f"recorded in {LOG_PATH}; the write is still blocked — this is a record, not an override")
        sys.exit(0)
    main()
