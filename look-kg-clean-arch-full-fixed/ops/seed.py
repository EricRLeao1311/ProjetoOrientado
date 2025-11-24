import json, os, urllib.request, time
API = "http://localhost:8000"
SEED = [
  {"nome":"saia azul jeans","categoria":"saia","cor":"azul","padrao":"liso","material":"jeans","estilo":"classico","ocasion":"casual","clima":"quente"},
  {"nome":"blusa branca algodao","categoria":"blusa","cor":"branco","padrao":"liso","material":"algodao","estilo":"classico","ocasion":"casual","clima":"quente"},
  {"nome":"sapato nude","categoria":"sapato","cor":"nude","padrao":"liso","material":"couro","estilo":"classico","ocasion":"casual","clima":"quente"},
  {"nome":"bolsa marrom pequena","categoria":"bolsa","cor":"marrom","padrao":"liso","material":"couro","estilo":"classico","ocasion":"casual","clima":"quente"},
  {"nome":"colar prata minimal","categoria":"acessorio","cor":"cinza","padrao":"liso","material":"metal","estilo":"classico","ocasion":"casual","clima":"quente"},
  {"nome":"camisa social preta","categoria":"blusa","cor":"preto","padrao":"liso","material":"algodao","estilo":"formal","ocasion":"formal","clima":"frio"},
  {"nome":"calca bege chino","categoria":"calca","cor":"bege","padrao":"liso","material":"algodao","estilo":"classico","ocasion":"casual","clima":"quente"}
]

def wait_api(url, tries=20):
  for i in range(tries):
    try:
      urllib.request.urlopen(url, timeout=3)
      return True
    except Exception:
      print(f"Aguardando API... ({i+1}/{tries})")
      time.sleep(2)
  return False

def post(path, data):
  req = urllib.request.Request(API + path, method="POST")
  req.add_header("Content-Type","application/json")
  urllib.request.urlopen(req, json.dumps(data).encode("utf-8"), timeout=10).read()

def main():
  if not wait_api(API + "/health"):
    raise SystemExit("API não respondeu no tempo esperado.")
  for p in SEED: post("/v1/items", p)
  print("Seed OK.")

if __name__ == "__main__":
  main()
