r"""PreToolUse guard: a live credential file may never enter the agent's context,
and a credential value may never be printed into the transcript.

STATUS: LIVE since 2026-08-27 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).
Property 2 (whole-environment dumps, credential-key greps over config-shaped
files) LIVE since 2026-10-03 — see the PROPERTY 2 block below; registry key
`SECRET_PRINT_GUARD`.

WHY A HOOK AND NOT A POLICY LINE. The connector layer's whole premise is a
one-way boundary: the agent may RUN a program that holds a key, and may never
READ the key. A prose rule fails at the exact moment it matters — a connector
returns 401 and the single most tempting next move is `cat .env` to "check the
key is there". Same argument as ui_verify_guard (L-011) and
transcript_read_guard: enforce, don't recall.

RULE (asset property, not a path instruction): a file whose name marks it as a
credential store may not be read by any tool, anywhere on this machine, at any
time. Not "in connector directories" — the property belongs to the file.

Covered tools: Read, Grep (content search would print the value), Bash and
PowerShell (cat / Get-Content / sed / findstr / strings / python open()).
Write is deliberately NOT covered: writing a .gitignore line or scaffolding a
.env.example is legitimate and reveals nothing.

TEMPLATES ARE NOT SECRETS: `.env.example` / `.env.sample` / `.env.template`
pass — they are the documented way to learn WHICH variables a connector needs
without learning their values.

THE COMPLIANT PATH the deny message must always name: run the connector's own
probe (`skills/literature-search-extract/connectors/probe.py`), which loads the
credential itself and reports presence/length/liveness without ever printing a
value. If a key is wrong or missing, the USER edits the .env; the agent never
does.

KNOWN BOUNDARY, accepted deliberately: this matches the TOKEN, not the
OPERATION. A shell command that merely *mentions* a credential filename is
denied even when it reads nothing — writing a commit message about the boundary
is the case that found it (2026-08-26, on this file's own first commit). The
blunt direction is the safe one: narrowing to "a read verb near the token"
means enumerating cat/type/head/sed/strings/Get-Content/open()/curl -T/scp and
losing to the first verb nobody listed. Say "credential file" in prose instead;
that costs a word. PROMOTION TRIGGER, named: if this blocks legitimate work
more than ~3 times, narrow it to read-verb proximity and add each observed false
positive to the must-pass suite first, so the narrowing is measured rather than
guessed.

OBSERVED FALSE POSITIVES (running count — this IS the trigger's evidence; add
to it, do not reset it):
  1. 2026-08-26  a git commit message describing this boundary
  2. 2026-08-26  `git check-ignore -v <path>` — a pure metadata query that
                 reads no content, run to confirm a future key would be ignored
  3. 2026-08-27  the SQL alias `i.key` in a `python -c` query against a Zotero
                 database — not a path at all, and it blocked real work
  4. 2026-10-04  PowerShell, read-only inventory card WC-P1-08 (sonnet
                 work-card executor, row 7f7497): a `-notmatch 'token|secret|
                 \.pem$|…'` EXCLUSION over Get-ChildItem names, plus a never-used
                 `$cred='…'` variable holding the same regex; timestamps only
  5. 2026-10-04  Bash, card WC-P1-09 (row 396444): `find . -type f | grep -i -E
                 '\.env|token|…'` — a names-only listing of which credential-
                 looking files EXIST (the shell twin of Glob, exempt above),
                 printed to the terminal; an inclusion, not an exclusion
                 Both cards said "never open credential-like files (<the name
                 patterns>)" and both executors copied that list into a filter:
                 the card text manufactured the misfire. Card authors say
                 "credential file" in prose instead (work-card template note).
  6. 2026-09-26  a signing tool handed a keystore path it reads itself
                 (reported via report_fp that day; folded here 2026-10-04).
                 NOT CLEARED: by token alone a tool that consumes a key cannot
                 be told from one that prints it — the override marker is the route
  7. 2026-09-27  a TypeScript property access on a `dataset` object inside a
                 python heredoc that wrote a .ts file (reported; folded
                 2026-10-04). NOT CLEARED: a property access and a key file are
                 the same token; the cost is writing the file with Write instead
  8. 2026-10-03  `grep -rln -i "secret\|api.key\|token" <dir>/*.py` — a
                 credential word as a names-only grep PATTERN (reported; folded
                 2026-10-04). CLEARED by narrowing pass 2
  9. 2026-10-04  prose naming FP-7's token inside a `ledger.py add --choice`
                 argument while this entry was being written (row 49c5ea) — the
                 FP-1 class outside `-m`. NOT CLEARED: prose arguments of
                 arbitrary tools are not determinable; say "credential file"
 10. 2026-10-05  FP-7 again: a JS `dataset` property name inside a python
                 heredoc that patched an HTML page (folded 2026-10-06). NOT
                 CLEARED, same reason as FP-7; the route is Write/Edit on the
                 file, never a heredoc carrying JS. Second instance of the
                 class -> a THIRD makes it the next narrowing candidate
                 (property-access form `\.dataset\.key\b` is determinable).
  Numbering is the order of logging: FP-6..8 happened before FP-4/5 but sat
  only in telemetry/hook-false-positives.jsonl until 2026-10-04.

NARROWING PASS DONE 2026-08-27 at FP-3, as promised. Not the read-verb
proximity originally sketched: FP-1's own text contained "cat", so a verb rule
would not have cleared it. What the three FPs actually had in common is that
the credential name was being TALKED ABOUT or RESOLVED, never read — so the
fix strips message bodies and metadata-only git subcommands before scanning,
and requires a 3+ character stem before `.key`. All 12 must-deny cases still
deny; the three FPs are now the must-pass FLOOR in tools/secret-guard-test/
(18 must-pass total), so a later re-tightening cannot silently undo this.

NARROWING PASS 2 DONE 2026-10-04 at FP-5. FP-4, FP-5 and FP-8 share one
shape: the credential name was a PATTERN over names or lines, never a path.
`strip_name_patterns()` (branch list above it) blanks a pattern operand before
scanning ONLY where it cannot name the file the same statement reads: negated
filters (`-notmatch`/`-notlike`, `-Exclude`, find `-not|! -name`, `-name …
-prune -o`, grep `--exclude`), grep patterns in names/count mode, inverted
non-recursive greps, positive greps whose remaining pipeline is stream filters
only, and literal variables nothing else references. Positive selection
feeding a reader (`| xargs cat`, `$( )`, `while read`, `-exec`, `-match … |
Get-Content`, `-Include`, `--include`, `grep -f`, `-prune` without `-o`, a
referenced or `$env:` variable) still denies, each as a must-deny twin.
Evidence 2026-10-04: suite 40 must-deny / 50 must-pass / 0 failures (before
the code change: the 9 new must-pass cases denied, all 14 twins denied);
mutation run — removing any of the 7 restrictions flips its twin (closed tail
14/14 → 11/14 deny), removing any branch re-denies the cases it clears;
backtest over 73,318 unique recorded shell commands: property-1 denies
84 → 75, 0 newly denied, the 9 cleared = FP-4, FP-5, FP-8, two `| grep -v`
stream filters, four code/manifest greps over .js/.toml/.py — every cleared
operand a non-credential file or a stream.
KNOWN BOUNDARY found while writing the twins, PRE-EXISTING and left as is: a
glob such as `*.pem` never matched (`*` is not a boundary char), so a glob of a
credential extension feeding a reader passes; tightening it would also gate
names-only `ls`/`find` listings. User ruling 2026-10-04: left as is until a
glob read of a credential is OBSERVED (review-when below). Not cleared
because not observed: positive `find -name` listings, Select-String patterns.
Next FP: append here, and narrow again only with the whole floor still green.

Fail-open on malformed input; deny is the only non-silent path.
review-when: a connector is registered whose credential file does not match
these patterns (add it to SECRET_TOKEN below — the single edit point), or
Claude Code adds a file-reading tool not in the matcher list, or a shape that
pass 2 clears is observed feeding a reader (add it to MUST_DENY, then narrow
that branch), or a glob of a credential extension is observed feeding a reader
(the 2026-10-04 ruling's trigger: decide the boundary char then, with the
names-only listings as must-pass cases first).

Proof-of-life: `python tools/secret-guard-test/test_secret_file_guard.py`
(two-sided: 50 must-deny, 53 must-pass — property 2 added 14 and 23, narrowing
pass 2 added 14 and 9, the property-2 masking fix P2-1 added 10 and 3).
"""
import json
import re
import sys

