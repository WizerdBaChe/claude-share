r"""PreToolUse guard: the Bash tool's SILENT transport defects (two in the

STATUS: LIVE since 2026-08-18 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).
tool's transport, L-024; one in the MSYS runtime underneath it, L-029).

(Raw docstring on purpose: this text quotes backslash runs as examples, and a
normal docstring turns `\|` into an invalid-escape SyntaxWarning — which is the
same class of defect the guard exists to talk about.)

Scope: the Bash tool only. The PowerShell tool and the Write tool were probed
against both defects on 2026-08-18 and have neither, so they fall straight
through. Measurement, probes and the retraction of a third suspected defect:
a dated shell-command error-audit report; rule: `ops/lessons.md`
L-024; global CLAUDE.md Environment bullets 1-2.

WHY A HOOK AND NOT A CLAUDE.md LINE (L-011). Both defects fail SILENTLY - the
command reports success while the bytes that reached disk are wrong. A rule
that says "remember not to do X" is only as good as recall at the moment of
writing, and the whole point of the routing rule is that the decision is
available BEFORE a character is typed. These two conditions are decidable from
the command string alone, with no judgment:

  (1) BACKSLASH COLLAPSE. A run of n consecutive backslashes arrives as
      ceil(n/2) - 1,2,3,4 become 1,1,2,2 - in every quoting context, while a
      backslash before a non-backslash passes untouched. Escaping harder cannot
      fix it: the layers needed depend on the quoting stack.
  (2) SIZE CEILING. Largest successful Bash command in 4,913 real calls:
      7,688 B. All 7 calls at or above 7,700 B failed - the command is
      truncated at the OS boundary, a heredoc delimiter is lost with it, and
      bash reports `unexpected EOF` pointing at an arbitrary line of the body.
  (3) MSYS PATH CONVERSION (L-029, 2026-08-23). The Bash tool is Git Bash /
      MSYS2, and MSYS rewrites argv for every native Windows exe: an argument
      that looks like a POSIX absolute path is converted - `/c` -> `C:/`,
      `/PID` -> `C:/Program Files/Git/PID`. A Windows switch is
      indistinguishable from a path at that layer, so `cmd /c ...` hands cmd
      `C:/` (an interactive shell that hangs on piped stdin or exits 0 having
      run nothing) and `taskkill /PID` errors. Quoting cannot help; the
      PowerShell tool (no MSYS layer), `MSYS_NO_PATHCONV=1`, or a doubled
      slash (`//c`) do. ANNOTATE-only: the pattern is determinable (known
      native exe at command position + a `/letter` token) but a veto needs a
      corpus backtest first, as (1) taught.

  (4) UNQUOTED WINDOWS DRIVE PATH (added 2026-09-20). Outside quotes bash
      treats every backslash as an escape and removes it, so
      `find D:\<dir> -name x` hands find the argument `D:<dir>`. With stderr
      discarded the result is a clean EMPTY output, which a session then
      reports as "not found" — the 2026-09-20 incident: five such searches in
      one session, each read as a true negative. CLAUDE.md carried this trap as
      "not hooked, so remember it" and recall did not hold. DENY when the
      quoting is resolvable, NOTICE when it is not (unbalanced quote,
      unterminated heredoc, backtick substitution) — see UNQUOTED PATH below.

GATE AUTHORITY (global CLAUDE.md) - and the backtest that corrected this
hook's first design. A gate may only rule on what it can DETERMINE; for
anything else the correct output is downgrade-and-forward, never veto.

  The size ceiling IS determinable: over 5,113 real Bash calls the rule fires
  7 times and all 7 already failed. Zero false positives by construction, so
  it is an unconditional DENY.

  The backslash collapse is NOT. The first version of this hook denied a
  halving that reached a durable sink. Backtesting it against the same 5,113
  calls flagged 112, of which 89 had SUCCEEDED - and sampling those showed a
  large share were the author already COMPENSATING for the collapse (writing
  four backslashes to land two; `\\|` in a markdown table to land `\|`;
  `[\\/]` in a JS regex to land `[\/]`). A naive escape and a deliberate
  compensation are byte-identical in the command string, so no amount of
  pattern work separates them - the gate cannot determine intent. It therefore
  ANNOTATES every halving and blocks none. The annotation still does the work
  the rule needs: it states exactly how many backslashes will be delivered, at
  the moment the command is issued, so a wrong assumption surfaces in the same
  turn instead of in a corrupted file three days later.

That asymmetry is the point. A gate that vetoed both would have been right
about 23 commands and wrong about 89, and a control wrong three times out of
four gets routed around rather than obeyed.

UNQUOTED PATH — why this one may veto when backslash-collapse may not. What
bash does to an unquoted backslash is deterministic; there is no "author was
compensating" reading of `D:\x` outside quotes. The only thing the gate can get
wrong is its own reading of the quoting, so the scanner reports whether it
resolved it, and an unresolved command is forwarded with a notice instead.
Backtest 2026-09-20 over 53,458 recorded Bash calls (1,493 transcripts, main +
subagent; script and result kept in
a retrieval-linkage audit's guard-backtest folder): 29 flagged, 0 unresolved;
20 failed loudly, 5 returned a silent empty result, 4 produced output with the
path mangled (2 of those were deliberate probes of this very trap — the
`[transport-checked]` marker is their exit). 0 of 29 were scanner misreads: the
first draft misread `"x $(wc -l < "D:\a")"` as unquoted, which is why `$(`
pushes a fresh quoting frame. Deliberately NOT gated: a double-quoted path
ending in a backslash (`ls "C:\dir\"`, 92 in the same corpus) — 83 of 92
already fail loudly with `unexpected EOF`, and a regex for it misfired on
doubled-backslash literals, so it has no veto-grade predicate yet. Known blind
spot: `D:\\x` unquoted (rule 1 already annotates every doubled run).

EVIDENCE BEFORE THE VETO. A denied command may carry a multi-KB heredoc body
that exists nowhere else. Everything this hook rejects is appended to
`telemetry/shell-transport-guard.jsonl` BEFORE the denial is emitted, so the
content is recoverable and so a false-positive rate can later be computed from
the same records that produced it.

Per-instance escape hatch: the literal marker [transport-checked] in the
command, for the case where the author has verified the transform is what they
want (e.g. deliberately writing four backslashes to land two).

Fail-open by design: any parse error exits 0 so a guard bug never blocks work.

SINK MEMBERSHIP IS THE REDIRECT, NOT AN EXTENSION LIST (repaired 2026-09-09).
`CONTENT_SINKS` used to decide "does this land durably" by matching the target's
EXTENSION against an enumeration, and that enumeration omitted .rb/.go/.rs/.java
/.lua. So `printf … > gen.rb` matched nothing and fell through to the other
notice, which asserted "Nothing here writes the result to a file or executes it
as source, so any damage shows up in this turn's own output" — false, and
worse than silence, because it told the reader the damage was visible when it
was not. The repair is not a longer list: an enumeration always loses to the
first member nobody wrote down (L-044), and the else-branch would have gone on
asserting the same thing about the next unlisted extension. `REDIRECT_ANY`
makes the REDIRECT the predicate, closed over every extension; the list now
only decides how specifically the sink can be NAMED. The fall-through notice
states what it checked instead of a universal negative, because a program
invoked here can still write the bytes itself and this guard cannot see that.

Proof-of-life: `python tools/shell-transport-test/test_shell_transport_guard.py`
(57/57 as of 2026-09-20, rule 4 added P1–P16; the allow+notice half is 48 of
the 57, so it is two-sided. Rule 4 verified in both directions: against the
pre-change hook P1–P3 and P13–P16 FAIL. Was 41/41 on 2026-09-09). A7–A15 pin the branch, not just the decision — both notices are
`notice`, so a case asserting only the decision could not fail on this defect
(L-062). Verified in both directions before shipping: against the pre-repair
hook A7–A10 and A15 FAIL, and against a deliberately over-broad REDIRECT_ANY
(`re.compile(r">")`) A11–A13 FAIL while A7–A10 stay green.
"""
import json
import os
import re
import sys
import time

