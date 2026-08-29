r"""PreToolUse guard: `$ErrorActionPreference='Stop'` governing a native exe.

Scope: PowerShell-language text, wherever it is written. The DETECTOR reads four
surfaces - the PowerShell tool's `command`, and `.ps1` content arriving through
Write, Edit or a Bash heredoc. The REGISTRATION in `settings.json` is narrower
than that, `Write|PowerShell`, and the difference is measured rather than
accidental; see WHAT THE BACKTEST CHANGED below. This hook is NOT about the Bash
tool's transport - `shell_transport_guard.py` owns that and stays Bash-only on
purpose, which is why this is a separate file: merging them would put a
transport guard on Write, and would falsify the "Bash tool only" scope claim
that its own docstring leans on.

THE DEFECT (Windows PowerShell 5.1; `ops/lessons.md` L-024 tail, L-011 hit 3;
global CLAUDE.md Environment, the "calling a native executable from PowerShell"
bullet - named by its opening words rather than by its ordinal, because an
ordinal in a pointer rots the first time the list is reordered and nothing
announces it). `$ErrorActionPreference='Stop'` is a
cmdlet-error preference. Applied to a native executable it is wrong in BOTH
directions at once:

  (A) IT FIRES WHEN IT SHOULD NOT. If the exe's stderr is redirected in any form
      (`2>&1`, `2>$null`, `2>file`, `*>&1`), PowerShell 5.1 wraps each stderr
      line in a NativeCommandError ErrorRecord. Under 'Stop' that record is
      TERMINATING, so a harmless warning on stderr aborts the script even though
      the exe returned exit code 0. (`cmd /c` is exempt - it swallows the
      stream.)
  (B) IT DOES NOT FIRE WHEN IT SHOULD. A native exe returning a non-zero exit
      code raises no PowerShell error at all in 5.1, so 'Stop' sails past it.
      `$LASTEXITCODE` is the only reliable signal, and it must be checked after
      every native call.

The two together are worse than either: the script aborts on the wrong events
and continues through the right ones, so the author's mental model of "Stop
makes failures loud" is inverted exactly where it is being relied on.

WHY A HOOK AND NOT (ONLY) A CLAUDE.md LINE - the measured A/B, not a hunch.
`ops/lessons.md` L-024 records three traps in ONE entry. Two got
`hooks/shell_transport_guard.py`; this one got prose in global CLAUDE.md and
nothing else. Over one project, one week, one author (bench-claude-arms):
the hooked traps were reached for twice and intercepted twice, zero loss; the
prose trap was hit once, was NOT prevented, and voided experiment run C3-02.
The transcript records the author writing, AFTER the failure, "my script hit the
trap recorded in your CLAUDE.md" - correct words, one step too late. A prose
rule is retrieved by trigger-word match at the moment of WRITING; the violating
decision was already taken at ROUTING time. L-011 hit 3 is the full analysis.

WHAT THE BACKTEST CHANGED ABOUT THIS HOOK'S SCOPE (2026-08-21). The ticket asked
for a check on the PowerShell tool, and the corpus said that alone would be
theatre. Over 3,405 deduplicated PowerShell-tool calls (56 days, live
transcripts + a local session-archive mirror) exactly TWO set
`$ErrorActionPreference='Stop'`, and both were the deliberate probes from the
2026-08-18 audit that DISCOVERED the trap. The real surface is script FILES: 47
of the 53 EAP='Stop' payloads in the whole corpus arrived through Write or Edit,
and the incident itself was `_bench-claude-arms/tools/run_arm.ps1` - a
file, Written, later Edited, executed by something else. A hook reading only
`PowerShell.command` would have had zero chance at the one event it exists for.

Then the same backtest priced each surface, and the prices are not close
(105 ms per invocation, all of it Python start-up - the analysis is free):

    tool         calls/day   tax/day   fires in 56 days
    Write             62.6     6.6 s   20     <- carries the hook
    PowerShell        60.8     6.4 s    1     <- the audit's own probe
    Edit             134.8    14.2 s    0
    Bash             199.1    20.9 s    1

Edit and Bash are 73% of the cost for one fire between them. Edit never fires
because an Edit's `new_string` is a FRAGMENT: it almost never carries both the
assignment and the call, and making it fire would mean reading the target file
inside a PreToolUse hook - deliberately not done, and named here so it is not
re-derived as a new idea. The Bash surface is a heredoc writing a .ps1, which
global CLAUDE.md's routing rule already forbids at the source and
`shell_transport_guard.py` already annotates; its single fire predates that
rule. So `settings.json` registers `Write|PowerShell` and the other two branches
stay in the code, tested but unregistered. `tools/ps-errorpref-backtest`
measures all four regardless of registration, so the choice can be re-made from
rows rather than re-argued - `ops/rule-registry.md` carries the review-when.

Final rates as registered: 21 fires over 56 days across 3,488 inspected
payloads (0.60%), 0.375/day, and reading all 22 corpus hits found no false
positive - every one is a real native-exe invocation under a live 'Stop'. The
load-bearing one is hit 18: run_arm.ps1 as first written, with
`(Get-Content $PromptFile -Raw) | & claude @claudeArgs 2>&1 | Out-String` under
'Stop'. That is the line that voided C3-02, and this guard fires on the Write
that created it, before it ever runs.

GATE AUTHORITY (global CLAUDE.md; `shell_transport_guard.py`'s docstring has the
long version). A gate may only rule on what it can DETERMINE; for anything else
the output is downgrade-and-forward, never veto. `$ErrorActionPreference='Stop'`
is CORRECT for a pure-cmdlet script - it is the documented way to make cmdlet
errors terminating - and whether the author means the native call to be governed
by it is not decidable from the text. Two shapes are byte-adjacent and
indistinguishable in intent: a script that wants Stop everywhere and has not
thought about the exe, and a script that wants Stop for its cmdlets and knows
about the exe. So this hook ANNOTATES and never denies. Same asymmetry the
backslash branch of the transport guard resolved, same reason.

WHAT IT DOES NOT DECIDE, stated so a reader does not over-trust it. This is a
positional text scan, not a PowerShell parser:
  - a native call inside a function DEFINED before the 'Stop' assignment but
    CALLED after it is scored by text order, not by call order;
  - an assignment whose right-hand side is a variable (`= $prevEap`) is read as
    "unknown", which clears the Stop state - so a restore under-fires rather
    than over-fires, deliberately;
  - `& $x` counts only when `$x`'s assignment names an .exe/.cmd/.bat. In this
    corpus `& $x` was as often a SCRIPT BLOCK or another .ps1, neither of which
    raises NativeCommandError, and that was the largest false-positive class in
    the first backtest;
  - `try`/`catch` is not modelled. It changes what happens on (A); it does
    nothing for (B).
Under-firing is the chosen error direction throughout: this hook's whole
justification is that it costs nothing to read, which stops being true the
moment it talks during scripts that are already correct.

Per-instance escape hatch: the literal marker [eap-checked] anywhere in the
payload, for a script whose author has verified the interaction.

Fail-open by design: any parse error exits 0, so a guard bug never blocks work.
Telemetry: every notice appends one row to `telemetry/ps-errorpref-guard.jsonl`
(excerpt only, never the whole file). Proof-of-life check:
`ops/references/integrity-sweep.md` check 21 - a hook that does not run is
itself silent (L-011, COST OF P1/P3).
"""
import json
import os
import re
import sys
import time