try:                        # receipt + misfire exit (rules/hook-deny-message.md)
    from deny_receipt import clause as _receipt, fp_clause as _fp
except Exception:           # a guard must not stop guarding if telemetry breaks
    def _receipt(hook, **fields): return ""
    def _fp(hook): return ""

# --- CONFIG: single edit point ---------------------------------------------
# A filename shape that means "this file holds a live credential".
# Anchored so it only fires on path-like occurrences, never on `$env:TEMP`,
# `conda env`, or `dict.keys()`.
SECRET_TOKEN = re.compile(
    r"""(?:^|[\s"'=<>|(,;&])            # start, or a shell/arg boundary
        (?:[~\w.\\/:+-]*[\\/])?         # optional leading directory part (~ incl.)
        (
            \.env(?!\.(?:example|sample|template)\b)[\w.-]*
          | [\w.-]*\.(?:pem|p12|pfx|jks|keystore)
          # `.key` needs a stem of 3+ chars OR a path separator before it.
          # Narrowed 2026-08-27 (FP-3): a bare `[\w.-]*\.key` matched the SQL
          # alias `i.key` and blocked a database query. Real key files are
          # `server.key` / `client.key` / `certs/x.key`, never one letter.
          | [\w.-]{3,}\.key
          | credentials?\.json
          | secrets?\.json
          | token\.json
          | id_rsa[\w.]*
          | id_ed25519[\w.]*
        )
        \b""",
    re.VERBOSE | re.IGNORECASE,
)

