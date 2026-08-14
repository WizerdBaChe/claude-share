#!/usr/bin/env python3
"""share_gate.py — fail-closed pre-publish gate for this share repo.

Run before every push that touches shipped content:

    python tools/share_gate.py            # all checks, exit 1 on any finding
    python tools/share_gate.py --check P  # one check
    python tools/share_gate.py --seed     # print undeclared tokens/refs, write nothing

Why this exists
---------------
De-identification used to be specified verbally, per push. That produced two
opposite failure classes on the same repo, both invisible until an outside
adopter hit them:

  OVER-SCRUB  interop-layer/README.md had 23 real, harmless, repo-relative
              paths replaced by a single `<URL>` token — including inside the
              runnable-command fence, so the manual could no longer be
              followed. Six different files collapsed onto one token.
  UNDER-DECLARE
              20+ rule files cite `hooks/model_cap_guard.py`,
              `hooks/ops_health_nudge.py` and `settings.json` as the MECHANISM
              enforcing a rule, while the repo ships none of them. An adopter
              reads "mechanically enforced", gets prose, and cannot tell.
              MIGRATION-MAP.md's own invariant 4 ("降級要留痕") forbids exactly
              this, and nothing was checking.

Both are now machine-detected. Neither is a judgement call at push time.

Checks
------
  L  leak         personal data, credentials, absolute home paths, private IPs
  P  placeholder  closed vocabulary; no undeclared token; none in a command
  R  reference    every source-environment asset cited either resolves inside
                  this repo, or carries a disposition in share-manifest.toml
  S  structure    the packaging shapes that silently break on the adopter side

Exit codes: 0 clean · 1 findings · 2 the gate itself could not run.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sharelib import (REPO_ROOT, load_manifest, scan_text, allowed,  # noqa: E402
                      LEAK_PATTERNS)

TEXT_SUFFIXES = {".md", ".py", ".toml", ".json", ".txt", ".yml", ".yaml", ".cfg"}
SKILLS_ROOT = "skill-toolkit/skills"


# --- helpers -----------------------------------------------------------------

def git(*args):
    out = subprocess.run(["git", "-C", str(REPO_ROOT), *args],
                         capture_output=True, text=True)
    if out.returncode != 0:
        print(f"FATAL: git {' '.join(args)} failed:\n{out.stderr}")
        sys.exit(2)
    return out.stdout


def tracked_files():
    return [p for p in git("ls-files").splitlines() if p]


def read(rel):
    p = REPO_ROOT / rel
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def code_fence_lines(text):
    """1-indexed line numbers that sit inside a ``` fence."""
    inside, fenced = False, set()
    for i, line in enumerate(text.split("\n"), 1):
        if line.lstrip().startswith("```"):
            inside = not inside
            continue
        if inside:
            fenced.add(i)
    return fenced


class Findings:
    def __init__(self):
        self.items = []

    def add(self, check, rel, line, msg, fix):
        self.items.append((check, rel, line, msg, fix))

    def __bool__(self):
        return bool(self.items)


# --- L: leak -----------------------------------------------------------------

def check_leak(manifest, files, f):
    for rel in files:
        if Path(rel).suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = read(rel)
        if text is None:
            continue
        for _, kind, line, sample in scan_text(text, rel):
            if allowed(manifest, rel, kind, sample):
                continue
            f.add("L", rel, line, f"{kind}: {sample}",
                  "remove it, or add a reasoned [[allow]] entry")


# --- P: placeholder ----------------------------------------------------------

TOKEN_RE = re.compile(r"<[A-Za-z_][A-Za-z0-9 _./|-]*>")
# A line the reader is expected to run or copy verbatim.
COMMAND_RE = re.compile(
    r"^\s*(?:\$|>|#\s*)?(?:python[0-9.]*|py|git|cd|bash|sh|pwsh|powershell|"
    r"node|npm|npx|pip|uv|curl|grep|rg|find)\b")
STANDALONE_RE = re.compile(r"`(<[A-Za-z_][A-Za-z0-9 _./|-]*>)`")
COLLAPSE_LIMIT = 4


