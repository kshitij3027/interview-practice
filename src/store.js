import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {rankArticles} from './search.js';

const fixture = fileURLToPath(new URL('../fixtures/catalog.json', import.meta.url));
const clone = value => structuredClone(value);
const issue = (status, code, message) => Object.assign(new Error(message), {status, code});

export function createStore(seed = JSON.parse(readFileSync(fixture, 'utf8'))) {
  const tenants = new Map(seed.tenants.map(t => [t.id, clone(t)]));
  const articles = new Map(seed.articles.map(a => [a.id, clone(a)]));

  function tenant(id) {
    const t = tenants.get(id);
    if (!t) throw issue(404, 'tenant_not_found', 'Unknown tenant');
    return t;
  }
  function article(tenantId, id) {
    tenant(tenantId);
    const a = articles.get(id);
    if (!a || a.tenantId !== tenantId) throw issue(404, 'article_not_found', 'Article unavailable');
    return a;
  }
  return {
    tenants: () => [...tenants.values()].map(clone).sort((a, b) => a.name.localeCompare(b.name)),
    search({tenantId, query = '', category = 'all', limit = 10}) {
      const t = tenant(tenantId);
      const ranked = rankArticles([...articles.values()].filter(a => a.tenantId === tenantId), {query, category, limit});
      return {...ranked, tenantId, tenantRevision: t.revision, query, category};
    },
    article: (tenantId, id) => ({...clone(article(tenantId, id)), tenantRevision: tenant(tenantId).revision}),
    updateNote({tenantId, id, expectedRevision, note}) {
      const a = article(tenantId, id);
      if (!Number.isSafeInteger(expectedRevision) || expectedRevision < 0)
        throw issue(400, 'bad_revision', 'expectedRevision must be a nonnegative integer');
      if (typeof note !== 'string' || note.trim().length > 300)
        throw issue(400, 'bad_note', 'note must be text of at most 300 characters');
      if (a.revision !== expectedRevision) throw issue(409, 'stale_article', 'Article changed; reload and try again');
      const next = note.trim();
      if (next !== a.note) { a.note = next; a.revision += 1; tenant(tenantId).revision += 1; }
      return {...clone(a), tenantRevision: tenant(tenantId).revision};
    }
  };
}
