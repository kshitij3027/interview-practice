import { loadOrders } from './model.js';

export class ApiError extends Error {
  constructor(status, message, details = {}) { super(message); this.status = status; this.details = details; }
}

const snapshot = (value) => structuredClone(value);

export class OrderStore {
  constructor(orders = loadOrders()) {
    this.orders = new Map(orders.map((order) => [order.id, snapshot(order)]));
    this.datasetRevision = 1;
  }

  list({ search = '', status = '' } = {}) {
    if (status && !['delivered', 'in_transit', 'cancelled'].includes(status)) throw new ApiError(400, 'invalid status filter');
    const term = search.trim().toLowerCase();
    const rows = [...this.orders.values()]
      .filter((order) => (!status || order.status === status) && (!term || `${order.id} ${order.customer}`.toLowerCase().includes(term)))
      .sort((a, b) => Date.parse(b.placedAt) - Date.parse(a.placedAt) || a.id.localeCompare(b.id));
    return { orders: rows.map(({ id, customer, placedAt, status, note, revision }) => ({ id, customer, placedAt, status, note, revision })), datasetRevision: this.datasetRevision };
  }

  detail(id) {
    const order = this.orders.get(id);
    if (!order) throw new ApiError(404, 'order not found');
    return { order: snapshot(order), datasetRevision: this.datasetRevision };
  }

  updateNote(id, { expectedRevision, note } = {}) {
    const order = this.orders.get(id);
    if (!order) throw new ApiError(404, 'order not found');
    if (!Number.isSafeInteger(expectedRevision) || expectedRevision < 0 || typeof note !== 'string' || note.length > 500) {
      throw new ApiError(400, 'invalid note request');
    }
    if (expectedRevision !== order.revision) throw new ApiError(409, 'stale order revision', { currentRevision: order.revision });
    const normalized = note.trim();
    if (normalized !== order.note) {
      order.note = normalized;
      order.revision++;
      this.datasetRevision++;
    }
    return this.detail(id);
  }
}