try:                        # receipt + misfire exit (rules/hook-deny-message.md)
    from deny_receipt import clause as _receipt, fp_clause as _fp, notice_clause
except Exception:           # a guard must not stop guarding if telemetry breaks
    def _receipt(hook, **fields): return ""
    def _fp(hook): return ""
    def notice_clause(hook, log=""): return ""

MARKER = "[transport-checked]"

# 7,688 B succeeded; 7,700 B and above did not (7/7). Sit on the measured edge
# rather than a round number, and register the provenance in rule-registry.
SIZE_LIMIT = 7700

BACKSLASH_RUN = re.compile(r"\\{2,}")

# Shapes where the halved bytes become durable: a file on disk, or source text
# executed by an interpreter. Anything else (grep, ls, git, echo) is inspection
# whose damage is visible in the same turn.
#
# ORDER MATTERS: the first match wins and supplies the LABEL, so the specific
# shapes come before REDIRECT_ANY, which is the catch-all that makes the set
# closed over redirects instead of over a list of extensions.
#
# 2026-09-09, the extension list stopped being the membership test. It used to
# BE the test, and it omitted .rb/.go/.rs/.java/.lua — so `printf … > gen.rb`
# matched no sink, and the fall-through notice then asserted "Nothing here
# writes the result to a file", which was false. Lengthening the list is the
# wrong repair (L-044: the object vocabulary must cover every class the rule
# names, and an enumeration always loses to the first member nobody listed).
# A redirect writes a file whatever the extension is, so the redirect ITSELF is
# now the predicate and the list only decides how specifically we can name it.
SOURCE_EXT = (r"md|py|ts|tsx|js|jsx|mjs|cjs|cs|json|jsonl|txt|html|css|scss|ps1|sh|bash|zsh|bat|cmd|"
              r"toml|yml|yaml|xml|csproj|sql|ini|cfg|conf|rb|go|rs|java|lua|kt|kts|swift|c|h|cc|cpp|"
              r"hpp|php|pl|pm|r|jl|dart|ex|exs|vue|svelte|tf|gradle|properties|dockerfile|mk|make")
