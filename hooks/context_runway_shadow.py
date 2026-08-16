r"""UserPromptSubmit SHADOW probe: context runway vs an unwritten checkpoint.

WHAT THIS IS FOR, and what it is deliberately NOT for.
Phase 3 measured that phase boundaries are SPOKEN, not mechanical: context
length is uncorrelated with "is this a boundary". Wiring this to the boundary
question would manufacture false positives. What it does answer is a different
and currently unguarded failure: a session reaching compaction (or death) with
a lot of work in it and NO checkpoint written, so the durable context survives
only as a lossy summary. `workflow-checkpoint` itself says a checkpoint written
near context exhaustion is exactly when sections silently go missing -- so the
value is warning while there is still room to write a good one.

The wording when this graduates must therefore be "runway is short, checkpoint
while it is still cheap", NEVER "this looks like a phase boundary".

MEASURED BASE RATE (2026-08-15, 149 sessions with main-loop usage records).
Checkpoint rate by session size: <100k 14%, 100-200k 46%, 200-300k 50%,
300-400k 65%, >400k 63%. It PLATEAUS around 63% instead of climbing toward
100% -- length alone does not cause a checkpoint to happen, and that plateau is
the gap. 29 of the 71 sessions that passed 200k never wrote one.
Honest bound: "no checkpoint" is not the same as "should have had one" (a
session where no phase completed correctly has none), so 41% is an UPPER bound
on the defect rate, not the rate. Shadow mode exists to close that gap.

WHY A HOOK AND NOT A WIDER SKILL DESCRIPTION (cost asymmetry, measured).
  hook notice, dismissed        ~60 tokens
  skill routed + asked + "no"   ~2,600 (workflow-checkpoint SKILL.md is 10,379
                                chars and loads in full on invoke)
  full checkpoint executed      tens of thousands
The gap that decides the carrier is the FIRST one: ~43x. A false fire of a hook
notice is nearly free, so the threshold can be liberal; a false fire of a
widened routing surface is not, so the description stays as it is (user ruling
2026-08-15: prefer more chances to ask, given the costs differ).

WHY THE THRESHOLD IS A GUESS AND WHAT WOULD SETTLE IT.
There is no observable ceiling in the data: main-loop context grows smoothly to
777k across 149 sessions with no pile-up at any window limit, so the window
cannot be recovered from transcripts and no fraction-of-window threshold can be
honest. The bands below are therefore anchored to the LOCAL distribution
(median session maximum 189k), not to a capacity. Marked PROVISIONAL in
rule-registry.md. Settled by shadow rows, not by re-reasoning.

THE CONJUNCTION IS THE POINT. Context alone fires in 65% of sessions at 150k;
requiring that no checkpoint has been written yet cuts that to 26%. Both
existing probes' every error was about WHAT COUNTS as the triggering event, so
the second condition is not a refinement here -- it IS the trigger.
A third condition (>=3 file writes) was measured and DROPPED: it moved 47
sessions to 45. A condition that does not discriminate is not rigour.

Files:
  cache/context-runway/<session>.json   bands already logged (rewritten)
  telemetry/context-runway-shadow.jsonl append-only, one row per band crossing

Fail-open, silent: any error exits 0 with no output, and stdout is empty
unconditionally even though UserPromptSubmit is one of the three events whose
stdout Claude would see. Proof-of-life: integrity-sweep check 20.
"""
import json
import os
import sys
import time
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
STATE_DIR = CLAUDE_DIR / "cache" / "context-runway"
LOG_PATH = Path(os.environ.get("CONTEXT_RUNWAY_LOG")
                or (CLAUDE_DIR / "telemetry" / "context-runway-shadow.jsonl"))

# PROVISIONAL. Anchored to the local distribution (median session max 189k),
# not to a context window -- see the module docstring. Two bands, so declining
# the first does not spend the session's only warning.
BANDS = (150_000, 300_000)

TAIL_BYTES = 262_144        # enough for the last usage record in every observed
                            # transcript; the cheap check runs on every prompt.


