#!/usr/bin/env python3
"""share_gate.py — fail-closed pre-publish gate for this share repo.

Run before every push that touches shipped content:

    python tools/share_gate.py                 # all repo-local checks, exit 1 on any finding
    python tools/share_gate.py --check P       # one check
    python tools/share_gate.py --source ~/.claude   # + check V, needs the source tree
    python tools/share_gate.py --seed          # print undeclared tokens/refs, write nothing

Anyone COLLECTING (rather than reading) must pass --source. That is the only
mode in which the gate can see whether a copy still matches what it claims;
tools/COLLECTION-RULES.md makes it step 6 of the procedure.

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
  C  collection   every file copied in from the source environment declares
                  where it came from and every edit made on the way
  D  dead         declarations that no longer match anything: a permission for
                  a finding that is gone, an absence for a file that now ships
  V  source-verify  (opt-in, --source) every collected file still matches what
                  its entry claims — the one thing C says it cannot do

Exit codes: 0 clean · 1 findings · 2 the gate itself could not run.
"""

import argparse
import json
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
    # `literal` is not a permission, it is a type correction: these tokens are
    # not placeholders standing for a value the reader supplies, they are names
    # that happen to be spelled inside angle brackets — a harness tag, an HTML
    # element quoted in prose. Declaring one under path_position_ok instead would
    # be recording a false claim ("a human confirmed the reader can fill it in")
    # to silence a finding, which is the shape of decay this gate exists to stop.
    literal = set(ph.get("literal", []))
    path_ok = set(ph.get("path_position_ok", [])) | substitution | literal
    command_ok = set(ph.get("command_position_ok", [])) | literal

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
    # Suffix match anywhere in the tree. Rule files cite a skill's own
    # `references/x.md` relative to a directory the citing file is not in, so
    # an exact-prefix rule reports those as missing when they are right there.
    # Deliberately loose: the failure worth catching is "nothing by this name
    # exists anywhere", not "it resolved via a different parent".
    if any(p.endswith("/" + key) or p == key for p in tracked):
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

    # S5 — the mounting template must mount exactly the hooks that ship.
    #
    # Added 2026-08-16 after the template was found mounting 7 hooks while 9
    # shipped. Nothing was broken and nothing was leaked: the two newest hooks
    # simply arrived with no way to turn them on, which reads to an adopter as
    # "these are optional" rather than "this file is out of date". The failure
    # is symmetrical and both halves matter — a hook with no mount is dead
    # weight, and a mount with no hook is `hooks/settings.example.json`'s own
    # stated worst case ("a mount pointing at a missing file is worse than an
    # absent mount"). Deliberate omissions are not silent: they go in the
    # template's `_README` and in a [[not_shipped]] entry, which is also why
    # this check reads the tree rather than a list it could drift from.
    tmpl = read("hooks/settings.example.json")
    if tmpl is not None:
        # Parse, do not grep. The first version of this check grepped the whole
        # file and reported ops_health_nudge.py as mounted twice — the second
        # "mount" was the _README line telling the reader how to smoke-test it
        # by hand. A check that cannot tell a mount from a sentence about a
        # mount is measuring the wrong thing, and its first output was a false
        # positive about the file it was written to protect.
        try:
            sites = [(event, b.get("matcher", ""),
                      h.get("command", "").replace("\\", "/")
                       .rsplit("/", 1)[-1].strip('"'))
                     for event, blocks in json.loads(tmpl).get("hooks", {}).items()
                     for b in blocks for h in b.get("hooks", [])]
            mounted = [name for _, _, name in sites]
        except (json.JSONDecodeError, AttributeError) as exc:
            f.add("S", "hooks/settings.example.json", 0,
                  f"does not parse as the settings shape: {exc}",
                  "an adopter merges this file into their own settings.json; "
                  "it has to be valid first")
            mounted = []
        mounted = [m for m in mounted if m.endswith(".py")]
        shipped = {p.split("/")[-1] for p in files
                   if p.startswith("hooks/") and p.endswith(".py")}
        for name in sorted(shipped - set(mounted)):
            f.add("S", "hooks/settings.example.json", 0,
                  f"{name} ships but is not mounted",
                  "add its block, or say in _README why it is deliberately unmounted")
        for name in sorted(set(mounted) - shipped):
            f.add("S", "hooks/settings.example.json", 0,
                  f"mounts {name}, which this repo does not ship",
                  "remove the block; a mount pointing at a missing file is worse "
                  "than an absent mount")
        # A duplicate is the same hook on the same (event, matcher) — NOT the
        # same hook twice. Corrected 2026-08-16, hours after this check shipped:
        # the source turned ui_verify_guard.py into a PreToolUse/PostToolUse
        # router, which is two mounts of one file and entirely correct, and the
        # first version of this rule would have reported the correct wiring as a
        # defect. A check that fires on the fix is worse than no check.
        for site in sorted({s for s in sites if sites.count(s) > 1}):
            f.add("S", "hooks/settings.example.json", 0,
                  f"{site[2]} is mounted twice on {site[0]} matcher {site[1]!r}",
                  "one mount per hook per event+matcher; a true duplicate runs "
                  "the hook twice for the same call")


