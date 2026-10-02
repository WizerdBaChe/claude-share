"""Synthetic test suite for hooks/shell_transport_guard.py.

Run: python test_shell_transport_guard.py [path-to-hook]
Default hook path: ~/.claude/hooks/shell_transport_guard.py

TWO-SIDED CALIBRATION (global CLAUDE.md gate rule). A gate that rejects
everything scores 100% on a one-sided calibration, so this suite carries both
known-TRUE cases (the guard MUST deny) and known-FALSE cases (the guard MUST
let through). The known-FALSE half is the load-bearing half: the guard's whole
justification is that routing costs nothing, which stops being true the moment
it blocks ordinary inspection commands.

The negative cases are not invented - they are the shapes that made up the
4,720 Bash calls in the 10-day sweep that carried no doubled backslash, plus
the inspection-with-backslashes shape that the sweep showed is common and
harmless (its damage is visible in the same turn's output).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (
    Path.home() / ".claude" / "hooks" / "shell_transport_guard.py")
PY = sys.executable
# CLAUDE_TELEMETRY_DIR (ruling 2026-09-11): this suite's session_id
# "synthtest-transport" is a readable literal, but nothing redirected the
# hook's writer, so its deny rows still landed in production
# telemetry/shell-transport-guard.jsonl (797 of 1190 rows per the 2026-09-10
# inventory). One temp dir for the whole run fixes that at the source.
_TELEMETRY_DIR = tempfile.mkdtemp(prefix="shell-transport-test-")
_ENV = dict(os.environ, CLAUDE_TELEMETRY_DIR=_TELEMETRY_DIR)

B2 = "\\" * 2
B4 = "\\" * 4


def run(tool, command, extra=None):
    payload = {
        "tool_name": tool,
        "tool_input": {"command": command},
        "session_id": "synthtest-transport",
        "cwd": "C:/tmp",
    }
    if extra:
        payload.update(extra)
    p = subprocess.run([PY, str(HOOK)], input=json.dumps(payload),
                       capture_output=True, text=True, encoding="utf-8", env=_ENV)
    out = (p.stdout or "").strip()
    decision, reason = None, ""
    if out:
        try:
            d = json.loads(out).get("hookSpecificOutput", {})
            decision = d.get("permissionDecision")
            reason = d.get("permissionDecisionReason") or d.get("additionalContext") or ""
            if decision is None and "additionalContext" in d:
                decision = "notice"
        except Exception:
            pass
    return p.returncode, decision, reason


RESULTS = []


def check(name, expect, tool, command, extra=None):
    rc, decision, reason = run(tool, command, extra)
    got = decision or "allow"
    ok = (got == expect) and rc == 0
    RESULTS.append((ok, name, expect, got, reason[:70]))
    return ok


# ------------------------------------- known TRUE (size ceiling: DENY)
# Only the size rule vetoes. It is the only one the gate can fully determine:
# 7 hits in 5,113 real calls, all 7 of which had already failed.
big_body = "x = 1\n" * 1400                      # ~8.4 KB
check("T1 command exactly at the measured ceiling (7700 B)", "deny", "Bash",
      "echo " + "a" * 7695)          # len("echo ") == 5 -> exactly SIZE_LIMIT
check("T2 one byte under the ceiling must pass", "allow", "Bash",
      "echo " + "a" * 7694)          # 7699 B — the boundary is exercised both ways
check("T3 oversized heredoc write", "deny", "Bash",
      "cat > big.py <<'EOF'\n" + big_body + "EOF")

# --------------- backslash collapse: ANNOTATE, never veto (see docstring)
# The backtest that forced this: 112 flagged / 89 of them had SUCCEEDED, and
# sampling showed a large share were deliberate compensation for the very
# collapse being flagged. Compensation and naive escaping are byte-identical,
# so a veto here would be wrong roughly three times out of four.
check("A1 heredoc to file carrying a doubled backslash -> notice", "notice", "Bash",
      "cat > out.py <<'EOF'\np = 'C:" + B2 + "Users" + B2 + "x'\nEOF")
check("A2 python heredoc carrying a doubled backslash -> notice", "notice", "Bash",
      "python - <<'PY'\ns = 'a" + B2 + "b'\nprint(s)\nPY")
check("A3 inline python -c carrying a doubled backslash -> notice", "notice", "Bash",
      'python -c "print(\'C:' + B2 + 'Users\')"')
check("A4 sed -i carrying a doubled backslash -> notice", "notice", "Bash",
      "sed -i 's/a/" + B2 + "n/' notes.md")
check("A5 redirect to a .py file -> notice", "notice", "Bash",
      'printf "%s" "p=\'a' + B2 + 'b\'" > gen.py')
check("A6 quadruple backslash (compensation shape) is NOT vetoed", "notice", "Bash",
      "cat > x.py <<'EOF'\np = 'a" + B4 + "b'\nEOF")

# ---- which NOTICE fires: durable sink vs "no sink recognised" (2026-09-09) ----
# The finding this closes (F-2 of the AP-62 drain): CONTENT_SINKS decided
# membership by an EXTENSION LIST that omitted .rb/.go/.rs/.java/.lua, so
# `printf … > gen.rb` matched nothing and the fall-through notice then ASSERTED
# "Nothing here writes the result to a file" — false, and told the reader the
# damage was visible in this turn when it was not. Lengthening the list would
# have left the same false claim waiting for the next unlisted extension
# (L-044), so the redirect itself became the predicate. These cases pin the
# BRANCH, not just the decision: the decision is `notice` either way, so a case
# that only asserted "notice" could not fail on the defect (L-062).
DURABLE = "lands durably"
NO_SINK = "No redirect, heredoc, in-place edit or inline-source shape"


def branch(name, want, command):
    rc, decision, reason = run("Bash", command)
    got = DURABLE if DURABLE in reason else (NO_SINK if NO_SINK in reason else "(neither)")
    RESULTS.append((rc == 0 and decision == "notice" and got == want,
                    name, "notice/" + ("sink" if want == DURABLE else "no-sink"),
                    "notice/" + ("sink" if got == DURABLE else
                                 "no-sink" if got == NO_SINK else got),
                    reason[:70]))


branch("A7 redirect to .rb — the extension the old list omitted", DURABLE,
       'printf "%s" "p=\'a' + B2 + 'b\'" > gen.rb')
branch("A8 redirect to .go", DURABLE, 'echo "a' + B2 + 'b" > main.go')
branch("A9 an extension NO list will ever carry is still a sink", DURABLE,
       'echo "a' + B2 + 'b" > payload.zzz')
branch("A10 append redirect to an unlisted extension", DURABLE,
       'echo "a' + B2 + 'b" >> notes.rst')
# Negative controls for REDIRECT_ANY — without these, a pattern that called
# EVERY command a sink would pass A7–A10 and look correct.
branch("A11 fd dup (2>&1) is not a file sink", NO_SINK,
       "grep -c 'a" + B2 + "b' report.md 2>&1")
branch("A12 /dev/null is not durable", NO_SINK,
       "echo 'a" + B2 + "b' > /dev/null")
branch("A13 a quoted arrow is not a redirect", NO_SINK,
       "echo 'a" + B2 + "b => c' | wc -c")
branch("A14 plain inspection still reaches the no-sink branch", NO_SINK,
       "grep -c '" + B2 + "' report.md")
# The claim itself: the no-sink notice must never assert the universal negative
# it used to. This is the case that fails if someone restores the old wording.
_rc, _d, _reason = run("Bash", "grep -c '" + B2 + "' report.md")
RESULTS.append(("Nothing here writes" not in _reason and "limit of what it checks" in _reason,
                "A15 the no-sink notice states what it CHECKED, never 'nothing here writes'",
                "bounded claim", "bounded claim" if "limit of what it checks" in _reason
                else "universal claim", _reason[:70]))

# --------------------------------------------------------------- known FALSE
check("F1 ordinary command, no backslashes", "allow", "Bash",
      "git status --porcelain && ls -la")
check("F2 single backslashes only (safe: transport leaves them alone)", "allow", "Bash",
      'ls "C:\\Users\\x\\.claude"')
check("F3 heredoc write with no backslashes at all", "allow", "Bash",
      "cat > notes.md <<'EOF'\nplain text only\nEOF")
check("F4 large but under the ceiling", "allow", "Bash",
      "echo " + "a" * 7000)
check("F5 PowerShell tool: probed clean, must fall through", "allow", "PowerShell",
      "$t = @'\np = 'C:" + B2 + "Users'\n'@; [IO.File]::WriteAllText('x.py', $t)")
check("F6 Write tool: different tool entirely", "allow", "Write",
      "irrelevant")
check("F7 escape hatch honoured", "allow", "Bash",
      "cat > x.py <<'EOF'  [transport-checked]\np = 'a" + B2 + "b'\nEOF")
check("F8 empty command", "allow", "Bash", "")
check("F9 oversized command with the escape hatch still passes", "allow", "Bash",
      "echo [transport-checked] " + "a" * 7700)

# ------------------------------------------- downgrade-and-forward (not deny)
check("N1 inspection with doubled backslash -> notice, never deny", "notice", "Bash",
      "grep -c '" + B2 + "' report.md")
check("N2 inspection, no sink, no redirect -> notice", "notice", "Bash",
      "echo 'a" + B2 + "b' | wc -c")

# --------------- (3) MSYS path conversion of Windows-native /flags (L-029)
# Observed 2026-08-23: `cmd /c ...` arrived as `cmd C:/ ...` (interactive cmd,
# 300 s silent hang) and `taskkill /PID` errored on `C:/Program Files/Git/PID`.
# ANNOTATE only; the known-FALSE half carries MSYS's own escapes.
check("M1 cmd /c at command position -> notice", "notice", "Bash",
      "cmd /c npx -y @playwright/mcp@latest")
check("M2 taskkill /PID -> notice", "notice", "Bash",
      "taskkill /PID 95716 /T /F")
check("M3 chained after && -> notice", "notice", "Bash",
      "sleep 1 && taskkill /F /IM node.exe")
check("M4 reg query with /v after a quoted key -> notice", "notice", "Bash",
      'reg query "HKCU\\Software\\Foo" /v Bar')
check("M5 POSIX path to a POSIX tool is not a Windows flag", "allow", "Bash",
      "ls -la /c/Users/x")
check("M6 doubled slash (MSYS escape) passes", "allow", "Bash",
      "cmd //c dir")
check("M7 MSYS_NO_PATHCONV prefix passes", "allow", "Bash",
      "MSYS_NO_PATHCONV=1 taskkill /PID 1 /F")
check("M8 'net' inside 'dotnet' is not the exe", "allow", "Bash",
      "dotnet build /p:Configuration=Release")

# --------------- (4) unquoted Windows drive path (2026-09-20)
# Backtest: 29 flagged in 53,458 recorded Bash calls, 29 true, 0 scanner
# misreads. The known-FALSE half is the load-bearing half again: every QUOTED
# spelling, every heredoc body and every non-Bash tool must pass untouched.
BS = "\\"
WIN = "D:" + BS + "work" + BS + "pipeline"
check("P1 find with an unquoted drive path and stderr discarded -> deny", "deny", "Bash",
      "find " + WIN + ' -type f -name "*.html" 2>/dev/null | head -10')
check("P2 grep -r with the unquoted path as a middle argument -> deny", "deny", "Bash",
      'grep -r "T-022" C:' + BS + "Users" + BS + "x" + BS + '.claude --include="*.md"')
check("P3 unquoted path as an option value after && -> deny", "deny", "Bash",
      "cd /c/x && python t.py --source C:" + BS + "Users" + BS + "x")
check("P4 double-quoted path passes", "allow", "Bash", 'find "' + WIN + '" -name "*.html"')
check("P5 single-quoted path passes", "allow", "Bash", "ls '" + WIN + "'")
check("P6 forward slashes pass", "allow", "Bash", "ls D:/work/pipeline")
check("P7 POSIX drive spelling passes", "allow", "Bash", "ls /d/work/pipeline")
check("P8 path inside a quoted heredoc body passes", "allow", "Bash",
      "python - <<'PY'\nfrom pathlib import Path\np = Path(r\"" + WIN + "\")\nprint(p)\nPY")
check("P9 quoted path inside $( ) inside double quotes passes (the first draft's misread)",
      "allow", "Bash", 'echo "lines=$(wc -l < "' + WIN + BS + 'a.py")"')
check("P10 path in a # comment passes", "allow", "Bash", "ls /tmp  # was " + WIN)
check("P11 escape hatch honoured", "allow", "Bash", "echo " + WIN + " [transport-checked]")
check("P12 PowerShell tool is out of scope", "allow", "PowerShell", "Get-ChildItem " + WIN)
check("P13 backtick substitution makes the quoting unresolvable -> notice, never deny",
      "notice", "Bash", "echo `date`; ls " + WIN)
check("P14 path after a TERMINATED heredoc is back in scope -> deny", "deny", "Bash",
      "cat > n.txt <<'EOF'\nplain\nEOF\nls " + WIN)
# Branch pins (L-062): the decision label alone cannot tell rule (4) from the
# size ceiling, so assert the value only rule (4) computes — the delivered form.
_rc, _d, _reason = run("Bash", "find " + WIN + " -name x")
RESULTS.append((_d == "deny" and "D:workpipeline" in _reason
                and "D:/work/pipeline" in _reason,
                "P15 deny reason states what bash would deliver and the forward-slash form",
                "deny+delivered", ("deny+delivered" if "D:workpipeline" in _reason
                                   else str(_d)), _reason[:70]))
_rc, _d, _reason = run("Bash", "echo `date`; ls " + WIN)
RESULTS.append((_d == "notice" and "could not resolve" in _reason,
                "P16 the unresolved branch says it could not resolve the quoting",
                "notice/unresolved", ("notice/unresolved" if "could not resolve" in _reason
                                      else str(_d)), _reason[:70]))

# ------------------------------------------------------------- fail-open
p = subprocess.run([PY, str(HOOK)], input="not json at all",
                   capture_output=True, text=True, encoding="utf-8", env=_ENV)
RESULTS.append((p.returncode == 0 and not (p.stdout or "").strip(),
                "R1 malformed stdin fails open", "allow", "allow", ""))

p = subprocess.run([PY, str(HOOK)], input=json.dumps({"tool_name": "Bash"}),
                   capture_output=True, text=True, encoding="utf-8", env=_ENV)
RESULTS.append((p.returncode == 0, "R2 missing tool_input fails open", "allow", "allow", ""))

# --------------------------------- class closure over the tool surface (AP-62)
# The tool names this guard has evidence about are exactly three: `Bash` (in
# scope, both defects live) and the two PROBED clean against both defects on
# 2026-08-18 -- PowerShell and Write, which is what F5 and F6 assert. Every
# OTHER tool matches none of those classes: it was never probed, so its
# transport is not known to be clean, only unexamined. The guard's declared
# degradation is the scope line in its docstring ("the Bash tool only"):
# `tool_name != "Bash"` exits 0 with no verdict and no telemetry row. The bytes
# below would DENY on Bash -- over the measured size ceiling AND carrying a
# doubled backslash into a durable sink -- so the fall-through here is the scope
# rule doing its job rather than a payload that had nothing to say.
p = subprocess.run(
    [PY, str(HOOK)],
    input=json.dumps({
        "tool_name": "NotebookEdit",
        "tool_input": {"notebook_path": "D:/nb/probe.ipynb", "cell_id": "c1",
                       "new_source": "p = 'C:" + B2 + "Users" + B2 + "x'\n" + big_body},
        "session_id": "synthtest-transport", "cwd": "C:/tmp"}),
    capture_output=True, text=True, encoding="utf-8", env=_ENV)
_spoke = bool((p.stdout or "").strip())
RESULTS.append((p.returncode == 0 and not _spoke,
                "U1 undetermined tool surface (NotebookEdit, never probed) -> the "
                "declared fall-through, not folded into probed-clean",
                "allow", "spoke" if _spoke else "allow", ""))

# ------------------------------------------- evidence-before-veto is real
# Read from _TELEMETRY_DIR (where _ENV's CLAUDE_TELEMETRY_DIR points the hook),
# not the hook's un-isolated default -- this suite now redirects every call.
log = Path(_TELEMETRY_DIR) / "shell-transport-guard.jsonl"
before = log.read_text(encoding="utf-8").count("\n") if log.exists() else 0
uniq = "MARKER-" + "z" * 12
run("Bash", "cat > ev.py <<'EOF'\np = '" + uniq + B2 + "'\nEOF")
after_txt = log.read_text(encoding="utf-8") if log.exists() else ""
RESULTS.append((uniq in after_txt and after_txt.count("\n") > before,
                "E1 denied command persisted in full before the veto",
                "logged", "logged" if uniq in after_txt else "MISSING", ""))

# ---------------------------------------------------------------- report
print("=" * 74)
print("shell_transport_guard  —  %s" % HOOK)
print("=" * 74)
passed = 0
for ok, name, expect, got, reason in RESULTS:
    print("  %s  %-52s expect=%-7s got=%s" % ("PASS" if ok else "FAIL", name, expect, got))
    if not ok and reason:
        print("        reason: %s" % reason)
    passed += 1 if ok else 0
print("-" * 74)
# The tally classifies every row, and says so when it cannot. Added 2026-09-09:
# these buckets used to test `r[3] == "notice"`, so the branch cases below
# (whose observed value is `notice/sink`) fell out of all three and the printed
# total silently disagreed with the case count — the summary stayed plausible
# while describing 31 of 41 rows. That is the same fold this suite's guard
# exists to catch (AP-62), so the classes are matched by PREFIX and anything
# still unnamed is printed rather than dropped.
n_deny = sum(1 for r in RESULTS if r[3].startswith("deny"))
n_allow = sum(1 for r in RESULTS if r[3].startswith("allow"))
n_notice = sum(1 for r in RESULTS if r[3].startswith("notice"))
unclassified = [r for r in RESULTS
                if not r[3].startswith(("deny", "allow", "notice"))]
tail = ""
if unclassified:
    tail = ("; %d row(s) in no decision class, counted nowhere above: %s"
            % (len(unclassified), ", ".join(r[1].split()[0] for r in unclassified)))
print("  %d/%d passed   (deny %d, allow %d, notice %d — two-sided: the allow+notice "
      "half is %d of %d cases%s)"
      % (passed, len(RESULTS), n_deny, n_allow, n_notice,
         n_allow + n_notice, len(RESULTS), tail))
sys.exit(0 if passed == len(RESULTS) else 1)
