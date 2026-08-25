export const state = {
  cases: [],
  selectedCase: null,
  filters: {status: '', priority: ''},
  loading: false,
  error: ''
};

export function setCases(cases) { state.cases = cases; }
export function setSelected(caseItem) { state.selectedCase = caseItem; }