MARKER = "[eap-checked]"

# Overridable so the test suite and the integrity sweep can DRIVE this hook
# without writing into the real log. `integrity-sweep.md` check 20 records the
# alternative: running a probe bare once leaked a synthetic row into production
# telemetry (P-005, 2026-08-15), and `shell_transport_guard`'s registry entry
# still has to say "discount the first ~90 rows -- the test suite writes real
# entries". A rate you have to subtract from is a rate nobody re-checks.
LOG_PATH = os.environ.get("PS_ERRORPREF_LOG") or os.path.join(
    os.path.expanduser("~"), ".claude", "telemetry", "ps-errorpref-guard.jsonl")

# Assignment to the preference variable. The right-hand side is captured
# permissively and classified afterwards, so that a RESTORE (`= $prevEap`) is
# still seen as an assignment and clears the tracked Stop state. The first
# version matched only bare words, which meant a restore was invisible and the
# state stayed 'Stop' over the rest of the file -- caught by case N9 of the
# calibration suite, which is the whole reason that suite exists.
EAP_SET = re.compile(r"\$ErrorActionPreference\s*=\s*([^\r\n;|]+)", re.I)

EAP_STATES = ("stop", "continue", "silentlycontinue", "ignore", "inquire", "suspend")


def eap_value(raw):
    """Classify the right-hand side. Anything not a literal preference word --
    a variable, an expression, a splat -- is 'unknown', which is treated as
    NOT-Stop: the deliberate under-fire direction."""
    tok = raw.strip().split()[0] if raw.strip() else ""
    tok = tok.strip("'\"").strip().lower()
    return tok if tok in EAP_STATES else "unknown"

