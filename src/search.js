export function normalizeTerm(value) {
  if (typeof value !== 'string') throw new TypeError('search term must be text');
  return value.normalize('NFKC').trim().toLocaleLowerCase('en-US').replace(/\s+/gu, ' ');
}

function tokens(text) {
  return normalizeTerm(text).split(' ').filter(Boolean);
}

export function baseScore(article, query) {
  const terms = [...new Set(tokens(query))];
  if (!terms.length) return 0;
  const title = normalizeTerm(article.title);
  const body = normalizeTerm(article.body);
  const tags = (article.tags ?? []).map(normalizeTerm);
  return terms.reduce((score, term) => score + (title.includes(term) ? 4 : 0) +
    (body.includes(term) ? 1 : 0) + (tags.includes(term) ? 3 : 0), 0);
}

export function rankArticles(articles, {query = '', category = 'all', limit = 10} = {}) {
  const normalized = normalizeTerm(query);
  const filtered = articles.filter(a => a.published && (category === 'all' || a.category === category))
    .map(article => ({...article, score: baseScore(article, normalized)}))
    .filter(a => !normalized || a.score > 0)
    .sort((a, b) => b.score - a.score || a.id.localeCompare(b.id));
  return {total: filtered.length, results: filtered.slice(0, limit)};
}
