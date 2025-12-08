#!/usr/bin/env python3
"""
Smoke-tests super simples para travar 'make up' se a API quebrar.

- GET /health
- POST /v1/graph/items (cria 4~5 peças mínimas)
- POST /v1/recommend/complementar
- POST /v1/recommend/completar
- POST /v1/graph/rebuild

Saída != 0 se qualquer etapa falhar.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error
from typing import Any, Dict, List

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

def req(method: str, path: str, payload: Dict[str, Any] | None = None, timeout: int = 10) -> Dict[str, Any]:
    url = f"{API}{path}"
    data = None
    headers = {"content-type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            txt = resp.read().decode("utf-8") or "{}"
            try:
                return json.loads(txt)
            except json.JSONDecodeError:
                return {"_raw": txt}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        raise SystemExit(f"HTTP {e.code} on {method} {path}: {body}")
    except Exception as e:
        raise SystemExit(f"Request failed {method} {path}: {e}")

def expect(cond: bool, msg: str):
    if not cond:
        raise SystemExit(f"[SMOKE FAIL] {msg}")

def main():
    print(f"[SMOKE] API = {API}")

    # 1) health
    h = req("GET", "/health")
    print("[SMOKE] /health =>", h)
    expect(h.get("status") in {"ok", "healthy", "up"}, "health status inválido")

    # 2) cria itens mínimos (upsert)
    seed: List[Dict[str, Any]] = [
        {"nome":"saia azul", "categoria":"saia", "cor":"azul", "padrao":"liso", "estilo":"classico", "ocasion":"casual", "clima":"quente", "material":"algodao"},
        {"nome":"blusa branca algodao", "categoria":"blusa", "cor":"branco", "padrao":"liso", "estilo":"classico", "ocasion":"casual", "clima":"quente", "material":"algodao"},
        {"nome":"sapato nude", "categoria":"sapato", "cor":"nude", "padrao":"liso", "estilo":"classico", "ocasion":"casual", "clima":"quente", "material":"couro"},
        {"nome":"bolsa marrom", "categoria":"bolsa", "cor":"marrom", "padrao":"liso", "estilo":"classico", "ocasion":"casual", "clima":"quente", "material":"couro"},
        {"nome":"colar prata minimal", "categoria":"acessorio", "cor":"prata", "padrao":"liso", "estilo":"classico", "ocasion":"casual", "clima":"quente", "material":"metal"},
    ]
    ids = []
    for obj in seed:
        r = req("POST", "/v1/graph/items", obj)
        expect("item_id" in r, "criação de item sem item_id")
        ids.append(r["item_id"])
    print(f"[SMOKE] itens criados/atualizados: {len(ids)}")

    # 3) complementar
    rc = req("POST", "/v1/recommend/complementar", {
        "query": "saia azul", "top_k": 10, "threshold": 0.0,
        "constraints": {"ocasion":"casual","clima":"quente"}
    })
    print("[SMOKE] complementar => ok")
    expect(isinstance(rc.get("results", []), list), "complementar sem lista 'results'")

    # 4) completar
    rcp = req("POST", "/v1/recommend/completar", {
        "itens": ["saia azul"],
        "targets": ["blusa","sapato","bolsa"],
        "top_k": 1
    })
    print("[SMOKE] completar => ok")
    expect("targets" in rcp, "completar sem 'targets'")
    expect(isinstance(rcp.get("targets"), dict), "'targets' não é dict")

    # 5) rebuild
    rb = req("POST", "/v1/graph/rebuild", {})
    print("[SMOKE] rebuild =>", rb)
    expect(isinstance(rb, dict), "rebuild sem corpo json")

    print("[SMOKE] OK ✅")
    sys.exit(0)

if __name__ == "__main__":
    main()
