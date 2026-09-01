# Stage 1: Builder
FROM python:3.14-slim AS builder

# Install uv via 
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Environment tuning for uv inside Docker
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/vortex/.venv

WORKDIR /vortex

# as long as pyproject.toml/uv.lock don't change, Docker reuses this
COPY pyproject.toml uv.lock .python-version ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# --- copy application code ---
COPY ./src ./src
COPY ./alembic ./alembic
COPY alembic.ini ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# Stage 2: Runtime
FROM python:3.14-slim AS runtime

# Create a non-root user
RUN groupadd --gid 1000 vortex && \
    useradd --uid 1000 --gid vortex --shell /bin/bash --create-home vortex

WORKDIR /vortex

# Copy the built venv + app code from the builder stage
COPY --from=builder --chown=vortex:vortex /vortex/.venv ./.venv
COPY --from=builder --chown=vortex:vortex /vortex/src ./src
COPY --from=builder --chown=vortex:vortex /vortex/alembic ./alembic
COPY --from=builder --chown=vortex:vortex /vortex/alembic.ini ./

ENV PATH="/vortex/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER vortex

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "vortex.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]