# --- C: collection -----------------------------------------------------------

VALID_STATUS = {"verbatim", "edited", "template"}


def check_collection(manifest, files, f):
    """Every file copied in from the source environment must declare itself.

    The failure this prevents is the one that produced the `<URL>` damage from
    the other side: content arriving with edits nobody wrote down, so no later
    reader can tell an intentional de-identification from a mistake. A collected
    file is declared once, with its source path and every edit made on the way;
    the roots it applies to are listed in `collected_roots`.

    What it cannot check: whether the copy still matches the source. The source
    lives on one machine and this repo does not. That is what the recorded edit
    list is for — it makes the diff reproducible by whoever does have both.
    """
    roots = tuple(manifest.get("collected_roots", []))
    if not roots:
        return
    declared = {e.get("path"): e for e in manifest.get("collected", [])}

    # The README/NOTICE skip is a NAME heuristic for the lane guides written
    # here (agents/README.md, hooks/README.md) — repo-authored, so they have no
    # source to declare. It misfires on a file that is genuinely collected and
    # merely named README.md: interop-layer/README.md is the source's own
    # operating manual. A declared entry overrides the heuristic, because
    # declaring a file IS the assertion that it was collected. Undeclared
    # READMEs behave exactly as before.
    # ACCEPTANCE.md joined the authored-name list on 2026-08-16
    # (compact-recovery round): a repo-authored acceptance checklist shipping
    # beside a collected file, caught by this check on the round's first gate
    # run. Same authored-file class, same declared-entry override; test case 11
    # is the negative control that keeps the exemption narrow.
    in_scope = {p for p in files if p.startswith(roots)
                and (p in declared
                     or not p.endswith(("README.md", "NOTICE.md",
                                        "ACCEPTANCE.md")))}

    for rel in sorted(in_scope):
        e = declared.get(rel)
        if not e:
            f.add("C", rel, 0, "collected file with no provenance entry",
                  "add a [[collected]] entry: source, status, and every edit")
            continue
        if not e.get("source"):
            f.add("C", rel, 0, "provenance entry has no source path",
                  "record where in the source environment it came from")
        status = e.get("status")
        if status not in VALID_STATUS:
            f.add("C", rel, 0, f"status {status!r} is not one of {sorted(VALID_STATUS)}",
                  "verbatim = byte-identical; edited = enumerate every change; "
                  "template = rewritten for adopters")
        elif status != "verbatim" and not e.get("edits"):
            f.add("C", rel, 0, f"status '{status}' with no recorded edits",
                  "list each change; an unrecorded edit is indistinguishable "
                  "from the over-scrub this gate exists to catch")

    for rel in sorted(declared):
        if rel not in in_scope:
            f.add("C", rel, 0, "provenance entry for a file that is not tracked here",
                  "remove the stale entry, or restore the file")


def _ignored(rel):
    out = subprocess.run(["git", "-C", str(REPO_ROOT), "check-ignore", "-q", rel],
                         capture_output=True)
    return out.returncode == 0


# --- D: dead declarations ----------------------------------------------------

