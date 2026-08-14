export function createStore() {
  let state = {
    overview: null,
    users: [],
    revision: 0,
    selectedSegment: 'all',
    message: '',
    loading: false
  };
  const listeners = new Set();
  return {
    get: () => state,
    set: patch => {
      state = { ...state, ...patch };
      for (const listener of listeners) listener(state);
    },
    subscribe: listener => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    }
  };
}
