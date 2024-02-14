FROM python:3.11-alpine as base
ARG WORKDIR=/opt/invoice-utils

WORKDIR $WORKDIR

RUN apk add --no-cache bash curl poetry

COPY poetry.lock poetry.lock
COPY poetry.toml poetry.toml
COPY pyproject.toml pyproject.toml

FROM base as test
ARG BUILD_PKGS="build-base zlib-dev jpeg-dev libffi-dev python3-dev"

RUN apk add --no-cache $BUILD_PKGS &&\
    poetry install --no-root &&\
    apk del $BUILD_PKGS

COPY . .

RUN poetry install

FROM python:3.11-alpine as runtime
ARG BUILD_PKGS="build-base zlib-dev jpeg-dev libffi-dev"

ENV PORT=8000

WORKDIR /opt/invoice-utils

COPY --from=base /base/requirements.txt .

RUN apk add --no-cache bash curl $BUILD_PKGS &&\
    pip install --upgrade pip &&\
    pip install -r requirements.txt &&\
    apk del $BUILD_PKGS

COPY src/ .

EXPOSE $PORT
ENTRYPOINT python -m uvicorn invoice_utils.web:app --host '0.0.0.0' --port ${PORT}
