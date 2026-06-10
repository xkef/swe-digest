# Claude routine

This repository is a public daily software engineering digest. The morning routine produces one dated digest, updates public memory, validates the site, commits one change, and pushes to `main` when running unattended.

## Read order

Read these files before writing:

1. `README.md`
2. `docs/routine.md`
3. `data/watchlist.toml`
4. `memory/profile.md`
5. `memory/followups.md`
6. `memory/entities.md`
7. `memory/source-reliability.md`
8. `PRIVATE_CONTEXT.md` if it exists locally

`PRIVATE_CONTEXT.md` is local-only. Never quote it, summarize it, or publish details from it.

## Repository rules

- Public output only.
- No secrets, account data, private employer details, private plans, private contacts, or unpublished personal details.
- Use Zola. Keep the site minimal.
- Keep JavaScript limited to static search unless a change has clear reading value.
- Use small inline SVG for illustrations when useful.
- No tracking, analytics, third-party embeds, or external runtime dependencies.
- Do not commit `dist/`, `public/`, local caches, or private files.
- Do not remove untracked files unless explicitly instructed.

## Daily output

Create or update:

```text
content/digests/YYYY-MM-DD/index.md
```

The digest must contain these sections in this order:

1. Top stories
2. AI
3. Security
4. Outages
5. Developer tools
6. Languages and runtimes
7. Infrastructure
8. Engineering posts
9. Markets and companies
10. HN and Reddit pulse
11. Watchlist follow-ups
12. Sources checked

Use this story shape:

```md
### Story title

- Category: AI | Security | Outage | Dev tools | Languages | Infrastructure | Engineering post | Markets | Pulse
- Status: confirmed | developing | rumor | discussion
- Sources: [primary](https://example.com), [discussion](https://news.ycombinator.com/item?id=0)
- Summary: One to three factual sentences.
- Why it matters: One sentence about engineering impact.
- Follow-up: Add only if this needs future tracking.
```

Set front matter at publish time:

```toml
[extra]
status = "published"
source_count = 0
```

Replace `source_count` with the number of distinct source links used in the digest body.

## Morning workflow

1. Sync:

   ```sh
   git switch main
   git pull --ff-only
   git status --short
   ```

   Stop if unrelated local changes exist.

2. Create the daily skeleton:

   ```sh
   make new-digest TODAY=YYYY-MM-DD
   ```

3. Review open memory:

   - Close resolved items in `memory/followups.md`.
   - Carry unresolved items into `Watchlist follow-ups` only when there is new information.
   - Add new recurring entities to `memory/entities.md`.
   - Update `memory/source-reliability.md` only with durable reliability notes.

4. Collect sources using `docs/routine.md` and `data/watchlist.toml`.

5. Verify each candidate story against a primary source when possible.

6. Rank stories by operational impact, security impact, ecosystem scope, migration pressure, and technical depth.

7. Write the digest. Separate verified facts from discussion, hype, and rumor.

8. Update public memory only when it improves future runs.

9. Run validation:

   ```sh
   make check
   git diff --check
   ```

10. Review the diff:

    ```sh
    git diff --stat
    git diff
    ```

11. Commit once. Use a short Conventional Commit subject:

    ```text
    chore: publish digest for YYYY-MM-DD
    ```

    For routine or site changes, use:

    ```text
    docs: update digest routine for YYYY-MM-DD
    feat: add digest site feature
    fix: repair digest site build
    ```

12. Push directly to `main` only after validation:

    ```sh
    git push origin main
    ```

If running in an interactive harness that requires commit approval, stage the intended files, present the exact commit message, and wait.

## Source standards

Primary source means official release note, changelog, advisory, incident report, filing, repository release, maintainer post, status page, or project documentation.

Discussion source means Hacker News, Reddit, Lobsters, YouTube commentary, podcasts, social media, or secondary analysis.

Rules:

- Link primary sources first.
- Link discussion sources after primary sources.
- Do not write a claim as fact unless the source supports it.
- Mark uncertain items as `rumor` or `developing`.
- Mark pure discussion as `discussion`.
- Do not include a story only because it is popular.
- Do not include market news unless it changes engineering context.
- Do not include AI benchmark claims without method or primary source.

