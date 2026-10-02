r"""Check the invariants Phase 8 established, as PROPERTIES OF THE REPO.

Everything here is machine-decidable, which is exactly why it lives in a script
instead of a checklist: the four facts below are the ones that rot silently, and
a rotted line-ending or an unregistered hook looks identical to a healthy one
until something breaks far downstream.

    python invariants.py                 # run from anywhere; defaults to ~/.claude
    python invariants.py --repo <path>

Exit code 0 = all hold, 1 = at least one broke. What it does NOT cover: the two
Bash transport defects themselves, which live at the Claude Code tool boundary
and cannot be reproduced from a subprocess. Those are in PROBES.md, by hand,
deliberately.
"""
import argparse
import io
import json
import os
import subprocess
import sys

CRLF = bytes([13, 10])
LF = bytes([10])
NUL = bytes([0])
BINARY_SNIFF_BYTES = 8000     # git's own is-binary heuristic window
GUARD_NOTICE_BASELINE = 2.7   # % of Bash calls, backtested 2026-08-19
GUARD_DENY_BASELINE = 0.14


def git(repo, *args):
    # core.quotePath=false: git C-quotes any path with a byte outside ASCII
    # ("outputs/.../\351\251\227...md"), and a caller then looks for a file at
    # the literal quoted name, fails, and moves on. Measured 2026-09-09 on this
    # repo: 1 of 1442 tracked files, dropped from the denominator since the
    # invariant was written. This flag is for the callers that read git's
    # newline-delimited output; the scan below uses -z, which suppresses quoting
    # on its own -- the inversion test says so, and the flag alone did not.
    return subprocess.run(["git", "-C", repo, "-c", "core.quotePath=false"] + list(args),
                          capture_output=True, text=True, encoding="utf-8").stdout


def content_class(data):
    """Declared, closed class set for a tracked file (PH-11 / AP-62).

      text   — CR/LF are line endings; this invariant rules on it
      binary — CR/LF are payload bytes; counted, never ruled on

    Uses git's own is-binary heuristic (a NUL byte in the first 8000 bytes) so
    the classifier and the tool whose file list it reads agree on the word.

    EXTENDING (AP-61): a class added here needs a specimen in controls.py, which
    asserts one file per class AND that a genuinely mixed TEXT file is still
    caught — widening a vocabulary must never be able to silence real rot.
    """
    return "binary" if NUL in data[:BINARY_SNIFF_BYTES] else "text"


def _scan_line_endings(repo):
    """-> (mixed text files, undetermined descriptions, {class: count}).

    The one place that walks the tracked files, so the verdict and
    `--list-mixed` can never disagree about what they are counting.
    """
    mixed, undetermined = [], []
    counts = {"text": 0, "binary": 0}
    # -z, so a path containing a newline cannot split into two names that both
    # then fail to resolve. With quotePath=false these are the last two ways the
    # population could shrink without saying so.
    for f in git(repo, "ls-files", "-z").split("\0"):
        if not f.strip():
            continue
        p = os.path.join(repo, f)
        if not os.path.isfile(p):
            # Tracked, and there is nothing here to classify. Both shapes below
            # used to `continue`, which put them in no count at all -- the same
            # silent fold the class set exists to prevent, one layer up: it is
            # the POPULATION being folded, not the verdict.
            undetermined.append("%s (%s)" % (
                f, "tracked, absent from the worktree" if not os.path.exists(p)
                else "tracked, not a regular file"))
            continue
        try:
            d = open(p, "rb").read()
        except Exception as exc:
            undetermined.append("%s (%s)" % (f, type(exc).__name__))
            continue
        cls = content_class(d)
        counts[cls] += 1
        if cls != "text":
            continue
        ncrlf = d.count(CRLF)
        if ncrlf and (d.count(LF) - ncrlf):
            mixed.append(f)
    return mixed, undetermined, counts


def _mixed_text_files(repo):
    return _scan_line_endings(repo)[0]


