export async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  let payload;
  try { payload = await response.json(); } catch { payload = {}; }
  if (!response.ok) {
    const error = new Error(payload.error?.message || `HTTP ${response.status}`);
    error.code = payload.error?.code || 'request_failed';
    error.status = response.status;
    error.details = payload.error?.details || {};
    throw error;
  }
  return payload;
}
