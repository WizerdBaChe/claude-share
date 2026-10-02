#!/usr/bin/env python
"""entry-schema-lint -- enumerate artifacts that do not carry the entry-schema core.

Reads the EMITTED artifacts (files under ~/.claude, optionally one project tree), never a
producer's intermediate state. Every check rules only on what it can DETERMINE; severity
follows the consumer of the report: a human/LLM reading the sweep -> WARN with a named
promotion trigger; a determinable absence on an artifact born AFTER the schema -> FAIL.

Schema:   ops/references/entry-schema.md            (fields, value sets, 14-surface adapter table)
Guide:    ops/references/principle-design-guide.md  (AP-nn asset properties this lint detects)
Wired in: ops/references/integrity-sweep.md check 29; config-self-audit section 4 (--path mode)
Controls: controls.py -- two-sided (known-bad caught AND known-good passed) for every check;
          run it after touching this file; its last line must read `ALL PASS n/n`.

Checks (ES-n; the numbering is owned by this docstring and registered in LABEL-REGISTRY.md §2):
  ES-1 hook header   every hooks/*.py registered in settings.json carries a module-docstring line
                     `STATUS: LIVE|SHADOW|RETIRED since <date>`; a SHADOW line names its
                     graduation criterion (WARN).                                 AP-12 AP-32
  ES-2 hook proof    every registered hook DECLARES a runnable proof-of-life in its own
                     docstring (``Proof-of-life: `python <suite>` ``), which sweep check 31
                     executes. Grammar and classes are pol.py's, not a copy (L-044);
                     a `manual` declaration naming only a sweep check is reported, never
                     accepted -- being named is not being run (AP-63).      AP-04 AP-45
  ES-3 rule file     rules/*.md: frontmatter present, `paths:` non-empty, stem named in the
                     CLAUDE.md `**Path-scoped rules**` index line (FAIL); review-when present
                     or the literal `none` (WARN).                               AP-16 AP-30
  ES-4 trigger class skill-trigger-classes.md blocks: the skill exists, class/source/on-fire
                     are inside the value sets, zero-means present.              AP-36
  ES-5 pointers      owner/mechanism paths resolve: rules-usage-dict §7 owner column,
                     LABEL-REGISTRY §2 owner column, `tools/`/`hooks/` paths named in rules/*.md
                     (FAIL); rule-registry entries carry current/why/evidence (WARN). AP-11 AP-33
  ES-6 guide cites   principle-design-guide.md citations resolve: `CLAUDE.md «phrase»` verbatim
                     in CLAUDE.md, `PHILOSOPHY §一.n` heading present (FAIL).
  ES-7 page builder  (--project-root only) *.py containing an `<html` literal: emits
                     data-page-class / data-audience; two or more builders share a local shell
                     module (WARN).                                              AP-38 AP-39 AP-49
  ES-8 tool-bound    a ruling sentence whose subject is a tool or a moment ("whenever the
                     pipeline emits", "when editing X") in rules/, skills/*/SKILL.md, ops/*.md
                     (WARN; lines that QUOTE the anti-pattern are excluded).     AP-47 (RD-1)
  ES-9 watched       every component under system-hmi's scan roots (hooks/*.py, tools/<x>,
                     skills/<x>, rules/*.md, agents/*.md) has a row in
                     tools/system-hmi/registry/subsystems.json or a reasoned row in
                     ignore.json; a path matched by two subsystems is an overlap (FAIL).
                     The enumeration is system-hmi's own hmi/scan.py, imported: one
                     instrument, and the HMI reads THIS lint's verdict (point
                     health-checks.entry-schema-lint) rather than re-deciding. Born
                     2026-09-29 with legacy count 0 (the 12 unregistered paths were
                     registered the same day), so it enters SEVERITY_PROMOTED at birth
                     under the second trigger; the save-time twin is golive_check's
                     registry_gap().                                             AP-08

Severity. FAIL = a determinable defect, or a missing core field on an artifact whose first
git commit is AFTER SCHEMA_BORN. WARN = legacy debt (first commit on or before SCHEMA_BORN)
or a heuristic check. UNDET = the check could not DETERMINE a verdict for that artifact
(unreadable, or a declaration shape no vocabulary here covers): printed loudly, counted in
neither total, and never an exit code -- folding it into either side is how a count stays
plausible while meaning nothing (AP-62). Every WARN class prints its count, which must not rise between sweeps
-- promotion triggers, both firing by editing SEVERITY_PROMOTED: a WARN class that rises in
two consecutive sweeps, OR a WARN class whose legacy count reaches 0 (nothing legacy is left
for the tier to describe, so the next WARN would be a regression printed quietly). ES-1..ES-5
were promoted 2026-09-08 under the second trigger; ES-7/ES-8 stay WARN because a heuristic
may prompt a review and never rule FAIL. Exit 0 = no FAIL; 1 = FAIL present (or --strict and any
WARN); 2 = an anchor this lint depends on is gone (settings.json, the CLAUDE.md index line,
integrity-sweep.md, skill-trigger-classes.md, tools/system-hmi/hmi/scan.py + its registry dir)
-- never silence.

Not covered (named so the ruler is visible): SKILL.md frontmatter beyond name/description
(loader-fixed; the carrier is the trigger-class block, ES-4); skill-trigger-dict.md bullets
(tools/skill-routing-audit.py owns them); intake records and xi cards (intake.py check,
xi.py); OPS.md rows, inbound-routing rows, 40-maintenance §2a rows (documented-only in the
adapter table); whether a hook's verdict kind (deny/warn/annotate) matches its docstring
(config-self-audit §1 reads the code). ES-7 and ES-8 are heuristics and say so in their
message: a hit is a review prompt, not a verdict.

Usage:
  python -X utf8 tools/entry-schema-lint/lint.py [--home DIR] [--path FILE] [--project-root DIR]
                                                 [--strict] [--json]
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import io
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCHEMA_BORN = "2026-09-08"  # first-commit dates AFTER this must conform (FAIL); on/before = legacy (WARN)
# A class listed here reports FAIL regardless of the artifact's birth date. Two named
# triggers put a class in this set, and both are recorded in the sweep's check 29:
#   (1) the class rose above its baseline in two consecutive sweeps (the original trigger);
#   (2) 2026-09-08 -- the class's LEGACY count reached 0. "WARN" here has only ever meant
#       "debt that predates the schema"; once none of it is left, a WARN in that class can
#       only come from an artifact edited (or an entry added) AFTER the schema, which is a
#       REGRESSION printed quietly. Re-introducing the exact debt this pass cleared is the
#       thing the tier was hiding, so the tier is retired class by class as it empties.
# ES-7/ES-8 are NOT eligible under either trigger: they are heuristics, and a heuristic may
# only prompt a review, never rule FAIL (CLAUDE.md gate rule -- it may rule on what it can
# DETERMINE). Rollback: remove a class from this set; the birth-date rule takes over again.
SEVERITY_PROMOTED: set[str] = {"ES-1", "ES-2", "ES-3", "ES-4", "ES-5", "ES-9"}

HERE = Path(__file__).resolve().parent
DEFAULT_HOME = HERE.parent.parent

STATUS_VALUES = ("LIVE", "SHADOW", "RETIRED")
CLASS_VALUES = ("always-on", "conditional", "phase-gated", "user-manual", "sub-service", "second-order")
SOURCE_VALUES = ("utterance", "artifact-context", "omission", "sub-service")
ONFIRE_VALUES = ("execute", "ask-first")
CHECKS = ("ES-1", "ES-2", "ES-3", "ES-4", "ES-5", "ES-6", "ES-7", "ES-8", "ES-9")

TOOL_BOUND = re.compile(
    r"(?i)\bwhenever\b[^.\n]{0,80}\b(emits?|runs?|calls?|writes?|generates?|outputs?|produces?)\b"
    r"|\bwhen editing\b"
)
# A line that QUOTES the anti-pattern is not an instance of it.
TOOL_BOUND_QUOTING = (
    "RD-1", "anti-pattern", "named defect", "fires only", "is the failure", "ES-8", "AP-47",
    "L-059", "«", "»", "never fires", "failure mode", "is dead", "tool trigger",
    "TOOL trigger", "not the tool", "never the tool", "instead of the asset",
)
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
             "archive", "_previous", "backups", "_calibration", "out"}
PATH_IN_TICK = re.compile(
    r"`((?:~/\.claude/|\.claude/)?(?:ops|skills|tools|rules|hooks|references|agents|interop)/[^`\s§:]+)"
)
OPS_BASENAME = re.compile(r"`(\d\d-[a-z-]+\.md)`")
# A review-when DECLARATION, in any of the three carriers rules/*.md actually use:
# a frontmatter key, a heading, or an inline sentence. The discriminating detail is
# the colon followed by a trigger -- a rule that merely MENTIONS the word (telling an
# author to hang one on a deliverable) has not declared its own, and measured
# 2026-09-08 that was a real file, not a hypothetical: rules/deliverable-doc-refs.md.
REVIEW_WHEN = re.compile(r"(?im)^#{2,}\s*(?:§\d+\s*)?review-when\b|`?review-when`?\s*:\s*\S[\s\S]{6,}")
FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


@dataclass
class Finding:
    check: str
    severity: str
    path: str
    msg: str

    def line(self) -> str:
        return f"{self.check} {self.severity} {self.path}: {self.msg}"


# ----------------------------------------------------------------------------- helpers

def read(p: Path) -> str:
    return io.open(p, encoding="utf-8", errors="replace").read()


def rel(home: Path, p: Path) -> str:
    try:
        return p.resolve().relative_to(home.resolve()).as_posix()
    except ValueError:
        return p.as_posix()


def first_commit_date(home: Path, relpath: str):
    """ISO date of the commit that ADDED relpath, or None (untracked / no git)."""
    try:
        r = subprocess.run(
            ["git", "-C", str(home), "log", "--diff-filter=A", "--follow", "--format=%as", "--", relpath],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )
    except Exception:
        return None
    if r.returncode != 0:
        return None
    lines = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    return lines[-1] if lines else None


def severity_for(home: Path, p: Path, check: str) -> str:
    """WARN for legacy artifacts (first commit on/before SCHEMA_BORN), FAIL otherwise."""
    if check in SEVERITY_PROMOTED:
        return "FAIL"
    d = first_commit_date(home, rel(home, p))
    return "WARN" if (d is not None and d <= SCHEMA_BORN) else "FAIL"


def module_docstring(text: str):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    return ast.get_docstring(tree, clean=False)


def frontmatter(text: str):
    m = FM_RE.match(text)
    if not m:
        return None
    keys: dict[str, str] = {}
    cur = None
    for line in m.group(1).splitlines():
        km = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if km:
            cur = km.group(1)
            keys[cur] = km.group(2).strip()
        elif cur and line.strip().startswith("-"):
            keys[cur] = (keys[cur] + " " + line.strip()).strip()
    return keys


def split_row(row: str) -> list[str]:
    return [c.strip() for c in re.split(r"(?<!\\)\|", row.strip().strip("|"))]


def table_rows(text: str, heading_regex: str) -> list[str]:
    """Body rows (header + separator dropped) of the first table under the matching heading."""
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not re.search(heading_regex, lines[i]):
        i += 1
    if i >= len(lines):
        return []
    i += 1
    rows: list[str] = []
    while i < len(lines) and not lines[i].startswith("## "):
        if lines[i].startswith("|"):
            rows.append(lines[i])
        i += 1
    return rows[2:] if len(rows) >= 2 else []


def resolve(home: Path, tok: str) -> bool:
    for pre in ("~/.claude/", ".claude/"):
        if tok.startswith(pre):
            tok = tok[len(pre):]
    tok = tok.rstrip("/").split(" ")[0]
    return (home / tok).exists()


def registered_hooks(home: Path):
    """Sorted basenames of hooks/*.py named in settings.json; None when the anchor is missing."""
    sj = home / "settings.json"
    if not sj.is_file():
        return None
    try:
        d = json.loads(read(sj))
    except json.JSONDecodeError:
        return None
    names: set[str] = set()
    for arr in (d.get("hooks") or {}).values():
        for entry in arr:
            for h in entry.get("hooks", []):
                for m in re.finditer(r"hooks/([A-Za-z0-9_]+\.py)", h.get("command", "")):
                    names.add(m.group(1))
    return sorted(names)


# ----------------------------------------------------------------------------- checks

def check_hooks_header(home: Path) -> list[Finding]:
    out: list[Finding] = []
    names = registered_hooks(home)
    if names is None:
        return [Finding("ANCHOR", "LOST", "settings.json", "missing or unparsable -- ES-1/ES-2 cannot run")]
    for n in names:
        p = home / "hooks" / n
        r = f"hooks/{n}"
        if not p.is_file():
            out.append(Finding("ES-1", "FAIL", r, "registered in settings.json but absent on disk (70-evolution §1.5: an outage)"))
            continue
        doc = module_docstring(read(p)) or ""
        m = re.search(r"^STATUS:\s*(\w+)(.*)$", doc, re.M)
        if not m:
            out.append(Finding("ES-1", severity_for(home, p, "ES-1"), r,
                               "no `STATUS:` line in the module docstring (LIVE|SHADOW|RETIRED since <date>)"))
            continue
        val = m.group(1).upper()
        if val not in STATUS_VALUES:
            out.append(Finding("ES-1", "FAIL", r, f"STATUS value `{m.group(1)}` not in {STATUS_VALUES}"))
            continue
        if val == "SHADOW":
            tail = doc[m.start():]
            if not re.search(r"(?i)graduat|promot|review-when|registry|criterion", tail):
                out.append(Finding("ES-1", severity_for(home, p, "ES-1"), r,
                                   "STATUS: SHADOW without a graduation criterion (which observation flips it to LIVE)"))
    return out


def load_pol(home: Path):
    """-> tools/hook-proof-of-life/pol.py as a module, or None.

    ES-2 does not re-implement the `Proof-of-life:` grammar. That grammar is
    OWNED by pol.py, which is the thing that actually executes the declared
    suites (sweep check 31); a second copy here would be a second vocabulary for
    one object class, and the two would drift apart silently -- the failure
    L-044 names. Importing it means a moved owner surfaces as a LOST anchor
    instead of as a lint that quietly disagrees with the runner.

    The linted tree is tried first (a ~/.claude clone brings its own runner),
    then the tree this file lives in -- so `--home <fixture>` is graded by the
    real grammar rather than by nothing at all. Both sites are named; if neither
    holds it the check goes LOST rather than passing everything.
    """
    for base in (home, DEFAULT_HOME):
        p = base / "tools" / "hook-proof-of-life" / "pol.py"
        if not p.is_file():
            continue
        try:
            spec = importlib.util.spec_from_file_location("_es2_pol", p)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.declaration  # noqa: B018 -- the one attribute this check binds to
        except Exception:
            continue
        return mod
    return None


def check_hooks_proof(home: Path) -> list[Finding]:
    """Every registered hook must DECLARE a runnable proof-of-life.

    The predicate used to be "the basename appears somewhere in
    integrity-sweep.md". That is a POSITION in an artifact that grows (AP-45):
    it went on reporting a plausible number while pointing at the wrong set --
    measured 2026-09-08, it flagged 11 hooks that all carry a declaration check
    31 executes, and flagged none of the 5 that carry nothing at all. It also
    contradicted the sweep, which deliberately keeps NO list of hooks.

    The position-free form is a property of the hook itself: it says, in its own
    docstring, what proves it still works. Being NAMED in the sweep is not being
    RUN by it (AP-63), so a `manual` declaration is reported, never accepted.
    """
    names = registered_hooks(home)
    if names is None:
        return []  # anchor finding already emitted by ES-1
    pol = load_pol(home)
    if pol is None:
        return [Finding("ANCHOR", "LOST", "tools/hook-proof-of-life/pol.py",
                        "missing or unimportable -- ES-2 cannot run (it owns the "
                        "`Proof-of-life:` declaration grammar that sweep check 31 executes)")]
    out: list[Finding] = []
    for n in names:
        p = home / "hooks" / n
        r = f"hooks/{n}"
        if not p.is_file():
            continue  # ES-1 already reports the outage; one absence, one finding
        kind, detail = pol.declaration(p)
        if kind == "executable":
            continue
        if kind == "manual":
            out.append(Finding("ES-2", severity_for(home, p, "ES-2"), r,
                               f"declares {detail} -- being NAMED in the sweep is not being RUN "
                               f"by it (AP-63). Repair: add a `Proof-of-life:` line naming a runnable "
                               f"suite (python <path>.py ...) "
                               f"to the module docstring; check 31 then executes it"))
        elif kind == "uncovered":
            out.append(Finding("ES-2", severity_for(home, p, "ES-2"), r,
                               "no `Proof-of-life:` line in the module docstring -- nothing re-runs "
                               "this hook's calibration, so a hook that died would look exactly like "
                               "a quiet week (AP-63; 40-maintenance §2a condition 3). Repair: write "
                               "the line naming a runnable suite, or add the suite first"))
        else:
            # AP-62: "I could not read it" is not "it has none". Counted in neither.
            out.append(Finding("ES-2", "UNDET", r,
                               f"declaration present but unclassifiable: {detail} -- counted in no "
                               f"verdict; read the docstring before believing either side"))
    return out


def index_line_stems(home: Path):
    cm = home / "CLAUDE.md"
    if not cm.is_file():
        return None
    for line in read(cm).splitlines():
        if line.startswith("**Path-scoped rules**"):
            return set(re.findall(r"`([a-z0-9-]+)`", line))
    return None


def check_rule_files(home: Path) -> list[Finding]:
    out: list[Finding] = []
    stems = index_line_stems(home)
    if stems is None:
        out.append(Finding("ANCHOR", "LOST", "CLAUDE.md",
                           "no line starting with `**Path-scoped rules**` -- ES-3 index check cannot run"))
    for p in sorted((home / "rules").glob("*.md")):
        r = rel(home, p)
        text = read(p)
        fm = frontmatter(text)
        if fm is None:
            out.append(Finding("ES-3", "FAIL", r, "no YAML frontmatter (`paths:` is what makes a rules/*.md load)"))
            continue
        if not fm.get("paths"):
            out.append(Finding("ES-3", "FAIL", r, "frontmatter has no `paths:` globs -- the file can never load"))
        if stems is not None and p.stem not in stems:
            out.append(Finding("ES-3", "FAIL", r,
                               "stem not named in the CLAUDE.md `**Path-scoped rules**` index line (dict-sync corollary)"))
        if "review-when" not in fm and not REVIEW_WHEN.search(text):
            out.append(Finding("ES-3", severity_for(home, p, "ES-3"), r,
                               "no review-when: no frontmatter key, no `## review-when` section, and no "
                               "inline `review-when: <event>` in the prose. A DATE is not a trigger -- name "
                               "the EVENT that invalidates the rule, or write `review-when: none` when "
                               "nothing outside the repo can"))
    return out


def check_trigger_classes(home: Path) -> list[Finding]:
    f = home / "ops" / "references" / "skill-trigger-classes.md"
    if not f.is_file():
        return [Finding("ANCHOR", "LOST", "ops/references/skill-trigger-classes.md", "missing -- ES-4 cannot run")]
    blocks: dict[str, dict[str, str]] = {}
    cur = None
    for line in read(f).splitlines():
        m = re.match(r"^## ([\w-]+)\s*$", line)
        if m:
            cur = m.group(1)
            blocks[cur] = {}
            continue
        if cur is None:
            continue
        m = re.match(r"^(class|source|on-fire|zero-means|proc):\s*(.*)$", line)
        if m and m.group(1) != "proc":
            v = m.group(2).strip()
            if m.group(1) != "zero-means":
                v = v.split("#")[0].strip()
            blocks[cur][m.group(1)] = v
    out: list[Finding] = []
    for name, b in blocks.items():
        r = f"ops/references/skill-trigger-classes.md ## {name}"
        if not (home / "skills" / name / "SKILL.md").is_file():
            out.append(Finding("ES-4", "FAIL", r, "block names a skill with no skills/<name>/SKILL.md (ghost entry)"))
        for key, vals in (("class", CLASS_VALUES), ("source", SOURCE_VALUES), ("on-fire", ONFIRE_VALUES)):
            v = b.get(key)
            if v is None:
                out.append(Finding("ES-4", "FAIL", r, f"missing `{key}:` (the routing audit reads it as `?`)"))
            elif v not in vals:
                out.append(Finding("ES-4", "FAIL", r, f"`{key}: {v}` not in {vals}"))
        if not b.get("zero-means"):
            out.append(Finding("ES-4", severity_for(home, f, "ES-4"), r,
                               "no `zero-means:` -- an unexplained zero prints as a defect"))
    return out


def check_pointers(home: Path) -> list[Finding]:
    out: list[Finding] = []
    # rules-usage-dict §七: owner = 3rd cell
    f = home / "ops" / "rules-usage-dict.md"
    if f.is_file():
        for row in table_rows(read(f), r"^## 七"):
            cells = split_row(row)
            if len(cells) < 4:
                continue
            toks = PATH_IN_TICK.findall(cells[2]) + ["ops/" + t for t in OPS_BASENAME.findall(cells[2])]
            for tok in toks:
                if not resolve(home, tok):
                    out.append(Finding("ES-5", "FAIL", "ops/rules-usage-dict.md §7",
                                       f"owner path `{tok}` does not exist (row `{cells[0][:40]}`)"))
    else:
        out.append(Finding("ANCHOR", "LOST", "ops/rules-usage-dict.md", "missing -- ES-5 cannot run"))
    # LABEL-REGISTRY §2: owner = 4th cell
    f = home / "LABEL-REGISTRY.md"
    if f.is_file():
        for row in table_rows(read(f), r"^## 2\."):
            cells = split_row(row)
            if len(cells) < 4:
                continue
            toks = PATH_IN_TICK.findall(cells[3]) + ["ops/" + t for t in OPS_BASENAME.findall(cells[3])]
            for tok in toks:
                if not resolve(home, tok):
                    out.append(Finding("ES-5", "FAIL", "LABEL-REGISTRY.md §2",
                                       f"owner path `{tok}` does not exist (family `{cells[0][:40]}`)"))
    # rules/*.md: a mechanism the text names must exist
    for p in sorted((home / "rules").glob("*.md")):
        for tok in set(PATH_IN_TICK.findall(read(p))):
            if tok.startswith(("tools/", "hooks/")) and not resolve(home, tok):
                out.append(Finding("ES-5", "FAIL", rel(home, p),
                                   f"names mechanism `{tok}` which does not exist (ghost mechanism, 40-maintenance §4.2)"))
    # rule-registry entries: schema fields present
    rr = home / "ops" / "rule-registry.md"
    if rr.is_file():
        for part in re.split(r"^### ", read(rr), flags=re.M)[1:]:
            title = part.split("\n", 1)[0].strip()[:60]
            missing = [k for k in ("current", "why", "evidence") if not re.search(rf"^\s*-\s*\**{k}\**:", part, re.M)]
            if missing:
                out.append(Finding("ES-5", severity_for(home, rr, "ES-5"), f"ops/rule-registry.md ### {title}",
                                   f"entry lacks {missing} (schema: key/current/why/evidence/history/review-when/rollback)"))
    return out


def check_guide_citations(home: Path) -> list[Finding]:
    g = home / "ops" / "references" / "principle-design-guide.md"
    if not g.is_file():
        return [Finding("ANCHOR", "LOST", "ops/references/principle-design-guide.md", "missing -- ES-6 cannot run")]
    text = read(g)
    cm = read(home / "CLAUDE.md") if (home / "CLAUDE.md").is_file() else ""
    ph = read(home / "PHILOSOPHY.md") if (home / "PHILOSOPHY.md").is_file() else ""
    out: list[Finding] = []
    for phrase in sorted(set(re.findall(r"CLAUDE\.md «([^»]+)»", text))):
        if phrase not in cm:
            out.append(Finding("ES-6", "FAIL", "ops/references/principle-design-guide.md",
                               f"CLAUDE.md phrase not found verbatim: «{phrase[:60]}» (the guide or CLAUDE.md moved)"))
    for n in sorted(set(re.findall(r"PHILOSOPHY §一\.(\d+)", text)), key=int):
        if not re.search(rf"^### {n}\.", ph, re.M):
            out.append(Finding("ES-6", "FAIL", "ops/references/principle-design-guide.md",
                               f"PHILOSOPHY §一.{n} heading (`### {n}.`) not found"))
    return out


def _walk(root: Path, pattern: str):
    for p in root.rglob(pattern):
        if set(p.relative_to(root).parts[:-1]) & SKIP_DIRS:
            continue
        yield p


def check_page_builders(root: Path) -> list[Finding]:
    """ES-7. An EMITTER is a *.py containing an `<html` literal. A ROOT is an emitter that
    imports no other emitter. A SHARED SHELL is a root imported by 2+ distinct non-test local
    modules (a compliant delegating builder has no `<html` literal of its own, so its
    importer need not be an emitter; one wrapper importing one shell is a builder split in
    two files, not sharing -- SSLD's build_dual.py -> viewer_dual.py). Per-builder verdict
    (position-free, one line per file): when 2+ roots exist, every root that is not a shared
    shell carries its own `<html` shell -- the T44 pattern. A helper imported by many builders
    (a materials table, a self-declaration stamp) is NOT a shell unless it emits the root tag
    itself; that distinction is what the first cut missed on the SSLD tree. Heuristic: the
    attribute checks are substring tests over the emitter's source."""
    out: list[Finding] = []
    pys = list(_walk(root, "*.py"))
    texts = {p: read(p) for p in pys}
    emitters = [p for p in pys if re.search(r"(?i)<html", texts[p])]
    emitter_stems = {p.stem for p in emitters}
    import_re = re.compile(r"(?m)^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))")

    def local_emitter_imports(p: Path) -> set[str]:
        names = {(m.group(1) or m.group(2)).split(".")[0] for m in import_re.finditer(texts[p])}
        return {n for n in names if n in emitter_stems and n != p.stem}

    importers: dict[str, set[str]] = {}
    for p in pys:
        r = p.relative_to(root).as_posix()
        if "test" in r.lower():
            continue  # a test importing a builder is not adoption
        for n in local_emitter_imports(p):
            importers.setdefault(n, set()).add(r)
    for p in emitters:
        r = p.relative_to(root).as_posix()
        t = texts[p]
        if "data-page-class" not in t:
            out.append(Finding("ES-7", "WARN", r, "contains an `<html` literal but never emits `data-page-class` (rules/deliverable-doc-refs.md)"))
        if "data-audience" not in t:
            out.append(Finding("ES-7", "WARN", r, "contains an `<html` literal but never emits `data-audience` (naming-and-placement §1)"))
    roots = [p for p in emitters if not local_emitter_imports(p)]
    if len(roots) >= 2:
        shared = {p.stem for p in roots if len(importers.get(p.stem, ())) >= 2}
        tail = f"; {len(shared)} shared shell(s) imported by 2+ modules exempt" if shared else ""
        for p in roots:
            if p.stem in shared:
                continue
            out.append(Finding("ES-7", "WARN", p.relative_to(root).as_posix(),
                               f"emits its own `<html` root and is not a shared shell "
                               f"({len(roots)} independent shells in this tree{tail} -- the T44 pattern; heuristic)"))
    return out


def check_tool_bound(home: Path, project_root=None) -> list[Finding]:
    files = list((home / "rules").glob("*.md")) + list((home / "skills").glob("*/SKILL.md"))
    files += [p for p in (home / "ops").glob("*.md") if p.name != "lessons.md"]
    if project_root:
        files += list(_walk(Path(project_root), "CLAUDE.md"))
    out: list[Finding] = []
    for p in files:
        if not p.is_file():
            continue
        for i, line in enumerate(read(p).splitlines(), 1):
            m = TOOL_BOUND.search(line)
            if not m or any(q in line for q in TOOL_BOUND_QUOTING):
                continue
            if m.start() > 0 and line[m.start() - 1] in "\"'“‘`":
                continue  # the phrase is quoted: a line that cites the anti-pattern is not an instance of it
            out.append(Finding("ES-8", "WARN", f"{rel(home, p)}:{i}",
                               f"ruling bound to a tool/moment, not an asset class (RD-1; heuristic): `{line.strip()[:90]}`"))
    return out


