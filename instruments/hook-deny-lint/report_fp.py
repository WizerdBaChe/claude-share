r"""report_fp — record that a hook denied something it should not have.

Named in every conforming deny message (rules/hook-deny-message.md R3). It
RECORDS; it never unblocks. The point is that a misfire has an exit at the
moment it happens: on 2026-08-29 the only exit available was a silent
workaround (`pdftotext`), the task succeeded, and the guard learned nothing —
the misfire surfaced 9 days later, through a user's question, after a wrong
security-incident record had already propagated into a project's evidence
ledger. A gate whose only exit is a silent workaround is training agents to
route around gates.

    python ~/.claude/tools/hook-deny-lint/report_fp.py --hook <name> --why "..."
    python ~/.claude/tools/hook-deny-lint/report_fp.py --rate

`--rate` prints reported misfires against denies logged by hooks/deny_receipt.py.
Both numbers come with their ruler: a hook with no receipt rows has never been
measured, which is not the same as never having misfired, and it is reported as
"unmeasured", not as 0%.
"""
import argparse
import json
import os
import time
from pathlib import Path

CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
# CLAUDE_TELEMETRY_DIR (O-2, 2026-09-11): same precedence as hooks/deny_receipt.py —
# a suite that exercises a hook's misfire exit must not write a real misfire row.
TELEMETRY = Path(os.environ["CLAUDE_TELEMETRY_DIR"]) if os.environ.get("CLAUDE_TELEMETRY_DIR") else CLAUDE_DIR / "telemetry"
FP_LOG = TELEMETRY / "hook-false-positives.jsonl"
SUITE_SESSIONS = CLAUDE_DIR / "tools" / "telemetry-framing" / "suite-sessions.json"


def _suite_allowlist() -> tuple:
    """(literals, {session_id: set(file names)}) from suite-sessions.json — the
    same list tools/telemetry-framing/framing.py reads. Missing = empty."""
    try:
        data = json.loads(SUITE_SESSIONS.read_text(encoding="utf-8"))
    except Exception:
        return frozenset(), {}
    files = data.get("session_files") or {}
    return (frozenset(data.get("literals") or ()),
            {str(k): frozenset(v or ()) for k, v in files.items()} if isinstance(files, dict) else {})


def _is_suite_row(row: dict, filename: str, allow: tuple) -> bool:
    sid = row.get("session") if row.get("session") is not None else row.get("session_id")
    return sid in allow[0] or filename in allow[1].get(sid, ())


def record(hook: str, why: str, target: str = "") -> Path:
    TELEMETRY.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": int(time.time()),
        "hook": hook,
        "why": why[:600],
        "target": target[:400],
        "session": str(os.environ.get("CLAUDE_CODE_SESSION_ID", ""))[:64],
        "cwd": str(Path.cwd())[:300],
    }
    with FP_LOG.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return FP_LOG


def _rows(path: Path):
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def rate() -> int:
    reports = _rows(FP_LOG)
    by_hook = {}
    for row in reports:
        by_hook.setdefault(str(row.get("hook", "?")), 0)
        by_hook[str(row.get("hook", "?"))] += 1

    allow = _suite_allowlist()
    print("hook                              denies  notices  reported-misfires  rate     suite-rows  rate-excl-suite")
    hooks_dir = CLAUDE_DIR / "hooks"
    names = sorted(p.stem for p in hooks_dir.glob("*.py")) if hooks_dir.is_dir() else []
    total_suite = 0
    for name in names:
        denies, notices, suite = _event_counts(name, allow)
        reported = by_hook.pop(name, 0)
        if not denies and not notices and not reported:
            continue
        events = denies + notices
        total_suite += suite
        if events:
            clean = events - suite
            excl = ("%.1f%%" % (100.0 * reported / clean)) if clean else "unmeasured"
            print("%-32s  %6d  %7d  %17d  %-7s  %10d  %s"
                  % (name, denies, notices, reported, "%.1f%%" % (100.0 * reported / events),
                     suite, excl))
        else:
            print("%-32s  %6s  %7s  %17d  %s"
                  % (name, "unmeasured", "-", reported, "no receipt rows"))
    for name, count in sorted(by_hook.items()):
        print("%-32s  %6s  %7s  %17d  %s"
              % (name, "unmeasured", "-", count, "no receipt rows"))
    _contamination_notes(reports)
    if total_suite:
        print("\nnote: suite-rows = deny/notice rows whose (session, file) is on "
              "tools/telemetry-framing/suite-sessions.json — suite runs before the "
              "writer honoured CLAUDE_TELEMETRY_DIR (O-2, 2026-09-11). Both rates are "
              "printed; neither is filtered for you: a genuine deny by one of those "
              "sessions in a listed file is indistinguishable from its suite rows.")
    print("\nruler: the denominator is denies + notices, because a misfire report does "
          "not say which surface it is about — using denies alone would overstate the "
          "rate of a hook that mostly annotates (F-8, 2026-09-09). denies = rows "
          "hooks/deny_receipt.py wrote since it was wired in (2026-09-07); notices = "
          "rows a hook wrote for a non-blocking annotation (`kind`/`verdict` = notice), "
          "which is what its receipt sentence points the reader at. misfires = rows "
          "this tool wrote. A hook with no rows is unmeasured, not clean.")
    return 0