# Any `>` / `>>` whose target is a path rather than a file-descriptor dup.
# Excluded: `>&`/`2>&1` (dup, not a file), `/dev/null` (not durable), and the
# `=>` / `->` / `-->` arrows that appear inside quoted prose and code fragments.
REDIRECT_ANY = re.compile(r"(?<![=<>&|-])>>?\s*(?!&)['\"]?(?!/dev/null\b)[^\s'\"|;&<>]+")
CONTENT_SINKS = (
    (re.compile(r"<<\s*['\"]?\w+"), "heredoc body"),
    (re.compile(r"(^|[;&|]\s*)(cat|tee)\s[^|;]*>>?"), "cat/tee redirect to a file"),
    (re.compile(r">>?\s*['\"]?[^\s'\"|;&]+\.(" + SOURCE_EXT + r")\b", re.I),
     "redirect to a source/config file"),
    (re.compile(r"\b(python3?|node|perl|ruby|sh|bash)\s+(-\w+\s+)*-(\s|$)"), "script piped to an interpreter"),
    (re.compile(r"\b(python3?\s+-c|node\s+-e|perl\s+-e|ruby\s+-e)\b"), "inline -c/-e source"),
    (re.compile(r"\bsed\s+-i\b"), "sed -i in-place edit"),
    (REDIRECT_ANY, "redirect to a file (extension not recognised)"),
)

# (3) L-029: a known Windows-native exe at COMMAND position (start, or after
# ; & | ( `) followed somewhere in its own argument list by a `/letter` token.
# `//c` does not match (the char before the second slash is a slash, not
# whitespace) - that is MSYS's own escape. Command position only: a bare `reg`
# or `net` in the middle of a grep/echo line is not an exe invocation.
WIN_NATIVE_EXE = (r"(?:cmd|taskkill|tasklist|reg|sc|net|netsh|schtasks|findstr|"
                  r"wmic|icacls|robocopy|xcopy|attrib|certutil|msiexec|where|sfc|dism)")
