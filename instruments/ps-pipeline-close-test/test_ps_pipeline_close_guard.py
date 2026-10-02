r"""Two-sided calibration suite for hooks/ps_pipeline_close_guard.py.

Run: python test_ps_pipeline_close_guard.py [path-to-hook]
Default hook path: ~/.claude/hooks/ps_pipeline_close_guard.py

TWO-SIDED CALIBRATION (global CLAUDE.md gate rule; ops/lessons.md L-019, L-025).
A gate that fires on everything scores 100% on a one-sided calibration, and a
gate that fires on nothing scores 100% on the other side. Both halves are here.
The known-SILENT half is the load-bearing one: this guard denies nothing, so its
whole justification is that it costs nothing to read - which stops being true the
moment it talks over pipelines that are already correct.

The negative cases are not invented. N1, N2, N6, N7, N11, N14 and N18 are shapes
lifted from the corpus scan of 2026-08-21 - cmdlet-to-`Select-Object -First` is
by far the most common `-First` shape in this tree, and N11 is the FIX that
`ops/lessons.md` L-027 prescribes. A guard that fired on the fix would be worse
than no guard.

This suite ships in the same commit as the hook, for the reason recorded in
L-025 fix (a)/(b): the mechanism it guards exists because a rule that was
correct, current and greppable never fired. Shipping its enforcement without the
calibration that same ledger demands would be the next entry.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (
    Path.home() / ".claude" / "hooks" / "ps_pipeline_close_guard.py")
PY = sys.executable

RESULTS = []

# Drive the REAL hook, but redirect its telemetry: a synthetic row in the
# production log makes the measured fire rate wrong forever (integrity-sweep
# check 20, P-005 - `shell_transport_guard`'s registry entry still carries a
# "discount the first ~90 rows" caveat because its suite did not do this).
TMPLOG = os.path.join(tempfile.mkdtemp(prefix="pipeclose-test-"), "log.jsonl")
ENV = dict(os.environ, PS_PIPECLOSE_LOG=TMPLOG,
           CLAUDE_TELEMETRY_DIR=os.path.dirname(TMPLOG))   # deny receipts too


def run(tool, tool_input):
    payload = {"tool_name": tool, "tool_input": tool_input,
               "session_id": "synthtest-pipeclose", "cwd": "C:/tmp"}
    p = subprocess.run([PY, str(HOOK)], input=json.dumps(payload),
                       capture_output=True, text=True, encoding="utf-8", env=ENV)
    out = (p.stdout or "").strip()
    decision, reason = "silent", ""
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
    RESULTS.append((ok, name, expect, decision, reason[:100]))


def ps(cmd):
    return {"command": cmd}


def wr(path, content):
    return {"file_path": path, "content": content}


# ---------------------------------------------------------------- known-FIRE
# Every one of these kills a live process. P1 and P2 are the two recorded hits
# of L-027 in their original wording.
check("P1  interpreter + Select-Object -First (L-027 hit 2)", "deny", "PowerShell",
      ps("python fuzz.py --seed 7 | Select-Object -First 30"), "python")
check("P2  call operator + interpreter (L-027 hit 1 shape)", "deny", "PowerShell",
      ps("& python tools/analyze.py D:/x/runs | Select-Object -First 30"))
check("P3  assignment prefix + `select` alias", "deny", "PowerShell",
      ps("$head = python x.py | select -First 5"))
check("P4  build tool", "deny", "PowerShell",
      ps("dotnet build -c Release | Select-Object -First 20"))
check("P5  pipeline continued across a newline", "deny", "PowerShell",
      ps("python x.py |\n  Select-Object -First 3"))
check("P6  explicit relative .exe", "deny", "PowerShell",
      ps(".\\tools\\run.exe --all | Select-Object -First 2"))
check("P8  native two segments upstream of the closer", "deny", "PowerShell",
      ps("python x.py | ForEach-Object { $_.Trim() } | Select-Object -First 4"))
check("P9  quoted absolute exe path after &", "deny", "PowerShell",
      ps("& \"C:\\Program Files\\tool\\t.exe\" | select -First 1"))
check("P10 & $var whose assignment names an exe", "deny", "PowerShell",
      ps("$exe = 'C:\\t\\a.exe'\n& $exe --scan | Select-Object -First 2"))
check("P11 `| more` is an early-closing consumer too", "deny", "PowerShell",
      ps("python x.py | more"))
check("P12 abbreviated parameter -f", "deny", "PowerShell",
      ps("python x.py | Select-Object -f 3"))
check("P13 the shape written INTO a .ps1 by Write", "notice", "Write",
      wr("D:/x/tools/run_arm.ps1",
         "$ErrorActionPreference = 'Continue'\n"
         "python .\\collect.py --run $Run | Select-Object -First 40\n"))
check("P14 package runner", "deny", "PowerShell",
      ps("npm run build | Select-Object -First 10"))
check("P15 hazard nested inside a foreach block", "deny", "PowerShell",
      ps("foreach ($f in $files) { python score.py $f | Select-Object -First 1 }"))
check("P16 interpreter with a flag before the script", "deny", "PowerShell",
      ps("py -3 tools/x.py | Select -First 8"))
check("P17 Edit that introduces the shape into a .ps1", "notice", "Edit",
      {"file_path": "D:/x/run.ps1", "old_string": "a",
       "new_string": "dotnet test | Select-Object -First 12"})
check("P18 the tier is named in the annotation (work vs report)", "deny",
      "PowerShell", ps("python x.py | Select-Object -First 3"), "L-027")

# ------------------------------------------ deny carries a WORKING retry (2026-09-23)
# The promotion from notice to deny is only cheap if the denial hands back a call
# that runs. So the retry is asserted verbatim AND fed back through the hook: a
# ready-made retry that the same hook denies again would be a loop, not a fix.
RETRY1 = "$out = python fuzz.py --seed 7; $out | Select-Object -First 30"
check("D1  the denial carries the rewritten call", "deny", "PowerShell",
      ps("python fuzz.py --seed 7 | Select-Object -First 30"), RETRY1)
check("D2  ... and that rewritten call passes the same hook", "silent", "PowerShell",
      ps(RETRY1))
RETRY3 = "$head = python x.py; $head | select -First 5"
check("D3  an assignment prefix keeps its own variable", "deny", "PowerShell",
      ps("$head = python x.py | select -First 5"), RETRY3)
check("D4  ... and that rewritten call passes too", "silent", "PowerShell", ps(RETRY3))
check("D5  the same shape WRITTEN into a .ps1 stays a notice (writing kills nothing)",
      "notice", "Write", wr("D:/x/a.ps1", "python fuzz.py --seed 7 | Select-Object -First 30\n"))

# --------------------------------------------------------------- known-SILENT
check("N1  cmdlet upstream - nothing to kill", "silent", "PowerShell",
      ps("Get-ChildItem -Recurse | Select-Object -First 5"))
check("N2  Get-Content -> -First is slow, not hazardous", "silent", "PowerShell",
      ps("Get-Content D:/big.log | Select-Object -First 20"))
check("N3  Select-Object without -First", "silent", "PowerShell",
      ps("python x.py | Select-Object Name, Length"))
check("N4  Where-Object consumes the whole pipeline", "silent", "PowerShell",
      ps("python x.py | Where-Object { $_ -match 'ok' }"))
check("N5  Out-String consumes the whole pipeline", "silent", "PowerShell",
      ps("python x.py 2>&1 | Out-String"))
check("N6  Get-Process | Select -First", "silent", "PowerShell",
      ps("Get-Process | Sort-Object CPU -Desc | Select-Object -First 3"))
check("N7  the shape quoted inside a string", "silent", "PowerShell",
      ps("Write-Host \"run: python x.py | Select-Object -First 30\""))
check("N8  the shape in a whole-line comment", "silent", "Write",
      wr("D:/x/a.ps1", "# never: python x.py | Select-Object -First 30\nGet-Date\n"))
check("N9  the shape inside a here-string", "silent", "Write",
      wr("D:/x/a.ps1",
         "$doc = @'\npython x.py | Select-Object -First 30\n'@\nWrite-Host $doc\n"))
check("N10 a bare closer with no upstream", "silent", "PowerShell",
      ps("Select-Object -First 5"))
check("N11 THE PRESCRIBED FIX must not fire", "silent", "PowerShell",
      ps("$out = & python x.py; $out | Select-Object -First 30"))
check("N12 escape hatch marker", "silent", "PowerShell",
      ps("python x.py | Select-Object -First 30   # [pipeline-checked]"))
check("N13 the recommended file form", "silent", "PowerShell",
      ps("Get-Content D:/big.log -TotalCount 20"))
check("N14 alias upstream (sort -> Sort-Object)", "silent", "PowerShell",
      ps("Get-ChildItem | sort Name | Select-Object -First 3"))
check("N15 a .md file carrying the shape is not PowerShell", "silent", "Write",
      wr("D:/x/NOTES.md", "Do not write `python x.py | Select-Object -First 30`.\n"))
check("N16 Edit on a non-.ps1 file", "silent", "Edit",
      {"file_path": "D:/x/a.txt", "old_string": "a",
       "new_string": "python x.py | Select-Object -First 3"})
check("N17 Select-String upstream is a cmdlet", "silent", "PowerShell",
      ps("Select-String -Path a.txt -Pattern x | Select-Object -First 2"))
check("N18 alias-to-alias", "silent", "PowerShell",
      ps("ls D:/x | select -First 3"))
check("N19 -Last buffers the whole stream", "silent", "PowerShell",
      ps("python x.py | Select-Object -Last 3"))
check("N20 curl/wget are cmdlet aliases in 5.1", "silent", "PowerShell",
      ps("curl https://example.com | Select-Object -First 1"))
check("N21 Bash call with no .ps1 in it", "silent", "Bash",
      ps("python x.py | head -30"))
check("N22 script block with the -f FORMAT operator, not -First", "silent",
      "PowerShell",
      ps("python x.py | Select-Object @{n='v';e={ '{0:N2}' -f $_.Cost }}"))
check("N23 & $var that holds a script block", "silent", "PowerShell",
      ps("$check = { Get-Date }\n& $check | Select-Object -First 1"))
check("N24 & $var that holds another .ps1", "silent", "PowerShell",
      ps("$boot = 'D:/x/bootstrap.ps1'\n& $boot | Select-Object -First 1"))
check("N25 pipeline with no early-closing consumer at all", "silent", "PowerShell",
      ps("python x.py | ForEach-Object { $_ } | Out-File D:/o.txt"))
check("N26 no pipe character anywhere", "silent", "PowerShell",
      ps("python x.py --first 30"))
check("N27 unrecognised bare word stays UNKNOWN (declared under-fire)", "silent",
      "PowerShell", ps("mytool --scan | Select-Object -First 3"))
# N28 was written as a POSITIVE case (P7) and the backtest flipped it. `git` is
# detected as report-tier, and report-tier does not annotate, because 60 of the
# 160 corpus hazards were `git diff|show|log` asking for the first N lines of
# something that only prints. The flip is recorded here rather than quietly
# rewritten: the expectation changed because of rows, which is the only reason
# an expectation may change after the detector exists.
check("N28 report-tier native is detected but silent (was P7)", "silent",
      "PowerShell", ps("git log --oneline | Select-Object -First 5"))
check("N29 report-tier: git diff, the most common corpus shape", "silent",
      "PowerShell", ps("git -C D:/x diff --unified=1 | Select-Object -First 160"))
check("N30 mutation-capable 'reporter' stays in the WORK tier", "deny",
      "PowerShell", ps("az vm create -n x -g y | Select-Object -First 1"))

# ------------------------------------------------- tier-widening control (B)
# `compose()` carries a second branch for the report tier. Under the shipped
# FIRE_TIERS nothing can reach it, and an untested branch beside a live one is
# the ghost-mechanism shape (40-maintenance.md §4.2). So drive a copy of the
# hook with the tier re-enabled: this proves the branch works AND doubles as the
# positive control for the silent half above -- N28/N29 have to be silent for a
# REASON, not because the detector missed them.
_variant_dir = tempfile.mkdtemp(prefix="pipeclose-variant-")
_wide = os.path.join(_variant_dir, "wide.py")
with open(HOOK, encoding="utf-8") as _fh:
    _src = _fh.read()
assert 'FIRE_TIERS = ("work",)' in _src, "FIRE_TIERS line moved; fix this control"
with open(_wide, "w", encoding="utf-8") as _fh:
    _fh.write(_src.replace('FIRE_TIERS = ("work",)', 'FIRE_TIERS = ("work", "report")'))
_saved_hook = HOOK
HOOK = Path(_wide)
check("C1  report tier DOES fire when re-enabled (branch is live)", "notice",
      "PowerShell", ps("git log --oneline | Select-Object -First 5"),
      "$LASTEXITCODE")
HOOK = _saved_hook
check("C2  ... and the identical input is silent as shipped", "silent",
      "PowerShell", ps("git log --oneline | Select-Object -First 5"))

# ------------------------------------------- class closure over classify() (D)
# `classify()` returns one of FOUR kinds -- work / report / safe / unknown --
# and only FIRE_TIERS speaks. N27 feeds an unrecognised bare word; nothing until
# now fed the OTHER escape, a subexpression upstream, which the hook's docstring
# names ("`(` subexpression - not resolved") and which is a real hazard: this
# command does kill python. Both foldings would be wrong and both would look
# plausible -- into `work` it fires on every parenthesised upstream, into `safe`
# it asserts nothing can be killed here. So the kind is asserted BY NAME beside
# the emitted verdict; silence alone cannot tell the two readings apart.
UNDET_CMD = "& (Get-Command python).Source fuzz.py --seed 7 | Select-Object -First 30"
check("U1 undetermined upstream: a subexpression matches no classify() kind -> silent",
      "silent", "PowerShell", ps(UNDET_CMD))

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("pipeclose_hook_under_test", HOOK)
_hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_hook)
_kind = _hook.classify(UNDET_CMD, UNDET_CMD.split("|")[0])[0]
RESULTS.append((_kind == "unknown",
                "U2 ... and classify() names that undetermined kind 'unknown', "
                "never 'work' or 'safe'",
                "unknown", _kind, ""))

# -------------------------------------------------------------------- report
fired_rows = sum(1 for _ in open(TMPLOG, encoding="utf-8")) if os.path.isfile(TMPLOG) else 0
pos = [r for r in RESULTS if r[2] in ("notice", "deny")]
neg = [r for r in RESULTS if r[2] == "silent"]
und = [r for r in RESULTS if r[2] not in ("notice", "deny", "silent")]
ok = [r for r in RESULTS if r[0]]

print("hook: %s" % HOOK)
print()
for good, name, expect, got, reason in RESULTS:
    print("%-4s %-58s expect=%-7s got=%s" % ("ok" if good else "FAIL", name, expect, got))
    if not good and reason:
        print("       -> %s" % reason)

print()
print("known-FIRE   : %d/%d" % (sum(1 for r in pos if r[0]), len(pos)))
print("known-SILENT : %d/%d" % (sum(1 for r in neg if r[0]), len(neg)))
print("class-kind   : %d/%d (kind asserted by name; sits in neither half above "
      "on purpose -- AP-62 excludes it from the verdict counts)"
      % (sum(1 for r in und if r[0]), len(und)))
print("TOTAL        : %d/%d" % (len(ok), len(RESULTS)))
print("telemetry rows written to the redirected log: %d "
      "(production log must be untouched)" % fired_rows)
sys.exit(0 if len(ok) == len(RESULTS) else 1)
