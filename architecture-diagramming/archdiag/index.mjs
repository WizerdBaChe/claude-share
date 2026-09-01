// tools/archdiag/index.mjs — build() entry point for archdiag deliverables.
// Pipeline: schema validation (B-7) → build-time geometry asserts → marker
// closure (build-time face of in-page check #8, on library-owned references)
// → deterministic page emission → write + sha256 receipt line.
// Contract: identical input (views + doc + sections + notes) => identical
// bytes (receipt-friendly). Provenance: S1 of
// outputs/diagram-authoring/selfbuild-scope-eval-2026-08-28.md.

import fs from 'node:fs';
import crypto from 'node:crypto';
import { validateViews } from './schema.mjs';
import { buildAsserts } from './asserts.mjs';
import { pageHtml, DEFS, EDGE } from './emit.mjs';

export function build(opts) {
  const { outPath, grid = 8, views } = opts;
  if (!outPath) throw new Error('build(): outPath is required');
  const schemaProblems = validateViews(views);
  if (schemaProblems.length) throw new Error('SCHEMA FAILED:\n- ' + schemaProblems.join('\n- '));
  const assertProblems = buildAsserts(views, grid);
  if (assertProblems.length) throw new Error('BUILD FAILED:\n- ' + assertProblems.join('\n- '));
  // Marker closure — determinable at build time, so it FAILS here instead of
  // waiting for the in-page check (gate-severity rule: determinable => FAIL).
  for (const [type, st] of Object.entries(EDGE))
    if (st.marker && !DEFS.includes(`id="${st.marker}"`))
      throw new Error(`DEFS FAILED: edge type "${type}" references undefined marker #${st.marker}`);
  if (!DEFS.includes('id="mFill"'))
    throw new Error('DEFS FAILED: init arrows reference undefined marker #mFill');
  // Line endings are environment, not content: emission is eol-immune so
  // receipts survive a CRLF checkout/editor touching the sources (endings
  // are also pinned LF in .gitattributes — belt and braces, same property).
  const html = pageHtml(opts).replace(/\r\n/g, '\n');
  fs.writeFileSync(outPath, html, 'utf8');
  const sha256 = crypto.createHash('sha256').update(html).digest('hex');
  // bytes = ENCODED length (utf8), never html.length: the string length counts
  // UTF-16 code units and understates every CJK page — measured 2026-08-31 on
  // ccfg-retrieval-audit-f1.html (37,408 "bytes" logged vs 41,328 on disk); a
  // receipt whose count cannot be checked against the file is the L-012 proxy
  // shape. sha256 was always over utf8 bytes and is unchanged.
  const bytes = Buffer.byteLength(html, 'utf8');
  console.log('written:', outPath, bytes, 'bytes; schema + build-time asserts passed; sha256', sha256);
  return { html, bytes, sha256 };
}
