import assert from 'node:assert/strict';
import { loadOrders } from '../src/model.js';
import { createApp } from '../src/server.js';

const orders = loadOrders();
const server = createApp();
try {
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  assert.equal((await (await fetch(`${base}/api/health`)).json()).ok, true);
  assert.equal((await (await fetch(`${base}/api/orders`)).json()).orders.length, orders.length);
  assert.match(await (await fetch(base)).text(), /ReturnCredit/);
  console.log(`verified ${orders.length} orders / ${orders.reduce((n, order) => n + order.lines.length, 0)} lines / ${orders.reduce((n, order) => n + order.refunds.length, 0)} historical refunds; HTTP smoke passed`);
} finally { server.close(); }
