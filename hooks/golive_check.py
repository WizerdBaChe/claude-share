r"""PostToolUse(Write|Edit|MultiEdit): run the proof-of-life of a hook the moment it goes live.

STATUS: LIVE since 2026-09-22 (design 17, release boundary R-3). Carries
`ops/rule-registry.md` key `GOLIVE_CHECK`.

WHY. A hook in ~/.claude is live the moment it is SAVED -- the harness runs the script from
disk on every event -- so "test before merge" is already too late for it. The measured case
behind pol.py (AP-63): `hooks/unattended_run.py` called a function it never imported, every
guard in it raised NameError, a crashing hook fails open, and the offline run's two guards
were inert for a day although their control suite existed and passed the moment it was run.
Nothing ran it. This hook is the event that runs it.

WHAT IT RUNS. The executable `Proof-of-life:` command each registered hook declares in its
own docstring (pol.py's grammar, imported, never copied), for every registered hook that
(a) IS the edited file, or (b) names the edited file, or the edited file's `tools/<x>/`
directory, inside that command, or (c) lists the edited file on a `Live-reads:` line in its
docstring. (a)/(b) take code files only (.py .json .toml .ps1); (c) takes ANY suffix, because
the files a hook reads at run time are mostly registers in Markdown. At most MAX_SUITES
suites, each capped at SUITE_TIMEOUT s; telemetry of the suites is isolated to a temp dir.

WHY (c). A hook whose suite checks LIVE data is broken by an edit to that data, and until
2026-09-23 nothing ran the suite on such an edit: `references/PROJECTS.md` gained rows three
times (09-21, 09-23 04:24, 09-23 15:25-15:49) without an activity-map row in
`references/USER-PROFILE.md`, user_profile_gist's live check L-1 went red each time, and each
time the only thing that found it was the HMI. The declaration sits in the reading hook, so a
new live-read source is declared where it is introduced (ops/lessons.md L-121).
Known limits (named, not gated): a tool a hook imports but its command does not name is not
mapped; a data file written by a script (Bash/PowerShell) rather than Write/Edit fires no
event here. The daily `hmi.py verdict` full collect still covers both.

ALSO AT THE SAME SAVE (2026-09-23): if the edited file is itself a control suite that
`tools/class-closure/closure.py` enumerates (every tools/*/controls.py, hooks/tests/*.py, and
each registered hook's declared suite) and names no unclassifiable case, the notice says so.
check 33 had been drained to 0 and promoted to FAIL on 2026-09-09, and 10 suites born in the
next 14 days still lacked the case, because nothing ran it at the moment a suite is written.
See `closure_gap()`. Only the STATIC half runs here: `tools/class-closure/exercise.py` (does
the named case actually run?) executes every suite (~80 s), so it lives in the sweep and the
HMI slow tier, never in a save-time hook.

ALSO AT THE SAME SAVE (2026-09-29): if the edited file belongs to a component system-hmi's
scan roots enumerate (hooks/*.py, rules/*.md, agents/*.md, tools/<x>, skills/<x>) and that
component has no `subsystems.json` row nor a reasoned `ignore.json` row, the notice says so.
`hmi.py scan` had carried 12 UNREGISTERED components for up to two weeks with no runner but a
hand-typed command. See `registry_gap()`; entry-schema-lint ES-9 is its sweep twin.

SEVERITY: notice (consumer = the model; nothing is blocked -- gate-severity-by-consumer).
Silent on pass and on every path it does not map. Fail-open on every error. A row is written
to telemetry/golive-check.jsonl for EVERY run, pass included, BEFORE any notice, so the cost
and the misfire rate have a denominator.

Proof-of-life: `python hooks/tests/test_golive_check.py`
review-when: pol.py's declaration grammar changes (MARKER/RUNNABLE); a hook's suite routinely
exceeds SUITE_TIMEOUT (then the notice turns into a timeout report and must be re-sized).
FALSE-POSITIVE LOG: none yet.
"""
import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# GOLIVE_HOME exists for the suite's fixture home only (a positive control that needs a
# really failing hook cannot break a live one); production never sets it.
HOME = Path(os.environ.get("GOLIVE_HOME") or Path(__file__).resolve().parents[1])
TOOL_NAMES = {"Write", "Edit", "MultiEdit"}
CODE_SUFFIXES = (".py", ".json", ".toml", ".ps1")
MAX_SUITES = 3
SUITE_TIMEOUT = 60
HOOK = "golive_check"


