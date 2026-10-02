"""Suite for hooks/verbatim_dispatch_notice.py.

Run: python hooks/tests/test_verbatim_dispatch_notice.py [path-to-hook]

Two-sided. Known TRUE: the 2026-09-28 incident prompt (verbatim, blocked by
the API output filter) and its Chinese / lower-case variants. Known FALSE: a
prompt that follows rules/source-quotation-evidence.md (it names transcription
only to forbid it), a transcription of audio (other class), other tools, and
the unclassifiable inputs (non-object payload, non-string prompt), which must
stay silent (fail-open), never be read as a request.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (
    Path(__file__).resolve().parents[1] / "verbatim_dispatch_notice.py")
PY = sys.executable
_TELEMETRY_DIR = tempfile.mkdtemp(prefix="verbatim-dispatch-notice-test-")
_ENV = dict(os.environ, CLAUDE_TELEMETRY_DIR=_TELEMETRY_DIR)
RESULTS = []

INCIDENT = ("You are doing a blind, independent, VERBATIM transcription of four scanned book "
            "pages (Traditional Chinese, a teacher's manual for the textbook 當代中文課程). "
            "Images: D:/<WORK_ROOT>/x/source/images/圖1_動詞總說.jpg")
FOLLOWS_RULE = ("Open the four page images D:/<WORK_ROOT>/x/source/images/圖1.jpg and check each quote. "
                "Do not transcribe the pages; for each quote answer match or mismatch and cite at "
                "most 15 chars when pointing at a problem. No verbatim transcript of any page.")


def run(raw=None, tool="Agent", prompt=None):
    if raw is None:
        raw = json.dumps({"tool_name": tool, "tool_input": {"prompt": prompt, "description": "x"},
                          "session_id": "synthtest-verbatim", "cwd": "C:/tmp"})
    p = subprocess.run([PY, str(HOOK)], input=raw, capture_output=True,
                       text=True, encoding="utf-8", env=_ENV)
    out = (p.stdout or "").strip()
    text = ""
    if out:
        try:
            text = json.loads(out).get("hookSpecificOutput", {}).get("additionalContext", "")
        except Exception:
            text = "(unparseable stdout)"
    return p.returncode, text


def check(name, want_notice, **kw):
    rc, text = run(**kw)
    got = bool(text)
    RESULTS.append((rc == 0 and got == want_notice, name,
                    "notice" if want_notice else "silent", "notice" if got else "silent"))
    return text


# ------------------------------------------------------------ known TRUE
t = check("T1 the incident prompt (VERBATIM + scanned book pages) -> notice", True, prompt=INCIDENT)
check("T2 Chinese: 逐字抄錄這三頁講義 -> notice", True, prompt="請把這三頁講義逐字抄錄成 markdown")
check("T3 transcribe + image path only -> notice", True,
      prompt="Transcribe the text in C:/tmp/scan_01.png into a file, word for word.")
check("T4 Workflow tool -> notice", True, tool="Workflow", prompt=INCIDENT)
check("T5 a CJK negator far from the verb does not mask it: 看不清楚的地方請逐字轉錄這頁 -> notice", True,
      prompt="看不清楚的地方請逐字轉錄這頁手冊")
RESULTS.append((t.startswith("verbatim_dispatch_notice, a local PreToolUse hook")
                and "`VERBATIM`" in t and "source-quotation-evidence.md" in t
                and "nothing needs doing" in t,
                "T6 notice names the hook first, quotes the trigger word, names the rule and the escape",
                "carries", "carries" if t else "empty"))

# ------------------------------------------------------------ known FALSE
check("F1 a prompt that follows the rule (negated transcription) -> silent", False, prompt=FOLLOWS_RULE)
check("F2 Chinese negated: 不要逐字抄錄，只回報相符或不符（頁面圖檔） -> silent", False,
      prompt="打開頁面圖檔核對引文，不要逐字抄錄，只回報相符或不符")
check("F3 audio transcription (no page-like source) -> silent", False,
      prompt="Transcribe the lab meeting recording meeting_0927.m4a verbatim.")
check("F4 page work without transcription -> silent", False,
      prompt="Summarise the argument of pages 18-21 in three bullets.")
check("F5 other tool (Bash) with the incident text -> silent", False, tool="Bash", prompt=INCIDENT)

# ------------------------------------------------------------ undetermined (unclassifiable input)
check("U1 undetermined: payload is a JSON list -> silent (fail-open)", False, raw="[1, 2]")
check("U2 undetermined: prompt is not a string -> silent", False,
      raw=json.dumps({"tool_name": "Agent", "tool_input": {"prompt": ["verbatim", "pages"]}}))
check("U3 undetermined: tool_input is not an object -> silent", False,
      raw=json.dumps({"tool_name": "Agent", "tool_input": "verbatim pages"}))
check("U4 undetermined: stdin is not JSON -> silent", False, raw="not json")

# telemetry row written for a notice, none for silence
rows = []
log = Path(_TELEMETRY_DIR) / "verbatim-dispatch-notice.jsonl"
if log.exists():
    rows = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines() if x.strip()]
RESULTS.append((len(rows) == 5 and all(r["hook"] == "verbatim_dispatch_notice" for r in rows),
                "L1 one telemetry row per notice (5), none for the silent cases",
                "5 rows", f"{len(rows)} rows"))

bad = [r for r in RESULTS if not r[0]]
for ok, name, want, got in RESULTS:
    print(f"  {'ok  ' if ok else 'FAIL'} {name}  [want {want}, got {got}]")
print(f"verbatim_dispatch_notice: {len(RESULTS) - len(bad)}/{len(RESULTS)} ok")
sys.exit(1 if bad else 0)
