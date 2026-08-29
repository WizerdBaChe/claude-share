// tools/archdiag/asserts.mjs — build-time assert set (runs on the model
// data before any bytes are written): grid snap, anchor-on-border,
// orthogonality. Byte-faithful cut of the identical block both source
// scripts carried (identity asserted at extraction).

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
}
  return problems;
}
