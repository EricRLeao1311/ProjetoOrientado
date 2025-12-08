# infrastructure/storage/catalog_repo.py
from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Base de storage: respeita env (DATA_DIR, KG_DATA_DIR, STORAGE_DIR), senão usa ./data
_BASE = (
    os.environ.get("DATA_DIR")
    or os.environ.get("KG_DATA_DIR")
    or os.environ.get("STORAGE_DIR")
    or (Path.cwd() / "data")
)
BASE_DIR = Path(_BASE)

# Caminhos de arquivos
CATALOG_PATH = BASE_DIR / "catalog.json"   # legado (JSON antigo)
CATALOG_DB = BASE_DIR / "catalog.db"       # novo backend SQLite

_lock = threading.RLock()

# Schema do SQLite
_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS items (
    item_id   TEXT PRIMARY KEY,
    nome      TEXT NOT NULL,
    categoria TEXT,
    cor       TEXT,
    padrao    TEXT,
    material  TEXT,
    estilo    TEXT,
    ocasion   TEXT,
    clima     TEXT,
    paleta    TEXT
);
"""


def _norm_name(s: Optional[str]) -> str:
    return (s or "").strip().lower()


def _get_conn() -> sqlite3.Connection:
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CATALOG_DB))
    conn.row_factory = sqlite3.Row
    return conn


def _maybe_import_from_json(conn: sqlite3.Connection) -> None:
    """
    Migra automaticamente do catalog.json para o SQLite se:
      - o JSON existir, e
      - a tabela items estiver vazia.
    Isso permite fazer a transição sem perder dados.
    """
    if not CATALOG_PATH.exists():
        return

    try:
        cur = conn.execute("SELECT COUNT(*) AS n FROM items")
        n = cur.fetchone()[0]
    except Exception:
        n = 0

    if n > 0:
        # Já tem dados no SQLite, não migrar automaticamente
        return

    try:
        txt = CATALOG_PATH.read_text(encoding="utf-8")
        data = json.loads(txt or "[]")
    except Exception:
        # Se o JSON estiver corrompido ou estranho, não faz nada
        return

    if not isinstance(data, list):
        return

    for it in data:
        # Garante item_id, se faltando
        if not it.get("item_id"):
            prefix = _norm_name(it.get("categoria") or "item")[:10] or "item"
            it["item_id"] = f"{prefix}_{uuid4().hex[:8]}"

        conn.execute(
            """
            INSERT OR REPLACE INTO items (
                item_id, nome, categoria, cor,
                padrao, material, estilo, ocasion,
                clima, paleta
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                it.get("item_id"),
                it.get("nome"),
                it.get("categoria"),
                it.get("cor"),
                it.get("padrao"),
                it.get("material"),
                it.get("estilo"),
                it.get("ocasion"),
                it.get("clima"),
                it.get("paleta"),
            ),
        )

    conn.commit()


def _ensure_db() -> None:
    """Garante que o arquivo catalog.db e a tabela items existam; migra do JSON se necessário."""
    with _lock:
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(CATALOG_DB))
        try:
            conn.executescript(_SCHEMA)
            conn.commit()
            _maybe_import_from_json(conn)
        finally:
            conn.close()


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "item_id": row["item_id"],
        "nome": row["nome"],
        "categoria": row["categoria"],
        "cor": row["cor"],
        "padrao": row["padrao"],
        "material": row["material"],
        "estilo": row["estilo"],
        "ocasion": row["ocasion"],
        "clima": row["clima"],
        "paleta": row["paleta"],
    }


def load_all() -> List[Dict[str, Any]]:
    """
    Carrega todos os itens do SQLite.
    Retorna lista de dicionários com as mesmas chaves de antes.
    """
    _ensure_db()
    conn = _get_conn()
    try:
        cur = conn.execute(
            """
            SELECT
                item_id, nome, categoria, cor,
                padrao, material, estilo, ocasion,
                clima, paleta
            FROM items
            ORDER BY item_id
            """
        )
        return [_row_to_dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def save_all(items: List[Dict[str, Any]]) -> None:
    """
    Substitui todo o conteúdo da tabela items pelo conteúdo da lista.
    Mantém a semântica do save_all antigo, mas agora em cima do SQLite.
    """
    _ensure_db()
    with _lock:
        conn = _get_conn()
        try:
            conn.execute("DELETE FROM items")
            for it in items:
                if not it.get("item_id"):
                    prefix = _norm_name(it.get("categoria") or "item")[:10] or "item"
                    it["item_id"] = f"{prefix}_{uuid4().hex[:8]}"

                conn.execute(
                    """
                    INSERT OR REPLACE INTO items (
                        item_id, nome, categoria, cor,
                        padrao, material, estilo, ocasion,
                        clima, paleta
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        it.get("item_id"),
                        it.get("nome"),
                        it.get("categoria"),
                        it.get("cor"),
                        it.get("padrao"),
                        it.get("material"),
                        it.get("estilo"),
                        it.get("ocasion"),
                        it.get("clima"),
                        it.get("paleta"),
                    ),
                )
            conn.commit()
        finally:
            conn.close()


def add_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upsert por (item_id) ou (nome+categoria). Gera item_id se não existir.
    Retorna o item salvo (com item_id).

    A lógica de upsert é mantida igual à versão antiga, só mudamos
    o backend de persistência (JSON -> SQLite).
    """
    with _lock:
        items = load_all()

        # Garante item_id
        if not item.get("item_id"):
            prefix = _norm_name(item.get("categoria") or "item")[:10] or "item"
            item["item_id"] = f"{prefix}_{uuid4().hex[:8]}"

        # Upsert por item_id
        by_id = next((i for i, it in enumerate(items) if it.get("item_id") == item["item_id"]), None)
        if by_id is not None:
            items[by_id] = item
            save_all(items)
            return item

        # Upsert por (nome + categoria)
        nm = _norm_name(item.get("nome"))
        cat = _norm_name(item.get("categoria"))
        for i, it in enumerate(items):
            if _norm_name(it.get("nome")) == nm and _norm_name(it.get("categoria")) == cat:
                items[i] = item
                save_all(items)
                return item

        # Novo item
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
    A semântica é a mesma da versão original: normaliza e filtra em Python.
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