# Escape hatch, same contract as dangerous_command_guard / model_cap_guard: the
# orchestrator may add this marker ONLY after the user approved that specific
# read in conversation. Reading a credential is never routine.
OVERRIDE = "[user-approved-secret-read]"
# ---------------------------------------------------------------------------

COMPLIANT_PATH = (
    "Run the connector's probe instead — it loads the credential itself and "
    "reports presence, length and liveness without printing a value: "
    "python ~/.claude/skills/literature-search-extract/connectors/probe.py "
    "--id <connector>. Variable NAMES are not gated, only values, so a "
    "connector's own .env.example stays available. A wrong or missing key is "
    "fixed by the USER editing the .env, never by the agent."
)


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


# Narrowing pass 2026-08-27, at the third observed false positive exactly as
# the promotion trigger promised. Two shapes are stripped BEFORE scanning,
# because in both the credential name is being TALKED ABOUT, not read:
#   FP-1  a commit/tag message body — prose about the boundary is not a read
#   FP-2  git subcommands that resolve names and cannot print file contents
# Everything else still denies. The three FPs are now the must-pass floor in
# tools/secret-guard-test/, so a future re-tightening cannot silently undo this.
MESSAGE_BODY = re.compile(r"""(-m|--message)\s+("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')""")
METADATA_ONLY_GIT = re.compile(r"\bgit\s+(check-ignore|check-attr|ls-files)\b")