# Native executables invoked by BARE NAME. Deliberately excludes every name that
# Windows PowerShell 5.1 resolves to a CMDLET ALIAS rather than to an exe --
# curl, wget, echo, ls, cat, cp, mv, rm, ps, kill, sort, tee, diff, where, type,
# sleep, pwd, man. Those raise no NativeCommandError and must not be flagged.
NATIVE_CMDS = (
    "git", "gh", "dotnet", "msbuild", "nuget", "vswhere", "signtool",
    "node", "npm", "npx", "pnpm", "yarn", "deno", "bun",
    "python", "python3", "py", "pip", "pip3", "pytest", "uv", "poetry", "conda",
    "cargo", "rustc", "rustup", "go", "java", "javac", "gradle", "mvn",
    "make", "cmake", "ninja", "gcc", "g", "clang",
    "docker", "podman", "kubectl", "helm", "terraform", "az", "aws", "gcloud",
    "ffmpeg", "ffprobe", "yt-dlp", "magick", "pandoc",
    "openssl", "ssh", "scp", "rsync", "tar", "unzip", "7z", "robocopy", "xcopy",
    "certutil", "reg", "schtasks", "netsh", "ipconfig", "wmic", "wsl", "adb",
    "claude", "pwsh", "powershell", "cmd", "bash", "sh", "perl", "ruby", "php",
)

# Command position: start of text, or after a newline / `;` / `|` / `{` / `(`
# / `&`. A name appearing mid-expression or inside a string is not a call.
_CMD_POS = r"(?:^|[\n;|{(&])[ \t]*"

BARE_NATIVE = re.compile(
    _CMD_POS + r"(?:@[ \t]*)?((?:" + "|".join(NATIVE_CMDS) +
    r")(?:\.exe|\.cmd|\.bat)?)(?=[ \t\r\n]|$)", re.I | re.M)

# Any explicit executable token at command position: .\x.exe, C:\p\x.exe, x.cmd
EXE_TOKEN = re.compile(
    _CMD_POS + r"((?:\.{0,2}[\\/])?[\w.:$\\/-]*\.(?:exe|cmd|bat))(?=[ \t\r\n]|$)",
    re.I | re.M)

# Call operator. `& "C:\x.exe"` is unambiguous. `& $x` is NOT: in this corpus it
# is a native exe about as often as it is a script block or another .ps1, so the
# variable is classified first and only a resolvable exe counts (see var_kind).
# `& { ... }` (an inline script block) never matches either pattern.
CALL_OP_LIT = re.compile(r"&[ \t]*(['\"])([^'\"\n]*\.(?:exe|cmd|bat))\1", re.I)
CALL_OP_VAR = re.compile(r"&[ \t]*\$((?:script:|global:|local:|env:)?\w+)", re.I)

# Any redirection of the error stream -- this is what turns (A) on.
STDERR_REDIR = re.compile(r"(?:^|[\s)\]'\"])(?:2|\*)>>?(?:&1|[ \t]*\S)")

LASTEXIT = re.compile(r"\$LASTEXITCODE", re.I)

# `cmd /c ...` swallows the child's stderr, so (A) does not reach PowerShell.
CMD_C = re.compile(r"\bcmd(?:\.exe)?[ \t]+/c\b", re.I)

# A Bash command that writes a .ps1 carries BOTH languages. Analyse only the
# heredoc body: the `powershell.exe -File ...` that runs it afterwards is Bash's
# invocation, not one governed by the preference set inside the script.
HEREDOC = re.compile(r"<<-?[ \t]*['\"]?(\w+)['\"]?[ \t]*\r?\n(.*?)\r?\n[ \t]*\1[ \t]*$",
                     re.S | re.M)


def strip_comments(text):
    """Remove PowerShell comments.

    Load-bearing, not cosmetic: the single most common way this exact string
    appears in the corpus is a comment EXPLAINING the trap (the fixed
    run_arm.ps1 carries one). Scoring those as assignments would make the guard
    loudest at the scripts that already got it right.

    Whole-line `#` only. A trailing `#` after code is left alone so that a `#`
    inside a string literal cannot swallow real code.
    """
    text = re.sub(r"<#.*?#>", "\n", text, flags=re.S)
    return re.sub(r"(?m)^[ \t]*#.*$", "", text)