def check_placeholder(manifest, files, f):
    """Position, not vocabulary.

    Free prose templates (`<project name>`, `<title>`) are none of the gate's
    business — there are ~160 of them and a closed vocabulary would be pure
    churn. What killed interop-layer/README.md was WHERE the token sat, and
    how many distinct real values it had eaten. Three positional rules, each of
    which independently catches that incident:

      P1 path position     `~/.claude/interop/<URL>` — the token stands where a
                           resolvable path belongs
      P2 command position  `python .../<URL> build` — the reader cannot run the
                           line verbatim
      P3 collapse          the same standalone token used >=4 times in one file:
                           one placeholder wearing many different real values
    """
    ph = manifest.get("placeholders", {})
    substitution = set(ph.get("substitution", []))
    path_ok = set(ph.get("path_position_ok", [])) | substitution
    command_ok = set(ph.get("command_position_ok", []))

    for rel in files:
        if Path(rel).suffix.lower() != ".md":
            continue
        text = read(rel)
        if text is None:
            continue
        fenced = code_fence_lines(text)
        standalone = {}
        for i, line in enumerate(text.split("\n"), 1):
            if line.lstrip().startswith("<!--"):
                continue
            runnable = bool(COMMAND_RE.match(line))
            for m in TOKEN_RE.finditer(line):
                tok, a, b = m.group(0), m.start(), m.end()
                before, after = line[max(0, a - 1):a], line[b:b + 1]
                if (before == "/" or after == "/") and tok not in path_ok:
                    f.add("P", rel, i, f"{tok} sits in a path position",
                          "restore the real path, or declare the token under "
                          "[placeholders] path_position_ok with a reason")
                if runnable and tok not in command_ok:
                    f.add("P", rel, i,
                          f"{tok} on a line the reader is meant to run",
                          "a command that cannot be pasted verbatim is broken; "
                          "put the real value in the fence and explain the "
                          "substitution in prose above it")
        for tok in STANDALONE_RE.findall(text):
            standalone[tok] = standalone.get(tok, 0) + 1
        for tok, n in standalone.items():
            if n >= COLLAPSE_LIMIT and tok not in path_ok:
                f.add("P", rel, 0,
                      f"{tok} used as a standalone value {n}x in one file",
                      "one token standing for many distinct values is the "
                      "over-scrub signature; restore the real values")


# --- R: reference ------------------------------------------------------------

BACKTICK_RE = re.compile(r"`([^`\n]{2,120})`")
ASSET_RE = re.compile(r"^(?:~/\.claude/)?(?P<p>[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)*)$")
INTERESTING_SUFFIX = (".py", ".json", ".md", ".toml", ".sh", ".ps1")


def check_reference(manifest, files, f):
    source_map = manifest.get("source_map", {})
    foreign = tuple(manifest.get("foreign_roots", []))
    declared = {e["path"]: e for e in manifest.get("not_shipped", [])}
    tracked = set(files)

    for rel in files:
        if Path(rel).suffix.lower() != ".md":
            continue
        text = read(rel)
        if text is None:
            continue
        for i, line in enumerate(text.split("\n"), 1):
            for m in BACKTICK_RE.finditer(line):
                raw = m.group(1).strip()
                if raw.startswith(foreign) or "://" in raw or " " in raw:
                    continue
                if not raw.endswith(INTERESTING_SUFFIX):
                    continue
                am = ASSET_RE.match(raw.lstrip("./"))
                if not am:
                    continue
                key = raw[len("~/.claude/"):] if raw.startswith("~/.claude/") else raw
                if key in declared or _declared_under(key, declared):
                    continue
                if _resolves(key, source_map, tracked, rel):
                    continue
                # Only assets that CLAIM to be part of the source environment
                # are in scope; a bare word like `README.md` resolves locally
                # and anything else is prose about someone else's tree.
                if not _claims_source_env(raw, key, source_map,
                                          manifest.get("source_env_roots", [])):
                    continue
                f.add("R", rel, i, f"cites `{raw}`, which this repo does not ship",
                      "map it in [source_map], or add a [[not_shipped]] entry "
                      "with disposition + fallback")


def _resolves(key, source_map, tracked, citing_file):
    if key in tracked:
        return True
    for src, dst in source_map.items():
        if key.startswith(src) and (dst + key[len(src):]) in tracked:
            return True
    # relative to the citing file — a skill pointing at its own references/
    here = citing_file.rsplit("/", 1)[0] if "/" in citing_file else ""
    if here and f"{here}/{key}" in tracked:
        return True
    # a bare filename that exists anywhere in the tree (e.g. `README.md`)
    if "/" not in key and any(p.endswith("/" + key) or p == key for p in tracked):
        return True
    return False


def _declared_under(key, declared):
    """A directory-level disposition covers everything beneath it."""
    return any(d.endswith("/") and key.startswith(d) for d in declared)


def _claims_source_env(raw, key, source_map, source_env_roots):
    if raw.startswith("~/.claude/"):
        return True
    if any(key.startswith(src) for src in source_map):
        return True
    return any(key.startswith(r) for r in source_env_roots)


# --- S: structure ------------------------------------------------------------

