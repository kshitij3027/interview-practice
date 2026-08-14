export function createStore() {
  const state = {
    accounts: [],
    selectedId: null,
    detail: null,
    error: '',
    creditBusy: false,
  };
  const listeners = new Set();

  return {
    get: () => state,
    set(patch) {
      Object.assign(state, patch);
      listeners.forEach(listener => listener(state));
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
