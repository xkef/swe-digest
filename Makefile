.POSIX:

MISE       = mise
ZOLA       = $(MISE) exec -- zola
DPRINT     = $(MISE) exec dprint@0.54.0 --
RUMDL      = $(MISE) exec rumdl@0.2.9 --
UV         = $(MISE) exec -- uv
# Install-free invocation: works with only python3 + PyYAML, so the scheduled
# workflows and the publish job never need a package install.
PY         = PYTHONPATH=tool/src python3 -m swe_digest
DIST       = dist
TODAY      = $(shell date -u +%Y-%m-%d)
RELEASE    = $(if $(GITHUB_SHA),$(shell git rev-parse --short HEAD 2>/dev/null || echo dev),$(shell git describe --tags --always 2>/dev/null || echo dev))
BUILD_DATE = $(shell date -u +%Y-%m-%dT%H:%MZ)

.PHONY: build serve check check-content fmt fmt-check fmt-run stories clean new-digest hn yt events papers books reddit stars run-log backtest test lint typecheck

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

# Developer/CI checks for the Python package itself. Not part of `check`, so
# the publish gate stays runnable with only python3 + PyYAML.
test:
	@cd tool && $(UV) run pytest

lint:
	@cd tool && $(UV) run ruff check .
	@cd tool && $(UV) run ruff format --check .

typecheck:
	@cd tool && $(UV) run mypy

build: stories
	@$(PY) check-content
	@command -v $(MISE) >/dev/null || { echo "mise not found"; exit 1; }
	@rm -rf $(DIST)
	@RELEASE="$(RELEASE)" BUILD_DATE="$(BUILD_DATE)" $(ZOLA) --root site build --output-dir "$(CURDIR)/$(DIST)"
	@$(MISE) exec -- pagefind --site $(DIST) --glob "digests/[0-9]*/*/index.html"

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
# on it. dprint owns TOML/JSON; rumdl owns Markdown. Both skip site/content/
# and snapshots/ (see tool/dprint.json and tool/.rumdl.toml). The tools
# install on demand here, so they stay out of the mise [tools] config.
fmt:
	@$(DPRINT) dprint fmt --config tool/dprint.json
	@$(RUMDL) rumdl fmt --config tool/.rumdl.toml

fmt-check:
	@$(DPRINT) dprint check --config tool/dprint.json
	@$(RUMDL) rumdl check --config tool/.rumdl.toml .

# fmt-run is the agent-safe subset: it formats only files inside the publish
# allowlist (today's digest, if present, plus the writable memory files), so an
# unattended run can tidy its own output without touching gated routine files.
# Tools install on demand; an unattended run treats a failure here as non-fatal.
fmt-run:
	@$(RUMDL) rumdl fmt --config tool/.rumdl.toml --no-exclude $$($(PY) fmt-paths $(TODAY))

new-digest:
	@$(PY) new-digest $(TODAY)

clean:
	@rm -rf $(DIST) public
