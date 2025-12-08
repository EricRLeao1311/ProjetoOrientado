from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ItemCreate(BaseModel):
    nome: str
    categoria: str
    cor: str
    padrao: Optional[str] = "liso"
    material: Optional[str] = None
    estilo: Optional[str] = "classico"
    ocasion: Optional[str] = "casual"
    clima: Optional[str] = "quente"

class RecommendComplementarIn(BaseModel):
    query: Optional[str] = None
    item_id: Optional[str] = None
    itens: Optional[List[str]] = None
    top_k: int = 10
    threshold: float = 0.0
    constraints: Optional[Dict[str, str]] = None

class RecommendCompletarIn(BaseModel):
    itens: List[str]
    top_k: int = 1
    targets: List[str] = ["sapato","bolsa","acessorio"]
