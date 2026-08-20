export const state = {
  accounts: [],
  plans: [],
  selectedAccount: null,
  loading: false,
  error: '',
};

export function setState(patch) {
  Object.assign(state, patch);
  window.dispatchEvent(new CustomEvent('statechange'));
}
