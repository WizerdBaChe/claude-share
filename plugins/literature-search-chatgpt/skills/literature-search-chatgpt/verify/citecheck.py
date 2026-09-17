#!/usr/bin/env python3
r"""citecheck — the machine half of this skill's anti-fabrication gate.

WHY THIS EXISTS. Everything the skill did before this file was self-report: the
same model that might fabricate a citation also decided whether the citation was
fabricated. Two measurements say that is not enough:

  * ALCE (Gao et al., EMNLP 2023, arXiv:2305.14627): on ELI5, even the best
    systems "lack complete citation support 50% of the time" — the citation is
    real, the claim is not in it.
  * Search Arena (Miroyan et al., ICLR 2026, arXiv:2506.05334, n=24,069):
    people rate answers higher for having MORE citations "even when the cited
    content does not directly support the attributed claims".

So the dangerous failure is not the invented DOI. It is the REAL source cited
for something it does not say — invisible to a reader, invisible to identifier
resolution, and rewarded by human judgement.

THE MOVE. Whether a source SUPPORTS a claim is not machine-determinable without
an entailment model. But it becomes determinable if the writer must name the
exact span it relies on: a script cannot judge support, and it CAN check that
the quoted span exists verbatim in the retrieved text. That turns an opinion
into a falsifiable statement. A fabricated support span fails here, loudly,
without any ML.

WHAT IT RULES ON, and only this (gate-severity-by-consumer, 2026-08-26):

  FAIL — determinable and closed:
    identifier does not resolve · resolved metadata contradicts the citation ·
    support_span absent from the retrieved text · no locator · access tag
    above what was actually retrieved
  WARN — undeterminable here, forwarded not vetoed:
    no local text stored for the source (span uncheckable) · network down ·
    [abstract]/[secondary] rows, where span checking is out of scope
  NEVER RULES ON: whether the span, granted it exists, actually entails the
    claim. That stays a human/model judgement and the ledger makes it auditable
    by printing claim and span side by side.

INPUT — an evidence ledger, JSONL, one load-bearing claim per line. Write it
BEFORE running this (the gate must not be able to destroy what it rejects):

  {"claim_id": "C1",
   "claim": "Single-crystal Ag films reach L_spp = 200 um at 780 nm.",
   "source_id": "10.1021/nl803811g",          # DOI | arXiv:2305.14627 | PMID:… | ISBN:…
   "cite_as": "Nagpal 2009",                   # what the deliverable prints
   "expect_year": 2009,                        # optional, checked if present
   "locator": "Fig. 3",
   "access_tag": "full",                       # full|partial|abstract|secondary
   "support_span": "propagation length of 200 um",   # verbatim from the source
   "source_text": "sources/nagpal2009.txt"}    # what was actually retrieved

Usage:
    python citecheck.py ledger.jsonl              # full run
    python citecheck.py ledger.jsonl --offline    # structure + spans, no network
    python citecheck.py --selftest                # two-sided calibration
    python citecheck.py ledger.jsonl --json

Exit: 0 = no FAIL. 1 = at least one FAIL. 2 = bad usage.
review-when: Crossref or the arXiv export API changes its response shape.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TIMEOUT = 15
_BASE_UA = "literature-search-extract-citecheck/1 (local, interactive)"

# CONTACT IS PER-HOST, NEVER GLOBAL. A contact-bearing User-Agent buys politeness
# (arXiv 429s unidentified clients harder, and identification is the channel for
# asking about a higher rate). But it also leaves an attributable query trail on
# whichever host receives it, so consent is per-service and does not generalise:
# the user approved arXiv on 2026-08-27 and declined Unpaywall and the Crossref
# polite pool in the same breath. One shared UA would have quietly overridden
# that. Add a host here ONLY on an explicit per-service approval.
CONTACT_BY_HOST = {
    "arxiv.org": "<contact-email>",          # adopter supplies per-service consent
    "export.arxiv.org": "<contact-email>",   # same service, same approval
}
TAG_RANK = {"secondary": 0, "abstract": 1, "partial": 2, "full": 3}


def ua_for(url: str) -> dict:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    contact = CONTACT_BY_HOST.get(host)
    return {"User-Agent": f"{_BASE_UA} mailto:{contact}" if contact else _BASE_UA}


# --------------------------------------------------------------------------
# normalization — a quote survives a PDF; it should survive this too
# --------------------------------------------------------------------------
LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi",
             "ﬄ": "ffl", "’": "'", "‘": "'", "“": '"',
             "”": '"', "–": "-", "—": "-", "−": "-",
             " ": " ", " ": " ", " ": " "}


def norm(text: str) -> str:
    """Collapse the differences a copy out of a PDF or HTML legitimately makes.

    Deliberately NOT fuzzy: it undoes typography and line wrapping, never
    wording. `de-\nvice` becomes `device`; "roughly 200" never becomes "200".
    """
    if not text:
        return ""
    # NFKC already folds ligatures, the non-breaking spaces, and the micro sign
    # (to Greek mu, NOT to "u" — which is why 'um' vs 'micro-m' stays a wording
    # difference and must fail). The table below covers only what NFKC leaves
    # alone: curly quotes and the dash family. Its ligature/space entries are
    # therefore no-ops kept for readability, not a second normalization rule.
    text = unicodedata.normalize("NFKC", text)
    for a, b in LIGATURES.items():
        text = text.replace(a, b)
    text = re.sub(r"-\s*\n\s*", "", text)     # hyphenation across a line break
    text = re.sub(r"\s+", " ", text)
    return text.strip().casefold()


def span_present(span: str, haystack: str) -> bool:
    return bool(span) and norm(span) in norm(haystack)


# --------------------------------------------------------------------------
# identifier resolution
# --------------------------------------------------------------------------
def _get(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=ua_for(url)),
                                    timeout=TIMEOUT) as r:
            return r.status, r.read(400_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, ""
    except Exception:                                       # noqa: BLE001
        return 0, ""


def resolve(source_id: str) -> dict:
    """Return {'ok': bool, 'title': str, 'year': int|None, 'authors': [str], 'via': str}."""
    sid = (source_id or "").strip()
    low = sid.lower()

    if low.startswith("arxiv:") or re.fullmatch(r"\d{4}\.\d{4,5}(v\d+)?", sid):
        aid = sid.split(":", 1)[1] if ":" in sid else sid
        status, body = _get("https://export.arxiv.org/api/query?id_list="
                            + urllib.parse.quote(aid))
        if status != 200 or "<entry>" not in body:
            return {"ok": False, "via": "arxiv"}
        title = re.search(r"<entry>.*?<title>(.*?)</title>", body, re.S)
        year = re.search(r"<published>(\d{4})", body)
        authors = re.findall(r"<name>(.*?)</name>", body)
        return {"ok": True, "via": "arxiv",
                "title": re.sub(r"\s+", " ", title.group(1)).strip() if title else "",
                "year": int(year.group(1)) if year else None,
                "authors": authors}

    if low.startswith("10.") or low.startswith("doi:"):
        doi = sid.split(":", 1)[1] if low.startswith("doi:") else sid
        status, body = _get("https://api.crossref.org/works/"
                            + urllib.parse.quote(doi, safe=""))
        if status != 200:
            return {"ok": False, "via": "crossref"}
        try:
            m = json.loads(body)["message"]
        except Exception:                                   # noqa: BLE001
            return {"ok": False, "via": "crossref"}
        parts = (m.get("issued", {}).get("date-parts") or [[None]])[0]
        return {"ok": True, "via": "crossref",
                "title": (m.get("title") or [""])[0],
                "year": parts[0] if parts else None,
                "authors": [a.get("family", "") for a in m.get("author", [])]}

    if low.startswith("pmid:"):
        pmid = sid.split(":", 1)[1]
        status, body = _get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
                            f"esummary.fcgi?db=pubmed&retmode=json&id={pmid}")
        if status != 200:
            return {"ok": False, "via": "pubmed"}
        try:
            rec = json.loads(body)["result"][pmid]
        except Exception:                                   # noqa: BLE001
            return {"ok": False, "via": "pubmed"}
        yr = re.match(r"(\d{4})", rec.get("pubdate", "") or "")
        return {"ok": True, "via": "pubmed", "title": rec.get("title", ""),
                "year": int(yr.group(1)) if yr else None,
                "authors": [a.get("name", "") for a in rec.get("authors", [])]}

    return {"ok": False, "via": "unsupported"}


def metadata_conflict(row: dict, meta: dict) -> str | None:
    """Only flags a CONTRADICTION, never a mere absence — the gate's own rule."""
    cite = (row.get("cite_as") or "").strip()
    surname = cite.split()[0].casefold() if cite else ""
    authors = [a.casefold() for a in meta.get("authors") or []]
    if surname and authors and not any(surname in a or a in surname for a in authors):
        return (f"cite_as names '{cite.split()[0]}' but the resolved record's "
                f"authors are {meta.get('authors')[:4]}")

    want = row.get("expect_year")
    if want is None:
        m = re.search(r"\b(1[89]\d{2}|20\d{2})\b", cite)
        want = int(m.group(1)) if m else None
    got = meta.get("year")
    if want and got and abs(int(want) - int(got)) > 1:
        return f"cite_as implies {want}, resolved record says {got}"
    return None


