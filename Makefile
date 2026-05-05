# Load .env if present
-include .env
export

# -- defaults (override via .env or env vars) ---------------
COMPOSE               := docker compose

.PHONY: build start stop restart logs status test clean

build:
	$(COMPOSE) build

start:
	$(COMPOSE) up -d

stop:
	$(COMPOSE) down

restart: stop start

logs:
	$(COMPOSE) logs -f

status:
	$(COMPOSE) ps

test:
	echo "Not implemented."

clean:
	$(COMPOSE) down -v

## other 
db:
	uv run python src/db/setup.py
	uv run python src/ingest_data.py
