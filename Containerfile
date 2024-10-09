FROM python:3.13-alpine as base

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CERBOTTANA_CONFIG_PATH=/data
WORKDIR /app


FROM base as builder

RUN apk add --no-cache gcc musl-dev libffi-dev
RUN apk add --no-cache git

RUN python -m venv /opt/poetry-venv
RUN /opt/poetry-venv/bin/pip install --upgrade pip setuptools
RUN /opt/poetry-venv/bin/pip install poetry

RUN python -m venv .venv

COPY poetry.lock pyproject.toml .
RUN /opt/poetry-venv/bin/poetry install --no-interaction --only main --no-root

COPY . .
RUN /opt/poetry-venv/bin/poetry build --no-interaction --format wheel
RUN .venv/bin/pip install --no-deps ./dist/*.whl


FROM builder as test-base

RUN apk add --no-cache gcc musl-dev linux-headers
RUN mkdir -p /data

RUN /opt/poetry-venv/bin/poetry install --no-interaction --no-root


FROM test-base as test

RUN /opt/poetry-venv/bin/poetry run poe black --check
RUN /opt/poetry-venv/bin/poetry run poe darglint
RUN /opt/poetry-venv/bin/poetry run poe mypy
RUN /opt/poetry-venv/bin/poetry run poe ruff
RUN /opt/poetry-venv/bin/poetry run poe pytest --cov

RUN /opt/poetry-venv/bin/poetry run coverage json -o /coverage/coverage.json
RUN /opt/poetry-venv/bin/poetry run coverage report --format=markdown > /coverage/coverage.md


FROM test-base as integration

ENV CERBOTTANA_SHOWDOWN_PATH=/pokemon-showdown

RUN apk add --no-cache nodejs npm
RUN mkdir -p /pokemon-showdown

RUN /opt/poetry-venv/bin/poetry run poe pytest-real-ps-instance


FROM base as final

ENV PATH="/app/.venv/bin:$PATH"
COPY --from=builder /app/.venv .venv

VOLUME /data

ENTRYPOINT [ "cerbottana" ]
