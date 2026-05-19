# Security Policy

## Supported Versions

Only the latest `0.1.x` release receives security updates during this early-stage period. Once a `1.0` major release ships, we'll formalize the support window.

## Reporting a Vulnerability

If you discover a security vulnerability, please **do NOT** open a public GitHub issue. Instead:

1. Open a private security advisory via GitHub: https://github.com/TopStriker33/vyralforge/security/advisories/new
2. Or email the maintainer directly (see GitHub profile)

Please include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigation if you have one

You'll receive an acknowledgement within 7 days, and we aim to ship a fix within 30 days for confirmed vulnerabilities.

## Scope

Vyral Forge is a local-first tool. The main security surface is:

- **API key handling** — keys live in `.env`, never logged, never committed (enforced via `.gitignore`)
- **Database storage** — SQLite stores scraped public content; no PII handling beyond what Apify returns
- **External calls** — only to declared API endpoints (Apify, Anthropic, optional TikTok-Api)

Out of scope:
- Vulnerabilities in the underlying SDKs (please report to those projects directly)
- Misuse of scraped data by end users (this is the user's responsibility per the MIT license)
- Third-party Apify actors (report to Apify directly)

## Disclosure

We follow coordinated disclosure: a fix ships before a public CVE-style advisory. Credit is given to reporters who request it.