def check_dead(manifest, files, f):
    """Declarations that no longer match anything.

    Every entry in share-manifest.toml widens the gate or explains an absence.
    A stale one is not inert: an [[allow]] whose finding is long gone is a
    standing permission nobody re-reads, a [[not_shipped]] for a file that now
    ships is a published lie about what an adopter gets, and a placeholder token
    declared with nothing using it is the residue of a rule that was rewritten
    without anyone checking what pointed at it.

    All three were found by hand on 2026-08-16 — the last one, a token retired
    from CLAUDE.md on 2026-08-06 and still declared here ten days later, only
    because the file it belonged to was being read for an unrelated reason.
    The manifest is the one file in this repo whose whole value is that its
    claims are true; nothing was checking the claims it had stopped making.
    """
    text = {}
    for rel in files:
        if Path(rel).suffix.lower() in TEXT_SUFFIXES:
            t = read(rel)
            if t is not None:
                text[rel] = t
    manifest_rel = "tools/share-manifest.toml"

    # D1 — a [[not_shipped]] path that now resolves inside the repo.
    #
    # `partial` is exempt, and the exemption is the point rather than a
    # loophole: partial MEANS part of it ships, so "it resolves" is what the
    # entry already says. The first version of this check did not know that and
    # reported both partial entries as findings — a gate ruling on something it
    # could not determine, which is the one thing this repo's own rules say a
    # gate may never do. The three dispositions below all assert total absence,
    # and for those a resolving path is a contradiction.
    source_map = manifest.get("source_map", {})
    tracked = set(files)
    ABSENT = {"upstream-absent", "referenced-only", "excluded-by-decision"}
    for e in manifest.get("not_shipped", []):
        key = e.get("path", "")
        if not key or key.endswith("/") or e.get("disposition") not in ABSENT:
            continue
        if _resolves(key, source_map, tracked, manifest_rel):
            f.add("D", manifest_rel, 0,
                  f"[[not_shipped]] {key!r} — but it resolves in this repo now",
                  "it ships: delete the entry and add a [[collected]] one, or "
                  "narrow the path if only part of it is absent")

    # D2 — an [[allow]] entry that excuses no current finding.
    for e in manifest.get("allow", []):
        rel, kind = e.get("file"), e.get("kind")
        if not rel or not kind:
            continue
        if rel not in text:
            f.add("D", manifest_rel, 0,
                  f"[[allow]] names {rel!r}, which is not a tracked text file",
                  "remove it; an exception for a file nobody publishes is noise "
                  "that reads as coverage")
            continue
        needle = e.get("match")
        if not any(k == kind and (not needle or needle in sample)
                   for _, k, _, sample in scan_text(text[rel], rel)):
            f.add("D", manifest_rel, 0,
                  f"[[allow]] for {rel} / {kind} matches nothing there any more",
                  "the finding it excused is gone: remove the entry rather than "
                  "leave a standing permission for a case nobody can see")

    # D3 — a declared placeholder token that appears nowhere.
    ph = manifest.get("placeholders", {})
    blob = "\n".join(t for rel, t in text.items() if rel != manifest_rel)
    for group in ("substitution", "path_position_ok", "command_position_ok",
                  "literal"):
        for tok in ph.get(group, []):
            if tok not in blob:
                f.add("D", manifest_rel, 0,
                      f"[placeholders] {group}: {tok} appears in no tracked file",
                      "the text that used it was rewritten; drop the token so "
                      "the vocabulary stays a description of this repo")


# --- V: verify against a real source tree ------------------------------------

