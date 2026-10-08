export async function request(url,options) {
  const response=await fetch(url,options);
  const data=await response.json();
  if(!response.ok) throw Error(data.message||'HTTP '+response.status);
  return data;
}
export const $=selector=>document.querySelector(selector);
export function el(tag,text,cls) {
  const node=document.createElement(tag);
  if(text!==undefined)node.textContent=text;
  if(cls)node.className=cls;
  return node;
}
