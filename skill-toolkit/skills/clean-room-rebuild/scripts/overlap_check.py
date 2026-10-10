#!/usr/bin/env python3
r"""overlap_check — surface-copy gate for a clean-room rebuild.

Compares OUR text (a concept spec card, or the rebuilt deliverable) against the
SOURCE it was derived from, and rules only on what it can determine: verbatim
or near-verbatim runs, and (for a spec) code blocks and the source's distinctive
identifiers. It never prints source text — only counts, candidate line numbers
and identifier names, so its output can travel into a transcript or a record.

Property served: skills/clean-room-rebuild/SKILL.md "a rebuilt asset carries no
source expression". Calibration: scripts/controls.py (positive, negative and
mutation controls; run it after any threshold change).

Usage
  overlap_check.py --source PATH [PATH...] --candidate FILE [--kind spec|output]
                   [--merger NAME,NAME] [--terms NAME,NAME] [--json]
                   [--k N] [--run-fail N] [--cont-fail X]

  PATH may be a file or a directory (text files are walked; .git, node_modules,
  build output are skipped). The gate reads PLAIN TEXT only: a PDF, DOCX, EPUB
  or other packaged document is not read — convert it to a text snapshot first
  (SKILL.md Step 0) and pass the snapshot.

Unread sources (counted apart, never silently)
  binary      a NUL byte in the first 4 KB (images, archives of code, blobs)
  document    a PDF / ZIP-packaged document (DOCX, EPUB, ODT ...) by magic bytes
  too_large   a single file over 2 MB
  over_cap    every file after the 20 MB total was reached (sorted path order)
  unreadable  an OS error
  A document, too_large, over_cap or unreadable skip means the gate did not see
  all of the source: NO-SURFACE-COPY is then withheld and the verdict is UNDET
  (FAIL and WARN still stand — what was seen was seen). A binary skip does not
  withhold it: those files hold no prose the gate could compare.

Verdicts (one line, then reasons)
  FAIL             a shared run >= RUN_FAIL tokens, or containment >= CONT_FAIL,
                   or (kind=spec) a code fence other than ```io, or a distinctive
                   source identifier not declared on a `merger:` or `terms:` line
  WARN             a shared run >= RUN_WARN tokens or containment >= CONT_WARN, or
                   (kind=output) a distinctive identifier shared with the source
                   and not passed in --merger/--terms — forwarded to a human or
                   main-loop read, never a veto
  NO-SURFACE-COPY  none of the above, over a fully read source. This is NOT
                   "clean": structure, ordering and selection (SSO) copied in new
                   words pass this gate.
  UNDET            the instrument cannot rule: candidate shorter than 3*K tokens,
                   no readable source text, or part of the source unread (above).
                   Not a pass: resolve the reason and re-run.

Exit: 0 = NO-SURFACE-COPY / WARN, 1 = FAIL, 2 = usage or I/O error, 3 = UNDET.
Tokens: NFKC + lower-case; each CJK character is one token; a run of word
characters in any other script (Latin with accents, Cyrillic, Greek, digits,
underscore) is one token; punctuation and whitespace are dropped. Names passed
as merger (interface names that MUST match) are dropped from both sides before
shingling, so a compatible interface does not count as copied prose.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

K = 10            # shingle length in tokens
RUN_FAIL = 25     # longest shared run (tokens) that is copying, not coincidence
RUN_WARN = 14
CONT_FAIL = 0.15  # share of candidate shingles found in the source
CONT_WARN = 0.04

SKIP_DIRS = {".git", "node_modules", "__pycache__", "dist", "build", ".venv", "venv",
             ".tox", ".mypy_cache", ".idea", ".vscode", "target", "out"}
MAX_FILE = 2_000_000
MAX_TOTAL = 20_000_000
DOC_MAGIC = (b"%PDF-", b"PK\x03\x04", b"\xd0\xcf\x11\xe0")   # PDF, ZIP container, OLE2 (.doc)
UNREAD_KINDS = ("document", "too_large", "over_cap", "unreadable")   # withhold NO-SURFACE-COPY

_CJK = "㐀-鿿豈-﫿぀-ヿ가-힯"
_TOKEN = re.compile(rf"[{_CJK}]|[^\W{_CJK}]+")
_IDENT = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{3,}\b")
_FENCE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)", re.M)
_DECL = {name: re.compile(rf"^\s*[-*]?\s*{name}\s*[:：]\s*(.+)$", re.M | re.I)
         for name in ("merger", "terms")}


def tokens_with_lines(text: str):
    """[(token, line_no)] over NFKC-lower-cased text."""
    out = []
    for ln, line in enumerate(unicodedata.normalize("NFKC", text).lower().splitlines(), 1):
        out.extend((m.group(0), ln) for m in _TOKEN.finditer(line))
    return out


def distinctive(name: str, private: bool = False) -> bool:
    """snake_case, camelCase/PascalCase-with-inner-capital, or letters+digits.
    With `private` (output mode), a single-word leading-underscore name such as
    `_cache` counts too; dunders (`__init__`) never do."""
    if name.startswith("__") and name.endswith("__"):
        return False
    if "_" in name.strip("_"):
        return True
    if private and name.startswith("_"):
        return True
    if re.search(r"[a-z][A-Z]", name):
        return True
    return bool(re.search(r"[A-Za-z]\d|\d[A-Za-z]", name)) and len(name) >= 5


def read_sources(paths, exclude=None):
    """(texts, skips): text of every readable source file, and a count per skip
    reason (see the module docstring). `exclude` (the candidate) is never read
    as a source, even when it sits inside a source directory."""
    texts = []
    skips = {k: 0 for k in ("binary",) + UNREAD_KINDS}
    exclude = Path(exclude).resolve() if exclude else None
    total = 0

    def take(p: Path):
        nonlocal total
        if exclude is not None and p.resolve() == exclude:
            return
        try:
            size = p.stat().st_size
            if size > MAX_FILE:
                skips["too_large"] += 1
                return
            if total + size > MAX_TOTAL:
                skips["over_cap"] += 1
                return
            raw = p.read_bytes()
        except OSError:
            skips["unreadable"] += 1
            return
        if raw.startswith(DOC_MAGIC):
            skips["document"] += 1
            return
        if b"\x00" in raw[:4096]:
            skips["binary"] += 1
            return
        total += len(raw)
        texts.append(raw.decode("utf-8", errors="replace"))

    for s in paths:
        p = Path(s)
        if p.is_file():
            take(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and not (SKIP_DIRS & set(f.relative_to(p).parts[:-1])):
                    take(f)
        else:
            raise FileNotFoundError(s)
    return texts, skips


def declared(candidate: str, kind: str, extra=()) -> set:
    """Names on the candidate's `kind:` lines (`merger:` / `terms:`) plus `extra`.
    A parenthetical on the line is the reason, not a name."""
    out = set(extra)
    for m in _DECL[kind].finditer(candidate):
        names = re.split(r"[(（]", m.group(1), maxsplit=1)[0]
        out.update(x.strip(" `'\"") for x in re.split(r"[,，、\s]+", names) if x.strip())
    return out


def check(source_texts, candidate: str, kind: str = "output", k: int = K,
          run_fail: int = RUN_FAIL, run_warn: int = RUN_WARN,
          cont_fail: float = CONT_FAIL, cont_warn: float = CONT_WARN,
          merger=(), terms=(), unread: int = 0) -> dict:
    """`unread`: source files the caller could not read as text (document,
    too_large, over_cap, unreadable). Non-zero withholds NO-SURFACE-COPY."""
    merger_names = declared(candidate, "merger", merger) if kind == "spec" else set(merger)
    term_names = declared(candidate, "terms", terms) if kind == "spec" else set(terms)
    masked = {t for n in merger_names for t, _ in tokens_with_lines(n)}

    cand = [(w, ln) for w, ln in tokens_with_lines(candidate) if w not in masked]
    src_shingles = set()
    src_idents = set()
    private = kind == "output"
    for t in source_texts:
        toks = [w for w, _ in tokens_with_lines(t) if w not in masked]
        src_shingles.update(hash(tuple(toks[i:i + k])) for i in range(len(toks) - k + 1))
        src_idents.update(n for n in _IDENT.findall(t) if distinctive(n, private))

    res = {"kind": kind, "k": k, "candidate_tokens": len(cand), "reasons": [],
           "longest_run": 0, "containment": 0.0, "run_lines": [],
           "code_fences": [], "leaked_identifiers": [], "merger_declared": sorted(merger_names),
           "terms_declared": sorted(term_names), "unread_sources": unread}
    if not src_shingles or len(cand) < 3 * k:
        res["verdict"] = "UNDET"
        res["reasons"].append("no readable source text (a PDF/DOCX/EPUB or URL needs a text "
                              "snapshot first)" if not src_shingles
                              else f"candidate has {len(cand)} tokens < 3*K={3 * k}")
        return res

    words = [w for w, _ in cand]
    n_sh = len(words) - k + 1
    covered = [False] * len(words)
    hits = 0
    for i in range(n_sh):
        if hash(tuple(words[i:i + k])) in src_shingles:
            hits += 1
            for j in range(i, i + k):
                covered[j] = True
    res["containment"] = round(hits / n_sh, 4)
    run = best = 0
    start = 0
    for i, c in enumerate(covered + [False]):
        if c:
            if run == 0:
                start = i
            run += 1
        else:
            if run > best:
                best = run
            if run >= run_warn:
                res["run_lines"].append([cand[start][1], cand[i - 1][1], run])
            run = 0
    res["longest_run"] = best

    fail = warn = False
    if best >= run_fail:
        fail = True
        res["reasons"].append(f"shared run of {best} tokens >= {run_fail}")
    elif best >= run_warn:
        warn = True
        res["reasons"].append(f"shared run of {best} tokens >= {run_warn} (read it)")
    if res["containment"] >= cont_fail:
        fail = True
        res["reasons"].append(f"containment {res['containment']:.1%} >= {cont_fail:.0%}")
    elif res["containment"] >= cont_warn:
        warn = True
        res["reasons"].append(f"containment {res['containment']:.1%} >= {cont_warn:.0%} (read it)")

    exempt = merger_names | term_names
    if kind == "spec":
        inside = False
        for ln, line in enumerate(candidate.splitlines(), 1):
            m = _FENCE.match(line)
            if not m:
                continue
            if not inside:
                inside = True
                if m.group(2).lower() != "io":
                    res["code_fences"].append(ln)
            else:
                inside = False
        if res["code_fences"]:
            fail = True
            res["reasons"].append("code fence in a spec card (only ```io blocks of "
                                  f"input/output examples are allowed): lines {res['code_fences']}")
        found = {n for n in _IDENT.findall(candidate) if n in src_idents and n not in exempt}
        if found:
            fail = True
            res["leaked_identifiers"] = sorted(found)
            res["reasons"].append(f"{len(found)} distinctive source identifier(s) not on a "
                                  f"`merger:` or `terms:` line: {', '.join(sorted(found)[:12])} "
                                  "(interface name -> merger; product/standard name such as "
                                  "GitHub or SHA256 -> terms; anything else -> rewrite)")
    else:
        # A result may legitimately share public interface names (pass them as
        # `merger`), but a shared PRIVATE name is the usual trace of recall from
        # training data (dry run 2026-10-09: `_compile_pattern`). Library names
        # (`lru_cache`) also land here; the reader dismisses those.
        shared = {n for n in _IDENT.findall(candidate) if n in src_idents and n not in exempt}
        if shared:
            warn = True
            res["shared_identifiers"] = sorted(shared)
            res["reasons"].append(f"{len(shared)} distinctive identifier(s) shared with the source "
                                  f"(read them; rename any that are not interface or library names): "
                                  f"{', '.join(sorted(shared)[:12])}")

    res["verdict"] = "FAIL" if fail else "WARN" if warn else "NO-SURFACE-COPY"
    if res["verdict"] == "NO-SURFACE-COPY" and unread:
        res["verdict"] = "UNDET"
        res["reasons"].append(f"{unread} source file(s) not read as text (document format, size "
                              "or total cap): no surface copy in what was read, the rest unseen")
    return res


RULER = ("ruler: rules on verbatim runs (K={k} tokens), containment, and for a spec its "
         "code fences + distinctive source identifiers (output: shared identifiers -> WARN). "
         "Not covered: copied structure, ordering or selection in new words; text inside "
         "unread files; patents; whether the source may be used at all.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", nargs="+", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--kind", choices=["spec", "output"], default="output")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--k", type=int, default=K)
    ap.add_argument("--run-fail", type=int, default=RUN_FAIL)
    ap.add_argument("--cont-fail", type=float, default=CONT_FAIL)
    ap.add_argument("--merger", default="",
                    help="comma-separated interface names the result may share with the source")
    ap.add_argument("--terms", default="",
                    help="comma-separated product/standard names (GitHub, SHA256) both may mention")
    a = ap.parse_args(argv)
    try:
        texts, skips = read_sources(a.source, exclude=a.candidate)
        cand = Path(a.candidate).read_text(encoding="utf-8")
    except (OSError, FileNotFoundError) as e:
        print(f"overlap_check: cannot read input: {e}", file=sys.stderr)
        return 2
    run_warn = min(RUN_WARN, a.run_fail)
    split = lambda s: [x.strip() for x in s.split(",") if x.strip()]  # noqa: E731
    unread = sum(skips[k] for k in UNREAD_KINDS)
    r = check(texts, cand, a.kind, a.k, a.run_fail, run_warn, a.cont_fail, min(CONT_WARN, a.cont_fail),
              merger=split(a.merger), terms=split(a.terms), unread=unread)
    r["source_files"] = len(texts)
    r["source_files_skipped"] = skips
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        skipped = ", ".join(f"{k} {v}" for k, v in skips.items() if v) or "none"
        print(f"{r['verdict']}  kind={r['kind']}  longest_run={r['longest_run']}  "
              f"containment={r['containment']:.1%}  candidate_tokens={r['candidate_tokens']}  "
              f"sources={len(texts)} (skipped: {skipped})")
        for x in r["reasons"]:
            print(f"  - {x}")
        for a1, b1, n in r["run_lines"]:
            print(f"  - candidate lines {a1}-{b1}: shared run of {n} tokens")
        print(RULER.format(k=r["k"]))
    return {"FAIL": 1, "UNDET": 3}.get(r["verdict"], 0)


if __name__ == "__main__":
    sys.exit(main())
