export const state = {
  segment: '', accounts: [], selectedId: null, detail: null, datasetRevision: 0, error: ''
};
export function mergeList(payload) {
  state.accounts = payload.accounts;
  state.datasetRevision = Math.max(state.datasetRevision, payload.dataset_revision || 0);
  if (state.selectedId && !state.accounts.some(a => a.id === state.selectedId)) state.selectedId = null;
}
export function mergeDetail(payload) {
  state.detail = payload;
  state.datasetRevision = Math.max(state.datasetRevision, payload.dataset_revision || 0);
  const incoming = payload.account;
  const index = state.accounts.findIndex(a => a.id === incoming.id);
  if (index >= 0) state.accounts[index] = incoming;
}
