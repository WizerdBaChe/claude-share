// tools/archdiag/emit.mjs — SVG + page emission for archdiag deliverables.
// Extracted (S1, 2026-08-29) from dit-audit-f1.build.mjs v1.1 ∪
// prism-audit-f2.build.mjs; the blocks below are byte-faithful cuts from
// those sources so regeneration stays receipt-stable. Single normalization
// applied at extraction: the node <rect> no longer leaves a stray space
// before "/>" when the overlay flag is off (keeps F1 v1.1 byte-identical;
// F2 absorbed the whitespace change in its v1.1 bump).
// Emission invariant: pageHtml is deterministic — identical model + doc
// strings => identical bytes (receipt-friendly). Doc strings (title/h1/
// legendbar/footerNote/section h2s) are trusted raw text/HTML from the
// build script; view-model strings go through esc().

import { inPageScript } from './selfcheck.mjs';

// ---------- shared styling (single source; F2 superset: ov + absent) ----------
const FILL = { block: '#dbeafe', ext: '#e2e8f0', store: '#fef3c7', state: '#dcfce7', proc: '#dbeafe', port: '#ede9fe' };
const STROKE = { block: '#2563eb', ext: '#64748b', store: '#b45309', state: '#16a34a', proc: '#2563eb', port: '#7c3aed' };
const OVL = { fill: '#ffedd5', stroke: '#ea580c' }; // branch-only overlay (un-accepted)
const EDGE = {
  call:  { stroke: '#64748b', dash: '', marker: 'mOpen' },   // synchronous call / import
  data:  { stroke: '#0f172a', dash: '', marker: 'mFill' },   // data flow
  proto: { stroke: '#0369a1', dash: '', marker: 'mProto' },  // async protocol (SSE / event)
  egress:{ stroke: '#b91c1c', dash: '', marker: 'mEgr' },    // leaves the process boundary
  warn:  { stroke: '#b91c1c', dash: '6 4', marker: 'mEgr' }, // error flow (dual-coded)
  trans: { stroke: '#0f172a', dash: '', marker: 'mFill' },   // FSM transition
  eps:   { stroke: '#7c3aed', dash: '5 4', marker: 'mEps' }, // automatic transition
  absent:{ stroke: '#94a3b8', dash: '2 3', marker: null },   // contractual NON-dependency (ADR-16)
};

// ---------- text helpers ----------
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const cjkW = (s, px) => [...s].reduce((w, ch) => w + (ch.charCodeAt(0) > 255 ? px : px * 0.55), 0);

// ---------- node/view SVG (F2 superset: ov overlay + badge, absent ✕,
// multi-inits, optional container titles / lifeline containers) ----------
function nodeSvg(n) {
  const kind = n.kind === 'stateT' ? 'state' : n.kind;
  const rx = (n.kind === 'state' || n.kind === 'stateT') ? 16 : n.kind === 'ext' ? n.h / 2 : 6;
  const fill = n.ov ? OVL.fill : FILL[kind];
  const stroke = n.ov ? OVL.stroke : STROKE[kind];
  let s = `<g class="node" data-id="${n.id}" data-x="${n.x}" data-y="${n.y}" data-w="${n.w}" data-h="${n.h}" data-kind="${n.kind}">`;
  s += `<rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="${rx}" fill="${fill}" stroke="${stroke}" stroke-width="1.5"${n.ov ? ' stroke-dasharray="6 4"' : ''}/>`;
  if (n.kind === 'stateT') s += `<rect x="${n.x + 4}" y="${n.y + 4}" width="${n.w - 8}" height="${n.h - 8}" rx="12" fill="none" stroke="${STROKE.state}" stroke-width="1.2"/>`;
  const cx = n.kind === 'ext' ? n.x + n.w / 2 : n.x + 12;
  const anchor = n.kind === 'ext' ? 'middle' : 'start';
  s += `<text class="lbl" x="${cx}" y="${n.y + 20}" font-size="13" font-weight="700" fill="#0f172a" text-anchor="${anchor}">${esc(n.t)}</text>`;
  if (n.ov) s += `<text class="lbl" x="${n.x + n.w - 8}" y="${n.y + n.h - 8}" font-size="11" font-weight="700" fill="#c2410c" text-anchor="end">未驗收</text>`;
  if (n.l?.length) {
    const tspans = n.l.map((ln, i) => `<tspan x="${cx}" y="${n.y + 38 + i * 15}">${esc(ln)}</tspan>`).join('');
    s += `<text class="lbl" font-size="11" fill="#334155" text-anchor="${anchor}">${tspans}</text>`;
  }
  return s + '</g>';
}