def check_line_endings(repo):
    """Mixed CRLF/LF in a tracked TEXT file (L-024).

    Measured 2026-09-08: without the binary class this reported `31 MIXED` of
    which 31 were PNGs and 0 were text — a 0%-precision `[!!]` standing for
    weeks, whose printed remedy ("use Edit, not `cat >>`") cannot apply to a PNG.
    A file that cannot be read is `undetermined`: reported, never counted as a
    defect — the invariant may only rule on what it can determine.
    """
    mixed, undetermined, counts = _scan_line_endings(repo)
    ok = not mixed
    tail = "" if not undetermined else ", %d undetermined: %s" % (
        len(undetermined), ", ".join(undetermined[:2]))
    if ok:
        detail = "0 mixed of %d text (%d binary excluded)%s" % (
            counts["text"], counts["binary"], tail)
        return True, detail, ""
    detail = "%d MIXED of %d text (%d binary excluded)%s: %s" % (
        len(mixed), counts["text"], counts["binary"], tail, ", ".join(mixed[:4]))
    return False, detail, (
        "appending with `cat >>` onto a CRLF file is the cause — use Edit (L-024). "
        "Full list: python tools/shell-audit/invariants.py --list-mixed")


def check_gitattributes(repo):
    p = os.path.join(repo, ".gitattributes")
    if not os.path.isfile(p):
        return False, "missing", "line endings fall back to per-machine core.autocrlf (D-038)"
    # one probe per consumer class (rule-registry "line endings", 2026-10-01):
    # human-read -> crlf, machine-read -> lf, a script whose interpreter needs lf -> lf
    probes = [("README.md", "crlf"), ("CLAUDE.md", "lf"),
              ("tools/memory-pipeline/provider-episodic/scripts/bump-version.sh", "lf")]
    bad = []
    for f, want in probes:
        if not os.path.exists(os.path.join(repo, f)):
            continue
        out = git(repo, "check-attr", "eol", "--", f)
        if ("eol: " + want) not in out:
            bad.append("%s -> %s (want %s)" % (f, out.strip().split(": ")[-1], want))
    ok = not bad
    return ok, ("resolves correctly" if ok else "; ".join(bad)), ""


def check_guard_registered(repo):
    p = os.path.join(repo, "settings.json")
    try:
        raw = io.open(p, encoding="utf-8-sig").read()
        d = json.loads(raw)
    except Exception as e:
        return False, "settings.json unreadable (%s)" % e, ""
    cmds = [h.get("command", "") for blk in d.get("hooks", {}).get("PreToolUse", [])
            for h in blk.get("hooks", [])]
    ok = any("shell_transport_guard" in c for c in cmds)
    return ok, ("registered in PreToolUse" if ok else "NOT registered"), \
        "" if ok else "the hook file is inert without a settings.json entry"


def check_guard_telemetry(repo):
    p = os.path.join(repo, "telemetry", "shell-transport-guard.jsonl")
    if not os.path.isfile(p):
        return True, "no rows yet (guard has not fired)", ""
    deny = notice = 0
    for line in io.open(p, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("verdict") == "deny":
            deny += 1
        elif r.get("verdict") == "notice":
            notice += 1
    total = deny + notice
    return True, ("%d rows: %d deny / %d notice  (backtested %.2f%% deny / %.1f%% notice "
                  "of ALL Bash calls — compare with `sweep.py`)"
                  % (total, deny, notice, GUARD_DENY_BASELINE, GUARD_NOTICE_BASELINE)), \
        ("a notice rate far above %.1f%% means the sink patterns drifted" % GUARD_NOTICE_BASELINE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=os.path.join(os.path.expanduser("~"), ".claude"))
    ap.add_argument("--list-mixed", action="store_true",
                    help="print every mixed-ending TEXT file (the repair sites the "
                         "line-endings verdict summarises), one per line")
    a = ap.parse_args()
    repo = os.path.abspath(a.repo)

    if a.list_mixed:
        ok, detail, _hint = check_line_endings(repo)
        print(detail)
        if ok:
            return 0
        for f in _mixed_text_files(repo):
            print(f)
        return 1

    checks = [
        ("line endings: no mixed-ending tracked file", check_line_endings),
        (".gitattributes present and resolving", check_gitattributes),
        ("shell_transport_guard registered", check_guard_registered),
        ("guard telemetry (informational)", check_guard_telemetry),
    ]
    print("repo: %s" % repo)
    print()
    failed = 0
    for name, fn in checks:
        try:
            ok, detail, hint = fn(repo)
        except Exception as e:
            ok, detail, hint = False, "check raised %s" % e, ""
        print("  [%s] %-42s %s" % ("ok" if ok else "!!", name, detail))
        if not ok:
            failed += 1
            if hint:
                print("       -> %s" % hint)
    print()
    print("%d/%d hold" % (len(checks) - failed, len(checks)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
