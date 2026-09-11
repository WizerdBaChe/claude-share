#!/usr/bin/env python3
r"""access_policy — the skill's read-only view of hooks/literature-host-policy.json.

WHY. `rules/literature-access.md` (2026-09-10) says which surface an agent may use on
which host and that an anti-bot challenge is a routing signal, never an obstacle. Until
this file, that was prose the executor had to remember — and the skill's own
search-sources.md still told it to render "anti-bot" pages with a headless browser.
This module turns the routing table into ONE function every retrieval path consults
BEFORE it fetches: `decide(host, surface)`.

WHERE THE POLICY LIVES. `~/.claude/hooks/literature-host-policy.json` — rule tier, so
that the machine-wide hook (`hooks/literature_host_guard.py`) and this skill read the
same rows. The skill never writes it; editing a row is a reviewed act by the user.

WHAT THIS RULES ON, and only this:
  * the host's row (exact or suffix match), or the file's `unlisted_default`;
  * whether `surface` is in the row's `agent_surfaces`;
  * a per-run count, when the caller passes one (max_per_run / distinct unlisted cap).
It does not know whether a page is paywalled, whether the user is entitled, or whether
a challenge will fire — those are outcomes fetchsrc.py records after the fact.

FAIL-CLOSED WITHOUT THE FILE. If the policy is missing or unreadable, `decide` refuses
every browser surface everywhere and allows script/webfetch only on OPEN_CORE (public
scholarly APIs). A missing file must never read as "everything allowed".

Usage:
    python access_policy.py --host ieeexplore.ieee.org [--surface webfetch]
    python access_policy.py --url https://link.springer.com/article/10.1007/x --surface browser_headless --check
    python access_policy.py --selftest
Exit: 0 allowed / usage ok · 1 refused (with --check) · 2 bad usage · 3 policy unreadable.
review-when: the policy schema changes ("schema" field) or a new surface name appears.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit

SURFACES = ("script", "webfetch", "browser_headless", "browser_user")
NON_AGENT_ROUTES = ("local_pdf", "user_provided", "hand_to_user")   # not surfaces: never judged here
OPEN_CORE = {"arxiv.org", "export.arxiv.org", "api.crossref.org", "doi.org", "api.semanticscholar.org",
             "eutils.ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov", "pmc.ncbi.nlm.nih.gov",
             "zenodo.org", "ntrs.nasa.gov", "osti.gov"}


def policy_path() -> Path:
    env = os.environ.get("LSE_HOST_POLICY")
    if env:
        return Path(env)
    home = Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))
    return home / "hooks" / "literature-host-policy.json"


def load(path: Path | None = None) -> dict | None:
    p = path or policy_path()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:                                   # noqa: BLE001 — unreadable = absent
        return None
    if not isinstance(data, dict) or not isinstance(data.get("hosts"), list):
        return None
    return data


def canon_host(host: str) -> str:
    """Lower-case, no leading dot, no trailing dot: `ieeexplore.ieee.org.` (the absolute-FQDN form,
    which DNS resolves identically) is the same host as `ieeexplore.ieee.org` (QA 2026-09-11 F-1)."""
    return (host or "").strip().lower().strip(".")


def host_of(url_or_host: str) -> str:
    raw = (url_or_host or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        if "/" in raw or ":" in raw:
            raw = "https://" + raw
        else:
            return canon_host(raw)
    try:
        return canon_host(urlsplit(raw).hostname or "")
    except Exception:                                   # noqa: BLE001
        return ""


def row_for(host: str, policy: dict | None) -> dict:
    """The matching row, or the unlisted default marked `class: unlisted`."""
    host = canon_host(host)
    if policy:
        best = None
        for row in policy["hosts"]:
            listed = canon_host(str(row.get("host", "")))
            if listed and (host == listed or host.endswith("." + listed)):
                if best is None or len(listed) > len(best.get("host", "")):
                    best = row
        if best:
            return dict(best)
        d = dict(policy.get("unlisted_default") or {})
        d.setdefault("class", "unlisted")
        d.setdefault("agent_surfaces", ["script", "webfetch"])
        d.setdefault("max_per_run", 1)
        d.setdefault("retention", "excerpt")
        d["host"] = host
        d["unlisted"] = True
        if host in OPEN_CORE:
            d.update({"class": "open", "agent_surfaces": ["script", "webfetch"], "max_per_run": 100,
                      "retention": "full", "unlisted": False, "note": "OPEN_CORE built-in"})
        return d
    # policy unreadable: fail closed except the built-in public-API core
    if host in OPEN_CORE:
        return {"host": host, "class": "open", "agent_surfaces": ["script", "webfetch"], "max_per_run": 100,
                "retention": "full", "unlisted": False, "policy_unreadable": True}
    return {"host": host, "class": "policy_unreadable", "agent_surfaces": [], "max_per_run": 0,
            "retention": "excerpt", "unlisted": True, "policy_unreadable": True}


def decide(host: str, surface: str, policy: dict | None = None, *, used_on_host: int = 0,
           distinct_unlisted: int = 0) -> tuple[bool, str, dict]:
    """(allowed, reason, row). `surface` may also be a non-agent route, which is allowed by definition."""
    if surface in NON_AGENT_ROUTES:
        return True, f"{surface} is not an agent surface (the user's or the file system's act)", {"host": host, "class": "n/a"}
    if surface not in SURFACES:
        return False, f"unknown surface {surface!r}; known: {', '.join(SURFACES)}", {"host": host, "class": "n/a"}
    if policy is None:
        policy = load()
    row = row_for(host, policy)
    cls = row.get("class")
    if row.get("policy_unreadable") and cls != "open":
        return False, ("policy file unreadable — refusing everything outside the built-in public-API core "
                       f"({policy_path()})"), row
    if cls in ("agent_banned", "institutional_only"):
        return False, (f"{host}: {cls} — {row.get('licence_basis', '')[:160]}. Hand the named document to the "
                       "user (DOI + URL); their reading is licensed, a program's is not"), row
    if surface not in (row.get("agent_surfaces") or []):
        if row.get("unlisted"):
            return False, (f"{host} is not listed in the policy; an unlisted host permits one script/webfetch of a "
                           f"named URL and NO browser surface until a row lists it ({policy_path().name})"), row
        return False, (f"{host}: surface {surface} is not in agent_surfaces {row.get('agent_surfaces')} "
                       f"({row.get('note') or row.get('licence_basis', '')[:120]})"), row
    cap = int(row.get("max_per_run", 0) or 0)
    if used_on_host >= cap:
        return False, (f"{host}: max_per_run {cap} reached ({used_on_host} already this run) — the shape of a run "
                       "that wants more is a bulk download; name the remaining targets for the user"), row
    if row.get("unlisted"):
        run_cap = int((policy or {}).get("unlisted_default", {}).get("run_cap_distinct_unlisted_hosts", 3))
        if distinct_unlisted >= run_cap:
            return False, (f"run-level cap: {run_cap} distinct unlisted hosts already in this run — add rows to "
                           f"{policy_path().name} before touching a {run_cap + 1}th"), row
    return True, f"{host}: {cls} — {surface} permitted for a named document (max_per_run {cap})", row


# ---------------------------------------------------------------- selftest (two-sided)
def selftest() -> int:
    import tempfile
    pol = {"schema": "literature-host-policy@1",
           "unlisted_default": {"class": "unlisted", "agent_surfaces": ["script", "webfetch"], "max_per_run": 1,
                                "retention": "excerpt", "run_cap_distinct_unlisted_hosts": 3},
           "hosts": [
               {"host": "open.example", "class": "open", "agent_surfaces": ["script", "webfetch", "browser_headless"],
                "max_per_run": 5, "retention": "full"},
               {"host": "landing.example", "class": "landing_page", "agent_surfaces": ["webfetch"], "max_per_run": 1,
                "retention": "excerpt"},
               {"host": "banned.example", "class": "agent_banned", "agent_surfaces": [], "max_per_run": 0,
                "retention": "excerpt", "licence_basis": "ToU forbids intelligent agents"},
               {"host": "inst.example", "class": "institutional_only", "agent_surfaces": [], "max_per_run": 0}]}
    cases = [  # (label, host, surface, kwargs, want_allowed)
        ("must-REFUSE banned + browser_user", "banned.example", "browser_user", {}, False),
        ("must-REFUSE banned + webfetch", "banned.example", "webfetch", {}, False),
        ("must-REFUSE banned + script", "banned.example", "script", {}, False),
        ("must-REFUSE institutional_only + webfetch", "inst.example", "webfetch", {}, False),
        ("must-ALLOW open + script", "open.example", "script", {}, True),
        ("must-ALLOW open subdomain + browser_headless", "www.open.example", "browser_headless", {}, True),
        ("must-REFUSE landing + browser_headless (surface not listed)", "landing.example", "browser_headless", {}, False),
        ("must-ALLOW landing + webfetch first document", "landing.example", "webfetch", {"used_on_host": 0}, True),
        ("must-REFUSE landing + webfetch second document (max_per_run 1)", "landing.example", "webfetch", {"used_on_host": 1}, False),
        ("must-ALLOW unlisted + webfetch", "nobody.example", "webfetch", {}, True),
        ("must-REFUSE unlisted + browser_headless", "nobody.example", "browser_headless", {}, False),
        ("must-REFUSE unlisted + browser_user", "nobody.example", "browser_user", {}, False),
        ("must-REFUSE 4th distinct unlisted host", "fourth.example", "webfetch", {"distinct_unlisted": 3}, False),
        ("must-ALLOW non-agent route local_pdf", "banned.example", "local_pdf", {}, True),
        ("must-REFUSE unknown surface", "open.example", "carrier-pigeon", {}, False),
        ("must-REFUSE banned host in absolute-FQDN form (trailing dot; QA F-1)", "banned.example.", "webfetch", {}, False),
        ("must-REFUSE banned host via a URL with a trailing dot", host_of("https://www.banned.example./doc/1"), "webfetch", {}, False),
    ]
    bad = 0
    print(f"{'verdict':9} case")
    print("-" * 72)
    for label, host, surface, kw, want in cases:
        ok_, reason, _ = decide(host, surface, pol, **kw)
        good = ok_ == want
        bad += 0 if good else 1
        print(f"{'ok' if good else 'BROKEN':9} {label}")
        if not good:
            print(f"{'':9}   got allowed={ok_}: {reason[:100]}")
    # policy unreadable: fail closed, except OPEN_CORE script/webfetch
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / "nope.json"
        os.environ["LSE_HOST_POLICY"] = str(missing)
        try:
            a1 = decide("link.springer.com", "webfetch", load())[0]
            a2 = decide("api.crossref.org", "script", load())[0]
            a3 = decide("api.crossref.org", "browser_headless", load())[0]
        finally:
            os.environ.pop("LSE_HOST_POLICY", None)
    for label, got, want in [("must-REFUSE any non-core host when the policy is unreadable", a1, False),
                             ("must-ALLOW OPEN_CORE script when the policy is unreadable", a2, True),
                             ("must-REFUSE OPEN_CORE browser when the policy is unreadable", a3, False)]:
        good = got == want
        bad += 0 if good else 1
        print(f"{'ok' if good else 'BROKEN':9} {label}")
    n = len(cases) + 3
    n_allow = sum(1 for c in cases if c[4]) + 1
    print("-" * 72)
    print(f"{n} cases ({n_allow} must-allow / {n - n_allow} must-refuse), {bad} broken — "
          f"{'calibrated' if not bad else 'NOT TRUSTWORTHY'}")
    # the live file must parse and cover the hosts ops/environment.md measured
    live = load()
    if live is None:
        print(f"WARN live policy unreadable at {policy_path()} — decide() is failing closed")
        return 1 if bad else 0
    listed = {r["host"] for r in live["hosts"]}
    need = {"ieeexplore.ieee.org", "www.sciencedirect.com", "onlinelibrary.wiley.com", "www.mdpi.com",
            "eprints.soton.ac.uk", "opg.optica.org", "iopscience.iop.org", "arxiv.org", "osti.gov"}
    miss = sorted(need - listed)
    print(f"live policy: {len(listed)} rows; measured hosts missing: {miss or 'none'}")
    return 1 if (bad or miss) else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--host")
    ap.add_argument("--url")
    ap.add_argument("--surface", default="webfetch")
    ap.add_argument("--check", action="store_true", help="exit 1 when refused")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    host = host_of(a.url) if a.url else host_of(a.host or "")
    if not host:
        ap.print_help()
        return 2
    pol = load()
    allowed, reason, row = decide(host, a.surface, pol)
    if a.json:
        print(json.dumps({"host": host, "surface": a.surface, "allowed": allowed, "reason": reason, "row": row},
                         ensure_ascii=False, indent=1))
    else:
        print(f"{'ALLOW' if allowed else 'REFUSE'} {host} via {a.surface}: {reason}")
        print(f"  class={row.get('class')} surfaces={row.get('agent_surfaces')} max_per_run={row.get('max_per_run')} "
              f"retention={row.get('retention')} verified={row.get('verified', '-')}")
    if pol is None:
        print(f"  (policy unreadable: {policy_path()})")
        return 3 if a.check else 0
    return (0 if allowed else 1) if a.check else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
