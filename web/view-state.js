export const $ = id => document.getElementById(id);
export const state = {tenantId:null, selectedId:null, article:null, searchSeq:0, detailSeq:0};
export const node = (tag, text) => {
  const el = document.createElement(tag);
  el.textContent = text;
  return el;
};
