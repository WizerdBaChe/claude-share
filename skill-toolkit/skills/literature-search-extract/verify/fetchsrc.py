#!/usr/bin/env python3
r"""fetchsrc — the only sanctioned way a run writes sources/<name>.txt.

WHY THIS EXISTS. P4.5's citecheck proves a support span exists verbatim in
`sources/<name>.txt`. It never asked where that file came from — an executor who
typed the "retrieved text" from memory would pass the span check with a text it
wrote itself. That is the fabrication vector the NTU library guide's golden rule
(逐一確認資料正確前絕不引用) points at, and no gate in this skill could see it.
This tool closes it by being the instrument that produces the file AND writes a
provenance manifest beside it (`sources/manifest.json`): url or path, host, route,
HTTP status, sha256, bytes, time, tool. citecheck's `provenance` check then rules on
the manifest; a text with no entry is what the check catches.

It is also the "instrument side" of rules/literature-access.md: it consults the
host policy BEFORE it fetches, prints host / route / status per source, treats a
challenge as a routing outcome, and never retries with another costume.

TWO THINGS IT REFUSES TO DO, by design:
  * fetch a host the policy bans, or with a surface the row does not list — it
    prints `HAND-TO-USER: <url>` and exits 3 (a licensed empty answer);
  * keep a licensed full text in the vault. A row with retention `excerpt` sends
    the full text to the SESSION SCRATCH and leaves only a manifest stub in the run;
    `excerpt` later derives sources/<name>.txt from the ledger's support spans
    (±WINDOW chars each). Nothing in the run folder is ever rewritten.

ROUTES (the manifest's `route` field):
  script          this tool fetched it over HTTP                — origin verifiable
  local_pdf       text extracted from a PDF on disk (pymupdf)   — origin = the file's sha256
  user_provided   a passage the USER handed over (`paste`)      — origin NOT verifiable:
                  citecheck WARNs and names it so a Licensed User can refute it;
                  FAIL in Mode 2, where no human is downstream to confirm
  hand_to_user    refused or challenged: a stub only, no text

Usage:
    python fetchsrc.py fetch   --run <dir> --url <u> --name <n> [--oa <licence note>]
    python fetchsrc.py local   --run <dir> --pdf <path> --name <n> [--oa <licence note>]
    python fetchsrc.py paste   --run <dir> --from <file> --name <n> [--oa <licence note>]
    python fetchsrc.py excerpt --run <dir> [--window 400]
    python fetchsrc.py status  --run <dir>
    python fetchsrc.py --selftest
Exit: 0 written · 2 usage · 3 refused / challenged (HAND-TO-USER line printed too, because
PowerShell `*>` loses exit codes — ops/lessons.md L-081).
review-when: the policy schema changes; citecheck renames `source_text`; arXiv pacing changes.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))                    # spannorm: the shared normal form, imported below
sys.path.insert(0, str(HERE.parent / "connectors"))
import access_policy  # noqa: E402

TOOL = "fetchsrc/1"
TIMEOUT = 25
WINDOW = 400
_BASE_UA = "literature-search-extract-fetchsrc/1 (local, interactive)"
CONTACT_BY_HOST = {"arxiv.org": "<contact-email>", "export.arxiv.org": "<contact-email>"}  # arXiv-only consent 2026-08-27
PACING_S = {"arxiv.org": 3.0, "export.arxiv.org": 3.0}
CHALLENGE_STATUS = {202, 401, 403, 407, 418, 429, 503}
CHALLENGE_MARKERS = ("cf-chl", "challenge-platform", "captcha", "just a moment", "radware", "anubis",
                     "proof-of-work", "botstopper", "access denied", "are you a robot", "verify you are human")
MAX_BYTES = 8_000_000


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_text_lf(p: Path, text: str) -> None:
    """Write a source text so the BYTES ON DISK are the bytes we hashed.

    Every payload this tool stores is hashed in memory (LF) and the manifest's sha256 is what
    citecheck's provenance check later compares the file against. `Path.write_text` opens in
    universal-newline text mode, so on Windows it silently turns every "\\n" into "\\r\\n" AFTER
    the hash was taken: the check then reads bytes nobody hashed and rules "edited after
    retrieval" on every multi-line source. `newline=""` writes the string through unchanged, so
    a run is byte-identical on Windows and POSIX. Never use write_text for a hashed payload.
    (SSLD T00 L8, 2026-09-12 — 12 of 12 multi-line sources FAILed provenance.)
    """
    with p.open("w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def scratch_root() -> Path:
    env = os.environ.get("LSE_FETCH_SCRATCH")
    if env:
        return Path(env)
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("TMPDIR") or "/tmp"
    return Path(base) / "Temp" / "lse-fetch"


# ---------------------------------------------------------------- manifest
def manifest_path(run: Path) -> Path:
    return run / "sources" / "manifest.json"


def load_manifest(run: Path) -> dict:
    p = manifest_path(run)
    if p.exists():
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(m, dict) and isinstance(m.get("entries"), dict):
                return m
        except Exception:                                # noqa: BLE001
            pass
    return {"schema": "lse-sources-manifest@1", "tool": TOOL, "entries": {}}


def save_manifest(run: Path, m: dict) -> None:
    (run / "sources").mkdir(parents=True, exist_ok=True)
    manifest_path(run).write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def run_counts(m: dict) -> tuple[dict, set]:
    per_host: dict = {}
    unlisted: set = set()
    for e in m["entries"].values():
        if e.get("route") not in ("script", "webfetch"):
            continue
        if e.get("status") in ("written", "scratch"):
            per_host[e.get("host", "")] = per_host.get(e.get("host", ""), 0) + 1
            if e.get("policy_row") == "unlisted":
                unlisted.add(e.get("host", ""))
    return per_host, unlisted


# ---------------------------------------------------------------- text extraction
def html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript|svg|head)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</h[1-6]>|</tr>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
    raw = re.sub(r"\n\s*\n+", "\n\n", raw)
    return raw.strip()


def pdf_bytes_to_text(b: bytes) -> str:
    try:
        import fitz  # type: ignore
        doc = fitz.open(stream=b, filetype="pdf")
        return "\n".join(p.get_text() for p in doc)
    except ImportError:
        from io import BytesIO
        from pypdf import PdfReader  # type: ignore
        r = PdfReader(BytesIO(b))
        return "\n".join((p.extract_text() or "") for p in r.pages)


def looks_challenged(status: int, body_head: str) -> bool:
    if status in CHALLENGE_STATUS:
        return True
    low = body_head.lower()
    return any(k in low for k in CHALLENGE_MARKERS)


def _http_get(url: str) -> tuple[int, bytes, str, str]:
    """(status, body, content_type, final_url). ONE request. urllib follows redirects itself, so the
    bytes may come from another host: `final_url` is what the caller re-judges against the policy
    (QA 2026-09-11 F-3 — the policy decision is made on the host the bytes actually came from)."""
    host = access_policy.host_of(url)
    contact = CONTACT_BY_HOST.get(host)
    ua = f"{_BASE_UA} mailto:{contact}" if contact else _BASE_UA
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "text/html,application/pdf,application/json,text/plain,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read(MAX_BYTES), (r.headers.get("Content-Type") or ""), (r.url or url)
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(200_000)
        except Exception:                                # noqa: BLE001
            body = b""
        return exc.code, body, ((exc.headers.get("Content-Type") or "") if exc.headers else ""), (getattr(exc, "url", "") or url)
    except Exception as exc:                             # noqa: BLE001
        return 0, str(exc).encode("utf-8", "replace"), "", url


HTTP_GET = _http_get   # selftest swaps this for a canned responder (3- or 4-tuple accepted)


def _get(url: str) -> tuple[int, bytes, str, str]:
    r = HTTP_GET(url)
    return (r[0], r[1], r[2], r[3]) if len(r) >= 4 else (r[0], r[1], r[2], url)


NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,119}")


def valid_name(name: str) -> bool:
    """A source name is one path segment: no separators, no `..`, no leading dot (QA 2026-09-11 F-2)."""
    return bool(name) and bool(NAME_RE.fullmatch(name)) and ".." not in name


def _pacing_path() -> Path:
    return scratch_root() / "pacing.json"


def _pace(host: str) -> None:
    """Per-host pacing state lives in scratch, never in the run's manifest (QA F-16)."""
    wait = PACING_S.get(host)
    if not wait:
        return
    p = _pacing_path()
    try:
        state = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:                                    # noqa: BLE001
        state = {}
    last = state.get(host)
    if last:
        delta = time.time() - float(last)
        if delta < wait:
            time.sleep(wait - delta)
    state[host] = time.time()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state), encoding="utf-8")
    except Exception:                                    # noqa: BLE001
        pass