def _pol():
    sys.path.insert(0, str(HOME / "tools" / "hook-proof-of-life"))
    import pol
    # pol creates one temp telemetry dir at import for a whole sweep; this hook runs
    # its own suites with its own dir, so remove pol's to leave no litter per edit.
    shutil.rmtree(getattr(pol, "_POL_TELEMETRY_DIR", ""), ignore_errors=True)
    return pol


def rel_in_home(file_path, home=HOME):
    try:
        p = Path(file_path).resolve()
        return p.relative_to(home.resolve()).as_posix()
    except Exception:
        return None


LIVE_READS = re.compile(r"^Live-reads:(.*)$", re.M)
LIVE_PATH = re.compile(r"`([^`\s]+)`")


def live_reads(hook_path):
    """Paths a hook declares on its `Live-reads:` docstring line(s), home-relative posix.
    Backticked paths only, so prose on the same line never becomes a path."""
    try:
        text = Path(hook_path).read_text(encoding="utf-8")
        if "Live-reads:" not in text:       # every edit in home walks every hook: stay cheap
            return []
        doc = ast.get_docstring(ast.parse(text)) or ""
    except Exception:
        return []
    return [p for m in LIVE_READS.finditer(doc) for p in LIVE_PATH.findall(m.group(1))]


def suites_for(rel, declared, reads=None):
    """declared: {hook_basename: command}; reads: {hook_basename: [live-read paths]}.
    -> ordered unique commands for `rel`."""
    if not rel:
        return []
    out = []
    for name, cmd in sorted(declared.items()):
        if rel in (reads or {}).get(name, ()) and cmd not in out:
            out.append(cmd)
    if rel.endswith(CODE_SUFFIXES):
        tool_dir = "/".join(rel.split("/")[:2]) + "/" if rel.startswith("tools/") else None
        for name, cmd in sorted(declared.items()):
            hit = (rel == f"hooks/{name}" or rel in cmd
                   or (tool_dir is not None and tool_dir in cmd))
            if hit and cmd not in out:
                out.append(cmd)
    return out[:MAX_SUITES]


def closure_gap(rel, home=HOME):
    """-> True when `rel` is a control suite class-closure enumerates and it names no
    unclassifiable case; False otherwise, including on any error (fail-open).

    WHY HERE (2026-09-23). check 33 was drained to 0 on 2026-09-09 and promoted to FAIL,
    yet 10 suites born in the next 14 days lacked the case: its only runners were the
    manual integrity sweep and, later, a HMI row -- the monitor-only shape of L-121. The
    moment a suite is written is the moment its author still knows which input the
    instrument cannot classify, so the check runs at that save. closure.py's own
    enumeration and proxy are imported, never copied, so this and check 33 cannot disagree.
    """
    if not rel or not rel.endswith(".py"):
        return False
    try:
        sys.path.insert(0, str(home / "tools" / "class-closure"))
        import closure
        if rel not in closure.suites(home):
            return False
        return closure.classify(home / rel)[0] == "lacks"
    except Exception:
        return False


SCAN_FILE_ROOTS = ("hooks", "rules", "agents")   # component = the file itself
SCAN_DIR_ROOTS = ("tools", "skills")              # component = the depth-1 folder


def registry_gap(rel, home=HOME):
    """-> the component id (a hook / rule / agent file, or a depth-1 tools/ or skills/
    folder) when `rel` lies under one of system-hmi's scan roots and that component has no row in
    tools/system-hmi/registry/subsystems.json nor a reasoned ignore.json row; "" otherwise,
    including on any error (fail-open).

    WHY HERE (2026-09-29). `hmi.py scan` had listed 12 UNREGISTERED components -- born over
    two weeks, each with a suite nobody's dashboard ran -- and the only runner of that scan
    was a hand-typed command. Same shape as closure_gap: the moment a component is first
    written is the moment its author knows which subsystem it belongs to. The enumeration is
    system-hmi's own hmi/scan.py, imported, and entry-schema-lint ES-9 is the sweep twin of
    this save-time check, so the three cannot disagree.
    """
    if not rel:
        return ""
    parts = rel.split("/")
    if parts[0] in SCAN_DIR_ROOTS and len(parts) >= 2:
        comp = "/".join(parts[:2])
    elif parts[0] in SCAN_FILE_ROOTS and len(parts) == 2:
        comp = rel
    else:
        return ""
    try:
        hmi = home / "tools" / "system-hmi"
        spec = importlib.util.spec_from_file_location("_golive_hmi_scan", hmi / "hmi" / "scan.py")
        scan = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scan)
        reg_dir = hmi / "registry"
        registry = {"subsystems": json.loads((reg_dir / "subsystems.json").read_text(encoding="utf-8")),
                    "ignore": (json.loads((reg_dir / "ignore.json").read_text(encoding="utf-8"))
                               if (reg_dir / "ignore.json").is_file() else [])}
        unregistered = {e["path"] for e in scan.scan(home, registry)["unregistered"]}
        return comp if comp in unregistered else ""
    except Exception:
        return ""


