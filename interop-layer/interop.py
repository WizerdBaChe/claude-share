#!/usr/bin/env python3
"""interop.py — compile portable-core.md into per-agent AGENTS.md files.

Commands:
  python interop.py build     compile + deploy to all registered targets
  python interop.py status    freshness report (stale targets, curation drift)
  python interop.py curated   record that portable-core.md was reviewed
                              against the current CLAUDE.md (run after each
                              curation pass)

Design invariants (see README.md / MIGRATION-MAP.md):
  - One-way flow: ~/.claude is the canonical source; targets never write back.
  - Never delete: a foreign file at a target path is backed up, not clobbered.
  - Every artifact carries a source stamp (git short hash) for staleness checks.
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
    },
    "antigravity": {
        "path": Path.home() / ".gemini" / "AGENTS.md",
        "profile": "full",
        "note": "cross-tool global rules (Antigravity >=1.20.3; also read by Gemini CLI)",
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


def assemble(profile, blocks, src_hash):
    picked = [b for b in blocks if profile in b["profiles"]]
    header = (
        f"<!-- managed-by: claude-interop | profile: {profile} | source: {src_hash}\n"
        f"     GENERATED FILE - do not edit. Edit ~/.claude/interop/portable-core.md\n"
        f"     and rerun: python ~/.claude/interop/interop.py build -->\n\n"
    )
    return header + "\n\n".join(b["body"] for b in picked) + "\n"


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


def cmd_build():
    if git("status", "--porcelain", "--", "interop/portable-core.md"):
        print("WARNING: portable-core.md has uncommitted changes; the stamp "
              "will point at the last commit, not your working copy. "
              "Commit first for an accurate stamp.")
    src_hash = git("rev-parse", "--short", "HEAD")
    blocks = parse_blocks()
    for name, t in TARGETS.items():
        path, profile = t["path"], t["profile"]
        if not path.parent.is_dir():
            print(f"[skip] {name}: {path.parent} does not exist (agent not installed)")
            continue
        if path.exists() and not STAMP_RE.search(path.read_text(encoding="utf-8")[:300]):
            bak = backup_foreign(path)
            print(f"[backup] {name}: foreign file moved to {bak.name}")
        path.write_text(assemble(profile, blocks, src_hash), encoding="utf-8")
        print(f"[write] {name}: {path} (profile={profile}, source={src_hash})")


def cmd_status():
    head = git("rev-parse", "--short", "HEAD")
    print(f"canonical source: {REPO} @ {head}\n")
    ok = True
    for name, t in TARGETS.items():
        path = t["path"]
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
        drift = git("log", "--oneline", f"{cur}..HEAD", "--", "CLAUDE.md")
        if drift:
            print(f"[curation] CLAUDE.md changed since last curation ({cur}):")
            for line in drift.splitlines():
                print(f"           {line}")
            print("           Review portable-core.md against these changes, "
                  "then run: curated")
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
    cmds = {"build": cmd_build, "status": cmd_status, "curated": cmd_curated}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]]()
