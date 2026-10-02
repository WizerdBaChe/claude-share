#!/usr/bin/env python3
"""mimic_view: the Level-1 overview of system-hmi drawn as a SCADA mimic; a click opens a faceplate.

STATUS: PROTOTYPE v2 since 2026-09-19. v1 (hub + 20 star links, anonymous lamp strips, "R/I" letters,
an unexplained bar) was reviewed by the user: "links, state display and UI have problems - look at the
WinCC design concepts and redo it; the bar is not full and clicking in does not say why".
Canon applied, point by point:
  * ISA-101 / High Performance HMI (a dated external-model design audit kept in the source environment, not shipped):
    one screen, no scrolling; colour reserved for abnormal states and never the only cue
    (fail = red down-triangle, warn = amber diamond, undetermined = magenta "?", normal = muted).
  * Siemens PCS 7 APL Style Guide (A5E03860312-01, primary source, read 2026-09-19):
    - a block icon carries: instance name (required), status display (required), analog value (optional);
      detail lives in a pop-up FACEPLATE with several VIEWS, not on the mimic and not on another page;
    - a bar graph always has its analog value beside it, so the number is never guessed from the bar;
    - the group display is a row of FIXED slots (one per alarm class): read by position, a slot is lit or blank.
  * One-line-diagram convention for links: one neutral busbar, one riser per column, one stub per
    block icon. No link crosses a block icon; only the STUB of an abnormal block takes its colour.
2026-09-23 softening pass (user: "too rigid, make it rounder"): radii, surfaces, filleted wires, pill chips,
segmented faceplate tabs - appearance only, canon in the <style> head comment; every behaviour below unchanged.
2026-09-23 deferred reading (hmi/deferral.py): a point whose warn is held off by a named, unfired trigger is
drawn grey with a pause glyph in a dashed ring - its own header count, a badge on its block icon, its trigger in the
faceplate - and never enters the alarm line, a slot, a stub colour or a card tint (ISA-101: not abnormal).
v1 behaviours kept: alarm line with click-through, snapshot-age heartbeat, memory-index enclosure with its
faces, sources row, view state in the URL hash (with a variable fallback where a hash cannot be set), Esc
closes, failures announce themselves.

    python tools/system-hmi/hmi.py collect && python tools/system-hmi/mimic_view.py   # -> out/mimic.html

Failure modes announce themselves: no snapshot -> the page says so; a script that does not parse or does
not reach its end -> the boot sentinel bar stays visible, and this generator's node --check exits 2;
a script error -> the same bar plus console.error; link drawing failure leaves the block icons readable.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TOOL = Path(__file__).resolve().parent
SNAP = TOOL / "out" / "snapshot.json"
GROUPS = TOOL / "registry" / "groups.json"
OUT = TOOL / "out" / "mimic.html"

PAGE = r"""<!doctype html>
<html lang="zh-Hant" data-page-class="dashboard" data-audience="user">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>system-hmi 總覽</title>
<style>
/* Softened 2026-09-23 (user: "clean but too rigid - make it rounder"). Canon for the softening, point by point:
   depth comes from layered surfaces + translucent borders and a shadow ONLY on what floats (the faceplate) -
   Siemens iX 5.2.1 (elevation page; --theme-shadow-4, --theme-color-soft-bdr, --theme-default-time 150ms);
   no gradients / 3D / decorative colour - ISA-101 unchanged; radius steps from the Material 3 shape scale
   (4/8/12/16/full) one notch above iX's 4 px, because rounder was the ask; nested radii are concentric
   (inner = outer - gap: card 10 -> slot 5, group 14 -> card 10); wires get round caps/joins and filleted corners. */
:root{--bg:#e3e6e9;--band:#eceef0;--panel:#f6f7f8;--edge:rgba(0,20,40,.15);--edge-std:rgba(0,20,40,.3);--ink:#23272b;--mute:#6b7278;
--norm:#8a9aa0;--slot:#e0e4e7;--fail:#c62828;--warn:#e08a00;--und:#b0188f;--line:#88919a;--hub:#38424b;
--r-card:10px;--r-in:5px;--r-big:14px;--t:.15s}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI","Microsoft JhengHei",Arial,sans-serif;font-variant-numeric:tabular-nums;
 display:grid;grid-template-rows:auto auto minmax(0,1fr) auto;height:100vh;overflow:hidden}
