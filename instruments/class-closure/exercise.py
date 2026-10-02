#!/usr/bin/env python3
"""class exercise — does each control suite's unclassifiable case actually RUN?

Status: live 2026-09-23 | severity: WARN (born; promotion trigger below) for a
suite whose named case never executes, `undetermined` for a run this tool could
not observe (excluded from every count, never folded) | controls: `controls.py`
(the `exercise` block, two-sided) | wired: `ops/references/integrity-sweep.md`
check 33 (second command); HMI point `health-checks.class-exercise` (slow tier,
inputs tools/ + hooks/); NOT at save time -- it runs every suite, and
golive_check keeps closure.py's static verdict | principle: PH-11 / AP-62.

WHY THIS EXISTS BESIDE closure.py
---------------------------------
closure.py decides, statically, whether a suite NAMES the unclassifiable class
in a code token. Two shapes survive that proxy (measured 2026-09-23):
  * named, never exercised: a case string that never runs (dead code, a skipped
    block), or a --selftest hook whose word sits in PRODUCTION code while the
    selftest never touches the class;
  * exercised, never named: a real unclassifiable-input case whose name never
    uses the word (dispatch_commit_notice before c0b30ee).
Both are facts about execution, so this tool runs each suite once and watches.

THE EVIDENCE: which marker lines execute (coverage, not mutation)
-----------------------------------------------------------------
Every suite runs once with `probe/` on PYTHONPATH; its sitecustomize records,
in the suite process and every python child it spawns, which SITE lines run.
Sites are derived from the corpus, never listed here (PH-11 / AP-61):
  * a marker statement -- a statement with MARKER (closure.py's, imported) in a
    code token; comments and docstrings excluded exactly as closure.py does;
  * the first statement of the body of an `if` / `elif` / `case` whose TEST
    names the marker (`if kind == UNDET: return None` has its branch there);
  * a SHAPE site: the first statement of the body of an `if` whose test has a
    `not isinstance(...)` arm (alone, or inside an and/or). This is the
    WORDLESS form of the class -- hooks answer an unclassifiable payload with
    silence or None, never with the word. Measured 2026-09-23: without shape
    sites 33 of 51 suites stopped at `case-only` / `branch-unreached`; with
    them 15. Replayed on dispatch_commit_notice as of c0b30ee~1 (the recorded
    false negative) it turns `absent` into `unnamed-exercise`.
    Labels carry `(shape)` so the reader sees which evidence it was.
Each executed site gets a ROLE relative to the suite being judged:
  CASE    a NAMED site in the suite file -- for a suite that is its hook's own
          `--selftest`, only inside a top-level function whose name contains
          `selftest` (the rest of that file is the instrument). A shape site in
          the suite's own helpers is neither side;
  BRANCH  an instrument site inside a function AND inside a guarded block (an
          if/elif/else body, an except handler, a match case), a marker-test
          body, or a shape site: code that runs only when the class is taken;
  OTHER   a declaration or an unconditional mention (`UNDET = "undetermined"`,
          a report line printing the count) -- executing it proves nothing.
The probe also reports which mapped files RAN at all, so a named branch in a
file the suite touched but never drove is listed (`unreached`).

Mutation was measured against and rejected: a GENERIC fold operator does not
exist (folding means "return the nearest real class", which only the instrument
knows -- a per-instrument operator list is the hand list PH-11 forbids), and a
label-renaming mutant survives on every fail-open hook whose undetermined
outcome is silence. A declared per-suite case id was rejected too: 51 suite
rewrites to produce another word proxy.

CLASSES (per suite)
-------------------
  exercised         a CASE site and a BRANCH site both ran in a passing run
  branch-unreached  a CASE site ran, no BRANCH site did, and a file the suite
                    ran holds a NAMED branch that never executed: the case does
                    not drive the instrument's own named branch. Forwarded, not
                    counted -- the file may be a shared library whose branch
                    belongs to another suite (feedback_notice -> feedback.py,
                    2026-09-23, covered by feedback-pool's own suite)
  case-only         a CASE site ran, no BRANCH site did, no named branch was
                    left unreached: the instrument answers the class by some
                    other means (a command grammar, a table shape) or the case
                    never reaches it. NOT determinable which -> reported, not
                    counted as a finding (downgrade-and-forward)
  named-only        static `carries`, the run passed, and NO CASE site ran:
                    the word is there, the case is not. THE FINDING (WARN)
  unnamed-exercise  static `lacks` and a BRANCH site ran: the case exists and
                    only its name is missing (closure.py's FAIL still stands;
                    this row tells the fixer to rename, not to write)
  absent            static `lacks`, no BRANCH site ran: closure.py's finding
  undetermined      suite unreadable/missing, exit != 0, timeout, exit 3
                    (inconclusive), or the probe did not load in the suite
                    process -- nothing about the case was observed

WHAT IT STILL CANNOT SEE (stated, not hidden)
---------------------------------------------
Line execution is not assertion: a CASE line that runs a check whose result is
discarded still reads as run. The CASE and BRANCH sites are matched per SUITE,
not per case: a shape guard run by some OTHER case of the same suite counts
(attributing a branch to the case that drove it was tried on paper and dropped
-- the live suites act first and assert on a later line, or loop over a table
whose marker sits on the table's name, so the case LINE is not where the work
happens). An `or` arm widens a shape guard beyond pure type mismatch, and a
`not isinstance` guard can also FILTER A LEGAL VARIANT: measured 2026-09-23,
hooks/delivery_gate_shadow.py skips transcript records whose `content` is a
string (a normal user turn), so the e2-gate suite reads `exercised` in the
canonical tree (live transcripts present) and `case-only` in a linked worktree
(none) -- the shape evidence there comes from the environment, not from the
suite's unclassifiable case. A shape-only `exercised` is therefore the weakest
row; the label says `(shape)` so it is never mistaken for a named one. A python
child spawned with a scrubbed environment (or -I/-E) runs untraced. A branch
that answers without the word and without a type guard is invisible, which is
exactly what `case-only` reports rather than guesses. `unnamed-exercise` can
also fire on a lacking suite whose shape guards run in normal operation; it
never changes closure.py's FAIL, so it is advice to the fixer, not a verdict.

COST (measured 2026-09-23, 51 suites): serial 227.9 s plain vs 233.2 s traced
(+2.3%, inside run-to-run noise), 51/51 identical exit codes; the default 4
workers finish in ~80 s. Each suite is run through `pol.run_suite` (telemetry
isolated, exit 3 = inconclusive, 420 s timeout), the same runner as check 31.

SEVERITY AND PROMOTION
----------------------
Born WARN (gate-severity-by-consumer: a new mechanism's first real output never
feeds downstream in the same step); only `named-only` counts. Promotion trigger,
recorded here so it is not a memory: two sweeps on different days, the first
no earlier than 2026-09-30, both read 0 `named-only` with `controls.py` green
-> `named-only` becomes FAIL and the WARN branch is deleted with a regression
case, as closure.py's was. (The live tree read 0 on its birth day; a same-day
promotion would rest on the mechanism's first output alone.)
Exit codes: 0 PASS, 1 WARN, 2 FAIL (reserved until promotion).

BASELINE 2026-09-23, canonical tree (the one the sweep and the HMI read): 51
suites -- 37 exercised (18 through a named branch, 19 through a shape site
only), 14 case-only, 0 branch-unreached, 0 named-only, 0 unnamed-exercise,
0 absent, 0 undetermined -> PASS. A linked worktree reads 36 / 15 (e2-gate, see
the limit above). Triage of the case-only rows (all instrument limits: the
class is a value of a command grammar, a table shape or an enum, answered
without the word or a type guard) is in
a dated evidence note (private, not shipped).
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import os
import sys
import tempfile
import time
import tokenize
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import closure  # noqa: E402  (suites, classify, MARKER, HOME -- one enumeration)
pol = closure.pol   # run_suite, TIMEOUT, EXIT_INCONCLUSIVE, declaration

PROBE_DIR = HERE / "probe"
CORPUS = ("tools", "hooks", "skills")          # where instruments live
SKIP_PARTS = {"node_modules", ".venv", "venv", "__pycache__", "archive"}
CLASSES = ("exercised", "branch-unreached", "case-only", "named-only", "unnamed-exercise", "absent",
           "undetermined")
GUARDED = {("If", "body"), ("If", "orelse"), ("ExceptHandler", "body"), ("match_case", "body")}


# --------------------------------------------------------------------------- sites
def _marker_lines(text: str, tree: ast.AST) -> set[int]:
    doc = closure._docstring_lines(tree)
    hits = set()
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE):
            continue
        if tok.type == tokenize.STRING and tok.start[0] in doc:
            continue
        if closure.MARKER.search(tok.string):
            hits.add(tok.start[0])
    return hits


def _header(node: ast.stmt) -> tuple[int, int]:
    """Line span of a statement's own text: a compound statement stops before its body."""
    hi = node.end_lineno or node.lineno
    for field in ("body", "orelse", "finalbody", "handlers", "cases"):
        kids = getattr(node, field, None)
        if isinstance(kids, list) and kids and hasattr(kids[0], "lineno"):
            hi = min(hi, kids[0].lineno - 1)
    return node.lineno, max(hi, node.lineno)


