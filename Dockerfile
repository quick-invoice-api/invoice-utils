FROM python:3.11-alpine as base

WORKDIR /base

COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml

RUN apk add --no-cache poetry &&\
    poetry export --only main --format requirements.txt --output requirements.txt --without-hashes --with-credentials &&\
    poetry export --with dev --format requirements.txt --output requirements.dev.txt --without-hashes --with-credentials &&\
    apk del poetry

FROM python:3.11-alpine as test
ARG BUILD_PKGS="build-base zlib-dev jpeg-dev libffi-dev"
WORKDIR /opt/invoice-utils

COPY --from=base /base/requirements.dev.txt .

RUN apk add --no-cache bash curl $BUILD_PKGS &&\
    pip install --upgrade pip wheel setuptools &&\
    pip install -r requirements.dev.txt &&\
    apk del $BUILD_PKGS

COPY . .

ENV PYTHONPATH=/opt/invoice-utils/src:$PYTHONPATH

ENTRYPOINT ["python", "-m", "pytest", "tests/"]

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
COPY entrypoint.sh entrypoint.sh

EXPOSE $PORT
ENTRYPOINT ["./entrypoint.sh"]
