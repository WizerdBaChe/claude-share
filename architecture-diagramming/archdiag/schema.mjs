// tools/archdiag/schema.mjs — structural validation of the view model (B-7).
// Scope discipline (gate-severity rule): this validator rules ONLY on what it
// can determine — field presence, types, enum membership, id resolution,
// declaration shape. Geometry belongs to asserts.mjs and the in-page §4
// checks; semantic choices (aggregation, view selection, node positions) stay
// human and are NEVER validated here.
// Determinable closure => FAIL: build() throws on any problem reported here.
// Enums derive from emit.mjs so they cannot fork from what the emitter
// actually renders (variant-recall rule: fix the source, never enumerate).

import { FILL, EDGE } from './emit.mjs';

export const NODE_KINDS = [...Object.keys(FILL), 'stateT'];
export const EDGE_TYPES = Object.keys(EDGE);

const isNum = (x) => typeof x === 'number' && Number.isFinite(x);
const isPt = (p) => Array.isArray(p) && p.length === 2 && isNum(p[0]) && isNum(p[1]);
const isStr = (x) => typeof x === 'string';
const isNonEmptyStr = (x) => isStr(x) && x.length > 0;

function checkInit(init, vid, label, P) {
  if (!init || !isPt(init.at) || !isPt(init.to)) P(`${vid}: ${label} must be { at: [x,y], to: [x,y] }`);
}

export function validateViews(views) {
  const problems = [];
  const P = (m) => problems.push(m);
  if (!Array.isArray(views) || views.length === 0) return ['views: empty or not an array'];
  const vids = new Set();
  for (const v of views) {
    const vid = v && v.id;
    if (!isNonEmptyStr(vid)) { P('view without a string id'); continue; }
    if (vids.has(vid)) P(`duplicate view id ${vid}`);
    vids.add(vid);
    if (!isNonEmptyStr(v.title)) P(`${vid}: missing title`);
    if (!Array.isArray(v.vb) || v.vb.length !== 2 || !v.vb.every((n) => isNum(n) && n > 0)) P(`${vid}: vb must be [w,h] with w,h > 0`);
    if (!isNonEmptyStr(v.subtitle)) P(`${vid}: missing subtitle (the view's question)`);
    if (!Array.isArray(v.declared) || v.declared.length === 0 || !v.declared.every(isNonEmptyStr))
      P(`${vid}: declared must be a non-empty array of declaration strings`);
    if (v.declaredCrossings !== undefined && (!Number.isInteger(v.declaredCrossings) || v.declaredCrossings < 0 || v.declaredCrossings > 3))
      P(`${vid}: declaredCrossings must be an integer 0..3 (over 3: split the view instead of declaring)`);
    const nodes = Array.isArray(v.nodes) ? v.nodes : [];
    const containers = Array.isArray(v.containers) ? v.containers : [];
    const edges = Array.isArray(v.edges) ? v.edges : [];
    if (!Array.isArray(v.nodes) || nodes.length === 0) P(`${vid}: nodes missing or empty`);
    if (v.edges !== undefined && !Array.isArray(v.edges)) P(`${vid}: edges must be an array`);
    const ids = new Set();
    for (const n of nodes) {
      if (!isNonEmptyStr(n.id)) { P(`${vid}: node without a string id`); continue; }
      if (ids.has(n.id)) P(`${vid}/${n.id}: duplicate id`);
      ids.add(n.id);
      if (!NODE_KINDS.includes(n.kind)) P(`${vid}/${n.id}: unknown kind "${n.kind}" (known: ${NODE_KINDS.join(', ')})`);
      for (const k of ['x', 'y', 'w', 'h']) if (!isNum(n[k])) P(`${vid}/${n.id}.${k}: not a finite number`);
      if (isNum(n.w) && n.w <= 0) P(`${vid}/${n.id}.w: must be > 0`);
      if (isNum(n.h) && n.h <= 0) P(`${vid}/${n.id}.h: must be > 0`);
      if (!isNonEmptyStr(n.t)) P(`${vid}/${n.id}: missing t (title text)`);
      if (n.l !== undefined && (!Array.isArray(n.l) || !n.l.every(isStr))) P(`${vid}/${n.id}.l: must be an array of strings`);
      if (!isNonEmptyStr(n.ev)) P(`${vid}/${n.id}: missing ev (evidence anchor — audit discipline, no untraced element)`);
    }
    for (const c of containers) {
      if (!isNonEmptyStr(c.id)) { P(`${vid}: container without a string id`); continue; }
      if (ids.has(c.id)) P(`${vid}/${c.id}: duplicate id (container vs node)`);
      ids.add(c.id);
      for (const k of ['x', 'y', 'w', 'h']) if (!isNum(c[k])) P(`${vid}/${c.id}.${k}: not a finite number`);
      if (c.title !== undefined && !isStr(c.title)) P(`${vid}/${c.id}.title: must be a string ('' allowed for lifelines)`);
    }
    const eids = new Set();
    for (const e of edges) {
      if (!isNonEmptyStr(e.id)) { P(`${vid}: edge without a string id`); continue; }
      if (eids.has(e.id)) P(`${vid}/${e.id}: duplicate edge id`);
      eids.add(e.id);
      if (!EDGE_TYPES.includes(e.type)) P(`${vid}/${e.id}: unknown edge type "${e.type}" (known: ${EDGE_TYPES.join(', ')})`);
      for (const end of ['from', 'to'])
        if (!ids.has(e[end])) P(`${vid}/${e.id}.${end}: "${e[end]}" resolves to no node/container in this view`);
      if (!Array.isArray(e.pts) || e.pts.length < 2 || !e.pts.every(isPt)) P(`${vid}/${e.id}.pts: must be >= 2 points of [x,y]`);
      if (e.pill !== undefined) {
        if (!isNonEmptyStr(e.pill)) P(`${vid}/${e.id}.pill: must be a non-empty string`);
        if (!isPt(e.pillAt)) P(`${vid}/${e.id}: pill requires pillAt [x,y]`);
      }
      if (!isNonEmptyStr(e.ev)) P(`${vid}/${e.id}: missing ev (evidence anchor — audit discipline, no untraced element)`);
    }
    if (v.init !== undefined) checkInit(v.init, vid, 'init', P);
    if (v.inits !== undefined) {
      if (!Array.isArray(v.inits) || v.inits.length === 0) P(`${vid}: inits must be a non-empty array`);
      else v.inits.forEach((init, i) => checkInit(init, vid, `inits[${i}]`, P));
    }
  }
  return problems;
}
