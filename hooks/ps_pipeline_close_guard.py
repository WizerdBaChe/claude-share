r"""PreToolUse guard: an early-closing pipeline consumer downstream of a native
or interpreter command.

Scope: PowerShell-language text, wherever it is written. The DETECTOR reads four
surfaces - the PowerShell tool's `command`, and `.ps1` content arriving through
Write, Edit or a Bash heredoc. The REGISTRATION in `settings.json` is narrower,
and the difference is measured rather than assumed; see WHAT THE BACKTEST SAID.
Sibling guards, and why this is a separate file rather than a branch in one of
them: `shell_transport_guard.py` owns the Bash tool's TRANSPORT (backslash
collapse, size ceiling) and stays Bash-only on purpose;
`ps_errorpref_guard.py` owns `$ErrorActionPreference` and reads the same four
surfaces. Merging any two would make each one's scope claim false.

THE DEFECT (Windows PowerShell 5.1 and 7 alike; `ops/lessons.md` L-027; global
CLAUDE.md Environment section). A PowerShell pipeline is demand-driven at its
tail. `Select-Object -First N` closes the pipeline the moment N objects have
arrived, and CLOSING IT TERMINATES THE UPSTREAM PROCESS. So

    python analyze.py | Select-Object -First 30

does not run `analyze.py` and show the first 30 lines. It runs `analyze.py`
until line 30, kills it, and returns exit 255. Both halves of the damage point
AWAY from the cause:

  - the output is truncated, so the program looks like it stopped early for its
    own reasons (hit 1 of L-027 sent the author hunting a missing
    `if __name__ == "__main__":` guard in a script that was fine);
  - the exit code says failure, so the program looks broken.

The consumer is not the suspect, because the consumer is the part the author
just added to make the output shorter. That is why it cost two full diagnosis
rounds, days apart, in one project.

WHY A HOOK AND NOT A LESSONS ENTRY (ruling #8 of
`_bench-claude-arms/REVIEW_RETRO_ADVERSARIAL_2026-08-21.md`). L-027
was filed in `ops/lessons.md`, and L-011's own first line about that layer is
that it "fires only when something greps it, i.e. essentially never". The
routing rule in L-011 assigns by TRIGGER SHAPE: a named tool call with
inspectable input goes to a PreToolUse hook. This trap is exactly that shape -
it is decidable from the command text alone, more mechanically than the
`$ErrorActionPreference` trap that already has a guard, and it cost two rounds
where that one cost one. The layer was chosen by where the retrospective
happened to be writing, not by the rule.

ANNOTATE, NEVER DENY (gate authority, global CLAUDE.md). A gate may rule only on
what it can DETERMINE. `git log --oneline | Select-Object -First 5` is a real
and reasonable idiom: the author wants five lines, the termination is harmless,
and only `$LASTEXITCODE` is left misleading. `python build.py | Select-Object
-First 5` looks identical to a text scanner and destroys the run. Whether the
upstream process still had work to do is not decidable from the text, so this
guard hands the reader the distinction and gets out of the way.

WHAT THE BACKTEST SAID (2026-08-21, `tools/ps-pipeline-close-backtest`). Run
BEFORE registration, because L-011's fifth shape is that a hook on the wrong
SURFACE is as silent as prose - the neighbouring guard's ticket asked for a check
on the PowerShell tool when 47 of 53 real payloads arrived through Write. Here
the corpus said the exact opposite, which is the whole reason to measure per trap
instead of copying the neighbour's answer. Over 726 transcript files and 56 days
(2026-06-22..2026-08-20):

    tool         calls   PS payloads   tax/day   hazards found
    PowerShell    3411          3411      6.4 s   160   <- carries the hook
    Write         3548            85      6.7 s     0
    Edit          7668           142     14.4 s     0
    Bash         11367           226     21.3 s     0

Zero fires on the three file-writing surfaces in 56 days, for 42.4 s/day of
tax - so `settings.json` registers `PowerShell` alone and the other three
branches stay in the code, tested but unregistered, exactly as its neighbour
does in the opposite direction. This trap is an INTERACTIVE idiom: it is typed
at a prompt to shorten output, not written into a script.

Of the 160, 100 are `work`-tier and 60 are `report`-tier; only `work` annotates
(see FIRE_TIERS). Reading the first 28 distinct work-tier statements found no
false positive and several genuinely destructive ones - `dotnet publish ... |
Select-Object -First 40`, `npx playwright test ... | Select-Object -First 60`,
`.venv/Scripts/python.exe -m pytest ... | Select-Object -First 16`. A publish and
a test run, killed to shorten a screen. Rate as registered: 100 fires / 3411
inspected payloads = 2.93%, 1.79 per day. `ops/rule-registry.md` key
`ps_pipeline_close_guard` holds the rows and the review-when.

WHAT IT DOES NOT DECIDE, stated so a reader does not over-trust it. This is a
masked positional scan, not a PowerShell parser:
  - the upstream command is classified by NAME. A `Verb-Noun` token or a known
    cmdlet alias is treated as safe (a cmdlet cannot be killed by pipeline
    close); an unrecognised bare word is UNKNOWN and does not fire. A
    user-defined function that shells out is therefore missed, deliberately;
  - `& $x` counts only when `$x`'s assignment names an .exe/.cmd/.bat - the
    same one-hop classification, and the same largest-false-positive-class
    reason, as `ps_errorpref_guard.var_kind`;
  - a pipeline built at runtime out of `Invoke-Expression` is invisible;
  - `-First` reached through a variable (`Select-Object @splat`) is invisible.
Under-firing is the chosen error direction throughout, for the same reason as
the sibling: an annotate-only guard justifies itself by costing nothing to read,
and that stops being true the moment it talks over correct code.

WHAT IS DELIBERATELY NOT FLAGGED, so it is not re-proposed as an improvement:
  - `Get-Content big.log | Select-Object -First 20`. The upstream is a cmdlet,
    nothing is killed. It is merely slower than `-TotalCount 20`, and a guard
    that fires on inefficiency is a linter, not a hazard gate.
  - `Where-Object`, `Out-String`, `Sort-Object`, `Measure-Object`, `Out-File`
    and `ForEach-Object` as the tail: all of them consume the whole pipeline.
    Only an early-closing consumer is the hazard.
  - `git diff | Select-Object -First 40` and its family: detected, counted, and
    silent. 60 of the 160 corpus hazards are this, every one of them an author
    asking for the first N lines of something that only prints. See FIRE_TIERS.

Per-instance escape hatch: the literal marker [pipeline-checked] anywhere in the
payload, for a truncation whose author has verified the upstream is safe to kill.

Fail-open by design: any parse error exits 0, so a guard bug never blocks work.
Telemetry: every notice appends one row to `telemetry/ps-pipeline-close.jsonl`
(excerpt only, never the whole file). Proof-of-life check:
`ops/references/integrity-sweep.md` check 23 - a hook that does not run is
itself silent (L-011, COST OF P1/P3).
"""
import json
import os
import re
import sys
import time