function viewSvg(v) {
  let s = [];
  for (const c of v.containers || []) {
    s.push(`<rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" rx="12" fill="#f8fafc" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="8 5" class="comp" data-id="${c.id}" data-x="${c.x}" data-y="${c.y}" data-w="${c.w}" data-h="${c.h}"/>`);
    if (c.title) s.push(`<text class="lbl" x="${c.x + 14}" y="${c.y + 22}" font-size="12" font-weight="600" fill="#475569">${esc(c.title)}</text>`);
  }
  for (const e of v.edges) {
    const st = EDGE[e.type];
    const d = e.pts.map((p, i) => (i ? 'L' : 'M') + p[0] + ' ' + p[1]).join(' ');
    s.push(`<path d="${d}" fill="none" stroke="${st.stroke}" stroke-width="1.6" ${st.dash ? `stroke-dasharray="${st.dash}"` : ''} ${st.marker ? `marker-end="url(#${st.marker})"` : ''} class="edge" data-edge="${e.id}" data-from="${e.from}" data-to="${e.to}" data-pts="${e.pts.flat().join(',')}" ${e.fromComp ? 'data-fromcomp="1"' : ''} ${e.selfLoop ? 'data-selfloop="1"' : ''}/>`);
    if (e.type === 'absent') { // contractual non-dependency: ✕ at first-segment midpoint
      const mx = (e.pts[0][0] + e.pts[1][0]) / 2, my = (e.pts[0][1] + e.pts[1][1]) / 2;
      s.push(`<path d="M${mx - 5} ${my - 5} L${mx + 5} ${my + 5} M${mx - 5} ${my + 5} L${mx + 5} ${my - 5}" stroke="#64748b" stroke-width="1.8" fill="none"/>`);
    }
  }
  s.push(`<metadata data-declared-crossings="${v.declaredCrossings || 0}"></metadata>`);
  for (const init of v.inits || (v.init ? [v.init] : [])) {
    s.push(`<circle cx="${init.at[0]}" cy="${init.at[1]}" r="7" fill="#0f172a"/>`);
    s.push(`<path d="M${init.at[0] + 7} ${init.at[1]} L${init.to[0]} ${init.to[1]}" stroke="#0f172a" stroke-width="1.6" marker-end="url(#mFill)"/>`);
  }
  for (const n of v.nodes) s.push(nodeSvg(n));
  for (const e of v.edges) {
    if (!e.pill) continue;
    const w = Math.ceil(cjkW(e.pill, 11)) + 12;
    const [px, py] = e.pillAt;
    s.push(`<rect class="pillbg" x="${px - w / 2}" y="${py - 9}" width="${w}" height="18" rx="9" fill="#ffffff" stroke="#cbd5e1" stroke-width="0.8"/>`);
    s.push(`<text class="lbl" x="${px}" y="${py + 4}" font-size="11" fill="#334155" text-anchor="middle">${esc(e.pill)}</text>`);
  }
  return s.join('\n');
}

export { FILL, STROKE, OVL, EDGE, esc, cjkW, nodeSvg, viewSvg };

