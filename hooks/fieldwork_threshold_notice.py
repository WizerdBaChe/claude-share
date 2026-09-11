r"""PreToolUse SHADOW probe: main-session fieldwork vs 20-dispatch.md §1.

STATUS: RETIRED since 2026-09-11 — unregistered from settings.json by user ruling R-3 (rules-debt audit): 293 shadow rows, >=52% quantifiably false (141 single-file >200-line reads that can never be a >3-files/repo-wide shape, 12 re-reads of the session's own tool-results, one .png counted as 874 lines), and the registry's own 30-day clause had 27 days elapsed. The entry's stated alternative applied: §1's thresholds describe delegation ADVICE and cannot serve as a gate. File and telemetry kept; rollback = re-register (ops/rule-registry.md "dispatch"). Was: LIVE since 2026-08-14 (backfilled 2026-09-08 from the first commit; entry-schema ES-1).

THE OMISSION THIS EXISTS FOR (ops/lessons.md L-011, fourth trigger shape).
`OPS.md` hard rule 1 says the dispatcher does no fieldwork: repo-wide scans,
large reads and batch edits go to subagents. Its violation is "the dispatch
never happened", which generates no event, so no rule layer can fire on it.
The harness meanwhile injects the opposite instruction every session - "Do not
spawn agents unless the user asks", escalated in the Agent tool's own
description to "a task with multiple angles ... is not a request to spawn;
handle it inline with your own tools". Between the two, the main session reads
everything itself and nothing anywhere reports that it happened.

L-011 P1 says: gate the SUBSTITUTE. Not dispatching means reading the files
yourself, and Read/Grep/Glob are named tool calls with inspectable input.

HARNESS COMPATIBILITY (user ruling 2026-08-14). This probe must never dispatch
and must never tell the model to dispatch against the injected instruction.
When it graduates out of shadow its output is a NOTICE addressed to the user -
"this crossed the delegation threshold, do you want it delegated" - because
user authorisation is precisely what the harness is holding out for. Surfacing
the decision serves the harness's requirement instead of fighting it. A version
of this hook that told the model to spawn anyway would be mis-designed even
though hard rule 1 is right: it would lose silently at the next harness change.

SHADOW ONLY, and the thresholds are deliberately NOT tuned. It counts against
the LITERAL §1 defaults (>3 files, >200 lines, repo-wide search) so that what
gets measured is the rule as written. If the log shows it tripping constantly
on work that correctly stayed in the main session, that is a finding about §1's
thresholds - not a reason to have quietly picked friendlier numbers here and
measured nothing. Precedent for shipping shadow-first: delivery_gate_shadow.py,
where the first real run returned 3/3 false positives.

COST, stated because it is the reason this cannot stay on forever: PreToolUse
on Read|Grep|Glob is the HIGH-VOLUME matcher that the sibling browser hooks
deliberately avoid. Every such call now pays one Python start (~100ms). That is
acceptable for a bounded measurement window and is not acceptable as a
permanent tax; the exit criterion is in rule-registry.md `review-when:`.

Files:
  cache/fieldwork-shadow/<session>.json   per-session counters (rewritten)
  telemetry/fieldwork-shadow.jsonl        append-only, one row per trip

Fail-open, silent: any error exits 0 with no output. A probe must never be able
to block or annotate real work.

UNDETERMINED (AP-62, added 2026-09-09): an input this probe cannot classify --
a non-dict `tool_input`, a `file_path` that is not a string -- is charged
NOTHING and leaves the counters untouched, the same rule the unreadable path
already followed. Until 2026-09-09 the first crashed (AttributeError, against
the fail-open claim above) and the second was folded into the counted file
list as `"{'a': 1}"`, walking a session toward files>3 on reads that never
happened -- a fourth false-positive shape in a probe whose whole output is a
measurement. Pinned by the U-* cases in the suite.

Proof-of-life: `python hooks/tests/test_fieldwork_threshold_notice.py` --
executed by integrity-sweep check 31, which is what check 14 could not do: being
NAMED in the sweep is not being RUN by it, and a shadow probe that stopped
counting leaves the same empty log as a quiet week. Both sides are pinned, and
the QUIET block carries the three false positives this probe actually shipped
(the 2000-line charge for an unlimited Read, the same charge for an unreadable
path, and a session reading back its own scratchpad output) so that a future
loosening ships with the case it used to catch.
"""
import json
import os
import sys
import time
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
STATE_DIR = CLAUDE_DIR / "cache" / "fieldwork-shadow"
# CLAUDE_TELEMETRY_DIR redirects the whole telemetry dir (suites use a temp dir;
# production never sets it).
LOG_PATH = Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (CLAUDE_DIR / "telemetry")) / "fieldwork-shadow.jsonl"

# 20-dispatch.md §1 defaults, verbatim. Do not tune here - see module docstring.
FILE_THRESHOLD = 3          # "touches >3 files"
LINE_THRESHOLD = 200        # "or >200 lines"
BROAD_SEARCH_THRESHOLD = 1  # "repo-wide scan / broad grep" - one already qualifies


