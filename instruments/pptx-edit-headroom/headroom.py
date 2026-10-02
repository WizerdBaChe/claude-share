#!/usr/bin/env python
"""pptx-edit-headroom — does this deck survive the reader's own one-line edit?

An editable deck is delivered so a human can edit it. Build-time fit checks
(width estimators, orphan-wrap rules, a COM render of the deck AS BUILT) all
measure the deck standing still; none of them measures what happens the moment
its reader adds a line. This instrument does exactly that, per text frame:

    duplicate the frame's own last paragraph -> re-measure -> restore

and rules on the two ways that edit breaks a slide:

    CLIP    a frame that will NOT grow (autosize none) now lays out text taller
            than its inner height: the reader's line is invisible.
    COLLIDE a frame that DOES grow (autosize shape-to-fit-text, and tables,
            whose row heights recompute) grew into another shape's box, or off
            the slide.

Determination is PowerPoint's own layout engine (TextRange2.BoundHeight and the
post-edit Shape.Height), never an estimator: python-pptx width estimators run
~4% narrow against bold JhengHei (rules/office-deck-deliverables.md), and for
autofit shapes the height python-pptx WROTE is not the height PowerPoint uses --
measured 2026-09-10 on an SSLD report deck, where a stored
374.4pt textbox collapsed to ~93pt the instant its text was touched. A gate
reading the stored geometry would have been ruling on a number PowerPoint had
already discarded.

    python headroom.py <deck.pptx> [--json out.json] [--quiet]
    python headroom.py --selftest        two-sided calibration, 4 controls

Severity (gate-severity-by-consumer): the consumer is a human editing a real
file, so a determinable break is FAIL. What this instrument cannot determine is
reported UNDET and forwarded, never silently passed:

    autosize=2 (shrink text on overflow)  PowerPoint absorbs the line by scaling
        the font; the scale lives in a:normAutofit/@fontScale, not on the COM
        object model. Promotion trigger: the first deck family that actually
        ships autosize=2 frames -- then read fontScale out of the saved package
        and FAIL below the family's font floor.
    shapes nested deeper than one group level.

The input file is never modified: everything runs on a temp copy, and each
frame is restored before the next is tested.
"""
import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# MsoAutoSize
AUTOSIZE_NONE, AUTOSIZE_SHAPE_TO_TEXT, AUTOSIZE_TEXT_TO_SHAPE = 0, 1, 2
MSO_GROUP = 6
CR = chr(13)
EPS = 0.5  # pt — below this an overlap is a rounding artifact, not a collision


def _shapes(container, depth=0):
    """Yield (shape, group_path). One group level is entered; deeper is reported."""
    for shp in container:
        if getattr(shp, "Type", None) == MSO_GROUP:
            if depth == 0:
                for inner, _ in _shapes(shp.GroupItems, depth + 1):
                    yield inner, shp.Name
            else:
                yield shp, "deep-group"
            continue
        yield shp, ""


def _frames(slide):
    """Yield (kind, shape, cell_or_None, textframe) for every frame carrying text."""
    for shp, group in _shapes(slide.Shapes):
        try:
            if shp.HasTable:
                for r in range(1, shp.Table.Rows.Count + 1):
                    for c in range(1, shp.Table.Columns.Count + 1):
                        cell = shp.Table.Cell(r, c)
                        tf = cell.Shape.TextFrame2
                        if tf.HasText:
                            yield "table", shp, (r, c), tf
                continue
        except Exception:
            pass
        try:
            if shp.HasTextFrame and shp.TextFrame2.HasText:
                yield ("deep-group" if group == "deep-group" else "text"), shp, None, shp.TextFrame2
        except Exception:
            continue


def _box(shp):
    return (shp.Left, shp.Top, shp.Left + shp.Width, shp.Top + shp.Height)


def _settled_box(shp, tf):
    """The box PowerPoint will actually use once the text is touched."""
    try:
        if tf is not None and tf.AutoSize == AUTOSIZE_SHAPE_TO_TEXT:
            h = tf.TextRange.BoundHeight + tf.MarginTop + tf.MarginBottom
            return (shp.Left, shp.Top, shp.Left + shp.Width, shp.Top + h)
    except Exception:
        pass
    return _box(shp)


