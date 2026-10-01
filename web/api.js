async function request(path,options={}){
  const response=await fetch(path,{...options,headers:{"Content-Type":"application/json",...(options.headers||{})}});
  const data=await response.json();
  if(!response.ok){const error=new Error(data.message||`Request failed (${response.status})`);error.status=response.status;error.data=data;throw error;}
  return data;
}
export async function listScreens(filters){const p=new URLSearchParams();if(filters.zone)p.set("zone",filters.zone);if(filters.status)p.set("status",filters.status);return request(`/api/screens${p.toString()?`?${p}`:""}`);}
export async function getScreen(id){return request(`/api/screens/${encodeURIComponent(id)}`);}
export async function updateMode(id,mode,expectedRevision){return request(`/api/screens/${encodeURIComponent(id)}/mode`,{method:"POST",body:JSON.stringify({mode,expectedRevision})});}