# ----------------------------------------------------------------------------- driver

def load_hmi_scan(home: Path):
    """-> (scan module, registry dict) from `home`'s own system-hmi, or (None, reason).

    ES-9 does not re-implement "what counts as a component": that enumeration is
    OWNED by tools/system-hmi/hmi/scan.py (scan roots, ignore semantics, overlap
    rule). Like load_pol(), the linted tree is read first; unlike it there is no
    fallback to this file's tree, because the REGISTRY being judged must be the
    linted tree's own -- grading a fixture against the live subsystems.json
    would report the live tree's coverage as the fixture's.
    """
    hmi_dir = home / "tools" / "system-hmi" / "hmi"
    reg_dir = home / "tools" / "system-hmi" / "registry"
    if not (hmi_dir / "scan.py").is_file() or not (reg_dir / "subsystems.json").is_file():
        return None, "tools/system-hmi/hmi/scan.py or registry/subsystems.json absent"
    try:
        spec = importlib.util.spec_from_file_location("_es9_hmi_scan", hmi_dir / "scan.py")
        scan = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scan)
        registry = {
            "subsystems": json.loads(read(reg_dir / "subsystems.json")),
            "ignore": json.loads(read(reg_dir / "ignore.json")) if (reg_dir / "ignore.json").is_file() else [],
        }
        return scan, registry
    except Exception as e:  # noqa: BLE001
        return None, f"system-hmi scan unimportable: {type(e).__name__}: {e}"


