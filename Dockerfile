# syntax=docker/dockerfile:1
FROM mcr.microsoft.com/playwright/python:v1.60.0-noble

# playwright chromium + system deps are pre-installed in this image
# tini is also pre-installed for zombie-process prevention

WORKDIR /app

COPY requirements.txt .
# Authenticate camoufox's GitHub release fetch to avoid api.github.com's
# 60/hr unauthenticated rate limit on the CI builder IP. camoufox's pkgman
# uses a plain requests.get (no token support), so credentials are supplied
# via ~/.netrc (which requests honors) from a build-time secret, then removed
# within the same layer so no token is baked into the image.
RUN --mount=type=secret,id=github_token \
    pip install --no-cache-dir -r requirements.txt && \
    if [ -s /run/secrets/github_token ]; then \
      printf 'machine api.github.com\n  login %s\n  password x-oauth-basic\n' "$(cat /run/secrets/github_token)" > ~/.netrc && \
      chmod 600 ~/.netrc; \
    fi && \
    python -m camoufox fetch && \
    rm -f ~/.netrc

COPY . .

# Create cache directory and non-root user for least-privilege execution
RUN mkdir -p /cache && \
    useradd -r -u 1002 -s /bin/false appuser && \
    chown -R appuser /app /cache

USER appuser

ENV PYTHONUNBUFFERED=1

# 1 worker: Playwright is not fork-safe.
# Scrapers run as a separate CLI process (python scrape.py), not from gunicorn.
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "1", "--timeout", "120", "app.run:server"]
