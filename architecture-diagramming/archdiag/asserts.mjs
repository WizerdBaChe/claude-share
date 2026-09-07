// tools/archdiag/asserts.mjs — build-time assert set (runs on the model
// data before any bytes are written): grid snap, anchor-on-border,
// orthogonality. Byte-faithful cut of the identical block both source
// scripts carried (identity asserted at extraction). 2026-09-05 additions
// (diagram-design borrow review): pill-centre-in-node (B-1) and shared-anchor
// (B-2) on the model, the a11y contract on the EMITTED page (B-3) — all
// determinable, so all FAIL.

export function buildAsserts(views, grid) {
  const problems = [];
for (const v of views) {
  const all = [...v.nodes, ...(v.containers || [])];
  for (const n of all) for (const k of ['x', 'y', 'w', 'h'])
    if (n[k] % grid !== 0) problems.push(`${v.id}/${n.id}.${k}=${n[k]} not x${grid}`);
  const byId = Object.fromEntries(all.map((n) => [n.id, n]));
  const onB = (p, n) =>
    ((Math.abs(p[0] - n.x) < 1 || Math.abs(p[0] - (n.x + n.w)) < 1) && p[1] >= n.y - 1 && p[1] <= n.y + n.h + 1) ||
    ((Math.abs(p[1] - n.y) < 1 || Math.abs(p[1] - (n.y + n.h)) < 1) && p[0] >= n.x - 1 && p[0] <= n.x + n.w + 1);
  for (const e of v.edges) {
    if (!onB(e.pts[0], byId[e.from])) problems.push(`${v.id}/${e.id} start off ${e.from}`);
    if (!onB(e.pts.at(-1), byId[e.to])) problems.push(`${v.id}/${e.id} end off ${e.to}`);
    for (let i = 1; i < e.pts.length; i++)
      if (e.pts[i - 1][0] !== e.pts[i][0] && e.pts[i - 1][1] !== e.pts[i][1]) problems.push(`${v.id}/${e.id} seg${i} not orthogonal`);
  }
  // pill over node (B-1): a pill's centre (pillAt) inside a NODE rect is
  // determinable from the model ⇒ FAIL here; in-page #9 repeats it measured.
  // Border straddles pass (calibration: selfcheck.mjs #9 comment).
  for (const e of v.edges) {
    if (!e.pillAt) continue;
    const [px, py] = e.pillAt;
    for (const n of v.nodes)
      if (px > n.x + 1 && px < n.x + n.w - 1 && py > n.y + 1 && py < n.y + n.h - 1)
        problems.push(`${v.id}/${e.id} pill centre (${px},${py}) inside node ${n.id}`);
  }
  // shared anchor (B-2): two DIFFERENT edges anchored on one border side closer
  // than the grid unit but not coincident read as one smudged line (R10
  // near-coincidence band). Gap 0 = deliberate bundle, passes. Determinable from
  // the model ⇒ FAIL here; in-page check #10 repeats it on the emitted bytes.
  const sidesOf = (p, n) => {
    const s = [];
    if (Math.abs(p[0] - n.x) < 1) s.push('left');
    if (Math.abs(p[0] - (n.x + n.w)) < 1) s.push('right');
    if (Math.abs(p[1] - n.y) < 1) s.push('top');
    if (Math.abs(p[1] - (n.y + n.h)) < 1) s.push('bottom');
    return s;
  };
  const slots = new Map();
  for (const e of v.edges) for (const [p, id] of [[e.pts[0], e.from], [e.pts.at(-1), e.to]]) {
    const n = byId[id]; if (!n) continue;
    for (const side of sidesOf(p, n)) {
      const key = `${id}|${side}`;
      if (!slots.has(key)) slots.set(key, []);
      slots.get(key).push({ e: e.id, c: side === 'left' || side === 'right' ? p[1] : p[0] });
    }
  }
  for (const [key, list] of slots)
    for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) {
      if (list[i].e === list[j].e) continue;
      const gap = Math.abs(list[i].c - list[j].c);
      if (gap > 0 && gap < grid) problems.push(`${v.id}/${key} anchors of ${list[i].e} and ${list[j].e} ${gap}px apart (< ${grid}, not coincident)`);
    }
}
  return problems;
}

// a11y contract (B-3) — checked on the EMITTED html, never on the model (the
// gate reads the artifact). Every `svg.dia` is an image with an accessible
// name and description: role="img"; aria-labelledby naming a <title> that is
// the svg's FIRST child and a <desc> right after it; both ids unique in the
// page (several inline SVGs share one document — an id collision makes AT
// read the wrong diagram). Determinable ⇒ FAIL.
export function a11yAsserts(html) {
  const problems = [];
  const re = /<svg class="dia"([^>]*)>([\s\S]*?)<g class="scene">/g;
  let m, count = 0;
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  while ((m = re.exec(html))) {
    count++;
    const attrs = m[1], head = m[2];
    const view = (attrs.match(/data-view="([^"]*)"/) || [])[1] || '?';
    if (!/\brole="img"/.test(attrs)) problems.push(`${view}: svg.dia lacks role="img"`);
    const lb = (attrs.match(/aria-labelledby="([^"]*)"/) || [])[1];
    if (!lb) { problems.push(`${view}: svg.dia lacks aria-labelledby`); continue; }
    const ids = lb.trim().split(/\s+/);
    if (ids.length !== 2) problems.push(`${view}: aria-labelledby must name exactly a title id and a desc id (got "${lb}")`);
    for (const id of ids) {
      const n = (html.match(new RegExp(`(?<![\\w-])id="${esc(id)}"`, 'g')) || []).length;
      if (n !== 1) problems.push(`${view}: id "${id}" occurs ${n}x in the page (must be exactly 1)`);
    }
    const t = head.match(/^\s*<title id="([^"]+)">([^<]*)<\/title>\s*<desc id="([^"]+)">([^<]*)<\/desc>\s*$/);
    if (!t) { problems.push(`${view}: the first children of svg.dia must be <title> then <desc>, before the scene`); continue; }
    if (t[1] !== ids[0] || t[3] !== ids[1]) problems.push(`${view}: aria-labelledby "${lb}" does not name its own title/desc ids`);
    if (!t[2].trim()) problems.push(`${view}: empty <title>`);
    if (!t[4].trim()) problems.push(`${view}: empty <desc>`);
  }
  if (count === 0) problems.push('no svg.dia found in the emitted page');
  return problems;
}
