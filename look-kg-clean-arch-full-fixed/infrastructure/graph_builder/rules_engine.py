# infrastructure/graph_builder/rules_engine.py
from typing import Dict, Any, List, Tuple, Set

# ===================== Vocabulários rígidos =====================
CATEGORIES = [
    "blusa","jaqueta","saia","calca","sapato","bolsa","acessorio",
    # adicione novas aqui (ex.: "vestido","cardigan")
]
PATTERNS   = ["liso","listrado","xadrez","poa"]
STYLES     = ["classico","casual","esportivo","streetwear","formal","romantico"]
OCCASIONS  = ["casual","formal","esportivo","trabalho","noite"]
CLIMES     = ["quente","frio","meia-estacao"]
COLORS     = [
    "preto","branco","cinza","nude","bege","marrom",
    "azul","azul-escuro","verde","verde-agua","ciano",
    "vermelho","laranja","amarelo","rosa"
]
MATERIALS  = [
    "algodao","jeans","couro","seda","linho","la","poliester","malha","metal"
]

# Sinônimos simples
CAT_SYNONYMS = {
    "calça":"calca","calsa":"calca","saía":"saia","camisa":"blusa",
    "casaco":"jaqueta","sapatos":"sapato","bolsas":"bolsa","acessório":"acessorio",
    # exemplo de novas: "vestidos":"vestido","cardigã":"cardigan"
}
COLOR_SYNONYMS = {"beige":"bege","prata":"cinza"}
MAT_SYNONYMS   = {"algodão":"algodao","lycra":"poliester"}

# Papéis (para invariantes do look)
ROLE = {
    "blusa":"top", "jaqueta":"top",
    "saia":"bottom", "calca":"bottom",
    "sapato":"foot", "bolsa":"bag",
    "acessorio":"accessory",
    # "vestido":"onepiece",  # se adicionar
}
SINGLETON_ROLES: Set[str] = {"bottom","foot","bag","onepiece"}

# ===================== Regras cromáticas =====================
PALETAS = {
    "azul":"fria","azul-escuro":"fria","verde":"fria","verde-agua":"fria","ciano":"fria",
    "vermelho":"quente","laranja":"quente","amarelo":"quente","rosa":"quente",
    "preto":"neutra","branco":"neutra","cinza":"neutra","nude":"neutra","marrom":"neutra","bege":"neutra",
}
ANALOGAS = {
    "azul":{"verde-agua","ciano","azul-escuro"},
    "verde":{"azul","ciano"},
    "vermelho":{"laranja","rosa"},
    "amarelo":{"laranja","bege"},
    "marrom":{"bege","nude"},
}
COMPLEMENTARES = {
    "azul":"laranja", "laranja":"azul",
    "vermelho":"verde", "verde":"vermelho",
    # amarelo ↔ roxo (não temos roxo na paleta), ignorado
}
TRIADES = [
    {"vermelho","amarelo","azul"},
    {"laranja","verde","rosa"},  # aproximação prática
]

# ===================== Matrizes de compatibilidade =====================
STYLE_MATRIX = {
    # alvo -> base  (quanto maior melhor)
    "classico":   {"classico":1.0,"formal":0.8,"casual":0.6,"romantico":0.7,"streetwear":0.4,"esportivo":0.4},
    "casual":     {"casual":1.0,"classico":0.7,"streetwear":0.7,"esportivo":0.6,"romantico":0.6,"formal":0.4},
    "esportivo":  {"esportivo":1.0,"streetwear":0.7,"casual":0.6,"classico":0.3,"formal":0.2,"romantico":0.3},
    "streetwear": {"streetwear":1.0,"casual":0.7,"esportivo":0.7,"classico":0.4,"formal":0.3,"romantico":0.4},
    "formal":     {"formal":1.0,"classico":0.8,"casual":0.4,"streetwear":0.3,"esportivo":0.2,"romantico":0.5},
    "romantico":  {"romantico":1.0,"classico":0.7,"casual":0.6,"formal":0.5,"streetwear":0.4,"esportivo":0.3},
}

