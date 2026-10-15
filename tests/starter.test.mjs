import test from 'node:test';
import assert from 'node:assert/strict';
import { createStore } from '../src/store.mjs';
import { createServer } from '../src/http.mjs';

function store() { return createStore(); }

test('campaigns are available and sorted by ID', () => {
  const campaigns = store().listCampaigns();
  assert.equal(campaigns.items.length, 3);
  assert.deepEqual(campaigns.items.map(c => c.id), ['camp-events', 'camp-launch', 'camp-renewal']);
});

test('contact list filters and searches case insensitively', () => {
  const s = store();
  assert.deepEqual(s.listContacts({q: ' aShA '}).items.map(x => x.id), ['c-101']);
  assert.equal(s.listContacts({segment:'launch', status:'archived'}).total, 1);
});

test('note updates trim input and count revisions exactly once', () => {
  const s = store();
  const before = s.getContact('c-101');
  const changed = s.updateContactNote('c-101', {expectedRevision:2, note:' Updated '});
  assert.equal(changed.note, 'Updated');
  assert.equal(changed.revision, before.revision + 1);
  assert.equal(changed.datasetRevision, before.datasetRevision + 1);
  const same = s.updateContactNote('c-101', {expectedRevision:3, note:'Updated'});
  assert.equal(same.revision, changed.revision);
  assert.equal(same.datasetRevision, changed.datasetRevision);
});

test('stale edits fail without mutation', () => {
  const s = store();
  assert.throws(() => s.updateContactNote('c-101', {expectedRevision:1, note:'foo'}), {status:409});
  assert.equal(s.getContact('c-101').note, 'VIP attendee');
});

test('unknown contacts and bad note requests fail clearly', () => {
  const s = store();
  assert.throws(() => s.getContact('missing'), {status:404});
  assert.throws(() => s.updateContactNote('c-101', {expectedRevision:2, note:null}), {status:400});
});

test('HTTP serves health and static app', async () => {
  const server = createServer(store());
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    const base = `http://127.0.0.1:${server.address().port}`;
    assert.deepEqual(await (await fetch(`${base}/api/health`)).json(), {ok:true});
    const page = await (await fetch(base)).text();
    assert.match(page, /WaveSend/);
    const contacts = await (await fetch(`${base}/api/contacts?segment=renewal`)).json();
    assert.equal(contacts.total, 2);
  } finally { await new Promise(resolve => server.close(resolve)); }
});
