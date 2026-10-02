#!/usr/bin/env python
"""pptx-presentation-gate — is this deck flat and clean? (rules/office-deck-deliverables.md P3)

Reads the EMITTED .pptx package (never the builder) and rules, per slide.

P1 (figure-led) is deliberately NOT here. Its limit is content density: more
than half of a page's narrative being information a figure could carry. Which
sentences could have been a figure is not determinable from the package, so
P1 is a reader pass (user ruling 2026-09-20). A figure-AREA share was built
and removed the same day: it measured layout, not density, and accepted decks
sit at a median of 23-38 % of slide area.

P3, flat and clean (every class) -- the decoration a flat design removes:

    GRADIENT  a gradient fill on a shape, line, text run or table cell
    EFFECT    shadow / glow / reflection / soft edge on a shape or picture frame
    3D        a bevel, extrusion or contour (a:sp3d)
    INHERITED the same three arriving through the theme: a shape that carries a
              p:style (python-pptx gives every autoshape one) and does not override
              it inherits theme effectStyle[effectRef] and fillStyle[fillRef].
              python-pptx's own default theme resolves effectRef idx=2 to an outer
              shadow, so an untouched add_shape() rectangle is NOT flat -- the
              failure this gate exists to see, since nothing on the slide XML
              itself says "shadow".
    COLOURS   more than --max-colours distinct non-grey colours on one slide,
              counted over shape fills, lines, text runs and table cells.
              Pictures and charts are the figure and are never counted.

Severity (gate-severity-by-consumer):
    GRADIENT / EFFECT / 3D / INHERITED are determinable from the package ->
        FAIL for a presentation-class deck (the default: an undeclared deck is
        presentation), WARN for --class conclusion (user ruling 2026-09-15:
        conclusion decks block only on overlap / skew).
    COLOURS is a count, not a defect -- whether five colours are five meanings
        or five decorations is the reader's call -> always WARN.
        Promotion trigger: a presentation deck the user rejects for colour
        noise while this gate reported it clean -> recalibrate the grey
        threshold / the cap, never promote on a guess.

Not determined (reported UNDET, forwarded): colours inside embedded chart parts
and pictures (they are the figure); slide layouts and masters (the template
owns them -- a decorated template is a template decision, reported once).

    python presentation_gate.py <deck.pptx> [--class presentation|conclusion]
                        [--max-colours 3] [--json out.json]
    python presentation_gate.py --selftest

Exit: 0 clean, 1 WARN only, 2 FAIL. Origin: B-14 (post EP005 平凡簡報術,
2026-09-20) + SSLD rulings (black/white/grey, no shadow on 3D figures).
"""
import argparse
import json
import posixpath
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
A = "{%s}" % NS["a"]
P = "{%s}" % NS["p"]
EFFECT_TAGS = {"outerShdw", "innerShdw", "prstShdw", "glow", "reflection", "softEdge"}
SCHEME_ALIAS = {"tx1": "dk1", "bg1": "lt1", "tx2": "dk2", "bg2": "lt2"}
GREY_SPREAD = 24  # max-min channel <= this reads as black / white / grey


# ---------------------------------------------------------------- package

def _rels(z, part):
    d, f = posixpath.split(part)
    rp = posixpath.join(d, "_rels", f + ".rels")
    if rp not in z.namelist():
        return {}
    out = {}
    for r in ET.fromstring(z.read(rp)).findall("rel:Relationship", NS):
        out[r.get("Type").rsplit("/", 1)[-1]] = posixpath.normpath(posixpath.join(d, r.get("Target")))
    return out


def _theme_for(z, slide_part, cache):
    layout = _rels(z, slide_part).get("slideLayout")
    master = _rels(z, layout).get("slideMaster") if layout else None
    theme = _rels(z, master).get("theme") if master else None
    if theme is None:
        return None
    if theme not in cache:
        cache[theme] = Theme(ET.fromstring(z.read(theme)))
    return cache[theme]


