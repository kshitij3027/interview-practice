export async function request(path, body) {
    const response = await fetch(path, body === undefined ? {} : {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data = await response.json();
    if (!response.ok) throw Object.assign(new Error(data.error || 'Request failed'),{status:response.status,data});
    return data;
}
export const list = () => request('/api/inspections');
export const detail = id => request('/api/inspections/'+encodeURIComponent(id));
export const save = (id,body) => request('/api/inspections/'+encodeURIComponent(id)+'/answer',body);
