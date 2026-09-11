#!/usr/bin/env python3
"""Sweep check 7b -- cap VALUE drift between the mechanism and the rule text.

WHY THIS EXISTS (the measured case, 2026-08-27)
-----------------------------------------------
`ops/40-maintenance.md` S3 promises that any threshold living BOTH as rule text
and in a mechanism "carries a drift check", and named sweep check 7 as that
check. Check 7 is:

    grep -nE 'getsize|len\\(text\\)|len\\(m\\.group|count\\("' hooks/ops_health_nudge.py

which can only ever show the UNIT. It cannot see a number, so it had never
covered the value at all. Sweep check 10 catches a cap literal copied into a
SECOND .py mechanism -- also not this. Under that gap, three constants drifted
across four sites:

    DICT_CAP        hook 28K   | hook docstring 24K | S3 table 20K | registry 24K
    CLAUDE_MD_CAP   hook 19968 | hook docstring 15K | S3 table 15K | registry ok
    SIZE_CAP        hook 22K   | hook docstring 15K | S3 table ok  | registry ok

The visible consequence: `skill-trigger-dict.md` was 2.6K over the enforced cap
and every rule file a reader might consult said it was fine.

WHAT IT RULES ON
----------------
Only what it can determine: for each constant it reads the value from the
MECHANISM (the hook, by AST -- so `28 * 1024` and `19968` are both understood)
and compares it with every site that restates it. Three verdicts:

    ok           the site agrees with the mechanism
    DRIFT        the site states a different value  -> exit 1
    ANCHOR LOST  the site's text moved and the binding no longer matches
                 anything -> exit 2. NOT silence: a check that quietly stops
                 looking is worse than no check (40-maintenance.md S3).

SEVERITY: FAIL (exit non-zero), not warn. The consumer is a hard reference --
a reader deciding whether a file is over budget acts on the number, and the two
values disagree in a way no reading can reconcile.

The strongest form of this check is the one it cannot perform: DELETE the
restatement. The hook's docstring now names its constants instead of copying
their values, which is why `docstring-checklist` below asserts an ABSENCE
rather than an agreement -- a name cannot drift from the thing it names.

USAGE
    python tools/ops-health-test/check_cap_binding.py
    python tools/ops-health-test/check_cap_binding.py --selftest

`--selftest` is the calibration this check's own rules demand: it feeds a
known-TRUE input (everything agreeing -> must report clean) AND a known-FALSE
input (one value moved, one anchor destroyed -> must report exactly those). A
checker that has only ever been shown broken input scores 100% on a one-sided
calibration. Run it after touching this file.

Stdlib only, read-only. Resolves the repo from its own path, so it works in a
git worktree -- unlike the hook, which is pinned to ~/.claude by design.
"""
import ast
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO, "hooks", "ops_health_nudge.py")
MAINT = os.path.join(REPO, "ops", "40-maintenance.md")
REGISTRY = os.path.join(REPO, "ops", "rule-registry.md")