// ---------- marker defs (single source; build-time closure in index.mjs:
// every EDGE marker must resolve here — determinable face of check #8) ----------
export const DEFS = `<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<marker id="mOpen" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M1 1 L9 5 L1 9" fill="none" stroke="#64748b" stroke-width="1.6"/></marker>
<marker id="mFill" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#0f172a"/></marker>
<marker id="mProto" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M1 1 L9 5 L1 9" fill="none" stroke="#0369a1" stroke-width="1.6"/></marker>
<marker id="mEgr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#b91c1c"/></marker>
<marker id="mEps" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M1 1 L9 5 L1 9" fill="none" stroke="#7c3aed" stroke-width="1.6"/></marker>
</defs></svg>`;

// ---------- page assembly ----------
export function pageHtml({ grid = 8, doc, views, sections, selfcheckNotes }) {
  const tabs = views.map((v, i) => `<button class="tab${i === 0 ? ' on' : ''}" data-tab="${v.id}">${esc(v.title)}</button>`).join('');
  const panes = views.map((v, i) => `
<section class="pane${i === 0 ? ' on' : ''}" id="pane-${v.id}">
  <p class="note">${esc(v.subtitle)}　宣告：${v.declared.map(esc).join('；')}</p>
  <svg class="dia" data-view="${v.id}" viewBox="0 0 ${v.vb[0]} ${v.vb[1]}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${esc(v.title)}">
    <g class="scene">${viewSvg(v)}</g>
  </svg>
</section>`).join('\n');
  const sectionHtml = sections.map((s) => `  <h2>${s.h2}</h2>${s.html}`).join('\n');
  const script = inPageScript({ grid, viewCount: views.length, notes: selfcheckNotes });
  return `<!doctype html>
<html lang="${doc.lang || 'zh-Hant'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${doc.title}</title>
<style>
  :root { color-scheme: light; }
  body { margin: 0; background: #fff; color: #0f172a; font-family: "Segoe UI", "Noto Sans TC", system-ui, sans-serif; }
  header { display: flex; gap: 8px; align-items: center; padding: 10px 16px; border-bottom: 1px solid #e2e8f0; flex-wrap: wrap; }
  header .sp { flex: 1; }
  .tab { font: inherit; font-size: 13px; padding: 6px 12px; border-radius: 8px; border: 1px solid #cbd5e1; background: #f8fafc; cursor: pointer; }
  .tab.on { background: #1d4ed8; color: #fff; border-color: #1d4ed8; }
  #geoStatus { font-size: 13px; padding: 4px 10px; border-radius: 8px; }
  #geoStatus.pass { background: #dcfce7; color: #166534; }
  #geoStatus.fail { background: #fee2e2; color: #991b1b; }
  .pane { display: none; border-bottom: 1px solid #e2e8f0; }
  .pane.on, body.measuring .pane { display: block; }
  svg.dia { display: block; width: 100%; height: auto; max-height: 78vh; }
  main { max-width: 1240px; margin: 0 auto; padding: 16px; }
  h1 { font-size: 18px; margin: 12px 16px 4px; }
  h2 { font-size: 15px; margin: 20px 0 8px; }
  table { border-collapse: collapse; font-size: 12.5px; width: 100%; }
  th, td { border: 1px solid #e2e8f0; padding: 5px 8px; text-align: left; vertical-align: top; }
  th { background: #f8fafc; }
  .note { font-size: 12.5px; color: #475569; margin: 8px 16px; }
  #geoDetail { font-family: Consolas, monospace; font-size: 12px; white-space: pre-wrap; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; max-height: 320px; overflow: auto; }
  .legendbar { font-size: 12px; color: #334155; padding: 6px 16px; border-bottom: 1px solid #e2e8f0; }
</style>
</head>
<body>
${DEFS}
<h1>${doc.h1}</h1>
<div class="legendbar">${doc.legendbar}</div>
<header>${tabs}<span class="sp"></span><span id="geoStatus">幾何自檢：執行中…</span></header>
${panes}
<main>
${sectionHtml}
  <h2>幾何自檢輸出（notation-precision §4，B-1 診斷物件格式）</h2>
  <div id="geoDetail">執行中…</div>
  <p class="note">${doc.footerNote}</p>
</main>
<script>
${script}
</script>
</body>
</html>
`;
}
