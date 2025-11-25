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
