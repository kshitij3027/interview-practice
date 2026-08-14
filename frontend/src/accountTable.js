export function renderAccountTable(accounts, selectedId) {
  const rows = accounts.map(account => `
    <tr data-account-id="${account.id}" class="${selectedId === account.id ? 'selected' : ''}">
      <td>${account.name}</td>
      <td>${account.external_id}</td>
      <td>$${(account.credit_cents / 100).toFixed(2)}</td>
      <td>${account.revision}</td>
    </tr>`).join('');
  return `<section><h2>Customer accounts</h2><table><thead><tr><th>Customer</th><th>External ID</th><th>Credit</th><th>Revision</th></tr></thead><tbody>${rows}</tbody></table></section>`;
}
