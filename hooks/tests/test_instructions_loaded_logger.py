"""Two-sided calibration for instructions_loaded_logger.py — stdlib only, hermetic.

Run: python hooks/tests/test_instructions_loaded_logger.py   (exit 0 = all pass)

WHY THIS EXISTS. This hook is pure observation: it never blocks, never prints,
and swallows every error by construction. Those are the right properties AND
the reason it can die unnoticed — a logger that stopped writing and a week with
no sessions produce the same empty file. Nothing about the running system
changes when it breaks, so only an executed suite can tell the two apart
(AP-63).

The hook's own docstring calls an empty live log "a real finding, not a hook
bug". That claim is only usable if the WRITER is known good, which is what the
W-* cases pin. The live row count is printed at the bottom as an observation
and counted in NO verdict (AP-62): this suite cannot determine whether the
`InstructionsLoaded` event fires in this Claude Code version, and folding that
question into pass/fail would make the number plausible and meaningless.

EXTENDING (PH-11 / AP-61): a new payload SHAPE the logger must survive gets a
case in the W block; a new redaction gets one beside W-3; a change to the
rotation policy gets one beside R-1/R-2.
"""
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "instructions_loaded_logger.py"
HOME = Path(__file__).resolve().parents[2]
LIVE = HOME / "telemetry" / "rule-loads.jsonl"

spec = importlib.util.spec_from_file_location("instructions_loaded_logger", HOOK)
logger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(logger)

FAILS: list[str] = []


def check(name: str, got, want) -> None:
    ok = got == want
    if not ok:
        FAILS.append(f"{name}: got {got!r}, want {want!r}")
    print(f"{'ok  ' if ok else 'FAIL'} {name}")


def check_that(name: str, cond: bool, detail="") -> None:
    if not cond:
        FAILS.append(f"{name}: {detail}" if detail else name)
    print(f"{'ok  ' if cond else 'FAIL'} {name}")


def feed(raw: str, log: Path):
    """Run main() with `raw` on stdin and `log` as the target; -> (rc, rows)."""
    real_stdin, real_log = sys.stdin, logger.LOG_PATH
    try:
        sys.stdin = io.StringIO(raw)
        logger.LOG_PATH = log
        rc = logger.main()
    finally:
        sys.stdin, logger.LOG_PATH = real_stdin, real_log
    if not log.is_file():
        return rc, []
    return rc, [ln for ln in log.read_text(encoding="utf-8").splitlines() if ln.strip()]


def fresh() -> Path:
    return Path(tempfile.mkdtemp(prefix="ill-")) / "rule-loads.jsonl"


PAYLOAD = {
    "session_id": "abc-123",
    "cwd": "C:\\Users\\g\\.claude",
    "hook_event_name": "InstructionsLoaded",
    "transcript_path": "C:\\Users\\g\\.claude\\projects\\x\\y.jsonl",
    "instructions": [{"path": "CLAUDE.md", "bytes": 12345}],
}

# ------------------------------------------------------------------ the writer
print("-- the writer: what a well-formed event must leave behind")

log = fresh()
rc, rows = feed(json.dumps(PAYLOAD), log)
check("W-0 exit code is 0", rc, 0)
check("W-1 one event writes exactly one row", len(rows), 1)
rec = json.loads(rows[0])
check("W-2 the row carries the five contract fields",
      sorted(rec), ["cwd", "event", "payload", "session_id", "ts"])
check("W-2b the event name is recorded", rec["event"], "InstructionsLoaded")
check_that("W-3 transcript_path is DROPPED from the body (documented redaction)",
           "transcript_path" not in rec["payload"], rec["payload"])
check_that("W-3b the rest of the payload is kept verbatim",
           rec["payload"].get("instructions") == PAYLOAD["instructions"],
           rec["payload"].get("instructions"))