# ---------------------------------------------------------------- write paths
def _store(run: Path, m: dict, name: str, text: str, entry: dict, retention: str) -> str:
    """Write text per retention. Returns the entry status."""
    if not valid_name(name):
        raise ValueError(f"invalid source name {name!r}: one path segment [A-Za-z0-9._-], no '..'")
    # LF is a PROPERTY of a stored source, not an accident of where the text came from: a PDF
    # extractor that hands back "\r\n" would otherwise give the same document a different sha on a
    # different machine. Normalise at the door, hash after, write through unchanged (write_text_lf).
    # Same shape as tools/archdiag/index.mjs, which normalises at emission because its sha256 is a
    # freeze receipt; ~/.claude/.gitattributes §"receipt-stable regeneration assets" is the ruling.
    text = text.replace("\r\n", "\n")
    full_sha = sha256_bytes(text.encode("utf-8"))
    entry.update({"sha256_full": full_sha, "bytes": len(text.encode("utf-8")), "chars": len(text),
                  "retention_policy": retention, "fetched_at": now_iso(), "tool": TOOL})
    if retention == "full":
        p = run / "sources" / f"{name}.txt"
        write_text_lf(p, text)
        entry.update({"retention_state": "full", "status": "written", "file": f"sources/{name}.txt",
                      "sha256_file": full_sha})
    else:
        sd = scratch_root() / run.name
        sd.mkdir(parents=True, exist_ok=True)
        sp = sd / f"{name}.txt"
        write_text_lf(sp, text)
        entry.update({"retention_state": "pending-excerpt", "status": "scratch", "scratch_path": str(sp),
                      "file": f"sources/{name}.txt"})
    m["entries"][name] = entry
    save_manifest(run, m)
    return entry["status"]


