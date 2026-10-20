async function json(url, init) {
  const response=await fetch(url,init);
  let body; try{body=await response.json()}catch{body={message:'Invalid server response'}}
  if(!response.ok){const error=new Error(body.message||'Request failed');error.code=body.error;error.details=body.details;throw error}
  return body;
}
export const api = {
  cases: ({tenant,status,q}) => json(`/api/cases?${new URLSearchParams({tenant,status,q})}`),
  detail: id => json(`/api/cases/${encodeURIComponent(id)}`),
  note: (id, body) => json(`/api/cases/${encodeURIComponent(id)}/note`,{method:'PATCH',headers:{'content-type':'application/json'},body:JSON.stringify(body)})
};
