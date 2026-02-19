# ── builder stage ────────────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

# Install uv (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy lockfile + manifest first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies into a system-wide site (no venv needed in container)
RUN uv sync --frozen --no-dev --no-cache

# ── runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.13-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY main.py .
COPY src/ src/

# Put venv on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Cloud Run injects PORT (default 8080). Single worker — Cloud Run handles scaling.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1 --no-access-log"]
