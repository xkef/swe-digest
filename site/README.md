# Site

The published site, built with Zola: <https://xkef.github.io/swe-digest/>.

## Authoring

Each day is one file, `content/digests/YYYY-MM-DD/index.md`, made of
`### Story` blocks with fixed bold field labels (`Category`, `Status`,
`Sources`, `Summary`, `Why it matters`). `CLAUDE.md` owns the section order,
the story shape, and the front matter.

Everything else is derived at build time by `swe-digest build-stories`:

- one Zola page per story, path-routed to `/digests/DATE/<slug>/`,
- `data/digests/DATE.json`, the section data behind each day page, the home
  page, and the archive rows,
- Pagefind indexes the rendered story pages after `zola build`.

`content/stories/` and `data/` are generated. Do not edit them by hand.

## Layout

- `zola.toml`: site config. The feed is digest days only, capped at 30 in the
  template.
- `content/`: `digests/` (authored), `stories/` and `_index.md` pages, and
  `about/`.
- `templates/`: `base`, `home`, `digest`, `digests` (archive), `story`,
  `about`, `404`, `feed.xml`, and shared macros.
- `static/`: one stylesheet, `favicon.svg`, and `search-init.js`,
  `theme.js`, `localtime.js`.
- `data/`: generated per-day JSON.

## Constraints

- JavaScript is limited to search, the theme toggle, and timestamp
  localization. Every page renders without it.
- No analytics, trackers, third-party embeds, or external runtime
  dependencies. Illustrations are small inline SVG.
- Every built HTML, CSS, and JS file outside the Pagefind index must gzip
  below the per-page budget. `swe_digest.gate.check_size` enforces it in
  `make check`.
- Digest markdown is plain text and links. Raw HTML, event handlers, and
  `javascript:` URIs fail the content gate.
- Digest and story pages link to prefilled issue templates for story
  suggestions and feedback.

## Commands

```sh
make serve   # build and serve on 127.0.0.1:3000
make build   # build into dist/ with Pagefind
make check   # build plus the content, memory, and size gates
```
