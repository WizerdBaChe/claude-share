// tools/archdiag/selfcheck.mjs — in-page §4 geometry self-check emitter.
// SINGLE SOURCE of the check set (#1..#8 incl. #8 reference-resolution).
// Invariant: a build script must never embed its own copy of this script —
// per-file copies are the instrument-drift defect S1 exists to kill
// (F1 v1.1 vs frozen F2 diverged within one day).
// Body is a byte-faithful cut of dit-audit-f1.build.mjs v1.1 (the superset
// side); the two provenance comments are parametrized via `notes` so an
// artifact can carry its own history without forking the check logic.
// Includes the tab handler deliberately: the measuring pass toggles
// body.measuring and relies on the pane/tab mechanism it ships with.

const DEFAULT_PRECOND2 = [
  '  // instrument precondition #2: getBBox() on a display:none pane returns zero',
  '  // rects — measure with every pane rendered, then restore the tab state.',
].join('\n');

const DEFAULT_CHECK8 = [
  '      // 8. reference resolution: a dangling url(#id) reference renders as',
  '      // silently absent — assert every url(#id) resolves (positive-control calibrated).',
].join('\n');

export function inPageScript({ grid = 8, viewCount, notes = {} }) {
  const precond2 = notes.precond2 ?? DEFAULT_PRECOND2;
  const check8 = notes.check8 ?? DEFAULT_CHECK8;
  return `(function () {
  'use strict';
  document.querySelectorAll('.tab').forEach((b) => b.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach((x) => x.classList.toggle('on', x === b));
    document.querySelectorAll('.pane').forEach((p) => p.classList.toggle('on', p.id === 'pane-' + b.dataset.tab));
  }));

  // ---- §4 self-checks, B-1 diagnostic-object output ----
  const diags = [];
  const stats = [];
  const D = (code, subject, evidence, fixes) => diags.push({ code, severity: 'error', subject, evidence, supportedFixes: fixes });
${precond2}
  document.body.classList.add('measuring');
  try {
    const PAD = 2, EPS = 2, GRIDU = ${grid};
    for (const svg of document.querySelectorAll('svg.dia')) {
      const view = svg.dataset.view;
      // precondition #1: no transform inside the scene
      for (const el of svg.querySelectorAll('[transform]'))
        D('instrument-precondition', { view, element: el.tagName }, { reason: 'transform inside asserted scene' }, ['emit absolute coordinates']);
      // precondition #2 assert: the scene must actually render
      if (svg.querySelector('.scene').getBBox().width === 0)
        D('instrument-precondition', { view }, { reason: 'scene not rendered (hidden pane?) — bboxes would be zero' }, ['measure with the pane rendered']);
      const nodes = [...svg.querySelectorAll('.node')].map((g) => ({ id: g.dataset.id, kind: g.dataset.kind, x: +g.dataset.x, y: +g.dataset.y, w: +g.dataset.w, h: +g.dataset.h }));
      const comps = [...svg.querySelectorAll('.comp')].map((g) => ({ id: g.dataset.id, x: +g.dataset.x, y: +g.dataset.y, w: +g.dataset.w, h: +g.dataset.h }));
      const edges = [...svg.querySelectorAll('.edge')].map((p) => {
        const v = p.dataset.pts.split(',').map(Number); const pts = [];
        for (let i = 0; i < v.length; i += 2) pts.push([v[i], v[i + 1]]);
        return { id: p.dataset.edge, from: p.dataset.from, to: p.dataset.to, pts, fromComp: !!p.dataset.fromcomp, selfLoop: !!p.dataset.selfloop };
      });
      // 1. label bboxes pairwise disjoint
      const labels = [...svg.querySelectorAll('.lbl')].map((t) => ({ el: t, b: t.getBBox() }));
      let pairs = 0;
      for (let i = 0; i < labels.length; i++) for (let j = i + 1; j < labels.length; j++) {
        const a = labels[i].b, b = labels[j].b; pairs++;
        if (a.x < b.x + b.width + PAD && b.x < a.x + a.width + PAD && a.y < b.y + b.height + PAD && b.y < a.y + a.height + PAD)
          D('label-overlap', { view, a: labels[i].el.textContent.slice(0, 14), b: labels[j].el.textContent.slice(0, 14) },
            { aRect: [a.x, a.y, a.width, a.height].map(Math.round), bRect: [b.x, b.y, b.width, b.height].map(Math.round) },
            ['move one label by ' + Math.ceil(Math.min(a.y + a.height - b.y, b.y + b.height - a.y) + PAD) + 'px vertically']);
      }
      // 2. anchors
      const rects = Object.fromEntries([...nodes, ...comps].map((n) => [n.id, n]));
      const onB = (p, n) =>
        ((Math.abs(p[0] - n.x) <= EPS || Math.abs(p[0] - (n.x + n.w)) <= EPS) && p[1] >= n.y - EPS && p[1] <= n.y + n.h + EPS) ||
        ((Math.abs(p[1] - n.y) <= EPS || Math.abs(p[1] - (n.y + n.h)) <= EPS) && p[0] >= n.x - EPS && p[0] <= n.x + n.w + EPS);
      for (const e of edges) {
        if (!onB(e.pts[0], rects[e.from])) D('anchor-off-node', { view, edge: e.id, end: 'start', node: e.from }, { point: e.pts[0] }, ['move start onto ' + e.from + ' border']);
        if (!onB(e.pts[e.pts.length - 1], rects[e.to])) D('anchor-off-node', { view, edge: e.id, end: 'end', node: e.to }, { point: e.pts[e.pts.length - 1] }, ['move end onto ' + e.to + ' border']);
      }
      // 3. containment
      const vb = svg.viewBox.baseVal, sb = svg.querySelector('.scene').getBBox();
      if (sb.x < 0 || sb.y < 0 || sb.x + sb.width > vb.width || sb.y + sb.height > vb.height)
        D('viewbox-clip', { view }, { scene: [sb.x, sb.y, sb.width, sb.height].map(Math.round), viewBox: [vb.width, vb.height] }, ['grow the viewBox or move content inward']);
      // 4. grid
      for (const n of nodes) for (const k of ['x', 'y', 'w', 'h'])
        if (n[k] % GRIDU !== 0) D('grid-off', { view, node: n.id, prop: k }, { value: n[k] }, ['snap to ' + GRIDU + 'px']);
      // 5. pass-through (self-loops and composite-source edges: own endpoints exempt as usual)
      const hit = (a, b, r) => Math.min(a[0], b[0]) < r.x + r.w - 1 && Math.max(a[0], b[0]) > r.x + 1 && Math.min(a[1], b[1]) < r.y + r.h - 1 && Math.max(a[1], b[1]) > r.y + 1;
      for (const e of edges) for (let i = 1; i < e.pts.length; i++)
        for (const n of nodes) {
          if (n.id === e.from || n.id === e.to) continue;
          if (hit(e.pts[i - 1], e.pts[i], n))
            D('edge-through-node', { view, edge: e.id, segment: i, node: n.id }, { seg: [e.pts[i - 1], e.pts[i]] }, ['reroute segment ' + i + ' around ' + n.id]);
        }
      // 6. crossings vs the view's DECLARED count — report WHICH pair at WHERE
      const declared = +(svg.querySelector('metadata')?.getAttribute('data-declared-crossings') || 0);
      let crossings = 0;
      const found = [];
      const segs = [];
      for (const e of edges) for (let i = 1; i < e.pts.length; i++) segs.push({ e: e.id, a: e.pts[i - 1], b: e.pts[i] });
      for (let i = 0; i < segs.length; i++) for (let j = i + 1; j < segs.length; j++) {
        const s = segs[i], t = segs[j];
        if (s.e === t.e) continue;
        const sv = s.a[0] === s.b[0], tv = t.a[0] === t.b[0];
        if (sv === tv) continue;
        const [vv, hh] = sv ? [s, t] : [t, s];
        const x = vv.a[0], y = hh.a[1];
        if (x > Math.min(hh.a[0], hh.b[0]) + 1 && x < Math.max(hh.a[0], hh.b[0]) - 1 && y > Math.min(vv.a[1], vv.b[1]) + 1 && y < Math.max(vv.a[1], vv.b[1]) - 1) {
          crossings++;
          found.push({ pair: [s.e, t.e], at: [x, y] });
        }
      }
      if (crossings > declared)
        for (const f of found)
          D('crossing-over-declared', { view, pair: f.pair }, { at: f.at, crossings, declared }, ['reroute ' + f.pair[0] + ' or ' + f.pair[1] + ' around (' + f.at + ')', 'or declare the crossing (≤3) with its coordinates']);
      stats.push(view + ': ' + nodes.length + ' nodes, ' + edges.length + ' edges, ' + pairs + ' label pairs, crossings ' + crossings + '/' + declared);
      // 7. fonts
      for (const t of svg.querySelectorAll('text.lbl'))
        if (parseFloat(t.getAttribute('font-size')) < 11)
          D('font-below-floor', { view, text: t.textContent.slice(0, 12) }, { size: t.getAttribute('font-size') }, ['raise to 11px']);
${check8}
      for (const el of svg.querySelectorAll('*')) {
        for (const attr of ['marker-end', 'marker-start', 'fill', 'stroke']) {
          const val = el.getAttribute && el.getAttribute(attr);
          const m = val && val.match(/^url\\(#([^)]+)\\)$/);
          if (m && !document.getElementById(m[1]))
            D('dangling-reference', { view, attr, id: m[1] }, { element: el.tagName }, ['define #' + m[1] + ' in a <defs> block']);
        }
      }
    }
  } catch (err) {
    diags.push({ code: 'selfcheck-crashed', severity: 'error', subject: {}, evidence: { message: err.message }, supportedFixes: [] });
  } finally {
    document.body.classList.remove('measuring');
  }
  const status = document.getElementById('geoStatus');
  const detail = document.getElementById('geoDetail');
  window.__geometryReport = { pass: diags.length === 0, diagnostics: diags, stats };
  if (diags.length === 0) {
    status.textContent = '幾何自檢：PASS（${viewCount} 視圖）'; status.className = 'pass';
    detail.textContent = 'PASS\\n' + stats.join('\\n');
  } else {
    status.textContent = '幾何自檢：FAIL（' + diags.length + '）'; status.className = 'fail';
    detail.textContent = JSON.stringify(diags, null, 1) + '\\n---\\n' + stats.join('\\n');
    console.error('geometry diagnostics', diags);
  }
})();`;
}
