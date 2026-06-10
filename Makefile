.POSIX:

MISE       = mise
ZOLA       = $(MISE) exec -- zola
DIST       = dist
TODAY      = $(shell date -u +%Y-%m-%d)
RELEASE    = $(if $(GITHUB_SHA),$(shell git rev-parse --short HEAD 2>/dev/null || echo dev),$(shell git describe --tags --always 2>/dev/null || echo dev))
BUILD_DATE = $(shell date -u +%Y-%m-%d)

.PHONY: build serve check clean new-digest

build:
	@command -v $(MISE) >/dev/null || { echo "mise not found"; exit 1; }
	@rm -rf $(DIST)
	@RELEASE="$(RELEASE)" BUILD_DATE="$(BUILD_DATE)" $(ZOLA) build --output-dir $(DIST)

serve:
	@command -v $(MISE) >/dev/null || { echo "mise not found"; exit 1; }
	@RELEASE="$(RELEASE)" BUILD_DATE="$(BUILD_DATE)" $(ZOLA) serve --interface 127.0.0.1 --port 3000 --output-dir $(DIST) --force

check: build
	@test -f $(DIST)/index.html
	@test -f $(DIST)/feed.xml
	@test -f $(DIST)/search_index.en.json -o -f $(DIST)/search_index.json
	@find $(DIST) -type f \( -name '*.html' -o -name '*.css' -o -name '*.js' \) -print | while read -r f; do \
		size=$$(gzip -c "$$f" | wc -c | tr -d ' '); \
		if [ "$$size" -gt 32768 ]; then \
			echo "$$f exceeds 32KB gzip ($$size bytes)"; exit 1; \
		fi; \
	done
	@echo "check ok"

new-digest:
	@python3 scripts/new_digest.py $(TODAY)

clean:
	@rm -rf $(DIST) public
