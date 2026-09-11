#!/usr/bin/env python
"""page-fill-gate — does a human-facing HTML page USE the width it is given?

    python fill_gate.py <file.html|url> [...] [--viewport 1707x830 ...] [--class X]
                        [--json] [--no-controls] [--quiet]

Property under test (user ruling 2026-09-04, `ops/environment.md` § Display):
a page read on this machine must not leave an asymmetric void on the right.
The named defect is the LEFT-ANCHORED CAP — a page container (or a painted,
row-alone block) capped in width and hugging the left edge, which is how one
shell's `max-width:1060px` became 13 deliverables with 31–40 % of the screen
unused. Symmetric voids (a centred reading column) are a different, allowed
shape; how much fill a page owes depends on its CLASS.

Classes are DATA in `page_classes.json` (one row = one class + its rule); a new
kind of page is a new row plus a fixture, never a code branch. The page declares
its class with `<html data-page-class="…">`. An undeclared page is INFERRED
from structure and its verdict is CAPPED AT WARN in both directions, because a
gate may only rule on what it can determine (global CLAUDE.md gate rule). The
cap used to apply to FAIL only, which meant an undeclared page could report a
clean PASS — a PASS that is an artifact of the guessed ruler, not a measurement
of the page, and one that gets carried forward as evidence. Corrected
2026-09-08 on a measured case:
`outputs/diagram-authoring/mfp-audit-f5-owner-view.html` reads reach 74 % with
symmetric voids, which PASSES as the inferred `document-short` and FAILS as
`document-long` — the class an audit page with diagrams plausibly is. The
promotion trigger that turns an inferred class into a declared one is written in
the registry's `unknown_policy`.

Severity (memory `gate-severity-by-consumer`): the container-level verdict is
determinable → FAIL; a per-block finding (a narrower painted box alone in its
row) is a judgment the reader makes → WARN with the selector printed, promoted
to FAIL per selector via `block_fail_selectors` once a human has reported it.

Controls run on EVERY invocation unless `--no-controls`: a known-bad fixture
(left-anchored 800px cap) must FAIL and a known-good fixture must PASS — a
reject-everything gate scores 100 % on a one-sided calibration.

Exit codes: 0 = no FAIL (WARNs allowed) · 1 = at least one FAIL · 2 = the
instrument is unavailable (Playwright/Chromium missing) — downgrade-and-forward,
the caller must print the warning and not claim the property.

Library use: `from fill_gate import gate_paths; rows = gate_paths([...])`.

review-when: the screen or scaling in `ops/environment.md` changes (edit
`reference_viewports`); Playwright's page.evaluate semantics change; a class
row is added (add its fixture to tests/ the same commit).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
REGISTRY_PATH = HERE / "page_classes.json"
FIXTURES = HERE / "fixtures"

MEASURE_JS = r"""(opts) => {
  const W = innerWidth, H = innerHeight, cs = el => getComputedStyle(el);
  const html = document.documentElement;
  const declared = html.getAttribute('data-page-class');
  // ---- chrome: fixed/sticky, near full-height, hugging an edge, not a rail ----
  let areaL = 0, areaR = W; const chrome = [];
  for (const el of document.querySelectorAll('body *')) {
    const s = cs(el); if (s.position !== 'fixed' && s.position !== 'sticky') continue;
    const r = el.getBoundingClientRect();
    if (r.height < H * 0.8 || r.width < 40 || r.width > W * 0.5) continue;
    if (el.matches('[data-rail], #rail')) continue;
    if (r.left <= 1) { areaL = Math.max(areaL, r.right); chrome.push({side: 'left', w: Math.round(r.width), id: el.id || el.tagName}); }
    else if (r.right >= W - 1) { areaR = Math.min(areaR, r.left); chrome.push({side: 'right', w: Math.round(r.width), id: el.id || el.tagName}); }
  }
  const rail = document.querySelector('[data-rail], #rail');
  const railR = rail ? rail.getBoundingClientRect() : null;
  const painted = s => (s.backgroundColor !== 'rgba(0, 0, 0, 0)' && s.backgroundColor !== 'transparent')
                       || parseFloat(s.borderLeftWidth) > 0 || parseFloat(s.borderRightWidth) > 0;
  const ownText = el => Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim().length > 0);
  const media = el => /^(IMG|SVG|CANVAS|VIDEO|TABLE|PRE|FIGURE|IFRAME)$/.test(el.tagName);
  const skip = el => el.closest('script,style,nav,#side,[hidden],[data-fill-ignore]') || cs(el).position === 'fixed';
  // ---- one measurement over one area (the page, or one slide) ----
  const measure = (root, L, R, limitTop) => {
    let minL = Infinity, maxR = -Infinity, n = 0; const blocks = [];
    for (const el of root.querySelectorAll('*')) {
      if (skip(el)) continue;
      const s = cs(el); if (s.display === 'inline' || s.display === 'none' || s.visibility === 'hidden') continue;
      const r = el.getBoundingClientRect(); if (r.width < 24 || r.height < 8) continue;
      if (limitTop != null && r.top > limitTop) continue;
      const isPainted = painted(s), isText = ownText(el), isMedia = media(el);
      if (!(isPainted || isText || isMedia)) continue;           // pure wrappers do not count
      minL = Math.min(minL, r.left); maxR = Math.max(maxR, r.right); n++;
      // Block findings are about WIDE TEXT CONTAINERS capped by their own CSS. Media, controls,
      // chips/badges (intrinsic sizes) and children of grid / row-flex parents (the PARENT
      // allocates their width) are never findings — that is the proportional-vs-pixel rule.
      if (isPainted && r.height >= 24 && r.width >= 300 && !isMedia && !el.closest('figure')
          && /^(DIV|P|SECTION|ARTICLE|ASIDE|BLOCKQUOTE|DL|UL|OL|H[1-6])$/.test(el.tagName)
          && !/inline/.test(s.display)) {
        const ps = el.parentElement ? cs(el.parentElement) : null;
        const allocated = ps && (ps.display.includes('grid') || (ps.display.includes('flex') && !ps.flexDirection.startsWith('column')));
        if (!allocated) blocks.push({el, r, s});
      }
    }
    if (railR && !limitTop) { /* rail counts as content on the page-level area */ }
    if (railR && limitTop != null) { maxR = Math.max(maxR, railR.right); }
    const areaW = R - L;
    const leftVoid = n ? Math.max(0, minL - L) : areaW, rightVoid = n ? Math.max(0, R - maxR) : areaW;
    // per-block: painted, alone in its row, narrower than 85 % of its parent, left-anchored
    const findings = [];
    for (const b of blocks) {
      const p = b.el.parentElement; if (!p) continue;
      const pr = p.getBoundingClientRect(); const ps = cs(p);
      const pl = pr.left + parseFloat(ps.paddingLeft), prr = pr.right - parseFloat(ps.paddingRight);
      const pw = prr - pl; if (pw < 200) continue;
      if (b.r.width >= pw * 0.85) continue;
      const alone = !Array.from(p.children).some(sib => sib !== b.el && (() => { const q = sib.getBoundingClientRect();
        return q.width >= 24 && q.top < b.r.bottom && q.bottom > b.r.top && (q.left >= b.r.right - 1 || q.right <= b.r.left + 1); })());
      if (!alone) continue;
      const lv = b.r.left - pl, rv = prr - b.r.right;
      if (rv - lv > pw * opts.asym) {
        const tag = b.el.tagName.toLowerCase() + (b.el.id ? '#' + b.el.id : '') + (b.el.className && typeof b.el.className === 'string' ? '.' + b.el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
        findings.push({sel: tag, w: Math.round(b.r.width), parent_w: Math.round(pw), right_void: Math.round(rv)});
      }
    }
    return {areaL: Math.round(L), areaR: Math.round(R), areaW: Math.round(areaW), n,
            minL: n ? Math.round(minL) : null, maxR: n ? Math.round(maxR) : null,
            leftVoid: Math.round(leftVoid), rightVoid: Math.round(rightVoid),
            fill: n ? +((maxR - minL) / areaW).toFixed(3) : 0, reach: n ? +((maxR - L) / areaW).toFixed(3) : 0,
            findings: findings.slice(0, 6), findings_total: findings.length};
  };
  // ---- inference (only consulted when undeclared) ----
  const infer = () => {
    const slides = document.querySelectorAll('.slide');
    if (slides.length >= 2 && (cs(html).scrollSnapType !== 'none' || slides[0].getBoundingClientRect().height >= H * 0.9)) return 'deck';
    if (chrome.some(c => c.side === 'left') && document.querySelector('main')) return 'document-long';
    let svgA = 0; for (const s of document.querySelectorAll('svg')) { const r = s.getBoundingClientRect(); if (r.top < H) svgA += Math.max(0, Math.min(r.bottom, H) - Math.max(r.top, 0)) * r.width; }
    if (svgA >= 0.4 * W * H) return 'diagram';
    const shellLike = el => { if (!el) return false; const s = cs(el); return (s.display === 'grid' || s.display === 'flex') && el.getBoundingClientRect().height >= H * 0.9 && /hidden|auto|clip/.test(s.overflowY + s.overflow); };
    if (shellLike(document.body) || shellLike(document.body.firstElementChild) || document.querySelector('.app-shell, #app > .app, [data-page-class="tool"]')) return 'tool';
    for (const g of document.querySelectorAll('*')) { const s = cs(g); if (s.display === 'grid' && g.children.length >= 6 && s.gridTemplateColumns.split(' ').length >= 3 && g.getBoundingClientRect().top < H) return 'dashboard'; }
    return 'document-short';
  };
  const cls = declared || infer();
  const out = {declared, inferred: declared ? null : cls, cls, W, H, chrome, rail: !!railR};
  if (opts.scope) {
    const scopes = Array.from(document.querySelectorAll(opts.scope)).slice(0, opts.maxScopes || 8);
    out.scopes = scopes.map((sc, i) => { const r = sc.getBoundingClientRect(), s = cs(sc);
      const m = measure(sc, r.left + parseFloat(s.paddingLeft), r.right - parseFloat(s.paddingRight), null); m.index = i + 1; m.id = sc.id || null; return m; });
    if (!scopes.length) out.page = measure(document.body, areaL, areaR, H * 3);
  } else {
    out.page = measure(document.body, areaL, areaR, H * 3);
    if (railR) out.page.maxR = Math.max(out.page.maxR || 0, Math.round(railR.right)), out.page.rightVoid = Math.max(0, Math.round(areaR - Math.max(out.page.maxR, railR.right))), out.page.reach = +(((out.page.maxR) - areaL) / (areaR - areaL)).toFixed(3);
  }
  return out;
}"""


def load_registry(path: pathlib.Path = REGISTRY_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def to_url(target: str) -> str:
    if "://" in target:
        return target
    return pathlib.Path(target).resolve().as_uri()


def verdict(meas: dict, reg: dict, forced_class: str | None = None) -> dict:
    """Pure function: measurement + registry -> {status, class, reasons...}. No browser here."""
    classes = reg["classes"]
    cls = forced_class or meas["cls"]
    inferred = (forced_class is None and meas["declared"] is None)
    rule = classes.get(cls)
    asym = reg["defect_left_anchored_cap"]["asymmetry_frac"]
    reasons, status = [], "PASS"
    if rule is None:
        return {"status": "WARN", "cls": cls, "inferred": inferred,
                "reasons": [f"class '{cls}' is not in page_classes.json — add a row; measured only"]}
    areas = meas.get("scopes") or [meas["page"]]
    worst = None
    for a in areas:
        st, why = "PASS", []
        if a["n"] == 0:
            st, why = "WARN", ["no painted/text block found in the measured area"]
        else:
            left_anchored = (a["rightVoid"] - a["leftVoid"]) > asym * a["areaW"]
            mode = rule["mode"]
            if mode == "centered":
                sym_ok = abs(a["leftVoid"] - a["rightVoid"]) <= rule.get("symmetry_px", 8) + 2
                if not sym_ok:
                    st = "FAIL"; why.append(f"not centred: left void {a['leftVoid']}px vs right void {a['rightVoid']}px")
                if a["fill"] < rule.get("min_fill", 0):
                    st = "FAIL"; why.append(f"fill {a['fill']:.0%} < {rule['min_fill']:.0%}")
            elif mode == "fill":
                if a["reach"] < rule["min_fill"]:
                    st = "FAIL"; why.append(f"reach {a['reach']:.0%} < {rule['min_fill']:.0%} (right void {a['rightVoid']}px of {a['areaW']}px)")
            elif mode == "centered-or-fill":
                sym_ok = abs(a["leftVoid"] - a["rightVoid"]) <= rule.get("symmetry_px", 8) + 2
                if not (sym_ok or a["reach"] >= 0.85):
                    st = "FAIL"; why.append(f"neither centred (voids {a['leftVoid']}/{a['rightVoid']}px) nor filled (reach {a['reach']:.0%})")
                if a["fill"] < rule.get("min_fill", 0):
                    st = "FAIL"; why.append(f"fill {a['fill']:.0%} < {rule['min_fill']:.0%}")
            if left_anchored and st != "FAIL":
                st = "FAIL"; why.append(f"left-anchored cap: right void {a['rightVoid']}px exceeds left void {a['leftVoid']}px by > {asym:.0%} of {a['areaW']}px")
            if a["findings_total"]:
                promoted = [f for f in a["findings"] if any(f["sel"].startswith(s) for s in reg.get("block_fail_selectors", []))]
                if promoted:
                    st = "FAIL"; why.append("promoted block(s): " + ", ".join(f["sel"] for f in promoted))
                elif st == "PASS":
                    st = "WARN"
                why.append(f"{a['findings_total']} narrower left-anchored painted block(s) alone in row: "
                           + ", ".join(f"{f['sel']} {f['w']}/{f['parent_w']}px" for f in a["findings"][:3]))
        if a.get("index"):
            why = [f"slide {a['index']}: {w}" for w in why]
        rank = {"PASS": 0, "WARN": 1, "FAIL": 2}
        if worst is None or rank[st] > rank[worst[0]]:
            worst = (st, why)
        reasons += why
    status = worst[0] if worst else "WARN"
    if inferred:
        # An inferred class caps the verdict at WARN in BOTH directions, fixed
        # 2026-09-08. The downgrade used to apply only to FAIL, so a page whose
        # class nobody declared could report a clean PASS -- and that PASS is an
        # artifact of the guess, not a measurement of the page. Measured case:
        # `outputs/diagram-authoring/mfp-audit-f5-owner-view.html` reads
        # reach 74% with symmetric 436/436 voids, which PASSES as the inferred
        # `document-short` and FAILS as `document-long`, the class an audit page
        # with diagrams plausibly is. The run printed "0 FAIL / 0 WARN" and that
        # number would have been carried forward as evidence. A gate may only
        # rule on what it can DETERMINE -- in the permissive direction too.
        was, status = status, "WARN"
        note = (f"class INFERRED as '{cls}' (no data-page-class) — verdict capped at "
                f"WARN, so this row is NOT evidence the page is well laid out; "
                f"it measured {was} against a GUESSED ruler. Repair: declare "
                f"`<html data-page-class=\"…\">` and re-run. ")
        reasons.insert(0, note + reg["unknown_policy"]["promotion_trigger"])
    return {"status": status, "cls": cls, "inferred": inferred, "reasons": reasons}


def gate_paths(targets, viewports=None, forced_class=None, reg=None, controls=True, advisory=None):
    """Measure every target at every viewport. Returns rows; raises RuntimeError(2) when the instrument is missing."""
    reg = reg or load_registry()
    gating = [tuple(v) for v in reg["reference_viewports"]["gating"]]
    adv = [tuple(v) for v in reg["reference_viewports"]["advisory"]]
    viewports = viewports or (gating + adv)
    advisory = set(advisory or adv) - set(gating)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # downgrade-and-forward: the caller prints, never claims
        raise RuntimeError(f"instrument unavailable: {exc}") from exc
    rows = []
    work = list(targets)
    if controls:
        work = [str(FIXTURES / "known-bad-left-cap.html"), str(FIXTURES / "known-good-fill.html")] + work
    with sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as exc:
            raise RuntimeError(f"instrument unavailable: {exc}") from exc
        for t in work:
            is_ctl = controls and t.startswith(str(FIXTURES))
            for (w, h) in ([gating[0]] if is_ctl else viewports):
                page = browser.new_page(viewport={"width": w, "height": h})
                page.route("http://**", lambda r: r.abort()); page.route("https://**", lambda r: r.abort())
                try:
                    page.goto(to_url(t), wait_until="load", timeout=60000)
                    page.wait_for_timeout(300)
                    cls_hint = forced_class
                    probe = page.evaluate("() => document.documentElement.getAttribute('data-page-class')")
                    cls_for_scope = cls_hint or probe
                    rule = reg["classes"].get(cls_for_scope or "", {})
                    opts = {"asym": reg["defect_left_anchored_cap"]["asymmetry_frac"],
                            "scope": rule.get("scope"), "maxScopes": rule.get("max_scopes", 8)}
                    meas = page.evaluate(MEASURE_JS, opts)
                    if not cls_for_scope and reg["classes"].get(meas["cls"], {}).get("scope"):
                        opts["scope"] = reg["classes"][meas["cls"]]["scope"]; meas = page.evaluate(MEASURE_JS, opts)
                    v = verdict(meas, reg, forced_class)
                    if (w, h) in advisory and v["status"] == "FAIL":
                        v["status"] = "WARN"; v["reasons"].insert(0, "advisory viewport — FAIL downgraded")
                    a = (meas.get("scopes") or [meas["page"]])
                    summary = a[0] if len(a) == 1 else min(a, key=lambda x: x["reach"])
                    rows.append({"target": t, "control": ("known-bad" if "bad" in t else "known-good") if is_ctl else None,
                                 "viewport": f"{w}x{h}", "class": v["cls"], "inferred": v["inferred"],
                                 "status": v["status"], "reach": summary["reach"], "fill": summary["fill"],
                                 "left_void": summary["leftVoid"], "right_void": summary["rightVoid"],
                                 "chrome": meas["chrome"], "reasons": v["reasons"]})
                except Exception as exc:
                    rows.append({"target": t, "control": None, "viewport": f"{w}x{h}", "class": "?", "inferred": True,
                                 "status": "WARN", "reach": 0, "fill": 0, "left_void": 0, "right_void": 0, "chrome": [],
                                 "reasons": [f"could not measure: {exc}"]})
                finally:
                    page.close()
        browser.close()
    if controls:
        bad = [r for r in rows if r["control"] == "known-bad"]; good = [r for r in rows if r["control"] == "known-good"]
        if not bad or bad[0]["status"] != "FAIL":
            raise RuntimeError("fill-gate calibration: known-bad control did NOT fire — instrument fault, no verdict is valid")
        if not good or good[0]["status"] != "PASS":
            raise RuntimeError("fill-gate calibration: known-good control did NOT pass — instrument fault, no verdict is valid")
    return rows


def fmt(r: dict) -> str:
    if r["control"]:
        who = "control " + r["control"]
    elif "://" in r["target"]:
        who = r["target"]
    else:
        p = pathlib.Path(r["target"])
        who = p.name if p.name.lower() not in ("index.html", "index.htm") else f"{p.parent.name}/{p.name}"
    cls = ("inferred:" if r["inferred"] else "") + str(r["class"])
    line = f"fill-gate: {r['status']:4s} {r['viewport']:9s} class={cls:24s} reach={r['reach']:.0%} fill={r['fill']:.0%} void L/R={r['left_void']}/{r['right_void']}px  {who}"
    if r["reasons"]:
        line += "\n" + "\n".join("           - " + x for x in r["reasons"])
    return line


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--viewport", action="append", help="WxH; repeatable; default = registry gating + advisory")
    ap.add_argument("--class", dest="cls", help="force a class (overrides the page's declaration)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-controls", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="only non-PASS lines")
    a = ap.parse_args(argv)
    vps = [tuple(int(x) for x in v.lower().split("x")) for v in a.viewport] if a.viewport else None
    try:
        rows = gate_paths(a.targets, viewports=vps, forced_class=a.cls, controls=not a.no_controls)
    except RuntimeError as exc:
        print(f"fill-gate: SKIP — {exc}. Downgrade-and-forward: the width property is UNVERIFIED for these files.", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        for r in rows:
            if a.quiet and r["status"] == "PASS" and not r["control"]:
                continue
            print(fmt(r))
        n_fail = sum(1 for r in rows if r["status"] == "FAIL" and not r["control"])
        n_warn = sum(1 for r in rows if r["status"] == "WARN")
        ctl = "controls fired (known-bad FAIL, known-good PASS)" if not a.no_controls else "controls SKIPPED"
        print(f"fill-gate: {'FAIL' if n_fail else 'PASS'} — {n_fail} FAIL / {n_warn} WARN over {len([r for r in rows if not r['control']])} file×viewport rows; {ctl}")
    return 1 if any(r["status"] == "FAIL" and not r["control"] for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