# constant -> [(site label, file, anchor regex capturing ONE value token)]
# The anchor is deliberately anchored on words a rewrite would keep and a
# RETITLING would not: losing it is reported, never assumed benign.
BINDINGS = {
    "CLAUDE_MD_CAP": [
        ("40-maintenance S3 table", MAINT,
         r"(?m)^\s*\|\s*global `CLAUDE\.md`[^|]*\|\s*([^|]+?)\s*\|"),
        ("rule-registry `CLAUDE_MD_CAP`", REGISTRY,
         r"(?s)### `CLAUDE_MD_CAP`.*?\n- current:\s*\**\s*([0-9][0-9,.]*\s*"
         r"[KkMm]?)"),
    ],
    "DICT_CAP": [
        ("40-maintenance S3 table", MAINT,
         r"(?m)^\s*\|\s*`skill-trigger-dict\.md`\s*\|\s*([^|]+?)\s*\|"),
        ("rule-registry `routing dict cap`", REGISTRY,
         r"(?s)### routing dict cap.*?\n- current:\s*\**\s*([0-9][0-9,.]*\s*"
         r"[KkMm]?)"),
    ],
    "SIZE_CAP": [
        ("40-maintenance S3 table", MAINT,
         r"(?m)^\s*\|\s*any `ops/\*\.md`[^|]*\|\s*([^|]+?)\s*\|"),
        ("rule-registry `ops file cap`", REGISTRY,
         r"(?s)### ops file cap.*?\n- current:\s*\**\s*([0-9][0-9,.]*\s*"
         r"[KkMm]?)"),
    ],
    "DESC_CAP": [
        ("40-maintenance S3 table", MAINT,
         r"(?m)^\s*\|\s*skill frontmatter description[^|]*\|\s*([^|]+?)\s*\|"),
        ("rule-registry `DESC_CAP`", REGISTRY,
         r"(?s)### `DESC_CAP`.*?\n- current:\s*\**\s*([0-9][0-9,.]*\s*"
         r"[KkMm]?)"),
    ],
    "BODY_CAP": [
        ("40-maintenance S3 table", MAINT,
         r"(?m)^\s*\|\s*any `SKILL\.md` body\s*\|\s*([^|]+?)\s*\|"),
        ("rule-registry `BODY_CAP`", REGISTRY,
         r"(?s)### `BODY_CAP`.*?\n- current:\s*\**\s*([0-9][0-9,.]*\s*"
         r"[KkMm]?)"),
    ],
    # LESSON_CAP binding removed 2026-09-07: the cap was retired with the
    # lesson intake cutover (ops/lessons.md is a generated index with no count
    # cap; tools/closeout-intake). Its intake caps are NOT file caps -- they
    # live in intake_core.DEFAULT_CAPS and the registry names them without
    # restating the values (rule-registry `INTAKE_FIELD_CAPS`), so there is no
    # second site to drift against and nothing for this check to bind.
}

VALUE_RX = re.compile(r"([0-9][0-9,]*(?:\.[0-9]+)?)\s*([KkMm])?")


def parse_value(text):
    """First number in `text`, K/M applied. None when there is no number.

    Tolerates the shapes rule text actually uses: `~22K`, `28K`, `19,968`,
    `19.5K`, `800`, `**300 lines**`.
    """
    m = VALUE_RX.search(text or "")
    if not m:
        return None
    n = float(m.group(1).replace(",", ""))
    mult = {"k": 1024, "m": 1024 * 1024}.get((m.group(2) or "").lower(), 1)
    return int(round(n * mult))


def hook_caps(src):
    """{name: int} for every module-level `X_CAP`-ish assignment in the hook.

    AST, not regex: sweep check 15 reads these with `r'NAME *= *(\\d+) *\\* *
    1024'` and has been CRASHING since 2026-08-18, when CLAUDE_MD_CAP became a
    plain 19968 and stopped matching -- so it has silently covered neither
    CLAUDE.md nor skill-trigger-dict.md since. The literal form is not a
    property worth depending on.
    """
    caps = {}
    for node in ast.parse(src).body:
        if not isinstance(node, ast.Assign):
            continue
        v = const_int(node.value)
        if v is None:
            continue
        for t in node.targets:
            if isinstance(t, ast.Name):
                caps[t.id] = v
    return caps


def const_int(node):
    """int value of a constant-arithmetic expression, else None.

    `ast.literal_eval` is NOT enough and the --selftest caught that on its
    first run: it rejects `28 * 1024` (a BinOp, not a literal), so the two caps
    written that way came back missing and every case reported ANCHOR LOST.
    A checker that cannot read half the constants it audits would have passed a
    one-sided calibration -- it fires on everything.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, int) \
            and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp):
        a, b = const_int(node.left), const_int(node.right)
        if a is None or b is None:
            return None
        if isinstance(node.op, ast.Mult):
            return a * b
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
    return None


def checklist_lines(src):
    """The numbered check list in the hook's module docstring."""
    doc = ast.get_docstring(ast.parse(src)) or ""
    return [l for l in doc.splitlines() if re.match(r"^\s*\d+\.\s", l)]


