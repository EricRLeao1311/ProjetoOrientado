# presentation/api/routers.py
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from application.services import RecommendationService
from presentation.api.schemas import ItemCreate, RecommendComplementarIn, RecommendCompletarIn
from infrastructure.storage import catalog_repo
from infrastructure.graph_builder import rules_engine as re

router = APIRouter(prefix="/v1")
svc = RecommendationService()

@router.post("/graph/items")
def create_item_and_edges(payload: ItemCreate):
    try:
        item = svc.upsert_item_and_generate_edges(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return {"item_id": item["item_id"], "item": item}

@router.post("/graph/rebuild")
def rebuild_graph():
    res = svc.rebuild_graph()
    return {"ok": True, **res}

@router.get("/items/{item_id}")
def get_item(item_id: str):
    it = catalog_repo.get_item(item_id)
    if not it:
        raise HTTPException(404, "Item não encontrado")
    return it

@router.post("/items/search")
def search_items(body: Dict[str, Any]):
    query = (body or {}).get("query",""); limit = (body or {}).get("limit", 100)
    return svc.search_items(query, limit=limit)

@router.post("/recommend/complementar")
def recommend_complementar(body: RecommendComplementarIn):
    selected: List[Dict[str, Any]] = []
    all_items = catalog_repo.load_all()
    if body.item_id:
        it = catalog_repo.get_item(body.item_id)
        if it: selected.append(it)
    elif body.itens:
        names = set([s.strip().lower() for s in body.itens])
        for it in all_items:
            if it.get("nome") in names or it.get("item_id") in names:
                selected.append(it)
    elif body.query:
        q = body.query.strip().lower()
        for it in all_items:
            if q in it.get("nome",""):
                selected.append(it); break
    if not selected and all_items:
        selected = [all_items[0]]

    res = svc.suggest_complements(selected, top_k=body.top_k, threshold=body.threshold, constraints=body.constraints)
    return res

@router.post("/recommend/completar")
def recommend_completar(body: RecommendCompletarIn):
    names = set([s.strip().lower() for s in body.itens])
    sels = [it for it in catalog_repo.load_all() if it.get("nome") in names or it.get("item_id") in names]
    res = svc.complete_look(sels, body.targets, top_k=body.top_k)
    if res.get("missing"):
        res["message"] = "Alguns alvos não puderam ser sugeridos (já existem no look, papel único ocupado ou sem item compatível)."
    return res

@router.post("/items")
def items_create(payload: ItemCreate):
    try:
        item = svc.upsert_item_and_generate_edges(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return item

@router.delete("/items/{item_id}")
def items_delete(item_id: str):
    ok = catalog_repo.remove_item(item_id)
    svc.rebuild_graph()
    if not ok:
        raise HTTPException(404, "Item não encontrado")
    return {"ok": True}

@router.get("/items/catalog")
def items_catalog():
    return catalog_repo.load_all()
