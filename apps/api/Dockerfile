FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libreoffice-impress \
        libreoffice-core \
        fonts-liberation \
        fonts-dejavu \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install uv (Astral Python package manager).
COPY --from=ghcr.io/astral-sh/uv:0.4 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock* /app/
RUN uv sync --frozen --no-dev --no-install-project || uv sync --no-dev --no-install-project

COPY src /app/src
COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic

RUN uv sync --frozen --no-dev || uv sync --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "changetools.main:app", "--host", "0.0.0.0", "--port", "8000"]
