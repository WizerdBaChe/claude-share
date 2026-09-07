// tools/archdiag/tokens.mjs — style-token table + contrast check, DERIVED
// from emit.mjs (M5: the palette is never listed a second time; this file
// reads the exported constants and prints them). Born 2026-09-05 from the
// diagram-design borrow review (B-6: token STRUCTURE borrowed — semantic
// roles, an inversion rule, a contrast constraint — the external palette
// was not).
//
//   node tools/archdiag/tokens.mjs          print the README token table (markdown)
//   node tools/archdiag/tokens.mjs --check  exit 2 when any TEXT/fill pair is
//                                           under WCAG AA 4.5:1 (determinable ⇒
//                                           FAIL); edge strokes vs the page are
//                                           graphics (3:1) and only WARN — their
//                                           consumer is the maintainer reading
//                                           this output. Promotion trigger: a
//                                           user report that an edge type cannot
//                                           be told from the background.
//
// Roles, not hex, are the contract. A dark theme is a SECOND role→hex map with
// the same roles that passes this same check and keeps the hue ranks (blue
// module / grey external / amber store / green state / violet port / orange
// un-accepted); it never recolors a role's meaning. Not built — deliverables
// declare `color-scheme: light` (emit.mjs CSS); build it only when a dark
// deliverable is requested (review-when).

// 2026-09-07: TEXT and SURFACE joined this import. They used to be a
// transcription right here, carrying a `grep-verified 2026-09-05` receipt —
// which meant `--check` imported the fills and edges but graded a COPY of the
// foregrounds. Proved by control rather than argued: mutating `FILL.block` in
// emit.mjs turned this red, mutating the node TITLE colour left it silent at
// 0 fail. Nothing here restates a colour any more; a dated receipt over a
// hand-copied table is the failure mode M5 exists to prevent, and it had
// grown back inside the file that enforces M5.
import { FILL, STROKE, OVL, EDGE, TEXT, SURFACE } from './emit.mjs';

const ROLE = {
  block: 'module / component (block)', proc: 'process (same colour as block: it IS a block in a DFD)',
  ext: 'external actor / system (capsule)', store: 'data store', state: 'state (statechart)',
  port: 'port / boundary interface',
};
const EDGE_ROLE = {
  call: 'synchronous call / import', data: 'data flow', proto: 'async protocol (SSE / event)',
  egress: 'leaves the process boundary', warn: 'error flow (dual-coded: dashed)', trans: 'FSM transition',
  eps: 'automatic transition', absent: 'contractual NON-dependency (dual-coded: dotted, ✕ glyph, no arrowhead)',
};

function lum(hex) {
  const c = hex.slice(1).match(/../g).map((h) => parseInt(h, 16) / 255)
    .map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
export function contrast(a, b) {
  const [hi, lo] = [lum(a), lum(b)].sort((p, q) => q - p);
  return +((hi + 0.05) / (lo + 0.05)).toFixed(2);
}

export function nodeRows() {
  const rows = Object.keys(FILL).map((k) => ({ role: k, meaning: ROLE[k] || '', fill: FILL[k], stroke: STROKE[k],
    title: contrast(TEXT.title, FILL[k]), sub: contrast(TEXT.sub, FILL[k]) }));
  rows.push({ role: 'ov (overlay)', meaning: 'branch-only / 未驗收 (dashed border + badge)', fill: OVL.fill, stroke: OVL.stroke,
    title: contrast(TEXT.title, OVL.fill), sub: contrast(TEXT.badge, OVL.fill) });
  rows.push({ role: 'pill', meaning: 'edge label', fill: SURFACE.pill, stroke: SURFACE.pillStroke, title: contrast(TEXT.sub, SURFACE.pill), sub: null });
  rows.push({ role: 'container', meaning: 'composite boundary / lifeline', fill: SURFACE.container, stroke: SURFACE.containerStroke, title: contrast(TEXT.container, SURFACE.container), sub: null });
  return rows;
}
export function edgeRows() {
  return Object.entries(EDGE).map(([k, st]) => ({ type: k, meaning: EDGE_ROLE[k] || '', stroke: st.stroke,
    dash: st.dash || 'solid', marker: st.marker || '—', vsPage: contrast(st.stroke, SURFACE.page) }));
}

// rows/edges are parameters so a control can feed a known-bad pair (the CLI
// always passes the live tables).
export function contrastProblems(rows = nodeRows(), edges = edgeRows()) {
  const fail = [], warn = [];
  for (const r of rows) {
    if (r.title < 4.5) fail.push(`${r.role}: title text on ${r.fill} = ${r.title} (< 4.5)`);
    if (r.sub !== null && r.sub < 4.5) fail.push(`${r.role}: secondary text on ${r.fill} = ${r.sub} (< 4.5)`);
  }
  for (const r of edges) if (r.vsPage < 3) warn.push(`edge ${r.type}: stroke ${r.stroke} vs page = ${r.vsPage} (< 3:1 graphics)`);
  return { fail, warn };
}

export function markdown() {
  const out = [];
  out.push('| role | meaning | fill | stroke | title text (AA ≥ 4.5) | secondary text |', '|---|---|---|---|---|---|');
  for (const r of nodeRows()) out.push(`| ${r.role} | ${r.meaning} | \`${r.fill}\` | \`${r.stroke}\` | ${r.title} | ${r.sub === null ? '—' : r.sub} |`);
  out.push('', '| edge type | meaning | stroke | dash | marker | vs page (graphics ≥ 3) |', '|---|---|---|---|---|---|');
  for (const r of edgeRows()) out.push(`| ${r.type} | ${r.meaning} | \`${r.stroke}\` | ${r.dash} | ${r.marker} | ${r.vsPage} |`);
  return out.join('\n');
}

if (process.argv[1] && /tokens\.mjs$/.test(process.argv[1].replace(/\\/g, '/'))) {
  const { fail, warn } = contrastProblems();
  if (process.argv.includes('--check')) {
    for (const w of warn) console.log('WARN', w);
    for (const f of fail) console.log('FAIL', f);
    console.log(`contrast: ${fail.length} fail, ${warn.length} warn (text AA 4.5:1 = FAIL; edge graphics 3:1 = WARN)`);
    process.exit(fail.length ? 2 : 0);
  }
  console.log(markdown());
  if (warn.length) console.log('\n' + warn.map((w) => 'WARN ' + w).join('\n'));
}
