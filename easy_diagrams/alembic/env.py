"""Pyramid bootstrap environment."""

import os

from pyramid.paster import get_appsettings
from pyramid.paster import setup_logging
from pyramid_auto_env import replace as replace_env_vars
from sqlalchemy import engine_from_config

from alembic import context
from easy_diagrams.models.meta import Base

# `autoenv_settings`` for overwriting configuration by using environment
# variables for more details see https://pypi.org/project/pyramid-auto-env/
config = context.config

setup_logging(config.config_file_name)


def heroku_options():
    db_url = os.environ.get(
        "DATABASE_URL", ""
    )  # XXX: remove this magic to be replaced with a heroku-run.sh script
    if db_url and db_url.startswith("postgres://"):
        # making heroku to work with sqlalchemy, see https://stackoverflow.com/questions/62688256/sqlalchemy-exc-nosuchmoduleerror-cant-load-plugin-sqlalchemy-dialectspostgre
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
    return {"DATABASE_URL": db_url, "BIND": "0.0.0.0:8000"}


def get_settings():
    # following the same logic from `main` function
    settings = get_appsettings(config.config_file_name, options=heroku_options())
    return replace_env_vars("ED", **settings)


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(url=get_settings()["sqlalchemy.url"])
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    engine = engine_from_config(get_settings(), prefix="sqlalchemy.")

    connection = engine.connect()
    context.configure(connection=connection, target_metadata=Base.metadata)

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
