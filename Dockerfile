FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

# Install uv (single layer) and clean up
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && curl -LsSf https://astral.sh/uv/install.sh | sh \
 && ln -s /root/.local/bin/uv /usr/local/bin/uv \
 && apt-get purge -y --auto-remove curl \
 && rm -rf /var/lib/apt/lists/*

# Copy only dependency descriptors first to leverage Docker-layer caching
COPY pyproject.toml uv.lock* ./

# Install only runtime deps (omit dev) and skip installing the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-install-project

# ---- Application code ------------------------------------------------------
COPY src/ ./src
COPY assets/ ./assets
COPY data/ ./data
COPY .env ./.env

EXPOSE 8807
CMD ["uv", "run", "src/app.py"]