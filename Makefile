.POSIX:

MISE       = mise
ZOLA       = $(MISE) exec -- zola
DPRINT     = $(MISE) exec dprint@0.54.0 --
RUMDL      = $(MISE) exec rumdl@0.2.9 --
UV         = $(MISE) exec -- uv
# Install-free invocation: works with only python3 + PyYAML, so the scheduled
# workflows and the publish job never need a package install.
PY         = PYTHONPATH=agent/src python3 -m swe_digest
DIST       = dist
TODAY      = $(shell date -u +%Y-%m-%d)
RELEASE    = $(if $(GITHUB_SHA),$(shell git rev-parse --short HEAD 2>/dev/null || echo dev),$(shell git describe --tags --always 2>/dev/null || echo dev))
BUILD_DATE = $(shell date -u +%Y-%m-%dT%H:%MZ)

.PHONY: build serve check check-content fmt fmt-check fmt-run stories clean new-digest hn yt events papers books reddit stars run-log backtest weekly-stats test lint typecheck clean-all

stories:
	@$(PY) build-stories

hn:
	@$(PY) fetch hn

yt:
	@$(PY) fetch youtube

events:
	@$(PY) fetch events

papers:
	@$(PY) fetch papers

books:
	@$(PY) fetch books

reddit:
	@$(PY) fetch reddit

stars:
	@$(PY) fetch stars

run-log:
	@$(PY) run-log

backtest:
	@$(PY) backtest

weekly-stats:
	@$(PY) weekly-stats

# Developer/CI checks for the Python package itself. Not part of `check`, so
# the publish gate stays runnable with only python3 + PyYAML.
test:
	@cd agent && $(UV) run pytest

lint:
	@cd agent && $(UV) run ruff check .
	@cd agent && $(UV) run ruff format --check .

typecheck:
	@cd agent && $(UV) run mypy

build: stories
	@$(PY) check-content
	@command -v $(MISE) >/dev/null || { echo "mise not found"; exit 1; }
	@rm -rf $(DIST)
	@RELEASE="$(RELEASE)" BUILD_DATE="$(BUILD_DATE)" $(ZOLA) --root site build --output-dir "$(CURDIR)/$(DIST)"
	@$(MISE) exec -- pagefind --site $(DIST) --glob "digests/[0-9]*/*/index.html"
	@rm -f $(DIST)/pagefind/pagefind-ui.* $(DIST)/pagefind/pagefind-component-ui.* $(DIST)/pagefind/pagefind-modular-ui.* $(DIST)/pagefind/pagefind-highlight.js

serve: stories
	@command -v $(MISE) >/dev/null || { echo "mise not found"; exit 1; }
	@RELEASE="$(RELEASE)" BUILD_DATE="$(BUILD_DATE)" $(ZOLA) --root site build --output-dir "$(CURDIR)/$(DIST)" --force
	@$(MISE) exec -- pagefind --site $(DIST) --glob "digests/[0-9]*/*/index.html"
	@RELEASE="$(RELEASE)" BUILD_DATE="$(BUILD_DATE)" $(ZOLA) --root site serve --interface 127.0.0.1 --port 3000 --output-dir "$(CURDIR)/$(DIST)" --force

check: build
	@test -f $(DIST)/index.html
	@test -f $(DIST)/feed.xml
	@test -d $(DIST)/pagefind
	@$(PY) check-size $(DIST)
	@echo "check ok"

check-content:
	@$(PY) check-content

# Formatting is enforced by CI's `format` job (`make fmt-check`) but is
# intentionally not part of `check`, so unattended digest runs are never gated
# on it. rumdl owns Markdown; dprint owns everything else. Both configs live at
# the root and both skip site/content/ and snapshots/. The tools install on
# demand here, so they stay out of the mise [tools] config.
#
# Two tools rather than one: dprint's Markdown plugin normalizes inline syntax
# and corrupts this repo's prose (see the note in .rumdl.toml). One config per
# tool, both at the root, so neither needs a second invocation.
fmt:
	@$(DPRINT) dprint fmt
	@$(RUMDL) rumdl fmt

fmt-check:
	@$(DPRINT) dprint check
	@$(RUMDL) rumdl check .

# fmt-run is the agent's own output: today's digest, put in the canonical form
# `check-content` enforces. Pure Python, so the publish job can run it with
# nothing installed, and whitespace-only, so it can never rewrite a published
# fact the way a markdown formatter would.
fmt-run:
	@$(PY) fmt-run $(TODAY)

new-digest:
	@$(PY) new-digest $(TODAY)

# Everything a build or a check regenerates, at both levels: the tool caches
# predate the move to agent/ and still accumulate at the root when a command is
# run from there. Not the fetch cache and not the virtualenvs — see clean-all.
CACHES = .mypy_cache .ruff_cache .pytest_cache .hypothesis .rumdl_cache .coverage

clean:
	@rm -rf $(DIST) public site/data site/content/stories site/content/home
	@rm -rf $(CACHES) $(addprefix agent/,$(CACHES))
	@find . -name .DS_Store -not -path './.git/*' -delete
	@echo "clean ok (kept .cache/ and the virtualenvs; use clean-all to drop those)"

# Also the day's collected sources and the virtualenvs. Re-fetching is not free:
# the Reddit fetcher paces its requests and takes tens of minutes to refill.
clean-all: clean
	@rm -rf .cache .run .venv agent/.venv
	@echo "clean-all ok (uv sync in agent/ rebuilds the environment)"
