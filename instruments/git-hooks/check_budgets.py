r"""pre-commit check: refuse a commit that GROWS an always-loaded rule file past its budget.

The budgets already exist and already fire -- hooks/ops_health_nudge.py reads
CLAUDE.md against CLAUDE_MD_CAP (unconditional every-session cost) and each
ops/*.md against SIZE_CAP (review trigger) at every SessionStart. What they
could not do is fire AT THE EDIT: three times (2026-09-23 Codex-tier bullet,
2026-10-03 fetchsrc paragraph, 2026-10-06 vault ruling) a rule-tier edit pushed
a file over its cap and the breach was discovered one or more sessions later as
a standing HMI alarm, after the editing session had closed (feedback pool,
rule:ops/20-dispatch.md, proposal "edit-time size check for ops/*.md"). This
repo commits every landing, so the commit is the edit-time event a check can sit
on.

What it rules on: for every STAGED CLAUDE.md and top-level ops/*.md (the same
set and the same exempt list the nudge judges -- caps and exemptions are read
from the nudge's source so there is one declaration), the staged blob's byte
size. Refused (exit 1) only when the blob is OVER its cap AND LARGER than the
HEAD version: a commit that shrinks an over-cap file, or leaves it unchanged,
always passes, so the gate can never block the extraction that fixes a breach.
What it does not rule on: a file whose cap cannot be read, a path git cannot
show, any failure of its own -> a notice on stderr, exit 0 (it rules only on
what it can determine).

Fix for a hit: the nudge's own remedy, repeated in the refusal -- CLAUDE.md:
merge into an existing conditional bullet or move the rule to a rules/ file or
a skill; ops/*.md: extract the concrete (examples, command blocks, cases) to
ops/references/ behind a pointer. Never compress a rule to fit. A deliberate
checkpoint that must land over cap is the user's call: `git commit --no-verify`.

Wired by: tools/git-hooks/pre-commit (core.hooksPath tools/git-hooks).
Calibrated 2026-10-06 in a throwaway repo (see ops/rule-registry.md, key
`rule-file budget gate`): R1 CLAUDE.md grown over cap -> refused; R2 ops file
grown over cap -> refused; P1 over-cap file shrunk -> passes; P2 over-cap file
untouched -> passes; P3 exempt ops file grown -> passes; P4 under-cap growth ->
passes; P5 caps unreadable -> notice, passes.
review-when: the nudge renames CLAUDE_MD_CAP / SIZE_CAP / SIZE_CAP_EXEMPT or
starts judging ops/ recursively (then the regexes and the path filter here must
follow); core.hooksPath changes.
"""
import os
import re
import subprocess
import sys

NUDGE_REL = os.path.join("hooks", "ops_health_nudge.py")


def read_caps(top):
    """(claude_md_cap, ops_cap, exempt_basenames) from the nudge's constants, or None."""
    src = open(os.path.join(top, NUDGE_REL), encoding="utf-8").read()
    m1 = re.search(r"(?m)^CLAUDE_MD_CAP\s*=\s*(\d+)", src)
    m2 = re.search(r"(?m)^SIZE_CAP\s*=\s*(\d+)\s*\*\s*1024", src)
    m3 = re.search(r"(?m)^SIZE_CAP_EXEMPT\s*=\s*\{([^}]*)\}", src)
    if not (m1 and m2 and m3):
        return None
    exempt = set(re.findall(r"\"([^\"]+)\"", m3.group(1)))
    return int(m1.group(1)), int(m2.group(1)) * 1024, exempt


def staged_paths():
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
        capture_output=True, check=True,
    ).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def blob_size(ref, path):
    """Byte size of <ref>:<path>, or 0 when it does not exist there."""
    r = subprocess.run(["git", "cat-file", "-s", f"{ref}:{path}"], capture_output=True)
    return int(r.stdout.decode().strip()) if r.returncode == 0 else 0


def judge(paths, caps):
    """[(path, staged, head, cap, remedy)] for every refused path."""
    claude_cap, ops_cap, exempt = caps
    hits = []
    for p in paths:
        if p == "CLAUDE.md":
            cap, remedy = claude_cap, (
                "UNCONDITIONAL every-session budget: MERGE into an existing conditional "
                "bullet, or move the rule to a rules/ path-scoped file or a skill; never "
                "append, never compress a rule to fit (ops/40-maintenance.md S3)")
        elif re.fullmatch(r"ops/[^/]+\.md", p) and os.path.basename(p) not in exempt:
            cap, remedy = ops_cap, (
                "EXTRACT the concrete (examples, command blocks, cases) to ops/references/ "
                "behind a pointer; keep rule + conditions + routing in place; never "
                "compress a rule to fit (ops/40-maintenance.md S3)")
        else:
            continue
        staged, head = blob_size("", p), blob_size("HEAD", p)
        if staged > cap and staged > head:
            hits.append((p, staged, head, cap, remedy))
    return hits


def main():
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                             check=True).stdout.decode().strip()
        caps = read_caps(top)
        paths = staged_paths()
    except Exception as e:  # cannot determine -> do not veto
        print(f"pre-commit budget check skipped: {e}", file=sys.stderr)
        return 0
    if caps is None:
        print(f"pre-commit budget check skipped: caps not found in {NUDGE_REL}", file=sys.stderr)
        return 0
    try:
        hits = judge(paths, caps)
    except Exception as e:
        print(f"pre-commit budget check skipped: {e}", file=sys.stderr)
        return 0
    for p, staged, head, cap, remedy in hits:
        print(f"{p}: staged {staged} B > cap {cap} B and grew from {head} B -- {remedy}",
              file=sys.stderr)
    if hits:
        print(f"commit refused: {len(hits)} rule file(s) grown past budget. Extract or "
              "relocate, re-stage, commit again (a commit that SHRINKS the file always "
              "passes).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
