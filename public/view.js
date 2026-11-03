export const $ = id => document.getElementById(id);
export function element(tag, text, className = '') {
  const node = document.createElement(tag);
  node.textContent = text;
  if (className) node.className = className;
  return node;
}
export function lotRow(lot, active) {
  const button = element('button', '', 'lot' + (active ? ' active' : ''));
  button.type = 'button'; button.dataset.id = lot.id;
  const content = element('div');
  content.append(element('strong', lot.id), element('small', `${lot.product} · ${lot.plantId} · ${lot.quantityKg} kg`, 'tiny'));
  button.append(content, element('span', lot.status, `badge ${lot.status}`));
  return button;
}
export function heading(tag, text) { return element(tag, text); }
