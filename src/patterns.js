const METHOD_RE = /^[A-Z]+$/;
const HOST_LABEL_RE = /^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$/;
const PARAM_RE = /^\{([A-Za-z_][A-Za-z0-9_]*)\}$/;

export function normalizeHost(host) {
  if (typeof host !== 'string' || host.length === 0) throw new Error('host is required');
  let value = host.toLowerCase();
  if (value.endsWith('.')) value = value.slice(0, -1);
  validateConcreteHost(value);
  return value;
}

function validateConcreteHost(host) {
  const labels = host.split('.');
  if (labels.length === 0 || labels.some((label) => !HOST_LABEL_RE.test(label))) {
    throw new Error(`invalid host: ${host}`);
  }
}

export function parseHostPattern(raw) {
  if (raw === '*') return { kind: 'global', raw: '*' };
  const lower = raw.toLowerCase();
  if (lower.startsWith('*.')) {
    const suffix = lower.slice(2);
    validateConcreteHost(suffix);
    return { kind: 'suffix', raw: lower, suffix, suffixLabels: suffix.split('.').length };
  }
  validateConcreteHost(lower);
  return { kind: 'exact', raw: lower, host: lower };
}

export function parseMethod(raw) {
  if (raw === 'ANY') return 'ANY';
  if (!METHOD_RE.test(raw)) throw new Error(`invalid method: ${raw}`);
  return raw;
}

export function parsePathPattern(raw) {
  if (raw === '/') return { raw, segments: [] };
  if (!raw.startsWith('/') || raw.endsWith('/') || raw.includes('//') || raw.includes('?') || raw.includes('#')) {
    throw new Error(`invalid canonical path pattern: ${raw}`);
  }

  const names = new Set();
  const parts = raw.slice(1).split('/');
  let multiSeen = false;
  const segments = parts.map((part, index) => {
    if (part === '**') {
      if (index !== parts.length - 1 || multiSeen) throw new Error('** must appear once and only as the final segment');
      multiSeen = true;
      return { kind: 'multi' };
    }
    if (part === '*') return { kind: 'single' };
    const match = PARAM_RE.exec(part);
    if (match) {
      const name = match[1];
      if (names.has(name)) throw new Error(`duplicate path parameter name: ${name}`);
      names.add(name);
      return { kind: 'param', name };
    }
    if (part.includes('{') || part.includes('}') || part.length === 0) {
      throw new Error(`invalid path segment: ${part}`);
    }
    return { kind: 'literal', value: part };
  });
  return { raw, segments };
}

export function parseRequestPath(raw) {
  if (raw === '/') return [];
  if (typeof raw !== 'string' || !raw.startsWith('/') || raw.endsWith('/') || raw.includes('//') || raw.includes('?') || raw.includes('#')) {
    throw new Error(`invalid canonical request path: ${raw}`);
  }
  const parts = raw.slice(1).split('/');
  if (parts.some((part) => part.length === 0)) throw new Error(`invalid canonical request path: ${raw}`);
  return parts;
}
