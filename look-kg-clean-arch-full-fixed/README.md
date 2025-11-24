# Look-KG — Sistema de recomendação de looks com Grafos (Clean Architecture)

Este repositório contém um sistema de recomendação de looks baseado em **Knowledge Graph** (grafo de conhecimento) e organizado segundo princípios de **Clean Architecture**.

A aplicação é composta por:
- **API** (backend) — expõe endpoints REST para gerenciar o grafo e gerar recomendações;
- **Web** (frontend) — interface visual para testar as recomendações e interagir com o sistema;
- **Infra/ops** — scripts e configuração de Docker/Compose para subir todo o ambiente com um único comando.

---

## Pré‑requisitos

Para rodar o projeto usando Docker:

- [Docker](https://www.docker.com/) instalado e em execução;
- [Docker Compose](https://docs.docker.com/compose/) — já incluso no Docker Desktop mais recente;
- `make` instalado (no WSL, Linux ou macOS).  
  - No Ubuntu/WSL: `sudo apt-get update && sudo apt-get install make`.

> Em Windows, o caminho recomendado é usar o **WSL** (Ubuntu) e rodar os comandos no terminal do WSL, dentro da pasta do projeto.

---

## Como rodar rapidamente (Docker)

Na raiz do projeto (onde está o `pyproject.toml`), execute:

```bash
make -f ops/Makefile up
```

Esse comando irá:

1. Construir a imagem da **API** e subir o container `api` em modo `detached`;
2. Esperar a API ficar saudável (`/health`);
3. Rodar os **smoke tests** (`ops/smoke.py`) contra a API;
4. Se o smoke passar, subir o container `web` (frontend);
5. Exibir a URL final do ambiente.

Após a execução bem‑sucedida, os serviços estarão disponíveis em:

- **API** (FastAPI + Swagger/OpenAPI):
  - http://localhost:8000/docs
- **Web** (frontend):
  - http://localhost:5173

> Se alguma porta estiver ocupada, ajuste o arquivo `ops/docker-compose.yml` conforme necessário.

### Popular o grafo (seed)

Com os containers rodando, rode o **seed** para preencher o grafo com dados iniciais (catálogo de itens, atributos, relações):

```bash
make -f ops/Makefile seed
```

Isso chama internamente o alvo `wait-api` e, em seguida, executa:

```bash
python3 ops/seed.py
```

O script `seed.py` conversa com a API (via HTTP) e registra os nós/arestas necessários para que o motor de recomendação funcione com um conjunto inicial de dados.

---

## Smoke tests (subida com verificação)

O comando `make -f ops/Makefile up` já roda automaticamente o **smoke** após subir a API.

O fluxo é:

1. Sobe apenas a API:
   ```bash
   docker compose -f ops/docker-compose.yml up --build -d api
   ```
2. Aguarda a API responder em `/health` (até 60s);
3. Executa o script `ops/smoke.py` apontando para a URL da API (`API_URL`, por padrão `http://localhost:8000`);
4. Se o smoke falhar:
   - Exibe logs da API;
   - Derruba o ambiente (`docker compose down`);
   - Retorna código de erro para o shell;
5. Se o smoke passar:
   - Sobe o container `web`.

### Variante para CI: `up-ci`

Existe também um alvo específico para ambientes de CI/CD:

```bash
make -f ops/Makefile up-ci
```

Ele:

- Sobe apenas a API (`api`);
- Aguarda `/health`;
- Roda o `ops/smoke.py` e **não** sobe o `web`.

Isso é útil para pipelines automatizados que querem apenas validar se a API está saudável.

---

## Alvos do `ops/Makefile`

Abaixo, a lista dos principais comandos disponíveis e o que cada um faz.

### `up`

```bash
make -f ops/Makefile up
```

- Sobe a API (`api`) com build;
- Aguarda a API ficar saudável (`/health`);
- Executa os smoke tests (`ops/smoke.py`);
- Em caso de sucesso, sobe o frontend `web`;
- Mostra as URLs de acesso.

### `up-ci`

```bash
make -f ops/Makefile up-ci
```

- Igual ao `up`, mas **não** sobe o frontend;
- Usado principalmente em pipelines de CI para verificar se a API está funcionando.

### `down`

```bash
make -f ops/Makefile down
```

- Derruba todos os containers definidos em `ops/docker-compose.yml`;
- Mantém volumes e imagens.

### `down-v`

```bash
make -f ops/Makefile down-v
```

- Derruba todos os containers;
- **Remove volumes, órfãos e imagens locais** relacionadas ao compose (`--rmi local`);
- Útil para um “reset total” do ambiente (mas também mais destrutivo).

### `stop`

```bash
make -f ops/Makefile stop
```

- Apenas para os containers (mantém tudo pronto para subir de novo com `start`/`up`).

### `restart`

```bash
make -f ops/Makefile restart
```

- Reinicia os containers já existentes.

### `ps`

```bash
make -f ops/Makefile ps
```

- Mostra o status dos serviços definidos no `docker-compose.yml`.

### `logs` / `logs-api` / `logs-web`

```bash
make -f ops/Makefile logs
make -f ops/Makefile logs-api
make -f ops/Makefile logs-web
```

- `logs`: segue os logs de todos os serviços;
- `logs-api`: apenas da API;
- `logs-web`: apenas do frontend.

### `wait-api`

```bash
make -f ops/Makefile wait-api
```

- Alvo auxiliar usado por outros comandos;
- Faz polling em `$(API_URL)/health` (padrão `http://localhost:8000/health`) por até 60 segundos;
- Se a API responder com sucesso, imprime “API OK!”;
- Se não responder no tempo, retorna erro.

### `seed`

```bash
make -f ops/Makefile seed
```

- Aguarda a API (`wait-api`);
- Executa `python3 ops/seed.py` no host;
- Ideal para popular/atualizar o catálogo de itens de teste após subir o ambiente.

### `test` (pytest no host)

```bash
make -f ops/Makefile test
```

- Roda os testes Python localmente (no host, fora do Docker);
- Tenta usar `pytest-cov` se disponível para gerar relatório de cobertura;
- Desativa carregamento automático de plugins (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`) para evitar conflitos.

> Caso você não tenha dependências de teste instaladas, instale com:
> ```bash
> pip install -e ".[test]"
> ```

### `test-docker` (pytest dentro do container)

```bash
make -f ops/Makefile test-docker
```

- Executa os testes **dentro** do container da API;
- Primeiro instala as dependências de teste (`pip install -e ".[test]"`);
- Em seguida roda `pytest` na pasta `tests` do container.

### `reset`

```bash
make -f ops/Makefile reset
```

- Faz um reset completo do ambiente:
  1. Chama `down-v` (derruba containers, remove volumes, órfãos e imagens locais);
  2. Sobe tudo via `up` (incluindo smoke);
  3. Aguarda a API;
  4. Roda o `seed`.

É a forma mais “limpa” de recriar o ambiente do zero.

### `rebuild`

```bash
make -f ops/Makefile rebuild
```

- Aguarda a API (`wait-api`);
- Faz um `POST` para `/v1/graph/rebuild` na API, enviando um corpo vazio `{}`;
- Usa `curl` silencioso (`-s -f`) e ignora erros para não quebrar o comando;
- Útil quando você quer reconstruir as arestas do grafo com base em algum estado já persistido.

---

## Dúvidas comuns

- **A API não responde em `/health` ao rodar `make up`**  
  - Verifique os logs da API:
    ```bash
    make -f ops/Makefile logs-api
    ```
  - Verifique se há portas em uso ou variáveis de ambiente faltando.

- **O `make test` está falhando por falta de plugins ou pytest-cov**  
  - Instale as dependências de teste:
    ```bash
    pip install -e ".[test]"
    ```

- **Quero limpar tudo e começar do zero**  
  - Use:
    ```bash
    make -f ops/Makefile reset
    ```

---

## Autor

Projeto mantido por **Eric Leão**.  

Sinta-se a vontade para adaptar este README, abrir issues, sugerir melhorias ou utilizar o projeto como base para outros sistemas de recomendação baseados em grafos.