def check_watched(home: Path) -> list[Finding]:
    """ES-9: every component system-hmi's scan can see is registered or reasoned-ignored."""
    scan, registry = load_hmi_scan(home)
    if scan is None:
        return [Finding("ANCHOR", "LOST", "tools/system-hmi", f"{registry} -- ES-9 cannot run")]
    try:
        result = scan.scan(home, registry)
    except Exception as e:  # noqa: BLE001
        return [Finding("ES-9", "UNDET", "tools/system-hmi/registry",
                        f"scan raised {type(e).__name__}: {e} -- coverage not determined")]
    out: list[Finding] = []
    for entry in result.get("unregistered", []):
        r = entry["path"]
        out.append(Finding("ES-9", severity_for(home, home / r, "ES-9"), r,
                           "no row in tools/system-hmi/registry/subsystems.json and none in "
                           "ignore.json -- nothing watches it; add a component_rules row under "
                           "the subsystem its function belongs to (or an ignore row with a reason)"))
    for ov in result.get("overlaps", []):
        out.append(Finding("ES-9", "FAIL", ov["path"],
                           "matched by more than one subsystem: " + ", ".join(ov["subsystems"])
                           + " -- one component, one owner row"))
    return out


def run(home: Path, project_root=None, only_path=None) -> list[Finding]:
    fs: list[Finding] = []
    fs += check_hooks_header(home)
    fs += check_hooks_proof(home)
    fs += check_rule_files(home)
    fs += check_trigger_classes(home)
    fs += check_pointers(home)
    fs += check_guide_citations(home)
    if project_root:
        fs += check_page_builders(Path(project_root))
    fs += check_tool_bound(home, project_root)
    fs += check_watched(home)
    if only_path:
        rp = rel(home, Path(only_path))
        fs = [f for f in fs if f.path.startswith(rp) or f.check == "ANCHOR"]
    return fs