# Narrowing pass 2026-10-04, at FP-5. FP-4, FP-5 and FP-8 shared one shape:
# the credential name was a PATTERN over names or lines (a -notmatch exclusion
# and a dead regex variable; a names-only `find | grep` listing; a `grep -l`),
# never a path. A pattern operand is blanked before scanning ONLY where it
# cannot name the file the same statement reads; every branch has a must-deny
# twin in tools/secret-guard-test/ that turns its shape into a read.
#   negated filters  drop what matches, so a reader downstream reads the rest:
#                    `$x -notmatch 'p'`, `-Exclude a,b`, find `-not|! -name p`,
#                    find `-name p -prune -o`, grep `--exclude[-dir]=p`
#   grep patterns    names/count mode (-l -L -c -q); inverted and not
#                    recursive; positive only when every later stage of the
#                    pipeline is a stream filter that cannot open a name it is
#                    handed (head/sort/wc/...), so `| xargs cat`, `$( )`,
#                    `while read` keep denying. -f (pattern FILE) never strips.
#   dead literals    `$v = 'p'` / `v='p'` whose name appears nowhere else once
#                    the negated operands above are gone; `$env:` and
#                    `V='p' cmd` reach a child process and never strip.
_QUOTED = r"'[^']*'" + "|" + r'"(?:[^"\\]|\\.)*"'
_OPERAND = "(?:" + _QUOTED + r"""|[^\s'"|;&()<>,]+)"""
NEGATED_FILTERS = (
    re.compile(r"(?i)(?:\$[\w:.]+|\))\s+-[ci]?not(?:match|like)\s+(?P<op>" + _QUOTED + r"|\$\{?[\w:]+\}?)"),
    re.compile(r"(?i)(?<![\w-])-Exclude\s+(?P<op>" + _OPERAND + r"(?:\s*,\s*" + _OPERAND + ")*)"),
    re.compile(r"(?:(?<=\s)-not|(?<=\s)\\?!)\s+-i?(?:name|path|wholename|regex)\s+(?P<op>" + _OPERAND + ")"),
    re.compile(r"-i?(?:name|path|wholename)\s+(?P<op>" + _OPERAND + r")\s+-prune\s+-o(?=\s)"),
    re.compile(r"--exclude(?:-dir)?(?:=|\s+)(?P<op>" + _OPERAND + ")"),
)
GREP_STAGE = re.compile(r"(?:^|(?<=[\s|;&(]))[ef]?grep(?P<flags>(?:\s+(?:-[A-Za-z]+|--[\w-]+(?:=\S+)?))*)"
                        r"\s+(?P<op>" + _OPERAND + ")")
_ARGS = r"(?:[^|;&()<>`$\n]|\d?>\s*/dev/null|2>&1)*"
CLOSED_TAIL = re.compile(_ARGS + r"(?:\|\s*(?:head|tail|sort|uniq|wc|cut|tr|nl|[ef]?grep)(?![\w-])"
                         + _ARGS + r")*(?:$|;|&&|\|\||\n)")
DEAD_LITERAL = (
    re.compile(r"\$(?P<name>[A-Za-z_]\w*)(?!:)\s*=\s*(?P<op>" + _QUOTED + ")"),
    re.compile(r"(?:^|(?<=[;&\n]))\s*(?P<name>[A-Za-z_]\w*)=(?P<op>" + _QUOTED + r")(?=\s*(?:;|&&|\n|$))"),
)


def _blank(text: str, spans: list) -> str:
    for s, e in sorted(spans, reverse=True):
        text = text[:s] + " " + text[e:]
    return text


def _grep_pattern_strippable(text: str, m: re.Match) -> bool:
    rest = re.match(r"[^|;&\n)]*", text[m.end():]).group(0)
    words = re.findall(r"(?:^|\s)(--?[\w-]+)", m.group("flags") + " " + rest)
    shorts = "".join(w[1:] for w in words if not w.startswith("--"))
    longs = {w for w in words if w.startswith("--")}
    if "f" in shorts or "--file" in longs:
        return False                       # the operand is a pattern FILE: a read
    if set(shorts) & set("lLcq") or longs & {"--files-with-matches", "--files-without-match",
                                              "--count", "--quiet", "--silent"}:
        return True                        # prints names or a count, never a line
    if set(shorts) & set("rRd") or longs & {"--recursive", "--dereference-recursive", "--directories"}:
        return False                       # recursive content mode reads every file
    if "v" in shorts or "--invert-match" in longs:
        return True
    return CLOSED_TAIL.match(text, m.end()) is not None


def strip_name_patterns(text: str) -> str:
    """Blank the pattern operands that cannot name the file read (see above)."""
    for rx in NEGATED_FILTERS:
        text = _blank(text, [m.span("op") for m in rx.finditer(text)])
    text = _blank(text, [m.span("op") for m in GREP_STAGE.finditer(text)
                         if _grep_pattern_strippable(text, m)])
    for rx in DEAD_LITERAL:
        dead = []
        for m in rx.finditer(text):
            elsewhere = text[:m.start()] + " " + text[m.end():]
            if not re.search(r"(?i)(?<!\w)" + re.escape(m.group("name")) + r"(?!\w)", elsewhere):
                dead.append(m.span("op"))
        text = _blank(text, dead)
    return text