def var_kind(src, name):
    """One-hop classification of the variable in `& $name`.

    Backtest evidence (2026-08-21): `& $var` was the single largest false-
    positive class -- `& $Condition` and `& $s` invoke SCRIPT BLOCKS, and
    `& $BootstrapScript` invokes another .ps1. All three raise cmdlet-style
    errors, not NativeCommandError, so annotating them would be simply wrong.
    Only a variable whose assignment names an executable counts. 'unknown' is
    dropped, which costs a few genuine hits (a path built by Get-ChildItem) and
    buys the removal of a whole wrong class -- the declared error direction.
    """
    pat = re.compile(r"\$(?:script:|global:|local:)?" + re.escape(name.split(":")[-1])
                     + r"\s*=\s*([^\r\n]+)", re.I)
    for m in pat.finditer(src):
        rhs = m.group(1)
        if rhs.lstrip().startswith("{"):
            return "block"
        if re.search(r"\.ps1\b", rhs, re.I):
            return "script"
        if re.search(r"\.(?:exe|cmd|bat)\b", rhs, re.I):
            return "native"
    if re.search(r"\[scriptblock\][ \t]*\$" + re.escape(name), src, re.I):
        return "block"
    return "unknown"


def in_string(src, pos):
    """Is `pos` inside a string literal?

    `(` is a genuine command position in PowerShell (`$h = (git rev-parse HEAD)`)
    and it is also the character before `npm` in
    `Write-Host "clean build (npm ci + npm run build)"` - which is how the second
    backtest still reported a Write-Host line as a native call. Quote parity on
    the candidate's own line settles it, plus a here-string check because those
    span lines and a naive parity test would read their contents as code.
    """
    if src.count("@'", 0, pos) > src.count("'@", 0, pos):
        return True
    if src.count('@"', 0, pos) > src.count('"@', 0, pos):
        return True
    seg = src[src.rfind("\n", 0, pos) + 1:pos]
    q = None
    i = 0
    while i < len(seg):
        ch = seg[i]
        if q is None:
            if ch in "'\"":
                q = ch
        elif ch == q:
            if q == "'" and seg[i + 1:i + 2] == "'":
                i += 1                      # '' is an escaped quote
            else:
                q = None
        elif q == '"' and ch == "`":
            i += 1                          # backtick escapes the next char
        i += 1
    return q is not None


def native_calls(src):
    """Positions of things that look like a native-executable invocation.

    The position recorded is the COMMAND TOKEN's, never the match's: _CMD_POS
    consumes the preceding newline, so `m.start()` points at the end of the
    PREVIOUS line. The first backtest reported `Write-Host ...` as the line of a
    `dotnet` call because of exactly that, which also meant the stderr-redirect
    test was reading the wrong line.
    """
    found = {}
    for pat in (BARE_NATIVE, EXE_TOKEN):
        for m in pat.finditer(src):
            tok = m.group(1).strip()
            if tok and not in_string(src, m.start(1)):
                found.setdefault(m.start(1), tok)
    for m in CALL_OP_LIT.finditer(src):
        if not in_string(src, m.start()):
            found.setdefault(m.start(), "& " + m.group(2))
    for m in CALL_OP_VAR.finditer(src):
        if not in_string(src, m.start()) and var_kind(src, m.group(1)) == "native":
            found.setdefault(m.start(), "& $" + m.group(1))
    return sorted(found.items())


def line_of(src, pos):
    start = src.rfind("\n", 0, pos) + 1
    end = src.find("\n", pos)
    return src[start:end if end != -1 else len(src)].strip()


def analyze(text):
    """Return None, or a dict describing the hazard. Pure; no I/O."""
    if "ErrorActionPreference" not in text:
        return None
    src = strip_comments(text)
    stops = [(m.start(), eap_value(m.group(1))) for m in EAP_SET.finditer(src)]
    if not any(v == "stop" for _, v in stops):
        return None

    calls = native_calls(src)
    if not calls:
        return None

    # Walk in text order, tracking the governing preference.
    events = [(p, "eap", v) for p, v in stops] + [(p, "call", t) for p, t in calls]
    events.sort(key=lambda e: e[0])
    state = "inherited"
    governed = []
    for pos, kind, val in events:
        if kind == "eap":
            state = val
        elif state == "stop":
            governed.append((pos, val))
    if not governed:
        return None

    redirected = []
    for pos, tok in governed:
        ln = line_of(src, pos)
        if STDERR_REDIR.search(ln) and not CMD_C.search(ln):
            redirected.append((pos, tok, ln))

    first_pos, first_tok = governed[0]
    return {
        "n": len(governed),
        "first": first_tok,
        "first_line": line_of(src, first_pos),
        "redirected": redirected,
        "checks_lastexit": bool(LASTEXIT.search(src)),
    }