def _overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w > EPS and h > EPS


def _last_paragraph(text):
    """The frame's own last line — a self-similar probe, locale- and scale-free."""
    parts = [p for p in text.replace("\x0b", CR).split(CR) if p.strip()]
    return parts[-1] if parts else "X"


def _set_text(tf, text):
    """Rewrite a frame's text.

    TextRange2.Characters(start, length).Delete() raises "collection not
    supported" under late binding on Office 16 (measured 2026-09-10), so the
    whole-text assignment is the restore primitive. It also serves as the
    settle touch: any edit makes PowerPoint recompute autofit geometry.
    """
    tf.TextRange.Text = text


def audit(deck: Path, quiet=False, content=None):
    """content: regexes matching the shape names a READER would plausibly extend.

    Whether a frame is body content or chrome is not something this instrument
    can determine -- a page-number box and a paragraph are both text frames, and
    the first real run against a delivered deck (SSLD 報告版, 2026-09-10) spent
    58 of its 72 findings on footers and badge pills nobody edits. So the
    predicate closes only over frames the CALLER declares; everything else is
    measured and printed, but ruled INFO. Undeclared run => WARN, never PASS.
    """
    import re

    import win32com.client

    pats = [re.compile(p) for p in (content or [])]

    def severity(shape_name):
        if not pats:
            return "WARN"
        return "FAIL" if any(p.search(shape_name) for p in pats) else "INFO"

    findings, stats = [], {"frames": 0, "slides": 0, "undet": 0, "declared": bool(pats)}
    app = win32com.client.Dispatch("PowerPoint.Application")
    pres = app.Presentations.Open(str(deck), ReadOnly=0, Untitled=0, WithWindow=0)
    try:
        sw, sh = pres.PageSetup.SlideWidth, pres.PageSetup.SlideHeight
        stats["slides"] = pres.Slides.Count
        for si in range(1, pres.Slides.Count + 1):
            slide = pres.Slides(si)
            frames = list(_frames(slide))

            # settle first: the stored height of an autofit shape is stale
            unsettled = []
            for kind, shp, cell, tf in frames:
                if kind == "deep-group":
                    continue
                try:
                    _set_text(tf, tf.TextRange.Text)
                except Exception as e:
                    unsettled.append((shp.Name, f"{type(e).__name__}: {e}"))
            for name, why in unsettled:
                findings.append(dict(where=f"slide {si} · {name}", verdict="UNDET",
                                     why=f"frame would not settle ({why}); its box may be stale"))
                stats["undet"] += 1

            baseline = {}
            for idx, (kind, shp, cell, tf) in enumerate(frames):
                try:
                    baseline[idx] = _settled_box(shp, None if kind == "table" else tf)
                except Exception:
                    baseline[idx] = None
            # non-text shapes are obstacles too
            obstacles = []
            for shp, _g in _shapes(slide.Shapes):
                try:
                    obstacles.append((shp.Name, _box(shp)))
                except Exception:
                    continue

            for idx, (kind, shp, cell, tf) in enumerate(frames):
                where = f"slide {si} · {shp.Name}" + (f" · cell{cell}" if cell else "")
                if kind == "deep-group":
                    findings.append(dict(where=where, verdict="UNDET",
                                         why="shape nested deeper than one group level"))
                    stats["undet"] += 1
                    continue
                stats["frames"] += 1
                try:
                    tr = tf.TextRange
                    autosize = tf.AutoSize
                    text0, n0 = tr.Text or "", tr.Length
                    inner_h = shp.Height - tf.MarginTop - tf.MarginBottom
                    probe = _last_paragraph(text0)

                    if autosize == AUTOSIZE_TEXT_TO_SHAPE:
                        findings.append(dict(where=where, verdict="UNDET",
                                             why="autosize=shrink-text-to-fit: the font scale "
                                                 "is not on the COM object model"))
                        stats["undet"] += 1
                        continue

                    h_before = shp.Height
                    tr.InsertAfter(CR + probe)
                    bh1 = tf.TextRange.BoundHeight
                    h_after = shp.Height
                    grew = h_after - h_before

                    if kind == "text" and autosize == AUTOSIZE_NONE:
                        if bh1 - inner_h > EPS:
                            findings.append(dict(
                                where=where, verdict=severity(shp.Name), mode="CLIP",
                                why=f"text {bh1:.1f}pt vs inner height {inner_h:.1f}pt "
                                    f"({bh1 - inner_h:.1f}pt clipped); frame does not grow",
                                probe=probe[:40]))
                    else:
                        box1 = (shp.Left, shp.Top, shp.Left + shp.Width, shp.Top + h_after)
                        if box1[3] - sh > EPS or box1[2] - sw > EPS:
                            findings.append(dict(
                                where=where, verdict=severity(shp.Name), mode="ESCAPE",
                                why=f"grew {grew:.1f}pt to bottom {box1[3]:.1f}pt, "
                                    f"past the {sh:.0f}pt slide edge", probe=probe[:40]))
                        else:
                            b0 = baseline.get(idx)
                            for oidx, (okind, oshp, ocell, otf) in enumerate(frames):
                                if oidx == idx or oshp.Name == shp.Name:
                                    continue
                                b_other = baseline.get(oidx)
                                if not b_other:
                                    continue
                                if _overlap(box1, b_other) and not (b0 and _overlap(b0, b_other)):
                                    findings.append(dict(
                                        where=where, verdict=severity(shp.Name), mode="COLLIDE",
                                        why=f"grew {grew:.1f}pt into "
                                            f"{oshp.Name}" + (f" cell{ocell}" if ocell else ""),
                                        probe=probe[:40]))
                                    break

                    _set_text(tf, text0)          # restore before the next frame
                except Exception as e:  # an unreadable frame is UNDET, never PASS
                    findings.append(dict(where=where, verdict="UNDET", why=f"{type(e).__name__}: {e}"))
                    stats["undet"] += 1
    finally:
        try:
            pres.Close()
        except Exception:
            pass
        try:
            app.Quit()
        except Exception:
            pass

    counts = {k: sum(1 for f in findings if f["verdict"] == k)
              for k in ("FAIL", "WARN", "INFO", "UNDET")}
    if not quiet:
        print(f"deck: {deck.name}  slides={stats['slides']}  frames={stats['frames']}")
        for f in findings:
            tag = f.get("mode", f["verdict"])
            print(f"  [{f['verdict']:<5}] {tag:<7} {f['where']}\n           {f['why']}")
        verdict = ("FAIL" if counts["FAIL"] else
                   "WARN (frame roles undeclared)" if counts["WARN"] else
                   "PASS" if not stats["undet"] else "PASS (with UNDET)")
        print(f"\nverdict: {verdict}  —  {counts['FAIL']} FAIL, {counts['WARN']} WARN, "
              f"{counts['INFO']} INFO, {stats['undet']} UNDET; "
              f"{stats['frames']} frames measured by PowerPoint")
        if not stats["declared"]:
            print("  ruler: no --content declared, so no finding could close as FAIL. "
                  "Chrome frames (page numbers, header strips, badge pills) are text\n"
                  "  frames too and a reader never extends them. Declare the content "
                  "frames to promote these WARNs to FAIL.")
    return findings, stats