def audit(hook_src, docs, caps=None):
    """[(status, constant, site, expected, found)]. Pure -- no file I/O.

    `docs` maps a path to its text, so --selftest can pass synthetic ones.
    """
    caps = caps if caps is not None else hook_caps(hook_src)
    out = []
    for const, sites in BINDINGS.items():
        want = caps.get(const)
        if want is None:
            out.append(("ANCHOR LOST", const, "hooks/ops_health_nudge.py",
                        "a module-level int assignment", "not found"))
            continue
        for label, path, rx in sites:
            text = docs.get(path, "")
            m = re.search(rx, text)
            if not m:
                out.append(("ANCHOR LOST", const, label,
                            "a site matching the binding regex", "no match"))
                continue
            got = parse_value(m.group(1))
            if got is None:
                out.append(("ANCHOR LOST", const, label,
                            "a number", repr(m.group(1).strip())))
            elif got != want:
                out.append(("DRIFT", const, label, want, got))
            else:
                out.append(("ok", const, label, want, got))

    # The absence property: no cap VALUE may appear in the docstring check
    # list. Dates and check numbers are not cap-shaped and do not trip it.
    # Only the constants this check actually binds. Scanning against EVERY
    # module-level int made "(audit 1st)" and "(40-maintenance S2)" read as cap
    # restatements, because SEV_LOSS is 1 and SEV_BREACH is 2 -- a gate ruling
    # on more than it can determine. Found by the live run, one step after the
    # selftest went green: a clean calibration does not license the first real
    # output (global CLAUDE.md, gate rule).
    cap_values = {caps[c] for c in BINDINGS if c in caps}
    for line in checklist_lines(hook_src):
        # strip the list number itself -- "7." is not a restated cap
        body = re.sub(r"^\s*\d+\.\s*", "", line)
        for tok, suffix in VALUE_RX.findall(body):
            if not tok:
                continue
            if suffix or parse_value(tok + (suffix or "")) in cap_values:
                out.append(("DRIFT", "docstring-checklist",
                            "hooks/ops_health_nudge.py docstring",
                            "constant NAMES only", line.strip()))
                break
    return out


def report(rows, quiet_ok=True):
    bad = [r for r in rows if r[0] != "ok"]
    for status, const, site, want, got in rows:
        if status == "ok" and quiet_ok:
            continue
        print(f"  {status:<12} {const:<20} {site}")
        if status != "ok":
            print(f"               mechanism says {want!r}, "
                  f"site says {got!r}")
    return bad


# --------------------------------------------------------------------------
# calibration: a known-TRUE input and a known-FALSE input, both required.
#
# The synthetic hook is ASSEMBLED, never written out as literal source lines.
# Writing the assignments out as source in this file makes sweep check 10
# ("cap VALUE drift across mechanisms" -- a grep in tools/ and hooks/ for a
# _CAP name assigned a KiB product) report hits in the very checker that
# exists to prevent cap drift. They would be false positives: a fixture is
# test data, not a second mechanism holding a live copy. Keep it assembled --
# and do not quote the offending shape in a comment either, which is how this
# note first tripped the same grep.
FIXTURE_CAPS = [("SIZE_CAP", 22 * 1024),
                ("DESC_CAP", 800), ("BODY_CAP", 300),
                ("CLAUDE_MD_CAP", 19968), ("DICT_CAP", 28 * 1024)]
TRUE_HOOK = ('"""Doc.\n\n'
             "  2. any ops/*.md over SIZE_CAP -> extract\n"
             "  7. CLAUDE.md over CLAUDE_MD_CAP -> breach\n"
             '"""\n'
             + "".join("%s = %d\n" % nv for nv in FIXTURE_CAPS))
FALSE_HOOK = TRUE_HOOK.replace(
    "  7. CLAUDE.md over CLAUDE_MD_CAP -> breach",
    "  7. CLAUDE.md > 15K BYTES -> breach")
NO_DICT_HOOK = TRUE_HOOK.replace("DICT_CAP = %d\n" % (28 * 1024), "")