def payload_for(tool, inp):
    """The PowerShell-language text a tool call carries -> (text, label).

    THE ROUTING LIVES HERE, not in main(), so that `tools/ps-errorpref-backtest`
    can import it. The first backtest reimplemented this routing and silently
    diverged: it fed the whole Bash command to analyze() while the hook fed only
    the heredoc body, so the reported hits included a `powershell.exe ... 2>&1`
    line that belongs to Bash and is not governed by anything. The instrument
    was measuring a detector nobody runs -- and its own docstring claimed it
    could not. One function, one surface.
    """
    if not isinstance(inp, dict):
        return None, None
    fp = str(inp.get("file_path", "") or "")
    cmd = str(inp.get("command", "") or "")
    if tool == "PowerShell":
        return (cmd or None), "this command"
    if tool == "Write" and fp.lower().endswith(".ps1"):
        return (str(inp.get("content", "") or "") or None), os.path.basename(fp)
    if tool == "Edit" and fp.lower().endswith(".ps1"):
        return (str(inp.get("new_string", "") or "") or None), os.path.basename(fp)
    if tool == "Bash" and ".ps1" in cmd:
        bodies = [b for _, b in HEREDOC.findall(cmd) if "ErrorActionPreference" in b]
        return ((bodies[0] if bodies else cmd) or None), "this .ps1 heredoc"
    return None, None


def record(payload, finding, label, size):
    """Never raises. Excerpt only -- this guard denies nothing, so it owes no
    recovery copy, and a Write payload can be a whole file."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts": int(time.time()),
                "session": payload.get("session_id", ""),
                "tool": payload.get("tool_name", ""),
                "target": label,
                "bytes": size,
                "governed_calls": finding["n"],
                "first_call": finding["first"][:120],
                "first_line": finding["first_line"][:200],
                "stderr_redirected": len(finding["redirected"]),
                "checks_lastexit": finding["checks_lastexit"],
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def notice(text):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": text,
        }
    }))
    sys.exit(0)


def compose(finding, label):
    """The annotation. States which of the two directions actually applies here,
    because 'both directions' as a slogan is what the prose layer already said."""
    parts = ["ps-errorpref guard: %s sets $ErrorActionPreference='Stop' and then "
             "invokes what looks like a native executable%s — first at `%s`. In "
             "Windows PowerShell 5.1 that preference governs CMDLET errors; against "
             "an exe it is wrong in both directions."
             % (label,
                "" if finding["n"] == 1 else " (%d such calls)" % finding["n"],
                finding["first_line"][:160] or finding["first"][:80])]

    if finding["redirected"]:
        _, tok, ln = finding["redirected"][0]
        parts.append(
            "ACTIVE HERE: the call `%s` has its error stream redirected, so every "
            "stderr line becomes a NativeCommandError record and, under 'Stop', a "
            "TERMINATING one — this aborts the script on a harmless warning even at "
            "exit code 0." % ln[:160])
    else:
        parts.append(
            "No stderr redirection on the governed calls, so the false-abort half is "
            "dormant — it arms itself the moment a `2>&1`, `2>$null` or `*>&1` is "
            "added to one of them.")

    if finding["checks_lastexit"]:
        parts.append(
            "$LASTEXITCODE is checked somewhere in this text; confirm it is checked "
            "after EVERY native call, since 'Stop' will not stop on a non-zero exit.")
    else:
        parts.append(
            "And nothing here reads $LASTEXITCODE: a non-zero exit from the exe "
            "raises no PowerShell error at all in 5.1, so 'Stop' sails straight past "
            "the real failure. That is the half people do not expect.")

    parts.append(
        "Fix that fits an existing script: save the preference, set it to 'Continue' "
        "around the native call, check $LASTEXITCODE, restore — "
        "the shape written after this trap voided a run. If the combination is "
        "deliberate and verified, re-run with %s. Detail: ops/lessons.md L-024 tail "
        "and L-011 hit 3." % MARKER)
    return " ".join(parts)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    try:
        # Anything not carrying PowerShell text falls through before a single
        # regex runs -- this hook sits on high-volume tools.
        text, label = payload_for(str(payload.get("tool_name", "")),
                                  payload.get("tool_input") or {})
        if not text or MARKER in text:
            sys.exit(0)

        finding = analyze(text)
        if not finding:
            sys.exit(0)

        record(payload, finding, label, len(text.encode("utf-8", "replace")))
        notice(compose(finding, label))
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)


if __name__ == "__main__":
    main()
