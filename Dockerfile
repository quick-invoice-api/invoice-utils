FROM python:3.11-alpine as base
ARG BUILD_PKGS="build-base zlib-dev jpeg-dev libffi-dev python3-dev"
ARG WORKDIR=/opt/invoice-utils

WORKDIR $WORKDIR

RUN apk add --no-cache bash curl poetry
COPY poetry.lock poetry.lock
COPY poetry.toml poetry.toml
COPY pyproject.toml pyproject.toml

FROM base as test

RUN apk add --no-cache $BUILD_PKGS && poetry install --no-root && apk del $BUILD_PKGS
COPY . .
RUN poetry install

FROM base
ENV PORT=8000

RUN apk add --no-cache $BUILD_PKGS && poetry install --only main --no-root && apk del $BUILD_PKGS
COPY src/ src
RUN poetry install

EXPOSE $PORT
ENTRYPOINT poetry run python -m uvicorn invoice_utils.web:app --host '0.0.0.0' --port ${PORT}
