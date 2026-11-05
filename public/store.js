export const state = { accounts: [], account: '', search: '', status: '', jobs: [], selectedId: null, detail: null, listEpoch: 0, detailEpoch: 0 };
export function resetSelection() { state.selectedId = null; state.detail = null; state.detailEpoch += 1; }
export function selectAccount(account) { if (state.account !== account) { state.account = account; state.listEpoch += 1; resetSelection(); } }
export function selectJob(id) { if (state.selectedId !== id) { state.selectedId = id; state.detail = null; state.detailEpoch += 1; } }
export function currentList(epoch, account) { return epoch === state.listEpoch && account === state.account; }
export function currentDetail(epoch, id, account) { return epoch === state.detailEpoch && id === state.selectedId && account === state.account; }
