.POSIX:

MISE       = mise
ZOLA       = $(MISE) exec -- zola
DPRINT     = $(MISE) exec dprint@0.54.0 --
RUMDL      = $(MISE) exec rumdl@0.2.9 --
UV         = $(MISE) exec -- uv
# Runs with python3, PyYAML, and feedparser, so the publish and site jobs need
# no package install beyond requirements/base.txt.
PY         = PYTHONPATH=src python3 -m digest
DIST       = dist
RELEASE    = $(if $(GITHUB_SHA),$(shell git rev-parse --short HEAD 2>/dev/null || echo dev),$(shell git describe --tags --always 2>/dev/null || echo dev))
BUILD_DATE = $(shell date -u +%Y-%m-%dT%H:%MZ)

.PHONY: daily improve check build serve test lint typecheck fmt fmt-check clean

# A local run bills the `claude` login on this machine.
daily:
	@$(UV) run python -m digest daily

improve:
	@$(UV) run python -m digest improve

check:
	@$(PY) check

build:
	@$(PY) build
	@rm -rf $(DIST)
	@RELEASE="$(RELEASE)" BUILD_DATE="$(BUILD_DATE)" $(ZOLA) --root site build --output-dir "$(CURDIR)/$(DIST)"
	@$(MISE) exec -- pagefind --site $(DIST) --glob "digests/[0-9]*/*/index.html"
# Every page is lang="en", so Pagefind never needs its fallback or UI bundles.
	@rm -f $(DIST)/pagefind/pagefind-ui.* $(DIST)/pagefind/pagefind-component-ui.* $(DIST)/pagefind/pagefind-modular-ui.* $(DIST)/pagefind/pagefind-highlight.js $(DIST)/pagefind/wasm.unknown.pagefind

serve:
	@$(PY) build
	@RELEASE="$(RELEASE)" BUILD_DATE="$(BUILD_DATE)" $(ZOLA) --root site serve --interface 127.0.0.1 --port 3000

test:
	@$(UV) run pytest

lint:
	@$(UV) run ruff check .
	@$(UV) run ruff format --check .

typecheck:
	@$(UV) run mypy

# dprint formats YAML, TOML, JSON, CSS, and HTML. rumdl formats Markdown,
# because dprint's Markdown plugin rewrites inline syntax. site/templates/ is
# formatted by hand: markup_fmt reflows Tera tags as prose.
fmt:
	@$(DPRINT) dprint fmt
	@$(RUMDL) rumdl fmt

fmt-check:
	@$(DPRINT) dprint check
	@$(RUMDL) rumdl check .

clean:
	@rm -rf $(DIST) site/data site/content/stories site/content/digests/[0-9]* .run
	@rm -rf .mypy_cache .ruff_cache .pytest_cache .coverage
