"""Two-sided calibration of page-fill-gate: one known-good and one known-bad page per class.

    python tools/page-fill-gate/tests/test_fill_gate.py

Every class row in page_classes.json must have BOTH a passing and a failing
fixture here — a class with only one side is not calibrated (a reject-everything
gate scores 100 % on a one-sided check). Adding a class row without adding its
pair fails this test on purpose.
"""
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import fill_gate  # noqa: E402

REG = fill_gate.load_registry()

BASE = """<!doctype html><html lang="zh-Hant"{attr}><head><meta charset="utf-8"><title>{title}</title>
<style>body{{margin:0;font-family:system-ui,sans-serif;line-height:1.6}} *{{box-sizing:border-box}}
p{{margin:8px 0}} .box{{border-left:4px solid #888;background:#f4f4f4;padding:10px 16px}}
table{{width:100%;border-collapse:collapse}} td{{border:1px solid #ccc;padding:4px}}
{css}</style></head><body>{body}</body></html>"""

TEXT = "<p>" + "本段是量測用的內文，長度足以在任何欄寬下換行。" * 6 + "</p>"

CASES = {
    # name: (class attr, css, body, expected status)
    "document-short centred 900": ("document-short",
        ".wrap{max-width:900px;margin:0 auto;padding:40px 20px}",
        f"<main class='wrap'><h1>標題</h1>{TEXT}<div class='box'>note</div>{TEXT}</main>", "PASS"),
    "document-short left-anchored 900": ("document-short",
        ".wrap{max-width:900px;margin:0;padding:40px 20px}",
        f"<main class='wrap'><h1>標題</h1>{TEXT}<div class='box'>note</div>{TEXT}</main>", "FAIL"),
    "document-long fluid + sidebar": ("document-long",
        "#side{position:fixed;left:0;top:0;bottom:0;width:280px;background:#eee} main{margin-left:280px;padding:36px clamp(20px,4vw,64px)}",
        f"<nav id='side'>TOC</nav><main><h1>標題</h1>{TEXT}<table><tr><td>a</td><td>b</td></tr></table>{TEXT}</main>", "PASS"),
    "document-long capped 1060 left": ("document-long",
        "#side{position:fixed;left:0;top:0;bottom:0;width:280px;background:#eee} main{margin-left:280px;padding:36px 72px;max-width:1060px}",
        f"<nav id='side'>TOC</nav><main><h1>標題</h1>{TEXT}<div class='box' style='max-width:36em'>note</div>{TEXT}</main>", "FAIL"),
    "document-long fluid main + rail": ("document-long",
        "#side{position:fixed;left:0;top:0;bottom:0;width:280px;background:#eee} main{margin-left:280px;margin-right:320px;padding:36px 48px} #rail{position:fixed;right:0;top:0;bottom:0;width:320px;background:#f8f8f8;border-left:1px solid #ccc;padding:16px}",
        f"<nav id='side'>TOC</nav><main><h1>標題</h1>{TEXT}{TEXT}</main><aside id='rail' data-rail><p>本節速查</p></aside>", "PASS"),
    "deck slides fill": ("deck",
        "html{scroll-snap-type:y proximity} .slide{min-height:100vh;padding:24px 72px} .thesis{background:#eef;border:1px solid #99c;padding:12px} .grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}",
        f"<section class='slide'><h1>結論</h1><div class='thesis'>一句話主張</div>{TEXT}</section><section class='slide'><div class='grid2'><div class='box'>a</div><div class='box'>b</div></div></section>", "PASS"),
    "deck thesis capped 56em left": ("deck",
        "html{scroll-snap-type:y proximity} .slide{min-height:100vh;padding:24px 72px} .thesis{background:#eef;border:1px solid #99c;padding:12px;max-width:40em;font-size:20px}",
        f"<section class='slide'><h1>結論</h1><div class='thesis'>一句話主張，這個框被上限卡在 40em 而且靠左，右邊空一大塊。</div>{TEXT}</section><section class='slide'><h2>二</h2>{TEXT}</section>", "WARN"),
    "tool proportional shell": ("tool",
        ".app{display:grid;grid-template-columns:clamp(220px,20vw,320px) minmax(0,1fr);height:100vh;overflow:hidden} .app>*{padding:16px;border:1px solid #ccc}",
        f"<div class='app'><aside>面板</aside><main>{TEXT}</main></div>", "PASS"),
    "tool centred 1240 cap": ("tool",
        ".container{max-width:1240px;margin:0 auto;padding:16px} .panes{display:grid;grid-template-columns:1fr 1fr;gap:16px}",
        f"<div class='container'><h1>工具</h1><div class='panes'><div class='box'>{TEXT}</div><div class='box'>{TEXT}</div></div></div>", "FAIL"),
    "diagram centred svg": ("diagram",
        "main{max-width:1240px;margin:0 auto;padding:16px} svg{width:100%;height:auto;display:block;border:1px solid #ccc}",
        "<main><h1>圖</h1><svg viewBox='0 0 1280 720'><rect x='10' y='10' width='1260' height='700' fill='#eef' stroke='#336'/></svg></main>", "PASS"),
    "diagram left-anchored svg": ("diagram",
        "main{max-width:1240px;margin:0;padding:16px} svg{width:100%;height:auto;display:block;border:1px solid #ccc}",
        "<main><h1>圖</h1><svg viewBox='0 0 1280 720'><rect x='10' y='10' width='1260' height='700' fill='#eef' stroke='#336'/></svg></main>", "FAIL"),
    "dashboard auto-fit cards": ("dashboard",
        ".cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;padding:16px}",
        "<div class='cards'>" + "".join(f"<div class='box'>card {i}</div>" for i in range(8)) + "</div>", "PASS"),
    "dashboard capped left": ("dashboard",
        ".cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;padding:16px;max-width:900px}",
        "<div class='cards'>" + "".join(f"<div class='box'>card {i}</div>" for i in range(8)) + "</div>", "FAIL"),
    "undeclared left cap -> inferred, WARN only": (None,
        "#side{position:fixed;left:0;top:0;bottom:0;width:280px;background:#eee} main{margin-left:280px;padding:36px 72px;max-width:1060px}",
        f"<nav id='side'>TOC</nav><main><h1>標題</h1>{TEXT}{TEXT}</main>", "WARN"),
    # The OTHER direction of the same rule, added 2026-09-08. A page with no
    # declared class that measures fine is still measured against a GUESS, so
    # its PASS is an artifact of the inference and must not be reported as
    # evidence. Before this, an undeclared page could print "0 FAIL / 0 WARN"
    # and that number would be carried forward
    # (outputs/diagram-authoring/mfp-audit-f5-owner-view.html, measured).
    "undeclared but well laid out -> STILL WARN, not PASS": (None,
        "main{padding:16px} .box{width:100%}",
        f"<main><div class='box'><h1>標題</h1>{TEXT}{TEXT}</div></main>", "WARN"),
}


