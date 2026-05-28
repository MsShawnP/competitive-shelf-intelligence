# competitive-shelf-intelligence — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

### 2026-05-28 — Tier set to Heavy
- **Why:** Project has a recurring maintenance offering ($2K–$5K/month)
  and multi-retailer scraping pipeline that will be maintained >3 months.
- **Scope:** Global
- **Do not:** Downgrade to Medium without re-running gstack gates.

---

## Data & Schema

[Decisions about data sources, schemas, transformations]

---

## Scraping & Acquisition

### 2026-05-28 — Use ScraperAPI for Walmart; keep Playwright for Amazon
- **Why:** Plain Playwright (+ playwright-stealth v2) is blocked by Walmart's
  server-side fingerprinting on both data-center and default IPs. Two attempts
  failed in session 1 — status 200 redirect to `/blocked`. Walmart detects
  headless Chromium at the TLS/network layer before any JS stealth patches run.
  ScraperAPI routes through real browsers on residential IPs and is the lowest-
  friction fix that preserves our HTML parsing logic unchanged.
- **Scope:** WalmartScraper only. Amazon is less aggressive; Playwright stays.
- **Do not:** Remove the Playwright fallback from WalmartScraper — it keeps
  fixture-based tests fast without needing ScraperAPI credits.

---

## Visualization

[Chart conventions, palette decisions, interactivity choices]

---

## Output Formats

[Decisions about deliverable formats, structure, organization]

---

## Writing & Voice

[Voice, style, terminology decisions specific to this project]

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions
