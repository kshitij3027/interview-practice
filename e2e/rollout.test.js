import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { expect, test } from 'playwright/test';
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

test.describe.configure({ mode: 'serial' });

async function withApp(page, fn) {
  const api = http.createServer(makeHandler(createStore()));
  const web = http.createServer(staticHandler);
  try {
    await listen(api, 3001);
    await listen(web);
    return await fn(page, `http://127.0.0.1:${web.address().port}`);
  } finally {
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

test('rollout preview preserves inputs, escapes exclusions and blocks divergent apply', async ({ page }) => withApp(page, async (page, url) => {
  let dialogs = 0;
  page.on('dialog', dialog => {
    dialogs += 1;
    dialog.dismiss();
  });

  await page.goto(url);
  await page.getByText('Acme Labs').waitFor();

  await calculateEuPaid(page);
  const results = page.locator('#rollout-results');
  await expect(page.waitForEvent('dialog', { timeout: 200 })).rejects.toThrow();
  expect(dialogs).toBe(0);
  await expect(results.getByText('Bright Systems')).toBeVisible();
  await expect(results.getByText('acct-106')).toBeVisible();
  await expect(results.getByText('acct-999')).toBeVisible();
  await expect(page.locator('#rollout-apply')).toBeEnabled();

  await page.fill('#rollout-exclude', '<img src=x onerror=alert(1)>');
  await page.click('#rollout-calculate');
  await page.locator('#rollout-results').getByText('<img src=x onerror=alert(1)>').waitFor();
  await expect(page.waitForEvent('dialog', { timeout: 200 })).rejects.toThrow();
  expect(dialogs).toBe(0);

  await calculateEuPaid(page);
  await page.fill('#rollout-percentage', '61');
  await page.getByText('Inputs changed since this calculation').waitFor();
  await expect(page.locator('#rollout-apply')).toBeDisabled();
  await page.fill('#rollout-percentage', '60');
  await expect(page.locator('#rollout-apply')).toBeEnabled();

  await page.selectOption('#rollout-cohort', 'c-pro-us');
  await page.getByText('Inputs changed since this calculation').waitFor();
  await expect(page.locator('#rollout-apply')).toBeDisabled();
  await page.selectOption('#rollout-cohort', 'c-eu-paid');
  await expect(page.locator('#rollout-apply')).toBeEnabled();

  await page.fill('#rollout-exclude', 'acct-106, acct-999, acct-101');
  await page.getByText('Inputs changed since this calculation').waitFor();
  await expect(page.locator('#rollout-apply')).toBeDisabled();
  await page.fill('#rollout-exclude', 'acct-106, acct-999');
  await expect(page.locator('#rollout-apply')).toBeEnabled();
}));

test('rollout apply reconciles revisions and stale previews disable apply', async ({ page }) => withApp(page, async (page, url) => {
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
  await expect(page.locator('#rollout-apply')).toBeDisabled();

  await page.click('button[data-id="acct-101"][data-v="true"]');
  await page.getByText('Flag revision 3').waitFor();
  await page.click('#rollout-calculate');
  await page.getByText('Calculated at flag revision 3').waitFor();
  await expect(page.locator('#rollout-apply')).toBeEnabled();
  await page.click('button[data-id="acct-101"][data-v="false"]');
  await page.getByText('Flag revision 4').waitFor();
  await page.getByText('Flag changed since this calculation').waitFor();
  await expect(page.locator('#rollout-apply')).toBeDisabled();
}));

test('stale apply shows conflict, preserves form and recovers after recalculation', async ({ page }) => withApp(page, async (page, url) => {
  await page.goto(url);
  await page.getByText('Flag revision 1').waitFor();

  await page.selectOption('#rollout-cohort', 'c-large-ent');
  await page.fill('#rollout-percentage', '100');
  await page.fill('#rollout-exclude', 'acct-777, acct-777');
  await page.click('#rollout-calculate');
  await page.locator('#rollout-results').getByText('Selected (2)', { exact: true }).waitFor();

  const override = await page.evaluate(async () => {
    const res = await fetch('http://localhost:3001/api/flags/smart-compose/override', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ accountId: 'acct-101', enabled: true, expectedRevision: 1 })
    });
    return res.json();
  });
  expect(override.flag.revision).toBe(2);

  await page.click('#rollout-apply');
  await page.getByText('Another change landed (flag is now revision 2). Recalculate to continue.').waitFor();
  await expect(page.locator('#rollout-apply')).toBeDisabled();
  await expect(page.locator('#rollout-cohort')).toHaveValue('c-large-ent');
  await expect(page.locator('#rollout-percentage')).toHaveValue('100');
  await expect(page.locator('#rollout-exclude')).toHaveValue('acct-777, acct-777');

  const afterConflict = await page.evaluate(async () => {
    const res = await fetch('http://localhost:3001/api/flags/smart-compose/accounts');
    const body = await res.json();
    return body.accounts
      .filter(account => account.id === 'acct-105' || account.id === 'acct-108')
      .map(account => account.override);
  });
  expect(afterConflict).toEqual([null, null]);

  await page.click('#rollout-calculate');
  await page.getByText('Calculated at flag revision 2').waitFor();
  await expect(page.locator('#rollout-conflict')).toBeEmpty();
  await expect(page.locator('#rollout-apply')).toBeEnabled();
}));
