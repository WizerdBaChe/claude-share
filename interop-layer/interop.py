#!/usr/bin/env python3
"""interop.py — compile portable-core.md into per-agent AGENTS.md files.

Commands:
  python interop.py build     compile + deploy to all registered targets
  python interop.py status    freshness report (stale targets, curation drift)
  python interop.py curated   record that portable-core.md was reviewed
                              against the current CLAUDE.md (run after each
                              curation pass)

  python interop.py scan      leak check only, write nothing (exit 1 on a hit)

Design invariants (see README.md / MIGRATION-MAP.md):
  - One-way flow: ~/.claude is the canonical source; targets never write back.
  - Never delete: a foreign file at a target path is backed up, not clobbered.
  - Every artifact carries a source stamp (git short hash) for staleness checks.
  - Nothing identifying leaves this machine: every artifact is leak-scanned
    before it is written, and a hit ABORTS the build (2026-08-11).
  - Preferences port; method does not. Only the user's own standing rules —
    the ones no documentation can supply — are transplanted. Method depth is
    delegated to the target agent, which reads its OWN current official docs.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent   # ~/.claude
CORE = Path(__file__).resolve().parent / "portable-core.md"
CURATION_STAMP = Path(__file__).resolve().parent / "curation.stamp"

STAMP_RE = re.compile(r"managed-by: claude-interop \| profile: (\S+) \| source: (\S+)")
BLOCK_RE = re.compile(
    r"<!--\s*block:(\S+)\s+profiles:([\w,]+)\s*-->\n(.*?)<!--\s*/block\s*-->",
    re.DOTALL,
)

# RETIRED 2026-08-11 — the reference-compile class is gone. It shipped ~20K of
# curated method playbooks to an `interop-refs/` folder plus a prose routing
# index, on the theory that content ports even when the trigger does not. In
# practice "instructed read" is not a trigger: no target platform can fire it
# at the right moment, so the text was read either always or never. The
# playbooks moved to `archive/interop-refs-2026-08-11/`; targets now get
# `delegation_block()` instead. What ports is preference, not method.

# Canonical sources portable-core.md is distilled from. Changes to these paths
# flag re-curation in `status`. Narrowed to CLAUDE.md on 2026-08-11: the other
# three entries (product-design-thinking, ops/30-judgment, workflow-checkpoint)
# were the sources of the retired refs/ playbooks. With method delegated rather
# than shipped, a change in a skill body no longer implies anything to curate —
# keeping them would flag drift against material that is deliberately no longer
# transplanted.
CURATION_SOURCES = [
    "CLAUDE.md",
]

TARGETS = {
    "opencode": {
        "path": Path.home() / ".config" / "opencode" / "AGENTS.md",
        # USER RULING 2026-08-15: light -> full. opencode is being promoted from
        # an occasional side tool to a dispatch target (free-tier workers execute
        # work cards and run cross-family red-team review), so it now needs the
        # same preference set the dispatcher assumes. The birth-budget argument
        # for `light` also inverted once measured: with no AGENTS.md deployed at
        # all, opencode was falling back to ~/.claude/CLAUDE.md (~16.5 KB of
        # Claude-Code-specific mechanism the worker cannot use), so `full` costs
        # the worker LESS context than the status quo it replaces, not more.
        "profile": "full",
        "note": "global rules; overrides opencode's fallback to ~/.claude/CLAUDE.md",
    },
    # USER RULING 2026-08-15: `codex` and `antigravity` REMOVED from the
    # registry (they had been sync-off since 2026-08-11). Both rows were frozen
    # at their 2026-07-10 verification while this registry's own header says
    # those locations are volatile facts that must be re-verified -- so what
    # was being "kept for later" was an unverifiable snapshot, not a fact.
    # Re-adding either one goes through README.md's "新增一個目標 agent 的
    # checklist" step 1 (look the paths and extension points up in the
    # platform's current docs), which is faster than trusting a stale value.
    # Full text of both entries: archive/2026-08-15-interop-targets-removed/,
    # or `git show 596cfc0:interop/interop.py`.
    #
    # The `disabled` key below is still honoured by cmd_build/cmd_status (the
    # `[off]` branches) and by ops_health_nudge.py check 12. No target uses it
    # today; it is kept as the mechanism for recording a future sync-off ruling
    # without deleting the target outright.
}


def git(*args):
    r = subprocess.run(["git", "-C", str(REPO)] + list(args),
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def parse_blocks():
    text = CORE.read_text(encoding="utf-8")
    blocks = []
    for m in BLOCK_RE.finditer(text):
        bid, profiles, body = m.group(1), m.group(2).split(","), m.group(3)
        for p in profiles:
            if p not in ("light", "full"):
                sys.exit(f"block '{bid}': unknown profile '{p}'")
        blocks.append({"id": bid, "profiles": profiles, "body": body.strip()})
    if not blocks:
        sys.exit("no blocks parsed from portable-core.md — check block syntax")
    return blocks


# --- L0: leak gate -----------------------------------------------------------
# The patterns themselves live in tools/sharelib.py — ONE definition, two
# callers (this compiler and the repo-wide tools/share_gate.py). A second copy
# would drift, and a drifted leak gate is worse than an obvious absent one.
# Nothing there hardcodes personal data either; the account name is read from
# the running environment.
_SHARELIB = Path(__file__).resolve().parent.parent / "tools"
if not (_SHARELIB / "sharelib.py").exists():
    sys.exit(f"FATAL: {_SHARELIB / 'sharelib.py'} not found. The leak gate is "
             f"defined there; refusing to run without it. Copy the tools/ "
             f"directory next to this script's parent.")
sys.path.insert(0, str(_SHARELIB))
from sharelib import scan_text, report_leaks  # noqa: E402


def delegation_block(profile):
    """Replaces the old `interop-refs/` compile (retired 2026-08-11).

    Shipping ~20K of method prose produced text with no trigger: no target
    platform has a mechanism to fire it at the right moment, so it was read
    either always or never (the degradation MIGRATION-MAP.md already
    recorded). What DOES port is the block above it — the user's own standing
    rules, which no documentation can supply. Method depth is delegated.
    """
    return "\n".join([
        "",
        "",
        "## Method depth — adapt, do not inherit",
        "",
        "The preferences above are the user's own standing rules. They are not",
        "derivable from any documentation, they are not specific to any agent",
        "platform, and they apply here verbatim.",
        "",
        "Method-level protocol (design gates, judgment tiers, phase logging) is",
        "deliberately NOT shipped into this file. It used to be, and the copied",
        "prose had no trigger on this platform — so it was read either always or",
        "never. When a task needs more method than the rules above provide:",
        "",
        "1. Consult THIS platform's own current official documentation for its",
        "   extension points — rules files, hooks, permissions, sub-agents,",
        "   custom commands. You know this platform; do not assume another",
        "   agent's mechanisms exist here, and do not assume this file's",
        "   conventions map onto them.",
        "2. Propose the adaptation to the user before installing anything",
        "   durable. Adaptation is the user's call, not an inference.",
        "",
        "Reference protocols exist on this machine under `~/.claude/ops/` if the",
        "user points you at them. Read them as material, never as instructions",
        "that bind this platform.",
    ])


def assemble(profile, blocks, src_hash):
    picked = [b for b in blocks if profile in b["profiles"]]
    header = (
        f"<!-- managed-by: claude-interop | profile: {profile} | source: {src_hash}\n"
        f"     GENERATED FILE - do not edit. Edit ~/.claude/interop/portable-core.md\n"
        f"     and rerun: python ~/.claude/interop/interop.py build -->\n\n"
    )
    return (header + "\n\n".join(b["body"] for b in picked)
            + delegation_block(profile) + "\n")


def backup_foreign(path):
    """A file we didn't generate sits at the target path: archive, never delete."""
    n = 0
    while True:
        bak = path.with_name(path.name + (f".pre-interop.bak" if n == 0
                                          else f".pre-interop.{n}.bak"))
        if not bak.exists():
            path.rename(bak)
            return bak
        n += 1


