#!/usr/bin/env python
"""afgate — the audience-fit skill's first instrument.

`skills/audience-fit` rules its companions in prose: invent nothing, let the
truth markers survive aggregation, keep the limitations in the main text, drop
the engineering voice. Every other mature skill here carries gates for its
rules; this one carried none, so a companion was accepted on the reader's
patience. Two of those rules are determinable, and this makes them so.

    voice   <companion>              the reader's text carries no builder artifact
    values  <original> <companion>   every number in the companion is accounted
                                     for by the original -- identity or a NAMED
                                     transform; an unaccounted number is invented
    limits  <original> <companion>   inventory of the original's limitation lines
                                     and which have no counterpart (REPORT only)
    all     <original> <companion>   the three above
    --selftest                       two-sided calibration on built fixtures

Borrowed 2026-09-10 from SSLD's audience-pack gates (INV17Gate / ParityGate
and a record-numbers check). ParityGate
proper -- a copy equals its source once the allowed-to-differ fields are blanked
-- does NOT transfer: an audience-fit companion is a REWRITE, not a copy. What
transfers is its question, asked of the parts that must not change.

`values` is a SCREEN, not a proof, and says so in its own output: numbers
carrying 3+ significant digits are the certified set; 1-2 digit tokens are
counting words, thresholds and round figures whose false-accept rate is high,
and that rate is printed rather than hidden.
"""
import argparse
import html
import math
import re
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------- reader text
_SCRIPT = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
_COMMENT = re.compile(r"<!--.*?-->", re.S)
_TAG = re.compile(r"<[^>]+>")
_FENCE = re.compile(r"```.*?```", re.S)
_DATE = re.compile(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b")


def reader_text(path: Path) -> str:
    """What a human actually reads: no markup, no scripts, no code fences.

    An HTML page's class names, ids and data-* attributes are the builder's,
    not the reader's -- scanning them would flag every page ever built.
    """
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in (".html", ".htm", ".svg"):
        raw = _COMMENT.sub(" ", _SCRIPT.sub(" ", raw))
        raw = _TAG.sub(" ", raw)
        raw = html.unescape(raw)
    else:
        raw = _FENCE.sub(" ", raw)
    return raw


# ---------------------------------------------------------------- voice check
# Closed classes: nothing a non-builder reader can act on. FAIL.
CLOSED = [
    ("pass-count", re.compile(r"\b\d+\s*(?:PASS|FAIL|WARN)\b|\b(?:PASS|FAIL)\s*[:：]?\s*\d+\b"),
     "a PASS count is not a credibility signal: it says the instrument ran, "
     "not that the claim is true"),
    ("path", re.compile(r"[A-Za-z]:\\[^\s　]{2,}|(?<![\w.])~?/[\w./-]{3,}\.\w{1,5}\b"
                        r"|\b[\w-]{2,}\.(?:py|mjs|js|ts|json|ya?ml|toml|html|md|pptx|xlsx|csv)\b"),
     "a file path is a builder's address; the reader has no shell"),
    ("sha", re.compile(r"\b[0-9a-f]{8,64}\b"),
     "a hash identifies a build, not a fact the reader can check"),
    ("run-id", re.compile(r"\bRUN\s*=|\brun[-_][0-9a-z]{4,}\b", re.I),
     "a run id belongs in the verify record, never on the reader's page"),
    ("gate-id", re.compile(r"\bINV-?\d+\b|\b[A-Z]{1,3}-\d{2,3}\b|\b[SVGT]\d{1,2}\s+(?:PASS|FAIL|WARN)\b"),
     "gate and invariant ids are the builder's vocabulary"),
]
# Open class: register, not fact. WARN -- a power_user audience legitimately
# reads some of these, so the reader profile decides.
BUILDER_WORDS = ["stdout", "stderr", "traceback", "regex", "schema", "subprocess",
                 "venv", "worktree", "commit", "branch", "repo", "hook", "gate",
                 "exit code", "sha256", "CLI", "stack trace", "閘", "建置腳本"]


# audience-fit MANDATES two builder-addressed regions inside a reader-facing
# companion: the provenance block (canonical link, audience, as-of anchor) and,
# for an A1 re-render, the aggregation mapping table. A path or a sha there is
# addressed to the auditor who must trace the companion back, not to the reader
# -- measured 2026-09-10, when this gate's first run against an ACCEPTED owner
# view (an owner view, user gate PASS 2026-08-31)
# raised 6 FAILs, every one of them inside those two regions.
APPARATUS = re.compile(r"工程正本|聚合對照|前後對照|出處與基準|provenance|canonical original",
                       re.I)


def check_voice(companion: Path, quiet=False, apparatus=APPARATUS):
    text = reader_text(companion)
    # zone split: the delivery apparatus begins at the first line that names it.
    # Content predicate, so the boundary moves with the document; both zone sizes
    # are printed, because a reader paragraph that drifts below the marker would
    # otherwise be exempted silently.
    split = len(text)
    if apparatus:
        for m in apparatus.finditer(text):
            split = text.rfind("\n", 0, m.start()) + 1
            break
    findings = []
    for name, pat, why in CLOSED:
        for m in pat.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            in_apparatus = m.start() >= split
            findings.append(dict(
                verdict="INFO" if in_apparatus else "FAIL", cls=name,
                hit=m.group(0)[:60], line=line,
                why=("delivery apparatus zone — audience-fit mandates the provenance "
                     "block and the 對照 table; this is addressed to the auditor")
                if in_apparatus else why))
    low = text[:split].lower()          # the apparatus zone speaks to the auditor
    for w in BUILDER_WORDS:
        n = low.count(w.lower())
        if n:
            findings.append(dict(verdict="WARN", cls="builder-word", hit=w, line=0,
                                 why=f"appears {n}x in the reader's main text; keep only "
                                     f"if the declared audience is power_user or maintainer"))
    if not quiet:
        _print(companion, findings,
               f"{split} chars of reader main text, {len(text) - split} chars of delivery "
               f"apparatus (provenance + 對照); only the main text can close as FAIL")
    return findings


# --------------------------------------------------------------- value check
_NUM = re.compile(r"(?<![\w.])[-+]?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?")


def numbers(text):
    out = []
    for m in _NUM.finditer(_DATE.sub(" ", text)):
        tok = m.group(0).replace(",", "")
        try:
            out.append((float(tok), m.group(0), text.count("\n", 0, m.start()) + 1))
        except ValueError:
            continue
    return out


def sigdigits(tok: str) -> int:
    d = re.sub(r"[^\d]", "", tok).lstrip("0")
    return len(d.rstrip("0")) if "." not in tok else len(d)


TRANSFORMS = [
    ("identity", lambda o: o),
    ("×100 (成百分比)", lambda o: o * 100),
    ("(x−1)×100 (相對變化百分比)", lambda o: (o - 1) * 100),
    ("(1−x)×100 (相對減少百分比)", lambda o: (1 - o) * 100),
    ("1/x", lambda o: 1 / o if o else None),
    ("×1000 / ÷1000 (單位換算)", lambda o: o * 1000),
    ("÷1000", lambda o: o / 1000),
    ("10·log10 (dB)", lambda o: 10 * math.log10(o) if o > 0 else None),
    ("20·log10 (dB)", lambda o: 20 * math.log10(o) if o > 0 else None),
    ("10^(x/10) (dB→比值)", lambda o: 10 ** (o / 10) if abs(o) < 300 else None),
]


def accounted(c_val, c_tok, pool):
    """Is this companion number explained by an original one? Return the reason."""
    k = max(0, 6 - sigdigits(c_tok))
    for name, f in TRANSFORMS:
        for o_val, o_tok, _ in pool:
            try:
                got = f(o_val)
            except (ValueError, ZeroDivisionError, OverflowError):
                got = None
            if got is None:
                continue
            if got == c_val or (got and abs(got - c_val) <= max(abs(got), abs(c_val)) * 1e-9):
                return f"{name} of {o_tok}"
            # the companion may legitimately round: 33.55 -> "33.6%"
            for places in range(0, 4):
                if round(got, places) == round(c_val, places) and round(got, places) == c_val:
                    return f"{name} of {o_tok}, rounded to {places}dp"
    return None


def check_values(original: Path, companion: Path, allow=None, quiet=False):
    pool = numbers(reader_text(original))
    comp = numbers(reader_text(companion))
    allow = dict(p.split("=", 1) for p in (allow or []))
    findings, certified, uncertified, by_transform = [], 0, 0, 0

    for val, tok, line in comp:
        sd = sigdigits(tok)
        if sd >= 3:
            certified += 1
        else:
            uncertified += 1
            continue                      # 1-2 digits: not certified, see the ruler
        if tok in allow:
            findings.append(dict(verdict="INFO", cls="allowed", hit=tok, line=line,
                                 why=f"ALLOW: {allow[tok]}"))
            continue
        why = accounted(val, tok, pool)
        if why is None:
            findings.append(dict(verdict="FAIL", cls="invented", hit=tok, line=line,
                                 why="no number in the canonical original explains this, "
                                     "under identity or any named transform"))
        elif not why.startswith("identity"):
            by_transform += 1
    ruler = (f"{len(comp)} numbers in the reader's text: {certified} certified "
             f"(3+ significant digits, {by_transform} via a named transform), "
             f"{uncertified} NOT certified (1-2 digits: counting words, thresholds, "
             f"round figures) — stated, not hidden. This is a SCREEN, not a proof.")
    if not quiet:
        _print(companion, findings, ruler)
    return findings


# --------------------------------------------------------------- limits check
LIMIT_WORDS = ["限制", "未驗", "未測", "假設", "不確定", "尚未", "無法", "僅適用",
               "caveat", "limitation", "unverified", "untested", "assumption",
               "not covered", "known issue"]


def check_limits(original: Path, companion: Path, quiet=False):
    """REPORT ONLY. Whether a limitation survived a rewrite is a reading, not a
    match: this lists what the original said and lets the human rule."""
    otext, ctext = reader_text(original), reader_text(companion)
    clow = ctext.lower()
    findings = []
    for raw in otext.splitlines():
        line = raw.strip()
        if not line or not any(w.lower() in line.lower() for w in LIMIT_WORDS):
            continue
        marker = next(w for w in LIMIT_WORDS if w.lower() in line.lower())
        findings.append(dict(
            verdict="INFO" if marker.lower() in clow else "UNDET",
            cls="limitation", hit=line[:90], line=0,
            why=("a line with the same marker exists in the companion — a human "
                 "decides whether it is the same limitation")
            if marker.lower() in clow else
            f"no line in the companion carries '{marker}' — dropped, or reworded?"))
    if not quiet:
        n_missing = sum(1 for f in findings if f["verdict"] == "UNDET")
        _print(companion, findings,
               f"{len(findings)} limitation lines in the original, {n_missing} with no "
               f"lexical counterpart. This check RULES ON NOTHING — audience-fit keeps "
               f"limitations in the main text, and only a reader can say whether a "
               f"reworded one still says it.")
    return findings


# --------------------------------------------------------------------- output
def _print(target, findings, ruler):
    print(f"target: {target.name}")
    for f in findings:
        loc = f":{f['line']}" if f["line"] else ""
        print(f"  [{f['verdict']:<5}] {f['cls']:<13} {f['hit']}{loc}\n           {f['why']}")
    counts = {k: sum(1 for f in findings if f["verdict"] == k)
              for k in ("FAIL", "WARN", "INFO", "UNDET")}
    print(f"  ruler: {ruler}")
    print(f"  {counts['FAIL']} FAIL, {counts['WARN']} WARN, {counts['INFO']} INFO, "
          f"{counts['UNDET']} UNDET\n")


# ---------------------------------------------------------------- calibration
ORIGINAL = """# ccfg retrieval audit (canonical, engineering voice)

The rewrite ratio measured 1.336 against the 2026-08-01 baseline over
tools/xi_scan.py, and the p90 latency was 812.5 ms.
Gate S7 PASS; run-id run_9f3a11c2; sha 4c1d9ba77e0f1122.
Limitation: the sampler was never run against a cold cache, so the cold path is
unverified.
Assumption: the 1310 nm figure is carried over from the earlier round.
Known issue: two of the eleven probes time out on this machine.
"""

CLEAN = """# 檢索健檢（受眾版）

比基準高 33.6%，反應時間 812.5 毫秒。
限制：冷啟動的情況沒有測過。
假設：波長數字沿用上一輪。
"""

INVENTED = """# 檢索健檢（受眾版）

比基準高 33.6%，反應時間 812.5 毫秒，命中率 91.4%。
限制：冷啟動的情況沒有測過。
"""

LEAKY = """# 檢索健檢（受眾版）

比基準高 33.6%。掃描器 tools/xi_scan.py 的 S7 PASS，run_9f3a11c2 這一輪
（sha 4c1d9ba77e0f1122）共 7 PASS。
限制：冷啟動的情況沒有測過。
"""


def selftest():
    tmp = Path(tempfile.mkdtemp(prefix="afgate-cal-"))
    files = {}
    for name, body in (("original.md", ORIGINAL), ("clean.md", CLEAN),
                       ("invented.md", INVENTED), ("leaky.md", LEAKY)):
        p = tmp / name
        p.write_text(body, encoding="utf-8")
        files[name] = p
    print(f"calibration fixtures: {tmp}\n")

    results = {}
    results["values/known-false"] = check_values(files["original.md"], files["clean.md"], quiet=True)
    results["values/known-true"] = check_values(files["original.md"], files["invented.md"], quiet=True)
    results["voice/known-false"] = check_voice(files["clean.md"], quiet=True)
    results["voice/known-true"] = check_voice(files["leaky.md"], quiet=True)
    lim = check_limits(files["original.md"], files["invented.md"], quiet=True)

    def fails(k):
        return [f for f in results[k] if f["verdict"] == "FAIL"]

    checks = [
        ("values known-false stays clean (33.6% is a named transform of 1.336)",
         not fails("values/known-false")),
        ("values known-true caught (91.4 explained by nothing)",
         any(f["hit"].startswith("91.4") for f in fails("values/known-true"))),
        ("voice known-false stays clean", not fails("voice/known-false")),
        ("voice known-true caught: path", any(f["cls"] == "path" for f in fails("voice/known-true"))),
        ("voice known-true caught: sha", any(f["cls"] == "sha" for f in fails("voice/known-true"))),
        ("voice known-true caught: run-id", any(f["cls"] == "run-id" for f in fails("voice/known-true"))),
        ("voice known-true caught: PASS count",
         any(f["cls"] == "pass-count" for f in fails("voice/known-true"))),
        ("limits rules on nothing (no FAIL ever)",
         not [f for f in lim if f["verdict"] == "FAIL"]),
        ("limits reports the dropped 假設 line",
         any(f["verdict"] == "UNDET" for f in lim)),
    ]
    for label, ok in checks:
        print(f"  [{'ok ' if ok else 'BAD'}] {label}")
    good = all(ok for _, ok in checks)
    print("\ncalibration:", "PASS — both sides separated on both determinable checks"
          if good else "BROKEN — this gate may not rule on a real companion")
    return 0 if good else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", nargs="?", choices=["voice", "values", "limits", "all"])
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--allow", action="append", metavar="VALUE=REASON",
                    help="a companion number that is legitimately not in the original; "
                         "the reason is printed beside it")
    ap.add_argument("--no-apparatus", action="store_true",
                    help="treat the whole file as the reader's main text "
                         "(no provenance/對照 zone)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.mode:
        ap.error("mode required (voice | values | limits | all)")

    found = []
    if a.mode == "voice":
        if len(a.files) != 1:
            ap.error("voice takes one file: the companion")
        found = check_voice(a.files[0], apparatus=None if a.no_apparatus else APPARATUS)
    else:
        if len(a.files) != 2:
            ap.error(f"{a.mode} takes two files: <original> <companion>")
        o, c = a.files
        if a.mode in ("values", "all"):
            found += check_values(o, c, allow=a.allow)
        if a.mode in ("limits", "all"):
            found += check_limits(o, c)
        if a.mode == "all":
            found += check_voice(c, apparatus=None if a.no_apparatus else APPARATUS)
    if any(f["verdict"] == "FAIL" for f in found):
        return 2
    return 1 if any(f["verdict"] == "WARN" for f in found) else 0


if __name__ == "__main__":
    sys.exit(main())
