r"""PreToolUse notice: a dispatch prompt that asks for a verbatim transcription of pages/images.

STATUS: LIVE since 2026-09-28.
Enforces: `rules/source-quotation-evidence.md` (registry key
`verbatim_dispatch_notice`). Graduation/promotion trigger: see the registry row.

WHAT IT GATES. An Agent/Workflow dispatch whose prompt asks the worker to
transcribe a source page word for word. On 2026-09-28 (a deck-building
session) such a subagent — "You are doing a blind,
independent, VERBATIM transcription of four scanned book pages" — terminated on
`API Error: 400 Output blocked by content filtering policy`: the output filter
blocks reproduction of a copyrighted text at length. The dispatch cost the
worker's whole run and a user question ("is it the network?").

WHY A NOTICE AND NEVER A DENY. The hook can see the WORDS of the request, not
the rights status of the pages: the user's own notes, an open-licence text or a
form they own are legitimately transcribed. It forwards the fact and the route.

DECISION (both must hold, per prompt):
  T  a transcription verb not negated within the preceding 12 chars —
     verbatim / transcribe / transcription / word-for-word / 逐字 / 抄錄 /
     轉錄 / 謄寫 / 全文照打 / 照抄
  S  a page-like source — page(s) / scan(ned) / book / manual / textbook /
     handout / pdf / an image path (.jpg .jpeg .png .tif .webp .heic) /
     頁 / 書 / 手冊 / 課本 / 教材 / 講義 / 掃描 / 圖檔 / 照片
Negation words (English within 20 chars, CJK within 4): not, never, no, don't,
without, avoid, 不, 不要, 不得, 不可, 不必, 不用, 不需, 勿, 禁止, 別, 避免,
無需. A prompt that follows the rule ("do not
transcribe; quote at most 15 chars") therefore stays silent.

Not gated, named: audio/video transcription (a different class — a lab
meeting recording is the user's own); the main loop's own output (no hook sees
assistant text before it is sent).

Fail-open: any parse problem, a non-object payload or a non-string prompt exits
0 with no output (a notice must never break a dispatch).

Extending: a new trigger word joins T or S with a control in the suite that
would have fired only because of it; a negation word joins NEG with a silent-side
control.

Proof-of-life: `python hooks/tests/test_verbatim_dispatch_notice.py`
"""
import json
import os
import re
import sys
import time

try:
    from deny_receipt import notice_clause
except Exception:           # a notice must not break the call if telemetry breaks
    def notice_clause(hook, log=""): return ""

HOOK = "verbatim_dispatch_notice"
TOOLS = ("Agent", "Workflow", "Task")
LOG_PATH = os.path.join(
    os.environ.get("CLAUDE_TELEMETRY_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "telemetry"),
    "verbatim-dispatch-notice.jsonl")
NOTICE_ID = ("verbatim_dispatch_notice, a local PreToolUse hook (not file or page "
             "content): ")

T_RE = re.compile(r"verbatim|transcri(?:be|bes|bing|ption|pt)|word[- ]for[- ]word|"
                  r"逐字|抄錄|轉錄|謄寫|全文照打|照抄", re.I)
S_RE = re.compile(r"\bpages?\b|\bscan(?:ned|s)?\b|\bbooks?\b|\bmanuals?\b|\btextbooks?\b|"
                  r"\bhandouts?\b|\bpdfs?\b|\.(?:jpe?g|png|tiff?|webp|heic)\b|"
                  r"頁|書|手冊|課本|教材|講義|掃描|圖檔|照片", re.I)
# English negators reach over a short verb phrase ("do not produce a verbatim");
# CJK ones only over <= 4 chars, so 「看不清楚的地方請逐字」 is not read as negated.
NEG_EN = re.compile(r"(?:\bnot\b|\bnever\b|\bno\b|don'?t|\bwithout\b|\bavoid\b)[^.;\n]{0,20}$", re.I)
NEG_ZH = re.compile(r"(?:不要|不得|不可|不必|不用|不需|勿|禁止|別|避免|無需|不)[^。；;，,\n]{0,4}$")


def triggered(prompt: str):
    """Return the first un-negated transcription phrase, or None."""
    if not S_RE.search(prompt):
        return None
    for m in T_RE.finditer(prompt):
        before = prompt[max(0, m.start() - 32):m.start()]
        if not (NEG_EN.search(before) or NEG_ZH.search(before)):
            return m.group(0)
    return None


def record(payload, word):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({
                "ts": int(time.time()), "kind": "notice", "hook": HOOK,
                "session": sid[:64] if isinstance(sid := payload.get("session_id"), str) else None,
                "word": word,
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(payload, dict) or payload.get("tool_name") not in TOOLS:
        sys.exit(0)
    ti = payload.get("tool_input")
    if not isinstance(ti, dict):
        sys.exit(0)
    prompt = ti.get("prompt")
    if not isinstance(prompt, str):
        sys.exit(0)
    word = triggered(prompt)
    if not word:
        sys.exit(0)
    record(payload, word)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": NOTICE_ID + (
                f"this dispatch asks for a transcription of pages or images (`{word}`). "
                "If those pages are a copyrighted source (a book, manual, handout or "
                "paywalled PDF), the worker's output will be blocked by the API filter "
                "(`Output blocked by content filtering policy`) and the run is lost. The "
                "route in rules/source-quotation-evidence.md replaces it: the worker "
                "returns locators plus quotes of at most 15 chars, or match/mismatch "
                "verdicts, and presence is checked locally with "
                "`python tools/quote-evidence/qe.py`. If the pages are the user's own or "
                "open-licence text, nothing needs doing."
            ) + notice_clause(HOOK),
        }
    }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
