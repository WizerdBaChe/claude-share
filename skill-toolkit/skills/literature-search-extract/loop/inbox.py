#!/usr/bin/env python3
r"""inbox — where full text is missing, and where a found PDF waits to be filed.

WHY THIS EXISTS. Every run already records what it could not read: a ledger row tagged
`abstract` and a `sources/manifest.json` entry whose route is `hand_to_user`. Each
record.md prints a query pack for its own run — but nothing lists the debt ACROSS runs,
so the user never knows which papers are owed, how many claims each one would lift, or
where a PDF they found should go. This tool reads the emitted artifacts (never a run's
intermediate state), aggregates by source key, and writes one offline HTML dashboard
plus a central bibliography derived from the same rows.

scan / dashboard / bib are READ-ONLY over EvidenceRuns and write only under the Inbox and
Bibliography folders. `ingest` is the one step that touches a run, and only through
`verify/fetchsrc.py local` (the sanctioned writer of sources/ + manifest.json): it files a
PDF from the Inbox as `filed/<FirstAuthor><Year>_<DOI suffix>.pdf` and registers its text in
every run whose ledger cites that work at [abstract] or whose fetch was refused. The manifest
entry carries the work's key, and that entry is what lifts the source out of "missing full
text". No reflux event is sent: `correction` means the evidence was WRONG and invalidates a
delivered run (design §3.7.2); a full text arriving is not an error (user ruling 2026-09-23).
Ledger rows keep their [abstract] tag until someone re-reads the claims — an extra mark, not
a precondition. A PDF is never deleted and never written into Zotero storage (ruling 2026-09-17).

Usage:
    python inbox.py scan      [--json]                 list missing-full-text sources, most claims first
    python inbox.py dashboard [--out <html>]           write <Inbox>/dashboard.html (+ README.md once)
    python inbox.py bib       [--out <json>] [--ris]   write <Bibliography>/evidence-runs-bib.json
                                                       (zotero_ris_export.py item schema; papers only);
                                                       --ris then resolves every DOI via Crossref into
                                                       <Bibliography>/EvidenceRuns.ris (instrument, not LLM)
    python inbox.py ingest    [--apply] [--filed] [--offline] [--json]
                                                       dry-run by default: per Inbox PDF, the DOI read from
                                                       pages 1-2, the filed name, the runs it would register
                                                       into. --apply moves + registers. --filed re-runs the
                                                       register step for PDFs already in filed\ (backfill;
                                                       never renamed). --offline skips the Crossref fallback.
    python inbox.py --selftest                         two-sided: missing/not-missing, plus ingest's DOI,
                                                       run-match, collision and idempotence controls

Paths (env overrides, same convention as runs.py):
    LSE_RUN_HOME     <vault>\literature\EvidenceRuns
    LSE_INBOX        <vault>\literature\Inbox          (user ruling 2026-09-17)
    LSE_BIB_HOME     <vault>\literature\Bibliography

Exit: 0 ok · 1 usage/environment · 2 selftest failed · 3 ingest left a row unresolved/colliding.
review-when: ledger field names change (access_tag / source_id / source_text);
             fetchsrc renames manifest routes or its `local` entry fields; the Inbox filing
             convention changes; reflux gains an event kind for full-text arrival.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import html
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import idkey  # noqa: E402

TOOL = "inbox/1"
DEFAULT_HOME = Path(r"<vault>\literature\EvidenceRuns")
DEFAULT_INBOX = Path(r"<vault>\literature\Inbox")
DEFAULT_BIB = Path(r"<vault>\literature\Bibliography")

# DOI prefix -> publisher. A LIST, not a grammar: an unknown prefix prints as its prefix.
PUBLISHER_BY_PREFIX = {
    "10.1109": "IEEE", "10.3390": "MDPI", "10.1364": "Optica", "10.1063": "AIP",
    "10.1038": "Nature", "10.1016": "Elsevier", "10.1002": "Wiley", "10.1117": "SPIE",
    "10.1021": "ACS", "10.1088": "IOP", "10.1007": "Springer", "10.1126": "Science",
    "10.1039": "RSC", "10.1103": "APS", "10.1515": "De Gruyter", "10.1080": "Taylor & Francis",
    "10.1145": "ACM", "10.1049": "IET", "10.48550": "arXiv", "10.1587": "IEICE",
    "10.7567": "JSAP", "10.35848": "JSAP", "10.1149": "ECS", "10.1186": "Springer OA",
}
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>?#]+)", re.I)  # stops at ?/# so an API URL's query string is not part of the DOI


def home() -> Path:
    return Path(os.environ.get("LSE_RUN_HOME", str(DEFAULT_HOME)))


def inbox_dir() -> Path:
    return Path(os.environ.get("LSE_INBOX", str(DEFAULT_INBOX)))


def bib_dir() -> Path:
    return Path(os.environ.get("LSE_BIB_HOME", str(DEFAULT_BIB)))


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------- reading runs
def _jsonl(p: Path) -> list[dict]:
    out = []
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def source_key(row: dict) -> str:
    """Normalised identity of a ledger row's source: doi:<..> / arxiv:<..> / unresolved:<hash>."""
    sid = str(row.get("source_id") or "").strip()
    k = idkey.key_from_identifier(sid) if sid else None
    if k:
        return k[1]
    basis = idkey.unresolved_basis(str(row.get("expect_title") or row.get("cite_as") or sid),
                                   (row.get("expect_authors") or [""])[0] if isinstance(row.get("expect_authors"), list) else "",
                                   row.get("expect_year"))
    return idkey.unresolved_key(basis)


def publisher_of(key: str, venue: str | None) -> str:
    if key.startswith("doi:"):
        prefix = key[4:].split("/", 1)[0]
        if prefix in PUBLISHER_BY_PREFIX:
            return PUBLISHER_BY_PREFIX[prefix]
        return f"DOI {prefix}"
    if key.startswith("arxiv:"):
        return "arXiv"
    return venue or "unresolved"


def _norm_name(name: str) -> str:
    """Source-text stem with retrieval-surface suffixes removed, so the abstract text `x_s2`
    and the refused full-text stub `x` meet on `x`."""
    return re.sub(r"(_s2|_search(_s2)?|_abs(tract)?|_oa|_pmc|_arxiv|_html|_pdf)+$", "", name.lower())


def read_run(run_dir: Path) -> dict:
    """One run's emitted artifacts, as the dashboard needs them. Never touches scratch."""
    rj = _json(run_dir / "run.json")
    rows = _jsonl(run_dir / "ledger.jsonl")
    man = _json(run_dir / "sources" / "manifest.json").get("entries", {}) or {}
    stubs = {k: v for k, v in man.items() if v.get("route") == "hand_to_user"}
    run = rj.get("run", {}) or {}
    req = rj.get("request", {}) or {}
    return {
        "run_id": run_dir.name,
        "path": str(run_dir),
        "state": run.get("state") or ("unknown" if rj else "no-run.json"),
        "created": run.get("created") or "",
        "depth": req.get("depth") or run.get("depth") or "",
        "caller": req.get("caller") or "",
        "question": req.get("question") or "",
        "registered": (run_dir / "record.md").exists(),
        "has_ledger": (run_dir / "ledger.jsonl").exists(),
        "has_manifest": (run_dir / "sources" / "manifest.json").exists(),
        "rows": rows,
        "manifest": man,
        "stubs": stubs,
        "tags": dict(collections.Counter((r.get("access_tag") or r.get("access_level") or "?") for r in rows)),
    }


def read_home(h: Path | None = None) -> list[dict]:
    h = h or home()
    if not h.exists():
        return []
    return [read_run(d) for d in sorted(h.iterdir()) if d.is_dir() and not d.name.startswith((".", "_"))]


def read_reflux(h: Path | None = None) -> list[dict]:
    return _jsonl((h or home()) / "reflux.jsonl")