# --------------------------------------------------------------------------
# the checks
# --------------------------------------------------------------------------
def check_row(row: dict, base: Path, offline: bool,
              resolver=None) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    tag = (row.get("access_tag") or "").strip().lower()

    if not row.get("locator"):
        out.append(("locator", "FAIL",
                    "no locator — an extracted item nobody can re-find is not "
                    "traceable, whatever it cites"))
    if tag not in TAG_RANK:
        out.append(("access_tag", "FAIL", f"access_tag {tag!r} is not one of "
                                          f"{sorted(TAG_RANK)}"))

    sid = row.get("source_id")
    if not sid:
        out.append(("identifier", "FAIL", "no source_id"))
    elif offline:
        out.append(("identifier", "WARN", "--offline: resolution skipped"))
    else:
        meta = (resolver or resolve)(sid)
        if not meta.get("ok"):
            out.append(("identifier", "FAIL",
                        f"{sid} did not resolve via {meta.get('via')} — an "
                        f"identifier that does not resolve must not appear in a "
                        f"deliverable (SKILL.md failure mode #1)"))
        else:
            conflict = metadata_conflict(row, meta)
            if conflict:
                out.append(("metadata", "FAIL", conflict))
            else:
                out.append(("identifier", "OK",
                            f"{sid} -> {meta['via']}: "
                            f"{(meta.get('title') or '')[:56]!r} ({meta.get('year')})"))

    # Span checking follows the TEXT, not the tag. An [abstract] row is a claim
    # about a text that WAS retrieved — the tag limits what may be claimed from
    # it, not whether the quote can be verified. Only [secondary] is exempt:
    # there the text was never in hand, which is what the tag means.
    span, ref = row.get("support_span"), row.get("source_text")
    if tag == "secondary":
        out.append(("support", "WARN",
                    "[secondary] row — the text was never retrieved, so no span "
                    "is checkable. Attribute as 'B, as cited in A' and keep A's "
                    "own row in the ledger"))
    elif not span:
        out.append(("support", "FAIL",
                    "no support_span. A [full]/[partial] claim must name the "
                    "exact text it rests on, or its support is unfalsifiable — "
                    "the failure mode ALCE and Search Arena both measured"))
    elif not ref:
        out.append(("support", "WARN",
                    "support_span given but no source_text stored, so it cannot "
                    "be verified. Store what was retrieved BEFORE the gate runs"))
    else:
        p = (base / ref) if not Path(ref).is_absolute() else Path(ref)
        if not p.exists():
            out.append(("support", "FAIL", f"source_text {ref} not found"))
        else:
            text = p.read_text(encoding="utf-8", errors="replace")
            if span_present(span, text):
                out.append(("support", "OK",
                            f"span found verbatim in {p.name} ({len(text):,} chars)"))
            else:
                out.append(("support", "FAIL",
                            f"support_span is NOT in {p.name}. Either the quote "
                            f"was reconstructed from memory or the wrong source "
                            f"was attached: {span[:64]!r}"))
            if tag == "full" and len(text) < 2000:
                out.append(("access_tag", "WARN",
                            f"tagged [full] but only {len(text):,} chars stored — "
                            f"if that is an abstract, the tag overstates"))
    return out


