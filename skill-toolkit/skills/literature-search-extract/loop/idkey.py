#!/usr/bin/env python3
r"""idkey — the ONE identity-key normalizer of the literature-search-extract feedback loop.

Design of record: ~/.claude/references/lse-feedback-loop-design.md §3.6 (INV-3, D-L7, D-L19,
SG-9, SG-10). One source, one key:

    normalize(source) -> {"key", "aliases", "unresolved", "version", "basis"}

Precedence (first hit wins): version-of-record DOI > journal DOI given in arXiv metadata >
arXiv id (versionless; the DataCite DOI 10.48550/arxiv.<id> becomes an alias) > ISBN-13 >
patent publication number > PMID > `unresolved:<sha1[:8] of basis>`.

`idutils` (BSD-3, pinned 1.7.0 — Invenio) validates and normalizes every scheme it covers;
the PATENT branch is hand-written (SG-10: idutils has no patent scheme) and carries its own
must-parse / must-reject fixtures in `--selftest`. This module NEVER mints an identifier: an
identifier that fails syntactic validation is not turned into a key — the source becomes
`unresolved:` with the raw string kept in `aliases` and a `gaps` note for the run.

The hash of an `unresolved:` key is an id, not the identity: the basis (NFKC title,
first-author surname, year, extra) travels with the key, and every join compares bases
(`runs.py affected` prints COLLISION on two different bases under one hash — D-L19).

Usage:
    python idkey.py normalize [--doi D] [--arxiv A] [--isbn I] [--patent P] [--pmid N]
                              [--title T] [--author "Surname, Given"] [--year YYYY] [--extra X]
    python idkey.py find "<free text cell>"      identifiers found in a free-text cell, precedence-ordered
    python idkey.py key "<one identifier>"        the key one identifier string would produce
    python idkey.py --selftest                    two-sided calibration (must-parse / must-reject)
Exit: 0 ok, 1 usage, 2 selftest broken.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata

try:
    import idutils  # type: ignore
except ImportError:  # pragma: no cover - the loop refuses to guess identifiers without it
    idutils = None

sys.stdout.reconfigure(encoding="utf-8")

SCHEMES = ("doi", "arxiv", "isbn", "patent", "pmid", "unresolved")
KEY_RE = re.compile(r"^(doi|arxiv|isbn|patent|pmid|unresolved):\S+$")
UNRESOLVED_HASH_LEN = 8          # tunable (design §6.5)

# --- patent numbers: the hand-written branch (SG-10) -------------------------------------
PATENT_CC = ("US", "EP", "WO", "JP", "CN", "KR", "DE", "GB", "TW", "FR", "CA", "AU")
_PATENT_RE = re.compile(
    r"^(?P<cc>[A-Z]{2})\s?(?P<num>[0-9]{4,12}|[0-9]{4}/[0-9]{5,7})\s?(?P<kind>[A-Z][0-9]?)?$")
_PATENT_FIND_RE = re.compile(
    r"\b(US|EP|WO|JP|CN|KR|DE|GB|TW|FR|CA|AU)\s?-?\s?([0-9]{4}/)?[0-9]{4,12}\s?(?:[A-Z][0-9]?)?\b")
_DOI_FIND_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>|)\]]+")
_ARXIV_FIND_RE = re.compile(
    r"(?<![\w./])(?:arXiv:\s?)?(\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?)",
    re.I)
_ISBN_FIND_RE = re.compile(r"ISBN(?:-1[03])?[:\s]*([0-9Xx][0-9Xx\- ]{8,16}[0-9Xx])")
_PMID_FIND_RE = re.compile(r"PMID[:\s]*(\d{1,9})\b")


def _fold(s: str) -> str:
    return unicodedata.normalize("NFKC", s or "").casefold().strip()


def _need_idutils() -> None:
    if idutils is None:
        raise RuntimeError("idutils is not installed: `pip install idutils==1.7.0` "
                           "(the loop never guesses an identifier scheme by hand)")


# --- per-scheme normalizers (each returns the normalized value or None) --------------------
def norm_doi(raw: str) -> str | None:
    """Lowercase, prefix-stripped DOI, or None when idutils rejects the syntax."""
    _need_idutils()
    s = (raw or "").strip()
    s = re.sub(r"^(doi:|DOI:|https?://(dx\.)?doi\.org/)", "", s, flags=re.I).strip()
    # idutils.is_doi is lenient ('10.9/fake' passes); Crossref's shape rule (prefix 10.NNNN+/suffix)
    # is applied on top so a malformed string is never minted into a key
    if not s or not idutils.is_doi(s) or not re.match(r"^10\.\d{4,9}/\S+$", s):
        return None
    return idutils.normalize_doi(s).lower()


def norm_arxiv(raw: str) -> tuple[str, str | None] | None:
    """(versionless id, version or None) — 'arXiv:2110.12851v1' -> ('2110.12851', 'v1')."""
    _need_idutils()
    s = (raw or "").strip()
    if not s or not idutils.is_arxiv(s):
        return None
    n = idutils.normalize_arxiv(s)            # 'arXiv:2110.12851v1' / 'arXiv:hep-th/9901001'
    n = re.sub(r"^arxiv:", "", n, flags=re.I)
    m = re.match(r"^(.*?)(v\d+)?$", n)
    return (m.group(1).lower(), m.group(2)) if m else (n.lower(), None)


def norm_isbn(raw: str) -> str | None:
    _need_idutils()
    s = (raw or "").strip()
    if not s or not idutils.is_isbn(s):
        return None
    return idutils.normalize_isbn(s).replace("-", "")   # ISBN-13 digits


def norm_patent(raw: str) -> str | None:
    s = re.sub(r"[\s,\-]", "", (raw or "").strip().upper())
    m = _PATENT_RE.match(s)
    if not m or m.group("cc") not in PATENT_CC:
        return None
    num = m.group("num").replace("/", "")
    kind = m.group("kind") or ""
    return f"{m.group('cc')}{num}{kind}"


def norm_pmid(raw: str) -> str | None:
    _need_idutils()
    s = re.sub(r"^pmid:?\s*", "", (raw or "").strip(), flags=re.I)
    if not s or not idutils.is_pmid(s):
        return None
    return idutils.normalize_pmid(s)


def key_from_identifier(raw: str) -> tuple[str, str] | None:
    """Detect the scheme of ONE identifier string; return (scheme, key) or None."""
    s = (raw or "").strip()
    if not s:
        return None
    m = KEY_RE.match(s)
    if m and s.split(":", 1)[0] != "unresolved":          # already a key: re-normalize
        scheme, rest = s.split(":", 1)
        return key_from_identifier(rest if scheme != "arxiv" else "arXiv:" + rest)
    d = norm_doi(s)
    if d:
        return ("doi", f"doi:{d}")
    a = norm_arxiv(s)
    if a:
        return ("arxiv", f"arxiv:{a[0]}")
    p = norm_patent(s)
    if p:
        return ("patent", f"patent:{p}")
    i = norm_isbn(s)
    if i:
        return ("isbn", f"isbn:{i}")
    n = norm_pmid(s)
    if n:
        return ("pmid", f"pmid:{n}")
    return None


def unresolved_basis(title: str, author: str, year, extra: str = "") -> dict:
    surname = (author or "").split(",")[0].strip()
    if not surname and author:
        surname = author.strip().split()[-1]
    return {"title_norm": _fold(title), "surname": _fold(surname),
            "year": str(year or "").strip(), "extra": _fold(extra)}


def unresolved_key(basis: dict) -> str:
    s = "|".join([basis.get("title_norm", ""), basis.get("surname", ""),
                  basis.get("year", ""), basis.get("extra", "")])
    return "unresolved:" + hashlib.sha1(s.encode("utf-8")).hexdigest()[:UNRESOLVED_HASH_LEN]


def normalize(source: dict) -> dict:
    """One source row -> {key, aliases, unresolved, version, basis, gaps[]}.

    `source` fields (all optional): doi, journal_doi, arxiv, isbn, patent, pmid, title, author,
    year, extra, identifier (free text: scanned with find_all as a last resort).
    """
    aliases: list[str] = []
    gaps: list[str] = []
    version = None
    ids = {k: (source.get(k) or "").strip() for k in
           ("doi", "journal_doi", "arxiv", "isbn", "patent", "pmid", "identifier")}

    def reject(scheme: str, raw: str) -> None:
        gaps.append(f"identifier unverifiable: {scheme} '{raw}' failed syntactic validation; "
                    f"kept as alias, source keyed as unresolved")
        aliases.append(raw)

    # 1-2: DOI of the version of record (journal_doi wins over a preprint's own DOI)
    for field in ("journal_doi", "doi"):
        if ids[field]:
            d = norm_doi(ids[field])
            if d:
                if d.startswith("10.48550/arxiv."):          # arXiv's DataCite DOI is an alias
                    aliases.append(f"doi:{d}")
                    continue
                key = f"doi:{d}"
                for other in ("doi", "journal_doi"):
                    if other != field and ids[other]:
                        od = norm_doi(ids[other])
                        if od and od != d:
                            aliases.append(f"doi:{od}")
                if ids["arxiv"]:
                    a = norm_arxiv(ids["arxiv"])
                    if a:
                        aliases.append(f"arxiv:{a[0]}")
                        version = a[1]
                return _pack(key, aliases, False, version, None, gaps)
            reject(field, ids[field])
    # 3: arXiv id
    if ids["arxiv"]:
        a = norm_arxiv(ids["arxiv"])
        if a:
            aliases.append(f"doi:10.48550/arxiv.{a[0]}")
            return _pack(f"arxiv:{a[0]}", aliases, False, a[1], None, gaps)
        reject("arxiv", ids["arxiv"])
    # 4: ISBN (edition is part of the identity)
    if ids["isbn"]:
        i = norm_isbn(ids["isbn"])
        if i:
            return _pack(f"isbn:{i}", aliases, False, version, None, gaps)
        reject("isbn", ids["isbn"])
    # 5: patent
    if ids["patent"]:
        p = norm_patent(ids["patent"])
        if p:
            return _pack(f"patent:{p}", aliases, False, version, None, gaps)
        reject("patent", ids["patent"])
    # 6: PMID
    if ids["pmid"]:
        n = norm_pmid(ids["pmid"])
        if n:
            return _pack(f"pmid:{n}", aliases, False, version, None, gaps)
        reject("pmid", ids["pmid"])
    # last resort: a free-text identifier cell
    if ids["identifier"]:
        found = find_all(ids["identifier"])
        if found:
            best = found[0]
            for f in found[1:]:
                aliases.append(f["key"])
            return _pack(best["key"], aliases, False, best.get("version"), None, gaps)
        aliases.append(ids["identifier"])
    # 7: unresolved — never dropped
    basis = unresolved_basis(source.get("title", ""), source.get("author", ""),
                             source.get("year", ""), source.get("extra", ""))
    if source.get("version"):
        version = str(source["version"])
    return _pack(unresolved_key(basis), aliases, True, version, basis, gaps)


def _pack(key, aliases, unresolved, version, basis, gaps):
    seen, uniq = set(), []
    for a in aliases:
        if a and a != key and a not in seen:
            seen.add(a)
            uniq.append(a)
    return {"key": key, "aliases": uniq, "unresolved": unresolved, "version": version,
            "basis": basis, "gaps": gaps}


def find_all(text: str) -> list[dict]:
    """Every identifier in a free-text cell, precedence-ordered, deduplicated by key."""
    text = text or ""
    out: list[dict] = []
    for m in _DOI_FIND_RE.finditer(text):
        raw = m.group(0).rstrip(".,;:")
        d = norm_doi(raw)
        if d and not d.startswith("10.48550/arxiv."):
            out.append({"scheme": "doi", "raw": raw, "key": f"doi:{d}", "version": None})
    for m in _ARXIV_FIND_RE.finditer(text):
        raw = m.group(0)
        if raw.lower().startswith("arxiv") or re.match(r"^\d{4}\.\d{4,5}", raw) or "/" in raw:
            a = norm_arxiv(raw if raw.lower().startswith("arxiv") else "arXiv:" + raw)
            if a:
                out.append({"scheme": "arxiv", "raw": raw, "key": f"arxiv:{a[0]}", "version": a[1]})
    for m in _ISBN_FIND_RE.finditer(text):
        i = norm_isbn(m.group(1))
        if i:
            out.append({"scheme": "isbn", "raw": m.group(0), "key": f"isbn:{i}", "version": None})
    for m in _PATENT_FIND_RE.finditer(text):
        p = norm_patent(m.group(0))
        if p:
            out.append({"scheme": "patent", "raw": m.group(0), "key": f"patent:{p}", "version": None})
    for m in _PMID_FIND_RE.finditer(text):
        n = norm_pmid(m.group(1))
        if n:
            out.append({"scheme": "pmid", "raw": m.group(0), "key": f"pmid:{n}", "version": None})
    order = {s: i for i, s in enumerate(SCHEMES)}
    out.sort(key=lambda r: order[r["scheme"]])
    seen, uniq = set(), []
    for r in out:
        if r["key"] not in seen:
            seen.add(r["key"])
            uniq.append(r)
    return uniq


def is_key(s: str) -> bool:
    return bool(KEY_RE.match(s or ""))


# --- two-sided calibration ------------------------------------------------------------------
def selftest() -> int:
    must_parse = [
        ("Ow 2010, uppercase DOI (a real duplicate found in this owner's Zotero library)", {"doi": "10.1364/OE.18.014511"}, "doi:10.1364/oe.18.014511"),
        ("Ow 2010, lowercase DOI (same item, case-different Zotero key) -> SAME key", {"doi": "10.1364/oe.18.014511"}, "doi:10.1364/oe.18.014511"),
        ("DOI with URL prefix", {"doi": "https://doi.org/10.1063/1.5145105"}, "doi:10.1063/1.5145105"),
        ("arXiv new style with version -> versionless key", {"arxiv": "arXiv:2110.12851v1"}, "arxiv:2110.12851"),
        ("arXiv old style", {"arxiv": "hep-th/9901001"}, "arxiv:hep-th/9901001"),
        ("journal DOI beats arXiv id", {"arxiv": "2002.00729v1", "journal_doi": "10.1063/1.5145105"}, "doi:10.1063/1.5145105"),
        ("ISBN-10 -> ISBN-13", {"isbn": "0-387-32989-7"}, "isbn:9780387329895"),
        ("patent EP1308760A1", {"patent": "EP1308760A1"}, "patent:EP1308760A1"),
        ("patent with spaces", {"patent": "US 2022/0146749 A1"}, "patent:US20220146749A1"),
        ("PMID", {"pmid": "20639936"}, "pmid:20639936"),
        ("free-text SRG cell", {"identifier": "DOI 10.1002/j.1538-7305.1977.tb00534.x; archive.org/details/bstj56-5-703"}, "doi:10.1002/j.1538-7305.1977.tb00534.x"),
    ]
    must_unresolve = [
        ("Corning datasheet (no formal id)", {"title": "Corning SMF-28 Ultra Optical Fiber PI1424", "author": "Corning", "year": 2013, "identifier": "Corning PI-1424-AEN (vendor datasheet)", "version": "March 2013"}),
        ("malformed patent", {"patent": "EPX-1308760"}),
        ("fabricated DOI shape that idutils rejects", {"doi": "10.9/fake"}),
        ("empty everything", {"title": "Untitled", "author": "", "year": ""}),
    ]
    broken = 0
    for name, src, want in must_parse:
        got = normalize(src)
        ok = got["key"] == want and not got["unresolved"]
        print(f"{'ok' if ok else 'BROKEN':7} must-PARSE   {name}: {got['key']}")
        broken += (not ok)
    for name, src in must_unresolve:
        got = normalize(src)
        ok = got["unresolved"] and got["key"].startswith("unresolved:") and got["basis"] is not None
        print(f"{'ok' if ok else 'BROKEN':7} must-UNRESOLVE {name}: {got['key']}")
        broken += (not ok)
    # the version stays out of the key, but is kept
    v = normalize({"arxiv": "arXiv:2110.12851v2"})
    ok = v["version"] == "v2" and v["key"] == "arxiv:2110.12851" and "doi:10.48550/arxiv.2110.12851" in v["aliases"]
    print(f"{'ok' if ok else 'BROKEN':7} must-PARSE   arXiv version kept apart + DataCite alias: {v['version']} {v['aliases']}")
    broken += (not ok)
    # collision instrument: two different bases must give different keys (hash) and different bases
    a = normalize({"title": "Passive alignment of optical fibers", "author": "Chen, A.", "year": 1997})
    b = normalize({"title": "Passive alignment of optical fibers", "author": "Chen, B.", "year": 1997, "extra": "OTFA ThE.21"})
    ok = a["basis"] != b["basis"]
    print(f"{'ok' if ok else 'BROKEN':7} must-DIFFER  same title, different basis: {a['key']} vs {b['key']}")
    broken += (not ok)
    n_pass, n_fail = len(must_parse) + 1, len(must_unresolve)
    if n_pass == 0 or n_fail == 0:
        print("ONE-SIDED — refusing to report")
        return 2
    print(f"{n_pass + n_fail + 1} cases ({n_pass} must-parse / {n_fail} must-unresolve / 1 must-differ), {broken} broken")
    return 0 if broken == 0 else 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    n = sub.add_parser("normalize")
    for f in ("doi", "journal_doi", "arxiv", "isbn", "patent", "pmid", "title", "author", "year", "extra", "identifier", "version"):
        n.add_argument(f"--{f.replace('_', '-')}", dest=f, default="")
    fp = sub.add_parser("find")
    fp.add_argument("text")
    kp = sub.add_parser("key")
    kp.add_argument("identifier")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.cmd == "normalize":
        print(json.dumps(normalize({k: getattr(a, k) for k in vars(a) if k not in ("cmd", "selftest")}),
                         ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "find":
        print(json.dumps(find_all(a.text), ensure_ascii=False, indent=1))
        return 0
    if a.cmd == "key":
        r = key_from_identifier(a.identifier)
        print(json.dumps({"scheme": r[0], "key": r[1]} if r else {"scheme": None, "key": None,
                         "note": "not a syntactically valid identifier — the source stays unresolved"}))
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
