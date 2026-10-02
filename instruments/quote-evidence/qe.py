r"""quote-evidence — pointer evidence for copyrighted source pages.

A claim drawn from a book page, a scanned handout or a paywalled PDF carries a
LOCATOR (which page, which paragraph) and ONE short quote (<= MAX_Q CJK-eq).
This tool proves the quote is on the named page by fuzzy-matching it against a
LOCAL OCR of the page. Nothing here ever prints the OCR text: the OCR files are
an instrument, written to a scratch/build folder and read only by `check`.

Property served: `rules/source-quotation-evidence.md` (a transcript of a
copyrighted page is never an artifact, a dispatch prompt or a model output;
evidence is locator + short quote + this local instrument). Born 2026-09-28
from the 當代中文 verb-section deck, where two verbatim-transcription attempts
(the main loop, then a subagent) died on `API Error: 400 Output blocked by
content filtering policy`.

Commands
  qe.py ocr IMAGE... --out DIR [--lang zh-Hant-TW]
        upscale grey copies into DIR/_in, run the Windows OCR engine
        (ocr.ps1), write DIR/<image-stem>.txt; prints line counts only.
  qe.py match --text-dir DIR --stem STEM --quote Q
  qe.py check REGISTRY --text-dir DIR [--verify VERIFY.json]

Registry shape (JSON): {"sources": {"<key>": "<ocr-stem>"},
  "claims": [{"id": "...", "anchors": [{"loc": "<key>·¶3", "q": "..."}]}]}
Locator key = text before the first `·`, `:` or space. VERIFY.json (optional,
written by a verdict-only verifier that looked at the image):
  {"quotes": {"<claim-id>|<quote>": "match" | "mismatch"}}

Verdicts per anchor
  PASS  score >= PASS_AT, or verifier "match"
  UNDET score in [UNDET_AT, PASS_AT), or quote shorter than MIN_Q normalized
        chars and not an exact hit — forwarded to an image check, never a veto
  FAIL  score < UNDET_AT; quote longer than MAX_Q; locator names no source;
        verifier "mismatch" (overrides any score)
  undetermined  the instrument could not rule: OCR file missing, anchor not an
        object, quote/locator not a string. Listed separately, excluded from
        every count above.

Ruler (printed after every `check`): the score says a quote OCCURS on the page
(presence). It cannot say that the quote SUPPORTS the claim, that a paraphrase
adds nothing, or that a table cell is right. Measured blind spot, pinned by
control C5: a one-character negation flip inside a quote (要 -> 不要) still
scores >= PASS_AT. Those classes go to a verdict-only verifier (reports
match/mismatch and paraphrase findings, never transcribes).

Calibration (2026-09-28, 4 CJK scans, 86 quotes): true quotes 0.75–1.00 after
upscaling, fabricated <= 0.67; hence PASS_AT 0.80 / UNDET_AT 0.60. Re-measure
with a new OCR engine, language, or scan quality class.

Severity: exit 1 on any FAIL (a quote not on its page is a hard defect for the
deliverable it feeds); UNDET and undetermined exit 0 but are printed with the
repair step.

Extending: a new source kind (PDF page, slide image) adds a backend that writes
DIR/<stem>.txt and leaves `check` unchanged; a new verdict row adds a control
pair (true + false) to controls.py in the same commit.

Proof-of-life: `python tools/quote-evidence/controls.py`
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
PASS_AT, UNDET_AT = 0.80, 0.60
MAX_Q = 15          # CJK-equivalent units per quote (one CJK char or one Latin word/number = 1)
MIN_Q = 6           # normalized chars below which a fuzzy score means nothing

_DROP = re.compile(r"[\s　「」『』（）()，,。．.、：:；;！!？?\-–—…·*＊\[\]〔〕]")
_LOC_SPLIT = re.compile(r"[·:：\s]")

RULER = ("ruler: score = fuzzy presence of the quote in the page's local OCR text "
         f"(PASS>={PASS_AT}, UNDET>={UNDET_AT}, min {MIN_Q} chars, max {MAX_Q} CJK-eq). "
         "Not covered: whether the quote SUPPORTS the claim, paraphrase drift, table "
         "cells, a one-char negation flip (control C5) — route those to a verdict-only "
         "image verifier.")


def norm(text: str) -> str:
    return _DROP.sub("", unicodedata.normalize("NFKC", text)).lower()


def cjk_eq(q: str) -> int:
    q = unicodedata.normalize("NFKC", q)
    return len(re.findall(r"[㐀-鿿]", q)) + len(re.findall(r"[A-Za-z]+(?:-[A-Za-z]+)?|\d+", q))


def best_score(quote: str, hay_norm: str) -> float:
    q = norm(quote)
    if not q or not hay_norm:
        return 0.0
    if q in hay_norm:
        return 1.0
    n, best = len(q), 0.0
    for w in {max(1, n - 2), max(1, n - 1), n, n + 1, n + 2}:   # absorb dropped/added OCR chars
        for i in range(0, max(1, len(hay_norm) - w + 1)):
            r = difflib.SequenceMatcher(None, q, hay_norm[i:i + w], autojunk=False).ratio()
            if r > best:
                best = r
                if best == 1.0:
                    return best
    return best


def loc_key(loc: str) -> str:
    return _LOC_SPLIT.split(loc.strip(), 1)[0]


def judge(quote, loc, sources: dict, text_dir: Path, verdict=None, cache=None):
    """Return (verdict, score|None, reason). verdict in PASS/UNDET/FAIL/undetermined."""
    if not isinstance(quote, str) or not isinstance(loc, str):
        return "undetermined", None, "quote/locator is not a string"
    key = loc_key(loc)
    if key not in sources:
        return "FAIL", None, f"locator {loc!r} names no source (known: {', '.join(sources)})"
    if cjk_eq(quote) > MAX_Q:
        return "FAIL", None, f"quote is {cjk_eq(quote)} CJK-eq > {MAX_Q}: shorten it to the fact-bearing words"
    f = text_dir / f"{sources[key]}.txt"
    if not f.exists():
        return "undetermined", None, f"OCR text missing: {f} — run `qe.py ocr` first"
    cache = cache if cache is not None else {}
    if f not in cache:
        cache[f] = norm(f.read_text(encoding="utf-8"))
    s = best_score(quote, cache[f])
    if verdict == "mismatch":
        return "FAIL", s, "verifier: quote not on the page image"
    if verdict == "match":
        return "PASS", s, "verified on the image"
    # a short quote's fuzzy score is noise (3 chars vs a 2-char hit = 0.80): only an exact hit counts
    if len(norm(quote)) < MIN_Q and s < 1.0:
        return "UNDET", s, f"quote shorter than {MIN_Q} chars and not exact — lengthen it or send to the image verifier"
    if s >= PASS_AT:
        return "PASS", s, ""
    if s >= UNDET_AT:
        return "UNDET", s, "send to the image verifier"
    return "FAIL", s, "not found on the page: fix the quote or the locator"


def check(registry: dict, text_dir: Path, verify: dict | None = None):
    sources = registry.get("sources") if isinstance(registry, dict) else None
    claims = registry.get("claims") if isinstance(registry, dict) else None
    if not isinstance(sources, dict) or not isinstance(claims, list):
        return [("undetermined", "-", None, "registry lacks a `sources` object or a `claims` list")]
    qv = ((verify or {}).get("quotes") or {}) if isinstance(verify, dict) else {}
    rows, cache = [], {}
    for c in claims:
        if not isinstance(c, dict):
            rows.append(("undetermined", "?", None, "claim is not an object"))
            continue
        cid = str(c.get("id", "?"))
        for a in c.get("anchors") or []:
            if not isinstance(a, dict):
                rows.append(("undetermined", cid, None, "anchor is not an object"))
                continue
            v, s, why = judge(a.get("q"), a.get("loc"), sources, text_dir,
                              qv.get(f"{cid}|{a.get('q')}"), cache)
            rows.append((v, cid, s, why))
    return rows


def report(rows) -> int:
    counts = {k: 0 for k in ("PASS", "UNDET", "FAIL")}
    und = []
    for v, cid, s, why in rows:
        if v == "undetermined":
            und.append((cid, why))
            continue
        counts[v] += 1
        if v != "PASS":
            sc = "-" if s is None else f"{s:.2f}"
            print(f"{v:5} {cid} score={sc} {why}")
    print(f"quote-evidence: PASS {counts['PASS']} · UNDET {counts['UNDET']} · FAIL {counts['FAIL']}"
          f" · undetermined {len(und)} (excluded)")
    for cid, why in und:
        print(f"  undetermined {cid}: {why}")
    print(RULER)
    return 1 if counts["FAIL"] else 0


def ocr(images, out: Path, lang: str) -> int:
    from PIL import Image
    tmp = out / "_in"
    tmp.mkdir(parents=True, exist_ok=True)
    for p in images:
        im = Image.open(p).convert("L")
        s = 2 if im.width < 1000 else 1.5      # an 823-px scan OCRed at 0.69; upscaled, 0.85+
        im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS).save(tmp / (Path(p).stem + ".png"))
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                        str(HERE / "ocr.ps1"), "-InDir", str(tmp), "-OutDir", str(out), "-Lang", lang],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
    return r.returncode


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("ocr")
    o.add_argument("images", nargs="+")
    o.add_argument("--out", required=True, type=Path)
    o.add_argument("--lang", default="zh-Hant-TW")
    m = sub.add_parser("match")
    m.add_argument("--text-dir", required=True, type=Path)
    m.add_argument("--stem", required=True)
    m.add_argument("--quote", required=True)
    c = sub.add_parser("check")
    c.add_argument("registry", type=Path)
    c.add_argument("--text-dir", required=True, type=Path)
    c.add_argument("--verify", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "ocr":
        return ocr(a.images, a.out, a.lang)
    if a.cmd == "match":
        v, s, why = judge(a.quote, a.stem, {a.stem: a.stem}, a.text_dir)
        return report([(v, a.stem, s, why)])
    reg = json.loads(a.registry.read_text(encoding="utf-8"))
    ver = json.loads(a.verify.read_text(encoding="utf-8")) if a.verify else None
    return report(check(reg, a.text_dir, ver))


if __name__ == "__main__":
    sys.exit(main())
