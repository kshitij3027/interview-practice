export const state = { statusFilter: 'all', documents: [], datasetRevision: null, selectedId: null, detail: null, loadingList: false, loadingDetail: false, savingRedaction: false, error: '' };
export function setError(message = '') { state.error = message; }
export function selectedSummary() { return state.documents.find((doc) => doc.id === state.selectedId) || null; }
