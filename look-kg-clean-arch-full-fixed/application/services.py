# application/services.py
from typing import List, Dict, Any, Optional
from infrastructure.storage import catalog_repo
from infrastructure.graph import networkx_repo
from infrastructure.graph_builder import rules_engine as re

ROLE = re.ROLE
SINGLETON_ROLES = re.SINGLETON_ROLES

def _present_categories(ctx: List[Dict[str, Any]]):
    return {i.get("categoria") for i in ctx}

def _present_roles(ctx: List[Dict[str, Any]]):
    return {ROLE.get(i.get("categoria")) for i in ctx if ROLE.get(i.get("categoria"))}

def _category_allowed(ctx: List[Dict[str, Any]], cat: str) -> bool:
    # 1) não repetir a mesma categoria
    if cat in _present_categories(ctx):
        return False
    # 2) não repetir papeis singletons (bottom/foot/bag)
    role = ROLE.get(cat)
    if role in SINGLETON_ROLES and role in _present_roles(ctx):
        return False
    return True

class RecommendationService:
    def __init__(self):
        self.graph = networkx_repo.GraphManager.singleton()

    def upsert_item_and_generate_edges(self, item: Dict[str, Any]) -> Dict[str, Any]:
        norm = re.normalize_item(item)  # valida e normaliza
        saved = catalog_repo.add_item(norm)
        all_items = catalog_repo.load_all()
        self.graph.upsert_item(saved, all_items)
        return saved

    def rebuild_graph(self) -> Dict[str, int]:
        all_items = catalog_repo.load_all()
        return self.graph.rebuild(all_items)

    def search_items(self, query: str, limit: int = 100) -> Dict[str, Any]:
        return {"items": catalog_repo.search(query, limit=limit)}

    def suggest_complements(self, selected: List[Dict[str, Any]], top_k: int = 10,
                            threshold: float = 0.0, constraints: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        # Filtra candidatos por categorias permitidas para o contexto
        candidates = [
            c for c in self.graph.all_candidates(exclude_ids=[s.get("item_id") for s in selected])
            if _category_allowed(selected, c.get("categoria"))
        ]
        results = []
        for c in candidates:
            sc, rationale = re.score_bottleneck(selected, c)
            if constraints:
                sc *= re.constraint_multiplier(c, constraints)
            if sc >= threshold:
                results.append({"item_id": c.get("item_id"), "nome": c.get("nome"), "categoria": c.get("categoria"),
                                "score": sc, "rationale": rationale})
        results.sort(key=lambda x: x["score"], reverse=True)
        return {"results": results[:top_k]}

    def complete_look(self, selected: List[Dict[str, Any]], targets: List[str], top_k: int = 1) -> Dict[str, Any]:
        out, missing = {}, []
        ctx = list(selected)
        all_cands = self.graph.all_candidates()

        for t in targets:
            if not _category_allowed(ctx, t):
                missing.append(f"{t} (já existe no look ou papel único ocupado)")
                continue
            pool = [c for c in all_cands if c.get("categoria") == t and _category_allowed(ctx, c.get("categoria"))]
            scored = []
            for c in pool:
                sc, rationale = re.score_bottleneck(ctx, c)
                scored.append((c, sc, rationale))
            scored.sort(key=lambda x: x[1], reverse=True)
            if scored and scored[0][1] > 0:
                best = [{"item_id": scored[0][0]["item_id"], "nome": scored[0][0]["nome"],
                         "categoria": scored[0][0]["categoria"], "score": scored[0][1], "rationale": scored[0][2]}]
                out[t] = best[:top_k]
                ctx.append(scored[0][0])  # adiciona ao contexto
            else:
                missing.append(t)

        return {"targets": out, "missing": missing}
