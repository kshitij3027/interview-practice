// End-to-end coverage for the funnel report's race behaviour.
//
// Deliberately NOT part of `npm test`: this file lives outside test/ and does not match Node's
// test-discovery patterns, so `node --test` will not pick it up. The graded suite stays
// dependency-free; this runs via `npm run e2e` and skips cleanly when Playwright is absent.
//
// Playwright is resolved from a global install rather than added to package.json, for the same
// reason. See README-e2e notes in phase4-5-work.md.

import test, { after, before, beforeEach, describe } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync, spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const API_PORT = 3101; // not 3001, so a dev server can stay running while these tests execute
const WEB_PORT = 5273;

// Playwright is resolved from wherever it happens to live — a local install, a global one, or
// nested inside a globally installed @playwright/cli — rather than being added to package.json.
// Playwright ships as CommonJS, so `chromium` may sit on the namespace or on `default`
// depending on how it is resolved. Check both, or the suite silently skips itself.
const chromiumFrom = module => module?.chromium ?? module?.default?.chromium ?? null;

async function loadChromium() {
  for (const specifier of ['playwright', '@playwright/test']) {
    try {
      const found = chromiumFrom(await import(specifier));
      if (found) return found;
    } catch { /* try the next */ }
  }
  try {
    const globalRoot = execFileSync('npm', ['root', '-g'], { encoding: 'utf8' }).trim();
    const searchPaths = [globalRoot, path.join(globalRoot, '@playwright', 'cli'), root];
    const require = createRequire(import.meta.url);
    for (const specifier of ['playwright', '@playwright/test']) {
      try {
        const entry = require.resolve(specifier, { paths: searchPaths });
        const found = chromiumFrom(await import(pathToFileURL(entry).href));
        if (found) return found;
      } catch { /* try the next */ }
    }
  } catch { /* fall through to skip */ }
  return null;
}

// The frontend hardcodes http://localhost:3001, so serve a copy of web/ with the API base
// rewritten to this run's port. Keeps the suite independent of any dev server.
function createWebServer(apiPort) {
  const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css' };
  return http.createServer((req, res) => {
    const name = req.url === '/' ? '/index.html' : req.url.split('?')[0];
    const file = path.join(root, 'web', path.normalize(name).replace(/^(\.\.[/\\])+/, ''));
    if (!fs.existsSync(file)) { res.writeHead(404); return res.end('not found'); }
    const body = fs.readFileSync(file, 'utf8').replaceAll('http://localhost:3001', `http://localhost:${apiPort}`);
    res.writeHead(200, { 'content-type': types[path.extname(file)] ?? 'text/plain' });
    res.end(body);
  });
}

