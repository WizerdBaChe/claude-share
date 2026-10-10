#!/usr/bin/env python3
"""controls — two-sided calibration for overlap_check.py.

Every verdict overlap_check can emit has a control that MUST produce it
(positive) and one that MUST NOT (negative); mutation controls prove each
verdict is carried by the rule under test, not by an accident of the fixture.
All fixture texts below were written for this file (no third-party text).

Run:  python -X utf8 ~/.claude/skills/clean-room-rebuild/scripts/controls.py
Exit: 0 = every control holds, 1 = at least one control failed.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import overlap_check as oc  # noqa: E402

EN_SOURCE = """The leaky meter keeps a reservoir of credits that drains whenever a caller
asks for work and slowly fills again as wall-clock time passes. Each request inspects
how many seconds have elapsed since the previous inspection, multiplies that interval
by the configured refill speed, and tops the reservoir up without ever exceeding its
ceiling. If the reservoir still holds at least one credit the request is admitted and
a single credit is removed; otherwise the request is turned away and the caller is
told how long to wait before trying again. Bursts are therefore bounded by the
ceiling while the long-run throughput converges on the refill speed.

class LeakyMeter:
    def __init__(self, refill_per_sec, ceiling):
        self.refill_per_sec = refill_per_sec
        self.ceiling = ceiling
        self.credits = ceiling
        self.lastInspectTs = time.monotonic()
