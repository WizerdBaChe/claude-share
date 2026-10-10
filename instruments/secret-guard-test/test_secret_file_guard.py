#!/usr/bin/env python3
"""Two-sided calibration for hooks/secret_file_guard.py.

A gate that denies everything scores 100% on a one-sided test, so this suite
carries BOTH controls and fails if either side collapses:

  MUST-DENY  (positive control) — real credential reads. If any passes, the
             guard is not protecting anything.
  MUST-PASS  (negative control) — ordinary work that merely looks similar
             ($env:TEMP, dict.keys(), .env.example, git status). If any is
             denied, the guard is a tax on normal sessions.

UNDETERMINED is a third result class, asserted and counted in NO verdict
(AP-62, `ops/references/principle-design-guide.md`). The guard's object classes
are its COVERED-TOOL list, enumerated in its docstring: Read and Grep (content
would print), Bash and PowerShell (cat / Get-Content / open()), with Glob
exempted because it returns names only. A tool name outside that list carrying a
real credential path matches no declared class. The guard cannot rule on it —
it never learns that tool's argument shape — so it emits no decision at all, and
this suite asserts exactly that: `undetermined`, not "pass". Calling it a
MUST-PASS would fold an unruled input into the negative control and inflate the
"guard is not a tax" count with a case the guard never examined.

The fold is DECLARED, which is why it is a specimen here and not a defect
report: the hook's docstring enumerates the covered tools, and its `review-when`
trigger names this exact event — "Claude Code adds a file-reading tool not in
the matcher list" — pointing at the single edit point. So each undetermined case
ships with its DETERMINABLE TWIN: the same credential path under a covered tool,
which must still deny. The twin is what keeps this honest — it proves the target
really is a credential and that the tool name alone moved the verdict. When a
listed tool becomes reachable, its case moves from here into MUST_DENY; that
move is the review-when trigger firing, and the twin is already written.

Run:  python tools/secret-guard-test/test_secret_file_guard.py
Exit 0 = all three classes behave. Exit 1 = a listed case flipped; the printed
table names which one, so the fix goes to SECRET_TOKEN, never to this file.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path.home() / ".claude" / "hooks" / "secret_file_guard.py"

# CLAUDE_TELEMETRY_DIR (ruling 2026-09-11): this suite's own MUST_DENY/MUST_PASS
# runs fired real deny rows into production telemetry/secret-file-guard.jsonl
# (402 rows across 7 sessions per the 2026-09-10 inventory) because nothing here
# redirected the hook's writer. One temp dir for the whole run fixes that at
# the source; TELEMETRY_ISOLATION_CHECK below proves the fix two-sidedly.
_RUN_TELEMETRY_DIR = tempfile.mkdtemp(prefix="secret-guard-test-")

MUST_DENY = [
    ("Read", {"file_path": r"<WORK_ROOT>\PatentsGrabber\.env"}),
    ("Read", {"file_path": "/home/u/proj/.env.local"}),
    ("Grep", {"pattern": "KEY", "path": r"<WORK_ROOT>\PatentsGrabber\.env"}),
    ("Bash", {"command": r'cat "<WORK_ROOT>\PatentsGrabber\.env"'}),
    ("Bash", {"command": "head -5 .env"}),
    ("Bash", {"command": "python -c \"print(open('.env').read())\""}),
    ("PowerShell", {"command": "Get-Content <WORK_ROOT>\\PatentsGrabber\\.env"}),
    ("PowerShell", {"command": "gc ./secrets.json | ConvertFrom-Json"}),
    ("Bash", {"command": "cat ~/.ssh/id_rsa"}),
    ("Bash", {"command": "openssl x509 -in server.pem -text"}),
    ("Read", {"file_path": "C:/certs/client.p12"}),
    ("Bash", {"command": "strings token.json"}),
    # PROPERTY 2 (2026-10-03): printing a credential value. The first two are
    # the RECORDED shapes from the R05 B1 sweep (values never copied here).
    ("PowerShell", {"command": "& python.exe -X utf8 -c @'\nimport psutil, os\np = psutil.Process(52768)\nenv = p.environ()\nprint(env)\n'@"}),
    ("Bash", {"command": 'cd /d/WORK/COMSOL_Test; grep -niE "license|password|passwd|serial|token" 06_x/route-J/prefs_enable_off/comsol.prefs | cut -c1-200'}),
    ("PowerShell", {"command": "Get-ChildItem env: | Sort-Object Name"}),
    ("PowerShell", {"command": "gci env:"}),
    ("PowerShell", {"command": "[Environment]::GetEnvironmentVariables()"}),
    ("Bash", {"command": "printenv"}),
    ("Bash", {"command": "env | sort"}),
    ("Bash", {"command": "python -c \"import os; print(os.environ)\""}),
    ("Bash", {"command": "node -e \"console.log(process.env)\""}),
    ("Bash", {"command": "cat /proc/1234/environ"}),
    ("Bash", {"command": "rg -n api_key config/settings.yaml"}),
    ("PowerShell", {"command": "Select-String -Path app.config -Pattern password"}),
    ("Grep", {"pattern": "password", "path": "<WORK_ROOT>/x/comsol.prefs", "output_mode": "content"}),
    # Found by the pre-birth backtest: a FILTERED dump still prints values
    # (2026-08-14, the filter matched the very variable holding the OAuth token).
    ("Bash", {"command": 'cd ~/.claude && echo "=== vars ===" && env | grep -iE "^(anthropic|claude|ai_agent)" | sort'}),
    # NARROWING PASS 2 (2026-10-04) regression twins. Each strip branch clears a
    # credential name only where it cannot name the file the same statement
    # reads; each case is one branch's shape turned into a read, and must deny.
    ("Bash", {"command": r"find . -type f | grep -E '\.env|\.pem' | xargs cat"}),       # name stream -> reader
    ("Bash", {"command": r"cat $(find . -type f | grep -iE '\.env$')"}),                 # ... inside a substitution
    ("Bash", {"command": r"""find . | grep '\.env$' | while read f; do cat "$f"; done"""}),
    ("Bash", {"command": r"grep -rv '\.env' ."}),                    # inverted but recursive: reads every file
    ("Bash", {"command": "grep -vf .env list.txt"}),                 # -f: the operand IS a file
    ("Bash", {"command": "find . -name .env -prune | xargs cat"}),   # -prune without -o still prints it
    ("Bash", {"command": r"find . -name '.env' -exec cat {} \;"}),   # positive -name is not stripped
    ("Bash", {"command": "grep -rn KEY --include=.env ."}),          # --include is the positive twin of --exclude
    ("PowerShell", {"command": r"Get-ChildItem -Recurse | Where-Object { $_.Name -match '\.env$' } | Get-Content"}),
    ("PowerShell", {"command": "Get-ChildItem -Recurse -Include server.pem | Get-Content"}),
    ("PowerShell", {"command": r"$p = '<WORK_ROOT>\PatentsGrabber\.env'; Get-Content $p"}),   # live variable
    ("PowerShell", {"command": r"$c = '\.env$'; Get-ChildItem -Recurse | Where-Object { $_.Name -match $c } | Get-Content"}),
    ("PowerShell", {"command": "$env:CRED_FILE = '.env'; python run.py"}),   # env scope reaches the child
    ("Bash", {"command": "CRED_FILE='.env' python run.py"}),                 # env prefix reaches the child
    # PROPERTY 2 masking twins (2026-10-04). A sed after the search clears a
    # credential-key grep only when it masks every value and nothing raw escapes
    # around it; each case keeps the search and the sed but breaks one of those.
    ("Bash", {"command": "grep -n password app.ini | sed -n 1,5p"}),               # sed that selects, not masks
    ("Bash", {"command": "grep -n password app.ini | sed 's/foo/bar/'"}),          # sed that edits something else
    ("Bash", {"command": "grep -n password app.ini | sed 's/=.*/=& <masked>/'"}),  # & re-inserts the value
    ("Bash", {"command": "grep -n password app.ini | sed -e p -e 's/=.*/=<m>/'"}), # p prints the raw line first
    ("Bash", {"command": "grep -n password app.ini | tee /dev/stderr | sed -E 's/([=:]).*/\\1 <masked>/'"}),
    ("Bash", {"command": "grep -n password app.ini >&2 | sed 's/=.*/=<m>/'"}),     # raw lines redirected past the mask
    ("Bash", {"command": "grep -n password app.ini 2>&1 | tee raw.txt | sed 's/=.*/=<REDACTED>/'; cat raw.txt"}),
    ("Bash", {"command": "grep -n password app.ini | sed 's/=.*/=<m>/'; grep -n password app.ini"}),  # a second, raw search
    ("Bash", {"command": "grep -n password app.ini; echo x | sed 's/=.*/=<m>/'"}), # mask in another statement
    ("Bash", {"command": "grep -n password app.ini | sed 's/=.*/=<m>/' app.ini"}), # sed reads a file, not the stream
]

MUST_PASS = [
    # Templates teach variable NAMES, never values — the documented setup path.
    ("Read", {"file_path": r"<WORK_ROOT>\PatentsGrabber\.env.example"}),
    ("Bash", {"command": "cat .env.example"}),
    ("Bash", {"command": "cat .env.template"}),
    # Shapes that merely resemble a secret token.
    ("PowerShell", {"command": "$env:TEMP"}),
    ("PowerShell", {"command": "Write-Output $env:PATH"}),
    ("Bash", {"command": "conda env list"}),
    ("Bash", {"command": "python -c \"print(d.keys())\""}),
    ("Bash", {"command": "curl -s --key-status http://127.0.0.1:8000/api/library"}),
    # The connector path this guard exists to keep open.
    ("Bash", {"command": "python connectors/probe.py --id patentsgrabber"}),
    ("Bash", {"command": "python <WORK_ROOT>/PatentsGrabber/tools/verify_ops.py"}),
    ("Bash", {"command": "curl -s http://127.0.0.1:8000/api/patent?q=US6285999B1"}),
    # The three OBSERVED false positives (2026-08-27). These are not invented
    # cases: each one blocked real work in one session, and the third triggered
    # the narrowing pass the guard's docstring promised. They are the floor —
    # a future re-tightening must keep all three passing.
    ("Bash", {"command": 'git commit -m "a connector 401s and cat .env is the tempting next move"'}),
    ("Bash", {"command": "git check-ignore -v skills/x/connectors/.env"}),
    ("Bash", {"command": 'python -c "for k,p in c.execute(q): print(i.key, a.path)"'}),
    # Observed false positives folded 2026-10-04, VERBATIM from the transcripts
    # (FP-4 / FP-5: sonnet work-card executors on read-only inventory cards told
    # "never open credential-like files (<names>)"; FP-8: a report_fp row of
    # 2026-10-03). In each, the credential name is a PATTERN over names or
    # lines — a -notmatch exclusion plus a dead regex variable, a names-only
    # find|grep listing, a grep -l — and nothing is read.
    ("PowerShell", {"command": r"""$skip='\\(node_modules|\.venv|venv|dist|build|\.git|__pycache__|\.idea)(\\|$)'