# ---------------------------------------------------------------- aggregation
def aggregate(runs: list[dict], events: list[dict]) -> dict:
    """Sources across runs, keyed by identity. `missing` = sources with ≥1 abstract row and
    no full/partial row ANYWHERE, or a hand_to_user stub with no text under that key — unless
    a full text was registered for the key (a `local_pdf` manifest entry carrying `key`, written
    by `ingest`) or a correction event names it."""
    src: dict[str, dict] = {}
    corrected = {e.get("key") for e in events if e.get("kind") == "correction" and e.get("key")}

    def slot(key: str) -> dict:
        return src.setdefault(key, {
            "key": key, "title": "", "cite_as": "", "year": None, "venue": "", "authors": [],
            "publisher": "", "rows_abstract": 0, "rows_full": 0, "rows_partial": 0, "rows_secondary": 0,
            "runs": {}, "urls": [], "stub_reasons": [], "corrected": key in corrected, "fulltext": [],
        })

    for run in runs:
        rid = run["run_id"]
        for name, ent in run["manifest"].items():
            if ent.get("route") == "local_pdf" and ent.get("key"):
                slot(ent["key"])["fulltext"].append({"run": rid, "name": name, "path": ent.get("path", ""),
                                                     "sha256": ent.get("sha256_source_file", ""),
                                                     "retention": ent.get("retention_state", "")})
        name_to_key: dict[str, str] = {}
        for r in run["rows"]:
            key = source_key(r)
            s = slot(key)
            tag = r.get("access_tag") or r.get("access_level") or "?"
            if tag in ("abstract", "full", "partial", "secondary"):
                s[f"rows_{tag}"] += 1
            s["title"] = s["title"] or r.get("expect_title") or ""
            s["cite_as"] = s["cite_as"] or r.get("cite_as") or ""
            s["year"] = s["year"] or r.get("expect_year")
            s["venue"] = s["venue"] or r.get("expect_venue") or ""
            if not s["authors"] and isinstance(r.get("expect_authors"), list):
                s["authors"] = r["expect_authors"]
            rr = s["runs"].setdefault(rid, {"abstract": 0, "full": 0, "partial": 0, "secondary": 0, "claims": []})
            if tag in rr:
                rr[tag] += 1
            if tag == "abstract":
                rr["claims"].append({"claim_id": r.get("claim_id"), "claim": r.get("claim", "")})
            st = str(r.get("source_text") or "")
            if st:
                name_to_key[_norm_name(Path(st).stem)] = key
        # stubs: linked to a key through the ledger's source_text name when possible,
        # otherwise reported under the run as an unlinked stub.
        for name, ent in run["stubs"].items():
            key = name_to_key.get(_norm_name(name))
            url = ent.get("url", "")
            m = DOI_RE.search(url or "")
            if not key and m:
                k = idkey.key_from_identifier(m.group(1).rstrip(".,;)"))
                key = k[1] if k else None
            if not key:
                key = f"stub:{rid}/{name}"
            s = slot(key)
            s["urls"].append({"run": rid, "url": url, "host": ent.get("host", ""),
                              "policy_class": ent.get("policy_class", ""), "reason": ent.get("reason", "")})
            s["stub_reasons"].append(ent.get("policy_class") or "refused")
            s["runs"].setdefault(rid, {"abstract": 0, "full": 0, "partial": 0, "secondary": 0, "claims": []})
    for s in src.values():
        s["publisher"] = publisher_of(s["key"], s["venue"])
        s["n_runs"] = len(s["runs"])
        s["missing"] = (not s["corrected"]) and not s["fulltext"] and s["rows_full"] == 0 and s["rows_partial"] == 0 \
            and (s["rows_abstract"] > 0 or bool(s["urls"]))
        # lifted = would be missing, but a full text was registered (ingest): the debt is paid while the
        # ledger rows keep their [abstract] tag until someone re-reads the claims
        s["lifted"] = bool(s["fulltext"]) and s["rows_full"] == 0 and s["rows_partial"] == 0 \
            and (s["rows_abstract"] > 0 or bool(s["urls"]))
    order = lambda s: (-s["rows_abstract"], -len(s["urls"]), s["publisher"], s["key"])  # noqa: E731
    missing = sorted((s for s in src.values() if s["missing"]), key=order)
    lifted = sorted((s for s in src.values() if s["lifted"]), key=order)
    return {"sources": src, "missing": missing, "lifted": lifted}


def file_state(f: dict, agg: dict, runs_by_id: dict) -> str:
    """Where a PDF stands: inbox (waiting for ingest) · registered · filed-owed (filed, some run
    still owed a registration: run `ingest --filed`) · filed-has-full · filed-uncited · filed-nodoi."""
    if f["where"] == "inbox":
        return "inbox"
    if not f.get("key"):
        return "filed-nodoi"
    src = agg["sources"].get(f["key"])
    if not src or not src["runs"]:
        return "filed-uncited"
    owed = owed_runs(src, runs_by_id)
    done = {x["run"] for x in src["fulltext"]}
    if owed and not set(owed) <= done:
        return "filed-owed"
    return "registered" if done else "filed-has-full"


# ---------------------------------------------------------------- inbox folder
CC_RE = re.compile(r"creative\s+commons|\bCC[\s-]BY\b", re.I)
COPYRIGHT_RE = re.compile(r"(?:©|\(c\)|copyright)\s*(19[5-9]\d|20[0-4]\d)\b", re.I)


def inspect_pdf(p: Path) -> dict:
    """What pages 1-2 of a PDF say about itself. DOI read with pymupdf; without it the file is
    `no-pymupdf` and unidentified (never guessed from the filename). `cc` = a Creative Commons
    statement on those pages, the only licence evidence ingest acts on."""
    import hashlib
    b = p.read_bytes()
    item = {"file": p.name, "path": str(p), "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest(),
            "doi": None, "key": None, "meta_author": "", "meta_subject": "", "cc": False, "copyright_year": None,
            "how": "pymupdf"}
    try:
        import fitz  # type: ignore
    except ImportError:
        item["how"] = "no-pymupdf"
        return item
    try:
        doc = fitz.open(stream=b, filetype="pdf")
        text = "".join((doc[i].get_text() or "") for i in range(min(2, doc.page_count)))
        meta = doc.metadata or {}
        item["meta_author"] = str(meta.get("author") or "")
        item["meta_subject"] = str(meta.get("subject") or "")
        item["cc"] = bool(CC_RE.search(text))
        m = COPYRIGHT_RE.search(text)
        item["copyright_year"] = int(m.group(1)) if m else None
        for m in DOI_RE.finditer(text):
            raw = m.group(1).rstrip(".,;)")
            k = idkey.key_from_identifier(raw)
            if k:
                item["doi"], item["key"] = raw, k[1]
                break
    except Exception as e:  # noqa: BLE001 — a bad PDF is a row, not a crash
        item["how"] = f"error: {type(e).__name__}"
    return item


def scan_inbox(d: Path | None = None) -> list[dict]:
    """PDFs waiting in the Inbox (`where: inbox`) and PDFs already filed (`where: filed`)."""
    d = d or inbox_dir()
    out = []
    for where, folder in (("inbox", d), ("filed", d / "filed")):
        if folder.exists():
            for p in sorted(folder.glob("*.pdf")):
                out.append(inspect_pdf(p) | {"where": where})
    return out


# ---------------------------------------------------------------- ingest
def _ascii_letters(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))
    return re.sub(r"[^A-Za-z]", "", s)


def surname_from_meta(author_field: str) -> str:
    """First author's surname from a PDF `author` metadata field ("Xiaoyu Li, Shengtao Yu and
    Chengqun Gui" -> Li; "Y. S. Ow, M. B. H. Breese" -> Ow). Empty when it does not look like a name."""
    first = re.split(r";|,| and ", author_field or "", maxsplit=1)[0].strip()
    toks = [t for t in re.split(r"\s+", first) if t]
    if not toks or len(toks) > 5:
        return ""
    sur = _ascii_letters(toks[-1])
    return sur[:1].upper() + sur[1:] if len(sur) >= 2 else ""