def refuse(run: Path, m: dict, name: str, entry: dict, why: str, target: str) -> int:
    entry.update({"route": "hand_to_user", "status": "refused", "reason": why, "fetched_at": now_iso(), "tool": TOOL})
    m["entries"][name] = entry
    save_manifest(run, m)
    print(f"HAND-TO-USER: {target} — {why}")
    print("  (not retrieved; record it in `gaps` as 'not retrieved, hand-to-user', never as 'not found')")
    return 3


def _bad_name(name: str) -> int:
    print(f"invalid --name {name!r}: one path segment [A-Za-z0-9._-] (max 120 chars), no '..' — nothing written")
    return 2


def cmd_fetch(a) -> int:
    if not valid_name(a.name):
        return _bad_name(a.name)
    run = Path(a.run).resolve()
    m = load_manifest(run)
    host = access_policy.host_of(a.url)
    pol = access_policy.load()
    per_host, unlisted = run_counts(m)
    allowed, reason, row = access_policy.decide(host, "script", pol, used_on_host=per_host.get(host, 0),
                                                distinct_unlisted=len(unlisted - {host}))
    entry = {"name": a.name, "url": a.url, "host": host, "policy_row": "unlisted" if row.get("unlisted") else row.get("host"),
             "policy_class": row.get("class"), "licence_basis": a.oa or row.get("licence_basis", ""),
             "policy_verified": row.get("verified", "")}
    if not allowed:
        return refuse(run, m, a.name, entry, reason, a.url)
    _pace(host)
    status, body, ctype, final_url = _get(a.url)
    final_host = access_policy.host_of(final_url) or host
    if final_host != host:
        # the bytes came from another host: judge THAT host, with the counts it already carries (QA F-3)
        allowed, reason, row = access_policy.decide(final_host, "script", pol, used_on_host=per_host.get(final_host, 0),
                                                    distinct_unlisted=len(unlisted - {final_host}))
        entry.update({"requested_url": a.url, "requested_host": host, "url": final_url, "host": final_host,
                      "redirected": True, "policy_row": "unlisted" if row.get("unlisted") else row.get("host"),
                      "policy_class": row.get("class"), "licence_basis": a.oa or row.get("licence_basis", ""),
                      "policy_verified": row.get("verified", "")})
        if not allowed:
            body = b""       # the bytes are discarded, never stored
            return refuse(run, m, a.name, entry, f"redirected to {final_host}: {reason}", final_url)
        host = final_host
    head = body[:4000].decode("utf-8", "replace")
    entry.update({"route": "script", "http_status": status, "content_type": ctype[:80]})
    print(f"fetch {a.name}: host={host} route=script status={status} bytes={len(body)}"
          + (f" (redirected from {entry['requested_host']})" if entry.get("redirected") else ""))
    if status != 200 or looks_challenged(status, head):
        why = (f"HTTP {status}" + (" (challenge / bot management)" if looks_challenged(status, head) else "")
               + " — a challenge is a routing signal, not an obstacle: no retry with another User-Agent, cookie jar, "
                 "headless browser or logged-in profile")
        entry["challenge"] = looks_challenged(status, head)
        return refuse(run, m, a.name, entry, why, a.url)
    if "pdf" in ctype.lower() or body[:5] == b"%PDF-":
        text = pdf_bytes_to_text(body)
        entry["kind"] = "pdf"
    elif "html" in ctype.lower() or b"<html" in body[:2000].lower():
        text = html_to_text(body.decode("utf-8", "replace"))
        entry["kind"] = "html"
    else:
        text = body.decode("utf-8", "replace")
        entry["kind"] = "text"
    retention = "full" if a.oa else row.get("retention", "excerpt")
    st = _store(run, m, a.name, text, entry, retention)
    print(f"  {st}: {len(text):,} chars, retention={retention}"
          + (" (full text in scratch; run `fetchsrc.py excerpt` after the ledger exists)" if st == "scratch" else ""))
    return 0