# ------------------------------------------------------------------ calibration
def _build_controls(path: Path):
    """Two known-TRUE (must FAIL) and two known-false (must PASS) frames.

    A gate that has only ever seen one side of its predicate is uncalibrated:
    a reject-everything gate scores 100% on a one-sided check.
    """
    from pptx import Presentation
    from pptx.util import Emu, Inches, Pt
    from pptx.enum.text import MSO_AUTO_SIZE

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]

    def textbox(slide, l, t, w, h, text, autosize, size=18):
        tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = Emu(0)
        tf.auto_size = autosize
        for i, line in enumerate(text):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = line
            p.runs[0].font.size = Pt(size)
        return tb

    # slide 1 — the negative controls (must PASS)
    s1 = prs.slides.add_slide(blank)
    textbox(s1, 0.5, 0.5, 6.0, 4.0, ["roomy fixed frame, one short line"],
            MSO_AUTO_SIZE.NONE)                                   # ctrl-pass-clip
    textbox(s1, 7.0, 0.5, 5.0, 0.6, ["growing frame with the whole slide below it"],
            MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT)                      # ctrl-pass-grow

    # slide 2 — the positive controls (must FAIL), one per failure mode
    s2 = prs.slides.add_slide(blank)
    packed = ["這一行是刻意塞滿的中文字句，用來把固定尺寸文字框填到剛好見底 line %d" % i
              for i in range(1, 5)]
    textbox(s2, 0.5, 0.5, 5.0, 1.35, packed, MSO_AUTO_SIZE.NONE, size=14)  # ctrl-fail-clip
    textbox(s2, 7.0, 6.9, 5.0, 0.5, ["a growing frame parked on the bottom edge"],
            MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT, size=16)             # ctrl-fail-escape
    textbox(s2, 0.5, 3.2, 5.0, 0.4, ["a growing frame with a neighbour right below it"],
            MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT, size=16)             # ctrl-fail-collide
    textbox(s2, 0.5, 3.75, 5.0, 1.0, ["the neighbour it grows into"],
            MSO_AUTO_SIZE.NONE, size=16)                          # (the obstacle)

    prs.save(str(path))