def main(argv=None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="entry-schema conformance lint (see module docstring)")
    ap.add_argument("--home", default=str(DEFAULT_HOME), help="the ~/.claude tree to lint")
    ap.add_argument("--project-root", help="a project tree for ES-7 (page builders) and ES-8 (CLAUDE.md)")
    ap.add_argument("--path", help="report only findings on this artifact (config-self-audit mode)")
    ap.add_argument("--strict", action="store_true", help="exit 1 on WARN too")
    ap.add_argument("--json", action="store_true", help="machine output")
    a = ap.parse_args(argv)
    home = Path(a.home)
    fs = run(home, a.project_root, a.path)
    fs.sort(key=lambda f: (f.check, f.severity, f.path, f.msg))
    if a.json:
        print(json.dumps([f.__dict__ for f in fs], ensure_ascii=False, indent=1))
    else:
        for f in fs:
            print(f.line())
        for c in CHECKS:
            fl = [f for f in fs if f.check == c]
            u = sum(f.severity == "UNDET" for f in fl)
            print(f"{c}: {sum(f.severity == 'FAIL' for f in fl)} FAIL / "
                  f"{sum(f.severity == 'WARN' for f in fl)} WARN"
                  + (f" / {u} UNDET" if u else ""))
    anchors = [f for f in fs if f.check == "ANCHOR"]
    nf = sum(f.severity == "FAIL" for f in fs)
    nw = sum(f.severity == "WARN" for f in fs)
    nu = sum(f.severity == "UNDET" for f in fs)
    print(f"entry-schema-lint: {nf} FAIL / {nw} WARN"
          + (f" / {nu} UNDETERMINED (in neither total)" if nu else "")
          + f" / anchors {'LOST' if anchors else 'ok'} "
          f"(schema born {SCHEMA_BORN}; legacy = WARN, born-after = FAIL; "
          f"promoted to FAIL either way: {', '.join(sorted(SEVERITY_PROMOTED)) or 'none'})")
    if anchors:
        return 2
    if nf or (a.strict and nw):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
