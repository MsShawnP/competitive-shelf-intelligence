# Code conventions for this project's `src/`

This file applies when Claude is working in `competitive-shelf-intelligence/src/`.

## Style

- Match the existing code style. If there's a linter config, follow it strictly.
- New files mirror the structure of nearby existing files.
- No mixing of paradigms inside a module without a reason worth stating in DECISIONS.md.

## Naming

- Functions: verbs (`parse_config`, `fetch_prices`, `detect_oos`)
- Variables: nouns (`product_url`, `scraped_row`, `price_trend`)
- Booleans: predicates (`is_available`, `has_promo`, `is_oos`)
- Avoid abbreviations unless they're standard in this codebase.

## Imports

- Sort imports: standard library first, then external, then internal/relative.
- No unused imports left in code.

## Comments

- Comment why, not what. The code already says what.
- TODO comments include a date or issue reference.
- Scraper-specific: comment why a particular selector or wait strategy was
  chosen — retailer page structure is a moving target and the reasoning matters.

## Tests

- Each new non-trivial function gets at least one test in `tests/`.
- Test names describe behavior in plain English.
- Avoid testing implementation details — test inputs and outputs.

## Error handling

- Don't swallow errors. If you catch one, log or rethrow with context.
- No bare `except:` blocks without a comment explaining why.
- Scrapers: on HTTP error or parse failure, log the failure with URL and
  timestamp. Do not silently skip.

## Scraping conventions

- Every scraper has a rate-limit parameter (default: 2–5 seconds between
  requests). Never hardcode 0 delay.
- Respect robots.txt. If `RobotsParser` says don't scrape a path, don't.
- User-agent must identify the scraper honestly. No impersonation.
- On anti-bot detection (CAPTCHA, 429, redirect to access-denied), stop
  and log — do not retry in a tight loop.

## Don't invent

- Before adding a new utility, check if a similar one already exists.
- Before adding a dependency, ask the user (and log to DECISIONS.md).
- Before refactoring an existing pattern, surface it as a question.

## When stuck

- Smallest reproducer.
- One change at a time.
- Run the test, read the actual output.