# Loader-classification fields (2026-09-10, O-1): positive control with the
# env var SET must read it back; negative control with it UNSET must read None
# -- an assertion on presence alone would pass on a logger that hard-coded it.
import os as _os
_saved = _os.environ.pop("CLAUDE_CODE_ENTRYPOINT", None)
try:
    _os.environ["CLAUDE_CODE_ENTRYPOINT"] = "probe-entry"
    log = fresh()
    _rc, rows = feed(json.dumps(PAYLOAD), log)
    rec = json.loads(rows[0])
    check("W-9 transcript_dir is the parent dir NAME only (path still redacted)",
          rec["payload"].get("transcript_dir"), "x")
    check("W-9b transcript_exists is False for a path that does not exist",
          rec["payload"].get("transcript_exists"), False)
    check("W-9c entrypoint reads CLAUDE_CODE_ENTRYPOINT when set",
          rec["payload"].get("entrypoint"), "probe-entry")
    check_that("W-9d ppid is an int", isinstance(rec["payload"].get("ppid"), int),
               rec["payload"].get("ppid"))
    del _os.environ["CLAUDE_CODE_ENTRYPOINT"]
    log = fresh()
    _rc, rows = feed(json.dumps(PAYLOAD), log)
    check("W-9e entrypoint is None when the env var is unset (negative control)",
          json.loads(rows[0])["payload"].get("entrypoint"), None)
finally:
    if _saved is not None:
        _os.environ["CLAUDE_CODE_ENTRYPOINT"] = _saved

log = fresh()
_rc, rows = feed('{"a": 1,, broken', log)
check("W-4 unparsed stdin still produces one valid JSON row", len(rows), 1)
check_that("W-4b and marks itself as unparsed",
           "_unparsed" in json.loads(rows[0])["payload"], rows[0][:100])

log = fresh()
_rc, rows = feed("[1, 2, 3]", log)
check_that("W-5 a non-object payload is marked, not crashed into",
           len(rows) == 1 and "_nonobject" in json.loads(rows[0])["payload"],
           rows[:1])

log = fresh()
_rc, rows = feed(json.dumps({"blob": "x" * (logger.MAX_PAYLOAD_CHARS * 3)}), log)
body = json.loads(rows[0])["payload"]
check_that("W-6 an oversized payload is truncated and says so",
           "_truncated" in body and "<truncated>" in body["_truncated"],
           list(body)[:3])
check_that(f"W-6b the row stays bounded (~MAX_PAYLOAD_CHARS={logger.MAX_PAYLOAD_CHARS})",
           len(rows[0]) < logger.MAX_PAYLOAD_CHARS * 2, len(rows[0]))

log = fresh()
rc, rows = feed("", log)
check("W-7 empty stdin writes NOTHING", rows, [])
check("W-7b and still exits 0", rc, 0)

log = fresh()
_rc, rows = feed(json.dumps({"note": "中文與 emoji 🚀 要原樣寫入"}), log)
check_that("W-8 CJK and emoji are stored verbatim, not escaped",
           "中文與 emoji 🚀 要原樣寫入" in rows[0], rows[0][:120])

# ------------------------------------------- AP-62: the undetermined input class
print("\n-- U-*: input the logger cannot classify is recorded AS unclassifiable")

# W-4/W-5 above show the two markers exist. What AP-62 actually requires is the
# second half: that an `undetermined` row can never be COUNTED as an event. This
# log's only verdict-bearing field is `event`, so the property to pin is that
# every unclassifiable shape leaves it null while naming its own class.
for label, raw, marker in [
    ("unparsed text", "{not json at all,,", "_unparsed"),
    ("a JSON scalar", '"just a string"', "_nonobject"),
    ("a JSON array", "[1, 2, 3]", "_nonobject"),
    ("a JSON null", "null", "_nonobject"),
]:
    log = fresh()
    _rc, rows = feed(raw, log)
    rec = json.loads(rows[0]) if rows else {}
    check_that(f"U-1 {label} -> one row, marked {marker}, and `event` stays null "
               f"so no consumer can count it as an InstructionsLoaded event",
               len(rows) == 1 and marker in rec.get("payload", {})
               and rec.get("event") is None,
               rows[:1])
    check_that(f"U-1b {label} -> the marker is the WHOLE payload, never merged "
               f"into fields that would read as a real event",
               list(rec.get("payload", {})) == [marker], rec.get("payload"))

