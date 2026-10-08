import { $, el } from './api-client.js';
export function renderDetail(data) {
  const s=data.shipment;
  const rows=[
    ['Customer',s.customer],['Product',s.label],['Route',s.route],
    ['Site',s.site],['State',s.state],
    ['Safe band (°C)',s.minC+' to '+s.maxC],
    ['Max sample gap',s.maxGapSeconds+' seconds'],
    ['Excursion trigger',s.triggerSeconds+' seconds'],
    ['Telemetry rows',String(data.readingCount)],
    ['Temperature hold',s.temperatureHold?'YES':'No'],
    ['Revision',String(s.revision)]
  ];
  const dl=el('dl');
  for(const [label,value] of rows)dl.append(el('dt',label),el('dd',value));
  $('#detail').replaceChildren(dl);
  $('#note').value=s.operatorNote;
  $('#note-form').hidden=false;
}
