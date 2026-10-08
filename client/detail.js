import { request, $ } from './api-client.js';
import { renderDetail } from './detail_view.js';
export function setupDetail(onChange) {
  let selected=null, generation=0, current=null;
  async function load(id=selected) {
    const seq=++generation;
    try {
      const data=await request('/api/shipments/'+encodeURIComponent(id));
      if(seq!==generation||id!==selected)return;
      current=data;
      renderDetail(data);
    }catch(error) {
      if(seq===generation&&id===selected)$('#detail-status').textContent=error.message;
    }
  }
  function select(id) {
    selected=id;current=null;generation++;
    $('#note-form').hidden=true;
    $('#detail').textContent='Loading shipment…';
    $('#detail-status').textContent='';
    load(id);
  }
  $('#note-form').addEventListener('submit',async event=>{
    event.preventDefault();
    const id=selected, before=current, seq=generation;
    if(!id||!before)return;
    const button=$('#note-form button');
    button.disabled=true;
    $('#detail-status').textContent='Saving…';
    try{
      const response=await request('/api/shipments/'+encodeURIComponent(id)+'/note',{
        method:'PATCH',headers:{'content-type':'application/json'},
        body:JSON.stringify({expectedRevision:before.shipment.revision,note:$('#note').value})
      });
      if(seq!==generation||id!==selected)return;
      current=response;
      $('#detail-status').textContent=response.changed?'Note saved.':'No changes.';
      renderDetail(response);onChange();
    }catch(error){
      if(seq===generation&&id===selected)$('#detail-status').textContent=error.message;
    }finally{button.disabled=false;}
  });
  return {select,load};
}