// Prefer Playwright's own browser build; fall back to an installed Google Chrome so the suite
// runs without downloading ~150MB of browser on a machine that already has one.
async function launchBrowser() {
  try {
    return await chromium.launch();
  } catch (error) {
    if (!/Executable doesn't exist/.test(error.message)) throw error;
    return chromium.launch({ channel: 'chrome' });
  }
}

const chromium = await loadChromium();

describe('funnel report end to end', { skip: chromium ? false : 'playwright not installed' }, () => {
  let api;
  let web;
  let browser;
  let page;

  const startApi = async () => {
    api = spawn(process.execPath, ['server.js'], { cwd: root, env: { ...process.env, PORT: String(API_PORT) } });
    for (let attempt = 0; attempt < 50; attempt += 1) {
      try {
        const response = await fetch(`http://localhost:${API_PORT}/api/overview`);
        if (response.ok) return;
      } catch { /* not up yet */ }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error('API did not start');
  };

  const stopApi = async () => {
    if (!api) return;
    const exited = new Promise(resolve => api.once('exit', resolve));
    api.kill();
    await exited;
    api = null;
  };

  // Read the report's own label, never the current selection — that distinction is the point.
  const meta = () => page.locator('.report-meta').innerText();
  const rows = () => page.locator('table.report tbody tr').allInnerTexts()
    .then(list => list.map(row => row.replace(/\s+/g, ' ').trim()));

  // Wait until no request is in flight and the report matches current state.
  const settled = () => page.waitForFunction(
    () => {
      const text = document.querySelector('.report-meta')?.textContent ?? '';
      return text.length > 0 && !text.includes('updating');
    },
    null,
    { timeout: 15000 }
  );

  const setDelay = async ms => {
    await page.fill('#delay', String(ms));
    await page.dispatchEvent('#delay', 'change');
  };

  const revisionOf = async () => Number((await meta()).match(/revision (\d+)/)?.[1] ?? 0);

  // Arrange helper: toggle a user's exclusion and wait for the report to actually reconcile.
  // Waiting on `settled()` alone is not enough — it can return before the request even starts,
  // while the meta line has not yet gained its "updating" suffix. Waiting for the revision to
  // advance is the only reliable signal that the change landed.
  const setExclusionAndSettle = async (userId, excluded) => {
    const before = await revisionOf();
    await page.click(`[data-${excluded ? 'exclude' : 'include'}="${userId}"]`);
    await page.waitForSelector(`[data-${excluded ? 'include' : 'exclude'}="${userId}"]`);
    await page.waitForFunction(
      previous => {
        const text = document.querySelector('.report-meta')?.textContent ?? '';
        const match = text.match(/revision (\d+)/);
        return Boolean(match) && Number(match[1]) > previous && !text.includes('updating');
      },
      before,
      { timeout: 15000 }
    );
  };

  const excludeAndSettle = userId => setExclusionAndSettle(userId, true);
  const includeAndSettle = userId => setExclusionAndSettle(userId, false);

  before(async () => {
    web = createWebServer(API_PORT);
    await new Promise(resolve => web.listen(WEB_PORT, resolve));
    browser = await launchBrowser();
    page = await browser.newPage();
    // window.prompt would otherwise block the page forever in a headless run.
    page.on('dialog', dialog => dialog.accept('internal QA'));
  });

  // Every test starts from a fresh server (revision 1, nothing excluded) and a fresh page, so
  // no test inherits another's dataset. Without this the suite is order-dependent: one failure
  // cascades into misleading failures in every test after it.
  beforeEach(async () => {
    await stopApi();
    await startApi();
    await page.goto(`http://localhost:${WEB_PORT}/`);
    await page.waitForSelector('table.report');
    await settled();
  });

  after(async () => {
    await browser?.close();
    await new Promise(resolve => web?.close(resolve));
    await stopApi();
  });

  test('renders the fixture oracle for the default segment', async () => {
    assert.equal(await meta(), 'segment: all · revision 1');
    assert.deepEqual(await rows(), [
      'control 4 4 (100.0%) 4 (100.0%) 2 (50.0%)',
      'treatment 4 4 (100.0%) 4 (100.0%) 3 (75.0%)'
    ]);
  });

  test('filters by segment', async () => {
    await page.selectOption('#segment', 'enterprise');
    await page.waitForFunction(() => document.querySelector('.report-meta').textContent.includes('enterprise'));
    assert.equal(await meta(), 'segment: enterprise · revision 1');
    assert.deepEqual(await rows(), [
      'control 2 2 (100.0%) 2 (100.0%) 1 (50.0%)',
      'treatment 2 2 (100.0%) 2 (100.0%) 2 (100.0%)'
    ]);
    await page.selectOption('#segment', 'all');
    await page.waitForFunction(() => !document.querySelector('.report-meta').textContent.includes('updating'));
  });

  test('a slow older report finishing last never re-renders an excluded user', async () => {
    // The dangerous ordering is the OLD request finishing LAST (AC 11). Giving both requests
    // the same delay would let the stale one land first, where its content is identical to
    // what is already on screen and the test proves nothing. So: start a very slow request,
    // then make the reconciling one fast.
    await setDelay(5000);
    await page.click('#run-report');
    await page.waitForTimeout(200);

    await setDelay(0);
    await page.click('[data-exclude="u-102"]');

    // The fast reconciling report lands almost immediately, with u-102 gone.
    await page.waitForFunction(
      () => document.querySelector('.report-meta').textContent === 'segment: all · revision 2',
      null,
      { timeout: 15000 }
    );
    const reconciled = [
      'control 4 4 (100.0%) 4 (100.0%) 2 (50.0%)',
      'treatment 3 3 (100.0%) 3 (100.0%) 2 (66.7%)'
    ];
    assert.deepEqual(await rows(), reconciled);

    // Now wait out the original 5s request. When it finally lands it carries revision 1 and
    // still counts u-102 — rendering it would put an excluded user back on screen.
    await page.waitForTimeout(6000);
    assert.deepEqual(await rows(), reconciled, 'the stale response must not re-render the excluded user');
    assert.equal(await meta(), 'segment: all · revision 2');
    assert.equal(await page.locator('[data-include="u-102"]').count(), 1);
  });

  test('a slow report for the previous segment finishing last never overwrites the new one', async () => {
    // Arrange: this test needs no exclusions, so it runs entirely at revision 1.
    // Same shape as the exclusion race: the `all` request must finish AFTER the enterprise one.
    await setDelay(5000);
    await page.click('#run-report');
    await page.waitForTimeout(200);

    await setDelay(0);
    await page.selectOption('#segment', 'enterprise');

    // Still labelled `all` while the enterprise report is in flight — never mislabelled.
    assert.match(await meta(), /segment: all .* updating to enterprise/);

    await page.waitForFunction(
      () => document.querySelector('.report-meta').textContent === 'segment: enterprise · revision 1',
      null,
      { timeout: 15000 }
    );
    const enterprise = [
      'control 2 2 (100.0%) 2 (100.0%) 1 (50.0%)',
      'treatment 2 2 (100.0%) 2 (100.0%) 2 (100.0%)'
    ];
    assert.deepEqual(await rows(), enterprise);

    // The `all` response lands last and must be discarded, not rendered under the new label.
    await page.waitForTimeout(6000);
    assert.deepEqual(await rows(), enterprise, 'the `all` response must never overwrite the enterprise report');
    assert.equal(await meta(), 'segment: enterprise · revision 1');
  });

  test('a failed report keeps the last known-good report visible', async () => {
    // Arrange: establish a known-good report of this test's own, rather than inheriting one.
    await setDelay(0);
    await page.click('#run-report');
    await settled();
    const before = await rows();

    await stopApi();
    await page.click('#run-report');
    await page.waitForSelector('.report-error');

    assert.match(await page.locator('.report-error').innerText(), /Report failed/);
    assert.equal(await page.locator('table.report').count(), 1, 'the analysis area must not be cleared');
    assert.deepEqual(await rows(), before);
  });

  test('a server restart is resynced from an authoritative read, not by applying a stale report', async () => {
    // Arrange: the client must know a revision the restarted server will not have, so exclude a
    // user first to reach revision 2.
    await excludeAndSettle('u-102');
    assert.equal(await meta(), 'segment: all · revision 2');

    // The restarted API resets to revision 1, below the revision the client knows. Every funnel
    // response therefore classifies as stale; recovery must come from resyncing against an
    // authoritative (undelayed) endpoint, never from rendering the stale report.
    await stopApi();
    await startApi();
    await page.click('#run-report');
    await page.waitForFunction(
      () => document.querySelector('.report-meta').textContent === 'segment: all · revision 1',
      null,
      { timeout: 15000 }
    );
    assert.equal(await page.locator('.report-error').count(), 0);
    assert.match(await page.locator('.message').innerText(), /server appears to have restarted/);
    // The reset dataset has no exclusions, so u-102 is back in the funnel.
    assert.deepEqual(await rows(), [
      'control 4 4 (100.0%) 4 (100.0%) 2 (50.0%)',
      'treatment 4 4 (100.0%) 4 (100.0%) 3 (75.0%)'
    ]);
  });

  test('a variant with no eligible users shows dashes, not NaN', async () => {
    // Exclude every control user so control's denominators are all zero.
    for (const userId of ['u-100', 'u-103', 'u-105', 'u-107']) await excludeAndSettle(userId);

    const [control] = await rows();
    assert.equal(control, 'control 0 0 (—) 0 (—) 0 (—)');
    const text = await page.locator('table.report').innerText();
    assert.doesNotMatch(text, /NaN|Infinity|null|undefined/);
  });

  test('a stale response on the newest request refetches rather than rendering', async () => {
    // The discard path is covered by the race tests. This is the other branch: the response is
    // the NEWEST request but was computed before a revision the client has since learned about.
    // Both halves must hold at once — mutating the dataset without also advancing the client's
    // known revision would classify as `apply`, proving nothing.
    await setDelay(5000);
    await page.click('#run-report');
    await page.waitForTimeout(200);
    await setDelay(0);

    // Mutate directly, so no funnel request is issued and latestRequestId stays put...
    await page.evaluate(async port => {
      await fetch(`http://localhost:${port}/api/users/u-102/exclusion`, {
        method: 'PATCH',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ excluded: true, reason: 'direct' })
      });
    }, API_PORT);

    // ...then advance the known revision via Refresh, which calls applyRevision but never
    // loadReport. Now the in-flight response is newest-but-behind: exactly `refetch`.
    await page.click('#refresh');
    await page.waitForFunction(() => document.querySelector('.report-meta').textContent.includes('updating to revision 2'));

    await page.waitForFunction(
      () => document.querySelector('.report-meta').textContent === 'segment: all · revision 2',
      null,
      { timeout: 20000 }
    );
    assert.deepEqual(await rows(), [
      'control 4 4 (100.0%) 4 (100.0%) 2 (50.0%)',
      'treatment 3 3 (100.0%) 3 (100.0%) 2 (66.7%)'
    ]);
    assert.equal(await page.locator('.report-error').count(), 0);
    // An empty notice distinguishes the refetch path from resyncRevision, which writes a message.
    assert.equal((await page.locator('.message').innerText()).trim(), '');
  });

  test('the displayed revision never decreases during a normal session', async () => {
    // Scoped to non-restart flow on purpose: resyncRevision deliberately lowers the revision
    // when an authoritative read proves the server restarted, and that case has its own test.
    const seen = [];
    const record = async () => {
      const match = (await meta()).match(/revision (\d+)/);
      if (match) seen.push(Number(match[1]));
    };

    await record();
    await excludeAndSettle('u-102');
    await record();
    await page.click('#refresh');
    await settled();
    await record();
    await includeAndSettle('u-102');
    await record();
    await page.selectOption('#segment', 'enterprise');
    await settled();
    await record();
    await page.click('#run-report');
    await settled();
    await record();

    assert.ok(seen.length >= 6, `expected six samples, got ${seen.length}`);
    for (let i = 1; i < seen.length; i += 1) {
      assert.ok(seen[i] >= seen[i - 1], `revision decreased: ${seen.join(' → ')}`);
    }
    assert.ok(seen.at(-1) > seen[0], `revision should have advanced overall: ${seen.join(' → ')}`);
  });

  test('exclusion validation still rejects an empty reason', async () => {
    page.removeAllListeners('dialog');
    page.on('dialog', dialog => dialog.accept('   '));
    try {
      await page.click('[data-exclude="u-100"]');
      await page.waitForFunction(() => document.querySelector('.message').textContent === 'invalid_reason');
      assert.equal(await page.locator('[data-exclude="u-100"]').count(), 1, 'the user must remain included');
      assert.equal(await meta(), 'segment: all · revision 1', 'a rejected exclusion must not move the revision');
    } finally {
      // Restore the default handler so this test cannot affect any other.
      page.removeAllListeners('dialog');
      page.on('dialog', dialog => dialog.accept('internal QA'));
    }
  });
});
