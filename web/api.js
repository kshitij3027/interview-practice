export async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options, headers: {...(options.body ? {'content-type':'application/json'} : {}), ...options.headers}
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.message ?? data.error ?? `HTTP ${response.status}`);
  return data;
}
export const params = values => new URLSearchParams(Object.entries(values).filter(([,v]) => v !== undefined && v !== null)).toString();
