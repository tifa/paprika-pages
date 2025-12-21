
ACTIVATE = . venv/bin/activate &&

COL_WIDTH = 10
FORMAT_YELLOW = 33
FORMAT_BOLD_YELLOW = \e[1;$(FORMAT_YELLOW)m
FORMAT_END = \e[0m
FORMAT_UNDERLINE = \e[4m

include .env

COMPOSE = CERT_RESOLVER=$(CERT_RESOLVER) docker compose -f compose.yaml

define usage
	@printf "Usage: make target\n\n"
	@printf "$(FORMAT_UNDERLINE)target$(FORMAT_END):\n"
	@grep -E "^[A-Za-z0-9_ -]*:.*#" $< | while read -r l; do printf "  $(FORMAT_BOLD_YELLOW)%-$(COL_WIDTH)s$(FORMAT_END)$$(echo $$l | cut -f2- -d'#')\n" $$(echo $$l | cut -f1 -d':'); done
endef

.git/hooks/pre-commit:
	@test -d .git && $(ACTIVATE) pre-commit install && touch $@ || true

venv: venv/.touchfile .git/hooks/pre-commit
venv/.touchfile: requirements-dev.txt requirements.txt
	@test -d venv || python3 -m venv venv
	@$(ACTIVATE) pip install uv
	@$(ACTIVATE) uv pip install -Ur requirements-dev.txt
	@touch $@

.PHONY: help
help: Makefile  # Print this message
	$(call usage)

# --------------------------------------------
## Development
# --------------------------------------------

.PHONY: start
start: venv  ## Start the app
	@$(COMPOSE) up -d --build

.PHONY: ui-down
stop:  ## Stop the app
	@$(COMPOSE) down --remove-orphans

.PHONY: restart
restart: stop start  ## Restart the app

.PHONY: sh
sh:  ## Start a shell in the mail container
	@$(COMPOSE) exec app bash

.PHONY: sync
sync:  ## Sync content
	@$(COMPOSE) exec app ./src/sync.py

# --------------------------------------------
## Operations
# --------------------------------------------

.PHONY: up
up:  ## Enter maintenance mode
	@$(COMPOSE) exec app ./src/maintenance.py down

.PHONY: down
down:  ## Exit maintenance mode
	@$(COMPOSE) exec app ./src/maintenance.py up

.PHONY: purge
purge:  ## Purge all data
	@rm -rf ./data/sqlite.db ./src/static/images/*.*