def run_one(cmd, home=HOME, timeout=SUITE_TIMEOUT):
    """-> (result, last_line, seconds); result in pass|fail|inconclusive."""
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="golive-telemetry-") as tel:
        env = dict(os.environ, PYTHONIOENCODING="utf-8", CLAUDE_TELEMETRY_DIR=tel)
        argv = cmd.split()
        if argv and argv[0] == "python":
            argv[0] = sys.executable
        try:
            proc = subprocess.run(argv, cwd=str(home), capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return "inconclusive", f"timed out after {timeout}s", time.monotonic() - start
        except Exception as exc:
            return "inconclusive", f"{type(exc).__name__}: {exc}", time.monotonic() - start
    tail = [ln for ln in (proc.stdout or proc.stderr or "").splitlines() if ln.strip()]
    last = (tail[-1] if tail else f"exit {proc.returncode}")[:160]
    if proc.returncode == 3:
        return "inconclusive", last, time.monotonic() - start
    return ("pass" if proc.returncode == 0 else "fail"), last, time.monotonic() - start


def notice_text(rel, bad, gap=False, unwatched=""):
    import deny_receipt
    parts = [f"Notice from golive_check (a local PostToolUse hook, not file content): "]
    if bad:
        parts.append(f"{rel} is live on save, so the proof-of-life suite(s) naming it were run now.")
    for cmd, result, last in bad:
        parts.append(f" {result.upper()}: `{cmd}` -> {last}.")
    if gap:
        parts.append(f"{' ' if bad else ''}this save touched {rel}, which the class-closure check "
                     "enumerates as a control suite, and none of its lines names a case it must call "
                     "`undetermined` (an unclassifiable input). Add one deliberate input "
                     "the instrument cannot classify (wrong type, unknown kind, a payload that parses "
                     "but is not an object) and assert it is reported undetermined or excluded, never "
                     "folded into a real verdict; the word must be in the case's name or message. "
                     "Re-check with `python -X utf8 tools/class-closure/closure.py`.")
    if unwatched:
        parts.append(" " if (bad or gap) else "")
        parts.append(f"this save touched {rel}, and its component {unwatched} is registered in "
                     "no system-hmi subsystem and ignored by no reasoned row, so nothing watches it. "
                     "Write a row to tools/system-hmi/registry/subsystems.json (component_rules, "
                     "under the subsystem its function belongs to), or write a reasoned row to "
                     "tools/system-hmi/registry/ignore.json; then re-check with "
                     "`python -X utf8 tools/system-hmi/hmi.py scan`.")
    parts.append(" Nothing was blocked. To re-check after a fix, run the same command.")
    parts.append(deny_receipt.notice_clause(HOOK))
    return "".join(parts)


def log_row(row):
    import deny_receipt
    try:
        path = deny_receipt.log_path(HOOK)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    try:
        if str(payload.get("tool_name", "")) not in TOOL_NAMES:
            sys.exit(0)
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict) or not isinstance(tool_input.get("file_path"), str):
            sys.exit(0)
        rel = rel_in_home(tool_input["file_path"])
        if not rel:
            sys.exit(0)
        pol = _pol()
        declared, reads = {}, {}
        for name in pol.registered_hooks():
            kind, detail = pol.declaration(HOME / "hooks" / name)
            if kind == "executable":
                declared[name] = detail
                reads[name] = live_reads(HOME / "hooks" / name)
        cmds = suites_for(rel, declared, reads)
        gap = closure_gap(rel)
        unwatched = registry_gap(rel)
        if not cmds and not gap and not unwatched:
            sys.exit(0)
        sys.path.insert(0, str(HOME / "hooks"))
        results = [(cmd, *run_one(cmd)) for cmd in cmds]
        bad = [(c, r, last) for c, r, last, _s in results if r != "pass"]
        log_row({"ts": int(time.time()), "kind": "notice" if (bad or gap or unwatched) else "pass",
                 "session_id": str(payload.get("session_id") or ""), "path": rel,
                 "suites": [{"cmd": c, "result": r, "last": last, "s": round(s, 1)}
                            for c, r, last, s in results],
                 "closure_lacks": gap, "unwatched": unwatched})
        if bad or gap or unwatched:
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": notice_text(rel, bad, gap, unwatched)}}))
    except SystemExit:
        raise
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