$cred='token|secret|\.pem$|\.key$|\\\.env'
$roots=[ordered]@{ 'ArchLens'='<WORK_ROOT>\ArchLens'; 'P2C-copy1'='<WORK_ROOT>\Paper2ChatAPP - 複製'; 'P2C-copy2'='<WORK_ROOT>\Paper2ChatAPP - 複製 (2)'; 'ArchLens_Series'='<WORK_ROOT>\ArchLens_Series' }
foreach($k in $roots.Keys){ $r=$roots[$k]; $f=Get-ChildItem -LiteralPath $r -Recurse -File -Force | Where-Object { $rel=$_.FullName.Substring($r.Length); ($rel -notmatch $skip) -and ($_.Name -notmatch 'token|secret|\.pem$|\.key$|^\.env') }
 $mn=($f|Sort-Object LastWriteTimeUtc|Select-Object -First 1); $mx=($f|Sort-Object LastWriteTimeUtc -Descending|Select-Object -First 1)
 $cn=($f|Sort-Object CreationTimeUtc|Select-Object -First 1); $cx=($f|Sort-Object CreationTimeUtc -Descending|Select-Object -First 1)
 "{0}: n={1} mtime_min={2:yyyy-MM-ddTHH:mm:ssZ} mtime_max={3:yyyy-MM-ddTHH:mm:ssZ} ctime_min={4:yyyy-MM-ddTHH:mm:ssZ} ctime_max={5:yyyy-MM-ddTHH:mm:ssZ}" -f $k,$f.Count,$mn.LastWriteTimeUtc,$mx.LastWriteTimeUtc,$cn.CreationTimeUtc,$cx.CreationTimeUtc }
