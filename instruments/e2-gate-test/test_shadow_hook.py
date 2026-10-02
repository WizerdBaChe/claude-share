"""Synthetic-payload test for delivery_gate_shadow.py event_kind (2026-08-12).

Runs the hook as a SUBPROCESS so stdout/exit-code are observed the way the
harness observes them, with the log redirected to a temp file via an injected
override -- the real telemetry log is never opened.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path.home() / ".claude" / "hooks" / "delivery_gate_shadow.py"
REAL_LOG = Path.home() / ".claude" / "telemetry" / "delivery-gate-shadow.jsonl"
TMP = Path(tempfile.mkdtemp()) / "test-log.jsonl"

# A resolvable main/subagent transcript pair for the happy path. SHARE EDITION:
# the source suite pointed at one real session on disk; this edition builds a
# synthetic pair in a temp tree, laid out the way the harness lays it out
# (<project>/<session>.jsonl and <project>/<session>/subagents/agent-<id>.jsonl),
# so the suite runs on a machine that has no such session.
PROJ = Path(tempfile.mkdtemp()) / "synthetic-project"
SID = "synthetic-session-0001"
REAL_MAIN = PROJ / f"{SID}.jsonl"
REAL_AGENT = "asynthetic0001"
(PROJ / SID / "subagents").mkdir(parents=True)
REAL_MAIN.write_text(json.dumps({"type": "user", "message": {"content": "x"}}) + "\n",
                     encoding="utf-8")
(PROJ / SID / "subagents" / f"agent-{REAL_AGENT}.jsonl").write_text(
    json.dumps({"type": "assistant", "message": {"content": [
        {"type": "text", "text": "x"}]}}) + "\n", encoding="utf-8")

# Shim: import the hook, point LOG_PATH at the temp file, then run main().
SHIM = f"""
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("dgs", r"{HOOK}")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.LOG_PATH = Path(r"{TMP}")
sys.exit(m.main())
"""

# Prose-vs-code fixtures (added 2026-08-15). Both organic would-block rows of
# the first soak were subagents writing spec documents, which have nothing to
# execute -- false positives from treating any write as a testable write. These
# two cases pin the distinction so the exclusion cannot silently regress.
# resolution is <main_parent>/<main_stem>/subagents/agent-<id>.jsonl,
# so the fixture dir must mirror that, not sit beside main.jsonl.
FIX = Path(tempfile.mkdtemp())
(FIX / "main" / "subagents").mkdir(parents=True)


def _write_fixture(agent, target):
    rec = {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "t1", "name": "Write",
         "input": {"file_path": target, "content": "x"}}]}}
    p = FIX / "main" / "subagents" / f"agent-{agent}.jsonl"
    p.write_text(json.dumps(rec) + "\n", encoding="utf-8")


_write_fixture("prosewriter", str(FIX / "docs" / "verification_PSM_v0.3.md"))
_write_fixture("codewriter", str(FIX / "src" / "calc.py"))


# Vocabulary fixtures (added 2026-09-08 with VERIFY_LOCAL / WEAK_SHELL). Two
# sides, because a vocabulary that only ever ADDS matches cannot be shown to
# have stayed honest: V1-V4 must be rescued, W1-W3 must NOT be. The weak side
# is the load-bearing half -- `git status` returning clean is the single easiest
# way to make would_block collapse to zero and the gate mean nothing.
def _write_verify_fixture(agent, cmd, is_error=False, tool="Bash"):
    """A subagent that writes code and then runs one command."""
    recs = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "w1", "name": "Write",
             "input": {"file_path": str(FIX / "src" / "calc.py"), "content": "x"}},
            {"type": "tool_use", "id": "c1", "name": tool,
             "input": {"command": cmd}}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "c1", "is_error": is_error}]}},
    ]
    p = FIX / "main" / "subagents" / f"agent-{agent}.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")


VOCAB = [
    # (agent, command, is_error, expect_verified, note)
    ("v1", "python tools/shell-audit/controls.py", False, True, "a control suite"),
    ("v2", "python hooks/worktree_scope_guard.py --selftest", False, True,
     "a selftest flag"),
    ("v3", "diff -u before.txt after.txt", False, True, "diff produces a verdict"),
    ("v4", "python tools/entry-schema-lint/lint.py", False, True, "a lint script"),
    ("v5", "pytest -q", False, True, "the portable vocabulary still works"),
    # the result must be CLEAN -- a failing verify is not a verification
    ("v6", "python tools/shell-audit/controls.py", True, False,
     "the same command with is_error True must NOT count"),
    # weak: looked at, not checked
    ("w1", "git status --short", False, False, "git status is not a verdict"),
    ("w2", "grep -rn TODO src/", False, False, "grep is not a verdict"),
    ("w3", "ls -la out/", False, False, "ls is not a verdict"),
]
for agent, cmd, err, _exp, _note in VOCAB:
    _write_verify_fixture(agent, cmd, err)


# AP-62: the class that is NEITHER. VERIFY_SHELL/VERIFY_LOCAL and WEAK_SHELL are
# the two declared command classes; a command matching neither belongs to
# neither, and the row must leave it there rather than fold it into the closer
# one. This is the load-bearing half of the docstring's residual split: 38 of
# the 178 would-block transcripts were read as "did not look at all" purely
# because `weak_evidence` was empty, and that reading holds ONLY while the raw
# command survives in `commands`. Drop `commands` in a future vocabulary edit
# and an unrecognised shape becomes indistinguishable from having run nothing
# at all -- the 38 would absorb it and the count would stay plausible.
UNDETERMINED = [
    ("u1", "node scripts/render-report.js",
     "undetermined: a build script is neither a verdict nor a looked-at shape"),
]
for agent, cmd, _note in UNDETERMINED:
    _write_verify_fixture(agent, cmd)

CASES = [
    ("prose-only write -> NOT a delivery-gate finding",
     {"session_id": "sP", "agent_id": "prosewriter", "agent_type": "general-purpose",
      "transcript_path": str(FIX / "main.jsonl")},
     {"wrote": False, "would_block": False}),

    ("code write, no verify -> still WOULD-BLOCK",
     {"session_id": "sC", "agent_id": "codewriter", "agent_type": "general-purpose",
      "transcript_path": str(FIX / "main.jsonl")},
     {"wrote": True, "verified": False, "would_block": True}),

    ("subagent-direct",
     {"session_id": "s1", "agent_id": "aXYZ", "agent_type": "code-reviewer",
      "transcript_path": str(PROJ / "subagents" / "agent-aXYZ.jsonl")},
     {"event_kind": "dispatch", "transcript_kind": "subagent-direct"}),

    ("subagent-resolved (real file on disk)",
     {"session_id": SID, "agent_id": REAL_AGENT, "agent_type": "general-purpose",
      "transcript_path": str(REAL_MAIN)},
     {"event_kind": "dispatch", "transcript_kind": "subagent-resolved",
      "transcript_read": True}),

    ("no agent_id",
     {"session_id": "s2", "transcript_path": str(REAL_MAIN)},
     {"event_kind": "no-agent-id", "wrote": None, "would_block": False}),

    ("missing file, subagents/ dir EXISTS (race candidate)",
     {"session_id": SID, "agent_id": "aDEADBEEF00000000",
      "transcript_path": str(REAL_MAIN)},
     {"event_kind": "no-transcript", "subagents_dir": True, "wrote": None}),

    ("missing file, no subagents/ dir (not a dispatch)",
     {"session_id": "s3", "agent_id": "aNOPE",
      "transcript_path": str(PROJ / "no-such-session-abc.jsonl")},
     {"event_kind": "no-transcript", "subagents_dir": False, "wrote": None}),

    ("no transcript_path",
     {"session_id": "s4", "agent_id": "aNONE"},
     {"event_kind": "no-transcript-path", "subagents_dir": None,
      "transcript_name": ""}),
]

# PRE-EXISTING behaviour, unchanged by the event_kind edit and asserted here so
# a later change cannot alter it silently: only UNPARSEABLE stdin returns early
# with no row. Empty / non-dict / null stdin degrade to payload={} and still
# write a row -- which is now labelled no-transcript-path, i.e. classified out
# of the phase-2 population instead of silently dropped.
RAW_CASES = [
    ("malformed stdin -> no row", "{not json at all", 0),
    ("empty stdin -> classified row", "", 1),
    ("non-dict JSON -> classified row", "[1,2,3]", 1),
    ("null JSON -> classified row", "null", 1),
]


def run(stdin_text):
    p = subprocess.run([sys.executable, "-c", SHIM], input=stdin_text,
                       capture_output=True, text=True)
    return p


def main():
    before = (REAL_LOG.stat().st_size, REAL_LOG.stat().st_mtime_ns) if REAL_LOG.exists() else None
    if TMP.exists():
        TMP.unlink()
    passed = failed = 0

    for name, payload, expect in CASES:
        p = run(json.dumps(payload))
        rows = [json.loads(l) for l in TMP.read_text(encoding="utf-8").splitlines() if l.strip()]
        row = rows[-1] if rows else {}
        errs = []
        if p.returncode != 0:
            errs.append(f"exit={p.returncode}")
        if p.stdout != "":
            errs.append(f"stdout={p.stdout!r}")
        if row.get("mode") != "shadow":
            errs.append(f"mode={row.get('mode')!r}")
        for k, v in expect.items():
            if row.get(k) != v:
                errs.append(f"{k}={row.get(k)!r} want {v!r}")
        if errs:
            failed += 1
            print(f"FAIL  {name}\n      {'; '.join(errs)}")
        else:
            passed += 1
            print(f"ok    {name}  -> event_kind={row['event_kind']} "
                  f"subagents_dir={row['subagents_dir']} would_block={row['would_block']}")

    for agent, cmd, err, expect_verified, note in VOCAB:
        p = run(json.dumps({"session_id": f"s-{agent}", "agent_id": agent,
                            "agent_type": "general-purpose",
                            "transcript_path": str(FIX / "main.jsonl")}))
        rows = [json.loads(l) for l in TMP.read_text(encoding="utf-8").splitlines()
                if l.strip()]
        row = rows[-1] if rows else {}
        errs = []
        if p.returncode != 0 or p.stdout != "":
            errs.append(f"exit={p.returncode} stdout={p.stdout!r}")
        if row.get("verified") is not expect_verified:
            errs.append(f"verified={row.get('verified')!r} want {expect_verified}")
        if row.get("would_block") is expect_verified:
            errs.append(f"would_block={row.get('would_block')!r}")
        # a weak command must be RECORDED, not merely dropped
        if agent.startswith("w") and not row.get("weak_evidence"):
            errs.append("weak_evidence empty -- the residual is unexplained")
        if errs:
            failed += 1
            print(f"FAIL  vocab {agent}: {cmd}\n      {'; '.join(errs)}")
        else:
            passed += 1
            print(f"ok    vocab {agent}: {cmd[:44]:44} -> verified="
                  f"{row.get('verified')}  ({note})")

    for agent, cmd, note in UNDETERMINED:
        p = run(json.dumps({"session_id": f"s-{agent}", "agent_id": agent,
                            "agent_type": "general-purpose",
                            "transcript_path": str(FIX / "main.jsonl")}))
        rows = [json.loads(l) for l in TMP.read_text(encoding="utf-8").splitlines()
                if l.strip()]
        row = rows[-1] if rows else {}
        errs = []
        if p.returncode != 0 or p.stdout != "":
            errs.append(f"exit={p.returncode} stdout={p.stdout!r}")
        if row.get("verified") is not False:
            errs.append(f"verified={row.get('verified')!r} -- an undetermined "
                        "command must never be promoted to a verdict")
        if row.get("weak_evidence"):
            errs.append(f"weak_evidence={row.get('weak_evidence')!r} -- folded "
                        "into the nearest declared class instead of left out")
        if cmd not in (row.get("commands") or []):
            errs.append(f"commands={row.get('commands')!r} -- the undetermined "
                        "command is not recoverable from the row")
        if row.get("would_block") is not True:
            errs.append(f"would_block={row.get('would_block')!r}, want True")
        if errs:
            failed += 1
            print(f"FAIL  undetermined {agent}: {cmd}\n      {'; '.join(errs)}")
        else:
            passed += 1
            print(f"ok    undet {agent}: {cmd[:44]:44} -> neither verified nor "
                  f"weak, kept in commands  ({note})")

    n_before = len([l for l in TMP.read_text(encoding='utf-8').splitlines() if l.strip()])
    for name, raw, want_rows in RAW_CASES:
        p = run(raw)
        rows = [json.loads(l) for l in TMP.read_text(encoding="utf-8").splitlines() if l.strip()]
        n_after = len(rows)
        errs = []
        if p.returncode != 0:
            errs.append(f"exit={p.returncode}")
        if p.stdout != "":
            errs.append(f"stdout={p.stdout!r}")
        if n_after - n_before != want_rows:
            errs.append(f"rows +{n_after - n_before}, want +{want_rows}")
        elif want_rows:
            row = rows[-1]
            if row.get("event_kind") != "no-transcript-path":
                errs.append(f"event_kind={row.get('event_kind')!r}")
            if row.get("wrote") is not None or row.get("would_block") is not False:
                errs.append(f"classified as data: wrote={row.get('wrote')!r}")
        n_before = n_after
        if errs:
            failed += 1
            print(f"FAIL  {name}\n      {'; '.join(errs)}")
        else:
            passed += 1
            print(f"ok    {name}  -> exit 0, empty stdout, rows +{want_rows}")

    after = (REAL_LOG.stat().st_size, REAL_LOG.stat().st_mtime_ns) if REAL_LOG.exists() else None
    print()
    if before != after:
        failed += 1
        print(f"FAIL  REAL LOG TOUCHED: {before} -> {after}")
    else:
        print(f"ok    real log untouched (size/mtime identical: {before[0] if before else 'log absent'} bytes)")

    print(f"\n{passed}/{passed + failed} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