OCC_MATRIX = {
    "casual":    {"casual":1.0,"esportivo":0.8,"trabalho":0.6,"noite":0.6,"formal":0.4},
    "formal":    {"formal":1.0,"trabalho":0.9,"noite":0.7,"casual":0.3,"esportivo":0.2},
    "esportivo": {"esportivo":1.0,"casual":0.8,"trabalho":0.3,"noite":0.3,"formal":0.2},
    "trabalho":  {"trabalho":1.0,"formal":0.9,"casual":0.6,"noite":0.5,"esportivo":0.3},
    "noite":     {"noite":1.0,"formal":0.7,"casual":0.6,"trabalho":0.5,"esportivo":0.3},
}

CLIMATE_MATRIX = {
    "quente": {"quente":1.0,"meia-estacao":0.7,"frio":0.2},
    "frio":   {"frio":1.0,"meia-estacao":0.7,"quente":0.2},
    "meia-estacao": {"meia-estacao":1.0,"quente":0.7,"frio":0.7},
}

# grupos de materiais (heurística leve)
MAT_GROUP = {
    "algodao":"leve", "linho":"leve", "seda":"leve",
    "jeans":"pesado", "couro":"pesado", "la":"pesado",
    "poliester":"tecnico", "malha":"tecnico",
    "metal":"acessorio",
}
MAT_MATRIX = {
    "leve":     {"leve":1.0, "pesado":0.7, "tecnico":0.6, "acessorio":0.8},
    "pesado":   {"pesado":1.0, "leve":0.7, "tecnico":0.6, "acessorio":0.8},
    "tecnico":  {"tecnico":1.0, "leve":0.6, "pesado":0.6, "acessorio":0.8},
    "acessorio":{"acessorio":1.0,"leve":0.8, "pesado":0.8, "tecnico":0.8},
}

# Padrões — penalizações/combos
PATTERN_MATRIX = {
    "liso":     {"liso":0.0,"listrado":0.0,"xadrez":0.0,"poa":0.0},         # liso combina com tudo (sem bônus)
    "listrado": {"liso":0.0,"listrado":-0.15,"xadrez":-0.15,"poa":-0.05},
    "xadrez":   {"liso":0.0,"listrado":-0.15,"xadrez":-0.1,"poa":-0.1},
    "poa":      {"liso":0.0,"listrado":-0.05,"xadrez":-0.1,"poa":-0.1},
}

# ===================== Normalização e validação =====================
def _norm(v: Any) -> str:
    return (v or "").strip().lower()

def normalize_item(it: Dict[str, Any]) -> Dict[str, Any]:
    categoria = _norm(it.get("categoria"))
    categoria = CAT_SYNONYMS.get(categoria, categoria)

    cor = COLOR_SYNONYMS.get(_norm(it.get("cor")), _norm(it.get("cor")))
    material = MAT_SYNONYMS.get(_norm(it.get("material")), _norm(it.get("material")))

    out = {
        "item_id": it.get("item_id"),
        "nome": _norm(it.get("nome")),
        "categoria": categoria,
        "cor": cor,
        "padrao": _norm(it.get("padrao")) or "liso",
        "material": material or None,
        "estilo": _norm(it.get("estilo")) or "classico",
        "ocasion": _norm(it.get("ocasion")) or "casual",
        "clima": _norm(it.get("clima")) or "quente",
    }
    out["paleta"] = PALETAS.get(out["cor"], "neutra")

    # validações rígidas
    if out["categoria"] not in CATEGORIES:
        raise ValueError(f"categoria inválida: {out['categoria']}")
    if out["padrao"] not in PATTERNS:
        raise ValueError(f"padrao inválido: {out['padrao']}")
    if out["estilo"] not in STYLES:
        raise ValueError(f"estilo inválido: {out['estilo']}")
    if out["ocasion"] not in OCCASIONS:
        raise ValueError(f"ocasion inválida: {out['ocasion']}")
    if out["clima"] not in CLIMES:
        raise ValueError(f"clima inválido: {out['clima']}")
    if out["cor"] not in COLORS:
        raise ValueError(f"cor inválida: {out['cor']}")
    if out["material"] and out["material"] not in MATERIALS:
        raise ValueError(f"material inválido: {out['material']}")

    return out