"--- Series docs/ file count (names not read):"; (Get-ChildItem -LiteralPath '<WORK_ROOT>\ArchLens_Series\docs' -Recurse -File -Force | Measure-Object).Count"""}),
    ("Bash", {"command": r"""cd "<WORK_ROOT>/AI_Skill" && find . -type f | grep -v -E 'node_modules|\.venv|__pycache__|\.git/' | wc -l; find . -type f | grep -i -E '\.env|token|secret|\.pem|\.key' ; find . -maxdepth 2 | head -150"""}),
    ("Bash", {"command": r"""cd ~/.claude; grep -rn -i "rotate\|輪替\|revoke" rules ops/*.md hooks/secret_file_guard.py tools/memory-pipeline/README.md tools/pii-membrane/README.md 2>/dev/null | head -8; echo ===; grep -rln -i "secret\|api.key\|token" tools/memory-pipeline/*.py 2>/dev/null | head; echo ===; grep -n -i "telegram\|sendMessage\|status" /d/AIWork/GitHubTrendWatch/CLAUDE.md | head -10; echo ===; grep -n "video-prompt-shelf" references/PROJECTS.md | cut -c1-500"""}),
    # Exclusion shapes named with that fold (constructed, not observed): a
    # negated name filter removes the credential from the set, so whatever reads
    # afterwards reads the rest. Each has a positive twin in MUST_DENY above.
    # Concrete names, not globs: a glob like `*.pem` was never matched at all
    # (`*` is not a boundary char), so a glob case would pass without testing
    # the narrowing — a pre-existing gap, logged in the guard's docstring.
    ("Bash", {"command": "find . -type f -not -name .env ! -name 'server.pem' | wc -l"}),
    ("Bash", {"command": "find . -name .env -prune -o -type f -print"}),
    ("PowerShell", {"command": "Get-ChildItem -Recurse -File -Exclude server.pem,'.env' | Measure-Object"}),
    ("Bash", {"command": "grep -rn TODO --exclude=.env --exclude-dir=.git ."}),
    ("Bash", {"command": r"find . -type f | grep -v -E '\.env$|\.pem$' | xargs wc -l"}),
    ("PowerShell", {"command": r"$skip = '\.env$|\.pem$'; Get-ChildItem -Recurse -File | Where-Object { $_.Name -notmatch $skip } | Measure-Object"}),
    # Ordinary session traffic.
    ("Bash", {"command": "git status --short"}),
    ("Read", {"file_path": r"<CLAUDE_HOME>\skills\literature-search-extract\SKILL.md"}),
    ("Glob", {"pattern": "**/.env"}),          # names only, no content
    ("Write", {"file_path": ".gitignore", "content": ".env\n"}),
    # PROPERTY 2 must-pass: names-only listings, one named variable, env used
    # to RUN a command, count/list-only greps, and greps over code or prose.
    ("PowerShell", {"command": "(Get-ChildItem env:).Name"}),
    ("PowerShell", {"command": "Get-ChildItem env:PATH"}),
    ("Bash", {"command": "env | cut -d= -f1 | sort"}),
    ("Bash", {"command": "printenv HOME"}),
    ("Bash", {"command": "env PYTHONIOENCODING=utf-8 python run.py"}),
    ("Bash", {"command": "python -c \"import os; print(sorted(os.environ))\""}),
    ("Bash", {"command": "python - <<'EOF'\nimport os, subprocess\nenv = os.environ.copy()\nsubprocess.run(['x'], env=env)\nEOF"}),
    ("Bash", {"command": "python -c \"import os; print(os.environ['TEMP'])\""}),
    ("Bash", {"command": "grep -l password config/*.ini"}),
    ("Bash", {"command": "grep -c password settings.yaml"}),
    ("Bash", {"command": "grep -n password src/auth.py"}),
    ("Bash", {"command": "grep -rn \"secret_file_guard\" ops/*.md"}),
    ("Bash", {"command": 'git commit -m "guard: block printenv and grep password over settings.yaml"'}),
    ("Grep", {"pattern": "password", "path": "<WORK_ROOT>/x/comsol.prefs"}),
    ("Grep", {"pattern": "password", "path": "<WORK_ROOT>/x/comsol.prefs", "output_mode": "count"}),
    ("Grep", {"pattern": "password", "path": "<WORK_ROOT>/x/src", "output_mode": "content"}),
    ("Bash", {"command": "python -X utf8 ~/.claude/tools/cred-sweep/cred_sweep.py --selftest"}),
    # Backtest false positives fixed before birth (2026-10-03): masked dumps,
    # `(env)` in commit subjects and Python, `env` inside a regex alternation,
    # and greps that merely NAME secret-handling tools.
    ("Bash", {"command": "env | grep -i '^claude' | sed 's/=.*$/=<set>/' | head"}),
    ("Bash", {"command": "git commit -q -F - <<'EOF'\nfeat(env): add portable backend bootstrap\nEOF"}),
    ("Bash", {"command": "python - <<'EOF'\nthr = float(np.median(env))\nEOF"}),
    ("Bash", {"command": 'git ls-files | grep -iE "\\.(env|key|pem|p12)$|credentials"'}),
    ("Bash", {"command": "grep -n 'secret_file_guard' tools/share-manifest.toml | cut -c1-200"}),
    ("PowerShell", {"command": "Get-ChildItem env: | Where-Object { $_.Name -match '^CLAUDE' } | ForEach-Object { $_.Name }"}),
    # PROPERTY 2 masking route (2026-10-04): the deny text's own third rewrite
    # (GREP_PATH) was still denied. The first is that text's example verbatim;
    # the second is the shape of a real denied call from that day's backtest.
    ("Bash", {"command": "grep -n password app.ini | sed -E 's/([=:]).*/\\1 <masked>/'"}),
    ("Bash", {"command": "grep -niE 'password|api_key' config/app.ini | sed 's/=.*/=<REDACTED>/'"}),
    ("Bash", {"command": "cd /d/x; grep -niE 'password' a.prefs | cut -c1-200 | sed 's/=.*$/=<m>/' | head -20"}),
]

