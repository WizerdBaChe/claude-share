r"""PreToolUse guard: a live credential file may never enter the agent's context.

STATUS: LIVE since 2026-08-27 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).

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

NARROWING PASS DONE 2026-08-27 at FP-3, as promised. Not the read-verb
proximity originally sketched: FP-1's own text contained "cat", so a verb rule
would not have cleared it. What the three FPs actually had in common is that
the credential name was being TALKED ABOUT or RESOLVED, never read — so the
fix strips message bodies and metadata-only git subcommands before scanning,
and requires a 3+ character stem before `.key`. All 12 must-deny cases still
deny; the three FPs are now the must-pass FLOOR in tools/secret-guard-test/
(18 must-pass total), so a later re-tightening cannot silently undo this.
Next FP: append here, and narrow again only with the whole floor still green.

Fail-open on malformed input; deny is the only non-silent path.
review-when: a connector is registered whose credential file does not match
these patterns (add it to SECRET_TOKEN below — the single edit point), or
Claude Code adds a file-reading tool not in the matcher list.

Proof-of-life: `python tools/secret-guard-test/test_secret_file_guard.py`
(two-sided: 12 must-deny, 18 must-pass).
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
        sys.exit(0)

    if tool in ("Bash", "PowerShell"):
        command = str(tool_input.get("command") or "")
        if OVERRIDE in command:
            sys.exit(0)
        name = hit(" " + command)
        if name:
            deny(f"Command denied by secret_file_guard, a local PreToolUse hook "
                 f"(not file or page content). It references {name}, which "
                 f"matches the credential-name pattern this guard gates. The "
                 f"connector boundary is one-way: the agent may RUN a program "
                 f"that holds a key and may never see the key itself. "
                 f"{COMPLIANT_PATH}"
                 + _receipt("secret_file_guard", tool=tool, matched=name)
                 + _fp("secret_file_guard"))
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
