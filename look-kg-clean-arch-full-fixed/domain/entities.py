from dataclasses import dataclass
from typing import Optional

@dataclass
class Item:
    item_id: str
    nome: str
    categoria: str
    cor: str
    padrao: Optional[str] = None
    material: Optional[str] = None
    estilo: Optional[str] = None
    ocasion: Optional[str] = None
    clima: Optional[str] = None
