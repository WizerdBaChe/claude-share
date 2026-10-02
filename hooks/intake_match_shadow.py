r"""UserPromptSubmit SHADOW probe: which lesson cards WOULD the intake store
inject for this prompt?

STATUS: SHADOW (observe-only) since 2026-09-07 (claude-config Phase 23,
closeout-capture R4 M3; design S-8 / INV-7 of
the closeout-capture R3 design note, contract that round's PSM §3.3). This hook NEVER
prints anything to stdout — nothing reaches the model — and it never blocks.
It runs `tools/closeout-intake/intake.py match --text-file <prompt> --json`
(tag overlap over `ops/lessons/`, bounded by INTAKE_INJECT_BUDGET: ≤3 cards /
≤1500 B) and appends one telemetry row per prompt. Graduation to real
injection is a separate USER gate: the criterion (precision on ~20 real
prompts, read from this telemetry) is pending a ruling and is NOT set here.

SEVERITY: WARN (its output is read by a human deciding whether to graduate;
nothing downstream consumes it). Fail-OPEN on every path: unparsable stdin, an
empty or harness-injected prompt, a missing tool, a timeout, a non-zero exit —
exit 0, empty stdout, and (only when a subprocess actually ran and failed) a
row with `error` so the failure rate is visible. Budget: MATCH_TIMEOUT_S; the
measured cost is written into every row as `ms` so the README's timing note
can be recomputed from the log instead of restated.

TELEMETRY: `telemetry/intake-match.jsonl` (override: INTAKE_MATCH_LOG — the
controls harness points it at a temp file). Row: {ts, session, n_cards, bytes,
ids, top_score, ms, prompt_len} (+ `error` on a failed run). The prompt text
itself is NOT logged (only its length): the log is a calibration instrument,
not a transcript.

Registration: settings.json UserPromptSubmit (no matcher). Store override for
tests: INTAKE_MATCH_STORE (passed as `--store`). Project resolution: the
subprocess runs with cwd = the payload's cwd, so intake.py's own
PROJECTS.md lookup applies — no second implementation here.

review-when: the match hook graduates (this file then prints cards and moves
to the DENY/inject severity class with a positive+negative control in
settings), or INTAKE_INJECT_BUDGET changes (re-read the `bytes` median).

Proof-of-life: `python tools/closeout-intake/controls.py` (ALL PASS 63/63 as of
2026-09-09; the suite prints the total, this line only quotes it).
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
INTAKE = CLAUDE_DIR / "tools" / "closeout-intake" / "intake.py"
# Precedence: INTAKE_MATCH_LOG (per-hook override) > CLAUDE_TELEMETRY_DIR
# (suite redirect; production never sets it) > default.
LOG_PATH = Path(os.environ.get("INTAKE_MATCH_LOG")
                or (Path(os.environ.get("CLAUDE_TELEMETRY_DIR") or (CLAUDE_DIR / "telemetry")) / "intake-match.jsonl"))
STORE = os.environ.get("INTAKE_MATCH_STORE") or ""
MATCH_TIMEOUT_S = 1.5
MIN_PROMPT_CHARS = 8          # shorter prompts carry no task words worth matching


def log_row(row: dict) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass


def run_match(prompt: str, cwd: str) -> tuple:
    """-> (result dict or None, error str or None, elapsed ms). Never raises."""
    tmp = None
    t0 = time.monotonic()
    try:
        fd, tmp = tempfile.mkstemp(prefix="intake-match-", suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(prompt)
        cmd = [sys.executable, str(INTAKE), "match", "--text-file", tmp, "--json"]
        if STORE:
            cmd += ["--store", STORE]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=MATCH_TIMEOUT_S,
                           cwd=cwd if cwd and os.path.isdir(cwd) else None)
        ms = int((time.monotonic() - t0) * 1000)
        if r.returncode != 0:
            return None, f"exit {r.returncode}: {(r.stderr or r.stdout).strip()[:120]}", ms
        return json.loads(r.stdout.strip().splitlines()[-1]), None, ms
    except subprocess.TimeoutExpired:
        return None, "timeout", int((time.monotonic() - t0) * 1000)
    except Exception as e:
        return None, repr(e)[:120], int((time.monotonic() - t0) * 1000)
    finally:
        if tmp:
            try:
                os.remove(tmp)
            except OSError:
                pass


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    try:
        if not isinstance(payload, dict):
            sys.exit(0)
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or len(prompt.strip()) < MIN_PROMPT_CHARS:
            sys.exit(0)
        if not INTAKE.is_file():
            sys.exit(0)
        res, err, ms = run_match(prompt, str(payload.get("cwd") or ""))
        row = {"ts": int(time.time()), "session": str(payload.get("session_id") or ""),
               "prompt_len": len(prompt), "ms": ms}
        if res is None:
            row.update({"n_cards": None, "bytes": None, "ids": [], "top_score": None, "error": err})
        else:
            row.update({"n_cards": res.get("n"), "bytes": res.get("bytes"),
                        "ids": res.get("ids") or [], "top_score": res.get("top_score")})
        log_row(row)
    except SystemExit:
        raise
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
