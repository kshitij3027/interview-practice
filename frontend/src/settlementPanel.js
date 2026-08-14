function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[char]));
}

function renderAllocations(row) {
  if (row.status !== 'valid') return escapeHtml(row.error ?? '');
  const allocations = (row.allocations ?? []).map(a =>
    `<li>${escapeHtml(a.invoice_id)}: $${(a.applied_cents / 100).toFixed(2)} applied · $${(a.remaining_after_cents / 100).toFixed(2)} remaining on invoice</li>`
  ).join('');
  const creditRemainder = row.credit_remainder_cents
    ? `<p class="credit-remainder">Credit remainder: $${(row.credit_remainder_cents / 100).toFixed(2)}</p>`
    : '';
  return `<ul>${allocations}</ul>${creditRemainder}`;
}

function renderRow(row) {
  return `<tr class="settlement-row settlement-row-${row.status}">
    <td>${escapeHtml(row.payment_id)}</td>
    <td><span class="badge badge-${row.status}">${row.status}</span></td>
    <td>${renderAllocations(row)}</td>
  </tr>`;
}

export function renderSettlementPanel(state) {
  const { csvText, preview, settlementBusy, settlementError, settlementCommitted } = state;
  const hasValidRow = Boolean(preview?.rows?.some(row => row.status === 'valid'));

  return `<section class="panel settlement-panel">
    <h2>Settlement import</h2>
    ${settlementError ? `<p class="error">${escapeHtml(settlementError)}</p>` : ''}
    ${settlementCommitted === 'already_committed' ? `<p class="success">This settlement was already committed — no changes were re-applied.</p>` : ''}
    ${settlementCommitted === 'committed' ? `<p class="success">Settlement committed — account balances updated below.</p>` : ''}
    <form id="settlement-preview-form">
      <label for="settlement-csv">Settlement CSV</label>
      <textarea id="settlement-csv" name="csvText" rows="6" placeholder="payment_id,customer_ref,amount" ${settlementBusy ? 'disabled' : ''}>${escapeHtml(csvText)}</textarea>
      <button type="submit" ${settlementBusy ? 'disabled' : ''}>${settlementBusy ? 'Previewing…' : 'Preview'}</button>
    </form>
    ${preview ? `
      <h3>Preview results</h3>
      <table>
        <thead><tr><th>Payment</th><th>Status</th><th>Detail</th></tr></thead>
        <tbody>${preview.rows.map(renderRow).join('')}</tbody>
      </table>
      ${hasValidRow ? `<button id="settlement-commit" type="button" ${settlementBusy ? 'disabled' : ''}>${settlementBusy ? 'Committing…' : 'Commit settlement'}</button>` : '<p>No valid rows to commit.</p>'}
    ` : ''}
  </section>`;
}
