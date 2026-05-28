FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# playwright chromium + system deps are pre-installed in this image
# tini is also pre-installed for zombie-process prevention

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m camoufox fetch

COPY . .

# Create cache directory for FileSystemCache
RUN mkdir -p /cache

ENV PYTHONUNBUFFERED=1

# 1 worker: Playwright is not fork-safe.
# Scrapers run as a separate CLI process (python scrape.py), not from gunicorn.
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "1", "--timeout", "120", "app.run:server"]
