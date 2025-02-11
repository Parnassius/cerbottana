FROM python:3.13-alpine@sha256:f9d772b2b40910ee8de2ac2b15ff740b5f26b37fc811f6ada28fce71a2542b0e as base

ENV PYTHONUNBUFFERED=1

ENV CERBOTTANA_CONFIG_PATH=/data
WORKDIR /app


FROM base as builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_FROZEN=1
ENV UV_LINK_MODE=copy

RUN apk upgrade --no-cache
RUN apk add --no-cache gcc musl-dev libffi-dev
RUN apk add --no-cache git

COPY --from=ghcr.io/astral-sh/uv@sha256:a0c0e6aed043f5138957ea89744536eed81f1db633dc9bb3be2b882116060be2 /uv /bin/uv

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-install-project --no-dev --no-editable

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-editable


FROM builder as test-base

RUN apk add --no-cache gcc musl-dev linux-headers
RUN apk add --no-cache make

RUN mkdir -p /data

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-editable


FROM test-base as test

RUN make lint
RUN make pytest

RUN uv run coverage json -o /coverage/coverage.json
RUN uv run coverage report --format=markdown > /coverage/coverage.md


FROM test-base as integration

ENV CERBOTTANA_SHOWDOWN_PATH=/pokemon-showdown

RUN apk add --no-cache nodejs npm

RUN mkdir -p /pokemon-showdown

RUN make pytest-integration


FROM base as final

ENV PATH="/app/.venv/bin:$PATH"
COPY --from=builder /app/.venv .venv

VOLUME /data

ENTRYPOINT [ "cerbottana" ]
