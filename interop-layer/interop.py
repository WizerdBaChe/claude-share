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
        "profile": "light",
        "note": "global rules; overrides opencode's fallback to ~/.claude/CLAUDE.md",
    },
    "codex": {
        "path": Path.home() / ".codex" / "AGENTS.md",
        "profile": "full",
        "note": "codex global instructions (CODEX_HOME)",
        # USER RULING 2026-08-11: push sync to codex is OFF. That environment
        # cannot use this one's design wholesale (its ops tree lives at
        # ~/.codex/ops/codex-ops/ and its own 05-authority still specifies a
        # 4-section boundary contract against this side's 5), and the compiled
        # output was judged not good enough to overwrite a hand-tuned file.
        # Codex-side changes are made FROM codex, by hand. `build` will not
        # write here and `status` will not count it as drift.
        # To re-enable: delete this line and run `status` first -- the file
        # there is now foreign, so `build` would back it up and replace it.
        "disabled": "user ruling 2026-08-11 — maintained from the codex side",
    },
    "antigravity": {
        "path": Path.home() / ".gemini" / "AGENTS.md",
        "profile": "full",
        "note": "cross-tool global rules (Antigravity >=1.20.3; also read by Gemini CLI)",
        # USER RULING 2026-08-11: no longer used, sync removed. The entry stays
        # (not deleted) because the path + profile + cross-tool caveat are
        # verified facts worth keeping if this ever comes back.
        # LEFTOVERS at the target from the 2026-07-10 build, deliberately NOT
        # touched from here: ~/.gemini/AGENTS.md and ~/.gemini/interop-refs/
        # {design,judgment,phase-log}-protocol.md. They are another
        # environment's files; removing them is the user's call.
        "disabled": "user ruling 2026-08-11 — agent no longer used",
    },
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
# Nothing here hardcodes personal data — that would make THIS file the leak.
# The account name is read from the running environment instead.
_USER = Path.home().name

LEAK_PATTERNS = [
    ("email address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("API key (prefixed)", re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{16,}"
        r"|AKIA[0-9A-Z]{12,}|xox[baprs]-[A-Za-z0-9-]{10,})")),
    ("secret-shaped assignment", re.compile(
        r"(?i)\b(?:api[_-]?key|secret|password|passwd|token|bearer)\b"
        r"\s*[:=]\s*['\"]?[A-Za-z0-9_\-/+]{16,}")),
    # >=32 hex avoids matching git short hashes, which the source stamp needs.
    ("hash / long hex", re.compile(r"\b[0-9a-fA-F]{32,}\b")),
    ("account name in a path", re.compile(
        r"(?i)(?:[A-Z]:[\\/]+Users[\\/]+|/home/|/c/Users/)" + re.escape(_USER)
        + r"\b")),
]


def scan_text(text, label):
    """Return [(label, kind, sample)] for anything that must not leave here."""
    hits = []
    for kind, rx in LEAK_PATTERNS:
        for m in rx.finditer(text):
            s = m.group(0)
            hits.append((label, kind, s[:12] + "…" if len(s) > 13 else s))
    return hits


def report_leaks(hits):
    print(f"LEAK CHECK FAILED — {len(hits)} finding(s); nothing was written.\n")
    for label, kind, sample in hits:
        print(f"  [{kind}] in {label}: {sample}")
    print("\nFix the source (interop/portable-core.md) or, for a false "
          "positive, narrow LEAK_PATTERNS — never bypass the gate.")


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