def resolve_name(info: dict, src: dict | None, offline: bool) -> dict:
    """First-author surname + year, each from the first source that has it: the ledger (metadata
    the run already verified) > PDF metadata (author field; a subject line carrying the DOI; a
    © year on pages 1-2) > Crossref via citecheck.resolve. The © year can be a reprint year; the
    ledger and the subject line outrank it for that reason."""
    got = {"author": "", "year": None, "author_from": "", "year_from": ""}
    if src:
        if src.get("authors"):
            got["author"], got["author_from"] = _ascii_letters(str(src["authors"][0]).split()[-1] if str(src["authors"][0]).strip() else ""), "ledger"
        if src.get("year"):
            got["year"], got["year_from"] = int(src["year"]), "ledger"
    if not got["author"]:
        sur = surname_from_meta(info.get("meta_author", ""))
        if sur:
            got["author"], got["author_from"] = sur, "pdf-metadata"
    if not got["year"] and info.get("doi") and info["doi"].lower() in info.get("meta_subject", "").lower():
        m = re.search(r"\b(19[5-9]\d|20[0-4]\d)\b", info["meta_subject"])   # publisher-embedded citation line
        if m:
            got["year"], got["year_from"] = int(m.group(1)), "pdf-metadata"
    if not got["year"] and info.get("copyright_year"):
        got["year"], got["year_from"] = info["copyright_year"], "pdf-copyright-line"
    if (not got["author"] or not got["year"]) and info.get("doi") and not offline:
        meta = CROSSREF(info["doi"])
        if meta.get("ok"):
            if not got["author"] and meta.get("authors"):
                got["author"], got["author_from"] = _ascii_letters(meta["authors"][0]), "crossref"
            if not got["year"] and meta.get("year"):
                got["year"], got["year_from"] = int(meta["year"]), "crossref"
    if got["author"]:
        got["author"] = got["author"][:1].upper() + got["author"][1:]
    return got


def _crossref(doi: str) -> dict:
    """The skill's DOI metadata helper (verify/citecheck.py resolve -> Crossref); imported lazily so
    scan/dashboard never need the network stack."""
    sys.path.insert(0, str(HERE.parent / "verify"))
    import citecheck  # noqa: E402
    return citecheck.resolve(doi)


CROSSREF = _crossref   # selftest swaps this for a canned answer


