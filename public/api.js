export async function api(path, params = {}, body) {
  const query = new URLSearchParams(params);
  const res = await fetch(`${path}?${query}`, body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const data = await res.json();
  if (!res.ok) throw Object.assign(new Error(data.error || 'Request failed'),{status:res.status,data});
  return data;
}
