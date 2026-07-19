FROM python:3.14-alpine as base

ENV PYTHONUNBUFFERED=1

ENV CERBOTTANA_CONFIG_PATH=/data
WORKDIR /app


FROM base as builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_FROZEN=1
ENV UV_LINK_MODE=copy
ENV UV_NO_EDITABLE=1
ENV UV_NO_SYNC=1

RUN apk add --no-cache git

COPY --from=ghcr.io/astral-sh/uv /uv /bin/uv

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-install-project --no-dev

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev


FROM builder as test-base

RUN apk add --no-cache make
RUN apk add --no-cache nodejs npm

ENV CERBOTTANA_SHOWDOWN_PATH=/pokemon-showdown

RUN mkdir -p /data /pokemon-showdown

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync


FROM test-base as test

RUN make lint
RUN make pytest

RUN uv run coverage json -o /coverage/coverage.json
RUN uv run coverage report --format=markdown > /coverage/coverage.md


FROM test-base as integration

RUN uv run pytest -m integration


FROM base as final

ENV PATH="/app/.venv/bin:$PATH"
COPY --from=builder /app/.venv .venv

VOLUME /data

ENTRYPOINT [ "cerbottana" ]