# ===================== Scoring helpers =====================
def _color_score(a: str, b: str) -> Tuple[float,str]:
    if not a or not b: return 0.0,""
    if a == b: return 0.6, "mesma cor"
    if b in ANALOGAS.get(a,set()) or a in ANALOGAS.get(b,set()): return 0.45, "análogas"
    if COMPLEMENTARES.get(a) == b or COMPLEMENTARES.get(b) == a: return 0.5, "complementares"
    for tri in TRIADES:
        if a in tri and b in tri: return 0.35, "tríade"
    if a in {"preto","branco","cinza","nude","bege","marrom"} or b in {"preto","branco","cinza","nude","bege","marrom"}:
        return 0.4, "neutro"
    return 0.2, "baixo contraste"

def _matrix_score(x: str, y: str, mat: Dict[str,Dict[str,float]], label: str) -> Tuple[float,str]:
    if not x or not y: return 0.0,""
    val = mat.get(x,{}).get(y, 0.4)
    txt = f"{label} compatível" if val>=0.7 else (f"{label} aceitável" if val>=0.5 else f"{label} distante")
    return val*0.3, txt  # normaliza peso local (será reponderado no mix final)

def _pattern_penalty(a: str, b: str) -> Tuple[float,str]:
    if not a or not b: return 0.0,""
    return PATTERN_MATRIX.get(a,{}).get(b,0.0), "padrões colidem" if PATTERN_MATRIX.get(a,{}).get(b,0.0) < 0 else ""

def _material_score(a: str, b: str) -> Tuple[float,str]:
    if not a or not b: return 0.05,"materiais neutros"
    ga, gb = MAT_GROUP.get(a,"leve"), MAT_GROUP.get(b,"leve")
    val = MAT_MATRIX.get(ga,{}).get(gb,0.6)
    return val*0.25, "materiais coerentes"

# papéis incompatíveis para aresta (evita “saia x calça”, “sapato x sapato”, etc.)
def _role_incompatible(cat_a: str, cat_b: str) -> bool:
    ra, rb = ROLE.get(cat_a), ROLE.get(cat_b)
    if not ra or not rb: return False
    if ra == rb and ra in SINGLETON_ROLES: return True
    if (ra == "bottom" and rb == "bottom"): return True
    return False

# ===================== Score final =====================
def score_pair(a: Dict[str,Any], b: Dict[str,Any]) -> Tuple[float,List[str]]:
    if a.get("categoria") == b.get("categoria"): 
        return 0.0, ["mesma categoria"]
    if _role_incompatible(a.get("categoria"), b.get("categoria")):
        return 0.0, ["papéis incompatíveis"]

    s = 0.0; rat: List[str] = []

    v,t = _color_score(a.get("cor"), b.get("cor")); s += v; rat.append(f"cor: {t}" if t else "")
    v,t = _matrix_score(a.get("estilo"), b.get("estilo"), STYLE_MATRIX, "estilo"); s += v; rat.append(t if t else "")
    v,t = _matrix_score(a.get("ocasion"), b.get("ocasion"), OCC_MATRIX, "ocasião"); s += v; rat.append(t if t else "")
    v,t = _matrix_score(a.get("clima"), b.get("clima"), CLIMATE_MATRIX, "clima"); s += v; rat.append(t if t else "")
    v,t = _material_score(a.get("material"), b.get("material")); s += v; rat.append(t if t else "")
    v,t = _pattern_penalty(a.get("padrao"), b.get("padrao")); s += v; rat.append(t if t else "")

    # pesos finais — já normalizados nos helpers (~ somar ~1.0); clamp
    rat = [x for x in rat if x]
    s = max(0.0, min(1.0, s))
    return s, rat

def score_bottleneck(ctx: List[Dict[str,Any]], cand: Dict[str,Any]) -> Tuple[float,List[str]]:
    if not ctx: return 0.0,[]
    vals: List[float] = []; rats: List[str] = []
    for it in ctx:
        v, r = score_pair(it, cand)
        vals.append(v); rats += r
    return (min(vals) if vals else 0.0), list(dict.fromkeys(rats))

def constraint_multiplier(c: Dict[str,str], cons: Dict[str,str]) -> float:
    mul = 1.0
    if cons.get("ocasion") and c.get("ocasion")==cons["ocasion"]: mul *= 1.05
    if cons.get("clima") and c.get("clima")==cons["clima"]:     mul *= 1.05
    return mul
