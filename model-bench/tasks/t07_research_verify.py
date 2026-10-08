"""T07 — verify 5 claims against 4 local documents with citations. Dispatch row: 'Research / multi-source verification' (mid, high)."""
import json
from _common import parse_json, verdict, write

ID = "t07_research_verify"
CATEGORY = "multi-source-verification"
DISPATCH_ROW = "Research / multi-source verification"
EXPECTED_TIER = "mid"
TOOLS = "default"
MAX_TURNS = 12
TIMEOUT_S = 600

DOCS = {
    "docs/spec-v2.md": """\
# Lumen Sync — Specification v2 (2026-04-02)

Lumen Sync v2 supports a maximum of 250 concurrent clients per node.
The default conflict strategy is last-writer-wins.
Transport is TLS 1.3 only; TLS 1.2 is rejected at the handshake.
Snapshots are retained for 30 days.
""",
    "docs/release-notes.md": """\
# Release notes

## 2.1.0 — 2026-06-15
- Raised the per-node client ceiling from 250 to 400 concurrent clients.
- Snapshot retention is unchanged at 30 days.

## 2.0.0 — 2026-04-02
- Initial v2 line. Last-writer-wins conflict strategy.
""",
    "docs/faq.md": """\
# FAQ

**Which TLS versions are accepted?** TLS 1.3 only. Older clients must upgrade.

**Is Lumen Sync open source?** The server is proprietary; the client SDK is published
under the MIT license.

**How long are snapshots kept?** Thirty days by default; enterprise plans can extend this.
""",
    "docs/blog-2026-07.md": """\
# Field report, July 2026

We ran a 400-client soak test on a single node for 72 hours. No dropped sessions.
Someone asked about running without TLS for lab use — not possible, the handshake
requires TLS 1.3.
""",
}

CLAIMS = [
    ("C1", "A single Lumen Sync node supports at most 250 concurrent clients."),
    ("C2", "Lumen Sync accepts TLS 1.2 connections."),
    ("C3", "Snapshots are retained for 30 days by default."),
    ("C4", "The Lumen Sync server is open source."),
    ("C5", "Lumen Sync supports a merge-based conflict strategy with three-way diff."),
]
GOLD = {"C1": "CONTRADICTED", "C2": "CONTRADICTED", "C3": "SUPPORTED", "C4": "CONTRADICTED", "C5": "INSUFFICIENT"}

PROMPT = """The directory `docs/` holds four documents about a product. Verify each claim below
USING ONLY those documents. Verdict rules (apply exactly):
- SUPPORTED: at least one document states it and no document contradicts it.
- CONTRADICTED: at least one document states something incompatible with the claim as written
  (a newer document superseding an older value counts as contradicting the older value).
- INSUFFICIENT: no document addresses the claim.
Output ONLY a JSON array with one element per claim, in the given order:
{"claim_id": "...", "verdict": "SUPPORTED|CONTRADICTED|INSUFFICIENT",
 "sources": [{"doc": "docs/<file>", "quote": "<a verbatim sentence or line from that document>"}]}
`sources` must be non-empty for SUPPORTED and CONTRADICTED, and may be [] for INSUFFICIENT.
No prose, no code fences.

Claims:
""" + "\n".join(f"{cid}: {text}" for cid, text in CLAIMS)


def setup(workdir):
    for rel, c in DOCS.items():
        write(workdir, rel, c)


def _norm(s):
    """Whitespace-insensitive: the fixture markdown is hard-wrapped, and a model that joins
    a wrapped sentence with a space has still quoted it verbatim (first live round: both
    haiku runs were failed on exactly this, with the right verdict and the right sentence)."""
    return " ".join(str(s).split())


def check(result, workdir):
    try:
        got = parse_json(result)
    except ValueError:
        return verdict(False, "output is not JSON")
    if not isinstance(got, list) or len(got) != len(CLAIMS):
        return verdict(False, f"expected {len(CLAIMS)} elements")
    wrong, badcite = [], []
    for el in got:
        cid = el.get("claim_id")
        if cid not in GOLD:
            return verdict(False, f"unknown claim_id {cid!r}")
        if el.get("verdict") != GOLD[cid]:
            wrong.append(f"{cid}:{el.get('verdict')}")
        srcs = el.get("sources") or []
        if GOLD[cid] != "INSUFFICIENT" and not srcs:
            badcite.append(f"{cid}: no source")
        for s in srcs:
            doc = str(s.get("doc", "")).lstrip("./")
            q = str(s.get("quote", "")).strip()
            body = DOCS.get(doc)
            if body is None or not q or _norm(q) not in _norm(body):
                badcite.append(f"{cid}: quote not found in {doc or '?'}")
    if wrong or badcite:
        return verdict(False, f"verdicts wrong: {wrong or 'none'}; citation problems: {badcite[:2] or 'none'}",
                       score=(len(CLAIMS) - len(wrong)) / len(CLAIMS) * (0.5 if badcite else 1.0))
    return verdict(True, "5/5 verdicts correct, every citation verbatim in its named document")


def _ok():
    return [
        {"claim_id": "C1", "verdict": "CONTRADICTED", "sources": [{"doc": "docs/release-notes.md", "quote": "- Raised the per-node client ceiling from 250 to 400 concurrent clients."}]},
        {"claim_id": "C2", "verdict": "CONTRADICTED", "sources": [{"doc": "docs/spec-v2.md", "quote": "Transport is TLS 1.3 only; TLS 1.2 is rejected at the handshake."}]},
        {"claim_id": "C3", "verdict": "SUPPORTED", "sources": [{"doc": "docs/spec-v2.md", "quote": "Snapshots are retained for 30 days."}]},
        {"claim_id": "C4", "verdict": "CONTRADICTED", "sources": [{"doc": "docs/faq.md", "quote": "The server is proprietary; the client SDK is published"}]},
        {"claim_id": "C5", "verdict": "INSUFFICIENT", "sources": []},
    ]


_bad_verdict = _ok(); _bad_verdict[0]["verdict"] = "SUPPORTED"
_bad_quote = _ok(); _bad_quote[2]["sources"][0]["quote"] = "Snapshots are kept for thirty days."
_wrapped = _ok(); _wrapped[3]["sources"][0]["quote"] = "The server is proprietary; the client SDK is published under the MIT license."
CONTROLS = [
    {"result": json.dumps(_ok()), "expect": True},
    {"result": json.dumps(_wrapped), "expect": True},  # joined a hard-wrapped line: still verbatim
    {"result": json.dumps(_bad_verdict), "expect": False},
    {"result": json.dumps(_bad_quote), "expect": False},
]
