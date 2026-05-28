# competitive-shelf-intelligence — Failure Log

What was attempted that didn't work, why it didn't work, and what was
tried next.

Lower bar than DECISIONS.md — capture failures even when they didn't
produce a durable rule.

---

## Format

### YYYY-MM-DD — [One-line failure description]

**Attempted:** [What was tried]

**Why it didn't work:** [Concrete reason]

**What we tried instead:** [The next attempt]

**Status:** Resolved / open / abandoned

**Tags:** [keywords for future text-search]

---

## Entries

### 2026-05-28 — Plain Playwright blocked by Walmart server-side bot detection

**Attempted:** Two approaches in session 1:
1. playwright-stealth v2 + custom "ShelfIntelligenceBot" user-agent
2. playwright-stealth v2 + native Chromium user-agent, stealth applied at
   both context and page level, locale + timezone set to US

**Why it didn't work:** Walmart redirects to `walmart.com/blocked` with HTTP
200 before any JavaScript runs. Detection occurs at the TLS fingerprint /
network layer — possibly based on data-center IP range, TLS cipher ordering,
or HTTP/2 fingerprint. playwright-stealth patches client-side JS signals only
and cannot affect network-layer fingerprinting.

**What we tried instead:** ScraperAPI rendering endpoint
(`api.scraperapi.com/?render=true`). Routes through real browsers on residential
IPs, transparent to our HTML parsing code.

**Status:** Resolved — WalmartScraper uses ScraperAPI when SCRAPERAPI_KEY is set.

**Tags:** walmart, playwright, bot-detection, scraperapi, anti-bot