def _shape_guard(test: ast.expr) -> bool:
    """A test that holds when a value matches NO declared type: `not isinstance(...)`, alone or
    as one arm of an `and` / `or` (`sid is not None and not isinstance(sid, str)`). The
    wordless form of the unclassifiable branch; an `or` arm may widen it, which is stated in
    the module docstring as a limit rather than filtered here."""
    if isinstance(test, ast.BoolOp):
        return any(_shape_guard(v) for v in test.values)
    return (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)
            and isinstance(test.operand, ast.Call) and isinstance(test.operand.func, ast.Name)
            and test.operand.func.id == "isinstance")


def file_sites(text: str) -> list[dict]:
    """-> [{lo, hi, top, branch, shape}] for one Python source. Raises SyntaxError on non-Python.

    `top` is the enclosing top-level function name (None at module/class level);
    `branch` is True for a site that runs only when the class is taken; `shape` marks a
    branch found by structure (the body of a `not isinstance` guard) rather than by the word.
    """
    tree = ast.parse(text)
    marks = _marker_lines(text, tree)
    sites: dict[tuple[int, int], dict] = {}

    def visit(node, top, in_fn, guarded):
        for field, val in ast.iter_fields(node):
            for kid in (val if isinstance(val, list) else [val]):
                if not isinstance(kid, ast.AST):
                    continue
                t, f, g = top, in_fn, guarded
                if isinstance(kid, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                    if top is None and not isinstance(kid, ast.Lambda):
                        t = kid.name
                    f, g = True, False
                elif in_fn and (type(node).__name__, field) in GUARDED:
                    g = True
                if isinstance(kid, ast.stmt):
                    lo, hi = _header(kid)
                    if any(lo <= m <= hi for m in marks):
                        # innermost statement wins: children are visited after parents
                        for key in [k for k in sites if k[0] <= lo and hi <= k[1] and k != (lo, hi)]:
                            del sites[key]
                        sites[(lo, hi)] = {"lo": lo, "hi": hi, "top": t, "branch": f and g,
                                           "shape": False}
                    test = getattr(kid, "test", None)
                    if isinstance(kid, ast.If) and f and kid.body and test is not None:
                        named = any(test.lineno <= m <= (test.end_lineno or test.lineno) for m in marks)
                        if named or _shape_guard(test):
                            blo, bhi = _header(kid.body[0])
                            sites.setdefault((blo, bhi), {"lo": blo, "hi": bhi, "top": t,
                                                          "branch": True, "shape": not named})
                if isinstance(kid, ast.match_case) and f and kid.body:
                    pat = kid.pattern
                    if any(pat.lineno <= m <= (pat.end_lineno or pat.lineno) for m in marks):
                        blo, bhi = _header(kid.body[0])
                        sites.setdefault((blo, bhi), {"lo": blo, "hi": bhi, "top": t, "branch": True,
                                                      "shape": False})
                visit(kid, t, f, g)

    visit(tree, None, False, False)
    return sorted(sites.values(), key=lambda s: s["lo"])


def site_index(root: Path) -> dict[str, list[dict]]:
    """-> {normcased abs path: sites} over every .py in CORPUS. Unparseable files are skipped:
    a file that is not Python has no sites, and a suite depending on one says so by its run."""
    index = {}
    for sub in CORPUS:
        base = root / sub
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            if SKIP_PARTS.intersection(p.parts):
                continue
            try:
                s = file_sites(p.read_text(encoding="utf-8"))
            except (SyntaxError, ValueError, UnicodeDecodeError, OSError, tokenize.TokenError):
                continue
            if s:
                index[os.path.normcase(str(p.resolve()))] = s
    return index


def probe_map(index: dict[str, list[dict]]) -> dict[str, list[int]]:
    return {f: sorted({ln for s in sites for ln in range(s["lo"], s["hi"] + 1)})
            for f, sites in index.items()}


# --------------------------------------------------------------------------- run
def command(root: Path, rel: str, via: str) -> str | None:
    """The command the suite is run by -- the declared one for a declared suite (pol's own
    grammar), `python <rel>` otherwise, exactly what check 33 / check 31 run."""
    if via.startswith("declared by hooks/"):
        kind, detail = pol.declaration(root / via[len("declared by "):])
        return detail if kind == "executable" else None
    return f"python {rel}"


def run(root: Path, rel: str, via: str, map_path: Path, workdir: Path) -> dict:
    """-> {ok, summary, starts, errors, hits:{(file, line)}}. Never raises."""
    cmd = command(root, rel, via)
    if cmd is None:
        return {"ok": None, "summary": "declaration no longer executable", "starts": 0,
                "errors": [], "hits": set()}
    out = workdir / (rel.replace("/", "__") + ".probe")
    out.unlink(missing_ok=True)
    extra = {"PYTHONPATH": os.pathsep.join(filter(None, [str(PROBE_DIR), os.environ.get("PYTHONPATH")])),
             "CC_PROBE_MAP": str(map_path), "CC_PROBE_OUT": str(out)}
    parts = cmd.split()
    if parts[0] == "python" and "-X" not in parts[1:3]:
        parts[1:1] = ["-X", "utf8"]
    ok, summary = pol.run_suite(" ".join(parts), root=root, env_extra=extra)
    starts, errors, hits, files = 0, [], set(), set()
    if out.exists():
        for line in out.read_text(encoding="utf-8", errors="replace").splitlines():
            kind, _, rest = line.partition("\t")
            if kind == "start":
                starts += 1
            elif kind == "error":
                errors.append(rest)
            elif kind == "file":
                files.add(rest)
            elif kind == "hit":
                f, _, ln = rest.rpartition("\t")
                if ln.isdigit():
                    hits.add((f, int(ln)))
    return {"ok": ok, "summary": summary, "starts": starts, "errors": errors, "hits": hits,
            "files": files}


# --------------------------------------------------------------------------- judge
def roles(root: Path, rel: str, via: str, hits: set, index: dict,
          files: set | None = None) -> dict[str, list[str]]:
    """Partition executed sites into CASE / BRANCH / OTHER for the suite `rel`, plus
    `unreached`: branch sites in instrument files that RAN (probe `file` records) whose
    lines never did -- the named branches the suite's case did not drive."""
    suite = os.path.normcase(str((root / rel).resolve()))
    own_selftest = via.startswith("declared by hooks/") and \
        os.path.normcase(str((root / via[len("declared by "):]).resolve())) == suite

    def in_case_region(f, site):
        return f == suite and (not own_selftest or bool(site["top"] and "selftest" in site["top"].lower()))

    out = {"case": set(), "branch": set(), "other": set()}
    ran_sites = set()
    for f, ln in hits:
        site = next((s for s in index.get(f, ()) if s["lo"] <= ln <= s["hi"]), None)
        if site is None:
            continue
        ran_sites.add((f, site["lo"]))
        label = f"{Path(f).name}:{site['lo']}" + (" (shape)" if site["shape"] else "")
        if in_case_region(f, site):
            # a case is NAMED; a type guard inside the suite's own helpers is neither side
            out["other" if site["shape"] else "case"].add(label)
        elif site["branch"]:
            out["branch"].add(label)
        else:
            out["other"].add(label)
    unreached = {f"{Path(f).name}:{s['lo']}" for f in (files or ()) for s in index.get(f, ())
                 if s["branch"] and not s["shape"] and not in_case_region(f, s)
                 and (f, s["lo"]) not in ran_sites}
    return {**{k: sorted(v) for k, v in out.items()}, "unreached": sorted(unreached)}


def judge(static: str, result: dict | None, r: dict | None) -> tuple[str, str]:
    """-> (class, detail) from the static verdict, the run, and the role partition."""
    if static == "undetermined":
        return "undetermined", "closure.py cannot read the suite"
    if result is None or result["ok"] is None:
        return "undetermined", (result or {}).get("summary", "not run")
    if result["ok"] == "inconclusive":
        return "undetermined", f"suite inconclusive: {result['summary']}"
    if result["ok"] is not True:
        return "undetermined", f"suite did not pass, so no run was observed: {result['summary']}"
    if result["starts"] == 0 or result["errors"]:
        why = result["errors"][0] if result["errors"] else "probe never loaded in the suite process"
        return "undetermined", f"probe: {why}"
    case, branch = r["case"], r["branch"]
    if static == "lacks":
        if branch:
            return "unnamed-exercise", f"branch ran: {', '.join(branch[:3])}"
        return "absent", "no branch site ran and the suite names no case"
    if case and branch:
        return "exercised", f"case {', '.join(case[:2])} · branch {', '.join(branch[:3])}"
    if case and r.get("unreached"):
        return "branch-unreached", (f"case {', '.join(case[:2])} ran; named branch(es) in code it "
                                    f"touched never did: {', '.join(r['unreached'][:4])}")
    if case:
        return "case-only", (f"case {', '.join(case[:2])} ran; no instrument it touched names the "
                             f"class in a branch")
    return "named-only", "the suite names the class but no case line naming it ran"


def scan(root: Path | None = None, only: list[str] | None = None, jobs: int = 4,
         settings: Path | None = None) -> list[dict]:
    root = (root or closure.HOME).resolve()
    index = site_index(root)
    work = Path(tempfile.mkdtemp(prefix="class-exercise-"))
    map_path = work / "map.json"
    map_path.write_text(json.dumps(probe_map(index)), encoding="utf-8")
    todo = [(rel, via) for rel, via in closure.suites(root, settings).items()
            if not only or any(o in rel for o in only)]

    def one(item):
        rel, via = item
        static = closure.classify(root / rel)[0]
        t = time.monotonic()
        res = None if static == "undetermined" else run(root, rel, via, map_path, work)
        part = (roles(root, rel, via, res["hits"], index, res["files"]) if res
                else {"case": [], "branch": [], "other": [], "unreached": []})
        kind, detail = judge(static, res, part)
        return {"suite": rel, "via": via, "static": static, "class": kind, "detail": detail,
                "case": part["case"], "branch": part["branch"], "other": len(part["other"]),
                "unreached": part["unreached"],
                "procs": res["starts"] if res else 0, "seconds": round(time.monotonic() - t, 1)}

    with ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        rows = list(ex.map(one, todo))
    return rows


def verdict(rows: list[dict]) -> tuple[str, str]:
    named = [r["suite"] for r in rows if r["class"] == "named-only"]
    undet = [r["suite"] for r in rows if r["class"] == "undetermined"]
    note = f"; {len(undet)} undetermined (excluded from every count)" if undet else ""
    if named:
        return "WARN", (f"WARN: {len(named)} suite(s) name the unclassifiable class but never run "
                        f"a case for it: {', '.join(named)}{note}")
    return "PASS", f"PASS: no suite names the class without running a case for it{note}"


def report(rows: list[dict], verbose: bool = False) -> int:
    counts = {c: sum(1 for r in rows if r["class"] == c) for c in CLASSES}
    print(f"class-exercise: {len(rows)} suite(s) — " +
          ", ".join(f"{counts[c]} {c}" for c in CLASSES))
    for r in rows:
        if verbose or r["class"] in ("named-only", "unnamed-exercise", "branch-unreached", "undetermined"):
            print(f"  {r['class']:16} {r['suite']}  {r['detail']}  [{r['seconds']}s, {r['procs']} proc]")
    level, line = verdict(rows)
    print(line)
    return {"PASS": 0, "WARN": 1, "FAIL": 2}[level]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=None, help="repo root (controls only)")
    ap.add_argument("--only", nargs="*", default=None, help="substring filter on suite paths")
    ap.add_argument("--jobs", type=int, default=4, help="suites run in parallel (default 4)")
    ap.add_argument("--json", action="store_true", help="rows as JSON, no verdict line")
    ap.add_argument("--verbose", action="store_true", help="print every row")
    a = ap.parse_args(argv)
    rows = scan(a.root, a.only, a.jobs)
    if a.json:
        print(json.dumps(rows, indent=1, ensure_ascii=False))
        return 0
    return report(rows, a.verbose)


if __name__ == "__main__":
    sys.exit(main())
