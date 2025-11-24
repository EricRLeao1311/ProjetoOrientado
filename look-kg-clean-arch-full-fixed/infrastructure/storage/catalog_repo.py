# infrastructure/storage/catalog_repo.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
import threading

# Base de storage: respeita env (DATA_DIR, KG_DATA_DIR, STORAGE_DIR), senão usa ./data
_BASE = (
    os.environ.get("DATA_DIR")
    or os.environ.get("KG_DATA_DIR")
    or os.environ.get("STORAGE_DIR")
    or (Path.cwd() / "data")
)
BASE_DIR = Path(_BASE)
CATALOG_PATH = BASE_DIR / "catalog.json"

_lock = threading.Lock()


def _ensure_file() -> None:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    if not CATALOG_PATH.exists():
        CATALOG_PATH.write_text("[]", encoding="utf-8")


def load_all() -> List[Dict[str, Any]]:
    _ensure_file()
    try:
        txt = CATALOG_PATH.read_text(encoding="utf-8")
        data = json.loads(txt or "[]")
        if isinstance(data, list):
            return data
        return []
    except Exception:
        # Corrupção eventual -> reseta
        CATALOG_PATH.write_text("[]", encoding="utf-8")
        return []


def save_all(items: List[Dict[str, Any]]) -> None:
    CATALOG_PATH.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")


def _norm_name(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def add_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upsert por (item_id) ou (nome+categoria). Gera item_id se não existir.
    Retorna o item salvo (com item_id).
    """
    with _lock:
        items = load_all()

        # Garante item_id
        if not item.get("item_id"):
            prefix = _norm_name(item.get("categoria") or "item")[:10] or "item"
            item["item_id"] = f"{prefix}_{uuid4().hex[:8]}"

        # Upsert
        by_id = next((i for i, it in enumerate(items) if it.get("item_id") == item["item_id"]), None)
        if by_id is not None:
            items[by_id] = item
            save_all(items)
            return item

        nm = _norm_name(item.get("nome"))
        cat = _norm_name(item.get("categoria"))
        for i, it in enumerate(items):
            if _norm_name(it.get("nome")) == nm and _norm_name(it.get("categoria")) == cat:
                items[i] = item
                save_all(items)
                return item

        items.append(item)
        save_all(items)
        return item


def get_item(item_id: str) -> Optional[Dict[str, Any]]:
    items = load_all()
    return next((it for it in items if it.get("item_id") == item_id), None)


def delete_item(item_id: str) -> bool:
    with _lock:
        items = load_all()
        new_items = [it for it in items if it.get("item_id") != item_id]
        changed = len(new_items) != len(items)
        if changed:
            save_all(new_items)
        return changed


def search(query: str = "", limit: int = 200) -> List[Dict[str, Any]]:
    """
    Busca simples por substring em nome/categoria/cor/estilo/material/ocasião.
    """
    q = _norm_name(query)
    items = load_all()
    if not q:
        return items[:limit]
    out: List[Dict[str, Any]] = []
    for it in items:
        hay = " ".join(
            _norm_name(it.get(k))
            for k in ["nome", "categoria", "cor", "material", "estilo", "ocasion", "clima", "padrao"]
        )
        if q in hay:
            out.append(it)
        if len(out) >= limit:
            break
    return out
