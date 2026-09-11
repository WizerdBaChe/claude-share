"""Regression matrix for transcript_read_guard.py — stdlib only, hermetic.

Run: python hooks/tests/test_transcript_read_guard.py   (exit 0 = all pass)

Pins the hook docstring's DECISION TABLE and BOUNDARIES AND UNKNOWNS ledger:
every allow/deny class documented there has a case here, INCLUDING the three
accepted bypasses (UNC admin share, hardlink, renamed copy) — those are
asserted as "pass" on purpose, so if canonicalization ever starts catching
them the ledger is flagged stale instead of silently drifting.

Born from the 2026-08-29 false-positive event (see the hook's FALSE-POSITIVE
LOG): path-only identity denied WebFetch PDF caches under
projects/**/tool-results/. Loosening a gate ships with the case it used to
catch (global CLAUDE.md rule): big .jsonl unbounded -> deny stays pinned.
"""
import contextlib
import ctypes
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "transcript_read_guard.py"

spec = importlib.util.spec_from_file_location("transcript_read_guard", HOOK)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

BIG = guard.SIZE_GATE + 1024
SMALL = 4 * 1024


def run_case(file_path, limit=None, offset=None):
    """Feed one PreToolUse payload through main(); return (verdict, stdout)."""
    tool_input = {"file_path": str(file_path)}
    if limit is not None:
        tool_input["limit"] = limit
    if offset is not None:
        tool_input["offset"] = offset
    payload = json.dumps({"tool_name": "Read", "tool_input": tool_input})
    stdout = io.StringIO()
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(payload)
    try:
        with contextlib.redirect_stdout(stdout):
            try:
                guard.main()
            except SystemExit:
                pass
    finally:
        sys.stdin = old_stdin
    out = stdout.getvalue()
    return ("deny" if '"deny"' in out else "pass"), out


def run_raw(payload_text):
    """Feed RAW stdin text (not necessarily a well-formed payload) through main()."""
    stdout = io.StringIO()
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(payload_text)
    crashed = None
    try:
        with contextlib.redirect_stdout(stdout):
            try:
                guard.main()
            except SystemExit:
                pass
            except Exception as exc:          # the pre-2026-09-09 shape: AttributeError
                crashed = f"{type(exc).__name__}: {exc}"
    finally:
        sys.stdin = old_stdin
    out = stdout.getvalue()
    if crashed:
        return "error", crashed
    return ("deny" if '"deny"' in out else "pass"), out


def short_name(p: Path):
    buf = ctypes.create_unicode_buffer(1024)
    n = ctypes.windll.kernel32.GetShortPathNameW(str(p), buf, 1024)
    return buf.value if n else None


