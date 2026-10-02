"""Suite for hooks/session_search_query_notice.py.

Run: python hooks/tests/test_session_search_query_notice.py [path-to-hook]

Two-sided: the known-FALSE half (single tokens, other tools, malformed input)
must stay silent, or the notice becomes noise on every search and gets read past.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (
    Path(__file__).resolve().parents[1] / "session_search_query_notice.py")
PY = sys.executable
_TELEMETRY_DIR = tempfile.mkdtemp(prefix="session-search-notice-test-")
_ENV = dict(os.environ, CLAUDE_TELEMETRY_DIR=_TELEMETRY_DIR)
TOOL = "mcp__ccd_session_mgmt__search_session_transcripts"
RESULTS = []


def run(raw=None, tool=TOOL, tool_input=None):
    if raw is None:
        raw = json.dumps({"tool_name": tool, "tool_input": tool_input,
                          "session_id": "synthtest-session-search", "cwd": "C:/tmp"})
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
t = check("T1 the incident query (CJK + spaces) -> notice", True,
          tool_input={"query": "沒蒐集 文獻全文 html", "limit": 10})
check("T2 two ASCII words -> notice", True, tool_input={"query": "full text"})
check("T3 tab-separated words -> notice", True, tool_input={"query": "loop\tinbox"})
check("T4 same tool under another MCP server prefix -> notice", True,
      tool="mcp__other__search_session_transcripts", tool_input={"query": "paper html survey"})
# Branch pin: the text must carry the value only this hook computes (the query)
# and name itself first, or a generic notice from elsewhere would satisfy T1.
RESULTS.append((t.startswith("session_search_query_notice, a local PreToolUse hook")
                and "`沒蒐集 文獻全文 html`" in t and "nothing needs" in t
                and "telemetry/session-search-query-notice.jsonl" in t,
                "T5 notice names the hook first, quotes the query, says what to do, names its row",
                "pinned", "pinned" if "`沒蒐集 文獻全文 html`" in t else "unpinned"))

# ----------------------------------------------------------- known FALSE
check("F1 single token -> silent", False, tool_input={"query": "dashboard.html"})
check("F2 single token with surrounding spaces -> silent", False, tool_input={"query": "  inbox.py  "})
check("F3 long CJK run without whitespace -> silent (named gap, not gated)", False,
      tool_input={"query": "沒蒐集到文獻全文正本"})
check("F4 a different tool with a multi-word query -> silent", False,
      tool="Grep", tool_input={"query": "two words", "pattern": "two words"})
check("F5 empty query -> silent", False, tool_input={"query": ""})
# AP-62: inputs matching no declared class are unclassifiable -> silent, no row, never folded
check("F6 unclassifiable: query is not a string -> silent", False, tool_input={"query": ["a b"]})
check("F7 unclassifiable: tool_input is not an object -> silent", False, tool_input="a b")
check("F8 malformed stdin fails open", False, raw="not json at all")
check("F9 unclassifiable: payload is a list, not an object -> silent", False, raw="[1, 2]")

# a non-string session_id is unclassifiable: the notice still fires (the query is real),
# but the row records session=None, never the str() of an object as if it were an id
check("T6 unclassifiable session_id -> notice still fires", True,
      raw=json.dumps({"tool_name": TOOL, "tool_input": {"query": "odd session"},
                      "session_id": {"a": 1}}))

# ------------------------------------------ the row exists before the text
log = Path(_TELEMETRY_DIR) / "session-search-query-notice.jsonl"
rows = [json.loads(x) for x in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
RESULTS.append((len(rows) == 5 and all(r.get("kind") == "notice" for r in rows),
                "E1 exactly one telemetry row per notice, none for silent calls",
                "5 rows", "%d rows" % len(rows)))
odd = [r for r in rows if r.get("query") == "odd session"]
RESULTS.append((len(odd) == 1 and odd[0].get("session") is None,
                "E2 unclassifiable session_id is recorded as undetermined (null), not str()-ed",
                "None", repr(odd[0].get("session")) if odd else "no row"))

print("=" * 74)
print("session_search_query_notice  —  %s" % HOOK)
print("=" * 74)
passed = 0
for ok, name, expect, got in RESULTS:
    print("  %s  %-70s expect=%-7s got=%s" % ("PASS" if ok else "FAIL", name, expect, got))
    passed += 1 if ok else 0
print("-" * 74)
n_silent = sum(1 for r in RESULTS if r[3] == "silent")
print("  %d/%d passed   (notice-side %d, silent-side %d — two-sided)"
      % (passed, len(RESULTS), len(RESULTS) - n_silent, n_silent))
sys.exit(0 if passed == len(RESULTS) else 1)