def selftest():
    tmp = Path(tempfile.mkdtemp(prefix="headroom-cal-"))
    deck = tmp / "controls.pptx"
    _build_controls(deck)
    print(f"calibration deck: {deck}")
    findings, stats = audit(deck, quiet=True, content=[r".*"])

    failed = {f["where"] for f in findings if f["verdict"] == "FAIL"}
    modes = {f.get("mode") for f in findings if f["verdict"] == "FAIL"}
    expect_fail = [w for w in failed if w.startswith("slide 2")]
    unexpected = [w for w in failed if w.startswith("slide 1")]

    print(f"  frames measured: {stats['frames']}")
    for f in findings:
        print(f"  [{f['verdict']:<5}] {f.get('mode','-'):<7} {f['where']} — {f['why']}")

    # severity plumbing: the same predicate, undeclared, must not close as FAIL
    und, _ = audit(deck, quiet=True)
    und_fail = [f for f in und if f["verdict"] == "FAIL"]

    ok = (len(expect_fail) == 3 and not unexpected
          and modes >= {"CLIP", "ESCAPE", "COLLIDE"} and not und_fail)
    print("\ncalibration:", "PASS — 3/3 known-true controls caught (CLIP·ESCAPE·COLLIDE), "
          "2/2 known-false clean, undeclared run closes nothing"
          if ok else
          f"BROKEN — known-true caught {len(expect_fail)}/3 {sorted(m for m in modes if m)}, "
          f"known-false wrongly flagged {len(unexpected)}, "
          f"undeclared run wrongly closed {len(und_fail)}")
    if not ok:
        print("  (a gate that cannot separate these sides may not rule on a real deck)")
    return 0 if ok else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("deck", nargs="?", type=Path)
    ap.add_argument("--json", type=Path, help="write findings as JSON")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--content", action="append", metavar="REGEX",
                    help="shape-name pattern for frames a reader would extend; "
                         "repeatable. Without it nothing can close as FAIL.")
    ap.add_argument("--selftest", action="store_true",
                    help="two-sided calibration on a generated control deck")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if not a.deck or not a.deck.exists():
        ap.error("deck not found")

    tmp = Path(tempfile.mkdtemp(prefix="headroom-"))
    copy = tmp / a.deck.name
    shutil.copy2(a.deck, copy)          # the delivered file is never touched
    findings, stats = audit(copy, quiet=a.quiet, content=a.content)
    if a.json:
        a.json.write_text(json.dumps(dict(deck=str(a.deck), stats=stats, findings=findings),
                                     ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    if any(f["verdict"] == "FAIL" for f in findings):
        return 2
    return 1 if any(f["verdict"] == "WARN" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
