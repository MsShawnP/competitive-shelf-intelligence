FROM mcr.microsoft.com/playwright/python:v1.60.0-noble

# playwright chromium + system deps are pre-installed in this image
# tini is also pre-installed for zombie-process prevention

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m camoufox fetch

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
