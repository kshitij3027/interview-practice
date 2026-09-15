export const state = {
  statusFilter: "all",
  campaigns: [],
  selectedId: null,
  selected: null,
  datasetRevision: null,
  loadingList: false,
  loadingDetail: false,
  savingStatus: false,
  error: null,
};

export function selectedSummary() {
  return state.campaigns.find((campaign) => campaign.id === state.selectedId) || null;
}