# --- PROPERTY 2 (born 2026-10-03): a credential VALUE may not be PRINTED -----
# Property 1 gates reading a file NAMED as a credential store. The R05 B1 sweep
# of 4,719 transcript files found two live values that got in another way, both
# printed by the agent itself: a whole-process environment dump (psutil
# `Process.environ()` inside a PowerShell python block, 2026-10-02, put the
# Claude Code OAuth token in the transcript) and a content grep for
# `password` over an application preferences file (2026-09-17). Transcripts are
# kept 3650 days and mirrored twice, so a printed value is a leaked value.
# Two determinable FORMS are gated; the undeterminable half (is this particular
# value secret?) is forwarded to the compliant rewrite, which costs nothing:
#   (a) a WHOLE-environment dump. One named variable passes ($env:TEMP,
#       printenv HOME, os.environ["X"]); so does a names-only listing.
#   (b) a content search whose pattern names a credential key and whose target
#       is a config-shaped file, printing matching lines. -l / -c / -q pass.
# KNOWN BOUNDARY: Read of a config-shaped file is NOT gated (it is the normal
# way to inspect configuration); neither is an unlabelled secret.
#
# PROPERTY-2 MISFIRES (running count, separate from property 1's log above;
# the SECRET_PRINT_GUARD review-when narrows at 3 — add, do not reset):
#   P2-1  2026-10-04  a value-MASKING grep, `grep … | sed 's/=.*/=<REDACTED>/'`
#         (a real call in that day's backtest), denied although GREP_PATH
#         names exactly that rewrite. A DEFECT IN THE RETRY TEXT, not a
#         narrowing of the gate's object: the deny message's third route
#         (R2, rules/hook-deny-message.md) led to the same deny, because
#         cred_grep_command honoured COUNT_ONLY only and the masking projection
#         was consulted by env_dump alone. Measured before the fix: the -c form
#         passed, GREP_PATH's own example denied. FIXED: MASK_SED below — a
#         masking sed AFTER the search in the same pipeline clears it, every
#         searching statement must be masked; must-pass 50 → 53, ten must-deny
#         twins (selecting/editing sed, `&`, `-e p`, tee, `>&2`, a second raw
#         search, the mask in another statement, sed reading a file). Mutation
#         run: dropping any one restriction flips at least one twin. The change
#         only adds a pass path, so nothing is newly denied. Counted as 1 of 3
#         toward the review-when, though the trigger condition was NOT loosened
#         beyond what the deny text already promised.
ENV_DUMP = re.compile(r"""
      \.environ\(\)                                        # psutil Process.environ()
    | /proc/[\w$*{}]+/environ
    | \b(?:print|pprint|json\.dumps)\s*\(\s*(?:dict\(\s*)?os\.environ\s*\)
    | console\.log\(\s*process\.env\s*\)
    | \[(?:System\.)?Environment\]::GetEnvironmentVariables\(
    | (?:^|;|&&|\|\|)[ \t]*(?:printenv|env|export\s+-p)[ \t]*(?:$|\|(?!\|)|>|;|&&)
    | \b(?:Get-ChildItem|gci|ls|dir|Get-Item|gi)\s+(?:-Path\s+)?env:[\\/]?\*?[ \t]*(?:$|[|;)])
    """, re.VERBOSE | re.IGNORECASE | re.MULTILINE)
NAMES_ONLY = re.compile(r"""
      cut\s+-d\s*['"]?=['"]?\s+-f\s*1\b
    | awk\s+-F\s*['"]?=['"]?\s+['"]\{\s*print\s+\$1\s*\}
    | \)\.(?:Name|Key)s?\b
    | Select-Object\s+(?:-ExpandProperty\s+)?(?:Name|Key)\b
    | \{\s*\$_\.(?:Name|Key)\s*\}
    | sed\s+(?:-E\s+)?['"]s[/|]=\.\*                       # value masked: s/=.*/=<set>/
    | \b(?:sorted|list)\(\s*os\.environ\s*\)
    | os\.environ\.keys\(\)
    """, re.VERBOSE | re.IGNORECASE)