# The credential path the undetermined cases and their twins share, so the only
# thing that differs across the pair is the tool name.
LIVE_ENV = r"<WORK_ROOT>\PatentsGrabber\.env"

# (tool, tool_input, twin, escapes) — asserted, counted in no verdict.
# Each `tool` is a real Claude Code / MCP tool name that can put file content in
# context and is NOT in the guard's covered-tool list. `twin` is the SAME
# credential path under a covered tool, and must still deny. Measured
# 2026-09-09: all three return rc 0 with an empty stdout — no decision emitted,
# which is not the same event as an allow decision.
UNDETERMINED = [
    ("mcp__filesystem__read_text_file", {"path": LIVE_ENV},
     ("Read", {"file_path": LIVE_ENV}),
     "an MCP file-reading server: outside the covered-tool list (Read/Grep/"
     "Bash/PowerShell), and its argument key `path` is not one the guard reads "
     "for this tool"),
    ("NotebookEdit", {"notebook_path": LIVE_ENV, "new_source": "x"},
     ("Read", {"file_path": LIVE_ENV}),
     "a notebook tool: outside the covered-tool list, and `notebook_path` is "
     "not a key the guard inspects"),
    ("Agent", {"subagent_type": "general-purpose",
               "prompt": f'open {LIVE_ENV} and tell me the key'},
     ("Bash", {"command": f'cat "{LIVE_ENV}"'}),
     "a dispatch surface: the read happens in a SUBAGENT, so the covered-tool "
     "list is consulted against 'Agent', which is not on it"),
]


