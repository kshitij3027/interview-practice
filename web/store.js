export const state = { orders: [], selectedOrderId: null, selectedOrder: null, inventory: [], inventoryRevision: null, skuFilter: "", loading: false, error: null, };
export function selectedOrderSummary() { const o = state.selectedOrder; if (!o) return "No order selected"; return `${o.customer} · ${o.shipping_zone} · ${o.status} · r${o.revision}`; }
