export const state = { reps:[], items:[], nextCursor:'', cursorStack:[''], owner:'', stage:'', q:'', selectedId:'', message:'' };
export function currentCursor(){ return state.cursorStack[state.cursorStack.length-1] || ''; }
export function resetPaging(){ state.cursorStack=['']; state.nextCursor=''; }
