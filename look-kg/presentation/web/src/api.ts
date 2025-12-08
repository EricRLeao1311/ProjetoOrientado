// presentation/web/src/api.ts
export const API = import.meta.env.VITE_API_URL || (typeof window !== 'undefined' ? window.location.origin.replace(':5173', ':8000') : "");

export async function apiSearch(query: string){
  const res = await fetch(`${API}/v1/items/search`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({query, limit: 200})
  });
  return res.json();
}
export async function apiCreateItem(payload: any){
  const res = await fetch(`${API}/v1/items`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload)
  });
  if(!res.ok) throw new Error(await res.text());
  return res.json();
}
export async function apiDeleteItem(item_id: string){
  const res = await fetch(`${API}/v1/items/${item_id}`, { method: "DELETE" });
  if(!res.ok) throw new Error(await res.text());
  return res.json();
}
export async function apiListCatalog(){
  const res = await fetch(`${API}/v1/items/catalog`);
  return res.json();
}
export async function apiGetItem(id: string){
  const res = await fetch(`${API}/v1/items/${id}`);
  return res.json();
}
export async function apiRecommendComplementar(payload: any){
  const res = await fetch(`${API}/v1/recommend/complementar`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload)
  });
  return res.json();
}
export async function apiRecommendCompletar(payload: any){
  const res = await fetch(`${API}/v1/recommend/completar`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload)
  });
  return res.json();
}
export async function apiRebuild(){
  const res = await fetch(`${API}/v1/graph/rebuild`, { method: "POST" });
  return res.json();
}

// Aliases (backward-compat)
export async function search(q:string){ return apiSearch(q); }
export async function createExample(){
  const exemplo = { nome:"blusa branca algodao exemplo", categoria:"blusa", cor:"branco", padrao:"liso", material:"algodao", estilo:"classico", ocasion:"casual", clima:"quente" };
  return apiCreateItem(exemplo);
}
export const createExampleItem = createExample;
export async function suggestComplementar(p:any){ return apiRecommendComplementar(p); }
export async function completarLook(p:any){ return apiRecommendCompletar(p); }
export async function completar(p:any){ return apiRecommendCompletar(p); }
export async function rebuildGraph(){ return apiRebuild(); }
