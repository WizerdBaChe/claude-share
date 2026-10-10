"""controls.py -- two-sided controls for entry-schema-lint (cases C-00..C-36, plus C-08b..C-08e and C-11b..C-11d).

Every ES check gets at least one POSITIVE control (a known-bad fixture that MUST be caught)
and one NEGATIVE control (a known-good fixture that MUST pass). A checker that has only been
shown one side has no verdict (global gate rule). Fixtures live in a TEMP tree -- never in
~/.claude -- except C-00, which runs the real tree and asserts only that no ANCHOR is lost.
Usage: python -X utf8 tools/entry-schema-lint/controls.py [--keep]
Last line: `ALL PASS n/n` (or `FAILED k/n`); exit 0 only on ALL PASS.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lint  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(cid: str, cond: bool, detail: str = "") -> None:
    RESULTS.append((cid, bool(cond), detail))
    print(f"{'PASS' if cond else 'FAIL'} {cid} {detail[:120]}")


def w(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def has(fs, check_id, path_part, msg_part="", severity=None) -> bool:
    return any(f.check == check_id and path_part in f.path and msg_part in f.msg
               and (severity is None or f.severity == severity) for f in fs)


def build_home(root: Path) -> Path:
    home = root / "home"
    py = "\"C:/py/python.exe\""
    hooks = ["good_guard.py", "bad_guard.py", "shadow_ok.py", "shadow_bad.py",
             "manual_guard.py", "undet_guard.py"]
    w(home / "settings.json", json.dumps({"hooks": {"PreToolUse": [{"matcher": "Write", "hooks": [
        {"type": "command", "command": f"{py} \"C:/x/.claude/hooks/{h}\""} for h in hooks]}]}}))
    # ES-2 fixtures span pol.py's four declaration classes: good/shadow_* are
    # `executable`, manual_guard is `manual`, undet_guard is `undetermined`, and
    # bad_guard is `uncovered`. bad_guard is ALSO absent from the fixture's
    # integrity-sweep.md -- the regression case for the predicate ES-2 replaced
    # on 2026-09-08 (a loosened gate ships what the old one used to catch).
    pol_line = 'Proof-of-life: `python hooks/{}.py --selftest`\n'
    w(home / "hooks" / "good_guard.py", '"""good_guard -- denies X.\n\nSTATUS: LIVE since 2026-09-08 (fixture).\n'
      + pol_line.format("good_guard") + '"""\nprint(1)\n')
    w(home / "hooks" / "bad_guard.py", '"""bad_guard -- denies Y. No status line here, no proof-of-life either.\n"""\nprint(1)\n')
    w(home / "hooks" / "shadow_ok.py", '"""shadow_ok.\n\nSTATUS: SHADOW (observe-only) since 2026-09-08; graduation criterion: 20 organic rows.\n'
      + pol_line.format("shadow_ok") + '"""\n')
    w(home / "hooks" / "shadow_bad.py", '"""shadow_bad.\n\nSTATUS: SHADOW since 2026-09-08.\n'
      + pol_line.format("shadow_bad") + '"""\n')
    w(home / "hooks" / "manual_guard.py", '"""manual_guard.\n\nSTATUS: LIVE since 2026-09-08 (fixture).\n'
      'Proof-of-life: integrity-sweep check 13.\n"""\n')
    w(home / "hooks" / "undet_guard.py", '"""undet_guard.\n\nSTATUS: LIVE since 2026-09-08 (fixture).\n'
      'Proof-of-life: ask the owner whether it still fires.\n"""\n')
    w(home / "ops" / "references" / "integrity-sweep.md",
      "# sweep\n```bash\npython hooks/good_guard.py --selftest\n# shadow_ok proof\n# shadow_bad proof\n"
      "# manual_guard and undet_guard are named HERE and nowhere else -- naming is not running\n```\n")
    w(home / "CLAUDE.md",
      "# prefs\n\n**Path-scoped rules** -- index: `good-rule` (x) · `ghost-mech` (y) · `nofm` (z) · "
      "`inline-rule` (w) · `mentions-rule` (v) · `empty-rule` (u). One rule there costs nothing.\n\n"
      "- **When authoring an invariant, checklist item, gate or ops rule:** property not advice.\n")
    w(home / "rules" / "good-rule.md",
      "---\npaths:\n  - \"**/*.svg\"\n---\n# good\nAny physical cross-section in this repo is cut from a solid by the paper-figure engine.\n\n## review-when\n- none\n")
    w(home / "rules" / "bad-rule.md",
      "---\npaths:\n  - \"**/*.py\"\n---\n# bad\nWhenever the pipeline emits a figure, run the gate.\n")
    w(home / "rules" / "nofm.md", "# no frontmatter at all\n")
    # ES-3 review-when carriers. `inline-rule` is the shape the detector was widened
    # to accept on 2026-09-08 (a declaration in prose, trigger WRAPPED onto the next
    # line). `mentions-rule` and `empty-rule` are the regression pair for that
    # loosening: naming the concept, or a colon with nothing after it, is not a
    # declaration -- measured on rules/deliverable-doc-refs.md, which said "hang a
    # `review-when` on the screen changing" while carrying only a review DATE.
    w(home / "rules" / "inline-rule.md",
      "---\npaths:\n  - \"**/*.frag\"\n---\n# inline\nA blank canvas is a defect, not a null result.\n"
      "Index line lives in `CLAUDE.md`; review-when: the\ntarget moves to WebGPU, where the failure surfaces "
      "as a validation error.\n")
    w(home / "rules" / "mentions-rule.md",
      "---\npaths:\n  - \"**/*.css\"\n---\n# mentions\nMeasure the glyph, not the box.\n"
      "Read the real geometry and hang a `review-when` on the screen or its scaling\nchanging. "
      "Index line lives in `CLAUDE.md`; review 2027-02.\n")
    w(home / "rules" / "empty-rule.md",
      "---\npaths:\n  - \"**/*.toml\"\n---\n# empty\nEvery generated file states its generator.\nreview-when:\n")
    w(home / "rules" / "ghost-mech.md",
      "---\npaths:\n  - \"**/x.py\"\nreview-when: none\n---\n# ghost\nEnforced by `tools/nonexistent-lint/lint.py`. "
      "The named anti-pattern is \"whenever the pipeline emits a figure\" (RD-1).\n"
      "The registry recorded that the old ruling read \"whenever the pipeline emits a figure\" and was rebound.\n")
    w(home / "skills" / "real-skill" / "SKILL.md", "---\nname: real-skill\ndescription: x\n---\n# real\nAny page a human opens carries its class.\n")
    w(home / "ops" / "references" / "skill-trigger-classes.md",
      "# classes\n## real-skill\nclass: conditional\nsource: utterance\non-fire: execute   # read-only\nzero-means: expected\n"
      "## ghost-skill\nclass: always-on\nsource: utterance\non-fire: execute\nzero-means: x\n"
      "## bad-enum\nclass: sometimes\nsource: utterance\n")
    w(home / "skills" / "bad-enum" / "SKILL.md", "---\nname: bad-enum\ndescription: x\n---\n")
    w(home / "ops" / "60-bootstrap.md", "# b\n")
    w(home / "ops" / "05-authority.md", "# a\n")
    w(home / "ops" / "rules-usage-dict.md",
      "# dict\n## 七、登記表\n| 類型 | 最小欄位 | owner | 何時必用 |\n|---|---|---|---|\n"
      "| ticket | a/b | `60-bootstrap.md` §C | x |\n| ghost | a | `ops/references/nope.md` | y |\n")
    w(home / "LABEL-REGISTRY.md",
      "# labels\n## 2. 家族表\n| 家族 | 軸 | 方向 | owner |\n|---|---|---|---|\n"
      "| `L0` | relax | L0→L2 | `ops/05-authority.md` §2 |\n| `ZZ-n` | x | none | `skills/missing/SKILL.md` |\n")
    w(home / "ops" / "rule-registry.md",
      "# registry\n## Mechanisms\n### good entry\n- current: 1\n- why: because\n- evidence: measured\n### thin entry\n- current: 2\n")
    # ES-9 fixture: the REAL scan.py (the enumeration is system-hmi's, imported) over a
    # fixture registry. good_guard registered; shadow_ok ignored with a reason; manual_guard
    # matched by TWO subsystems (overlap); every other hook / the skill dirs unregistered.
    real_scan = lint.DEFAULT_HOME / "tools" / "system-hmi" / "hmi" / "scan.py"
    if real_scan.is_file():
        w(home / "tools" / "system-hmi" / "hmi" / "scan.py", real_scan.read_text(encoding="utf-8"))
    w(home / "tools" / "system-hmi" / "registry" / "subsystems.json", json.dumps([
        {"id": "guards", "title_zh": "g", "title_en": "g", "order": 1, "component_rules": [
            {"glob": "hooks/good_guard.py", "kind": "hook"},
            {"glob": "hooks/manual_guard.py", "kind": "hook"}]},
        {"id": "other", "title_zh": "o", "title_en": "o", "order": 2, "component_rules": [
            {"glob": "hooks/manual_guard.py", "kind": "hook"},
            {"glob": "skills/real-skill", "kind": "skill"}]}]))
    w(home / "tools" / "system-hmi" / "registry" / "ignore.json", json.dumps([
        {"path_glob": "hooks/shadow_ok.py", "reason": "fixture: deliberately unwatched", "added": "2026-09-29"}]))
    w(home / "PHILOSOPHY.md", "# p\n## 一\n### 1. first\ntext\n")
    # ES-5 top-level docs: two dead pointers (a missing tool, a glob over a folder the
    # fixture lacks) beside the four classes that must stay silent -- an existing file, a
    # matching glob, a placeholder template, and a skill-relative path that only resolves
    # under skills/real-skill/ (the trigger-dict shape; 4/4 false positives without it).
    w(home / "skills" / "real-skill" / "references" / "only-in-skill.md", "# r\n")
    w(home / "OPERATOR-GUIDE.md",
      "# guide\n| `hooks/` | wiring in settings.json; state in `hooks/good_guard.py` |\n"
      "| `skills/` | see `skills/*/SKILL.md` |\n| `agents/` | see `agents/*.md` |\n"
      "Run `tools/ghost-tool/run.py`. Digest: `references/<project>-session-digest.md`.\n"
      "Mode table: `references/only-in-skill.md`.\n")
    w(home / "ops" / "references" / "principle-design-guide.md",
      "# guide\nsource: CLAUDE.md \u00abWhen authoring an invariant, checklist item, gate or ops rule\u00bb\n"
      "source: CLAUDE.md \u00abNot a phrase in the fixture\u00bb\nsource: PHILOSOPHY §一.1\nsource: PHILOSOPHY §一.9\n")
    return home


