import assert from 'node:assert/strict';
import { readWorkspace, readJsonl } from '../src/data.mjs';
import { createStore } from '../src/store.mjs';

const workspace = readWorkspace();
const events = readJsonl('consent_events.jsonl');
const history = readJsonl('send_history.jsonl');
assert.ok(workspace.contacts.length > 0 && workspace.campaigns.length > 0);
assert.equal(new Set(workspace.contacts.map(item => item.id)).size, workspace.contacts.length);
assert.equal(new Set(workspace.campaigns.map(item => item.id)).size, workspace.campaigns.length);
const ids = new Set(workspace.contacts.map(item => item.id));
for (const event of events) { assert.ok(ids.has(event.contactId)); assert.ok(event.eventId && event.effectiveAt && event.receivedAt); }
for (const item of history) { assert.ok(item.id && item.phone && item.createdAt); }
assert.equal(createStore().listContacts().total, workspace.contacts.length);
console.log(`Fixture baseline verified: ${workspace.campaigns.length} campaigns / ${workspace.contacts.length} contacts / ${events.length} consent events / ${history.length} history records`);