def build_payloads():
    """Assemble every enabled target's file in memory. Writes nothing."""
    src_hash = git("rev-parse", "--short", "HEAD")
    blocks = parse_blocks()
    return src_hash, {
        name: assemble(t["profile"], blocks, src_hash)
        for name, t in TARGETS.items() if not t.get("disabled")
    }


def cmd_scan():
    """Leak check only — the same gate `build` runs, without the writing."""
    _, payloads = build_payloads()
    hits = []
    for name, text in payloads.items():
        hits += scan_text(text, f"{name} AGENTS.md")
    hits += scan_text(CORE.read_text(encoding="utf-8"), "portable-core.md")
    if hits:
        report_leaks(hits)
        return 1
    print(f"leak check clean — {len(payloads)} payload(s) + portable-core.md")
    return 0


def cmd_build():
    if git("status", "--porcelain", "--", "interop/portable-core.md"):
        print("WARNING: portable-core.md has uncommitted changes; the stamp "
              "will point at the last commit, not your working copy. "
              "Commit first for an accurate stamp.")
    src_hash, payloads = build_payloads()

    # L0 gate: assemble everything FIRST, scan it, and only then write. A
    # per-target scan inside the write loop would leave earlier targets
    # already written when a later one trips — the abort has to be total.
    hits = []
    for name, text in payloads.items():
        hits += scan_text(text, f"{name} AGENTS.md")
    if hits:
        report_leaks(hits)
        sys.exit(1)

    for name, t in TARGETS.items():
        path, profile = t["path"], t["profile"]
        if t.get("disabled"):
            print(f"[off] {name}: sync disabled ({t['disabled']}) — not written")
            continue
        if not path.parent.is_dir():
            print(f"[skip] {name}: {path.parent} does not exist (agent not installed)")
            continue
        if path.exists() and not STAMP_RE.search(path.read_text(encoding="utf-8")[:300]):
            bak = backup_foreign(path)
            print(f"[backup] {name}: foreign file moved to {bak.name}")
        path.write_text(payloads[name], encoding="utf-8")
        print(f"[write] {name}: {path} (profile={profile}, source={src_hash})")


