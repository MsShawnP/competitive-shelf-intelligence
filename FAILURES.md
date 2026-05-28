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

---

### 2026-05-28 — camoufox (Firefox stealth) blocked by Walmart from Fly.io data center

**Attempted:** camoufox v0.4.11 with `os="windows"`, `block_webrtc=True`, `headless=True` launched from Fly.io machine (IAD region, data center IP).

**Why it didn't work:** Walmart bot detection operates at the IP layer — data center IP ranges are blocked before any HTTP or browser fingerprint is evaluated. camoufox patches browser-layer signals (JS navigator, WebGL, canvas) but cannot change the source IP. All scraped pages returned `walmart.com/blocked`.

**What we tried instead:** Google Shopping price fallback (transport 3). Also non-functional — see next entry.

**Status:** Partially resolved — camoufox works from residential IPs (laptops, home machines). For Fly.io, set `SCRAPERAPI_KEY` (residential proxy routing) or `PROXY_URL` (BrightData / Oxylabs residential proxy URL).

**Tags:** walmart, camoufox, firefox, bot-detection, fly-io, data-center-ip

---

### 2026-05-28 — Google Shopping returns JS-only shell to plain requests

**Attempted:** `requests.get("https://www.google.com/search?q=site:walmart.com+...&tbm=shop")` with realistic Chrome headers to extract Walmart prices from Google Shopping results.

**Why it didn't work:** Google returns a `<noscript>` redirect page (`/sorry/...`) when JavaScript is not executed. The full Shopping results require JS rendering. HTML response contained no product prices.

**What we tried instead:** Added as transport 3 in `WalmartScraper` for fallback visibility, but marked non-functional from server environments. For the demo, seeded synthetic competitor data instead.

**Status:** Abandoned for production. Would require Playwright or ScraperAPI rendering to work.

**Tags:** walmart, google-shopping, requests, javascript, bot-detection

---

### 2026-05-28 — Amazon scraping blocked from Fly.io data center immediately

**Attempted:** `python scrape.py --retailer amazon` on Fly.io machine (IAD data center IP).

**Why it didn't work:** Amazon returned CAPTCHA/access-denied on the first request to TRUFF's ASIN URL. Scraper correctly raised `BlockDetectedError` and halted the run (0 scraped, 1 failed). Same IP-layer block as Walmart — data center ranges are flagged before any browser fingerprint evaluation.

**What we tried instead:** No alternative transport for Amazon yet. Real Amazon scraping requires ScraperAPI (`SCRAPERAPI_KEY`) or a residential proxy.

**Status:** Open. Set `SCRAPERAPI_KEY` to resolve.

**Tags:** amazon, bot-detection, captcha, fly-io, data-center-ip

---

### 2026-05-28 — camoufox binary invisible to subprocesses on Windows Microsoft Store Python

**Attempted:** `python -m camoufox fetch` successfully downloaded the Firefox binary under Microsoft Store Python 3.13. `os.path.exists()` returned True. But when camoufox launched via `Camoufox(headless=True)`, Playwright's subprocess could not find the binary at the same path.

**Why it didn't work:** Microsoft Store Python uses UWP filesystem virtualization — the binary was written to a virtualized AppData path visible only to the parent Python process. Subprocesses (including Playwright's browser launcher) resolve to the real path, which has no file. `Test-Path` in PowerShell also returned False (sees the real path), confirming the virtual/real split.

**What we tried instead:** Accepted the fallback to Google Shopping on Windows. camoufox works correctly on Linux/Fly.io when installed via non-UWP Python.

**Status:** Windows-only limitation. Use system Python (not Microsoft Store) or WSL if camoufox is needed locally.

**Tags:** camoufox, windows, uwp, microsoft-store-python, filesystem-virtualization, playwright

---

### 2026-05-28 — Playwright version mismatch in Docker (base image v1.49 vs pip v1.60)

**Attempted:** Dockerfile used `mcr.microsoft.com/playwright/python:v1.49.0-noble` base image but `requirements.txt` allowed `playwright>=1.49,<2.0` which resolved to 1.60.0 at build time.

**Why it didn't work:** On first start, Playwright reported: `Executable doesn't exist at /ms-playwright/chromium_headless_shell-1223/... — current: v1.49.0-noble, required: v1.60.0-noble`. The pip package version and the base image version must match exactly.

**What we tried instead:** Updated Dockerfile to `FROM mcr.microsoft.com/playwright/python:v1.60.0-noble` and pinned `playwright==1.60.0` in requirements.txt. Deploy succeeded.

**Status:** Resolved. Always pin `playwright==X.Y.Z` to match the base image tag exactly.

**Tags:** playwright, docker, version-mismatch, dockerfile, fly-io
