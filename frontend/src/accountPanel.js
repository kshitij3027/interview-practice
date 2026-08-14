export function renderAccountPanel(detail, busy) {
  if (!detail) return '<section><p>Select an account.</p></section>';
  const invoices = detail.invoices.map(invoice => `<li>${invoice.id} · due ${invoice.due_date} · $${(invoice.remaining_cents / 100).toFixed(2)} remaining · ${invoice.status}</li>`).join('');
  return `<section class="panel">
    <h2>${detail.account.name}</h2>
    <p>Available credit: <strong>$${(detail.account.credit_cents / 100).toFixed(2)}</strong></p>
    <h3>Invoices</h3><ul>${invoices}</ul>
    <form id="credit-form">
      <h3>Manual customer credit</h3>
      <input name="amount" aria-label="credit amount" type="number" min="0.01" step="0.01" placeholder="Amount" required />
      <input name="reason" aria-label="credit reason" placeholder="Reason" required />
      <button ${busy ? 'disabled' : ''}>${busy ? 'Saving…' : 'Add credit'}</button>
    </form>
  </section>`;
}
