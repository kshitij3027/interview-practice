export const state = {
  employees: [],
  shifts: [],
  site: 'all',
  selectedShiftId: null,
  selectedShift: null,
  loading: false,
  saving: false,
  error: '',
  notice: '',
};

export function selectedShiftFromList() {
  return state.shifts.find((shift) => shift.id === state.selectedShiftId) || null;
}
