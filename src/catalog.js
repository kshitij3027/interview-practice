import fs from 'node:fs';
import { recordsFromCsv } from './csv.js';
import { parseHostPattern, parseMethod, parsePathPattern } from './patterns.js';

const REQUIRED = ['route_id', 'host_pattern', 'method', 'path_pattern', 'priority', 'upstream'];

function canonicalRow(row) {
  return REQUIRED.map((key) => row[key]).join('\u0000');
}

export function buildCatalog(rows) {
  const byId = new Map();
  const routes = [];

  for (const row of rows) {
    for (const key of REQUIRED) {
      if (!(key in row)) throw new Error(`missing route column: ${key}`);
    }
    if (!row.route_id) throw new Error('route_id is required');
    if (!row.upstream) throw new Error(`route ${row.route_id}: upstream is required`);

    const existing = byId.get(row.route_id);
    if (existing) {
      if (existing.canonical !== canonicalRow(row)) {
        throw new Error(`conflicting definitions for route_id ${row.route_id}`);
      }
      continue;
    }

    const priority = Number(row.priority);
    if (!Number.isSafeInteger(priority)) throw new Error(`route ${row.route_id}: priority must be an integer`);

    const route = {
      routeId: row.route_id,
      host: parseHostPattern(row.host_pattern),
      method: parseMethod(row.method),
      path: parsePathPattern(row.path_pattern),
      priority,
      upstream: row.upstream,
      canonical: canonicalRow(row)
    };
    byId.set(route.routeId, route);
    routes.push(route);
  }

  routes.sort((a, b) => a.routeId.localeCompare(b.routeId));
  return { routes };
}

export function loadCatalog(path) {
  const text = fs.readFileSync(path, 'utf8');
  return buildCatalog(recordsFromCsv(text));
}

export function loadQueries(path) {
  const lines = fs.readFileSync(path, 'utf8').split(/\r?\n/).filter(Boolean);
  return lines.map((line, index) => {
    try {
      const value = JSON.parse(line);
      if (!value.request_id) throw new Error('request_id is required');
      return value;
    } catch (err) {
      throw new Error(`invalid query line ${index + 1}: ${err.message}`);
    }
  });
}
