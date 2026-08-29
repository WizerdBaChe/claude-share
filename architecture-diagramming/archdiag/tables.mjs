// tools/archdiag/tables.mjs — HTML table emitter for the deliverable's
// model / matrix / drift / gap / measurement sections. Byte-faithful cut
// of the identical helper both source scripts carried.

import { esc } from './emit.mjs';

export const table = (h, rows) => `<table><thead><tr>${h.map((x) => `<th>${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
