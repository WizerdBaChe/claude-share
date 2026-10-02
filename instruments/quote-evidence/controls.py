"""Two-sided controls for tools/quote-evidence/qe.py.

Run: python tools/quote-evidence/controls.py

Every control records the ASSERTED VALUE (score or verdict) so a flip is visible
as a value change, not only a label (rules/verification-ladder.md, L-062). The
page text is self-authored for this suite — never a copyrighted page.

Text-level controls (C1–C12) need nothing but Python. The end-to-end control
(E1/E2) renders the same text into an image and runs the Windows OCR engine; if
the engine or a CJK font is missing it reports `undetermined` (named, excluded
from the pass count, never read as a pass).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qe  # noqa: E402

PAGE = ("本工具只比對短引文是否出現在頁面上，不轉錄整頁內容。"
        "每條主張都要附出處與十五字以內的引文。"
        "核對者只回報相符或不符，不抄寫原文。")
RESULTS = []


def rec(name, ok, value):
    RESULTS.append((bool(ok), name, value))


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "p1.txt").write_text(PAGE, encoding="utf-8")
        # OCR-damaged copy: one char dropped inside the quoted span
        (d / "p2.txt").write_text(PAGE.replace("整頁", "整"), encoding="utf-8")
        src = {"P1": "p1", "P2": "p2", "P9": "absent"}

        def j(q, loc, verdict=None):
            return qe.judge(q, loc, src, d, verdict)

        v, s, _ = j("不轉錄整頁內容", "P1·¶1")
        rec("C1 exact quote -> PASS", v == "PASS" and s == 1.0, f"{v} {s}")
        v, s, _ = j("只比對短引文是否出現在頁面上", "P2·¶1")
        v2, s2, _ = j("不轉錄整頁內容", "P2·¶1")
        rec("C2 quote with one OCR-dropped char -> PASS", v2 == "PASS" and s2 < 1.0, f"{v2} {s2:.2f}")
        v, s, _ = j("第一冊適合初級程度學習者", "P1·¶1")
        rec("C3 fabricated quote -> FAIL", v == "FAIL" and s < qe.UNDET_AT, f"{v} {s:.2f}")
        v, s, _ = j("核對者要抄寫整段原文", "P1·¶3")
        rec("C4 meaning-inverted near-quote -> FAIL", v == "FAIL", f"{v} {s:.2f}")
        # C5 pins the measured blind spot: a one-char negation flip is NOT caught.
        # If this starts failing, the instrument improved: update the RULER and qe docstring.
        v, s, _ = j("每條主張都不要附出處", "P1·¶2")
        rec("C5 BLIND SPOT pinned: one-char negation flip still scores >= PASS_AT",
            v == "PASS" and s >= qe.PASS_AT, f"{v} {s:.2f}")
        v, s, why = j("本工具只比對短引文是否出現在頁面上不轉錄整頁內容", "P1·¶1")
        rec("C6 over-length quote -> FAIL (size)", v == "FAIL" and "CJK-eq" in why, f"{v} {qe.cjk_eq('本工具只比對短引文是否出現在頁面上不轉錄整頁內容')}")
        v, s, _ = j("引文", "P1·¶2")
        rec("C7 too-short quote with no exact hit -> not PASS unless exact",
            v == "PASS" and s == 1.0, f"{v} {s}")   # exact substring is still presence
        v, s, _ = j("引用文", "P1·¶2")
        rec("C7b too-short non-exact quote -> UNDET or FAIL, never PASS", v in ("UNDET", "FAIL"), f"{v} {s:.2f}")
        v, s, _ = j("不轉錄整頁內容", "P9·¶1")
        rec("C8 OCR text missing -> undetermined", v == "undetermined" and s is None, v)
        v, s, _ = j(12345, "P1·¶1")
        rec("C9 non-string quote -> undetermined", v == "undetermined", v)
        v, s, _ = j("不轉錄整頁內容", "圖7·¶1")
        rec("C10 locator naming no source -> FAIL", v == "FAIL" and s is None, v)
        v, s, _ = j("不轉錄整頁內容", "P1·¶1", "mismatch")
        rec("C11 verifier mismatch overrides score 1.0 -> FAIL", v == "FAIL" and s == 1.0, f"{v} {s}")
        v, s, _ = j("核對者只要回報對或錯", "P1·¶3")
        v_m, s_m, _ = j("核對者只要回報對或錯", "P1·¶3", "match")
        rec("C12 verifier match lifts a sub-PASS score -> PASS (same score both sides)",
            v != "PASS" and v_m == "PASS" and s == s_m, f"{v} {s:.2f} -> {v_m} {s_m:.2f}")

        # registry-level: counts exclude undetermined; exit code follows FAIL only
        reg = {"sources": src, "claims": [
            {"id": "a", "anchors": [{"loc": "P1·¶1", "q": "不轉錄整頁內容"}]},
            {"id": "b", "anchors": [{"loc": "P9·¶1", "q": "不轉錄整頁內容"}, "not-an-object"]}]}
        rows = qe.check(reg, d)
        kinds = [r[0] for r in rows]
        rec("R1 registry: PASS + 2 undetermined, exit 0",
            kinds == ["PASS", "undetermined", "undetermined"], kinds)
        reg["claims"].append({"id": "c", "anchors": [{"loc": "P1·¶2", "q": "第一冊適合初級程度學習者"}]})
        rows = qe.check(reg, d)
        import io
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            rc = qe.report(rows)
        rec("R2 registry with one FAIL -> exit 1 and ruler printed", rc == 1 and "ruler:" in buf.getvalue(), rc)
        rows = qe.check({"claims": []}, d)
        rec("R3 registry without sources -> undetermined, not PASS", rows[0][0] == "undetermined", rows[0][0])

        # end-to-end through the real OCR engine
        e2e = end_to_end(d)
        if e2e is None:
            print("  undetermined E1/E2: OCR engine or CJK font unavailable — end-to-end not measured")

    bad = [r for r in RESULTS if not r[0]]
    for ok, name, value in RESULTS:
        print(f"  {'ok  ' if ok else 'FAIL'} {name}  [{value}]")
    print(f"quote-evidence controls: {len(RESULTS) - len(bad)}/{len(RESULTS)} ok"
          + ("" if e2e is not None else " (end-to-end undetermined)"))
    return 1 if bad else 0


def end_to_end(d: Path):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        return None
    font_path = Path("C:/Windows/Fonts/msjh.ttc")
    if not font_path.exists():
        return None
    font = ImageFont.truetype(str(font_path), 40)
    lines = [PAGE[i:i + 18] for i in range(0, len(PAGE), 18)]
    im = Image.new("L", (900, 70 * len(lines) + 40), 255)
    dr = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        dr.text((20, 20 + 70 * k), ln, fill=0, font=font)
    img = d / "e2e.png"
    im.save(img)
    out = d / "ocr"
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        rc = qe.ocr([img], out, "zh-Hant-TW")
    if rc != 0 or not (out / "e2e.txt").exists():
        return None
    src = {"E": "e2e"}
    v, s, _ = qe.judge("不轉錄整頁內容", "E·¶1", src, out)
    rec("E1 end-to-end OCR: true quote -> PASS", v == "PASS", f"{v} {s:.2f}")
    v, s, _ = qe.judge("第一冊適合初級程度學習者", "E·¶1", src, out)
    rec("E2 end-to-end OCR: fabricated quote -> FAIL", v == "FAIL", f"{v} {s:.2f}")
    return True


if __name__ == "__main__":
    sys.exit(main())
