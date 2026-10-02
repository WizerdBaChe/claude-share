/**
 * Standalone acceptance for ui-state-probe.
 *   node verify.mjs            (from this directory; needs playwright + chromium)
 * Expect 9 PASS lines and "all checks passed".
 */
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
import { readFileSync, statSync, rmSync } from 'node:fs';
import { probe } from './ui-probe.mjs';

const FIXTURE = new URL('./fixture.html', import.meta.url).href;
const SHOT = fileURLToPath(new URL('./.verify-shot.png', import.meta.url));

let failures = 0;
const check = (name, cond, detail = '') => {
  if (cond) console.log(`PASS  ${name}`);
  else {
    console.log(`FAIL  ${name}  ${detail}`);
    failures++;
  }
};

/** The control: what a naive "hover then measure" reads on the same fixture. */
async function naiveRead() {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 800, height: 600 } });
    await page.goto(FIXTURE, { waitUntil: 'load' });
    await page.hover('#slow');
    return await page.evaluate(() =>
      getComputedStyle(document.querySelector('#slow')).backgroundColor
    );
  } finally {
    await browser.close();
  }
}

const RESTING = 'rgb(238, 238, 238)';
const HOVERED = 'rgb(0, 102, 204)';

// 1. resting state reads the resting token
const rest = await probe({ url: FIXTURE, selector: '#slow', props: ['background-color'] });
check('resting background-color', rest.styles['background-color'] === RESTING, rest.styles['background-color']);

// 2. the property this asset exists for: hover reads the TARGET, not an interpolation
const hov = await probe({ url: FIXTURE, selector: '#slow', state: 'hover', props: ['background-color', 'color'] });
check('hover reads the settled target', hov.styles['background-color'] === HOVERED, hov.styles['background-color']);
check('hover settles every animating property', hov.styles.color === 'rgb(255, 255, 255)', hov.styles.color);

// 3. the control proves the mechanism: naive measurement lands mid-transition
const naive = await naiveRead();
check(
  'control: naive read does NOT reach the target (this is the bug)',
  naive !== HOVERED,
  `naive returned ${naive}; fixture transition may be too fast`
);

// 4. determinism — three runs, byte-identical
const runs = [];
for (let i = 0; i < 3; i++) {
  const r = await probe({ url: FIXTURE, selector: '#slow', state: 'hover', props: ['background-color'] });
  runs.push(r.styles['background-color']);
}
check('three hover runs agree', new Set(runs).size === 1, runs.join(' / '));

// 5. focus is driven the same way
const foc = await probe({ url: FIXTURE, selector: '#focusable', state: 'focus', props: ['opacity'] });
check('focus reads settled opacity', foc.styles.opacity === '1', foc.styles.opacity);

// 6. an infinite animation cannot finish() — the freeze stylesheet must still pin it
const inf1 = await probe({ url: FIXTURE, selector: '#forever', props: ['opacity'] });
const inf2 = await probe({ url: FIXTURE, selector: '#forever', props: ['opacity'] });
check('infinite animation is frozen reproducibly', inf1.styles.opacity === inf2.styles.opacity,
  `${inf1.styles.opacity} vs ${inf2.styles.opacity}`);

// 7. screenshot is produced out-of-process (no visible window required)
rmSync(SHOT, { force: true });
await probe({ url: FIXTURE, selector: '#slow', state: 'hover', shot: SHOT });
const png = statSync(SHOT);
check('screenshot written headless', png.size > 1000 && readFileSync(SHOT).subarray(1, 4).toString() === 'PNG',
  `size=${png.size}`);
rmSync(SHOT, { force: true });

// 8. a missing selector fails loudly instead of returning a plausible object
let threw = false;
try {
  await probe({ url: FIXTURE, selector: '#nope', timeout: 1500 });
} catch {
  threw = true;
}
check('missing selector throws', threw);

console.log(failures === 0 ? '\nall checks passed' : `\n${failures} check(s) failed`);
process.exitCode = failures === 0 ? 0 : 1;
