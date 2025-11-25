# ops/migrate_catalog_to_sqlite.py

import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # raiz do projeto
CATALOG_JSON = BASE_DIR / "data/catalog.json"
CATALOG_DB   = BASE_DIR / "data/catalog.db"
SCHEMA_SQL   = BASE_DIR / "ops" / "catalog_schema.sql"


def init_db(conn: sqlite3.Connection) -> None:
    """Cria o schema no SQLite usando o arquivo .sql."""
    with open(SCHEMA_SQL, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()


def migrate_json_to_db(conn: sqlite3.Connection) -> None:
    """Lê o catalog.json (lista de itens) e insere nas tabelas."""
    with open(CATALOG_JSON, "r", encoding="utf-8") as f:
        items = json.load(f)  # <<-- É UMA LISTA, não um dict

    cur = conn.cursor()

    # Limpa a tabela antes (idempotente)
    cur.execute("DELETE FROM items")
    conn.commit()

    for item in items:
        cur.execute(
            """
            INSERT INTO items (
                item_id, nome, categoria, cor,
                padrao, material, estilo, ocasion,
                clima, paleta
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["item_id"],
                item.get("nome"),
                item.get("categoria"),
                item.get("cor"),
                item.get("padrao"),
                item.get("material"),
                item.get("estilo"),
                item.get("ocasion"),  # mantém o campo igual ao JSON
                item.get("clima"),
                item.get("paleta"),
            ),
        )

    conn.commit()


def main() -> None:
    if not CATALOG_JSON.exists():
        raise FileNotFoundError(f"catalog.json não encontrado em: {CATALOG_JSON}")

    conn = sqlite3.connect(str(CATALOG_DB))
    try:
        init_db(conn)
        migrate_json_to_db(conn)
        print(f"✔ Migração concluída! Banco criado/atualizado em: {CATALOG_DB}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
