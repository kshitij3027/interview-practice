async function request(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || 'Request failed');
    error.status = response.status;
    error.code = data.error?.code;
    throw error;
  }
  return data;
}

const query = params => new URLSearchParams(params).toString();
export const listStudios = () => request('/api/studios');
export const listAssets = (studio, status, q) => request(`/api/assets?${query({ studio, status, q })}`);
export const getAsset = (studio, id) => request(`/api/assets/${encodeURIComponent(id)}?${query({ studio })}`);
export const saveNote = (studio, id, note, expectedRevision) => request(
  `/api/assets/${encodeURIComponent(id)}/note?${query({ studio })}`,
  { method: 'PATCH', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ note, expectedRevision }) }
);
