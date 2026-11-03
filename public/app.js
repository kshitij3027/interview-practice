import { api } from './api.js';
import { $, element, lotRow } from './view.js';
const state = {selected: null, detail: null, listRequest: 0, detailRequest: 0};
const notice = (text, error = false) => { $('notice').textContent = text; $('notice').classList.toggle('error', error); };
async function list() {
  const token = ++state.listRequest;
  const query = new URLSearchParams({plant: $('plant').value, status: $('status').value, q: $('search').value.trim(), limit: '100'});
  try {
    const result = await api(`/api/lots?${query}`);
    if (token !== state.listRequest) return;
    const parent = $('lot-list'); parent.replaceChildren();
    for (const lot of result.lots) {
      const row = lotRow(lot, state.selected === lot.id);
      row.addEventListener('click', () => select(lot.id)); parent.append(row);
    }
    $('lot-count').textContent = `${result.lots.length} / ${result.total}`;
  } catch (e) { if (token === state.listRequest) notice(e.message, true); }
}
async function select(id) {
  const token = ++state.detailRequest;
  state.selected = id;
  list();
  try {
    const result = await api(`/api/lots/${encodeURIComponent(id)}`);
    if (token !== state.detailRequest || state.selected !== id) return;
    state.detail = result;
    renderDetail();
  } catch (e) { if (token === state.detailRequest) notice(e.message, true); }
}
function renderDetail() {
  const {lot, specification: spec, samples} = state.detail;
  const root = $('details'); root.replaceChildren();
  root.append(element('h2', `${lot.id} · ${lot.product}`));
  const tiles = element('div', '', 'grid');
  const values = [['Plant', lot.plantId], ['Lifecycle', lot.status], ['Quantity', `${lot.quantityKg} kg`], ['Lot revision', String(lot.revision)],
                  ['Target pH', `${spec.phMin} – ${spec.phMax}`], ['Moisture ceiling', `${spec.moistureMaxPct}%`],
                  ['Minimum samples', String(spec.minSamples)], ['Recorded samples', String(samples.length)]];
  for (const [key, value] of values) {
    const tile = element('div', '', 'tile'); tile.append(element('small', key, 'muted'), element('strong', value)); tiles.append(tile);
  }
  root.append(tiles);
  const wrap = element('div', '', 'block');
  const label = element('label', 'Internal operator note');
  const area = element('textarea'); area.value = lot.note; area.id = 'note-input'; label.append(area);
  const save = element('button', 'Save note');
  save.addEventListener('click', async () => {
    const currentId = state.selected; save.disabled = true;
    try {
      const result = await api(`/api/lots/${encodeURIComponent(lot.id)}/note`, {method: 'PATCH', body: JSON.stringify({note: area.value, expectedRevision: lot.revision})});
      if (state.selected !== currentId) return;
      state.detail.lot = result.lot; notice('Note saved.'); renderDetail(); list();
    } catch (e) {
      notice(e.message, true);
      if (e.status === 409 && state.selected === currentId) select(currentId);
    } finally { save.disabled = false; }
  });
  wrap.append(label, save); root.append(wrap);
}
let searchTimeout;
for (const id of ['plant','status']) $(id).addEventListener('change', list);
$('search').addEventListener('input', () => { clearTimeout(searchTimeout); searchTimeout = setTimeout(list, 200); });
$('refresh').addEventListener('click', () => { list(); if (state.selected) select(state.selected); });
try {
  const meta = await api('/api/meta');
  for (const plant of meta.plants) { const option = document.createElement('option'); option.value = plant.id; option.textContent = plant.name; $('plant').append(option); }
  await list();
} catch (e) { notice(e.message, true); }