# Unclassifiable SHAPE (AP-62): stdin that parses but is not the object the
# guard reads -- the payload itself, or a dict whose tool_input is not an
# object. The guard's docstring: "Fail-open on malformed input; deny is the only
# non-silent path." So each must exit 0, print nothing and write no receipt row.
# The inner case needs a TRUTHY non-dict (`tool_input or {}` turns [] into {}),
# and a covered tool, so the guard is the only thing between it and `.get`.
UNCLASSIFIABLE = [
    "[]",
    "null",
    json.dumps({"tool_name": "Bash", "tool_input": ["git status"]}),
]


def unclassifiable_shape_check() -> list[tuple[str, str, str]]:
    """rc 0, empty stdout, and the run's receipt file the same size before and
    after -- the last because MUST_DENY has already grown it, so absence of a
    new row is a size comparison, not an existence check."""
    failures: list[tuple[str, str, str]] = []
    receipts = Path(_RUN_TELEMETRY_DIR) / "secret-file-guard.jsonl"
    env = dict(os.environ, CLAUDE_TELEMETRY_DIR=_RUN_TELEMETRY_DIR)
    for raw in UNCLASSIFIABLE:
        before = receipts.stat().st_size if receipts.exists() else -1
        proc = subprocess.run([sys.executable, str(HOOK)], input=raw,
                              capture_output=True, text=True, timeout=15, env=env)
        after = receipts.stat().st_size if receipts.exists() else -1
        silent = not (proc.stdout or "").strip()
        ok = proc.returncode == 0 and silent and before == after
        print(f"{'UNCLASS':10} {'open' if ok else 'BROKE!':8} unclassifiable "
              f"payload {raw[:44]!r}: rc {proc.returncode}, "
              f"{'silent' if silent else 'SPOKE'}, receipts {before} -> {after}")
        if not ok:
            failures.append((
                "UNCLASSIFIABLE shape did not fail open", "-",
                f"{raw!r} -> rc {proc.returncode}, stdout "
                f"{(proc.stdout or '').strip()[:60]!r}, stderr "
                f"{(proc.stderr or '').strip()[-60:]!r}, receipts {before} -> "
                f"{after}. A JSON value that is not a payload object matches no "
                f"covered-tool class; the guard must stay silent, not raise."))
    return failures