MARKER = "[pipeline-checked]"

# Overridable so the test suite and the integrity sweep can DRIVE this hook
# without writing into the real log (integrity-sweep check 20, P-005: a probe
# run bare once leaked a synthetic row into production telemetry, and a rate you
# have to subtract from is a rate nobody re-checks).
LOG_PATH = os.environ.get("PS_PIPECLOSE_LOG") or os.path.join(
    os.path.expanduser("~"), ".claude", "telemetry", "ps-pipeline-close.jsonl")

# --------------------------------------------------------------------------
# Classification tables.
#
# TIER_WORK   - the upstream is executing a program that may still have work to
#               do, or side effects to finish. Killing it mid-run is the L-027
#               damage, so this tier annotates.
# TIER_REPORT - a native exe whose whole job is to print and exit. Killing it
#               costs a misleading $LASTEXITCODE and nothing else. DETECTED AND
#               MEASURED, but not annotated - see FIRE_TIERS.
# Membership rule, so the lists can be extended without re-arguing: a name goes
# in TIER_REPORT only if it CANNOT mutate anything. That is why `az`, `aws`,
# `gcloud`, `reg`, `schtasks`, `netsh`, `signtool`, `nuget` and `openssl` sit in
# TIER_WORK despite reading like reporters - each of them can create or change
# something, and a half-finished one is the expensive case.
# --------------------------------------------------------------------------
TIER_WORK = (
    "python", "python3", "py", "pytest", "pip", "pip3", "uv", "poetry", "conda",
    "node", "npm", "npx", "pnpm", "yarn", "deno", "bun", "tsc", "ts-node",
    "ruby", "perl", "php", "java", "javac", "gradle", "mvn",
    "dotnet", "msbuild", "cargo", "rustc", "go", "make", "cmake", "ninja",
    "gcc", "clang", "cl", "link",
    "ffmpeg", "ffprobe", "yt-dlp", "magick", "pandoc",
    "docker", "podman", "kubectl", "helm", "terraform",
    "robocopy", "xcopy", "rsync", "tar", "unzip", "7z", "ssh", "scp",
    "pwsh", "powershell", "cmd", "bash", "sh", "wsl", "adb", "claude",
    "az", "aws", "gcloud", "reg", "schtasks", "netsh", "signtool", "nuget",
    "openssl", "certutil",
)
TIER_REPORT = (
    "git", "gh", "rg", "findstr", "fc", "tree",
    "systeminfo", "tasklist", "nvidia-smi", "ipconfig", "wmic", "vswhere",
)