class Theme:
    def __init__(self, root):
        cs = root.find(".//a:clrScheme", NS)
        self.colours = {}
        if cs is not None:
            for c in cs:
                tag = c.tag.replace(A, "")
                v = c.find("a:srgbClr", NS)
                s = c.find("a:sysClr", NS)
                self.colours[tag] = (v.get("val") if v is not None
                                     else s.get("lastClr") if s is not None else None)
        fsl = root.find(".//a:fmtScheme/a:fillStyleLst", NS)
        bgl = root.find(".//a:fmtScheme/a:bgFillStyleLst", NS)
        esl = root.find(".//a:fmtScheme/a:effectStyleLst", NS)
        self.fills = list(fsl) if fsl is not None else []
        self.bgfills = list(bgl) if bgl is not None else []
        self.effects = list(esl) if esl is not None else []

    def fill_style(self, idx):
        if idx >= 1001 and idx - 1001 < len(self.bgfills):
            return self.bgfills[idx - 1001]
        if 1 <= idx <= len(self.fills):
            return self.fills[idx - 1]
        return None

    def effect_style(self, idx):
        return self.effects[idx - 1] if 1 <= idx <= len(self.effects) else None

    def resolve(self, el, style_clr=None):
        """a colour-choice element's parent -> RRGGBB or None."""
        for c in el:
            t = c.tag.replace(A, "")
            if t == "srgbClr":
                return c.get("val").upper()
            if t == "sysClr":
                return (c.get("lastClr") or "").upper() or None
            if t == "schemeClr":
                v = c.get("val")
                if v == "phClr":
                    return style_clr
                return (self.colours.get(SCHEME_ALIAS.get(v, v)) or "").upper() or None
            if t == "prstClr":
                return {"black": "000000", "white": "FFFFFF"}.get(c.get("val"), "PRST:" + c.get("val"))
        return None


def _is_grey(hexv):
    if not hexv or len(hexv) != 6:
        return True
    try:
        ch = [int(hexv[i:i + 2], 16) for i in (0, 2, 4)]
    except ValueError:
        return False
    return max(ch) - min(ch) <= GREY_SPREAD


# ---------------------------------------------------------------- checks

def _decor(node):
    """Decoration found under one spPr / effectStyle node -> set of kinds."""
    kinds = set()
    if node is None:
        return kinds
    if node.find(".//a:gradFill", NS) is not None:
        kinds.add("GRADIENT")
    el = node.find("a:effectLst", NS)
    if el is not None and any(c.tag.replace(A, "") in EFFECT_TAGS for c in el):
        kinds.add("EFFECT")
    if node.find("a:effectDag", NS) is not None:
        kinds.add("EFFECT")
    sp3d = node.find("a:sp3d", NS)
    if sp3d is not None and (sp3d.find("a:bevelT", NS) is not None or sp3d.find("a:bevelB", NS) is not None
                             or int(sp3d.get("extrusionH", "0")) > 0 or int(sp3d.get("contourW", "0")) > 0):
        kinds.add("3D")
    return kinds


FILL_TAGS = ("noFill", "solidFill", "gradFill", "blipFill", "pattFill", "grpFill")


def check_shape(sp, theme):
    """-> (decor kinds, inherited kinds, colours) for one sp / cxnSp / pic."""
    sppr = sp.find("p:spPr", NS)
    own = _decor(sppr)
    inherited = set()
    colours = []
    style = sp.find("p:style", NS)
    is_pic = sp.tag == P + "pic"
    style_clr = None
    if style is not None and theme is not None:
        eref = style.find("a:effectRef", NS)
        fref = style.find("a:fillRef", NS)
        has_eff = sppr is not None and (sppr.find("a:effectLst", NS) is not None
                                        or sppr.find("a:effectDag", NS) is not None)
        if eref is not None and not has_eff:
            inherited |= _decor(theme.effect_style(int(eref.get("idx", "0"))))
        has_fill = sppr is not None and any(sppr.find("a:" + t, NS) is not None for t in FILL_TAGS)
        if fref is not None and not has_fill and not is_pic:
            fs = theme.fill_style(int(fref.get("idx", "0")))
            if fs is not None and fs.tag == A + "gradFill":
                inherited.add("GRADIENT")
            style_clr = theme.resolve(fref)
            if fs is not None and fs.tag in (A + "solidFill", A + "gradFill"):
                colours.append(style_clr)
    if not is_pic and theme is not None:
        if sppr is not None:
            f = sppr.find("a:solidFill", NS)
            if f is not None:
                colours.append(theme.resolve(f, style_clr))
            ln = sppr.find("a:ln/a:solidFill", NS)
            if ln is not None:
                colours.append(theme.resolve(ln, style_clr))
        for rpr in sp.iter(A + "rPr"):
            f = rpr.find("a:solidFill", NS)
            if f is not None:
                colours.append(theme.resolve(f))
            if rpr.find("a:gradFill", NS) is not None:
                own.add("GRADIENT")
    return own, inherited, [c for c in colours if c]


