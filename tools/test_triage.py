#!/usr/bin/env python3
"""test_triage.py — one case per bucket and per precedence edge of triage.py.

    python tools/test_triage.py

Evidence rung (global-claude-md/rules/verification-ladder.md): rung 1 over the
classifier's BRANCH table — every bucket in `triage.ORDER` and every place two
branches compete for one path has a case, and the suite asserts the bucket
list itself so a new branch cannot land untested. Over paths it is rung 0:
the paths are examples. That split is honest for a sorter whose domain is
"any path" but whose decisions are a finite table.

Three of the cases are the ones a sorter gets wrong silently, and each names
the damage:
  collected-beats-directory  archdiag is collected from under the excluded
                             `tools/` tree; calling it `recheck` would run the
                             wrong procedure over a shipped file
  segment-boundary           `skills/asset-vault` must not swallow
                             `skills/asset-vault-extra/` — a prefix match
                             would hide a new skill behind an old verdict
  archive-is-a-directory     `archived-notes.md` is a file name, not an
                             `archive/` segment, so it stays a candidate
Positive control: the last case mutates the classifier (drops the collected
branch) and asserts the collected-beats-directory case then FAILS — a suite
that cannot see its own branch removed is not measuring that branch.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triage  # noqa: E402

MANIFEST = {
    "collected": [
        {"path": "architecture-diagramming/archdiag/emit.mjs",
         "source": "~/.claude/tools/archdiag/emit.mjs"},
        {"path": "hooks/a.py", "source": "~/.claude/hooks/a.py"},
        {"path": "hooks/gone.py", "source": "~/.claude/hooks/gone.py"},
        {"path": "claude-ops/ops/uat.md", "source": "~/.claude/ops/uat.md"},
    ],
    "not_shipped": [
        {"path": "tools/", "disposition": "excluded-by-decision"},
        {"path": "skills/asset-vault", "disposition": "excluded-by-decision"},
        {"path": "hooks/old_test.py", "disposition": "excluded-by-decision"},
    ],
}
COLLECTED, NOT_SHIPPED = triage.build_index(MANIFEST)
UNTRACKED = {"ops/new-untracked.md", "ops/uat.md"}
DIRTY = {"hooks/a.py"}

# (name, rec, expected bucket, expected flags subset)
CASES = [
    ("refresh", {"path": "hooks/a.py", "status": "M"}, "refresh", {"dirty"}),
    ("refresh-untracked", {"path": "ops/uat.md", "status": "?"}, "refresh", {"untracked"}),
    ("collected-beats-directory", {"path": "tools/archdiag/emit.mjs", "status": "M"},
     "refresh", set()),
    ("source-gone", {"path": "hooks/gone.py", "status": "D"}, "source-gone", set()),
    ("never-root", {"path": "projects/x/memory/MEMORY.md", "status": "M"}, "never", set()),
    ("never-segment", {"path": "skills/p/archive/2026/x.md", "status": "A"}, "never", set()),
    ("never-skill-dotclaude", {"path": "skills/p/.claude/settings.json", "status": "A"},
     "never", set()),
    ("uncommitted", {"path": "ops/new-untracked.md", "status": "?"}, "uncommitted", set()),
    ("recheck-directory", {"path": "tools/new-tool/x.py", "status": "A"}, "recheck", set()),
    ("recheck-exact-prefix", {"path": "skills/asset-vault/SKILL.md", "status": "M"},
     "recheck", set()),
    ("segment-boundary", {"path": "skills/asset-vault-extra/SKILL.md", "status": "A"},
     "candidate", set()),
    ("archive-is-a-directory", {"path": "ops/archived-notes.md", "status": "A"},
     "candidate", set()),
    ("deleted", {"path": "rules/never-shipped.md", "status": "D"}, "deleted", set()),
    ("rename-flags-stale-entry",
     {"path": "hooks/tests/old_test.py", "status": "R", "old": "hooks/old_test.py"},
     "candidate", {"entry-names-old-path"}),
    ("candidate", {"path": "rules/brand-new.md", "status": "A"}, "candidate", set()),
]


def run(classify):
    bad = []
    for name, rec, bucket, flags in CASES:
        got = classify(rec, COLLECTED, NOT_SHIPPED, UNTRACKED, DIRTY)
        if got["bucket"] != bucket or not flags <= set(got["flags"]):
            bad.append(f"{name}: expected {bucket} {sorted(flags)}, "
                       f"got {got['bucket']} {got['flags']}")
    return bad


def main():
    failures = run(triage.classify)

    covered = {b for _, _, b, _ in CASES}
    missing = set(triage.ORDER) - covered
    if missing:
        failures.append(f"bucket(s) with no case: {sorted(missing)}")

    # positive control: remove the collected branch; its case must now fail
    def mutant(rec, collected, *rest):
        return triage.classify(rec, {}, *rest)
    mutant_bad = run(mutant)
    if not any(m.startswith("collected-beats-directory") for m in mutant_bad):
        failures.append("CONTROL: dropping the collected branch went unnoticed")

    for f in failures:
        print(f"  FAIL {f}")
    total = len(CASES) + 2
    print(f"{total - len(failures)}/{total} cases behaved as specified "
          f"({len(CASES)} branch cases, bucket coverage, 1 positive control)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
