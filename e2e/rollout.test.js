import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { createStore } from '../src/dataStore.js';
import { makeHandler } from '../src/routes.js';

const root = fileURLToPath(new URL('..', import.meta.url));
const webRoot = join(root, 'web');
const types = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8']
]);

async function listen(server, port = 0) {
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, () => {
      server.off('error', reject);
      resolve();
    });
  });
}

async function close(server) {
  await new Promise(resolve => server.close(resolve));
}

function staticHandler(req, res) {
  const url = new URL(req.url, 'http://localhost');
  const name = url.pathname === '/' ? '/index.html' : url.pathname;
  const path = join(webRoot, name);
  if (!path.startsWith(webRoot)) {
    res.writeHead(404);
    res.end('not found');
    return;
  }
  readFile(path).then(body => {
    res.writeHead(200, { 'content-type': types.get(extname(path)) || 'application/octet-stream' });
    res.end(body);
  }, () => {
    res.writeHead(404);
    res.end('not found');
  });
}

async function withApp(fn) {
  const api = http.createServer(makeHandler(createStore()));
  const web = http.createServer(staticHandler);
  let browser;
  try {
    await listen(api, 3001);
    await listen(web);
    browser = await chromium.launch();
    const page = await browser.newPage();
    return await fn(page, `http://127.0.0.1:${web.address().port}`);
  } finally {
    if (browser) await browser.close();
    if (web.listening) await close(web);
    if (api.listening) await close(api);
  }
}

async function calculateEuPaid(page) {
  await page.selectOption('#rollout-cohort', 'c-eu-paid');
  await page.fill('#rollout-percentage', '60');
  await page.fill('#rollout-exclude', 'acct-106, acct-999');
  await page.click('#rollout-calculate');
  await page.locator('#rollout-results').getByText('Explicitly overridden (1)').waitFor();
  await page.locator('#rollout-results').getByText('acct-999').waitFor();
}

test('rollout preview preserves inputs, escapes exclusions and blocks divergent apply', () => withApp(async (page, url) => {
  let dialogs = 0;
  page.on('dialog', dialog => {
    dialogs += 1;
    dialog.dismiss();
  });

  await page.goto(url);
  await page.getByText('Acme Labs').waitFor();

  await calculateEuPaid(page);
  const results = page.locator('#rollout-results');
  await assert.rejects(page.waitForEvent('dialog', { timeout: 200 }));
  assert.equal(dialogs, 0);
  await assert.ok(await results.getByText('Bright Systems').isVisible());
  await assert.ok(await results.getByText('acct-106').isVisible());
  await assert.ok(await results.getByText('acct-999').isVisible());
  assert.equal(await page.locator('#rollout-apply').isEnabled(), true);

  await page.fill('#rollout-exclude', '<img src=x onerror=alert(1)>');
  await page.click('#rollout-calculate');
  await page.locator('#rollout-results').getByText('<img src=x onerror=alert(1)>').waitFor();
  await assert.rejects(page.waitForEvent('dialog', { timeout: 200 }));
  assert.equal(dialogs, 0);

  await calculateEuPaid(page);
  await page.fill('#rollout-percentage', '61');
  await page.getByText('Inputs changed since this calculation').waitFor();
  assert.equal(await page.locator('#rollout-apply').isEnabled(), false);
  await page.fill('#rollout-percentage', '60');
  assert.equal(await page.locator('#rollout-apply').isEnabled(), true);

  await page.selectOption('#rollout-cohort', 'c-pro-us');
  await page.getByText('Inputs changed since this calculation').waitFor();
  assert.equal(await page.locator('#rollout-apply').isEnabled(), false);
  await page.selectOption('#rollout-cohort', 'c-eu-paid');
  assert.equal(await page.locator('#rollout-apply').isEnabled(), true);

  await page.fill('#rollout-exclude', 'acct-106, acct-999, acct-101');
  await page.getByText('Inputs changed since this calculation').waitFor();
  assert.equal(await page.locator('#rollout-apply').isEnabled(), false);
  await page.fill('#rollout-exclude', 'acct-106, acct-999');
  assert.equal(await page.locator('#rollout-apply').isEnabled(), true);
}));

test('rollout apply reconciles revisions and stale previews disable apply', () => withApp(async (page, url) => {
  await page.goto(url);
  await page.getByText('Flag revision 1').waitFor();

  await page.selectOption('#rollout-cohort', 'c-large-ent');
  await page.fill('#rollout-percentage', '100');
  await page.fill('#rollout-exclude', '');
  await page.click('#rollout-calculate');
  await page.locator('#rollout-results').getByText('Selected (2)', { exact: true }).waitFor();
  await page.click('#rollout-apply');
  await page.getByText('Applied to').waitFor();
  await page.getByText('Flag revision 2').waitFor();
  await page.getByText('Flag changed since this calculation').waitFor();
  assert.equal(await page.locator('#rollout-apply').isEnabled(), false);

  await page.click('button[data-id="acct-101"][data-v="true"]');
  await page.getByText('Flag revision 3').waitFor();
  await page.click('#rollout-calculate');
  await page.getByText('Calculated at flag revision 3').waitFor();
  assert.equal(await page.locator('#rollout-apply').isEnabled(), true);
  await page.click('button[data-id="acct-101"][data-v="false"]');
  await page.getByText('Flag revision 4').waitFor();
  await page.getByText('Flag changed since this calculation').waitFor();
  assert.equal(await page.locator('#rollout-apply').isEnabled(), false);
}));