# --------------------------------------------------------------------------
# calibration
# --------------------------------------------------------------------------
def selftest(tmp: Path) -> int:
    tmp.mkdir(parents=True, exist_ok=True)
    src = tmp / "source.txt"
    src.write_text(
        "We report a propagation length of 200 um at 780 nm for atomically "
        "smooth single-crystalline silver films. " + ("filler. " * 300),
        encoding="utf-8")

    clean = {"claim_id": "OK1", "claim": "L_spp is 200 um at 780 nm.",
             "source_id": "arXiv:2305.14627", "cite_as": "Gao 2023",
             "locator": "Sec. 3", "access_tag": "full",
             "support_span": "propagation length of 200 um at 780 nm",
             "source_text": str(src)}

    # (label, row, want_fail) — the expectation lives IN the case, never in a
    # parallel list: a parallel list is how a calibration silently inverts.
    cases = [
        ("must-PASS: clean row", clean, False),
        ("must-PASS: collapsed whitespace",
         {**clean, "support_span": "propagation   length of 200 um  at 780 nm"}, False),
        ("must-PASS: hyphenation across a line break (PDF copy-out)",
         {**clean, "support_span": "propa-\ngation length of 200 um"}, False),
        ("must-PASS: curly quotes and ligature folded",
         {**clean, "support_span": "atomically smooth single-crystalline silver ﬁlms"},
         False),
        # NOT typography: NFKC folds the micro sign to Greek mu, never to "u".
        # 'um' and 'µm' are different characters in the source, so this is a
        # wording difference and MUST fail — the gate never guesses intent.
        ("must-FAIL: 'µm' where the source wrote 'um'",
         {**clean, "support_span": "propagation length of 200 µm at 780 nm"}, True),
        ("must-FAIL: fabricated identifier",
         {**clean, "source_id": "10.9999/this-doi-does-not-exist-12345"}, True),
        ("must-FAIL: real source, span it never said",
         {**clean, "support_span": "propagation length of 900 um at 1550 nm"}, True),
        ("must-FAIL: hedge the source never wrote ('roughly 200')",
         {**clean, "support_span": "propagation length of roughly 200 um"}, True),
        ("must-FAIL: wrong author attached to a real id",
         {**clean, "cite_as": "Nagpal 2009", "expect_year": 2009}, True),
        ("must-FAIL: no locator", {**clean, "locator": ""}, True),
        ("must-FAIL: [full] claim with no span",
         {**clean, "support_span": ""}, True),
    ]

    # Calibration must be deterministic. Live scholarly APIs are the production
    # path, but a transient API outage must not turn this two-sided gate test into
    # four false failures. The fixture resolver preserves the cases' identity and
    # metadata semantics while keeping the selftest offline.
    def fixture_resolve(source_id: str) -> dict:
        if (source_id or "").casefold() == "arxiv:2305.14627":
            return {"ok": True, "via": "fixture", "title": "Fixture paper",
                    "year": 2023, "authors": ["Gao"]}
        if (source_id or "").casefold() == "10.9999/this-doi-does-not-exist-12345":
            return {"ok": False, "via": "fixture"}
        return {"ok": False, "via": "fixture"}

    bad = 0
    print(f"{'verdict':9} case")
    print("-" * 72)
    for label, row, want_fail in cases:
        checks = check_row(row, tmp, offline=False, resolver=fixture_resolve)
        failed = any(v == "FAIL" for _, v, _ in checks)
        ok = failed == want_fail
        bad += 0 if ok else 1
        print(f"{'ok' if ok else 'BROKEN':9} {label}")
        if not ok:
            for n, v, d in checks:
                print(f"{'':9}   {v:5} {n}: {d[:88]}")
    print("-" * 72)
    n_pass = sum(1 for _, _, w in cases if not w)
    n_fail = len(cases) - n_pass
    print(f"{len(cases)} cases ({n_pass} must-pass / {n_fail} must-fail), "
          f"{bad} broken — "
          f"{'gate is calibrated' if not bad else 'GATE IS NOT TRUSTWORTHY'}")
    if not n_pass or not n_fail:
        print("ONE-SIDED: a gate that only ever rejects scores 100% here. "
              "Both sides must be populated for this result to mean anything.")
        return 1
    return 1 if bad else 0


# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("ledger", nargs="?")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        import tempfile
        with tempfile.TemporaryDirectory(prefix="citecheck-selftest-") as tmp:
            return selftest(Path(tmp))
    if not args.ledger:
        ap.print_help()
        return 2

    path = Path(args.ledger)
    if not path.exists():
        print(f"ledger not found: {path}")
        return 2
    base = path.resolve().parent

    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        try:
            rows.append(json.loads(line))
        except Exception as exc:                            # noqa: BLE001
            print(f"line {n}: not JSON ({exc}) — skipped")

    results = [{"claim_id": r.get("claim_id", f"row{i}"),
                "claim": r.get("claim", ""),
                "checks": check_row(r, base, args.offline)}
               for i, r in enumerate(rows, 1)]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(f"\n[{r['claim_id']}] {r['claim'][:70]}")
            for name, verdict, detail in r["checks"]:
                print(f"  {verdict:5} {name:11} {detail}")
        fails = sum(1 for r in results for c in r["checks"] if c[1] == "FAIL")
        warns = sum(1 for r in results for c in r["checks"] if c[1] == "WARN")
        print(f"\n{len(results)} claim(s): {fails} FAIL, {warns} WARN")
        if fails:
            print("A FAIL is not a style note: that claim may not ship as cited.")
    return 1 if any(c[1] == "FAIL" for r in results for c in r["checks"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
