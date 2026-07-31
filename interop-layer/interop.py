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
REFS_DIR = Path(__file__).resolve().parent / "refs"
CURATION_STAMP = Path(__file__).resolve().parent / "curation.stamp"

STAMP_RE = re.compile(r"managed-by: claude-interop \| profile: (\S+) \| source: (\S+)")
BLOCK_RE = re.compile(
    r"<!--\s*block:(\S+)\s+profiles:([\w,]+)\s*-->\n(.*?)<!--\s*/block\s*-->",
    re.DOTALL,
)

# Reference-compile class (MIGRATION-MAP.md): curated method playbooks whose
# CONTENT ports but whose triggering mechanism does not. Deployed to an
# `interop-refs/` folder next to each target's AGENTS.md; a prose routing
# index is appended to the generated AGENTS.md (degradation: mechanical
# trigger -> instructed read). Profile-gated like blocks; keep this registry
# small (birth budget) — every entry is context rent at the target.
REFS = {
    "design-protocol": {
        "profiles": ["full"],
        "route": "BEFORE designing a new product, new tool/utility, or a "
                 "complex feature whose approach is undecided",
    },
    "judgment-protocol": {
        "profiles": ["full"],
        "route": "when producing a design/plan/evaluation deliverable, or a "
                 "hard-to-reverse decision, or the user explicitly asks for "
                 "depth",
    },
    "phase-log-protocol": {
        "profiles": ["full"],
        "route": "when a project phase/milestone completes, or the user says "
                 "'continue / recap project X' in a fresh session",
    },
}

# Canonical sources each ref is distilled from (repo-relative). Changes to
# these paths flag re-curation in `status`, same loop as CLAUDE.md ->
# portable-core.md.
CURATION_SOURCES = [
    "CLAUDE.md",
    "skills/product-design-thinking/SKILL.md",
    "ops/30-judgment.md",
    "skills/workflow-checkpoint/SKILL.md",
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


def refs_for(profile):
    return {n: r for n, r in REFS.items() if profile in r["profiles"]}


def routing_index(profile):
    """Prose routing block appended to AGENTS.md — the degraded substitute
    for mechanical skill triggering (loss recorded in MIGRATION-MAP.md)."""
    picked = refs_for(profile)
    if not picked:
        return ""
    lines = [
        "\n\n## Deep-method playbooks (read on trigger, not preloaded)",
        "",
        "The `interop-refs/` folder next to this file holds full method",
        "playbooks. When a situation below arises, READ the named file",
        "BEFORE starting the work — do not improvise the methodology from",
        "these one-line summaries.",
        "",
    ]
    for name, r in sorted(picked.items()):
        lines.append(f"- `interop-refs/{name}.md` — {r['route']}.")
    return "\n".join(lines)


def assemble(profile, blocks, src_hash):
    picked = [b for b in blocks if profile in b["profiles"]]
    header = (
        f"<!-- managed-by: claude-interop | profile: {profile} | source: {src_hash}\n"
        f"     GENERATED FILE - do not edit. Edit ~/.claude/interop/portable-core.md\n"
        f"     and rerun: python ~/.claude/interop/interop.py build -->\n\n"
    )
    return (header + "\n\n".join(b["body"] for b in picked)
            + routing_index(profile) + "\n")


def assemble_ref(name, profile, src_hash):
    src = REFS_DIR / f"{name}.md"
    if not src.is_file():
        sys.exit(f"ref '{name}' registered but {src} does not exist")
    header = (
        f"<!-- managed-by: claude-interop | profile: {profile} | source: {src_hash}\n"
        f"     GENERATED FILE - do not edit. Edit ~/.claude/interop/refs/{name}.md\n"
        f"     and rerun: python ~/.claude/interop/interop.py build -->\n\n"
    )
    return header + src.read_text(encoding="utf-8")


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
    if git("status", "--porcelain", "--", "interop/portable-core.md", "interop/refs"):
        print("WARNING: portable-core.md or refs/ has uncommitted changes; the "
              "stamp will point at the last commit, not your working copy. "
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
        refs_dir = path.parent / "interop-refs"
        for ref_name in refs_for(profile):
            ref_path = refs_dir / f"{ref_name}.md"
            refs_dir.mkdir(exist_ok=True)
            if (ref_path.exists()
                    and not STAMP_RE.search(ref_path.read_text(encoding="utf-8")[:300])):
                bak = backup_foreign(ref_path)
                print(f"[backup] {name}: foreign file moved to {bak.name}")
            ref_path.write_text(assemble_ref(ref_name, profile, src_hash),
                                encoding="utf-8")
            print(f"[write] {name}: {ref_path} (ref, source={src_hash})")


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
                  "interop/portable-core.md", "interop/interop.py",
                  "interop/refs")
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
    cmds = {"build": cmd_build, "status": cmd_status, "curated": cmd_curated}
    if len(sys.argv) != 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]]()
