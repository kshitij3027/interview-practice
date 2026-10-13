import {api, params} from './api.js';
import {$, state, node} from './view-state.js';
import {detail} from './detail-view.js';
export async function search() {
  const seq = ++state.searchSeq;
  const tenantId = $('tenant').value, q = $('query').value, category = $('category').value;
  state.tenantId = tenantId;
  try {
    const data = await api('/api/articles?' + params({tenantId,q,category,limit:20}));
    if (seq !== state.searchSeq) return;
    $('summary').textContent = `${data.total} matching articles · revision ${data.tenantRevision}`;
    $('results').replaceChildren(...data.results.map(a => {
      const button = node('button', `${a.title} · ${a.category} · score ${a.score}`);
      button.className = 'result';
      button.onclick = () => detail(a.id);
      return button;
    }));
  } catch(error) {if(seq === state.searchSeq) $('summary').textContent = error.message;}
}
export function resetTenant() {
  state.article = null; state.selectedId = null; ++state.detailSeq;
  $('article').replaceChildren(node('p','Select an article.'));
  $('note-form').hidden = true;
  search();
}