# Bare words Windows PowerShell 5.1 resolves to a CMDLET or FUNCTION, not to an
# exe. A cmdlet is not a process and cannot be killed by pipeline close, so
# these must never fire. `more` is the exception and lives in EARLY_CLOSE.
CMDLET_ALIASES = frozenset("""
gci ls dir gc cat type gi gp gm gu gv gl gh_ ni nv ri rp rv sc si sp sv
select where foreach group sort measure compare tee ft fl fw fh
echo write cls clear cd chdir pushd popd pwd copy cp move mv del erase rd rmdir
ps kill sleep man help history h r ise saps spps start stop
diff epal epcsv ipal ipcsv gsv sasv spsv gwmi gcm gjb rjb sajb wjb
curl wget iwr irm ac asnp
""".split())

# The hazard: a consumer that stops asking for input before the source is done.
# `Select-Object -First N` (and its `select` alias) is the documented case;
# PowerShell accepts unambiguous parameter prefixes, and among Select-Object's
# parameters `-f` can only be `-First`. `more` pages and closes the same way.
EARLY_CLOSE = re.compile(
    r"^\s*(?:"
    r"(?:select-object|select(?![\w-]))\b[^|]*?\s-f(?:i(?:r(?:s(?:t)?)?)?)?\b"
    r"|more(?:\.com)?\s*$"
    r")", re.I)

EXE_SUFFIX = re.compile(r"\.(?:exe|cmd|bat|com)$", re.I)
VERB_NOUN = re.compile(r"^[a-z]+-[a-z0-9_]+$", re.I)
ASSIGN_PREFIX = re.compile(r"^\s*\$[\w:]+\s*(?:\+|-|\*|/)?=\s*")
LEADING_CALL = re.compile(r"^\s*&\s*")


def mask(text):
    """Return a same-length copy of `text` with the CONTENT of comments, string
    literals and here-strings replaced by spaces.

    Positional splitting then sees only code. This is load-bearing rather than
    cosmetic: the most common way `| Select-Object -First` appears in a .ps1 is
    inside a Write-Host line explaining a command to a human, and scoring those
    would make the guard loudest where nothing runs.
    """
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        # <# ... #> block comment
        if ch == "<" and nxt == "#":
            j = text.find("#>", i + 2)
            j = n if j == -1 else j + 2
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
            continue
        # here-string @' ... '@  /  @" ... "@
        if ch == "@" and nxt in "'\"":
            term = "\n" + nxt + "@"
            j = text.find(term, i + 2)
            j = n if j == -1 else j + len(term)
            for k in range(i, j):
                if out[k] != "\n":
                    out[k] = " "
            i = j
            continue
        # whole-line comment (a trailing # after code is left alone: a # inside
        # a string literal must not be able to swallow real code)
        if ch == "#" and text[:i].rsplit("\n", 1)[-1].strip() == "":
            j = text.find("\n", i)
            j = n if j == -1 else j
            for k in range(i, j):
                out[k] = " "
            i = j
            continue
        if ch in "'\"":
            q, j = ch, i + 1
            while j < n:
                if text[j] == "`" and q == '"':
                    j += 2
                    continue
                if text[j] == q:
                    if q == "'" and text[j + 1:j + 2] == "'":
                        j += 2
                        continue
                    break
                if text[j] == "\n":          # unterminated - do not eat the file
                    break
                j += 1
            for k in range(i + 1, min(j, n)):
                if out[k] != "\n":
                    out[k] = " "
            i = min(j, n) + 1
            continue
        i += 1
    return "".join(out)


