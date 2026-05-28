# Test conventions for this project's `tests/`

This file applies when Claude is working in `competitive-shelf-intelligence/tests/`.

## What gets tested

- Public-facing functions and behaviors.
- Edge cases surfaced during /clarify.
- Anything in FAILURES.md that has a corresponding fix in code.
- Scraper parsing logic — use saved HTML fixtures, not live network calls.

## What doesn't need a test

- Glue code (one-line wrappers, trivial mappings).
- Configuration constants.
- Pure type definitions.

## Structure

- Mirror the source tree: `src/scrapers/walmart.py` → `tests/scrapers/test_walmart.py`.
- One file per source module unless tests are huge.
- Group related tests by behavior, not by function name.

## Test names

- Describe what the test verifies, in plain English.
- Pattern: `test_<behavior>_when_<condition>`.
- Bad: `test_function_1`, `test_parse`.
- Good: `test_returns_oos_when_add_to_cart_button_absent`,
        `test_extracts_promo_price_when_badge_present`.

## Scraper tests

- Never make live HTTP requests in tests. Use saved HTML fixtures.
- Store fixtures in `tests/fixtures/<retailer>/`.
- If a retailer changes its page structure, add a new fixture and a
  test that documents the failure mode.

## Setup and teardown

- Prefer fresh state per test over shared mutable state.
- If setup is heavy (DB, network), pin it explicitly and document why.

## Assertions

- One concept per test. If a test asserts five unrelated things, split it.
- Assertions should print useful failure messages.

## Mocks and fakes

- Mock at the boundary (network, filesystem, time), not internal pure functions.
- If you mock a function, comment why.

## Running

- Tests must be runnable with a single command. Document it in README.md.
- A failing test is more useful than an unrun test.

## When a test fails

- Read the actual output, not what you expected to see.
- Bisect: which change broke it?
- Don't suppress with `skip` or `xfail` without a PLAN item to come back.
