# python:3.12-slim had unpatched Debian CVEs
# python:3.13-slim-bookworm — Python 3.13 LTS on explicitly pinned Debian bookworm
FROM python:3.13-slim-bookworm

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (stub the package dir so hatchling can discover it)
COPY pyproject.toml .
RUN mkdir -p app && touch app/__init__.py
RUN pip install --no-cache-dir -e ".[dev]"

# Copy source
COPY . .

# Run Alembic migrations then start uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
