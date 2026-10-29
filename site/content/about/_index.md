+++
title = "About, privacy, and use"
description = "What this site is, how to use it, how it handles personal data, and how to request a correction or removal."
template = "about.html"
+++

## What this site is

SWE Digest is an independent, automated software engineering digest. Scheduled
runs collect public engineering news from primary sources, Hacker News, Reddit,
arXiv, and engineering blogs, then publish dated summaries that link back to the
original sources. Digests update five times a day, at 01:30, 05:30, 09:30,
13:30, and 17:30 UTC. It is a personal editorial project. It is not affiliated
with, endorsed by, or speaking for any company, vendor, or the people and
projects it covers.

## No warranty and no reliance

The digest is provided for general information only, "as is" and without
warranty of any kind. Summaries are generated automatically and may contain
errors, omissions, or items that were accurate when written but have since
changed. Nothing here is professional, security, legal, or financial advice.

Security and outage items are time-sensitive and may be incomplete or wrong.
Always verify against the linked primary source (the vendor advisory, release
note, or status page) before acting, and follow your own vendor's official
guidance for patching and incident response. Do not rely on this site as a sole
source for any operational decision.

## Licensing and reuse

- Source code in the repository is licensed under the MIT License (see the
  `LICENSE` file).
- Original digest text and site copy are licensed under
  [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)
  (CC BY 4.0). Reuse with attribution and a link back.
- Linked sources, quoted titles, and other third-party material remain the
  property of their respective owners and are referenced under applicable
  quotation provisions.

## JSON API

Every build publishes the digest as static JSON under `/api/`. Start at
[`/api/index.json`](https://xkef.github.io/swe-digest/api/index.json), which
links to the rest.

| File                  | Holds                                                         |
| --------------------- | ------------------------------------------------------------- |
| `index.json`          | every day, newest first, with its story count and links       |
| `digests/<date>.json` | one day's stories with every field                            |
| `stories/<n>.json`    | all stories, newest first, 100 a page, with `prev` and `next` |
| `search.json`         | each story's date, title, section, category, blurb, thread, and URL |
| `threads.json`        | every follow-up thread, open or closed, and its stories       |

The site is static, so the server answers no queries. To search, download
`search.json` and filter it. Text fields are plain text, with code marked by
backticks. Treat them as untrusted input. Each file carries a `version`, which
changes only when a field changes meaning or goes away.

## Privacy

This site runs no analytics, sets no cookies, embeds no third-party trackers,
and has no public accounts or comment system. Reading a page sends no data to
the maintainer. The site is hosted on GitHub Pages, and the host may record
standard request logs (such as IP address and user agent) under GitHub's own
privacy policy; the maintainer does not collect or process those logs.

A few readers the maintainer invites can enroll a browser to leave feedback on
stories. That feedback goes to a Cloudflare Worker the maintainer runs. Every
page loads the script for it, but in a browser that isn't enrolled the script
sends nothing.

Everyone else interacts through the public GitHub repository. Anything you
submit there is public.

## People and projects covered

The digest reports on public, engineering-relevant work and public statements by
named practitioners and organizations: releases, talks, posts, advisories, and
similar. It links the primary source and attributes statements only to verified
accounts. It does not
publish private contact details, private personal information, or
special-category data, and it does not track private behavior.

This processing is carried out for editorial publication under the Swiss Federal
Act on Data Protection (FADP).

## Corrections and removal

If you are mentioned and want a correction, added context, removal, or exclusion
from future coverage, open a
[correction or removal request](https://github.com/xkef/swe-digest/issues/new?template=removal.yml)
and identify the specific page or item. Use that template rather than a blank
issue: it keeps the request open for a human. Issues are public and are monitored. Reasonable
requests are honored promptly, and asking to be excluded does not require a
reason.
