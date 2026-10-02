r"""PreToolUse notice: a multi-word query to the session-transcript search.

STATUS: LIVE since 2026-09-20.

WHAT IT GATES. The Desktop MCP tool `…__search_session_transcripts` matches the
WHOLE query string as one literal, case-insensitive substring (its own
description says "Substring match"). A query such as `沒蒐集 文獻全文 html` can
only hit a transcript containing that exact phrase, so it returns
"No matching sessions found." — text identical to a true negative.

WHY A HOOK (2026-09-20 incident, audit
a retrieval-linkage audit's false-null incident statistics).
Over 640 main-loop transcripts: 15 multi-word calls, 11 returned no match; 9
single-token calls, 0 returned no match. In the incident session eight
multi-word queries in a row came back empty and the session reported the topic
as never discussed, while `dashboard.html` alone hit ten sessions — one of them
titled after the very thing being searched for. The tool's semantics cannot be
changed from here, and a rule saying "remember it is literal" is the kind that
was measured not to hold.

WHY PreToolUse AND NOT PostToolUse. The condition is decidable from the query
BEFORE the call, and PreToolUse `additionalContext` is a surface this
environment already relies on (shell_transport_guard). No existing PostToolUse
hook here sends text to the model, so that surface is unmeasured.

WHY A NOTICE AND NEVER A DENY. An exact phrase is sometimes what the caller
wants (4 of the 15 multi-word calls did hit). The gate can determine how the
tool will READ the query, not what the caller intended, so it forwards with the
fact attached.

Not gated, named so the gap is visible: a long CJK query with no whitespace
(`沒蒐集到文獻全文正本`) is the same trap and carries no whitespace to key on.

Fail-open: any parse problem exits 0 with no output.

Proof-of-life: `python hooks/tests/test_session_search_query_notice.py`
"""
import json
import os
import sys
import time

try:
    from deny_receipt import notice_clause
except Exception:           # a notice must not break the call if telemetry breaks
    def notice_clause(hook, log=""): return ""

HOOK = "session_search_query_notice"
TOOL_SUFFIX = "search_session_transcripts"
LOG_PATH = os.path.join(
    os.environ.get("CLAUDE_TELEMETRY_DIR") or os.path.join(os.path.expanduser("~"), ".claude", "telemetry"),
    "session-search-query-notice.jsonl")

NOTICE_ID = ("session_search_query_notice, a local PreToolUse hook (not file or page "
             "content): ")


def record(payload, query):
    """Persist before emitting. Never raises."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({
                "ts": int(time.time()),
                "kind": "notice",
                "hook": HOOK,
                # a non-string id is unclassifiable: null, never str()-ed into a fake session name
                "session": sid[:64] if isinstance(sid := payload.get("session_id"), str) else None,
                "tokens": len(query.split()),
                "query": query[:200],
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if not isinstance(payload, dict):
        sys.exit(0)
    if not str(payload.get("tool_name", "")).endswith(TOOL_SUFFIX):
        sys.exit(0)
    ti = payload.get("tool_input")
    if not isinstance(ti, dict):
        sys.exit(0)
    query = ti.get("query")
    if not isinstance(query, str):
        sys.exit(0)
    query = query.strip()
    if len(query.split()) < 2:
        sys.exit(0)

    record(payload, query)
    shown = query[:80]
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": NOTICE_ID + (
                f"this query contains whitespace (`{shown}`). The session-transcript "
                "search treats the whole query string as ONE literal, case-insensitive "
                "substring, so it hits only where that exact phrase occurs. An empty "
                "result for this query is therefore not evidence that no session "
                "covered the topic. If the exact phrase is what you want, nothing needs "
                "doing; otherwise run the search again with a single distinctive token "
                "(a file name, an identifier, a rare word), one call per candidate token."
            ) + notice_clause(HOOK),
        }
    }, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
