# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12
ARG OS_VERSION=trixie
FROM python:${PYTHON_VERSION}-slim-${OS_VERSION} AS base

FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

WORKDIR /workspace

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-editable --no-dev

FROM base AS runner

SHELL ["/bin/bash", "-c"]

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN set -euxo pipefail; \
    adduser \
        --disabled-password \
        --gecos "" \
        --home "/nonexistent" \
        --shell "/sbin/nologin" \
        --no-create-home \
        --uid "${UID}" \
        appuser

# Copy the environment, but not the source code
COPY --from=builder --chown=appuser:appuser /workspace/.venv /workspace/.venv

USER appuser

COPY parse.py /workspace

ENV PATH="/workspace/.venv/bin:$PATH"

ENTRYPOINT ["python3", "/workspace/parse.py"]