def _event_counts(hook: str, allow: tuple = (frozenset(), {})):
    """(denies, notices, suite_events) across every telemetry file a hook
    writes rows to. `suite_events` is how many of those deny/notice rows sit on
    the suite-session allowlist FOR THAT FILE (O-2, 2026-09-11) — counted
    separately, never subtracted here, so `rate()` can print both readings.

    A hook's own rows carry `verdict`, deny_receipt's carry `kind`, and two
    hooks log to a file that is not named after them — so the log name is taken
    from the hook when it matches and from the known exceptions when it does
    not. A receipt sentence that names a file this function does not count
    would leave the notice surface with a numerator and no denominator.
    """
    stems = {hook.replace("_", "-")} | set(LOG_ALIASES.get(hook, ()))
    denies = notices = suite = 0
    for stem in stems:
        fname = stem + ".jsonl"
        for row in _rows(TELEMETRY / fname):
            kind = str(row.get("kind") or row.get("verdict") or "")
            if kind == "deny":
                denies += 1
            elif kind == "notice":
                notices += 1
            else:
                continue
            if _is_suite_row(row, fname, allow):
                suite += 1
    return denies, notices, suite


# Hooks whose telemetry file is not <hook-name>.jsonl. Kept beside the reader
# rather than derived, because the alternative is a rate that silently reads an
# empty file.
LOG_ALIASES = {
    "ps_pipeline_close_guard": ("ps-pipeline-close",),
    "compact_loss_record": ("compact-loss",),
}

# Known control-fixture contamination, by the signature its own hook documents.
# It is COUNTED and printed, never filtered out: the same signature matched a
# genuine deny row on 2026-09-09 (a real command that quoted the fixture path),
# so a filter would silently delete true rows from the denominator. Both
# numbers are printed and the reader rules.
CONTAMINATION = {
    "intake_guard": ("hooks/intake_guard.py TELEMETRY CAVEAT",
                     ("L-999", "L-011.md", "lessons.md 'x'")),
}


def _contamination_notes(reports) -> None:
    reported = {}
    for row in reports:
        reported[str(row.get("hook", "?"))] = reported.get(str(row.get("hook", "?")), 0) + 1
    for hook, (where, signatures) in sorted(CONTAMINATION.items()):
        stems = {hook.replace("_", "-")} | set(LOG_ALIASES.get(hook, ()))
        rows = [r for stem in stems for r in _rows(TELEMETRY / (stem + ".jsonl"))]
        events = [r for r in rows
                  if str(r.get("kind") or r.get("verdict") or "") in ("deny", "notice")]
        hits = [r for r in events
                if any(s in json.dumps(r, ensure_ascii=False) for s in signatures)]
        if not hits:
            continue
        rest = len(events) - len(hits)
        misfires = reported.get(hook, 0)
        alt = ("%.1f%%" % (100.0 * misfires / rest)) if rest else "unmeasured"
        print("\nnote: %s — %d of its %d rows match the control-fixture signature "
              "recorded in %s. The rate above does NOT exclude them; excluding them "
              "it reads %s over %d rows. Neither number is filtered for you: the same "
              "signature also matches genuine rows whose command quoted it."
              % (hook, len(hits), len(events), where, alt, rest))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hook")
    ap.add_argument("--why")
    ap.add_argument("--target", default="")
    ap.add_argument("--rate", action="store_true")
    args = ap.parse_args()

    if args.rate:
        return rate()
    if not args.hook or not args.why:
        ap.error("--hook and --why are both required (or use --rate)")
    path = record(args.hook, args.why, args.target)
    print("recorded: %s misfire -> %s" % (args.hook, path))
    print("this did not unblock the call; re-run it by the route the deny named, "
          "or ask the user if there is no legitimate route.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
