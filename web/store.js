export function createState() {
  return { filters: { warehouse: '', status: '' }, cases: [], selectedId: null, selected: null, datasetRevision: null, batchIds: [], busy: false, error: '' };
}
export function findSelected(state) { return state.cases.find(c => c.id === state.selectedId) || state.selected; }