def context_total(transcript: Path) -> int:
    """Main-loop context at the most recent assistant record, or 0.

    Reads only the tail: this runs once per user prompt, and the answer is
    always in the last few records. Sidechain (subagent) records are skipped --
    a subagent's prompt size is not this session's context, and counting them
    would inflate exactly the sessions that delegated correctly.

    Escalates to a full read when the tail holds no usage record at all. That
    is not a rare edge: one session ends with 256KB of tool and sidechain
    records and the tail-only version returned 0 for it, i.e. it silently
    reported "no context used" for the second-largest session on disk. Found
    2026-08-15 by running the function against real transcripts rather than
    reasoning about them -- the same way both sibling probes' defects surfaced.
    """
    try:
        size = transcript.stat().st_size
        with transcript.open("rb") as fh:
            if size > TAIL_BYTES:
                fh.seek(size - TAIL_BYTES)
                fh.readline()               # discard the partial line
            lines = fh.read().decode("utf-8", "replace").splitlines()
        total = _last_usage(lines)
        if total or size <= TAIL_BYTES:
            return total
        with transcript.open("r", encoding="utf-8", errors="replace") as fh:
            return _last_usage(fh.read().splitlines())
    except Exception:
        return 0


def _last_usage(lines) -> int:
    for line in reversed(lines):
        if '"usage"' not in line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if rec.get("isSidechain"):
            continue
        usage = (rec.get("message") or {}).get("usage") or {}
        if not usage:
            continue
        total = (usage.get("input_tokens", 0)
                 + usage.get("cache_creation_input_tokens", 0)
                 + usage.get("cache_read_input_tokens", 0))
        if not total:
            continue    # a `usage` block whose three fields are all zero is a
                        # real and trailing shape (interrupted turns): session
                        # one session ends with one, and taking it at face value
                        # reported 0 tokens for a 564k session.
        return total
    return 0


def checkpoint_written(transcript: Path) -> bool:
    """Has this session written into a phase log yet?

    Substring detection over raw lines, deliberately the SAME detector used to
    measure the base rate in the docstring -- a shipped rule that disagrees
    with the measurement that justified it is measuring nothing. It over-counts
    (a mention of the path in prose can match) which biases toward NOT firing,
    the safe direction for a probe.

    Only called once the cheap band check has already passed, so the full-file
    read is paid at most twice per session rather than once per prompt.
    """
    try:
        with transcript.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if "phase-log" not in line:
                    continue
                low = line.replace(" ", "").lower()
                if '"name":"write"' in low or '"name":"edit"' in low:
                    return True
    except Exception:
        return True          # unreadable: assume written, i.e. stay silent
    return False


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    raw = payload.get("transcript_path")
    if not raw:
        sys.exit(0)
    transcript = Path(str(raw))
    if not transcript.is_file():
        sys.exit(0)

    session = str(payload.get("session_id", "unknown"))[:64]
    state_path = STATE_DIR / f"{session}.json"
    try:
        logged = set(json.loads(state_path.read_text(encoding="utf-8")).get("bands", []))
    except Exception:
        logged = set()

    total = context_total(transcript)
    # Every band already passed is retired together, and only the highest is
    # announced. Retiring just the one announced meant a session that arrived
    # already above 300k emitted the 300k notice and then the 150k notice on
    # the very next prompt -- two warnings for one crossing, and the second one
    # weaker than the first. Found 2026-08-15 by re-running the same session.
    crossed = [b for b in BANDS if total >= b and b not in logged]
    if not crossed:
        sys.exit(0)
    band = max(crossed)

    if checkpoint_written(transcript):
        sys.exit(0)          # the conjunction, and the reason this is not noise

    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({
                "ts": int(time.time()),
                "session": session,
                "cwd": payload.get("cwd", ""),
                "would_notice": True,
                "band": band,
                "context": total,
                "checkpoint_written": False,
                # The graduated wording, recorded so a review judges the actual
                # message rather than the number that triggered it.
                "wording": ("context is long and no checkpoint exists yet -- "
                            "write one while it is still cheap"),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass

    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        logged.update(crossed)
        state_path.write_text(json.dumps({"bands": sorted(logged)}), encoding="utf-8")
    except Exception:
        pass

    sys.exit(0)   # SHADOW: empty stdout, never notices, never blocks.


if __name__ == "__main__":
    main()
