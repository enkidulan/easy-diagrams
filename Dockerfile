FROM enkidulan/plantuml:1.2024.8

# create a user
RUN adduser -D app --uid 1000
USER app
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
