.POSIX:

MISE       = mise
ZOLA       = $(MISE) exec -- zola
DPRINT     = $(MISE) exec dprint@0.54.0 --
RUMDL      = $(MISE) exec rumdl@0.2.9 --
DIST       = dist
TODAY      = $(shell date -u +%Y-%m-%d)
RELEASE    = $(if $(GITHUB_SHA),$(shell git rev-parse --short HEAD 2>/dev/null || echo dev),$(shell git describe --tags --always 2>/dev/null || echo dev))
BUILD_DATE = $(shell date -u +%Y-%m-%dT%H:%MZ)

.PHONY: build serve check check-content fmt fmt-check fmt-run stories clean new-digest hn yt events papers books run-log backtest yield

stories:
	@python3 scripts/build_stories.py

hn:
	@python3 scripts/fetch_hn.py

yt:
	@python3 scripts/fetch_youtube.py

events:
	@python3 scripts/fetch_events.py

papers:
	@python3 scripts/fetch_papers.py

books:
	@python3 scripts/fetch_books.py

run-log:
	@python3 scripts/run_log.py

backtest:
	@python3 scripts/backtest_misses.py

yield:
	@python3 scripts/yield_stats.py

build: stories
	@python3 scripts/check_content.py
	@command -v $(MISE) >/dev/null || { echo "mise not found"; exit 1; }
	@rm -rf $(DIST)
	@RELEASE="$(RELEASE)" BUILD_DATE="$(BUILD_DATE)" $(ZOLA) build --output-dir $(DIST)
	@$(MISE) exec -- pagefind --site $(DIST)

serve: stories
	@command -v $(MISE) >/dev/null || { echo "mise not found"; exit 1; }
	@RELEASE="$(RELEASE)" BUILD_DATE="$(BUILD_DATE)" $(ZOLA) build --output-dir $(DIST)
	@$(MISE) exec -- pagefind --site $(DIST)
	@RELEASE="$(RELEASE)" BUILD_DATE="$(BUILD_DATE)" $(ZOLA) serve --interface 127.0.0.1 --port 3000 --output-dir $(DIST) --force

check: build
	@test -f $(DIST)/index.html
	@test -f $(DIST)/feed.xml
	@test -d $(DIST)/pagefind
	@find $(DIST) -type f -not -path '$(DIST)/pagefind/*' \( -name '*.html' -o -name '*.css' -o -name '*.js' \) -print | while read -r f; do \
		size=$$(gzip -c "$$f" | wc -c | tr -d ' '); \
		if [ "$$size" -gt 32768 ]; then \
			echo "$$f exceeds 32KB gzip ($$size bytes)"; exit 1; \
		fi; \
	done
	@echo "check ok"

check-content:
	@python3 scripts/check_content.py

# Formatting is owner-side and intentionally not part of `check` or CI, so
# unattended digest runs are never gated on it. dprint owns TOML/JSON; rumdl
# owns Markdown. Both skip content/ and data/ (see dprint.json and .rumdl.toml).
# The tools install on demand here, so they stay out of mise.toml [tools].
fmt:
	@$(DPRINT) dprint fmt
	@$(RUMDL) rumdl fmt

fmt-check:
	@$(DPRINT) dprint check
	@$(RUMDL) rumdl check .

# fmt-run is the agent-safe subset: it formats only files inside the publish
# allowlist (today's digest, if present, plus the writable memory files), so an
# unattended run can tidy its own output without touching gated routine files.
# Tools install on demand; an unattended run treats a failure here as non-fatal.
fmt-run:
	@files="memory/followups.md memory/entities.md memory/source-reliability.md memory/access-notes.md"; \
	[ -f "content/digests/$(TODAY)/index.md" ] && files="content/digests/$(TODAY)/index.md $$files" || true; \
	$(RUMDL) rumdl fmt --no-exclude $$files

new-digest:
	@python3 scripts/new_digest.py $(TODAY)

clean:
	@rm -rf $(DIST) public