# Narrowed before birth (backtest 2026-10-03, 78,635 recorded calls): bare
# `secret` / `credential` matched tool and file NAMES (secret_file_guard,
# dpapi-secret-store) in code greps, and bare words like `settings` matched
# prose. A key needs its compound form; a target needs a config extension.
CRED_KEY = re.compile(r"(?i)pass(?:word|wd)|api[_.-]?key|(?:client|secret)[_.-]?(?:secret|key)\b"
                      r"|(?:access|auth|bot|refresh)[_.-]?token")
CONFIG_SHAPED = re.compile(
    r"(?i)[\w*-]\.(?:prefs|ini|conf|cfg|config|properties|ya?ml|toml|json|xml|plist|npmrc|netrc|pgpass)\b")
SEARCH_VERB = re.compile(r"(?i)(?:^|[\s;&|(])(?:grep|egrep|fgrep|rg|ag|findstr|Select-String|sls)\b")
COUNT_ONLY = re.compile(
    r"(?:^|\s)-[a-zA-Z]*[lLcq][a-zA-Z]*(?=\s|$)|--(?:files-with-matches|files-without-match|count|quiet)\b"
    r"|\s-List\b|\.Count\b|Measure-Object")

ENV_PATH = (
    "List variable NAMES instead — PowerShell `(Get-ChildItem env:).Name`, "
    "Bash `env | cut -d= -f1`, Python `sorted(os.environ)` — or read one named "
    "variable that is not a credential. To check that a credential is set, print "
    "its length, never its value."
)
GREP_PATH = (
    "Ask for presence or count instead: add -l (which files match) or -c (how "
    "many lines), or mask the value before it prints, e.g. "
    "`... | sed -E 's/([=:]).*/\\1 <masked>/'`. Reading the value is the "
    "user's step, not the agent's."
)


def env_dump(text: str) -> str | None:
    m = ENV_DUMP.search(text)
    if not m or NAMES_ONLY.search(text):
        return None
    return m.group(0).strip(" ;&|()")


# Masking route (2026-10-04, misfire P2-1): GREP_PATH's third rewrite, a sed
# that masks the value AFTER the search in the same pipeline. Tighter than
# NAMES_ONLY's sed branch, which env_dump still uses unchanged: the stage is
# exactly one substitution whose pattern runs from the `=`/`:` separator to the
# end of the line, whose replacement holds no `&` and no backreference beyond
# \1 (the separator), with no file operand, no -n/-e/p, nothing after it.
MASK_SED = re.compile(r"""sed(?:\s+-[Er])?\s+(?P<q>['"])s(?P<d>[/|#])
    (?:\(\[[=:]{1,2}\]\)|\[[=:]{1,2}\]|=|:)(?:\\s\*|[ ]\*)?\.\*\$?(?P=d)
    (?:(?!(?P=d))[^'"\n&\\]|\\1)*(?P=d)g?(?P=q)\s*$""", re.VERBOSE)
STREAM_STAGE = re.compile(r"(?:head|tail|sort|uniq|wc|cut|tr|nl|[ef]?grep)(?![\w-])"
                          r"(?:[^|;&()<>`$\n]|\d?>\s*/dev/null|2>&1)*$")


def _split_shell(text: str) -> list[list[str]]:
    """Statements (on ; && || newline) of pipeline stages (on |), quote-aware."""
    stmts, stages, cur, q, i = [], [], "", None, 0
    while i < len(text):
        c = text[i]
        if q:
            q = None if c == q else q
        elif c in "'\"":
            q = c
        elif text.startswith(("&&", "||"), i) or c in ";\n":
            stages.append(cur); stmts.append(stages); stages, cur = [], ""
            i += 2 if c in "&|" else 1
            continue
        elif c == "|":
            stages.append(cur); cur = ""
            i += 1
            continue
        cur += c
        i += 1
    stages.append(cur); stmts.append(stages)
    return [[s.strip() for s in st] for st in stmts]


def _masked(stages: list[str]) -> bool:
    """The search stage's output reaches the transcript only through MASK_SED."""
    first = next(i for i, s in enumerate(stages) if SEARCH_VERB.search(" " + s))
    tail = stages[first + 1:]
    if re.search(r"[>`]|\$\(|\btee\b", re.sub(r"\d?>\s*/dev/null|2>&1", "", stages[first])):
        return False
    j = next((k for k, s in enumerate(tail) if MASK_SED.match(s)), None)
    return j is not None and all(STREAM_STAGE.match(s) for k, s in enumerate(tail) if k != j)