def check_deck(path, klass="presentation", max_colours=3):
    findings, undet = [], []
    cache = {}
    stats = {"slides": 0, "shapes": 0, "styled": 0, "max_colours": 0}
    with zipfile.ZipFile(path) as z:
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
        rp =ET.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
        targets = {r.get("Id"): posixpath.normpath(posixpath.join("ppt", r.get("Target")))
                   for r in rp.findall("rel:Relationship", NS)}
        order = [targets[s.get("{%s}id" % NS["r"])] for s in pres.findall("p:sldIdLst/p:sldId", NS)]
        for n, part in enumerate(order, 1):
            root = ET.fromstring(z.read(part))
            theme = _theme_for(z, part, cache)
            if theme is None:
                undet.append(f"slide {n}: no theme reachable, inheritance not resolved")
            colours = set()
            for sp in root.iter():
                if sp.tag not in (P + "sp", P + "cxnSp", P + "pic"):
                    continue
                name = (sp.find(".//p:cNvPr", NS).get("name") if sp.find(".//p:cNvPr", NS) is not None else "?")
                own, inh, cols = check_shape(sp, theme)
                stats["shapes"] += 1
                stats["styled"] += sp.find("p:style", NS) is not None
                for k in sorted(own):
                    findings.append({"slide": n, "shape": name, "kind": k, "source": "own"})
                for k in sorted(inh - own):
                    findings.append({"slide": n, "shape": name, "kind": "INHERITED", "detail": k, "source": "theme"})
                colours.update(c for c in cols if not _is_grey(c))
            for tc in root.iter(A + "tcPr"):
                if tc.find("a:gradFill", NS) is not None:
                    findings.append({"slide": n, "shape": "table cell", "kind": "GRADIENT", "source": "own"})
                f = tc.find("a:solidFill", NS)
                if f is not None and theme is not None:
                    c = theme.resolve(f)
                    if c and not _is_grey(c):
                        colours.add(c)
            if root.find(".//a:graphicData[@uri='http://schemas.openxmlformats.org/drawingml/2006/chart']", NS) is not None:
                undet.append(f"slide {n}: chart colours not read (the chart is the figure)")
            stats["slides"] += 1
            stats["max_colours"] = max(stats["max_colours"], len(colours))
            if len(colours) > max_colours:
                findings.append({"slide": n, "shape": "-", "kind": "COLOURS",
                                 "detail": f"{len(colours)} > {max_colours}: " + " ".join(sorted(colours))})
    decor_sev = "FAIL" if klass == "presentation" else "WARN"
    for f in findings:
        f["severity"] = "WARN" if f["kind"] == "COLOURS" else decor_sev
    return findings, undet, stats


def report(findings, undet, stats, quiet=False):
    # the ruler beside the rate: a clean verdict over 0 shapes read is not a clean deck
    print(f"read: {stats['slides']} slides, {stats['shapes']} shapes "
          f"({stats['styled']} theme-styled), most non-grey colours on one slide = {stats['max_colours']}")
    for f in findings:
        extra = f" ({f['detail']})" if f.get("detail") else ""
        print(f"{f['severity']:4}  slide {f['slide']:>2}  {f['kind']:9} {f['shape']}{extra}")
    for u in undet:
        print(f"UNDET {u}")
    sev = {f["severity"] for f in findings}
    code = 2 if "FAIL" in sev else 1 if "WARN" in sev else 0
    if not quiet:
        print(f"presentation-gate: {len(findings)} finding(s), exit {code}")
    return code