def main() -> int:
    failures, skipped = [], []
    with tempfile.TemporaryDirectory() as td:
        corpus = Path(td) / "corpus"
        outside = Path(td) / "outside"
        guard.CORPUS_ROOTS = (corpus,)
        # In-process deny() calls reach deny_receipt.clause(); redirect its
        # TELEMETRY dir here (not just CLAUDE_CONFIG_DIR) so a "deny" case
        # above never appends to production telemetry/transcript-read-guard.jsonl.
        _prev_telemetry_dir = os.environ.get("CLAUDE_TELEMETRY_DIR")
        os.environ["CLAUDE_TELEMETRY_DIR"] = str(Path(td) / "telemetry")

        def mk(rel: str, size: int) -> Path:
            p = (corpus / rel) if not rel.startswith("!") else (outside / rel[1:])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"x" * size)
            return p

        cases = [
            # (name, path, limit, offset, expected)
            # -- accepted behaviour the loosening must NOT regress:
            ("big jsonl unbounded", mk("s1/a.jsonl", BIG), None, None, "deny"),
            ("big jsonl limit over window",
             mk("s1/b.jsonl", BIG), guard.LINE_WINDOW + 1, None, "deny"),
            ("big digest md unbounded",
             mk("digests/proj/sess.md", BIG), None, None, "deny"),
            # -- windowed / small reads stay friction-free:
            ("big jsonl windowed",
             mk("s1/c.jsonl", BIG), guard.LINE_WINDOW, None, "pass"),
            ("small jsonl unbounded", mk("s1/d.jsonl", SMALL), None, None, "pass"),
            # -- the 2026-08-29 false positives, fixed:
            ("webfetch pdf in tool-results",
             mk("s1/tool-results/webfetch-x.pdf", BIG), None, None, "pass"),
            ("tool-result overflow txt",
             mk("s1/tool-results/overflow.txt", BIG), None, None, "pass"),
            ("model tokenizer json",
             mk("model-cache/tokenizer.json", BIG), None, None, "pass"),
            ("error log txt in session dir",
             mk("s1/auto-mode-classifier-error.txt", BIG), None, None, "pass"),
            ("non-digest big md", mk("s1/notes.md", BIG), None, None, "pass"),
            # -- scope: records outside every corpus root are untouched:
            ("big jsonl outside corpus", mk("!x/a.jsonl", BIG), None, None, "pass"),
            # -- input-edge semantics (decision table, probed 2026-08-29):
            ("uppercase extension .JSONL", mk("s2/UP.JSONL", BIG), None, None, "deny"),
            ("uppercase DIGESTS/ + .MD", mk("DIGESTS/X.MD", BIG), None, None, "deny"),
            ("size exactly == gate passes",
             mk("s2/eq.jsonl", guard.SIZE_GATE), None, None, "pass"),
            ("string limit counts as absent",
             mk("s2/sl.jsonl", BIG), "50", None, "deny"),
            ("offset alone is not a window",
             mk("s2/of.jsonl", BIG), None, 500, "deny"),
            # -- documented accepted bypass (ledger pin):
            ("renamed copy .jsonl.bak escapes shape",
             mk("s2/r.jsonl.bak", BIG), None, None, "pass"),
        ]

        # -- path-alias canonicalization (probed 2026-08-29):
        alias_target = mk("s3/alias.jsonl", BIG)
        cases.append(("extended-length prefix form",
                      "\\\\?\\" + str(alias_target), None, None, "deny"))

        sn = short_name(alias_target)
        if sn and sn.lower() != str(alias_target).lower():
            cases.append(("8.3 short-name form", sn, None, None, "deny"))
        else:
            skipped.append("8.3 short-name (no short name generated here)")

        junc = Path(td) / "junc"
        subprocess.run(["cmd", "/c", "mklink", "/J", str(junc),
                        str(alias_target.parent)], capture_output=True)
        if junc.exists():
            cases.append(("junction alias into corpus",
                          junc / alias_target.name, None, None, "deny"))
        else:
            skipped.append("junction (mklink /J unavailable)")

        hard = Path(td) / "hard.jsonl"
        subprocess.run(["cmd", "/c", "mklink", "/H", str(hard),
                        str(alias_target)], capture_output=True)
        if hard.exists():
            cases.append(("hardlink alias (documented bypass)",
                          hard, None, None, "pass"))
        else:
            skipped.append("hardlink (mklink /H unavailable)")

        drive = str(alias_target)[:2]
        if drive.lower() == "c:":
            unc = "//localhost/c$" + str(alias_target)[2:].replace("\\", "/")
            cases.append(("UNC admin-share form (documented bypass)",
                          unc, None, None, "pass"))
        else:
            skipped.append("UNC admin-share (fixture not on C:)")

        deny_text = ""
        for name, path, limit, offset, expected in cases:
            verdict, out = run_case(path, limit, offset)
            status = "ok " if verdict == expected else "FAIL"
            if verdict != expected:
                failures.append(name)
            if verdict == "deny":
                deny_text = out
            print(f"{status} {verdict:4} (want {expected:4}) | {name}")

        # -- AP-62 unclassifiable input: payloads that match NO row of the
        # decision table, because there is nothing to classify — identity,
        # scope, size and window are all undecidable. The hook's declared
        # degradation is the silent pass ("Fail-open on malformed input"), so
        # `undetermined` must surface as a pass and must NEVER be folded into
        # a deny: a fold is invisible here, since the deny count stays
        # plausible while the reason names a file nobody asked to read.
        # The middle two crashed with AttributeError until 2026-09-09 — the
        # class existed in the corpus and was never enumerated.
        undetermined = [
            ("undetermined: stdin is not JSON at all", "not json {"),
            ("undetermined: JSON array, not a payload object",
             json.dumps([{"tool_name": "Read"}])),
            ("undetermined: tool_input is a list, not an object",
             json.dumps({"tool_name": "Read", "tool_input": ["file_path"]})),
            ("undetermined: file_path is an object, not a path",
             json.dumps({"tool_name": "Read",
                         "tool_input": {"file_path": {"unexpected": "shape"}}})),
        ]
        for name, raw_payload in undetermined:
            verdict, detail = run_raw(raw_payload)
            status = "ok " if verdict == "pass" else "FAIL"
            if verdict != "pass":
                failures.append(f"{name} -> {verdict} ({detail})")
            print(f"{status} {verdict:4} (want pass) | {name}")

        # Deny-message contract (see hook docstring): constraint + retry only.
        reason = json.loads(deny_text)["hookSpecificOutput"][
            "permissionDecisionReason"]
        for banned in ("Policy:", "memory-archive"):
            if banned in reason:
                failures.append(f"deny message contains banned text: {banned}")
                print(f"FAIL deny-message contract: contains {banned!r}")
        for required in ("offset", f"limit<={guard.LINE_WINDOW}"):
            if required not in reason:
                failures.append(f"deny message missing: {required}")
                print(f"FAIL deny-message contract: missing {required!r}")
        if not failures:
            print("ok   deny-message contract (no authority claim, no "
                  "read-elsewhere imperative, retry mechanics present)")

        if _prev_telemetry_dir is None:
            os.environ.pop("CLAUDE_TELEMETRY_DIR", None)
        else:
            os.environ["CLAUDE_TELEMETRY_DIR"] = _prev_telemetry_dir

    for s in skipped:
        print(f"skip {s}")
    print(f"\n{len(cases) + len(undetermined)} cases "
          f"({len(undetermined)} unclassifiable-input), {len(failures)} failures, "
          f"{len(skipped)} skipped")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