TRUE_MAINT = """
  | global `CLAUDE.md` (trim/merge, never append) | 19,968 (19.5K) | bytes |
  | skill frontmatter description (x every skill) | ~800 | chars |
  | any `ops/*.md` - except `lessons.md` | ~22K | bytes |
  | `skill-trigger-dict.md` | 28K | bytes |
  | any `SKILL.md` body | ~300 | lines |
"""
TRUE_REGISTRY = """
### `CLAUDE_MD_CAP` - x
- current: **19,968 bytes (19.5 KiB)**
### `BODY_CAP` - x
- current: 300 lines
### `DESC_CAP` - x
- current: 800 chars hard / 700 birth budget
### routing dict cap
- current: **28K bytes on `skill-trigger-dict.md`**
### ops file cap
- current: **22K bytes per `ops/*.md`**
"""


def selftest():
    ok = True

    def case(name, rows, expect):
        nonlocal ok
        got = sorted((s, c, t) for s, c, t, _, _ in rows if s != "ok")
        if got != sorted(expect):
            ok = False
            print(f"INSTRUMENT FAILURE  {name}\n  expected {sorted(expect)}"
                  f"\n  got      {got}")
        else:
            print(f"pass  {name}")

    # known-TRUE: everything agrees. A checker that cannot return clean is a
    # checker whose 100% hit rate means nothing.
    case("known-TRUE: all sites agree -> clean",
         audit(TRUE_HOOK, {MAINT: TRUE_MAINT, REGISTRY: TRUE_REGISTRY}), [])

    # known-FALSE 1: the real 2026-08-27 defect, one value moved.
    drifted = TRUE_MAINT.replace("| `skill-trigger-dict.md` | 28K |",
                                 "| `skill-trigger-dict.md` | ~20K |")
    case("known-FALSE: S3 table 20K vs hook 28K -> DRIFT",
         audit(TRUE_HOOK, {MAINT: drifted, REGISTRY: TRUE_REGISTRY}),
         [("DRIFT", "DICT_CAP", "40-maintenance S3 table")])

    # known-FALSE 2: a value copied back into the docstring check list.
    case("known-FALSE: docstring restates 15K -> DRIFT",
         audit(FALSE_HOOK, {MAINT: TRUE_MAINT, REGISTRY: TRUE_REGISTRY}),
         [("DRIFT", "docstring-checklist",
           "hooks/ops_health_nudge.py docstring")])

    # known-FALSE 3: the site was retitled. Must be ANCHOR LOST, never "ok".
    case("known-FALSE: registry heading renamed -> ANCHOR LOST",
         audit(TRUE_HOOK, {MAINT: TRUE_MAINT,
                           REGISTRY: TRUE_REGISTRY.replace(
                               "### routing dict cap", "### dict size")}),
         [("ANCHOR LOST", "DICT_CAP", "rule-registry `routing dict cap`")])

    # known-FALSE 4: the constant vanished from the mechanism.
    case("known-FALSE: constant deleted from the hook -> ANCHOR LOST",
         audit(NO_DICT_HOOK, {MAINT: TRUE_MAINT, REGISTRY: TRUE_REGISTRY}),
         [("ANCHOR LOST", "DICT_CAP", "hooks/ops_health_nudge.py")])

    print("\nselftest: " + ("all cases ruled correctly"
                            if ok else "INSTRUMENT IS NOT TRUSTWORTHY"))
    return 0 if ok else 2


def main():
    if "--selftest" in sys.argv[1:]:
        return selftest()
    with open(HOOK, encoding="utf-8") as f:
        hook_src = f.read()
    docs = {}
    for p in (MAINT, REGISTRY):
        with open(p, encoding="utf-8") as f:
            docs[p] = f.read()
    rows = audit(hook_src, docs)
    print(f"cap binding: {len(rows)} site(s) checked against "
          f"hooks/ops_health_nudge.py")
    bad = report(rows, quiet_ok="-v" not in sys.argv[1:])
    if not bad:
        print("  all sites agree with the mechanism")
        return 0
    return 2 if any(s == "ANCHOR LOST" for s, *_ in bad) else 1


if __name__ == "__main__":
    sys.exit(main())
