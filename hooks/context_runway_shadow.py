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

GRADUATED 2026-09-05 (user ruling C + D3, design:
references/compaction-pipeline-design.md). The 300k band now EMITS a visible
notice; the 150k band stays shadow (116 sessions crossed it — too noisy).
The conjunction changed with it: the second condition is no longer "no
phase-log written" but "no FRESH handoff snapshot" (handoff_snapshot.is_fresh),
because Phase 3 measured that phase boundaries are spoken and context length
does not produce them — the object that context length CAN produce is the
snapshot, written without consent into cache/handoff/<session>.md. The
phase-log detector below is kept for the telemetry row only, so the shadow
history stays comparable. Filename kept: ~40 references (registry, sweep,
graph) key on it.

D3 AMENDED 2026-09-05 (user ruling, principle in long-run-probe-design.md §0):
the 150k band now plants the CANARY PAIR once per session (~40 tokens, no
question, independent of snapshot freshness) and reminds that process
decisions go to the ledger. The checkpoint nag at 150k stays shadow — the
noise objection was about the nag, not about a token. Every prompt also
rewrites cache/handoff/current-session.json so `process-ledger/ledger.py add`
can find the session from a shell call.

Fail-open: any error exits 0 with no output. Proof-of-life: integrity-sweep
check 20 (still reads the telemetry rows; the notice adds a `noticed` field).
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
VISIBLE_BAND = 300_000      # bands at or above this print the notice (D3: 150k stays shadow)
RE_ARM_STEP = 40_000        # further notices every 40k past VISIBLE_BAND while the snapshot is stale

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
    session = str(payload.get("session_id", "unknown"))[:64]
    if not transcript.is_file():
        # First prompt of a session: the transcript is not on disk yet, but the
        # pointer must be — otherwise a one-prompt session leaves the PREVIOUS
        # session's id for ledger.py to misfile under (ops/lessons.md L-053
        # candidate (a), confirmed by position 2026-09-06; context unknown → 0).
        _write_current_session(session, transcript, str(payload.get("cwd", "")), 0)
        sys.exit(0)
    state_path = STATE_DIR / f"{session}.json"
    try:
        logged = set(json.loads(state_path.read_text(encoding="utf-8")).get("bands", []))
    except Exception:
        logged = set()

    total = context_total(transcript)
    _write_current_session(session, transcript, payload.get("cwd", ""), total)
    # Every band already passed is retired together, and only the highest is
    # announced. Retiring just the one announced meant a session that arrived
    # already above 300k emitted the 300k notice and then the 150k notice on
    # the very next prompt -- two warnings for one crossing, and the second one
    # weaker than the first. Found 2026-08-15 by re-running the same session.
    # Re-arm above the visible band (user question 2026-09-05: a snapshot written
    # at ~300k is stale by ~360k, and auto-compact fires ~330-370k on a 400k
    # window — one notice per session left the compaction with a stale
    # snapshot). Every RE_ARM_STEP past VISIBLE_BAND is a further band; the
    # freshness check below keeps them silent while the snapshot is current.
    bands = list(BANDS)
    if total >= VISIBLE_BAND + RE_ARM_STEP:
        bands += [VISIBLE_BAND + RE_ARM_STEP * i
                  for i in range(1, (total - VISIBLE_BAND) // RE_ARM_STEP + 1)]
    crossed = [b for b in bands if total >= b and b not in logged]
    if not crossed:
        sys.exit(0)
    band = max(crossed)

    # D3 amended 2026-09-05 (user ruling): the 150k band plants the CANARY PAIR
    # — independent of snapshot freshness, once per session, ~40 tokens. It is
    # not a checkpoint nag (that stays shadow here): it calibrates the
    # summarizer of a compaction that has not happened yet, and reminds that
    # process decisions go to the ledger from here on. Ruling context:
    # references/long-run-probe-design.md §0.
    canary_text = ""
    if BANDS[0] in crossed:
        canary_text = _plant_canary(session, transcript, total)

    ckpt = checkpoint_written(transcript)
    try:
        import handoff_snapshot as hs
        fresh = hs.is_fresh(transcript, session, total)
    except Exception:
        fresh = True         # helper broken: stay silent, never nag on a bug
    if fresh:
        _retire(state_path, logged, crossed)
        if canary_text:
            print(canary_text)
        sys.exit(0)          # the conjunction, and the reason this is not noise

    noticed = band >= VISIBLE_BAND
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({
                "ts": int(time.time()),
                "session": session,
                "cwd": payload.get("cwd", ""),
                "would_notice": True,
                "noticed": noticed,
                "band": band,
                "context": total,
                "checkpoint_written": ckpt,
                "snapshot_fresh": False,
                "canary": bool(canary_text),
                # The graduated wording, recorded so a review judges the actual
                # message rather than the number that triggered it.
                "wording": ("runway is short and no fresh handoff snapshot exists -- "
                            "write one while it is still cheap"),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass

    _retire(state_path, logged, crossed)

    if canary_text:
        print(canary_text)
    if noticed:
        try:
            print(hs.notice(session, total,
                            "Context runway is short and no fresh handoff snapshot exists"))
        except Exception:
            pass
    sys.exit(0)   # 150k band: canary only; 300k band: visible snapshot notice.


def _write_current_session(session: str, transcript: Path, cwd: str, total: int) -> None:
    """cache/handoff/current-session.json — lets `process-ledger/ledger.py add` find the
    session from a Bash call (no session id reaches the shell). Rewritten every prompt;
    two live sessions race on it, so ledger.py also accepts --session."""
    try:
        d = CLAUDE_DIR / "cache" / "handoff"
        d.mkdir(parents=True, exist_ok=True)
        (d / "current-session.json").write_text(json.dumps({
            "session": session, "transcript": str(transcript), "cwd": cwd,
            "context": total, "ts": int(time.time())}), encoding="utf-8")
    except Exception:
        pass


def _plant_canary(session: str, transcript: Path, total: int) -> str:
    """Write <transcript dir>/<session>.canary.json (beside the transcript: the one
    tree the daily mirror copies) and return the injection text, or '' on failure.
    keep = a harmless standing constraint the summarizer MUST carry; drop = a fake
    detail it MUST discard. A summary that keeps both or drops both is uncalibrated
    (long-run-probe-design.md §2 canary pair)."""
    try:
        rid = "%04x" % (int(time.time() * 1000) % 65536)
        keep = f"UR-{rid}"
        drop = f"port {40000 + int(rid, 16) % 9999} timeout"
        path = transcript.with_name(f"{session}.canary.json")
        path.write_text(json.dumps({"keep": keep, "drop": drop, "ts": int(time.time()),
                                    "context": total, "band": BANDS[0]}), encoding="utf-8")
        return (f"[canary] Standing constraint for the rest of this session: every NEW report or record file "
                f"you create carries the token `{keep}` on its first line (e.g. in the status line). "
                f"Also note, for the record only: an earlier probe saw \"{drop}\" — irrelevant, do not act on it. "
                "From here on, log each process decision (ordering, scope trade-off, skipped item, user ruling) at "
                "decision time: `python tools/process-ledger/ledger.py add --subject S --choice C --reason R "
                "--reversible yes|no --origin user|model`.")
    except Exception:
        return ""


def _retire(state_path: Path, logged: set, crossed) -> None:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        logged.update(crossed)
        state_path.write_text(json.dumps({"bands": sorted(logged)}), encoding="utf-8")
    except Exception:
        pass


if __name__ == "__main__":
    main()