# The counter-case: a well-formed event is NOT marked. Without this the U-1
# block would pass on a logger that marked everything undetermined.
log = fresh()
_rc, rows = feed(json.dumps(PAYLOAD), log)
rec = json.loads(rows[0])
check_that("U-2 a well-formed event carries NO undetermined marker and does "
           "count (the negative control for U-1)",
           rec["event"] == "InstructionsLoaded"
           and not any(k.startswith("_") for k in rec["payload"]),
           rec["payload"])

# ------------------------------------------------------------------ rotation
print("\n-- rotation: bounded disk use, at most two generations")

log = fresh()
log.parent.mkdir(parents=True, exist_ok=True)
log.write_text("x" * (logger.MAX_BYTES + 1), encoding="utf-8")
_rc, rows = feed(json.dumps(PAYLOAD), log)
backup = log.with_suffix(".jsonl.1")
check_that("R-1 an oversized log is rotated aside", backup.is_file(), list(log.parent.iterdir()))
check("R-1b and the live file restarts at one row", len(rows), 1)

log.write_text("y" * (logger.MAX_BYTES + 1), encoding="utf-8")
_rc, rows = feed(json.dumps(PAYLOAD), log)
check_that("R-2 a second rotation replaces the old backup (two generations, not N)",
           backup.is_file() and backup.read_text(encoding="utf-8").startswith("y"),
           backup.read_text(encoding="utf-8")[:3])
check("R-2b no third generation is kept",
      sorted(p.name for p in log.parent.iterdir()),
      ["rule-loads.jsonl", "rule-loads.jsonl.1"])

# ------------------------------------------------------------------ fail-open
print("\n-- fail-open: observability may never cost a session")

blocked = Path(tempfile.mkdtemp(prefix="ill-blocked-")) / "afile"
blocked.write_text("not a directory", encoding="utf-8")
rc, rows = feed(json.dumps(PAYLOAD), blocked / "rule-loads.jsonl")
check("F-1 an unwritable target still exits 0", rc, 0)
check("F-1b and writes nothing", rows, [])

real_stdin = sys.stdin
try:
    class Exploding(io.StringIO):
        def read(self, *a):
            raise OSError("stdin went away")
    sys.stdin = Exploding()
    check("F-2 a stdin that raises still exits 0", logger.main(), 0)
finally:
    sys.stdin = real_stdin

# ------------------------------------------------------- isolation + live note
print("\n-- isolation, and one observation that is counted in no verdict")

before = LIVE.stat().st_size if LIVE.is_file() else None
log = fresh()
feed(json.dumps(PAYLOAD), log)
after = LIVE.stat().st_size if LIVE.is_file() else None
check("I-1 the LIVE telemetry file was not touched by this suite", after, before)

if LIVE.is_file():
    live_rows = sum(1 for ln in LIVE.read_text(encoding="utf-8", errors="replace")
                    .splitlines() if ln.strip())
    # AP-62: this suite cannot determine whether `InstructionsLoaded` fires in
    # the running Claude Code version, so the number is REPORTED, never scored.
    print(f"note [uncounted] live rule-loads.jsonl carries {live_rows} row(s). "
          f"Zero here means the event does not fire in this version — a real "
          f"finding about Claude Code, not a failure of this hook (see the "
          f"hook docstring); the W-* cases above are what say the writer works.")
else:
    print("note [uncounted] telemetry/rule-loads.jsonl does not exist yet — "
          "either no session has fired InstructionsLoaded, or the event is "
          "absent in this version. Not a verdict on the writer.")

print()
if FAILS:
    print(f"{len(FAILS)} FAILURE(S):")
    for f in FAILS:
        print("  " + f)
    sys.exit(1)
print("ALL TESTS PASSED")
