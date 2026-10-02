#!/usr/bin/env node
/**
 * doctor.mjs — self-check + repair for the ui-shot runner.
 *
 * Why it exists (user requirement, 2026-08-16): the runner is an INSTALLATION,
 * and installations rot silently — a node upgrade, an npm cache prune, a
 * playwright uninstall, or a machine move can break the default pixel route
 * while every document still says it works. A control that rots unnoticed is
 * worse than none, so the install ships with its own verifier and repairer.
 *
 * Usage:
 *   node doctor.mjs            check only (4 checks, ~2-4s)
 *   node doctor.mjs --repair   on failure: npm i (exact pin) /
 *                              npx playwright install chromium, then re-check
 *   node doctor.mjs --full     also run the asset's own 9-check acceptance
 *                              (scripts/verify.mjs)
 *
 * File names: the asset trio keeps its ORIGINAL names (ui-probe.mjs,
 * verify.mjs, fixture.html) — verify.mjs hardcodes './fixture.html' and
 * './ui-probe.mjs', so item.json's renamed targets would break it.
 *
 * Checks:
 *   1. node >= 20 (the asset's acceptance floor)
 *   2. `playwright` resolves FROM THE SCRIPTS DIR at the version pinned in
 *      package.json (resolution is what broke on 2026-08-16: browsers were
 *      installed while no dir tree could resolve the package)
 *   3. the pinned chromium build's executable exists
 *   4. end-to-end: ui-probe.mjs against the bundled fixture over file://,
 *      expecting exit 0 and a non-empty PNG
 *
 * Exit 0 = all pass. Exit 1 = something failed (details on stdout).
 * Callers: run this FIRST whenever a pixel-route recipe fails; the route
 * documentation names it as the first-line diagnostic.
 */
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, statSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SCRIPTS = join(HERE, 'scripts');
const REPAIR = process.argv.includes('--repair');
const FULL = process.argv.includes('--full');

const results = [];
function report(name, ok, note = '') {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${note ? '  (' + note + ')' : ''}`);
  results.push(ok);
  return ok;
}

function npm(args) {
  execFileSync(process.platform === 'win32' ? 'npm.cmd' : 'npm', args, {
    cwd: HERE, stdio: 'inherit', shell: process.platform === 'win32',
  });
}

function checkNode() {
  const major = Number(process.versions.node.split('.')[0]);
  return report('1 node >= 20', major >= 20, `running ${process.versions.node}`);
}

function checkResolve() {
  const pinned = JSON.parse(readFileSync(join(HERE, 'package.json'), 'utf-8'))
    .dependencies.playwright;
  try {
    // Resolve exactly as scripts/ui-probe.mjs would: from the scripts dir.
    const req = createRequire(join(SCRIPTS, '_resolve-anchor.js'));
    const version = JSON.parse(
      readFileSync(req.resolve('playwright/package.json'), 'utf-8')).version;
    return report('2 playwright resolves at pinned version', version === pinned,
      `pinned ${pinned}, resolved ${version}`);
  } catch {
    return report('2 playwright resolves at pinned version', false,
      `pinned ${pinned}, resolves to NOTHING from ${SCRIPTS}`);
  }
}

async function checkBrowser() {
  try {
    // doctor.mjs sits beside node_modules, so bare-specifier import resolves
    // the same install the scripts use; tolerate CJS default-only interop.
    const pw = await import('playwright');
    const chromium = pw.chromium || (pw.default && pw.default.chromium);
    const exe = chromium.executablePath();
    return report('3 chromium executable present', existsSync(exe), exe);
  } catch (e) {
    return report('3 chromium executable present', false, String(e).slice(0, 120));
  }
}

function checkProbe() {
  const out = mkdtempSync(join(tmpdir(), 'ui-shot-doctor-'));
  const png = join(out, 'doctor.png');
  try {
    execFileSync(process.execPath, [
      join(SCRIPTS, 'ui-probe.mjs'),
      '--url', pathToFileURL(join(SCRIPTS, 'fixture.html')).href,
      '--selector', 'body', '--props', 'background-color',
      '--shot', png, '--timeout', '15000',
    ], { stdio: 'pipe' });
    const ok = existsSync(png) && statSync(png).size > 0;
    return report('4 end-to-end probe writes a PNG', ok,
      ok ? `${statSync(png).size} bytes` : 'no file');
  } catch (e) {
    return report('4 end-to-end probe writes a PNG', false, String(e).slice(0, 160));
  } finally {
    rmSync(out, { recursive: true, force: true });
  }
}

async function main() {
  checkNode();
  let okResolve = checkResolve();
  if (!okResolve && REPAIR) {
    console.log('-- repair: npm i (exact pin) --');
    npm(['i', '--no-audit', '--no-fund']);
    okResolve = checkResolve();
  }
  let okBrowser = okResolve ? await checkBrowser() : report('3 chromium executable present', false, 'skipped: no resolve');
  if (okResolve && !okBrowser && REPAIR) {
    console.log('-- repair: npx playwright install chromium --');
    npm(['exec', '--yes', '--', 'playwright', 'install', 'chromium']);
    okBrowser = await checkBrowser();
  }
  if (okResolve && okBrowser) checkProbe();
  else report('4 end-to-end probe writes a PNG', false, 'skipped: prerequisites failed');

  if (FULL && results.every(Boolean)) {
    console.log('-- full: asset acceptance (ui-probe.verify.mjs) --');
    try {
      execFileSync(process.execPath, [join(SCRIPTS, 'verify.mjs')],
        { cwd: SCRIPTS, stdio: 'inherit' });
      report('5 asset acceptance suite', true);
    } catch {
      report('5 asset acceptance suite', false);
    }
  }

  const n = results.filter(Boolean).length;
  console.log(`\n${n}/${results.length} passed`);
  process.exit(results.every(Boolean) ? 0 : 1);
}

main();
