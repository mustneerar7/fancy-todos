# =============================================================================
# STEP 1: Builder base image
#   - Starts from the official uv image with Python 3.11 (matches .python-version).
#   - uv resolves and installs dependencies straight from uv.lock, so builds are
#     reproducible.
# =============================================================================
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Compile .pyc files at install time (faster startup), copy instead of hardlink
# (the cache is a separate mount), and never let uv download its own Python.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0


# =============================================================================
# STEP 2: Install dependencies only
#   - Copies just pyproject.toml + uv.lock, so this layer is cached until the
#     dependencies change.
#   - --no-dev leaves out pytest/ruff/coverage; --frozen fails if the lockfile
#     is out of date instead of silently re-resolving.
# =============================================================================
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project


# =============================================================================
# STEP 3: Copy application source
#   - Brings in the app package, Alembic config and the start/prestart scripts.
#   - Kept after the dependency step so code edits don't reinstall packages.
# =============================================================================
COPY pyproject.toml uv.lock alembic.ini ./
COPY app ./app
COPY scripts/prestart.sh scripts/start.sh ./scripts/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# =============================================================================
# STEP 4: Slim runtime image
#   - Starts over from plain python:3.11-slim, so uv and build caches are not
#     shipped to production.
#   - Only the ready-made virtualenv and the source are copied across.
# =============================================================================
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

COPY --from=builder /app /app

# Put the virtualenv first on PATH so `fastapi`, `alembic` and `python` resolve
# to it, and make Python log straight to stdout/stderr without buffering.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1


# =============================================================================
# STEP 5: Run as a non-root user
#   - Creates an unprivileged "app" user and hands it the /app directory.
#   - If the app is ever compromised, the attacker is not root inside the container.
# =============================================================================
RUN groupadd --system app \
    && useradd --system --gid app --no-create-home app \
    && chown -R app:app /app

USER app


# =============================================================================
# STEP 6: Healthcheck and startup
#   - Docker polls the /utils/health-check/ endpoint to decide if the app is healthy.
#   - Runs migrations and seeds the superuser (prestart.sh), then serves the app
#     with the multi-worker production server (start.sh). No config is baked
#     into the image; everything comes from the runtime environment.
# =============================================================================
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f\"http://127.0.0.1:{os.environ.get('PORT', '8000')}/api/v1/utils/health-check/\", timeout=4)" || exit 1

CMD ["bash", "-c", "bash scripts/prestart.sh && exec bash scripts/start.sh"]
