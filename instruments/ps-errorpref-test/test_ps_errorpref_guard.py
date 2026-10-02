r"""Synthetic test suite for hooks/ps_errorpref_guard.py.

Run: python test_ps_errorpref_guard.py [path-to-hook]
Default hook path: ~/.claude/hooks/ps_errorpref_guard.py

TWO-SIDED CALIBRATION (global CLAUDE.md gate rule; ops/lessons.md L-025). A gate
that fires on everything scores 100% on a one-sided calibration, and a gate that
fires on nothing scores 100% on the other side. Both halves are here, and the
known-FALSE half is the load-bearing one: this guard's entire justification is
that it costs nothing to read, which stops being true the moment it talks over
scripts that are already correct.

This suite exists in the same commit as the hook for a specific reason recorded
in L-025: the mechanism it guards was itself created because a rule that was
correct, current and always in context still failed to fire. Shipping its
enforcement WITHOUT the calibration the same rule demands would have been the
fourth entry in that ledger.

The negative cases are not invented. N1-N4 are shapes taken from the corpus
scan of 2026-08-21: pure-cmdlet scripts under 'Stop' (the single most common
EAP='Stop' shape in the tree), comments explaining the trap, and the CORRECTED
run_arm.ps1 pattern that scopes the preference around the native call.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (
    Path.home() / ".claude" / "hooks" / "ps_errorpref_guard.py")
PY = sys.executable

RESULTS = []


# The suite drives the REAL hook but redirects its telemetry: a synthetic row in
# the production log makes the measured fire rate wrong forever, and the
# neighbouring guard's registry entry already carries a "discount the first ~90
# rows" caveat because its suite does not do this (integrity-sweep check 20,
# P-005).
TMPLOG = os.path.join(tempfile.mkdtemp(prefix="eap-test-"), "log.jsonl")
ENV = dict(os.environ, PS_ERRORPREF_LOG=TMPLOG)


def run(tool, tool_input):
    payload = {"tool_name": tool, "tool_input": tool_input,
               "session_id": "synthtest-eap", "cwd": "C:/tmp"}
    p = subprocess.run([PY, str(HOOK)], input=json.dumps(payload),
                       capture_output=True, text=True, encoding="utf-8", env=ENV)
    out = (p.stdout or "").strip()
    decision, reason = "allow", ""
    if out:
        try:
            d = json.loads(out).get("hookSpecificOutput", {})
            if d.get("permissionDecision"):
                decision = d["permissionDecision"]
                reason = d.get("permissionDecisionReason", "")
            elif "additionalContext" in d:
                decision, reason = "notice", d["additionalContext"]
        except Exception:
            decision = "UNPARSEABLE-OUTPUT"
    return p.returncode, decision, reason


def check(name, expect, tool, tool_input, must_contain=None):
    rc, decision, reason = run(tool, tool_input)
    ok = (decision == expect) and rc == 0
    if ok and must_contain:
        ok = must_contain in reason
    RESULTS.append((ok, name, expect, decision, reason[:90]))


def ps(cmd):
    return {"command": cmd}


def wr(path, content):
    return {"file_path": path, "content": content}


def ed(path, new):
    return {"file_path": path, "old_string": "x", "new_string": new}


# ============================================================ known TRUE (fire)
# The ticket's own required positive: EAP=Stop plus `git ...`.
check("T1 EAP=Stop + bare `git` (the ticket's required positive)", "notice",
      "PowerShell", ps("$ErrorActionPreference = 'Stop'\ngit status --porcelain"))

check("T2 the real incident shape: Stop at top, native exe later in a .ps1",
      "notice", "Write",
      wr("D:/proj/tools/run_arm.ps1",
         "$ErrorActionPreference = 'Stop'\n"
         "$runDir = 'D:/runs/x'\n"
         "Push-Location $runDir\n"
         "$stdout = (Get-Content $PromptFile -Raw) | & claude @claudeArgs | Out-String\n"
         "Pop-Location\n"))

check("T3 stderr IS redirected -> the false-abort half is named as live",
      "notice", "PowerShell",
      ps("$ErrorActionPreference='Stop'; dotnet build -v minimal 2>&1 | Out-Null"),
      must_contain="ACTIVE HERE")

check("T4 no stderr redirect -> the dormant wording, not the live one",
      "notice", "PowerShell",
      ps("$ErrorActionPreference='Stop'\ndotnet build -v minimal\nWrite-Output done"),
      must_contain="dormant")

check("T5 no $LASTEXITCODE anywhere -> the missed-exit-code half is named",
      "notice", "PowerShell",
      ps("$ErrorActionPreference='Stop'\npython -m pytest tests/"),
      must_contain="nothing here reads $LASTEXITCODE")

check("T6 call operator against a variable holding an exe", "notice", "Write",
      wr("C:/tmp/probe.ps1",
         "$ErrorActionPreference = 'Stop'\n$py = 'C:/py/python.exe'\n& $py -c \"print(1)\"\n"))

check("T7 explicit .exe token at command position", "notice", "Write",
      wr("C:/tmp/verify.ps1",
         "$ErrorActionPreference = 'Stop'\n.\\dist\\BatchRenameStudio.exe --plan\n"))

check("T8 Edit fragment carrying both halves", "notice", "Edit",
      ed("D:/proj/publish.ps1",
         "$ErrorActionPreference = 'Stop'\ndotnet publish -c Release\n"))

check("T9 Bash heredoc writing a .ps1", "notice", "Bash",
      ps("cd D:/proj && cat > /tmp/smoke.ps1 <<'PSEOF'\n"
         "$ErrorActionPreference = 'Stop'\n"
         "npm.cmd run build\n"
         "PSEOF"))

check("T10 Stop set AFTER an early Continue still governs a later call",
      "notice", "PowerShell",
      ps("$ErrorActionPreference='Continue'\ngit fetch\n"
         "$ErrorActionPreference='Stop'\ngit push"))

# ========================================================== known FALSE (quiet)
# The load-bearing half. Every one of these is a shape the corpus actually
# contains, and a guard that talks over them is noise, not a control.
check("N1 EAP=Stop with cmdlets ONLY (the ticket's required negative)", "allow",
      "PowerShell",
      ps("$ErrorActionPreference = 'Stop'\n"
         "New-Item -ItemType Directory -Path C:/tmp/x -Force | Out-Null\n"
         "Copy-Item C:/a/b.txt C:/tmp/x/\n"
         "Get-ChildItem C:/tmp/x | Select-Object Name, Length\n"))

check("N2 the CORRECTED run_arm.ps1 shape: preference scoped around the call",
      "allow", "Write",
      wr("D:/proj/tools/run_arm.ps1",
         "$ErrorActionPreference = 'Stop'\n"
         "New-Item -ItemType Directory -Path $runDir -Force | Out-Null\n"
         "$prevEap = $ErrorActionPreference\n"
         "$ErrorActionPreference = 'Continue'\n"
         "$stdout = (Get-Content $PromptFile -Raw) | & claude @claudeArgs | Out-String\n"
         "$exit = $LASTEXITCODE\n"
         "$ErrorActionPreference = $prevEap\n"))

check("N3 a COMMENT explaining the trap is not an assignment", "allow", "Write",
      wr("D:/proj/tools/run_arm.ps1",
         "# No 2>&1 here. Under $ErrorActionPreference='Stop', redirecting a native\n"
         "# exe's stderr makes PowerShell 5.1 wrap each stderr line in an\n"
         "# ErrorRecord, so judge the call by $LASTEXITCODE instead.\n"
         "git status --porcelain\n"))

check("N4 block comment <# ... #> explaining the trap", "allow", "Write",
      wr("D:/proj/tools/publish.ps1",
         "<#\n.SYNOPSIS\n  Publishes the exe.\n.NOTES\n"
         "  Do not set $ErrorActionPreference = 'Stop' here: dotnet writes to\n"
         "  stderr on restore and it would abort at exit 0.\n#>\n"
         "dotnet publish -c Release\n"))

check("N5 EAP set to Continue, never to Stop", "allow", "PowerShell",
      ps("$ErrorActionPreference='Continue'; git --version; dotnet --info"))

check("N6 native exe with NO EAP assignment at all", "allow", "PowerShell",
      ps("git status --porcelain; if ($?) { dotnet build }"))

check("N7 EAP=Stop then only ALIASES that look native but are cmdlets", "allow",
      "PowerShell",
      ps("$ErrorActionPreference='Stop'\n"
         "curl https://example.com/x.json | Out-File x.json\n"
         "echo done\nls C:/tmp\ncat C:/tmp/x.txt\nsort C:/tmp/x.txt\n"))

check("N8 native call BEFORE the Stop assignment is not governed by it", "allow",
      "PowerShell",
      ps("git fetch --all\n$ErrorActionPreference='Stop'\n"
         "Get-ChildItem . | Measure-Object\n"))

check("N9 Stop cleared before the native call by an unrecognised RHS", "allow",
      "PowerShell",
      ps("$ErrorActionPreference='Stop'\nRemove-Item C:/tmp/x -Recurse -Force\n"
         "$ErrorActionPreference=$saved\ngit push origin main\n"))

check("N10 `& { scriptblock }` is not a native invocation", "allow", "PowerShell",
      ps("$ErrorActionPreference='Stop'\n$sb = { Get-Date }\n$null = & { Get-Date }\n"))

check("N11 a .ps1 whose text merely MENTIONS git in a string", "allow", "Write",
      wr("C:/tmp/x.ps1",
         "$ErrorActionPreference = 'Stop'\n"
         "Write-Output 'run git status by hand afterwards'\n"
         "Set-Content -Path C:/tmp/note.txt -Value 'dotnet build is not run here'\n"))

check("N12 non-.ps1 Write is not PowerShell text", "allow", "Write",
      wr("C:/tmp/notes.md",
         "$ErrorActionPreference = 'Stop'\ngit status\n"))

check("N13 non-.ps1 Edit is not PowerShell text", "allow", "Edit",
      ed("C:/tmp/notes.md", "$ErrorActionPreference = 'Stop'\ndotnet build\n"))

check("N14 Bash command with no .ps1 in it", "allow", "Bash",
      ps("$ErrorActionPreference = 'Stop'; git status"))

check("N15 Read tool is not in scope at all", "allow", "Read",
      {"file_path": "C:/tmp/x.ps1"})

check("N16 escape hatch honoured", "allow", "PowerShell",
      ps("$ErrorActionPreference='Stop'  # [eap-checked]\ngit push"))

check("N17 empty command", "allow", "PowerShell", ps(""))

check("N18 `cmd /c` swallows stderr -> not reported as the live half", "notice",
      "PowerShell",
      ps("$ErrorActionPreference='Stop'\ncmd /c \"git status\" 2>&1"),
      must_contain="dormant")

# ============================== regression: the three defects the backtest found
# All three were live in the first version and none was visible to the 33 cases
# above. They are here so a later edit cannot quietly restore them.
check("B1 the reported line is the CALL's line, not the one before it",
      "notice", "Write",
      wr("C:/tmp/publish.ps1",
         "$ErrorActionPreference = 'Stop'\n"
         "Write-Host '== building =='\n"
         "dotnet publish -c Release\n"),
      must_contain="dotnet publish -c Release")

check("B2 stderr redirect is detected on the CALL's own line", "notice", "Write",
      wr("C:/tmp/probe.ps1",
         "$ErrorActionPreference = 'Stop'\n"
         "Write-Host 'no redirect on this line'\n"
         "dotnet build -v minimal 2>&1 | Out-Null\n"),
      must_contain="ACTIVE HERE")

check("B3 `& $sb` where the variable holds a SCRIPT BLOCK is not native",
      "allow", "Write",
      wr("C:/tmp/measure.ps1",
         "$ErrorActionPreference = 'Stop'\n"
         "$Condition = { (Get-Date).Second -gt 30 }\n"
         "$value = & $Condition\n"
         "Write-Output $value\n"))

check("B4 `& $x` where the variable holds another .ps1 is not native", "allow",
      "Write",
      wr("C:/tmp/start.ps1",
         "$ErrorActionPreference = 'Stop'\n"
         "$BootstrapScript = Join-Path $PSScriptRoot 'bootstrap-backend.ps1'\n"
         "& $BootstrapScript -Cuda\n"))

check("B5 `& $x` where the variable resolves to an .exe IS native", "notice",
      "Write",
      wr("C:/tmp/run.ps1",
         "$ErrorActionPreference = 'Stop'\n"
         "$VenvPython = Join-Path $Root '.venv\\Scripts\\python.exe'\n"
         "& $VenvPython -m pip install -r requirements.txt\n"))

check("B6 `[scriptblock]` parameter is not native", "allow", "Write",
      wr("C:/tmp/wait.ps1",
         "$ErrorActionPreference = 'Stop'\n"
         "function Wait-For([scriptblock]$Condition) { while (-not (& $Condition)) "
         "{ Start-Sleep 1 } }\n"))

check("B7 Bash heredoc: only the .ps1 BODY is analysed, not the bash around it",
      "allow", "Bash",
      ps("cd D:/proj && cat > /tmp/x.ps1 <<'PSEOF'\n"
         "$ErrorActionPreference = 'Stop'\n"
         "Get-ChildItem . | Measure-Object\n"
         "PSEOF\n"
         "powershell.exe -ExecutionPolicy Bypass -File /tmp/x.ps1"))

check("B8a a native name inside a STRING is not a call (the `(npm ...)` case)",
      "allow", "Write",
      wr("C:/tmp/build.ps1",
         "$ErrorActionPreference = 'Stop'\n"
         "Write-Host \"==> clean frontend build (npm ci + npm run build)\"\n"
         "Copy-Item a b\n"))

check("B8b a native name inside a HERE-STRING is not a call", "allow", "Write",
      wr("C:/tmp/note.ps1",
         "$ErrorActionPreference = 'Stop'\n"
         "$readme = @'\n"
         "Run these by hand:\n"
         "git pull\n"
         "dotnet build\n"
         "'@\n"
         "Set-Content -Path README.txt -Value $readme\n"))

check("B8c a real `(git ...)` sub-expression still fires", "notice", "Write",
      wr("C:/tmp/head.ps1",
         "$ErrorActionPreference = 'Stop'\n"
         "$sha = (git rev-parse HEAD)\n"))

check("B8 ... but a native call INSIDE the body still fires", "notice", "Bash",
      ps("cd D:/proj && cat > /tmp/y.ps1 <<'PSEOF'\n"
         "$ErrorActionPreference = 'Stop'\n"
         "& taskkill.exe /pid $p.Id /t /f 2>&1 | Out-Null\n"
         "PSEOF\n"
         "powershell.exe -File /tmp/y.ps1"))

# ============================================== class closure over var_kind()
# `var_kind()` classifies the variable in `& $x` over an ENUMERATED set of
# kinds -- block / script / native -- and the hook's docstring closes it:
# "'unknown' is dropped, which costs a few genuine hits (a path built by
# Get-ChildItem) and buys the removal of a whole wrong class -- the declared
# error direction". B3/B4/B5 exercise the three enumerated kinds; nothing until
# now fed an assignment that matches NONE of them. `(Get-Command claude).Source`
# is that input, and it is the shape a script uses to resolve an exe by name.
# Two assertions: the emitted verdict, and the kind BY NAME -- because silence
# alone cannot tell "I could not classify this" apart from "I classified it as
# harmless", and only the second reading is the honest one here.
UNDET_PS1 = ("$ErrorActionPreference = 'Stop'\n"
             "$Tool = (Get-Command claude).Source\n"
             "& $Tool --version\n")
check("U1 undetermined `& $x`: assignment names no enumerated kind -> stays quiet",
      "allow", "Write", wr("C:/tmp/resolve.ps1", UNDET_PS1))

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("eap_hook_under_test", HOOK)
_hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_hook)
_kind = _hook.var_kind(UNDET_PS1, "Tool")
RESULTS.append((_kind == "unknown",
                "U2 ... and var_kind() names that undetermined kind 'unknown', "
                "never folding it into 'native'",
                "unknown", _kind, ""))

# ================================================================== robustness
p = subprocess.run([PY, str(HOOK)], input="not json at all",
                   capture_output=True, text=True, encoding="utf-8")
RESULTS.append((p.returncode == 0 and not (p.stdout or "").strip(),
                "R1 malformed stdin fails open", "allow", "allow", ""))

p = subprocess.run([PY, str(HOOK)], input=json.dumps({"tool_name": "PowerShell"}),
                   capture_output=True, text=True, encoding="utf-8")
RESULTS.append((p.returncode == 0, "R2 missing tool_input fails open",
                "allow", "allow", ""))

p = subprocess.run([PY, str(HOOK)],
                   input=json.dumps({"tool_name": "Write",
                                     "tool_input": {"file_path": None,
                                                    "content": ["not", "a", "string"]}}),
                   capture_output=True, text=True, encoding="utf-8")
RESULTS.append((p.returncode == 0, "R3 wrong-typed tool_input fails open",
                "allow", "allow", ""))

# A 400 KB .ps1: the guard sits on Write, so it must not be quadratic on size.
import time  # noqa: E402
big = ("$ErrorActionPreference = 'Stop'\n" + "Write-Output 'x'\n" * 20000 +
       "git status\n")
t0 = time.time()
rc, decision, reason = run("Write", wr("C:/tmp/big.ps1", big))
dt = time.time() - t0
RESULTS.append((rc == 0 and decision == "notice" and dt < 5.0,
                "R4 400KB .ps1 handled in %.2fs" % dt, "notice", decision, ""))

# ============================================================== proof of write
# E1 asserts the row lands in the REDIRECTED log; E2 asserts the production log
# gained nothing. E2 is the half that keeps the measured fire rate usable -- the
# neighbouring guard's registry entry has to say "discount the first ~90 rows,
# the test suite writes real entries", and a rate you must subtract from is a
# rate nobody re-checks.
log = Path(TMPLOG)
before = log.read_text(encoding="utf-8").count("\n") if log.exists() else 0
prod = Path.home() / ".claude" / "telemetry" / "ps-errorpref-guard.jsonl"
prod_before = prod.read_text(encoding="utf-8").count("\n") if prod.exists() else 0
uniq = "MARKER-" + "q" * 10
run("Write", wr("C:/tmp/%s.ps1" % uniq,
                "$ErrorActionPreference='Stop'\ngit status\n"))
after = log.read_text(encoding="utf-8") if log.exists() else ""
RESULTS.append((uniq in after and after.count("\n") > before,
                "E1 the notice is recorded in telemetry (proof of life)",
                "logged", "logged" if uniq in after else "MISSING", ""))
prod_after = prod.read_text(encoding="utf-8").count("\n") if prod.exists() else 0
RESULTS.append((prod_after == prod_before,
                "E2 the PRODUCTION telemetry gained no synthetic rows",
                "untouched", "untouched" if prod_after == prod_before else "POLLUTED", ""))

# ===================================================================== report
print("=" * 78)
print("ps_errorpref_guard  -  %s" % HOOK)
print("=" * 78)
passed = 0
for ok, name, expect, got, reason in RESULTS:
    print("  %s  %-56s expect=%-7s got=%s" % ("PASS" if ok else "FAIL", name, expect, got))
    if not ok and reason:
        print("        got reason: %s" % reason)
    passed += 1 if ok else 0
print("-" * 78)
n_fire = sum(1 for r in RESULTS if r[3] == "notice")
n_quiet = sum(1 for r in RESULTS if r[3] == "allow")
print("  %d/%d passed" % (passed, len(RESULTS)))
print("  two-sided: %d cases MUST fire, %d cases MUST stay quiet "
      "(a gate that always fires fails the second half, and vice versa)"
      % (sum(1 for r in RESULTS if r[2] == "notice"),
         sum(1 for r in RESULTS if r[2] == "allow")))
print("  observed: notice %d, allow %d" % (n_fire, n_quiet))
sys.exit(0 if passed == len(RESULTS) else 1)
