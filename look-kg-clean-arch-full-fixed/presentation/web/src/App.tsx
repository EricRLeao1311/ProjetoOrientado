import React, { useEffect, useMemo, useState } from "react";
import {
  apiSearch, apiCreateItem, apiDeleteItem, apiRecommendComplementar,
  apiRecommendCompletar, apiRebuild, apiListCatalog, apiGetItem
} from "./api";
import {
  CATEGORIES, PATTERNS, STYLES, OCCASIONS, CLIMES, COLORS, MATERIALS, Category
} from "./constants";

type Item = {
  item_id?: string;
  nome: string;
  categoria: Category | string;
  cor: string;
  padrao?: string;
  material?: string;
  estilo?: string;
  ocasion?: string;
  clima?: string;
};

// aceita any para não esbarrar em 'Item | undefined'
function isValidItem(x: any): x is Item {
  return !!x
    && typeof x.nome === "string" && x.nome.trim() !== ""
    && typeof x.categoria === "string" && x.categoria.trim() !== ""
    && typeof x.cor === "string" && x.cor.trim() !== "";
}

export default function App(){
  const [query, setQuery] = useState("");
  const [catalog, setCatalog] = useState<Item[]>([]);
  const [look, setLook] = useState<Item[]>([]);
  const [threshold, setThreshold] = useState(0.5);
  const [targets, setTargets] = useState<Category[]>([]);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [form, setForm] = useState<Item>({
    nome:"", categoria:"", cor:"", padrao:"", material:"", estilo:"", ocasion:"", clima:""
  });

  useEffect(()=>{ refreshCatalog(); }, []);
  async function refreshCatalog(){
    try {
      const list = await apiListCatalog();
      if (Array.isArray(list)) { setCatalog(list); return; }
    } catch {}
    const r = await apiSearch(query); setCatalog(r.items || []);
  }
  async function onSearch(){
    const r = await apiSearch(query); setCatalog(r.items || []);
  }

  // === helpers seguros ===
  function addToLook(raw: Partial<Item>){
    if (!isValidItem(raw)) { console.warn("Ignorando item inválido ao adicionar ao look:", raw); return; }
    const it: Item = { ...raw };
    setLook(prev => {
      const exists = prev.some(x => (x.item_id && it.item_id && x.item_id===it.item_id) || x.nome===it.nome);
      return exists ? prev : [...prev, it];
    });
  }
  function removeFromLook(it: Item){
    setLook(prev => prev.filter(x => x.item_id!==it.item_id && x.nome!==it.nome));
  }

  const [targetInput, setTargetInput] = useState("");
  function addTargetFromInput(){
    const v = targetInput.trim().toLowerCase();
    if (!v) return;
    if (!CATEGORIES.includes(v as Category)) { alert("Categoria inválida"); return; }
    setTargets(prev => prev.includes(v as Category) ? prev : [...prev, v as Category]);
    setTargetInput("");
  }
  function clearForm(){
    setForm({nome:"", categoria:"", cor:"", padrao:"", material:"", estilo:"", ocasion:"", clima:""});
  }

  async function saveManual(){
    if(!form.nome || !form.categoria || !form.cor){
      alert("Informe nome, categoria e cor."); return;
    }
    const payload = {
      ...form,
      padrao: form.padrao || undefined,
      estilo: form.estilo || undefined,
      ocasion: form.ocasion || undefined,
      clima: form.clima || undefined,
      material: form.material || undefined,
    };
    const saved = await apiCreateItem(payload);
    clearForm();
    await refreshCatalog();
    alert(`Peça salva: ${saved.nome}`);
  }
  async function delFromCatalog(it: Item){
    if(!it.item_id){ alert("Atualize catálogo primeiro (sem item_id)."); return; }
    if(!confirm(`Remover "${it.nome}" do guarda-roupa?`)) return;
    await apiDeleteItem(it.item_id);
    await refreshCatalog();
  }

  async function suggest(){
    if (look.length<1){ alert("Adicione pelo menos 1 peça ao look."); return; }
    setLoading(true);
    try{
      const payload:any = { top_k: 100, threshold, itens: look.map(i=>i.nome) };
      const r = await apiRecommendComplementar(payload);
      setResults({ tipo:"sugerir", data: r });
    } finally { setLoading(false); }
  }
  async function complete(){
    if (look.length<1){ alert("Adicione pelo menos 1 peça ao look."); return; }
    if (!targets.length){ alert("Selecione pelo menos 1 target."); return; }
    setLoading(true);
    try{
      const payload:any = { itens: look.map(i=>i.nome), top_k: 1, targets };
      const r = await apiRecommendCompletar(payload);
      setResults({ tipo:"completar", data: r });
    } finally { setLoading(false); }
  }

  // Adicionar a partir de um resultado de recomendação (robusto)
  async function addFromResult(r: any){
    const norm = (s: any) => (typeof s === "string" ? s.trim().toLowerCase() : "");

    // monta um objeto a partir do próprio resultado (caso ele já venha “rico”)
    const from = (obj: any): Partial<Item> => ({
      item_id:  obj?.item_id ?? obj?.id,
      nome:     obj?.nome ?? obj?.name ?? "",
      categoria:obj?.categoria ?? obj?.category ?? "",
      cor:      obj?.cor ?? obj?.color ?? obj?.attrs?.cor ?? obj?.item?.cor ?? "",
      padrao:   obj?.padrao ?? obj?.attrs?.padrao ?? obj?.item?.padrao ?? "",
      material: obj?.material ?? obj?.attrs?.material ?? obj?.item?.material ?? "",
      estilo:   obj?.estilo ?? obj?.attrs?.estilo ?? obj?.item?.estilo ?? "",
      ocasion:  obj?.ocasion ?? obj?.attrs?.ocasion ?? obj?.item?.ocasion ?? "",
      clima:    obj?.clima ?? obj?.attrs?.clima ?? obj?.item?.clima ?? "",
    });

    // 0) se o próprio resultado já tem tudo, usa direto
    const maybe = from(r);
    if (isValidItem(maybe)) { addToLook(maybe); return; }

    // 1) tenta casar no catálogo (id ou nome+categoria)
    if (r?.item_id){
      const byId = catalog.find(i => i.item_id === r.item_id);
      if (byId && isValidItem(byId)) { addToLook(byId); return; }
    }
    const byName = catalog.find(i =>
      norm(i.nome) === norm(r?.nome) &&
      (!r?.categoria || norm(i.categoria) === norm(r.categoria))
    );
    if (byName && isValidItem(byName)) { addToLook(byName); return; }

    // 2) tenta carregar pelo id
    if (r?.item_id){
      try {
        const full = await apiGetItem(r.item_id);
        if (isValidItem(full)) { addToLook(full); return; }
      } catch {/* segue */}
    }

    // 3) tenta buscar pelo nome
    try {
      const s = await apiSearch(r?.nome || "");
      const cand = (s.items || []).find((i: any) =>
        norm(i.nome) === norm(r?.nome) &&
        (!r?.categoria || norm(i.categoria) === norm(r.categoria))
      );
      if (isValidItem(cand)) { addToLook(cand); return; }
    } catch {/* segue */}

    // 4) fallback final — só adiciona se válido (com cor); senão ignora
    if (isValidItem(maybe)) { addToLook(maybe); }
    else {
      alert("Não foi possível obter os atributos completos da sugestão. Tente buscar no catálogo e adicionar por lá.");
    }
  }

  const lookCats = useMemo(()=>new Set(look.map(i=>i.categoria)), [look]);
  const keyOf = (it: Partial<Item>) => (it.item_id || `${it.nome || "?"}-${it.categoria || "?"}`);

  return (
    <div style={{maxWidth:1200, margin:"0 auto", padding:24, fontFamily:"system-ui, Arial"}}>
      <h1>Look-KG — Teste rápido</h1>

      {/* Cabeçalho */}
      <div style={{display:"flex", flexWrap:"wrap", gap:12, alignItems:"center"}}>
        <div style={{display:"flex", gap:8}}>
          <input placeholder="buscar no guarda-roupa..." value={query} onChange={e=>setQuery(e.target.value)} />
          <button type="button" onClick={onSearch}>Buscar</button>
          <button type="button" onClick={suggest} disabled={loading}>Sugerir (≥ threshold)</button>
          <button type="button" onClick={complete} disabled={loading}>Completar look</button>
          <button type="button" onClick={()=>apiRebuild().then(()=>alert("Grafo reconstruído"))} disabled={loading}>Gerar/Atualizar grafo</button>
          <button type="button" onClick={()=>setLook([])}>Limpar look</button>
        </div>

        <div style={{display:"flex", alignItems:"center", gap:8, marginLeft:"auto"}}>
          <span>threshold: {threshold.toFixed(2)}</span>
          <input type="range" min="0" max="1" step="0.05" value={threshold}
                 onChange={e=>setThreshold(parseFloat(e.target.value))} style={{width:150}}/>
        </div>

        <div style={{display:"flex", alignItems:"center", gap:8, width:"100%", flexWrap:"wrap"}}>
          <span style={{fontWeight:600}}>targets:</span>
          <div style={{display:"flex", gap:6, flexWrap:"wrap"}}>
            {targets.map(t=>(
              <span key={t} style={{border:"1px solid #ccc", borderRadius:16, padding:"2px 8px"}}>
                {t} <button type="button" onClick={()=>setTargets(prev => prev.filter(x=>x!==t))} style={{marginLeft:6}}>x</button>
              </span>
            ))}
          </div>
          <div style={{display:"flex", gap:6, alignItems:"center"}}>
            <input list="catlist" placeholder="adicionar target..." value={targetInput}
                   onChange={e=>setTargetInput(e.target.value)}
                   onKeyDown={(e)=>{ if(e.key==="Enter"){ e.preventDefault(); addTargetFromInput(); }}}/>
            <button type="button" onClick={addTargetFromInput}>+</button>
            <datalist id="catlist">
              {CATEGORIES.map(c=><option key={c} value={c}/>)}
            </datalist>
          </div>
        </div>
      </div>

      {/* Corpo */}
      <div style={{display:"grid", gridTemplateColumns:"1fr 1fr", gap:24, marginTop:24}}>
        <div>
          <h2>Guarda-roupa</h2>

          {/* Form manual (sem <form>) */}
          <div style={{padding:12, border:"1px solid #ddd", borderRadius:8, marginBottom:12}}>
            <h3>Adicionar peça manualmente</h3>
            <div style={{display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:8}}>
              <input placeholder="nome*" value={form.nome} onChange={e=>setForm({...form, nome:e.target.value})}/>
              <select value={form.categoria} onChange={e=>setForm({...form, categoria:e.target.value})}>
                <option value="">categoria*</option>
                {CATEGORIES.map(c=><option key={c} value={c}>{c}</option>)}
              </select>
              <select value={form.cor} onChange={e=>setForm({...form, cor:e.target.value})}>
                <option value="">cor*</option>
                {COLORS.map(c=><option key={c} value={c}>{c}</option>)}
              </select>

              <select value={form.padrao} onChange={e=>setForm({...form, padrao:e.target.value})}>
                <option value="">padrão</option>
                {PATTERNS.map(c=><option key={c} value={c}>{c}</option>)}
              </select>
              <select value={form.material} onChange={e=>setForm({...form, material:e.target.value})}>
                <option value="">material</option>
                {MATERIALS.map(m=><option key={m} value={m}>{m}</option>)}
              </select>
              <select value={form.estilo} onChange={e=>setForm({...form, estilo:e.target.value})}>
                <option value="">estilo</option>
                {STYLES.map(c=><option key={c} value={c}>{c}</option>)}
              </select>

              <select value={form.ocasion} onChange={e=>setForm({...form, ocasion:e.target.value})}>
                <option value="">ocasião</option>
                {OCCASIONS.map(c=><option key={c} value={c}>{c}</option>)}
              </select>
              <select value={form.clima} onChange={e=>setForm({...form, clima:e.target.value})}>
                <option value="">clima</option>
                {CLIMES.map(c=><option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div style={{marginTop:8, display:"flex", gap:8}}>
              <button type="button" onClick={saveManual}>Salvar peça</button>
              <button type="button" onClick={clearForm}>Limpar</button>
            </div>
          </div>

          <Catalog items={catalog} onAdd={addToLook} onDelete={delFromCatalog}/>
        </div>

        <div>
          <h2>Look</h2>
          <Selected items={look} onRemove={removeFromLook} keyOf={keyOf}/>
          {results && <Results block={results} onAddFromResult={addFromResult} lookCats={lookCats}/>}
        </div>
      </div>
    </div>
  );
}

function Catalog({items, onAdd, onDelete}:{items:Item[]; onAdd:(i:Item)=>void; onDelete:(i:Item)=>void}){
  return (
    <div>
      {items.map(it => (
        <div key={(it.item_id || `${it.nome}-${it.categoria}`)} style={{border:"1px solid #ddd", borderRadius:8, padding:12, marginBottom:12}}>
          <b>{it.nome}</b> <em>({it.categoria})</em>
          <div>cor: {it.cor} | material: {it.material || "-"} | estilo: {it.estilo || "-"} | ocasião: {it.ocasion || "-"}</div>
          <div style={{display:"flex", gap:8, marginTop:8}}>
            <button type="button" onClick={()=>onAdd(it)}>Adicionar ao look</button>
            <button type="button" onClick={()=>onDelete(it)}>Excluir do guarda-roupa</button>
          </div>
        </div>
      ))}
    </div>
  );
}

function Selected({items, onRemove, keyOf}:{items:Item[]; onRemove:(i:Item)=>void; keyOf:(it:Partial<Item>)=>string}){
  return (
    <div>
      {items.map(it => (
        <div key={keyOf(it)} style={{border:"1px solid #ddd", borderRadius:8, padding:12, marginBottom:12}}>
          <b>{it.nome || "—"}</b> <em>({it.categoria || "—"})</em>
          <div>cor: {it.cor || "—"} | material: {it.material || "—"} | estilo: {it.estilo || "—"} | ocasião: {it.ocasion || "—"}</div>
          <div><button type="button" onClick={()=>onRemove(it)}>Remover</button></div>
        </div>
      ))}
      {!items.length && <div style={{color:"#666"}}>Nenhuma peça no look.</div>}
    </div>
  );
}

function Results({block, onAddFromResult, lookCats}:{block:any; onAddFromResult:(r:any)=>void; lookCats:Set<string>}){
  if (block.tipo === "sugerir"){
    const arr = block.data?.results || [];
    if (!arr.length) return <div style={{marginTop:12}}>Sem sugestões no threshold atual.</div>;
    return (
      <div style={{marginTop:12}}>
        <h3>Resultados — Sugerir</h3>
        {arr.map((r:any, i:number)=>(
          <div key={r.item_id || `${r.nome}-${r.categoria}-${i}`} style={{border:"1px solid #eee", borderRadius:8, padding:8, marginBottom:8, display:"flex", justifyContent:"space-between", gap:12}}>
            <div>
              <b>{r.nome}</b> <em>({r.categoria})</em> — score: {r.score?.toFixed?.(2)}
              {r.rationale && <div style={{fontSize:12, color:"#444"}}>{r.rationale.join("; ")}</div>}
            </div>
            <div>
              <button type="button" onClick={()=>onAddFromResult(r)}>Adicionar ao look</button>
            </div>
          </div>
        ))}
      </div>
    );
  } else {
    const data = block.data;
    const missing = data?.missing || [];
    return (
      <div style={{marginTop:12}}>
        <h3>Resultados — Completar look</h3>
        {data?.targets && Object.keys(data.targets).map((k:string)=>{
          const r = data.targets[k][0];
          return (
            <div key={k} style={{border:"1px solid #eee", borderRadius:8, padding:8, marginBottom:8, display:"flex", justifyContent:"space-between", gap:12}}>
              <div>
                <b>{k}</b>: {r?.nome} — score: {r?.score?.toFixed?.(2)}
              </div>
              <div>
                {!!r?.item_id && !lookCats.has(k) &&
                  <button type="button" onClick={()=>onAddFromResult(r)}>Adicionar ao look</button>}
              </div>
            </div>
          );
        })}
        {!!missing.length && <div style={{color:"#a00"}}>Não encontramos itens para: {missing.join(", ")}.</div>}
      </div>
    );
  }
}
