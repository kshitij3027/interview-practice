import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const fixtureUrl = new URL('../fixtures/orders.json', import.meta.url);
const safeInt = (value) => Number.isSafeInteger(value) && value >= 0;

export function loadOrders(file = fileURLToPath(fixtureUrl)) {
  const orders = JSON.parse(readFileSync(file, 'utf8'));
  if (!Array.isArray(orders)) throw new Error('orders fixture must be an array');
  const ids = new Set();
  for (const order of orders) {
    if (typeof order.id !== 'string' || !order.id || ids.has(order.id)) throw new Error('invalid or duplicate order ID');
    ids.add(order.id);
    if (!['delivered', 'in_transit', 'cancelled'].includes(order.status)) throw new Error('invalid order status');
    if (!Number.isFinite(Date.parse(order.placedAt)) || !/[+-]\d\d:\d\d$|Z$/.test(order.placedAt)) throw new Error('invalid placedAt');
    if (typeof order.customer !== 'string' || typeof order.note !== 'string' || !safeInt(order.revision) || !safeInt(order.shippingCents)) throw new Error('invalid order metadata');
    if (!Array.isArray(order.lines) || !order.lines.length || !Array.isArray(order.refunds)) throw new Error('invalid order lines or refunds');
    const lineIds = new Set();
    for (const line of order.lines) {
      if (!line.lineId || lineIds.has(line.lineId)) throw new Error('duplicate line ID');
      lineIds.add(line.lineId);
      for (const key of ['quantity','unitPriceCents','discountCents','taxCents','refundedQuantity','refundedCents']) {
        if (!safeInt(line[key])) throw new Error(`invalid ${key}`);
      }
      if (line.quantity === 0 || line.refundedQuantity > line.quantity) throw new Error('invalid line quantities');
      if (line.discountCents > line.unitPriceCents * line.quantity) throw new Error('invalid line discount');
      if (!Number.isSafeInteger(line.unitPriceCents * line.quantity - line.discountCents + line.taxCents)) throw new Error('line amount overflow');
    }
  }
  return orders;
}
