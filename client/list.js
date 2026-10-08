import { request, $, el } from './api-client.js';
export function setupList(onSelect) {
  let sequence=0, selected=null;
  async function load() {
    const seq=++sequence;
    const params=new URLSearchParams({
      site:$('#site').value,state:$('#state').value,search:$('#search').value
    });
    $('#list-status').textContent='Loading shipments…';
    try {
      const data=await request('/api/shipments?'+params);
      if(seq!==sequence)return;
      const box=$('#shipments');
      box.replaceChildren();
      for(const s of data.items) {
        const button=el('button',s.id+' · '+s.customer+' · '+s.label+' ('+s.state+')','shipment');
        button.setAttribute('aria-pressed',String(selected===s.id));
        button.addEventListener('click',()=>{selected=s.id;onSelect(s.id);load();});
        box.append(button);
      }
      $('#list-status').textContent=data.items.length+' shipment(s) · data revision '+data.datasetRevision;
    }catch(error){if(seq===sequence)$('#list-status').textContent=error.message;}
  }
  $('#site').addEventListener('change',load);
  $('#state').addEventListener('change',load);
  $('#search').addEventListener('input',load);
  return {load};
}