# ---------------------------------------------------------------- selftest

def selftest():
    import tempfile
    from pathlib import Path
    from lxml import etree as LET
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches

    tmp = Path(tempfile.mkdtemp(prefix="flatgate_"))

    def deck(name, build):
        p = Presentation()
        s = p.slides.add_slide(p.slide_layouts[6])
        build(s)
        out = tmp / f"{name}.pptx"
        p.save(out)
        return out

    def flat_rect(s, rgb="1F4E79", x=0):
        r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5 + x), Inches(1), Inches(1), Inches(1))
        r.fill.solid()
        r.fill.fore_color.rgb = RGBColor.from_string(rgb)
        r.line.fill.background()
        r.shadow.inherit = False
        return r

    def inject(shape, xml):
        shape._element.spPr.append(LET.fromstring(xml))

    cases = []
    cases.append(("clean", deck("clean", lambda s: flat_rect(s)), "presentation", set(), 0))
    cases.append(("default-add_shape", deck("default", lambda s: s.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(2), Inches(1))), "presentation", {"INHERITED"}, 2))

    def grad(s):
        r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(1), Inches(2), Inches(1))
        r.fill.gradient()
        r.shadow.inherit = False
    cases.append(("gradient", deck("gradient", grad), "presentation", {"GRADIENT"}, 2))
    cases.append(("gradient-conclusion", tmp / "gradient.pptx", "conclusion", {"GRADIENT"}, 1))

    def shadow(s):
        r = flat_rect(s)
        el = r._element.spPr.find(A + "effectLst")
        el.append(LET.fromstring(
            f'<a:outerShdw xmlns:a="{NS["a"]}" blurRad="40000" dist="20000"><a:srgbClr val="000000"/></a:outerShdw>'))
    cases.append(("explicit-shadow", deck("shadow", shadow), "presentation", {"EFFECT"}, 2))

    def bevel(s):
        r = flat_rect(s)
        inject(r, f'<a:sp3d xmlns:a="{NS["a"]}"><a:bevelT w="63500" h="25400"/></a:sp3d>')
    cases.append(("bevel", deck("bevel", bevel), "presentation", {"3D"}, 2))

    def five(s):
        for i, c in enumerate(["C00000", "00B050", "0070C0", "FFC000", "7030A0"]):
            flat_rect(s, c, i * 1.2)
    cases.append(("five-colours", deck("five", five), "presentation", {"COLOURS"}, 1))

    def greys(s):
        for i, c in enumerate(["000000", "404040", "808080", "A6A6A6", "D9D9D9", "FFFFFF"]):
            flat_rect(s, c, i * 1.2)
    cases.append(("six-greys", deck("greys", greys), "presentation", set(), 0))

    ok = True
    for name, path, klass, want, want_code in cases:
        f, _, _ = check_deck(path, klass)
        got = {x["kind"] for x in f}
        code = 2 if any(x["severity"] == "FAIL" for x in f) else 1 if f else 0
        passed = got == want and code == want_code
        ok &= passed
        print(f"{'PASS' if passed else 'FAIL'}  {name:20} kinds={sorted(got)} exit={code} (want {sorted(want)} {want_code})")
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 2


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("deck", nargs="?")
    ap.add_argument("--class", dest="klass", choices=["presentation", "conclusion"], default="presentation")
    ap.add_argument("--max-colours", type=int, default=3)
    ap.add_argument("--json")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.deck:
        ap.error("deck path required")
    findings, undet, stats = check_deck(a.deck, a.klass, a.max_colours)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"deck": a.deck, "class": a.klass, "stats": stats, "findings": findings, "undet": undet},
                      fh, ensure_ascii=False, indent=2)
    sys.exit(report(findings, undet, stats, a.quiet))


if __name__ == "__main__":
    main()