def statements(text, code):
    """Split into pipeline statements, as (start, end) offsets into `text`.

    Separators are `\\n`, `;`, `&&` and `||` at bracket depth 0. A newline that
    CONTINUES a pipeline is not a separator: PowerShell continues when the line
    ends with `|` or a backtick, and (7+) when the next line starts with `|`.
    Missing that is how a two-line pipeline escapes a one-line scanner.
    """
    spans, start, depth = [], 0, 0
    i, n = 0, len(code)
    while i < n:
        ch = code[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif depth == 0:
            if ch == ";":
                spans.append((start, i))
                start = i + 1
            elif ch in "&|" and code[i:i + 2] in ("&&", "||"):
                spans.append((start, i))
                i += 2
                start = i
                continue
            elif ch == "\n":
                before = code[start:i].rstrip()
                after = code[i + 1:].lstrip()
                if not (before.endswith("|") or before.endswith("`")
                        or after.startswith("|")):
                    spans.append((start, i))
                    start = i + 1
        i += 1
    spans.append((start, n))
    return [(a, b) for a, b in spans if code[a:b].strip()]


def segments(code, a, b):
    """Split one statement into pipeline segments, as offsets into the text."""
    out, start, depth = [], a, 0
    for i in range(a, b):
        ch = code[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif ch == "|" and depth == 0 and code[i:i + 2] != "||" \
                and not (i > a and code[i - 1] == "|"):
            out.append((start, i))
            start = i + 1
    out.append((start, b))
    return out


def var_kind(src, name):
    """One-hop classification of the variable in `& $name`.

    Same rule and same evidence as `ps_errorpref_guard.var_kind`: in this corpus
    `& $var` is a script block or another .ps1 about as often as it is an exe,
    and neither of those is a separate process, so only a variable whose
    assignment names an executable counts.
    """
    pat = re.compile(r"\$(?:script:|global:|local:)?"
                     + re.escape(name.split(":")[-1]) + r"\s*=\s*([^\r\n]+)", re.I)
    for m in pat.finditer(src):
        rhs = m.group(1).lstrip()
        if rhs.startswith("{"):
            return "block"
        if re.search(r"\.ps1\b", rhs, re.I):
            return "script"
        if re.search(r"\.(?:exe|cmd|bat|com)\b", rhs, re.I):
            return "native"
    return "unknown"


def classify(src, seg):
    """Classify one pipeline segment -> ('work' | 'report' | 'safe' | 'unknown',
    displayed token)."""
    s = ASSIGN_PREFIX.sub("", seg).strip()
    if not s:
        return "unknown", ""
    called = False
    if LEADING_CALL.match(s):
        called, s = True, LEADING_CALL.sub("", s).strip()
    if s.startswith("{"):
        return "safe", "{ }"                      # script block, not a process
    if s.startswith("$"):
        m = re.match(r"\$([\w:]+)", s)
        if called and m and var_kind(src, m.group(1)) == "native":
            return "work", "& $" + m.group(1)
        return "unknown", s[:40]
    if s.startswith("("):
        return "unknown", s[:40]                  # subexpression - not resolved
    if s[0] in "'\"":
        m = re.match(r"(['\"])(.*?)\1", s)        # `& "C:\Program Files\x.exe"`
        tok = m.group(2) if m else s.split()[0].strip("'\"")
    else:
        tok = s.split()[0]
    base = EXE_SUFFIX.sub("", tok)
    leaf = re.split(r"[\\/]", base)[-1].lower()
    if EXE_SUFFIX.search(tok) or re.search(r"[\\/]", tok):
        return ("work", tok) if (EXE_SUFFIX.search(tok) or called) else ("unknown", tok)
    if leaf in CMDLET_ALIASES:
        return "safe", tok
    if VERB_NOUN.match(base) and leaf not in TIER_WORK and leaf not in TIER_REPORT:
        return "safe", tok
    if leaf in TIER_WORK:
        return "work", tok
    if leaf in TIER_REPORT:
        return "report", tok
    return "unknown", tok


# Which classes actually annotate. SET FROM THE BACKTEST, not from taste.
# Over 56 days the detector found 160 hazards on the PowerShell tool: 100 in the
# `work` tier and 60 in `report` - and all 60 of those were `git diff|show|log`
# or `gh`, i.e. an author asking for the first N lines of something that only
# prints. Annotating them would be 1.07 notices/day over code that is correct,
# which is how an annotate-only guard trains its reader to skim it (40-
# maintenance.md §4.3, ritualization). So `report` stays DETECTED and MEASURED
# and does not speak. Re-open this line if the backtest's report rows ever show
# an upstream that can mutate something; the tier tables carry the membership
# rule that keeps that from drifting. `ops/rule-registry.md` key
# `ps_pipeline_close_guard` holds the rows and the review-when.
FIRE_TIERS = ("work",)


def scan_regions(code):
    """The whole text, plus the inside of every `{ }` block.

    Two passes rather than one, because a pipeline can live at either level and
    a single pass has to lose one of them. `segments()` deliberately does not
    split on a `|` inside braces - otherwise
    `python x.py | ForEach-Object { Get-Item $_ } | Select-Object -First 4`
    would be torn in half and the real hazard would vanish. The cost of that is
    that `foreach (...) { python x.py | Select-Object -First 1 }` is invisible
    at the top level, so the block bodies are scanned as regions of their own.
    Hits are deduplicated by statement text.
    """
    regions, stack = [(0, len(code))], []
    for i, ch in enumerate(code):
        if ch == "{":
            stack.append(i)
        elif ch == "}" and stack:
            a = stack.pop()
            if i - a > 1:
                regions.append((a + 1, i))
    return regions


def analyze(text):
    """Return None, or a dict describing the hazard. Pure; no I/O."""
    if "|" not in text:
        return None
    low = text.lower()
    if "select" not in low and "more" not in low:
        return None
    code = mask(text)
    hits, seen = [], set()
    for ra, rb in scan_regions(code):
        for a, b in statements(text[ra:rb], code[ra:rb]):
            a, b = a + ra, b + ra
            segs = segments(code, a, b)
            if len(segs) < 2:
                continue
            closer = None
            for idx, (sa, sb) in enumerate(segs):
                # Truncate at the first `{`: a script block's body can contain
                # the `-f` FORMAT OPERATOR (`{ $_ -f 1 }`), which is not the
                # `-First` parameter and must not read as one.
                if idx and EARLY_CLOSE.match(code[sa:sb].split("{")[0]):
                    closer = idx
                    break
            if closer is None:
                continue
            for sa, sb in segs[:closer]:
                tier, tok = classify(text, text[sa:sb])
                if tier in FIRE_TIERS:
                    stmt = " ".join(text[a:b].split())[:200]
                    if (tok, stmt) in seen:
                        break
                    seen.add((tok, stmt))
                    hits.append({
                        "tier": tier,
                        "upstream": tok[:60],
                        "consumer": text[segs[closer][0]:segs[closer][1]].strip()[:60],
                        "statement": stmt,
                    })
                    break
    if not hits:
        return None
    return {
        "n": len(hits),
        "first": hits[0],
        "tiers": sorted({h["tier"] for h in hits}),
        "all": hits,
    }


def payload_for(tool, inp):
    """The PowerShell-language text a tool call carries -> (text, label).

    THE ROUTING LIVES HERE, not in main(), so the backtest can import it instead
    of reimplementing it. The neighbouring guard's first backtest kept its own
    copy, diverged the same day, and reported hits on a detector nobody runs.
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
        return (cmd or None), "this .ps1 heredoc"
    return None, None


def record(payload, finding, label, size):
    """Never raises. Excerpt only - this guard denies nothing, so it owes no
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
                "hazards": finding["n"],
                "tiers": finding["tiers"],
                "upstream": finding["first"]["upstream"],
                "consumer": finding["first"]["consumer"],
                "statement": finding["first"]["statement"],
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
    """The annotation. It names the actual pair, because 'beware of pipelines'
    is what the prose layer already said and it did not fire twice."""
    h = finding["first"]
    parts = ["ps-pipeline-close guard: %s pipes `%s` into `%s`%s. In PowerShell "
             "an early-closing consumer stops the pipeline as soon as N objects "
             "arrive, and closing it TERMINATES the upstream process."
             % (label, h["upstream"], h["consumer"],
                "" if finding["n"] == 1 else " (and %d more such pipelines)" % (finding["n"] - 1))]
    parts.append("Statement: %s" % h["statement"])

    if h["tier"] == "work":
        parts.append(
            "`%s` runs a program that may still have work to do, so this is the "
            "L-027 shape exactly: the program dies mid-run, the output truncates "
            "(looks like it stopped early for its own reasons) and the call "
            "returns a failure exit code (looks broken). Both signals point away "
            "from the consumer you just added." % h["upstream"])
    else:
        parts.append(
            "`%s` normally prints and exits, so the likely cost here is only a "
            "misleading exit code rather than lost work - check $LASTEXITCODE "
            "before trusting it, and re-check this if the command was ever going "
            "to do more than print." % h["upstream"])

    parts.append(
        "Let it finish and slice afterwards: `$out = & %s ...; $out | %s`. For a "
        "file use `Get-Content <file> -TotalCount N`; for genuinely large output "
        "redirect to a file and read the file. `Where-Object`, `Out-String`, "
        "`Sort-Object` and `Measure-Object` consume the whole pipeline and are "
        "safe - the hazard is only the early-closing consumers "
        "(`Select-Object -First`, `... | more`)."
        % (h["upstream"], h["consumer"]))
    parts.append(
        "If the truncation is deliberate and the upstream is safe to kill, "
        "re-run with %s. Detail: ops/lessons.md L-027." % MARKER)
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
