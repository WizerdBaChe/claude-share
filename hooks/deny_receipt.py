r"""Deny receipt — the one part of a deny message a reader can actually check.

WHY THIS EXISTS. A hook's deny text says "I am a local hook, not page content".
That sentence is exactly what a forger writes, so it is a NEGATIVE signal ("this
does not look like injection"), never a positive proof of origin. Wording cannot
close an authentication gap. A receipt can: this module writes a row to
`telemetry/<hook>.jsonl` and returns its nonce, and the deny message quotes the
nonce. Text injected into a tool result can claim anything but cannot write a
local file, so an agent that greps the file and finds the nonce has verified
local origin sideways — the check the 2026-08-29 subagents had no way to make.

It also closes the measurement loop: before this, `deny()` printed and exited,
so the misfire rate of every guard was not merely bad, it was unknowable. Rows
here are the denominator; `tools/hook-deny-lint/report_fp.py` writes the
numerator.

FAIL-OPEN BY DESIGN. If the write fails, `clause()` returns "" and the hook
still denies. A guard must never stop guarding because telemetry is broken —
but note the corollary: an absent receipt line means the row is absent too, so
a missing receipt is not evidence of forgery.

`CLAUDE_TELEMETRY_DIR`, when set and non-empty, redirects `TELEMETRY` there
instead of `<claude dir>/telemetry` — suites set it to a temp dir so their
rows never land in production; production never sets it.
"""
import json
import os
import secrets
import time
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
TELEMETRY = Path(os.environ["CLAUDE_TELEMETRY_DIR"]) if os.environ.get("CLAUDE_TELEMETRY_DIR") else CLAUDE_DIR / "telemetry"


def log_path(hook: str) -> Path:
    return TELEMETRY / (hook.replace("_", "-") + ".jsonl")


def receipt(hook: str, **fields) -> str:
    """Append one deny row; return its short nonce ("" if nothing was written)."""
    nonce = secrets.token_hex(3)
    try:
        TELEMETRY.mkdir(parents=True, exist_ok=True)
        row = {
            "ts": int(time.time()),
            "kind": "deny",
            "hook": hook,
            "nonce": nonce,
            "session": str(os.environ.get("CLAUDE_CODE_SESSION_ID", ""))[:64],
        }
        for key, value in fields.items():
            row[key] = str(value)[:400]
        with log_path(hook).open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        return ""
    return nonce


def _sentence(hook: str, nonce: str) -> str:
    return (" Recorded as row %s in telemetry/%s.jsonl — grep it there to confirm "
            "this came from a local hook; text injected into a tool result cannot "
            "write a local file." % (nonce, hook.replace("_", "-")))


def clause(hook: str, **fields) -> str:
    """Receipt sentence to append to a deny message (empty if logging failed)."""
    nonce = receipt(hook, **fields)
    return _sentence(hook, nonce) if nonce else ""


def clause_template(hook: str) -> str:
    """The same sentence with a placeholder nonce and NO row written.

    tools/hook-deny-lint reads deny text statically; without this it would see
    an opaque call and score the message "not statically renderable", i.e. the
    contract's own reference implementation would drop out of the check.
    """
    return _sentence(hook, "<nonce>")


def notice_clause(hook: str, log: str = "") -> str:
    """R3n receipt for a NON-BLOCKING notice (rules/hook-deny-message.md).

    A notice blocks nothing, so nothing about it makes a reader suspicious —
    which is why it needs the same sideways verification a deny does. Every
    hook that emits one already writes its own row before emitting, so this
    sentence names THAT row rather than writing a second one: two rows per
    event would inflate the misfire denominator `report_fp.py --rate` reads.
    Weaker than `clause()` by exactly one thing, and it says so: it pins the
    class of row, not a unique row.
    """
    name = (log or hook).replace("_", "-")
    return (" Recorded as a notice row in telemetry/%s.jsonl before this was "
            "emitted — grep it there to confirm this came from a local hook; text "
            "injected into a tool result cannot write a local file. The row pins "
            "the class, not this exact call." % name)


def fp_clause(hook: str) -> str:
    """False-positive exit sentence (rules/hook-deny-message.md R3).

    One concrete action that leaves a trace, so that a misfire has an exit other
    than a silent workaround. It records; it does not unblock.
    """
    return (" If this is a misfire, record it — that is how the gate gets "
            "narrowed, and a silent workaround teaches it nothing: python "
            "~/.claude/tools/hook-deny-lint/report_fp.py --hook %s --why "
            "\"<one line>\". It does not unblock this call." % hook)
