#!/usr/bin/env python3
"""psearch.py — federated search over EXTERNAL platforms (code, model hubs,
practitioner communities). Sibling of tools/recall/recall.py and built on its
leg contract: one adapter per platform, `(query, k) -> list[item]`, which may
`raise LegUnavailable(reason)`; legs run in parallel; output is one block per
leg (recall card 16: disjoint corpora are never fused into one score).

Scope: LEADS, not evidence. Scholarly sources (papers, preprints, citation
graphs) are owned by skills/literature-search-extract and have no leg here.
Each leg's route, auth and robots/ToS status come from
ops/references/platform-source-registry.json; the block header prints that
status so a `gray` source is visible as such. An unavailable leg means the
platform could not be ASKED, never that nobody discussed the topic.

Usage:
    psearch.py query "<2-4 keywords>" [--per-leg 5] [--legs github,reddit,...] [--subs a+b] [--json]
        [--wide]          # user asked for as broad a search as possible: + qiita + agy, >=8 per leg
        [--no-fallback]   # by default a refused reddit leg is retried through agy
    psearch.py reddit-thread <thread-url> [--k 15]     # post + top comments via RSS
    psearch.py civitai-hash <model-file>               # where did this local model come from
    psearch.py legs                                    # registry status + quota state

Volume (user ruling 2026-10-04: Reddit RSS allowed at low, user-initiated
volume): every request goes through `_throttle`, which enforces a per-host
minimum spacing and daily cap persisted in state/hosts.json, and stops on a
429 instead of retrying. No scheduled or bulk use.

Extension point: write `leg_<name>(query, k)`, add it to ALL_LEGS (+ DEFAULT
if it should run without --legs) and map it to its registry id in LEG_REGISTRY.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import hashlib
import html
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "ops" / "references" / "platform-source-registry.json"
STATE = pathlib.Path(__file__).resolve().parent / "state" / "hosts.json"
UA = "windows:platform-search:0.1 (personal research tool; low volume)"
TIMEOUT = 20
ATOM = {"a": "http://www.w3.org/2005/Atom"}

# host -> (min seconds between requests, max requests per local day)
HOST_POLICY = {
    "www.reddit.com": (3.0, 60),
    "api.stackexchange.com": (1.0, 250),   # anonymous quota is 300/day per IP
    "qiita.com": (2.0, 50),                # anonymous 60/hour
    "civitai.com": (2.0, 40),              # robots disallows /api/* -> keep it small
}
DEFAULT_POLICY = (1.0, 500)


class LegUnavailable(Exception):
    """The platform could not be asked for this query."""


# --------------------------------------------------------------------------
# Throttle + HTTP
# --------------------------------------------------------------------------

def _load_state() -> dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")


def _throttle(host: str) -> None:
    """Spacing + daily cap per host. Read-modify-write without a lock: legs in
    one run hit different hosts, and a lost count between two concurrent runs
    errs by one request, not by a burst."""
    spacing, cap = HOST_POLICY.get(host, DEFAULT_POLICY)
    state = _load_state()
    today = _dt.date.today().isoformat()
    h = state.get(host, {})
    if h.get("day") != today:
        h = {"day": today, "count": 0, "last": 0.0}
    if h["count"] >= cap:
        raise LegUnavailable(f"daily cap {cap} reached for {host} (state/hosts.json)")
    if h.get("blocked_until", 0) > time.time():
        raise LegUnavailable(f"{host} rate-limited until {time.strftime('%H:%M:%S', time.localtime(h['blocked_until']))}")
    wait = h["last"] + spacing - time.time()
    if wait > 0:
        time.sleep(wait)
    h["last"] = time.time()
    h["count"] += 1
    state[host] = h
    _save_state(state)


def _mark_blocked(host: str, seconds: float) -> None:
    state = _load_state()
    state.setdefault(host, {})["blocked_until"] = time.time() + max(seconds, 30)
    _save_state(state)


def fetch(url: str) -> tuple[bytes, dict]:
    host = urllib.parse.urlsplit(url).hostname or ""
    _throttle(host)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read()
            headers = {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as e:
        if e.code == 429:
            reset = float(e.headers.get("x-ratelimit-reset") or e.headers.get("retry-after") or 60)
            _mark_blocked(host, reset)
            raise LegUnavailable(f"HTTP 429 from {host}; backing off {int(reset)}s")
        raise LegUnavailable(f"HTTP {e.code} from {host}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise LegUnavailable(f"network error: {e}")
    # Stop BEFORE the 429: a 200 that reports an exhausted window blocks the
    # host until its reset (Reddit's anonymous RSS window is a few requests).
    remaining = headers.get("x-ratelimit-remaining")
    if remaining is not None:
        try:
            if float(remaining) < 1:
                _mark_blocked(host, float(headers.get("x-ratelimit-reset") or 60))
        except ValueError:
            pass
    if headers.get("content-encoding") == "gzip" or body[:2] == b"\x1f\x8b":
        body = gzip.decompress(body)
    return body, headers


def fetch_json(url: str):
    body, headers = fetch(url)
    try:
        return json.loads(body), headers
    except ValueError:
        raise LegUnavailable(f"non-JSON answer ({_blocked_hint(body)})")


def _blocked_hint(body: bytes) -> str:
    text = body[:4000].decode("utf-8", "replace").lower()
    if "blocked by network security" in text:
        return "blocked by network security page"
    if "challenge" in text or "cf-chl" in text or "請稍候" in text:
        return "bot challenge page"
    return "unexpected body"


def _snip(text: str, n: int = 200) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    return re.sub(r"\s+", " ", text).strip()[:n]


def _item(title: str, where: str, snippet: str = "", meta: str = "") -> dict:
    return {"title": _snip(title, 160), "where": where, "snippet": _snip(snippet), "meta": meta}


# --------------------------------------------------------------------------
# Parsers — pure functions, exercised offline by controls.py
# --------------------------------------------------------------------------

def _atom_root(body: bytes) -> ET.Element:
    """Parse and REQUIRE an Atom <feed> root. A well-formed HTML page (block or
    challenge) parses as XML too and would otherwise read as zero entries --
    a refused route mistaken for 'no discussion' (caught by controls.py)."""
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        raise LegUnavailable(f"not an Atom feed ({_blocked_hint(body)})")
    if root.tag != "{http://www.w3.org/2005/Atom}feed":
        raise LegUnavailable(f"not an Atom feed: root <{root.tag}> ({_blocked_hint(body)})")
    return root


def parse_reddit_atom(body: bytes) -> list[dict]:
    """Search or listing RSS -> items. A non-Atom body (block page) raises."""
    root = _atom_root(body)
    out = []
    for e in root.findall("a:entry", ATOM):
        link = e.find("a:link", ATOM)
        cat = e.find("a:category", ATOM)
        out.append(_item(
            e.findtext("a:title", "", ATOM),
            link.get("href", "") if link is not None else "",
            e.findtext("a:content", "", ATOM),
            " ".join(x for x in ((cat.get("label") if cat is not None else ""),
                                 (e.findtext("a:updated", "", ATOM) or e.findtext("a:published", "", ATOM))[:10]) if x),
        ))
    return out


def parse_reddit_thread(body: bytes) -> list[dict]:
    """Thread RSS -> [post, comment, ...] with author and full-ish text."""
    root = _atom_root(body)
    out = []
    for e in root.findall("a:entry", ATOM):
        link = e.find("a:link", ATOM)
        out.append({
            "author": e.findtext("a:author/a:name", "", ATOM),
            "date": (e.findtext("a:updated", "", ATOM) or "")[:10],
            "title": e.findtext("a:title", "", ATOM),
            "where": link.get("href", "") if link is not None else "",
            "text": _snip(e.findtext("a:content", "", ATOM), 700),
        })
    return out


def parse_hn(data: dict) -> list[dict]:
    return [_item(h.get("title") or "", f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                  h.get("url") or "", f"{h.get('points', 0)} pts, {h.get('num_comments', 0)} comments, {(h.get('created_at') or '')[:10]}")
            for h in data.get("hits", [])]


def parse_se(data: dict, site: str) -> list[dict]:
    return [_item(q.get("title", ""), q.get("link", ""), " ".join(q.get("tags", [])),
                  f"{site} score {q.get('score', 0)}, {q.get('answer_count', 0)} answers"
                  f"{' (accepted)' if q.get('accepted_answer_id') else ''}, "
                  f"{_dt.datetime.fromtimestamp(q.get('last_activity_date', 0), _dt.timezone.utc).date()}")
            for q in data.get("items", [])]


def parse_discourse(data: dict, host: str) -> list[dict]:
    blurbs = {}
    for p in data.get("posts", []):
        blurbs.setdefault(p.get("topic_id"), p.get("blurb", ""))
    return [_item(t.get("title", ""), f"https://{host}/t/{t.get('slug', '')}/{t.get('id')}",
                  blurbs.get(t.get("id"), ""), f"{host.split('.')[1]} {t.get('posts_count', '?')} posts, {(t.get('created_at') or '')[:10]}")
            for t in data.get("topics", [])]


def parse_hf(data: list) -> list[dict]:
    return [_item(m.get("id", ""), f"https://huggingface.co/{m.get('id', '')}", m.get("pipeline_tag") or "",
                  f"{m.get('downloads', 0)} dl, {m.get('likes', 0)} likes, {(m.get('lastModified') or m.get('createdAt') or '')[:10]}")
            for m in data]


def parse_civitai(data: dict) -> list[dict]:
    out = []
    for m in data.get("items", []):
        v = (m.get("modelVersions") or [{}])[0]
        out.append(_item(m.get("name", ""), f"https://civitai.com/models/{m.get('id')}", m.get("type", ""),
                         f"{m.get('type', '')} base {v.get('baseModel', '?')}, {(m.get('stats') or {}).get('downloadCount', 0)} dl"))
    return out


def parse_agy(text: str) -> list[dict]:
    """agy answer -> items. No JSON list = undetermined (raised, never a zero);
    a non-object row or a row without an http URL is excluded, not guessed."""
    text = text or ""
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end <= start:
        raise LegUnavailable("agy answer held no JSON list (undetermined, not zero)")
    try:
        rows = json.loads(text[start:end + 1])
    except ValueError:
        raise LegUnavailable("agy JSON list did not parse (undetermined, not zero)")
    out = []
    for r in rows if isinstance(rows, list) else []:
        if not isinstance(r, dict) or not str(r.get("url", "")).startswith("http"):
            continue
        out.append(_item(str(r.get("title", "")), str(r["url"]), str(r.get("tip", "")),
                         f"agy-reported, unverified: {r.get('platform', '')} {r.get('date', '')}".strip()))
    return out


def parse_qiita(data: list) -> list[dict]:
    return [_item(a.get("title", ""), a.get("url", ""), " ".join(t.get("name", "") for t in a.get("tags", [])),
                  f"{a.get('likes_count', 0)} likes, {(a.get('updated_at') or '')[:10]}")
            for a in data]


# --------------------------------------------------------------------------
# Legs
# --------------------------------------------------------------------------

def _q(s: str) -> str:
    return urllib.parse.quote(s)


def _gh(args: list[str]) -> list[dict]:
    try:
        p = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise LegUnavailable(f"gh failed: {e}")
    if p.returncode != 0:
        raise LegUnavailable(f"gh exit {p.returncode}: {p.stderr.strip()[:160]}")
    return json.loads(p.stdout or "[]")


def leg_github(query: str, k: int) -> list[dict]:
    rows = _gh(["search", "repos", query, "--limit", str(k), "--sort", "stars",
                "--json", "fullName,description,url,stargazersCount,updatedAt"])
    return [_item(r["fullName"], r["url"], r.get("description") or "",
                  f"{r.get('stargazersCount', 0)} stars, updated {(r.get('updatedAt') or '')[:10]}") for r in rows]


def leg_gh_issues(query: str, k: int) -> list[dict]:
    rows = _gh(["search", "issues", query, "--limit", str(k), "--sort", "comments",
                "--json", "title,url,repository,updatedAt,commentsCount,state"])
    return [_item(r["title"], r["url"], "",
                  f"{(r.get('repository') or {}).get('nameWithOwner', '')} {r.get('state', '')}, "
                  f"{r.get('commentsCount', 0)} comments, {(r.get('updatedAt') or '')[:10]}") for r in rows]


SUBS: str | None = None  # set from --subs


def leg_reddit(query: str, k: int) -> list[dict]:
    base = f"https://www.reddit.com/r/{SUBS}/search.rss" if SUBS else "https://www.reddit.com/search.rss"
    extra = "&restrict_sr=1" if SUBS else ""
    body, _ = fetch(f"{base}?q={_q(query)}&sort=relevance&t=all&limit={k + 3}{extra}")
    # site-wide search also returns matching SUBREDDITS; keep threads only
    return [it for it in parse_reddit_atom(body) if "/comments/" in it["where"]][:k]


def leg_hn(query: str, k: int) -> list[dict]:
    data, _ = fetch_json(f"https://hn.algolia.com/api/v1/search?query={_q(query)}&tags=story&hitsPerPage={k}")
    return parse_hn(data)


SE_SITES = ["stackoverflow"]  # set from --se-sites


def leg_se(query: str, k: int) -> list[dict]:
    out = []
    for site in SE_SITES:
        data, _ = fetch_json(f"https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance"
                             f"&q={_q(query)}&site={site}&pagesize={k}")
        out += parse_se(data, site)
    return out[: k * len(SE_SITES)]


DISCOURSE_HOSTS = ["discuss.huggingface.co", "discuss.pytorch.org"]


def leg_discourse(query: str, k: int) -> list[dict]:
    out, errors = [], []
    for host in DISCOURSE_HOSTS:
        try:
            data, _ = fetch_json(f"https://{host}/search.json?q={_q(query)}")
            out += parse_discourse(data, host)[:k]
        except LegUnavailable as e:
            errors.append(f"{host}: {e}")
    if errors and not out:
        raise LegUnavailable("; ".join(errors))
    return out


def leg_hf(query: str, k: int) -> list[dict]:
    data, _ = fetch_json(f"https://huggingface.co/api/models?search={_q(query)}&sort=downloads&limit={k}")
    return parse_hf(data)


def leg_civitai(query: str, k: int) -> list[dict]:
    data, _ = fetch_json(f"https://civitai.com/api/v1/models?query={_q(query)}&limit={k}&nsfw=false")
    return parse_civitai(data)


def leg_qiita(query: str, k: int) -> list[dict]:
    data, _ = fetch_json(f"https://qiita.com/api/v2/items?query={_q(query)}&per_page={k}")
    return parse_qiita(data)


EXTDISPATCH = ROOT / "tools" / "extdispatch" / "extdispatch.py"
# SHARE EDITION: the source pointed this at a worker directory on a non-system
# drive. The agy leg needs tools/extdispatch/ (not shipped); without it the
# subprocess below fails and the leg reports itself unavailable.
AGY_DIR = str(ROOT / "tools" / "extdispatch" / "agy-cwd")  # must be on extdispatch's allowlist
# Must exceed extdispatch's WHOLE query chain (2 models x (300 s budget + 30 s
# kill grace)) so extdispatch always ends its own run: killing it earlier leaves
# its slot lock (30 min stale window) and an orphaned agy.exe behind -- measured
# 2026-10-04, three slots jammed by a 330 s value. Typical run is ~50 s.
AGY_TIMEOUT = 2 * (300 + 30) + 60
AGY_FORMAT = (
    " Use ONLY the web search tool -- do not open a browser, fetch pages or run any other tool "
    "(agy on Windows hangs on a tool approval nobody can give)."
    " Answer ONLY with a JSON array, no prose: [{\"title\": ..., \"url\": exact page URL, "
    "\"platform\": ..., \"date\": \"YYYY-MM-DD\" or \"\", \"tip\": one concrete point from the page}]. "
    "Never invent a URL; omit an item you cannot give a real URL for."
)


def _agy(prompt: str) -> list[dict]:
    """One extdispatch `query` run (Gemini with Google Search grounding). Google
    licenses Reddit data, so this reaches threads our own requests cannot.
    Costs one of the day's agy dispatches and ~1-3 min."""
    py = [sys.executable, "-X", "utf8", str(EXTDISPATCH)]
    try:
        g = subprocess.run([*py, "grant", "--dir", AGY_DIR, "--profile", "query", "--uses", "1",
                            "--ttl-min", "10", "--issuer", "agent", "--token-only"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        if g.returncode != 0:
            raise LegUnavailable(f"agy grant refused: {g.stderr.strip()[:160]}")
        r = subprocess.run([*py, "run", "--profile", "query", "--dir", AGY_DIR, "--grant", g.stdout.strip(),
                            "--prompt", prompt + AGY_FORMAT],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=AGY_TIMEOUT,
                           stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise LegUnavailable(f"agy failed: {e}")
    if r.returncode != 0:
        raise LegUnavailable(f"agy exit {r.returncode}: {(r.stderr or r.stdout).strip()[-160:]}")
    return parse_agy(r.stdout)


def leg_agy(query: str, k: int) -> list[dict]:
    return _agy(f"Using web search, find up to {k} of the most useful pages where practitioners discuss: "
                f"{query}. Prefer Reddit, Hacker News, GitHub issues/discussions, Stack Exchange, Hugging Face "
                f"and vendor forums, plus non-English communities (Qiita, Zenn, V2EX) when relevant; "
                f"no academic papers.")[:k]


def leg_agy_reddit(query: str, k: int) -> list[dict]:
    subs = f" in r/{SUBS.replace('+', ', r/')}" if SUBS else ""
    return _agy(f"Using web search, find up to {k} Reddit threads{subs} (reddit.com/r/.../comments/... URLs) "
                f"discussing: {query}.")[:k]


ALL_LEGS = {
    "github": leg_github, "gh_issues": leg_gh_issues, "hf": leg_hf, "reddit": leg_reddit,
    "hn": leg_hn, "se": leg_se, "discourse": leg_discourse, "civitai": leg_civitai, "qiita": leg_qiita,
    "agy": leg_agy,
}
# civitai is ComfyUI-asset scope only; qiita is Japanese; agy is slow and metered -- all opt-in.
DEFAULT = ["github", "gh_issues", "hf", "reddit", "hn", "se", "discourse"]
# --wide: the user asked for as broad a search as possible (「盡可能更多搜尋」).
WIDE = DEFAULT + ["qiita", "agy"]
WIDE_MIN_PER_LEG = 8
LEG_REGISTRY = {
    "github": "github", "gh_issues": "github", "hf": "huggingface", "reddit": "reddit", "hn": "hackernews",
    "se": "stackexchange", "discourse": "discourse-forums", "civitai": "civitai", "qiita": "qiita",
    "agy": "agy-grounded",
}


def registry_status() -> dict[str, str]:
    try:
        rows = json.loads(REGISTRY.read_text(encoding="utf-8"))["platforms"]
    except (OSError, ValueError, KeyError):
        return {}
    return {r["id"]: r.get("status", "?") for r in rows}


def _call(name: str, query: str, k: int):
    try:
        return ALL_LEGS[name](query, k)
    except LegUnavailable as e:
        return e
    except Exception as e:  # noqa: BLE001 -- any leg failure is "unavailable", never a crash
        return LegUnavailable(f"{type(e).__name__}: {e}")


RELAX_WORDS = 3


def relax_query(query: str) -> str | None:
    """First RELAX_WORDS words, or None when the query is already that short."""
    words = query.split()
    return " ".join(words[:RELAX_WORDS]) if len(words) > RELAX_WORDS else None


def run_query(query: str, per_leg: int, legs: list[str], fallback: bool = True) -> dict:
    raw = {}
    with ThreadPoolExecutor(max_workers=len(legs)) as pool:
        futs = {pool.submit(_call, n, query, per_leg): n for n in legs}
        for f in as_completed(futs):
            raw[futs[f]] = f.result()
    blocks = build_blocks(raw, legs, registry_status())
    # Keyword APIs AND-match every word, so an agent's sentence-long query
    # returns a real but useless zero. Retry those once on the first
    # RELAX_WORDS words (the caller's own leading terms) and say so.
    relaxed = relax_query(query)
    if relaxed:
        zero = [n for n in legs if n != "agy" and blocks[n]["status"] == "available(0)"]
        if zero:
            with ThreadPoolExecutor(max_workers=len(zero)) as pool:
                futs = {pool.submit(_call, n, relaxed, per_leg): n for n in zero}
                for f in as_completed(futs):
                    n, r = futs[f], f.result()
                    if isinstance(r, list) and r:
                        blocks[n]["status"] = f"available({len(r)}) on relaxed query '{relaxed}' (full query: 0)"
                        blocks[n]["items"] = r
    # Reddit fallback: our own requests were refused/limited -> ask agy, whose
    # search engine is licensed to index Reddit. Skipped when agy already ran
    # (--wide), since its answer already covers Reddit.
    if fallback and "reddit" in legs and "agy" not in legs and isinstance(raw.get("reddit"), LegUnavailable):
        try:
            items = leg_agy_reddit(query, per_leg)
            blocks["reddit"] = {"registry": blocks["reddit"]["registry"],
                                "status": f"available({len(items)}) via agy fallback; direct: {raw['reddit']}",
                                "items": items}
        except LegUnavailable as e:
            blocks["reddit"]["status"] += f"; agy fallback also unavailable({e})"
    return blocks


def build_blocks(raw: dict, legs: list[str], status: dict[str, str]) -> dict:
    """Pure: leg results -> blocks. A result that is neither list[item] nor
    LegUnavailable is `undetermined` and excluded (recall AP-62), never
    iterated as items."""
    blocks = {}
    for n in legs:
        r = raw[n]
        reg = status.get(LEG_REGISTRY.get(n, ""), "unregistered")
        if isinstance(r, LegUnavailable):
            blocks[n] = {"registry": reg, "status": f"unavailable({r})", "items": []}
        elif not isinstance(r, list):
            blocks[n] = {"registry": reg, "status": f"undetermined(non-list leg result: {type(r).__name__})", "items": []}
        else:
            blocks[n] = {"registry": reg, "status": f"available({len(r)})", "items": r}
    return blocks


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def cmd_query(a) -> int:
    global SUBS, SE_SITES
    SUBS = a.subs
    if a.se_sites:
        SE_SITES = a.se_sites.split(",")
    legs = a.legs.split(",") if a.legs else (WIDE if a.wide else DEFAULT)
    per_leg = max(a.per_leg, WIDE_MIN_PER_LEG) if a.wide else a.per_leg
    bad = [x for x in legs if x not in ALL_LEGS]
    if bad:
        print(f"unknown leg(s): {bad}; known: {sorted(ALL_LEGS)}", file=sys.stderr)
        return 2
    blocks = run_query(a.text, per_leg, legs, fallback=not a.no_fallback)
    if a.json:
        print(json.dumps({"query": a.text, "blocks": blocks}, ensure_ascii=False, indent=1))
    else:
        for n, b in blocks.items():
            print(f"{n} [{b['registry']}]: {b['status']}")
            for i, it in enumerate(b["items"], 1):
                print(f"  {i}. {it['title']}  ->  {it['where']}")
                if it["meta"]:
                    print(f"      {it['meta']}")
                if a.verbose and it["snippet"]:
                    print(f"      {it['snippet']}")
        print("note: an unavailable leg was not ASKED -- its silence is not absence of discussion. "
              "Leads only; scholarly evidence -> literature-search-extract.")
    ok = sum(1 for b in blocks.values() if b["status"].startswith("available"))
    if ok == 0:
        print("ERROR: zero available legs", file=sys.stderr)
        return 2
    return 0


def cmd_reddit_thread(a) -> int:
    url = a.url.split("?")[0].rstrip("/")
    if "/comments/" not in url:
        print("expected a thread URL containing /comments/", file=sys.stderr)
        return 2
    try:
        body, _ = fetch(f"{url}/.rss?limit={a.k}")
        entries = parse_reddit_thread(body)
    except LegUnavailable as e:
        print(f"unavailable: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(entries, ensure_ascii=False, indent=1))
        return 0
    for i, e in enumerate(entries):
        tag = "POST" if i == 0 else f"c{i}"
        print(f"[{tag}] {e['author']} {e['date']}  {e['title'] if i == 0 else ''}".rstrip())
        print(f"   {e['text']}")
    return 0


def cmd_civitai_hash(a) -> int:
    p = pathlib.Path(a.file)
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    digest = h.hexdigest()
    try:
        d, _ = fetch_json(f"https://civitai.com/api/v1/model-versions/by-hash/{digest}")
    except LegUnavailable as e:
        print(f"{p.name}: sha256 {digest[:16]}... -> {e} (404 = not on Civitai, or removed)")
        return 1
    m = d.get("model") or {}
    print(f"{p.name}: {m.get('name')} | version {d.get('name')} | {m.get('type')} | base {d.get('baseModel')}"
          f" | https://civitai.com/models/{d.get('modelId')}?modelVersionId={d.get('id')}")
    words = d.get("trainedWords") or []
    if words:
        print(f"  trigger words: {', '.join(words[:10])}")
    return 0


def cmd_legs(_a) -> int:
    status = registry_status()
    state = _load_state()
    today = _dt.date.today().isoformat()
    for n in ALL_LEGS:
        flag = "default" if n in DEFAULT else "opt-in"
        print(f"{n:10s} {flag:8s} registry={status.get(LEG_REGISTRY[n], 'unregistered')}")
    for host, (sp, cap) in HOST_POLICY.items():
        h = state.get(host, {})
        used = h.get("count", 0) if h.get("day") == today else 0
        print(f"  quota {host}: {used}/{cap} today, spacing {sp}s")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="psearch.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("query")
    q.add_argument("text")
    q.add_argument("--per-leg", type=int, default=5)
    q.add_argument("--legs", default=None, help=f"comma list; default {','.join(DEFAULT)}")
    q.add_argument("--subs", default=None, help="restrict reddit to subs, e.g. LocalLLaMA+comfyui")
    q.add_argument("--se-sites", default=None, help="e.g. stackoverflow,physics,electronics")
    q.add_argument("--wide", action="store_true",
                   help=f"broadest search (user says 「盡可能更多搜尋」): legs {','.join(WIDE)}, "
                        f">= {WIDE_MIN_PER_LEG} per leg; agy adds ~1-3 min")
    q.add_argument("--no-fallback", action="store_true", help="do not ask agy when reddit is refused")
    q.add_argument("--json", action="store_true")
    q.add_argument("-v", "--verbose", action="store_true")
    t = sub.add_parser("reddit-thread")
    t.add_argument("url")
    t.add_argument("--k", type=int, default=15)
    t.add_argument("--json", action="store_true")
    c = sub.add_parser("civitai-hash")
    c.add_argument("file")
    sub.add_parser("legs")
    return p


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    return {"query": cmd_query, "reddit-thread": cmd_reddit_thread,
            "civitai-hash": cmd_civitai_hash, "legs": cmd_legs}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