#err{background:var(--fail);color:#fff;padding:.4em 1em;font-size:14px;grid-row:1}
.g{display:inline-block;width:1em;height:1em;vertical-align:-.12em;flex:none}.g svg{width:100%;height:100%;display:block;overflow:visible}
.fp,.al,.run,.pt,.sc,.tab,#plate .x{transition:background-color var(--t),border-color var(--t),box-shadow var(--t),color var(--t)}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
/* header: title, the three counts, heartbeat */
#head{display:flex;align-items:center;gap:1.6vw;padding:.4em 1.2vw;background:var(--band);border-bottom:1px solid var(--edge);min-width:0}
#head .title{font-weight:600;font-size:18px;letter-spacing:.03em;white-space:nowrap}
.count{display:flex;align-items:center;gap:.35em;font-size:26px;font-weight:600;white-space:nowrap}
.count small{font-size:12px;font-weight:400;color:var(--mute)}
.count.dim{font-size:20px;font-weight:500;color:var(--mute)}   /* deferred: counted, not an alarm - smaller and grey */
.run{font:inherit;font-size:12px;padding:.2em .9em;border:1px solid var(--edge-std);border-radius:999px;background:#fff;color:var(--ink);cursor:pointer;white-space:nowrap}
.run:hover{background:var(--ink);border-color:var(--ink);color:#fff}.run[disabled]{opacity:.45;cursor:wait}
#ctl{display:flex;align-items:center;gap:.5em;font-size:12px;color:var(--mute);white-space:nowrap}
#msg{font-size:13px;padding:.15em .8em;border-radius:999px;display:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0}
#msg.busy{display:block;background:#fff;border:1px solid var(--edge)}#msg.bad{display:block;background:var(--warn);color:#fff}
#beat{margin-left:auto;font-size:13px;color:var(--mute);white-space:nowrap}#beat b{color:var(--ink)}
#beat.old{color:#fff;background:var(--und);padding:.15em .7em;border-radius:999px}#beat.old b{color:#fff}
/* alarm line */
#aline{display:flex;gap:.5vw;padding:.35em 1.2vw;background:var(--band);border-bottom:1px solid var(--edge);min-width:0;overflow:hidden;min-height:2.3em}
.al{display:flex;align-items:center;gap:.4em;font-size:13px;background:#fff;border:1px solid var(--edge);border-radius:999px;padding:.12em .8em .12em .6em;
 cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;flex:0 1 auto}
.al:hover{border-color:var(--edge-std);box-shadow:0 0 0 1px var(--edge-std)}.al.more{background:none;border-style:dashed;border-color:var(--edge-std);cursor:default;flex:none;color:var(--mute);box-shadow:none}
/* working area: system node + busbar on top, five columns of block icons below */
#work{position:relative;display:grid;grid-template-rows:auto minmax(0,1fr);padding:1vh 3vw 1vh;min-height:0;min-width:0}
#wires{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;z-index:0}
#top{display:flex;justify-content:center;padding-bottom:3.2vh;position:relative;z-index:1}
#sys{display:flex;align-items:center;gap:1em;background:var(--hub);color:#fff;padding:.4em 1.5em;border:3px solid var(--norm);border-radius:var(--r-big)}
#sys.s-fail{border-color:var(--fail)}#sys.s-warn{border-color:var(--warn)}#sys.s-und{border-color:var(--und)}
#sys .big{font-size:30px;font-weight:600;line-height:1}#sys .sm{font-size:13px;opacity:.85}
#cols{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:0 2vw;min-height:0;position:relative;z-index:1}
.col{display:flex;flex-direction:column;gap:2.6vh;min-height:0;min-width:0;padding-left:26px}
#grp{border:1.5px dashed rgba(35,39,43,.5);border-radius:calc(var(--r-card) + 6px);background:rgba(255,255,255,.34);padding:.4vh .4vw .6vh 0;display:flex;flex-direction:column;min-height:0;min-width:0}
#grp .gh{display:flex;align-items:center;gap:.5em;font-size:13px;font-weight:600;padding:0 0 .3vh 26px;min-width:0;flex-wrap:wrap}
#grp .faces{display:flex;gap:.7em;font-weight:400;font-size:12px;margin-left:auto}
#grp .face{display:flex;align-items:center;gap:.25em;white-space:nowrap}
#grp .col{flex:1}
/* block icon: name + worst state; group display (fixed slots); two worded lamps; coverage bar with its value.
   The state lamp (2026-09-23, user: "a light bar only in the middle") is a detached pill on the left edge,
   vertically centred and clear of the corners; an ABNORMAL card also takes a faint tint of its state colour
   (background ~7 %, border ~35 %) and a soft glow on the lamp. A normal card stays neutral - ISA-101 keeps
   colour for abnormal states only, and the lamp's colour is never the only cue (the glyph beside the name). */
.fp{--st:var(--norm);position:relative;flex:0 1 auto;min-height:0;background:var(--panel);border:1px solid var(--edge);border-radius:var(--r-card);
 padding:.5vh .65vw .55vh calc(.65vw + 8px);cursor:pointer;display:flex;flex-direction:column;gap:.7vh;overflow:hidden;min-width:0}
.fp::before{content:"";position:absolute;left:3px;top:24%;bottom:24%;width:4px;border-radius:999px;background:var(--st);opacity:.75}
.fp.s-fail{--st:var(--fail)}.fp.s-warn{--st:var(--warn)}.fp.s-und{--st:var(--und)}
.fp.s-fail,.fp.s-warn,.fp.s-und{background:color-mix(in srgb,var(--st) 7%,var(--panel));border-color:color-mix(in srgb,var(--st) 35%,transparent)}
.fp.s-fail::before,.fp.s-warn::before,.fp.s-und::before{opacity:1;box-shadow:0 0 6px 0 color-mix(in srgb,var(--st) 55%,transparent)}
.fp:hover{background:#fff;border-color:var(--edge-std)}
.fp.s-fail:hover,.fp.s-warn:hover,.fp.s-und:hover{background:color-mix(in srgb,var(--st) 5%,#fff);border-color:color-mix(in srgb,var(--st) 55%,transparent)}
.fp.sel{background:#fff;border-color:var(--ink);box-shadow:0 0 0 1px var(--ink)}
.fp.s-fail.sel,.fp.s-warn.sel,.fp.s-und.sel{background:color-mix(in srgb,var(--st) 5%,#fff);border-color:var(--ink)}
.fp .hd{display:flex;align-items:center;justify-content:space-between;gap:.4em;min-width:0}
.fp .nm{font-size:14px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fp .hd .g{font-size:18px}
.fp .hd .dfb{display:flex;align-items:center;gap:.2em;margin-left:auto;font-size:12px;color:var(--mute);flex:none}.fp .hd .dfb .g{font-size:13px}
.gd{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:4px}
.slot{display:flex;align-items:center;justify-content:center;gap:.3em;background:var(--slot);border-radius:var(--r-in);color:transparent;font-weight:600;font-size:13px;height:1.5em}
.slot .g{opacity:.28;font-size:13px}
.slot.on{color:#fff}.slot.on .g{opacity:1}
.slot.on.fail{background:var(--fail)}.slot.on.warn{background:var(--warn)}.slot.on.und{background:var(--und)}
.slot.on .g polygon,.slot.on .g circle{fill:#fff;stroke:#fff}.slot.on .g text{fill:var(--und)}
.two{display:flex;gap:1em;font-size:12px;color:var(--mute);white-space:nowrap;overflow:hidden}
.two span{display:flex;align-items:center;gap:.3em}.two .g{font-size:14px}
.cov{display:flex;align-items:center;gap:.5em;font-size:12px;color:var(--mute);white-space:nowrap}
.cov .bar{flex:1;height:8px;background:var(--slot);border-radius:999px;overflow:hidden;position:relative;min-width:0}
.cov .bar b{position:absolute;inset:0 auto 0 0;background:var(--norm);border-radius:999px}
.cov .bar i{position:absolute;top:0;bottom:0;width:1.5px;background:rgba(255,255,255,.8)}
.cov .v{color:var(--ink);font-weight:600;font-size:13px;min-width:2.6em;text-align:right}
/* short viewports (FHD at 150% scaling = 1280x~610): tighten, never clip */
@media (max-height:720px){.slot{height:1.25em;font-size:14px}.fp{gap:0;padding:.2vh .6vw .2vh calc(.6vw + 8px)}.fp .nm{font-size:14px}.fp .hd .g{font-size:17px}
 .col{gap:1.2vh}#top{padding-bottom:2.2vh}#sys .big{font-size:24px}.two,.cov{font-size:11px}.two .g{font-size:12px}#grp .gh{font-size:12px}}
/* faceplate (pop-up): views = state | coverage */
#plate{position:absolute;top:.8vh;bottom:1vh;width:40%;right:1.2vw;background:#fafbfb;border:1px solid var(--edge-std);border-radius:var(--r-big);overflow:hidden;z-index:5;display:none;
 flex-direction:column;box-shadow:0 0 2px 0 rgba(0,0,0,.2),0 4px 8px 0 rgba(0,0,0,.1),0 12px 18px 0 rgba(0,0,0,.1);min-width:0}
#plate.on{display:flex}#plate.left{right:auto;left:1.2vw}
#plate .ph{display:flex;align-items:center;gap:.6em;padding:.55em .7em .55em 1em;background:var(--hub);color:#fff}
#plate .ph b{font-size:16px;font-weight:600}#plate .ph code{font-size:12px;opacity:.75}
#plate .ph .run{border-color:rgba(255,255,255,.55);background:transparent;color:#fff}#plate .ph .run:hover{background:#fff;color:var(--ink)}
#plate .x{margin-left:auto;cursor:pointer;font-size:15px;line-height:1;padding:.3em .45em;border-radius:8px;border:1px solid rgba(255,255,255,.4)}
#plate .x:hover{background:rgba(255,255,255,.16);border-color:rgba(255,255,255,.7)}
#plate .tabs{display:flex;gap:4px;margin:.6em .9em .1em;padding:3px;border-radius:10px;background:var(--slot);align-self:flex-start}
#plate .tab{padding:.3em 1.1em;font-size:14px;cursor:pointer;border-radius:7px;color:var(--mute)}
#plate .tab:hover{color:var(--ink)}
#plate .tab.on{background:#fff;color:var(--ink);font-weight:600;box-shadow:0 1px 2px rgba(0,20,40,.18)}
#pbody{overflow:auto;padding:.6em .9em .9em;min-height:0;flex:1}
.cn{font-size:12px;color:var(--mute);margin:.8em 0 .2em;padding:0 .3em .15em;border-bottom:1px solid var(--edge);display:flex;justify-content:space-between;gap:.5em}
.cn:first-child{margin-top:0}
.pt{display:flex;align-items:center;gap:.45em;font-size:14px;padding:.22em .4em;border-radius:7px;cursor:pointer;min-width:0}
.pt span.a{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pt:hover,.pt.hl{background:#fff;box-shadow:0 0 0 1px var(--edge)}
.pt .st{margin-left:auto;font-size:11px;color:var(--mute);white-space:nowrap}
.ev{font-size:12.5px;color:#3c4349;margin:.2em 0 .6em 1.6em;display:none;word-break:break-word;background:rgba(0,20,40,.035);border-radius:8px;padding:.45em .7em}
.ev.on{display:block}.ev code{color:var(--mute)}
.sum{font-size:14px;margin-bottom:.7em}.sum b{font-size:22px;font-weight:600}
.cr{margin-bottom:.55em}.cr .rh{display:flex;align-items:center;gap:.5em;font-size:14px;cursor:pointer;padding:.15em .3em;border-radius:7px}
.cr .rh:hover{background:#fff}
.cr .rh .bar{flex:0 0 30%;height:8px;background:var(--slot);border-radius:999px;overflow:hidden;position:relative}.cr .rh .bar b{position:absolute;inset:0 auto 0 0;background:var(--norm);border-radius:999px}
.cr .rh .n{margin-left:auto;font-size:13px;white-space:nowrap}.cr .rh .n b{color:var(--warn)}
.cr .why{font-size:12px;color:var(--mute);margin-left:1.8em}
.cr ul{display:none;margin:.25em 0 .2em 1.8em;padding-left:1em;font-size:12.5px;columns:2}.cr.open ul{display:block}
.nop{font-size:13px;color:var(--mute)}
/* footer: reading sources + legend */
#foot{display:flex;gap:.6vw;padding:.35em 1.2vw;background:var(--band);border-top:1px solid var(--edge);font-size:12px;align-items:center;min-width:0;white-space:nowrap}
#foot .lab{color:var(--mute);flex:none}.sc{display:flex;align-items:center;gap:.3em;background:#fff;border:1px solid var(--edge);border-radius:999px;padding:.1em .7em .1em .5em;flex:none}
#srcs{display:flex;gap:.5vw;min-width:0;overflow:hidden;flex:1}
#legend{flex:none;display:flex;gap:.9em;color:var(--mute)}#legend span{display:flex;align-items:center;gap:.25em}
</style></head>
<body>
<div id="err">畫面程式沒有執行（語法錯誤或被瀏覽器擋下）— 這不是「全部正常」。請重跑 mimic_view.py 並看它的輸出。</div>
<div id="head"><span class="title">~/.claude 系統總覽</span>
 <span class="count" id="cF"></span><span class="count" id="cW"></span><span class="count" id="cU"></span><span class="count dim" id="cD"></span><span id="msg"></span><div id="beat"></div><span id="ctl"></span></div>
<div id="aline"></div>
<div id="work"><svg id="wires"></svg>
 <div id="top"><div id="sys"><span class="big" id="sysN"></span><span class="sm" id="sysT"></span></div></div>
 <div id="cols"><div class="col" id="c0"></div><div class="col" id="c1"></div>
  <div id="grp"><div class="gh"><span id="grpT"></span><span class="faces" id="faces"></span></div><div class="col" id="cG"></div></div>
  <div class="col" id="c2"></div><div class="col" id="c3"></div></div>
 <div id="plate"><div class="ph"><span id="pG"></span><b id="pT"></b><code id="pI"></code><span id="pRun" style="margin-left:auto"></span><span class="x" data-close="1" style="margin-left:.6em" title="關閉 (Esc)">✕</span></div>
  <div class="tabs"><span class="tab" data-view="state">警報與狀態</span><span class="tab" data-view="cov">監看覆蓋</span></div><div id="pbody"></div></div>
</div>
<div id="foot"><span class="lab">讀值來源</span><span id="srcs"></span><span id="legend"></span></div>
<script>
const SNAP=/*SNAP*/null, GROUPS=/*GROUPS*/null, LIVE=/*LIVE*/null;
function runBtn(k,v,label){return LIVE?' <button class="run" data-run="'+k+'" data-val="'+esc(v)+'">'+label+'</button>':'';}
const ORDER={fail:0,warn:1,und:2,def:3,pass:4,none:5};
const CRIT=[['C1','已登錄','登錄表裡有這個元件'],['C2','有對帳點在看','有監看點核對「登錄的」和「磁碟上的」是否一致'],
 ['C3','有健全點在看','有監看點檢查它的功能是否完好'],['C4','有自我測試','元件自己帶測試，且測試有在跑'],['C5','HMI 以外也有機制在看','排程、hook 或其他工具也在看它，不是只有這個畫面']];
function fatal(m){const e=document.getElementById('err');e.style.display='block';e.textContent='畫面產生失敗：'+m;console.error('[mimic_view]',m);}
function glyph(s){const c={fail:'var(--fail)',warn:'var(--warn)',und:'var(--und)',def:'var(--mute)',pass:'var(--norm)',none:'var(--norm)'}[s];
 const rj=' stroke="'+c+'" stroke-width="2" stroke-linejoin="round"';   /* same shape, softened vertices */
 const sh={fail:'<polygon points="2,2.8 14,2.8 8,14" fill="'+c+'"'+rj+'/>',warn:'<polygon points="8,1.6 14.4,8 8,14.4 1.6,8" fill="'+c+'"'+rj+'/>',
 und:'<circle cx="8" cy="8" r="7" fill="'+c+'"/><text x="8" y="12" font-size="11" text-anchor="middle" fill="#fff" font-weight="700">?</text>',
 /* deferred = "on hold": pause bars inside a dashed ring, grey - a shape cue, never an alarm colour */
 def:'<circle cx="8" cy="8" r="6.6" fill="none" stroke="'+c+'" stroke-width="1.4" stroke-dasharray="2.6 1.6"/><rect x="5.2" y="4.8" width="2" height="6.4" rx=".8" fill="'+c+'"/><rect x="8.8" y="4.8" width="2" height="6.4" rx=".8" fill="'+c+'"/>',
 pass:'<circle cx="8" cy="8" r="6" fill="none" stroke="'+c+'" stroke-width="2.5"/>',none:'<circle cx="8" cy="8" r="6" fill="none" stroke="'+c+'" stroke-width="1.5" stroke-dasharray="3 2"/>'}[s];
 return '<span class="g"><svg viewBox="0 0 16 16">'+sh+'</svg></span>';}
function hold(p){const d=(p.reading||{}).deferral;return !!(d&&d.status==='holding');}
function pst(p){const r=p.reading||{};if(r.state==='pass'&&hold(p))return 'def';if(r.state==='pass'||r.state==='warn'||r.state==='fail')return r.state;return 'und';}
function worst(a){return a.length?a.slice().sort((x,y)=>ORDER[x]-ORDER[y])[0]:'none';}
function nz(s){return (s==='pass'||s==='warn'||s==='fail')?s:(s==null?'none':'und');}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function base(id){const p=String(id).replace(/\/+$/,'').split('/');return p[p.length-1]||id;}
try{
 if(!SNAP) throw new Error('沒有快照資料；請先執行 hmi.py collect 再重產');
 const subs=SNAP.subsystems, comps=SNAP.components, pts=SNAP.points, grp=(SNAP.groups||[])[0], greg=(GROUPS||[])[0]||{};
 const ptsOf={}, compBy={};
 pts.forEach(p=>{(ptsOf[p.subsystem]=ptsOf[p.subsystem]||[]).push(p);});
 comps.forEach(c=>{(compBy[c.subsystem]=compBy[c.subsystem]||[]).push(c);});
 const $=id=>document.getElementById(id);
 function subWorst(s){const own=worst([nz(s.r_state),nz(s.i_state)].filter(x=>x!=='none')), pw=worst((ptsOf[s.id]||[]).map(pst));
  return ORDER[own]<=ORDER[pw]?own:(pw==='pass'?own:pw);}
 /* coverage: met criteria / applicable criteria over the subsystem's components (null = not applicable) */
 function coverage(id){const cs=compBy[id]||[];let met=0,app=0;const miss={};CRIT.forEach(k=>miss[k[0]]=[]);const appl={};CRIT.forEach(k=>appl[k[0]]=0);
  cs.forEach(c=>{const cm=c.completeness||{};CRIT.forEach(k=>{const v=cm[k[0]];if(v===true){met++;app++;appl[k[0]]++;}else if(v===false){app++;appl[k[0]]++;miss[k[0]].push(c.id);}});});
  return {met,app,miss,appl,n:cs.length,pct:app?Math.round(100*met/app):null};}
 /* ---- header + alarm line */
 const n=s=>pts.filter(p=>pst(p)===s).length;
 $('cF').innerHTML=glyph('fail')+n('fail')+'<small>失敗</small>';$('cW').innerHTML=glyph('warn')+n('warn')+'<small>警告</small>';$('cU').innerHTML=glyph('und')+n('und')+'<small>未判定</small>';
 $('cD').innerHTML=glyph('def')+n('def')+'<small>延後</small>';$('cD').title='刻意延後、有具名觸發條件且尚未觸發的監看點：不是警報，觸發後會自動變回警告';
 const abn=pts.filter(p=>pst(p)==='fail'||pst(p)==='warn').sort((a,b)=>ORDER[pst(a)]-ORDER[pst(b)]), SHOW=6;
 $('aline').innerHTML=abn.slice(0,SHOW).map(p=>'<span class="al" data-sub="'+esc(p.subsystem)+'" data-pt="'+esc(p.id)+'" title="'+esc(p.id)+'">'+glyph(pst(p))+esc(p.alias||p.id)+'</span>').join('')
  +(abn.length>SHOW?'<span class="al more">另有 '+(abn.length-SHOW)+' 筆</span>':'')+(abn.length?'':'<span class="al more">沒有警報</span>');
 const fin=Date.parse(SNAP.run.finished_at), age=Math.round((Date.now()-fin)/60000);
 $('beat').innerHTML='快照 <b>'+(age<90?age+' 分鐘':age<2880?Math.round(age/60)+' 小時':Math.round(age/1440)+' 天')+'</b> 前';
 if(age>1440) $('beat').className='old';
 /* ---- block icons */
 function icon(s){const ps=ptsOf[s.id]||[], w=subWorst(s), cv=coverage(s.id), c=k=>ps.filter(p=>pst(p)===k).length;
  const slot=k=>{const v=c(k);return '<span class="slot '+k+(v?' on':'')+'">'+glyph(k)+(v||'')+'</span>';};
  const nd=c('def'), dfb=nd?'<span class="dfb" title="'+nd+' 個監看點延後中（觸發條件未成立，不是警報）">'+glyph('def')+nd+'</span>':'';
  return '<div class="fp s-'+w+'" data-sub="'+esc(s.id)+'" data-w="'+w+'" title="'+esc(s.id)+'"><div class="hd"><span class="nm">'+esc(s.title_zh||s.id)+'</span>'+dfb+glyph(w)+'</div>'
   +'<div class="gd">'+slot('fail')+slot('warn')+slot('und')+'</div>'
   +'<div class="two"><span>'+glyph(nz(s.r_state))+'登錄對帳</span><span>'+glyph(nz(s.i_state))+'功能健全</span></div>'
   +'<div class="cov" data-sub="'+esc(s.id)+'" data-view="cov" title="點開看缺哪幾項"><span>監看覆蓋</span><span class="bar"><b style="width:'+(cv.pct||0)+'%"></b>'
   +[20,40,60,80].map(x=>'<i style="left:'+x+'%"></i>').join('')+'</span><span class="v">'+(cv.pct==null?'—':cv.pct+'%')+'</span></div></div>';}
 const inGrp=new Set(Object.keys((greg.subsystems)||{}));
 const rest=subs.filter(s=>!inGrp.has(s.id)), gs=subs.filter(s=>inGrp.has(s.id)), per=Math.ceil(rest.length/4);
 [0,1,2,3].forEach(i=>{$('c'+i).innerHTML=rest.slice(i*per,(i+1)*per).map(icon).join('');});
 $('cG').innerHTML=gs.map(icon).join('');
 if(grp){$('grpT').textContent=grp.title_zh;$('faces').innerHTML=Object.keys(grp.faces).sort().map(k=>{const f=grp.faces[k], en=String(f.title||k).split(/\s+/)[0], t=({inventory:'盤點',memory:'記憶',retrieval:'檢索',awareness:'覺察'})[en]||en;
   return '<span class="face" title="'+esc(f.title)+'">'+glyph(worst([nz(f.r_state),nz(f.i_state)].filter(x=>x!=='none')))+esc(t)+'</span>';}).join('');}
 else $('grp').style.border='none';
 const bad=subs.filter(s=>['fail','warn'].includes(subWorst(s))).length;
 $('sys').className='s-'+worst(subs.map(subWorst));$('sysN').textContent=bad+' / '+subs.length;$('sysT').textContent='子系統異常';
 /* ---- footer */
 const sm={};
 pts.forEach(p=>{const k=p.adapter==='native'?((p.reading||{}).source||'?'):'其他轉接';(sm[k]=sm[k]||[]).push(pst(p));});
 $('srcs').innerHTML=Object.keys(sm).sort((a,b)=>sm[b].length-sm[a].length).map(k=>{const u=sm[k].filter(x=>x==='und').length;
  return '<span class="sc" title="'+u+' 個點沒有讀值">'+glyph(u===sm[k].length?'fail':u?'und':'pass')+esc(k)+' <b>'+sm[k].length+'</b></span>';}).join('');
 $('legend').innerHTML=[['fail','失敗'],['warn','警告'],['und','未判定／沒跑'],['def','延後（等觸發）'],['pass','正常'],['none','沒人在看']].map(x=>'<span>'+glyph(x[0])+x[1]+'</span>').join('');
 /* ---- faceplate */
 function stateView(s,hl){const ps=ptsOf[s.id]||[], by={};ps.forEach(p=>{(by[p.component]=by[p.component]||[]).push(p);});
  const keys=Object.keys(by).sort((a,b)=>ORDER[worst(by[a].map(pst))]-ORDER[worst(by[b].map(pst))]);
  const watched=new Set(keys), blind=(compBy[s.id]||[]).filter(c=>!watched.has(c.id)).length;
  return (keys.length?keys.map(k=>'<div class="cn"><span title="'+esc(k)+'">'+esc(base(k))+'</span><span>'+by[k].length+' 點</span></div>'
    +by[k].slice().sort((a,b)=>ORDER[pst(a)]-ORDER[pst(b)]).map(p=>{const r=p.reading||{}, d=r.deferral||null, h=hold(p);
     /* a holding deferral names its trigger and hides the remedy it defers; a fired or rejected one says so beside the warn */
     const dl=!d?'':h?'<br><b>延後中：</b>觸發條件「'+esc(d.trigger)+'」尚未成立（'+(d.kind==='probe'?'機器每次收集時檢查':'人工判斷，觸發時由人改記錄')+'）。原始讀值：警告 — '+esc(d.raw_evidence)+(d.ruling?'<br><b>裁示：</b>'+esc(d.ruling):'')
      :d.status==='fired'?'<br><b>延後已結束：</b>觸發條件「'+esc(d.trigger)+'」已成立，所以回到警告。'
      :'<br><b>延後沒有生效：</b>'+esc(d.reason||'');
     const rem=h?'<br><b>處置：</b>目前不用做；觸發條件成立後才處理':((r.remedy&&r.remedy!=='None')||p.remedy?'<br><b>處置：</b>'+esc((r.remedy&&r.remedy!=='None')?r.remedy:p.remedy):'');
     return '<div class="pt'+(p.id===hl?' hl':'')+'" data-ev="1">'+glyph(pst(p))+'<span class="a">'+esc(p.alias||p.id)+'</span><span class="st">'+(h?'延後 · ':'')+(p.class==='integrity'?'功能健全':'登錄對帳')+'</span></div>'
      +'<div class="ev'+(p.id===hl?' on':'')+'">'+esc(p.why||'')+(h?'':'<br>'+esc(r.evidence||r.skip_reason||''))+dl+rem+'<br><code>'+esc(p.id)+'</code>'+runBtn('point_id',p.id,'重跑這個檢查')+'</div>';}).join('')).join('')
    :'<div class="nop">這個子系統沒有任何監看點。</div>')
   +(blind?'<div class="cn"><span>沒有監看點的元件</span><span>'+blind+' 個</span></div><div class="nop">清單在「監看覆蓋」分頁。</div>':'');}
 function covView(s){const cv=coverage(s.id);
  if(!cv.app) return '<div class="nop">這個子系統沒有可評分的元件。</div>';
  return '<div class="sum">監看覆蓋 <b>'+cv.pct+'%</b>　=　符合 '+cv.met+' 項 ÷ 應符合 '+cv.app+' 項（'+cv.n+' 個元件 × 最多 5 項）</div>'
   +CRIT.map(k=>{const m=cv.miss[k[0]], a=cv.appl[k[0]], ok=a-m.length;
    return '<div class="cr'+(m.length&&m.length<=12?' open':'')+'"><div class="rh" data-tog="1">'+glyph(m.length?'warn':'pass')+'<span>'+k[1]+'</span><span class="bar"><b style="width:'+(a?100*ok/a:0)+'%"></b></span>'
     +'<span class="n">'+ok+' / '+a+(m.length?'　<b>缺 '+m.length+'</b>':'')+'</span></div><div class="why">'+k[2]+'</div>'
     +(m.length?'<ul>'+m.map(x=>'<li title="'+esc(x)+'">'+esc(base(x))+'</li>').join('')+'</ul>':'')+'</div>';}).join('');}
 function openPlate(id,view,hl){const s=subs.find(x=>x.id===id), pl=$('plate');
  document.querySelectorAll('.fp.sel').forEach(f=>f.classList.remove('sel'));
  if(!s){pl.classList.remove('on');return;}
  const f=document.querySelector('.fp[data-sub="'+CSS.escape(id)+'"]');
  if(f){f.classList.add('sel');const r=f.getBoundingClientRect();pl.classList.toggle('left',(r.left+r.width/2)>innerWidth*.56);}
  $('pG').innerHTML=glyph(subWorst(s));$('pT').textContent=s.title_zh||s.id;$('pI').textContent=s.id;$('pRun').innerHTML=runBtn('subsystem_id',s.id,'重跑這個子系統');
  document.querySelectorAll('#plate .tab').forEach(t=>{t.classList.toggle('on',t.dataset.view===view);t.dataset.sub=id;});
  $('pbody').innerHTML=view==='cov'?covView(s):stateView(s,hl);pl.classList.add('on');
  const h=$('pbody').querySelector('.hl');if(h) h.scrollIntoView({block:'center'});}
 /* ---- view state: the URL hash is its home; VIEW is the fallback where a hash cannot be set */
 let VIEW='';
 function go(v){VIEW=v;try{location.hash=v;}catch(x){} route();}
 function route(){const hs=(location.hash||'').replace(/^#/,''), src=(hs===VIEW||!VIEW&&hs)?hs:VIEW;
  const m=/sub=([^&]+)/.exec(src), v=/view=([^&]+)/.exec(src), h=/pt=([^&]+)/.exec(src);
  openPlate(m?decodeURIComponent(m[1]):null, v&&v[1]==='cov'?'cov':'state', h&&decodeURIComponent(h[1]));}
 /* ---- live mode: re-run read-only probes through the local service; static file says why it cannot */
 let busy=false;
 function say(cls,t){const m=$('msg');m.className=cls;m.textContent=t;}
 function refresh(k,v){if(busy||!LIVE)return;busy=true;const t0=Date.now();
  document.querySelectorAll('.run').forEach(b=>b.disabled=true);
  const tick=setInterval(()=>say('busy','收集中… '+Math.round((Date.now()-t0)/1000)+' 秒（不能取消，完成後畫面自動更新）'),500);
  const done=(cls,t)=>{clearInterval(tick);busy=false;document.querySelectorAll('.run').forEach(b=>b.disabled=false);say(cls,t);};
  const body={token:LIVE.token};body[k]=v;
  fetch('/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
   .then(r=>r.json().then(j=>({s:r.status,j})))
   .then(x=>{if(x.s===200){clearInterval(tick);location.reload();}
    else if(x.s===409) done('bad','另一個收集正在跑，稍後再按：'+(x.j.detail||''));
    else {console.error('[mimic_view] refresh failed',x);done('bad','重跑失敗（'+x.s+'）：'+(x.j.detail||x.j.error||''));}})
   .catch(e=>{console.error('[mimic_view] service unreachable',e);done('bad','本機服務沒有回應 — 請從桌面捷徑「系統監看（可重跑）」重新開啟');});}
 if(LIVE){$('ctl').innerHTML=runBtn('tier','cheap','重新收集')+runBtn('tier','full','完整收集（慢）');
  setInterval(()=>{if(busy)return;fetch('/api/meta').then(r=>r.json()).then(j=>{if(j.finished_at&&j.finished_at!==SNAP.run.finished_at) location.reload();
    else if(j.code&&j.disk&&j.code!==j.disk) say('bad','畫面程式已更新，這個服務還是舊版 — 從桌面捷徑「系統監看（可重跑）」重新開啟即換成新版');
    else if($('msg').dataset.lost){delete $('msg').dataset.lost;say('','');}})
   .catch(()=>{$('msg').dataset.lost='1';say('bad','本機服務沒有回應 — 畫面停在上次快照');});},20000);}
 else $('ctl').innerHTML='<span title="這是靜態檔，不能重跑檢查。要能重跑，請用桌面捷徑「系統監看（可重跑）」開啟">靜態檔 · 不能重跑</span>';
 document.addEventListener('click',e=>{const t=e.target.closest('[data-run],[data-close],[data-tog],[data-ev],[data-sub]');if(!t)return;
  if(t.dataset.run) refresh(t.dataset.run,t.dataset.val);
  else if(t.dataset.close) go('');
  else if(t.dataset.tog) t.parentNode.classList.toggle('open');
  else if(t.dataset.ev){const x=t.nextElementSibling;if(x) x.classList.toggle('on');}
  else go('sub='+encodeURIComponent(t.dataset.sub)+(t.dataset.view?'&view='+t.dataset.view:'')+(t.dataset.pt?'&pt='+encodeURIComponent(t.dataset.pt):''));});
 document.addEventListener('keydown',e=>{if(e.key==='Escape') go('');});
 window.addEventListener('hashchange',()=>{VIEW=(location.hash||'').replace(/^#/,'');route();});
 window.addEventListener('resize',()=>requestAnimationFrame(wire));
 /* ---- links: busbar under the system node, one riser per column, one stub per block icon.
    Every L-shaped corner (bus ends, a riser's last stub) is filleted with radius R; T-junctions keep their dot. */
 function wire(){try{const svg=$('wires'), box=$('work').getBoundingClientRect(), sy=$('sys').getBoundingClientRect();
  const X=v=>Math.round(v-box.left)+.5, Y=v=>Math.round(v-box.top)+.5, N='var(--line)', R=9;
  const P=(d,col,w,extra)=>'<path d="'+d+'" stroke="'+col+'" stroke-width="'+w+'" fill="none" stroke-linecap="round" stroke-linejoin="round"'+(extra||'')+'/>';
  const colsEl=[...document.querySelectorAll('#cols .col')], first=$('cols').getBoundingClientRect();
  const busY=Y((sy.bottom+first.top)/2), sx=X(sy.left+sy.width/2);
  const cols=colsEl.map(c=>{const fps=[...c.querySelectorAll('.fp')];return fps.length?{fps,rx:X(c.getBoundingClientRect().left+11)}:null;}).filter(Boolean);
  if(!cols.length){svg.innerHTML='';return;}
  const xs=cols.map(c=>c.rx), x0=Math.min.apply(null,xs), x1=Math.max.apply(null,xs);
  let out=P('M'+x0+' '+(busY+R)+' Q'+x0+' '+busY+' '+(x0+R)+' '+busY+' H'+(x1-R)+' Q'+x1+' '+busY+' '+x1+' '+(busY+R),N,4)
   +P('M'+sx+' '+Y(sy.bottom)+' V'+busY,N,4);
  cols.forEach(({fps,rx})=>{const top=(rx===x0||rx===x1)?busY+R:busY;
   fps.forEach((f,i)=>{const r=f.getBoundingClientRect(), y=Y(r.top+r.height/2), w=f.dataset.w, hot=(w==='fail'||w==='warn'||w==='und'), last=i===fps.length-1;
    const col={fail:'var(--fail)',warn:'var(--warn)',und:'var(--und)'}[w]||N, sx0=last?rx+R:rx;
    if(last) out=P('M'+rx+' '+top+' V'+Math.max(top,y-R)+' Q'+rx+' '+y+' '+(rx+R)+' '+y,N,2)+out;
    out+=P('M'+sx0+' '+y+' H'+X(r.left),col,hot?4:2,w==='und'?' stroke-dasharray="1.5 7"':'')
     +((!last||hot)?'<circle cx="'+sx0+'" cy="'+y+'" r="'+(hot?5:3.5)+'" fill="'+col+'"/>':'');});});
  svg.innerHTML=out;}catch(x){console.error('[mimic_view] links not drawn',x);}}
 route();requestAnimationFrame(wire);
 document.getElementById('err').style.display='none';
}catch(x){fatal(x.message||String(x));}
</script></body></html>
"""


def script_parses(doc):
    """True / False / None (undetermined: no node on PATH). A parse error kills the whole inline script, so the
    page would show nothing at all; the boot sentinel makes that visible, this check catches it at build time."""
    node = shutil.which("node")
    body = doc.split("<script>", 1)[1].rsplit("</script>", 1)[0]
    if not node:
        print("mimic_view: script syntax NOT checked (node not found) - undetermined, open the page to see", file=sys.stderr)
        return None
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "mimic.js"
        f.write_text(body, encoding="utf-8")
        r = subprocess.run([node, "--check", str(f)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print("mimic_view: inline script does NOT parse - the page would be blank:", file=sys.stderr)
        print(r.stderr[-600:], file=sys.stderr)
        return False
    return True


def render(snap, groups, live=None):
    """The page as a string. live = {"token": ...} when served by hmi/server.py (refresh controls on);
    None for the static file (controls replaced by a line saying why)."""
    def inline(obj):   # "</" must not appear inside a <script> block
        return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")

    return (PAGE.replace("/*SNAP*/null", inline(snap)).replace("/*GROUPS*/null", inline(groups))
            .replace("/*LIVE*/null", inline(live)))


def main():
    try:
        snap = json.loads(SNAP.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        snap = None
        print(f"mimic_view: snapshot unreadable ({exc}); the page will say so", file=sys.stderr)
    try:
        groups = json.loads(GROUPS.read_text(encoding="utf-8"))
        groups = groups if isinstance(groups, list) else groups.get("groups", [])
    except (OSError, ValueError):
        groups = []

    doc = render(snap, groups)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(doc, encoding="utf-8")
    if script_parses(doc) is False:
        return 2
    print(str(OUT), time.strftime("%H:%M:%S"))
    return 0 if snap else 1


if __name__ == "__main__":
    sys.exit(main())