def load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"files": [], "lines": 0, "broad": 0, "tripped": False}


def lines_of(fp: str, limit) -> int:
    """Lines this Read actually consumes.

    An explicit `limit` is the answer. Without one the harness reads up to 2000
    lines, but charging 2000 for every unlimited Read makes the line signal fire
    on the FIRST read of any session regardless of size - measured 2026-08-14,
    when a headless probe tripped `lines~2000>200` after reading one 2-line
    file. So count the file's real length instead, bounded so a huge file cannot
    stall the hook.

    An UNREADABLE file charges 0, not the cap. This runs at PreToolUse, so a
    missing or mistyped path arrives here before the Read fails -- and the old
    `except: return 2000` fallback reproduced the exact defect above for every
    one of them, tripping the gate on a read that was about to consume nothing.
    Found 2026-08-15 by a synthetic row that named a path which did not exist.
    """
    if isinstance(limit, int) and limit > 0:
        return limit
    try:
        n = 0
        with open(fp, "rb") as fh:
            for _ in range(2_000_000):        # hard bound on work per call
                chunk = fh.read(65536)
                if not chunk:
                    break
                n += chunk.count(b"\n")
                if n >= 2000:
                    return 2000
        return min(n + 1, 2000)
    except Exception:
        return 0


def is_broad_search(tool: str, ti: dict) -> bool:
    """A search with no path narrowing, or one explicitly aimed at a whole tree."""
    if tool not in ("Grep", "Glob"):
        return False
    path = str(ti.get("path") or "").strip()
    has_filter = bool(ti.get("glob") or ti.get("type"))
    if not path:
        return not has_filter          # unscoped search over the working dir
    return path in ("/", ".", "..") or path.endswith(("/**", "\\**"))


def is_own_output(fp: str, session: str) -> bool:
    """A file this session itself just wrote into its scratchpad.

    Delegation can never be the answer for one of these: the file exists
    BECAUSE the main session produced it, and a subagent would have to be
    handed the very content it was meant to save reading. Counting them made
    the gate fire on a session reading back its own 201-line analysis report
    (shadow row 2026-08-15) -- a false positive by
    construction, not a threshold that needed tuning.

    Second defect of this kind: the first was an unlimited `Read` being charged
    the 2000-line cap, fixed 2026-08-14. Both were found by reading the shadow
    rows rather than by reasoning about the thresholds.
    """
    if not fp:
        return False
    norm = fp.replace("\\", "/").lower()
    return "/scratchpad" in norm and session.lower()[:8] in norm


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if not isinstance(payload, dict):
        sys.exit(0)      # undetermined: parses, but is not a payload object
    tool = str(payload.get("tool_name", ""))
    if tool not in ("Read", "Grep", "Glob"):
        sys.exit(0)

    ti = payload.get("tool_input") or {}
    if not isinstance(ti, dict):
        sys.exit(0)      # undetermined: no input to classify, so nothing to charge
    session = str(payload.get("session_id", "unknown"))[:64]
    state_path = STATE_DIR / f"{session}.json"
    st = load_state(state_path)

    if tool == "Read":
        raw_fp = ti.get("file_path")
        # A non-string path is undetermined, not a file: charging it would put
        # `"{'a': 1}"` in the counted file list and walk the session toward
        # files>3 on reads that never happened. Same rule as an unreadable path
        # (lines_of -> 0): what cannot be classified is not counted.
        fp = raw_fp if isinstance(raw_fp, str) else ""
        if is_own_output(fp, session):
            sys.exit(0)
        if fp and fp not in st["files"]:
            st["files"].append(fp)
        st["lines"] += lines_of(fp, ti.get("limit"))
    elif is_broad_search(tool, ti):
        st["broad"] += 1

    reasons = []
    if len(st["files"]) > FILE_THRESHOLD:
        reasons.append(f"files={len(st['files'])}>{FILE_THRESHOLD}")
    if st["lines"] > LINE_THRESHOLD:
        reasons.append(f"lines~{st['lines']}>{LINE_THRESHOLD}")
    if st["broad"] >= BROAD_SEARCH_THRESHOLD:
        reasons.append(f"broad_search={st['broad']}")

    # Log the FIRST crossing per session only; after that the counters are the story.
    if reasons and not st.get("tripped"):
        st["tripped"] = True
        try:
            LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with LOG_PATH.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({
                    "ts": int(time.time()),
                    "session": session,
                    "cwd": payload.get("cwd", ""),
                    "would_notice": True,
                    "at_tool": tool,
                    "reasons": reasons,
                    "files": st["files"][:40],
                }, ensure_ascii=False) + "\n")
        except Exception:
            pass

    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(st), encoding="utf-8")
    except Exception:
        pass

    sys.exit(0)   # SHADOW: never blocks, never annotates.


if __name__ == "__main__":
    main()