def check_verify(manifest, files, f, source_root):
    """The one thing check C says it cannot do — done when the source is here.

    check C's docstring is explicit: it cannot verify that a copy still matches
    its source, because the source lives on one machine and this repo does not.
    That is true of the published repo and false of the machine doing the
    collecting, where both trees are mounted at once. On 2026-08-16 that gap
    cost six de-identification decisions: a verbatim refresh overwrote files
    whose repo copies were deliberately different, and every mechanical check
    passed, because none of them was comparing anything.

    Opt-in on purpose (`--source PATH`) and never silently skipped — an adopter
    has no source to point at, and a check that quietly does nothing is worse
    than an absent one. Three findings, and the second is the one that matters:

      verbatim but differs   the copy drifted, or the source moved on
      edited/template but IDENTICAL to source
                             the declared edit is gone. Either it was never
                             applied, or a refresh reverted it. This is the
                             failure that has no other detector.
      declared source missing
                             the entry points at a path the source no longer
                             has; the disposition rests on a claim that expired
      source is content-dirty
                             the source file has uncommitted changes, so the
                             copy is a snapshot of a state committed nowhere.
                             COLLECTION-RULES.md step 0 says stop; this is that
                             step, applied to the paths that actually matter
                             instead of to the whole tree. Line-ending-only
                             dirt is not reported — a signal that is routinely
                             false teaches its reader to ignore it.

    KNOWN LIMIT, found on this check's first real use (2026-08-16) and stated
    here rather than in a note somewhere else: for an `edited` or `template`
    entry, V can only assert that the file DIFFERS from the source. It cannot
    tell "differs by exactly the declared edits" from "differs because the
    source moved on and this copy is stale". There is no machine-readable form
    of an edit list, and inventing one would trade a prose record a human can
    audit for a schema that would rot. The dirty-source finding above closes the
    common case; the rest is what the `edits` list and a human are for.
    """
    root = Path(source_root).expanduser()
    if not root.is_dir():
        print(f"FATAL: --source {source_root} is not a directory")
        sys.exit(2)

    # Content-dirty paths at the source, by line count. --numstat, not
    # --porcelain: a file shows M for line endings alone, and G-4 of this
    # check's own review round is that treating that as "stop" trains the
    # reader to stop obeying.
    dirty = set()
    out = subprocess.run(["git", "-C", str(root), "diff", "--numstat"],
                         capture_output=True, text=True)
    for line in out.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and (parts[0] != "0" or parts[1] != "0"):
            dirty.add(parts[2].strip())

    prefix = "~/.claude/"
    checked = 0
    for e in manifest.get("collected", []):
        rel, src, status = e.get("path"), e.get("source", ""), e.get("status")
        if not rel or not src.startswith(prefix):
            f.add("V", "tools/share-manifest.toml", 0,
                  f"[[collected]] {rel}: source {src!r} is not under {prefix}",
                  f"record the source path as {prefix}<path>")
            continue
        s, r = root / src[len(prefix):], REPO_ROOT / rel
        if not s.exists():
            f.add("V", rel, 0, f"declared source {src} does not exist",
                  "the source moved or was deleted: re-locate it and correct "
                  "the entry, or remove the file and say why in [[not_shipped]]")
            continue
        if not r.exists():
            continue          # check C already reports this
        checked += 1
        if src[len(prefix):] in dirty:
            # The escape is a declared, dated reason on the entry — the same
            # shape as every other exception in this manifest, because the
            # alternative (a red gate for a legitimate transient state) is the
            # permanently-on alarm nobody reads. An empty ack does not count.
            ack = (e.get("source_dirty_ack") or "").strip()
            if ack:
                print(f"  [V] ack: {rel} — source dirty, declared: {ack[:88]}")
            else:
                f.add("V", rel, 0,
                      f"source {src} has uncommitted content changes",
                      "your copy is a snapshot of a state committed nowhere: "
                      "commit at the source and re-collect, or add a dated "
                      "source_dirty_ack to this entry saying why it does not "
                      "matter for this file")
        same = (s.read_bytes().replace(b"\r\n", b"\n")
                == r.read_bytes().replace(b"\r\n", b"\n"))
        if status == "verbatim" and not same:
            f.add("V", rel, 0, "declared verbatim, but differs from the source",
                  "re-collect it, or change the status and enumerate every edit")
        elif status in ("edited", "template") and same:
            f.add("V", rel, 0,
                  f"declared '{status}', but is byte-identical to the source",
                  "the declared edits are not in the file — a refresh most "
                  "likely reverted them; re-apply them or delete the claim")
    print(f"  [V] compared {checked} collected file(s) against {root}")


def _resolves_public(key, manifest, files):
    return _resolves(key, manifest.get("source_map", {}), set(files), "")


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

CHECKS = {"L": check_leak, "P": check_placeholder, "R": check_reference,
          "S": check_structure, "C": check_collection, "D": check_dead}
NAMES = {"L": "leak", "P": "placeholder", "R": "reference",
         "S": "structure", "C": "collection", "D": "dead-declaration",
         "V": "source-verify"}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", default="LPRSCD",
                    help="subset of LPRSCD (default: all). V requires --source.")
    ap.add_argument("--source", metavar="PATH",
                    help="path to the source environment; enables check V, "
                         "which compares every collected file against it")
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
    if args.source:
        check_verify(manifest, files, f, args.source)
        selected.append("V")

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
