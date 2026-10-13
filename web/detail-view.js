import {api, params} from './api.js';
import {$, state, node} from './view-state.js';
import {search} from './search-view.js';
export async function detail(id) {
  const seq = ++state.detailSeq, tenantId = state.tenantId;
  state.selectedId = id;
  try {
    const a = await api('/api/articles/' + id + '?' + params({tenantId}));
    if(seq !== state.detailSeq || tenantId !== state.tenantId) return;
    state.article = a;
    $('article').replaceChildren(node('h3',a.title),node('p',a.body),node('small',`Revision ${a.revision} · ${a.category}`));
    $('note').value = a.note;
    $('note-form').hidden = false;
  } catch(error) {if(seq === state.detailSeq) $('feedback').textContent = error.message;}
}
export async function saveNote(event) {
  event.preventDefault();
  const a = state.article, tenantId = state.tenantId;
  if(!a) return;
  try {
    const updated = await api('/api/articles/' + a.id + '/note', {
      method:'PATCH', body:JSON.stringify({tenantId,expectedRevision:a.revision,note:$('note').value})
    });
    if(tenantId !== state.tenantId || state.selectedId !== a.id) return;
    state.article = updated;
    await detail(a.id); await search();
    $('feedback').textContent = 'Note saved';
  } catch(error) {$('feedback').textContent = error.message;}
}