def cmd_local(a) -> int:
    if not valid_name(a.name):
        return _bad_name(a.name)
    run = Path(a.run).resolve()
    m = load_manifest(run)
    pdf = Path(a.pdf)
    if not pdf.exists():
        print(f"no such file: {pdf}")
        return 2
    b = pdf.read_bytes()
    text = pdf_bytes_to_text(b)
    entry = {"name": a.name, "path": str(pdf), "host": "", "route": "local_pdf", "kind": "pdf",
             "sha256_source_file": sha256_bytes(b), "policy_row": "n/a", "policy_class": "local",
             "licence_basis": a.oa or "user's own copy on disk (Zotero storage / local library); text is a working derivative"}
    if getattr(a, "key", ""):
        # identity key of the work this PDF is (loop/inbox.py ingest passes it): lets the dashboard
        # lift the source out of "missing full text" without re-reading the PDF
        entry["key"] = a.key
    st = _store(run, m, a.name, text, entry, "full" if a.oa else "excerpt")
    print(f"local {a.name}: route=local_pdf sha256={entry['sha256_source_file'][:12]} chars={len(text):,} {st}")
    return 0


def cmd_paste(a) -> int:
    if not valid_name(a.name):
        return _bad_name(a.name)
    run = Path(a.run).resolve()
    m = load_manifest(run)
    src = Path(getattr(a, "from"))
    if not src.exists():
        print(f"no such file: {src}")
        return 2
    text = src.read_text(encoding="utf-8", errors="replace")
    entry = {"name": a.name, "path": str(src), "host": access_policy.host_of(a.origin) if a.origin else "",
             "origin_url": a.origin or "", "route": "user_provided", "origin_verifiable": False,
             "policy_row": "n/a", "policy_class": "user_provided",
             "licence_basis": a.oa or "passage handed over by the user (a Licensed User); the agent did not retrieve it",
             "note": "origin is NOT machine-verifiable: citecheck WARNs (FAIL in Mode 2) and the deliverable's source list "
                     "prints [user-provided passage] so the user can refute it"}
    st = _store(run, m, a.name, text, entry, "full" if a.oa else "excerpt")
    print(f"paste {a.name}: route=user_provided (origin unverifiable) chars={len(text):,} {st}")
    return 0


# ---------------------------------------------------------------- excerpt (retention pass)
# The normal form is defined ONCE, in spannorm.py, and this pass imports it rather than
# re-implementing it. It used to be a hand-written char walk that was meant to match
# citecheck.norm() and measurably did not (3171 of 4000 random strings folded differently;
# 247 of those changed a hyphen ruling). What cuts the excerpt and what rules on the span
# must be the same function, or the cutter removes the text the gate then asks for.
from spannorm import norm_span, norm_with_map  # noqa: E402,F401  (re-exported for callers)


def ledger_spans_for(run: Path, name: str) -> list[str]:
    p = run / "ledger.jsonl"
    spans: list[str] = []
    if not p.exists():
        return spans
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        try:
            row = json.loads(line)
        except Exception:                                # noqa: BLE001
            continue
        ref = str(row.get("source_text") or "")
        if Path(ref).name == f"{name}.txt" and row.get("support_span"):
            spans.append(str(row["support_span"]))
    return spans


def excerpt_text(full: str, spans: list[str], window: int) -> tuple[str, int, list[str]]:
    ns, idx = norm_with_map(full)
    ranges: list[tuple[int, int]] = []
    missing: list[str] = []
    for sp in spans:
        q = norm_span(sp)
        pos = ns.find(q) if q else -1
        if pos < 0 or not idx:
            missing.append(sp)
            continue
        raw_a = idx[pos]
        raw_b = idx[min(pos + len(q) - 1, len(idx) - 1)] + 1
        ranges.append((max(0, raw_a - window), min(len(full), raw_b + window)))
    ranges.sort()
    merged: list[list[int]] = []
    for a_, b_ in ranges:
        if merged and a_ <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b_)
        else:
            merged.append([a_, b_])
    parts = [full[a_:b_] for a_, b_ in merged]
    return "\n[…]\n".join(parts), len(spans) - len(missing), missing


def cmd_excerpt(a) -> int:
    """Derive excerpt windows from the scratch full text. Re-derives an already-excerpted entry when the
    ledger now cites a different set of spans than the one recorded (`spans_cited`), or with --redo
    (QA 2026-09-11 F-11); the scratch copy must still exist for that."""
    run = Path(a.run).resolve()
    m = load_manifest(run)
    redo = bool(getattr(a, "redo", False))
    done = 0
    for name, e in list(m["entries"].items()):
        if e.get("retention_policy") != "excerpt":
            continue
        state = e.get("retention_state")
        spans = ledger_spans_for(run, name)
        if state == "excerpt":
            stale = sorted(set(spans)) != sorted(set(e.get("spans_cited") or []))
            if not (redo or stale):
                continue
            sp = Path(e.get("scratch_path", ""))
            if not sp.exists():
                print(f"{name}: ledger spans changed since the excerpt was derived but the scratch copy is gone "
                      f"({sp}) — re-fetch, then run excerpt again; file left as is")
                continue
            full = sp.read_text(encoding="utf-8", errors="replace")
            print(f"{name}: re-deriving ({'--redo' if redo else 'ledger spans changed'})")
        elif state == "pending-excerpt":
            sp = Path(e.get("scratch_path", ""))
            if not sp.exists():
                print(f"{name}: scratch copy missing ({sp}) — re-fetch; nothing written")
                continue
            full = sp.read_text(encoding="utf-8", errors="replace")
        else:
            print(f"{name}: retention_state {state!r} — nothing to do")
            continue
        if not spans:
            print(f"{name}: no ledger row cites sources/{name}.txt yet — write the ledger first; nothing written")
            continue
        text, found, missing = excerpt_text(full, spans, a.window)
        p = run / "sources" / f"{name}.txt"
        write_text_lf(p, text)
        e.update({"retention_state": "excerpt", "status": "written", "spans_found": found, "spans_missing": missing,
                  "spans_cited": sorted(set(spans)), "window": a.window,
                  "sha256_file": sha256_bytes(text.encode("utf-8")), "excerpted_at": now_iso()})
        m["entries"][name] = e
        done += 1
        print(f"{name}: excerpt written — {found}/{len(spans)} spans, {len(text):,} chars"
              + (f"; MISSING spans: {[s[:40] for s in missing]}" if missing else ""))
    save_manifest(run, m)
    print(f"{done} file(s) excerpted")
    return 0


