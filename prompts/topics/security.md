# Security and outages

## Security checks

Primary sources:

- CISA Known Exploited Vulnerabilities catalog.
- NVD CVE feed.
- GitHub Security Advisories (`https://api.github.com/advisories`).
- OSV database.
- Vendor advisories for affected projects.
- Project release notes for patched versions.
- Cloudflare, Google TAG, Microsoft MSRC, Mandiant, Trail of Bits, Wiz, Snyk,
  GitHub Security Lab.

Priority rules:

- Active exploitation outranks CVSS score.
- Widely deployed developer infrastructure outranks niche exposure.
- Supply chain compromise outranks ordinary bug disclosure.
- Include patched version, affected version, exploitation status, and
  mitigation.

Include supply chain incidents, package registry compromise, credential theft,
CI compromise, dependency confusion, and malware campaigns affecting developers.

## Outage checks

Check status and incident pages for:

- GitHub
- Cloudflare
- AWS
- Azure
- Google Cloud
- OpenAI
- Anthropic
- Vercel
- Netlify
- Fastly
- Akamai
- Datadog
- Sentry
- Slack
- Discord
- npm
- PyPI
- Docker Hub
- Stripe
- Twilio
- Okta
- Auth0
- Fastmail

Extraction rules:

- Include user-visible impact, start time, end time if known, affected regions,
  affected services, and root cause if published.
- Prefer official incident reports.
- Do not write root cause speculation as fact.
