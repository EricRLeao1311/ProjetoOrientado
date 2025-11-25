# ops/Makefile

# ---- Configs ----------
COMPOSE := docker compose -f ops/docker-compose.yml
API_URL ?= http://localhost:8000
CURL    := curl -sf

.DEFAULT_GOAL := help

# ---- Targets ----------
.PHONY: help up up-ci down stop restart ps logs logs-api logs-web seed wait-api test reset down-v rebuild test-docker migrate-catalog

help:
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  make -f ops/Makefile up        - Sobe API, roda smoke; se OK, sobe Web"
	@echo "  make -f ops/Makefile up-ci     - Sobe API e roda apenas o smoke (sem Web)"
	@echo "  make -f ops/Makefile down      - Derruba containers"
	@echo "  make -f ops/Makefile down-v    - Derruba TUDO (⚠ apaga volumes/imagens locais)"
	@echo "  make -f ops/Makefile seed      - Roda seed depois de wait-api (usa catalog.db)"
	@echo "  make -f ops/Makefile test      - Pytest no host"
	@echo "  make -f ops/Makefile test-docker - Pytest dentro do container api"
	@echo "  make -f ops/Makefile rebuild   - Chama /v1/graph/rebuild"
	@echo ""

# --------- UP com smoke test ----------
up:
	$(COMPOSE) up --build -d api
	$(MAKE) -f ops/Makefile wait-api
	@echo ">> Rodando smoke-tests contra $(API_URL)"
	@python3 ops/smoke.py "$(API_URL)" || { \
		echo ""; \
		echo "!!! Smoke falhou. Logs da API e derrubando ambiente..."; \
		$(COMPOSE) logs --no-color api || true; \
		$(COMPOSE) down || true; \
		exit 1; \
	}
	@echo ">> Smoke OK! Subindo Web..."
	$(COMPOSE) up -d web
	@echo ">> Ambiente pronto em: $(API_URL)  (Frontend: http://localhost:5173)"

# Variante CI: não sobe Web; retorna exit code do smoke
up-ci:
	$(COMPOSE) up --build -d api
	$(MAKE) -f ops/Makefile wait-api
	@python3 ops/smoke.py "$(API_URL)"

down:
	$(COMPOSE) down

down-v:
	$(COMPOSE) down -v --remove-orphans --rmi local

stop:
	$(COMPOSE) stop

restart:
	$(COMPOSE) restart

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

logs-api:
	$(COMPOSE) logs -f api

logs-web:
	$(COMPOSE) logs -f web

# Aguarda a API ficar saudável
wait-api:
	@echo "Aguardando API em $(API_URL)/health ..."
	@for i in $$(seq 1 60); do \
		if $(CURL) "$(API_URL)/health" > /dev/null 2>&1; then \
			echo "API OK!"; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "ERRO: API não respondeu em 60s em $(API_URL)/health"; \
	exit 1

# Seed do catálogo (host)
seed: wait-api
	python3 ops/seed.py

# Testes (host) – com fallback sem pytest-cov e proteção WSL
test:
	@if pytest --help | grep -q -- --cov; then \
		echo ">> Rodando testes com cobertura"; \
		PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests --maxfail=1 --disable-warnings --cov=./ --cov-report=term-missing:skip-covered; \
	else \
		echo ">> pytest-cov não encontrado; rodando SEM cobertura (instale com: pip install -e '.[test]')"; \
		PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests -o addopts="" --maxfail=1 --disable-warnings; \
	fi

# Pytest dentro do container da API
test-docker:
	$(COMPOSE) exec api sh -lc "pip install -e '.[test]' && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests --maxfail=1 --disable-warnings"

# Reset total: limpa volumes, sobe com smoke, migra catálogo e semeia
reset: down-v up wait-api migrate-catalog seed

# Reconstrução das arestas
rebuild: wait-api
	@echo "Chamando /v1/graph/rebuild ..."
	@$(CURL) -s -X POST "$(API_URL)/v1/graph/rebuild" -H 'content-type: application/json' -d '{}' || true
	@echo ""