def build_projects(root: Path):
    bad = root / "proj_bad"
    w(bad / "a" / "build_a.py", "html = '<html><body>a</body></html>'\nopen('a.html','w').write(html)\n")
    w(bad / "b" / "build_b.py", "import json\nhtml = '<HTML lang=zh>'\n")
    good = root / "proj_good"
    w(good / "shell.py", "def page(body):\n    return '<html data-page-class=\"document-short\" data-audience=\"audience\">' + body\n")
    # compliant delegators: NO `<html` literal and NO attribute words of their own -- the shell
    # carries both; a comment restating them would be a placebo the check must not need
    w(good / "build_x.py", "from shell import page\nprint(page('x'))\n")
    w(good / "build_y.py", "import shell\nprint(shell.page('y'))\n")
    # mixed: a shared shell exists, one builder uses it, one builder rolls its own root; a
    # helper imported by BOTH builders must not count as a shell (the SSLD `selfdecl` case)
    mixed = root / "proj_mixed"
    w(mixed / "shell.py", "def page(body):\n    return '<html data-page-class=\"document-short\" data-audience=\"audience\">' + body\n")
    w(mixed / "selfdecl.py", "def stamp():\n    return 'generator=x'\n")
    w(mixed / "build_ok.py", "import selfdecl\nfrom shell import page\nprint(page(selfdecl.stamp()))\n")
    w(mixed / "build_ok2.py", "import shell\nprint(shell.page('two'))\n")  # shared = imported by 2+ modules
    w(mixed / "tests" / "test_own.py", "import build_own\nimport shell\n")  # a test import is not adoption
    w(mixed / "build_own.py", "import selfdecl\nhtml = '<html data-page-class=\"document-short\" data-audience=\"audience\">' + selfdecl.stamp()\n")
    return bad, good, mixed


