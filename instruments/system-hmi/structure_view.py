#!/usr/bin/env python3
"""structure_view: ONE static page answering one question -- "what is this system made of, and what
watches what?" -- generated from the registry-driven snapshot, never hand-drawn.

STATUS: LIVE since 2026-09-19 (user ruling: run the structure diagram now; visual direction D-9 waits
until the user has looked at it). Containment view: sources -> group faces -> subsystem -> component ->
point. It is NOT the HMI page (HMI-06): no service, no refresh, no controls. A derived file under out/;
regenerate instead of editing.

    python tools/system-hmi/hmi.py collect          # refresh the snapshot first (optional)
    python tools/system-hmi/structure_view.py       # -> tools/system-hmi/out/structure.html

Failure modes announce themselves: a missing or unreadable snapshot produces a page that says so.
"""
import html
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

TOOL = Path(__file__).resolve().parent
SNAP = TOOL / "out" / "snapshot.json"
OUT = TOOL / "out" / "structure.html"

CSS = """
:root{--ink:#22201c;--mute:#6f6a60;--line:#d9d3c5;--paper:#faf7f0;--card:#fffdf8;
--pass:#2f7d4f;--warn:#b7791f;--fail:#b3332b;--und:#7a7f87;--na:#c9c3b4}
*{box-sizing:border-box}
html{font-family:"Noto Serif TC","Source Han Serif TC","PMingLiU",Georgia,serif;color:var(--ink);background:var(--paper)}
body{margin:0;padding:2.2vw 2.6vw 4vw}
h1{font-size:clamp(22px,2vw,32px);margin:0 0 .2em;letter-spacing:.02em}
h2{font-size:clamp(16px,1.25vw,21px);margin:2.2em 0 .7em;border-bottom:1px solid var(--line);padding-bottom:.35em}
h2 small,.sub{color:var(--mute);font-weight:400;font-size:.8em}
p.lead{margin:.2em 0 0;color:var(--mute);font-size:clamp(13px,.95vw,15px)}
.legend{display:flex;flex-wrap:wrap;gap:.5em 1.6em;margin-top:1em;font-size:13px;color:var(--mute)}
.dot{display:inline-block;width:.8em;height:.8em;border-radius:50%;vertical-align:-.05em;margin-right:.35em}
.s-pass{background:var(--pass)}.s-warn{background:var(--warn)}.s-fail{background:var(--fail)}
.s-und{background:var(--und)}.s-na{background:var(--na)}
.grid{display:grid;gap:1.1vw;grid-template-columns:repeat(auto-fill,minmax(min(100%,23em),1fr))}
.grid.narrow{grid-template-columns:repeat(auto-fill,minmax(min(100%,15em),1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:.9em 1em;min-width:0}
.card h3{font-size:16px;margin:0 0 .15em;display:flex;justify-content:space-between;gap:.6em;align-items:baseline}
.card h3 span.en{color:var(--mute);font-weight:400;font-size:12px}
.badges{white-space:nowrap;font-family:Consolas,monospace;font-size:12px}
.badge{display:inline-block;padding:.05em .45em;border-radius:3px;color:#fff;margin-left:.25em}
.meta{font-size:12px;color:var(--mute);margin:.1em 0 .6em}
.comp{border-top:1px dotted var(--line);padding:.4em 0 .3em}
.comp .cid{font-family:Consolas,monospace;font-size:12px;word-break:break-all}
.comp .cl{font-size:11px;color:var(--mute);margin-left:.4em;white-space:nowrap}
.chips{display:flex;flex-wrap:wrap;gap:.25em .3em;margin-top:.3em}
.chip{font-size:11.5px;border:1px solid var(--line);border-left-width:4px;border-radius:3px;padding:.05em .45em;background:#fff;cursor:help}
.chip.pass{border-left-color:var(--pass)}.chip.warn{border-left-color:var(--warn)}.chip.fail{border-left-color:var(--fail)}
.chip.und{border-left-color:var(--und);color:var(--mute)}.chip.i{font-style:italic}
.nopoint{font-size:11px;color:var(--na)}
.err{border:2px solid var(--fail);padding:1em;background:#fff}
table.t{border-collapse:collapse;width:100%;font-size:13px}table.t td,table.t th{border-bottom:1px solid var(--line);padding:.3em .5em;text-align:left;vertical-align:top}
"""


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def cls(state, quality=None):
    if state in ("pass", "warn", "fail"):
        return state
    return "und"


