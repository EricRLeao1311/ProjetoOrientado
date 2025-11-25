# ops/seed.py

import os
import sqlite3
import json
import urllib.request
import time
from pathlib import Path
from typing import Dict, Any, Iterable

# URL da API (pode ser sobrescrita por variável de ambiente)
API = os.getenv("API_URL", "http://localhost:8000")

BASE_DIR = Path(__file__).resolve().parent.parent
CATALOG_DB = BASE_DIR / "data/catalog.db"


def wait_api(url, tries=20):
    for i in range(tries):
        try:
            urllib.request.urlopen(url, timeout=3)
            return True
        except Exception:
            print(f"Aguardando API... ({i+1}/{tries})")
            time.sleep(2)
    return False


def post(path: str, data: Dict[str, Any]):
    req = urllib.request.Request(API + path, method="POST")
    req.add_header("Content-Type", "application/json")
    body = json.dumps(data).encode("utf-8")
    urllib.request.urlopen(req, body, timeout=10).read()


def load_items_from_db() -> Iterable[Dict[str, Any]]:
    """
    Lê os itens existentes do catalog.db (tabela items) e devolve no formato esperado pela API.
    """
    if not CATALOG_DB.exists():
        raise FileNotFoundError(
            f"Banco de catálogo não encontrado em {CATALOG_DB}. "
            f"Rode primeiro: python3 ops/migrate_catalog_to_sqlite.py"
        )

    conn = sqlite3.connect(str(CATALOG_DB))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                item_id, nome, categoria, cor,
                padrao, material, estilo, ocasion,
                clima, paleta
            FROM items
            ORDER BY item_id
            """
        )
        for row in cur.fetchall():
            payload = {
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
            # remove Nones
            yield {k: v for k, v in payload.items() if v is not None}
    finally:
        conn.close()


# =========================
# Peças extras para enriquecer o catálogo
# =========================

EXTRA_ITEMS = [
    # BLUSAS (tops)
    {"nome": "blusa azul algodao", "categoria": "blusa", "cor": "azul", "padrao": "liso",
     "material": "algodao", "estilo": "casual", "ocasion": "casual", "clima": "meia-estacao", "paleta": "fria"},
    {"nome": "blusa rosa seda", "categoria": "blusa", "cor": "rosa", "padrao": "liso",
     "material": "seda", "estilo": "romantico", "ocasion": "festa", "clima": "quente", "paleta": "quente"},
    {"nome": "camiseta branca basica", "categoria": "blusa", "cor": "branco", "padrao": "liso",
     "material": "algodao", "estilo": "casual", "ocasion": "casual", "clima": "quente", "paleta": "neutra"},
    {"nome": "camisa social azul claro", "categoria": "blusa", "cor": "azul claro", "padrao": "liso",
     "material": "algodao", "estilo": "formal", "ocasion": "trabalho", "clima": "meia-estacao", "paleta": "fria"},
    {"nome": "blusa listrada branca e azul", "categoria": "blusa", "cor": "branco e azul", "padrao": "listrado",
     "material": "malha", "estilo": "casual", "ocasion": "casual", "clima": "meia-estacao", "paleta": "fria"},
    {"nome": "blusa preta canelada", "categoria": "blusa", "cor": "preto", "padrao": "liso",
     "material": "malha", "estilo": "street", "ocasion": "casual", "clima": "frio", "paleta": "neutra"},

    # SAIAS
    {"nome": "saia midi preta", "categoria": "saia", "cor": "preto", "padrao": "liso",
     "material": "viscose", "estilo": "classico", "ocasion": "trabalho", "clima": "meia-estacao", "paleta": "neutra"},
    {"nome": "saia jeans clara", "categoria": "saia", "cor": "azul claro", "padrao": "liso",
     "material": "jeans", "estilo": "casual", "ocasion": "casual", "clima": "quente", "paleta": "fria"},
    {"nome": "saia floral colorida", "categoria": "saia", "cor": "colorido", "padrao": "floral",
     "material": "viscose", "estilo": "romantico", "ocasion": "festa", "clima": "quente", "paleta": "quente"},
    {"nome": "saia plissada bege", "categoria": "saia", "cor": "bege", "padrao": "liso",
     "material": "poliester", "estilo": "classico", "ocasion": "formal", "clima": "meia-estacao", "paleta": "neutra"},
    {"nome": "saia xadrez preta e branca", "categoria": "saia", "cor": "preto e branco", "padrao": "xadrez",
     "material": "algodao", "estilo": "street", "ocasion": "casual", "clima": "frio", "paleta": "neutra"},
    {"nome": "saia jeans escura desfiada", "categoria": "saia", "cor": "azul escuro", "padrao": "liso",
     "material": "jeans", "estilo": "street", "ocasion": "casual", "clima": "meia-estacao", "paleta": "fria"},

    # CALÇAS
    {"nome": "calca jeans skinny azul escuro", "categoria": "calca", "cor": "azul escuro", "padrao": "liso",
     "material": "jeans", "estilo": "casual", "ocasion": "casual", "clima": "meia-estacao", "paleta": "fria"},
    {"nome": "calca social preta", "categoria": "calca", "cor": "preto", "padrao": "liso",
     "material": "poliamida", "estilo": "formal", "ocasion": "trabalho", "clima": "meia-estacao", "paleta": "neutra"},
    {"nome": "calca de linho bege", "categoria": "calca", "cor": "bege", "padrao": "liso",
     "material": "linho", "estilo": "classico", "ocasion": "trabalho", "clima": "quente", "paleta": "neutra"},
    {"nome": "calca jogger verde oliva", "categoria": "calca", "cor": "verde oliva", "padrao": "liso",
     "material": "malha", "estilo": "esportivo", "ocasion": "esporte", "clima": "meia-estacao", "paleta": "terrosa"},
    {"nome": "calca pantacourt branca", "categoria": "calca", "cor": "branco", "padrao": "liso",
     "material": "viscose", "estilo": "classico", "ocasion": "casual", "clima": "quente", "paleta": "neutra"},
    {"nome": "calca xadrez cinza", "categoria": "calca", "cor": "cinza", "padrao": "xadrez",
     "material": "algodao", "estilo": "street", "ocasion": "casual", "clima": "frio", "paleta": "neutra"},

    # SAPATOS
    {"nome": "tenis branco casual", "categoria": "sapato", "cor": "branco", "padrao": "liso",
     "material": "couro", "estilo": "casual", "ocasion": "casual", "clima": "meia-estacao", "paleta": "neutra"},
    {"nome": "sandalia rasteira dourada", "categoria": "sapato", "cor": "dourado", "padrao": "liso",
     "material": "couro", "estilo": "casual", "ocasion": "praia", "clima": "quente", "paleta": "quente"},
    {"nome": "bota preta cano curto", "categoria": "sapato", "cor": "preto", "padrao": "liso",
     "material": "couro", "estilo": "street", "ocasion": "casual", "clima": "frio", "paleta": "neutra"},
    {"nome": "scarpin nude salto medio", "categoria": "sapato", "cor": "nude", "padrao": "liso",
     "material": "couro", "estilo": "classico", "ocasion": "formal", "clima": "meia-estacao", "paleta": "neutra"},
    {"nome": "tenis esportivo cinza", "categoria": "sapato", "cor": "cinza", "padrao": "liso",
     "material": "malha", "estilo": "esportivo", "ocasion": "esporte", "clima": "meia-estacao", "paleta": "neutra"},
    {"nome": "sandalia de salto preta", "categoria": "sapato", "cor": "preto", "padrao": "liso",
     "material": "couro", "estilo": "formal", "ocasion": "festa", "clima": "quente", "paleta": "neutra"},

    # BOLSAS
    {"nome": "bolsa tiracolo preta", "categoria": "bolsa", "cor": "preto", "padrao": "liso",
     "material": "couro", "estilo": "classico", "ocasion": "trabalho", "clima": "meia-estacao", "paleta": "neutra"},
    {"nome": "bolsa de palha praia", "categoria": "bolsa", "cor": "palha", "padrao": "liso",
     "material": "palha", "estilo": "casual", "ocasion": "praia", "clima": "quente", "paleta": "terrosa"},
    {"nome": "bolsa vermelha estruturada", "categoria": "bolsa", "cor": "vermelho", "padrao": "liso",
     "material": "couro", "estilo": "street", "ocasion": "festa", "clima": "meia-estacao", "paleta": "quente"},
    {"nome": "mochila marrom casual", "categoria": "bolsa", "cor": "marrom", "padrao": "liso",
     "material": "couro", "estilo": "casual", "ocasion": "casual", "clima": "meia-estacao", "paleta": "terrosa"},
    {"nome": "bolsa pequena prata festa", "categoria": "bolsa", "cor": "prata", "padrao": "liso",
     "material": "metal", "estilo": "romantico", "ocasion": "festa", "clima": "noite", "paleta": "fria"},
    {"nome": "bolsa transversal bege", "categoria": "bolsa", "cor": "bege", "padrao": "liso",
     "material": "couro", "estilo": "classico", "ocasion": "casual", "clima": "meia-estacao", "paleta": "neutra"},

    # ACESSÓRIOS
    {"nome": "brinco dourado argola", "categoria": "acessorio", "cor": "dourado", "padrao": "liso",
     "material": "metal", "estilo": "classico", "ocasion": "festa", "clima": "quente", "paleta": "quente"},
    {"nome": "colar longo com pingente", "categoria": "acessorio", "cor": "prata", "padrao": "liso",
     "material": "metal", "estilo": "casual", "ocasion": "casual", "clima": "meia-estacao", "paleta": "fria"},
    {"nome": "pulseira de couro marrom", "categoria": "acessorio", "cor": "marrom", "padrao": "liso",
     "material": "couro", "estilo": "street", "ocasion": "casual", "clima": "meia-estacao", "paleta": "terrosa"},
    {"nome": "relogio de metal prateado", "categoria": "acessorio", "cor": "prata", "padrao": "liso",
     "material": "metal", "estilo": "classico", "ocasion": "trabalho", "clima": "meia-estacao", "paleta": "fria"},
    {"nome": "lenço estampado colorido", "categoria": "acessorio", "cor": "colorido", "padrao": "floral",
     "material": "seda", "estilo": "romantico", "ocasion": "casual", "clima": "meia-estacao", "paleta": "quente"},
    {"nome": "cinto preto fivela dourada", "categoria": "acessorio", "cor": "preto", "padrao": "liso",
     "material": "couro", "estilo": "classico", "ocasion": "casual", "clima": "meia-estacao", "paleta": "neutra"},
]


def iter_seed_items() -> Iterable[Dict[str, Any]]:
    """
    Gera todos os itens que o seed deve enviar:
    - Primeiro os itens do banco (catalog.db)
    - Depois as peças extras definidas em EXTRA_ITEMS
    """
    # Itens que já estão no banco
    for it in load_items_from_db():
        yield it

    # Itens extras (sem item_id - a API gera)
    for it in EXTRA_ITEMS:
        yield it


def main():
    if not wait_api(API + "/health"):
        raise SystemExit("API não respondeu no tempo esperado.")

    count = 0
    for item in iter_seed_items():
        post("/v1/items", item)
        count += 1
        print(f"[SEED] item: {item.get('item_id') or item.get('nome')}")
    print(f"Seed OK. Total de itens enviados: {count}")


if __name__ == "__main__":
    main()
