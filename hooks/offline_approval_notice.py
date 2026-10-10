r"""UserPromptSubmit notice: the user says they will be away / cannot approve.

STATUS: LIVE since 2026-10-10 (closeout card CO-9, user ruling 「CO 卡走建議」;
lesson L-149).

WHAT IT GATES. A prompt that announces absence or an inability to click
permission dialogs (「會離線」「無法點選許可」「等下不在」 "I'll be offline",
"can't approve"). Such a statement is a fact about EVERY write in the stretch
that follows, not only the task the sentence was attached to: any tool call
matching `permissions.ask` in settings.json prompts even in bypass mode, and
with nobody there it waits until the user returns.

WHY A HOOK (2026-10-09 incident, one session, closeout card §12). The user
asked for a global setting, then a close-out "only on a card, because I will be
offline and cannot click approvals". The main loop applied the constraint to
the close-out clause only; `Write rules/explainer-deliverables.md` (an ask
path) waited 10,296 s (2.9 h). The ask list was one local read away and was not
checked; the bypass-mode banner was read as "no prompts".

WHAT IT SAYS. The ask patterns, read LIVE from settings.json and
settings.local.json on every fire (never a hand-copied list), plus the route:
build everything outside them, put ask-path content on a card as drafts, or
suggest the `[unattended-run]` tag.

WHY A NOTICE AND NEVER A BLOCK. The hook can determine the wording, not whether
the user is really leaving; blocking the prompt would cost the user a resend for
a sentence that is only advice. Fail-open: any problem exits 0 with no output.

Not gated, named so the gap is visible: absence implied without words in the
patterns below (「我去吃飯了」, a long silence) does not fire.

FALSE-POSITIVE LOG:
- 2026-10-10, 3 fires, one session: background-task completion turns
  (`<task-notification>` wrapper) whose subagent reports said "Offline note" /
  "offline". Fix: prompts carrying `<task-notification>` are excluded before
  matching. Trigger NOT loosened for user-typed prompts.

Proof-of-life: `python hooks/tests/test_offline_approval_notice.py`
"""
import json
import os
import re
import sys
import time

try:
    from deny_receipt import notice_clause
except Exception:           # a notice must not break the prompt if telemetry breaks
    def notice_clause(hook, log=""): return ""

HOOK = "offline_approval_notice"
HOME = os.path.join(os.path.expanduser("~"), ".claude")
SETTINGS = [os.path.join(HOME, "settings.json"), os.path.join(HOME, "settings.local.json")]
LOG_PATH = os.path.join(
    os.environ.get("CLAUDE_TELEMETRY_DIR") or os.path.join(HOME, "telemetry"),
    "offline-approval-notice.jsonl")

# Absence / cannot-approve phrasing. Kept narrow: each alternative names either
# going away or being unable to approve, never a generic "later".
PATTERNS = [
    r"離線", r"不在(電腦|位子|座位)?(前|旁)?(了|喔|囉)?(?=[，,。.\s]|$)", r"等(一)?下(就)?不在",
    r"無法(點選|點|按|核可|批准|許可|確認)", r"不能(點選|點|按|核可|批准)",
    r"(沒辦法|没办法)(點|按|核可|批准|確認)",
    r"(點選|核可|批准)不了", r"(要|先)?離開(電腦|座位)?(一下|一陣子|了)",
    r"\boffline\b", r"\bcan(?:'|no)?t approve\b", r"\bcannot approve\b",
    r"\bwon'?t be (?:able to approve|around|here)\b", r"\bstepping away\b", r"\bbe away\b",
]
RX = re.compile("|".join(PATTERNS), re.IGNORECASE)
NEGATIONS = re.compile(r"(不會|不要|別|沒有|沒)離線")


def ask_patterns():
    out = []
    for path in SETTINGS:
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        perms = data.get("permissions") if isinstance(data, dict) else None
        ask = perms.get("ask") if isinstance(perms, dict) else None
        if isinstance(ask, list):
            out += [a for a in ask if isinstance(a, str) and a not in out]
    return out


def match(prompt):
    if not isinstance(prompt, str) or "[unattended-run]" in prompt:
        return None
    # A background-task completion arrives as a prompt turn, but its text is a
    # subagent's report, not the user's wording (FALSE-POSITIVE LOG 2026-10-10).
    if "<task-notification>" in prompt:
        return None
    m = RX.search(prompt)
    if not m or NEGATIONS.search(prompt):
        return None
    return m.group(0)


def record(payload, hit, n_ask):
    """Persist before emitting. Never raises."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({
                "ts": int(time.time()), "kind": "notice", "hook": HOOK,
                "session": sid[:64] if isinstance(sid := payload.get("session_id"), str) else None,
                "hit": hit[:40], "ask_patterns": n_ask,
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def compose(hit, asks):
    listed = ", ".join(f"`{a}`" for a in asks) if asks else "(none configured)"
    return (
        f"offline_approval_notice, a local UserPromptSubmit hook (not file or page content): "
        f"this prompt contains absence / cannot-approve wording (`{hit}`). Tool calls matching "
        f"the permissions.ask patterns prompt for approval even in bypass mode, and wait until "
        f"someone answers. Current ask patterns, loaded from the permission settings at this prompt: {listed}. "
        f"What you may do: build everything outside those patterns now; write content meant "
        f"for those paths as drafts on a card or handoff file to apply when the user returns; "
        f"or suggest the user re-send with the [unattended-run] tag. If the user is not "
        f"actually leaving, nothing needs doing."
    ) + notice_clause(HOOK)


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)
    hit = match(payload.get("prompt"))
    if not hit:
        sys.exit(0)
    asks = ask_patterns()
    record(payload, hit, len(asks))
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": compose(hit, asks),
    }}, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