FORBIDDEN_TRACKED = ("/.claude/", "__pycache__/", "/archive/")


def check_structure(manifest, files, f):
    tracked = set(files)

    # S1 — nothing that is personal-by-default may be tracked at all.
    for rel in files:
        probe = "/" + rel
        for bad in FORBIDDEN_TRACKED:
            if bad in probe:
                f.add("S", rel, 0, f"tracked path contains {bad}",
                      "untrack it; these are personal/history by default")

    # S2 — exactly one SKILL.md per skill, at the skill root.
    skills = sorted({p.split("/")[2] for p in files
                     if p.startswith(SKILLS_ROOT + "/") and len(p.split("/")) > 3})
    for name in skills:
        want = f"{SKILLS_ROOT}/{name}/SKILL.md"
        if want not in tracked:
            f.add("S", want, 0, "skill has no SKILL.md at its root",
                  "a loader that scans for SKILL.md will not see this skill")
    for rel in files:
        parts = rel.split("/")
        if rel.endswith("/SKILL.md") and rel.startswith(SKILLS_ROOT + "/") \
                and len(parts) != 4:
            f.add("S", rel, 0, "nested SKILL.md below the skill root",
                  "recursive loaders register it as a second skill; rename it")

    # S3 — a directory with no tracked file vanishes on clone.
    for d in sorted({str(p.relative_to(REPO_ROOT)).replace("\\", "/")
                     for p in REPO_ROOT.rglob("*") if p.is_dir()}):
        if d.startswith((".git", "archive")) or "__pycache__" in d:
            continue
        if any(p == d or p.startswith(d + "/") for p in tracked):
            continue
        if _ignored(d):
            continue
        f.add("S", d, 0, "directory holds no tracked file — absent after clone",
              "add its content, add a .gitkeep, or delete the directory")

    # S4 — the skill inventory table must match the tree.
    inv = read("skill-toolkit/README.md") or ""
    listed = set(re.findall(r"^\| `([a-z0-9-]+)` \|", inv, re.M))
    if listed and listed != set(skills):
        f.add("S", "skill-toolkit/README.md", 0,
              f"inventory table {sorted(listed ^ set(skills))} differs from the tree",
              "keep the table and skills/ in step")


def _ignored(rel):
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "check-ignore", "-q", rel],
                         capture_output=True)
    return out.returncode == 0


# --- seed --------------------------------------------------------------------

def seed(manifest, files):
    """Print what a human would need to declare. Writes nothing, ever."""
    ph = manifest.get("placeholders", {})
    known = set(ph.get("template", [])) | set(ph.get("substitution", []))
    tokens = {}
    for rel in files:
        if Path(rel).suffix.lower() != ".md":
            continue
        text = read(rel) or ""
        for tok in TOKEN_RE.findall(text):
            if tok not in known:
                tokens.setdefault(tok, set()).add(rel)
    print("# undeclared placeholder tokens (token -> files)")
    for tok, where in sorted(tokens.items(), key=lambda kv: -len(kv[1])):
        print(f'  "{tok}"  # {len(where)} file(s): {sorted(where)[0]}'
              + (" …" if len(where) > 1 else ""))
    print(f"\n{len(tokens)} undeclared token(s).")


# --- main --------------------------------------------------------------------

CHECKS = {"L": check_leak, "P": check_placeholder,
          "R": check_reference, "S": check_structure}
NAMES = {"L": "leak", "P": "placeholder", "R": "reference", "S": "structure"}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", default="LPRS",
                    help="subset of LPRS (default: all)")
    ap.add_argument("--seed", action="store_true",
                    help="print undeclared placeholders and exit; writes nothing")
    args = ap.parse_args()

    manifest = load_manifest()
    files = tracked_files()

    if args.seed:
        seed(manifest, files)
        return 0

    f = Findings()
    selected = [c for c in args.check.upper() if c in CHECKS]
    if not selected:
        print(f"FATAL: --check {args.check!r} selects nothing")
        return 2
    for c in selected:
        CHECKS[c](manifest, files, f)

    if not f:
        print(f"share gate CLEAN — {len(files)} tracked file(s), "
              f"checks {'+'.join(NAMES[c] for c in selected)}")
        return 0

    print(f"SHARE GATE FAILED — {len(f.items)} finding(s)\n")
    for check, rel, line, msg, fix in sorted(f.items):
        loc = f"{rel}:{line}" if line else rel
        print(f"  [{check}] {loc}\n      {msg}\n      → {fix}")
    print("\nNothing is auto-fixed on purpose: automatic scrubbing is what "
          "produced the damage this gate exists to catch.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