WIN_FLAG_CONVERSION = re.compile(
    r"(?:^|[;&|(`]\s*)(" + WIN_NATIVE_EXE + r")(?:\.exe)?"
    r"((?:\s+[^\s;&|]+)*?)\s+/([A-Za-z?]+)\b",
    re.I,
)

# (4) Unquoted Windows drive path. The scanner answers two questions: which
# drive-path tokens sit OUTSIDE quotes, and whether it could resolve the quoting
# at all. Only the first answer may veto; an unresolved command is forwarded.
_HEREDOC_OPEN = re.compile(r"<<(-?)\s*(?:'(\w+)'|\"(\w+)\"|\\?(\w+))")
_PATH_TOKEN_END = re.compile(r"[\s;&|<>()\"'`]")


def _skip_heredocs(cmd, i, pending):
    """`i` sits just after a newline; consume each pending heredoc body."""
    for strip_tabs, delim in pending:
        while True:
            if i >= len(cmd):
                return i, False
            j = cmd.find("\n", i)
            line = cmd[i:] if j < 0 else cmd[i:j]
            probe = line.lstrip("\t") if strip_tabs else line
            i = len(cmd) if j < 0 else j + 1
            if probe.rstrip("\r") == delim:
                break
            if j < 0:
                return i, False
    return i, True


def unquoted_drive_paths(cmd):
    """Return (hits, resolvable): drive-path tokens outside quotes, as written."""
    hits, pending = [], []
    i, n = 0, len(cmd)
    # One frame per quoting context. `$(` pushes a fresh frame even from inside
    # double quotes, because bash restarts quoting there:
    # "x $(wc -l < "D:\a") y" keeps D:\a QUOTED (the first draft misread this).
    stack = [["n", 0]]
    fuzzy = False
    while i < n:
        c = cmd[i]
        frame = stack[-1]
        state = frame[0]
        if state in ("n", "dq") and c == "$" and cmd[i + 1:i + 2] == "(":
            stack.append(["n", 0])
            i += 2
            continue
        if state in ("n", "dq") and c == "`":
            fuzzy = True          # backtick substitution: quoting not modelled
        if state == "n":
            if c == "\\":
                i += 2
                continue
            if c == "(":
                frame[1] += 1
            elif c == ")":
                if frame[1] == 0 and len(stack) > 1:
                    stack.pop()
                else:
                    frame[1] = max(0, frame[1] - 1)
            elif c == "'":
                frame[0] = "sq"
            elif c == '"':
                frame[0] = "dq"
            elif c == "$" and cmd[i + 1:i + 2] == "'":
                frame[0] = "ansi"
                i += 1
            elif c == "#" and (i == 0 or cmd[i - 1] in " \t\n;"):
                j = cmd.find("\n", i)
                i = n if j < 0 else j
                continue
            elif c == "<" and cmd[i:i + 2] == "<<" and cmd[i:i + 3] != "<<<":
                m = _HEREDOC_OPEN.match(cmd, i)
                if m:
                    pending.append((bool(m.group(1)),
                                    m.group(2) or m.group(3) or m.group(4)))
                    i = m.end()
                    continue
            elif c == "\n" and pending:
                i, ok = _skip_heredocs(cmd, i + 1, pending)
                pending = []
                if not ok:
                    return hits, False
                continue
            elif (c.isalpha() and cmd[i + 1:i + 3] == ":\\" and i + 3 < n
                  and cmd[i + 3] not in "\\ \t\r\n\"'"
                  and (i == 0 or not (cmd[i - 1].isalnum() or cmd[i - 1] in "_\\/.-"))):
                m = _PATH_TOKEN_END.search(cmd, i)
                end = m.start() if m else n
                hits.append(cmd[i:end])
                i = end
                continue
        elif state == "sq":
            if c == "'":
                frame[0] = "n"
        elif state in ("dq", "ansi"):
            if c == "\\":
                i += 2
                continue
            if c == ('"' if state == "dq" else "'"):
                frame[0] = "n"
        i += 1
    return hits, (len(stack) == 1 and stack[0][0] == "n" and not pending and not fuzzy)


