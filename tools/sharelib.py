#!/usr/bin/env python3
"""sharelib.py — the one place this repo defines what must not be published.

Single source of truth for the leak patterns. Two callers:

  tools/share_gate.py        repo-wide pre-publish gate (every tracked file)
  interop-layer/interop.py   per-payload gate before writing a target AGENTS.md

Nothing here hardcodes personal data — that would make THIS file the leak.
The account name is read from the running environment instead.

Design invariants:
  - Fail closed. An unrecognised construct is a finding, not a pass. The only
    way past a finding is an explicit, reasoned entry in share-manifest.toml.
  - Patterns live here and only here. A second copy drifts; the 2026-08-12
    `~/.agents/skills/` incident is the standing evidence for that.
  - Positive detection only. The gate never edits a file — over-eager
    automatic scrubbing is what produced the `<URL>` damage this module exists
    to prevent (see PLACEHOLDER checks in share_gate.py).
"""

import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = Path(__file__).resolve().parent / "share-manifest.toml"

_USER = Path.home().name

# --- leak patterns -----------------------------------------------------------
# Kept in the order they were proven (interop.py, verified 2026-08-11 by
# planting one secret of each class inside a real block: 6/6 aborted).
# Entries 7-8 are repo-scope additions: interop.py only ever saw text it had
# just assembled, so it did not need to care about someone ELSE's home path.

LEAK_PATTERNS = [
    # The TLD must be alphabetic: `three@0.185.1` is an npm specifier, not an
    # address, and it appears legitimately in version tables.
    ("email address", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    # 2026-08-16: `sk_live_`/`sk_test_` and `AIza` added. They were in the
    # SOURCE environment's own copy of this list (interop.py, before that file
    # was refactored to import from here) and were dropped on the way in — so
    # for the whole life of this gate a Stripe-shaped or Google API key would
    # have published cleanly. Found by running interop-layer/test_interop.py,
    # whose known-TRUE calibration set names both, against this module. That is
    # the argument for two-sided calibration stated in the repo's own rules,
    # working: a one-sided gate cannot report what it never looks for.
    ("API key (prefixed)", re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{16,}|sk_(?:live|test)_[A-Za-z0-9]{10,}"
        r"|gh[pousr]_[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_-]{30,}"
        r"|AKIA[0-9A-Z]{12,}|xox[baprs]-[A-Za-z0-9-]{10,})")),
    ("secret-shaped assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|passwd|token|bearer)\b"
        r"\s*[:=]\s*['\"]?[A-Za-z0-9_\-/+]{16,}")),
    # >=32 hex avoids matching git short hashes, which the source stamp needs.
    ("hash / long hex", re.compile(r"\b[0-9a-fA-F]{32,}\b")),
    ("account name in a path", re.compile(
        r"(?i)(?:[A-Z]:[\\/]+Users[\\/]+|/home/|/c/Users/)" + re.escape(_USER)
        + r"\b")),
    # Repo scope: ANY named home directory, not just this machine's account.
    # A share copied from a colleague's tree leaks their name just as well.
    ("absolute home path (any account)", re.compile(
        r"(?i)(?:[A-Z]:[\\/]+Users[\\/]+|/home/|/Users/|/c/Users/)"
        r"(?!<)[A-Za-z][A-Za-z0-9._-]{1,}")),
    ("private network host", re.compile(
        r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b")),
    # 2026-08-16. The blind spot that let nine private paths through a refresh,
    # plus three that had been published since long before it. The two patterns
    # above only know about HOME directories, so a second-drive tree — a private
    # asset library, real project roots, the operator's own publication root —
    # scanned clean while being exactly what hard rule 2 of
    # tools/COLLECTION-RULES.md calls a scrub target: "a pointer to a private asset
    # the reader cannot open". Found by grepping the refreshed tree by hand, which
    # is the argument for encoding it: the next refresh will not have that reader.
    # (No example is spelled out in this comment on purpose — writing one would
    # make this module a finding under its own pattern.)
    # System roots are excluded because they resolve identically on every Windows
    # machine and carry no information about this one; `Users` is excluded because
    # the two home-path patterns above already own it and would double-report.
    ("absolute local path (non-system drive)", re.compile(
        r"\b[A-Za-z]:[\\/]{1,2}"
        r"(?!(?:Users|Windows|Program Files|Program Files \(x86\)|ProgramData|"
        r"Temp|tmp|Python[0-9]*)\b)"
        r"(?!<)[A-Za-z0-9_][A-Za-z0-9 _.+-]*")),
]


def scan_text(text, label):
    """Return [(label, kind, line_no, sample)] for anything that must not ship."""
    hits = []
    for kind, rx in LEAK_PATTERNS:
        for m in rx.finditer(text):
            s = m.group(0)
            line_no = text.count("\n", 0, m.start()) + 1
            hits.append((label, kind, line_no,
                         s[:24] + "…" if len(s) > 25 else s))
    return hits


def report_leaks(hits, source_hint="the source file"):
    print(f"LEAK CHECK FAILED — {len(hits)} finding(s); nothing was written.\n")
    for label, kind, line_no, sample in hits:
        print(f"  [{kind}] {label}:{line_no}: {sample}")
    print(f"\nFix {source_hint}. For a genuine false positive, add a reasoned "
          f"[[allow]] entry to {MANIFEST.name} — never widen or bypass the "
          f"patterns themselves.")


# --- manifest ----------------------------------------------------------------

def load_manifest(path=None):
    """Read share-manifest.toml. Absent manifest is a hard error, not a skip:
    a missing declaration file must not read as 'nothing to declare'."""
    p = Path(path) if path else MANIFEST
    if not p.exists():
        print(f"FATAL: {p} is missing. The gate declares its exceptions there; "
              f"running without it would silently pass everything.")
        sys.exit(2)
    with p.open("rb") as fh:
        return tomllib.load(fh)


def allowed(manifest, rel_path, kind, sample):
    """True when an [[allow]] entry covers this finding.

    Matching is deliberately narrow: file AND kind must both match, and the
    entry must carry a non-empty reason. A wildcard file is not accepted.
    """
    for entry in manifest.get("allow", []):
        if entry.get("file") != rel_path:
            continue
        if entry.get("kind") != kind:
            continue
        if not entry.get("reason"):
            continue
        needle = entry.get("match")
        if needle and needle not in sample:
            continue
        return True
    return False
