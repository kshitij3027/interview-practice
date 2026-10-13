import {api} from './api.js';
import {$,node} from './view-state.js';
import {search,resetTenant} from './search-view.js';
import {saveNote} from './detail-view.js';
$('filters').onsubmit = event => {event.preventDefault();search();};
$('tenant').onchange = resetTenant;
$('note-form').onsubmit = saveNote;
try {
  const tenants = await api('/api/tenants');
  for(const t of tenants) {
    const option = node('option',t.name);
    option.value = t.id;
    $('tenant').append(option);
  }
  if(tenants.length) await search();
} catch(error) { $('summary').textContent = error.message; }
