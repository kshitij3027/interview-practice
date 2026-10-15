import { readWorkspace, readJsonl } from './data.mjs';
import { compactSearch, expectedRevision, fail, noteValue } from './validation.mjs';

export function createStore({ workspace = readWorkspace(), consentEvents = readJsonl('consent_events.jsonl'), sendHistory = readJsonl('send_history.jsonl') } = {}) {
  const contacts = new Map(workspace.contacts.map(contact => [contact.id, structuredClone(contact)]));
  const campaigns = new Map(workspace.campaigns.map(campaign => [campaign.id, structuredClone(campaign)]));
  const feed = structuredClone(consentEvents);
  const history = structuredClone(sendHistory);
  let datasetRevision = workspace.datasetRevision;

  const snapshot = contact => ({ ...structuredClone(contact), datasetRevision });

  function listContacts({ q = '', segment = '', status = '' } = {}) {
    const term = compactSearch(q);
    const items = [...contacts.values()].filter(contact =>
      (!segment || contact.segment === segment) &&
      (!status || contact.status === status) &&
      (!term || [contact.name, contact.phone, contact.id].some(field => compactSearch(field).includes(term)))
    ).sort((a, b) => a.name.localeCompare(b.name, 'en') || a.id.localeCompare(b.id, 'en'));
    return { items: items.map(contact => structuredClone(contact)), total: items.length, datasetRevision };
  }

  function listCampaigns() {
    return { items: [...campaigns.values()].sort((a, b) => a.id.localeCompare(b.id)).map(item => structuredClone(item)), datasetRevision };
  }

  function getContact(id) {
    const contact = contacts.get(id);
    if (!contact) fail(404, 'not_found', 'Unknown contact');
    return snapshot(contact);
  }

  function getCampaign(id) {
    const campaign = campaigns.get(id);
    if (!campaign) fail(404, 'not_found', 'Unknown campaign');
    return { ...structuredClone(campaign), datasetRevision };
  }

  function updateContactNote(id, body) {
    const contact = contacts.get(id);
    if (!contact) fail(404, 'not_found', 'Unknown contact');
    const revision = expectedRevision(body?.expectedRevision);
    if (revision !== contact.revision) fail(409, 'stale_revision', 'Contact changed. Refresh before saving.');
    const note = noteValue(body?.note);
    if (note !== contact.note) {
      contact.note = note;
      contact.revision += 1;
      datasetRevision += 1;
    }
    return snapshot(contact);
  }

  return { listContacts, listCampaigns, getContact, getCampaign, updateContactNote };
}
