FROM python:3.11-alpine

# Install python, java and graphviz
RUN  apk update \
  && apk upgrade \
  && apk add ca-certificates \
  && update-ca-certificates \
  && apk add --update coreutils --update openjdk11 tzdata curl wget unzip bash sudo nss graphviz \
  && pip install --no-cache-dir --upgrade poetry \
  && rm -rf /var/cache/apk/*

# create user
RUN adduser -D app --uid 1000

# Download plantuml
USER app
WORKDIR /plantuml
RUN wget -O /plantuml/plantuml.jar https://github.com/plantuml/plantuml/releases/download/v1.2024.8/plantuml-lgpl-1.2024.8.jar

USER app
WORKDIR /app
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

COPY pyproject.toml poetry.lock ./
RUN touch README.rst
RUN poetry install --compile --without dev --no-root

COPY easy_diagrams ./easy_diagrams
RUN poetry install --compile --without dev

CMD poetry run pserve easy_diagrams/config/production.ini BIND=0.0.0.0:${PORT:-8000} DATABASE_URL=${DATABASE_URL}