def cred_grep_command(text: str) -> str | None:
    if not (SEARCH_VERB.search(text) and CRED_KEY.search(text)):
        return None
    m = CONFIG_SHAPED.search(text)
    if not m or COUNT_ONLY.search(text):
        return None
    searching = [st for st in _split_shell(text) if any(SEARCH_VERB.search(" " + s) for s in st)]
    if searching and all(_masked(st) for st in searching):
        return None
    return m.group(0)


def hit(text: str) -> str | None:
    if not text:
        return None
    scanned = MESSAGE_BODY.sub(" ", text)
    if METADATA_ONLY_GIT.search(scanned):
        return None
    m = SECRET_TOKEN.search(scanned)
    return m.group(1) if m else None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)      # undetermined: parses, but is not a payload object (AP-62)

    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        sys.exit(0)

    if tool in ("Read", "Grep", "Glob"):
        # Glob returns names only, never content — listing a directory that
        # happens to contain a .env leaks nothing. Only Read/Grep can print it.
        if tool == "Glob":
            sys.exit(0)
        target = tool_input.get("file_path") or tool_input.get("path") or ""
        name = hit(" " + str(target))
        if name:
            deny(f"{tool} denied by secret_file_guard, a local PreToolUse hook "
                 f"(not file or page content). The target {name} matches the "
                 f"credential-name pattern this guard gates, and {tool} would "
                 f"put its contents in context. {COMPLIANT_PATH}"
                 + _receipt("secret_file_guard", tool=tool, matched=name)
                 + _fp("secret_file_guard"))
        if tool == "Grep" and tool_input.get("output_mode") == "content":
            where = " ".join(str(tool_input.get(k) or "") for k in ("path", "glob", "type"))
            if CRED_KEY.search(str(tool_input.get("pattern") or "")):
                m = CONFIG_SHAPED.search(where)
                if m:
                    deny(f"Grep denied by secret_file_guard, a local PreToolUse "
                         f"hook (not file or page content). Its pattern names a "
                         f"credential key and its target matches the config-file "
                         f"shape {m.group(0)}, so content mode would print any "
                         f"stored value into the transcript, which is kept for "
                         f"years. Use output_mode files_with_matches or count "
                         f"instead. {GREP_PATH}"
                         + _receipt("secret_file_guard", tool=tool, matched="cred-grep")
                         + _fp("secret_file_guard"))
        sys.exit(0)

    if tool in ("Bash", "PowerShell"):
        command = str(tool_input.get("command") or "")
        if OVERRIDE in command:
            sys.exit(0)
        name = hit(" " + strip_name_patterns(command))
        if name:
            deny(f"Command denied by secret_file_guard, a local PreToolUse hook "
                 f"(not file or page content). It references {name}, which "
                 f"matches the credential-name pattern this guard gates. The "
                 f"connector boundary is one-way: the agent may RUN a program "
                 f"that holds a key and may never see the key itself. "
                 f"{COMPLIANT_PATH}"
                 + _receipt("secret_file_guard", tool=tool, matched=name)
                 + _fp("secret_file_guard"))
        scanned = MESSAGE_BODY.sub(" ", command)
        what = env_dump(scanned)
        if what:
            deny(f"Command denied by secret_file_guard, a local PreToolUse hook "
                 f"(not file or page content). The fragment `{what[:40]}` "
                 f"matches the whole-environment-dump pattern this guard gates: "
                 f"an environment carries live tokens, and printed ones would "
                 f"sit in the transcript, which is kept for years. {ENV_PATH}"
                 + _receipt("secret_file_guard", tool=tool, matched="env-dump")
                 + _fp("secret_file_guard"))
        shape = cred_grep_command(scanned)
        if shape:
            deny(f"Command denied by secret_file_guard, a local PreToolUse hook "
                 f"(not file or page content). It searches for a credential key "
                 f"in a file matching the config-file shape {shape} and would "
                 f"print the matching lines, values included, into the "
                 f"transcript, which is kept for years. {GREP_PATH}"
                 + _receipt("secret_file_guard", tool=tool, matched="cred-grep")
                 + _fp("secret_file_guard"))
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
