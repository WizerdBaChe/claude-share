#!/usr/bin/env node
/**
 * ui-state-probe — read an element's SETTLED visual state, out-of-process.
 *
 * Two failure modes this exists for:
 *
 * 1. getComputedStyle() during a CSS transition returns the interpolated
 *    mid-flight value (CSSOM resolved value), not the target. An agent or a
 *    test that hovers and then measures over a non-deterministic round trip
 *    reads a random point on the curve, so the assertion is flaky rather than
 *    stably wrong. Fixed here by finishing every running animation via the Web
 *    Animations API before any measurement, and by passing
 *    `animations: 'disabled'` to the screenshot.
 *
 * 2. An in-app / embedded browser pane whose window is occluded goes to
 *    document.visibilityState === "hidden"; the compositor stops producing
 *    frames and every screenshot call times out while DOM reads keep working.
 *    Fixed here by not using that pane at all: this runs headless in its own
 *    process, where there is no window to occlude.
 *
 * Usage:
 *   node ui-probe.mjs --url http://localhost:5173 --selector "#submit" \
 *                     --state hover --props background-color,color --shot out.png
 *
 * Output: one JSON object on stdout. Exit 0 = probed, 1 = probe failed.
 */

import { pathToFileURL } from 'node:url';
import { chromium, firefox, webkit } from 'playwright';

const ENGINES = { chromium, firefox, webkit };

const DEFAULTS = {
  url: null,
  selector: null,
  state: 'none', // none | hover | focus | active
  props: ['background-color', 'color', 'opacity', 'transform'],
  viewport: { width: 1280, height: 800 },
  engine: 'chromium',
  timeout: 10000,
  settleTimeout: 2000,
  shot: null,
  fullPage: false,
  colorScheme: null, // null | 'light' | 'dark'
  reducedMotion: false,
  headed: false,
};

/**
 * Runs INSIDE the page. Finishes every animation in the subtree (CSS
 * transitions surface as CSSTransition objects on the WAAPI timeline), forces
 * a reflow, then reads the requested properties. Synchronous on purpose: no
 * sleep, no transitionend race.
 */
const SETTLE_AND_READ = ([selector, props]) => {
  const el = document.querySelector(selector);
  if (!el) return { error: 'selector-not-found' };
  el.getAnimations({ subtree: true }).forEach((a) => {
    try {
      a.finish();
    } catch {
      /* infinite animations cannot finish; they are frozen by the stylesheet instead */
    }
  });
  void document.body.offsetHeight;
  const cs = getComputedStyle(el);
  const styles = {};
  for (const p of props) styles[p] = cs.getPropertyValue(p).trim();
  const r = el.getBoundingClientRect();
  return {
    styles,
    box: { x: r.x, y: r.y, width: r.width, height: r.height },
    visible: r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none',
  };
};

const FREEZE_STYLESHEET =
  '*,*::before,*::after{transition:none!important;animation-duration:0s!important;' +
  'animation-delay:0s!important;animation-iteration-count:1!important;caret-color:transparent!important}';

export async function probe(options = {}) {
  const o = { ...DEFAULTS, ...options };
  if (!o.url) throw new Error('probe: --url is required');
  if (!o.selector) throw new Error('probe: --selector is required');
  const engine = ENGINES[o.engine];
  if (!engine) throw new Error(`probe: unknown engine "${o.engine}"`);

  const browser = await engine.launch({ headless: !o.headed });
  try {
    const page = await browser.newPage({
      viewport: o.viewport,
      ...(o.colorScheme ? { colorScheme: o.colorScheme } : {}),
      ...(o.reducedMotion ? { reducedMotion: 'reduce' } : {}),
    });
    page.setDefaultTimeout(o.timeout);

    const consoleErrors = [];
    page.on('console', (m) => m.type() === 'error' && consoleErrors.push(m.text()));
    page.on('pageerror', (e) => consoleErrors.push(String(e)));

    await page.goto(o.url, { waitUntil: 'load' });
    await page.waitForSelector(o.selector, { state: 'attached' });

    // Non-hover states are driven before freezing so their transitions can be
    // finished by the same pass; :hover must survive, so the pointer is parked
    // on the element and nothing moves it afterwards.
    if (o.state === 'hover') await page.hover(o.selector);
    else if (o.state === 'focus') await page.focus(o.selector);
    else if (o.state === 'active') {
      const b = await page.locator(o.selector).boundingBox();
      if (b) {
        await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2);
        await page.mouse.down();
      }
    }

    // Freeze what finish() cannot: infinite keyframe loops, and anything that
    // starts after the measurement below.
    await page.addStyleTag({ content: FREEZE_STYLESHEET });

    const result = await page.evaluate(SETTLE_AND_READ, [o.selector, o.props]);
    if (result.error === 'selector-not-found') {
      throw new Error(`probe: selector "${o.selector}" matched nothing`);
    }

    let shot = null;
    if (o.shot) {
      await page.screenshot({ path: o.shot, fullPage: o.fullPage, animations: 'disabled' });
      shot = o.shot;
    }

    if (o.state === 'active') await page.mouse.up().catch(() => {});

    return {
      url: o.url,
      selector: o.selector,
      state: o.state,
      settled: true,
      ...result,
      screenshot: shot,
      consoleErrors,
    };
  } finally {
    await browser.close();
  }
}

/* ---------------------------------- CLI ---------------------------------- */

function parseCli(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) continue;
    const key = a.slice(2);
    const next = argv[i + 1];
    const takesValue = next !== undefined && !next.startsWith('--');
    switch (key) {
      case 'url':
      case 'selector':
      case 'state':
      case 'shot':
      case 'engine':
      case 'color-scheme':
        if (takesValue) out[key === 'color-scheme' ? 'colorScheme' : key] = next;
        if (takesValue) i++;
        break;
      case 'props':
        if (takesValue) out.props = next.split(',').map((s) => s.trim()).filter(Boolean);
        if (takesValue) i++;
        break;
      case 'viewport': {
        if (takesValue) {
          const [w, h] = next.split('x').map(Number);
          out.viewport = { width: w, height: h };
          i++;
        }
        break;
      }
      case 'timeout':
        if (takesValue) out.timeout = Number(next);
        if (takesValue) i++;
        break;
      case 'full-page':
        out.fullPage = true;
        break;
      case 'reduced-motion':
        out.reducedMotion = true;
        break;
      case 'headed':
        out.headed = true;
        break;
      default:
        if (takesValue) i++;
    }
  }
  return out;
}

const isMain = Boolean(process.argv[1]) && import.meta.url === pathToFileURL(process.argv[1]).href;

if (isMain) {
  try {
    const result = await probe(parseCli(process.argv.slice(2)));
    process.stdout.write(JSON.stringify(result, null, 2) + '\n');
  } catch (err) {
    process.stdout.write(JSON.stringify({ settled: false, error: String(err.message ?? err) }, null, 2) + '\n');
    process.exitCode = 1;
  }
}
