export const state = {
  segment: "",
  customers: [],
  selectedId: null,
  detail: null,
  datasetRevision: null,
  busy: false,
  error: ""
};

export function setList(payload) {
  state.customers = payload.customers;
  state.datasetRevision = payload.dataset_revision;
  if (state.selectedId && !state.customers.some(c => c.id === state.selectedId)) {
    state.selectedId = null;
    state.detail = null;
  }
}

export function setDetail(payload) {
  state.detail = payload.customer;
  state.selectedId = payload.customer.id;
  state.datasetRevision = Math.max(state.datasetRevision ?? 0, payload.dataset_revision);
}
