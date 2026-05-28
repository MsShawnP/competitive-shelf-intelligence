# competitive-shelf-intelligence — Project Context for Claude

## What this project is

Competitive pricing, promo, and out-of-stock monitoring for specialty food
brands. Scrapes publicly available data from Walmart, Amazon, and Instacart
to give $5M–$20M brands the competitive visibility they can't afford from
syndicated data (IRI/Nielsen). Delivers a Streamlit dashboard showing price
positioning, promotional calendars, OOS events, and review trends. Proves
the Lailara practice can acquire data, not just analyze it.

**Business question this project answers:** What are your competitors doing
on shelf right now — and how does your brand's price, promo, and availability
stack up against them?

## Tier

**Heavy** — full 11-step workflow with gstack gates.

## Stack and tools

TBD — scoped during /clarify and /ce:brainstorm.

(Expected: Python · Playwright · Postgres · Dash · Plotly · pandas)

Notes:
- Dash chosen over Streamlit — already deployed on Fly.io in retail-velocity-decision-tool
- dbt excluded from v1 — plain SQL views sufficient for one dashboard consumer

## Project files

- CLAUDE.md (this file) — permanent rules and facts
- DECISIONS.md — durable choices and reasoning
- HANDOFF.md — current session state
- PLAN.md — current work arc
- FAILURES.md — things tried that didn't work
- docs/solutions/ — documented solutions to past problems (bugs, best practices, workflow patterns), organized by category with YAML frontmatter (module, tags, problem_type); relevant when debugging or implementing in documented areas

Read PLAN.md and HANDOFF.md at session start. DECISIONS.md and
FAILURES.md as relevant.

## Voice and standards

- Economist style: sober, declarative, data-forward
- No marketing voice ("leverage," "synergy," "best-in-class," "unlock")
- No hedging that softens a real finding
- Charts must be readable by non-data-scientist audiences

## Rules

### Honesty and judgment

- Say "I don't know" or "I can't verify this" instead of guessing.
- Tell me what I need to hear, not what I want to hear. If a decision
  looks wrong, say so. Honest assessment, not validation.
- If a rule in this file is too vague to verify, flag it for revision.

### Building and proposing

- No speculative abstractions. If something isn't needed right now,
  don't build it.
- When proposing a tool or approach, present at least two alternatives
  with tradeoffs, even if one is clearly preferred.
- Tie proposals back to the business question above.

### Ethical scraping

- Respect robots.txt and rate limits on every scraper.
- No bypassing authentication, CAPTCHAs, or access controls.
- Collect only publicly visible product page data.
- If a retailer's ToS or anti-bot measures make reliable scraping
  infeasible, flag it and propose an alternative before proceeding.

### How to work the project

- Work in vertical slices — one feature end-to-end before moving to the next.
- Do not start tasks outside the current PLAN.md arc without flagging it first.
- Do not refactor unrelated code unprompted.

### Git branching

- Before risky or experimental changes, suggest creating a branch.
- Keep it simple: `git checkout -b experiment/short-description`.

### Scope creep detection

- If work drifts from PLAN.md for more than ~15 minutes, flag it.

## Working with PLAN.md

PLAN.md defines the current arc of work. Read it at session start.

- Mark tasks complete as they're finished, in the same commit as the work.
- "Out of scope" items are decisions — do not pull them in without explicit
  user approval.

## Session reminders

### Reminding the user to /log

Prompt when: a meaningful change lands, a natural pause point is reached,
or ~30–45 minutes have passed since the last /log.

### Reminding the user to /wrap

Prompt when: context usage crosses 65%, user signals stopping, a natural
milestone is reached, or 90+ minutes have passed.

### Session start protocol

1. Read CLAUDE.md, PLAN.md, and HANDOFF.md.
2. If HANDOFF.md's most recent entry is >24h old AND there are uncommitted
   changes, flag it.
3. Briefly state the starting point from HANDOFF.md.
4. Confirm the current PLAN.md arc is still active.
5. Check Improvement History in PLAN.md for overdue audit.
6. Remind: "type / to see commands. Main ones: /log, /wrap, /improve."

## Defaults

- Default to flagging gaps rather than filling with unverified content.
- Default to short responses unless the task is substantive.
- Default to answering, not offering to answer.