def doi_suffix(doi: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", doi.split("/", 1)[1] if "/" in doi else doi).strip("-._")


def owed_runs(src: dict | None, runs_by_id: dict) -> list[str]:
    """Runs whose ledger cites the work at [abstract] with no full/partial row of their own, or
    whose fetch of it was refused (hand_to_user stub linked to the key)."""
    if not src:
        return []
    stub_runs = {u["run"] for u in src.get("urls", [])}
    out = []
    for rid, rr in src["runs"].items():
        if rid in runs_by_id and ((rr["abstract"] and not (rr["full"] or rr["partial"])) or rid in stub_runs):
            out.append(rid)
    return sorted(out)


def plan_ingest(files: list[dict], runs: list[dict], agg: dict, filed_dir: Path, offline: bool) -> list[dict]:
    """Pure: decide, per PDF, its filed name and the runs to register into. Touches nothing."""
    runs_by_id = {r["run_id"]: r for r in runs}
    plan = []
    for f in files:
        row = dict(f, action="", target="", runs=[], skip={}, reason="", oa="")
        src = agg["sources"].get(f["key"]) if f.get("key") else None
        if f["where"] == "filed":
            row["target"] = f["path"]
        else:
            nm = resolve_name(f, src, offline)
            row["name_from"] = {"author": nm["author_from"], "year": nm["year_from"]}
            if not (nm["author"] and nm["year"]):
                row.update(action="UNRESOLVED", reason=("no DOI on pages 1-2; " if not f.get("doi") else "")
                           + "first author / year not found (ledger, PDF metadata"
                           + (")" if offline or not f.get("doi") else ", Crossref)") + " — left in place")
                plan.append(row)
                continue
            tail = doi_suffix(f["doi"]) if f.get("doi") else f"nodoi-{f['sha256'][:8]}"
            target = filed_dir / f"{nm['author']}{nm['year']}_{tail}.pdf"
            row["target"] = str(target)
            if target.exists():
                same = inspect_pdf(target)["sha256"] == f["sha256"]
                row.update(action="DUPLICATE" if same else "COLLISION",
                           reason=("identical file already filed" if same else "a different file already has this name")
                           + " — left in place, nothing registered")
                plan.append(row)
                continue
        if not f.get("key"):
            row.update(action=row["action"] or ("FILE" if f["where"] == "inbox" else "KEEP"),
                       reason="no DOI on pages 1-2 — filed, not registered into any run")
            plan.append(row)
            continue
        name = Path(row["target"]).stem
        owed = owed_runs(src, runs_by_id)
        for rid in owed:
            ent = runs_by_id[rid]["manifest"].get(name)
            if ent and ent.get("sha256_source_file") == f["sha256"]:
                row["skip"][rid] = "already registered"
            elif ent:
                row["skip"][rid] = f"manifest already has a different entry named {name}"
            else:
                row["runs"].append(rid)
        row["oa"] = ("Creative Commons licence statement on pages 1-2 of the PDF (detected by inbox.py ingest)"
                     if f.get("cc") else "")
        if f["where"] == "inbox":
            row["action"] = "FILE+REGISTER" if row["runs"] else "FILE"
        else:
            row["action"] = "REGISTER" if row["runs"] else "KEEP"
        if not row["runs"]:
            row["reason"] = ("already registered in every owing run" if row["skip"] else
                             "cited only with full text already" if src and src["runs"] else
                             "not cited by any run") + " — not registered"
        plan.append(row)
    return plan


def apply_ingest(plan: list[dict], runs: list[dict]) -> None:
    """Move, then register through fetchsrc.py local. A move never overwrites (checked in the plan and
    again here); a PDF is never deleted."""
    sys.path.insert(0, str(HERE.parent / "verify"))
    import fetchsrc  # noqa: E402
    paths = {r["run_id"]: r["path"] for r in runs}
    for row in plan:
        if row["action"] not in ("FILE", "FILE+REGISTER", "REGISTER"):
            continue
        target = Path(row["target"])
        if row["where"] == "inbox":
            if target.exists():
                row.update(action="COLLISION", reason="target appeared after planning — left in place", runs=[])
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            Path(row["path"]).rename(target)          # rename refuses to replace an existing file on Windows
            row["filed"] = True
        row["registered"] = {}
        for rid in row["runs"]:
            # a legacy run may have no sources/ yet; fetchsrc writes the text before the manifest
            Path(paths[rid], "sources").mkdir(exist_ok=True)
            try:
                rc = fetchsrc.cmd_local(argparse.Namespace(run=paths[rid], pdf=str(target), name=target.stem,
                                                           oa=row["oa"], key=row["key"]))
            except Exception as e:  # noqa: BLE001 — one run failing is a reported row, not a crash
                rc = f"error: {type(e).__name__}: {e}"
            row["registered"][rid] = rc


def cmd_ingest(a) -> int:
    runs = read_home()
    agg = aggregate(runs, read_reflux())
    files = [f for f in scan_inbox() if f["where"] == ("filed" if a.filed else "inbox")]
    plan = plan_ingest(files, runs, agg, inbox_dir() / "filed", a.offline)
    if a.apply:
        apply_ingest(plan, runs)
    if a.json:
        print(json.dumps(plan, ensure_ascii=False, indent=1))
    else:
        print(f"ingest ({'APPLY' if a.apply else 'dry-run'}; {'filed' if a.filed else 'Inbox'}: {len(plan)} PDF)  home: {home()}")
        for r in plan:
            print(f"- {r['file']}  doi={r.get('doi') or '-'}  -> {r['action']}")
            if r["target"] and r["where"] == "inbox" and r["action"] not in ("UNRESOLVED",):
                print(f"    name: {Path(r['target']).name}  (author: {r.get('name_from', {}).get('author') or '-'}, "
                      f"year: {r.get('name_from', {}).get('year') or '-'})")
            for rid in r["runs"]:
                rc = r.get("registered", {}).get(rid)
                print(f"    register -> {rid}  retention={'full (CC)' if r['oa'] else 'excerpt (licensed)'}"
                      + ("" if rc is None else f"  rc={rc}"))
            for rid, why in r["skip"].items():
                print(f"    skip {rid}: {why}")
            if r["reason"]:
                print(f"    {r['reason']}")
        if not plan:
            print("  nothing to do")
        if not a.apply and any(r["action"] in ("FILE", "FILE+REGISTER", "REGISTER") for r in plan):
            print("dry-run: nothing moved or registered — re-run with --apply")
    bad = [r for r in plan if r["action"] in ("UNRESOLVED", "COLLISION", "DUPLICATE")
           or any(v != 0 for v in r.get("registered", {}).values())]
    return 3 if bad else 0


INBOX_README = """---
xi: 1
what: 文獻全文暫存區——查證時只讀到摘要或被付費牆擋下的論文，找到 PDF 後先放這裡等待收錄 (staging inbox for full-text PDFs owed to evidence runs)
tags: [literature-search-extract, inbox, staging, full-text]
aliases: [文獻暫存區, 全文 Inbox, LSE Inbox]
date: {date}
status: live
kind: topic-map
source: "literature-search-extract loop/inbox.py"
review-when: "Inbox filing convention or ingest step changes"
---

# Inbox — 全文暫存區

**放什麼**：`dashboard.html` 列為「缺全文」的論文，你找到 PDF 後直接丟進本資料夾，檔名隨意
（工具讀 PDF 第一、二頁認 DOI，不看檔名）。

**看哪裡**：`dashboard.html`（離線單檔；重產指令見下）。四個檢視：缺全文、各輪次、書目、Inbox。

**收錄 (ingest)**：`inbox.py ingest` 先試跑（只列出會做什麼），確認後加 `--apply`。每個 PDF
會被改名為 `<第一作者><年份>_<DOI 尾碼>.pdf` 移到 `filed\\`（同名已存在就不動、列為衝突），
等你批次匯入 Zotero；凡是引用這篇但只讀到摘要、或抓取被擋下的 run，都用 `fetchsrc.py local`
登錄全文，儀表隨即把它移出「缺全文」。不發 `reflux.py correction`——那是「證據錯了」、會把
已交付的 run 標成作廢；拿到全文不是錯（裁定 2026-09-23）。人工重讀主張是額外標記，不是前提。
沒有 DOI 或沒有 run 欠它的 PDF 照樣歸檔，只是不登錄，輸出會寫明。手動放進 `filed\\` 的 PDF 用
`ingest --filed --apply` 補登錄。PDF 永不刪除；Zotero 的 storage 由 Zotero 管理，任何腳本都不
直接寫入（裁定 2026-09-17）。

**重產**：
```powershell
python <CLAUDE_HOME>\\skills\\literature-search-extract\\loop\\inbox.py ingest
python <CLAUDE_HOME>\\skills\\literature-search-extract\\loop\\inbox.py ingest --apply
python <CLAUDE_HOME>\\skills\\literature-search-extract\\loop\\inbox.py dashboard
python <CLAUDE_HOME>\\skills\\literature-search-extract\\loop\\inbox.py bib
```
"""


# ---------------------------------------------------------------- bibliography
def build_bib(agg: dict, runs: list[dict]) -> dict:
    """zotero_ris_export.py item schema, papers only: a source is a paper when it carries a DOI or
    arXiv id and at least one READ row (full/partial/abstract). `secondary`-only sources stay out
    (connectors.md §Zotero close-out: never read = not in a paper bibliography)."""
    items = []
    for s in sorted(agg["sources"].values(), key=lambda s: (s["publisher"], s["key"])):
        read = s["rows_full"] + s["rows_partial"] + s["rows_abstract"]
        # papers only: DOI or arXiv identity. Patents / ISBN / unresolved / stub keys are real
        # sources with their own tiers but do not belong in a paper bibliography (connectors.md).
        if read == 0 or not s["key"].startswith(("doi:", "arxiv:")):
            continue
        scheme, ident = s["key"].split(":", 1)
        item = {
            "id": re.sub(r"[^A-Za-z0-9]+", "", (s["cite_as"] or ident))[:40] or ident,
            "first_author": (s["authors"] or [""])[0],
            "year": s["year"],
            "title": s["title"] or s["cite_as"],
            "notes": f"evidence runs: {', '.join(sorted(s['runs']))}; access: "
                     f"full={s['rows_full']} partial={s['rows_partial']} abstract={s['rows_abstract']}",
            "_runs": sorted(s["runs"]),
            "_access": "full" if s["rows_full"] else ("partial" if s["rows_partial"] else "abstract"),
            "_publisher": s["publisher"],
        }
        if scheme == "doi":
            item["doi"] = ident
        else:
            item["manual"] = {"type": "JOUR", "title": item["title"], "authors": s["authors"],
                              "year": s["year"], "venue": s["venue"], "url": f"https://arxiv.org/abs/{ident}"}
        items.append(item)
    return {
        "schema": "lse-bib/central@1", "generated": now_iso(), "tool": TOOL,
        "home": str(home()), "n_runs": len(runs), "n_items": len(items),
        "collection": "EvidenceRuns",
        "note": "Derived from every run's ledger.jsonl; regenerate, never edit. RIS: "
                "python ../scripts/zotero_ris_export.py <this file> --collection-name <name> --out-dir <dir>",
        "items": items,
    }


# ---------------------------------------------------------------- dashboard html
def render_dashboard(runs: list[dict], agg: dict, inbox: list[dict], events: list[dict]) -> str:
    runs_by_id = {r["run_id"]: r for r in runs}
    data = {
        "generated": now_iso(),
        "home": str(home()), "inbox": str(inbox_dir()), "bib": str(bib_dir() / "evidence-runs-bib.json"),
        "runs": [{k: v for k, v in r.items() if k not in ("rows", "manifest", "stubs")} | {"n_rows": len(r["rows"]), "n_stubs": len(r["stubs"])} for r in runs],
        "missing": [{k: v for k, v in s.items()} for s in agg["missing"]],
        "lifted": [{k: v for k, v in s.items()} for s in agg["lifted"]],
        "sources": [{k: v for k, v in s.items() if k != "runs"} | {"run_ids": sorted(s["runs"])} for s in agg["sources"].values()],
        "inbox_files": [{k: v for k, v in f.items() if k not in ("meta_subject",)} | {"state": file_state(f, agg, runs_by_id)}
                        for f in inbox],
        "n_events": len(events),
    }
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return DASHBOARD_HTML.replace("__DATA__", payload)


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="zh-Hant" data-page-class="dashboard">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>文獻全文欠缺儀表</title>
<style>
:root{--bg:#fafaf8;--fg:#1c1c1a;--muted:#6b6b66;--line:#dedcd6;--card:#ffffff;--accent:#2f5d9a;--warn:#b4531a;--ok:#2d7a4f;--chip:#ecebe6}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#171716;--fg:#ecebe6;--muted:#a3a29b;--line:#34342f;--card:#1f1f1d;--accent:#8db3ea;--warn:#e8925a;--ok:#6cc08f;--chip:#2a2a27}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,"Noto Sans TC","Microsoft JhengHei",sans-serif}
header{padding:16px 24px 8px;border-bottom:1px solid var(--line)}
h1{font-size:20px;margin:0 0 4px}.sub{color:var(--muted);font-size:13px}
nav{display:flex;gap:6px;flex-wrap:wrap;padding:10px 24px;border-bottom:1px solid var(--line)}
nav button{font:inherit;padding:6px 14px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:6px;cursor:pointer}
nav button[aria-current="page"]{background:var(--accent);color:#fff;border-color:var(--accent)}
main{padding:16px 24px 40px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-bottom:16px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px}
.kpi b{display:block;font-size:24px}.kpi span{color:var(--muted);font-size:13px}
.tools{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:8px 0 12px}
.tools label{font-size:13px;color:var(--muted)}select,input[type=search]{font:inherit;padding:4px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card)}table{width:100%;border-collapse:collapse;min-width:900px}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{font-size:13px;color:var(--muted);font-weight:600;position:sticky;top:0;background:var(--card)}
tr:last-child td{border-bottom:0}td.num{text-align:right;font-variant-numeric:tabular-nums}
.chip{display:inline-block;padding:1px 8px;border-radius:10px;background:var(--chip);font-size:12px;margin:1px 2px 1px 0;white-space:nowrap}
.warn{color:var(--warn)}.ok{color:var(--ok)}.muted{color:var(--muted)}
details summary{cursor:pointer;color:var(--accent)}details ul{margin:4px 0 0 0;padding-left:18px;font-size:13px}
code{font-size:13px;background:var(--chip);padding:1px 4px;border-radius:4px}
.note{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin-bottom:12px;font-size:14px}
.empty{padding:24px;text-align:center;color:var(--muted)}
a{color:var(--accent)}
@media (max-width:700px){header,nav,main{padding-left:16px;padding-right:16px}}
</style>
</head>
<body>
<header>
<h1>文獻全文欠缺儀表 (missing full-text dashboard)</h1>
<div class="sub" id="sub"></div>
</header>
<nav aria-label="檢視">
<button data-view="missing">缺全文</button>
<button data-view="runs">各輪次</button>
<button data-view="bib">書目</button>
<button data-view="inbox">Inbox</button>
</nav>
<main id="main"></main>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const $ = s => document.querySelector(s);
const VIEWS = ['missing','runs','bib','inbox'];
document.getElementById('sub').textContent = `產生於 ${D.generated} ・ 資料來源 ${D.home} ・ 暫存區 ${D.inbox}`;

function state(){ const h = location.hash.replace(/^#/,''); const [v, q] = h.split('?'); const p = new URLSearchParams(q||'');
  return { view: VIEWS.includes(v)?v:'missing', pub: p.get('pub')||'', q: p.get('q')||'' }; }
function setState(s){ const p = new URLSearchParams(); if(s.pub) p.set('pub', s.pub); if(s.q) p.set('q', s.q);
  const qs = p.toString(); location.hash = s.view + (qs?'?'+qs:''); }

function chips(s){ return `<span class="chip warn">abstract ${s.rows_abstract}</span>` + (s.urls.length?`<span class="chip warn">擋下 ${s.urls.length}</span>`:'') + (s.rows_secondary?`<span class="chip">secondary ${s.rows_secondary}</span>`:''); }
function link(key){ if(key.startsWith('doi:')) return `<a href="https://doi.org/${esc(key.slice(4))}" target="_blank" rel="noopener">${esc(key.slice(4))}</a>`;
  if(key.startsWith('arxiv:')) return `<a href="https://arxiv.org/abs/${esc(key.slice(6))}" target="_blank" rel="noopener">arXiv:${esc(key.slice(6))}</a>`; return `<code>${esc(key)}</code>`; }

function viewMissing(s){
  const pubs = [...new Set(D.missing.map(m=>m.publisher))].sort();
  const isPaper = m => /^(doi|arxiv):/.test(m.key);
  const papers = D.missing.filter(isPaper);
  const stubs = D.missing.filter(m => !isPaper(m));
  const rows = papers.filter(m => (!s.pub || m.publisher===s.pub) && (!s.q || (m.title+' '+m.cite_as+' '+m.key).toLowerCase().includes(s.q.toLowerCase())));
  const stubTable = stubs.length ? `<h2 style="font-size:16px;margin:20px 0 8px">存根：被擋下但沒有論文識別碼 (${stubs.length})</h2><div class="note">API 檢索 URL、廠商網頁、新聞稿等：fetchsrc 記了「未取回」，但沒有 DOI 可對應到論文。這些不是 Inbox 要補的 PDF，列出只為完整。</div><div class="tw"><table><thead><tr><th>run／名稱</th><th>主機</th><th>政策類別</th><th>URL</th></tr></thead><tbody>${stubs.map(m=>m.urls.map(u=>`<tr><td><code>${esc(m.key.replace(/^stub:/,''))}</code></td><td>${esc(u.host)}</td><td>${esc(u.policy_class||'?')}</td><td><a href="${esc(u.url)}" target="_blank" rel="noopener">${esc(u.url.slice(0,90))}${u.url.length>90?'…':''}</a></td></tr>`).join('')).join('')}</tbody></table></div>` : '';
  const inboxKeys = new Set(D.inbox_files.filter(f=>f.state==='inbox'||f.state==='filed-owed').map(f=>f.key).filter(Boolean));
  const claims = D.missing.reduce((a,m)=>a+m.rows_abstract,0);
  const lifted = D.lifted || [];
  const liftedTable = lifted.length ? `<h2 style="font-size:16px;margin:20px 0 8px">已登錄全文、移出清單 (${lifted.length})</h2><div class="note">收錄 (ingest) 已把 PDF 全文登錄進引用它的輪次（<code>fetchsrc.py local</code>），所以不再算缺全文。這些主張在 ledger 裡仍標 <code>[abstract]</code>——人工重讀後改標是額外的標記，不是前提。</div><div class="tw"><table><thead><tr><th>來源</th><th>識別碼</th><th class="num">主張</th><th>登錄到</th></tr></thead><tbody>${lifted.map(m=>`<tr><td><b>${esc(m.title||m.cite_as)}</b><div class="muted">${esc(m.cite_as)} ${m.year?'· '+m.year:''}</div></td><td>${link(m.key)}</td><td class="num">${m.rows_abstract}</td><td>${m.fulltext.map(x=>`<div><span class="chip ok">${esc(x.run)}</span> <code>${esc(x.name)}</code> <span class="muted">${esc(x.retention)}</span></div>`).join('')}</td></tr>`).join('')}</tbody></table></div>` : '';
  let h = `<div class="kpis">
    <div class="kpi"><b>${papers.length}</b><span>缺全文的論文 (papers, DOI／arXiv)</span></div>
    <div class="kpi"><b>${claims}</b><span>只到摘要層級的主張 (claims at [abstract])</span></div>
    <div class="kpi"><b>${D.missing.filter(m=>m.urls.length).length}</b><span>被主機擋下 (hand-to-user)</span></div>
    <div class="kpi"><b>${D.missing.filter(m=>inboxKeys.has(m.key)).length}</b><span>已有 PDF 待收錄</span></div>
    <div class="kpi"><b>${lifted.length}</b><span>已登錄全文、移出清單</span></div></div>
  <div class="note">「缺全文」＝ 在所有輪次裡沒有任何一列讀到 full／partial、也沒有登錄過全文，且至少有一列停在 abstract 或被主機擋下。找到 PDF 後丟進 <code>${esc(D.inbox)}</code>，執行 <code>inbox.py ingest --apply</code> 收錄，重產本頁即移出本清單。排序：受影響主張數多者在前。</div>
  <div class="tools"><label>出版社 <select id="pub"><option value="">全部</option>${pubs.map(p=>`<option ${p===s.pub?'selected':''}>${esc(p)}</option>`).join('')}</select></label>
  <label>搜尋 <input type="search" id="q" value="${esc(s.q)}" placeholder="標題／作者／DOI"></label><span class="muted">${rows.length} / ${papers.length}</span></div>`;
  if(!rows.length) return h + `<div class="empty">沒有符合的項目</div>` + liftedTable + stubTable;
  h += `<div class="tw"><table><thead><tr><th>來源</th><th>出版社</th><th>識別碼</th><th>狀態</th><th class="num">主張</th><th>引用輪次</th><th>去哪裡找</th></tr></thead><tbody>`;
  for(const m of rows){
    const title = m.title || m.cite_as || '(無標題)';
    const runs = m.run_ids ? m.run_ids : Object.keys(m.runs||{});
    const claimList = Object.entries(m.runs||{}).flatMap(([r,v])=>v.claims.map(c=>`<li><code>${esc(r)}</code> ${esc(c.claim_id)}：${esc(c.claim)}</li>`)).join('');
    const where = m.urls.length ? m.urls.map(u=>`<div><a href="${esc(u.url)}" target="_blank" rel="noopener">${esc(u.host)}</a> <span class="muted">(${esc(u.policy_class||'?')})</span></div>`).join('') : `<span class="muted">DOI 連結</span>`;
    h += `<tr><td><b>${esc(title)}</b><div class="muted">${esc(m.cite_as)} ${m.year?'· '+m.year:''} ${m.venue?'· '+esc(m.venue):''}</div>${claimList?`<details><summary>受影響主張 ${m.rows_abstract}</summary><ul>${claimList}</ul></details>`:''}</td>
      <td>${esc(m.publisher)}</td><td>${link(m.key)}</td><td>${chips(m)}${inboxKeys.has(m.key)?'<span class="chip ok">Inbox 已有</span>':''}</td>
      <td class="num">${m.rows_abstract}</td><td>${runs.map(r=>`<span class="chip">${esc(r)}</span>`).join('')}</td><td>${where}</td></tr>`;
  }
  return h + `</tbody></table></div>` + liftedTable + stubTable;
}

function viewRuns(){
  const unreg = D.runs.filter(r=>!r.registered).length;
  let h = `<div class="kpis"><div class="kpi"><b>${D.runs.length}</b><span>輪次 (runs)</span></div><div class="kpi"><b>${unreg}</b><span>未登錄（無 record.md，README 不列）</span></div><div class="kpi"><b>${D.runs.reduce((a,r)=>a+r.n_stubs,0)}</b><span>hand-to-user 存根</span></div></div>
  <div class="note">未登錄的輪次不會出現在 EvidenceRuns README，也沒跑過 Zotero 收尾——這就是「bib 很久沒出現」的原因。登錄指令：<code>python loop/runs.py register &lt;run_dir&gt;</code>（會先要求 reuse_check）。</div>
  <div class="tw"><table><thead><tr><th>run</th><th>建立</th><th>狀態</th><th>登錄</th><th>深度</th><th>問題</th><th>存取層級分布</th><th class="num">存根</th></tr></thead><tbody>`;
  for(const r of D.runs){
    const tags = Object.entries(r.tags||{}).map(([k,v])=>`<span class="chip ${k==='abstract'?'warn':''}">${esc(k)} ${v}</span>`).join('');
    h += `<tr><td><code>${esc(r.run_id)}</code></td><td>${esc((r.created||'').slice(0,10))}</td><td>${esc(r.state)}</td><td>${r.registered?'<span class="ok">已登錄</span>':'<span class="warn">未登錄</span>'}</td><td>${esc(r.depth)}</td><td>${esc((r.question||'').slice(0,110))}${(r.question||'').length>110?'…':''}</td><td>${tags||'<span class="muted">無 ledger</span>'}</td><td class="num">${r.n_stubs}</td></tr>`;
  }
  return h + `</tbody></table></div>`;
}

function viewBib(s){
  const items = D.sources.filter(x => !x.key.startsWith('unresolved:') && !x.key.startsWith('stub:') && (x.rows_full+x.rows_partial+x.rows_abstract)>0)
    .filter(x => (!s.pub || x.publisher===s.pub) && (!s.q || (x.title+' '+x.cite_as+' '+x.key).toLowerCase().includes(s.q.toLowerCase())))
    .sort((a,b)=> (a.publisher+a.key).localeCompare(b.publisher+b.key));
  const pubs = [...new Set(D.sources.map(m=>m.publisher))].sort();
  let h = `<div class="note">集中書目：所有輪次的 ledger 推導、不含只作 secondary 引用的來源。機器版在 <code>${esc(D.bib)}</code>（zotero_ris_export.py 的 item 結構），產 RIS：<code>python scripts/zotero_ris_export.py &lt;bib.json&gt; --collection-name &lt;名稱&gt; --out-dir &lt;dir&gt;</code>。</div>
  <div class="tools"><label>出版社 <select id="pub"><option value="">全部</option>${pubs.map(p=>`<option ${p===s.pub?'selected':''}>${esc(p)}</option>`).join('')}</select></label>
  <label>搜尋 <input type="search" id="q" value="${esc(s.q)}"></label><span class="muted">${items.length} 篇</span></div>
  <div class="tw"><table><thead><tr><th>標題</th><th>作者／年</th><th>出版社</th><th>識別碼</th><th>最佳存取</th><th>輪次</th></tr></thead><tbody>`;
  for(const x of items){
    const best = x.rows_full?'<span class="ok">full</span>':(x.rows_partial?'partial':'<span class="warn">abstract</span>');
    h += `<tr><td>${esc(x.title||x.cite_as)}</td><td>${esc((x.authors||[]).slice(0,2).join(', '))}${(x.authors||[]).length>2?' et al.':''} ${x.year||''}</td><td>${esc(x.publisher)}</td><td>${link(x.key)}</td><td>${best}</td><td>${(x.run_ids||[]).map(r=>`<span class="chip">${esc(r)}</span>`).join('')}</td></tr>`;
  }
  return h + `</tbody></table></div>`;
}

function viewInbox(){
  const byKey = Object.fromEntries(D.sources.map(s=>[s.key,s]));
  const STATE = {
    'inbox': ['warn','待收錄','執行 ingest --apply'],
    'filed-owed': ['warn','已歸檔、待登錄','有輪次欠這篇全文：執行 ingest --filed --apply'],
    'registered': ['ok','已登錄全文','已登錄進欠它的輪次'],
    'filed-has-full': ['','已歸檔','引用它的輪次原本就有全文'],
    'filed-uncited': ['','已歸檔','不在任何輪次（個人閱讀），不登錄'],
    'filed-nodoi': ['','已歸檔、未辨識 DOI','前兩頁找不到 DOI，不登錄'],
  };
  const waiting = D.inbox_files.filter(f=>f.where==='inbox'), filed = D.inbox_files.filter(f=>f.where==='filed');
  let h = `<div class="kpis"><div class="kpi"><b>${waiting.length}</b><span>Inbox 待收錄</span></div><div class="kpi"><b>${filed.length}</b><span>已歸檔 (filed)</span></div><div class="kpi"><b>${filed.filter(f=>f.state==='filed-owed').length}</b><span>已歸檔、待登錄</span></div></div>
  <div class="note"><b>暫存資料夾</b> <code>${esc(D.inbox)}</code>：找到的 PDF 直接放這裡（檔名隨意，工具讀 PDF 前兩頁認 DOI）。<code>inbox.py ingest</code> 先試跑、<code>--apply</code> 才動手：改名為 <code>&lt;第一作者&gt;&lt;年份&gt;_&lt;DOI 尾碼&gt;.pdf</code> 移到 <code>filed\\</code>（等你批次匯入 Zotero），並把全文登錄進欠它的輪次。手動放進 <code>filed\\</code> 的用 <code>ingest --filed --apply</code> 補登錄。</div>`;
  if(!D.inbox_files.length) return h + `<div class="empty">Inbox 與 filed 目前都沒有 PDF</div>`;
  h += `<div class="tw"><table><thead><tr><th>檔案</th><th>位置</th><th class="num">大小</th><th>辨識到的 DOI</th><th>對應來源</th><th>狀態</th></tr></thead><tbody>`;
  for(const f of [...waiting, ...filed]){
    const s = f.key ? byKey[f.key] : null;
    const [cls, label, hint] = STATE[f.state] || ['', f.state, ''];
    h += `<tr><td><code>${esc(f.file)}</code></td><td>${f.where==='inbox'?'Inbox':'filed'}</td><td class="num">${(f.bytes/1024).toFixed(0)} KB</td><td>${f.doi?link('doi:'+f.doi):'<span class="warn">未辨識</span>'}${f.how!=='pymupdf'?` <span class="muted">(${esc(f.how)})</span>`:''}</td><td>${s&&s.run_ids.length?esc(s.title||s.cite_as):'<span class="muted">不在任何輪次</span>'}</td><td><span class="chip ${cls}">${esc(label)}</span><div class="muted">${esc(hint)}</div></td></tr>`;
  }
  return h + `</tbody></table></div>`;
}

function render(){
  const s = state();
  document.querySelectorAll('nav button').forEach(b => { if(b.dataset.view===s.view) b.setAttribute('aria-current','page'); else b.removeAttribute('aria-current'); });
  const m = $('#main');
  m.innerHTML = s.view==='missing'?viewMissing(s):s.view==='runs'?viewRuns():s.view==='bib'?viewBib(s):viewInbox();
  const pub = $('#pub'), q = $('#q');
  if(pub) pub.addEventListener('change', ()=>setState({...state(), pub: pub.value}));
  if(q) q.addEventListener('change', ()=>setState({...state(), q: q.value}));
}
document.querySelectorAll('nav button').forEach(b => b.addEventListener('click', ()=>setState({view: b.dataset.view, pub:'', q:''})));
window.addEventListener('hashchange', render);
render();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------- commands
def cmd_scan(a) -> int:
    runs = read_home()
    if not runs:
        print(f"no runs under {home()}")
        return 1
    agg = aggregate(runs, read_reflux())
    if a.json:
        print(json.dumps({"home": str(home()), "n_runs": len(runs), "missing": agg["missing"]}, ensure_ascii=False, indent=1))
        return 0
    print(f"home: {home()}  runs: {len(runs)}  (unregistered: {sum(1 for r in runs if not r['registered'])})")
    print(f"missing full text: {len(agg['missing'])} sources, "
          f"{sum(s['rows_abstract'] for s in agg['missing'])} claims at [abstract]")
    print(f"{'claims':>6}  {'blocked':>7}  {'publisher':<14} {'key':<40} title")
    for s in agg["missing"]:
        print(f"{s['rows_abstract']:>6}  {len(s['urls']):>7}  {s['publisher']:<14} {s['key'][:40]:<40} {(s['title'] or s['cite_as'])[:70]}")
    return 0


def cmd_dashboard(a) -> int:
    runs = read_home()
    if not runs:
        print(f"no runs under {home()}")
        return 1
    agg = aggregate(runs, read_reflux())
    inbox_dir().mkdir(parents=True, exist_ok=True)
    (inbox_dir() / "filed").mkdir(exist_ok=True)
    readme = inbox_dir() / "README.md"
    if not readme.exists():
        readme.write_text(INBOX_README.format(date=dt.date.today().isoformat()), encoding="utf-8")
        print(f"wrote {readme}")
    out = Path(a.out) if a.out else inbox_dir() / "dashboard.html"
    files = scan_inbox()
    out.write_text(render_dashboard(runs, agg, files, read_reflux()), encoding="utf-8")
    print(f"wrote {out}  runs={len(runs)} missing={len(agg['missing'])} lifted={len(agg['lifted'])} "
          f"inbox_pdfs={sum(f['where'] == 'inbox' for f in files)} filed_pdfs={sum(f['where'] == 'filed' for f in files)}")
    return 0


def cmd_bib(a) -> int:
    runs = read_home()
    if not runs:
        print(f"no runs under {home()}")
        return 1
    agg = aggregate(runs, read_reflux())
    bib = build_bib(agg, runs)
    bib_dir().mkdir(parents=True, exist_ok=True)
    out = Path(a.out) if a.out else bib_dir() / "evidence-runs-bib.json"
    out.write_text(json.dumps(bib, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {out}  items={bib['n_items']} (from {len(runs)} runs)")
    if getattr(a, "ris", False):
        # Instrument step: every DOI resolved through doi.org / Crossref by the existing exporter
        # (only those two hosts are contacted); the ledger's expect_* fields are never the RIS source.
        import subprocess
        exporter = HERE.parent / "scripts" / "zotero_ris_export.py"
        cmd = [sys.executable, str(exporter), str(out), "--collection-name", bib["collection"], "--out-dir", str(out.parent)]
        rc = subprocess.run(cmd, encoding="utf-8").returncode
        rc2 = subprocess.run(cmd + ["--check"], encoding="utf-8").returncode
        print(f"ris: export rc={rc} check rc={rc2} -> {out.parent / (bib['collection'] + '.ris')}")
        return rc or rc2
    return 0


def _selftest_ingest(td: Path, h: Path, ok) -> int:
    """ingest controls, each two-sided, on the selftest home (runs 20260101_pos: 10.1109/TEST.2026.1 at
    [abstract] + refused stub; 20260102_neg: 10.3390/TEST.2 at [full]). Returns 1 when it cannot run."""
    global CROSSREF
    try:
        import fitz  # type: ignore
    except ImportError:
        print("  FAIL ingest controls: pymupdf missing — ONE-SIDED, refusing to report ingest as calibrated")
        return 1
    inbox = Path(os.environ["LSE_INBOX"])
    filed = inbox / "filed"
    os.environ["LSE_FETCH_SCRATCH"] = str(td / "scratch")

    def pdf(path: Path, text: str, author: str = "") -> None:
        doc = fitz.open()
        doc.new_page().insert_text((72, 72), text)
        if author:
            doc.set_metadata({"author": author})
        doc.save(str(path))

    # a third run owes a DOI whose PDF the user filed by hand (backfill case); CC -> full retention
    bf = h / "20260103_bf"
    bf.mkdir(parents=True)          # no sources/ yet: registering must create it, not crash (2026-09-23)
    (bf / "run.json").write_text(json.dumps({"run": {"state": "delivered"}, "request": {"question": "q"}}), encoding="utf-8")
    (bf / "ledger.jsonl").write_text(json.dumps({"claim_id": "C1", "claim": "z", "source_id": "10.1109/BF.2021.7", "cite_as": "Hand 2021",
                                                "expect_year": 2021, "expect_authors": ["Hand"], "access_tag": "abstract",
                                                "source_text": "sources/hand_s2.txt"}) + "\n", encoding="utf-8")
    pdf(filed / "Hand2021_BF.2021.7.pdf", "DOI: 10.1109/BF.2021.7\nThis article is licensed under a Creative Commons Attribution 4.0 License.")
    pdf(inbox / "a.pdf", "Journal of Tests\ndoi:10.1109/TEST.2026.1.", author="Ann Smith, Bob Jones")      # owed, author from metadata
    pdf(inbox / "b.pdf", "no identifier on this page")                                                        # no DOI, no author
    pdf(inbox / "c.pdf", "https://doi.org/10.3390/TEST.2", author="Carl Neg")                                 # cited, already full
    pdf(inbox / "d.pdf", "doi 10.1038/uncited.9")                                                             # uncited, name via Crossref
    pdf(inbox / "e.pdf", "doi 10.1364/TEST.5", author="Eve Col")                                              # name collision
    pdf(filed / "Col2020_TEST.5.pdf", "a different paper that took the name first")
    pdf(inbox / "f.pdf", "Received 2019. (c) 2019 Test Society", author="Fay Nodoi")                         # no DOI, resolvable
    CROSSREF = lambda doi: ({"ok": True, "authors": ["Dee"], "year": 2024} if doi.lower() == "10.1038/uncited.9"   # noqa: E731
                            else {"ok": True, "authors": [], "year": 2020} if doi.lower() == "10.1364/test.5" else {"ok": False})
    try:
        runs = read_home()
        agg = aggregate(runs, [])
        by = {r["run_id"]: r for r in runs}
        states = {f["file"]: file_state(f, agg, by) for f in scan_inbox()}
        ok("scan sees Inbox and filed\\ (6 waiting, 2 filed)", sum(f == "inbox" for f in states.values()) == 6 and len(states) == 8)
        ok("hand-filed owed PDF shows filed-owed; a hand-filed one without DOI does not",
           states["Hand2021_BF.2021.7.pdf"] == "filed-owed" and states["Col2020_TEST.5.pdf"] == "filed-nodoi")
        plan = {r["file"]: r for r in plan_ingest([f for f in scan_inbox() if f["where"] == "inbox"], runs, agg, filed, offline=False)}
        ok("DOI found: a.pdf -> Smith2026_TEST.2026.1.pdf (author from PDF metadata, year from ledger)",
           Path(plan["a.pdf"]["target"]).name == "Smith2026_TEST.2026.1.pdf" and plan["a.pdf"]["action"] == "FILE+REGISTER")
        ok("DOI not found and no name: b.pdf UNRESOLVED, not moved", plan["b.pdf"]["action"] == "UNRESOLVED")
        ok("no DOI but name resolvable: f.pdf filed as Nodoi2019_nodoi-*, not registered",
           plan["f.pdf"]["action"] == "FILE" and Path(plan["f.pdf"]["target"]).name.startswith("Nodoi2019_nodoi-") and not plan["f.pdf"]["runs"])
        ok("run match: a.pdf registers into exactly the owing run", plan["a.pdf"]["runs"] == ["20260101_pos"])
        ok("no run match: c.pdf (cited [full]) and d.pdf (uncited) are filed, not registered",
           plan["c.pdf"]["action"] == "FILE" and not plan["c.pdf"]["runs"] and plan["d.pdf"]["action"] == "FILE"
           and Path(plan["d.pdf"]["target"]).name == "Dee2024_uncited.9.pdf")
        ok("collision: e.pdf -> COLLISION, left in place", plan["e.pdf"]["action"] == "COLLISION")
        ok("dry-run moved nothing", (inbox / "a.pdf").exists() and not (filed / "Smith2026_TEST.2026.1.pdf").exists())
        rc = cmd_ingest(argparse.Namespace(apply=True, filed=False, offline=False, json=False))
        ok("apply exit 3 (unresolved + collision rows reported)", rc == 3)
        ok("apply: a/c/d/f moved; b/e left in place; the colliding filed file untouched",
           all((filed / n).exists() for n in ("Smith2026_TEST.2026.1.pdf", "Neg2025_TEST.2.pdf", "Dee2024_uncited.9.pdf"))
           and not (inbox / "a.pdf").exists() and (inbox / "b.pdf").exists() and (inbox / "e.pdf").exists()
           and inspect_pdf(filed / "Col2020_TEST.5.pdf")["sha256"] != inspect_pdf(inbox / "e.pdf")["sha256"])
        man = _json(h / "20260101_pos" / "sources" / "manifest.json")["entries"]
        ent = man.get("Smith2026_TEST.2026.1", {})
        ok("registered through fetchsrc local: route local_pdf, key, licensed -> excerpt (scratch)",
           ent.get("route") == "local_pdf" and ent.get("key") == "doi:10.1109/test.2026.1" and ent.get("retention_state") == "pending-excerpt")
        ok("negative: the full-only run got no entry",
           "Neg2025_TEST.2" not in _json(h / "20260102_neg" / "sources" / "manifest.json").get("entries", {}))
        agg2 = aggregate(read_home(), [])
        ok("registered source leaves missing and appears in lifted",
           "doi:10.1109/test.2026.1" not in [s["key"] for s in agg2["missing"]] and "doi:10.1109/test.2026.1" in [s["key"] for s in agg2["lifted"]])
        ok("negative: the hand-filed owed source is still missing before backfill",
           "doi:10.1109/bf.2021.7" in [s["key"] for s in agg2["missing"]])
        rc = cmd_ingest(argparse.Namespace(apply=True, filed=True, offline=True, json=False))
        bfman = _json(bf / "sources" / "manifest.json")["entries"].get("Hand2021_BF.2021.7", {})
        ok("backfill registers the hand-filed PDF (CC -> full text written), name unchanged",
           rc == 0 and bfman.get("retention_state") == "full" and (bf / "sources" / "Hand2021_BF.2021.7.txt").exists()
           and (filed / "Hand2021_BF.2021.7.pdf").exists())
        before = {r: (h / r / "sources" / "manifest.json").read_bytes() for r in ("20260101_pos", "20260103_bf")}
        rc2 = cmd_ingest(argparse.Namespace(apply=True, filed=True, offline=True, json=False))
        rc3 = cmd_ingest(argparse.Namespace(apply=True, filed=False, offline=True, json=False))
        ok("idempotent: re-running backfill and ingest changes no manifest",
           rc2 == 0 and all((h / r / "sources" / "manifest.json").read_bytes() == b for r, b in before.items()))
        ok("idempotent: second Inbox pass still reports b/e, moves nothing", rc3 == 3 and (inbox / "b.pdf").exists() and (inbox / "e.pdf").exists())
        by = {r["run_id"]: r for r in read_home()}
        agg3 = aggregate(list(by.values()), [])
        st3 = {f["file"]: file_state(f, agg3, by) for f in scan_inbox()}
        ok("dashboard states after ingest: registered / filed-has-full / filed-uncited / filed-nodoi",
           st3["Smith2026_TEST.2026.1.pdf"] == "registered" and st3["Hand2021_BF.2021.7.pdf"] == "registered"
           and st3["Neg2025_TEST.2.pdf"] == "filed-has-full" and st3["Dee2024_uncited.9.pdf"] == "filed-uncited"
           and next(v for k, v in st3.items() if k.startswith("Nodoi2019_")) == "filed-nodoi")
    finally:
        CROSSREF = _crossref
    return 0


def selftest() -> int:
    """Positive control: a run with one abstract row + one hand_to_user stub -> 1 missing.
    Negative control: a run whose only row on that key is full -> 0 missing. Then the ingest controls."""
    fails = 0

    def ok(name, cond):
        nonlocal fails
        print(("  ok   " if cond else "  FAIL ") + name)
        if not cond:
            fails += 1

    with tempfile.TemporaryDirectory() as td:
        h = Path(td) / "EvidenceRuns"
        pos = h / "20260101_pos"
        (pos / "sources").mkdir(parents=True)
        (pos / "run.json").write_text(json.dumps({"run": {"state": "open", "created": "2026-01-01"}, "request": {"question": "q"}}), encoding="utf-8")
        (pos / "ledger.jsonl").write_text(json.dumps({"claim_id": "C1", "claim": "x", "source_id": "10.1109/TEST.2026.1", "cite_as": "A 2026",
                                                     "expect_year": 2026, "access_tag": "abstract", "source_text": "sources/a_s2.txt"}) + "\n", encoding="utf-8")
        (pos / "sources" / "manifest.json").write_text(json.dumps({"entries": {"a_s2": {"route": "script"}, "a": {"route": "hand_to_user", "url": "https://ieeexplore.ieee.org/document/1", "host": "ieeexplore.ieee.org", "policy_class": "agent_banned"}}}), encoding="utf-8")
        neg = h / "20260102_neg"
        (neg / "sources").mkdir(parents=True)
        (neg / "run.json").write_text(json.dumps({"run": {"state": "delivered"}, "request": {"question": "q"}}), encoding="utf-8")
        (neg / "ledger.jsonl").write_text(json.dumps({"claim_id": "C1", "claim": "y", "source_id": "10.3390/TEST.2", "cite_as": "B 2025",
                                                     "expect_year": 2025, "access_tag": "full", "source_text": "sources/b.txt"}) + "\n", encoding="utf-8")
        os.environ["LSE_RUN_HOME"] = str(h)
        os.environ["LSE_INBOX"] = str(Path(td) / "Inbox")
        os.environ["LSE_BIB_HOME"] = str(Path(td) / "Bib")
        runs = read_home()
        agg = aggregate(runs, [])
        ok("two runs read", len(runs) == 2)
        ok("positive control: IEEE source reported missing", [s["key"] for s in agg["missing"]] == ["doi:10.1109/test.2026.1"])
        ok("stub linked to the abstract row's key (not a stub: orphan)", agg["missing"][0]["urls"] and agg["missing"][0]["publisher"] == "IEEE")
        ok("negative control: full-only MDPI source NOT missing", not agg["sources"]["doi:10.3390/test.2"]["missing"])
        # the same key read full in another run lifts it out of missing
        agg2 = aggregate(runs + [{"run_id": "r3", "rows": [{"source_id": "10.1109/TEST.2026.1", "access_tag": "full", "source_text": "sources/a.txt"}], "stubs": {}, "manifest": {}}], [])
        ok("full row in a later run lifts the debt", not agg2["sources"]["doi:10.1109/test.2026.1"]["missing"])
        ok("correction event lifts the debt", not aggregate(runs, [{"kind": "correction", "key": "doi:10.1109/test.2026.1"}])["sources"]["doi:10.1109/test.2026.1"]["missing"])
        bib = build_bib(agg, runs)
        ok("bib has both read papers", sorted(i.get("doi") for i in bib["items"]) == ["10.1109/test.2026.1", "10.3390/test.2"])
        rc = cmd_dashboard(argparse.Namespace(out=None))
        html_path = Path(os.environ["LSE_INBOX"]) / "dashboard.html"
        ok("dashboard written with page class", rc == 0 and 'data-page-class="dashboard"' in html_path.read_text(encoding="utf-8"))
        ok("README written once", (Path(os.environ["LSE_INBOX"]) / "README.md").exists())
        fails += _selftest_ingest(Path(td), h, ok)
        for k in ("LSE_RUN_HOME", "LSE_INBOX", "LSE_BIB_HOME", "LSE_FETCH_SCRATCH"):
            os.environ.pop(k, None)
    print("selftest:", "PASS" if not fails else f"FAIL ({fails})")
    return 0 if not fails else 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("scan"); s.add_argument("--json", action="store_true")
    d = sub.add_parser("dashboard"); d.add_argument("--out")
    b = sub.add_parser("bib"); b.add_argument("--out"); b.add_argument("--ris", action="store_true", help="also resolve every DOI via Crossref into <collection>.ris (network)")
    i = sub.add_parser("ingest")
    i.add_argument("--apply", action="store_true", help="move and register (default: dry-run)")
    i.add_argument("--filed", action="store_true", help="register PDFs already in filed\\ (backfill; never renamed)")
    i.add_argument("--offline", action="store_true", help="no Crossref fallback for first author / year")
    i.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.cmd == "ingest":
        return cmd_ingest(a)
    if a.cmd == "scan":
        return cmd_scan(a)
    if a.cmd == "dashboard":
        return cmd_dashboard(a)
    if a.cmd == "bib":
        return cmd_bib(a)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
