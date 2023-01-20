FROM python:3.11-alpine as base

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CERBOTTANA_CONFIG_PATH=/data
WORKDIR /app


FROM base as builder

RUN python -m venv /opt/poetry-venv
RUN /opt/poetry-venv/bin/pip install --upgrade pip setuptools
RUN /opt/poetry-venv/bin/pip install poetry

RUN python -m venv .venv

COPY poetry.lock pyproject.toml .
RUN /opt/poetry-venv/bin/poetry install --no-interaction --only main --no-root

COPY . .
RUN /opt/poetry-venv/bin/poetry build --no-interaction --format wheel
RUN .venv/bin/pip install ./dist/*.whl


FROM base as final

COPY --from=builder /app/.venv .venv

VOLUME /data

ENTRYPOINT [ ".venv/bin/bot" ]