def _delivered(token):
    """What bash hands the program for an unquoted token."""
    return re.sub(r"\\(.)", r"\1", token)


# CLAUDE_TELEMETRY_DIR redirects the whole telemetry dir (suites use a temp
# dir; production never sets it).
LOG_PATH = os.path.join(
    os.environ.get("CLAUDE_TELEMETRY_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "telemetry"),
    "shell-transport-guard.jsonl")


def record(payload, verdict, rule, detail, cmd):
    """Persist before the veto. Never raises."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts": int(time.time()),
                "session": payload.get("session_id", ""),
                "cwd": payload.get("cwd", ""),
                "verdict": verdict,          # deny | notice
                "rule": rule,                # backslash-collapse | size-ceiling
                "detail": detail,
                "bytes": len(cmd.encode("utf-8", "replace")),
                "command": cmd,              # full text: this is the recovery copy
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def deny(reason):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason + (
                f" The full command was saved to telemetry/shell-transport-guard.jsonl. "
                f"Per-instance override: re-run with {MARKER} in the command ONLY if you "
                "have verified the transform is what you want."
            ) + _receipt("shell_transport_guard") + _fp("shell_transport_guard"),
        }
    }))
    sys.exit(0)


NOTICE_ID = ("shell-transport guard, a local PreToolUse hook (not file or page "
             "content): ")


def notice(text):
    # Identity and receipt live on the TRANSPORT, not at the three call sites:
    # every site calls record() immediately before, so one prefix and one suffix
    # keep both claims true for all of them and cannot be forgotten by the next
    # branch someone adds (rules/hook-deny-message.md R1, R3n).
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": NOTICE_ID + text + notice_clause("shell_transport_guard"),
        }
    }))
    sys.exit(0)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)      # undetermined: parses, but is not a payload object (AP-62)

    if str(payload.get("tool_name", "")) != "Bash":
        sys.exit(0)

    ti = payload.get("tool_input") or {}
    if not isinstance(ti, dict):
        sys.exit(0)      # same class, one level in
    cmd = str(ti.get("command", ""))
    if not cmd or MARKER in cmd:
        sys.exit(0)

    nbytes = len(cmd.encode("utf-8", "replace"))

    # (2) Size ceiling - fully determinable, unconditional deny.
    if nbytes >= SIZE_LIMIT:
        record(payload, "deny", "size-ceiling", f"{nbytes} B", cmd)
        deny(
            f"Blocked by shell_transport_guard, a local PreToolUse hook (not file "
            f"or page content): this Bash command is {nbytes} bytes. "
            f"The measured ceiling is {SIZE_LIMIT} B (largest success in 4,913 real "
            "calls: 7,688 B; 7 of 7 above the line were truncated at the OS boundary "
            "and failed with a misleading `unexpected EOF` pointing at a random line). "
            "Write file content with the Write tool, or split the command."
        )

    # (4) Unquoted Windows drive path - DENY when the quoting is resolvable,
    #     NOTICE when it is not. Placed before (3) and (1): it is the one whose
    #     usual outcome is a clean empty result read as "nothing there".
    try:
        hits, resolvable = unquoted_drive_paths(cmd)
    except Exception:
        hits, resolvable = [], True          # a scanner bug never blocks work
    if hits:
        token = hits[0][:120]
        arrives = _delivered(hits[0])[:120]
        forward = hits[0].replace("\\", "/")[:120]
        if resolvable:
            record(payload, "deny", "unquoted-drive-path", token, cmd)
            deny(
                "Blocked by shell_transport_guard, a local PreToolUse hook (not file "
                "or page content): this Bash command carries a token matching the "
                f"unquoted-drive-path pattern this guard gates: `{token}`. Outside "
                "quotes Git Bash removes every backslash, so the program would receive "
                f"`{arrives}` — it then fails, or with stderr discarded returns a clean "
                "empty result that is indistinguishable from a true negative. Wrap the "
                f"path in double quotes, or write it with forward slashes (`{forward}`), "
                "or run the command with the PowerShell tool."
            )
        record(payload, "notice", "unquoted-drive-path", "quoting-unresolved: " + token, cmd)
        notice(
            f"this command carries `{token}`, and this guard could not resolve the "
            "command's quoting (an unbalanced quote, an unterminated heredoc, or a "
            "backtick substitution), so it cannot tell whether that path sits outside "
            "quotes. If it does, Git Bash removes its backslashes and the program "
            f"receives `{arrives}`; an empty result from this command is then not "
            "evidence of absence. If the path is inside quotes, nothing needs doing; "
            "otherwise quote it or use forward slashes before trusting the output."
        )

    # (3) MSYS path conversion of a Windows-native /flag - ANNOTATE (L-029).
    #     Placed before (1) because this failure is the silent one.
    if "MSYS_NO_PATHCONV" not in cmd:
        m3 = WIN_FLAG_CONVERSION.search(cmd)
        if m3:
            exe, flag = m3.group(1), m3.group(3)
            record(payload, "notice", "msys-path-conversion", f"{exe} /{flag}", cmd)
            notice(
                f"`{exe} ... /{flag}` — the Bash tool is Git "
                "Bash/MSYS2, which rewrites arguments that look like POSIX paths before "
                "a Windows-native exe sees them: `/c` -> `C:/`, `/PID` -> `C:/Program "
                "Files/Git/PID`. `cmd` then waits on `C:/` (silent hang, or exits 0 "
                "having run nothing); taskkill/reg/findstr error. Run Windows-native "
                "`/flag` commands through the PowerShell tool, or prefix "
                "`MSYS_NO_PATHCONV=1`, or double the slash (`//c`)."
            )

    # (1) Backslash collapse - ANNOTATE, never veto (see the module docstring:
    #     compensation and naive escaping are byte-identical here).
    m = BACKSLASH_RUN.search(cmd)
    if m:
        run = len(m.group(0))
        delivered = -(-run // 2)
        sink = next((label for pat, label in CONTENT_SINKS if pat.search(cmd)), None)
        if sink:
            record(payload, "notice", "backslash-collapse", sink, cmd)
            notice(
                f"a run of {run} backslashes will be delivered "
                f"as {delivered} — and this command reaches a {sink}, so whatever "
                "arrives lands durably while the command still reports success. If "
                f"{delivered} is what you intended, carry on; if you meant {run}, "
                "nothing you can write here will deliver them (the layers needed "
                "depend on the quoting stack). Use the Write tool for file content or "
                "the PowerShell tool — both probed clean — or single backslashes, "
                "forward slashes, or a Python raw string. Either way, read the written "
                "bytes back before believing the exit code."
            )
        # No sink matched. That is a statement about what this guard RECOGNISES,
        # not about what the command does, and the difference is the whole point
        # of the 2026-09-09 repair: the previous text asserted "Nothing here
        # writes the result to a file or executes it as source", which for
        # `printf … > gen.rb` was simply false — the extension list was the
        # membership test and .rb was not on it. REDIRECT_ANY closes the redirect
        # class, so this branch is now a much stronger negative; it is still not
        # a universal one (a program invoked here can write files of its own),
        # so it says what it checked and stops there. An instrument may only
        # rule on what it can determine (AP-62).
        record(payload, "notice", "backslash-collapse", "no-sink-recognised", cmd)
        notice(
            f"a run of {run} backslashes will be delivered as "
            f"{delivered}. No redirect, heredoc, in-place edit or inline-source shape "
            "matched here, so this guard has no evidence the halved bytes land "
            "anywhere durable — but that is the limit of what it checks, not a "
            "guarantee: a program invoked here can still write them itself. If the "
            "result looks wrong, the collapse is why; if this command hands text to "
            "something that stores it, read the stored bytes back."
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
