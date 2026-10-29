import { listStudios, listAssets, getAsset, saveNote } from './api.js';

const el = id => document.getElementById(id);
const state = { studio: '', status: '', q: '', selected: '', rows: [], asset: null, listSeq: 0, detailSeq: 0 };

function message(text, isError = false) {
  el('message').textContent = text;
  el('message').className = isError ? 'error' : '';
}

function renderList() {
  const container = el('assets');
  container.replaceChildren();
  for (const asset of state.rows) {
    const button = document.createElement('button');
    button.className = asset.id === state.selected ? 'selected' : '';
    button.textContent = `${asset.title} · ${asset.status} · r${asset.revision}`;
    button.addEventListener('click', () => selectAsset(asset.id));
    container.append(button);
  }
  if (!state.rows.length) container.textContent = 'No matching assets.';
}

function renderDetail() {
  const asset = state.asset;
  const panel = el('detail');
  panel.replaceChildren();
  if (!asset) { panel.textContent = 'Choose an asset.'; return; }
  const heading = document.createElement('h2');
  heading.textContent = `${asset.title} (${asset.id})`;
  panel.append(heading);
  const meta = document.createElement('p');
  meta.textContent = `${asset.series} · ${asset.status} · ${asset.durationMs} ms · revision ${asset.revision}`;
  panel.append(meta);
  const captionHeading = document.createElement('h3');
  captionHeading.textContent = 'Published captions';
  panel.append(captionHeading);
  for (const locale of asset.supportedLocales) {
    const section = document.createElement('section');
    const cues = asset.captions[locale] || [];
    const header = document.createElement('h4');
    header.textContent = `${locale} (${cues.length} cues)`;
    section.append(header);
    const pre = document.createElement('pre');
    pre.textContent = cues.map(cue => `${cue.startMs}–${cue.endMs}: ${cue.text}`).join('\n') || 'Not published.';
    section.append(pre);
    panel.append(section);
  }
  const form = document.createElement('form');
  const label = document.createElement('label');
  label.textContent = 'Internal note';
  const textarea = document.createElement('textarea');
  textarea.value = asset.note;
  textarea.required = true;
  label.append(textarea);
  const submit = document.createElement('button');
  submit.textContent = 'Save note';
  form.append(label, submit);
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const id = asset.id, studio = state.studio;
    submit.disabled = true;
    try {
      const result = await saveNote(studio, id, textarea.value, asset.revision);
      if (state.studio === studio && state.selected === id) {
        state.asset = result.asset;
        renderDetail();
        message('Note saved.');
        await refreshList();
      }
    } catch (error) {
      if (state.studio === studio && state.selected === id) {
        message(`${error.message}${error.status === 409 ? ' Reload this asset.' : ''}`, true);
        submit.disabled = false;
      }
    }
  });
  panel.append(form);
}

async function selectAsset(id) {
  state.selected = id;
  state.asset = null;
  renderList(); renderDetail();
  const seq = ++state.detailSeq;
  const studio = state.studio;
  try {
    const result = await getAsset(studio, id);
    if (seq !== state.detailSeq || studio !== state.studio || id !== state.selected) return;
    state.asset = result.asset;
    renderDetail();
  } catch (error) {
    if (seq === state.detailSeq) message(error.message, true);
  }
}

async function refreshList() {
  const seq = ++state.listSeq;
  const studio = state.studio;
  if (!studio) return;
  try {
    const result = await listAssets(studio, state.status, state.q);
    if (seq !== state.listSeq || studio !== state.studio) return;
    state.rows = result.assets;
    el('count').textContent = `${result.total} results`;
    renderList();
  } catch (error) {
    if (seq === state.listSeq) message(error.message, true);
  }
}

async function init() {
  const data = await listStudios();
  const select = el('studio');
  for (const studio of data.studios) {
    const option = document.createElement('option');
    option.value = studio.id;
    option.textContent = studio.name;
    select.append(option);
  }
  state.studio = select.value;
  select.addEventListener('change', () => {
    state.studio = select.value;
    state.selected = ''; state.asset = null; ++state.detailSeq;
    renderDetail(); refreshList();
  });
  el('status').addEventListener('change', event => { state.status = event.target.value; refreshList(); });
  el('search').addEventListener('input', event => { state.q = event.target.value; refreshList(); });
  await refreshList();
}

init().catch(error => message(error.message, true));