"""

EN_LIGHT_EDIT = EN_SOURCE.split("\n\n")[0].replace("reservoir", "pool", 1) \
    .replace("caller", "client", 1).replace("slowly", "gradually")

EN_SYNONYM_EVERY_FEW = """The leaky gauge holds a tank of tokens that empties each time a
client requests work and gradually refills again as real time goes by. Every call checks
how many seconds have passed since the prior check, scales that gap by the set refill
pace, and fills the tank without ever passing its cap. If the tank still keeps at least
one token the call is allowed and one token is taken; else the call is refused and the
client learns how long to pause before retrying."""

EN_PARAPHRASE = """Purpose: a rate limiter that lets short spikes through but caps
sustained traffic. State: a budget counted in units of permitted operations, plus the
moment the budget was last brought up to date. Behaviour: elapsed time replenishes the
budget at a fixed pace, never beyond an upper bound. An incoming operation either spends
one unit and proceeds or, when nothing is left, is rejected together with an estimate of
the delay until a unit becomes available. Over a long window the accepted operations per
second approach the replenish pace; momentary bursts are limited by the upper bound."""

CJK_SOURCE = """漏桶計量器維持一個額度水庫，每當呼叫者請求工作時就扣除額度，並隨著時間流逝慢慢回補。
每次請求都會檢查距離上次檢查經過了幾秒，把這段間隔乘上設定的回補速度，然後把水庫補滿但不超過上限。
若水庫仍有至少一個額度，請求就被允許並扣掉一個額度；否則請求被拒絕，並告訴呼叫者要等多久再試。"""

CJK_PARAPHRASE = """這是一種限流做法：短時間的尖峰可以通過，但長時間的流量會被壓住。
系統用一份可用次數的預算來記帳，時間會以固定步調把預算加回去，最多加到頂。
新進來的操作若還有預算就花掉一單位放行；預算見底時就退回，並附上大約還要等候的時間。
長期來看，每秒放行量會趨近補充步調，瞬間尖峰則受頂值限制。"""

SHORT_QUOTE = EN_PARAPHRASE + '\nThe source calls the bound its "ceiling".'
SPEC_CODE = EN_PARAPHRASE + "\n\n```python\nbudget = min(cap, budget + dt * pace)\n```\n"
SPEC_IO = EN_PARAPHRASE + "\n\n```io\nadmit() on an empty budget -> rejected, wait ~0.5 s\n```\n"
SPEC_LEAK = EN_PARAPHRASE + "\nThe timestamp field is lastInspectTs and the pace is refill_per_sec."
SPEC_MERGER = SPEC_LEAK + "\n- merger: lastInspectTs, refill_per_sec (public constructor/API names)"
SPEC_PLAIN_WORD = EN_PARAPHRASE + "\nThe upper bound is called the ceiling in the interface."

# external review 2026-10-09 (zip read by another agent): fixtures for its findings
NOUN_SOURCE = EN_SOURCE + "\nThe project lives on GitHub, ships a JavaScript port and signs releases with SHA256.\n"
SPEC_NOUNS = EN_PARAPHRASE + "\nA port for JavaScript exists; releases are signed with SHA256 and hosted on GitHub."
SPEC_NOUNS_TERMS = SPEC_NOUNS + "\n- terms: GitHub, JavaScript, SHA256 (products and standards, not source names)"
API_NAMES = ["open_ledger", "close_ledger", "post_entry", "void_entry", "list_entries",
             "find_entry", "lock_period", "unlock_period", "export_csv", "import_csv",
             "verify_chain", "rebuild_index", "compact_store", "snapshot_store", "restore_store"]
API_SOURCE = EN_SOURCE + "\nPublic calls: " + ", ".join(API_NAMES) + ".\n"
API_RESULT = EN_PARAPHRASE + "\nOur module keeps the same calls for compatibility: " + ", ".join(API_NAMES) + "."
PRIVATE_SOURCE = EN_SOURCE + "\n        self._cache = {}\n    def __init__(self): pass\n"
PRIVATE_RESULT = EN_PARAPHRASE + "\nInternally we memoise results in _cache and set up state in __init__."
CYR_SOURCE = """Счётчик хранит запас кредитов, который убывает при каждом запросе и медленно
пополняется со временем. Каждый запрос смотрит, сколько секунд прошло с прошлой проверки,
умножает этот интервал на скорость пополнения и доливает запас, не превышая предел."""
CJK_LIGHT_EDIT = CJK_SOURCE.replace("水庫", "水池", 1).replace("呼叫者", "使用者", 1).replace("慢慢", "逐步", 1)

results = []


def rec(name: str, ok: bool, got) -> None:
    results.append(ok)
    print(f"{'ok  ' if ok else 'FAIL'}  {name}: {got}")


def v(cand, kind="output", src=(EN_SOURCE,), **kw):
    return oc.check(list(src), cand, kind, **kw)


def main() -> int:
    # --- positive controls: each MUST fire -----------------------------------
    r = v(EN_SOURCE.split("\n\n")[0])
    rec("P1 verbatim paragraph -> FAIL", r["verdict"] == "FAIL", r["verdict"])
    r = v(EN_LIGHT_EDIT)
    rec("P2 three-word light edit -> FAIL", r["verdict"] == "FAIL", (r["verdict"], r["longest_run"]))
    r = v(CJK_SOURCE, src=(CJK_SOURCE,))
    rec("P3 CJK verbatim -> FAIL", r["verdict"] == "FAIL", r["verdict"])
    r = v(SPEC_CODE, "spec")
    rec("P4 spec with a code fence -> FAIL", r["verdict"] == "FAIL" and r["code_fences"], r["reasons"])
    r = v(SPEC_LEAK, "spec")
    rec("P5 spec leaking source identifiers -> FAIL",
        r["verdict"] == "FAIL" and set(r["leaked_identifiers"]) == {"lastInspectTs", "refill_per_sec"},
        r["leaked_identifiers"])
    r = v("too short to judge", src=(EN_SOURCE,))
    rec("P6 tiny candidate -> UNDET", r["verdict"] == "UNDET", r["reasons"])
    r = v(EN_PARAPHRASE, src=("",))
    rec("P7 empty source -> UNDET", r["verdict"] == "UNDET", r["reasons"])
    r = v(SPEC_LEAK, "output")
    rec("P8 a result sharing source identifiers -> WARN (dry run 2026-10-09: _compile_pattern)",
        r["verdict"] == "WARN" and r.get("shared_identifiers") == ["lastInspectTs", "refill_per_sec"],
        (r["verdict"], r.get("shared_identifiers")))

    # --- negative controls: each MUST NOT fire --------------------------------
    r = v(EN_PARAPHRASE)
    rec("N1 independent EN paraphrase -> NO-SURFACE-COPY", r["verdict"] == "NO-SURFACE-COPY",
        (r["verdict"], r["longest_run"], r["containment"]))
    r = v(CJK_PARAPHRASE, src=(CJK_SOURCE,))
    rec("N2 independent CJK paraphrase -> NO-SURFACE-COPY", r["verdict"] == "NO-SURFACE-COPY",
        (r["verdict"], r["longest_run"], r["containment"]))
    r = v(SHORT_QUOTE)
    rec("N3 one short quoted word -> NO-SURFACE-COPY", r["verdict"] == "NO-SURFACE-COPY", r["verdict"])
    r = v(SPEC_IO, "spec")
    rec("N4 spec with an ```io example -> not FAIL", r["verdict"] != "FAIL", r["reasons"])
    r = v(SPEC_MERGER, "spec")
    rec("N5 identifiers declared on a merger line -> not FAIL", r["verdict"] != "FAIL",
        (r["verdict"], r["merger_declared"]))
    rec("N5b a parenthetical on the merger line is not a declared name",
        r["merger_declared"] == ["lastInspectTs", "refill_per_sec"], r["merger_declared"])
    r = v(SPEC_LEAK, "output", merger=("lastInspectTs", "refill_per_sec"))
    rec("N7 shared names passed as merger -> NO-SURFACE-COPY", r["verdict"] == "NO-SURFACE-COPY",
        (r["verdict"], r.get("shared_identifiers")))
    r = v(SPEC_PLAIN_WORD, "spec")
    rec("N6 a plain English word shared with source is not a leak", r["verdict"] != "FAIL",
        r["leaked_identifiers"])

    # --- external review 2026-10-09 ---------------------------------------------
    r = v(SPEC_NOUNS, "spec", src=(NOUN_SOURCE,))
    rec("P9 product/standard names shared but undeclared -> FAIL (names them, hints `terms:`)",
        r["verdict"] == "FAIL" and {"GitHub", "JavaScript", "SHA256"} <= set(r["leaked_identifiers"]),
        r["leaked_identifiers"])
    r = v(SPEC_NOUNS_TERMS, "spec", src=(NOUN_SOURCE,))
    rec("N8 the same names on a `terms:` line -> not FAIL, merger left empty",
        r["verdict"] != "FAIL" and not r["merger_declared"] and "SHA256" in r["terms_declared"],
        (r["verdict"], r["terms_declared"]))
    r = v(API_RESULT, "output", src=(API_SOURCE,))
    rec("P10 a long run of shared interface names, none declared -> WARN or FAIL",
        r["verdict"] in ("WARN", "FAIL"), (r["verdict"], r["longest_run"]))
    r = v(API_RESULT, "output", src=(API_SOURCE,), merger=API_NAMES)
    rec("N9 the same names passed as merger are masked before shingling -> NO-SURFACE-COPY",
        r["verdict"] == "NO-SURFACE-COPY", (r["verdict"], r["longest_run"]))
    r = v(PRIVATE_RESULT, "output", src=(PRIVATE_SOURCE,))
    rec("P11 a shared single-word private name (_cache) -> WARN; a dunder is not counted",
        r["verdict"] == "WARN" and r.get("shared_identifiers") == ["_cache"], r.get("shared_identifiers"))
    r = v(PRIVATE_RESULT, "spec", src=(PRIVATE_SOURCE,))
    rec("M4 kind=spec -> the private-name rule does not apply", "_cache" not in r["leaked_identifiers"],
        r["leaked_identifiers"])
    r = v(CYR_SOURCE * 2, src=(CYR_SOURCE,))
    rec("P12 Cyrillic verbatim -> FAIL (non-Latin scripts are tokens)", r["verdict"] == "FAIL",
        (r["verdict"], r["candidate_tokens"]))
    toks = [t for t, _ in oc.tokens_with_lines("résumé naïve")]
    rec("N10 accented Latin words stay whole", toks == ["résumé", "naïve"], toks)
    r = v(CJK_LIGHT_EDIT, src=(CJK_SOURCE,))
    rec("P13 CJK three-word light edit -> FAIL", r["verdict"] == "FAIL", (r["verdict"], r["longest_run"]))
    r = v(EN_PARAPHRASE, unread=1)
    rec("P14 NO-SURFACE-COPY with an unread source file -> UNDET", r["verdict"] == "UNDET", r["reasons"])
    r = v(EN_SOURCE.split("\n\n")[0], unread=1)
    rec("N11 an unread file does not soften a FAIL on what was read", r["verdict"] == "FAIL", r["verdict"])
    r = v(EN_PARAPHRASE, unread=0)
    rec("M5 unread=0 -> P14's input is NO-SURFACE-COPY again", r["verdict"] == "NO-SURFACE-COPY", r["verdict"])

    # --- ruler control: documents the stated blind spot, never a pass claim ---
    r = v(EN_SYNONYM_EVERY_FEW)
    rec("R1 synonym swap every few words is NOT caught (ruler: SSO/near-paraphrase)",
        r["verdict"] != "FAIL", (r["verdict"], r["longest_run"], r["containment"]))

    # --- mutation controls: remove the rule, the positive must stop firing ----
    r = v(EN_SOURCE.split("\n\n")[0], run_fail=10**9, run_warn=10**9, cont_fail=2.0, cont_warn=2.0)
    rec("M1 thresholds disabled -> P1 no longer FAILs", r["verdict"] != "FAIL", r["verdict"])
    r = v(SPEC_CODE, "output")
    rec("M2 kind=output -> P4's fence rule does not apply", not r["code_fences"], r["verdict"])
    r = v(SPEC_LEAK, "output")
    rec("M3 kind=output -> P5's identifier rule does not apply", not r["leaked_identifiers"], r["verdict"])

    # --- source walking + CLI exit codes --------------------------------------
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "sub").mkdir()
        (root / ".git").mkdir()
        (root / "sub" / "meter.md").write_text(EN_SOURCE, encoding="utf-8")
        (root / ".git" / "hidden.txt").write_text(CJK_SOURCE, encoding="utf-8")
        (root / "blob.bin").write_bytes(b"\x00\x01" + CJK_SOURCE.encode("utf-8"))
        texts, skips = oc.read_sources([str(root)])
        rec("W1 directory walk reads text, skips .git and binaries",
            len(texts) == 1 and skips["binary"] == 1, (len(texts), skips))
        r = v(CJK_SOURCE, src=texts)
        rec("W2 text only in skipped files does not count", r["verdict"] != "FAIL", r["verdict"])
        # a PDF whose first 4 KB hold no NUL byte must still not be read as text
        (root / "paper.pdf").write_bytes(b"%PDF-1.7\n" + EN_PARAPHRASE.encode("utf-8"))
        (root / "book.epub").write_bytes(b"PK\x03\x04" + EN_PARAPHRASE.encode("utf-8"))
        texts, skips = oc.read_sources([str(root)])
        rec("W3 PDF / ZIP documents are counted as `document`, apart from binaries",
            len(texts) == 1 and skips["document"] == 2 and skips["binary"] == 1, skips)
        cap = oc.MAX_TOTAL
        oc.MAX_TOTAL = 10
        try:
            texts, skips = oc.read_sources([str(root)])
        finally:
            oc.MAX_TOTAL = cap
        rec("W4 files past the total cap are counted as `over_cap`, not as binaries",
            not texts and skips["over_cap"] == 4 and skips["binary"] == 0, skips)
        cand_fail = root / "c1.md"
        cand_fail.write_text(EN_SOURCE.split("\n\n")[0], encoding="utf-8")
        cand_ok = root / "c2.md"
        cand_ok.write_text(EN_PARAPHRASE, encoding="utf-8")
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()) as out:
            e1 = oc.main(["--source", str(root), "--candidate", str(cand_fail)])
            e0 = oc.main(["--source", str(root), "--candidate", str(cand_ok)])
            e3 = oc.main(["--source", str(root / "paper.pdf"), "--candidate", str(cand_ok)])
        with contextlib.redirect_stderr(io.StringIO()):
            e2 = oc.main(["--source", str(root / "missing"), "--candidate", str(cand_ok)])
        (root / "paper.pdf").unlink()
        (root / "book.epub").unlink()
        with contextlib.redirect_stdout(io.StringIO()):
            e0 = oc.main(["--source", str(root), "--candidate", str(cand_ok)])
        rec("X1 CLI exit codes FAIL=1 / clean=0 / missing input=2 / UNDET (a PDF as the only "
            "source)=3; candidates sit INSIDE the source dir and must never count as source",
            (e1, e0, e2, e3) == (1, 0, 2, 3), (e1, e0, e2, e3))
        printed = out.getvalue()
        rec("X2 CLI never prints source text", "reservoir of credits" not in printed, len(printed))

    n_bad = results.count(False)
    print(f"\n{len(results) - n_bad}/{len(results)} controls hold")
    return 1 if n_bad else 0


if __name__ == "__main__":
    sys.exit(main())