## Hacker News procedure

Use Hacker News as discovery and technical discussion.

Check:

- Front page.
- High activity stories from the last 24 hours.
- Ask HN.
- Show HN.
- Targeted queries from `data/watchlist.toml`.

For each relevant item record:

- HN item id.
- Title.
- Original URL.
- HN discussion URL.
- Points and comment count when available.
- Primary source status.

Include an HN item when one of these is true:

- It points to a primary source with engineering impact.
- It contains high-quality technical corrections or context.
- It shows broad practitioner concern about a tool, outage, migration, or security issue.
- It is a Show HN project with unusual technical substance.

Do not treat HN ranking as verification.

## Reddit procedure

Use Reddit as pulse, not verification.

Check hot and top daily posts for subreddits listed in `data/watchlist.toml`.

Include a Reddit topic when one of these is true:

- It links to a primary source that matters.
- Multiple practitioners report the same operational failure mode.
- It reveals adoption friction for a watched tool or platform.
- It shows fast-moving hype around AI or developer tooling that needs labeling.

Label Reddit-only items as `discussion` unless independently verified.

## AI procedure

Track:

- Model releases.
- API changes.
- Pricing changes.
- Deprecations.
- Tool use and agent changes.
- Coding model changes.
- Open weight releases and license changes.
- Inference, quantization, GPU, CUDA, and serving changes.
- AI security issues with practical impact.
- Research only when it has clear engineering relevance or strong ecosystem attention.

Always include model identifier, release date, source, and concrete change when known.

## Security procedure

Prioritize active exploitation over CVSS score.

For CVEs and advisories, capture:

- Affected project.
- Affected versions.
- Patched versions.
- Exploitation status.
- Mitigation.
- Primary advisory.

Include supply chain incidents, package registry compromise, credential theft, CI compromise, dependency confusion, and malware campaigns affecting developers.

## Outage procedure

Use official incident pages when possible.

Capture:

- Provider.
- Affected services.
- Affected regions.
- Start time.
- End time if known.
- User-visible impact.
- Root cause only if published by the provider.

Never infer root cause from user reports.

## Engineering blog procedure

Include posts with implementation detail, code, architecture tradeoffs, debugging, incident analysis, performance analysis, migration detail, language design, or production lessons.

Exclude listicles, launch posts without technical detail, and marketing posts unless they announce a concrete release that affects engineering work.

## YouTube procedure

Use YouTube only when it adds information not present in writing.

Prefer maintainer talks, release explainers, conference talks, live debugging sessions, and technically specific interviews.

Link the video as explanation, not as primary source, unless the video is the primary announcement.

## Markets procedure

Track acquisitions, IPOs, S-1 filings, mergers, governance changes, and licensing changes only when they affect:

- Developer tools.
- AI platforms.
- Cloud infrastructure.
- Security products.
- Databases.
- Open source sustainability.
- Semiconductors.
- Payments infrastructure.
- Platform ownership or roadmap.

Use official filings or reputable reporting. State the engineering relevance directly.

## Writing rules

- No emojis.
- No filler words.
- No exaggeration.
- No soft formulations.
- No conversational transitions.
- No calls to action.
- No en dashes or em dashes.
- Use short factual sentences.
- Keep dates in ISO format.
- Prefer concrete nouns and verbs.
- Separate fact, inference, and discussion.
- Use `confirmed`, `developing`, `rumor`, or `discussion` precisely.
- If no meaningful story exists for a section, write `No major items found.`

## Quality gate

Before publishing, verify:

- The digest has 3 to 7 top stories unless the day is unusually quiet.
- Every story has at least one source.
- Primary sources precede discussion links.
- Rumors and discussions are labeled.
- Security items include affected versions or state that they are not yet known.
- Outage items avoid root cause speculation.
- AI items name the model, product, or API surface.
- Company events state engineering impact.
- Follow-ups are added only for concrete future checks.
- `make check` passes.
- Commit subject is 72 characters or less.