def main() -> int:
    failures = []
    # registry shape: every class has a mode and at least one threshold
    for name, row in REG["classes"].items():
        if row.get("mode") not in ("centered", "fill", "centered-or-fill") or not (row.get("min_fill") or row.get("symmetry_px")):
            failures.append(f"registry row {name!r} lacks mode/threshold")
    covered = {c[0] for c in CASES.values() if c[0]}
    for name in REG["classes"]:
        sides = {CASES[k][3] for k in CASES if CASES[k][0] == name}
        if name not in covered or not ({"PASS"} & sides) or not ({"FAIL", "WARN"} & sides):
            failures.append(f"class {name!r} has no two-sided fixture pair in this test")
    with tempfile.TemporaryDirectory() as td:
        paths, expect = [], {}
        for name, (cls, css, body, want) in CASES.items():
            p = pathlib.Path(td) / (name.replace(" ", "_").replace("/", "_").replace(">", "").replace(",", "") + ".html")
            attr = f' data-page-class="{cls}"' if cls else ""
            p.write_text(BASE.format(attr=attr, title=name, css=css, body=body), encoding="utf-8")
            paths.append(str(p)); expect[str(p)] = (name, want)
        try:
            rows = fill_gate.gate_paths(paths, viewports=[(1707, 830)], controls=True)
        except RuntimeError as exc:
            print(f"SKIP: {exc}"); return 2
        for r in rows:
            if r["control"]:
                print(f"control {r['control']:10s} {r['status']}"); continue
            name, want = expect[r["target"]]
            ok = r["status"] == want
            print(f"{'ok  ' if ok else 'MISS'} {name:42s} want {want:4s} got {r['status']:4s} reach={r['reach']:.0%} voidL/R={r['left_void']}/{r['right_void']} class={('inferred:' if r['inferred'] else '')+str(r['class'])}")
            if not ok:
                failures.append(f"{name}: want {want}, got {r['status']} — " + "; ".join(r["reasons"]))
    print("\n".join(failures) if failures else "test_fill_gate: PASS (all classes two-sided, controls fired)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
