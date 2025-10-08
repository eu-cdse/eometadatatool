ARG GDAL_VERSION=3.11.0

FROM ghcr.io/osgeo/gdal:ubuntu-full-${GDAL_VERSION} AS builder

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    python3.13

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get install -y \
    build-essential python3.13-dev

COPY --from=ghcr.io/astral-sh/uv /uv /uvx /bin/
ENV UV_FROZEN=1
ENV UV_LINK_MODE=copy
WORKDIR /app
COPY uv.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable


FROM ghcr.io/osgeo/gdal:ubuntu-full-${GDAL_VERSION}

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update \
    && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    python3.13

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT ["metadata_extract"]
