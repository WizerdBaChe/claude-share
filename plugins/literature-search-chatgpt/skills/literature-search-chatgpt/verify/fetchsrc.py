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
    full_sha = sha256_bytes(text.encode("utf-8"))
    entry.update({"sha256_full": full_sha, "bytes": len(text.encode("utf-8")), "chars": len(text),
                  "retention_policy": retention, "fetched_at": now_iso(), "tool": TOOL})
    if retention == "full":
        p = run / "sources" / f"{name}.txt"
        p.write_text(text, encoding="utf-8")
        entry.update({"retention_state": "full", "status": "written", "file": f"sources/{name}.txt",
                      "sha256_file": full_sha})
    else:
        sd = scratch_root() / run.name
        sd.mkdir(parents=True, exist_ok=True)
        sp = sd / f"{name}.txt"
        sp.write_text(text, encoding="utf-8")
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
def norm_with_map(text: str) -> tuple[str, list[int]]:
    """citecheck.norm() with an index map back to the raw string (one raw index per norm char)."""
    out: list[str] = []
    idx: list[int] = []
    i, n = 0, len(text)
    prev_space = True
    while i < n:
        ch = text[i]
        # hyphenation across a line break: "de-\n  vice" -> "device"
        if ch == "-" and i + 1 < n:
            j = i + 1
            while j < n and text[j] in " \t":
                j += 1
            if j < n and text[j] == "\n":
                j += 1
                while j < n and text[j] in " \t\r\n":
                    j += 1
                i = j
                continue
        if ch.isspace():
            if not prev_space:
                out.append(" ")
                idx.append(i)
            prev_space = True
            i += 1
            continue
        prev_space = False
        folded = unicodedata.normalize("NFKC", ch)
        folded = {"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-", "−": "-"}.get(folded, folded)
        for c in folded.casefold():
            out.append(c)
            idx.append(i)
        i += 1
    s = "".join(out).strip()
    if out and out[-1] == " ":
        idx = idx[:len(s)]
    return s, idx


def norm_span(span: str) -> str:
    s, _ = norm_with_map(span)
    return s


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
        p.write_text(text, encoding="utf-8")
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
        "https://open.example/paper": (200, b"<html><body><p>We report a propagation length of 200 um at 780 nm for silver "
                                             b"films.</p><script>x</script></body></html>", "text/html"),
        "https://landing.example/a1": (200, b"<html><p>Abstract: the film shows sub-nanometer roughness of 0.4 nm RMS " +
                                            b"in every sample measured. " * 40 + b"</p></html>", "text/html"),
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
            # 3 landing (excerpt) host: scratch only, no file in the run
            rc = cmd_fetch(A(run=str(run), url="https://landing.example/a1", name="landing", oa=""))
            m = load_manifest(run)
            e = m["entries"].get("landing", {})
            ok("must-NOT write licensed full text into the run folder", rc == 0 and not (run / "sources" / "landing.txt").exists())
            ok("must-KEEP full text in scratch with pending-excerpt state",
               e.get("retention_state") == "pending-excerpt" and Path(e.get("scratch_path", "")).exists())
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
            ok("must-RECORD excerpt state + sha", e.get("retention_state") == "excerpt" and e.get("sha256_file") == sha256_bytes(txt.encode("utf-8")))
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
            # 9 paste: origin unverifiable flagged
            (tmpp / "p.txt").write_text("the user pasted this passage " * 30, encoding="utf-8")
            a = A(run=str(run), name="pasted", oa="", origin="")
            setattr(a, "from", str(tmpp / "p.txt"))
            rc = cmd_paste(a)
            m = load_manifest(run)
            ok("must-MARK paste as user_provided / origin_verifiable false",
               rc == 0 and m["entries"]["pasted"].get("route") == "user_provided" and m["entries"]["pasted"].get("origin_verifiable") is False)
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
