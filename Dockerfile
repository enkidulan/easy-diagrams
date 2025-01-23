FROM python:3.13-alpine

# Install python, java and graphviz
RUN  apk update \
  && apk upgrade \
  && apk add ca-certificates \
  && update-ca-certificates \
  && apk add --update coreutils --update openjdk11 tzdata curl wget unzip bash sudo nss graphviz nginx \
  && pip install --no-cache-dir --upgrade poetry \
  && rm -rf /var/cache/apk/*

# create a user
RUN adduser -D app --uid 1000
USER app

# Download plantuml
WORKDIR /plantuml
RUN wget -O /plantuml/plantuml.jar https://github.com/plantuml/plantuml/releases/download/v1.2024.8/plantuml-lgpl-1.2024.8.jar

WORKDIR /app
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PATH=$PATH:/app/.venv/bin/

COPY pyproject.toml poetry.lock ./
RUN touch README.rst
RUN poetry install --compile --without dev --no-root

COPY easy_diagrams ./easy_diagrams
RUN poetry install --compile --without dev
USER root
RUN chown -R app: /app/easy_diagrams/config

USER app
CMD supervisord -c easy_diagrams/config/supervisord.conf