def badge(label, state):
    c = {"pass": "var(--pass)", "warn": "var(--warn)", "fail": "var(--fail)"}.get(state, "var(--na)")
    return f'<span class="badge" style="background:{c}" title="{esc(label)} = {esc(state or "no reading")}">{esc(label)}</span>'


def chip(p):
    r = p.get("reading") or {}
    st = r.get("state")
    tip = " | ".join(x for x in [p.get("id"), p.get("why"), f"class={p.get('class')} tier={p.get('tier')}",
                                 f"source={r.get('source')}", f"state={st} quality={r.get('quality')}",
                                 (r.get("skip_reason") and f"skip={r.get('skip_reason')}") or "",
                                 (r.get("evidence") or "")[:300]] if x)
    i = " i" if p.get("class") == "integrity" else ""
    return f'<span class="chip {cls(st)}{i}" title="{esc(tip)}">{esc(p.get("alias") or p.get("id"))}</span>'


def page(body, title="system-hmi 結構圖"):
    return (f'<!doctype html><html lang="zh-Hant" data-page-class="dashboard"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>'
            f'<style>{CSS}</style></head><body>{body}</body></html>')


def build(snap):
    subs, comps, points = snap["subsystems"], snap["components"], snap["points"]
    groups, scan, run = snap.get("groups", []), snap.get("scan", {}), snap.get("run", {})
    by_sub_comp = defaultdict(lambda: defaultdict(list))
    for p in points:
        by_sub_comp[p.get("subsystem")][p.get("component")].append(p)
    comps_by_sub = defaultdict(list)
    for c in comps:
        comps_by_sub[c.get("subsystem")].append(c)
    # native points name the reporting tool; every other adapter's "source" is a one-off command or
    # file, so those are grouped by adapter type to keep this band readable
    adapter_zh = {"exit-code": "直接跑指令看結束碼", "status-file": "讀工具留下的狀態檔", "line-scan": "掃描文字檔的某一行",
                  "fs-link": "檢查連結／junction", "manual": "人工填報"}
    src = Counter(((p.get("reading") or {}).get("source") or "?") if p.get("adapter") == "native"
                  else f"{p.get('adapter')}（{adapter_zh.get(p.get('adapter'), '其他轉接')}）" for p in points)
    states = Counter(cls((p.get("reading") or {}).get("state")) for p in points)
    o = []
    o.append("<h1>system-hmi 結構圖 <span class='sub'>這套系統由什麼構成、誰在看誰</span></h1>")
    o.append(f"<p class='lead'>由登錄表與最近一次快照<strong>自動產生</strong>（不是手畫；登錄表改了就重產）。"
             f"快照 {esc(run.get('finished_at'))} · 層級 {esc(','.join(run.get('tiers_run') or []))} · "
             f"{len(subs)} 個子系統 · {len(comps)} 個元件 · {len(points)} 個監看點 · "
             f"通過 {states['pass']}／警告 {states['warn']}／失敗 {states['fail']}／未判定 {states['und']}</p>")
    o.append("<div class='legend'>"
             "<span><i class='dot s-pass'></i>通過</span><span><i class='dot s-warn'></i>警告</span>"
             "<span><i class='dot s-fail'></i>失敗</span><span><i class='dot s-und'></i>未判定／這一層沒跑（不等於通過）</span>"
             "<span><b>R</b>＝對帳類（東西跟紀錄合不合）</span><span><b>I</b>＝健全類（機制本身活著嗎；標籤為斜體）</span>"
             "<span>元件後的 n/5＝完整度檢核（C1–C5）</span><span>滑鼠停在標籤上＝這個點為什麼存在＋證據</span></div>")

    o.append("<h2>① 讀值從哪來 <small>來源 (sources)：每個來源是一支既有工具，HMI 只讀它的回報、不自己量</small></h2><div class='grid narrow'>")
    for name, n in src.most_common():
        o.append(f"<div class='card'><h3>{esc(name)}</h3><div class='meta'>{n} 個監看點</div></div>")
    o.append("</div>")

    for g in groups:
        o.append(f"<h2>② 能力群組：{esc(g.get('title_zh'))} <small>{esc(g.get('title_en'))} — 橫跨多個子系統的一項「能力」，分四個面各自亮燈</small></h2><div class='grid'>")
        for fid, f in sorted((g.get("faces") or {}).items()):
            o.append(f"<div class='card'><h3><span>{esc(fid)}　{esc(f.get('title'))}</span>"
                     f"<span class='badges'>{badge('R', f.get('r_state'))}{badge('I', f.get('i_state'))}</span></h3>"
                     f"<div class='meta'>{esc(f.get('points'))} 個點 · 未判定 {esc(f.get('degraded'))}</div></div>")
        o.append("</div>")

    o.append("<h2>③ 子系統 → 元件 → 監看點 <small>卡片＝子系統；虛線列＝元件（磁碟上真的存在的檔案／資料夾）；標籤＝看著它的點</small></h2><div class='grid'>")
    order = {"fail": 0, "warn": 1, None: 2, "pass": 3}
    for s in sorted(subs, key=lambda s: (min(order.get(s.get("r_state"), 2), order.get(s.get("i_state"), 2)), s["id"])):
        sid = s["id"]
        hist = " ".join(f"{k}:{v}" for k, v in sorted((s.get("completeness_histogram") or {}).items()))
        o.append(f"<div class='card'><h3><span>{esc(s.get('title_zh'))} <span class='en'>{esc(sid)}</span></span>"
                 f"<span class='badges'>{badge('R', s.get('r_state'))}{badge('I', s.get('i_state'))}</span></h3>"
                 f"<div class='meta'>{len(comps_by_sub[sid])} 元件 · {sum(len(v) for v in by_sub_comp[sid].values())} 點 · 完整度 {esc(hist) or '—'}</div>")
        seen = set()
        for c in sorted(comps_by_sub[sid], key=lambda c: (-len(by_sub_comp[sid].get(c["id"], [])), c["id"])):
            seen.add(c["id"])
            pts = by_sub_comp[sid].get(c["id"], [])
            comp = c.get("completeness") or {}
            o.append(f"<div class='comp'><span class='cid'>{esc(c['id'])}</span>"
                     f"<span class='cl'>{esc(c.get('kind'))} · {esc(comp.get('score', ''))} {esc(comp.get('label', ''))}</span>")
            o.append("<div class='chips'>" + ("".join(chip(p) for p in pts) or "<span class='nopoint'>沒有點在看它</span>") + "</div></div>")
        rest = [p for cid, ps in by_sub_comp[sid].items() if cid not in seen for p in ps]
        if rest:
            o.append("<div class='comp'><span class='cid'>（登錄表外的對象／整個子系統層級）</span><div class='chips'>"
                     + "".join(chip(p) for p in rest) + "</div></div>")
        o.append("</div>")
    o.append("</div>")

    o.append("<h2>④ 登錄表與磁碟的落差 <small>新東西出現而沒登錄＝警告；這就是「新系統會立刻被追蹤」的機制</small></h2>")
    o.append("<table class='t'><tr><th>項目</th><th>數量</th><th>內容（前 12）</th></tr>")
    for k, label in (("unregistered", "磁碟上有、登錄表沒有"), ("missing", "登錄表有、磁碟上沒有"),
                     ("overlaps", "兩條規則搶同一個檔"), ("unregistered_points", "來源回報了、登錄表沒有的點")):
        v = scan.get(k) or []
        items = [x if isinstance(x, str) else json.dumps(x, ensure_ascii=False) for x in v[:12]]
        o.append(f"<tr><td>{label}</td><td>{len(v)}</td><td class='cid'>{esc('、'.join(items))}</td></tr>")
    o.append(f"<tr><td>刻意忽略</td><td>{esc(scan.get('ignored_count'))}</td><td></td></tr></table>")
    o.append(f"<p class='lead' style='margin-top:2em'>產生於 {time.strftime('%Y-%m-%d %H:%M')} · registry sha256 {esc(str(run.get('registry_sha256'))[:12])} · "
             f"這一頁是結構視圖，不是操作面板：沒有服務、不會自動更新。</p>")
    return page("".join(o))


def main():
    try:
        snap = json.loads(SNAP.read_text(encoding="utf-8"))
        doc = build(snap)
        rc = 0
    except Exception as exc:  # noqa: BLE001 -- the page must say what went wrong instead of staying blank
        doc = page(f"<h1>system-hmi 結構圖</h1><div class='err'><b>無法產生：</b>{esc(type(exc).__name__)}: {esc(exc)}<br>"
                   f"請先執行 <code>python tools/system-hmi/hmi.py collect</code>，再重跑本工具。</div>")
        print(f"structure_view: FAILED {type(exc).__name__}: {exc}", file=sys.stderr)
        rc = 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc, encoding="utf-8")
    print(str(OUT))
    return rc


if __name__ == "__main__":
    sys.exit(main())