def cmd_status():
    head = git("rev-parse", "--short", "HEAD")
    print(f"canonical source: {REPO} @ {head}\n")
    ok = True
    for name, t in TARGETS.items():
        path = t["path"]
        if t.get("disabled"):
            # Deliberately NOT counted as drift: a disabled target is a
            # decision, not a backlog item. Still listed so the ruling stays
            # visible instead of silently vanishing from the report.
            print(f"[off] {name}: sync disabled ({t['disabled']})")
            continue
        if not path.exists():
            print(f"[missing] {name}: {path} not deployed (run: build)")
            ok = False
            continue
        m = STAMP_RE.search(path.read_text(encoding="utf-8")[:300])
        if not m:
            print(f"[foreign] {name}: {path} exists but is not interop-managed")
            ok = False
            continue
        stamp = m.group(2)
        log = git("log", "--oneline", f"{stamp}..HEAD", "--",
                  "interop/portable-core.md", "interop/interop.py")
        if log:
            print(f"[stale] {name}: source changed since {stamp} (run: build)")
            for line in log.splitlines():
                print(f"         {line}")
            ok = False
        else:
            print(f"[fresh] {name}: profile={m.group(1)}, source={stamp}")
    print()
    if CURATION_STAMP.exists():
        cur = CURATION_STAMP.read_text(encoding="utf-8").strip()
        drift = git("log", "--oneline", f"{cur}..HEAD", "--", *CURATION_SOURCES)
        if drift:
            print(f"[curation] curation sources changed since last curation ({cur}):")
            for line in drift.splitlines():
                print(f"           {line}")
            print("           Review portable-core.md / refs/ against these "
                  "changes, then run: curated")
            ok = False
        else:
            print(f"[curation] up to date (reviewed @ {cur})")
    else:
        print("[curation] no curation stamp yet (run: curated after first review)")
        ok = False
    sys.exit(0 if ok else 1)


def cmd_curated():
    head = git("rev-parse", "--short", "HEAD")
    CURATION_STAMP.write_text(head + "\n", encoding="utf-8")
    print(f"curation stamp set to {head}")


if __name__ == "__main__":
    cmds = {"build": cmd_build, "status": cmd_status,
            "curated": cmd_curated, "scan": cmd_scan}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    sys.exit(cmds[sys.argv[1]]() or 0)