def main() -> int:
    keep = "--keep" in sys.argv
    root = Path(tempfile.mkdtemp(prefix="esl-controls-"))
    try:
        home = build_home(root)
        bad, good, mixed = build_projects(root)

        # C-00 live tree: anchors intact (no fixture; the only control that touches ~/.claude, read-only)
        live = lint.run(lint.DEFAULT_HOME)
        check("C-00", not any(f.check == "ANCHOR" for f in live), "live ~/.claude: no ANCHOR lost")

        # ES-1 hook header
        h = lint.check_hooks_header(home)
        check("C-01", has(h, "ES-1", "bad_guard.py", "no `STATUS:`", "FAIL"), "known-bad: hook without STATUS -> FAIL (untracked = born after schema)")
        check("C-02", not has(h, "ES-1", "good_guard.py"), "known-good: STATUS: LIVE passes")
        check("C-03", has(h, "ES-1", "shadow_bad.py", "graduation", "FAIL"),
              "known-bad: SHADOW without a graduation criterion is caught (FAIL since the "
              "2026-09-08 promotion; it was WARN before, and the finding is the same one)")
        check("C-04", not has(h, "ES-1", "shadow_ok.py"), "known-good: SHADOW with criterion passes")
        # C-05/C-05b/C-05c are the two-sided control for the SEVERITY LEVER itself. Until
        # 2026-09-08 nothing tested that SEVERITY_PROMOTED does anything -- and four findings
        # hardcoded "WARN" instead of calling severity_for, so the promotion the docstring
        # promised was INERT for ES-1's graduation case, ES-3, ES-4 and ES-5. A trigger that
        # cannot fire is worse than none: it is still trusted.
        orig = lint.first_commit_date
        saved_prom = lint.SEVERITY_PROMOTED
        try:
            lint.first_commit_date = lambda home_, rp: "2026-08-01"
            lint.SEVERITY_PROMOTED = set()
            h2 = lint.check_hooks_header(home)
            check("C-05", has(h2, "ES-1", "bad_guard.py", "", "WARN"),
                  "birth-date rule with the promotion lifted: legacy (first commit before schema) -> WARN not FAIL")
            lint.SEVERITY_PROMOTED = {"ES-1"}
            h2b = lint.check_hooks_header(home)
            check("C-05b", has(h2b, "ES-1", "bad_guard.py", "", "FAIL")
                  and not has(h2b, "ES-1", "bad_guard.py", "", "WARN"),
                  "promotion lever: the SAME legacy fixture reports FAIL once ES-1 is in "
                  "SEVERITY_PROMOTED -- the named trigger is wired, not decorative")
        finally:
            lint.first_commit_date = orig
            lint.SEVERITY_PROMOTED = saved_prom
        check("C-05c", not ({"ES-7", "ES-8"} & lint.SEVERITY_PROMOTED),
              "the heuristics are NOT promotable: ES-7/ES-8 prompt a review and may never rule "
              "FAIL (a gate rules only on what it can DETERMINE)")
        w(home / "hooks" / "wrong_status.py", '"""x\n\nSTATUS: MAYBE since 2026-09-08.\n"""\n')
        sj = json.loads((home / "settings.json").read_text(encoding="utf-8"))
        sj["hooks"]["PreToolUse"][0]["hooks"].append({"type": "command", "command": "\"p\" \"C:/x/.claude/hooks/wrong_status.py\""})
        sj["hooks"]["PreToolUse"][0]["hooks"].append({"type": "command", "command": "\"p\" \"C:/x/.claude/hooks/absent.py\""})
        w(home / "settings.json", json.dumps(sj))
        h3 = lint.check_hooks_header(home)
        check("C-06", has(h3, "ES-1", "wrong_status.py", "not in", "FAIL"), "known-bad: STATUS value outside the set -> FAIL")
        check("C-07", has(h3, "ES-1", "absent.py", "absent on disk", "FAIL"), "known-bad: registered hook missing on disk -> FAIL")

        # ES-2 hook proof-of-life. The predicate is the DECLARATION in the hook's
        # own docstring (pol.py's grammar), not a position in integrity-sweep.md.
        p2 = lint.check_hooks_proof(home)
        check("C-08", has(p2, "ES-2", "bad_guard.py", "no `Proof-of-life:`", "FAIL"),
              "known-bad: no declaration -> FAIL (also absent from the sweep: the regression case "
              "for the position-based predicate replaced 2026-09-08)")
        check("C-09", not has(p2, "ES-2", "good_guard.py"),
              "known-good: a hook declaring a runnable suite passes")
        check("C-08b", has(p2, "ES-2", "manual_guard.py", "being NAMED in the sweep is not being RUN"),
              "known-bad: `manual` declaration (a sweep check, not a command) is reported, never accepted")
        check("C-08c", has(p2, "ES-2", "undet_guard.py", "unclassifiable", "UNDET")
              and not any(f.check == "ES-2" and "undet_guard" in f.path and f.severity in ("FAIL", "WARN")
                          for f in p2),
              "AP-62: an unclassifiable declaration is UNDET -- reported, and in NEITHER verdict count")
        check("C-08d", {f.path for f in p2 if f.check == "ES-2"} ==
              {"hooks/bad_guard.py", "hooks/manual_guard.py", "hooks/undet_guard.py",
               "hooks/wrong_status.py"},
              "coverage: exactly the hooks without an executable declaration are flagged, "
              "and a registered-but-absent hook is left to ES-1 (one absence, one finding)")
        saved_pol = lint.load_pol
        try:
            lint.load_pol = lambda h: None
            check("C-08e", any(f.check == "ANCHOR" and "pol.py" in f.path
                               for f in lint.check_hooks_proof(home)),
                  "anchor lost (the grammar's owner is gone) -> ANCHOR finding, never a clean pass")
        finally:
            lint.load_pol = saved_pol

        # ES-3 rule files
        r3 = lint.check_rule_files(home)
        check("C-10", has(r3, "ES-3", "bad-rule.md", "index line", "FAIL"), "known-bad: stem missing from CLAUDE.md index line -> FAIL")
        check("C-11", has(r3, "ES-3", "bad-rule.md", "review-when", "FAIL"), "known-bad: no review-when -> FAIL (ES-3 promoted 2026-09-08)")
        check("C-12", has(r3, "ES-3", "nofm.md", "no YAML frontmatter", "FAIL"), "known-bad: no frontmatter -> FAIL")
        check("C-13", not has(r3, "ES-3", "good-rule.md") and not has(r3, "ES-3", "ghost-mech.md"),
              "known-good: indexed + paths + review-when (section or key) passes")
        check("C-11b", not has(r3, "ES-3", "inline-rule.md"),
              "known-good: an inline `review-when: <event>` declaration, trigger wrapped onto the "
              "next line, passes (the 2026-09-08 widening)")
        check("C-11c", has(r3, "ES-3", "mentions-rule.md", "review-when", "FAIL"),
              "regression for that widening: a rule that only MENTIONS `review-when` (and carries a "
              "review DATE) is still caught")
        check("C-11d", has(r3, "ES-3", "empty-rule.md", "review-when", "FAIL"),
              "regression: `review-when:` with nothing after it is not a declaration")
        cm = home / "CLAUDE.md"
        saved = cm.read_text(encoding="utf-8")
        w(cm, "# prefs without the index line\n")
        r3b = lint.check_rule_files(home)
        check("C-14", any(f.check == "ANCHOR" and "CLAUDE.md" in f.path for f in r3b), "anchor lost (no index line) -> ANCHOR finding, never silence")
        w(cm, saved)

        # ES-4 trigger classes
        t4 = lint.check_trigger_classes(home)
        check("C-15", has(t4, "ES-4", "ghost-skill", "ghost entry", "FAIL"), "known-bad: block for a skill that does not exist -> FAIL")
        check("C-16", has(t4, "ES-4", "bad-enum", "not in", "FAIL") and has(t4, "ES-4", "bad-enum", "missing `on-fire:`", "FAIL"),
              "known-bad: enum outside the set + missing key -> FAIL")
        check("C-17", not has(t4, "ES-4", "real-skill"), "known-good: complete block with a `# comment` on on-fire passes")

        # ES-5 pointers
        p5 = lint.check_pointers(home)
        check("C-18", has(p5, "ES-5", "rules-usage-dict", "ops/references/nope.md", "FAIL"), "known-bad: §7 owner path dead -> FAIL")
        check("C-19", has(p5, "ES-5", "LABEL-REGISTRY", "skills/missing/SKILL.md", "FAIL"), "known-bad: LABEL-REGISTRY owner path dead -> FAIL")
        check("C-20", has(p5, "ES-5", "ghost-mech.md", "tools/nonexistent-lint", "FAIL"), "known-bad: rules/*.md names a mechanism that does not exist -> FAIL")
        check("C-21", not has(p5, "ES-5", "", "60-bootstrap.md") and not has(p5, "ES-5", "", "05-authority.md"),
              "known-good: resolvable owner paths (bare ops basename and full path) pass")
        check("C-22", has(p5, "ES-5", "thin entry", "why", "FAIL") and not has(p5, "ES-5", "good entry"),
              "rule-registry: entry lacking why/evidence -> FAIL (ES-5 promoted 2026-09-08, the "
              "container's legacy count having reached 0); complete entry passes")
        check("C-37", has(p5, "ES-5", "OPERATOR-GUIDE.md", "tools/ghost-tool/run.py", "FAIL")
              and has(p5, "ES-5", "OPERATOR-GUIDE.md", "glob `agents/*.md` matches nothing", "FAIL"),
              "known-bad: top-level doc names a missing tool, and a glob over an absent folder -> FAIL")
        guide = [f for f in p5 if f.path == "OPERATOR-GUIDE.md"]
        check("C-38", len(guide) == 2,
              "known-good: existing file, matching glob, <placeholder> and skill-relative path stay silent "
              f"(guide findings = {len(guide)}, expected exactly the two of C-37)")
        label = [f for f in p5 if "skills/missing/SKILL.md" in f.msg]
        check("C-39", len(label) == 1 and label[0].path == "LABEL-REGISTRY.md §2",
              f"a dead LABEL-REGISTRY §2 owner is reported once, by §2, not again by the top-level pass (got {len(label)})")

        # ES-6 guide citations
        g6 = lint.check_guide_citations(home)
        check("C-23", has(g6, "ES-6", "principle-design-guide", "Not a phrase", "FAIL") and has(g6, "ES-6", "principle-design-guide", "§一.9", "FAIL"),
              "known-bad: phrase absent from CLAUDE.md and missing PHILOSOPHY heading -> FAIL")
        check("C-24", not has(g6, "ES-6", "", "When authoring an invariant") and not has(g6, "ES-6", "", "§一.1 "),
              "known-good: verbatim phrase and existing heading pass")

        # ES-7 page builders
        b7 = lint.check_page_builders(bad)
        g7 = lint.check_page_builders(good)
        check("C-25", has(b7, "ES-7", "build_a.py", "data-page-class") and has(b7, "ES-7", "build_b.py", "data-audience")
              and has(b7, "ES-7", "build_a.py", "independent shells") and has(b7, "ES-7", "build_b.py", "independent shells"),
              "known-bad: two unshared shells without class/audience -> 3 WARN kinds, shell WARN per builder")
        check("C-26", not g7, "known-good: two builders sharing shell.py, both attrs emitted -> no findings")
        m7 = lint.check_page_builders(mixed)
        check("C-30", has(m7, "ES-7", "build_own.py", "independent shells") and not has(m7, "ES-7", "build_ok.py")
              and not has(m7, "ES-7", "shell.py") and len(m7) == 1,
              "mixed: own-root builder WARNed once; shell.py (2 importers) and the delegators pass; a helper is not a shell; a test import is not adoption")

        # ES-8 tool-bound rulings
        e8 = lint.check_tool_bound(home)
        check("C-27", has(e8, "ES-8", "bad-rule.md", "Whenever the pipeline emits", "WARN"), "known-bad: 'whenever the pipeline emits' -> WARN")
        check("C-28", not has(e8, "ES-8", "good-rule.md") and not has(e8, "ES-8", "real-skill"), "known-good: class-bound sentences pass")
        check("C-29", not has(e8, "ES-8", "ghost-mech.md", "named anti-pattern"), "quoting the anti-pattern (RD-1 on the line) is excluded")
        check("C-31", not has(e8, "ES-8", "ghost-mech.md", "old ruling read"),
              "a phrase inside quote marks with no other marker is excluded (regression pair for C-27)")

        # ES-9 watched (system-hmi registry coverage)
        e9 = lint.check_watched(home)
        check("C-32", has(e9, "ES-9", "hooks/bad_guard.py", "no row", "FAIL") and has(e9, "ES-9", "skills/bad-enum", "no row"),
              "known-bad: hook and skill dir with no subsystems.json row -> FAIL (untracked = born after schema)")
        check("C-32b", has(e9, "ES-9", "hooks/bad_guard.py", '{"glob": "hooks/bad_guard.py", "kind": "') and not has(e9, "ES-9", "hooks/good_guard.py", '"glob"'),
              "the FAIL text carries the exact row to add for the failing path (positive), and a registered path gets none (negative)")
        check("C-33", not has(e9, "ES-9", "hooks/good_guard.py") and not has(e9, "ES-9", "skills/real-skill"),
              "known-good: registered hook and skill pass")
        check("C-34", not has(e9, "ES-9", "hooks/shadow_ok.py"), "known-good: reasoned ignore.json row passes")
        check("C-35", has(e9, "ES-9", "hooks/manual_guard.py", "more than one subsystem", "FAIL"),
              "known-bad: a path matched by two subsystems is an overlap -> FAIL")
        no_hmi = root / "no-hmi"
        w(no_hmi / "settings.json", "{}")
        u9 = lint.check_watched(no_hmi)
        check("C-36", any(f.check == "ANCHOR" and "system-hmi" in f.path for f in u9) and not any(f.check == "ES-9" for f in u9),
              "undetermined: a tree with no system-hmi loses the anchor, ES-9 rules on nothing (never a clean pass)")

        # driver: exit codes
        rc_ok = lint.main(["--home", str(home)]) if False else None  # noqa: F841 (kept out: prints a full report)
    finally:
        if keep:
            print(f"fixture kept at {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)

    n = len(RESULTS)
    bad_n = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"ALL PASS {n}/{n}" if bad_n == 0 else f"FAILED {bad_n}/{n}")
    return 0 if bad_n == 0 else 1


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