def cmd_status(a) -> int:
    run = Path(a.run).resolve()
    m = load_manifest(run)
    for name, e in m["entries"].items():
        print(f"{name:24} route={e.get('route', '-'):13} status={e.get('status', '-'):9} host={e.get('host', '-') or '-':28} "
              f"http={e.get('http_status', '-')} retention={e.get('retention_policy', '-')}/{e.get('retention_state', '-')}")
    per_host, unlisted = run_counts(m)
    print(f"{len(m['entries'])} entries; per-host {per_host}; distinct unlisted hosts {sorted(unlisted)}")
    return 0


# ---------------------------------------------------------------- selftest (two-sided, hermetic)
def selftest() -> int:
    import tempfile
    global HTTP_GET
    bad = 0

    def ok(label: str, cond: bool, detail: str = "") -> None:
        nonlocal bad
        bad += 0 if cond else 1
        print(f"{'ok' if cond else 'BROKEN':9} {label}" + ("" if cond else f"   <- {detail}"))

    calls: list[str] = []
    canned = {
        # both bodies carry MORE THAN ONE paragraph on purpose: html_to_text then puts a real "\n" in the
        # stored text, which is what the platform's text-mode newline translation would corrupt. A
        # single-line fixture cannot see that defect (it was blind to it until 2026-09-12).
        "https://open.example/paper": (200, b"<html><body><p>We report a propagation length of 200 um at 780 nm for silver "
                                             b"films.</p><p>A second paragraph, so the stored text contains a newline."
                                             b"</p><script>x</script></body></html>", "text/html"),
        "https://landing.example/a1": (200, b"<html><p>Abstract: the film shows sub-nanometer roughness of 0.4 nm RMS " +
                                            b"in every sample measured.</p><p> " * 40 + b"</p></html>", "text/html"),
        "https://landing.example/a2": (200, b"<html><p>second</p></html>", "text/html"),
        "https://wall.example/x": (403, b"<html>Just a moment... cf-chl challenge-platform</html>", "text/html"),
        "https://nobody1.example/p": (200, b"<html><p>one</p></html>", "text/html"),
        "https://nobody2.example/p": (200, b"<html><p>two</p></html>", "text/html"),
        "https://nobody3.example/p": (200, b"<html><p>three</p></html>", "text/html"),
        "https://nobody4.example/p": (200, b"<html><p>four</p></html>", "text/html"),
        # a redirect the transport followed: the bytes come from the banned host (QA F-3)
        "https://open.example/redirect-me": (200, b"<html><p>licensed body</p></html>", "text/html",
                                             "https://banned.example/after-redirect"),
        "https://open.example/redirect-open": (200, b"<html><p>moved but still open</p></html>", "text/html",
                                               "https://www.open.example/moved"),
    }

    def fake_get(url: str):
        calls.append(url)
        return canned.get(url, (404, b"", "text/html"))

    pol = {"schema": "literature-host-policy@1",
           "unlisted_default": {"class": "unlisted", "agent_surfaces": ["script", "webfetch"], "max_per_run": 1,
                                "retention": "excerpt", "run_cap_distinct_unlisted_hosts": 3},
           "hosts": [{"host": "open.example", "class": "open", "agent_surfaces": ["script", "webfetch"], "max_per_run": 5, "retention": "full"},
                     {"host": "landing.example", "class": "landing_page", "agent_surfaces": ["script", "webfetch"], "max_per_run": 1, "retention": "excerpt"},
                     {"host": "wall.example", "class": "landing_page", "agent_surfaces": ["script", "webfetch"], "max_per_run": 3, "retention": "excerpt"},
                     {"host": "banned.example", "class": "agent_banned", "agent_surfaces": [], "max_per_run": 0, "retention": "excerpt",
                      "licence_basis": "ToU forbids intelligent agents"}]}
    with tempfile.TemporaryDirectory(prefix="fetchsrc-selftest-") as tmp:
        tmpp = Path(tmp)
        (tmpp / "policy.json").write_text(json.dumps(pol), encoding="utf-8")
        os.environ["LSE_HOST_POLICY"] = str(tmpp / "policy.json")
        os.environ["LSE_FETCH_SCRATCH"] = str(tmpp / "scratch")
        run = tmpp / "20260911_selftest"
        (run / "sources").mkdir(parents=True)
        HTTP_GET = fake_get
        try:
            class A:  # minimal argparse stand-in
                def __init__(self, **kw): self.__dict__.update(kw)

            # 1 banned host: refused, no HTTP call
            n0 = len(calls)
            rc = cmd_fetch(A(run=str(run), url="https://banned.example/doc", name="banned", oa=""))
            ok("must-REFUSE banned host (exit 3, zero HTTP calls)", rc == 3 and len(calls) == n0, f"rc={rc} calls={len(calls) - n0}")
            m = load_manifest(run)
            ok("must-RECORD refusal as hand_to_user stub", m["entries"].get("banned", {}).get("route") == "hand_to_user")
            # 2 open host: full text written + manifest sha
            rc = cmd_fetch(A(run=str(run), url="https://open.example/paper", name="open", oa=""))
            m = load_manifest(run)
            e = m["entries"].get("open", {})
            f = run / "sources" / "open.txt"
            ok("must-WRITE open host full text", rc == 0 and f.exists() and "propagation length of 200 um" in f.read_text(encoding="utf-8"))
            ok("must-STRIP script tags", "x" != f.read_text(encoding="utf-8").strip()[-1] and "<script>" not in f.read_text(encoding="utf-8"))
            ok("must-RECORD sha256 matching the file", e.get("sha256_file") == sha256_bytes(f.read_bytes()) and e.get("route") == "script")
            # the manifest hash is a hash of BYTES ON DISK: assert against read_bytes(), never read_text()
            # (read_text folds CRLF back to LF and would hide the defect). A text with no newline cannot
            # exercise this, hence the multi-paragraph fixture above.
            raw = f.read_bytes()
            n_crlf = raw.count(b"\r\n")
            ok("must-STORE the text with the newline it was hashed with (no platform CRLF translation)",
               b"\n" in raw and n_crlf == 0, f"{n_crlf} CRLF in {f.name}")
            # 3 landing (excerpt) host: scratch only, no file in the run
            rc = cmd_fetch(A(run=str(run), url="https://landing.example/a1", name="landing", oa=""))
            m = load_manifest(run)
            e = m["entries"].get("landing", {})
            ok("must-NOT write licensed full text into the run folder", rc == 0 and not (run / "sources" / "landing.txt").exists())
            ok("must-KEEP full text in scratch with pending-excerpt state",
               e.get("retention_state") == "pending-excerpt" and Path(e.get("scratch_path", "")).exists())
            sraw = Path(e.get("scratch_path", "")).read_bytes()
            ok("must-RECORD sha256_full matching the scratch bytes (feedback-loop.md: sha256_full proves the "
               "excerpt came from that text)", b"\n" in sraw and e.get("sha256_full") == sha256_bytes(sraw),
               f"{sraw.count(b'\r\n')} CRLF in scratch")
            # 4 max_per_run on landing host
            rc = cmd_fetch(A(run=str(run), url="https://landing.example/a2", name="landing2", oa=""))
            ok("must-REFUSE second document on a max_per_run 1 host", rc == 3)
            # 5 challenge: exit 3, exactly one call, no retry
            n0 = len(calls)
            rc = cmd_fetch(A(run=str(run), url="https://wall.example/x", name="wall", oa=""))
            m = load_manifest(run)
            ok("must-STOP on a challenge (exit 3, ONE call, no retry)", rc == 3 and len(calls) - n0 == 1
               and m["entries"]["wall"].get("challenge") is True, f"rc={rc} calls={len(calls) - n0}")
            # 6 unlisted cap: 3 distinct allowed, 4th refused
            rcs = [cmd_fetch(A(run=str(run), url=f"https://nobody{i}.example/p", name=f"nb{i}", oa="")) for i in (1, 2, 3)]
            rc4 = cmd_fetch(A(run=str(run), url="https://nobody4.example/p", name="nb4", oa=""))
            ok("must-ALLOW three distinct unlisted hosts, REFUSE the fourth", rcs == [0, 0, 0] and rc4 == 3, f"{rcs} {rc4}")
            # 6b QA F-2: a --name that is not one path segment is refused before anything is written
            outside = tmpp / "outside_run_marker.txt"
            rc = cmd_fetch(A(run=str(run), url="https://open.example/paper", name="../../outside_run_marker", oa=""))
            ok("must-REFUSE a traversal --name (exit 2, nothing written outside the run)", rc == 2 and not outside.exists(), f"rc={rc}")
            rc = cmd_fetch(A(run=str(run), url="https://open.example/paper", name="a/b", oa=""))
            ok("must-REFUSE a --name with a separator", rc == 2)
            # 6c QA F-3: a redirect onto a banned host is judged on the FINAL host; the bytes are not stored
            rc = cmd_fetch(A(run=str(run), url="https://open.example/redirect-me", name="redir", oa=""))
            m = load_manifest(run)
            e = m["entries"].get("redir", {})
            ok("must-REFUSE bytes that arrived from a banned host after a redirect (final host judged)",
               rc == 3 and e.get("route") == "hand_to_user" and e.get("host") == "banned.example"
               and e.get("redirected") is True and not (run / "sources" / "redir.txt").exists(), f"rc={rc} host={e.get('host')}")
            rc = cmd_fetch(A(run=str(run), url="https://open.example/redirect-open", name="redir2", oa=""))
            m = load_manifest(run)
            e = m["entries"].get("redir2", {})
            ok("must-ALLOW a redirect that stays on an open host and record the final URL",
               rc == 0 and e.get("host") == "www.open.example" and e.get("url") == "https://www.open.example/moved", f"rc={rc} {e.get('url')}")
            ok("must-KEEP pacing state out of the manifest (QA F-16)", "_last_fetch" not in m)
            # 7 excerpt: ledger span -> window; full text gone from the run, span present
            ledger = run / "ledger.jsonl"
            ledger.write_text(json.dumps({"claim_id": "C1", "claim": "roughness 0.4 nm RMS", "source_id": "10.1000/x",
                                          "cite_as": "Park 2022", "locator": "p.2", "access_tag": "partial",
                                          "support_span": "sub-nanometer roughness of 0.4 nm RMS",
                                          "source_text": "sources/landing.txt"}) + "\n", encoding="utf-8")
            rc = cmd_excerpt(A(run=str(run), window=30))
            m = load_manifest(run)
            e = m["entries"]["landing"]
            txt = (run / "sources" / "landing.txt").read_text(encoding="utf-8")
            ok("must-DERIVE excerpt containing the span", rc == 0 and "sub-nanometer roughness of 0.4 nm RMS" in txt)
            ok("must-SHRINK to windows (not the full text)", len(txt) < len(Path(e["scratch_path"]).read_text(encoding="utf-8")) // 2,
               f"{len(txt)} chars")
            xraw = (run / "sources" / "landing.txt").read_bytes()
            ok("must-RECORD excerpt state + sha", e.get("retention_state") == "excerpt" and e.get("sha256_file") == sha256_bytes(xraw))
            ok("must-WRITE the excerpt with the newline it was hashed with (no CRLF translation)",
               b"\n" in xraw and xraw.count(b"\r\n") == 0, f"{xraw.count(b'\r\n')} CRLF in landing.txt")
            # 7b QA F-11: a second ledger row citing a new span in the same source re-derives the excerpt
            rc = cmd_excerpt(A(run=str(run), window=30))
            ok("must-SKIP an excerpt whose ledger spans are unchanged", rc == 0 and
               (run / "sources" / "landing.txt").read_text(encoding="utf-8") == txt)
            with ledger.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"claim_id": "C2", "claim": "every sample", "source_id": "10.1000/x", "cite_as": "Park 2022",
                                     "locator": "p.2", "access_tag": "partial", "support_span": "in every sample measured",
                                     "source_text": "sources/landing.txt"}) + "\n")
            rc = cmd_excerpt(A(run=str(run), window=30))
            m = load_manifest(run)
            txt2 = (run / "sources" / "landing.txt").read_text(encoding="utf-8")
            ok("must-RE-DERIVE when the ledger cites a new span in an already-excerpted source",
               rc == 0 and "in every sample measured" in txt2 and len(m["entries"]["landing"].get("spans_cited") or []) == 2, f"rc={rc}")
            # 8 excerpt map correctness on hyphenation / whitespace
            full = "The propa-\n  gation   length\nwas 200 um. " + "pad " * 50
            text, found, missing = excerpt_text(full, ["propagation length was 200 um"], 5)
            ok("must-LOCATE a span across hyphenation + collapsed whitespace", found == 1 and "200 um" in text, f"{found} {missing}")
            text, found, missing = excerpt_text(full, ["propagation length was 900 um"], 5)
            ok("must-REPORT a span the text does not contain", found == 0 and missing, f"{found}")
            # 8b SSLD T00 2026-09-12: a lone "-" cell means "not reported" — it is data, not
            # hyphenation. Dropping it wherever it preceded a newline cut an excerpt that no
            # longer carried the span citecheck then demanded to find in it.
            tbl = ("Current work\nMeasured Multi-tip taper\n1550 nm\n-1.50 dB \n- \n- \nCurrent work\n" + "pad " * 50)
            text, found, missing = excerpt_text(tbl, ["Measured Multi-tip taper 1550 nm -1.50 dB - -"], 5)
            ok("must-LOCATE a span ending in two '- -' not-reported cells", found == 1 and not missing, f"{found} {missing}")
            text, found, missing = excerpt_text(tbl, ["-1.50 dB - x"], 5)
            ok("must-REPORT a '- -' span the text does not carry (the rule stayed narrow)", found == 0 and missing, f"{found}")
            try:
                import citecheck as _cc
            except ImportError:
                _cc = None   # share edition: verify/citecheck.py is not shipped; its half of the check below is named, not skipped silently
            import spannorm
            # The cutter and the gate must not merely agree — they must BE the same function.
            # Equality over fixtures is what used to be asserted here, and it passed while the two
            # implementations disagreed on 3171 of 4000 random strings (spannorm.py header).
            if _cc is None:
                ok("must-USE the one shared normal form (fetchsrc half only: citecheck.py is not part of this share)",
                   norm_with_map is spannorm.norm_with_map, "fetchsrc has its own normalizer again")
            else:
                ok("must-USE the one shared normal form, not a copy that agrees on the fixtures",
                   norm_with_map is spannorm.norm_with_map and _cc.norm is spannorm.norm,
                   "fetchsrc or citecheck has its own normalizer again")
            _rule = spannorm.selfcheck()
            ok("must-HOLD the normal form's own properties (spannorm.selfcheck)", not _rule, f"{_rule}")
            text, found, missing = excerpt_text("on wafer-\nscale high-density arrays here " + "pad " * 50,
                                                ["wafer-scale high-density arrays"], 5)
            ok("must-LOCATE a span whose compound was split at its own hyphen", found == 1 and not missing,
               f"{found} {missing}")
            # 9 paste: origin unverifiable flagged
            (tmpp / "p.txt").write_text("the user pasted this passage " * 30, encoding="utf-8")
            a = A(run=str(run), name="pasted", oa="", origin="")
            setattr(a, "from", str(tmpp / "p.txt"))
            rc = cmd_paste(a)
            m = load_manifest(run)
            ok("must-MARK paste as user_provided / origin_verifiable false",
               rc == 0 and m["entries"]["pasted"].get("route") == "user_provided" and m["entries"]["pasted"].get("origin_verifiable") is False)
            # 9b a producer that hands back CRLF (a PDF extractor on Windows) must not change the
            # document's identity: the store normalises at the door, so the sha is platform-free
            crlf_entry = {"name": "crlfsrc", "route": "local_pdf", "host": "", "policy_row": "n/a"}
            _store(run, m, "crlfsrc", "line one\r\nline two\r\n", crlf_entry, "full")
            m = load_manifest(run)
            craw = (run / "sources" / "crlfsrc.txt").read_bytes()
            ok("must-NORMALISE a CRLF-bearing producer text to LF before hashing it",
               craw == b"line one\nline two\n" and m["entries"]["crlfsrc"]["sha256_file"] == sha256_bytes(craw),
               f"{craw!r}")
            # 10 local pdf (only if a PDF library is present)
            try:
                import fitz  # type: ignore
                doc = fitz.open()
                page = doc.new_page()
                page.insert_text((72, 72), "A tiny PDF with a value of 42 nm here.")
                pdfp = tmpp / "t.pdf"
                doc.save(str(pdfp))
                rc = cmd_local(A(run=str(run), pdf=str(pdfp), name="tiny", oa="yes"))
                m = load_manifest(run)
                ok("must-EXTRACT a local PDF and record its sha256", rc == 0 and (run / "sources" / "tiny.txt").exists()
                   and "42 nm" in (run / "sources" / "tiny.txt").read_text(encoding="utf-8")
                   and m["entries"]["tiny"].get("sha256_source_file") == sha256_bytes(pdfp.read_bytes()))
            except ImportError:
                print("skip      local-pdf case (pymupdf not installed)")
        finally:
            HTTP_GET = _http_get
            os.environ.pop("LSE_HOST_POLICY", None)
            os.environ.pop("LSE_FETCH_SCRATCH", None)
    print("-" * 72)
    print(f"{bad} broken — {'calibrated' if not bad else 'NOT TRUSTWORTHY'}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    f = sub.add_parser("fetch"); f.add_argument("--run", required=True); f.add_argument("--url", required=True); f.add_argument("--name", required=True); f.add_argument("--oa", default="")
    l = sub.add_parser("local"); l.add_argument("--run", required=True); l.add_argument("--pdf", required=True); l.add_argument("--name", required=True); l.add_argument("--oa", default="")
    l.add_argument("--key", default="", help="identity key of the work (doi:… / arxiv:…), recorded in the manifest entry")
    p = sub.add_parser("paste"); p.add_argument("--run", required=True); p.add_argument("--from", required=True); p.add_argument("--name", required=True); p.add_argument("--origin", default=""); p.add_argument("--oa", default="")
    e = sub.add_parser("excerpt"); e.add_argument("--run", required=True); e.add_argument("--window", type=int, default=WINDOW)
    e.add_argument("--redo", action="store_true", help="re-derive every excerpt from scratch even if the ledger spans are unchanged")
    s = sub.add_parser("status"); s.add_argument("--run", required=True)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.cmd:
        ap.print_help()
        return 2
    return {"fetch": cmd_fetch, "local": cmd_local, "paste": cmd_paste, "excerpt": cmd_excerpt, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