def verdict_of(tool: str, tool_input: dict) -> tuple[str | None, int]:
    """-> (permissionDecision or None, returncode). None = the guard emitted no
    decision at all, which is the undetermined outcome, not an allow."""
    payload = json.dumps({"tool_name": tool, "tool_input": tool_input})
    env = dict(os.environ, CLAUDE_TELEMETRY_DIR=_RUN_TELEMETRY_DIR)
    proc = subprocess.run([sys.executable, str(HOOK)], input=payload,
                          capture_output=True, text=True, timeout=15, env=env)
    out = (proc.stdout or "").strip()
    if not out:
        return None, proc.returncode
    try:
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"], proc.returncode
    except Exception:
        return None, proc.returncode


def denied(tool: str, tool_input: dict) -> bool:
    return verdict_of(tool, tool_input)[0] == "deny"


def telemetry_isolation_check() -> list[tuple[str, str, str]]:
    """Two-sided control for CLAUDE_TELEMETRY_DIR (ruling 2026-09-11).

    POSITIVE: with the var set, the deny row this call fires lands under the
    temp dir this control names (not production).
    NEGATIVE: the live telemetry/secret-file-guard.jsonl row count is read
    before and after; it must be identical. A hook that ignored the var fails
    BOTH sides at once -- the temp file never appears (positive fails) AND the
    production count moves (negative fails) -- so neither side can pass by
    accident while the other silently absorbs the miss.
    """
    failures: list[tuple[str, str, str]] = []
    prod_path = Path.home() / ".claude" / "telemetry" / "secret-file-guard.jsonl"

    def prod_rows() -> int:
        if not prod_path.exists():
            return 0
        text = prod_path.read_text(encoding="utf-8", errors="replace")
        return sum(1 for ln in text.splitlines() if ln.strip())

    before = prod_rows()
    with tempfile.TemporaryDirectory(prefix="secret-guard-isolation-") as td:
        env = dict(os.environ, CLAUDE_TELEMETRY_DIR=td)
        payload = json.dumps({"tool_name": "Bash",
                              "tool_input": {"command": "cat ~/.ssh/id_rsa"}})
        subprocess.run([sys.executable, str(HOOK)], input=payload,
                       capture_output=True, text=True, timeout=15, env=env)
        temp_log = Path(td) / "secret-file-guard.jsonl"
        temp_has_row = temp_log.exists() and temp_log.stat().st_size > 0
        after = prod_rows()

    print(f"{'ISOLATE':10} {'ok' if temp_has_row else 'MISSING!':8} "
          f"positive: deny row lands under CLAUDE_TELEMETRY_DIR")
    print(f"{'ISOLATE':10} {'ok' if after == before else 'GREW!!':8} "
          f"negative: production row count unchanged ({before} -> {after})")
    if not temp_has_row:
        failures.append(("TELEMETRY ISOLATION missing", "Bash",
                         "CLAUDE_TELEMETRY_DIR was set but no row landed under the temp "
                         "dir -- the hook is not honouring the var"))
    if after != before:
        failures.append(("TELEMETRY ISOLATION leaked", "Bash",
                         f"production telemetry/secret-file-guard.jsonl grew from {before} "
                         f"to {after} rows while CLAUDE_TELEMETRY_DIR was set"))
    return failures


def main() -> int:
    failures = []
    print(f"{'side':10} {'verdict':8} case")
    print("-" * 78)
    for tool, ti in MUST_DENY:
        label = (ti.get("command") or ti.get("file_path") or ti.get("path") or "")[:52]
        ok = denied(tool, ti)
        print(f"{'MUST-DENY':10} {'deny' if ok else 'PASS!!':8} {tool}: {label}")
        if not ok:
            failures.append(("MUST-DENY leaked", tool, label))
    for tool, ti in MUST_PASS:
        label = (ti.get("command") or ti.get("file_path") or ti.get("pattern") or "")[:52]
        ok = not denied(tool, ti)
        print(f"{'MUST-PASS':10} {'pass' if ok else 'DENY!!':8} {tool}: {label}")
        if not ok:
            failures.append(("MUST-PASS blocked", tool, label))

    # --- UNDETERMINED: asserted, counted in no verdict (AP-62) --------------
    for tool, ti, (twin_tool, twin_ti), escapes in UNDETERMINED:
        label = (ti.get("path") or ti.get("notebook_path") or ti.get("prompt") or "")[:52]
        decision, rc = verdict_of(tool, ti)
        ok = decision is None and rc == 0
        print(f"{'UNDET':10} {'undet' if ok else 'RULED!':8} {tool}: {label}")
        print(f"{'':10} {'':8}   escapes: {escapes}")
        if not ok:
            failures.append((
                "UNDETERMINED ruled on", tool,
                f"{label} -- the guard emitted {decision!r} (rc {rc}) on an input "
                f"its covered-tool list does not cover. Either the list grew (move "
                f"this case to MUST_DENY -- the review-when trigger fired) or the "
                f"guard is now ruling on inputs it cannot examine."))
        # the determinable twin: same credential, a covered tool, must still deny
        twin_label = (twin_ti.get("file_path") or twin_ti.get("command") or "")[:52]
        if not denied(twin_tool, twin_ti):
            failures.append((
                "UNDETERMINED twin leaked", twin_tool,
                f"{twin_label} -- the twin of {tool} must deny, or the case above "
                f"proves nothing: an `undetermined` verdict on a path that is not "
                f"gated anywhere is just a pass wearing a different label."))

    # --- unclassifiable shape: fail-open (AP-62) ---------------------------
    failures.extend(unclassifiable_shape_check())

    # --- CLAUDE_TELEMETRY_DIR two-sided control (ruling 2026-09-11) --------
    failures.extend(telemetry_isolation_check())

    print("-" * 78)
    print(f"must-deny: {len(MUST_DENY)}   must-pass: {len(MUST_PASS)}   "
          f"undetermined (not counted): {len(UNDETERMINED)}   "
          f"unclassifiable shape (fail-open): {len(UNCLASSIFIABLE)}   "
          f"failures: {len(failures)}")
    for kind, tool, label in failures:
        print(f"  FAIL [{kind}] {tool}: {label}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
